"""Vortex spatial (v1) : effet de téléportation sans ensemble (guide 15). Design original, fiche de référence
.claude/references/effets/vortex-distorsion.md (grammaire visuelle d'une distorsion en spirale, déroulé, couleurs, sons).
Écrit effet_vortex.png, effet_vortex_e.png et .build/effet_vortex_brut.bbmodel.

Idée : l'espace se tord en spirale autour du joueur et l'aspire en un point (départ) ; à l'arrivée, la spirale tourne à
l'envers et le recrache.

Pièces (posées au sol, pieds du joueur à l'origine, face à -Z ; aucun groupe du corps ; centre du vortex C = (0, 17, 0))
- Spirale face caméra (cam_) : cinq bras logarithmiques trans_ gris-violet sombre à bord clair, peints à 4,9 texels par px
  (bras lisses), découpés en trois anneaux concentriques qui tournent à des vitesses différentes (la spirale se resserre) ;
  plaque d'anneaux concentriques ondulés derrière le joueur ; lueur add_ violette des bords (nuit) ; trou sombre au centre
  (trans_) cerclé d'un halo add_ ; flash add_ en étoile à l'implosion ; onde de choc (anneau trans_ + add_).
- Spirale au sol (même peinture, face up), onde au sol, quatre cerceaux de distorsion horizontaux autour du corps et trois
  anneaux d'ondulation face caméra (charge : l'air ondule).
- 14 fragments d'espace (petits cubes sombres à arête claire) en orbite, aspirés en spirale de plus en plus vite.
- Particules (31 points emit_, ctrl_emit chacun) : poussiere, fragment, eclat (modélisées) ; portal, reverse_portal,
  smoke, squid_ink (Minecraft). Les points de poussière, fragment et encre tournent avec le tourbillon et visent le centre
  (départ) ou le dehors (arrivée).

Animations : charge (loop 4,8 s), depart (3,6 s : la spirale se forme, le joueur est tordu et aspiré au centre en
rétrécissant, implosion en un point, petite onde), arrivee (3,4 s : point, la spirale tourne à l'envers et recrache le
joueur, onde de choc au sol, la spirale se déroule et s'efface), particle_*_fall.
Groupe joueur : position vers le centre et échelle 1 -> 0 (départ), 0 -> 1 depuis le centre (arrivée) ; rien dans charge.
Sons embarqués originaux (sons/*.py, tools/synthe.py) : départ vortex_torsion, vortex_aspiration, vortex_implosion ;
arrivée vortex_detorsion, vortex_expulsion ; aucun pendant la charge.

Fonctions avancées : cam_, trans_, add_, ctrl_alpha, ctrl_emit, _e, emit_ / emit_mc_, particle_, groupe joueur, sons
embarqués. Ce qui se juge seulement en jeu (onglet Effets, « Essayer ») : particules et leur direction (portal converge-t-il
vers le centre ?), additif réel, tri trans_ des couches autour du joueur avec et sans shader, volume des sons.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "effet_vortex"
TEX = 512
SS = 3
RNG = np.random.default_rng(57)

C = (0.0, 17.0, 0.0)          # centre du vortex (torse du joueur)
R = 23.0                      # rayon de la spirale face caméra (px)
NA, PAS = 6, 6.0              # nombre de bras, enroulement (psi = NA*theta + PAS*ln r : ~140° de courbure)


# ------------------------------------------------------------------ outils de peinture
def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def grille(W, H, ss=SS):
    n_w, n_h = W * ss, H * ss
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w * 2 - 1, 1 - (np.arange(n_h) + 0.5) / n_h * 2)


def lanczos(a, W, H):
    return np.array(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)).astype(np.float32)


def flou(f, N):
    im = Image.fromarray(np.clip(f * 255, 0, 255).astype(np.uint8))
    im = im.resize((max(2, N // 3), max(2, N // 3)), Image.BILINEAR).resize((N, N), Image.BILINEAR)
    return np.clip(np.asarray(im).astype(np.float32) / 255 * 1.5, 0, 1)


def sur(rgb_d, a_d, rgb_s, a_s):
    """Composition « par-dessus » en alpha droit (a dans 0..1)."""
    a = a_s + a_d * (1 - a_s)
    num = rgb_s * a_s[..., None] + rgb_d * (a_d * (1 - a_s))[..., None]
    rgb = np.where(a[..., None] > 1e-4, num / np.maximum(a, 1e-4)[..., None], rgb_s)
    return rgb, a


def vers_trans(rgb, a, N, seuil=5):
    """RGBA trans_ (alpha 1..254) réduit par LANCZOS ; la couleur garde sa valeur sous l'alpha (pas de liseré noir)."""
    c = np.stack([lanczos(rgb[..., k], N, N) for k in range(3)], axis=-1)
    al = lanczos(a * 255, N, N)
    arr = np.zeros((N, N, 4), np.uint8)
    al = np.where(al > seuil, np.clip(al, 1, 254), 0)
    arr[..., :3] = c
    arr[..., 3] = al
    arr[al == 0, :3] = 0
    return arr


def vers_add(f, couleur, N, gain):
    """Additif : couleur * intensité ; presque noir = transparent ; alpha 0/255."""
    arr = np.zeros((N, N, 4), np.uint8)
    for k in range(3):
        arr[..., k] = np.clip(f * couleur[k] * gain, 0, 255).astype(np.uint8)
    a = arr[..., :3].max(axis=2) > 8
    arr[..., 3] = a * 255
    arr[~a, :3] = 0
    return arr


def vers_opaque(rgb, a, N, seuil=110):
    c = np.stack([lanczos(rgb[..., k], N, N) for k in range(3)], axis=-1)
    al = lanczos(a * 255, N, N)
    arr = np.zeros((N, N, 4), np.uint8)
    arr[..., :3] = c
    arr[..., 3] = np.where(al > seuil, 255, 0)
    arr[arr[..., 3] == 0, :3] = 0
    return arr


# ------------------------------------------------------------------ peinture
GRIS_SOMBRE, GRIS_CLAIR = np.array([26, 20, 42.0]), np.array([78, 66, 110.0])
BORD = np.array([228, 218, 252.0])
TRAIT = np.array([186, 172, 226.0])
VOILE = np.array([150, 140, 184.0])


