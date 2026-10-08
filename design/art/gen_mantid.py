"""Generate the MANTID-7 insectoid combat robot illustration as SVG.

Grey-and-red armoured insect drone in a crouched strike stance, in the grim
industrial sci-fi look of Quasimorph. Run: python3 gen_mantid.py > mantid.svg
"""
import math
import random

random.seed(7)
W, H = 1400, 1000

# Palette
G0, G1, G2, G3, G4, G5, G6 = "#121417", "#1e2125", "#2c3036", "#3f444b", "#585e66", "#7b828b", "#aab0b8"
R0, R1, R2, R3, GLOW = "#3a0808", "#6e1010", "#a3181a", "#d22a24", "#ff4630"

out = []


def add(s):
    out.append(s)


def pt(p):
    return f"{p[0]:.1f},{p[1]:.1f}"


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def norm(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy) or 1
    return (-dy / l, dx / l), (dx / l, dy / l), l


def taper(a, b, w1, w2, bulge=0.0):
    """Polygon for a tapered limb segment, optionally bulging mid-way."""
    n, _, _ = norm(a, b)
    pts = []
    steps = 8
    for i in range(steps + 1):
        t = i / steps
        w = (w1 + (w2 - w1) * t) / 2 + bulge * math.sin(math.pi * t)
        c = lerp(a, b, t)
        pts.append((c[0] + n[0] * w, c[1] + n[1] * w))
    for i in range(steps, -1, -1):
        t = i / steps
        w = (w1 + (w2 - w1) * t) / 2 + bulge * math.sin(math.pi * t)
        c = lerp(a, b, t)
        pts.append((c[0] - n[0] * w, c[1] - n[1] * w))
    return " ".join(pt(p) for p in pts)


def bolt(p, r=2.6, dark=False):
    add(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{r}" fill="{G1 if dark else G2}"/>'
        f'<circle cx="{p[0]-r*0.3:.1f}" cy="{p[1]-r*0.3:.1f}" r="{r*0.45:.1f}" fill="{G5 if not dark else G4}"/>')


def scratches(a, b, w, n=6, col=G6, op=0.35):
    nrm, d, l = norm(a, b)
    for _ in range(n):
        t = random.uniform(0.1, 0.9)
        o = random.uniform(-w / 2.6, w / 2.6)
        c = lerp(a, b, t)
        c = (c[0] + nrm[0] * o, c[1] + nrm[1] * o)
        ln = random.uniform(4, 14)
        ang = random.uniform(-0.6, 0.6)
        dx = d[0] * math.cos(ang) - d[1] * math.sin(ang)
        dy = d[0] * math.sin(ang) + d[1] * math.cos(ang)
        add(f'<line x1="{c[0]:.1f}" y1="{c[1]:.1f}" x2="{c[0]+dx*ln:.1f}" y2="{c[1]+dy*ln:.1f}" '
            f'stroke="{col}" stroke-width="0.8" opacity="{op}"/>')


def piston(a, b, off, far=False):
    nrm, _, _ = norm(a, b)
    a2 = (a[0] + nrm[0] * off, a[1] + nrm[1] * off)
    b2 = (b[0] + nrm[0] * off, b[1] + nrm[1] * off)
    m = lerp(a2, b2, 0.55)
    add(f'<line x1="{pt(a2).split(",")[0]}" y1="{a2[1]:.1f}" x2="{m[0]:.1f}" y2="{m[1]:.1f}" '
        f'stroke="{G1}" stroke-width="{9 if not far else 7}" stroke-linecap="round"/>')
    add(f'<line x1="{a2[0]:.1f}" y1="{a2[1]:.1f}" x2="{m[0]:.1f}" y2="{m[1]:.1f}" '
        f'stroke="{G4 if not far else G3}" stroke-width="{6 if not far else 4.5}" stroke-linecap="round"/>')
    add(f'<line x1="{m[0]:.1f}" y1="{m[1]:.1f}" x2="{b2[0]:.1f}" y2="{b2[1]:.1f}" '
        f'stroke="{G6 if not far else G4}" stroke-width="{3 if not far else 2.4}" stroke-linecap="round"/>')
    bolt(a2, 3.2, far)
    bolt(b2, 3.2, far)


def cables(a, b, sag, col, w=2.2, n=2):
    for i in range(n):
        off = i * 4
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + sag + off
        add(f'<path d="M{a[0]:.1f},{a[1]+off:.1f} Q{mx:.1f},{my:.1f} {b[0]:.1f},{b[1]+off:.1f}" '
            f'fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>')


