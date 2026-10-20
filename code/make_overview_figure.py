import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Ellipse, Polygon
import numpy as np, sys
OUT=sys.argv[1]
plt.rcParams["font.family"]="Liberation Serif"
K="#111111"; RED="#d03a2b"; BLUE="#2b6fb0"; TEAL="#3aa0b5"
PINK="#dc9a94"; LILAC="#cdc5df"; YEL="#fbeeb0"; CELL="#a9cbe8"
W,H=100,66
fig,ax=plt.subplots(figsize=(7.0,4.62)); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis("off")
FS=6.6
def region(x,y,w,h,title,note=None,right=False):
    ax.add_patch(Rectangle((x,y),w,h,fc="none",ec=K,lw=0.9,ls=(0,(4,2.5))))
    ax.text(x+w-1.5 if right else x+1.5,y+h-1.4,title,fontsize=10,weight="bold",va="top",ha="right" if right else "left")
    if note: ax.text(x+w-1.5,y+h-2.2,note,fontsize=6.3,style="italic",va="top",ha="right")
def rbox(x,y,w,h,text,fs=FS,fc="white",rot=0,bold=True):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=0.9",fc=fc,ec=K,lw=0.9))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=fs,weight="bold" if bold else "normal",rotation=rot,linespacing=1.15)
def box(x,y,w,h,text,fs=6.3,fc="white",rot=0):
    ax.add_patch(Rectangle((x,y),w,h,fc=fc,ec=K,lw=0.9))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=fs,weight="bold",rotation=rot,linespacing=1.15)
def label(x,y,t,fs=6.6,va="top"):
    ax.text(x,y,t,ha="center",va=va,fontsize=fs,weight="bold",linespacing=1.1)
def docs(x,y,w,h,text):
    for d in (1.6,0.8,0):
        xx,yy=x+d,y-d
        ax.add_patch(Polygon([(xx,yy),(xx+w,yy),(xx+w,yy+h-1.4),(xx+w-1.4,yy+h),(xx,yy+h)],fc="white",ec=K,lw=0.8,zorder=3-d))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=7,weight="bold",linespacing=1.15,zorder=5)
def cyl(x,y,w,h,text):
    e=2.2
    ax.add_patch(Rectangle((x,y),w,h,fc="white",ec="none"))
    ax.plot([x,x],[y,y+h],color=K,lw=0.9); ax.plot([x+w,x+w],[y,y+h],color=K,lw=0.9)
    t=np.linspace(np.pi,2*np.pi,60); ax.plot(x+w/2+w/2*np.cos(t),y+e/2*np.sin(t),color=K,lw=0.9)
    ax.add_patch(Ellipse((x+w/2,y+h),w,e,fc="white",ec=K,lw=0.9))
    ax.text(x+w/2,y+h/2-0.5,text,ha="center",va="center",fontsize=FS,weight="bold",linespacing=1.15)
def arrow(pts,color=K,lw=0.9):
    xs,ys=zip(*pts); ax.plot(xs,ys,color=color,lw=lw)
    ax.annotate("",xy=pts[-1],xytext=pts[-2],arrowprops=dict(arrowstyle="-|>,head_length=0.45,head_width=0.22",color=color,lw=lw,shrinkA=0,shrinkB=0))

# ================= Data Preparation =================
region(2,36,96,28,"Data Preparation")
docs(4,44.5,9.5,9,"GitSkills\nSample")
ax.add_patch(FancyBboxPatch((17.5,40.5),13,17,boxstyle="round,pad=0,rounding_size=1",fc="white",ec=K,lw=0.9))
for i,t in enumerate(["repo / path","file_sha","front matter","body length"]):
    box(18.5,53.2-i*4.0,11,3.2,t)
