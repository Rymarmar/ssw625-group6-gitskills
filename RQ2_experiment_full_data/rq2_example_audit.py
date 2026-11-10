#!/usr/bin/env python3
"""Audit RQ2 repetition examples for the SSW625 Phase 3 replication package.

Run alongside rq2_full_analysis.py and rq2_parsing.py, with the downloaded
GitSkills dataset in the sibling data/artifacts/ folder. This script ONLY reads
Parquet files and writes small example-audit reports. It never changes the data
or the full-dataset experiment checkpoints.

The built-in three content hashes reproduce the initial exploratory candidates
from part-00000.parquet. These are CANDIDATES, not verified true/false labels.
"""

import argparse
import csv
from difflib import SequenceMatcher
import json
from pathlib import Path
import re

import duckdb
import tiktoken

from rq2_full_analysis import extract_body
from rq2_parsing import remove_code_blocks, repeated_content_analysis

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = SCRIPT_DIR.parent / "data" / "artifacts" / "part-00000.parquet"
DEFAULT_OUTPUT = SCRIPT_DIR / "rq2_outputs" / "example_audit"
DEFAULT_HASHES = [
    "0c021c5af83e78e5b4d4b25da0c5558eb0f7f904",
    "26a681e10e146686cd62e827f2e00801364fab98",
    "1ea5db6e9a0720eba0558db26a078f83a2f2b99e",
]
MIN_CHARS = 80
MIN_WORDS = 10


def normalize_block(block):
    """Use exactly the RQ2 detector's normalization rule."""
    return " ".join(block.split()).casefold()


def eligible_blocks(text):
    """Split normalized line endings, excluding fenced code as RQ2 does."""
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = remove_code_blocks(text)
    result = []
    for block in re.split(r"\n[ \t]*\n+", text):
        block = block.strip()
        norm = normalize_block(block)
        if len(norm) >= MIN_CHARS and len(norm.split()) >= MIN_WORDS:
            result.append((block, norm))
    return result


def exact_repeat_pairs(blocks):
    """All repeat occurrences after the first, matching the RQ2 metric."""
    first = {}
    repeats = []
    for index, (original, norm) in enumerate(blocks):
        if norm in first:
            first_index, first_text = first[norm]
            repeats.append({
                "first_paragraph": first_index + 1,
                "repeated_paragraph": index + 1,
                "first_excerpt": first_text[:240],
                "repeat_excerpt": original[:240],
            })
        else:
            first[norm] = (index, original)
    return repeats


def near_duplicate_pairs(blocks, threshold=0.88, max_paragraphs=180, max_pairs=5):
    """Candidates for manual review, NOT automatically labeled false negatives.

    Pair search is deliberately bounded to avoid quadratic work on very long files.
    """
    selected = blocks[:max_paragraphs]
    found = []
    for i, (first_text, first_norm) in enumerate(selected):
        for j in range(i + 1, len(selected)):
            second_text, second_norm = selected[j]
            if first_norm == second_norm:
                continue  # exact repeats are already captured above
            ratio = min(len(first_norm), len(second_norm)) / max(len(first_norm), len(second_norm))
            if ratio < threshold:
                continue
            similarity = SequenceMatcher(None, first_norm, second_norm, autojunk=False).ratio()
            if similarity >= threshold:
                found.append({
                    "paragraph_1": i + 1,
                    "paragraph_2": j + 1,
                    "similarity": round(similarity, 4),
                    "excerpt_1": first_text[:240],
                    "excerpt_2": second_text[:240],
                })
                if len(found) >= max_pairs:
                    return found
    return found


