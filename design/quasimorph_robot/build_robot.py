"""RealWare combat robot - head-on, combat guard, gritty lit pixel art.
Forms are modelled as simple 3D primitives (capsules, spheres, beveled plates), lit by one light
from the upper-left, then quantised to a small palette with a black silhouette outline.
usage: python3 build_robot.py <out dir>"""
import sys, math
import numpy as np
from PIL import Image, ImageDraw
OUT=sys.argv[1].rstrip('/')+'/'
W,H=84,108
def hx(s): return tuple(int(s[i:i+2],16) for i in (0,2,4))
ARMOR=[hx(c) for c in '161313 211c1c 2c2626 383131 443c3c 524848 625757 766a67 8f8380 ad a19d'.replace('ad a19d','ada19d').split()]
ARMOR+= [hx('cdc3bd'),hx('e6ded8')]
METAL=[hx(c) for c in '0c0a0b 151214 1e1a1c 29242a 363038 4a4250 6a6272'.split()]
RED=[hx(c) for c in '2a0805 4a0e07 701508 a01c0b e02a11 ff6a45'.split()]
BLACK=(0,0,0)

depth=np.full((H,W),-1e9); normal=np.zeros((H,W,3)); mat=np.zeros((H,W),dtype=int)-1
pid=np.zeros((H,W),dtype=int)-1; paint=np.zeros((H,W),dtype=int)   # paint: 0 none, 1 groove, 2 lip, 3 logo, 4 eye
_pid=[0]
def put(x,y,z,n,m,p=None):
    if 0<=x<W and 0<=y<H and z>depth[y,x]:
        depth[y,x]=z; normal[y,x]=n; mat[y,x]=m; pid[y,x]=_pid[0] if p is None else p; paint[y,x]=0
def nid(): _pid[0]+=1

def capsule(P,D,r0,r1,z0,z1,m=0):
    nid(); (px,py),(dx,dy)=P,D; L2=(dx-px)**2+(dy-py)**2
    for y in range(int(min(py,dy)-max(r0,r1))-1,int(max(py,dy)+max(r0,r1))+2):
        for x in range(int(min(px,dx)-max(r0,r1))-1,int(max(px,dx)+max(r0,r1))+2):
            cx_,cy_=x+0.5,y+0.5
            t=max(0,min(1,((cx_-px)*(dx-px)+(cy_-py)*(dy-py))/L2)) if L2 else 0.0
            ax,ay=px+t*(dx-px),py+t*(dy-py); r=r0+(r1-r0)*t
            ox,oy=cx_-ax,cy_-ay; d=math.hypot(ox,oy)
            if d<r:
                nz=math.sqrt(max(0,1-(d/r)**2)); s=d/r
                n=np.array([ox/(d+1e-9)*s,oy/(d+1e-9)*s,nz])
                put(x,y,z0+(z1-z0)*t+r*nz,n,m)
def sphere(c,r,z,m=1): capsule(c,c,r,r,z,z,m)
def plate(poly,z,thick,bevel,m=0,dome=0.0,grooves=(),bolts=()):
    """flat-faced armour plate with a rounded bevel; normals from its height field"""
    nid()
    img=Image.new('L',(W,H)); ImageDraw.Draw(img).polygon(poly,fill=1); mask=np.array(img).astype(bool)
    ys,xs=np.nonzero(mask)
    if len(xs)==0: return
    # distance to the plate edge (brute force on a small set)
    edge=[(x,y) for x,y in zip(xs,ys) if not all(0<=x+dx<W and 0<=y+dy<H and mask[y+dy,x+dx] for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))]
    E=np.array(edge,dtype=float)
    hgt=np.full((H,W),np.nan)
    cxm,cym=xs.mean(),ys.mean(); sx=max(1,(xs.max()-xs.min())/2); sy=max(1,(ys.max()-ys.min())/2)
    for x,y in zip(xs,ys):
        e=np.min(np.hypot(E[:,0]-x,E[:,1]-y))+0.5
        prof=1.0 if e>=bevel else math.sqrt(max(0,1-(1-e/bevel)**2))
        h=thick*prof - dome*(((x-cxm)/sx)**2+((y-cym)/sy)**2)
        hgt[y,x]=h
    for g in grooves:                                   # cut panel lines into the plate
        for (x,y) in g:
            if 0<=x<W and 0<=y<H and not np.isnan(hgt[y,x]): hgt[y,x]-=1.2
    for (bx,by) in bolts:
        if not np.isnan(hgt[by,bx]): hgt[by,bx]+=0.8
    for x,y in zip(xs,ys):
        def h(xx,yy): 
            v=hgt[yy,xx] if 0<=xx<W and 0<=yy<H else np.nan
            return hgt[y,x] if np.isnan(v) else v
        gx=(h(x+1,y)-h(x-1,y))/2; gy=(h(x,y+1)-h(x,y-1))/2
        n=np.array([-gx,-gy,1.0]); n/=np.linalg.norm(n)
        put(x,y,z+hgt[y,x],n,m)
    for g in grooves:
        for (x,y) in g:
            if 0<=x<W and 0<=y<H and pid[y,x]==_pid[0]: paint[y,x]=1
            if 0<=x<W and 0<=y+1<H and pid[y+1,x]==_pid[0] and (x,y+1) not in g: paint[y+1,x]=2
