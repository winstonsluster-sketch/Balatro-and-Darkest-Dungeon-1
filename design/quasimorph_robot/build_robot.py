"""RealWare military robot, head-on view, Quasimorph pixel style.
Every part is redrawn facing the viewer from the source part designs; one light from the upper-left.
usage: python3 build_robot.py <out dir>"""
import sys
from PIL import Image
OUT=sys.argv[1].rstrip('/')+'/'
def H(s): return tuple(int(s[i:i+2],16) for i in (0,2,4))+(255,)
K=H('000000')
AR=[H(c) for c in '2b2626 3a3333 4a4242 5a5151 675d5c 7a706e 9c908c bfb5af ddd5cf'.split()]   # armour
GR=[H(c) for c in '110e0e 1d1717 261e1e 352d2d 514444'.split()]                           # joints / dark metal
RD=[H(c) for c in '380b04 701508 e02a11'.split()]
W,Hh=84,104
cv=Image.new('RGBA',(W,Hh)); px=cv.load()
FIG_X0,FIG_W=14,56                       # figure extent, for the global light falloff

def ramp(r,v):
    v=max(0.0,min(0.999,v)); return r[int(v*len(r))]
def noise(x,y): return ((x*73856093)^(y*19349663))%7/7.0-0.5
def mask_rows(cx,y0,widths,shift=None):
    m=set()
    for i,w in enumerate(widths):
        o=shift[i] if shift else 0
        l=cx-w//2+o
        for x in range(l,l+w): m.add((x,y0+i))
    return m
def dome(mask,bright=0.0,lx=0.3,ly=0.25,r=AR,rim=0.14,shadow=0.3):
    xs=[p[0] for p in mask]; ys=[p[1] for p in mask]
    x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys); w=max(1,x1-x0); h=max(1,y1-y0)
    pix={}
    for (x,y) in mask:
        d=(((x-x0)/w-lx)**2+((y-y0)/h-ly)**2)**.5
        g=(x-FIG_X0)/FIG_W                                   # whole figure: light from the left
        v=0.86+bright-d*1.25-0.18*g+noise(x,y)*0.11
        if (x-1,y) not in mask or (x,y-1) not in mask: v+=rim
        if (x+1,y) not in mask or (x,y+1) not in mask: v-=shadow
        pix[(x,y)]=ramp(r,v)
    return pix
def metal(mask,ribs=True):
    """dark mechanical joints: horizontal ribs, lit left edge"""
    xs=[p[0] for p in mask]; x0,x1=min(xs),max(xs); ys=[p[1] for p in mask]; y0=min(ys)
    pix={}
    for (x,y) in mask:
        t=(x-x0)/max(1,x1-x0)
        c=GR[3] if t<0.3 else GR[2] if t<0.7 else GR[1]
        if ribs and (y-y0)%2==1: c=GR[1] if t<0.5 else GR[0]
        if (x-1,y) not in mask and (y-y0)%2==0: c=GR[4]
        pix[(x,y)]=c
    return pix
def draw(pix):
    for (x,y) in pix:
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            q=(x+dx,y+dy)
            if q not in pix and 0<=q[0]<W and 0<=q[1]<Hh: px[q]=K
    for (x,y),c in pix.items(): px[x,y]=c
def seam(pix,pts,lit=None):
    for p in pts:
        if p in pix: pix[p]=AR[0]
    if lit:
        for p in lit:
            if p in pix: pix[p]=AR[6]

cx=42
LOGO=["#########..",
      "##########.",
      "........##.",
      ".###.####..",
      "#.###.##...",
      "##.###.##..",
      "##..###.##.",
      "##...###.##",
      "##....###.#"]

# ---------------- legs ----------------
def leg(c):
    thigh=dome(mask_rows(c,50,[11,11,12,12,12,12,12,11,11,11,11,10,10,10,10,9,9]),bright=0.05)
    seam(thigh,[(x,58) for x in range(c-5,c+5)],[(x,59) for x in range(c-5,c-2)])
    draw(thigh)
    draw(metal(mask_rows(c,67,[8,8,8,8,8])))                                # knee joint
    shin=dome(mask_rows(c,72,[9,10,10,10,10,10,9,9,9,8,8,8,8,8,7]),bright=0.08,lx=0.35)
    for y in range(74,84): 
        if (c-1,y) in shin: shin[(c-1,y)]=AR[7] if y<79 else AR[6]          # shin ridge
    draw(shin)
    draw(dome(mask_rows(c,65,[4,6,6,6,6,4]),bright=0.25,ly=0.2))           # kneecap
    draw(metal(mask_rows(c,87,[6,6])))                                     # ankle
    boot=dome(mask_rows(c,89,[8,10,11,12,12]),bright=0.12,lx=0.3,ly=0.2)
    for x in range(c-6,c+6): boot[(x,94)]=GR[1] if (x-c)%3 else GR[0]      # sole + tread
    seam(boot,[(x,91) for x in range(c-4,c+4)])
    draw(boot)
for c in (cx-7,cx+7):
    draw(metal(mask_rows(c,48,[7,7,7,7]),ribs=False))                     # hip joints
for c in (cx-7,cx+7): leg(c)

