# Group 6 - GitSkills Phase 2 analysis package

Luke Spagnoli, Xiying Huang, Rifat Rahman Khan, Benedict Martinez.

## Submission status

This package combines the supplied RQ1 and RQ2 analyses. The final current
Overleaf report must still be reviewed and added. The overview diagram snapshot
still has an empty RQ2 branch; do not submit it as a completed diagram.
See SUBMISSION-CHECKLIST.md. No API key or paid model call is needed.

RQ1 studies the distribution of exact cross-repository skill reuse.
RQ2's scripts compare length, structure, token counts, and within-file repeated
blocks between single-repository and cross-repository contents. Use the final
question wording from the current Overleaf report, not an older ZIP.

## Setup — Windows PowerShell

Extract this package and open a terminal in the folder containing this README.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Download agent_skills_sample.zip from
https://github.com/giuseppedestefanis/gitskills-sample and extract its database
to `data/agent_skills_sample.db`. The database is not included in this ZIP.
The first tokenization run may download the cl100k_base vocabulary; it does
not send the skill texts to an AI service. Later runs can use the local cache.

## RQ1 commands

```powershell
.\.venv\Scripts\python.exe code/rq1_reuse.py sample data/agent_skills_sample.db
.\.venv\Scripts\python.exe code/rq1_reuse.py analyze
.\.venv\Scripts\python.exe code/make_figures.py
.\.venv\Scripts\python.exe code/check_saved_results.py
.\.venv\Scripts\python.exe code/check_report_claims.py data/agent_skills_sample.db
```

The sample command creates two parquet files under data/. Analyze writes seven
tables under out/. check_saved_results compares them to supplied results/rq1/.
make_figures generates the two RQ1 result plots under figures/. It does not
overwrite the overview diagram. The supplemental prose checks document Gini
and within-repository path statistics; see RQ1_REVIEW.md for unresolved claims.

To generate a new BLANK manual coding workbook (not regenerate human labels):

```powershell
.\.venv\Scripts\python.exe code/make_coding_sheet.py data/agent_skills_sample.db rq1_coding_sheet.xlsx
```

The 50 completed manual labels and original codebook are in results/rq1/.
The workbook generator's codebook predates the completed CSV codebook; clarify
same-owner copy and group C's hosting categories as noted in RQ1_REVIEW.md.

## RQ2 commands

```powershell
.\.venv\Scripts\python.exe code/rq2/rq2_first_analysis.py
.\.venv\Scripts\python.exe code/rq2/rq2_token_overhead.py
.\.venv\Scripts\python.exe code/check_rq2_results.py
```

RQ2 reads the same database directly; it does not require RQ1 parquet outputs.
New summaries go to out/rq2/. Rifat's original summaries stay in results/rq2/.
The checker compares normalized text (ignoring outer whitespace only).

The .py files have only input/output paths adapted for this shared layout;
the analysis logic is retained. Original notebooks are included for reference:
they still expect agent_skills_sample.db in the notebook's working directory
and write rq2_outputs/. The commands above are the verified combined workflow.

## What RQ2 measures

- One representative per distinct content; groups use one versus at least two repositories.
- First script: dataset body_chars, ATX-style Markdown headings outside fenced
  code, and the representative folder's reference-file flag. Heading parsing
  is heuristic, not a full Markdown parser, and scans the stored file text.
- Token script: cl100k_base counts of the instruction body after removing
  detected leading front matter, including code blocks in total token counts.
- The 5,000-token threshold is a descriptive cutoff, not a model context limit.
- Repetition means repeated blank-line-separated blocks WITHIN a file, outside
  fenced code, matching after whitespace/case normalization, with at least
  80 characters and 10 words. Later copies are counted; the first is not.
- Repeated-block token share is summed separately tokenized repeated blocks
  divided by summed body tokens. It is an indicator, not an exact counterfactual
  saving from deleting text and not a measurement of wasted tokens.
- These descriptive results do not establish causality, actual runtime,
  task success, invocation frequency, or that repeated instructions are unnecessary.

## Files

| Folder/file | Purpose |
|---|---|
| code/ | RQ1 scripts, checks, and original RQ1 notebook |
| code/rq2/ | RQ2 scripts and original notebooks |
| data/README.md | Dataset instructions |
| results/rq1/ | Original RQ1 table snapshots and human coding |
| results/rq2/ | Original RQ2 summaries |
| out/ | Fresh results and verification records |
| figures/ | Regenerated RQ1 result plots |
| report/figures/ | Original figure snapshots; overview still incomplete |
| RQ1_REVIEW.md | Earlier RQ1 audit and outstanding checks |
| REPORT-INTEGRATION.md | Earlier draft edits; confirm against current RQ2 |
| SUBMISSION-CHECKLIST.md | Remaining integration tasks |
