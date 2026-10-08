"""Quasimorph-style military robot (grey/red), assembled at native 1x from the five source parts.
usage: python3 build_robot.py <dir with n1..n5.png native parts> <out dir>"""
import sys
from PIL import Image, ImageOps
SRC,OUT=sys.argv[1].rstrip('/')+'/',sys.argv[2].rstrip('/')+'/'
def H(s): return tuple(int(s[i:i+2],16) for i in (0,2,4))+(255,)
K=H('000000')
BR=[H(c) for c in '261209 3d1f12 4f2c19 623921 704325 84512f aa6e46 cea173 e2cc98'.split()]
BR_EXTRA=[H('502c1a'),H('8d5936')]
GR=[H(c) for c in '110e0e 1d1717 261e1e 352d2d 514444'.split()]
GN=[H(c) for c in '0b2b13 10381a 2a461b 465e24'.split()]
OR=H('c27a2d'); RD=[H(c) for c in '380b04 701508 e02a11'.split()]
def fam(c):
    if c[3]==0: return None
    if c==K: return 'k'
    if c in BR or c in BR_EXTRA: return 'b'
    if c in GR: return 'g'
    return 'x'
P={i:Image.open(f'{SRC}n{i}.png').convert('RGBA') for i in range(1,6)}
def crop(im): return im.crop(im.getbbox())

def twin(im):
    """Opposite-side counterpart: mirrored silhouette, but re-lit so light still falls from
    the upper-left (a straight flip would move every highlight to the wrong side)."""
    M=ImageOps.mirror(im); w,h=im.size; m=M.load(); o=im.load()
    out=M.copy(); q=out.load()
    for y in range(h):
        x=0
        while x<w:
            if m[x,y][3]==0: x+=1; continue
            a=x
            while x<w and m[x,y][3]: x+=1
            b=x-1                          # run a..b in mirror == run (w-1-b)..(w-1-a) in original
            for k in range(b-a+1):
                src=o[w-1-b+k,y]; cur=m[a+k,y]
                if fam(src)==fam(cur) and fam(cur) in ('b','g'): q[a+k,y]=src
    return out

def paint(im,pts,col,only=('b',)):
    px=im.load()
    for x,y in pts:
        if 0<=x<im.width and 0<=y<im.height and fam(px[x,y]) in only: px[x,y]=col


def relight(im,rows=True,cols=True):
    """after a rotation/mirror: keep the silhouette, restore source light direction inside each run"""
    def runs(get,set_,n,m,src_get):
        for j in range(m):
            i=0
            while i<n:
                if get(i,j)[3]==0: i+=1; continue
                a=i
                while i<n and get(i,j)[3]: i+=1
                b=i-1
                vals=[src_get(k,j) for k in range(a,b+1)][::-1]
                for k in range(a,b+1):
                    cur=get(k,j); v=vals[k-a]
                    if fam(cur)==fam(v) and fam(cur) in ('b','g'): set_(k,j,v)
    out=im.copy(); q=out.load(); src=im.copy(); sq=src.load()
    if rows:
        runs(lambda i,j:q[i,j], lambda i,j,v:q.__setitem__((i,j),v), im.width, im.height, lambda i,j:sq[i,j])
    if cols:
        s2=out.copy(); s2q=s2.load()
        runs(lambda i,j:q[j,i], lambda i,j,v:q.__setitem__((j,i),v), im.height, im.width, lambda i,j:s2q[j,i])
    return out
SA=crop(P[1].rotate(90,expand=True))                   # upright arm
upper=SA.crop((0,0,SA.width,21))                         # upper arm + elbow joint
fore=SA.crop((0,19,SA.width,SA.height))                  # forearm + fist
fore_up=relight(fore.rotate(180))                        # raised: fist on top, still lit from upper-left
leg=crop(P[3].rotate(-90,expand=True))
pad=crop(P[5])
src_head=P[2]
GUN=Image.open(SRC+'gun.png').convert('RGBA')            # CS M249 from Quasimorph, native 1x
def forearm(length):
    """forearm pointing at the viewer is foreshortened: keep the elbow cuff and the fist"""
    f=fore; keep_top=3; keep_bot=length-keep_top
    out=Image.new('RGBA',(f.width,length))
    out.alpha_composite(f.crop((0,0,f.width,keep_top)),(0,0))
    out.alpha_composite(f.crop((0,f.height-keep_bot,f.width,f.height)),(0,keep_top))
    return out