label(24,39.6,"Information\nExtraction")
arrow([(15.2,49),(17.5,49)])
rbox(34,40.5,4.6,17,"Grouping by file_sha",rot=90)
arrow([(30.5,49),(34,49)])
cyl(42.5,44,10.5,9,"Content\nGroups\n(13,000)")
arrow([(38.6,49),(42.5,49)])
# per-content table (matrix look)
tx,ty,tw,th=58,42.5,15,13
ax.add_patch(FancyBboxPatch((tx,ty),tw,th,boxstyle="round,pad=0,rounding_size=1",fc="white",ec=K,lw=0.9))
cols=["sha","files","repos","loc."]; cw=(tw-2)/4
for j,c in enumerate(cols):
    ax.add_patch(Rectangle((tx+1+j*cw,ty+th-3.3),cw,2.3,fc="#e6e6e6",ec=K,lw=0.5))
    ax.text(tx+1+j*cw+cw/2,ty+th-2.15,c,fontsize=5.6,ha="center",va="center",weight="bold")
    for i in range(4):
        ax.add_patch(Rectangle((tx+1+j*cw,ty+th-3.3-(i+1)*2.1),cw,2.1,fc=CELL if (i+j)%2==0 else "white",ec=K,lw=0.4))
label(tx+tw/2,ty-1.0,"Per-content Table")
arrow([(53,49),(58,49)],color=RED)
rbox(79,43.5,16,11,"Stratified Sampling\n\n20 top reused\n20 cross-repo\n10 single-repo",fs=6.2)
arrow([(73,49),(79,49)],color=BLUE)

# ================= RQ2 =================
region(2,2,29,29.5,"RQ2: Complexity",note=None)

# ================= RQ1 =================
region(34,2,37,29.5,"RQ1: Exact Reuse",right=True)
# distribution box with bars
dx,dy,dw,dh=36,11,10.5,10
ax.add_patch(FancyBboxPatch((dx,dy),dw,dh,boxstyle="round,pad=0,rounding_size=0.9",fc="white",ec=K,lw=0.9))
for i,hh in enumerate((7,4.3,2.8,1.8,1.2)):
    ax.add_patch(Rectangle((dx+1.1+i*1.7,dy+1.2),1.3,hh,fc=CELL,ec=K,lw=0.5))
label(dx+dw/2,dy-0.9,"Reuse\nDistribution",fs=6.3)
bx=50.5; bw=12.5
rbox(bx,21,bw,4.6,"Concentration\n(top-k, Gini)",fs=6.2)
rbox(bx,13.6,bw,4.6,"Robustness\n(short files, forks)",fs=6.2)
rbox(bx,6.2,bw,4.6,"Location Test\n(chi-square, OR)",fs=6.2)
for yy in (23.3,15.9,8.5):
    arrow([(46.5,16),(48.5,16),(48.5,yy),(bx,yy)]) if yy!=15.9 else arrow([(46.5,16),(bx,16)])
box(65,6.2,4.5,19.4,"RQ1 Results",fc=PINK,rot=90)
for yy in (23.3,15.9,8.5):
    arrow([(bx+bw,yy),(65,yy)])

# ================= Manual Analysis =================
region(74,2,24,29.5,"Manual Analysis")
ax.add_patch(Rectangle((75.5,3.5),21,22.3,fc="none",ec=TEAL,lw=0.9,ls=(0,(4,2.5))))
label(84.5,25.2,"Coding of 50 groups",fs=6.3)
rbox(78.5,17.3,10.5,4.3,"Explore")
rbox(78.5,10.6,10.5,4.3,"Analyze",fc=YEL)
rbox(78.5,4.6,10.5,4.3,"Synthesize")
arrow([(83.75,17.3),(83.75,14.9)]); arrow([(83.75,10.6),(83.75,8.9)])
ax.text(90.3,12.75,"type\ntask\nchannel",fontsize=5.5,ha="left",va="center",linespacing=1.05)

# ================= cross-region flows =================
# red: per-content table -> RQ1 distribution and RQ2 relate
arrow([(65.5,40.0),(65.5,33),(41.25,33),(41.25,21)],color=RED)

ax.text(53,33.4,"reuse counts",fontsize=6.3,weight="bold",ha="center",va="bottom")
# blue: sampling -> manual analysis
arrow([(93.5,43.5),(93.5,25.8)],color=BLUE)
ax.text(92.8,33.4,"50 groups",fontsize=6.3,weight="bold",ha="right",va="center")
# manual -> RQ1 results
arrow([(78.5,6.75),(69.5,6.75)],color=BLUE)
ax.text(74,8.2,"reuse\nchannels",fontsize=5.8,weight="bold",ha="center",va="bottom",linespacing=1.0,bbox=dict(fc="white",ec="none",pad=0.4),zorder=6)
fig.subplots_adjust(0,0,1,1)
fig.savefig(OUT+".pdf"); fig.savefig(OUT+".png",dpi=220)
