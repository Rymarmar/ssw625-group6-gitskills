"""Compare a fresh RQ1 run (out/) with the saved tables and summarize manual labels.

Usage: python code/check_saved_results.py            # after a run on the public sample
       python code/check_saved_results.py full       # after a run on the full dataset
"""
import sys
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parents[1]
sorts = {
    't1_overview.csv': ['label'],
    't2_repos_per_content.csv': ['bucket'],
    't3_concentration.csv': ['top_k'],
    't4_top50_reused.csv': ['file_sha'],
    't5_nonfork.csv': ['label'],
    't6_by_location.csv': ['location_class'],
    't7_location_test.csv': ['unit', 'location_class'],
    't0_exact_counts.csv': ['label'],
    't8_concentration_curve.csv': ['k'],
    't9_top_percent_share.csv': ['top_pct_of_reused_contents'],
}
saved = root / ('results/rq1_full' if sys.argv[1:] == ['full'] else 'results/rq1')
for name, keys in sorts.items():
    if not (saved / name).exists():
        print('SKIP (not saved from the earlier run):', name)
        continue
    actual = pd.read_csv(root / 'out' / name).sort_values(keys).reset_index(drop=True)
    expected = pd.read_csv(saved / name)
    expected = expected.sort_values(keys).reset_index(drop=True)
    pd.testing.assert_frame_equal(actual[expected.columns], expected, check_dtype=False, rtol=1e-10, atol=1e-200)
    print('PASS:', name)
manual = pd.read_csv(root / 'results/rq1/manual_coding.csv').fillna('')
assert len(manual) == 50 and manual.file_sha.nunique() == 50
print('PASS: 50 manually coded, distinct content hashes')
for field in ['skill_type', 'placement_pattern']:
    print('\nManual counts:', field)
    print(pd.crosstab(manual.group, manual[field]).to_string())
print('\nThese checks validate reproduction and label counts, not the accuracy of human judgments.')
