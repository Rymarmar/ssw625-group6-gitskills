# Group 6 — GitSkills Phase 3

Luke Spagnoli, Xiying Huang, Rifat Rahman Khan, Benedict Martinez.

## What this package contains

Both quantitative research questions now use the **full GitSkills dataset**:
3,797,117 file occurrences and 1,877,981 distinct contents. The manual RQ1
review remains a stratified sample of 50 contents selected from the public
13,000-content sample. It is not a manual review of the full dataset.

- **RQ1:** exact-content reuse across repositories, its distribution and placement patterns.
- **RQ2:** instruction length, headings, reference presence, token counts and exact repeated blocks.
- These are artifact measurements, not measurements of agent runtime, task success or achievable token savings.

| Material | Location |
| --- | --- |
| Full RQ1 scripts | `code/rq1_reuse.py`, `code/rq1_extra.py` |
| Full RQ1 saved outputs | `results/rq1_full/` |
| Manual codes, independent coders, agreement, disagreements and final codes | `results/rq1/manual_*.csv`, `manual_agreement.txt` |
| Full RQ2 scripts and corrected parser | `RQ2_experiment_full_data/` |
| Full RQ2 saved summaries | `RQ2_experiment_full_data/rq2_outputs/full_dataset/` |
| RQ2 manual examples and evidence | `RQ2_experiment_full_data/rq2_outputs/example_audit/` |
| Final report source and figures | `report/phase3-source/` |
| Integration verification logs and scope | `verification/` |

The files in `code/rq2/`, `results/rq2/`, the numerical tables in `results/rq1/`,
and existing `out/` files are retained **Phase 2 pilot materials**. They are not
the Phase 3 full-dataset outputs. Root review/checklist documents are historical
notes and are explicitly marked as such. Use this README for the final workflow.

## Setup (Windows PowerShell)

Open a terminal in the folder containing this README. Python 3.10 or later is
recommended. No OpenAI API key or paid model call is required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Tokenization uses `cl100k_base` locally. Its first use may download the tokenizer
vocabulary; skill contents are not sent to an LLM service.

## Quick verification without the large dataset

```powershell
.\.venv\Scripts\python.exe code/check_paper_numbers.py
.\.venv\Scripts\python.exe -m unittest discover -s RQ2_experiment_full_data/tests -v
.\.venv\Scripts\python.exe code/manual_agreement.py results/rq1/manual_coder1.csv results/rq1/manual_coder2.csv verification/manual_disagreements_recomputed.csv
```

If tests cannot import the RQ2 modules when launched from the root, run them
from their own directory instead:

```powershell
Push-Location RQ2_experiment_full_data
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
Pop-Location
```

The final integration check passed **95 RQ1 numerical consistency checks** and
**21 RQ2 tests**. `check_paper_numbers.py` compares calculations from saved RQ1
outputs with expected values encoded in that script. It does **not** read the
current manuscript or independently rerun the full dataset. Test success does
not establish that manual judgments are correct. The final integration did not
repeat either complete full-data analysis; the supplied full-run summaries are
the authors' saved results. See `verification/README.md` for the exact scope.

## Obtain the data

Full dataset: https://huggingface.co/datasets/mvaccargiu/gitskills

Public sample for manual selection and the Phase 2 pilot:
https://github.com/giuseppedestefanis/gitskills-sample

Download `agent_skills_sample.zip` from the sample repository and extract the
SQLite database to `data/agent_skills_sample.db` for the manual-selection workflow.
The quantitative Phase 3 analyses require **all** artifact Parquet parts, not
this sample database. Raw data and local checkpoints are omitted from GitHub.

The download script uses the dataset's `refs/convert/parquet` revision. That
reference may change; the saved results represent the dataset used by the
authors. Preserve the downloaded source files when reproducing this snapshot.

## Reproduce full RQ1

Run these from the project root. The fetch step downloads raw Parquet files
under `hf_raw/`, then writes the selected occurrence columns to `data/occ.parquet`
and repository data to `data/repos.parquet`. It can use a Hugging Face token
through `HF_TOKEN` if access requires one; never commit a token.

```powershell
.\.venv\Scripts\python.exe code/rq1_reuse.py fetch
.\.venv\Scripts\python.exe code/rq1_reuse.py analyze
.\.venv\Scripts\python.exe code/rq1_extra.py data/occ.parquet
.\.venv\Scripts\python.exe code/check_saved_results.py full
```

