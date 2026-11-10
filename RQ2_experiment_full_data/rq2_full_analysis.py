#!/usr/bin/env python3
"""SSW625 Phase 3: full GitSkills Parquet dataset, RQ2.

Computes structure and token/repetition statistics in a single run, with
per-Parquet-part checkpoints. Does not modify downloaded dataset or Phase 2 code.

Expected layout:
    ssw625_project/
      data/artifacts/part-*.parquet
      RQ2_experiment/                 # original sample work (untouched)
      RQ2_experiment_full_data/       # this package

Run:
    python3 rq2_full_analysis.py --max-parts 1  # optional small staged test
    python3 rq2_full_analysis.py                # full run; resumes completed parts
"""

import argparse
from array import array
import csv
import gzip
import hashlib
import json
from pathlib import Path
from statistics import median
import sys

try:
    import duckdb
except ImportError:
    sys.exit("duckdb is required: python3 -m pip install duckdb")
try:
    import tiktoken
except ImportError:
    sys.exit("tiktoken is required: python3 -m pip install tiktoken")

from rq2_parsing import heading_count, repeated_content_analysis

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
ARTIFACT_DIR = PROJECT_ROOT / "data" / "artifacts"
OUTPUT_DIR = SCRIPT_DIR / "rq2_outputs" / "full_dataset"
WORK_DIR = OUTPUT_DIR / "_work"
METRICS_DIR = WORK_DIR / "per_part_metrics"
MANIFEST_PATH = WORK_DIR / "manifest.json"
DB_PATH = WORK_DIR / "reuse_counts.duckdb"

TOKENIZER = "cl100k_base"
TOKEN_LIMIT = 5000
MIN_BLOCK_CHARS = 80
MIN_BLOCK_WORDS = 10
FIELDS = ["file_sha", "repo_count", "content_present", "body_chars", "headings",
          "has_references", "tokens", "repeated_blocks", "repeated_tokens"]
PIPELINE_VERSION = "2026-11-phase3-full-v1"


def extract_body(content):
    """Preserve the Phase 2 rule: remove leading YAML front matter if closed."""
    text = content.lstrip("\ufeff")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return "".join(lines[i + 1:])
    return text


def _source_fingerprint(parts):
    """Invalidate cached metrics if inputs or parsing/analysis code changes."""
    digest = hashlib.sha256()
    digest.update(PIPELINE_VERSION.encode())
    for src in (Path(__file__).resolve(), SCRIPT_DIR / "rq2_parsing.py"):
        digest.update(src.name.encode())
        digest.update(src.read_bytes())
    for path in parts:
        st = path.stat()
        digest.update(f"{path.resolve()}\t{st.st_size}\t{st.st_mtime_ns}\n".encode())
    return digest.hexdigest()


def _prepare_manifest(parts):
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    expected = {"pipeline": PIPELINE_VERSION, "fingerprint": _source_fingerprint(parts),
                "parquet_files": len(parts)}
    if MANIFEST_PATH.exists():
        current = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if current != expected:
            raise RuntimeError(
                "Input files or analysis code changed since checkpoints were generated.\n"
                "To avoid mixing results from different runs, move/rename the "
                f"checkpoint directory first: {WORK_DIR}\n"
                "Then rerun. Do not delete your data/artifacts folder."
            )
    else:
        # Do not mistakenly trust stale results if the manifest was removed alone.
        if DB_PATH.exists() or list(METRICS_DIR.glob("*.csv.gz")):
            raise RuntimeError(f"Existing checkpoints without manifest: {WORK_DIR}")
        MANIFEST_PATH.write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")


def _connect(memory_limit, threads):
    db = duckdb.connect(str(DB_PATH))
    temp_dir = WORK_DIR / "duckdb_spill"
    temp_dir.mkdir(parents=True, exist_ok=True)
    # Configured for a typical Mac with limited RAM; on-disk spilling is allowed.
    db.execute(f"SET memory_limit='{memory_limit}'")
    db.execute(f"SET threads={threads}")
    db.execute(f"SET temp_directory='{str(temp_dir).replace(chr(39), chr(39)*2)}'")
    db.execute("SET preserve_insertion_order=false")
    return db


