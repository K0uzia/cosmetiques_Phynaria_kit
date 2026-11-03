"""Chapeau macaron : gros macaron à la fraise posé de travers sur le dessus de la tête, une petite fourchette plantée dedans.
Ensemble « Pâtisserie » (fraise, vanille, chocolat). Design original, série kawaii.
Écrit chapeau_macaron.png, chapeau_macaron_e.png et .build/chapeau_macaron_brut.bbmodel à côté de ce script.

Construction (groupe de premier niveau head) :
- chaque coque = 5 étages bombés ; un étage = 4 prismes carrés pleins tournés de 22,5° (âme à 16 pans, faces latérales peintes)
  + un disque « peau » de même hauteur, découpé en cercle par alpha, qui ne montre que sa face extérieure (dessus pour la coque
  du haut, dessous pour celle du bas) : silhouette ronde vue de dessus, profil bombé vu de côté ;
- pied (collerette) : même principe, disque au bord irrégulier, plus clair, ombre de recouvrement peinte sous la coque ;
- ganache vanille : âme à 16 pans, liseré de confiture peint sur le flanc ;
- fourchette : dents, tête, col argentés, manche chocolat, plantée en biais dans le dessus.
Le macaron repose sur le bord de sa coque basse, côté droit : le pivot du groupe est ce point de contact (il vacille dessus).
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "chapeau_macaron"
AVEC_E = True       # calque _e embarqué en seconde texture, jamais assigné aux faces (correctif du mod annoncé le 2026-11-03, à vérifier en jeu)
TEX = 512
SS = 4
TAU = 2 * math.pi

# ------------------------------------------------------------------ palette (bases poussées vers le blanc : la lumière chaude de nuit les réchauffe)
ROSE_TOP = (255, 218, 230)
ROSE_MID = (252, 184, 206)
ROSE_RIM = (234, 146, 176)
ROSE_OMB = (204, 116, 152)
ROSE_HI = (255, 244, 248)
PIED = (255, 228, 238)
PIED_D = (236, 180, 204)
VAN = (255, 251, 236)
VAN_OMB = (226, 212, 196)
VAN_SPECK = (120, 84, 60)
JAM = (214, 40, 78)
JAM_D = (150, 18, 52)
JAM_HI = (255, 150, 172)
SILV_D, SILV_M, SILV_L = (150, 158, 180), (218, 224, 238), (255, 255, 255)
CHOC_D, CHOC_M, CHOC_L = (62, 34, 24), (104, 60, 40), (156, 102, 70)
E_FOND = (13, 9, 11)          # fond additif très sombre
E_REFLET = (170, 172, 190)    # seul point lumineux : reflet de la fourchette


def lerp(a, b, k):
    return a + (b - a) * k


def C(c):
    return np.array(c, np.float32)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def mix(base, c, k):
    return lerp(base, C(c), np.clip(k, 0, 1)[..., None])


def finish(col, alpha, W, H):
    """Réduit la peinture sur-échantillonnée : alpha 0/255, couleur moyenne hors silhouette."""
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    solid = np.array(Image.fromarray((alpha * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = rgb
    if solid.any():
        arr[~solid, :3] = rgb[solid].mean(axis=0).astype(np.uint8)
    arr[..., 3] = solid * 255
    return arr


def e_flat(im, c=E_FOND):
    e = np.zeros(im.shape, np.uint8)
    e[..., :3] = c
    e[..., 3] = im[..., 3]
    return e


# ------------------------------------------------------------------ profil du macaron (px du modèle)
# coque : flanc à 16 pans (R_RIM, H_RIM), épaulement conique de 16 plaques (jusqu'au rayon R_CAP, hauteur H_CONE), chapeau en disque
R_RIM, H_RIM = 3.70, 0.58
R_CAP, H_CONE = 2.72, 0.62
COS16 = math.cos(math.pi / 16)
A_RIM = (R_RIM - 0.03) * COS16           # apothème du flanc
A_CAP = (R_CAP - 0.03) * COS16           # apothème du haut de l'épaulement
R_CAPD = A_CAP / COS16 + 0.05            # rayon du disque du chapeau : couvre les coins du haut des plaques
R_PIED, H_PIED = 3.86, 0.42
R_GAN, H_GAN = 3.38, 0.86
R_MAX = R_PIED + 0.04


def shell_col(r, gx, gy, rng_img):
    """Couleur du dessus d'une coque selon le rayon réel : dôme clair au centre, bord plus soutenu, reflet doux décentré."""
    col = lerp(C(ROSE_TOP), C(ROSE_MID), smooth(r / R_CAPD)[..., None] ** 1.5)
    hl = np.clip(1 - np.hypot(gx + 0.8, gy + 0.85) / 1.0, 0, 1)
    col = mix(col, ROSE_HI, smooth(hl) * 0.85)
    col = col * (1 - 0.05 * rng_img)[..., None]          # grain de la coque
    return col


