"""Check every RQ1 number in the report against the saved result files.

Usage (from the repository root):
    python code/check_paper_numbers.py

Each check takes a number exactly as it is printed in the report and recomputes it
from results/rq1_full/ (full dataset), results/rq1/ (public sample and manual
analysis). Rounding is half-up. A value is BORDERLINE when the saved file does not
keep enough decimals to decide the last printed digit (for example 60.65 -> 60.6 or
60.7); re-running code/rq1_reuse.py writes exact counts (t0, t7 n_cross_repo, t9)
that settle it.
"""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import re
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "results" / "rq1_full"
SAMPLE = ROOT / "results" / "rq1"

results = []


def fmt(x, places, thousands=False):
    q = Decimal(1).scaleb(-places)
    d = Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP)
    return f"{d:,}" if thousands else str(d)


def borderline(stored, places):
    """True if `stored` (a value already rounded in a CSV) ends exactly on a 5 just
    past the printed digit, so its true value could round either way."""
    s = repr(float(stored))
    if "e" in s or "." not in s:
        return False
    frac = s.split(".")[1].rstrip("0")
    return len(frac) == places + 1 and frac[-1] == "5"


def check(where, printed, value, places=1, stored=False, thousands=False):
    """printed: the text in the report; value: the recomputed number.
    stored=True means `value` was read from a CSV that already rounded it."""
    expected = fmt(value, places, thousands)
    if stored and borderline(value, places):
        status = "BORDERLINE"
    else:
        status = "PASS" if printed == expected else "FAIL"
    results.append((status, where, printed, expected, value))


def pct(a, b):
    return 100 * Decimal(int(a)) / Decimal(int(b))


# ---------------- full dataset ----------------
t1 = pd.read_csv(FULL / "t1_overview.csv").set_index("label")
t2 = pd.read_csv(FULL / "t2_repos_per_content.csv").set_index("bucket")
t3 = pd.read_csv(FULL / "t3_concentration.csv").set_index("top_k")
t4 = pd.read_csv(FULL / "t4_top50_reused.csv")
t5 = pd.read_csv(FULL / "t5_nonfork.csv")
t7 = pd.read_csv(FULL / "t7_location_test.csv").set_index(["unit", "location_class"])
t8 = pd.read_csv(FULL / "t8_concentration_curve.csv")
extra = (FULL / "extra.txt").read_text()

a, b = t1.loc["all"], t1.loc["body_chars>=100"]
N_OCC, N_CON = int(a.occurrences), int(a.distinct_contents)
REUSED = int(a.contents_in_2plus_repos)

# Abstract, Section 5.1, Table 2
check("Table 2 / abstract: file occurrences", "3,797,117", N_OCC, 0, thousands=True)
check("Table 2 / abstract: distinct contents", "1,877,981", N_CON, 0, thousands=True)
check("Table 2: contents in >=2 repositories", "306,088", REUSED, 0, thousands=True)
check("Table 2: % duplicated", "60.77", a.pct_occ_duplicated, 2, stored=True)
check("Table 2: % cross-repository", "54.91", a.pct_occ_cross_repo, 2, stored=True)
check("Abstract / Results: 54.9% cross-repository", "54.9", a.pct_occ_cross_repo, 1, stored=True)
check("Results: 60.8% share their content", "60.8", a.pct_occ_duplicated, 1, stored=True)
check("Table 2: % within-repository only", "5.86", a.pct_occ_within_repo_only, 2, stored=True)
check("Results: 5.9% within a single repository", "5.9", a.pct_occ_within_repo_only, 1, stored=True)
check("Table 2 (body>=100): occurrences", "3,745,469", b.occurrences, 0, thousands=True)
check("Table 2 (body>=100): distinct contents", "1,858,036", b.distinct_contents, 0, thousands=True)
check("Table 2 (body>=100): contents in >=2 repos", "303,013", b.contents_in_2plus_repos, 0, thousands=True)
check("Table 2 (body>=100): % duplicated", "60.65", b.pct_occ_duplicated, 2, stored=True)
check("Table 2 (body>=100): % cross-repository", "54.87", b.pct_occ_cross_repo, 2, stored=True)
check("Table 2 (body>=100): % within-repository only", "5.78", b.pct_occ_within_repo_only, 2, stored=True)

# Results text
check("Summary: about 61% are exact copies", "61", a.pct_occ_duplicated, 0, stored=True)
check("Results: GitSkills-style duplication 50.5%", "50.5", pct(N_OCC - N_CON, N_OCC))
one = t2.loc["1"]
check("Results: single-repo contents 83.7%", "83.7", pct(one.distinct_contents, N_CON))
check("Summary: 84% of contents in one repository", "84", pct(one.distinct_contents, N_CON), 0)
check("Results / overview figure: 1,571,893 single-repo contents", "1,571,893",
      one.distinct_contents, 0, thousands=True)