def spirale(N, rtex, rmin=None, rmax=None):
    """Bras de spirale (trans_) : disque de rayon normalisé rtex (1 = rayon R) peint en N texels.
    rmin / rmax : anneau gardé (fondu de 0,03 de part et d'autre). Renvoie (rgba, bord N×N pour _e et lueur)."""
    x, y = grille(N, N)
    x, y = x * rtex, y * rtex
    r = np.hypot(x, y) + 1e-6
    th = np.arctan2(y, x)
    g = math.hypot(NA, PAS)
    u = ((NA * th + PAS * np.log(r)) / (2 * math.pi)) % 1.0
    per = 2 * math.pi * r / g                     # distance (en rayons) par unité de phase
    w = 0.46
    aa = rtex * 2 / N                            # un texel
    dl, dt = (w - u) * per, u * per              # distance au bord d'attaque (clair) et au bord de fuite (fondu)
    dedans = (u < w).astype(np.float32)
    sd = np.where(u < w, dl, -(u - w) * per)       # distance signée au bord d'attaque (> 0 dans le bras)
    # profils doux, sans marche d'alpha (le jeu échantillonne au plus proche : un bord dur fait des escaliers)
    cov = dedans * np.clip(sd / 0.022, 0, 1) * np.clip(dt / 0.09, 0, 1) ** 0.8
    rim = np.exp(-((sd - 0.014) / 0.016) ** 2) * (sd > -0.04)
    traits = np.zeros_like(r)
    for f in (0.33, 0.6):
        ds = np.abs(u - f * w) * per
        traits = np.maximum(traits, dedans * np.clip((0.012 - ds) / aa + 0.5, 0, 1) * (1 - f * 0.4))
    env = smooth((0.99 - r) / 0.2)               # fondu extérieur
    centre = smooth((r - 0.05) / 0.12)           # les bras se perdent dans le trou central
    # couleurs
    k = np.clip(r, 0, 1)[..., None]
    corps = GRIS_SOMBRE * (1 - k) + GRIS_CLAIR * k
    rgb = np.broadcast_to(VOILE, r.shape + (3,)).copy()
    a = 0.11 * env * (1 - cov)
    rgb, a = sur(rgb, a, corps, cov * env * (0.74 + 0.14 * (1 - k[..., 0])))
    rgb, a = sur(rgb, a, np.broadcast_to(TRAIT, r.shape + (3,)), traits * env * centre * 0.5)
    rgb, a = sur(rgb, a, np.broadcast_to(BORD, r.shape + (3,)), rim * env * centre * 0.93)
    masque = np.ones_like(r)
    if rmin is not None:
        masque *= smooth((r - rmin + 0.03) / 0.06)
    if rmax is not None:
        masque *= smooth((rmax + 0.03 - r) / 0.06)
    a = a * masque
    bord = lanczos(rim * env * centre * masque * 255, N, N) / 255
    return vers_trans(rgb, a, N), bord


def anneaux_tex(N):
    """Anneaux concentriques ondulés (plaque derrière le joueur) : filets clairs, bande sombre en dedans, vide au centre."""
    x, y = grille(N, N)
    r = np.hypot(x, y) + 1e-6
    th = np.arctan2(y, x)
    aa = 2 / N
    rgb = np.broadcast_to(VOILE, r.shape + (3,)).copy()
    a = 0.06 * smooth((0.98 - r) / 0.15)
    vide = np.clip(1 - r / 0.34, 0, 1) ** 1.3
    rgb, a = sur(rgb, a, np.broadcast_to(np.array([8, 5, 15.0]), r.shape + (3,)), vide * 0.62)
    for j, r0 in enumerate((0.32, 0.5, 0.67, 0.84)):
        rr = r * (1 + 0.03 * np.sin(7 * th + 1.9 * j))
        d = rr - r0
        bande = np.clip((-d) / 0.07, 0, 1) * np.clip((d + 0.07) / aa, 0, 1) * (1 - np.clip((-d) / 0.07, 0, 1)) * 4
        rgb, a = sur(rgb, a, np.broadcast_to(GRIS_SOMBRE, r.shape + (3,)), np.clip(bande, 0, 1) * 0.42)
        fil = np.exp(-(d / 0.016) ** 2)
        rgb, a = sur(rgb, a, np.broadcast_to(BORD, r.shape + (3,)), fil * (0.55 + 0.1 * j))
    a = a * smooth((0.99 - r) / 0.06)
    fil_e = lanczos(np.clip(a, 0, 1) * 0, N, N)
    return vers_trans(rgb, a, N), fil_e


def anneau_tex(N, r0=0.86):
    """Anneau fin (ondulation de l'air, onde de choc) : filet clair et bande de miroitement en dedans."""
    x, y = grille(N, N)
    r = np.hypot(x, y)
    aa = 2 / N
    fil = np.exp(-((r - r0) / 0.022) ** 2)
    band = np.clip((r - 0.55) / (r0 - 0.55), 0, 1) ** 2 * (r < r0)
    rgb = np.broadcast_to(np.array([176, 166, 212.0]), r.shape + (3,)).copy()
    a = band * 0.16
    ombre = np.exp(-((r - r0 + 0.05) / 0.02) ** 2)          # filet sombre en dedans : l'anneau se lit comme une réfraction
    rgb, a = sur(rgb, a, np.broadcast_to(np.array([40, 32, 62.0]), r.shape + (3,)), ombre * 0.45)
    rgb, a = sur(rgb, a, np.broadcast_to(BORD, r.shape + (3,)), fil * 0.82)
    return vers_trans(rgb, a, N), lanczos(fil * 255, N, N) / 255


def anneau_add_f(N, r0=0.86):
    x, y = grille(N, N)
    r = np.hypot(x, y)
    return lanczos(np.clip(1 - np.abs(r - r0) / 0.12, 0, 1) ** 1.6 * 255, N, N) / 255


def trou_tex(N):
    """Trou sombre du centre (trans_) : disque presque noir violacé, bord fondu, fin liseré clair."""
    x, y = grille(N, N)
    r = np.hypot(x, y)
    aa = 2 / N
    rgb = np.broadcast_to(np.array([10, 6, 20.0]), r.shape + (3,)).copy()
    a = 0.9 * smooth((0.72 - r) / 0.3)
    fil = np.exp(-((r - 0.66) / 0.03) ** 2)
    rgb, a = sur(rgb, a, np.broadcast_to(np.array([200, 186, 240.0]), r.shape + (3,)), fil * 0.6)
    return vers_trans(rgb, a, N)


def halo_f(N):
    x, y = grille(N, N)
    r = np.hypot(x, y)
    return lanczos(np.clip(1 - np.abs(r - 0.68) / 0.3, 0, 1) ** 1.5 * 255, N, N) / 255


def flash_f(N):
    x, y = grille(N, N)
    r = np.hypot(x, y) + 1e-6
    th = np.arctan2(y, x)
    etoile = np.clip(1 - r / (0.22 + 0.75 * np.abs(np.cos(2 * th)) ** 18), 0, 1) ** 1.4
    coeur = np.clip(1 - r / 0.35, 0, 1) ** 1.2
    return lanczos(np.maximum(etoile, coeur) * 255, N, N) / 255


def fragment_tex(N, seed):
    """Fragment d'espace (cube opaque) : face sombre violacée, arête claire d'un texel, reflet en coin."""
    rng = np.random.default_rng(seed)
    arr = np.zeros((N, N, 4), np.uint8)
    base = np.array([30, 22, 48]) if seed % 2 == 0 else np.array([44, 34, 66])
    for i in range(N):
        for j in range(N):
            v = base + rng.integers(-4, 5)
            if i in (0, N - 1) or j in (0, N - 1):
                v = np.array([204, 192, 238]) if (i + j) % 3 else np.array([168, 154, 210])
            arr[i, j, :3] = np.clip(v, 0, 255)
    arr[1, 1, :3] = (120, 106, 160)
    arr[..., 3] = 255
    return arr