def hline(x0,x1,y): return [(x,y) for x in range(x0,x1+1)]
def vline(x,y0,y1): return [(x,y) for y in range(y0,y1+1)]
def mirror(poly,c): return [(2*c-x,y) for x,y in poly]

cx=42
# ---------------- legs (back to front order doesn't matter: z-buffer) ----------------
for s in (-1,1):
    X=lambda x: cx+s*(x-cx) if s==1 else 2*cx-x if False else cx+s*(cx-x)*-1
    hipx=cx+s*9; kx=cx+s*15; ax_=cx+s*16
    sphere((hipx,57),4.5,3)
    capsule((hipx,57),(kx,76),6.5,5.5,3,5)                         # thigh
    sphere((kx,77),4,5)                                            # knee joint
    plate([(kx-4,72),(kx+4,72),(kx+5,76),(kx+3,80),(kx-3,80),(kx-5,76)],z=11,thick=3,bevel=2,dome=0.8)  # kneecap
    capsule((kx,79),(ax_,96),5.5,4.3,5,4)                           # shin
    sphere((ax_,97),3,4)                                           # ankle
    foot=[(ax_-7,97),(ax_+7,97),(ax_+9,101),(ax_+9,104),(ax_-9,104),(ax_-9,101)]
    plate(foot,z=4,thick=4,bevel=2,dome=0.5,grooves=[vline(ax_-3,100,104),vline(ax_+3,100,104)])
    for tx in (ax_-6,ax_,ax_+6):                                   # claw tips (source claw feet)
        capsule((tx,103),(tx+ (tx-ax_)//3,106),1.4,0.8,7,7,m=1)
# ---------------- pelvis / waist (flat, armoured, no belly) ----------------
plate([(32,50),(52,50),(54,53),(48,59),(36,59),(30,53)],z=5,thick=5,bevel=2,dome=0.8,
      grooves=[vline(cx,52,58)],bolts=[(34,53),(50,53)])
capsule((cx,44),(cx,51),5,5,1,1,m=1)                                # spine housing
plate([(34,43),(50,43),(49,50),(35,50)],z=5,thick=3,bevel=1.5,grooves=[hline(35,49,46)])   # abdominal plates
# ---------------- chest ----------------
chest=[(27,21),(57,21),(61,26),(60,35),(55,42),(48,45),(36,45),(29,42),(24,35),(23,26)]
plate(chest,z=4,thick=7,bevel=3,dome=2.0,grooves=[vline(cx,24,44),hline(28,56,38)],
      bolts=[(28,25),(56,25),(27,33),(57,33)])
LOGO=["#########..","##########.","........##.",".###.####..","#.###.##...","##.###.##..","##..###.##.","##...###.##","##....###.#"]
logo_px=[(cx-5+i,25+j) for j,row in enumerate(LOGO) for i,ch in enumerate(row) if ch=='#']
chest_id=_pid[0]
# ---------------- head ----------------
capsule((cx,18),(cx,21),3.5,3.5,2,2,m=1)                           # 2px neck
plate([(34,5),(50,5),(52,8),(52,16),(49,19),(35,19),(32,16),(32,8)],z=7,thick=6,bevel=2.5,dome=1.0,
      grooves=[hline(34,50,9)])
head_id=_pid[0]
for s in (-1,1):                                                   # twin fins (the source ear fins)
    fx=cx+s*6
    plate([(fx-1,6),(fx+s*4,1),(fx+s*5,2),(fx+2*s+ (1 if s>0 else -1),7)],z=8,thick=2,bevel=1)
eye_c=(cx,13)
# ---------------- arms: combat guard ----------------
for s,fist_y in ((-1,17),(1,21)):
    shx=cx+s*18; ex=cx+s*24; fx=cx+s*14
    sphere((shx,25),4.5,1)                                          # shoulder joint
    capsule((shx,26),(ex,44),5.3,4.6,1,3)                           # upper arm
    sphere((ex,45),4,4)                                            # elbow
    capsule((ex,45),(fx,fist_y+5),5.2,4.4,4,12)                     # forearm, raised toward the viewer
    plate([(fx-5,fist_y-2),(fx+5,fist_y-2),(fx+6,fist_y+2),(fx+5,fist_y+6),(fx-5,fist_y+6),(fx-6,fist_y+2)],
          z=14,thick=4,bevel=2,dome=0.8,grooves=[hline(fx-5,fx+5,fist_y),vline(fx-2,fist_y+1,fist_y+5),vline(fx+2,fist_y+1,fist_y+5)])
    # pauldron with the source spike
    pc=cx+s*19
    pd=[(pc-9,20),(pc-4,16),(pc+4,16),(pc+9,20),(pc+10,27),(pc+7,32),(pc-7,32),(pc-10,27)]
    plate(pd,z=8,thick=6,bevel=3,dome=2.0,grooves=[hline(pc-9,pc+9,26)],bolts=[(pc-6,22),(pc+6,22)])
    sp=[(pc+s*6,18),(pc+s*12,12),(pc+s*10,19)]
    plate(sp,z=12,thick=2,bevel=1)

# ---------------- shading ----------------
L=np.array([-0.55,-0.65,0.55]); L/=np.linalg.norm(L); Hv=L+np.array([0,0,1.0]); Hv/=np.linalg.norm(Hv)
rng=np.random.default_rng(7)
grime=np.zeros((H,W))
for sc,amp in ((8,0.16),(3,0.07)):                                  # blotchy grime
    g=rng.random((H//sc+2,W//sc+2)); gi=np.array(Image.fromarray((g*255).astype(np.uint8)).resize((W+sc,H+sc),Image.BILINEAR))[:H,:W]/255
    grime+= (gi-0.5)*2*amp
grime-= np.linspace(0,0.16,H)[:,None]                               # dirt gathers toward the feet
speck=rng.random((H,W))<0.10
scuff=rng.random((H,W))<0.025
img=np.zeros((H,W,3),dtype=np.uint8); alpha=np.zeros((H,W),dtype=bool)
for y in range(H):
    for x in range(W):
        if mat[y,x]<0: continue
        alpha[y,x]=True
        n=normal[y,x]; lam=max(0,n@L); spec=max(0,n@Hv)**18
        # ambient occlusion from nearby surfaces in front
        occ=0
        for dy in (-2,-1,0,1,2):
            for dx in (-2,-1,0,1,2):
                yy,xx=y+dy,x+dx
                if 0<=yy<H and 0<=xx<W and mat[yy,xx]>=0 and depth[yy,xx]>depth[y,x]+2: occ+=1
        v=0.03+0.74*lam+0.42*spec-0.03*occ+grime[y,x]-(0.08 if speck[y,x] else 0)+(0.14 if scuff[y,x] and lam>0.4 else 0)
        if mat[y,x]==1: v=0.05+0.7*lam+0.7*spec-0.03*occ+grime[y,x]*0.6
        if paint[y,x]==1: v-=0.28
        if paint[y,x]==2: v+=0.12
        ramp=ARMOR if mat[y,x]==0 else METAL
        if pid[y,x]==chest_id and (x,y) in logo_px:                 # stencilled RealWare mark, takes the light & grime
            ramp=RED[1:6]; v=v*0.9+0.12
            if speck[y,x] and grime[y,x]<-0.05: ramp=ARMOR; v=0.12   # worn stencil
        img[y,x]=ramp[int(max(0,min(0.999,v))*len(ramp))]
# eye: recessed socket with the source cross-ring glow
ex,ey=eye_c
for y in range(ey-3,ey+4):
    for x in range(ex-3,ex+4):
        if abs(x-ex)<=3 and abs(y-ey)<=3: img[y,x]=METAL[0]
EYE=[".R.","RRR",".R."]
for j in range(-2,3):
    for i in range(-2,3):
        d=abs(i)+abs(j)
        if d==2 and (i==0 or j==0): img[ey+j,ex+i]=RED[2]
        if d==1: img[ey+j,ex+i]=RED[4]
img[ey,ex]=RED[5]; img[ey-1,ex-1]=RED[1]; img[ey+1,ex+1]=RED[1]
# internal separation: dark line where a nearer part overlaps
out=img.copy()
for y in range(H):
    for x in range(W):
        if not alpha[y,x]: continue
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            yy,xx=y+dy,x+dx
            if 0<=yy<H and 0<=xx<W and alpha[yy,xx] and pid[yy,xx]!=pid[y,x] and depth[yy,xx]>depth[y,x]+1.5:
                out[y,x]=BLACK if depth[yy,xx]>depth[y,x]+4 else METAL[0]; break
# black silhouette outline
rgba=np.zeros((H,W,4),dtype=np.uint8); rgba[...,:3]=out; rgba[...,3]=alpha*255
for y in range(H):
    for x in range(W):
        if not alpha[y,x] and any(0<=y+dy<H and 0<=x+dx<W and alpha[y+dy,x+dx] for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))):
            rgba[y,x]=(0,0,0,255)
im=Image.fromarray(rgba,'RGBA'); im=im.crop(im.getbbox())
o=Image.new('RGBA',(im.width+2,im.height+2)); o.alpha_composite(im,(1,1))
o.save(OUT+'robot_1x.png')
o.resize((o.width*3,o.height*3),Image.NEAREST).save(OUT+'robot_3x.png')
bg=Image.new('RGBA',o.size,(200,200,200,255)); bg.alpha_composite(o)
bg.resize((o.width*6,o.height*6),Image.NEAREST).save(OUT+'robot_6x_preview.png')
print(o.size)