def disc(R, size, seed, kind="shell"):
    """Disque vu de dessus, couvrant [-R, R] en px du modèle. kind : shell, pied."""
    w = size * SS
    g = (np.arange(w) + 0.5) / w * 2 * R - R
    gx, gy = np.meshgrid(g, g)
    r, th = np.hypot(gx, gy), np.arctan2(gy, gx)
    rng = np.random.default_rng(seed)
    grain = np.array(Image.fromarray((rng.random((size, size)) * 255).astype(np.uint8)).resize((w, w), Image.NEAREST)) / 255.0
    grain = (grain > 0.82).astype(np.float32)
    if kind == "shell":
        col = shell_col(r, gx, gy, grain)
        alpha = r < R
    else:
        # collerette : bord irrégulier, bulles, ombre de recouvrement sous la coque (r < 3,7)
        edge = R - 0.05 + 0.03 * np.sin(th * 23 + 0.4) + 0.025 * np.sin(th * 37 + 1.7) + 0.015 * np.sin(th * 61)
        alpha = r < edge
        col = np.empty(gx.shape + (3,), np.float32)
        col[...] = PIED
        bub = (np.sin(th * 47) * np.sin(r * 31 + th * 5) > 0.55)
        col = mix(col, PIED_D, bub * 0.7)
        col = mix(col, PIED_D, smooth((r - (edge - 0.07)) / 0.07) * 0.6)
        col = mix(col, ROSE_OMB, np.clip(1 - (r - R_RIM) / 0.12, 0, 1) * 0.75)
    return finish(col, alpha, size, size)


def side_tile(top, bot, W=64, H=12, seed=0, grain=True):
    """Flanc d'un étage : dégradé vertical (haut -> bas), grain léger."""
    rng = np.random.default_rng(seed)
    a = np.zeros((H, W, 4), np.float32)
    for yy in range(H):
        a[yy, :, :3] = lerp(C(top), C(bot), (yy + 0.5) / H)
    if grain:
        a[..., :3] *= (1 - 0.05 * (rng.random((H, W)) > 0.82))[..., None]
    a[..., 3] = 255
    return a.astype(np.uint8)


def pied_side(W=64, H=14):
    """Flanc de la collerette : petites bulles rondes irrégulières (pas de stries), ombre de recouvrement sous la coque."""
    rng = np.random.default_rng(7)
    w, h = W * SS, H * SS
    x, y = np.meshgrid((np.arange(w) + 0.5) / SS, (np.arange(h) + 0.5) / SS)
    col = np.empty((h, w, 3), np.float32)
    col[...] = PIED
    for _ in range(26):
        cx, cy, rx, ry = rng.uniform(0, W), rng.uniform(3, H - 2), rng.uniform(1.2, 2.4), rng.uniform(1.0, 2.0)
        d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        col = mix(col, PIED_D, (d < 1) * 0.55)
        col = mix(col, (255, 248, 250), ((d < 0.35) & (y < cy)) * 0.7)
    col = mix(col, lerp(C(PIED_D), C(ROSE_OMB), 0.5), np.clip(1 - y / 2.6, 0, 1))      # sous la coque
    col = mix(col, PIED_D, np.clip((y - (H - 1.5)) / 1.5, 0, 1) * 0.6)
    return finish(col, np.ones((h, w), bool), W, H)


