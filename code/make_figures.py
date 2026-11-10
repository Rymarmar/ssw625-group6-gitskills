"""Draw the RQ1 figures from the CSV outputs.
Run after: python code/rq1_reuse.py analyze  (writes out/t2_... and out/t8_...)
Usage: python code/make_figures.py [results_dir] [figures_dir]"""
import os, sys
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = sys.argv[1] if len(sys.argv) > 1 else "out"
OUT = sys.argv[2] if len(sys.argv) > 2 else "figures"
os.makedirs(OUT, exist_ok=True)
BLUE = "#2a78d6"; INK = "#0b0b0b"; INK2 = "#52514e"; GRID = "#e4e3df"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"], "font.size": 8, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6})
LBL = dict(ha="center", va="bottom", fontsize=6.5, color=INK, bbox=dict(fc="white", ec="none", pad=0.5))

# ---- Figure 2: repositories per content, as % of contents and % of file occurrences
t2 = pd.read_csv(f"{RES}/t2_repos_per_content.csv")
t2["pc"] = 100 * t2.distinct_contents / t2.distinct_contents.sum()
t2["po"] = 100 * t2.occurrences / t2.occurrences.sum()
fig, axs = plt.subplots(1, 2, figsize=(3.4, 1.9), sharey=True)
for ax, col, title in [(axs[0], "pc", "(a) Distinct contents"), (axs[1], "po", "(b) File occurrences")]:
    x = np.arange(len(t2)); ax.bar(x, t2[col], color=BLUE, width=0.72, zorder=2)
    for i, v in enumerate(t2[col]):
        ax.text(i, v + 1.5, f"{v:.0f}" if v >= 0.5 else "<1" if v >= 0.05 else "<0.1", **LBL)
    ax.set_xticks(x, t2.bucket, rotation=45, ha="right", fontsize=6.5)
    ax.set_title(title, fontsize=8, color=INK, pad=4)
    ax.yaxis.grid(True, color=GRID, lw=0.5, zorder=0); ax.set_ylim(0, 98)
axs[0].set_ylabel("% of total")
fig.supxlabel("Number of repositories containing the content", fontsize=7, y=0.0)
fig.tight_layout(pad=0.3)
fig.savefig(f"{OUT}/rq1_repos_per_content.pdf"); fig.savefig(f"{OUT}/rq1_repos_per_content.png", dpi=220)

# ---- Figure 3: concentration curve of cross-repository reuse
t8 = pd.read_csv(f"{RES}/t8_concentration_curve.csv")
n = int(t8.k.max())
px = np.concatenate([[0], t8.pct_contents]); py = np.concatenate([[0], t8.cum_pct])
fig, ax = plt.subplots(figsize=(3.4, 2.1))
ax.plot([0, 100], [0, 100], color=INK2, lw=0.8, ls=(0, (3, 2)), zorder=1)
ax.text(80, 75, "equal reuse", fontsize=6.5, color=INK2, rotation=31, ha="center", va="center")
ax.plot(px, py, color=BLUE, lw=1.6, zorder=2)
ax.yaxis.grid(True, color=GRID, lw=0.5, zorder=0); ax.xaxis.grid(True, color=GRID, lw=0.5, zorder=0)
for p, off in [(1, (6, 2)), (10, (6, -4))]:
    y = float(np.interp(p, t8.pct_contents, t8.cum_pct))
    ax.plot(p, y, "o", ms=4, color=BLUE, zorder=3)
    ax.annotate(f"top {p}%: {y:.0f}%", (p, y), xytext=off, textcoords="offset points",
                ha="left", va="top", fontsize=6.5, color=INK, bbox=dict(fc="white", ec="none", pad=0.5))
ax.set_xlim(0, 100); ax.set_ylim(0, 100)
ax.set_xlabel(f"% of reused contents (n = {n:,}), most reused first", fontsize=7)
ax.set_ylabel("Cumulative % of cross-repo\nfile occurrences", fontsize=7)
fig.tight_layout(pad=0.3)
fig.savefig(f"{OUT}/rq1_concentration.pdf"); fig.savefig(f"{OUT}/rq1_concentration.png", dpi=220)
print("Figures written to", OUT)
