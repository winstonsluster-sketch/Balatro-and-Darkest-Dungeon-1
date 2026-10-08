"""RealWare combat robot, head-on, built only from the source sprites' own pixels.
Each posed segment samples the matching segment of a source sprite along its length and across
its width (light side always upper-left), so streaks, speckle, seams, cables and joints are the
source art. Recoloured brown->grey value for value at the end.
usage: python3 build_robot.py <dir with n1..n5.png> <out dir>"""
import sys, math
from PIL import Image, ImageOps
SRC,OUT=sys.argv[1].rstrip('/')+'/',sys.argv[2].rstrip('/')+'/'
def H(s): return tuple(int(s[i:i+2],16) for i in (0,2,4))+(255,)
K=H('000000')
BR=[H(c) for c in '261209 3d1f12 4f2c19 623921 704325 84512f aa6e46 cea173 e2cc98'.split()]
BR_X=[H('502c1a'),H('8d5936')]
GR=[H(c) for c in '110e0e 1d1717 261e1e 352d2d 514444'.split()]
GN=[H(c) for c in '0b2b13 10381a 2a461b 465e24'.split()]
OR=H('c27a2d'); RD=[H(c) for c in '380b04 701508 e02a11'.split()]
def fam(c):
    if c[3]==0: return None
    if c==K: return 'k'
    if c in BR or c in BR_X: return 'b'
    if c in GR: return 'g'
    return 'x'
P={i:Image.open(f'{SRC}n{i}.png').convert('RGBA') for i in range(1,6)}
def crop(im): return im.crop(im.getbbox())
def twin(im):
    """mirrored silhouette, source light direction restored inside every row run"""
    M=ImageOps.mirror(im); w,h=im.size; m=M.load(); o=im.load(); out=M.copy(); q=out.load()
    for y in range(h):
        x=0
        while x<w:
            if m[x,y][3]==0: x+=1; continue
            a=x
            while x<w and m[x,y][3]: x+=1
            b=x-1
            for k in range(b-a+1):
                src=o[w-1-b+k,y]; cur=m[a+k,y]
                if fam(src)==fam(cur) and fam(cur) in ('b','g'): q[a+k,y]=src
    return out

ARM=crop(P[1].rotate(90,expand=True))     # upright: shoulder top, elbow, forearm, fist bottom
LEG=crop(P[3].rotate(-90,expand=True))    # upright: hip top, knee, shin, claw foot bottom
PAD=crop(P[5]); HEAD=P[2]

W,Hh=84,100
cv=Image.new('RGBA',(W,Hh)); px=cv.load()

def segment(src,r0,r1,Pp,Dp,width_scale=1.0):
    """map source rows r0..r1 (upright, proximal at top) onto the posed segment Pp->Dp"""
    ax,ay=Dp[0]-Pp[0],Dp[1]-Pp[1]; L=math.hypot(ax,ay); ax/=L; ay/=L
    nx,ny=-ay,ax
    if nx+ny<0: nx,ny=-nx,-ny                         # +n points away from the upper-left light
    sw=src.width; sp=src.load(); half=sw/2*width_scale
    xs=[Pp[0],Dp[0]]; ys=[Pp[1],Dp[1]]
    for y in range(int(min(ys)-sw),int(max(ys)+sw)+1):
        for x in range(int(min(xs)-sw),int(max(xs)+sw)+1):
            dx,dy=x+0.5-Pp[0],y+0.5-Pp[1]
            t=dx*ax+dy*ay; s=dx*nx+dy*ny
            if not (0<=t<L) or not (-half<=s<half): continue
            sx=int((s+half)/width_scale); sy=r0+int(t*(r1-r0)/L)
            if 0<=sx<sw and r0<=sy<r1:
                c=sp[sx,sy]
                if c[3] and 0<=x<W and 0<=y<Hh: px[x,y]=c
def paste(im,x,y): cv.alpha_composite(im,(x,y))
def region_fill(src,rect,dst_box):
    """fill a box by sampling a source rect (nearest), for plates the source set has no direct part for"""
    sx0,sy0,sx1,sy1=rect; dx0,dy0,dx1,dy1=dst_box; sp=src.load()
    out=Image.new('RGBA',(dx1-dx0,dy1-dy0)); op=out.load()
    for y in range(dy1-dy0):
        for x in range(dx1-dx0):
            op[x,y]=sp[sx0+x*(sx1-sx0)//(dx1-dx0), sy0+y*(sy1-sy0)//(dy1-dy0)]
    return out
def shape(im,mask_fn):
    q=im.load()
    for y in range(im.height):
        for x in range(im.width):
            if not mask_fn(x,y): q[x,y]=(0,0,0,0)
    return im
def outline(im):
    """1px black silhouette outline, as every source sprite has"""
    q=im.load(); w,h=im.size; add=[]
    for y in range(h):
        for x in range(w):
            if q[x,y][3]==0 and any(0<=x+dx<w and 0<=y+dy<h and q[x+dx,y+dy][3] for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))):
                add.append((x,y))
    for p in add: q[p]=K
    return im

