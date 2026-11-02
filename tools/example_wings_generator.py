"""Aurelion v7 — ailes d'archange construites en volumes (comme un modèle Minecraft propre).
Convention validée par calibration : rotations appliquées telles quelles, X+ = bascule vers l'arrière,
Y+ = pivote vers l'arrière (côté gauche), Z+ = la pointe monte (côté gauche). Côté droit : Y et Z inversés.
Pas de scale/position. Une seule paire. Plumes = rachis + vane en 3 cubes d'épaisseur 0.5 ; rangées tuilées dans le plan."""
import json, base64, io, math, uuid as _uuid
import numpy as np
from PIL import Image, ImageDraw

TEX = 256
tex = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
d = ImageDraw.Draw(tex)
IV = (248, 244, 234); IV2 = (236, 230, 216); WR = (222, 212, 194); SH = (196, 184, 162)
GO = (232, 192, 100); GOL = (255, 232, 168); GOD = (156, 112, 40); WH = (255, 255, 255)

SS = 4
def rgb(c): return np.array(c, float)
def paint_feather(W, H, kind):
    """Silhouette de plume découpée. kind : 'p' primaire (pointe dorée), 's' secondaire, 'c' couverture (courte, ronde)."""
    w, h = W * SS, H * SS
    img = np.zeros((h, w, 4), np.float32)
    for y in range(h):
        t = 1 - y / (h - 1)                                      # 0 base -> 1 pointe
        curve = 0.10 if kind != 'c' else 0.05
        rx = w * 0.5 + curve * w * (t * t - 0.1 * t)
        if kind == 'c':
            hw = w * 0.46 * ((0.55 + 0.45 * (t / 0.4) ** 0.6) if t < 0.4 else math.sqrt(max(0.0, 1 - ((t - 0.4) / 0.6) ** 2)))
            inner = hw
        else:
            pk = 0.45
            hw = w * 0.46 * ((0.18 + 0.82 * (t / pk) ** 0.85) if t < pk else max(0.0, 1 - ((t - pk) / (1 - pk)) ** 1.6) ** 0.7)
            inner = hw * 0.72
        hw = max(hw, 0.7 * SS)
        for x in range(w):
            dx = x - rx
            lim = hw if dx > 0 else inner
            if abs(dx) > lim: continue
            r = abs(dx) / max(1e-6, lim)
            col = rgb(WH) * (1 - r) ** 0.6 + rgb(IV) * (1 - (1 - r) ** 0.6)
            col = col * (1 - 0.35 * r ** 2) + rgb(WR) * (0.35 * r ** 2)
            if kind == 's': col = col * 0.94
            # ombre de recouvrement à la base
            shd = max(0.0, 1 - t / 0.35) ** 1.4
            col = col * (1 - 0.40 * shd) + rgb(SH) * (0.40 * shd)
            # barbes
            if math.sin((y * 1.0 - abs(dx) * 2.0) / SS * 1.1) > 0.85: col = np.minimum(255, col + 7)
            # liseré doré externe
            if r > 0.86 and t > 0.25: col = col * 0.40 + rgb(GO) * 0.60
            if kind == 'p' and t > 0.84:
                k = (t - 0.84) / 0.16; col = col * (1 - 0.8 * k) + rgb(GO) * 0.8 * k
            if kind == 'c' and t > 0.93: col = col * 0.3 + rgb(GO) * 0.7
            if abs(dx) < 0.7 * SS and kind != 'c': col = col * 0.5 + rgb(GOL if t < 0.15 else WH) * 0.5
            img[y, x, :3] = np.clip(col, 0, 255); img[y, x, 3] = 255
    pil = Image.fromarray(img.astype(np.uint8), "RGBA").resize((W, H), Image.LANCZOS)
    a = np.array(pil); a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    return Image.fromarray(a, "RGBA")

