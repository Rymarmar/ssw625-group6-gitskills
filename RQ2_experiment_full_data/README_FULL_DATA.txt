SSW 625 - Phase 3 - Research Question 2 (FULL GitSkills dataset)

This is a NEW folder. It does not overwrite or depend on the Phase 2 sample
scripts, notebooks, results, or regression-validation database.

Expected Mac folder layout:

ssw625_project/
  data/
    artifacts/
      part-00000.parquet
      ... (all downloaded artifact Parquet parts)
    repos/
      ...
  gitskills-sample/
    agent_skills_sample.db
  RQ2_experiment/              [original sample analysis, keep as-is]
  RQ2_experiment_full_data/    [this folder]
    rq2_full_analysis.py
    rq2_parsing.py
    tests/
      test_parsing.py
      test_full_analysis.py

The dataset path is resolved relative to rq2_full_analysis.py:
  PROJECT_ROOT / "data" / "artifacts"
You do not need to move the downloaded Parquet files.
For RQ2, the artifacts data already contains repository names and has_references;
no join to the repos table is needed for these specific measurements.

Prerequisites (in your existing Python p310 environment):
  python3 -m pip install duckdb tiktoken

From RQ2_experiment_full_data:
  python3 -m unittest discover -s tests -v

Optional staged run (builds full-dataset reuse counts; tokenizes only one
Parquet part). This is not a full-dataset result:
  python3 rq2_full_analysis.py --max-parts 1

Full run (resumes completed parts without re-tokenizing them):
  python3 rq2_full_analysis.py

If your Mac has limited RAM, the default DuckDB limit is 2GB and threads=2.
The program processes one Parquet part at a time and fetches rows in batches.
On-disk DuckDB temporary files and compressed intermediate CSVs may use
additional disk space. Keep free space available.

Outputs appear after ALL parts have completed:
  rq2_outputs/full_dataset/rq2_first_analysis_summary.txt
  rq2_outputs/full_dataset/rq2_token_overhead_summary.txt
  rq2_outputs/full_dataset/rq2_quality_check.txt

Checkpoint data stays under:
  rq2_outputs/full_dataset/_work/

If the program is interrupted, run the same command again. Completed part
checkpoints are reused; any incomplete .partial shard is reprocessed.

The program detects when the source Parquet files or code change. If it reports
an incompatible checkpoint fingerprint, rename the _work directory to preserve
it, then rerun. Do not remove or modify the original data/ directory.

Methodology:
  * Group by exact file_sha to get distinct repository counts.
  * Use dedup_primary representative of each distinct content.
  * Mark reused if content appears in 2+ different repositories.
  * Measure body_chars, Markdown heading counts, and has_references.
  * Measure tokens with cl100k_base, stripping leading YAML front matter.
  * Detect repeated blocks after CRLF/CR normalization and correct fence logic.
  * Use the Phase 2 thresholds: >=80 normalized characters and >=10 words.
  * Count only repetitions AFTER the first occurrence of each block.

The sample baseline has 13,000 contents. Full GitSkills is much larger;
measurements may differ. The code will not write a full-data report until
all Parquet parts are complete and the number of primary rows equals the number
of distinct content hashes in the reuse-count table.

Limitations: The reports measure artifact content, not whether AI agents loaded
or executed the instructions; repetition is a heuristic, not token savings.

Only the Python scripts, tests, requirements, and this README are included.
No .ipynb files, dataset copies, or misleading precomputed full-data results.
