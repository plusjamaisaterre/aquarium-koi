#!/usr/bin/env python3
"""Generates the pixel-art aquarium scene (SVG) for the aquarium-koi mod."""
import math, random, sys, json

W, H = 320, 180
OUT = sys.argv[1] if len(sys.argv) > 1 else "scene.svg"

# ---------- helpers ----------
def hx(c):
    c = c.lstrip('#'); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
def tohex(r, g, b):
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(round(v)))) for v in (r, g, b))
def mixc(a, b, t):
    a, b = hx(a), hx(b); return tohex(*(a[i] + (b[i] - a[i]) * t for i in range(3)))
def light(c, t): return mixc(c, '#ffffff', t)
def dark(c, t): return mixc(c, '#000000', t)

def hash2(x, y, s=0):
    n = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xffffffff
    n = (n ^ (n >> 13)) * 1274126177 & 0xffffffff
    return ((n ^ (n >> 16)) & 0xffff) / 65535.0

def vnoise(x, y, scale, s=0):
    fx, fy = x / scale, y / scale
    x0, y0 = math.floor(fx), math.floor(fy)
    tx, ty = fx - x0, fy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = hash2(x0, y0, s); b = hash2(x0 + 1, y0, s)
    c = hash2(x0, y0 + 1, s); d = hash2(x0 + 1, y0 + 1, s)
    return (a + (b - a) * tx) + ((c + (d - c) * tx) - (a + (b - a) * tx)) * ty