tex.paste(paint_feather(32, 96, 'p'), (0, 0))
tex.paste(paint_feather(32, 96, 's'), (32, 0))
tex.paste(paint_feather(32, 48, 'c'), (64, 0))
# couverture dorée (bord d'attaque) : même silhouette, teintée
cg = np.array(paint_feather(32, 48, 'c')).astype(float)
lum = cg[..., :3].mean(axis=2, keepdims=True) / 255
cg[..., :3] = rgb(GOD) * (1 - lum) + rgb(GOL) * lum
tex.paste(Image.fromarray(cg.astype(np.uint8), "RGBA"), (64, 48))
# or uni 16x16 (96,16) ; blanc os 16x16 (112,16) ; transparent (250,250)
d.rectangle([96, 16, 111, 31], fill=GO + (255,)); d.rectangle([98, 18, 109, 29], outline=GOL + (255,))
d.rectangle([112, 16, 127, 31], fill=IV + (255,)); d.line([112, 23, 127, 23], fill=WH + (255,), width=3)
# halo 96x96 (0,128)
halo = Image.new("RGBA", (288, 288), (0, 0, 0, 0)); hd = ImageDraw.Draw(halo)
hd.ellipse([18, 18, 270, 270], outline=GO + (255,), width=18); hd.ellipse([46, 46, 242, 242], outline=GOL + (255,), width=5)
ha = np.array(halo.resize((96, 96), Image.LANCZOS)); ha[..., 3] = np.where(ha[..., 3] > 100, 255, 0)
tex.paste(Image.fromarray(ha, "RGBA"), (0, 128))
tex.save("aurelion_wings.png")
buf = io.BytesIO(); tex.save(buf, "PNG", optimize=True)
tex_b64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

UV_P = (0, 0, 32, 96); UV_S = (32, 0, 64, 96); UV_C = (64, 0, 96, 48); UV_G = (64, 48, 96, 96)
UV_GOLD = (96, 16, 112, 32); UV_BONE = (112, 16, 128, 32); UV_HALO = (0, 128, 96, 224); CLEAR = [250, 250, 252, 252]