def poussiere_tex(N=8):
    x, y = grille(N, N, 6)
    r = np.hypot(x, y)
    a = (r < 0.85).astype(np.float32)
    k = np.clip(1 - r, 0, 1)[..., None]
    rgb = np.array([70, 60, 102.0]) * (1 - k) + np.array([196, 184, 232.0]) * k
    return vers_opaque(rgb, a, N)


def eclat_part_tex(N=16):
    x, y = grille(N, N, 6)
    r = np.hypot(x, y) + 1e-6
    th = np.arctan2(y, x)
    a = (r < 0.18 + 0.78 * np.abs(np.cos(2 * th)) ** 10).astype(np.float32)
    k = np.clip(1 - r, 0, 1)[..., None]
    rgb = np.array([170, 150, 230.0]) * (1 - k) + np.array([246, 240, 255.0]) * k
    return vers_opaque(rgb, a, N)


def frag_part_tex(N=16):
    """Éclat d'espace (particule) : tesson triangulaire sombre, bord clair."""
    x, y = grille(N, N, 6)
    p = [(-0.75, -0.7), (0.8, -0.35), (-0.1, 0.85)]
    def cote(a, b):
        return (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])
    d = np.minimum(np.minimum(cote(p[0], p[1]), cote(p[1], p[2])), cote(p[2], p[0]))
    a = (d > 0).astype(np.float32)
    rgb = np.where((d < 0.28)[..., None], np.array([214, 202, 246.0]), np.array([36, 28, 56.0]))
    return vers_opaque(rgb, a, N)


# ------------------------------------------------------------------ atlas
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_A_POSER, _E = [], {}


def a_poser(nom, im, e=None):
    _A_POSER.append((nom, im))
    if e is not None:
        _E[nom] = e


def ranger(pas=8):
    n = TEX // pas
    occ = np.zeros((n, n), bool)
    for nom, im in sorted(_A_POSER, key=lambda p: -p[1].shape[0] * p[1].shape[1]):
        h, w = im.shape[:2]
        gh, gw = -(-h // pas), -(-w // pas)
        place = next(((gy, gx) for gy in range(n - gh + 1) for gx in range(n - gw + 1) if not occ[gy:gy + gh, gx:gx + gw].any()), None)
        assert place is not None, f"atlas plein : {nom}"
        gy, gx = place
        occ[gy:gy + gh, gx:gx + gw] = True
        y, x = gy * pas, gx * pas
        tex[y:y + h, x:x + w] = im
        UV[nom] = (x, y, x + w, y + h)
    print(f"atlas : {occ.mean() * 100:.0f} % occupé")


# gains additifs (cumul ≤ 255 : au pire lueur des bras + halo + onde + flash au même pixel, voir la fiche de référence)
G_LUEUR, G_HALO, G_ONDE, G_FLASH = 0.42, 0.38, 0.40, 0.95
VIOLET = (120, 84, 210)
N_S = 224                                            # spirale entière : 224 texels pour 2R = 46 px (4,9 texels/px)
R_MID, R_IN = 0.70, 0.37                             # rayons de coupe des anneaux (fondu de 0,03 de part et d'autre)
s_plein, bord_plein = spirale(N_S, 1.0)
a_poser("spirale", s_plein)                          # spirale au sol
s_ext, b_ext = spirale(N_S, 1.0, rmin=R_MID)
a_poser("sp_ext", s_ext, b_ext)
N_MID = 160
s_mid, b_mid = spirale(N_MID, R_MID + 0.03, rmin=R_IN, rmax=R_MID)
a_poser("sp_mid", s_mid, b_mid)
N_IN = 88
s_in, b_in = spirale(N_IN, R_IN + 0.03, rmax=R_IN)
a_poser("sp_in", s_in, b_in)
an_t, _ = anneaux_tex(192)
a_poser("anneaux", an_t)
a_poser("lueur", vers_add(flou(lanczos(bord_plein * 255, 96, 96) / 255, 96), VIOLET, 96, G_LUEUR))
ring, ring_fil = anneau_tex(128)
a_poser("anneau", ring, ring_fil)
a_poser("anneau_add", vers_add(anneau_add_f(64), VIOLET, 64, G_ONDE))
a_poser("trou", trou_tex(64))
a_poser("halo", vers_add(halo_f(64), VIOLET, 64, G_HALO))
a_poser("flash", vers_add(flash_f(48), (230, 214, 255), 48, G_FLASH))
for k in range(2):
    a_poser(f"frag{k}", fragment_tex(8, k))
a_poser("p_poussiere", poussiere_tex())
a_poser("p_eclat", eclat_part_tex())
a_poser("p_fragment", frag_part_tex())
ranger()

# calque _e : bords clairs des bras et filet des anneaux (lisibles de nuit), arêtes des fragments ; rien sur l'additif
for nom_, b_ in _E.items():
    x0, y0, x1, y1 = UV[nom_]
    for c_, v_ in enumerate((176, 160, 232)):
        tex_e[y0:y1, x0:x1, c_] = np.clip(v_ * b_, 0, 255).astype(np.uint8)
    tex_e[y0:y1, x0:x1, 3] = np.where(tex[y0:y1, x0:x1, 3] > 0, 255, 0)
for k in range(2):
    x0, y0, x1, y1 = UV[f"frag{k}"]
    blk = tex[y0:y1, x0:x1, :3].astype(np.float32)
    clair = blk.mean(axis=2) > 140
    tex_e[y0:y1, x0:x1, :3] = (np.where(clair[..., None], np.array([150, 132, 214]), 0)).astype(np.uint8)
    tex_e[y0:y1, x0:x1, 3] = 255

_b64 = []
for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(fn, optimize=True)
    _buf = io.BytesIO()
    im_.save(_buf, "PNG", optimize=True)
    _b64.append("data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode())
tex_b64, tex_e_b64 = _b64


# ------------------------------------------------------------------ géométrie
def nuid():
    return str(_uuid.uuid4())


class G:
    def __init__(self, nom, origin, parent=None, rotation=None):
        assert len(nom) <= 64
        self.nom, self.origin, self.uuid, self.enfants = nom, [round(float(v), 3) for v in origin], nuid(), []
        self.rotation = [round((float(v) + 180) % 360 - 180, 3) for v in rotation] if rotation is not None else None
        if parent is not None:
            parent.enfants.append(self)

    def json(self):
        d = {"name": self.nom, "origin": self.origin, "uuid": self.uuid,
             "children": [c.json() if isinstance(c, G) else c for c in self.enfants]}
        if self.rotation and any(self.rotation):
            d["rotation"] = self.rotation
        return d


elements = []


def r3(v):
    return [round(float(a), 3) for a in v]


def plaque(g, nom, c, w, h, uv, face="south", ep=0.3):
    c = np.asarray(c, float)
    if face in ("south", "north"):
        a, b = c - (w / 2, h / 2, ep / 2), c + (w / 2, h / 2, ep / 2)
    else:
        a, b = c - (w / 2, ep / 2, h / 2), c + (w / 2, ep / 2, h / 2)
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": r3(a), "to": r3(b), "origin": r3(c),
         "box_uv": False, "faces": {face: {"uv": [round(float(v), 2) for v in uv], "texture": 0}}}
    elements.append(e)
    g.enfants.append(e["uuid"])
    return e


def cube(g, nom, centre, cote, uv, rot=None):
    c = np.asarray(centre, float)
    f = {k: {"uv": list(uv), "texture": 0} for k in ("north", "south", "east", "west", "up", "down")}
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": r3(c - cote / 2), "to": r3(c + cote / 2), "origin": r3(c),
         "box_uv": False, "faces": f}
    if rot is not None:
        e["rotation"] = r3(rot)
    elements.append(e)
    g.enfants.append(e["uuid"])