def fnum(v):
    s = ('%.2f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s

def pix_paths(px):
    """px: dict (x,y)->color. Emits one stroked path per colour, runs merged."""
    by = {}
    for (x, y), c in px.items():
        if c is None: continue
        by.setdefault(c, []).append((y, x))
    out = []
    for c, pts in sorted(by.items()):
        pts.sort()
        runs = []
        for y, x in pts:
            if runs and runs[-1][0] == y and runs[-1][1] + runs[-1][2] == x:
                runs[-1][2] += 1
            else:
                runs.append([y, x, 1])
        d = []
        cx = cy = None
        for y, x, n in runs:
            if cx is None:
                d.append('M%d %s' % (x, fnum(y + .5)))
            else:
                d.append('m%d %d' % (x - cx, y - cy))
            d.append('h%d' % n)
            cx, cy = x + n, y
        s = ''.join(d)
        s = s.replace(' -', '-')
        out.append('<path stroke="%s" d="%s"/>' % (c, s))
    return ''.join(out)

def outline(px, col, skip_top=False):
    add = {}
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in px and q not in add:
                if skip_top and dy == -1: continue
                add[q] = col
    px.update(add)

# ---------- palette ----------
WATER = ['#6ae6f2', '#4fd0ee', '#3ab6e8', '#2c9ade', '#2380d0', '#1d69bf', '#1956aa', '#164593', '#13397e']
FAR = '#1f6fb8'; FAR2 = '#1b60a6'; FAR3 = '#2a83c8'
ROCK = ['#2e1f38', '#4a3150', '#664462', '#83576b', '#a26e72', '#c48c7c', '#dfb085', '#f3d29c']
SAND = ['#f7e4b0', '#ecd095', '#dfba7c', '#c99d63', '#b08455']

rnd = random.Random(7)
parts = []  # svg strings in order

# ---------- defs & style ----------
CSS = r"""
svg{shape-rendering:crispEdges}
.p path{fill:none;stroke-width:1.04}
.ray{animation:ray 9s ease-in-out infinite alternate}
@keyframes ray{from{opacity:.35}to{opacity:.9}}
.sway{transform-box:fill-box;transform-origin:50% 100%;animation:sway 5s ease-in-out infinite alternate}
@keyframes sway{from{transform:rotate(-4deg)}to{transform:rotate(4deg)}}
.tail{transform-box:fill-box;transform-origin:100% 50%;animation:wag .9s ease-in-out infinite alternate}
@keyframes wag{from{transform:skewY(-14deg) scaleX(.9)}to{transform:skewY(14deg) scaleX(1)}}
.flip{transform-box:fill-box;transform-origin:100% 0%;animation:flap 2.6s ease-in-out infinite alternate}
@keyframes flap{from{transform:rotate(-18deg)}to{transform:rotate(22deg)}}
.bob{animation:bob 4s ease-in-out infinite alternate}
@keyframes bob{from{transform:translateY(-2.5px)}to{transform:translateY(2.5px)}}
.bub{animation:rise 9s linear infinite}
@keyframes rise{0%{transform:translate(0,0);opacity:0}8%{opacity:1}50%{transform:translate(2px,-80px)}92%{opacity:1}100%{transform:translate(-1px,-160px);opacity:0}}
.snow{animation:snow 26s linear infinite}
@keyframes snow{0%{transform:translate(0,0);opacity:0}15%{opacity:.8}85%{opacity:.8}100%{transform:translate(14px,60px);opacity:0}}
.surf{animation:surf 14s linear infinite}
@keyframes surf{from{transform:translateX(0)}to{transform:translateX(-64px)}}
.glow{animation:glow 4.5s ease-in-out infinite alternate}
@keyframes glow{from{opacity:.55}to{opacity:1}}
.caus{animation:caus 6s ease-in-out infinite alternate}
@keyframes caus{from{opacity:.1}to{opacity:.55}}
.jelly{transform-box:fill-box;transform-origin:50% 0%;animation:pulse 3.2s ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scale(1,1)}45%{transform:scale(1.12,.86)}}
.drift{animation:drift 40s ease-in-out infinite alternate}
@keyframes drift{from{transform:translate(0,6px)}to{transform:translate(10px,-18px)}}
.shine{animation:shine 11s ease-in-out infinite alternate}
.petal{transform-box:fill-box;transform-origin:50% 50%;animation:petal 30s linear infinite}
@keyframes petal{0%{transform:translate(0,0) rotate(0deg);opacity:0}6%{opacity:1}25%{transform:translate(10px,40px) rotate(90deg)}50%{transform:translate(-4px,80px) rotate(180deg)}75%{transform:translate(8px,120px) rotate(270deg)}94%{opacity:1}100%{transform:translate(0,160px) rotate(360deg);opacity:0}}
.stem{transform-box:fill-box;transform-origin:50% 0%;animation:stem 7s ease-in-out infinite alternate}
@keyframes stem{from{transform:rotate(-3deg)}to{transform:rotate(3deg)}}
.pel0,.pel1,.pel2{animation:pel0 10s linear 1 both}.pel1{animation-name:pel1}.pel2{animation-name:pel2}
@keyframes pel0{0%{transform:translate(0,-5px);opacity:0}4%{opacity:1}78%{opacity:1}100%{transform:translate(3px,44px);opacity:0}}
@keyframes pel1{0%{transform:translate(0,-5px);opacity:0}4%{opacity:1}70%{opacity:1}100%{transform:translate(-4px,38px);opacity:0}}
@keyframes pel2{0%{transform:translate(0,-5px);opacity:0}4%{opacity:1}84%{opacity:1}100%{transform:translate(1px,50px);opacity:0}}
.sp0,.sp1,.sp2,.sp3{animation:sp0 1.4s ease-out 1 both}.sp1{animation-name:sp1}.sp2{animation-name:sp2}.sp3{animation-name:sp3}
@keyframes sp0{from{transform:translate(0,0);opacity:1}to{transform:translate(-6px,-5px);opacity:0}}
@keyframes sp1{from{transform:translate(0,0);opacity:1}to{transform:translate(6px,-5px);opacity:0}}
@keyframes sp2{from{transform:translate(0,0);opacity:1}to{transform:translate(-5px,5px);opacity:0}}
@keyframes sp3{from{transform:translate(0,0);opacity:1}to{transform:translate(5px,5px);opacity:0}}
.nib{animation:nib .45s ease-in-out infinite alternate}
@keyframes nib{from{transform:translateX(-1px)}to{transform:translateX(1.5px)}}
.eb{animation:eb 3s ease-out 1 both}
@keyframes eb{0%{transform:translate(0,0);opacity:0}10%{opacity:1}100%{transform:translate(2px,-34px);opacity:0}}
.pf0,.pf1,.pf2{transform-box:fill-box;transform-origin:50% 50%;animation:pf0 13s linear 1 both}.pf1{animation-name:pf1}.pf2{animation-name:pf2}
@keyframes pf0{0%{transform:translate(0,-8px) rotate(0deg);opacity:0}5%{opacity:1}30%{transform:translate(9px,30px) rotate(120deg)}60%{transform:translate(-5px,70px) rotate(240deg)}90%{opacity:1}100%{transform:translate(4px,110px) rotate(360deg);opacity:0}}
@keyframes pf1{0%{transform:translate(0,-8px) rotate(0deg);opacity:0}5%{opacity:1}30%{transform:translate(-8px,26px) rotate(-120deg)}60%{transform:translate(6px,62px) rotate(-240deg)}90%{opacity:1}100%{transform:translate(-3px,96px) rotate(-360deg);opacity:0}}
@keyframes pf2{0%{transform:translate(0,-8px) rotate(0deg);opacity:0}5%{opacity:1}30%{transform:translate(5px,34px) rotate(90deg)}60%{transform:translate(-9px,74px) rotate(200deg)}90%{opacity:1}100%{transform:translate(2px,120px) rotate(300deg);opacity:0}}
@keyframes shine{from{opacity:.25}to{opacity:.7}}
"""
swim_css = []

defs = """<defs>
<linearGradient id="gr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fffbe0" stop-opacity=".55"/><stop offset=".6" stop-color="#d8fbff" stop-opacity=".16"/><stop offset="1" stop-color="#d8fbff" stop-opacity="0"/></linearGradient>
<radialGradient id="vg" cx=".5" cy=".42" r=".75"><stop offset=".55" stop-color="#05224a" stop-opacity="0"/><stop offset="1" stop-color="#05224a" stop-opacity=".55"/></radialGradient>
<radialGradient id="pool" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff6cf" stop-opacity=".7"/><stop offset="1" stop-color="#fff6cf" stop-opacity="0"/></radialGradient>
<radialGradient id="lg" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ffd76a" stop-opacity=".85"/><stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient>
</defs>"""

# ---------- water (smooth gradient, like sunlit open water) ----------
stops=''.join('<stop offset="%.3f" stop-color="%s"/>' % (i/(len(WATER)-1), c) for i, c in enumerate(WATER))
defs = defs.replace('</defs>', '<linearGradient id="wa" x1="0" y1="0" x2="0" y2="1">%s</linearGradient></defs>' % stops)
parts.append('<rect width="%d" height="%d" fill="url(#wa)"/>' % (W, H))
# soft sun glow under the surface
defs = defs.replace('</defs>', '<radialGradient id="sun" cx=".5" cy="0" r=".5"><stop offset="0" stop-color="#fffbe0" stop-opacity=".45"/><stop offset="1" stop-color="#fffbe0" stop-opacity="0"/></radialGradient></defs>')
parts.append('<rect x="0" y="-60" width="320" height="170" fill="url(#sun)"/>')

# ---------- far silhouettes ----------
far = {}
def far_ridge(x0, x1, base, amp, col, seed):
    for x in range(x0, x1):
        t = (x - x0) / max(1, (x1 - x0))
        top = base - amp * math.sin(math.pi * t) ** 0.7 - 6 * vnoise(x, 0, 9, seed)
        for y in range(int(top), H):
            far[(x, y)] = col
far_ridge(-5, 120, 150, 60, FAR3, 3)
far_ridge(210, 330, 152, 70, FAR3, 4)
far_ridge(60, 200, 165, 28, FAR, 5)
# shipwreck (own design): tilted hull, broken masts, rigging
def wreck(ox, oy):
    tilt = -0.18
    for x in range(0, 78):
        # hull outline: deck line tilted, keel curve
        deck = oy + x * tilt
        keel = deck + 16 + 6 * math.sin(math.pi * x / 78)
        if x < 8: keel = deck + 16 * (x / 8) + 2
        for y in range(int(deck), int(keel)):
            col = FAR2 if (x + y) % 9 else FAR
            if (y - int(deck)) % 5 == 0: col = '#185595'
            far[(ox + x, y)] = col
        # broken rail
        if x % 4 == 0 and x > 6:
            far[(ox + x, int(deck) - 1)] = FAR2; far[(ox + x, int(deck) - 2)] = FAR2
    # holes in hull
    for (hx_, hy_, r) in ((30, 9, 3), (48, 6, 2.5), (60, 4, 2)):
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                if dx * dx + dy * dy <= r * r:
                    far.pop((ox + hx_ + dx, int(oy + (hx_ + dx) * tilt + hy_ + dy)), None)
    # masts
    for (mx, mh, lean) in ((26, 46, 0.15), (52, 34, -0.12)):
        by_ = oy + mx * tilt
        for k in range(mh):
            xx = ox + mx + int(k * lean)
            far[(xx, int(by_ - k))] = FAR2; far[(xx + 1, int(by_ - k))] = FAR2
        # yard arm
        ya = int(by_ - mh * 0.75)
        for k in range(-9, 10):
            far[(ox + mx + int(mh * .75 * lean) + k, ya + int(k * 0.2))] = FAR2
        # rigging lattice
        for k in range(0, 22):
            far[(ox + mx + k, int(by_ - mh * 0.75 + k * 1.0))] = FAR
            if k % 3 == 0:
                for j in range(0, 22 - k, 3):
                    far[(ox + mx + k, int(by_ - mh * 0.75 + k + j))] = FAR
wreck(206, 132)
def pagoda(cx, base):
    C = '#1d64a8'; C2 = '#2272b8'
    y = base
    for tier in range(5):
        w = 15 - tier * 2
        # walls
        for k in range(4):
            for x in range(cx - w // 2 + 2, cx + w // 2 - 1):
                far[(x, y - k)] = C
        y -= 4
        # roof with upturned eaves
        for x in range(cx - w // 2 - 3, cx + w // 2 + 4):
            far[(x, y)] = C; far[(x, y - 1)] = C2 if abs(x - cx) < w // 2 else C
        far[(cx - w // 2 - 4, y - 1)] = C; far[(cx + w // 2 + 4, y - 1)] = C
        far[(cx - w // 2 - 4, y - 2)] = C; far[(cx + w // 2 + 4, y - 2)] = C
        y -= 2
    for k in range(9): far[(cx, y - k)] = C
    for k in (2, 4, 6): far[(cx - 1, y - k)] = C; far[(cx + 1, y - k)] = C
pagoda(46, 104)
parts.append('<g class="p" opacity=".95">' + pix_paths(far) + '</g>')

# ---------- light rays ----------
rays = []
for i, (x, w, sk, dl) in enumerate(((70, 16, 40, 0), (112, 10, 46, -3), (150, 22, 52, -6), (196, 12, 58, -2), (236, 18, 62, -5), (36, 8, 34, -7), (270, 9, 64, -4))):
    pts = '%d,0 %d,0 %d,%d %d,%d' % (x, x + w, x + w + sk + w, H, x + sk - w // 2, H)
    rays.append('<polygon class="ray" style="animation-delay:%ds;animation-duration:%ds" points="%s" fill="url(#gr)"/>' % (dl, 7 + i % 4 * 2, pts))
parts.append('<g>' + ''.join(rays) + '</g>')
# sand light pool
parts.append('<ellipse cx="160" cy="168" rx="70" ry="14" fill="url(#pool)" class="shine"/>')

# ---------- near rocks, sand, corals ----------
near = {}
def ground(x):
    return 162 + 2.5 * math.sin(x / 17.0) + 1.5 * math.sin(x / 7.3 + 1)
# sand
for x in range(W):
    g = int(ground(x))
    for y in range(g, H):
        n = vnoise(x, y, 7, 11) + 0.12 * hash2(x, y, 3)
        lit = max(0, 1 - abs(x - 160) / 90) * 0.5
        ripple = 0.25 * math.sin(x * 0.5 + y * 1.7)
        v = n + lit + ripple - (y - g) * 0.03
        idx = 4 if v < 0.25 else 3 if v < 0.55 else 2 if v < 0.85 else 1 if v < 1.15 else 0
        near[(x, y)] = SAND[idx]
    near[(x, g)] = SAND[0] if hash2(x, 1, 9) > .3 else SAND[1]
# pebbles
for i in range(26):
    px_, py_ = rnd.randint(0, W - 1), rnd.randint(166, 177)
    col = rnd.choice(['#ff8fb1', '#9b7cff', '#64d6c3', '#ffffff', '#f0a35e', '#8aa0c8'])
    for dx in range(2):
        near[(px_ + dx, py_)] = col
    near[(px_, py_ - 1)] = light(col, .5)
    near[(px_ + 2, py_)] = dark(col, .35)

def rock_blob(cx, cy, rx, ry, seed):
    pts = set()
    for x in range(int(cx - rx - 3), int(cx + rx + 4)):
        for y in range(int(cy - ry - 3), int(cy + ry + 4)):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            d += (vnoise(x, y, 6, seed) - .5) * .55
            # flatten tops into ledges
            if y < cy - ry * .55 and vnoise(x, 0, 11, seed + 1) > .55: d += .25
            if d < 1: pts.add((x, y))
    tops = {}
    for (x, y) in pts:
        if x not in tops or y < tops[x]: tops[x] = y
    blob = {}
    for (x, y) in pts:
        if not (0 <= x < W and 0 <= y < H): continue
        dt = y - tops[x]
        n = vnoise(x, y, 9, seed + 2)
        side = (x - cx) / rx  # light comes from top-left
        if dt < 2: c = ROCK[7] if hash2(x, y, seed) > .35 else ROCK[6]
        elif dt < 3: c = ROCK[6]
        else:
            v = 1 - dt / (ry * 2.2) - side * .25 + (n - .5) * .5
            idx = 5 if v > .85 else 4 if v > .6 else 3 if v > .35 else 2 if v > .1 else 1
            c = ROCK[idx]
            if vnoise(x, y, 4, seed + 7) > .8 and dt > 5: c = ROCK[1]  # cracks
        blob[(x, y)] = c
    edge = {}
    for (x, y) in blob:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in blob:
                edge[(x, y)] = ROCK[0] if dy != -1 else blob[(x, y)]
    blob.update(edge)
    near.update(blob)
    return tops

coral_spots = []
L = [(10, 150, 34, 46, 21), (34, 128, 30, 26, 22), (8, 108, 22, 30, 23), (62, 160, 32, 16, 24), (90, 168, 22, 10, 25)]
R = [(312, 146, 34, 50, 31), (286, 124, 28, 24, 32), (318, 98, 20, 30, 33), (258, 160, 30, 16, 34), (232, 170, 20, 8, 35)]
for b in L + R:
    tops = rock_blob(*b)
    xs = sorted(tops)
    for x in xs[3:-3:7]:
        coral_spots.append((x, tops[x]))
rock_blob(160, 178, 16, 6, 40)

def put(d, x, y, c):
    if 0 <= x < W and 0 <= y < H: d[(x, y)] = c

def branch_coral(d, x, y, ramp, h, seed):
    r = random.Random(seed)
    stack = [(x, y, h, 0)]
    while stack:
        bx, by, bh, dirx = stack.pop()
        cx, cy = bx, by
        for k in range(bh):
            if r.random() < .3: cx += dirx or r.choice((-1, 1))
            cy -= 1
            t = k / max(1, bh)
            col = ramp[0] if t < .3 else ramp[1] if t < .8 else ramp[2]
            put(d, cx, cy, col); put(d, cx + 1, cy, ramp[0] if t < .5 else ramp[1])
            if k > 2 and r.random() < .12 and bh - k > 3:
                stack.append((cx, cy, int((bh - k) * .8), r.choice((-1, 1))))
        put(d, cx, cy - 1, ramp[2]); put(d, cx + 1, cy - 1, ramp[3])

def fan_coral(d, x, y, ramp, rw, rh, seed):
    for dx in range(-rw, rw + 1):
        for dy in range(0, rh + 1):
            if (dx / rw) ** 2 + (dy / rh) ** 2 <= 1:
                if (dx + dy) % 3 == 0 or (dx - dy) % 3 == 0 or dy == 0:
                    t = dy / rh
                    put(d, x + dx, y - dy, ramp[0] if t < .35 else ramp[1] if t < .75 else ramp[2])
    for dy in range(0, 3): put(d, x, y - dy, ramp[0])

def bulb_coral(d, x, y, ramp, r_, seed):
    for dx in range(-r_, r_ + 1):
        for dy in range(-r_, 1):
            if dx * dx + dy * dy * 1.6 <= r_ * r_:
                v = math.sin((dx * 1.3 + dy * 2.1)) + (dy / r_) * -1.2
                col = ramp[2] if v > 1.1 else ramp[1] if v > 0 else ramp[0]
                put(d, x + dx, y + dy, col)
    put(d, x - 1, y - int(r_ * .7), ramp[3])

def tube_coral(d, x, y, ramp, seed):
    r = random.Random(seed)
    for i in range(3):
        tx = x + i * 3 - 3; th = r.randint(5, 10)
        for k in range(th):
            put(d, tx, y - k, ramp[0]); put(d, tx + 1, y - k, ramp[1])
        put(d, tx, y - th, ramp[3]); put(d, tx + 1, y - th, ramp[2])

RAMPS = {
    'pink': ['#c8336f', '#ff5f9e', '#ff9cc6', '#ffe0ef'],
    'purple': ['#6a3cc0', '#9b6bff', '#c9a6ff', '#f0e4ff'],
    'orange': ['#c8501f', '#ff7a33', '#ffb066', '#ffe2b8'],
    'red': ['#a82130', '#ef3a45', '#ff7a6e', '#ffd0c4'],
    'yellow': ['#c28a12', '#f7c531', '#ffe46b', '#fffbd0'],
    'teal': ['#127a7a', '#1fc2b0', '#6ff0d8', '#d8fff6'],
    'lime': ['#3d8a20', '#7ed23a', '#b9f26a', '#efffc8'],
}
kinds = ['branch', 'fan', 'bulb', 'tube']
cr = random.Random(5)
for i, (x, y) in enumerate(coral_spots):
    k = kinds[i % 4]; ramp = RAMPS[list(RAMPS)[(i * 3) % len(RAMPS)]]
    if k == 'branch': branch_coral(near, x, y, ramp, cr.randint(7, 13), i)
    elif k == 'fan': fan_coral(near, x, y, ramp, cr.randint(5, 8), cr.randint(6, 10), i)
    elif k == 'bulb': bulb_coral(near, x, y + 1, ramp, cr.randint(3, 5), i)
    else: tube_coral(near, x, y + 1, ramp, i)
# corals on the sand floor at the sides
for (x, k, rp) in ((52, 'branch', 'pink'), (70, 'bulb', 'orange'), (100, 'fan', 'purple'), (118, 'tube', 'teal'),
                   (205, 'branch', 'red'), (222, 'bulb', 'yellow'), (246, 'fan', 'pink'), (140, 'bulb', 'purple'), (182, 'branch', 'orange')):
    y = int(ground(x)) + 1
    if k == 'branch': branch_coral(near, x, y, RAMPS[rp], 12, x)
    elif k == 'fan': fan_coral(near, x, y, RAMPS[rp], 8, 10, x)
    elif k == 'bulb': bulb_coral(near, x, y, RAMPS[rp], 4, x)
    else: tube_coral(near, x, y, RAMPS[rp], x)
# starfish
def starfish(d, x, y, c):
    for k in range(5):
        a = -math.pi / 2 + k * 2 * math.pi / 5
        for r_ in range(0, 4):
            put(d, x + int(round(math.cos(a) * r_)), y + int(round(math.sin(a) * r_ * .6)), c if r_ < 3 else light(c, .3))
    put(d, x, y, light(c, .4))
starfish(near, 132, 172, '#ff7a3d'); starfish(near, 268, 176, '#ff5f9e'); starfish(near, 30, 175, '#f7c531')
parts.append('<g class="p">' + pix_paths(near) + '</g>')

# caustic light flecks on the sand and ledges
caus = []
cr2 = random.Random(9)
for i in range(10):
    x = cr2.randint(40, 280); y = int(ground(x)) + cr2.randint(1, 10)
    w_ = cr2.randint(2, 5)
    caus.append('<rect class="caus" style="animation-delay:-%.1fs;animation-duration:%.1fs" x="%d" y="%d" width="%d" height="1" fill="#fffbe2"/>' % (cr2.random() * 6, 4 + cr2.random() * 4, x, y, w_))
parts.append('<g>' + ''.join(caus) + '</g>')

# ---------- stone lantern (toro) with glow ----------
def lantern(ox, oy):
    d = {}
    S = ['#5d6476', '#8b93a6', '#b9c0cf', '#e2e6ee']
    rows = [  # (y, x0, x1, shade)
        (0, 5, 6, 3), (1, 3, 8, 2), (2, 1, 10, 2), (3, 0, 11, 1), (4, 1, 10, 0),
        (5, 3, 8, 1), (6, 3, 8, 1), (7, 3, 8, 1), (8, 3, 8, 1), (9, 2, 9, 0),
        (10, 4, 7, 1), (11, 4, 7, 1), (12, 4, 7, 1), (13, 4, 7, 2), (14, 4, 7, 1), (15, 2, 9, 0), (16, 1, 10, 0)]
    for (y, a, b, s) in rows:
        for x in range(a, b + 1):
            c = S[s]
            if x == a: c = S[max(0, s - 1)]
            if x == a + 1 and s < 3: c = S[min(3, s + 1)]
            d[(ox + x, oy + y)] = c
    for y in range(6, 9):
        for x in range(4, 8): d[(ox + x, oy + y)] = '#ffd25e' if (x + y) % 3 else '#fff3b0'
    outline(d, '#2a2f44')
    return d
lant = lantern(84, 146)
parts.append('<ellipse class="glow" cx="90" cy="153" rx="14" ry="11" fill="url(#lg)"/>')
parts.append('<g class="p">' + pix_paths(lant) + '</g>')
# moss on lantern
parts.append('<g class="p">' + pix_paths({(85, 149): '#7ed23a', (86, 149): '#b9f26a', (93, 150): '#7ed23a'}) + '</g>')

# ---------- torii gate ----------
def torii(ox, base):
    d = {}
    V, VL, VD, K = '#e8452c', '#ff7a55', '#b42d1c', '#2a1618'
    top = base - 34
    # pillars
    for px_ in (ox + 5, ox + 26):
        for y in range(top + 3, base + 1):
            d[(px_, y)] = VL; d[(px_ + 1, y)] = V; d[(px_ + 2, y)] = VD
        for x in range(px_ - 1, px_ + 4): d[(x, base)] = K; d[(x, base - 1)] = K
    # kasagi (top beam) with upturned ends
    for x in range(ox - 2, ox + 36):
        lift = 1 if x < ox + 1 or x > ox + 32 else 0
        d[(x, top - lift)] = K; d[(x, top + 1 - lift)] = V if x % 6 else VL; d[(x, top + 2 - lift)] = VD
    d[(ox - 3, top - 2)] = K; d[(ox + 36, top - 2)] = K
    # nuki (lower beam) and plaque
    for x in range(ox + 2, ox + 32):
        d[(x, top + 8)] = VL; d[(x, top + 9)] = VD
    for y in range(top + 3, top + 8):
        for x in range(ox + 15, ox + 19): d[(x, y)] = K if y in (top + 3, top + 7) or x in (ox + 15, ox + 18) else '#f7d36a'
    # algae and a little coral on the pillars
    for (x, y) in ((ox + 5, base - 6), (ox + 6, base - 7), (ox + 27, base - 9), (ox + 28, base - 10), (ox + 7, base - 14)):
        d[(x, y)] = '#7ed23a'
    outline(d, '#5a1410')
    return d
parts.append('<g class="p">' + pix_paths(torii(112, int(ground(128)) + 1)) + '</g>')
lant2 = lantern(196, int(ground(200)) - 16)
parts.append('<ellipse class="glow" style="animation-delay:-2s" cx="202" cy="%d" rx="13" ry="10" fill="url(#lg)"/>' % (int(ground(200)) - 9))
parts.append('<g class="p">' + pix_paths(lant2) + '</g>')

# ---------- seaweed (animated) ----------
def seaweed(x, base, h, seed, cols):
    d = {}
    r = random.Random(seed)
    for k in range(h):
        y = base - k
        off = int(round(1.6 * math.sin(k / 4.0 + seed)))
        c = cols[0] if k < h * .3 else cols[1] if k < h * .8 else cols[2]
        d[(x + off, y)] = c; d[(x + off + 1, y)] = cols[0] if k % 5 == 0 else c
        if k % 5 == 2 and k > 2:
            sd = 1 if (k // 5) % 2 else -1
            d[(x + off + (2 if sd > 0 else -1), y)] = cols[2]
            d[(x + off + (3 if sd > 0 else -2), y - 1)] = cols[2]
    outline(d, dark(cols[0], .45))
    return d
SW = [['#1e7a34', '#35b04a', '#7ee06a'], ['#2a8a5a', '#3fc28a', '#9ff0c0'], ['#5a8a20', '#8cc43a', '#d0f070']]
sweed = []
for i, (x, h) in enumerate(((6, 44), (18, 30), (44, 26), (76, 20), (108, 34), (170, 22), (214, 24), (240, 30), (272, 40), (298, 52), (310, 34))):
    base = int(ground(x)) + 2 if 40 < x < 280 else 178
    d = seaweed(x, base, h, i * 1.7, SW[i % 3])
    sweed.append('<g class="p sway" style="animation-delay:-%.1fs;animation-duration:%.1fs">%s</g>' % (i * .9, 4 + (i % 4) * .8, pix_paths(d)))
parts.append(''.join(sweed))

# ---------- creatures ----------
def koi_sprite(kind, seed):
    """Facing right. Returns (body_px, tail_px). Body x 7..33, tail x 0..7."""
    cy = 7.0
    body, tail = {}, {}
    pat = {
        'kohaku': ('#fffaf2', [('#ff3b2f', .50)], None),
        'sanke': ('#fffaf2', [('#ff4a2a', .52), ('#20202a', .80)], None),
        'showa': ('#1d1d28', [('#ff4a2a', .45), ('#fffaf2', .70)], None),
        'ogon': ('#ffc531', [('#ffe27a', .62)], None),
        'tancho': ('#fffaf2', [], 'spot'),
        'yamabuki': ('#ff8a1f', [('#ffb347', .6)], None),
        'kujaku': ('#e8f0ff', [('#ff9a3c', .5)], 'net'),
    }[kind]
    base, layers, special = pat
    X0, X1 = 7, 33
    for x in range(X0, X1 + 1):
        t = (x - X0) / (X1 - X0)
        # koi profile: thick shoulders, tapered peduncle, rounded snout
        h = 0.9 + 3.3 * math.sin(math.pi * min(1, .06 + t * .92)) ** .6
        if t > .88: h -= (t - .88) * 14
        for y in range(0, 15):
            dy = y + .5 - cy
            if abs(dy) <= h:
                c = base
                for col, th in layers:
                    if vnoise(x, y, 3.6, seed + sum(map(ord, col)) % 97) + (-.15 if dy > 1 else .06) > th: c = col
                if special == 'spot' and (x - 27) ** 2 * .8 + (y - 5) ** 2 < 5.5: c = '#ff2a2a'
                if special == 'net' and (x + y) % 3 == 0 and dy < 1: c = '#ff9a3c'
                # sunlight on the back, scale glints, shaded belly
                if dy < -h + 1.2: c = light(c, .5)
                elif dy < -h + 2.2 and (x + y) % 4 == 0: c = light(c, .3)
                elif dy > h - 1.1: c = dark(c, .3)
                body[(x, y)] = c
    fin = '#ffe6dc' if kind not in ('ogon', 'yamabuki') else '#ffe9a8'
    if kind == 'showa': fin = '#e8e0f0'
    fin2 = light(fin, .55)
    # dorsal fin, long and low
    tops = {}
    for (x, y) in body:
        tops[x] = min(tops.get(x, 99), y)
    for x in range(13, 26):
        hgt = 3 if x < 18 else 2 if x < 23 else 1
        for k in range(1, hgt + 1): body[(x, tops[x] - k)] = fin if k < hgt else fin2
    # big translucent pectoral fin
    for (x, y) in ((25, 11), (24, 11), (23, 12), (24, 12), (22, 12), (23, 13), (21, 13), (22, 13), (21, 12)):
        if (x, y) not in body: body[(x, y)] = fin if y < 13 else fin2
    # pelvic + anal fins
    for (x, y) in ((16, 11), (15, 11), (15, 12), (11, 10), (10, 10)):
        if (x, y) not in body: body[(x, y)] = fin2
    # eye, nostril, barbels (whiskers)
    body[(30, 6)] = '#101018'
    body[(30, 5)] = '#ffffff' if base != '#1d1d28' else '#ffd0a0'
    body[(34, 8)] = dark(fin, .25); body[(35, 9)] = dark(fin, .25)
    # tail: wide, forked, flowing
    for x in range(0, X0 + 1):
        spread = 1.0 + (X0 - x) * 0.85
        for y in range(-2, 17):
            dy = y + .5 - cy
            if abs(dy) <= spread and not (x < 3 and abs(dy) < 1.6 - x * .4):
                tail[(x, y)] = fin if abs(dy) < spread - 1.1 else fin2
                if (x + abs(int(dy))) % 3 == 0 and abs(dy) < spread - 1: tail[(x, y)] = light(fin, .25)
    allp = dict(body); allp.update(tail)
    ol = {}
    for (x, y) in allp:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in allp: ol[q] = '#3a1d2a' if q[0] > X0 else '#8a5a62'
    for q, c in ol.items():
        (tail if q[0] <= X0 else body)[q] = c
    return body, tail

def turtle_sprite(seed):
    body, flip = {}, {}
    cy = 8
    for x in range(5, 24):
        u = (x - 14) / 9.5
        if abs(u) > 1: continue
        hs = 6.2 * math.sqrt(1 - u * u)
        for y in range(0, 12):
            if cy - hs <= y + .5 <= cy + 1.5:
                dt = y + .5 - (cy - hs)
                cell = (int((x - 5) / 4.2) + int((y - 1) / 3.0)) % 2
                c = '#43a34e' if cell else '#5cbd55'
                if ((x - 5) % 4 == 0 or (y - 1) % 3 == 0) and dt > 1.5: c = '#2c7a3a'
                if dt < 1.4: c = '#a8ec7a'
                elif dt < 2.4: c = light(c, .25)
                if y >= cy + 1: c = '#e7c25e'
                body[(x, y)] = c
    for x in range(7, 22): body[(x, cy + 2)] = '#f1dfa0' if x % 3 else '#d8c27e'
    # head
    for x in range(23, 29):
        for y in range(cy - 2, cy + 3):
            if ((x - 25.5) / 3.2) ** 2 + ((y + .5 - cy) / 2.3) ** 2 <= 1:
                c = '#93d46c' if (x + y) % 4 else '#5e9a3e'
                if y == cy - 2: c = '#c2f09a'
                body[(x, y)] = c
    body[(27, cy - 1)] = '#121a12'; body[(26, cy - 2)] = '#ffffff'
    # back flipper
    for (x, y) in ((6, cy + 3), (5, cy + 3), (4, cy + 4), (5, cy + 4)): body[(x, y)] = '#7cc25a'
    # front flipper (animated): local in its own group
    for k in range(0, 9):
        for w in range(0, 3 - k // 4):
            flip[(19 - k, cy + 3 + k // 2 + w)] = '#86cc60' if w == 0 else '#5e9a3e'
    outline(body, '#173a22'); outline(flip, '#173a22')
    for q in list(flip):
        if q in body and body[q] != '#173a22': del flip[q]
    return body, flip

def fish_sprite(kind):
    d = {}
    if kind == 'clown':
        for x in range(0, 12):
            for y in range(0, 7):
                t = x / 11
                h = 0.6 + 2.6 * math.sin(math.pi * min(1, t * .95 + .1)) ** .8
                if abs(y + .5 - 3.5) <= h:
                    c = '#ff7a1a'
                    if x in (7, 8) or x in (3,) or x == 0: c = '#ffffff'
                    if x in (6, 9, 2): c = '#1a1420'
                    if y + .5 - 3.5 < -h + 1: c = light(c, .35)
                    d[(x + 2, y)] = c
        for y in range(1, 6): d[(0, y)] = '#ff7a1a'; d[(1, y)] = '#ffffff' if y in (1, 5) else '#ff7a1a'
        d[(11, 2)] = '#101018'
    elif kind == 'tang':
        for x in range(0, 10):
            for y in range(0, 11):
                if ((x - 5) / 4.6) ** 2 + ((y - 5) / 5) ** 2 <= 1:
                    c = '#ffd92e'
                    if ((x - 5) / 4.6) ** 2 + ((y - 5) / 5) ** 2 < .25: c = '#fff07a'
                    if y < 2: c = '#fff7b0'
                    d[(x + 2, y)] = c
        for y in range(2, 9): d[(1, y)] = '#ffc11a'
        for y in range(1, 10): d[(0, y)] = '#ffe066' if y in (1, 9) else '#ffc11a'
        for x in range(4, 9): d[(x, -1)] = '#ffe066'; d[(x, 11)] = '#ffc11a'
        d[(5, -2)] = '#fff7b0'; d[(9, 9)] = '#ffffff'
        d[(10, 4)] = '#101018'
    elif kind == 'angel':
        for x in range(0, 11):
            for y in range(0, 12):
                if abs(x - 6) / 5 + abs(y - 6) / 6 <= 1:
                    c = '#ffe14a' if (x // 2) % 2 else '#1d2a5a'
                    if x > 8: c = '#ffe14a'
                    d[(x + 1, y)] = c
        for k in range(4): d[(4 - k // 2, 12 + k)] = '#fff4c0'
        d[(10, 5)] = '#101018'
        for y in range(4, 8): d[(0, y)] = '#ffe14a'
    elif kind == 'neon':
        for x in range(0, 6):
            d[(x, 0)] = '#6ffaff'; d[(x, 1)] = '#ff2f6a' if x < 3 else '#f6f6ff'
        d[(6, 1)] = '#f6f6ff'; d[(5, 0)] = '#101018'
        d[(-1, 0)] = '#9fe0ff'; d[(-1, 1)] = '#ff2f6a'
        return d
    outline(d, '#20142a')
    return d

def swimmer(inner, x0, y0, dur, delay, left=False, span=(-40, 360), bobdur=4, flip_w=0):
    i = len(swim_css)
    a, b = span
    if left:
        frm, to = b - x0, a - x0
    else:
        frm, to = a - x0, b - x0
    swim_css.append('.s%d{animation:s%d %ds linear infinite;animation-delay:-%ds}@keyframes s%d{from{transform:translateX(%dpx)}to{transform:translateX(%dpx)}}' % (i, i, dur, delay, i, frm, to))
    flipattr = ' transform="translate(%d 0) scale(-1 1)"' % flip_w if left else ''
    return '<g transform="translate(%d %d)"><g class="s%d"><g class="bob" style="animation-duration:%.1fs;animation-delay:-%.1fs"><g%s>%s</g></g></g></g>' % (
        x0, y0, i, bobdur, delay % 5, flipattr, inner)

creatures = []
# turtles (behind koi)
for (x0, y0, dur, dl, left) in ((214, 50, 120, 30, True), (40, 118, 150, 90, False)):
    body, flip = turtle_sprite(1)
    inner = '<g class="p">%s</g><g class="p flip" style="animation-delay:-%ds">%s</g>' % (pix_paths(body), dl % 3, pix_paths(flip))
    creatures.append(swimmer(inner, x0, y0, dur, dl, left, (-50, 370), 6, 30))
# koi
for (kind, x0, y0, dur, dl, left) in (('kohaku', 120, 70, 62, 10, False), ('ogon', 230, 96, 74, 40, True), ('showa', 60, 40, 70, 25, True),
                                      ('tancho', 180, 128, 58, 5, False), ('sanke', 270, 30, 80, 55, False), ('yamabuki', 30, 88, 66, 33, True)):
    body, tail = koi_sprite(kind, len(creatures) * 13)
    inner = '<g class="p tail" style="animation-delay:-%.1fs">%s</g><g class="p">%s</g>' % (dl % 7 * .13, pix_paths(tail), pix_paths(body))
    creatures.append(swimmer(inner, x0, y0, dur, dl, left, (-45, 365), 3.5 + (dl % 3), 36))
# tropical fish
for (kind, x0, y0, dur, dl, left) in (('clown', 96, 104, 46, 12, False), ('clown', 104, 110, 46, 13, False), ('tang', 250, 120, 52, 20, True),
                                      ('angel', 200, 66, 60, 44, True), ('tang', 70, 60, 56, 30, False), ('clown', 280, 84, 50, 3, True)):
    d = fish_sprite(kind)
    creatures.append(swimmer('<g class="p">%s</g>' % pix_paths(d), x0, y0, dur, dl, left, (-30, 350), 2.5 + dl % 3, 14))
# neon school
school = []
sr = random.Random(3)
for k in range(8):
    sx, sy = sr.randint(0, 34), sr.randint(0, 14)
    school.append('<g transform="translate(%d %d)"><g class="bob" style="animation-duration:%.1fs;animation-delay:-%.1fs"><g class="p">%s</g></g></g>' % (sx, sy, 1.6 + sr.random(), sr.random() * 2, pix_paths(fish_sprite('neon'))))
creatures.append(swimmer(''.join(school), 150, 46, 38, 8, False, (-50, 370), 5, 0))
# jellyfish
def jelly(col):
    d = {}
    for x in range(0, 9):
        for y in range(0, 5):
            if ((x - 4) / 4.5) ** 2 + ((y - 4.5) / 4.5) ** 2 <= 1:
                c = col if y > 1 else light(col, .4)
                if y == 4: c = dark(col, .15)
                d[(x, y)] = c
    d[(2, 1)] = '#ffffff'; d[(3, 1)] = '#ffffff'
    for t in range(4):
        for k in range(0, 7 + t % 2 * 3):
            d[(1 + t * 2 + int(round(math.sin(k / 1.6 + t))), 5 + k)] = light(col, .3) if k % 2 else col
    return d
for (x, y, col, dl) in ((246, 22, '#ff8ed6', 0), (58, 26, '#b7a2ff', 15)):
    creatures.append('<g transform="translate(%d %d)"><g class="drift" style="animation-delay:-%ds"><g class="p jelly" style="animation-delay:-%.1fs" opacity=".88">%s</g></g></g>' % (x, y, dl, dl % 3, pix_paths(jelly(col))))
parts.append(''.join(creatures))

# ---------- bubbles ----------
bub = []
BUB = {
    1: ['#'],
    2: ['##', '##'],
    3: ['.#.', '#o#', '.#.'],
    4: ['.##.', '#*.#', '#..#', '.##.'],
    5: ['.###.', '#*..#', '#...#', '#...#', '.###.'],
}
def bubble(x, y, s):
    d = {}
    for j, row in enumerate(BUB[s]):
        for i, ch in enumerate(row):
            if ch == '#': d[(x + i, y + j)] = '#dffcff'
            elif ch == '*': d[(x + i, y + j)] = '#ffffff'
            elif ch == 'o': d[(x + i, y + j)] = '#9feaff'
    return '<g class="p">' + pix_paths(d) + '</g>'
br = random.Random(4)
for (sx, sy) in ((24, 120), (92, 148), (134, 168), (232, 150), (292, 112), (196, 166), (60, 156)):
    for k in range(4):
        s = br.choice((1, 2, 3, 3, 4, 5))
        dur = 7 + br.random() * 6
        bub.append('<g transform="translate(%d %d)"><g class="bub" style="animation-duration:%.1fs;animation-delay:-%.1fs">%s</g></g>' % (
            sx + br.randint(-2, 2), sy, dur, k * dur / 4 + br.random(), bubble(0, -k * 26, s)))
parts.append('<g>' + ''.join(bub) + '</g>')

# marine snow
snow = []
for k in range(14):
    x, y = br.randint(0, W), br.randint(10, 150)
    snow.append('<rect class="snow" style="animation-delay:-%.1fs;animation-duration:%ds" x="%d" y="%d" width="1" height="1" fill="#e9fbff" opacity=".7"/>' % (br.random() * 26, 20 + k % 12, x, y))
parts.append('<g>' + ''.join(snow) + '</g>')

# ---------- surface shimmer ----------
surf = {}
for x in range(0, W + 64):
    y = 2 + int(round(1.5 * math.sin(x * 2 * math.pi / 32) + .8 * math.sin(x * 2 * math.pi / 16 + 1)))
    for yy in range(0, y): surf[(x, yy)] = '#bff7ff'
    surf[(x, y)] = '#e9fdff' if x % 8 < 5 else '#bff7ff'
    if x % 16 in (3, 4, 5, 9): surf[(x, y + 2)] = '#a6eeff'
    if x % 32 in (6, 7, 20): surf[(x, y + 4)] = '#8fe6fb'
parts.append('<g class="p surf" opacity=".9">' + pix_paths(surf) + '</g>')

# lotus pads floating on the surface, roots hanging down
lot = []
for (x, w, fl) in ((22, 22, True), (52, 14, False), (250, 26, True), (284, 16, True), (300, 12, False)):
    d = {}
    for dx in range(-w // 2, w // 2 + 1):
        hgt = 3 if abs(dx) < w // 2 - 2 else 2
        for y in range(0, hgt):
            d[(x + dx, y)] = '#1f6b3a' if y < hgt - 1 else '#3f9a4e'
        if abs(dx) == w // 2 - 3: d[(x + dx, hgt)] = '#3f9a4e'
    d[(x + 1, 0)] = '#9be37a'; d[(x + 2, 1)] = '#9be37a'
    stem = {}
    for k in range(3, 18 + w // 2):
        stem[(x + int(round(math.sin(k / 5.0) * 1.2)), k)] = '#3f9a4e' if k % 4 else '#5fb85c'
    lot.append('<g class="p stem" style="animation-delay:-%ds">%s</g><g class="p">%s</g>' % (x % 7, pix_paths(stem), pix_paths(d)))
    if fl:
        f = {(x - 2, 0): '#ff9ec4', (x - 1, 0): '#ffd0e2', (x, 0): '#ff9ec4', (x - 1, 1): '#ff6fa8'}
        lot.append('<g class="p">%s</g>' % pix_paths(f))
parts.append(''.join(lot))
pet = []
pr = random.Random(12)
for k in range(16):
    x, y = pr.randint(0, W), pr.randint(-10, 40)
    c1, c2 = pr.choice((('#ffc3d9', '#ff9ec4'), ('#ffe0ec', '#ffb3cf'), ('#ffd0e2', '#ff8fbf')))
    pet.append('<g transform="translate(%d %d)"><g class="p petal" style="animation-delay:-%.1fs;animation-duration:%ds">%s</g></g>' % (
        x, y, pr.random() * 30, 24 + k % 5 * 3, pix_paths({(0, 0): c1, (1, 0): c1, (1, 1): c2, (2, 1): c1})))
parts.append(''.join(pet))
# ---------- feeding time: every 75 s food falls and one koi comes to eat ----------
def autofeed(fx, fy, period=75):
    out = []
    css = []
    fr = random.Random(21)
    for k, dx in enumerate((3, -4, 1)):
        css.append('@keyframes afp%d{0%%{transform:translate(0,-5px);opacity:0}2%%{opacity:1}27%%{opacity:1}31%%{transform:translate(%dpx,42px);opacity:0}100%%{transform:translate(%dpx,42px);opacity:0}}'
                   '.afp%d{animation:afp%d %ds linear infinite;animation-delay:-0s}' % (k, dx, dx, k, k, period))
    for k in range(8):
        px_, py_ = fx + fr.randint(-7, 7), fy + fr.randint(-3, 3)
        c = ('#c8742a', '#e8a33f', '#a0521c', '#f2c060')[k % 4]
        out.append('<g transform="translate(%d %d)"><g class="afp%d" style="animation-delay:-%.1fs">%s</g></g>' % (
            px_, py_, k % 3, k * 0.15, pix_paths({(0, 0): '#ffe0a0', (1, 0): c})))
    tx, ty = fx - 35, fy - 7
    at = lambda x, y: 'transform:translate(%dpx,%dpx)' % (x - tx, y - ty)
    css.append('@keyframes afk{0%%{%s}4%%{%s;animation-timing-function:ease-out}14%%{%s;animation-timing-function:ease-in-out}'
               '28%%{%s;animation-timing-function:ease-in}38%%{%s}100%%{%s}}.afk{animation:afk %ds linear infinite;animation-delay:-0s}'
               % (at(-45, ty - 12), at(-45, ty - 12), at(tx, ty), at(tx + 3, ty + 30), at(365, ty + 18), at(365, ty + 18), period))
    body, tail = koi_sprite('tancho', 900)
    koi = '<g class="p tail" style="animation-duration:.5s">%s</g><g class="p">%s</g>' % (pix_paths(tail), pix_paths(body))
    out.append('<g transform="translate(%d %d)"><g class="afk"><g class="nib">%s</g></g></g>' % (tx, ty, koi))
    # happy bubbles while it eats
    for k in range(3):
        out.append('<g transform="translate(%d %d)"><g class="bub" style="animation-duration:%ds;animation-delay:-%ds">%s</g></g>' % (
            fx + k * 3 - 3, fy + 20, period, period - 12 - k * 2, bubble(0, 0, 2)))
    return '<style>%s</style><g class="p">%s</g>' % (''.join(css), ''.join(out))
parts.append(autofeed(212, 56))

# glass reflections (fixed, on the pane in front)
parts.append('<g class="shine" opacity=".5"><polygon points="18,0 30,0 0,52 0,31" fill="#ffffff" opacity=".10"/><polygon points="36,0 40,0 2,66 0,66 0,62" fill="#ffffff" opacity=".12"/>'
             '<polygon points="300,0 320,0 320,10 296,52 286,52" fill="#ffffff" opacity=".06"/></g>')
parts.append('<rect width="%d" height="%d" fill="url(#vg)"/>' % (W, H))

import re as _re
def _delay(m):
    body = m.group(2)
    if 'animation:' in body and 'animation-delay' not in body:
        body += ';animation-delay:-0s'
    return m.group(1) + '{' + body + '}'
CSS = _re.sub(r'(^|\n)([^{@\n]+)\{([^{}]*)\}', lambda m: m.group(1) + m.group(2) + '{' + (m.group(3) + (';animation-delay:-0s' if 'animation:' in m.group(3) and 'animation-delay' not in m.group(3) else '')) + '}', CSS)
svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid slice"><style>%s%s</style>%s%s</svg>'
       % (W, H, ' '.join(l.strip() for l in CSS.strip().splitlines()), ''.join(swim_css), defs, ''.join(parts)))
open(OUT, 'w').write(svg)
feeders = []
for k, kind in enumerate(('kohaku', 'ogon', 'showa', 'tancho', 'yamabuki')):
    body, tail = koi_sprite(kind, 500 + k * 13)
    feeders.append('<g class="p tail" style="animation-duration:.5s">%s</g><g class="p">%s</g>' % (pix_paths(tail), pix_paths(body)))
json.dump(feeders, open(OUT + '.feeders.json', 'w'))
for i, q in enumerate(parts): print(i, len(q), q[:50])
print(len(svg), 'chars')
