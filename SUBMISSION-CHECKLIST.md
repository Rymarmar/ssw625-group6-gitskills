# Group 6 — what remains before submission

## 1. Export the CURRENT Overleaf project

Rifat says he updated sections 5.5 and 6.2. The available earlier source ZIP
predates those changes. Download both the current compiled PDF and the current
source ZIP for a final check. Do not restore the older main.tex over the live one.

## 2. Check that the report describes the implemented RQ2

Both supplied RQ2 scripts ran against the public sample and reproduced their
saved summaries. The code compares single-repository and cross-repository
contents, then examines token counts and within-file repeated paragraphs.
It does not run an AI agent or directly test whether structure predicts tokens.
If the final question asks about a predictive relationship, narrow the wording
to the descriptive comparisons actually performed or supply that additional
analysis; do not silently overstate what the two scripts establish.

Results to check against section 6.2:

| Measure | Single repository | Cross-repository |
|---|---:|---:|
| Distinct contents | 10,146 | 2,854 |
| Median body characters (printed rounding) | 4,455 | 4,649 |
| Median heading count | 10 | 12 |
| With reference files | 24.9% | 18.6% |
| Median instruction tokens (printed rounding) | 1,177 | 1,180 |
| More than 5,000 tokens | 5.9% | 5.4% |
| With repeated blocks | 0.8% | 0.8% |
| Repeated-block token share | 0.07% | 0.10% |

Overall: 13,000 contents; median tokens 1,177; 5.8% exceed 5,000 tokens;
0.8% contain detected repeated blocks; 311 repeated blocks containing 17,851
tokens; repeated-block token share 0.08%.

These are descriptive statistics. Similar displayed medians do not prove
statistical equivalence; repetition detection does not identify all semantic
redundancy; repeated text is not necessarily unnecessary. The 5,000-token
cutoff is a chosen descriptive threshold, not an agent or model capacity limit.

## 3. Integrate the report

- Match the introduction's closing framing, related-work transition, problem
  statement, and proposed solution to the FINAL RQ2 and implemented methods.
- Fill the overview's RQ2 branch: representative text -> structure/token/block
  measurements -> compare reuse groups -> descriptive results. Use the actual
  methods and update its caption; the supplied old caption says complexity
  relates to reuse and its box is empty.
- Replace abstract xxx only after reviewing both complete findings sections.
- Finish or remove empty optional headings, as appropriate to the course template.
- Check the Study Design (1–2 pages) and Experiments (2–6 pages) guidance.
- Resolve errors/unresolved references and remove stale publication metadata.

## 4. Resolve the RQ1 audit points

- Check the reported Gini with Xiying: all-content repository-count Gini is
  0.4047502308053712 (0.405 at three decimals, 0.40 at two).
- Obtain/document the exact query for the collection/mirror 15.2% vs 5.0%
  statement, or omit that unsupported-in-package statistic if not recoverable.
- Say 78% occur in only one repository in this sample, not "never reused."
- Say 24 of 40 manually coded cross-repository contents were labeled
  collection/mirror, not that this is the share of all copies.
- Explain content-level location uses the designated representative.
- Reconcile group C hosting categories with the manual codebook's n/a guidance.

## 5. Package and submit

The combined code ZIP contains both analyses, original result snapshots, fresh
verification outputs, dependencies, and README. It intentionally excludes the
large downloadable database. Add the final report after checking it.

Use the instructor's actual Canvas submission instructions for accepted file
types and number of uploads. The screenshot explicitly requires scripts and a
README, preferably on GitHub. Do not submit only the paper PDF. If Canvas accepts
multiple files, provide the final PDF plus the code ZIP (or the permitted repo
link). If a single archive is required, include both in that archive.

One group member should confirm the correct final files were uploaded and that
Canvas shows a submission receipt. No submission or upload has been performed
as part of this review.