# ---------------------------------------------------------------- géométrie
def nuid(): return str(_uuid.uuid4())
elements, groups = [], {}
def cube(name, frm, to, origin, rot=(0, 0, 0), faces=None):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to],
         "origin": [round(v, 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": list(uv), "texture": 0} for f, uv in faces.items()}}
    if any(rot): e["rotation"] = [round(v, 2) for v in rot]
    elements.append(e); return e["uuid"]
def group(name, origin, parent=None, rotation=(0, 0, 0)):
    groups[name] = {"origin": [round(v, 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [round(v, 2) for v in rotation]}
    return name

Z = 4.5
TH = 0.5

def feather(name, s, ax, ay, L, w, tilt, z, uv, parent, own_bone=False, taper=None):
    sx = lambda v: s * v
    bx = sx(ax)
    u0, v0, u1, v1 = uv
    if s > 0: u0, u1 = u1, u0
    faces = {"north": [u1, v0, u0, v1], "south": [u0, v0, u1, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    tgt = group(name, [bx, ay, z], parent=parent) if own_bone else parent
    groups[tgt]["ids"].append(cube(name, [bx - w / 2, ay - L, z - TH / 2], [bx + w / 2, ay + 0.6, z + TH / 2], [bx, ay, z], rot=(0, 0, sx(tilt)), faces=faces))

def polyline(P):
    lens = [math.dist(P[i], P[i + 1]) for i in range(len(P) - 1)]; tot = sum(lens)
    def at(u):
        dd = u * tot
        for i, L in enumerate(lens):
            if dd <= L or i == len(lens) - 1:
                f = min(1.0, dd / L); return P[i][0] + f * (P[i + 1][0] - P[i][0]), P[i][1] + f * (P[i + 1][1] - P[i][1]), i
            dd -= L
    return at
def bell(x, c, w): return math.exp(-((x - c) / w) ** 2)

# bras : épaule -> coude (monte) -> poignet (monte un peu) -> bout (presque plat), arche au-dessus des épaules
ARM = [(3.0, 23.0), (9.5, 30.5), (18.0, 34.5), (27.0, 35.5)]
YAW = [-24, 8, -8]          # balayage arrière au repos (humérus en arrière, avant-bras revient, main repart)
ARM_D = [(3.0, 18.5), (8.0, 16.0), (14.5, 14.0), (20.5, 12.0)]      # petite paire : part sous l'omoplate, descend vers l'extérieur
YAW_D = [-30, 8, -8]
SEG = ["shoulder", "elbow", "wrist"]

def build(s):
    tag = "l" if s < 0 else "r"
    sx = lambda v: s * v
    segs = []
    for i in range(3):
        segs.append(group(f"{SEG[i]}_{tag}", [sx(ARM[i][0]), ARM[i][1], Z], parent=segs[i - 1] if i else None, rotation=(0, sx(YAW[i]), 0)))
    at = polyline(ARM)
    par = lambda u: segs[at(u)[2]]
    # os du bras : 3 cubes épais (dorés aux articulations) — donne un vrai bord d'attaque
    for i in range(3):
        (x0, y0), (x1, y1) = ARM[i], ARM[i + 1]
        L = math.dist(ARM[i], ARM[i + 1]); ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        a, b = sorted([sx(x0 - 0.3), sx(x0 + L + 0.3)]); th = 1.2 - 0.2 * i
        groups[segs[i]]["ids"].append(cube(f"arm{i}_{tag}", [a, y0 - th / 2, Z - th / 2], [b, y0 + th / 2, Z + th / 2], [sx(x0), y0, Z], rot=(0, 0, sx(ang)),
                                           faces={k: list(UV_GOLD) for k in ("north", "south", "up", "down", "east", "west")}))
        r = 1.0 - 0.15 * i
        groups[segs[i]]["ids"].append(cube(f"joint{i}_{tag}", [sx(x0) - r, y0 - r, Z - r], [sx(x0) + r, y0 + r, Z + r], [sx(x0), y0, Z],
                                           faces={k: list(UV_GOLD) for k in ("north", "south", "east", "west", "up", "down")}))
    def tilt_of(u):
        if u < 0.26: return -10 + 10 * u / 0.26
        if u < 0.64: return 2 + 10 * (u - 0.26) / 0.38
        return 12 + 52 * ((u - 0.64) / 0.36) ** 1.15
    # primaires (main) : 8, longues, s'effilent
    for k in range(8):
        u = 0.64 + 0.36 * (k + 0.5) / 8; f = (k + 0.5) / 8
        ax, ay, _ = at(u)
        L = 22 + 8 * bell(f, 0.5, 0.4) - 6 * max(0, (f - 0.75) / 0.25)
        feather(f"p{k}_{tag}", s, ax, ay - 0.6, L, 6.4 - 1.0 * f, tilt_of(u), Z - 0.1 * k, UV_P, par(u), own_bone=True)
    # secondaires (avant-bras) : 8
    for k in range(10):
        u = 0.26 + 0.38 * (k + 0.5) / 10; f = (k + 0.5) / 10
        ax, ay, _ = at(u)
        feather(f"s{k}_{tag}", s, ax, ay - 0.6, 16 + 3 * f + (1.0 if k % 2 else 0), 6.2, tilt_of(u), Z - 0.9 - 0.08 * k, UV_S, par(u), own_bone=True)
    # tertiaires (humérus) : 3
    for k in range(3):
        u = 0.03 + 0.22 * (k + 0.5) / 3
        ax, ay, _ = at(u)
        feather(f"t{k}_{tag}", s, ax, ay - 0.6, 12 + 1.5 * k, 6.2, tilt_of(u), Z - 1.6 - 0.1 * k, UV_S, par(u))
    # couvertures tuilées : 2 rangées devant (z+), chevauchent la base des rémiges ; inclinées pour s'allonger sur la rangée suivante
    for row, (n, L, w, dz, lift, uv) in enumerate([(13, 9.0, 5.6, 1.0, 0.6, UV_C), (16, 5.4, 4.6, 1.9, 1.3, UV_C), (18, 3.0, 3.6, 2.7, 1.9, UV_G)]):
        for k in range(n):
            u = 0.03 + 0.94 * (k + 0.5) / n
            ax, ay, _ = at(u)
            feather(f"c{row}{k}_{tag}", s, ax, ay + lift, L + 2 * u, w, tilt_of(u) * 0.9, Z + dz, uv, par(u))
    # scapulaires dorées à la racine (3)
    for k in range(3):
        feather(f"sc{k}_{tag}", s, 2.6 + 0.9 * k, 24.4, 5.0 - 0.4 * k, 4.2, -16 + 14 * k, Z + 3.3, UV_C, segs[0])
    # ======== petite paire basse ========
    segd = []
    for i in range(3):
        segd.append(group(f"d{SEG[i]}_{tag}", [sx(ARM_D[i][0]), ARM_D[i][1], Z], parent=segd[i - 1] if i else None, rotation=(0, sx(YAW_D[i]), 0)))
    atd = polyline(ARM_D); pard = lambda u: segd[atd(u)[2]]
    for i in range(3):
        (x0, y0), (x1, y1) = ARM_D[i], ARM_D[i + 1]
        L = math.dist(ARM_D[i], ARM_D[i + 1]); ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        a, b = sorted([sx(x0 - 0.3), sx(x0 + L + 0.3)]); th = 0.9 - 0.15 * i
        groups[segd[i]]["ids"].append(cube(f"darm{i}_{tag}", [a, y0 - th / 2, Z - 1.2 - th / 2], [b, y0 + th / 2, Z - 1.2 + th / 2], [sx(x0), y0, Z - 1.2], rot=(0, 0, sx(ang)),
                                           faces={k: list(UV_GOLD) for k in ("north", "south", "up", "down", "east", "west")}))
    def tilt_d(u): return (4 + 12 * u) if u < 0.6 else 11 + 44 * ((u - 0.6) / 0.4) ** 1.1
    ZD = Z - 1.2
    for k in range(6):                                            # primaires basses
        u = 0.6 + 0.4 * (k + 0.5) / 6; f = (k + 0.5) / 6
        ax, ay, _ = atd(u)
        feather(f"dp{k}_{tag}", s, ax, ay - 0.5, 13 + 6 * bell(f, 0.5, 0.4) - 3 * max(0, (f - 0.7) / 0.3), 5.0, tilt_d(u), ZD - 0.1 * k, UV_P, pard(u), own_bone=True)
    for k in range(7):                                            # secondaires basses
        u = 0.1 + 0.5 * (k + 0.5) / 7; f = (k + 0.5) / 7
        ax, ay, _ = atd(u)
        feather(f"ds{k}_{tag}", s, ax, ay - 0.5, 10 + 2.5 * f + (0.8 if k % 2 else 0), 5.0, tilt_d(u), ZD - 0.8 - 0.08 * k, UV_S, pard(u), own_bone=True)
    for row, (n, L, w, dz, lift, uv) in enumerate([(10, 6.0, 4.6, 0.9, 0.5, UV_C), (12, 3.2, 3.6, 1.7, 1.1, UV_G)]):
        for k in range(n):
            u = 0.03 + 0.94 * (k + 0.5) / n
            ax, ay, _ = atd(u)
            feather(f"dc{row}{k}_{tag}", s, ax, ay + lift, L + 1.5 * u, w, tilt_d(u) * 0.9, ZD + dz, uv, pard(u))
    return segs[0], segd[0]

(L_, LD_), (R_, RD_) = build(-1), build(1)
H = group("halo", [0, 36.0, 0])
groups[H]["ids"].append(cube("halo", [-6.5, 35.9, -6.5], [6.5, 36.1, 6.5], [0, 36, 0],
                             faces={"up": list(UV_HALO), "down": [UV_HALO[2], UV_HALO[1], UV_HALO[0], UV_HALO[3]],
                                    "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR}))

def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}
outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [{"name": "item", "origin": [0, 0, 0], "uuid": nuid(), "children": [bone("halo"), bone(L_), bone(R_), bone(LD_), bone(RD_)]}]}]

# ---------------------------------------------------------------- animations (convention calibrée)
# gauche : (x, y, z) = (bascule arrière, pivote arrière, pointe monte) ; droite : y et z inversés
TAU = 2 * math.pi
def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x, 2)), "y": str(round(y, 2)), "z": str(round(z, 2))}], "time": round(t, 3), "interpolation": "catmullrom"}
def S(T, amp, ph=0.0, off=0.0): return lambda t: off + amp * math.sin(TAU * t / T + math.radians(ph))
def C(v): return lambda t: v
def sm(t, a, b):
    if t <= a: return 0.0
    if t >= b: return 1.0
    u = (t - a) / (b - a); return u * u * (3 - 2 * u)
def bump(t, a, b, c, d): return sm(t, a, b) * (1 - sm(t, c, d))

def anim(name, length, segs, fan, n_kf=None, fan_w=(1.0, 0.5)):
    """segs : nom -> (fx, fy, fz) fonctions ; fan(t) -> écart des primaires (secondaires à 50 %)."""
    A = {}
    def put(g, kfs): A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}
    n = n_kf or max(4, int(round(length * 6)))
    times = [i * length / n for i in range(n + 1)]      # keyframe final = même pose qu'à t=0 (boucle fermée quel que soit l'interpolateur)
    for s, tag in ((-1, "l"), (1, "r")):
        for seg, (fx, fy, fz) in segs.items():
            put(f"{seg}_{tag}", [kf("rotation", t, -fx(t), s * -fy(t), s * -fz(t)) for t in times])
            dl = 0.08 * length
            put(f"d{seg}_{tag}", [kf("rotation", t, -0.8 * fx((t - dl) % length), s * -0.8 * fy((t - dl) % length), s * -0.8 * fz((t - dl) % length)) for t in times])
        for g in groups:
            if g.endswith(f"_{tag}") and ((g[0] in "ps" and g[1].isdigit()) or (g[:2] in ("dp", "ds") and g[2].isdigit())):
                w = fan_w[0] if g[0] == "p" or g[:2] == "dp" else fan_w[1]
                put(g, [kf("rotation", t, 0, 0, s * -(fan(t) * w)) for t in times])
    return {"uuid": nuid(), "name": name, "loop": "loop", "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}

Z0 = C(0)
# idle 8 s : respiration + étirement 4.6–7.2 s (ailes s'ouvrent vers l'arrière et montent)
st = lambda t: bump(t, 4.6, 5.4, 6.0, 7.2)
mix = lambda f, v: (lambda t: f(t) * (1 - st(t)) + v * st(t))
idle = anim("idle", 8.0, {
    "shoulder": (mix(Z0, 10), mix(S(4, 2), -14), mix(S(4, 2.5), 14)),
    "elbow":    (Z0, mix(S(4, 1, 40), -6), mix(S(4, -1.5, 40), 6)),
    "wrist":    (Z0, mix(S(4, 0.8, 80), -10), mix(S(4, -1, 80), 4))},
    fan=lambda t: 1.5 * math.sin(TAU * t / 4) + 9 * st(t), n_kf=48)

# fly 2.4 s : plan basculé vers l'horizontale (x ≈ 55), battement Z ample, remontée poignet replié (y)
T = 2.4
fly = anim("fly", T, {
    "shoulder": (S(T, 8, 0, 55), S(T, 6, 0, 4), S(T, 28, 0, 6)),
    "elbow":    (Z0, lambda t: -4 + 14 * max(0.0, -math.cos(TAU * t / T + 0.4)), S(T, 12, -25, -4)),
    "wrist":    (Z0, lambda t: -6 + 22 * max(0.0, -math.cos(TAU * t / T + 0.8)), S(T, 14, -45, -4))},
    fan=lambda t: 4 + 10 * math.cos(TAU * t / T - 0.4), n_kf=24)

# glide (élytres) 3.6 s : horizontal, grandes ouvertes, battement lent
G = 3.6
glide = anim("glide", G, {
    "shoulder": (S(G, 6, 0, 58), C(8), S(G, 22, 0, 8)),
    "elbow":    (Z0, lambda t: -4 + 10 * max(0.0, -math.cos(TAU * t / G + 0.5)), S(G, 10, -30, -6)),
    "wrist":    (Z0, lambda t: -8 + 18 * max(0.0, -math.cos(TAU * t / G + 0.9)), S(G, 12, -55, -4))},
    fan=lambda t: 8 + 4 * math.cos(TAU * t / G), n_kf=24)

# air 1.5 s : demi-basculées, relevées, ouvertes (freinage)
AI = 1.5
air = anim("air", AI, {"shoulder": (S(AI, 2, 0, 36), C(12), S(AI, 3, 0, 14)), "elbow": (Z0, C(-4), S(AI, 2, 30, 4)), "wrist": (Z0, C(-6), C(2))}, fan=C(10))

# walk 1.6 s : un peu vers l'arrière, balancement
W = 1.6
walk = anim("walk", W, {"shoulder": (Z0, S(W, 2, 0, 12), S(W, 2.5, 0, -2)), "elbow": (Z0, S(W, 1.5, -34, -4), S(W, 1.5, -34)), "wrist": (Z0, S(W, 1.5, -63, 6), S(W, 1.5, -63))}, fan=C(0))
# run 1.0 s : nettement vers l'arrière, repliées en S, abaissées
R = 1.0
run = anim("run", R, {"shoulder": (C(6), S(R, 2, 0, 34), S(R, 2.5, 0, -10)), "elbow": (Z0, S(R, 1.5, -40, -18), S(R, 2, -40, -2)), "wrist": (Z0, S(R, 2, -80, 26), S(R, 2.5, -80))}, fan=C(-6))
# sneak 3 s : repliées contre le dos
SN = 3.0
sneak = anim("sneak", SN, {"shoulder": (C(6), S(SN, 1, 0, 44), S(SN, 1, 0, -18)), "elbow": (Z0, C(-30), S(SN, 1, 30, -22)), "wrist": (Z0, C(26), C(-24))}, fan=C(-16))
# sleep 4 s : repliées, tombantes
SL = 4.0
sleep = anim("sleep", SL, {"shoulder": (C(2), S(SL, 1, 0, 38), S(SL, 1, 0, -24)), "elbow": (Z0, C(-28), C(6)), "wrist": (Z0, C(34), C(6))}, fan=C(-14))
# swim 2 s : profilées vers l'arrière, légèrement à plat
SW = 2.0
swim = anim("swim", SW, {"shoulder": (C(-14), S(SW, 1.5, 0, 38), S(SW, 2, 0, -12)), "elbow": (Z0, S(SW, 2, -46, -22), S(SW, 2, -46)), "wrist": (Z0, S(SW, 3, -92, 28), S(SW, 3, -92))}, fan=C(-12))
# mount 3 s : repos relevé
MT = 3.0
mount = anim("mount", MT, {"shoulder": (C(8), S(MT, 2.5, 0, 2), S(MT, 2.5, 0, 6)), "elbow": (Z0, S(MT, 1.5, 30, -2), Z0), "wrist": (Z0, C(-2), Z0)}, fan=C(3))
# attack 0.8 s : déploiement brusque
AT = 0.8
atk = lambda t: bump(t, 0.0, 0.14, 0.30, 0.8)
attack = anim("attack", AT, {"shoulder": (lambda t: 28 * atk(t), lambda t: -20 * atk(t), lambda t: 16 * atk(t)),
                             "elbow": (Z0, lambda t: -8 * atk(t), lambda t: 6 * atk(t)), "wrist": (Z0, lambda t: -12 * atk(t), lambda t: 4 * atk(t))},
              fan=lambda t: 18 * atk(t), n_kf=16)
# hurt 0.8 s : sursaut vers l'arrière + tremblement
HU = 0.8
hu = lambda t: bump(t, 0.0, 0.08, 0.22, 0.8); tr = lambda t: 3 * math.sin(TAU * t * 6) * (1 - sm(t, 0.3, 0.8))
hurt = anim("hurt", HU, {"shoulder": (Z0, lambda t: 16 * hu(t), lambda t: 12 * hu(t) + tr(t)),
                         "elbow": (Z0, lambda t: -6 * hu(t), lambda t: -4 * hu(t) + tr(t)), "wrist": (Z0, lambda t: 8 * hu(t), lambda t: -4 * hu(t) + tr(t))},
            fan=lambda t: -10 * hu(t) + tr(t), n_kf=16)

ANIMS = [idle, fly, glide, sneak, walk, run, air, swim, mount, sleep, attack, hurt]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": "aurelion_wings",
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner,
         "textures": [{"name": "aurelion_wings.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}], "animations": ANIMS}
json.dump(model, open("aurelion_wings.bbmodel", "w"), separators=(",", ":"))
json.load(open("aurelion_wings.bbmodel"))
def depth(n, d=1): return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])
import os
print(len(elements), "cubes ;", len(groups) + 2, "groupes ; profondeur", depth(outliner[0]), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize("aurelion_wings.bbmodel") // 1024, "Ko")
