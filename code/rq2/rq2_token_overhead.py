# %% [markdown]
# # RQ2: Preliminary Analysis of Potential Input-Token Overhead
#
# Dataset: GitSkills Sample
#
# Purpose:
# Investigate instruction-token requirements and repeated
# instruction content in SKILL.md files.
#
# We compare:
# 1. Skills used in a single repository.
# 2. Skills reused across multiple repositories.
#
# Measurements:
# - Instruction token counts
# - Skills exceeding 5,000 tokens
# - Repeated instruction blocks
# - Tokens associated with repeated blocks
#
# This is a preliminary study.
# We do not measure actual AI agent performance.
#
# The script prints results and saves a text report.
#
# Compatible with Jupytext.


# %% [markdown]
# ## Step 1: Import Libraries

# %%

from pathlib import Path
from collections import defaultdict
from statistics import median
import sqlite3
import re

try:
    import tiktoken
except ImportError:
    raise SystemExit(
        "The tiktoken library is missing.\n"
        "Install it using:\n"
        "python3 -m pip install tiktoken"
    )


# %% [markdown]
# ## Step 2: Configure Paths and Settings

# %%

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "agent_skills_sample.db"

OUTPUT_DIR = PROJECT_ROOT / "out" / "rq2"

REPORT_PATH = OUTPUT_DIR / "rq2_token_overhead_summary.txt"

TOKEN_LIMIT = 5000

MIN_BLOCK_CHARS = 80

MIN_BLOCK_WORDS = 10

TOKENIZER_NAME = "cl100k_base"


# %% [markdown]
# ## Step 3: Initialize Tokenizer
#
# We use the cl100k_base tokenizer.
#
# Token counts depend on the tokenizer.
# They are not actual agent execution measurements.

# %%

encoding = tiktoken.get_encoding(TOKENIZER_NAME)


def count_tokens(text):

    if not text:
        return 0

    return len(
        encoding.encode(
            text,
            disallowed_special=()
        )
    )


# %% [markdown]
# ## Step 4: Load GitSkills Data
#
# Each distinct SKILL.md content is analyzed once.
#
# Repository counts distinguish reused skills
# from skills used in only one repository.

# %%

if not DB_PATH.is_file():

    raise FileNotFoundError(
        f"Database not found: {DB_PATH.resolve()}"
    )


query = """
WITH repository_counts AS (
    SELECT
        file_sha,
        COUNT(DISTINCT repo_full_name) AS repo_count
    FROM artifacts
    GROUP BY file_sha
)

SELECT
    a.file_sha,
    a.content,
    r.repo_count

FROM artifacts AS a

JOIN repository_counts AS r
    ON a.file_sha = r.file_sha

WHERE a.dedup_primary = 1
  AND a.content IS NOT NULL

ORDER BY a.file_sha
"""


with sqlite3.connect(
    f"file:{DB_PATH.resolve()}?mode=ro",
    uri=True
) as conn:

    records = conn.execute(query).fetchall()


if not records:
    raise ValueError("No skill contents were found.")


print(f"Loaded {len(records):,} distinct SKILL.md contents.")


# %% [markdown]
# ## Step 5: Extract Instruction Body
#
# SKILL.md files may contain YAML front matter.
#
# We remove the front matter when it is at the
# beginning of the file and has a closing delimiter.
#
# This keeps the analysis focused on the
# instruction body rather than metadata.

# %%

def extract_body(content):

    text = content.lstrip("\ufeff")

    lines = text.splitlines(keepends=True)

    if not lines:
        return ""

    if lines[0].strip() != "---":
        return text

    for index in range(1, len(lines)):

        if lines[index].strip() in ("---", "..."):

            return "".join(lines[index + 1:])

    return text


# %% [markdown]
# ## Step 6: Remove Code Blocks for Repetition Detection
#
# We exclude fenced code blocks when searching for
# repeated instruction paragraphs.
#
# However, code blocks remain included in the
# total instruction-token measurements.

# %%

def remove_code_blocks(text):

    result = []

    fence_char = None

    fence_length = 0

    for line in text.splitlines(keepends=True):

        stripped = line.rstrip("\r\n")

        match = re.match(
            r"^ {0,3}(`{3,}|~{3,})",
            stripped
        )

        if fence_char is None:

            if match:

                marker = match.group(1)

                fence_char = marker[0]

                fence_length = len(marker)

                result.append("\n\n")

            else:
                result.append(line)

        else:

            closing_pattern = (
                r"^ {0,3}"
                + re.escape(fence_char)
                + r"{"
                + str(fence_length)
                + r",}[ \t]*$"
            )

            if re.match(closing_pattern, stripped):

                fence_char = None

                fence_length = 0

                result.append("\n\n")

    return "".join(result)


# %% [markdown]
# ## Step 7: Detect Repeated Instruction Blocks
#
# We examine paragraphs separated by blank lines.
#
# A block must contain:
# - At least 80 characters
# - At least 10 words
#
# We normalize whitespace and letter case.
#
# The first occurrence is not counted as repeated.
# Later occurrences of the same normalized block are.
#
# This is a conservative indicator of repetition.
# It does not prove that repeated text is unnecessary.

# %%

def repeated_content_analysis(body):

    text = remove_code_blocks(body)

    blocks = re.split(
        r"\n[ \t]*\n+",
        text
    )

    seen = set()

    repeated_blocks = 0

    repeated_tokens = 0

    for block in blocks:

        block = block.strip()

        normalized = " ".join(
            block.split()
        ).casefold()

        if len(normalized) < MIN_BLOCK_CHARS:
            continue

        if len(normalized.split()) < MIN_BLOCK_WORDS:
            continue

        if normalized in seen:

            repeated_blocks += 1

            repeated_tokens += count_tokens(block)

        else:

            seen.add(normalized)

    return repeated_blocks, repeated_tokens