def ganache_side(W=64, H=26):
    """Flanc de ganache : vanille, points de vanille, liseré de confiture au milieu (≈ 0,26 px, 8 texels), ombre sous chaque pied."""
    rng = np.random.default_rng(11)
    a = np.zeros((H, W, 4), np.float32)
    a[..., :3] = VAN
    sp = rng.random((H, W)) > 0.94
    a[sp, :3] = lerp(C(VAN), C(VAN_SPECK), 0.75)
    for yy in range(H):
        q = (yy + 0.5) / H
        o = max(0.0, 1 - min(q, 1 - q) / 0.16)
        a[yy, :, :3] = lerp(a[yy, :, :3], C(VAN_OMB), o * 0.8)
    j0, j1 = H // 2 - 4, H // 2 + 4
    a[j0:j1, :, :3] = JAM
    a[j0, :, :3] = JAM_D
    a[j1 - 1, :, :3] = JAM_D
    a[j0 + 2, :, :3] = lerp(C(JAM), C(JAM_HI), 0.8)
    # coulures : la confiture déborde par endroits
    for c_ in rng.integers(0, W - 3, 6):
        a[j1:j1 + int(rng.integers(2, 4)), c_:c_ + 3, :3] = JAM
    a[..., 3] = 255
    return a.astype(np.uint8)


def metal_tile(W=16, H=32):
    """Argent : bords sombres, filet clair (le reflet), qui est aussi la seule zone lumineuse du calque _e."""
    a = np.zeros((H, W, 4), np.float32)
    e = np.zeros((H, W, 4), np.uint8)
    for xx in range(W):
        q = (xx + 0.5) / W
        c = lerp(C(SILV_M), C(SILV_D), smooth(abs(q - 0.45) * 2.2))
        a[:, xx, :3] = c
    a[:, 4:8, :3] = SILV_L
    a[..., :3] *= np.linspace(1.0, 0.9, H)[:, None, None]
    a[..., 3] = 255
    e[..., :3] = (26, 26, 32)
    e[:, 4:8, :3] = E_REFLET
    e[..., 3] = 255
    return a.astype(np.uint8), e


def choc_tile(W=16, H=40):
    """Chocolat : brun profond, filet de reflet, quelques vermicelles roses (ensemble Pâtisserie)."""
    rng = np.random.default_rng(5)
    a = np.zeros((H, W, 4), np.float32)
    for xx in range(W):
        q = (xx + 0.5) / W
        a[:, xx, :3] = lerp(C(CHOC_M), C(CHOC_D), smooth(abs(q - 0.4) * 2.4))
    a[:, 4:7, :3] = lerp(C(CHOC_M), C(CHOC_L), 0.9)
    for _ in range(7):
        x0, y0 = int(rng.integers(1, W - 4)), int(rng.integers(2, H - 4))
        a[y0:y0 + 2, x0:x0 + 3, :3] = (ROSE_MID if rng.random() < 0.6 else VAN)
    a[..., 3] = 255
    return a.astype(np.uint8)


# ------------------------------------------------------------------ atlas
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_cur = [0, 0, 0]


def place(name, im, em=None):
    h, w = im.shape[:2]
    if _cur[0] + w > TEX:
        _cur[:] = [0, _cur[1] + _cur[2] + 2, 0]
    x, y = _cur[0], _cur[1]
    assert y + h <= TEX - 6, "atlas plein"
    tex[y:y + h, x:x + w] = im
    tex_e[y:y + h, x:x + w] = e_flat(im) if em is None else em
    UV[name] = (x, y, x + w, y + h)
    _cur[0] += w + 2
    _cur[2] = max(_cur[2], h)


place("cap", disc(R_CAPD, 72, 100))
rd = np.zeros((40, 40, 4), np.uint8)
yy_, xx_ = np.mgrid[0:40, 0:40]
rd[..., :3] = ROSE_RIM
rd[..., 3] = (np.hypot(xx_ - 19.5, yy_ - 19.5) < 20) * 255
place("rimdisc", rd)
place("disc_pied", disc(R_MAX, int(round(R_MAX * 26)), 120, kind="pied"))
place("rim_side", side_tile(ROSE_RIM, tuple(lerp(C(ROSE_RIM), C(ROSE_OMB), 0.55)), H=20, seed=200))


def cone_tile(W=30, H=30):
    """Plaque de l'épaulement : trapèze (haut = côté chapeau, plus étroit), dégradé du rose du chapeau vers celui du flanc."""
    w, h = W * SS, H * SS
    x, y = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    half = 0.5 * lerp(A_CAP / A_RIM, 1.0, y)
    alpha = np.abs(x - 0.5) < half + 0.01
    col = lerp(C(ROSE_MID), C(ROSE_RIM), smooth(y)[..., None])
    rng = np.random.default_rng(3)
    gr = np.array(Image.fromarray(((rng.random((H, W)) > 0.82) * 255).astype(np.uint8)).resize((w, h), Image.NEAREST)) / 255.0
    col = col * (1 - 0.05 * gr)[..., None]
    return finish(col, alpha, W, H)


