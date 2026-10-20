"""Draw the Phase 2 figures. Run after: python code/rq1_reuse.py analyze"""
import duckdb, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os; OUT="figures/"; os.makedirs(OUT, exist_ok=True)
BLUE="#2a78d6"; INK="#0b0b0b"; INK2="#52514e"; GRID="#e4e3df"
plt.rcParams.update({"font.family":"DejaVu Serif","font.size":8,"axes.edgecolor":INK2,"axes.labelcolor":INK,
 "xtick.color":INK2,"ytick.color":INK2,"axes.spines.top":False,"axes.spines.right":False,"axes.linewidth":0.6})

# ---- Fig: repos-per-content distribution, two panels on the same % scale
t2=pd.read_csv("out/t2_repos_per_content.csv")
t2["pc"]=100*t2.distinct_contents/t2.distinct_contents.sum(); t2["po"]=100*t2.occurrences/t2.occurrences.sum()
fig,axs=plt.subplots(1,2,figsize=(3.4,1.9),sharey=True)
for ax,col,title in [(axs[0],"pc","(a) Distinct contents"),(axs[1],"po","(b) File occurrences")]:
    x=np.arange(len(t2)); ax.bar(x,t2[col],color=BLUE,width=0.72,zorder=2)
    for i,v in enumerate(t2[col]):
        ax.text(i,v+1.5,f"{v:.0f}" if v>=1 else "<0.1",ha="center",va="bottom",fontsize=6.5,color=INK)
    ax.set_xticks(x,t2.bucket,rotation=45,ha="right",fontsize=6.5); ax.set_title(title,fontsize=8,color=INK,pad=4)
    ax.yaxis.grid(True,color=GRID,lw=0.5,zorder=0); ax.set_ylim(0,92)
axs[0].set_ylabel("% of total"); fig.supxlabel("Number of repositories containing the content",fontsize=7,y=0.0)
fig.tight_layout(pad=0.3); fig.savefig(OUT+"rq1_repos_per_content.pdf"); fig.savefig(OUT+"rq1_repos_per_content.png",dpi=220)

# ---- Fig: concentration curve
con=duckdb.connect()
nr=con.sql("SELECT count(*) occ FROM 'data/occ.parquet' GROUP BY file_sha HAVING count(DISTINCT repo_full_name)>1 ORDER BY count(DISTINCT repo_full_name) DESC, count(*) DESC").df().occ.values
cum=100*np.cumsum(nr)/nr.sum(); k=np.arange(1,len(nr)+1)
n=len(nr); px=np.concatenate([[0],100*k/n]); py=np.concatenate([[0],cum])
fig,ax=plt.subplots(figsize=(3.4,2.1))
ax.plot([0,100],[0,100],color=INK2,lw=0.8,ls=(0,(3,2)),zorder=1)
ax.text(80,75,"equal reuse",fontsize=6.5,color=INK2,rotation=31,ha="center",va="center")
ax.plot(px,py,color=BLUE,lw=1.6,zorder=2)
ax.yaxis.grid(True,color=GRID,lw=0.5,zorder=0); ax.xaxis.grid(True,color=GRID,lw=0.5,zorder=0)
for kk,off in [(100,(6,-4)),(1000,(6,-10))]:
    x=100*kk/n; y=cum[kk-1]
    ax.plot(x,y,"o",ms=4,color=BLUE,zorder=3)
    ax.annotate(f"top {kk} ({x:.1f}%): {y:.0f}%",(x,y),xytext=off,textcoords="offset points",ha="left",va="top",fontsize=6.5,color=INK,bbox=dict(fc="white",ec="none",pad=0.5))
ax.set_xlim(0,100); ax.set_ylim(0,100)
ax.set_xlabel(f"% of reused contents (n = {n:,}), most reused first",fontsize=7)
ax.set_ylabel("Cumulative % of cross-repo\nfile occurrences",fontsize=7)
fig.tight_layout(pad=0.3); fig.savefig(OUT+"rq1_concentration.pdf"); fig.savefig(OUT+"rq1_concentration.png",dpi=220)

print("RQ1 plots written to", OUT)