# ---------------- pelvis / waist ----------------
pel=dome(mask_rows(cx,44,[24,24,24,22,20,18,14,10]),bright=0.05,ly=0.15)  # angular hip armour, no belly
seam(pel,[(x,45) for x in range(cx-11,cx+11)],[(x,46) for x in range(cx-11,cx-6)])
seam(pel,[(cx,y) for y in range(47,51)])
draw(pel)
# waist: spine column flanked by two pistons, all recessed dark metal
waist={}
for y in range(37,44):
    for x in range(cx-6,cx+6): waist[(x,y)]=GR[0]
for x0 in (cx-5,cx+3):                                                    # pistons
    for y in range(37,44):
        waist[(x0,y)]=GR[4] if y<40 else GR[3]; waist[(x0+1,y)]=GR[2]
for y in range(37,44):                                                    # spine segments
    for x in range(cx-2,cx+2):
        waist[(x,y)]=(GR[3] if x<cx else GR[2]) if (y-37)%3!=2 else GR[0]
draw(waist)
# ---------------- arms ----------------
def arm(c,side):
    sh=[0]*16
    upper=dome(mask_rows(c,24,[9,9,10,10,10,10,10,10,10,9,9,9,9,9,9,8],sh),bright=0.05)
    draw(upper)
    draw(metal(mask_rows(c,40,[7,7,7,7])))                                  # elbow
    fc=c+side                                                             # forearm hangs a touch outward
    fore=dome(mask_rows(fc,44,[10,11,11,11,10,10,10,9,9,9,8,8,8]),bright=0.1)
    seam(fore,[(x,48) for x in range(fc-5,fc+5)],[(x,49) for x in range(fc-5,fc-2)])
    draw(fore)
    draw(metal(mask_rows(fc,57,[6,6])))                                     # wrist
    fist=dome(mask_rows(fc,59,[7,8,8,8,8,7,5]),bright=0.12,ly=0.2)
    seam(fist,[(x,61) for x in range(fc-3,fc+4)])                          # knuckle line
    seam(fist,[(fc-1,y) for y in range(62,64)]+[(fc+2,y) for y in range(62,64)])
    draw(fist)
arm(cx-19,-1); arm(cx+19,1)

# ---------------- torso ----------------
tw=[24,30,32,32,32,32,31,30,29,28,27,26,24,22,20,18,16,15,14]
torso=dome(mask_rows(cx,18,tw),bright=0.12,lx=0.3,ly=0.2)
seam(torso,[(cx-13+i,30+i//3) for i in range(9)]+[(cx+12-i,30+i//3) for i in range(9)],
     [(cx-13+i,31+i//3) for i in range(5)])                               # angled lower-chest plates
for (x,y) in [(cx-13,21),(cx+12,21)]: torso[(x,y)]=GR[0]                    # rivets
lx0,ly0=cx-6,20                                                            # RealWare mark
for j,row in enumerate(LOGO):
    for i,ch in enumerate(row):
        if ch=='#': torso[(lx0+i,ly0+j)]=RD[2]
draw(torso)
draw(metal(mask_rows(cx,16,[8,8]),ribs=False))                             # 2px neck
# ---------------- pauldrons (over the shoulders) ----------------
for c,side in ((cx-18,-1),(cx+18,1)):
    rows=[12,14,15,15,15,15,15,14,13,11]
    sh=[(-side if i<2 else 0) for i in range(len(rows))]          # chamfer toward the neck
    pd=dome(mask_rows(c,15,rows,sh),bright=0.2,lx=0.3,ly=0.2)
    seam(pd,[(x,21) for x in range(c-7,c+8)],[(x,22) for x in range(c-7,c-3)])
    seam(pd,[(x,23) for x in range(c-7,c+8)])
    draw(pd)

# ---------------- head ----------------
crest=dome(mask_rows(cx,3,[4,4,4]),bright=0.2,lx=0.2,ly=0.2)               # low central crest
draw(crest)
head=dome(mask_rows(cx,5,[10,12,14,14,14,14,14,14,13,12,10]),bright=0.12,lx=0.3,ly=0.15)
for x in range(cx-6,cx+6): head[(x,8)]=AR[7] if x<cx-1 else AR[5]           # brow ridge catches the light
for x in range(cx-5,cx+5): head[(x,9)]=GR[0]                               # shadow under the brow
for x in range(cx-4,cx+4): head[(x,10)]=GR[0]                              # eye slit
for x,c in ((cx-3,RD[0]),(cx-2,RD[1]),(cx-1,RD[2]),(cx,RD[2]),(cx+1,RD[1]),(cx+2,RD[0])): head[(x,10)]=c
for x in range(cx-4,cx+4): head[(x,11)]=GR[0]
for x in (cx-3,cx-1,cx+1): head[(x,13)]=GR[0]                              # jaw vents
draw(head)

out=cv.crop(cv.getbbox()); o=Image.new('RGBA',(out.width+2,out.height+2)); o.alpha_composite(out,(1,1))
o.save(OUT+'robot_1x.png')
o.resize((o.width*3,o.height*3),Image.NEAREST).save(OUT+'robot_3x.png')
bg=Image.new('RGBA',o.size,(200,200,200,255)); bg.alpha_composite(o)
bg.resize((o.width*6,o.height*6),Image.NEAREST).save(OUT+'robot_6x_preview.png')
print(o.size)
