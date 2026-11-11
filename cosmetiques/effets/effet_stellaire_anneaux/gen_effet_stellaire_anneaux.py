"""Effet de téléportation « Anneaux de transport » (guide 15), pièce sans ensemble. Design original, fiche de référence
.claude/references/effets/anneaux-transport.md (déroulé, proportions, couleurs échantillonnées, timing, sons).
Écrit effet_stellaire_anneaux.png, effet_stellaire_anneaux_e.png et .build/effet_stellaire_anneaux_brut.bbmodel.

- **Plaque au sol** (rayon 25 px, opaque, acier sombre) gravée de rainures pleines (≥ 8 texels) : bord à crans et cartouches,
  couronne de cercles, cœur à six rais. Trois couches add_ des rainures (cœur, couronne, bord) s'allument tour à tour,
  anneau de tirets add_ qui tourne, rideau de lumière qui monte du bord, poussière de lumière (charge).
- **Cinq anneaux** en vrais volumes (rayon 22 px, section 3,8 × 4,6 px, 64 segments à 5,6°) : acier sombre presque neutre
  (v2, d'après la référence) : plots en relief alternés haut et bas avec rivet, nervure médiane polie, gravures rares
  inventées, liseré lumineux bleuté haut et bas (_e + gaine add_), plots aussi en géométrie dessus et dessous ; lumières
  blanc neutre à reflets bleutés (v1 : or ambré).
  Ils naissent dans le ciel sous une lueur, descendent l'un après l'autre en tournant (une courbe par anneau, vitesse
  continue) et se posent en colonne avec un petit amorti ; le dernier arrivé repart le premier, vers le ciel.
- **Éclair** : une bande de lumière remonte la colonne (descend à l'arrivée), colonne de lumière, stries horizontales qui
  fusent entre les anneaux (4 orientations), liserés qui flambent au passage de la bande, rayon qui jaillit vers le ciel,
  lueur au sommet. Au départ, la copie du joueur est cachée d'un coup au plus fort (échelle < 0,05 : seule chose que le mod
  applique à la copie) ; à l'arrivée, le joueur apparaît dans la colonne.
Mouvements : une courbe lisse par phase, 30 clés/s.

Particules (guide 5 ter ; cadence animée par ctrl_emit) : poussiere (point de lumière qui monte du bord de la plaque),
etincelle (trait vif projeté du bord d'un anneau qui se pose), eclat (éclat de lumière qui monte du sommet à l'éclair),
emit_mc_electric_spark (crépitement dans la colonne à l'éclair), emit_mc_wax_on (éclats orange quand un anneau se pose).
Pas d'end_rod. Sons embarqués originaux v2 (sons/, v1 dans sons/v1/) : anneaux_descente, anneaux_eclair, anneaux_retour ;
rien pendant la charge.

Fonctions : add_, _e, cam_, ctrl_alpha, ctrl_emit, particle_/emit_, emit_mc_, groupe joueur, sons embarqués. À juger en
jeu : lisibilité des gravures et des liserés à 3–10 blocs, de jour et de nuit ; stries et éclair ; particules et cadences ;
avec shader.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "effet_stellaire_anneaux"
TEX = 512
TAU = 2 * math.pi
FPS = 30

# ------------------------------------------------------------------ dimensions (px)
R_OUT, R_IN = 22.0, 18.2        # anneau : rayons extérieur et intérieur
HA = 4.6                        # hauteur d'un anneau
PAS = 7.8                       # pas de la colonne (écart 3,2 px, ≈ 0,7 × la hauteur, comme la référence)
Y0 = 0.6                        # bas de l'anneau du bas
NA = 5
YC = [Y0 + HA / 2 + PAS * i for i in range(NA)]          # centres : 2,9 … 34,1 ; sommet 36,4
NSEG = 64                       # 5,6° entre segments voisins
W_SEG = 2 * R_OUT * math.tan(math.pi / NSEG)             # 2,16 px
R_PL = 25.0                     # plaque au sol
Y_HAUT = 130.0                  # altitude où naissent les anneaux (8 blocs au-dessus de leur place)
R_COL, H_COL = 10.0, 35.6       # colonne de lumière
Y_TOP = YC[-1] + HA / 2         # sommet de la colonne

# ------------------------------------------------------------------ palette v2 (2026-11-07, retour « pas comme ça dans la série »)
# Métal mesuré sur la référence (fiche anneaux-transport.md, Couleurs) : acier sombre presque neutre (saturation 0,03 sous
# lumière neutre), valeurs 33 / 45 / 110, reflets nets 200–225 ; il paraît bronze brun seulement sous un éclairage chaud.
# Lumière du transport : blanc neutre au cœur (251, 249, 248), stries légèrement bleutées. v1 : or ambré.
OR = dict(clair=(138, 134, 127), moyen=(86, 82, 77), fonce=(56, 53, 50), creux=(20, 18, 17), lis=(182, 186, 192),
          reflet=(214, 218, 226))
STOPS = [(0.0, (0, 0, 0)), (0.25, (34, 42, 66)), (0.5, (128, 148, 192)), (0.75, (208, 218, 240)), (0.9, (240, 244, 252)),
         (1.0, (255, 255, 255))]


def palette(f):
    f = np.clip(f, 0, 1)
    xs = [s_[0] for s_ in STOPS]
    return np.stack([np.interp(f, xs, [s_[1][c] for s_ in STOPS]) for c in range(3)], axis=-1)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def grille(N, demi, SS=3):
    n = N * SS
    c = ((np.arange(n) + 0.5) / n * 2 - 1) * demi
    return np.meshgrid(c, -c)


def reduire(arr, taille):
    """Image flottante (h, w, c) sur-échantillonnée -> taille (w, h) par LANCZOS."""
    out = []
    for c in range(arr.shape[2]):
        im = Image.fromarray(np.clip(arr[..., c], 0, 255).astype(np.uint8), "L").resize(taille, Image.LANCZOS)
        out.append(np.asarray(im).astype(float))
    return np.stack(out, axis=-1)


def vers_add(f, N, gain, teinte=None):
    """Intensité f (sur-échantillonnée) -> RGBA additif : palette × gain, noir transparent (alpha 0/255)."""
    taille = (N, N) if np.ndim(N) == 0 else N
    g = reduire(np.clip(f, 0, 1)[..., None] * 255, taille)[..., 0] / 255
    rgb = palette(g) / 255 * gain * np.clip(g * 1.4, 0, 1)[..., None]
    arr = np.zeros(g.shape + (4,), np.uint8)
    arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    lum = arr[..., :3].max(axis=2)
    arr[..., 3] = (lum > 6) * 255
    arr[lum <= 6, :3] = 0
    return arr


def profil_add(prof, gain, w=4, bouts=None):
    """Texture w × len(prof) : constante en travers (u), profil le long de v (pleine en travers : sûre aux mipmaps)."""
    f = np.repeat(np.asarray(prof, float)[:, None], w, axis=1)
    rgb = palette(f) / 255 * gain * np.clip(f * 1.6, 0, 1)[..., None]
    arr = np.zeros(f.shape + (4,), np.uint8)
    arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    lum = arr[..., :3].max(axis=2)
    arr[..., 3] = (lum > 6) * 255
    arr[lum <= 6, :3] = 0
    return arr


def profil_long(prof, gain, h=2, froid=0.0):
    """Texture len(prof) × h : profil le long de u (strie), constant en travers ; froid : bouts teintés de cyan pâle."""
    f = np.asarray(prof, float)
    rgb = palette(f) / 255 * gain * np.clip(f * 1.6, 0, 1)[:, None]
    if froid:
        u = np.abs(np.linspace(-1, 1, len(f)))[:, None]
        cy = np.array([150, 225, 235]) / 255 * gain * np.clip(f * 1.6, 0, 1)[:, None]
        k = froid * smooth((u - 0.35) / 0.5)
        rgb = rgb * (1 - k) + cy * k
    arr = np.zeros((h, len(f), 4), np.uint8)
    arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)[None]
    lum = arr[..., :3].max(axis=2)
    arr[..., 3] = (lum > 6) * 255
    arr[lum <= 6, :3] = 0
    return arr


def segment_d(x, y, a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    t = np.clip(((x - a[0]) * d[0] + (y - a[1]) * d[1]) / max(d @ d, 1e-12), 0, 1)
    return np.hypot(x - a[0] - t * d[0], y - a[1] - t * d[1])


# ------------------------------------------------------------------ textures
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)


def poser(nom, im, x, y, e=None):
    h, w = im.shape[:2]
    assert x + w <= TEX and y + h <= TEX and not tex[y:y + h, x:x + w, 3].any(), nom
    tex[y:y + h, x:x + w] = im
    if e is not None:
        tex_e[y:y + h, x:x + w] = e
    UV[nom] = (x, y, x + w, y + h)


def metal(h, w, rng, base, clair=0.12, sombre=0.18, grain=0.04):
    """Métal brossé (±4 %), éclairé d'en haut : h × w × 3 flottant."""
    v = np.linspace(0, 1, h)[:, None]
    lum = 1 + clair * (1 - v) * 2 - sombre * v
    br = 1 + grain * np.repeat(rng.standard_normal((h, w // 6 + 1))[:, :, None], 6, axis=2).reshape(h, -1)[:, :w]
    return np.asarray(base, float)[None, None] * (lum * br)[..., None]


# 1. frises de la face extérieure (512 × 20 chacune ; un segment = 8 unités = 16 texels ; v = 0 en haut)
# Profil d'après la référence : arête claire haut et bas, plots en relief alternés en haut (segments pairs) et en bas
# (segments impairs) avec un rivet clair, nervure médiane polie qui fait le tour, panneaux creux entre les plots.
# Gravures rares (une marque inventée tous les 8 segments), pas de cartouches.
FW, FH, SSF, KF = 512, 20, 4, 2          # frise peinte en unités de 512 × 20, rendue à ×2 (1024 × 40)
rng = np.random.default_rng(5)


def boite(uc, vc, ax, ay, rr):
    """Distance signée à un rectangle aux coins ronds centré (demi-côtés ax, ay)."""
    qx, qy = np.maximum(np.abs(uc) - (ax - rr), 0), np.maximum(np.abs(vc) - (ay - rr), 0)
    return np.hypot(qx, qy) - rr + np.minimum(np.maximum(np.abs(uc) - ax, np.abs(vc) - ay), 0)


def frise():
    h, w = FH * SSF * KF, FW * SSF * KF
    vv, uu = np.meshgrid((np.arange(h) + 0.5) / (SSF * KF), (np.arange(w) + 0.5) / (SSF * KF), indexing="ij")    # en unités
    img = metal(h, w, rng, OR["fonce"], clair=0.10, sombre=0.15, grain=0.035)       # panneaux creux
    plein = metal(h, w, rng, OR["moyen"], clair=0.16, sombre=0.2)                  # surfaces en relief
    em = np.zeros_like(img)
    seg = (uu // 8).astype(int)
    us = (uu % 8) - 4                                                                  # −4 … 4 dans le segment
    C = {k: np.array(v, float) for k, v in OR.items()}
    # arêtes haut et bas : chanfrein clair (lumière d'en haut) puis rainure
    img[vv < 1.4] = C["lis"]
    img[(vv >= 1.4) & (vv < 2.2)] = C["creux"]
    img[vv > FH - 1.4] = C["moyen"]
    img[(vv <= FH - 1.4) & (vv > FH - 2.2)] = C["creux"]
    em[vv < 1.0] = (120, 150, 205)                                                     # filet bleuté, discret de nuit
    em[vv > FH - 1.0] = (120, 150, 205)
    # nervure médiane : bande polie, arête haute claire, filet de reflet, ombre dessous
    mid = (vv >= 8.6) & (vv < 11.4)
    img[mid] = plein[mid]
    img[(vv >= 8.6) & (vv < 9.3)] = C["clair"]
    img[(vv >= 9.6) & (vv < 10.1)] = C["reflet"]
    img[(vv >= 11.4) & (vv < 12.1)] = C["creux"]
    img[(vv >= 7.9) & (vv < 8.6)] = C["creux"]
    em[(vv >= 9.6) & (vv < 10.1)] = (70, 88, 125)
    # plots en relief : en haut sur les segments pairs, en bas sur les impairs (rectangles aux coins ronds)
    for haut in (True, False):
        vc = vv - (4.0 if haut else FH - 4.0)
        sel = (seg % 2 == 0) if haut else (seg % 2 == 1)
        d = boite(us, vc, 3.0, 1.6, 0.5)
        plot = sel & (d < 0)
        img[plot] = plein[plot]
        img[plot & (d > -0.6) & (vc < 0)] = C["clair"]                                # arête haute éclairée
        img[plot & (d > -0.6) & (vc > 0.4)] = C["fonce"]                              # arête basse
        img[sel & (d >= 0) & (d < 0.7)] = C["creux"]                                  # joint autour du plot
        img[sel & (d >= 0.7) & (d < 1.3) & (vc > 0)] = C["fonce"] * 0.7               # ombre portée dessous
        dr = np.hypot(us, vc + 0.3)                                                   # rivet : point clair, ombre dessous
        img[sel & (dr < 1.25) & (vc > -0.1)] = C["creux"]
        img[sel & (dr < 0.85)] = C["reflet"]
    # gravures rares inventées : tous les 8 segments, une marque (barre, trait, arc) dans le panneau libre
    for k in range(0, 64, 8):
        kk = k + 3
        m = seg == kk
        vc = vv - (FH - 4.0 if kk % 2 == 0 else 4.0)                                 # panneau libre (sans plot)
        d = np.minimum.reduce([segment_d(us, vc, (-1.6, -1.2), (-1.6, 1.2)), segment_d(us, vc, (-0.6, 0.0), (1.4, 0.0)),
                               np.abs(np.hypot(us - 0.6, vc) - 1.2) + 9 * (us < 0.9)])
        d = np.where(m, d, 9.0)
        img[d < 0.32] = C["creux"]
        img[(d >= 0.32) & (d < 0.6) & (vc > 0)] = C["clair"] * 0.8
    img[(np.abs(us) > 3.85) & ~mid] *= 0.75                                           # joint léger entre segments
    return reduire(img, (FW * KF, FH * KF)), reduire(em, (FW * KF, FH * KF))


def rgba(rgb, a=255):
    out = np.zeros(rgb.shape[:2] + (4,), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    out[..., 3] = a
    return out


def rgba_e(rgb):
    out = rgba(rgb)
    out[rgb.max(axis=2) < 8] = 0
    return out


im, em = frise()                    # 1 024 × 40 en deux bandes de 512 (16 texels par segment)
for j in range(2):
    poser(f"frise{j}", rgba(im[:, 512 * j:512 * (j + 1)]), 0, 40 * j, e=rgba_e(em[:, 512 * j:512 * (j + 1)]))

# 2. plaque au sol (256², up) : disque or bronze, rainures pleines de 8 à 12 texels ; masques de zone pour les lueurs
NP = 256
SSP = 3
x, y = grille(NP, R_PL, SSP)
r, phi = np.hypot(x, y), np.arctan2(y, x)
dedans = r < R_PL - 0.3
w8 = 0.85                                                     # demi-largeur d'une rainure (1,7 px ≈ 8,7 texels)
rain_bord = (np.abs(r - 23.2) < 0.55) | (np.abs(r - 17.4) < w8 * 0.8)
ang = (phi % (TAU / 24)) - TAU / 48
rain_bord |= (r > 18.4) & (r < 22.4) & (np.abs(ang * r) < 0.55) & ((np.floor(phi / (TAU / 24)) % 3) != 0)
for k in range(8):                                            # huit cartouches : barre + point
    a = TAU * (k + 0.5) / 8 + TAU / 48 * 0
    a = TAU * (3 * k) / 24 + TAU / 48
    cx, cy = 20.4 * math.cos(a), 20.4 * math.sin(a)
    rain_bord |= np.hypot(x - cx, y - cy) < 0.95
rain_mil = (np.abs(r - 9.0) < 0.6)
for k in range(12):
    a = TAU * k / 12
    cx, cy = 13.2 * math.cos(a), 13.2 * math.sin(a)
    rain_mil |= np.abs(np.hypot(x - cx, y - cy) - 1.7) < 0.55
rain_coeur = np.abs(r - 4.6) < 0.55
for k in range(6):
    a = TAU * k / 6
    rain_coeur |= (segment_d(x, y, (1.3 * math.cos(a), 1.3 * math.sin(a)), (3.6 * math.cos(a), 3.6 * math.sin(a))) < 0.5)
rain_coeur |= r < 0.8
rain = (rain_bord | rain_mil | rain_coeur) & dedans
base = metal(NP * SSP, NP * SSP, rng, (84, 80, 76), clair=0.0, sombre=0.0, grain=0.03)
base *= (1 - 0.22 * smooth((r - 15) / 10))[..., None]           # plus sombre vers le bord
base[(r > 24.0) & dedans] = OR["moyen"]                         # bord biseauté clair
base[rain] = OR["creux"]
pl = reduire(base, (NP, NP))
pa = (reduire(dedans[..., None].astype(float) * 255, (NP, NP))[..., 0] > 110)
pl_rgba = rgba(pl)
pl_rgba[~pa] = 0
em = np.zeros(base.shape)
em[rain] = (52, 70, 110)
em_r = rgba_e(reduire(em, (NP, NP)))
em_r[~pa] = 0
poser("plaque", pl_rgba, 0, 80, e=em_r)


def lueur_rainures(masque, N, demi, gain):
    """Rainures d'une zone en lumière additive (cœur blanc bleuté + léger halo), même tracé que la plaque."""
    xx, yy = grille(N, demi, SSP)
    # ré-échantillonne le masque de la plaque sur la grille de la zone
    ix = np.clip(((xx / R_PL + 1) / 2 * NP * SSP).astype(int), 0, NP * SSP - 1)
    iy = np.clip(((1 - (yy / R_PL + 1) / 2) * NP * SSP).astype(int), 0, NP * SSP - 1)
    m = masque[iy, ix].astype(float)
    k = max(1, int(SSP * N / (2 * demi) * 0.5))
    halo = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(k * 1.5))).astype(float) / 255
    return vers_add(np.maximum(m * 0.95, halo * 0.45), N, gain)


poser("lueur_bord", lueur_rainures(rain_bord & dedans, 256, R_PL, 235), 256, 80)
poser("lueur_mil", lueur_rainures(rain_mil, 160, 16.0, 235), 0, 336)
poser("lueur_coeur", lueur_rainures(rain_coeur, 96, 8.0, 245), 160, 336)

# 3. petites pièces des anneaux
rng2 = np.random.default_rng(9)
top = metal(16, 8, rng2, OR["moyen"], clair=0.0, sombre=0.0)          # dessus : v = 0 dehors (−Z local), u le long
top[:2] = OR["lis"]                                                  # bord extérieur clair
top[2:3] = OR["creux"]
top[7:9] = OR["fonce"]                                               # rainure circulaire au milieu du dessus
top[:, 7:8] = OR["creux"]                                            # joint entre segments
top[-2:] = OR["fonce"]
poser("dessus", rgba(top), 256, 336)
inn = metal(20, 8, rng2, (52, 49, 46), clair=0.1, sombre=0.25)       # face intérieure : acier sombre, fente qui luit
inn[9:11] = (220, 230, 250)
inn_e = np.zeros_like(inn)
inn_e[9:11] = (150, 180, 235)
poser("interieur", rgba(inn), 264, 336, e=rgba_e(inn_e))
poser("dessous", rgba(metal(16, 8, rng2, OR["fonce"], 0, 0)), 272, 336)
poser("flanc", rgba(metal(20, 16, rng2, OR["fonce"], 0.1, 0.1)), 280, 336)
nerv = np.zeros((4, 4, 3)) + OR["moyen"]                             # plots du dessus et du dessous
nerv[0] = OR["clair"]
nerv[-1] = OR["fonce"]
poser("nervure", rgba(nerv), 296, 336)

# 4. lumières (add_), pleines en travers
vv = (np.arange(24) + 0.5) / 24                                       # gaine du liseré : deux pics au bord haut et bas
y_pl = vv * (HA + 1.6) - 0.8                                          # en px depuis le bas de l'anneau
pics = np.exp(-((y_pl - HA) / 0.45) ** 2) + np.exp(-(y_pl / 0.45) ** 2)
poser("gaine", profil_add(np.clip(pics, 0, 1) * 0.95, 200), 304, 336)
poser("lueur", profil_add(np.exp(-((vv - 0.5) / 0.3) ** 2), 170), 312, 336)   # gaine d'apparition
vc = (np.arange(32) + 0.5) / 32
poser("colonne", profil_add(0.75 * smooth(vc / 0.08) * smooth((1 - vc) / 0.15), 50), 320, 336)
vf = (np.arange(16) + 0.5) / 16
poser("front", profil_add(np.exp(-((vf - 0.5) / 0.26) ** 2), 80), 328, 336)
vb = (np.arange(64) + 0.5) / 64                                       # rayon : v = 0 en haut (s'éteint vers le ciel)
poser("rayon", profil_add(0.95 * (1 - vb) ** 0.4 * smooth(vb / 0.05), 90), 336, 336)
ul = np.linspace(-1, 1, 64)
poser("strie", profil_long(np.exp(-(ul / 0.55) ** 2) * 0.95, 60, h=2, froid=0.8), 344, 336)
st_h = np.exp(-(ul / 0.45) ** 2)[None, :] * np.exp(-(np.linspace(-1, 1, 12)[:, None] / 0.5) ** 2)
poser("strie_halo", vers_add(np.repeat(np.repeat(st_h, 3, 0), 3, 1), (64, 12), 16), 344, 340)
vr = (np.arange(32) + 0.5) / 32                                       # rideau : v = 0 en haut
poser("rideau", profil_add(0.8 * vr ** 1.6 * smooth((1 - vr) / 0.05), 70), 352, 360)

# 5. anneau de tirets (add_, tourne) et lueur ronde (cam_)
x, y = grille(64, 16.0)
r, phi = np.hypot(x, y), np.arctan2(y, x)
ang = (phi % (TAU / 12)) - TAU / 24
f_t = smooth((0.75 - np.abs(r - 14.6)) / 0.3) * smooth((0.11 - np.abs(ang)) / 0.04)
poser("tirets", vers_add(f_t, 64, 230), 256, 408)
x, y = grille(64, 1.0)
r = np.hypot(x, y)
f_g = np.maximum.reduce([np.exp(-(r / 0.22) ** 2), 0.5 * np.exp(-(r / 0.55) ** 2),
                         np.exp(-(np.abs(y) / 0.05) ** 2) * np.clip(1 - np.abs(x), 0, 1) ** 1.5 * 0.8])
poser("halo", vers_add(f_g * 0.9, 64, 150), 320, 408)

# 6. particules
poser("point", profil_add(np.ones(8) * 0.85, 255, w=8), 384, 408)
poser("trait", profil_add((1 - (np.arange(16) + 0.5) / 16) ** 1.2, 255), 392, 408)
x, y = grille(16, 1.0)
f_ec = np.clip(1 - (np.abs(x) ** 0.6 + np.abs(y) ** 0.6), 0, 1) ** 0.8
poser("eclat", vers_add(f_ec, 16, 255), 400, 408)

CLEAR = [TEX - 2, TEX - 2, TEX - 1, TEX - 1]
assert not tex[TEX - 2:, TEX - 2:, 3].any()
assert set(np.unique(tex[..., 3])) <= {0, 255}
tex_e[tex_e[..., 3] == 0, :3] = 0


def b64(arr, chemin):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(chemin, optimize=True)
    b = io.BytesIO()
    im_.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


tex_b64, tex_e_b64 = b64(tex, f"{NOM}.png"), b64(tex_e, f"{NOM}_e.png")


# ------------------------------------------------------------------ géométrie
def nuid():
    return str(_uuid.uuid4())


def rot180(a):
    return (a + 180.0) % 360.0 - 180.0


class G:
    def __init__(self, nom, origin, parent=None, rotation=None):
        assert len(nom) <= 64
        self.nom, self.origin, self.uuid, self.enfants = nom, [round(float(v), 4) for v in origin], nuid(), []
        self.rotation = rotation
        if parent is not None:
            parent.enfants.append(self)

    def json(self):
        d = {"name": self.nom, "origin": self.origin, "uuid": self.uuid,
             "children": [c.json() if isinstance(c, G) else c for c in self.enfants]}
        if self.rotation:
            d["rotation"] = [round(rot180(float(v)), 4) for v in self.rotation]
        return d


elements = []


def cube(g, nom, a, b, faces, origin=None, rotation=None):
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in a], "to": [round(float(v), 4) for v in b],
         "origin": [round(float(v), 4) for v in (origin if origin is not None else (np.add(a, b) / 2))], "box_uv": False,
         "faces": {k: {"uv": [round(float(v), 3) for v in uv], "texture": 0} for k, uv in faces.items()}}
    if rotation is not None and any(abs(v) > 1e-6 for v in rotation):
        e["rotation"] = [round(rot180(float(v)), 4) for v in rotation]
    for k in ("north", "south", "east", "west", "up", "down"):
        e["faces"].setdefault(k, {"uv": CLEAR, "texture": 0})
    elements.append(e)
    g.enfants.append(e["uuid"])


def autour(g, nom, centre, r, w, y0, y1, ep, faces, rot):
    """Cube tangent posé à −Z du centre (rayon r : face nord dehors), tourné de rot° autour de l'axe Y du centre."""
    cx, cy, cz = centre
    cube(g, nom, (cx - w / 2, y0, cz - r - ep / 2), (cx + w / 2, y1, cz - r + ep / 2), faces, origin=(cx, cy, cz),
         rotation=(0, rot, 0))


def plaque_h(g, nom, c, demi, uv, ep=0.2):
    """Plaque horizontale (face up seule)."""
    c = np.asarray(c, float)
    cube(g, nom, c - (demi, ep / 2, demi), c + (demi, ep / 2, demi), {"up": uv})


def sous_uv(uv, u0, u1):
    return [uv[0] + u0, uv[1], uv[0] + u1, uv[3]]


EMIT = {}


def emit(sorte, pos, parent, rotation=None, nom=None):
    lst = EMIT.setdefault(sorte, [])
    n = nom or ("emit_" + sorte + (str(len(lst) + 1) if lst else ""))
    g = G(n, pos, parent, rotation=rotation)
    c = G("ctrl_emit", pos, g)
    lst.append((g, c))
    return g


EFFET = G("effet", (0, 0, 0))
JOUEUR = G("joueur", (0, 0, 0))
O = (0.0, 0.0, 0.0)

# --- plaque au sol (échelle = iris) et ses lumières
PLAQUE = G("plaque", O, EFFET)
cube(PLAQUE, "disque", (-R_PL, 0.04, -R_PL), (R_PL, 0.36, R_PL), {"up": UV["plaque"]})
ZONES = {}
for nom, demi, yy in (("bord", R_PL, 0.5), ("mil", 16.0, 0.72), ("coeur", 8.0, 0.94)):
    g = G(f"add_rainures_{nom}", O, PLAQUE)
    plaque_h(g, f"lueur_{nom}", (0, yy, 0), demi, UV[f"lueur_{nom}"], ep=0.1)
    ZONES[nom] = (g, G("ctrl_alpha", O, g))
TIRETS = G("add_tirets", O, PLAQUE)
plaque_h(TIRETS, "tirets", (0, 1.16, 0), 16.0, UV["tirets"], ep=0.1)
A_TIRETS = G("ctrl_alpha", O, TIRETS)
RIDEAU = G("add_rideau", O, PLAQUE)
A_RIDEAU = G("ctrl_alpha", O, RIDEAU)
NR = 48
for k in range(NR):
    autour(RIDEAU, f"rideau{k}", O, R_PL - 1.2, 2 * (R_PL - 1.2) * math.tan(math.pi / NR) + 0.02, 0.4, 18.4, 0.1,
           {"north": UV["rideau"], "south": UV["rideau"]}, 360 * k / NR)
for k in range(6):
    a = TAU * (k + 0.5) / 6
    emit("poussiere", (23 * math.cos(a), 0.6, 23 * math.sin(a)), PLAQUE)

# --- les cinq anneaux : ANN (position, rotation, échelle) > corps, gaine du liseré, gaine d'apparition
ANNEAUX = []
for i in range(NA):
    c = (0.0, YC[i], 0.0)
    A = G(f"anneau_{i + 1}", c, EFFET)
    corps = G(f"corps_{i + 1}", c, A)
    off = (24 * i + 4 * (i % 2)) % NSEG                                                    # décalage des cartouches d'un anneau à l'autre
    for k in range(NSEG):
        d = 0.12 if k % 2 else 0.0                                  # dessus et dessous décalés : jamais coplanaires
        y0, y1 = YC[i] - HA / 2 + d, YC[i] + HA / 2 + d
        kk = (k + off) % NSEG
        autour(corps, f"a{i + 1}s{k}", c, (R_OUT + R_IN) / 2, W_SEG, y0, y1, R_OUT - R_IN,
               {"north": sous_uv(UV[f"frise{kk // 32}"], 16 * (kk % 32), 16 * (kk % 32) + 16), "south": UV["interieur"], "up": UV["dessus"],
                "down": UV["dessous"], "east": UV["flanc"], "west": UV["flanc"]}, 360 * k / NSEG)
        fn = {f: UV["nervure"] for f in ("north", "south", "east", "west", "up", "down")}
        if k % 2 == 0:                                              # plot en relief sur le dessus (segments pairs)
            autour(corps, f"a{i + 1}n{k}", c, R_OUT - 1.0, 1.5, y1, y1 + 0.45, 2.2, fn, 360 * k / NSEG)
        else:                                                       # plot sous l'anneau (segments impairs)
            autour(corps, f"a{i + 1}n{k}", c, R_OUT - 1.0, 1.5, y0 - 0.45, y0, 2.2, fn, 360 * k / NSEG)
    gaine = G(f"add_lisere_{i + 1}", c, A)
    a_g = G("ctrl_alpha", c, gaine)
    lueur = G(f"add_apparition_{i + 1}", c, A)
    a_l = G("ctrl_alpha", c, lueur)
    for k in range(NSEG):
        rg = R_OUT + 0.3
        autour(gaine, f"g{i + 1}s{k}", c, rg, 2 * rg * math.tan(math.pi / NSEG) + 0.01, YC[i] - HA / 2 - 0.8,
               YC[i] + HA / 2 + 0.8, 0.12, {"north": UV["gaine"]}, 360 * k / NSEG)
        rl = R_OUT + 0.75
        autour(lueur, f"l{i + 1}s{k}", c, rl, 2 * rl * math.tan(math.pi / NSEG) + 0.01, YC[i] - HA / 2 - 2.0,
               YC[i] + HA / 2 + 2.0, 0.12, {"north": UV["lueur"], "south": UV["lueur"]}, 360 * k / NSEG)
    pts = []
    for j, a in enumerate((35.0, 215.0)):                           # deux points d'étincelles, +Y vers l'extérieur
        ar_ = math.radians(a)
        pos = (R_OUT * math.sin(ar_) * -1, YC[i] - HA / 2 + 0.3, -R_OUT * math.cos(ar_))
        # +Y du groupe couché vers l'extérieur (rotation x de 90° puis lacet)
        pts.append(emit("etincelle", pos, A, rotation=(-80, a, 0)))
    emit("mc_wax_on", (R_OUT * math.sin(math.radians(125)), YC[i], -R_OUT * math.cos(math.radians(125))), A,
         nom="emit_mc_wax_on")
    ANNEAUX.append(dict(A=A, gaine=gaine, a_g=a_g, lueur=lueur, a_l=a_l))

# --- éclair : colonne, bande qui remonte, stries entre les anneaux, rayon vers le ciel, lueur au sommet
ECLAIR = G("eclair", O, EFFET)
COL = G("add_colonne", O, ECLAIR)
A_COL = G("ctrl_alpha", O, COL)
NC = 20
for k in range(NC):
    autour(COL, f"col{k}", O, R_COL, 2 * R_COL * math.tan(math.pi / NC) + 0.02, 0.3, H_COL, 0.1,
           {"north": UV["colonne"], "south": UV["colonne"]}, 360 * k / NC)
FRONT = G("add_front", O, ECLAIR)
for k in range(NC):
    rf = R_COL + 1.5
    autour(FRONT, f"front{k}", O, rf, 2 * rf * math.tan(math.pi / NC) + 0.02, -4.0, 4.0, 0.1,
           {"north": UV["front"], "south": UV["front"]}, 360 * k / NC)
STRIES = []
for g_ in range(NA - 1):
    yg = YC[g_] + PAS / 2
    S_ = G(f"add_stries_{g_ + 1}", (0, yg, 0), ECLAIR)
    for o in range(4):
        cube(S_, f"strie{g_ + 1}_{o}", (-46, yg - 0.5, -0.05), (46, yg + 0.5, 0.05),
             {"north": UV["strie"], "south": UV["strie"]}, origin=(0, yg, 0), rotation=(0, 45 * o, 0))
        cube(S_, f"strieh{g_ + 1}_{o}", (-40, yg - 2.4, 0.25), (40, yg + 2.4, 0.35),
             {"north": UV["strie_halo"], "south": UV["strie_halo"]}, origin=(0, yg, 0), rotation=(0, 45 * o, 0))
    STRIES.append((S_, G("ctrl_alpha", (0, yg, 0), S_), yg))
RAYON = G("add_rayon", (0, Y_TOP, 0), ECLAIR)
A_RAYON = G("ctrl_alpha", (0, Y_TOP, 0), RAYON)
for k in range(8):
    autour(RAYON, f"rayon{k}", (0, Y_TOP, 0), 2.6, 2 * 2.6 * math.tan(math.pi / 8) + 0.02, Y_TOP, Y_TOP + 200, 0.1,
           {"north": UV["rayon"], "south": UV["rayon"]}, 360 * k / 8)
SOMMET = G("sommet", (0, Y_TOP + 2, 0), ECLAIR)
CAM_S = G("cam_sommet", (0, Y_TOP + 2, 0), SOMMET)
ADD_S = G("add_sommet", (0, Y_TOP + 2, 0), CAM_S)
cube(ADD_S, "halo_sommet", (-22, Y_TOP + 2 - 22, -0.05), (22, Y_TOP + 2 + 22, 0.05), {"south": UV["halo"]})
for k, yy in enumerate((6.0, 14.0, 22.0, 30.0)):
    emit("mc_electric_spark", (0, yy, 0), ECLAIR, nom="emit_mc_electric_spark")
for k in range(2):
    emit("eclat", ((-3.0, 3.0)[k], Y_TOP, 0), ECLAIR)

# --- particules (une plaque chacune ; groupes à la racine)
PART = {}
PART["poussiere"] = G("particle_poussiere", O)
cube(PART["poussiere"], "p_poussiere", (-0.3, 0.6, -0.15), (0.3, 1.2, 0.15), {"south": UV["point"], "north": UV["point"]})
PART["etincelle"] = G("particle_etincelle", O)
cube(PART["etincelle"], "p_etincelle", (-0.2, 0.3, -0.15), (0.2, 2.1, 0.15), {"south": UV["trait"], "north": UV["trait"]})
PART["eclat"] = G("particle_eclat", O)
cube(PART["eclat"], "p_eclat", (-0.7, 0.4, -0.15), (0.7, 1.8, 0.15), {"south": UV["eclat"], "north": UV["eclat"]})
outliner = [EFFET.json(), JOUEUR.json()] + [PART[k].json() for k in ("poussiere", "etincelle", "eclat")]
NEMIT = sum(len(v) for v in EMIT.values())
assert NEMIT <= 32, NEMIT


# ------------------------------------------------------------------ animations
def s(v):
    return v if isinstance(v, str) else str(round(float(v) + 0.0, 4))


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": s(x), "y": s(y), "z": s(z)}], "time": round(t, 4), "interpolation": "linear"}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def temps(L, fps=FPS):
    n = max(2, int(round(L * fps)))
    return [round(L * i / n, 4) for i in range(n + 1)]


class Anim:
    def __init__(self, nom, L, loop):
        self.nom, self.L, self.loop, self.A, self.sons = nom, L, loop, {}, []
        self.T = temps(L)

    def piste(self, g, ch, f, T=None):
        T = self.T if T is None else T
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += [kf(ch, t, *f(t)) for t in T]

    def fixe(self, g, ch, v):
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"].append(kf(ch, 0, *v))

    def alpha(self, c, f):
        """ctrl_alpha : f(t) ∈ [0, 1] (0 invisible) -> x = f − 1."""
        self.piste(c, "position", lambda t: (max(0.0, min(1.0, f(t))) - 1.0, 0, 0))

    def son(self, t, nom):
        self.sons.append({"channel": "sound", "data_points": [{"effect": nom, "file": ""}], "time": round(t, 3)})
        self.A["effects"] = {"name": "Effects", "type": "effect", "keyframes": self.sons}

    def cadence(self, sorte, f):
        """ctrl_emit (x) de chaque point de la sorte : f(t, i) -> −1 (coupé) … +7."""
        for i, (g, c) in enumerate(EMIT[sorte]):
            self.piste(c, "position", lambda t, i=i: (max(-1.0, min(7.0, f(t, i))), 0, 0))

    def json(self):
        return {"uuid": nuid(), "name": self.nom, "loop": self.loop, "override": False, "length": self.L, "snapping": 30,
                "selected": self.nom == "depart", "animators": self.A}


uni = lambda v: (v, v, v)
Z3 = (0, 0, 0)
UN = (1, 1, 1)


def cacher(an, groupes):
    for g in groupes:
        an.fixe(g, "scale", Z3)


# ---- courbes des anneaux (une courbe par phase, vitesse continue)
TFALL = 0.6                     # durée d'une descente
M1 = 0.13                       # pente résiduelle à la pose (en hauteurs par durée) : petit amorti continu
W_AM, K_AM = TAU * 5.0, 7.0     # amorti : 5 Hz, s'éteint en ≈ 0,3 s
TRISE = 0.65


def hauteur_descente(t, t0, i):
    """Hauteur au-dessus de la place : Hermite (part du repos, arrive avec une petite vitesse), puis oscillation amortie
    qui prolonge cette vitesse (pas d'arrêt sec, pas de rebond)."""
    if t <= t0:
        return Y_HAUT
    u = (t - t0) / TFALL
    if u <= 1:
        h01, h11 = -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
        return Y_HAUT * (1 - (h01 + h11 * M1))
    v = M1 * Y_HAUT / TFALL * (0.45 if i == 0 else 1.0)            # l'anneau du bas touche presque la plaque
    tau = t - t0 - TFALL
    return -v / W_AM * math.exp(-K_AM * tau) * math.sin(W_AM * tau)


def hauteur_montee(t, t0):
    """Décroche (petit appui de 0,3 px), puis monte en accélérant."""
    if t <= t0:
        return 0.0
    u = (t - t0) / TRISE
    appui = -0.3 * math.sin(math.pi * min(u / 0.15, 1.0)) if u < 0.15 else 0.0
    return appui + Y_HAUT * max(0.0, (u - 0.08) / 0.92) ** 2.3 if u <= 1 else Y_HAUT


def anneaux_anim(an, t_desc, t_mont, t_front, L, sens_front):
    """t_desc[i] : début de la descente ; t_mont[i] : début de la remontée ; t_front(i) : passage de la bande."""
    for i, R in enumerate(ANNEAUX):
        sg = 1 if i % 2 == 0 else -1
        td, tm = t_desc[i], t_mont[i]

        def pos(t, i=i, td=td, tm=tm):
            if t < tm:
                return (0, hauteur_descente(t, td, i), 0)
            return (0, hauteur_montee(t, tm), 0)

        def rot(t, td=td, tm=tm, sg=sg):
            if t < tm:
                u = min(1.0, max(0.0, (t - td) / TFALL))
                return (0, sg * 40 * (1 - u) ** 2, 0)                 # tourne en descendant, s'arrête posé
            u = min(1.0, (t - tm) / TRISE)
            return (0, -sg * 45 * u ** 2, 0)

        def ech(t, td=td, tm=tm):
            if t < td or t > tm + TRISE:
                return Z3
            a = 0.55 + 0.45 * sm(t, td, td + 0.16)                    # naît sous la lueur
            b = 1 - 0.45 * sm(t, tm + TRISE - 0.16, tm + TRISE - 0.01)
            return uni(a * b if t < tm + TRISE - 0.01 else 0.0)

        an.piste(R["A"], "position", pos)
        an.piste(R["A"], "rotation", rot)
        an.piste(R["A"], "scale", ech)
        tf = t_front(i)
        land = td + TFALL
        an.alpha(R["a_g"], lambda t, land=land, tf=tf: 0.5 + 0.5 * bump(t, land - 0.05, land, land + 0.05, land + 0.35)
                 + 0.5 * bump(t, tf - 0.08, tf, tf + 0.15, tf + 0.6))
        an.alpha(R["a_l"], lambda t, td=td, tm=tm, tf=tf: bump(t, td - 0.02, td + 0.04, td + 0.1, td + 0.35)
                 + 0.0 * tf  # pas de lueur au passage de la bande (ctrl_alpha partiel non simulé par l aperçu)
                 + bump(t, tm + TRISE - 0.3, tm + TRISE - 0.12, tm + TRISE - 0.05, tm + TRISE))


def plaque_charge_alpha(t, L):
    return {k: 0.55 + 0.45 * math.cos(TAU * (t / L - 0.15 * j)) for j, k in enumerate(("coeur", "mil", "bord"))}


# ---- charge (loop 4 s) : la plaque s'éclaire du cœur au bord, les tirets tournent, la lueur monte
LC = 4.0
ch = Anim("charge", LC, "loop")
ch.fixe(EFFET, "scale", UN)
ch.fixe(PLAQUE, "scale", UN)
cacher(ch, [ECLAIR] + [R["A"] for R in ANNEAUX])
for j, k in enumerate(("coeur", "mil", "bord")):
    ch.alpha(ZONES[k][1], lambda t, k=k: plaque_charge_alpha(t, LC)[k])
ch.piste(TIRETS, "rotation", lambda t: (0, 360 * t / LC, 0))
ch.alpha(A_TIRETS, lambda t: 0.7 + 0.3 * math.sin(TAU * t / LC * 2))
ch.piste(RIDEAU, "scale", lambda t: (1, 0.75 + 0.25 * math.sin(TAU * t / LC) + 0.06 * math.sin(TAU * 3 * t / LC), 1))
ch.alpha(A_RIDEAU, lambda t: 0.55 + 0.25 * math.sin(TAU * t / LC + 1.0))
ch.cadence("poussiere", lambda t, i: 1.0 + 0.8 * math.sin(TAU * (t / LC + i / 6)))
for so in ("etincelle", "mc_wax_on", "mc_electric_spark", "eclat"):
    ch.cadence(so, lambda t, i: -1)

# ---- depart (once 4,6 s)
LD = 4.6
D_DESC = [0.15 + 0.22 * i for i in range(NA)]               # posés à 0,75 … 1,63 s
TS0, TS1 = 2.0, 2.35                                        # la bande remonte la colonne
THIDE = 2.24                                                # la copie disparaît (bande à hauteur de poitrine)
D_MONT = [2.85 + 0.2 * (NA - 1 - i) for i in range(NA)]     # le dernier arrivé repart le premier
TFIN_D = D_MONT[0] + TRISE                                  # 4,3 s
de = Anim("depart", LD, "once")
de.fixe(EFFET, "scale", UN)
de.piste(EFFET, "scale", lambda t: uni(1.0 if t < LD - 0.04 else 0.0), T=[0, round(LD - 0.05, 4), LD])
de.piste(PLAQUE, "scale", lambda t: (lambda k: (k, 1, k))(1 - sm(t, 4.15, 4.5)))
front_d = lambda y: TS0 + (TS1 - TS0) * y / H_COL
anneaux_anim(de, D_DESC, D_MONT, lambda i: front_d(YC[i]), LD, 1)
for j, k in enumerate(("coeur", "mil", "bord")):
    de.alpha(ZONES[k][1], lambda t, j=j: (0.75 + 0.25 * sm(t, 0.0, 0.3)) * (1 - 0.5 * sm(t, 2.6, 3.4)) * (1 - sm(t, 3.9, 4.3))
             + 0.6 * bump(t, front_d(0) - 0.1, front_d(0), front_d(0) + 0.1, front_d(0) + 0.5))
de.piste(TIRETS, "rotation", lambda t: (0, 90 * t + 140 * t * t, 0))
de.alpha(A_TIRETS, lambda t: 1.0 - sm(t, 2.4, 3.2))
de.piste(RIDEAU, "scale", lambda t: (1, (0.85 + 0.35 * sm(t, 0.0, 1.6)) * (1 - sm(t, 2.35, 2.8)) + 0.001, 1))
de.alpha(A_RIDEAU, lambda t: 0.7 * (1 - sm(t, 2.3, 2.8)))
# éclair
de.fixe(ECLAIR, "scale", UN)
de.piste(COL, "scale", lambda t: (1, max(0.001, sm(t, TS0 - 0.02, TS1)), 1))
de.alpha(A_COL, lambda t: sm(t, TS0 - 0.05, TS0 + 0.05) * (1 - sm(t, 2.5, 3.0)))
de.piste(FRONT, "position", lambda t: (0, -2 + (H_COL + 6) * min(1.0, max(0.0, (t - TS0) / (TS1 - TS0 + 0.08))), 0))
de.piste(FRONT, "scale", lambda t: uni(bump(t, TS0 - 0.06, TS0 + 0.02, TS1 + 0.02, TS1 + 0.12)))
for S_, a_, yg in STRIES:
    tg = front_d(yg)
    de.piste(S_, "scale", lambda t, tg=tg: (lambda k: (k, 1, k))(0.0 if t < tg - 0.03 else 0.25 + 1.0 * sm(t, tg - 0.03, tg + 0.25)))
    de.alpha(a_, lambda t, tg=tg: bump(t, tg - 0.03, tg + 0.03, tg + 0.12, tg + 0.55))
de.piste(RAYON, "scale", lambda t: (1, max(0.001, sm(t, TS1 - 0.05, TS1 + 0.22)), 1))
de.alpha(A_RAYON, lambda t: sm(t, TS1 - 0.08, TS1) * (1 - sm(t, 2.6, 3.1)))
de.piste(SOMMET, "scale", lambda t: uni(1.1 * bump(t, TS1 - 0.08, TS1 + 0.04, TS1 + 0.1, TS1 + 0.55)))
# la copie du joueur : debout, cachée d'un coup dans la bande (échelle < 0,05 ; seule chose lue au départ)
de.fixe(JOUEUR, "position", Z3)
de.piste(JOUEUR, "scale", lambda t: uni(1.0 if t < THIDE else 0.0), T=[0, round(THIDE - 0.01, 4), round(THIDE, 4), LD])
# particules
de.cadence("poussiere", lambda t, i: -1 if t > 2.4 else 1.5 + 2 * sm(t, 0, 0.6))
de.cadence("etincelle", lambda t, i: (lambda land, tf: -1 + 7 * bump(t, land - 0.02, land, land + 0.08, land + 0.25)
                                      + 5 * bump(t, tf - 0.03, tf, tf + 0.08, tf + 0.25))(D_DESC[i // 2] + TFALL, front_d(YC[i // 2])))
de.cadence("mc_wax_on", lambda t, i: (lambda land: -1 + 6 * bump(t, land - 0.02, land, land + 0.1, land + 0.3))(D_DESC[i] + TFALL))
de.cadence("mc_electric_spark", lambda t, i: -1 + 7 * bump(t, front_d(6 + 8 * i) - 0.05, front_d(6 + 8 * i), front_d(6 + 8 * i) + 0.15, front_d(6 + 8 * i) + 0.45))
de.cadence("eclat", lambda t, i: -1 + 7 * bump(t, TS1 - 0.05, TS1, TS1 + 0.2, TS1 + 0.5))
de.son(0.1, "anneaux_descente")
de.son(TS0 - 0.15, "anneaux_eclair")
de.son(D_MONT[-1] - 0.05, "anneaux_retour")

# ---- arrivee (once 4,5 s) : la plaque s'ouvre, les anneaux descendent, la lumière tombe du ciel et le joueur apparaît
LA = 4.5
A_DESC = [0.2 + 0.22 * i for i in range(NA)]                # posés à 0,8 … 1,68 s
TR0 = 1.85                                                  # le rayon tombe du ciel
TA0, TA1 = 2.0, 2.35                                        # la bande descend la colonne
TAPP = 2.16                                                 # le joueur apparaît
A_MONT = [2.9 + 0.2 * (NA - 1 - i) for i in range(NA)]
ar = Anim("arrivee", LA, "once")
ar.fixe(EFFET, "scale", UN)
ar.piste(EFFET, "scale", lambda t: uni(1.0 if t < LA - 0.04 else 0.0), T=[0, round(LA - 0.05, 4), LA])
ar.piste(PLAQUE, "scale", lambda t: (lambda k: (k, 1, k))(max(0.001, sm(t, 0.0, 0.35)) * (1 - sm(t, 4.1, 4.42))))
front_a = lambda y: TA0 + (TA1 - TA0) * (1 - y / H_COL)
anneaux_anim(ar, A_DESC, A_MONT, lambda i: front_a(YC[i]), LA, -1)
for j, k in enumerate(("coeur", "mil", "bord")):
    ar.alpha(ZONES[k][1], lambda t, j=j: sm(t, 0.05 + 0.12 * (2 - j), 0.35 + 0.12 * (2 - j)) * (1 - 0.5 * sm(t, 2.6, 3.4)) * (1 - sm(t, 3.9, 4.3))
             + 0.6 * bump(t, TA1 - 0.1, TA1, TA1 + 0.1, TA1 + 0.5))
ar.piste(TIRETS, "rotation", lambda t: (0, 300 * t - 30 * t * t, 0))
ar.alpha(A_TIRETS, lambda t: sm(t, 0.2, 0.6) * (1 - sm(t, 2.6, 3.4)))
ar.piste(RIDEAU, "scale", lambda t: (1, max(0.001, 1.1 * sm(t, 0.3, 1.2) * (1 - sm(t, 2.3, 2.8))), 1))
ar.alpha(A_RIDEAU, lambda t: 0.7 * (1 - sm(t, 2.3, 2.8)))
ar.fixe(ECLAIR, "scale", UN)
# rayon : tombe du ciel (pivot au sommet de la colonne : il grandit vers le haut, donc on le fait descendre en position)
ar.piste(RAYON, "scale", lambda t: (1, max(0.001, sm(t, TR0, TR0 + 0.18)), 1))
ar.piste(RAYON, "position", lambda t: (0, 200 * (1 - sm(t, TR0, TR0 + 0.18)), 0))
ar.alpha(A_RAYON, lambda t: sm(t, TR0 - 0.02, TR0 + 0.04) * (1 - sm(t, 2.5, 3.0)))
ar.piste(SOMMET, "scale", lambda t: uni(1.1 * bump(t, TR0 + 0.1, TA0, TA0 + 0.05, TA0 + 0.45)))
ar.piste(COL, "scale", lambda t: (1, 1, 1))
ar.alpha(A_COL, lambda t: sm(t, TA0, TA1) * (1 - sm(t, 2.7, 3.2)))
ar.piste(FRONT, "position", lambda t: (0, H_COL + 4 - (H_COL + 6) * min(1.0, max(0.0, (t - TA0) / (TA1 - TA0 + 0.08))), 0))
ar.piste(FRONT, "scale", lambda t: uni(bump(t, TA0 - 0.06, TA0 + 0.02, TA1 + 0.02, TA1 + 0.12)))
for S_, a_, yg in STRIES:
    tg = front_a(yg)
    ar.piste(S_, "scale", lambda t, tg=tg: (lambda k: (k, 1, k))(0.0 if t < tg - 0.03 else 0.25 + 1.0 * sm(t, tg - 0.03, tg + 0.25)))
    ar.alpha(a_, lambda t, tg=tg: bump(t, tg - 0.03, tg + 0.03, tg + 0.12, tg + 0.55))
ar.fixe(JOUEUR, "position", Z3)
ar.piste(JOUEUR, "scale", lambda t: uni(0.0 if t < TAPP else 1.0), T=[0, round(TAPP - 0.01, 4), round(TAPP, 4), LA])
ar.cadence("poussiere", lambda t, i: -1 if t < 0.3 or t > 3.2 else 1 + 3 * bump(t, TAPP, TAPP + 0.1, 2.6, 3.1))
ar.cadence("etincelle", lambda t, i: (lambda land, tf: -1 + 7 * bump(t, land - 0.02, land, land + 0.08, land + 0.25)
                                      + 5 * bump(t, tf - 0.03, tf, tf + 0.08, tf + 0.25))(A_DESC[i // 2] + TFALL, front_a(YC[i // 2])))
ar.cadence("mc_wax_on", lambda t, i: (lambda land: -1 + 6 * bump(t, land - 0.02, land, land + 0.1, land + 0.3))(A_DESC[i] + TFALL))
ar.cadence("mc_electric_spark", lambda t, i: -1 + 7 * bump(t, front_a(6 + 8 * i) - 0.05, front_a(6 + 8 * i), front_a(6 + 8 * i) + 0.15, front_a(6 + 8 * i) + 0.45))
ar.cadence("eclat", lambda t, i: -1 + 6 * bump(t, TR0, TR0 + 0.05, TA0, TA0 + 0.3))
ar.son(0.15, "anneaux_descente")
ar.son(TA0 - 0.2, "anneaux_eclair")
ar.son(A_MONT[-1] - 0.05, "anneaux_retour")


# ---- particules
def part_anim(sorte, L, ch_, f, n=12):
    a = Anim(f"particle_{sorte}_fall", L, "loop")
    a.piste(PART[sorte], ch_, f, T=[round(i * L / n, 4) for i in range(n + 1)])
    return a


pp = part_anim("poussiere", 1.2, "scale", lambda t: uni(1 + 0.3 * math.sin(TAU * t / 1.2)), n=8)
pe = part_anim("etincelle", 0.3, "scale", lambda t: uni(1 + 0.3 * math.sin(TAU * t / 0.3)), n=8)
pc = part_anim("eclat", 1.0, "rotation", lambda t: (0, 360 * t / 1.0, 0), n=12)

ANIMS = [ch.json(), de.json(), ar.json(), pp.json(), pe.json(), pc.json()]
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures,
         "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
embarquer_sons(model, {n: f"sons/{n}.ogg" for n in ("anneaux_descente", "anneaux_eclair", "anneaux_retour")})
limiter_sons(model, max_effet=3)

os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


def ngroupes(n):
    return 1 + sum(ngroupes(c) for c in n.get("children", []) if isinstance(c, dict))


print(len(elements), "cubes ;", sum(ngroupes(n) for n in model["outliner"]), "groupes ; profondeur", max(depth(n) for n in model["outliner"]),
      ";", len(model["animations"]), "anims ;", sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()),
      "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;", NEMIT, "emit_ :", {k: len(v) for k, v in EMIT.items()})
