"""Inter-coder agreement for the RQ1 manual analysis (50 contents).
Compares coder 1 and coder 2 on Q1 skill type, Q2 task category and
Q3 placement pattern, prints percent agreement and Cohen's kappa, and
writes a disagreement sheet for adjudication.
Usage: python code/manual_agreement.py coder1.csv coder2.csv out/manual_disagreements.csv
Each CSV needs the columns: id, group, Q1, Q2, Q3."""
import sys
from collections import Counter
import pandas as pd

ALIASES = {"specific": "project-specific"}


def kappa(x, y):
    n = len(x)
    po = sum(a == b for a, b in zip(x, y)) / n
    cx, cy = Counter(x), Counter(y)
    pe = sum(cx[k] * cy[k] for k in set(cx) | set(cy)) / n / n
    return po, (po - pe) / (1 - pe)


c1, c2, out = sys.argv[1:4]
a = pd.read_csv(c1).set_index("id"); b = pd.read_csv(c2).set_index("id")
for q in ("Q1", "Q2", "Q3"):
    for df in (a, b):
        df[q] = df[q].fillna("").str.strip().replace(ALIASES)
rows = []
for q in ("Q1", "Q2", "Q3"):
    for label, ids in (("all 50", a.index), ("groups A+B", a.index[a.group.str[0].isin(["A", "B"])])):
        po, k = kappa(list(a.loc[ids, q]), list(b.loc[ids, q]))
        rows.append((q, label, len(ids), round(100 * po, 1), round(k, 2)))
print(pd.DataFrame(rows, columns=["question", "subset", "n", "pct_agree", "cohen_kappa"]).to_string(index=False))
dis = a.join(b, lsuffix="_coder1", rsuffix="_coder2")
mask = (dis.Q1_coder1 != dis.Q1_coder2) | (dis.Q2_coder1 != dis.Q2_coder2) | (dis.Q3_coder1 != dis.Q3_coder2)
dis[mask].to_csv(out)
print(f"{mask.sum()} contents with at least one disagreement -> {out}")