def audit_text(content, count_tokens, similarity_threshold=0.88):
    """Compare an exploratory splitter with the actual Phase 3 detector."""
    raw = (content or "").replace("\r\n", "\n").replace("\r", "\n")
    # The user's exploratory command did NOT remove fenced blocks or front matter:
    naive_blocks = []
    for block in re.split(r"\n[ \t]*\n+", raw):
        norm = normalize_block(block.strip())
        if len(norm) >= MIN_CHARS and len(norm.split()) >= MIN_WORDS:
            naive_blocks.append((block.strip(), norm))
    exploratory = exact_repeat_pairs(naive_blocks)

    body = extract_body(content or "")
    eligible = eligible_blocks(body)
    exact = exact_repeat_pairs(eligible)
    repeats, tokens = repeated_content_analysis(body, count_tokens, MIN_CHARS, MIN_WORDS)
    if repeats != len(exact):
        raise AssertionError("Audit parsing differs from rq2_parsing.repeated_content_analysis")
    near = near_duplicate_pairs(eligible, threshold=similarity_threshold)
    return {
        "exploratory_repeat_count": len(exploratory),
        "corrected_repeat_count": repeats,
        "corrected_repeated_tokens": tokens,
        "exact_repeat_examples": exact[:5],
        "near_duplicate_candidates": near,
        "exploratory_only_possible_causes": (
            "Front matter, fenced code, or different paragraph segmentation may explain discrepancies; "
            "inspect the full source before assigning a label."
        ) if len(exploratory) > repeats else "",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(DEFAULT_SOURCE),
                        help="One Parquet part or glob; default reproduces the original three candidates")
    parser.add_argument("--sha", action="append", help="Content SHA to audit (repeat for multiple); default is 3 candidates")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Destination folder for audit reports")
    parser.add_argument("--similarity-threshold", type=float, default=0.88,
                        help="Near-duplicate candidate threshold, not a ground-truth classifier")
    args = parser.parse_args(argv)
    if not (0.0 < args.similarity_threshold <= 1.0):
        parser.error("--similarity-threshold must be in (0,1]")
    hashes = args.sha or DEFAULT_HASHES
    src = Path(args.source)
    # glob paths are valid even when Path.exists is false; check the parent for a simple part.
    if "*" not in str(src) and not src.is_file():
        parser.error(f"Missing Parquet input: {src}")
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    placeholders = ",".join("?" for _ in hashes)
    sql = f"""SELECT file_sha, repo_full_name, path, content
              FROM read_parquet(?)
              WHERE dedup_primary = 1 AND file_sha IN ({placeholders})"""
    with duckdb.connect() as con:
        found_rows = con.execute(sql, [str(src), *hashes]).fetchall()
    encoding = tiktoken.get_encoding("cl100k_base")
    count_tokens = lambda block: len(encoding.encode(block, disallowed_special=()))
    records = []
    for sha, repo, path, content in found_rows:
        metrics = audit_text(content, count_tokens, args.similarity_threshold)
        records.append({"file_sha": sha, "repo_full_name": repo, "path": path, **metrics})
    records.sort(key=lambda r: hashes.index(r["file_sha"]))

    summary_path = output_dir / "rq2_example_audit.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as outf:
        writer = csv.writer(outf)
        writer.writerow(["file_sha", "repo_full_name", "path", "exploratory_repeat_count",
                         "corrected_repeat_count", "corrected_repeated_tokens", "near_duplicate_candidate_count"])
        for rec in records:
            writer.writerow([rec["file_sha"], rec["repo_full_name"], rec["path"],
                             rec["exploratory_repeat_count"], rec["corrected_repeat_count"],
                             rec["corrected_repeated_tokens"], len(rec["near_duplicate_candidates"])])

    evidence_path = output_dir / "rq2_example_evidence.json"
    evidence_path.write_text(json.dumps({
        "description": "Unreviewed textual evidence; do not call these verified TP/FP/FN.",
        "source_parquet": str(src),
        "comparison": "Exploratory raw splitter versus corrected Phase 3 parser",
        "candidate_hashes": hashes,
        "records": records,
        "not_found": [sha for sha in hashes if sha not in {r["file_sha"] for r in records}],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    review_path = output_dir / "rq2_manual_review_template.csv"
    with review_path.open("w", newline="", encoding="utf-8") as outf:
        writer = csv.writer(outf)
        writer.writerow(["file_sha", "reviewer", "manual_label_TP_FP_FN_or_not_applicable",
                         "evidence_reference", "rationale", "review_date"])
        for rec in records:
            writer.writerow([rec["file_sha"], "", "UNREVIEWED", "", "", ""])

    print(f"Candidates requested: {len(hashes)}; representative contents found: {len(records)}")
    for rec in records:
        print(f"{rec['file_sha']} | exploratory={rec['exploratory_repeat_count']} | "
              f"corrected={rec['corrected_repeat_count']} | "
              f"near-match candidates={len(rec['near_duplicate_candidates'])}")
    print(f"Saved {summary_path}")
    print(f"Saved {evidence_path}")
    print(f"Saved {review_path}")
    print("Review evidence manually before assigning true/false-positive/negative labels.")


if __name__ == "__main__":
    main()