cx=42
def rows(im,r0,r1): return im.crop((0,r0,im.width,r1))
# ---------------- legs: planted wide, kneecaps outward, source pixels untouched ----------------
legL,legR=twin(LEG),LEG
paste(legL,cx-21,52); paste(legR,cx+3,52)
# ---------------- waist: the source elbow mechanism ----------------
paste(outline(rows(ARM,15,21).crop((4,0,15,6))),cx-5,40)
# ---------------- pelvis: source plate laid across ----------------
pel=region_fill(ARM.rotate(90,expand=True),(4,3,24,12),(0,0,20,8))
pel=outline(shape(pel,lambda x,y: abs(x-9.5)<=9.5-max(0,y-4)*1.5))
paste(pel,cx-10,46)
# ---------------- arms: upper arm + elbow hang from the shoulder ----------------
armL,armR=twin(ARM),ARM
uL,uR=rows(armL,0,22),rows(armR,0,22)
paste(uL,cx-31,21); paste(uR,cx+15,21)
# ---------------- chest: two 1:1 plates of the source upper-arm armour, each lit upper-left ----------------
plate=rows(ARM,1,15).crop((0,0,15,14))
chest=Image.new('RGBA',(30,18))
chest.alpha_composite(plate,(0,0)); chest.alpha_composite(plate,(15,0))
chest.alpha_composite(rows(ARM,1,5).crop((1,0,15,4)),(1,14)); chest.alpha_composite(rows(ARM,1,5).crop((1,0,15,4)),(15,14))
chest=shape(chest,lambda x,y: abs(x-14.5)<=15-max(0,y-9)*1.1 and not (y<1 and abs(x-14.5)>12))
cq=chest.load()
for y in range(0,14):
    if cq[14,y][3]: cq[14,y]=BR[0]
    if cq[15,y][3]: cq[15,y]=K
for x in range(0,30):
    if cq[x,13][3]: cq[x,13]=BR[0]
LOGO=["#########..","##########.","........##.",".###.####..","#.###.##...","##.###.##..","##..###.##.","##...###.##","##....###.#"]
for j,row in enumerate(LOGO):
    for i,ch in enumerate(row):
        if ch=='#': cq[10+i,2+j]=RD[2] if j<7 else RD[1]
paste(outline(chest),cx-15,20)
# ---------------- head: source face panel, eye socket centred, ear fins; 2px neck ----------------
hp=HEAD.load()
face=Image.new('RGBA',(18,9)); fq=face.load()
cols=list(range(8,13))+list(range(1,8))+list(range(13,19))
for i,sx in enumerate(cols):
    for j,sy in enumerate(range(6,15)):
        c=hp[sx,sy]
        if c[3]: fq[i,j]=c
for j in range(9):
    for i in (0,17):
        if fq[i,j][3]: fq[i,j]=K
head=Image.new('RGBA',(20,16)); head.alpha_composite(face,(1,6))
for (sx0,sx1,dx) in ((10,15,2),(16,21,13)):
    for y in range(1,7):
        for x in range(sx0,sx1):
            c=hp[x,y]
            if c[3]: head.putpixel((dx+x-sx0,y-1),c)
head=outline(crop(head))
neck=outline(rows(ARM,16,18).crop((7,0,13,2)))
paste(neck,cx-3,17)
paste(head,cx-9,3)
# ---------------- pauldrons ----------------
paste(PAD,cx-30,15); paste(twin(PAD),cx+16,15)
# ---------------- fists: forearms point at the viewer, knuckles forward just inside the elbows ----------------
fist=crop(rows(ARM,30,ARM.height))
paste(twin(fist),cx-25,40); paste(fist,cx+13,40)

outline(cv)
GREY={'261209':'2b2626','3d1f12':'3a3333','4f2c19':'4a4242','502c1a':'4a4242','623921':'5a5151',
      '704325':'675d5c','84512f':'7a706e','8d5936':'807573','aa6e46':'9c908c','cea173':'bfb5af','e2cc98':'ddd5cf',
      '0b2b13':'380b04','10381a':'380b04','2a461b':'701508','465e24':'701508','c27a2d':'e02a11'}
GREY={H(k):H(v) for k,v in GREY.items()}
for y in range(Hh):
    for x in range(W):
        c=px[x,y]
        if c[3] and c in GREY: px[x,y]=GREY[c]
o=crop(cv); out=Image.new('RGBA',(o.width+2,o.height+2)); out.alpha_composite(o,(1,1))
out.save(OUT+'robot_1x.png')
out.resize((out.width*3,out.height*3),Image.NEAREST).save(OUT+'robot_3x.png')
bg=Image.new('RGBA',out.size,(200,200,200,255)); bg.alpha_composite(out)
bg.resize((out.width*6,out.height*6),Image.NEAREST).save(OUT+'robot_6x_preview.png')
print(out.size)
