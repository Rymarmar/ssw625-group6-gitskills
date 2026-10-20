"""Supplementary checks of prose claims, using the supplied public sample."""
import json
from pathlib import Path
import sqlite3
import sys
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
db = Path(sys.argv[1]).resolve()
if not db.is_file():
    raise SystemExit(f'Database not found: {db}')
with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as con:
    occ = pd.read_sql('SELECT file_sha, repo_full_name, path FROM artifacts', con)
groups = occ.groupby('file_sha').agg(occurrences=('path', 'size'), n_repos=('repo_full_name', 'nunique'))
x = np.sort(groups.n_repos.to_numpy())
n = len(x)
gini = float(2 * np.sum(np.arange(1, n + 1) * x) / (n * x.sum()) - (n + 1) / n)
within = groups[(groups.occurrences > 1) & (groups.n_repos == 1)].index
rows = occ[occ.file_sha.isin(within)].copy()
rows['top_level_component'] = rows.path.str.split('/').str[0]
multiple = rows.groupby('file_sha').top_level_component.nunique() > 1
result = {
    'gini_population': 'repository counts of all distinct contents, including single-repository contents',
    'distinct_contents': n,
    'gini_repositories_per_content': gini,
    'gini_rounded_two_decimals': round(gini, 2),
    'within_repository_only_contents': len(within),
    'within_contents_multiple_top_level_components': int(multiple.sum()),
    'pct_within_contents_multiple_top_level_components': float(100 * multiple.mean()),
    'interpretation': 'Multiple top-level path components do not by themselves establish multi-agent installation.'
}
(root / 'out').mkdir(exist_ok=True)
(root / 'out/report_claim_checks.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