place("cone", cone_tile())
place("pied_side", pied_side())
place("gan_side", ganache_side())
m_, me_ = metal_tile()
place("metal", m_, me_)
place("choc", choc_tile())

CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC
assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
assert tex_e[..., :3].max() <= 200, "calque trop vif"
_b64 = []
for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(fn, optimize=True)
    _buf = io.BytesIO()
    im_.save(_buf, "PNG", optimize=True)
    _b64.append("data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode())
tex_b64, tex_e_b64 = _b64

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


def rot_matrix(rx, ry, rz):
    """Même ordre que le mod et le renderer : R = Rz Ry Rx, degrés."""
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def euler(R):
    """Angles (X, Y, Z) tels que R = Rz Ry Rx ; cas du blocage de cardan (Y = ±90°) traité à part (Z = 0)."""
    if abs(R[2, 0]) > 0.99999:
        sg = -1.0 if R[2, 0] > 0 else 1.0           # Y = sg * 90°
        out = (math.degrees(math.atan2(sg * R[0, 1], R[1, 1])), sg * 90.0, 0.0)
    else:
        ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
        out = (math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0])))
    assert np.allclose(rot_matrix(*out), R, atol=1e-6), "euler : rotation mal reconstruite"
    return out


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups and len(name) <= 64
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(float(v), 2) for v in rotation]}
    return name


def add_el(g, name, c, size, rot, faces):
    c, size = np.asarray(c, float), np.asarray(size, float)
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in c - size / 2],
         "to": [round(float(v), 3) for v in c + size / 2], "origin": [round(float(v), 3) for v in c], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def cube_axes(g, name, c, size, X, Y, faces):
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    add_el(g, name, c, size, euler(R_), faces)


def all_faces(tile):
    return {f: list(UV[tile]) for f in ("north", "south", "east", "west", "up", "down")}


# Placement : macaron droit, axe vertical en (CX, CZ), bas de la coque basse en y = Y0 (fixé plus bas pour reposer sur la tête)
CX, CZ = 1.0, 0.1
TILT = (3.0, 0.0, -16.0)        # +X : le haut part vers l'arrière ; -Z : le côté droit (+X) descend (guide, section 3)
SHELL_H = H_RIM + H_CONE + 0.05
TOTAL_H = 2 * SHELL_H + 2 * H_PIED + H_GAN
RT = rot_matrix(*TILT)

# point de contact : point le plus bas, après bascule, du bord des étages de la coque basse (macaron posé en y = 0)
cands = []
for R, y in ((R_CAPD, 0.0), (R_RIM, H_CONE)):
    for a in np.linspace(0, TAU, 72, endpoint=False):
        cands.append(V(CX + R * math.cos(a), y, CZ + R * math.sin(a)))
low = min(cands, key=lambda p: (RT @ p)[1])
HEAD_TOP = 32.25                # 0,25 px au-dessus de la tête ; entre de 0,25 px dans la seconde couche du skin, au seul point de contact
Y0 = HEAD_TOP - low[1]
PIV = V(low[0], HEAD_TOP, low[2])

MAC = group("macaron", PIV, rotation=TILT)