def leg(hip, knee, foot, far=False):
    s = 0.82 if far else 1.0
    base = G2 if far else G3
    plate = G3 if far else G4
    hi = G4 if far else G6
    red = R1 if far else R2
    # hydraulic lines behind the limb
    cables(hip, knee, 18 * s, G1, 2.4 * s)
    cables(knee, lerp(knee, foot, 0.4), 10 * s, R0 if far else R1, 2 * s, 1)
    # coxa
    add(f'<circle cx="{hip[0]}" cy="{hip[1]}" r="{24*s:.1f}" fill="{G1}"/>'
        f'<circle cx="{hip[0]}" cy="{hip[1]}" r="{18*s:.1f}" fill="{base}" stroke="{G1}" stroke-width="2"/>')
    # femur
    add(f'<polygon points="{taper(hip, knee, 40*s, 30*s, 7*s)}" fill="{G1}"/>')
    add(f'<polygon points="{taper(hip, knee, 34*s, 24*s, 6*s)}" fill="{base}"/>')
    fa, fb = lerp(hip, knee, 0.12), lerp(hip, knee, 0.86)
    add(f'<polygon points="{taper(fa, fb, 26*s, 18*s, 5*s)}" fill="{plate}" filter="url(#bevel)"/>')
    nrm, _, _ = norm(hip, knee)
    e1, e2 = lerp(fa, fb, 0.05), lerp(fa, fb, 0.95)
    add(f'<line x1="{e1[0]+nrm[0]*-9*s:.1f}" y1="{e1[1]+nrm[1]*-9*s:.1f}" x2="{e2[0]+nrm[0]*-7*s:.1f}" '
        f'y2="{e2[1]+nrm[1]*-7*s:.1f}" stroke="{hi}" stroke-width="1.4" opacity="0.7"/>')
    # red warning band on femur
    ra, rb = lerp(hip, knee, 0.55), lerp(hip, knee, 0.68)
    add(f'<polygon points="{taper(ra, rb, 27*s, 25*s)}" fill="{red}"/>')
    for t in (0.58, 0.64):
        c = lerp(hip, knee, t)
        add(f'<line x1="{c[0]+nrm[0]*12*s:.1f}" y1="{c[1]+nrm[1]*12*s:.1f}" x2="{c[0]-nrm[0]*12*s:.1f}" '
            f'y2="{c[1]-nrm[1]*12*s:.1f}" stroke="{G1}" stroke-width="2.2" opacity="0.8"/>')
    for t in (0.2, 0.42, 0.8):
        bolt(lerp(hip, knee, t), 2.2 * s, far)
    scratches(hip, knee, 26 * s, 7)
    # tibia
    ankle = lerp(knee, foot, 0.86)
    add(f'<polygon points="{taper(knee, ankle, 32*s, 12*s, 4*s)}" fill="{G1}"/>')
    add(f'<polygon points="{taper(knee, ankle, 26*s, 8*s, 3*s)}" fill="{base}"/>')
    ta, tb = lerp(knee, ankle, 0.1), lerp(knee, ankle, 0.7)
    add(f'<polygon points="{taper(ta, tb, 20*s, 11*s, 2*s)}" fill="{plate}" filter="url(#bevel)"/>')
    # serrated spines along the tibia's back edge
    nt, dt, lt = norm(knee, ankle)
    for i in range(5):
        t = 0.25 + i * 0.12
        c = lerp(knee, ankle, t)
        w = (26 - 18 * t) * s / 2
        b0 = (c[0] - nt[0] * w, c[1] - nt[1] * w)
        tip = (b0[0] - nt[0] * 10 * s - dt[0] * 6 * s, b0[1] - nt[1] * 10 * s - dt[1] * 6 * s)
        b1 = (b0[0] + dt[0] * 8 * s, b0[1] + dt[1] * 8 * s)
        add(f'<polygon points="{pt(b0)} {pt(tip)} {pt(b1)}" fill="{G2 if far else G4}" stroke="{G1}" stroke-width="1"/>')
    scratches(knee, ankle, 18 * s, 5)
    # knee joint
    add(f'<circle cx="{knee[0]}" cy="{knee[1]}" r="{20*s:.1f}" fill="{G1}"/>'
        f'<circle cx="{knee[0]}" cy="{knee[1]}" r="{15*s:.1f}" fill="{plate}" filter="url(#bevel)"/>'
        f'<circle cx="{knee[0]}" cy="{knee[1]}" r="{6*s:.1f}" fill="{red}" stroke="{G1}" stroke-width="2"/>')
    for k in range(6):
        a = k * math.pi / 3
        bolt((knee[0] + math.cos(a) * 11 * s, knee[1] + math.sin(a) * 11 * s), 1.6 * s, far)
    piston(lerp(hip, knee, 0.35), lerp(knee, foot, 0.28), -16 * s, far)
    # ankle + talons
    add(f'<circle cx="{ankle[0]:.1f}" cy="{ankle[1]:.1f}" r="{8*s:.1f}" fill="{G1}"/>'
        f'<circle cx="{ankle[0]:.1f}" cy="{ankle[1]:.1f}" r="{5*s:.1f}" fill="{plate}"/>')
    for ang in (-0.55, 0.0, 0.55):
        c, sn = math.cos(ang), math.sin(ang)
        dx, dy = dt[0] * c - dt[1] * sn, dt[0] * sn + dt[1] * c
        ln = (lt * 0.14 + 22) * s
        tip = (ankle[0] + dx * ln, ankle[1] + dy * ln)
        mid = (ankle[0] + dx * ln * 0.5 + nt[0] * 6 * ang * s * 4, ankle[1] + dy * ln * 0.5)
        add(f'<path d="M{ankle[0]-nt[0]*5*s:.1f},{ankle[1]-nt[1]*5*s:.1f} Q{mid[0]:.1f},{mid[1]:.1f} {pt(tip)} '
            f'Q{mid[0]+3:.1f},{mid[1]:.1f} {ankle[0]+nt[0]*5*s:.1f},{ankle[1]+nt[1]*5*s:.1f} Z" '
            f'fill="{G2 if far else G5}" stroke="{G0}" stroke-width="1.5"/>')
    if not far:
        add(f'<ellipse cx="{foot[0]:.1f}" cy="{foot[1]+16:.1f}" rx="34" ry="6" fill="#000" opacity="0.45" filter="url(#blur4)"/>')