W,Hh=96,104
cv=Image.new('RGBA',(W,Hh)); px=cv.load()
def layer_draw(pix):
    for (x,y) in pix:
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            q=(x+dx,y+dy)
            if q not in pix and 0<=q[0]<W and 0<=q[1]<Hh: px[q]=K
    for (x,y),c in pix.items(): px[x,y]=c
def sprite(im,x,y): cv.alpha_composite(im,(x,y))
def ramp(r,v):
    v=max(0.0,min(0.999,v)); return r[int(v*len(r))]
def cyl(rows,y0,light=0.32,top=0.0,gain=1.0):
    pix={}; n=len(rows)
    for i,(l,r) in enumerate(rows):
        w=max(1,r-l)
        for x in range(l,r+1):
            t=(x-l)/w
            v=1-abs(t-light)*1.9 if t>light else 1-(light-t)*1.2
            v=v*0.78*gain-0.06-(i/n)*0.22+top*(1-i/n)
            if t>0.88: v-=0.15
            pix[(x,y0+i)]=ramp(BR[:8],v)
    return pix
def joint(cx,cy,r):
    pix={}
    for y in range(cy-r,cy+r+1):
        for x in range(cx-r,cx+r+1):
            if ((x-cx)**2+(y-cy)**2)**.5<=r+0.3:
                lx=((x-cx+r*0.4)**2+(y-cy+r*0.4)**2)**.5/(r*1.6)
                pix[(x,y)]=ramp(GR,1-lx)
    return pix


# ---- armour shading that copies the source sprites: dark mottled body, lit upper-left rim,
#      shadowed lower-right rim, no smooth stripes ----
DR=[BR[0],BR[1],BR[2],BR[4],H('8d5936'),BR[6],BR[7]]
def noise(x,y): return ((x*73856093)^(y*19349663))%7/7.0-0.5
def shade(mask,bright=0.0,hl=True,form=0.30):
    xs=[p[0] for p in mask]; ys=[p[1] for p in mask]
    x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys); w=max(1,x1-x0); h=max(1,y1-y0)
    pix={}
    for (x,y) in mask:
        nx=(x-x0)/w; ny=(y-y0)/h
        v=0.42+bright-form*nx-0.18*ny+noise(x,y)*0.18
        if (x-1,y) not in mask or (x,y-1) not in mask: v+=0.30          # lit rim
        if (x+1,y) not in mask or (x,y+1) not in mask: v-=0.30          # shadow rim
        pix[(x,y)]=ramp(DR[:6] if not hl else DR,v)
    return pix
def dome(mask,bright=0.0,lx=0.3,ly=0.3):
    """convex plate: highlight cluster toward the upper-left, falling off to a dark lower-right"""
    xs=[p[0] for p in mask]; ys=[p[1] for p in mask]
    x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys); w=max(1,x1-x0); h=max(1,y1-y0)
    pix={}
    for (x,y) in mask:
        d=(((x-x0)/w-lx)**2+((y-y0)/h-ly)**2)**.5
        v=0.78+bright-d*1.05+noise(x,y)*0.06
        if (x-1,y) not in mask or (x,y-1) not in mask: v+=0.12
        if (x+1,y) not in mask or (x,y+1) not in mask: v-=0.3
        pix[(x,y)]=ramp(DR,v)
    return pix
def rows_mask(rows,y0): return {(x,y0+i) for i,(l,r) in enumerate(rows) for x in range(l,r+1)}
def slot(pix,x,y,n=2):                                                    # recessed vent like the source torso
    for k in range(n): pix[(x+k,y)]=GR[0]
    for k in range(n): pix.setdefault((x+k,y-1),None); pix[(x+k,y-1)]=BR[0]

