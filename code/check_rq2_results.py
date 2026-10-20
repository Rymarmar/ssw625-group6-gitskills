"""Compare rerun RQ2 summaries with Rifat's supplied results."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
for name in ['rq2_first_analysis_summary.txt', 'rq2_token_overhead_summary.txt']:
    actual = (root / 'out/rq2' / name).read_text(encoding='utf-8').strip()
    expected = (root / 'results/rq2' / name).read_text(encoding='utf-8').strip()
    if actual != expected:
        raise SystemExit(f'MISMATCH: {name}; compare the output with the saved summary.')
    print('PASS:', name)