def _build_reuse_table(db, parts):
    existing = db.execute("SELECT count(*) FROM information_schema.tables "
                          "WHERE table_name = 'reuse_counts'").fetchone()[0]
    if existing:
        print("Using existing full-dataset reuse-count table.", flush=True)
        return
    print("Computing distinct repository counts for every file_sha in the full dataset...", flush=True)
    glob_path = str(ARTIFACT_DIR / "*.parquet")
    db.execute("""
        CREATE TABLE reuse_counts AS
        SELECT file_sha,
               COUNT(DISTINCT repo_full_name) AS repo_count,
               COUNT(*) AS occurrence_count
        FROM read_parquet(?)
        WHERE file_sha IS NOT NULL
        GROUP BY file_sha
    """, [glob_path])
    # The table is persistent; a later resumed run need not repeat this step.
    summary = db.execute(
        "SELECT COUNT(*), SUM(occurrence_count) FROM reuse_counts"
    ).fetchone()
    print(f"Reuse table: {summary[0]:,} content hashes; "
          f"{summary[1]:,} occurrences with non-null hashes.", flush=True)


def _compute_part(db, part_path, encoder, batch_size=256):
    final = METRICS_DIR / (part_path.stem + ".csv.gz")
    if final.exists():
        print(f"Checkpoint exists, skipping: {part_path.name}", flush=True)
        return
    partial = METRICS_DIR / (part_path.stem + ".csv.gz.partial")
    if partial.exists():
        partial.unlink()  # only an incomplete output file from a previous run
    print(f"Processing {part_path.name}...", flush=True)

    query = """
        SELECT a.file_sha, a.content, a.body_chars, a.has_references, r.repo_count
        FROM read_parquet(?) AS a
        INNER JOIN reuse_counts AS r ON a.file_sha = r.file_sha
        WHERE a.dedup_primary = 1
    """
    # A separate cursor allows incremental fetches instead of fetchall().
    cursor = db.cursor()
    cursor.execute(query, [str(part_path)])
    processed = 0
    with gzip.open(partial, "wt", newline="", encoding="utf-8", compresslevel=3) as outf:
        writer = csv.writer(outf)
        writer.writerow(FIELDS)
        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            for sha, content, chars, has_refs, repo_count in rows:
                if content is None:
                    writer.writerow([sha, repo_count, 0, "", "", has_refs, "", "", ""])
                else:
                    body = extract_body(content)
                    tokens = len(encoder.encode(body, disallowed_special=()))
                    repeated, repeated_tokens = repeated_content_analysis(
                        body,
                        count_tokens=lambda block: len(encoder.encode(block, disallowed_special=())),
                        min_block_chars=MIN_BLOCK_CHARS,
                        min_block_words=MIN_BLOCK_WORDS,
                    )
                    writer.writerow([sha, repo_count, 1, "" if chars is None else chars,
                                     heading_count(content), "" if has_refs is None else has_refs,
                                     tokens, repeated, repeated_tokens])
                processed += 1
                if processed % 10000 == 0:
                    print(f"  {processed:,} representative contents processed in "
                          f"{part_path.name}", flush=True)
    cursor.close()
    partial.replace(final)  # completed shards are committed atomically
    print(f"Completed {part_path.name}: {processed:,} representatives.", flush=True)


class StructureStats:
    def __init__(self):
        self.lengths = array("I")
        self.headings = array("I")
        self.ref_known = 0
        self.ref_yes = 0
        self.short = 0

    def add(self, chars, headings, has_refs):
        self.lengths.append(chars)
        self.headings.append(headings)
        self.short += int(chars < 100)
        if has_refs is not None:
            self.ref_known += 1
            self.ref_yes += int(has_refs == 1)

    @property
    def n(self):
        return len(self.lengths)

    @property
    def median_chars(self):
        return median(self.lengths) if self.n else None

    @property
    def median_headings(self):
        return median(self.headings) if self.n else None

    @property
    def refs_pct(self):
        return 100 * self.ref_yes / self.ref_known if self.ref_known else None


class TokenStats:
    def __init__(self):
        self.values = array("I")
        self.sum_tokens = 0
        self.above_limit = 0
        self.with_repeated = 0
        self.repeated_blocks = 0
        self.repeated_tokens = 0

    def add(self, tokens, repeats, repeated_tokens):
        self.values.append(tokens)
        self.sum_tokens += tokens
        self.above_limit += int(tokens > TOKEN_LIMIT)
        self.with_repeated += int(repeats > 0)
        self.repeated_blocks += repeats
        self.repeated_tokens += repeated_tokens

    @property
    def n(self):
        return len(self.values)

    @property
    def median_tokens(self):
        return median(self.values) if self.n else None

    @property
    def above_pct(self):
        return 100 * self.above_limit / self.n if self.n else None

    @property
    def repeated_pct(self):
        return 100 * self.with_repeated / self.n if self.n else None

    @property
    def overhead_pct(self):
        return 100 * self.repeated_tokens / self.sum_tokens if self.sum_tokens else None


def _pct(value, precision=1):
    return "N/A" if value is None else f"{value:.{precision}f}%"


def _int(value):
    return "N/A" if value is None else f"{value:,.0f}"


