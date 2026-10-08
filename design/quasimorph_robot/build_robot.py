import sys
from PIL import Image, ImageOps
D='/tmp/claude-0/-home-user-Balatro-and-Darkest-Dungeon-1/d08569cd-1307-511f-9e29-d7d22a0cec3e/scratchpad/'
def H(s): return tuple(int(s[i:i+2],16) for i in (0,2,4))+(255,)
K=H('000000')
BR=[H(c) for c in '261209 3d1f12 4f2c19 623921 704325 84512f aa6e46 cea173 e2cc98'.split()]
GR=[H(c) for c in '110e0e 1d1717 261e1e 352d2d 514444'.split()]
GN=[H(c) for c in '0b2b13 10381a 2a461b 465e24'.split()]
OR=H('c27a2d'); RD=[H(c) for c in '380b04 701508 e02a11'.split()]
P={i:Image.open(f'{D}n{i}.png').convert('RGBA') for i in range(1,6)}
def crop(im): return im.crop(im.getbbox())
head=crop(P[2]); torso=crop(P[4])
arm=crop(P[1].rotate(90,expand=True)); leg=crop(P[3].rotate(-90,expand=True)); pad=crop(P[5])

W,Hh=70,100
cv=Image.new('RGBA',(W,Hh)); px=cv.load()

def layer_draw(pix):
    """pix: dict (x,y)->rgba. Draw 4-neighbour black outline, then fill (sprite-style)."""
    for (x,y) in pix:
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            q=(x+dx,y+dy)
            if q not in pix and 0<=q[0]<W and 0<=q[1]<Hh: px[q]=K
    for (x,y),c in pix.items(): px[x,y]=c
def sprite(im,x,y): cv.alpha_composite(im,(x,y))

def ramp(r,v):
    v=max(0.0,min(0.999,v)); return r[int(v*len(r))]

def cyl(rows, y0, light=0.32, top=0.0, ramp_=BR, gain=1.0, base=0.0):
    """rows: list of (left,right) inclusive per row starting at y0. Cylinder shading, light upper-left."""
    pix={}
    n=len(rows)
    for i,(l,r) in enumerate(rows):
        w=max(1,r-l)
        for x in range(l,r+1):
            t=(x-l)/w
            v=1-abs(t-light)*1.9 if t>light else 1-(light-t)*1.2
            v=v*0.78*gain+base-0.06 - (i/n)*0.22 + top*(1-i/n)
            if t>0.88: v-=0.15
            pix[(x,y0+i)]=ramp(ramp_[:8] if ramp_ is BR else ramp_,v)
    return pix

def taper(y0,h,c_top,w_top,c_bot,w_bot):
    rows=[]
    for i in range(h):
        f=i/max(1,h-1); c=c_top+(c_bot-c_top)*f; w=w_top+(w_bot-w_top)*f
        rows.append((round(c-w/2),round(c+w/2)-1))
    return rows

# ---------- new parts ----------
def neck(cx,y0,h):
    pix={}
    for i in range(h):
        for x in range(cx-3,cx+3):
            t=(x-(cx-3))/5
            band=GR[3] if i%2==0 else GR[1]
            if t<0.2 and i%2==0: band=GR[4]
            if t>0.8: band=GR[0]
            pix[(x,y0+i)]=band
    return pix

def cable(points,shade=1):
    pix={}
    for j,(x,y) in enumerate(points):
        pix[(x,y)]=GN[shade if j%3 else shade+1]
    return pix

def spine(cx,y0,h):
    """exposed vertebrae column + ribbed flank housing"""
    pix={}
    # housing (dark metal), slightly waisted
    rows=taper(y0,h,cx,12,cx,9)
    for i,(l,r) in enumerate(rows):
        for x in range(l,r+1):
            t=(x-l)/max(1,r-l)
            c=GR[2] if 0.15<t<0.75 else (GR[3] if t<=0.15 else GR[0])
            if i%3==2: c=GR[0]
            pix[(x,y0+i)]=c
    # vertebrae: brown nubs down the middle
    for i in range(0,h-1,3):
        y=y0+i
        for x in range(cx-2,cx+2):
            t=(x-(cx-2))/3
            pix[(x,y)]=BR[6] if t<0.3 else (BR[5] if t<0.7 else BR[3])
        for x in range(cx-2,cx+2):
            pix[(x,y+1)]=BR[3] if x<cx+1 else BR[1]
    return pix

