# Review of the supplied Phase 2 package

## Verified

The public sample was downloaded from the dataset repository linked in the
original README. Database SHA-256:
`683888c923a51952fb66f83f21351ed5bf1127ddddf380e517592ae27c367658`.

- The original sample-extraction and analysis scripts ran successfully.
- All seven regenerated CSV tables match the supplied snapshots (comparison
  ignores row order and numeric dtype, with strict numerical tolerances).
- Both RQ1 result plots were regenerated and visually inspected.
- The manual workbook generator ran successfully after providing openpyxl.
- All 50 sampled content hashes, in order, match the completed coding CSV.
- Manual coding counts match the report's table: general/project-specific
  counts 20/0, 18/2, and 7/3 in A, B, and C. There are 24 collection/mirror
  and nine independent-adoption labels among the 40 A/B contents.
- The original notebook's embedded analysis matches the standalone analysis
  script; the notebook itself was not run in Colab.

These checks verify reproduction, not correctness of each human classification.

## Changes in this separate reviewed copy

- Added openpyxl (required by the workbook generator) and explicitly listed numpy.
- Expanded README with Windows commands, input/output paths, manual analysis
  instructions, and the package's incomplete RQ2 status.
- Removed the outdated overview-generation block from make_figures.py. This
  prevents a routine RQ1 plot run from creating a conflicting RQ2 diagram.
  The separate make_overview_figure.py is preserved, with its RQ2 box unfinished.
- Used a bundled Matplotlib font for portable RQ1 plot rendering.
- Added check_saved_results.py to compare fresh tables with the original snapshots.
- Added check_report_claims.py for explicitly defined Gini and within-repository
  path checks. It does not change the original RQ1 calculations or labels.

## Issues to resolve before submission

1. **RQ2 remains missing.** Integrate Rifat's final question, method, code,
   findings, and overview-figure branch. The Overleaf ZIP has a blank RQ2
   question; the newer PDF/pasted text had token-requirements wording.
2. **Gini discrepancy.** Across all 13,000 distinct contents, the standard Gini
   of repository counts is 0.4047502308053712, rounding to 0.40, not the report's
   0.41. Ask Xiying whether a different population/formula was used. If the
   population is all contents, use 0.405 (three decimals) or 0.40 (two decimals).
3. **Other prose claims.** The supplemental check reproduces 524 within-only
   contents and 70.6107% with multiple top-level path components. The main
   script did not export these statistics. The 15.2% versus 5.0% collection/mirror
   heuristic still needs its exact query/definition from Xiying; the report's
   "keywords such as awesome and mirror" is insufficient to recreate it exactly.
4. **Codebook consistency.** The workbook-generator codebook predates the
   completed CSV codebook (same-owner copy is missing). Both say group C's
   reuse channel is not applicable, yet six C records have categories. The
   report interprets those as hosting-repository categories. Document that
   distinction consistently. Preserve the completed labels.
5. **Interpretation.** Do not call 78% "never reused"; they occur in one
   repository in this sample. Do not translate 24/40 sampled contents into
   a population share of copies or assert causal distribution channels.
6. **Representative location.** The content-level location test selects
   dedup_primary = 1; explain this choice and its limitation in the report.
7. **Report cleanup.** Abstract, empty end sections, stale efficiency claims,
   placeholder RQ2 caption, and template metadata need integration/cleanup.
8. **Final package.** Add the final report and RQ2 outputs. This ZIP is a
   reviewed RQ1 handoff, not a completed submission.

Run the supplementary prose checks from the package root:

```powershell
.\.venv\Scripts\python.exe code/check_report_claims.py data/agent_skills_sample.db
```

## Preserved provenance

Original supplied CSVs and completed manual labels remain under results/rq1/.
New outputs are under out/ and figures/. Original figure snapshots remain in
report/figures/. No files were uploaded to the shared Overleaf project or sent
to group members. The source ZIPs in Downloads were not changed.

The dataset and generated parquet files are omitted from the handoff ZIP;
follow data/README.md to obtain the dataset. The large local verification files
are not needed in a submission archive.