RW=["xxx.x...x","x.x.x...x","xx..x.x.x","x.x.xx.xx","x.x.x...x"]   # placeholder stencil
def torso34(tx,y0):
    """3/4 torso facing left: lit front face (left), shaded side face (right)"""
    seam=tx+14
    front=[];side=[]
    for i in range(24):
        bul=[0,1,1,2,2,2,2,2,2,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0][i]
        l=tx-bul+(3 if i>=15 else 0)+(1 if i==0 else 0)
        r=tx+23-(1 if i==0 else 0)-(1 if i>=13 else 0)-(1 if i>=17 else 0)-(1 if i>=20 else 0)
        front.append((l,seam-1)); side.append((seam,r))
    pix={}
    pix.update(dome(rows_mask(front[:15],y0),bright=0.2,lx=0.3,ly=0.25))
    pix.update(dome(rows_mask(front[15:],y0+15),bright=0.05,lx=0.35,ly=0.2))
    pix.update(dome(rows_mask(side[:15],y0),bright=-0.12,lx=0.1,ly=0.2))
    pix.update(dome(rows_mask(side[15:],y0+15),bright=-0.2,lx=0.1,ly=0.2))
    for y in range(y0+1,y0+24): pix[(seam,y)]=BR[0]                    # edge between the faces
    for x in range(front[14][0]+1,side[14][1]): pix[(x,y0+14)]=BR[0]   # chest / abdomen split
    for x in range(front[15][0]+1,front[15][0]+5): pix[(x,y0+15)]=BR[5]
    for y in range(y0+16,y0+23):                                         # exposed spine at the back
        r=side[y-y0][1]
        for k,x in enumerate(range(r-2,r+1)): pix[(x,y)]=[GR[3],GR[2],GR[0]][k] if (y-y0)%2 else GR[0]
    lx_,ly_=tx+3,y0+4                                                    # logo plate (placeholder RW)
    for j in range(-1,6):
        for i in range(-1,10): pix[(lx_+i,ly_+j)]=BR[1]
    for j,line in enumerate(RW):
        for i,ch in enumerate(line):
            if ch=="x": pix[(lx_+i,ly_+j)]=RD[2] if j<2 else RD[1]
    for x in range(lx_-1,lx_+10): pix[(x,ly_+6)]=BR[5]
    # battle damage: torn plate at the lower front of the chest, wires showing
    bx,by=front[12][0]+2,y0+11
    for (x,y) in ((bx,by),(bx+1,by),(bx+2,by),(bx,by+1),(bx+1,by+1),(bx,by+2)): pix[(x,y)]=GR[0]
    pix[(bx+1,by+1)]=RD[0]; pix[(bx,by+2)]=GR[3]; pix[(bx+1,by+2)]=RD[1]
    pix[(bx+3,by)]=BR[6]; pix[(bx+2,by+1)]=BR[6]                          # bright torn edge
    return pix
def boot(ax,ay):
    spans=[(-3,3),(-5,4),(-7,5),(-9,5),(-10,6),(-10,6)]
    rows=[(ax+l,ax+r) for l,r in spans]
    pix=dome(rows_mask(rows,ay),bright=0.35,lx=0.2,ly=0.15)
    for x in range(ax-10,ax+7): pix[(x,ay+6)]=GR[1] if (x-ax)%3 else GR[0]     # sole + tread
    for x in range(ax-10,ax-6): pix[(x,ay+6)]=GR[2]
    for y in range(ay+2,ay+6): pix[(ax-4,y)]=BR[1]                            # toe-cap seam
    pix[(ax-7,ay+3)]=BR[8]; pix[(ax-8,ay+4)]=BR[7]; pix[(ax-6,ay+3)]=BR[7]   # toe-cap shine
    pix[(ax+4,ay+3)]=GR[0]                                                     # heel bolt
    return pix
def abdomen_spine(cx,y0,h):
    pix={}
    for i in range(h):
        for x in range(cx-2,cx+3):
            pix[(x,y0+i)]=[GR[1],GR[2],GR[3],GR[2],GR[0]][x-(cx-2)] if i%2==0 else GR[0]
    return pix