O = (0, 0, 0)
Cv = np.array(C)
EFFET = G("effet", O)
JOUEUR = G("joueur", O)                       # groupe vide : position et échelle du joueur (guide 15)
ALPHA = {}

# --- vortex face caméra : tout tourne autour de C, la couche de devant à +5 px vers la caméra, les anneaux derrière
VORTEX = G("vortex", C, EFFET)
CAM_SP = G("cam_spirale", C, VORTEX)
TR_SP = G("trans_spirale", C, CAM_SP)
ALPHA["spirale"] = G("ctrl_alpha", C, TR_SP)
TOURNE = {}
for j, (nom, uvn, rt, z) in enumerate((("ext", "sp_ext", 1.0, 5.0), ("mid", "sp_mid", R_MID + 0.03, 5.22),
                                        ("int", "sp_in", R_IN + 0.03, 5.44))):
    TOURNE[nom] = G(f"tourne_{nom}", C, TR_SP)
    plaque(TOURNE[nom], f"bras_{nom}", (C[0], C[1], z), 2 * R * rt, 2 * R * rt, UV[uvn], ep=0.1)
CAM_AN = G("cam_anneaux", C, VORTEX)
TR_AN = G("trans_anneaux", C, CAM_AN)
ALPHA["anneaux"] = G("ctrl_alpha", C, TR_AN)
TOURNE["anneaux"] = G("tourne_anneaux", C, TR_AN)
plaque(TOURNE["anneaux"], "anneaux", (C[0], C[1], -5.0), 2 * R * 1.08, 2 * R * 1.08, UV["anneaux"], ep=0.1)
CAM_LU = G("cam_lueur", C, VORTEX)
ADD_LU = G("add_lueur", C, CAM_LU)
ALPHA["lueur"] = G("ctrl_alpha", C, ADD_LU)
TOURNE["lueur"] = G("tourne_lueur", C, ADD_LU)
plaque(TOURNE["lueur"], "lueur", (C[0], C[1], 5.7), 2 * R, 2 * R, UV["lueur"], ep=0.1)
# trou central et son halo (échelle propre : il grandit pendant l'aspiration)
TROU = G("trou", C, VORTEX)
CAM_TR = G("cam_trou", C, TROU)
TR_TR = G("trans_trou", C, CAM_TR)
plaque(TR_TR, "trou", (C[0], C[1], 5.95), 7.0, 7.0, UV["trou"], ep=0.1)
ADD_HA = G("add_halo", C, CAM_TR)
ALPHA["halo"] = G("ctrl_alpha", C, ADD_HA)
plaque(ADD_HA, "halo", (C[0], C[1], 6.15), 9.5, 9.5, UV["halo"], ep=0.1)

# --- onde de choc face caméra (anneau trans_ + add_)
CHOC = G("choc", C, EFFET)
CAM_CH = G("cam_choc", C, CHOC)
TR_CH = G("trans_choc", C, CAM_CH)
ALPHA["choc"] = G("ctrl_alpha", C, TR_CH)
plaque(TR_CH, "choc", (C[0], C[1], 6.35), 2 * R, 2 * R, UV["anneau"], ep=0.1)
ADD_CH = G("add_choc", C, CAM_CH)
ALPHA["choc_add"] = G("ctrl_alpha", C, ADD_CH)
plaque(ADD_CH, "choc_lueur", (C[0], C[1], 6.55), 2 * R * 1.05, 2 * R * 1.05, UV["anneau_add"], ep=0.1)

# --- flash de l'implosion (étoile add_)
FLASH = G("flash", C, EFFET)
CAM_FL = G("cam_flash", C, FLASH)
ADD_FL = G("add_flash", C, CAM_FL)
plaque(ADD_FL, "flash", (C[0], C[1], 6.8), 12, 12, UV["flash"], ep=0.1)

# --- spirale au sol (même peinture, face up), onde au sol
SOL = G("sol", O, EFFET)
TR_SO = G("trans_sol", O, SOL)
ALPHA["sol"] = G("ctrl_alpha", O, TR_SO)
TOURNE["sol"] = G("tourne_sol", O, TR_SO)
plaque(TOURNE["sol"], "spirale_sol", (0, 0.3, 0), 44, 44, UV["spirale"], face="up", ep=0.1)
ONDE = G("onde_sol", O, EFFET)
TR_ON = G("trans_onde_sol", O, ONDE)
ALPHA["onde"] = G("ctrl_alpha", O, TR_ON)
plaque(TR_ON, "onde_sol", (0, 0.55, 0), 30, 30, UV["anneau"], face="up", ep=0.1)
ADD_ON = G("add_onde_sol", O, ONDE)
ALPHA["onde_add"] = G("ctrl_alpha", O, ADD_ON)
plaque(ADD_ON, "onde_sol_lueur", (0, 0.75, 0), 32, 32, UV["anneau_add"], face="up", ep=0.1)

# --- charge : trois anneaux d'ondulation face caméra (air qui ondule) et quatre cerceaux horizontaux autour du corps
ONDUL = []
for k in range(3):
    g = G(f"ondulation{k + 1}", C, EFFET)
    cg = G(f"cam_ondulation{k + 1}", C, g)
    tg = G(f"trans_ondulation{k + 1}", C, cg)
    ALPHA[f"ondul{k}"] = G("ctrl_alpha", C, tg)
    plaque(tg, f"ondulation{k + 1}", (C[0], C[1], -0.6 + 0.6 * k), 2 * R * 0.95, 2 * R * 0.95, UV["anneau"], ep=0.1)
    ONDUL.append(g)
CERC = []
for k, h in enumerate((3.0, 11.0, 19.0, 27.0)):
    g = G(f"cerceau{k + 1}", (0, h, 0), EFFET)
    tg = G(f"trans_cerceau{k + 1}", (0, h, 0), g)
    ALPHA[f"cerc{k}"] = G("ctrl_alpha", (0, h, 0), tg)
    plaque(tg, f"cerceau{k + 1}", (0, h, 0), 20, 20, UV["anneau"], face="up", ep=0.1)
    CERC.append(g)