def scythe(shoulder, elbow, tip, far=False):
    s = 0.85 if far else 1.0
    base = G2 if far else G3
    plate = G3 if far else G4
    edge = "#8a8f96" if far else "#d9dde2"
    red = R1 if far else R3
    cables(shoulder, elbow, -14 * s, R0 if far else R1, 2.4 * s)
    # upper arm (raptorial femur)
    add(f'<polygon points="{taper(shoulder, elbow, 44*s, 34*s, 9*s)}" fill="{G1}"/>')
    add(f'<polygon points="{taper(shoulder, elbow, 38*s, 28*s, 8*s)}" fill="{base}"/>')
    add(f'<polygon points="{taper(lerp(shoulder, elbow, .1), lerp(shoulder, elbow, .9), 28*s, 20*s, 6*s)}" '
        f'fill="{plate}" filter="url(#bevel)"/>')
    # inner spines on the upper arm (like a mantis's raptorial femur)
    n, d, l = norm(shoulder, elbow)
    for i in range(7):
        t = 0.2 + i * 0.1
        c = lerp(shoulder, elbow, t)
        b0 = (c[0] + n[0] * 18 * s, c[1] + n[1] * 18 * s)
        ln = (16 if i % 2 else 10) * s
        tip2 = (b0[0] + n[0] * ln - d[0] * 4, b0[1] + n[1] * ln - d[1] * 4)
        b1 = (b0[0] + d[0] * 7 * s, b0[1] + d[1] * 7 * s)
        add(f'<polygon points="{pt(b0)} {pt(tip2)} {pt(b1)}" fill="{edge}" stroke="{G1}" stroke-width="1"/>')
    for t in (0.25, 0.5, 0.75):
        bolt(lerp(shoulder, elbow, t), 2.4 * s, far)
    rb = lerp(shoulder, elbow, 0.3), lerp(shoulder, elbow, 0.4)
    add(f'<polygon points="{taper(rb[0], rb[1], 30*s, 29*s)}" fill="{red}" opacity="0.9"/>')
    scratches(shoulder, elbow, 28 * s, 9)
    # blade: curved scythe from elbow to tip, serrated inner edge
    ex, ey = elbow
    tx, ty = tip
    c1 = (ex + (tx - ex) * 0.35, ey - 70 * s)
    c2 = (tx - 10, ty - 120 * s)
    ic1 = (ex + (tx - ex) * 0.45, ey - 10 * s)
    ic2 = (tx - 50 * s, ty - 50 * s)
    add(f'<path d="M{ex-14*s:.1f},{ey-6*s:.1f} C{pt(c1)} {pt(c2)} {tx:.1f},{ty:.1f} '
        f'C{pt(ic2)} {pt(ic1)} {ex+16*s:.1f},{ey+18*s:.1f} Z" fill="{G1}"/>')
    add(f'<path d="M{ex-8*s:.1f},{ey-2*s:.1f} C{c1[0]:.1f},{c1[1]+8:.1f} {c2[0]:.1f},{c2[1]+10:.1f} {tx:.1f},{ty:.1f} '
        f'C{ic2[0]:.1f},{ic2[1]-6:.1f} {ic1[0]:.1f},{ic1[1]-6:.1f} {ex+12*s:.1f},{ey+12*s:.1f} Z" '
        f'fill="url(#{"bladeFar" if far else "blade"})"/>')
    # honed edge highlight along inner curve
    add(f'<path d="M{tx:.1f},{ty:.1f} C{ic2[0]:.1f},{ic2[1]-6:.1f} {ic1[0]:.1f},{ic1[1]-6:.1f} {ex+12*s:.1f},{ey+12*s:.1f}" '
        f'fill="none" stroke="{edge}" stroke-width="{2.4*s:.1f}" opacity="0.9"/>')
    # serration teeth along inner edge
    def cubic(p0, p1, p2, p3, t):
        mt = 1 - t
        return (mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0],
                mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1])
    P = ((tx, ty), (ic2[0], ic2[1] - 6), (ic1[0], ic1[1] - 6), (ex + 12 * s, ey + 12 * s))
    for i in range(9):
        t = 0.32 + i * 0.065
        a = cubic(*P, t)
        b = cubic(*P, t + 0.04)
        nn, _, _ = norm(a, b)
        tipp = ((a[0] + b[0]) / 2 - nn[0] * 9 * s, (a[1] + b[1]) / 2 - nn[1] * 9 * s)
        add(f'<polygon points="{pt(a)} {pt(tipp)} {pt(b)}" fill="{edge}" stroke="{G1}" stroke-width="0.8"/>')
    # fuller groove + glowing heat channel
    g1 = (ex + (tx - ex) * 0.2, ey - 20 * s)
    g2 = (ex + (tx - ex) * 0.7, ty - 60 * s)
    add(f'<path d="M{pt(g1)} Q{c1[0]+20:.1f},{c1[1]+30:.1f} {pt(g2)}" fill="none" stroke="{G1}" stroke-width="{5*s:.1f}" stroke-linecap="round"/>')
    add(f'<path d="M{pt(g1)} Q{c1[0]+20:.1f},{c1[1]+30:.1f} {pt(g2)}" fill="none" stroke="{GLOW if not far else R2}" '
        f'stroke-width="{2*s:.1f}" stroke-linecap="round" filter="url(#glow)"/>')
    # elbow joint
    add(f'<circle cx="{ex}" cy="{ey}" r="{24*s:.1f}" fill="{G1}"/>'
        f'<circle cx="{ex}" cy="{ey}" r="{18*s:.1f}" fill="{plate}" filter="url(#bevel)"/>'
        f'<circle cx="{ex}" cy="{ey}" r="{8*s:.1f}" fill="{red}" stroke="{G1}" stroke-width="2"/>')
    for k in range(8):
        a = k * math.pi / 4
        bolt((ex + math.cos(a) * 13 * s, ey + math.sin(a) * 13 * s), 1.5 * s, far)
    # shoulder ball
    add(f'<circle cx="{shoulder[0]}" cy="{shoulder[1]}" r="{26*s:.1f}" fill="{G1}"/>'
        f'<circle cx="{shoulder[0]}" cy="{shoulder[1]}" r="{20*s:.1f}" fill="{base}" filter="url(#bevel)"/>')
    piston(lerp(shoulder, elbow, 0.15), lerp(shoulder, elbow, 0.85), 22 * s, far)