check("Overview figure: 306,088 reused contents", "306,088", N_CON - int(one.distinct_contents), 0, thousands=True)
over10 = t2.loc[["11-100", "101-1000"] + ([">1000"] if ">1000" in t2.index else [])]
check("Results: 23,475 contents in >10 repos", "23,475", over10.distinct_contents.sum(), 0, thousands=True)
check("Results: 1.3% of contents in >10 repos", "1.3", pct(over10.distinct_contents.sum(), N_CON))
check("Results: single-repo contents hold 45.1% of files", "45.1", pct(one.occurrences, N_OCC))
check("Results: >10-repo contents hold 26.8% of files", "26.8", pct(over10.occurrences.sum(), N_OCC))
gini = float(re.search(r"Gini[^:]*:\s*([0-9.]+)", extra).group(1))
check("Results: Gini 0.38", "0.38", gini, 2)
k1 = -(-REUSED // 100)
check("Results: top 1% is about 3,000 contents", "3,000", round(k1, -3), 0, thousands=True)
t9 = FULL / "t9_top_percent_share.csv"
if t9.exists():
    t9 = pd.read_csv(t9).set_index("top_pct_of_reused_contents").pct_of_cross_repo_occ
    top1, top10 = t9.loc[1], t9.loc[10]
else:  # older run without t9: the curve has a point within 1-2 contents of each cut
    pick = lambda k: t8.iloc[(t8.k - k).abs().idxmin()].cum_pct
    top1, top10 = pick(k1), pick(-(-REUSED * 10 // 100))
check("Results: top 1% hold 18.1% of cross-repo occurrences", "18.1", top1)
check("Results: top 10% hold 52.9%", "52.9", top10)
check("Figure 3 label: top 1%: 18%", "18", top1, 0)
check("Figure 3 label: top 10%: 53%", "53", top10, 0)
check("Results: top 100 hold 2.1%", "2.1", t3.loc[100].pct_of_cross_repo_occ, 1, stored=True)
for name, n in [("frontend-design", "951"), ("verification-before-completion", "914"),
                ("webapp-testing", "781"), ("pdf", "661"), ("systematic-debugging", "656")]:
    check(f"Results: {name} repositories", n, t4[t4.name == name].n_repos.max(), 0)
m = re.search(r"top 100 contents\s+([0-9.]+).*?all files\s+([0-9.]+)", extra, re.S)
check("Results: top-100 collection/mirror share 3.4%", "3.4", float(m.group(1)), 1, stored=True)
check("Results: all-file collection/mirror share 5.4%", "5.4", float(m.group(2)), 1, stored=True)
check("Robustness: 54.9% after removing short contents", "54.9", b.pct_occ_cross_repo, 1, stored=True)
check("Robustness: 54.8% after removing forks", "54.8", t5.pct_occ_cross_repo.iloc[0], 1, stored=True)
m = re.search(r"within_repo_contents\s+pct_multiple_top_folders\s+(\d+)\s+([0-9.]+)", extra)
check("Results: 82,413 within-repo-only contents", "82,413", int(m.group(1)), 0, thousands=True)
check("Results: 67.2% span top-level folders", "67.2", float(m.group(2)), 1, stored=True)
check("Step 3: 19,945 short contents (full)", "19,945",
      N_CON - int(b.distinct_contents), 0, thousands=True)

# Location (text and Table 3)
for unit, label in [("file occurrences", "Files"), ("distinct contents", "Contents")]:
    for loc in ["canonical", "skills-dir", "other"]:
        r = t7.loc[(unit, loc)]
        printed = {("Files", "canonical"): ("373,652", "42.8", "0.559 [0.555, 0.563]"),
                   ("Files", "skills-dir"): ("2,102,053", "55.6", "0.938 [0.934, 0.942]"),
                   ("Files", "other"): ("1,321,412", "57.2", None),
                   ("Contents", "canonical"): ("273,721", "23.5", "2.423 [2.394, 2.453]"),
                   ("Contents", "skills-dir"): ("1,037,938", "17.1", "1.629 [1.614, 1.645]"),
                   ("Contents", "other"): ("566,322", "11.3", None)}[(label, loc)]
        check(f"Table 3 {label} {loc}: n", printed[0], r.n, 0, thousands=True)
        if "n_cross_repo" in r.index:
            check(f"Table 3 {label} {loc}: % cross-repo", printed[1], pct(r.n_cross_repo, r.n))
        else:
            check(f"Table 3 {label} {loc}: % cross-repo", printed[1], r.pct_cross_repo, 1, stored=True)
        if printed[2]:
            o, lo, hi = re.match(r"([0-9.]+) \[([0-9.]+), ([0-9.]+)\]", printed[2]).groups()
            check(f"Table 3 {label} {loc}: OR", o, r.odds_ratio_vs_other, 3, stored=True)
            check(f"Table 3 {label} {loc}: CI low", lo, r.or_ci95_low, 3, stored=True)
            check(f"Table 3 {label} {loc}: CI high", hi, r.or_ci95_high, 3, stored=True)
    or_text = {"Files": "0.56", "Contents": "2.42"}[label]
    check(f"Results: OR = {or_text} ({label})", or_text, t7.loc[(unit, "canonical")].odds_ratio_vs_other, 2, stored=True)
    first = t7.loc[unit].iloc[0]
    chi, v = {"Files": ("25,503", "0.08"), "Contents": ("21,538", "0.11")}[label]
    check(f"Results: chi-square ({label})", chi, first.chi2, 0, stored=True, thousands=True)
    check(f"Results: Cramer's V ({label})", v, first.cramers_v, 2, stored=True)
    results.append(("PASS" if first.p_value < 0.001 else "FAIL", f"Results: p < 0.001 ({label})",
                    "p < 0.001", f"p = {first.p_value:.3g}", first.p_value))

# ---------------- public sample (pilot) ----------------
s1 = pd.read_csv(SAMPLE / "t1_overview.csv").set_index("label")
s3 = pd.read_csv(SAMPLE / "t3_concentration.csv").set_index("top_k")
check("Section 5.1: sample has 13,000 contents", "13,000", s1.loc["all"].distinct_contents, 0, thousands=True)
check("Results: sample has 2,854 reused contents", "2,854", s1.loc["all"].contents_in_2plus_repos, 0, thousands=True)
check("Results: sample top 100 held 30.7%", "30.7", s3.loc[100].pct_of_cross_repo_occ, 1, stored=True)
check("Step 3: 145 short contents (sample)", "145",
      s1.loc["all"].distinct_contents - s1.loc["body_chars>=100"].distinct_contents, 0)

# ---------------- manual analysis ----------------
fin = pd.read_csv(SAMPLE / "manual_final.csv")
g = fin.group.str[0]
ct = lambda q, code, grp: int(((fin[q] == code) & (g == grp)).sum())
table1 = {("Q1", "general"): "19 17 5", ("Q1", "project-specific"): "1 3 5",
          ("Q3", "collection/mirror"): "12 13 3", ("Q3", "independent adoption"): "5 2 0",
          ("Q3", "multi-agent install"): "2 2 0", ("Q3", "template/scaffold"): "1 1 4",
          ("Q3", "same-owner copy"): "0 2 0"}
for (q, code), printed in table1.items():
    got = " ".join(str(ct(q, code, x)) for x in "ABC")
    results.append(("PASS" if got == printed else "FAIL", f"Table 1: {code} (A B C)", printed, got, got))
none_c = int((fin[q].isna() & (g == "C")).sum())
results.append(("PASS" if none_c == 3 else "FAIL", "Table 1: none recorded (C)", "3", str(none_c), none_c))
ab = g.isin(["A", "B"])
check("Synthesize: 19 of the 20 most reused are general", "19", ct("Q1", "general", "A"), 0)
check("Synthesize: 5 of the 10 single-repo are project-specific", "5", ct("Q1", "project-specific", "C"), 0)
check("Synthesize: 25 collection/mirror in A+B", "25", int((ab & (fin.Q3 == "collection/mirror")).sum()), 0)
check("Synthesize: seven independent adoption in A+B", "7", int((ab & (fin.Q3 == "independent adoption")).sum()), 0)
agree = (SAMPLE / "manual_agreement.txt").read_text()
for q, printed in [("Q1", "0.62"), ("Q2", "0.91"), ("Q3", "0.62")]:
    k = float(re.search(rf"{q}\s+all 50\s+50\s+[0-9.]+\s+([0-9.]+)", agree).group(1))
    check(f"Table 1 caption: kappa {q}", printed, k, 2, stored=True)

# ---------------- report ----------------
width = max(len(r[1]) for r in results)
for status, where, printed, expected, _ in results:
    mark = "" if status == "PASS" else f"   (recomputed: {expected})"
    print(f"{status:<10} {where:<{width}}  report: {printed}{mark}")
n_fail = sum(r[0] == "FAIL" for r in results)
n_border = sum(r[0] == "BORDERLINE" for r in results)
print(f"\n{len(results)} checks: {len(results) - n_fail - n_border} pass, {n_fail} fail, {n_border} borderline")
sys.exit(1 if n_fail else 0)