def pelvis(cx,y0):
    # inverted trapezoid plate with a codpiece guard
    rows=[]
    for i in range(8):
        w=20-max(0,i-2)*2
        rows.append((cx-w//2,cx+w//2-1))
    pix=cyl(rows,y0,light=0.3,top=0.15)
    # panel line across + highlight under
    for x in range(rows[3][0]+2,rows[3][1]-1):
        pix[(x,y0+3)]=BR[1]
    for x in range(rows[4][0]+3,cx-1): pix[(x,y0+4)]=BR[6]
    # center guard
    for i in range(5):
        for x in range(cx-3+i//2, cx+3-i//2):
            t=(x-(cx-3))/5
            pix[(x,y0+6+i)]=BR[7] if (t<0.35 and i<2) else (BR[5] if t<0.6 else BR[2])
    pix[(cx-2,y0+6)]=BR[8]
    return pix

def joint(cx,cy,r):
    pix={}
    for y in range(cy-r,cy+r+1):
        for x in range(cx-r,cx+r+1):
            d=((x-cx)**2+(y-cy)**2)**.5
            if d<=r+0.3:
                lx=((x-cx+r*0.4)**2+(y-cy+r*0.4)**2)**.5/(r*1.6)
                pix[(x,y)]=ramp(GR,1-lx)
    return pix

def thigh(cx,y0,h,side):
    rows=taper(y0,h,cx,11,cx+side*3,8)
    pix=cyl(rows,y0,light=0.3 if side<0 else 0.4,top=0.1)
    # armor plate seam + rivets
    m=y0+h//2
    l,r=rows[h//2]
    for x in range(l+1,r): pix[(x,m)]=BR[1]
    for x in range(l+1,l+4): pix[(x,m+1)]=BR[6]
    pix[(l+2,y0+2)]=GR[0]; pix[(r-2,y0+2)]=GR[0]
    # hydraulic piston on the inner side
    for i in range(3,h-2):
        l,r=rows[i]; x=r+1 if side<0 else l-1
        pix[(x,y0+i)]=GR[4] if i<h//2 else GR[2]
        if i==h//2: pix[(x,y0+i)]=GR[0]
    # exposed hydraulic on the inner side
    return pix

def kneecap(cx,y0):
    rows=[(cx-3,cx+2),(cx-4,cx+3),(cx-4,cx+3),(cx-3,cx+2),(cx-2,cx+1)]
    pix=cyl(rows,y0,light=0.3,top=0.3)
    pix[(cx-2,y0+1)]=BR[8]
    return pix

def shin(cx,y0,h,side):
    rows=[]
    for i in range(h):
        f=i/(h-1)
        w=9+ (1 if 0.15<f<0.5 else 0) - round(f*3)   # calf bulge then taper to ankle
        o=round(side*f*1.5); rows.append((cx-w//2+o, cx-w//2+w-1+o))
    pix=cyl(rows,y0,light=0.35,top=0.15)
    # shin ridge highlight
    for i in range(2,h-3):
        l,r=rows[i]; x=l+ (r-l)*35//100
        pix[(x,y0+i)]=BR[7] if i<h//2 else BR[6]
    # vents
    for k in (h//2+1,h//2+3):
        l,r=rows[k]
        for x in range(r-3,r): pix[(x,y0+k)]=GR[0]
    return pix

cx=35
torso_x,torso_y=cx-10,24
head_x,head_y=cx-10,2
layer_draw(neck(cx,head_y+15,torso_y+5-(head_y+15)))
layer_draw(spine(cx,41,10))
sprite(leg,cx-18,52)                      # long toe points outward
sprite(ImageOps.mirror(leg),cx,52)
layer_draw(joint(cx-8,54,3)); layer_draw(joint(cx+8,54,3))
layer_draw(pelvis(cx,48))
sprite(ImageOps.mirror(arm),cx-25,torso_y+2)
sprite(arm,cx+9,torso_y+2)
sprite(torso,torso_x,torso_y)
sprite(head,head_x,head_y)
sprite(pad,cx-24,torso_y-4)
sprite(ImageOps.mirror(pad),cx+8,torso_y-4)
layer_draw(cable([(cx+5,42),(cx+6,43),(cx+6,44),(cx+6,45),(cx+5,46)]))
layer_draw(cable([(cx-6,42),(cx-7,43),(cx-7,44),(cx-6,45)],0))
out=crop(cv); o=Image.new('RGBA',(out.width+2,out.height+2)); o.alpha_composite(out,(1,1))
o.save(D+'robot3_1x.png')
bg=Image.new('RGBA',o.size,(200,200,200,255)); bg.alpha_composite(o)
bg.resize((o.width*6,o.height*6),Image.NEAREST).save(D+'preview3.png')
print(o.size)