# ---------------------------------------------------------------- document
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
add("""<defs>
<radialGradient id="bg" cx="0.58" cy="0.42" r="0.8">
  <stop offset="0" stop-color="#2a2022"/><stop offset="0.45" stop-color="#16171a"/><stop offset="1" stop-color="#08090a"/>
</radialGradient>
<radialGradient id="alarm" cx="0.5" cy="0.5" r="0.5">
  <stop offset="0" stop-color="#ff2a1a" stop-opacity="0.35"/><stop offset="1" stop-color="#ff2a1a" stop-opacity="0"/>
</radialGradient>
<linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#1a1b1e"/><stop offset="1" stop-color="#0c0d0f"/>
</linearGradient>
<linearGradient id="blade" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#6d737b"/><stop offset="0.5" stop-color="#4a4f56"/><stop offset="1" stop-color="#9ca2aa"/>
</linearGradient>
<linearGradient id="bladeFar" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#3e434a"/><stop offset="1" stop-color="#555b63"/>
</linearGradient>
<linearGradient id="hull" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#6c727a"/><stop offset="0.45" stop-color="#454a51"/><stop offset="1" stop-color="#22252a"/>
</linearGradient>
<linearGradient id="hullRed" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#c0221f"/><stop offset="1" stop-color="#5a0c0c"/>
</linearGradient>
<linearGradient id="barrel" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#2a2d32"/><stop offset="0.3" stop-color="#8d939b"/><stop offset="0.6" stop-color="#3d4148"/><stop offset="1" stop-color="#16181b"/>
</linearGradient>
<pattern id="hazard" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <rect width="16" height="16" fill="#a3181a"/><rect width="8" height="16" fill="#1a1b1e"/>
</pattern>
<pattern id="grate" width="6" height="6" patternUnits="userSpaceOnUse">
  <rect width="6" height="6" fill="#16181b"/><rect x="1" y="1" width="4" height="4" fill="#060708"/>
</pattern>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<filter id="bigglow" x="-100%" y="-100%" width="300%" height="300%">
  <feGaussianBlur stdDeviation="10"/>
</filter>
<filter id="blur4"><feGaussianBlur stdDeviation="4"/></filter>
<filter id="blur12" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="12"/></filter>
<filter id="bevel" x="-10%" y="-10%" width="120%" height="120%">
  <feGaussianBlur in="SourceAlpha" stdDeviation="2" result="b"/>
  <feSpecularLighting in="b" surfaceScale="3" specularConstant="0.6" specularExponent="18" lighting-color="#d8dde3" result="s">
    <feDistantLight azimuth="235" elevation="45"/>
  </feSpecularLighting>
  <feComposite in="s" in2="SourceAlpha" operator="in" result="s2"/>
  <feComposite in="SourceGraphic" in2="s2" operator="arithmetic" k1="0" k2="1" k3="0.55" k4="0"/>
</filter>
<filter id="grime" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.035 0.06" numOctaves="4" seed="3" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.12  0 0 0 0 0.09  0 0 0 0 0.07  1.6 0 0 0 -0.75" result="stain"/>
  <feComposite in="stain" in2="SourceAlpha" operator="in" result="s"/>
  <feTurbulence type="fractalNoise" baseFrequency="1.4" numOctaves="2" seed="9" result="f"/>
  <feColorMatrix in="f" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.0 0.8" result="speck"/>
  <feComposite in="speck" in2="SourceAlpha" operator="in" result="sp"/>
  <feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="s"/><feMergeNode in="sp"/></feMerge>
</filter>
<filter id="smoke" x="-30%" y="-30%" width="160%" height="160%">
  <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="4" seed="11"/>
  <feColorMatrix type="matrix" values="0 0 0 0 0.35  0 0 0 0 0.33  0 0 0 0 0.33  0 0 0 1.4 -0.6"/>
  <feComposite in2="SourceGraphic" operator="in"/>
</filter>
<linearGradient id="fadeG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.45" stop-color="#fff" stop-opacity="1"/></linearGradient>
<mask id="fade"><rect x="-50" y="560" width="1500" height="440" fill="url(#fadeG)"/></mask>
<radialGradient id="vign" cx="0.5" cy="0.5" r="0.72">
  <stop offset="0.55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.85"/>
</radialGradient>
<radialGradient id="eye" cx="0.4" cy="0.35" r="0.7">
  <stop offset="0" stop-color="#fff3d6"/><stop offset="0.25" stop-color="#ff6a3d"/><stop offset="0.7" stop-color="#d2160f"/><stop offset="1" stop-color="#4a0505"/>
</radialGradient>
</defs>""")