def ring(g, name, y0, R, h, side_tile_, n=16, flip=False):
    """Âme polygonale à n pans (n = 16 ou 8), inscrite dans le disque de rayon R : union de n/2 barreaux 2a × 2a·tan(π/n)
    tournés de 360/n degrés (a = apothème). Chaque barreau couvre exactement son secteur : la réunion est le polygone, sans pointes.
    Seuls les bouts (les pans) sont peints ; faces longues, dessus et dessous transparents (internes ou couverts par le disque)."""
    a = (R - 0.03) * math.cos(math.pi / n)
    w = a * math.tan(math.pi / n)
    u0, v0, u1, v1 = UV[side_tile_]
    sf = [u0, v1, u1, v0] if flip else [u0, v0, u1, v1]
    for k in range(n // 2):
        add_el(g, f"{name}_{k}", V(CX, y0 + h / 2, CZ), (2 * a, h - 0.04, 2 * w), (0, k * 360.0 / n, 0),
               {"east": sf, "west": sf, "north": CLEAR, "south": CLEAR, "up": CLEAR, "down": CLEAR})


def disc_skin(g, name, y0, R, h, tile, face):
    """Peau : disque découpé par alpha, une seule face visible (up ou down), tranches transparentes."""
    faces = {f: CLEAR for f in ("north", "south", "east", "west", "up", "down")}
    u0, v0, u1, v1 = UV[tile]
    for fc in face.split("+"):
        faces[fc] = [u0, v0, u1, v1] if fc == "up" else [u0, v1, u1, v0]
    add_el(g, name, V(CX, y0 + h / 2, CZ), (2 * R, h, 2 * R), (0, 0, 0), faces)


def shell(name, y_base, sg):
    """Coque partant du pied en y_base, vers le haut (sg = +1) ou vers le bas (sg = -1). Renvoie la hauteur du sommet du chapeau."""
    face = "up" if sg > 0 else "down"
    y1 = y_base + sg * H_RIM
    ring(MAC, f"{name}_flanc", min(y_base, y1), R_RIM, H_RIM, "rim_side", flip=sg < 0)
    disc_skin(MAC, f"{name}_flanc_peau", min(y_base, y1), R_RIM, H_RIM, "rimdisc", face)
    y2 = y1 + sg * H_CONE
    ctr = V(CX, 0, CZ)
    w_bot = 2 * A_RIM * math.tan(math.pi / 16)
    u0, v0, u1, v1 = UV["cone"]
    for m in range(16):
        th = math.radians(m * 22.5)
        n_ = V(math.cos(th), 0, -math.sin(th))
        t_ = V(math.sin(th), 0, math.cos(th))
        P1 = ctr + n_ * A_RIM + V(0, y1, 0)
        P2 = ctr + n_ * A_CAP + V(0, y2, 0)
        Y_ = unit(P2 - P1)
        Z_ = np.cross(t_, Y_)
        out = 1.0 if Z_ @ n_ > 0 else -1.0
        L_ = float(np.linalg.norm(P2 - P1)) + 0.05
        c_ = (P1 + P2) / 2 + Y_ * 0.025 - Z_ * out * 0.15
        faces = {f: CLEAR for f in ("north", "south", "east", "west", "up", "down")}
        faces["south" if out > 0 else "north"] = [u0, v0, u1, v1] if out > 0 else [u1, v0, u0, v1]
        cube_axes(MAC, f"{name}_epaule{m}", c_, (w_bot, L_, 0.3), t_, Y_, faces)
    y_top = y2 + sg * 0.05
    disc_skin(MAC, f"{name}_chapeau", min(y_top, y_top - sg * 0.3), R_CAPD, 0.3, "cap", face)
    return y_top


# coque basse (construite depuis son pied, vers le bas), pied bas, ganache, pied haut, coque haute
yb = Y0 + SHELL_H
shell("coque_b", yb, -1)
ring(MAC, "pied_b", yb, R_PIED - 0.02, H_PIED, "pied_side", flip=True)
disc_skin(MAC, "pied_b_peau", yb, R_MAX, H_PIED, "disc_pied", "down+up")
yb += H_PIED
Y_GAN = yb + H_GAN / 2
ring(MAC, "ganache", yb, R_GAN, H_GAN + 0.04, "gan_side")
yb += H_GAN
ring(MAC, "pied_h", yb, R_PIED - 0.02, H_PIED, "pied_side")
disc_skin(MAC, "pied_h_peau", yb, R_MAX, H_PIED, "disc_pied", "up+down")
yb += H_PIED
yb = shell("coque_h", yb, +1)
Y_TOP = yb
assert abs((Y_TOP - Y0) - TOTAL_H) < 1e-6

# Fourchette : plantée près du sommet, côté gauche-arrière, penchée vers la gauche et l'arrière (repère du macaron droit)
INS = V(CX - 0.5, Y_TOP, CZ + 0.4)
D = unit(V(-0.72, 1.0, 0.5))                      # des dents vers le manche
XF = unit(np.cross(V(0, 0, 1), D))                # écartement des dents
XF = -XF if XF[0] > 0 else XF
FORK = group("fourchette", INS, parent=MAC)
BASE = INS - D * 0.6                              # bout des dents, enfoncé de 0,6 px


def fseg(name, u0, u1, w, t, tile, dx=0.0):
    c = BASE + D * ((u0 + u1) / 2) + XF * dx
    cube_axes(FORK, name, c, (w, u1 - u0, t), XF, D, all_faces(tile))


for k, dx in enumerate((-0.62, 0.0, 0.62)):
    fseg(f"dent{k}", 0.0, 1.78 - 0.08 * abs(k - 1), 0.42, 0.32, "metal", dx)
fseg("tete", 1.58, 2.06, 1.70, 0.40, "metal")
fseg("epaule", 1.98, 2.40, 1.05, 0.34, "metal")
fseg("col", 2.30, 3.80, 0.55, 0.42, "metal")
fseg("manche", 3.66, 6.20, 0.80, 0.52, "choc")
fseg("bout", 6.10, 6.50, 0.58, 0.46, "choc")
TIP = BASE + D * 6.5


# MIROIR D'AXES : seul endroit à toucher si la convention change (guide, section 3).
# Intentions : side > 0 = penche davantage vers son côté bas (droite, +X) ; back > 0 = le haut part vers l'arrière ; twist > 0 = le côté droit avance.
SX, SY, SZ = +1, +1, -1


def mirror(side, back, twist=0.0):
    return SX * back, SY * twist, SZ * side


# ------------------------------------------------------------------ poses : points du modèle après animation (contrôle d'appui sur la tête)
_by = {e["uuid"]: e for e in elements}


def corners(g):
    out = []
    for eid in groups[g]["ids"]:
        e = _by[eid]
        a, b = np.array(e["from"]), np.array(e["to"])
        Re, oe = rot_matrix(*e.get("rotation", (0, 0, 0))), np.array(e["origin"])
        for cx in (a[0], b[0]):
            for cy in (a[1], b[1]):
                for cz in (a[2], b[2]):
                    out.append(Re @ (V(cx, cy, cz) - oe) + oe)
    return np.array(out)


def shift_y(dy):
    for g in (MAC, FORK):
        groups[g]["origin"][1] = round(groups[g]["origin"][1] + dy, 3)
        for eid in groups[g]["ids"]:
            e = _by[eid]
            for k in ("from", "to", "origin"):
                e[k][1] = round(e[k][1] + dy, 3)


def pose_pts(m, f=None, pts_m=None, pts_f=None):
    def T(g, s):
        o = np.array(groups[g]["origin"])
        R = rot_matrix(*(np.array(groups[g]["rotation"]) + np.array(mirror(*s.get("rot", (0, 0, 0))))))
        S = np.array(s.get("scale", (1, 1, 1)))
        P = np.array(s.get("pos", (0, 0, 0)))
        return lambda p: (R @ (S * (p - o)).T).T + o + P
    Tm = T(MAC, m)
    out = Tm(corners(MAC) if pts_m is None else pts_m)
    if f is not None:
        out = np.vstack([out, Tm(T(FORK, f)(corners(FORK) if pts_f is None else pts_f))])
    return out


def ymin_head(P):
    over = (np.abs(P[:, 0]) < 4.5) & (np.abs(P[:, 2]) < 4.5)
    return float(P[over, 1].min()) if over.any() else 99.0


# pose de base : posé sur la tête (HEAD_TOP)
_dy = HEAD_TOP - ymin_head(pose_pts({}))
shift_y(_dy)
TIP = TIP + V(0, _dy, 0)
PTS_M, PTS_F = corners(MAC), corners(FORK)
PIV = np.array(groups[MAC]["origin"])


def rest_on_head(s):
    """Ajoute la remontée nécessaire pour que la pose repose sur la tête au lieu d'y entrer (le macaron s'appuie, il ne traverse pas)."""
    lift = max(0.0, HEAD_TOP - ymin_head(pose_pts(s, pts_m=PTS_M)))
    p = list(s.get("pos", (0, 0, 0)))
    p[1] += lift
    s = dict(s)
    s["pos"] = tuple(p)
    return s



def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone(MAC)]}]