# --- fragments d'espace en orbite : orbite (lacet) > rayon (échelle vers C) > fragment (culbute)
FRAG = G("fragments", C, EFFET)
FR = []
for k in range(14):
    th = (k * 137.5 + 20) % 360
    r = 12 + 12 * ((k * 0.618) % 1.0)
    dy = -12 + 26 * ((k * 0.382 + 0.1) % 1.0)
    pos = Cv + np.array([r * math.cos(math.radians(th)), dy, r * math.sin(math.radians(th))])
    orb = G(f"orbite{k + 1}", C, FRAG)
    ray = G(f"rayon{k + 1}", C, orb)
    fg = G(f"frag{k + 1}", pos, ray)
    cote = 0.9 + 1.1 * ((k * 0.73) % 1.0)
    cube(fg, f"fragment{k + 1}", pos, cote, UV[f"frag{k % 2}"],
         rot=(RNG.uniform(-40, 40), RNG.uniform(-40, 40), RNG.uniform(-40, 40)))
    FR.append((orb, ray, fg, th, r))

# --- points de départ des particules (+Y du groupe = direction de départ), chacun avec son ctrl_emit
EMG = G("emetteurs", O, EFFET)
TOURB = G("tourbillon", C, EFFET)              # tourne avec la spirale ; ses points visent le centre ou le dehors
EMITS, CTRL, ORIENT = [], {}, []


def emit(nom, pos, sorte, parent=EMG, rot=None, th=None):
    ge = G(nom, pos, parent, rotation=rot)
    CTRL.setdefault(sorte, []).append(G("ctrl_emit", pos, ge))
    EMITS.append((ge, sorte))
    if th is not None:
        ORIENT.append((ge, th))


def dehors(th, a):
    """Rotation qui penche +Y de a degrés vers la direction horizontale th (Rz·Ry·Rx de Blockbench)."""
    return (a, 90 - th, 0)


def sur_orbite(th, r, dy):
    return Cv + np.array([r * math.cos(math.radians(th)), dy, r * math.sin(math.radians(th))])


for k in range(8):
    th = k * 45 + 10
    emit("emit_poussiere" + (str(k + 1) if k else ""), sur_orbite(th, 19, -10 + 3.2 * k), "poussiere", parent=TOURB, th=th)
for k in range(6):
    th = k * 60 + 35
    emit("emit_fragment" + (str(k + 1) if k else ""), sur_orbite(th, 23, -6 + 3.0 * k), "fragment", parent=TOURB, th=th)
for k in range(4):
    th = k * 90 + 60
    emit("emit_mc_squid_ink", sur_orbite(th, 16, -4 + 4 * k), "squid_ink", parent=TOURB, th=th)
for k in range(3):
    emit("emit_eclat" + (str(k + 1) if k else ""), Cv + np.array([0, -2 + 2 * k, 0]), "eclat", rot=dehors(k * 120, 60))
for k in range(3):
    emit("emit_mc_portal", Cv + np.array([0, -3 + 3 * k, 0]), "portal")
for k in range(4):
    th = k * 90 + 45
    emit("emit_mc_reverse_portal", (9 * math.cos(math.radians(th)), 0.6, 9 * math.sin(math.radians(th))), "reverse_portal")
for y in (0.8, 9.0, 17.0):
    emit("emit_mc_smoke", (0, y, 0), "smoke")

# --- particules modélisées (modèles, à la racine)
PART_P = G("particle_poussiere", O)
plaque(PART_P, "poussiere", (0, 0.6, 0), 0.4, 0.4, UV["p_poussiere"])
PART_F = G("particle_fragment", (3, 0, 0))
plaque(PART_F, "fragment", (3, 0.8, 0), 0.8, 0.8, UV["p_fragment"])
PART_E = G("particle_eclat", (-3, 0, 0))
plaque(PART_E, "eclat", (-3, 0.7, 0), 0.6, 0.6, UV["p_eclat"])

outliner = [EFFET.json(), JOUEUR.json(), PART_P.json(), PART_F.json(), PART_E.json()]


# ------------------------------------------------------------------ animations
def s(v):
    return v if isinstance(v, str) else str(round(v + 0.0, 4))


def kf(ch, t, x, y, z, interp="linear"):
    return {"channel": ch, "data_points": [{"x": s(x), "y": s(y), "z": s(z)}], "time": round(t, 4), "interpolation": interp}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def ein(t, a, b, p=2.2):
    """Accélération (ease-in) de 0 à 1 entre a et b."""
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    return ((t - a) / (b - a)) ** p


def eout(t, a, b, p=2.2):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    return 1 - (1 - (t - a) / (b - a)) ** p


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def step(t, t0):
    return 1.0 if t >= t0 else 0.0


def ressort(t, t0, amp, f=4.0, k=7.0):
    if t <= t0:
        return 0.0
    u = t - t0
    return amp * math.exp(-k * u) * math.sin(2 * math.pi * f * u)


def u3(v):
    return (v, v, v)


def xz(v):
    return (v, 1, v)


def net(v, seuil=0.04):
    return v if v >= seuil else 0.0


class Anim:
    def __init__(self, nom, L, loop, fps=12, extra=()):
        self.nom, self.L, self.loop, self.A = nom, L, loop, {}
        ts = set(round(i / fps, 4) for i in range(int(L * fps) + 1)) | {round(L, 4)} | {round(e, 4) for e in extra if 0 <= e <= L}
        if loop == "loop":
            ts.discard(round(L, 4))
            ts |= {round(L, 4)}
        self.T = sorted(ts)

    def piste(self, g, ch, fn, T=None):
        if not callable(fn):
            keys = [kf(ch, 0, *fn)]
        else:
            ts = list(T or self.T)
            vals = [fn(t) for t in ts]
            keys = []
            for k_, (t, v) in enumerate(zip(ts, vals)):
                if ch == "scale" and k_ and (not any(vals[k_ - 1])) != (not any(v)):
                    keys.append(kf(ch, t - 0.002, *vals[k_ - 1]))
                keys.append(kf(ch, t, *v))
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += keys

    def cacher(self, *gs):
        for g in gs:
            self.piste(g, "scale", (0, 0, 0))

    def emettre(self, sorte, fn):
        for i, c in enumerate(CTRL[sorte]):
            if callable(fn):
                self.piste(c, "position", lambda t, i=i: (max(-1.0, min(7.0, fn(t, i))), 0, 0))
            else:
                self.piste(c, "position", (fn, 0, 0))

    def viser(self, dedans):
        """Points du tourbillon : +Y vers le centre (penché dans le sens de rotation) ou vers le dehors."""
        for ge, th in ORIENT:
            self.piste(ge, "rotation", dehors(th + 150, 72) if dedans else dehors(th + 30, 72))

    def son(self, t, nom):
        self.A.setdefault("effects", {"name": "Effects", "type": "effect", "keyframes": []})["keyframes"].append(
            {"channel": "sound", "data_points": [{"effect": nom, "file": ""}], "time": round(t, 4)})

    def json(self):
        return {"uuid": nuid(), "name": self.nom, "loop": self.loop, "override": False, "length": self.L, "snapping": 24,
                "selected": self.nom == "charge", "animators": self.A}