# %% [markdown]
# ## Step 8: Analyze Every Skill
#
# We calculate instruction tokens and repeated
# content for each unique SKILL.md file.
#
# The analysis separates:
# - Single-repository skills
# - Cross-repository reused skills

# %%

groups = defaultdict(list)

for file_sha, content, repo_count in records:

    body = extract_body(content)

    total_tokens = count_tokens(body)

    repeated_blocks, repeated_tokens = (
        repeated_content_analysis(body)
    )

    if repo_count >= 2:
        group_name = "Cross-repository reused"
    else:
        group_name = "Single-repository"

    groups[group_name].append({

        "total_tokens": total_tokens,

        "repeated_blocks": repeated_blocks,

        "repeated_tokens": repeated_tokens,

        "above_limit": total_tokens > TOKEN_LIMIT

    })


print("Instruction and repetition analysis completed.")


# %% [markdown]
# ## Step 9: Calculate Summary Statistics
#
# Measurements:
# - Number of skills
# - Median instruction tokens
# - Percentage exceeding 5,000 tokens
# - Percentage containing repeated blocks
# - Total repeated-block tokens
# - Repeated tokens as a share of all tokens

# %%

def summarize(items):

    n = len(items)

    total_tokens = sum(
        x["total_tokens"] for x in items
    )

    total_repeated_tokens = sum(
        x["repeated_tokens"] for x in items
    )

    above_limit = sum(
        x["above_limit"] for x in items
    )

    files_with_repetition = sum(
        x["repeated_blocks"] > 0 for x in items
    )

    total_repeated_blocks = sum(
        x["repeated_blocks"] for x in items
    )

    return {

        "n": n,

        "median_tokens": median(
            x["total_tokens"] for x in items
        ),

        "total_tokens": total_tokens,

        "above_limit_pct": (
            100 * above_limit / n if n else 0
        ),

        "repetition_pct": (
            100 * files_with_repetition / n if n else 0
        ),

        "repeated_blocks": total_repeated_blocks,

        "repeated_tokens": total_repeated_tokens,

        "overhead_pct": (
            100 * total_repeated_tokens / total_tokens
            if total_tokens else 0
        )

    }


single = summarize(
    groups["Single-repository"]
)

reused = summarize(
    groups["Cross-repository reused"]
)

all_skills = summarize(
    groups["Single-repository"]
    + groups["Cross-repository reused"]
)


# %% [markdown]
# ## Step 10: Prepare Results Report
#
# The report includes only important findings.
#
# It is designed to be:
# - Easy to read
# - Easy to share with group members
# - Useful when writing the Phase 2 report

# %%

def group_report(name, stats):

    return [

        name,

        f"Number of skills: {stats['n']:,}",

        f"Median instruction tokens: "
        f"{stats['median_tokens']:,.0f}",

        f"Skills exceeding {TOKEN_LIMIT:,} tokens: "
        f"{stats['above_limit_pct']:.1f}%",

        f"Skills containing repeated blocks: "
        f"{stats['repetition_pct']:.1f}%",

        f"Total repeated blocks: "
        f"{stats['repeated_blocks']:,}",

        f"Tokens in repeated blocks: "
        f"{stats['repeated_tokens']:,}",

        f"Repeated-block token share: "
        f"{stats['overhead_pct']:.2f}%",

        ""

    ]


lines = [

    "RQ2: PRELIMINARY TOKEN OVERHEAD ANALYSIS",

    "GITSKILLS SAMPLE DATASET",

    "",

    "1. DATASET INFORMATION",

    f"Distinct SKILL.md contents analyzed: {len(records):,}",

    f"Tokenizer: {TOKENIZER_NAME}",

    "Tokenized content: SKILL.md instruction body",

    f"Token threshold: {TOKEN_LIMIT:,}",

    "",

    "2. OVERALL RESULTS",

]

lines.extend(
    group_report("All skills", all_skills)
)

lines.append(
    "3. SINGLE-REPOSITORY SKILLS"
)

lines.extend(
    group_report("Single-repository", single)
)

lines.append(
    "4. CROSS-REPOSITORY REUSED SKILLS"
)

lines.extend(
    group_report("Cross-repository reused", reused)
)

lines.extend([

    "5. METHODOLOGY NOTES",

    "Each distinct SKILL.md content is analyzed once.",

    "A reused skill appears in at least two repositories.",

    "Token counts exclude leading YAML front matter when detected.",

    "Token counts depend on the selected tokenizer.",

    "Repeated blocks are detected within individual files.",

    "Whitespace and letter case are normalized for matching.",

    "Only blocks with at least 80 characters and 10 words are checked.",

    "Fenced code blocks are excluded from repetition detection.",

    "Repeated-token counts exclude the first occurrence of each block.",

    "Repeated-block token share measures potential overhead.",

    "Repeated content is not necessarily unnecessary.",

    "Removing repeated content may affect instruction quality.",

    "Reuse frequency does not measure agent execution frequency.",

    "This is a preliminary descriptive study.",

    "Actual agent runtime and task success are not measured.",

])


# %% [markdown]
# ## Step 11: Print Results
#
# Display the report in the terminal or notebook.

# %%

report = "\n".join(lines) + "\n"

print()
print(report)


# %% [markdown]
# ## Step 12: Save Results
#
# Save the same report in a separate text file.
#
# This file can be shared with group members
# and used when preparing the Phase 2 report.

# %%

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

REPORT_PATH.write_text(
    report,
    encoding="utf-8"
)

print(
    f"Report saved to: {REPORT_PATH.resolve()}"
)