# ------------------------------------------------------------------ animations

def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def per(L, k=1, ph=0.0):
    """sin de période L/k, déphasé de ph (en fraction de cycle)."""
    return lambda t: math.sin(TAU * (k * t / L - ph))


POSES = {}      # nom d'anim -> (L, fonctions) pour le contrôle d'intersection


def anim(name, L, mac, fork, loop="loop", fps=10):
    """mac(t), fork(t) -> dict(rot=(side, back, twist), pos=(x, y, z), scale=(sx, sy, sz)) ; les deux en intention."""
    n = max(8, int(round(L * fps)))
    times = [i * L / n for i in range(n + 1)]
    A = {}
    for g, f in ((MAC, mac), (FORK, fork)):
        kfs = []
        samples = [(t, f(t % L if loop == "loop" and t < L - 1e-9 else (0.0 if loop == "loop" else t))) for t in times]
        if g == MAC:
            samples = [(t, rest_on_head(s_)) for t, s_ in samples]
        if any(s.get("rot") for _, s in samples):
            kfs += [kf("rotation", t, mirror(*s.get("rot", (0, 0, 0)))) for t, s in samples]
        if any(s.get("pos") for _, s in samples):
            kfs += [kf("position", t, s.get("pos", (0, 0, 0))) for t, s in samples]
        if any(s.get("scale") for _, s in samples):
            kfs += [kf("scale", t, s.get("scale", (1, 1, 1))) for t, s in samples]
        if kfs:
            A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}
    POSES[name] = (L, mac, fork, loop)
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": L, "snapping": 24,
            "selected": name == "idle", "animators": A}