def rot_z(an, ang_ext, vrille=lambda t: 0.0, k_an=-0.35):
    """Rotation des couches de la spirale : l'intérieur tourne plus vite que l'extérieur (la spirale se resserre)."""
    an.piste(TOURNE["ext"], "rotation", lambda t: (0, 0, ang_ext(t)))
    an.piste(TOURNE["lueur"], "rotation", lambda t: (0, 0, ang_ext(t)))
    an.piste(TOURNE["mid"], "rotation", lambda t: (0, 0, ang_ext(t) + 0.45 * vrille(t)))
    an.piste(TOURNE["int"], "rotation", lambda t: (0, 0, ang_ext(t) + vrille(t)))
    an.piste(TOURNE["anneaux"], "rotation", lambda t: (0, 0, k_an * ang_ext(t)))
    an.piste(TOURNE["sol"], "rotation", lambda t: (0, 0.8 * ang_ext(t), 0))


# ---- charge (loop 4,8 s) : l'air ondule autour du joueur (anneaux qui partent du corps), cerceaux qui respirent
LC = 4.8
an = Anim("charge", LC, "loop", fps=16)
P_ON = 1.6
for k, g in enumerate(ONDUL):
    ph = lambda t, k=k: ((t / P_ON) + k / 3) % 1.0
    an.piste(g, "scale", lambda t, ph=ph: u3(0.25 + 0.85 * ph(t)))
    an.piste(ALPHA[f"ondul{k}"], "position", lambda t, ph=ph: (-1 + 0.45 * math.sin(math.pi * ph(t)) ** 1.5, 0, 0))
for k, g in enumerate(CERC):
    w = 2 * math.pi / (LC / 4)
    an.piste(g, "scale", lambda t, k=k, w=w: xz(1 + 0.16 * math.sin(w * t - 1.1 * k)))
    an.piste(ALPHA[f"cerc{k}"], "position", lambda t, k=k, w=w: (-0.62 + 0.18 * math.sin(w * t - 1.1 * k), 0, 0))
an.piste(SOL, "scale", lambda t: xz(0.55 + 0.04 * math.sin(2 * math.pi * t / LC * 2)))
an.piste(ALPHA["sol"], "position", lambda t: (-0.62 + 0.1 * math.sin(2 * math.pi * t / LC * 2), 0, 0))
an.piste(TOURNE["sol"], "rotation", lambda t: (0, -360 * t / LC, 0))
an.piste(TOURB, "rotation", lambda t: (0, -360 * t / LC, 0))
an.viser(True)
an.cacher(VORTEX, CHOC, FLASH, ONDE, FRAG)
an.emettre("reverse_portal", lambda t, i: 0.6 * math.sin(2 * math.pi * t / LC * 2 - i * math.pi / 2) - 0.2)
an.emettre("poussiere", lambda t, i: -0.4 + 0.6 * math.sin(2 * math.pi * t / LC - i * math.pi / 4))
for so in ("fragment", "eclat", "portal", "smoke", "squid_ink"):
    an.emettre(so, -1)
charge = an.json()

# ---- depart (once 3,6 s) : la spirale se forme, le joueur est tordu et aspiré au centre en rétrécissant, implosion, onde
LD, TI = 3.6, 2.5                                   # durée, implosion
EX = [TI - 0.04, TI - 0.02, TI, TI + 0.02, TI + 0.04, TI + 0.06, TI + 0.08, TI + 0.1, TI + 0.13]
an = Anim("depart", LD, "once", fps=20, extra=EX)
fin_v = lambda t: 1 - sm(t, TI - 0.03, TI + 0.1)      # effondrement de la spirale en 0,13 s
form = lambda t: 0.12 + 0.88 * eout(t, 0.05, 0.95) + ressort(t, 0.95, 0.04, 3, 6)
an.piste(VORTEX, "scale", lambda t: u3(net(form(t) * fin_v(t) * (1 - 0.06 * sm(t, 1.2, TI - 0.05)))))
ang_d = lambda t: -(70 * t + 58 * t * t) - 140 * sm(t, TI - 0.05, TI + 0.12)
rot_z(an, ang_d, lambda t: -26 * sm(t, 0.6, TI - 0.1))      # le cœur prend de l'avance : la spirale se resserre
an.piste(ALPHA["spirale"], "position", lambda t: (-1 + sm(t, 0.0, 0.45), 0, 0))
an.piste(ALPHA["anneaux"], "position", lambda t: (-1 + 0.95 * sm(t, 0.15, 0.8), 0, 0))
an.piste(ALPHA["lueur"], "position", lambda t: (-1 + 0.9 * sm(t, 0.2, 0.9) + 0.1 * bump(t, 1.8, 2.2, TI, TI + 0.1), 0, 0))
an.piste(TROU, "scale", lambda t: u3(0.35 + 0.95 * sm(t, 0.5, TI - 0.1)))
an.piste(ALPHA["halo"], "position", lambda t: (-0.6 + 0.6 * sm(t, 0.8, 2.2), 0, 0))
# joueur : petite résistance, puis aspiré (rétrécit en accélérant) vers le centre, tremblement qui grandit.
# v2 (retour en jeu 2026-11-07 « au départ le perso ne rétrécit pas mais grossit ») : cause mesurée dans le bytecode du mod
# 1.4.0 (TeleportEffects.submit) : la copie du départ est dessinée à sa taille normale, son échelle n'est jamais appliquée ;
# seule la position la suit, et elle n'est plus dessinée sous l'échelle 0,05. La remontée qui gardait le torse rétréci au
# centre (y = 17 × (1 − s)) la faisait donc monter d'un bloc à taille 1 : elle semblait grossir. Tant que le mod n'applique
# pas l'échelle (demande au développeur), la copie reste à sa place (torse déjà au centre), tremble, et disparaît dans
# l'implosion (échelle < 0,05). L'échelle reste écrite, monotone de 1 à 0, sans dépasser 1, pour le jour où elle sera lue.
COPIE_ECHELLE_LUE = True
sj = lambda t: 1 - ein(t, 1.0, TI - 0.04, 1.7)
an.piste(JOUEUR, "scale", lambda t: u3(net(sj(t), 0.02)))
an.piste(JOUEUR, "position", lambda t: (0.7 * sm(t, 0.9, 1.6) * math.sin(2 * math.pi * 6.5 * t) * (1 - sm(t, 2.1, TI)),
                                        (C[1] * (1 - min(1.0, sj(t))) if COPIE_ECHELLE_LUE else 0.0)
                                        + 0.4 * bump(t, 0.75, 0.95, 1.05, 1.2), 0))
# fragments : apparaissent, tournent de plus en plus vite et sont aspirés au centre
for k, (orb, ray, fg, th, r) in enumerate(FR):
    t0 = 0.35 + 0.05 * k
    sens = 1.0 + 0.25 * (k % 3)
    an.piste(orb, "rotation", lambda t, sens=sens: (0, (55 * t + 75 * t * t) * sens, 0))
    an.piste(ray, "scale", lambda t, t0=t0, k=k: u3(net(eout(t, t0, t0 + 0.25) * (1 - ein(t, 0.9 + 0.05 * k, TI - 0.02, 2.4)))))
    an.piste(fg, "rotation", lambda t, k=k: (190 * t * (1 + 0.2 * k % 2), 260 * t, 140 * t * ((k % 3) - 1)))
