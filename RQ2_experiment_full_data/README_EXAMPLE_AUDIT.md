# RQ2 repetition-example audit (Phase 3)

This optional script documents a reproducible search for candidate cases in
actual GitSkills content. It is a companion to `rq2_full_analysis.py`, not a
replacement. It uses `extract_body()` from the full analysis and the corrected
`repeated_content_analysis()` from `rq2_parsing.py`.

## File layout

Place `rq2_example_audit.py` next to `rq2_full_analysis.py` and
`rq2_parsing.py`, with `tests/test_example_audit.py` in the existing `tests/`
folder. The GitSkills Parquet data must remain in the sibling `data/artifacts/`
folder. Do not add the raw 13.4 GB dataset to GitHub.

## Run

From the `RQ2_experiment_full_data/` directory:

```sh
python3 -m unittest discover -s tests -v
python3 rq2_example_audit.py
```

By default, this reproduces the three exploratory candidates initially found
in `data/artifacts/part-00000.parquet`. For another file/hash:

```sh
python3 rq2_example_audit.py --source '../data/artifacts/*.parquet' --sha YOUR_FILE_SHA
```

Outputs are written to `rq2_outputs/example_audit/`:

- `rq2_example_audit.csv`: quantitative comparison of the original exploratory
  splitter with the corrected RQ2 detector.
- `rq2_example_evidence.json`: up to five short excerpts of exact repeated
  blocks and possible near-duplicate pairs for manual review.
- `rq2_manual_review_template.csv`: reviewer/label/rationale fields. These
  fields intentionally remain unreviewed until a person inspects the examples.

## Interpretation

An exploratory candidate is NOT a verified true positive, false positive, or
false negative. The original one-off search did not remove fenced code or
leading YAML front matter. The corrected analysis does both. A repeated
paragraph may also be useful or intentional: exact textual repetition is not
proof of unnecessary instructions or achievable token savings.

Potential near-duplicate pairs are limited to the first 180 eligible paragraphs
per file and use SequenceMatcher with a threshold of 0.88 by default. This is
an exploratory candidate search, not an exhaustive measure of false negatives.

The three candidate hashes and reproducible script should be retained with
the manually adjudicated examples in the replication package.

## GitHub submission

Commit the source files, tests, small CSV/JSON evidence reports, and a short
manual classification note. Include a link to the official GitSkills dataset
release in your main README; do not upload large Parquet files or checkpoint
DuckDB databases. Check the evidence JSON for excessively long or sensitive
content before publishing it, even though the source dataset is public.
