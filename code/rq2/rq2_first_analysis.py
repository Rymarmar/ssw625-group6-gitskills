# %% [markdown]
# # RQ2: First Preliminary Analysis of GitSkills
#
# This script is compatible with Jupytext.
#
# Purpose:
# Compare SKILL.md files used in a single repository with
# those reused across multiple repositories.
#
# Measurements:
# 1. Number of unique skills
# 2. Instruction length
# 3. Number of Markdown headings
# 4. Presence of supporting reference files
#
# Results are printed and saved to a text file.
#
# This is a preliminary study.
# It does not measure actual AI agent performance.


# %% [markdown]
# ## Step 1: Import Libraries

# %%
from pathlib import Path
import re
import sqlite3
from statistics import median


# %% [markdown]
# ## Step 2: Configure File Paths

# %%
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "agent_skills_sample.db"

OUTPUT_DIR = PROJECT_ROOT / "out" / "rq2"

REPORT_PATH = OUTPUT_DIR / "rq2_first_analysis_summary.txt"


# %% [markdown]
# ## Step 3: Connect to the GitSkills Dataset
#
# We analyze each distinct SKILL.md content once.
# Repository counts are used to identify reused skills.

# %%

if not DB_PATH.is_file():
    raise FileNotFoundError(
        f"Database not found: {DB_PATH.resolve()}\n"
        "Place agent_skills_sample.db in the project data/ folder."
    )

query = """
    WITH reuse_counts AS (
        SELECT
            file_sha,
            COUNT(*) AS occurrences,
            COUNT(DISTINCT repo_full_name) AS repository_count
        FROM artifacts
        GROUP BY file_sha
    )

    SELECT
        a.file_sha,
        a.content,
        a.body_chars,
        a.has_references,
        r.repository_count,
        r.occurrences

    FROM artifacts AS a

    JOIN reuse_counts AS r
        ON a.file_sha = r.file_sha

    WHERE a.dedup_primary = 1

    ORDER BY a.file_sha
"""

with sqlite3.connect(
    f"file:{DB_PATH.resolve()}?mode=ro",
    uri=True
) as conn:

    records = conn.execute(query).fetchall()

    total_occurrences = conn.execute(
        "SELECT COUNT(*) FROM artifacts"
    ).fetchone()[0]

if not records:
    raise ValueError(
        "No primary SKILL.md records were found."
    )


# %% [markdown]
# ## Step 4: Measure Instruction Structure
#
# Count Markdown headings in each SKILL.md file.
#
# Headings inside fenced code blocks are ignored.
#
# Heading count is a structural measurement.
# It does not directly measure instruction quality.

# %%

def heading_count(content):

    count = 0
    fence = None

    for line in (content or "").splitlines():

        match = re.match(
            r"^ {0,3}(`{3,}|~{3,})",
            line
        )

        if match:

            marker = match.group(1)

            if fence is None:
                fence = marker[0]

            elif marker[0] == fence:
                fence = None

            continue

        if fence is None and re.match(
            r"^ {0,3}#{1,6}[ \t]+\S",
            line
        ):
            count += 1

    return count


# %% [markdown]
# ## Step 5: Separate Skills into Two Groups
#
# Group A: Skills appearing in one repository.
#
# Group B: Skills reused across two or more repositories.
#
# Each distinct content is counted once.

# %%

single_repo = []
cross_repo = []

for (
    sha,
    content,
    body_chars,
    has_references,
    repository_count,
    occurrences
) in records:

    if content is None or body_chars is None:
        raise ValueError(
            f"Instruction text or length missing for {sha}"
        )

    item = {
        "body_chars": body_chars,
        "headings": heading_count(content),
        "has_references": has_references,
    }

    if repository_count >= 2:
        cross_repo.append(item)

    else:
        single_repo.append(item)


# %% [markdown]
# ## Step 6: Calculate Summary Statistics
#
# We calculate:
# - Number of unique skills
# - Median instruction length
# - Median heading count
# - Percentage with supporting reference files
#
# Unknown reference values are excluded from percentages.

# %%

def summarize(group):

    known_ref_flags = [
        x["has_references"]
        for x in group
        if x["has_references"] is not None
    ]

    return {
        "n": len(group),

        "median_chars": median(
            x["body_chars"] for x in group
        ),

        "median_headings": median(
            x["headings"] for x in group
        ),

        "refs_pct": (
            100 * sum(
                flag == 1 for flag in known_ref_flags
            ) / len(known_ref_flags)
            if known_ref_flags
            else None
        ),

        "refs_known": len(known_ref_flags),
    }


single = summarize(single_repo)

reused = summarize(cross_repo)

short_contents = sum(
    x["body_chars"] < 100
    for x in single_repo + cross_repo
)


# %% [markdown]
# ## Step 7: Prepare the Results Report
#
# The report summarizes only the important findings.
#
# The same results will appear:
# 1. In the terminal or notebook.
# 2. In a separate text file.

# %%

def format_percent(value):

    if value is None:
        return "Not available"

    return f"{value:.1f}%"


lines = [

    "RQ2: FIRST PRELIMINARY ANALYSIS",
    "GITSKILLS SAMPLE DATASET",

    "",

    "1. DATASET INFORMATION",

    f"Distinct SKILL.md contents: {len(records):,}",

    f"Total file occurrences: {total_occurrences:,}",

    f"Contents with body under 100 characters: {short_contents:,}",

    "",

    "2. COMPARISON GROUPS",

    f"Single-repository skills: {single['n']:,}",

    f"Cross-repository reused skills: {reused['n']:,}",

    "",

    "3. INSTRUCTION LENGTH",

    f"Median length - single repository: "
    f"{single['median_chars']:,.0f} characters",

    f"Median length - reused: "
    f"{reused['median_chars']:,.0f} characters",

    "",

    "4. INSTRUCTION STRUCTURE",

    f"Median Markdown headings - single repository: "
    f"{single['median_headings']:,.0f}",

    f"Median Markdown headings - reused: "
    f"{reused['median_headings']:,.0f}",

    "",

    "5. SUPPORTING REFERENCE FILES",

    f"Single-repository skills with references: "
    f"{format_percent(single['refs_pct'])}",

    f"Reused skills with references: "
    f"{format_percent(reused['refs_pct'])}",

    "",

    "6. METHODOLOGY NOTES",

    "Each distinct SKILL.md content is counted once.",

    "Reused skills appear in at least two repositories.",

    "Instruction length is measured in characters.",

    "Markdown headings are counted outside fenced code blocks.",

    "Reference percentages exclude missing values.",

    "This is a descriptive preliminary analysis.",

    "The results do not establish causality.",

    "Actual agent efficiency is not measured.",

    "Token overhead will be investigated separately.",

]


# %% [markdown]
# ## Step 8: Print Results
#
# Display the report in the terminal or Jupyter notebook.

# %%

report = "\n".join(lines) + "\n"

print(report)


# %% [markdown]
# ## Step 9: Save Results to a Text File
#
# Create the output folder automatically.
#
# Save the report for sharing with group members
# and preparing the Phase 2 report.

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