def squash(k):
    """k > 0 : se tasse (volume à peu près conservé) ; k < 0 : s'étire."""
    return (1 + 0.45 * k, 1 - k, 1 + 0.45 * k)


# Le macaron repose sur son bord droit : il ne peut que se soulever de l'autre côté (side <= 0 surtout), sinon il entrerait dans la tête.
def rock(t, L, k, amp, ph=0.0):
    s = per(L, k, ph)(t)
    return -amp * (0.5 + 0.5 * s)          # entre -amp et 0


# idle 8 s : léger balancement (période 4 s) et, vers 5 s, petit « boing » (tassement puis rebond)
def idle_m(t):
    b = bump(t, 4.9, 5.15, 5.2, 5.6)
    r = bump(t, 5.4, 5.65, 5.75, 6.3)
    return {"rot": (rock(t, 8, 2, 1.2), 0.4 * per(8, 2, 0.25)(t), 0), "scale": squash(0.07 * b - 0.04 * r),
            "pos": (0, 0.12 * r, 0)}


def idle_f(t):
    b = bump(t, 5.05, 5.3, 5.4, 6.4)
    return {"rot": (-0.8 * per(8, 2, 0.12)(t) + 4.0 * b * math.sin(TAU * (t - 5.05) * 2.2), 0.6 * per(8, 2, 0.4)(t), 0)}


# walk 1,6 s (2 pas) : vacille au pas, petits sauts ; la fourchette suit avec ~0,15 cycle de retard
def walk_m(t):
    return {"rot": (rock(t, 1.6, 2, 3.0), 1.2 * per(1.6, 2, 0.25)(t), 0.8 * per(1.6, 1)(t)),
            "pos": (0, 0.18 * (0.5 - 0.5 * math.cos(TAU * 2 * t / 1.6)), 0), "scale": squash(0.03 * math.cos(TAU * 2 * t / 1.6))}


def walk_f(t):
    return {"rot": (-3.5 * per(1.6, 2, 0.15)(t), 2.0 * per(1.6, 2, 0.4)(t), 1.5 * per(1.6, 1, 0.15)(t))}


# run 1,0 s : vent de face, le macaron se penche en arrière et vacille fort, la fourchette tremble
def run_m(t):
    return {"rot": (rock(t, 1.0, 2, 4.5), 4.0 + 2.0 * per(1.0, 2, 0.25)(t), 1.2 * per(1.0, 1)(t)),
            "pos": (0, 0.28 * (0.5 - 0.5 * math.cos(TAU * 2 * t)), 0), "scale": squash(0.05 * math.cos(TAU * 2 * t))}


def run_f(t):
    return {"rot": (-5.0 * per(1.0, 2, 0.18)(t), 9.0 + 3.0 * per(1.0, 4, 0.2)(t), 2.0 * per(1.0, 2, 0.4)(t))}


# sneak 3 s : se tasse, respire doucement
def sneak_m(t):
    return {"rot": (rock(t, 3, 1, 1.0), -1.0, 0), "scale": squash(0.12 + 0.025 * per(3, 1)(t))}


def sneak_f(t):
    return {"rot": (0.8 * per(3, 1, 0.15)(t), -3.0 + 1.0 * per(3, 1, 0.2)(t), 0)}