# ondulations : les anneaux se resserrent vers le centre (aspiration), deux fois plus vite
for k, g in enumerate(ONDUL):
    ph = lambda t, k=k: (1 - ((t / 0.8) + k / 3) % 1.0)
    an.piste(g, "scale", lambda t, ph=ph: u3((0.2 + 1.0 * ph(t)) * (1 - step(t, TI))))
    an.piste(ALPHA[f"ondul{k}"], "position", lambda t, ph=ph: (-1 + 0.42 * math.sin(math.pi * ph(t)) ** 1.5 * sm(t, 0.0, 0.3), 0, 0))
for k, g in enumerate(CERC):
    an.piste(g, "scale", lambda t, k=k: xz(net((1.0 - 0.7 * ein(t, 0.4 + 0.08 * k, TI - 0.05, 1.6)) * (1 - step(t, TI)))))
    an.piste(ALPHA[f"cerc{k}"], "position", lambda t, k=k: (-0.6 + 0.25 * sm(t, 0.3, 1.0), 0, 0))
an.piste(SOL, "scale", lambda t: xz(net((0.55 + 0.45 * eout(t, 0.1, 1.1)) * (1 - sm(t, TI - 0.02, TI + 0.14)))))
an.piste(ALPHA["sol"], "position", lambda t: (-0.62 + 0.42 * sm(t, 0.1, 0.9), 0, 0))
# implosion : flash en étoile, onde de choc face caméra et au sol
an.piste(FLASH, "scale", lambda t: u3(net(1.3 * sm(t, TI, TI + 0.03) * (1 - sm(t, TI + 0.05, TI + 0.32)), 0.05)))
an.piste(CHOC, "scale", lambda t: u3(step(t, TI + 0.04) * (0.25 + 1.35 * eout(t, TI + 0.04, TI + 0.7)) * (1 - step(t, TI + 0.72))))
an.piste(ALPHA["choc"], "position", lambda t: (-0.1 - 0.9 * sm(t, TI + 0.2, TI + 0.7), 0, 0))
an.piste(ALPHA["choc_add"], "position", lambda t: (-0.9 * sm(t, TI + 0.15, TI + 0.65), 0, 0))
an.piste(ONDE, "scale", lambda t: xz(step(t, TI + 0.06) * (0.2 + 2.2 * eout(t, TI + 0.06, TI + 0.85)) * (1 - step(t, TI + 0.86))))
an.piste(ALPHA["onde"], "position", lambda t: (-0.2 - 0.8 * sm(t, TI + 0.3, TI + 0.85), 0, 0))
an.piste(ALPHA["onde_add"], "position", lambda t: (-1.0 * sm(t, TI + 0.25, TI + 0.8), 0, 0))
an.piste(TOURB, "rotation", lambda t: (0, -(60 * t + 85 * t * t), 0))
an.piste(TOURB, "scale", lambda t: u3(1 - 0.8 * ein(t, 0.9, TI, 1.6) + 0.8 * step(t, TI)))
an.viser(True)
an.piste(EFFET, "scale", lambda t: u3(1 - step(t, LD - 0.04)))
fin = lambda t: 1 - step(t, TI)
an.emettre("poussiere", lambda t, i: (-1 + 2.5 * sm(t, 0.2, 0.7) + 2.5 * sm(t, 1.2, 2.2)) * fin(t) - step(t, TI))
an.emettre("fragment", lambda t, i: -1 + 4 * bump(t, 0.7 + 0.08 * i, 0.9 + 0.08 * i, 2.3, TI))
an.emettre("squid_ink", lambda t, i: -1 + 3.5 * bump(t, 1.0, 1.5, 2.3, TI))
an.emettre("portal", lambda t, i: -1 + 4.5 * bump(t, 0.4, 1.0, 2.35, TI + 0.02))
an.emettre("eclat", lambda t, i: -1 + 7 * bump(t, TI, TI + 0.02, TI + 0.15, TI + 0.45))
an.emettre("reverse_portal", lambda t, i: (-0.2 - 0.8 * sm(t, 0.0, 0.6)) + 4.5 * bump(t, TI + 0.05, TI + 0.1, TI + 0.4, TI + 0.8))
an.emettre("smoke", lambda t, i: -1 + 5 * bump(t, TI + 0.04, TI + 0.1, TI + 0.35, TI + 0.9))
an.son(0.05, "vortex_torsion")                  # l'espace se tord : grondement qui monte en vrillant
an.son(1.1, "vortex_aspiration")                # aspiration : souffle qui enfle jusqu'à l'implosion
an.son(TI - 0.03, "vortex_implosion")           # implosion en un point et petite onde
depart = an.json()

# ---- arrivee (once 3,4 s) : un point, la spirale tourne à l'envers et recrache le joueur, onde de choc au sol, elle se
# déroule et s'efface
LA, TE = 3.4, 1.45                                  # durée, le joueur touche le sol
EX = [0.0, 0.02, 0.04, 0.06, 0.1, TE - 0.02, TE, TE + 0.02, TE + 0.05]
an = Anim("arrivee", LA, "once", fps=20, extra=EX)
ouvre = lambda t: 0.1 + 0.9 * eout(t, 0.03, 0.6) + ressort(t, 0.6, 0.05, 3, 6)
an.piste(VORTEX, "scale", lambda t: u3(net(ouvre(t) * (1 + 0.28 * sm(t, TE + 0.1, 3.0)) * (1 - step(t, 3.05)))))
ang_a = lambda t: 330 * min(t, 2.8) - 58 * min(t, 2.8) ** 2
rot_z(an, ang_a, lambda t: 22 * (1 - sm(t, 0.2, 2.2)))      # le cœur se déroule d'abord
an.piste(ALPHA["spirale"], "position", lambda t: (-1 + sm(t, 0.0, 0.25) - sm(t, 1.75, 2.75), 0, 0))
an.piste(ALPHA["anneaux"], "position", lambda t: (-1 + 0.95 * sm(t, 0.05, 0.5) - 0.95 * sm(t, 1.6, 2.6), 0, 0))
an.piste(ALPHA["lueur"], "position", lambda t: (-1 + sm(t, 0.0, 0.4) - sm(t, 1.7, 2.7), 0, 0))
an.piste(TROU, "scale", lambda t: u3(net(1.25 * eout(t, 0.0, 0.5) * (1 - ein(t, 0.9, TE + 0.25, 1.5)))))
an.piste(ALPHA["halo"], "position", lambda t: (-0.9 * sm(t, 0.9, TE + 0.3), 0, 0))
sa = lambda t: eout(t, 0.5, TE - 0.12, 2.0) * (1 + 0.04 * bump(t, TE - 0.25, TE - 0.12, TE - 0.05, TE + 0.15))
an.piste(JOUEUR, "scale", lambda t: u3(net(sa(t), 0.02)))
an.piste(JOUEUR, "position", lambda t: (0, max(0.0, C[1] * (1 - min(1.0, sa(t)))), 0))
# fragments : recrachés du centre, ils s'écartent en ralentissant puis s'effacent
for k, (orb, ray, fg, th, r) in enumerate(FR):
    sens = 1.0 + 0.25 * (k % 3)
    t0 = 0.5 + 0.03 * k
    an.piste(orb, "rotation", lambda t, sens=sens: (0, -(260 * t - 50 * t * t) * sens, 0))
    an.piste(ray, "scale", lambda t, t0=t0, k=k: u3(net(1.15 * eout(t, t0, t0 + 0.9, 2.6) * (1 - sm(t, 2.0 + 0.04 * k, 2.6 + 0.04 * k)))))
    an.piste(fg, "rotation", lambda t, k=k: (210 * t, 280 * t * (1 + 0.15 * (k % 2)), 120 * t))