def ab_plate(xin,y0,h,side):
    """side -1: plate left of spine (xin = its inner edge), +1: right of spine"""
    rows=[]
    for i in range(h):
        w=8-i//3
        rows.append((xin-w+1,xin) if side<0 else (xin,xin+w-1))
        if i in (0,h-1): rows[-1]=(rows[-1][0]+(1 if side<0 else 0),rows[-1][1]-(0 if side<0 else 1))
    pix=shade(rows_mask(rows,y0),bright=0.12,form=0.5)
    m=y0+h//2-1
    l,r=rows[h//2-1]
    for x in range(l+1,r): pix[(x,m)]=BR[0]
    for x in range(l+1,l+3): pix[(x,m+1)]=BR[4]
    return pix
def belt(cx,y0,w):
    pix={}
    for i in range(3):
        for x in range(cx-w//2,cx-w//2+w):
            t=(x-(cx-w//2))/w
            pix[(x,y0+i)]=(GR[3] if t<0.35 else GR[2]) if i==0 else (GR[2] if t<0.35 else GR[1]) if i==1 else GR[0]
    for x in range(cx-2,cx+2):
        pix[(x,y0)]=GR[4] if x==cx-2 else GR[3]; pix[(x,y0+1)]=GR[3]
    return pix
def strap(x,y0,y1):
    pix={}
    for y in range(y0,y1):
        pix[(x,y)]=GN[3] if (y-y0)%5 else GN[2]; pix[(x+1,y)]=GN[2]; pix[(x+2,y)]=GN[1] if (y-y0)%5 else GN[0]
    return pix
def buckle(x,y):
    return {(x,y):GR[4],(x+1,y):GR[3],(x+2,y):GR[2],(x,y+1):GR[3],(x+1,y+1):GR[0],(x+2,y+1):GR[1]}
def pouch(x0,y0,w=5,h=4):
    pix={}
    for i in range(h):
        for x in range(x0,x0+w):
            t=(x-x0)/(w-1)
            pix[(x,y0+i)]=GN[3] if (i==0 and t<0.6) else GN[2] if t<0.5 else GN[1] if t<0.85 else GN[0]
    for x in range(x0,x0+w): pix[(x,y0+1)]=GN[0] if x>x0 else GN[1]
    pix[(x0+w//2,y0+1)]=GR[3]
    return pix
def pelvis(cx,y0):
    rows=[(cx-7,cx+7),(cx-7,cx+7),(cx-6,cx+7),(cx-5,cx+6)]
    return dome(rows_mask(rows,y0),bright=0.05)
def tasset(xl,y0,w,h,side):
    rows=[]
    for i in range(h):
        sl=i//4                                           # flares outward as it hangs
        l=xl-(sl if side<0 else 0); r=xl+w-1+(sl if side>0 else 0)
        if i==h-1: l+=1; r-=1
        rows.append((l,r))
    pix=shade(rows_mask(rows,y0),bright=0.2)
    for ry in (h//2-1,):
        l,r=rows[ry]
        for x in range(l+1,r): pix[(x,y0+ry)]=BR[1]
        for x in range(l+1,l+4): pix[(x,y0+ry+1)]=BR[5]
    l,r=rows[2]; pix[(l+2,y0+2)]=GR[0]; pix[(r-2,y0+2)]=GR[0]
    return pix
def shell(cxl,y0,rows_w):
    rows=[(cxl-w//2,cxl-w//2+w-1) for w in rows_w]
    return dome(rows_mask(rows,y0),bright=0.1,lx=0.2,ly=0.2)
def neck(cx,y0,h):
    return {(x,y0+i):(GR[3] if i%2==0 else GR[1]) if x<cx+2 else GR[0] for i in range(h) for x in range(cx-3,cx+3)}
def antenna(x,y0,h):
    pix={(x,y0+i):GR[3] if i<h//2 else GR[2] for i in range(h)}
    pix[(x,y0)]=GR[4]; pix[(x+1,y0+h-2)]=GR[1]; pix[(x+1,y0+h-1)]=GR[1]
    return pix
def cable(points,shade_=1):
    return {(x,y):GN[shade_ if j%3 else shade_+1] for j,(x,y) in enumerate(points)}

LOGO=['#########..', '##########.', '........##.', '.###.####..', '#.###.##...', '##.###.##..', '##..###.##.', '##...###.##', '##....###.#']

# ---------------- assemble: head-on combat stance ----------------
cx=44
# legs: wide stance, kneecaps outward, claw feet planted; armour shells behind thigh and calf for bulk
LY=50
legL=twin(leg); legR=leg
for c in (cx-12,cx+12):
    layer_draw(shade(rows_mask([(c-w//2,c-w//2+w-1) for w in [12,13,14,14,14,14,14,13,13,12,12,11,10]],LY+2),bright=0.2))
    layer_draw(shade(rows_mask([(c+(1 if c>cx else -1)-w//2,c+(1 if c>cx else -1)-w//2+w-1) for w in [10,11,11,11,11,10,10,9]],LY+19),bright=0.15))
sprite(legL,cx-12-8,LY); sprite(legR,cx+12-10,LY)
# pelvis + narrow mechanical waist (no belly)
pel=shade(rows_mask([(cx-9,cx+9),(cx-10,cx+10),(cx-10,cx+10),(cx-9,cx+9),(cx-7,cx+7),(cx-5,cx+5)],46),bright=0.32)
for y in range(47,51): pel[(cx,y)]=BR[0]
layer_draw(pel)
wst={}
for y in range(40,46):
    for x in range(cx-5,cx+6):
        t=(x-(cx-5))/10
        wst[(x,y)]=(GR[3] if t<0.3 else GR[2] if t<0.7 else GR[1]) if (y-40)%2==0 else GR[0]
layer_draw(wst)
# upper arms hang from the shoulders
sprite(twin(upper),cx-31,22); sprite(upper,cx+15,22)
# torso: V chest drawn the way the source torso is shaded
tw=[24,28,30,30,30,30,29,28,27,26,25,24,22,20,18,16,14,13,12,12]
trows=[(cx-w//2,cx-w//2+w-1) for w in tw]
torso=shade(rows_mask(trows,20),bright=0.38,form=0.4)
for ry in (12,):
    l,r=trows[ry]
    for x in range(l+1,r): torso[(x,20+ry)]=BR[0]
    for x in range(l+1,l+5): torso[(x,21+ry)]=BR[5]
for ry in (6,9):
    l,r=trows[ry]; slot(torso,l+2,20+ry); slot(torso,r-3,20+ry)
for j,row in enumerate(LOGO):
    for i,ch in enumerate(row):
        if ch=='#': torso[(cx-5+i,22+j)]=RD[2]
layer_draw(torso)
# neck: 2px
layer_draw({(x,y):(GR[3] if x<cx else GR[1]) if y==18 else GR[0] for x in range(cx-3,cx+3) for y in (18,19)})
# head: front face, the source eye socket centred, the source ear fins on top
face=shade(rows_mask([(cx-7,cx+6)]*9,8),bright=0.4,form=0.4)
for x in range(cx-6,cx+6): face[(x,16)]=GR[0] if x%2 else GR[2]           # jaw grille
hp=src_head.load()
for (sx0,sx1,dx) in ((10,15,cx-8),(16,21,cx+2)):                           # ears
    for y in range(1,7):
        for x in range(sx0,sx1):
            c=hp[x,y]
            if c[3] and c!=K: face[(dx+x-sx0,y+2)]=c
for y in range(7,14):                                                      # eye socket, exact source pixels
    for x in range(2,8):
        c=hp[x,y]
        face[(cx-3+x-2,y+2)]=c if c[3] else BR[2]
layer_draw(face)
# pauldrons over the shoulder joints
sprite(pad,cx-30,17); sprite(twin(pad),cx+16,17)
# combat stance: CS M249 held across the body
gx,gy=cx-27,37
FIST=SA.crop((0,33,SA.width,SA.height)); FIST=FIST.crop(FIST.getbbox())     # knuckles only
def forearm_h(L,point_right):
    """forearm reaching across toward the gun: source forearm plates, lengthened from its middle"""
    mid=SA.crop((0,21,SA.width,31))
    rows=[mid.crop((0,i,SA.width,i+1)) for i in range(mid.height)]
    while len(rows)<L: rows.insert(5,rows[5])
    im=Image.new('RGBA',(SA.width,L))
    for i,r in enumerate(rows[:L]): im.alpha_composite(r,(0,i))
    im=im.rotate(90 if point_right else -90,expand=True)
    return relight(im)
# elbows sit at (cx-27,40) and (cx+25,40); grips on the gun
gripF=(gx+16,gy+15); gripR=(gx+35,gy+10)
fa=forearm_h(gripF[0]-(cx-27)+2,True);  sprite(fa,cx-27,38)
fb=forearm_h((cx+25)-gripR[0]+2,False); sprite(fb,gripR[0]-1,36)
sprite(GUN,gx,gy)
fl=twin(FIST); sprite(fl,gripF[0]-fl.width//2+1,gripF[1]-2)
sprite(FIST,gripR[0]-FIST.width//2,gripR[1]-1)

GREY={'261209':'2b2626','3d1f12':'3a3333','4f2c19':'4a4242','502c1a':'4a4242','623921':'5a5151',
      '704325':'675d5c','84512f':'7a706e','8d5936':'807573','aa6e46':'9c908c','cea173':'bfb5af','e2cc98':'ddd5cf',
      '0b2b13':'380b04','10381a':'380b04','2a461b':'701508','465e24':'701508','c27a2d':'e02a11'}
GREY={H(k):H(v) for k,v in GREY.items()}
for y in range(Hh):
    for x in range(W):
        c=px[x,y]
        if c[3] and c in GREY: px[x,y]=GREY[c]
out=crop(cv); o=Image.new('RGBA',(out.width+2,out.height+2)); o.alpha_composite(out,(1,1))
o.save(OUT+'robot_1x.png')
o.resize((o.width*3,o.height*3),Image.NEAREST).save(OUT+'robot_3x.png')
bg=Image.new('RGBA',o.size,(200,200,200,255)); bg.alpha_composite(o)
bg.resize((o.width*6,o.height*6),Image.NEAREST).save(OUT+'robot_6x_preview.png')
print(o.size)