Fresh RQ1 results go to `out/`; saved full results remain in `results/rq1_full/`.
Do not run sample extraction between full extraction and analysis: both use
the same working filenames. The optional full-data Colab notebook is
`code/rq1_full_colab.ipynb`.

| RQ1 saved output | Meaning |
| --- | --- |
| `t1_overview.csv` | File/content counts and reuse percentages |
| `t2_repos_per_content.csv` | Repository coverage distribution |
| `t3_concentration.csv` | Top-k concentration |
| `t4_top50_reused.csv` | Most widely reused contents |
| `t5_nonfork.csv` | Non-fork robustness comparison |
| `t6_by_location.csv`, `t7_location_test.csv` | Placement classes, effect sizes and tests |
| `t8_concentration_curve.csv` | Cumulative concentration curve |
| `extra.txt` | Gini, path-pattern shares and within-repository duplication |

The full saved run predates `t0_exact_counts.csv`, `t9_top_percent_share.csv`
and `t7`'s `n_cross_repo` column. A fresh run also writes those. The comparison
script skips unsaved files and compares common columns; the paper-number
checker uses the saved concentration curve for top-percent shares.

To regenerate the distribution plots:

```powershell
.\.venv\Scripts\python.exe code/make_figures.py results/rq1_full figures
```

The authoritative final overview and both white-box diagrams are supplied in
`report/phase3-source/Images/`. Figure numbers are assigned by LaTeX, not by the
filenames. The old diagram generator is retained for provenance.

## Reproduce full RQ2

RQ2 needs the raw artifact Parquet files **including content**. The selected
`data/occ.parquet` used by RQ1 does not contain everything RQ2 needs.
After RQ1's fetch, place copies of all raw artifact parts in `data/artifacts/`:

```powershell
New-Item -ItemType Directory -Force data/artifacts
Copy-Item hf_raw/artifacts/train/*.parquet data/artifacts/
Push-Location RQ2_experiment_full_data
..\.venv\Scripts\python.exe rq2_full_analysis.py
Pop-Location
```

Copying requires additional disk space for the raw files. Alternatively, place
an existing complete download directly in `data/artifacts/`. The full dataset
is large; do not start a full rerun just to perform the quick verification above.

RQ2 processes Parquet parts in batches with resumable checkpoints under
`RQ2_experiment_full_data/rq2_outputs/full_dataset/_work/`. Summary reports are
finalized only after all parts are processed. `--max-parts 1` is a staged check,
**not** a full result. Rerun the same command to resume. Preserve checkpoints
unless the program reports an incompatible input/code fingerprint.

The three supplied full reports are `rq2_first_analysis_summary.txt`,
`rq2_token_overhead_summary.txt`, and `rq2_quality_check.txt`.
They report 1,571,893 single-repository and 306,088 reused contents; median
tokens 1,206 and 1,257; and an overall repeated-token share of about 0.08%.

For the four manually reviewed examples, see `rq2_manual_review_completed.csv`
and the evidence files in `rq2_outputs/example_audit/`. The exploratory false
positive is not a false positive of the corrected detector. The false-negative
example uses a broader repeated-list criterion than exact paragraph matching.
See `README_EXAMPLE_AUDIT.md` for the optional search commands.

## Reproduce the manual RQ1 selection

```powershell
.\.venv\Scripts\python.exe code/make_coding_sheet.py data/agent_skills_sample.db verification/rq1_coding_sheet.xlsx
```

Selection uses seed 625: 20 most reused contents, 20 other reused contents and
10 single-repository contents. The generated workbook reads the final codebook
from `results/rq1/manual_codebook.csv`. Labels describe observed **placement
patterns**, not verified copying direction or adoption provenance. The historical
label `independent adoption` means copies in unrelated ordinary projects without
another observed placement pattern; it does not prove independent adoption.

## Report and assistance

Compile `report/phase3-source/main.tex` in Overleaf with its accompanying files.
Upload the final compiled PDF to the course submission together with the
replication materials as permitted by Canvas. The manuscript acknowledges
ChatGPT, Claude and Codex assistance. Authors remain responsible for the work.