for k, g in enumerate(ONDUL):
    ph = lambda t, k=k: ((t / 0.7) + k / 3) % 1.0
    an.piste(g, "scale", lambda t, ph=ph: u3((0.25 + 1.0 * ph(t)) * (1 - step(t, 2.2))))
    an.piste(ALPHA[f"ondul{k}"], "position", lambda t, ph=ph: (-1 + 0.42 * math.sin(math.pi * ph(t)) ** 1.5 * (1 - sm(t, 1.4, 2.1)), 0, 0))
for k, g in enumerate(CERC):
    an.piste(g, "scale", lambda t, k=k: xz(net(step(t, 0.5) * (0.3 + 1.4 * eout(t, 0.5 + 0.06 * k, TE + 0.4)) * (1 - step(t, 2.3)))))
    an.piste(ALPHA[f"cerc{k}"], "position", lambda t, k=k: (-0.35 - 0.65 * sm(t, 1.2, 2.2), 0, 0))
an.piste(SOL, "scale", lambda t: xz(net((0.2 + 0.8 * eout(t, 0.0, 0.7)) * (1 + 0.25 * sm(t, TE, 2.9)) * (1 - step(t, 3.0)))))
an.piste(ALPHA["sol"], "position", lambda t: (-0.2 - 0.8 * sm(t, 1.9, 2.9), 0, 0))
# point d'ouverture puis onde de choc au sol quand le joueur se pose
an.piste(FLASH, "scale", lambda t: u3(net(0.8 * (1 - sm(t, 0.05, 0.3)) + 0.9 * bump(t, TE - 0.02, TE, TE + 0.04, TE + 0.25), 0.05)))
an.piste(CHOC, "scale", lambda t: u3(step(t, TE) * (0.4 + 1.3 * eout(t, TE, TE + 0.6)) * (1 - step(t, TE + 0.62))))
an.piste(ALPHA["choc"], "position", lambda t: (-0.1 - 0.9 * sm(t, TE + 0.15, TE + 0.6), 0, 0))
an.piste(ALPHA["choc_add"], "position", lambda t: (-0.9 * sm(t, TE + 0.1, TE + 0.55), 0, 0))
an.piste(ONDE, "scale", lambda t: xz(step(t, TE) * (0.3 + 2.4 * eout(t, TE, TE + 0.8)) * (1 - step(t, TE + 0.82))))
an.piste(ALPHA["onde"], "position", lambda t: (-0.8 * sm(t, TE + 0.25, TE + 0.8), 0, 0))
an.piste(ALPHA["onde_add"], "position", lambda t: (-1.0 * sm(t, TE + 0.2, TE + 0.75), 0, 0))
an.piste(TOURB, "rotation", lambda t: (0, 220 * t - 40 * t * t, 0))
an.piste(TOURB, "scale", lambda t: u3(0.3 + 0.8 * eout(t, 0.4, 1.4)))
an.viser(False)
an.piste(EFFET, "scale", lambda t: u3(1 - step(t, LA - 0.04)))
an.emettre("poussiere", lambda t, i: -1 + 3.5 * bump(t, 0.45, 0.6, 1.6, 2.1))
an.emettre("fragment", lambda t, i: -1 + 4.5 * bump(t, 0.55 + 0.05 * i, 0.65 + 0.05 * i, 1.2, 1.6))
an.emettre("squid_ink", lambda t, i: -1 + 4 * bump(t, 0.55, 0.65, 1.0, 1.35))
an.emettre("eclat", lambda t, i: -1 + 6 * bump(t, 0.0, 0.02, 0.12, 0.35) + 6 * bump(t, TE, TE + 0.02, TE + 0.12, TE + 0.4))
an.emettre("reverse_portal", lambda t, i: -1 + 4 * bump(t, 0.4, 0.6, 1.8, 2.6))
an.emettre("smoke", lambda t, i: -1 + 5 * bump(t, TE, TE + 0.05, TE + 0.3, TE + 0.9))
an.emettre("portal", -1)
an.son(0.0, "vortex_detorsion")                 # le point se déchire et la spirale se déroule à l'envers
an.son(TE - 0.95, "vortex_expulsion")           # souffle qui sort, coup sourd quand le joueur se pose
arrivee = an.json()


# ---- animations des particules (guide 5 ter §3) : rotation fermée sur la boucle
def anim_particule(nom, L, g, rot=None, pulse=None):
    a_ = Anim(nom, L, "loop", fps=16)
    if rot:
        a_.piste(g, "rotation", lambda t: tuple(r_ * 360 * t / L for r_ in rot))
    if pulse:
        a_.piste(g, "scale", lambda t: u3(1 + pulse * max(0.0, math.sin(2 * math.pi * t / L)) ** 3))
    return a_.json()


p_pous = anim_particule("particle_poussiere_fall", 1.0, PART_P, rot=(0, 0, 1), pulse=0.5)
p_frag = anim_particule("particle_fragment_fall", 0.8, PART_F, rot=(1, 2, 1))
p_ecl = anim_particule("particle_eclat_fall", 0.5, PART_E, rot=(0, 0, 1), pulse=0.8)

ANIMS = [charge, depart, arrivee, p_pous, p_frag, p_ecl]
assert len(EMITS) <= 32, len(EMITS)
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures,
         "animations": ANIMS}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
embarquer_sons(model, {n: f"sons/{n}.ogg" for n in ("vortex_torsion", "vortex_aspiration", "vortex_implosion",
                                                    "vortex_detorsion", "vortex_expulsion")})
limiter_sons(model, max_effet=3)                  # un son par étape physique (categories/effets.md), rien pendant la charge
for a_ in ANIMS:
    eff = a_["animators"].get("effects")
    assert not eff or len(eff["keyframes"]) <= 3, a_["name"]

os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


def ngroupes(n):
    return 1 + sum(ngroupes(c) for c in n.get("children", []) if isinstance(c, dict))


print(len(elements), "cubes ;", sum(ngroupes(n) for n in model["outliner"]), "groupes ; profondeur", max(depth(n) for n in model["outliner"]), ";",
      len(model["animations"]), "anims ;", sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()), "keyframes ;",
      os.path.getsize(OUT) // 1024, "Ko ;", len(EMITS), "emit_")