# fly 2,4 s : le vent couche la fourchette, le macaron ondule
def fly_m(t):
    return {"rot": (rock(t, 2.4, 1, 2.5), 6.0 + 2.0 * per(2.4, 1, 0.25)(t), 1.5 * per(2.4, 1)(t)), "scale": squash(-0.03 * per(2.4, 1)(t))}


def fly_f(t):
    return {"rot": (-3.0 * per(2.4, 1, 0.15)(t), 14.0 + 3.0 * per(2.4, 3, 0.2)(t), 2.0 * per(2.4, 2)(t))}


# glide 3,6 s et swim 3,6 s : corps couché, la tête regarde devant : le flux couche tout vers l'arrière
def glide_m(t):
    return {"rot": (rock(t, 3.6, 2, 2.0), 9.0 + 1.5 * per(3.6, 2, 0.25)(t), 0.8 * per(3.6, 1)(t))}


def glide_f(t):
    return {"rot": (-2.0 * per(3.6, 2, 0.15)(t), 20.0 + 4.0 * per(3.6, 6, 0.2)(t), 0)}


def swim_m(t):
    return {"rot": (rock(t, 3.6, 1, 2.5), 5.0 + 2.5 * per(3.6, 1, 0.25)(t), 1.5 * per(3.6, 1)(t))}


def swim_f(t):
    return {"rot": (-3.0 * per(3.6, 1, 0.2)(t), 10.0 + 4.0 * per(3.6, 2, 0.3)(t), 0)}


# fall 1,2 s : en l'air, le macaron décolle un peu et s'étire, la fourchette se redresse
def fall_m(t):
    return {"rot": (rock(t, 1.2, 1, 2.0), -2.0, 0), "pos": (0, 0.35 + 0.08 * per(1.2, 1)(t), 0), "scale": squash(-0.06 + 0.015 * per(1.2, 2)(t))}


def fall_f(t):
    return {"rot": (1.5 * per(1.2, 2, 0.15)(t), -6.0 + 2.0 * per(1.2, 1, 0.2)(t), 0)}


# hurt 0,8 s, une fois : sursaut (décolle, se tasse à l'atterrissage), tremblement amorti de la fourchette ; dernière image au neutre
def hurt_m(t):
    up = bump(t, 0.0, 0.1, 0.16, 0.36)
    land = bump(t, 0.3, 0.38, 0.42, 0.62)
    return {"rot": (-6.0 * up + 1.5 * math.sin(TAU * t * 4 / 0.8) * (1 - sm(t, 0.3, 0.75)) * (t > 0.3) * -1, 3.0 * up, 0),
            "pos": (0, 1.1 * up, 0), "scale": squash(-0.08 * up + 0.12 * land)}


def hurt_f(t):
    v = math.sin(TAU * t * 6 / 0.8) * (1 - sm(t, 0.1, 0.78))
    return {"rot": (9.0 * v * (t > 0.05), -10.0 * bump(t, 0.0, 0.1, 0.2, 0.5), 0)}


ANIMS = [anim("idle", 8.0, idle_m, idle_f, fps=8), anim("walk", 1.6, walk_m, walk_f), anim("run", 1.0, run_m, run_f, fps=12),
         anim("sneak", 3.0, sneak_m, sneak_f), anim("fly", 2.4, fly_m, fly_f), anim("glide", 3.6, glide_m, glide_f, fps=8),
         anim("swim", 3.6, swim_m, swim_f, fps=8), anim("fall", 1.2, fall_m, fall_f),
         anim("hurt", 0.8, hurt_m, hurt_f, loop="once", fps=20)]


# ------------------------------------------------------------------ contrôle : rien ne doit entrer dans la tête (seconde couche comprise), dans aucune pose
worst = 99.0
for name, (L, mf, ff, loop) in POSES.items():
    for t in np.linspace(0, L, 41):
        worst = min(worst, ymin_head(pose_pts(rest_on_head(mf(t)), ff(t), PTS_M, PTS_F)))
assert worst >= HEAD_TOP - 0.05, f"le macaron entre dans la tête : y min {worst:.2f}"

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
assert 60 <= len(elements) <= 150, f"budget : {len(elements)} cubes"
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      f"y min sur la tête {worst:.2f} ; pivot {PIV.round(2).tolist()} ; haut de la fourchette {TIP.round(2).tolist()}")
