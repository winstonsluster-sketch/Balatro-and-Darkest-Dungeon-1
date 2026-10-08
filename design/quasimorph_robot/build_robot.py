"""Quasimorph-style military robot, assembled at native 1x from the five source parts.
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

head=crop(P[2]); core=crop(P[4])
armR=crop(P[1].rotate(90,expand=True));  armL=twin(armR)
legR=crop(P[3].rotate(-90,expand=True)); legL=twin(legR)      # kneecaps face outward
padL=crop(P[5]);                         padR=twin(padL)

# --- per-side wear & markings: same model of limb, different unit history ---
for y,c in ((8,GN[3]),(9,GN[2]),(10,GN[1])):             # olive armband, left upper arm
    paint(armL,[(x,y) for x in range(armL.width)],c)
paint(armL,[(5,9)],GN[3])
paint(armR,[(8,6),(9,7),(10,8)],BR[7]); paint(armR,[(9,6),(10,7),(11,8)],BR[1])   # gouge, right upper arm
paint(armR,[(3,24),(3,27)],GR[0])                                                    # field-repair rivets
V=((0,0),(1,1),(2,2),(3,1),(4,0))
for row,(lit,sh) in ((10,(H('e2cc98'),BR[1])),(13,(H("cea173"),BR[1]))):        # rank chevrons, left pad
    paint(padL,[(8+dx,row+dy) for dx,dy in V],lit,('b','g'))
    paint(padL,[(8+dx,row+dy+1) for dx,dy in V if (dx,dy)!=(2,2)],sh,('b','g'))
for x,y in ((6,8),(7,8),(8,8),(8,9),(7,10),(7,11),(7,12)):                         # stencilled "7", right pad
    paint(padR,[(x,y)],H('cea173'),('b','g'))
paint(legL,[(10,20),(11,21)],BR[7]); paint(legL,[(11,20),(12,21)],BR[1])             # knee scuff

W,Hh=90,118
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

def carapace(cx,y0):
    prof=[24,28,30,32,32,32,32,32,32,32,32,32,32,31,30,29,28,27,26,25,24,23,22,22]
    rows=[(cx-w//2,cx-w//2+w-1) for w in prof]
    pix=cyl(rows,y0,light=0.3,top=0.2)
    for ry in (7,12,17):                                   # rib seams with lit lip below
        l,r=rows[ry]
        for x in range(l+1,r): pix[(x,y0+ry)]=BR[1]
        for x in range(l+1,l+5): pix[(x,y0+ry+1)]=BR[6]
    for ry in (3,9,14,19):
        l,r=rows[ry]; pix[(l+2,y0+ry)]=GR[0]; pix[(r-2,y0+ry)]=GR[0]
    return pix
def abdomen(cx,y0):
    pix={}
    for i,w in enumerate((20,20,19,19,18,18,17)):
        rows=[(cx-w//2,cx-w//2+w-1)]
        seg=cyl(rows,0,light=0.3,top=0.25 if i%2==0 else 0.0)
        for (x,_),c in seg.items(): pix[(x,y0+i)]=c if i%2==0 else BR[1] if x%4==0 else c
    for i in (2,5):
        for x in range(cx-9,cx+9):
            if (x,y0+i) in pix: pix[(x,y0+i)]=BR[0] if x>cx+4 else BR[1]
    return pix
def belt(cx,y0,w):
    pix={}
    for i in range(3):
        for x in range(cx-w//2,cx-w//2+w):
            t=(x-(cx-w//2))/w
            pix[(x,y0+i)]=(GN[2] if t<0.4 else GN[1]) if i<2 else GN[0]
    for x in range(cx-w//2,cx-w//2+w//2): pix[(x,y0)]=GN[3]
    for x in range(cx-2,cx+2):                         # buckle
        for i in range(3): pix[(x,y0+i)]=GR[3] if i==0 else GR[2]
    pix[(cx-2,y0)]=GR[4]; pix[(cx-1,y0+1)]=OR
    return pix
def pouch(x0,y0,w=5,h=4):
    pix={}
    for i in range(h):
        for x in range(x0,x0+w):
            t=(x-x0)/(w-1)
            pix[(x,y0+i)]=GN[3] if (i==0 and t<0.6) else GN[2] if t<0.5 else GN[1] if t<0.85 else GN[0]
    for x in range(x0,x0+w): pix[(x,y0+1)]=GN[0] if x>x0 else GN[1]      # flap edge
    pix[(x0+w//2,y0+1)]=OR                                               # snap
    return pix
def pelvis(cx,y0):
    rows=[(cx-(w//2),cx-(w//2)+w-1) for w in (26,26,24,22,20,18)]
    pix=cyl(rows,y0,light=0.3,top=0.15)
    for x in range(rows[2][0]+2,rows[2][1]-1): pix[(x,y0+2)]=BR[1]
    for i in range(5):
        for x in range(cx-3+i//2,cx+3-i//2):
            t=(x-(cx-3))/5
            pix[(x,y0+6+i)]=BR[7] if (t<0.35 and i<2) else (BR[5] if t<0.6 else BR[2])
    return pix
def neck(cx,y0,h):
    return {(x,y0+i):(GR[3] if i%2==0 else GR[1]) if x<cx+2 else GR[0] for i in range(h) for x in range(cx-3,cx+3)}
def antenna(x,y0,h):
    pix={(x,y0+i):GR[3] if i<h//2 else GR[2] for i in range(h)}
    pix[(x,y0)]=GR[4]; pix[(x+1,y0+h-2)]=GR[1]; pix[(x+1,y0+h-1)]=GR[1]
    return pix
def bandolier(x0,y0,n):
    pix={}
    for t in range(n):
        x,y=x0+t,y0+t
        for k in range(3): pix[(x,y+k)]=GR[1] if k else GR[2]
        if t%3==1:                                         # brass round, tip catches the light
            pix[(x,y)]=H('cea173'); pix[(x,y+1)]=OR; pix[(x,y+2)]=OR
            pix[(x+1,y+1)]=OR if (x+1,y+1) not in pix else pix[(x+1,y+1)]
    return pix
def cable(points,shade=1):
    return {(x,y):GN[shade if j%3 else shade+1] for j,(x,y) in enumerate(points)}

# ---------------- assemble ----------------
cx=44
cy=30                       # carapace top
layer_draw(antenna(cx+6,cy-26,12))
layer_draw(neck(cx,cy-4,6))
# legs, hips
hip=11
sprite(legL,cx-hip-8,cy+38); sprite(legR,cx+hip-9,cy+38)
layer_draw(pouch(cx+hip-6,cy+43,5,5))                # thigh rig on the right leg
layer_draw(joint(cx-hip+1,cy+39,3)); layer_draw(joint(cx+hip-1,cy+39,3))
layer_draw(pelvis(cx,cy+34))
layer_draw(abdomen(cx,cy+23))
layer_draw(belt(cx,cy+30,26))
layer_draw(pouch(cx-12,cy+31)); layer_draw(pouch(cx+7,cy+31))
# arms behind carapace & pads
sprite(armL,cx-29,cy+4); sprite(armR,cx+13,cy+4)
layer_draw(carapace(cx,cy))
sprite(core,cx-10,cy+2)
layer_draw(bandolier(cx-13,cy+1,25))
layer_draw(cable([(cx+12,cy+19),(cx+13,cy+20),(cx+13,cy+21),(cx+12,cy+22)],0))
sprite(head,cx-10,cy-18)
sprite(padL,cx-25,cy-4); sprite(padR,cx+10,cy-4)

out=crop(cv); o=Image.new('RGBA',(out.width+2,out.height+2)); o.alpha_composite(out,(1,1))
o.save(OUT+'robot_1x.png')
o.resize((o.width*3,o.height*3),Image.NEAREST).save(OUT+'robot_3x.png')
bg=Image.new('RGBA',o.size,(200,200,200,255)); bg.alpha_composite(o)
bg.resize((o.width*6,o.height*6),Image.NEAREST).save(OUT+'robot_6x_preview.png')
print(o.size)