def _summarize_metrics(part_paths, counts):
    structures = {name: StructureStats() for name in ("single", "reused")}
    tokens = {name: TokenStats() for name in ("all", "single", "reused")}
    primary_rows = no_content = missing_chars = 0
    for part in part_paths:
        metrics_path = METRICS_DIR / (part.stem + ".csv.gz")
        with gzip.open(metrics_path, "rt", newline="", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            if reader.fieldnames != FIELDS:
                raise RuntimeError(f"Unexpected metrics columns: {metrics_path}")
            for record in reader:
                primary_rows += 1
                if record["content_present"] == "0":
                    no_content += 1
                    continue
                group = "reused" if int(record["repo_count"]) >= 2 else "single"
                if record["body_chars"] != "":
                    refs = (None if record["has_references"] == ""
                            else int(record["has_references"]))
                    structures[group].add(int(record["body_chars"]), int(record["headings"]), refs)
                else:
                    missing_chars += 1
                token_count = int(record["tokens"])
                repeated_blocks = int(record["repeated_blocks"])
                repeated_tokens = int(record["repeated_tokens"])
                tokens[group].add(token_count, repeated_blocks, repeated_tokens)
                tokens["all"].add(token_count, repeated_blocks, repeated_tokens)
    if primary_rows != counts[0]:
        raise RuntimeError(
            f"Representative rows ({primary_rows:,}) do not equal distinct content "
            f"hashes ({counts[0]:,}). Do not report these as complete full-data results."
        )
    return structures, tokens, (primary_rows, no_content, missing_chars)


def _write_reports(structures, tokens, quality, counts):
    primary_rows, missing_content, missing_chars = quality
    total_hashes, total_occurrences = counts
    single, reused = structures["single"], structures["reused"]

    lines1 = [
        "RQ2: INSTRUCTION LENGTH AND STRUCTURE ANALYSIS",
        "GITSKILLS FULL DATASET (PARQUET)", "",
        "1. DATASET INFORMATION",
        f"Distinct content hashes: {total_hashes:,}",
        f"Total file occurrences with non-null hashes: {total_occurrences:,}",
        f"Representative rows: {primary_rows:,}",
        f"Representatives without content (excluded): {missing_content:,}",
        f"Representatives with content but missing body_chars (structure excluded): {missing_chars:,}",
        f"Distinct contents with body under 100 characters: {single.short + reused.short:,}", "",
        "2. COMPARISON GROUPS (STRUCTURAL MEASURES)",
        f"Single-repository skills analyzed: {single.n:,}",
        f"Cross-repository reused skills analyzed: {reused.n:,}", "",
        "3. INSTRUCTION LENGTH",
        f"Median length - single repository: {_int(single.median_chars)} characters",
        f"Median length - reused: {_int(reused.median_chars)} characters", "",
        "4. INSTRUCTION STRUCTURE",
        f"Median Markdown headings - single repository: {_int(single.median_headings)}",
        f"Median Markdown headings - reused: {_int(reused.median_headings)}", "",
        "5. SUPPORTING REFERENCE FILES",
        f"Single-repository skills with references: {_pct(single.refs_pct)}",
        f"Reused skills with references: {_pct(reused.refs_pct)}",
        f"Known reference flags - single: {single.ref_known:,}",
        f"Known reference flags - reused: {reused.ref_known:,}", "",
        "6. METHODOLOGY NOTES",
        "One dedup_primary representative per content hash; reuse uses distinct repository names.",
        "Instruction length uses the dataset's body_chars value.",
        "Markdown headings are counted outside correctly bounded fenced code blocks.",
        "Reference percentages exclude unknown values; missing text/lengths are reported.",
        "Results are descriptive, not measures of runtime or task success.", "",
    ]

    def token_block(label, v):
        return [label,
                f"Number of skills analyzed: {v.n:,}",
                f"Median instruction tokens: {_int(v.median_tokens)}",
                f"Skills exceeding {TOKEN_LIMIT:,} tokens: {_pct(v.above_pct)}",
                f"Skills containing repeated blocks: {_pct(v.repeated_pct)}",
                f"Total repeated blocks: {v.repeated_blocks:,}",
                f"Tokens in repeated blocks: {v.repeated_tokens:,}",
                f"Repeated-block token share: {_pct(v.overhead_pct, 2)}", ""]
    lines2 = [
        "RQ2: INSTRUCTION TOKEN AND REPETITION ANALYSIS",
        "GITSKILLS FULL DATASET (PARQUET)", "",
        "1. DATASET INFORMATION",
        f"Distinct content hashes: {total_hashes:,}",
        f"Representatives without content (excluded): {missing_content:,}",
        f"Tokenizer: {TOKENIZER}",
        "Tokenized content: SKILL.md instruction body (excluding parsed front matter)",
        f"Token threshold: {TOKEN_LIMIT:,}", "",
        "2. OVERALL RESULTS",
    ]
    lines2.extend(token_block("All skills", tokens["all"]))
    lines2.append("3. SINGLE-REPOSITORY SKILLS")
    lines2.extend(token_block("Single-repository", tokens["single"]))
    lines2.append("4. CROSS-REPOSITORY REUSED SKILLS")
    lines2.extend(token_block("Cross-repository reused", tokens["reused"]))
    lines2.extend([
        "5. METHODOLOGY NOTES",
        "Each distinct content hash is counted once, using its designated primary representative.",
        "A reused skill occurs in at least two distinct repositories.",
        "The cl100k_base tokenizer measures instruction-body text, not agent-execution tokens.",
        "Front matter is removed only when it begins the file and has a closing delimiter.",
        "CRLF/CR line endings are normalized before paragraph splitting.",
        "Repeated blocks must contain at least 80 normalized characters and 10 words.",
        "Whitespace and case are normalized; valid fenced code blocks are excluded.",
        "Repeated-token counts exclude the first occurrence of each block.",
        "Repeated text may be useful; no token savings or agent performance is inferred.", "",
    ])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    a = OUTPUT_DIR / "rq2_first_analysis_summary.txt"
    b = OUTPUT_DIR / "rq2_token_overhead_summary.txt"
    a.write_text("\n".join(lines1), encoding="utf-8")
    b.write_text("\n".join(lines2), encoding="utf-8")
    quality_file = OUTPUT_DIR / "rq2_quality_check.txt"
    quality_file.write_text(
        "\n".join([f"Content hashes: {total_hashes:,}",
                   f"Occurrences with non-null hash: {total_occurrences:,}",
                   f"Representative rows: {primary_rows:,}",
                   f"Missing content: {missing_content:,}",
                   f"Missing body_chars among fetched content: {missing_chars:,}",
                   f"Structure analyzed: {single.n + reused.n:,}",
                   f"Token analyzed: {tokens['all'].n:,}"]) + "\n",
        encoding="utf-8",
    )
    print(f"\nSaved full-data results to {OUTPUT_DIR}")
    print(f"  {a.name}\n  {b.name}\n  {quality_file.name}", flush=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--max-parts", type=int, help="Process at most N new Parquet parts (staged check)")
    p.add_argument("--memory-limit", default="2GB", help="DuckDB memory limit, e.g. 1GB, 2GB, 4GB")
    p.add_argument("--threads", type=int, default=2, help="DuckDB threads (default: 2)")
    p.add_argument("--batch-size", type=int, default=256, help="Maximum records fetched per batch")
    args = p.parse_args(argv)
    if args.max_parts is not None and args.max_parts < 1:
        p.error("--max-parts must be >= 1")
    if args.threads < 1 or args.batch_size < 1:
        p.error("--threads and --batch-size must be >= 1")

    parts = sorted(ARTIFACT_DIR.glob("*.parquet"))
    if not parts:
        p.error(f"No Parquet files under {ARTIFACT_DIR}. Keep this project folder next to data/.")
    print(f"Dataset: {ARTIFACT_DIR} ({len(parts)} Parquet parts)", flush=True)
    _prepare_manifest(parts)
    db = _connect(args.memory_limit, args.threads)
    try:
        _build_reuse_table(db, parts)
        counts = db.execute("SELECT COUNT(*), SUM(occurrence_count) FROM reuse_counts").fetchone()
        encoder = tiktoken.get_encoding(TOKENIZER)
        processed_now = 0
        for i, part in enumerate(parts, 1):
            result = METRICS_DIR / (part.stem + ".csv.gz")
            if result.exists():
                print(f"[{i}/{len(parts)}] Already complete: {part.name}", flush=True)
                continue
            if args.max_parts is not None and processed_now >= args.max_parts:
                break
            print(f"[{i}/{len(parts)}] ", end="", flush=True)
            _compute_part(db, part, encoder, args.batch_size)
            processed_now += 1
        remaining = [part for part in parts
                     if not (METRICS_DIR / (part.stem + ".csv.gz")).exists()]
        if remaining:
            print(f"\n{len(remaining)} Parquet parts remain. No final full-data report "
                  "has been written. Rerun the same command without --max-parts "
                  "to resume.", flush=True)
            return 0
        print("All Parquet parts analyzed. Aggregating saved per-content measurements...", flush=True)
        structures, token_stats, quality = _summarize_metrics(parts, counts)
        _write_reports(structures, token_stats, quality, counts)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
