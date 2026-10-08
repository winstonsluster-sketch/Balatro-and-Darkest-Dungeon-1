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

head=crop(P[2])
arm=crop(P[1].rotate(90,expand=True))                 # shoulder top, elbow points back (right)
leg=twin(crop(P[3].rotate(-90,expand=True)))          # kneecap faces forward (left), lit upper-left
leg=leg.crop((0,0,leg.width,28))                      # source claw-foot replaced by a proper boot
pad=crop(P[5])
ORDER=[BR[0],BR[1],BR[2],BR[3],BR[4],BR[5],BR[6],BR[7],BR[8]]
def darker(im,n=2):
    """far-side limb: same part, further from the light"""
    im=im.copy(); q=im.load()
    for y in range(im.height):
        for x in range(im.width):
            c=q[x,y]
            if not c[3]: continue
            if c in BR_EXTRA: c=BR[2] if c==BR_EXTRA[0] else BR[5]
            if c in ORDER: q[x,y]=ORDER[max(0,ORDER.index(c)-n)]
            elif c in GR: q[x,y]=GR[max(0,GR.index(c)-1)]
            elif c in GN or c==OR: q[x,y]=GR[1]          # far-side cable sinks into shadow
    return im
# wear: chip out of the pauldron's front edge, scratches on the near arm
pq=pad.load()
for x,y in ((2,4),(3,4),(2,5),(3,5),(4,5),(3,6),(4,6)): pq[x,y]=(0,0,0,0)
for x,y in ((1,4),(1,5),(2,6),(3,7),(4,7),(5,6),(5,5),(4,4),(3,3),(2,3)):
    if pq[x,y][3]: pq[x,y]=K
paint(arm,[(9,5),(10,6)],BR[7]); paint(arm,[(10,5),(11,6)],BR[1])
paint(arm,[(6,25),(7,26),(8,27)],BR[1])
W,Hh=80,110
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
        v=0.42+bright-form*nx-0.18*ny+noise(x,y)*0.07
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

# ---------------- assemble (uniform 3/4 view, facing left) ----------------
tx=24; ty=26
DK=lambda d:{k:(ORDER[max(0,ORDER.index(v)-2)] if v in ORDER else GR[max(0,GR.index(v)-1)] if v in GR else v) for k,v in d.items()}
def leg_at(img,lx,dark):
    sh=shell(lx+11,LY+2,[6,7,7,7,7,7,7,6,6,5,5,4])
    layer_draw(DK(sh) if dark else sh)
    sprite(img,lx,LY)
    a=joint(lx+6,LY+28,2); b=boot(lx+6,LY+29)
    layer_draw(DK(a) if dark else a); layer_draw(DK(b) if dark else b)
LY=ty+26
# far side, back to front
sprite(darker(pad),tx-7,ty-3)
sprite(darker(arm),tx-9,ty+2)
layer_draw(DK(joint(tx+5,ty+27,3)))
leg_at(darker(leg),tx-3,True)
layer_draw(neck(tx+11,ty-3,4))
layer_draw(pelvis(tx+11,ty+23))
layer_draw(torso34(tx,ty))
layer_draw(joint(tx+17,ty+27,4))
leg_at(leg,tx+9,False)
layer_draw(tasset(tx+13,ty+24,9,8,1))
sprite(head,tx+1,ty-20)
sprite(arm,tx+15,ty+3)
sprite(pad,tx+13,ty-3)

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