# ---------------------------------------------------------------- environment
add(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
# bulkhead wall panels
for i in range(9):
    x = i * 165 - 20
    add(f'<rect x="{x}" y="60" width="158" height="600" fill="#1b1c20" stroke="#0b0c0e" stroke-width="4"/>')
    add(f'<rect x="{x+12}" y="80" width="134" height="250" fill="#18191c" stroke="#25272b" stroke-width="2"/>')
    add(f'<rect x="{x+12}" y="350" width="134" height="290" fill="url(#grate)" opacity="0.6"/>')
    for yy in (70, 650):
        for xx in (x + 8, x + 150):
            add(f'<circle cx="{xx}" cy="{yy}" r="3" fill="#2a2c31"/>')
# pipes along the wall
for y, r in ((40, 14), (78, 8), (300, 10)):
    add(f'<rect x="0" y="{y-r}" width="{W}" height="{r*2}" fill="#202226"/>'
        f'<rect x="0" y="{y-r+2}" width="{W}" height="{r*0.6:.0f}" fill="#34373c" opacity="0.7"/>')
    for x in range(60, W, 230):
        add(f'<rect x="{x}" y="{y-r-3}" width="16" height="{r*2+6}" fill="#151619"/>')
# hazard stencil and alarm lights
add('<rect x="0" y="660" width="1400" height="18" fill="url(#hazard)" opacity="0.5"/>')
add('<text x="118" y="250" font-family="Impact, Arial Narrow, sans-serif" font-size="74" fill="#2a2b2f" letter-spacing="6">C-17</text>')
add('<text x="1090" y="245" font-family="Arial Narrow, sans-serif" font-size="22" fill="#5a1515" letter-spacing="3" opacity="0.8">⚠ QUARANTINE</text>')
add('<text x="1090" y="272" font-family="Arial Narrow, sans-serif" font-size="14" fill="#3c3e43" letter-spacing="2">SECTOR 7 · DECK B</text>')
for x in (250, 1150):
    add(f'<circle cx="{x}" cy="120" r="220" fill="url(#alarm)"/>')
    add(f'<rect x="{x-22}" y="104" width="44" height="26" rx="5" fill="#2a0c0c" stroke="#111" stroke-width="3"/>'
        f'<rect x="{x-16}" y="108" width="32" height="16" rx="4" fill="{GLOW}" filter="url(#glow)"/>')
# floor
add(f'<polygon points="0,678 {W},678 {W},{H} 0,{H}" fill="url(#floor)"/>')
for i in range(-6, 16):
    x0 = 700 + (i - 5) * 70
    x1 = 700 + (i - 5) * 210
    add(f'<line x1="{x0}" y1="678" x2="{x1}" y2="{H}" stroke="#25272b" stroke-width="2"/>')
for y in (700, 735, 785, 850, 940):
    add(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#222428" stroke-width="2"/>')
# red light pooling on the floor
add('<ellipse cx="660" cy="860" rx="520" ry="110" fill="#5a0d0d" opacity="0.25" filter="url(#blur12)"/>')
# debris and spent casings
for _ in range(26):
    x, y = random.uniform(80, 1320), random.uniform(820, 980)
    a = random.uniform(0, 180)
    add(f'<rect x="{x:.0f}" y="{y:.0f}" width="12" height="4.5" rx="1.5" fill="#8a6a2c" stroke="#3a2a0e" stroke-width="1" '
        f'transform="rotate({a:.0f} {x:.0f} {y:.0f})"/>')
for _ in range(14):
    x, y = random.uniform(60, 1340), random.uniform(800, 990)
    pts = " ".join(pt((x + random.uniform(-14, 14), y + random.uniform(-6, 6))) for _ in range(5))
    add(f'<polygon points="{pts}" fill="#26282c" stroke="#121315" stroke-width="1"/>')
# scorch marks
add('<ellipse cx="1120" cy="900" rx="120" ry="24" fill="#050505" opacity="0.6" filter="url(#blur4)"/>')
add('<ellipse cx="640" cy="905" rx="430" ry="48" fill="#000" opacity="0.6" filter="url(#blur12)"/>')

# ---------------------------------------------------------------- robot
add('<g filter="url(#grime)">')

# far-side legs and arm (darker, partly behind the body)
leg((715, 520), (930, 395), (1075, 835), far=True)
leg((620, 528), (760, 600), (835, 860), far=True)
leg((470, 515), (270, 380), (150, 815), far=True)
scythe((760, 420), (885, 250), (1120, 345), far=True)

# abdomen: segmented armoured hull, tilted up toward the rear
add('<g transform="rotate(-11 380 480)">')
add('<ellipse cx="370" cy="482" rx="196" ry="108" fill="#0f1012"/>')
add('<ellipse cx="370" cy="478" rx="188" ry="100" fill="url(#hull)"/>')
for i, x in enumerate((230, 290, 350, 410, 470)):
    rx = 30
    add(f'<path d="M{x},{392 + abs(i-2)*6} Q{x+rx},{480} {x},{570 - abs(i-2)*6}" fill="none" stroke="#14161a" stroke-width="5"/>')
    add(f'<path d="M{x+4},{396 + abs(i-2)*6} Q{x+rx+4},{480} {x+4},{566 - abs(i-2)*6}" fill="none" stroke="#7b828b" stroke-width="1.4" opacity="0.6"/>')
# dorsal red armour shell
add('<path d="M205,430 Q260,372 380,368 Q500,370 548,420 Q470,402 380,404 Q270,408 205,430 Z" fill="url(#hullRed)" stroke="#1a0606" stroke-width="2"/>')
add('<path d="M240,412 Q320,384 380,384 Q460,384 520,410" fill="none" stroke="#ff6a4a" stroke-width="1.5" opacity="0.5"/>')
# heat vents with glow
for i in range(5):
    x = 250 + i * 48
    add(f'<rect x="{x}" y="500" width="30" height="34" rx="3" fill="#0a0a0b" stroke="#2a2d32" stroke-width="2"/>')
    for k in range(4):
        add(f'<rect x="{x+3}" y="{504+k*8}" width="24" height="3" fill="{GLOW}" opacity="{0.55 - k*0.1:.2f}"/>')
    add(f'<rect x="{x}" y="500" width="30" height="34" fill="{GLOW}" opacity="0.18" filter="url(#bigglow)"/>')
# stinger / sensor tail at rear
add('<polygon points="185,470 120,452 60,470 120,494 190,500" fill="#2b2e33" stroke="#0e0f11" stroke-width="3"/>')
add('<polygon points="62,470 22,466 62,476" fill="#c9cdd2"/>')
add(f'<circle cx="120" cy="472" r="6" fill="{GLOW}" filter="url(#glow)"/>')
add('<rect x="300" y="545" width="120" height="16" fill="url(#hazard)" stroke="#0e0f11" stroke-width="2"/>')
add('</g>')
for p in ((270, 420), (330, 410), (440, 405), (240, 520), (500, 520)):
    bolt(p, 2.6)

# ammo belt from abdomen to the dorsal cannon
belt = [(470, 430), (500, 395), (540, 372), (575, 362)]
for i in range(len(belt) - 1):
    a, b = belt[i], belt[i + 1]
    for t in (0, 0.33, 0.66):
        c = lerp(a, b, t)
        add(f'<rect x="{c[0]-5:.1f}" y="{c[1]-9:.1f}" width="10" height="18" rx="2" fill="#a17e36" stroke="#3a2a0e" stroke-width="1.5"/>'
            f'<rect x="{c[0]-5:.1f}" y="{c[1]-9:.1f}" width="10" height="5" fill="#c98e2f"/>')

# thorax: heavy armoured core
add('<path d="M520,420 L560,385 L705,378 L770,415 L780,520 L735,585 L560,592 L515,540 Z" fill="#0e0f11"/>')
add('<path d="M528,424 L564,392 L702,386 L762,420 L770,518 L728,577 L564,584 L524,537 Z" fill="url(#hull)"/>')
add('<path d="M560,400 L700,394 L748,424 L745,470 L575,478 L548,445 Z" fill="#555b63" filter="url(#bevel)" stroke="#16181b" stroke-width="2"/>')
add('<path d="M575,478 L745,470 L752,520 L720,560 L585,566 L555,530 Z" fill="#3a3e45" filter="url(#bevel)" stroke="#16181b" stroke-width="2"/>')
# red chest plate with stencil
add('<path d="M600,486 L720,482 L726,520 L705,548 L610,551 L594,520 Z" fill="url(#hullRed)" stroke="#170505" stroke-width="2"/>')
add('<text x="612" y="527" font-family="Impact, Arial Narrow, sans-serif" font-size="27" fill="#1a1b1e" opacity="0.85" letter-spacing="2">MT-7</text>')
add('<rect x="610" y="534" width="90" height="8" fill="url(#hazard)" opacity="0.9"/>')
# panel lines and vents on the thorax top
for x in range(590, 720, 14):
    add(f'<rect x="{x}" y="412" width="8" height="40" rx="2" fill="#1d1f23"/><rect x="{x+1}" y="413" width="2" height="38" fill="#7b828b" opacity="0.4"/>')
for p in ((570, 405), (695, 398), (740, 430), (560, 440), (740, 465), (575, 560), (715, 555), (535, 520)):
    bolt(p, 3)
scratches((540, 450), (760, 450), 120, 40, op=0.3)
# power core window
add(f'<circle cx="565" cy="505" r="20" fill="#0a0a0b" stroke="#2b2e33" stroke-width="4"/>'
    f'<circle cx="565" cy="505" r="13" fill="{GLOW}" filter="url(#glow)"/>'
    f'<circle cx="565" cy="505" r="40" fill="{GLOW}" opacity="0.25" filter="url(#bigglow)"/>'
    f'<path d="M552,505 L578,505 M565,492 L565,518" stroke="#2a0606" stroke-width="3"/>')

# dorsal twin autocannon on a gimbal
add('<path d="M570,392 L610,350 L700,348 L725,388 Z" fill="#0e0f11"/>')
add('<path d="M578,388 L614,356 L696,354 L716,386 Z" fill="#4a4f56" filter="url(#bevel)"/>')
add('<rect x="600" y="300" width="140" height="62" rx="8" fill="#0e0f11"/>')
add('<rect x="605" y="305" width="130" height="52" rx="6" fill="url(#hull)"/>')
add('<rect x="612" y="311" width="62" height="18" fill="url(#hullRed)" stroke="#170505" stroke-width="1.5"/>')
add('<text x="616" y="325" font-family="Arial Narrow, sans-serif" font-size="12" fill="#f2d4cc" letter-spacing="1">20MM</text>')
for p in ((612, 345), (728, 312), (728, 348), (688, 345)):
    bolt(p, 2.4)
for y in (316, 340):
    add(f'<rect x="730" y="{y-8}" width="190" height="16" rx="3" fill="#0e0f11"/>')
    add(f'<rect x="732" y="{y-6}" width="186" height="12" rx="2" fill="url(#barrel)"/>')
    for x in range(760, 880, 18):
        add(f'<rect x="{x}" y="{y-7}" width="8" height="14" fill="#1a1c1f" opacity="0.8"/>')
    add(f'<rect x="900" y="{y-10}" width="34" height="20" rx="3" fill="#2b2e33" stroke="#0e0f11" stroke-width="2"/>')
    for k in range(3):
        add(f'<rect x="{905+k*9}" y="{y-10}" width="4" height="20" fill="#0a0a0b"/>')
add('<rect x="740" y="322" width="150" height="12" fill="#1a1c1f"/>')
# targeting laser
add(f'<line x1="936" y1="328" x2="1400" y2="372" stroke="{GLOW}" stroke-width="1.4" opacity="0.7" filter="url(#glow)"/>')
add(f'<rect x="690" y="290" width="36" height="14" rx="3" fill="#1e2125" stroke="#0e0f11" stroke-width="2"/>'
    f'<circle cx="718" cy="297" r="4" fill="{GLOW}" filter="url(#glow)"/>')

# neck: segmented collar linking thorax to head
add('<polygon points="%s" fill="#0e0f11"/>' % taper((760, 462), (858, 476), 58, 48))
add('<polygon points="%s" fill="#3f444b" filter="url(#bevel)"/>' % taper((764, 462), (854, 476), 50, 40))
for x in (782, 806, 830):
    add(f'<line x1="{x}" y1="{442+(x-760)*0.14:.0f}" x2="{x+3}" y2="{486+(x-760)*0.14:.0f}" stroke="#121417" stroke-width="4"/>')
cables((770, 486), (850, 496), 10, R2, 2.6, 2)
# head: armoured wedge with compound optic cluster and mandibles
add('<g transform="translate(92 14)">')
add('<path d="M748,420 L820,402 L905,430 L935,470 L900,512 L812,520 L758,492 Z" fill="#0e0f11"/>')
add('<path d="M756,424 L820,410 L898,434 L924,470 L894,505 L814,512 L764,488 Z" fill="url(#hull)"/>')
add('<path d="M770,425 L820,414 L892,438 L870,452 L800,448 Z" fill="#7b828b" filter="url(#bevel)" stroke="#16181b" stroke-width="1.5"/>')
add('<path d="M800,448 L870,452 L892,438 L918,470 L878,470 L812,470 Z" fill="#1a1b1e"/>')
# optic cluster
for (cx, cy, r) in ((832, 462, 11), (862, 464, 9), (888, 466, 7), (816, 482, 6), (848, 486, 5), (874, 486, 4)):
    add(f'<circle cx="{cx}" cy="{cy}" r="{r+3}" fill="#0a0a0b"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#eye)" filter="url(#glow)"/>')
add(f'<ellipse cx="855" cy="470" rx="70" ry="30" fill="{GLOW}" opacity="0.3" filter="url(#bigglow)"/>')
add('<path d="M780,494 L900,500" stroke="url(#hazard)" stroke-width="8"/>')
for p in ((775, 432), (808, 420), (790, 500)):
    bolt(p, 2.2)
# antennae
add('<path d="M800,416 Q760,330 700,262" fill="none" stroke="#111" stroke-width="4"/>'
    '<path d="M800,416 Q760,330 700,262" fill="none" stroke="#7b828b" stroke-width="2"/>'
    f'<circle cx="700" cy="262" r="4" fill="{GLOW}" filter="url(#glow)"/>')
add('<path d="M830,414 Q820,320 790,240" fill="none" stroke="#111" stroke-width="3.5"/>'
    '<path d="M830,414 Q820,320 790,240" fill="none" stroke="#585e66" stroke-width="1.6"/>'
    f'<circle cx="790" cy="240" r="3" fill="{GLOW}" filter="url(#glow)"/>')
# mandibles
add('<path d="M880,505 Q930,525 958,505 Q940,540 900,535 Q875,528 868,512 Z" fill="#9aa0a8" stroke="#0e0f11" stroke-width="2.5"/>')
add('<path d="M845,512 Q900,560 940,548 Q910,575 868,560 Q840,545 835,520 Z" fill="#c3c8cf" stroke="#0e0f11" stroke-width="2.5"/>')
for x in (890, 905, 920):
    add(f'<polygon points="{x},{548+(x-890)*0.2:.0f} {x+5},{540+(x-890)*0.2:.0f} {x+9},{550+(x-890)*0.2:.0f}" fill="#e8eaed" stroke="#0e0f11" stroke-width="0.8"/>')
add('</g>')

# near legs (rear to front so the front leg overlaps)
leg((500, 560), (300, 450), (210, 900))
leg((610, 575), (690, 700), (585, 925))
leg((700, 560), (850, 575), (1010, 905))

# near raptorial scythe arm, raised to strike
scythe((735, 455), (835, 275), (1080, 400))

add('</g>')  # end grime

# ---------------------------------------------------------------- atmosphere
# muzzle smoke and heat shimmer
add('<rect x="-50" y="560" width="1500" height="440" fill="#fff" filter="url(#smoke)" opacity="0.22" mask="url(#fade)"/>')
# sparks from the blade edge
for _ in range(40):
    x, y = random.gauss(1060, 50), random.gauss(400, 40)
    l = random.uniform(4, 16)
    a = random.uniform(-0.4, 1.4)
    add(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x+math.cos(a)*l:.1f}" y2="{y+math.sin(a)*l:.1f}" '
        f'stroke="{random.choice(["#ffd27a", "#ff8a3d", GLOW])}" stroke-width="{random.uniform(0.8, 2):.1f}" stroke-linecap="round" filter="url(#glow)"/>')
# drifting embers
for _ in range(60):
    x, y = random.uniform(0, W), random.uniform(0, H)
    add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{random.uniform(0.6, 2):.1f}" fill="#ff6a3d" opacity="{random.uniform(0.2, 0.7):.2f}"/>')
# red key light wash from the right
add('<rect width="1400" height="1000" fill="#ff1a0a" opacity="0.06" style="mix-blend-mode:screen"/>')
add(f'<rect width="{W}" height="{H}" fill="url(#vign)"/>')
# scanline overlay
add('<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity="0.18"/></pattern>')
add(f'<rect width="{W}" height="{H}" fill="url(#scan)"/>')

# HUD-style dossier label
add('<g font-family="Consolas, DejaVu Sans Mono, monospace">')
add('<rect x="40" y="40" width="360" height="132" fill="#0a0b0c" opacity="0.82" stroke="#5a1515" stroke-width="1.5"/>')
add('<rect x="40" y="40" width="6" height="132" fill="#d22a24"/>')
add('<text x="62" y="76" font-size="30" fill="#e7e9ec" font-weight="bold" letter-spacing="4">MANTID-7</text>')
add('<text x="62" y="100" font-size="13" fill="#d22a24" letter-spacing="2">HOSTILE · CLASS III ASSAULT DRONE</text>')
add('<text x="62" y="124" font-size="12" fill="#7b828b">HULL 340  ARMOR 12  DODGE 18%</text>')
add('<text x="62" y="142" font-size="12" fill="#7b828b">ARMS: MONOEDGE SCYTHE ×2</text>')
add('<text x="62" y="160" font-size="12" fill="#7b828b">       20MM TWIN AUTOCANNON</text>')
add('</g>')
# corner brackets
for (x, y, dx, dy) in ((20, 20, 1, 1), (W - 20, 20, -1, 1), (20, H - 20, 1, -1), (W - 20, H - 20, -1, -1)):
    add(f'<path d="M{x},{y+dy*40} L{x},{y} L{x+dx*40},{y}" fill="none" stroke="#d22a24" stroke-width="3" opacity="0.8"/>')

add("</svg>")
print("\n".join(out))
