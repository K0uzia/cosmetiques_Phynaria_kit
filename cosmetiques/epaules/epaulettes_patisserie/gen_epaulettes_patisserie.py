"""Épaulettes fraise chantilly (ensemble Pâtisserie, thème Mignon). Design original, refonte du 2026-11-08.
Écrit epaulettes_patisserie.png, epaulettes_patisserie_e.png et .build/epaulettes_patisserie_brut.bbmodel à côté de ce script.

Retour de l'utilisateur (2026-11-08) : « les epaule sont jsute moche de ouf sauf la demoniaque » ; « les truc kawaii sont tous bof ».
L'ancienne version (une guimauve posée sur chaque épaule, visage, fanion) était petite, pâle et sans attache : elle se lisait
comme un jouet posé sur le bras. Référence de réussite : epaulieres_abyssales (volume, attache, taille). On reprend sa grammaire
(rang haut en éventail qui coiffe l'épaule, rang bas qui descend sur le flanc du bras, éléments qui remontent pour la
silhouette, lanières devant et derrière le bras, asymétrie gauche plus chargée) et on la traduit en pâtisserie :

- rang haut : « nappage miroir » à la fraise, pétales de glaçage rose franc qui coiffent l'épaule et coulent en gouttes rondes
  de longueurs inégales (technique du drip cake), reflet blanc net en fenêtre, vermicelles colorés posés sans se toucher ;
- rang bas : tuiles de pâte sablée dorée au bord festonné, bord plus cuit, piqûres de fourchette, cristaux de sucre ;
- sous-col : tranche de génoise (vrai volume) sous la racine des deux rangs, qui ferme l'écart avec l'épaule ;
- garniture qui remonte : chantilly pochée à la douille cannelée (étages octogonaux tournés de 15°, les cannelures font la
  spirale), fraise brillante à graines, cerise à queue et feuille, rosettes de crème ; gauche : grand tourbillon + fraise +
  deux rosettes ; droite : tourbillon plus petit + cerise + deux rosettes ;
- attache : ruban de chocolat décoré de points de crème, devant et derrière le bras ; nœud de satin fraise devant,
  perle de sucre derrière ; deux pans libres qui se balancent (bout en queue d'aronde).
Volume : chaque pétale et chaque tuile = deux peaux découpées par alpha autour d'âmes pleines plus étroites (recette validée).
Couleurs franches (leçon du thème Mignon : pastels trop clairs = blancs) : rose fraise (238, 92, 142), or de biscuit, crème
chaude, chocolat, rouge fraise ; ombres colorées, jamais grises ; liserés foncés saturés.

Distances : sous-col au-dessus de y = 24,4 (seconde couche du bras à 24,25) et à |x| >= 4,75 (tête + seconde couche à 4,5) ;
aucune garniture à |x| < 5,8 au-dessus de y = 24 (place pour un chapeau) ; tuiles à >= 8,37 de l'axe extérieur du bras ;
rubans à 2,37 px de l'axe du bras (seconde couche à 2,25). Contrôlés par les assertions en fin de géométrie.

Animations : idle (8 s : la chantilly respire en squash-and-stretch, un « boing » vers 4,8 s), walk, run, sneak, fall ;
event_equip (1,2 s : l'épaulette sort en « plop », la garniture arrive une à une, la fraise et la cerise tombent et
rebondissent ; un son block.honey_block.place) ; event_unequip (0,6 s) ; event_land (la chantilly s'écrase et rebondit).
Pas d'attack ni de hurt (pièce portée). Aucun son en mouvement (tools/sons.py).
Fonctions avancées : calque _e (reflets nets du glaçage et des fruits, fond très léger contre le saumon de nuit),
overlay_ambiance (ctrl_teinte / ctrl_lumiere, tools/ambiance.py, glaçage un peu plus sombre sous la pluie),
canal scale (squash-and-stretch, plop) et position (chute des fruits) : à juger en jeu (/cosmetique apercu).
Sources : .claude/styles/patisserie.md (Sources, section « Épaulettes »).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True
NOM = "epaulettes_patisserie"
TEX = 512
TAU = 2 * math.pi


def C(*a):
    return np.array(a, np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ palette (couleurs franches, ombres colorées)
GL_CLAIR, GL_BASE, GL_OMBRE, GL_LIS, GL_REFLET = C(255, 170, 200), C(238, 92, 142), C(176, 40, 96), C(140, 22, 74), C(255, 246, 250)
BI_CLAIR, BI_BASE, BI_CUIT, BI_OMBRE = C(252, 214, 140), C(232, 162, 82), C(186, 104, 44), C(122, 62, 30)
CR_CLAIR, CR_BASE, CR_CREUX = C(255, 254, 248), C(255, 243, 218), C(232, 196, 160)
CH_CLAIR, CH_BASE, CH_OMBRE = C(150, 92, 62), C(98, 54, 34), C(56, 28, 18)
FR_CLAIR, FR_BASE, FR_OMBRE, FR_GRAIN = C(255, 108, 116), C(222, 30, 58), C(128, 8, 30), C(255, 222, 118)
SAT_CLAIR, SAT_BASE, SAT_OMBRE = C(255, 176, 204), C(244, 108, 156), C(170, 40, 96)
V_CLAIR, V_OMBRE = C(110, 196, 80), C(44, 116, 42)
VERMI = [C(110, 222, 190), C(110, 184, 250), C(255, 226, 96), C(186, 148, 250), C(255, 255, 255), C(255, 150, 104)]
E_REFLET = (66, 52, 60)     # x 2,4 par tools/ambiance.py (plafond 225) -> (158, 125, 144) : reflet net la nuit
E_FOND = (13, 9, 11)        # fond très léger (non multiplié, sous le seuil de 24) contre le saumon de nuit


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


# ------------------------------------------------------------------ cartes peintes (coordonnées en px du modèle)
CARDS = []


def card(name, x0, x1, y0, y1, shape, paint, seed=1):
    CARDS.append(dict(name=name, x0=x0, x1=x1, y0=y0, y1=y1, shape=shape, paint=paint, seed=seed, w=x1 - x0, h=y1 - y0))


def dist_in(M, k, cap=1.0):
    """Distance au bord (px), plafonnée : érosions successives."""
    cur = Image.fromarray(M.astype(np.uint8) * 255, "L")
    D = np.zeros(M.shape, np.float32)
    for _ in range(max(1, int(cap * k))):
        a = np.array(cur) > 127
        if not a.any():
            break
        D += a
        cur = cur.filter(ImageFilter.MinFilter(3))
    return D / k


def seg_dist(X, Y, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-9
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
    return np.hypot(X - (ax + t * dx), Y - (ay + t * dy))


def ell(d, P, k, cx, cy, rx, ry):
    x, y = P((cx, cy))
    d.ellipse([x - rx * k, y - ry * k, x + rx * k, y + ry * k], fill=255)


def vermicelles(rng, X, Y, M, zone, n, used):
    """Petits bâtonnets de sucre (0,42 x 0,15 px), posés au hasard sans se toucher."""
    col = np.zeros(X.shape + (3,), np.float32)
    msk = np.zeros(X.shape, bool)
    tries = 0
    while n > 0 and tries < 400:
        tries += 1
        cx, cy = rng.uniform(*zone[0]), rng.uniform(*zone[1])
        if any(math.hypot(cx - ux, cy - uy) < 0.62 for ux, uy in used):
            continue
        a = rng.uniform(0, math.pi)
        dx, dy = 0.21 * math.cos(a), 0.21 * math.sin(a)
        dd = seg_dist(X, Y, (cx - dx, cy - dy), (cx + dx, cy + dy))
        m = (dd < 0.085) & M
        if m.sum() < 4:
            continue
        c = VERMI[len(used) % len(VERMI)]
        col[m] = c * 0.92
        col[(dd < 0.05) & M] = np.minimum(c * 1.08 + 10, 255)
        msk |= m
        used.append((cx, cy))
        n -= 1
    return col, msk


# --- rang haut : pétale de glaçage fraise qui coule
NL, NW, NM = 5.6, 3.6, 0.15


def nappe_hw(t):
    return NW / 2 * (0.5 + 0.5 * math.sin(math.pi / 2 * min(t / 0.4, 1)))


def make_nappe(name, drips, spr_seed, hl_side):
    def shape(d, P, k):
        n = 30
        up = [(0.7 * NL * i / n, nappe_hw(0.7 * i / n)) for i in range(n + 1)]
        d.polygon([P(p) for p in up + [(x, -y) for x, y in reversed(up)]], fill=255)
        ell(d, P, k, 0.7 * NL, 0, 0.16 * NL, NW / 2)
        for yy, ln, r in drips:      # coulures : ruban arrondi + goutte au bout
            x_end = 0.8 * NL + ln
            d.polygon([P((0.62 * NL, yy - r)), P((x_end, yy - r * 0.9)), P((x_end, yy + r * 0.9)), P((0.62 * NL, yy + r))], fill=255)
            ell(d, P, k, x_end, yy, r * 1.22, r * 1.22)

    def paint(X, Y, M, D, rng):
        t = X / NL
        col = lerp(GL_CLAIR, GL_BASE, np.clip(t * 1.25, 0, 1)[..., None] ** 0.9)
        col = lerp(col, GL_OMBRE, (np.clip((t - 0.62) * 2.2, 0, 1) * 0.55)[..., None])
        col = lerp(col, GL_OMBRE, (np.clip(1 - t / 0.14, 0, 1) * 0.6)[..., None])          # recouvrement à la racine
        col = lerp(col, GL_LIS, (np.clip(1 - D / 0.2, 0, 1) * 0.85)[..., None])            # liseré coloré
        used = []
        vc, vm = vermicelles(np.random.default_rng(spr_seed), X, Y, M & (D > 0.3), ((0.16 * NL, 0.66 * NL), (-NW * 0.36, NW * 0.36)), 9, used)
        # reflet net : fenêtre allongée + point, contraste franc (glaçage brillant)
        hy = hl_side * 0.2 * NW
        hl = (((X - 0.36 * NL) / (0.17 * NL)) ** 2 + ((Y - hy) / (0.07 * NW)) ** 2 < 1) | (np.hypot(X - 0.58 * NL, Y - hy * 1.15) < 0.12)
        for yy, ln, r in drips:
            hl |= np.hypot(X - (0.8 * NL + ln - r * 0.3), Y - (yy + r * 0.35)) < r * 0.36
        hl &= M & ~vm
        col = np.where(vm[..., None], vc, col)
        col = lerp(col, GL_REFLET, hl[..., None] * 1.0)
        col *= (1 + 0.025 * np.sin(X * 9 + Y * 5))[..., None]
        e = np.zeros_like(col)
        e[M] = E_FOND
        e[hl] = E_REFLET
        return col, e
    card(name, -NM, NL + NM, -NW / 2 - NM, NW / 2 + NM, shape, paint)


make_nappe("nappe_a", [(-1.05, 0.55, 0.26), (0.05, 1.0, 0.3), (1.0, 0.25, 0.24)], 41, 1)
make_nappe("nappe_b", [(-0.6, 0.95, 0.28), (0.55, 0.45, 0.26)], 42, -1)
make_nappe("nappe_c", [(-1.2, 0.3, 0.22), (-0.25, 0.7, 0.28), (0.9, 0.85, 0.27)], 43, 1)

# --- rang bas : tuile de pâte sablée festonnée
TL, TW, TM = 6.4, 3.1, 0.15


def tuile_hw(t):
    return TW / 2 * (0.6 + 0.4 * math.sin(math.pi / 2 * min(t / 0.3, 1)))


def make_tuile(name, lobes, seed):
    def shape(d, P, k):
        n = 30
        up = [(0.84 * TL * i / n, tuile_hw(0.84 * i / n)) for i in range(n + 1)]
        d.polygon([P(p) for p in up + [(x, -y) for x, y in reversed(up)]], fill=255)
        r = TW / (2 * lobes) * 1.12
        for j in range(lobes):
            yy = -TW / 2 + TW * (j + 0.5) / lobes
            ell(d, P, k, 0.84 * TL, yy * 0.97, r, r)

    def paint(X, Y, M, D, rng):
        t = X / TL
        r = np.random.default_rng(seed)
        nz = np.array(Image.fromarray((r.random((10, 10)) * 255).astype(np.uint8), "L").resize(X.shape[::-1], Image.BICUBIC), np.float32) / 255
        col = lerp(BI_BASE, BI_CLAIR, (np.clip(D / 0.9, 0, 1) * 0.75)[..., None])
        col = col * (0.95 + 0.1 * nz)[..., None]
        col = lerp(col, BI_CUIT, (np.clip(1 - D / 0.38, 0, 1) * 0.8)[..., None])           # bord plus cuit
        col = lerp(col, BI_OMBRE, (np.clip(1 - t / 0.32, 0, 1) ** 1.3 * 0.85)[..., None])  # sous le glaçage
        pk = np.zeros(X.shape, bool)
        for i in range(4):                                                                  # piqûres de fourchette
            for j in (-1, 0, 1):
                pk |= np.hypot(X - (0.42 + 0.12 * i) * TL, Y - j * 0.75 + (0.18 if i % 2 else 0)) < 0.1
        col = lerp(col, BI_CUIT * 0.8, (pk & M)[..., None] * 0.9)
        sg = np.zeros(X.shape, bool)
        for _ in range(16):                                                                 # cristaux de sucre
            cx, cy = r.uniform(0.35, 0.9) * TL, r.uniform(-0.4, 0.4) * TW
            sg |= np.hypot(X - cx, Y - cy) < 0.075
        col = lerp(col, CR_CLAIR, (sg & M & ~pk)[..., None] * 0.95)
        return col, np.zeros_like(col)
    card(name, -TM, TL + TM, -TW / 2 - TM, TW / 2 + TM, shape, paint)


make_tuile("tuile_a", 3, 51)
make_tuile("tuile_b", 4, 52)
make_tuile("tuile_c", 3, 53)

# --- ruban de chocolat : haut droit, deux pans libres (bout en queue d'aronde). y descend depuis la jointure.
SW = 1.5
RUB_H = {"rub_h": 4.4, "rub_m": 2.8, "rub_b": 3.0}


def make_ruban(name, H, queue):
    w = SW / 2

    def shape(d, P, k):
        if queue:
            d.polygon([P(p) for p in [(-w, 0), (w, 0), (w, -H), (0, -H + 0.65), (-w, -H)]], fill=255)
        else:
            d.polygon([P(p) for p in [(-w, 0), (w, 0), (w, -H), (-w, -H)]], fill=255)

    def paint(X, Y, M, D, rng):
        col = lerp(CH_BASE, CH_OMBRE, (np.clip(np.abs(X) / w, 0, 1) ** 2 * 0.4)[..., None])
        col = lerp(col, CH_CLAIR, (np.clip(1 - D / 0.16, 0, 1) * 0.75)[..., None])          # bord satiné
        dots = np.zeros(X.shape, bool)
        sh = np.zeros(X.shape, bool)
        for i in range(int(H / 0.62)):
            yy = -0.4 - i * 0.62
            if yy < -H + (0.9 if queue else 0.3):
                break
            dots |= np.hypot(X, Y - yy) < 0.15
            sh |= np.hypot(X + 0.05, Y - yy + 0.06) < 0.19
        col = lerp(col, CH_OMBRE, (sh & M)[..., None] * 0.7)
        col = lerp(col, CR_BASE, (dots & M)[..., None] * 1.0)
        col = lerp(col, CR_CLAIR, ((np.hypot(X + 0.04, Y - np.round((Y + 0.4) / 0.62) * 0.62 + 0.4 - 0.05) < 0.06) & dots)[..., None] * 1.0)
        return col, np.zeros_like(col)
    card(name, -w - 0.1, w + 0.1, -H - 0.1, 0.1, shape, paint)


make_ruban("rub_h", RUB_H["rub_h"], False)
make_ruban("rub_m", RUB_H["rub_m"], False)
make_ruban("rub_b", RUB_H["rub_b"], True)

# --- boucle du nœud de satin (x part du nœud vers l'extérieur)
BL = 2.2


def _boucle_shape(d, P, k):
    d.polygon([P(p) for p in [(0, -0.3), (0, 0.3), (1.0, 0.72), (1.0, -0.72)]], fill=255)
    ell(d, P, k, 1.3, 0.0, 0.82, 0.76)


def _boucle_paint(X, Y, M, D, rng):
    col = lerp(SAT_BASE, SAT_CLAIR, (np.clip(D / 0.5, 0, 1) * 0.6)[..., None])
    col = lerp(col, SAT_OMBRE, (np.clip(1 - D / 0.16, 0, 1) * 0.85)[..., None])
    pli = (np.abs(Y + 0.08 * X) < 0.07) & (X < 1.5)
    col = lerp(col, SAT_OMBRE, pli[..., None] * 0.8)
    col = lerp(col, SAT_OMBRE, (np.clip(1 - X / 0.5, 0, 1) * 0.6)[..., None])
    hl = (np.abs(Y - 0.38) < 0.07) & (X > 0.7) & (X < 1.7) & M
    col = lerp(col, C(255, 236, 244), hl[..., None] * 1.0)
    e = np.zeros_like(col)
    e[M] = E_FOND
    e[hl] = E_REFLET
    return col, e


card("boucle", -0.05, BL, -0.82, 0.82, _boucle_shape, _boucle_paint)


# --- calice de la fraise (5 sépales), feuille de cerise
def _calice_shape(d, P, k):
    for i in range(5):
        a = TAU * i / 5 + 0.3
        pts = []
        for j in range(13):
            u = j / 12
            r_ = 1.08 * u
            w_ = 0.26 * math.sin(math.pi * u) ** 0.8
            pts.append((r_ * math.cos(a) - w_ * math.sin(a), r_ * math.sin(a) + w_ * math.cos(a)))
        for j in range(12, -1, -1):
            u = j / 12
            r_ = 1.08 * u
            w_ = 0.26 * math.sin(math.pi * u) ** 0.8
            pts.append((r_ * math.cos(a) + w_ * math.sin(a), r_ * math.sin(a) - w_ * math.cos(a)))
        d.polygon([P(p) for p in pts], fill=255)
    ell(d, P, k, 0, 0, 0.36, 0.36)


def _vert_paint(X, Y, M, D, rng):
    col = lerp(V_OMBRE, V_CLAIR, (np.clip(D / 0.25, 0, 1) * 0.8)[..., None])
    col = lerp(col, V_OMBRE * 0.8, (np.hypot(X, Y) < 0.3)[..., None] * 0.5)
    return col, np.zeros_like(col)


card("calice", -1.2, 1.2, -1.2, 1.2, _calice_shape, _vert_paint)


def _feuille_shape(d, P, k):
    ell(d, P, k, 0.75, 0, 0.72, 0.34)


def _feuille_paint(X, Y, M, D, rng):
    col = lerp(V_OMBRE, V_CLAIR, (np.clip(D / 0.2, 0, 1) * 0.85)[..., None])
    col = lerp(col, V_OMBRE, ((np.abs(Y) < 0.045) & (X > 0.1))[..., None] * 0.8)
    return col, np.zeros_like(col)


card("feuille", -0.05, 1.55, -0.4, 0.4, _feuille_shape, _feuille_paint)


# --- volumes ronds (garniture) : silhouette de profil peinte, posée sur 3 ou 4 plaques croisées autour d'une âme pleine.
# Carte : x en travers (-R..R), y le long de l'axe (0 = base, H = bout).
RONDS = {}


def make_rond(name, R, H, prof, paint, M=0.12):
    def shape(d, P, k):
        n = 48
        up = [(prof(i / n) * R, H * i / n) for i in range(n + 1)]
        d.polygon([P((x, y)) for x, y in up] + [P((-x, y)) for x, y in reversed(up)], fill=255)
    RONDS[name] = (R, H, prof, M)
    card(name, -R - M, R + M, -M, H + M, shape, paint)


def anneaux(rings):
    """Profil d'une crème pochée : anneaux empilés (centre, demi-hauteur, rayon, en fractions), chacun bombé."""
    def prof(t):
        return max([r * max(0.0, 1 - ((t - yc) / hh) ** 2) ** 0.45 for yc, hh, r in rings] + [0.0])
    return prof


def paint_creme_rond(rings):
    """Chaque anneau : dessus éclairé, dessous dans l'ombre (creux coloré), cannelures en biais, liseré doux."""
    def paint(X, Y, M, D, rng):
        H = Y[M].max() if M.any() else 1.0
        t = Y / H
        best = np.full(X.shape, -1.0)
        u = np.zeros(X.shape)
        for yc, hh, r in rings:
            v = r * np.clip(1 - ((t - yc) / hh) ** 2, 0, 1) ** 0.45
            m = v > best
            best[m], u[m] = v[m], ((t - yc) / hh)[m]
        col = lerp(CR_BASE, CR_CLAIR, (np.clip(u, 0, 1) * 0.9)[..., None])
        col = lerp(col, CR_CREUX, (np.clip(-u - 0.15, 0, 1) * 0.95)[..., None])
        groove = np.abs(np.sin(TAU * (X / 0.5 + 1.2 * u))) < 0.2
        col = lerp(col, CR_CREUX, (groove & (np.abs(u) < 0.8))[..., None] * 0.5)
        col = lerp(col, CR_CREUX, (np.clip(1 - D / 0.1, 0, 1) * 0.6)[..., None])
        e = np.zeros_like(col)
        e[M] = E_FOND
        return col, e
    return paint


ANN_T = [(0.17, 0.2, 1.0), (0.47, 0.17, 0.8), (0.72, 0.14, 0.58), (0.9, 0.11, 0.32)]
ANN_R = [(0.15, 0.16, 1.0), (0.42, 0.14, 0.82), (0.66, 0.13, 0.6), (0.86, 0.13, 0.34)]
ANN_P = [(0.5, 0.5, 1.0)]


def prof_fraise(t):
    return (0.8 + 0.2 * math.sin(math.pi / 2 * min(t / 0.3, 1))) * max(0.0, 1 - t ** 2.2) ** 0.6


def paint_fraise_rond(X, Y, M, D, rng):
    H = Y[M].max() if M.any() else 1.0
    t = np.clip(Y / H, 0, 1)
    col = lerp(FR_OMBRE, FR_BASE, np.clip(D / 0.55, 0, 1)[..., None] ** 0.7)
    col = lerp(col, FR_CLAIR, (np.clip(D / 0.9, 0, 1) * np.clip(1 - np.abs(X + 0.3) / 0.7, 0, 1) * 0.55)[..., None])
    pit, seed = np.zeros(X.shape, bool), np.zeros(X.shape, bool)
    for i in range(9):
        for j in range(-4, 5):
            cx, cy = j * 0.44 + (0.22 if i % 2 else 0), 0.3 + i * 0.36
            pit |= np.hypot(X - cx, (Y - cy) * 0.85) < 0.13
            seed |= np.hypot(X - cx, (Y - cy) * 1.25) < 0.065
    inner = D > 0.12
    col = lerp(col, FR_OMBRE, (pit & inner)[..., None] * 0.5)
    col = np.where((seed & inner)[..., None], FR_GRAIN, col)
    hl = (((X + 0.42) / 0.16) ** 2 + ((Y - 0.42 * H) / (0.26 * H)) ** 2 < 1) & M & ~seed
    col = lerp(col, C(255, 236, 238), hl[..., None] * 1.0)
    col = lerp(col, C(255, 190, 170), (np.clip(1 - t / 0.1, 0, 1) * 0.5)[..., None])   # épaule claire sous le calice
    e = np.zeros_like(col)
    e[M] = E_FOND
    e[hl] = E_REFLET
    return col, e


def prof_cerise(t):
    return max(0.0, 1 - (2 * t - 1) ** 2) ** 0.5 * (1 - 0.12 * max(0.0, (t - 0.85) / 0.15))


def paint_cerise_rond(X, Y, M, D, rng):
    H = Y[M].max() if M.any() else 1.0
    col = lerp(C(104, 4, 24), C(204, 16, 50), np.clip(D / 0.45, 0, 1)[..., None] ** 0.8)
    col = lerp(col, C(240, 70, 92), (np.clip(D / 0.7, 0, 1) * np.clip(1 - np.hypot(X + 0.2, Y - 0.6 * H) / 0.5, 0, 1))[..., None])
    hl = (np.hypot((X + 0.32) / 0.13, (Y - 0.66 * H) / 0.2) < 1) & M
    col = lerp(col, C(255, 240, 244), hl[..., None] * 1.0)
    e = np.zeros_like(col)
    e[M] = E_FOND
    e[hl] = E_REFLET
    return col, e


make_rond("tourb_l", 1.8, 4.6, anneaux(ANN_T), paint_creme_rond(ANN_T))
make_rond("tourb_r", 1.45, 3.8, anneaux(ANN_T), paint_creme_rond(ANN_T))
make_rond("rosette", 1.05, 1.6, anneaux(ANN_R[:3] + [(0.84, 0.16, 0.3)]), paint_creme_rond(ANN_R[:3] + [(0.84, 0.16, 0.3)]))
make_rond("fraise_s", 1.35, 3.4, prof_fraise, paint_fraise_rond)
make_rond("cerise_s", 0.95, 1.85, prof_cerise, paint_cerise_rond)
make_rond("pointe", 0.5, 1.0, anneaux([(0.35, 0.36, 1.0), (0.75, 0.25, 0.55)]), paint_creme_rond([(0.35, 0.36, 1.0), (0.75, 0.25, 0.55)]))



# ------------------------------------------------------------------ images fixes (vrais volumes, 6 faces)
def _rgba(c):
    return np.dstack([np.clip(c, 0, 255), np.full(c.shape[:2], 255.0)]).astype(np.uint8)


def paint_creme(W=96, H=24):
    """Chantilly à la douille cannelée : 3 cannelures par face (v), plus claire vers le haut (u)."""
    jj, ii = np.mgrid[0:H, 0:W]
    v, u = (jj + 0.5) / H, (ii + 0.5) / W
    f = 0.5 + 0.5 * np.cos(TAU * 3 * v)
    c = lerp(CR_CREUX, CR_BASE, (f ** 0.6)[..., None])
    c = lerp(c, CR_CLAIR, (np.clip(f - 0.75, 0, 1) * 4 * 0.8)[..., None])
    c = c * (0.93 + 0.07 * u)[..., None]
    return _rgba(c)


def paint_genoise(S=48):
    r = np.random.default_rng(5)
    c = np.empty((S, S, 3), np.float32)
    c[...] = (246, 204, 112)
    yy, xx = np.mgrid[0:S, 0:S]
    for _ in range(46):
        cx, cy, rr = r.uniform(0, S), r.uniform(0, S), r.uniform(0.8, 1.9)
        m = np.hypot(xx - cx, yy - cy) < rr
        c[m] = (212, 160, 76)
    return _rgba(c)


def paint_fraise(W=96, H=32):
    """Fraise : rouge brillant, graines dorées en quinconce dans de petits creux, plus claire au centre de chaque face."""
    jj, ii = np.mgrid[0:H, 0:W]
    v, u = (jj + 0.5) / H, (ii + 0.5) / W
    c = lerp(FR_OMBRE, FR_BASE, (1 - np.abs(v - 0.5) * 1.6).clip(0, 1)[..., None] ** 0.6)
    c = lerp(c, FR_CLAIR, (np.clip(0.35 - np.abs(v - 0.42), 0, 1) * 2.2 * (0.5 + 0.5 * (1 - u)))[..., None])
    for a in range(0, W, 9):
        for b in range(4, H, 9):
            x0, y0 = a + (4.5 if (b // 9) % 2 else 0), b
            pit = np.hypot(ii - x0, (jj - y0) * 0.8) < 2.4
            c[pit] = lerp(c[pit], FR_OMBRE, 0.55)
            seed = np.hypot(ii - x0, (jj - y0) * 1.3) < 1.3
            c[seed] = FR_GRAIN
    return _rgba(c)


def paint_cerise(W=48, H=24):
    jj, ii = np.mgrid[0:H, 0:W]
    v, u = (jj + 0.5) / H, (ii + 0.5) / W
    c = lerp(C(110, 6, 26), C(206, 18, 52), (1 - np.abs(v - 0.5) * 1.8).clip(0, 1)[..., None] ** 0.7)
    c = lerp(c, C(255, 120, 130), (np.clip(0.3 - np.abs(v - 0.4), 0, 1) * 2)[..., None])
    hl = (np.abs(v - 0.34) < 0.12) & (np.abs(u - 0.4) < 0.08)
    c[hl] = (255, 240, 244)
    return _rgba(c), hl


def paint_flat(c0, c1, W=32, H=16, seed=3):
    r = np.random.default_rng(seed)
    n = np.array(Image.fromarray((r.random((6, 6)) * 255).astype(np.uint8), "L").resize((W, H), Image.BICUBIC), np.float32)[..., None] / 255
    return _rgba(lerp(c0, c1, n))


UV = {}
ALPHA = np.zeros((TEX, TEX), np.uint8)
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
tex_b64 = tex_e_b64 = None


def atlas():
    """Range toutes les images (densité la plus haute qui tient) et écrit les deux PNG."""
    global tex_b64, tex_e_b64
    cer, cer_hl = paint_cerise()
    fixed = [("creme", paint_creme()), ("genoise", paint_genoise()), ("fraise", paint_fraise()), ("cerise", cer),
             ("tige", paint_flat(C(80, 110, 40), C(120, 92, 46), 32, 8)), ("choco", paint_flat(CH_OMBRE, CH_BASE, 32, 32, 4)),
             ("perle", paint_flat(C(255, 190, 214), C(255, 236, 244), 24, 24, 6)),
             ("glace_tr", paint_flat(GL_OMBRE, GL_BASE, 32, 16, 7)), ("biscuit_tr", paint_flat(BI_CUIT, BI_BASE, 32, 16, 8))]
    fixed_e = {"cerise": cer_hl}

    def pack(dens):
        items = [(n, im.shape[1], im.shape[0]) for n, im in fixed] + [(p["name"], int(math.ceil(p["w"] * dens)), int(math.ceil(p["h"] * dens))) for p in CARDS]
        items.sort(key=lambda it: -it[2])
        uv, x, y, shelf = {}, 0, 0, 0
        for n, w, h in items:
            if x + w + 1 > TEX:
                x, y, shelf = 0, y + shelf + 1, 0
            if y + h > TEX - 6 or w > TEX:
                return None
            uv[n] = (x, y, x + w, y + h)
            x += w + 1
            shelf = max(shelf, h)
        return uv

    dens = 40.0
    while (uv := pack(dens)) is None:
        dens -= 0.2
    UV.update(uv)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, im in fixed:
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1] = im
        tex_e[v0:v1, u0:u1, :3] = E_FOND
        tex_e[v0:v1, u0:u1, 3] = 255
        if n in fixed_e:
            tex_e[v0:v1, u0:u1, :3][fixed_e[n]] = E_REFLET
    for i, p in enumerate(CARDS):
        u0, v0, u1, v1 = UV[p["name"]]
        W, H, ss = u1 - u0, v1 - v0, 3
        k = W * ss / p["w"]
        P = lambda q, p=p, W=W, H=H: ((q[0] - p["x0"]) / p["w"] * W * ss, (p["y1"] - q[1]) / p["h"] * H * ss)
        mimg = Image.new("L", (W * ss, H * ss), 0)
        p["shape"](ImageDraw.Draw(mimg), P, k)
        M = np.array(mimg) > 127
        jj, ii = np.mgrid[0:H * ss, 0:W * ss]
        X = p["x0"] + (ii + 0.5) / (W * ss) * p["w"]
        Y = p["y1"] - (jj + 0.5) / (H * ss) * p["h"]
        D = dist_in(M, k)
        col, e = p["paint"](X, Y, M, D, np.random.default_rng(100 + i))
        al = M.reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.5
        cc = col.reshape(H, ss, W, ss, 3).mean(axis=(1, 3))
        ee = e.reshape(H, ss, W, ss, 3).mean(axis=(1, 3))
        if al.any():
            cc[~al] = cc[al].mean(axis=0)
        tex[v0:v1, u0:u1, :3] = np.clip(cc, 0, 255).astype(np.uint8)
        tex[v0:v1, u0:u1, 3] = al * 255
        em = al & (ee.max(axis=2) > 2)
        tex_e[v0:v1, u0:u1, :3] = np.clip(ee, 0, 255).astype(np.uint8) * em[..., None]
        tex_e[v0:v1, u0:u1, 3] = em * 255
    assert tex[TEX - 3, TEX - 3, 3] == 0
    ALPHA[...] = tex[..., 3]
    tex[..., :3] &= 0xFC
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
    b64 = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        b64.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    tex_b64, tex_e_b64 = b64
    return dens


DENS = atlas()

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx, ordre du mod et du renderer."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def group(name, origin, parent=None):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def plate(g, name, c, X, Y, w, h, tile, th=0.3):
    """Plaque fine : contour par l'alpha, tranches transparentes. u suit X, le haut de l'image est +Y."""
    X, Y = unit(np.asarray(X, float)), unit(np.asarray(Y, float))
    u0, v0, u1, v1 = UV[tile]
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def bloc(g, name, c, X, Y, l, w, th, tile, ends=(True, True)):
    """Vrai volume : l le long de X, w le long de Y, th le long de X x Y ; ends = faces de bout (east/west) visibles."""
    X, Y = unit(np.asarray(X, float)), unit(np.asarray(Y, float))
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    u0, v0, u1, v1 = UV[tile]
    fc = {f: [u0, v0, u1, v1] for f in ("north", "south", "up", "down")}
    fc["west"] = [u0, v0, u1, v1] if ends[0] else CLEAR
    fc["east"] = [u0, v0, u1, v1] if ends[1] else CLEAR
    c = np.asarray(c, float)
    cube(g, name, c - (l / 2, w / 2, th / 2), c + (l / 2, w / 2, th / 2), c, euler(R_), fc)


def bar(g, name, p, q, r, tile, u0=0.0, u1=1.0, ov=0.0, turn=0.0, up=None, caps=(True, True)):
    """Tronçon à section octogonale (deux pavés à 45°, culots à 0,12 px l'un de l'autre). turn : torsion (degrés)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X = unit(q - p)
    ref = np.asarray(up, float) if up is not None else (V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0))
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    ct, st = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    Y, Z_ = ct * Y + st * Z_, -st * Y + ct * Z_
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R0 = np.column_stack([X, Y, Z_])
    R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
    bu0, bv0, bu1, bv1 = UV[tile]
    ua = lerp(bu0, bu1, u0)
    ub = max(lerp(bu0, bu1, u1), ua + 2)
    lg = [ua, bv0, ub, bv1]
    end = [ub - 2, bv0 + 2, ub, bv1 - 2]
    faces = {"south": lg, "north": lg, "up": lg, "down": lg, "east": end if caps[1] else CLEAR, "west": end if caps[0] else CLEAR}
    cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R0), faces)
    ch = min(0.12, L * 0.2)
    cube(g, name + "o", p + (-ov + ch, -r * 0.97, -r * 0.97), p + (L + ov - ch, r * 0.97, r * 0.97), p, euler(R45), faces)


def etages(g, name, base, axis, secs, tile, twist=15.0, up=None, first_cap=False):
    """Volume rond par étages octogonaux le long de axis. secs = [(rayon, longueur)]. Le culot du plus large est visible
    (marche), celui du plus étroit est enfoui de 0,15 px dans son voisin. Renvoie le point du bout."""
    A = unit(np.asarray(axis, float))
    pos = np.asarray(base, float).copy()
    tot = sum(l for _, l in secs)
    acc = 0.0
    n = len(secs)
    for i, (r, l) in enumerate(secs):
        start, end = pos.copy(), pos + A * l
        c0, c1 = (first_cap if i == 0 else True), True
        if i > 0 and r < secs[i - 1][0]:
            c0, start = False, start - A * 0.15
        if i < n - 1 and secs[i + 1][0] > r:
            c1, end = False, end + A * 0.15
        bar(g, f"{name}{i}", start, end, r, tile, acc / tot, (acc + l) / tot, turn=twist * i, up=up, caps=(c0, c1))
        pos = pos + A * l
        acc += l
    return pos


def lame(g, name, root, d, nhint, L, W, tile, cardL, cardW, cardM, hwf, core_tile, ofs=0.0, peau=0.45):
    """Pétale / tuile en vrai volume : deux peaux découpées (plan ±peau) autour de trois âmes pleines plus étroites
    qui suivent la demi-largeur hwf(t) du contour."""
    X = unit(np.asarray(d, float))
    N = unit(np.asarray(nhint, float) - (np.asarray(nhint, float) @ X) * X)
    Y = np.cross(N, X)
    root = np.asarray(root, float) + N * ofs
    sL, sW = L / cardL, W / cardW
    c = root + X * (L / 2)
    for k_, sg in (("p", 1), ("q", -1)):
        plate(g, f"{name}{k_}", c + N * sg * peau, X, Y, (cardL + 2 * cardM) * sL, (cardW + 2 * cardM) * sW, tile)
    th = 2 * (peau - 0.15 - 0.11)
    segs = [(0.05, 0.3), (0.3, 0.55), (0.55, 0.78)]
    for j, (a, b) in enumerate(segs):
        hw = min(hwf(a), hwf(b)) * sW * 0.84
        bloc(g, f"{name}a{j}", root + X * L * (a + b) / 2, X, Y, L * (b - a), 2 * hw, th, core_tile, ends=(j == 0, j == len(segs) - 1))


# Un côté : s = -1 gauche, +1 droit.
GARN, STRAPS = [], []
STRAP_Z = 2.72      # âme de chocolat (0,54) : face intérieure à 2,37 px de l'axe du bras (seconde couche à 2,25)
STRAP_CORE = 0.54


def ruban(armure, s, tag, zs, nom, x_top, x_bot, y_top, y_band, k_tail):
    z = zs * STRAP_Z
    X_ = V(s * -zs, 0, 0)
    top, bot = V(s * x_top, y_top, z), V(s * x_bot, y_band, z)
    Y_h = unit(top - bot)
    X_h = unit(X_ - (X_ @ Y_h) * Y_h)
    Hh = np.linalg.norm(top - bot)
    Hc = Hh - 0.15
    mid = top - Y_h * (Hc / 2)
    plate(armure, f"rub_h_{nom}_{tag}", mid, X_h, Y_h, SW + 0.2, Hc + 0.2, "rub_h")
    bloc(armure, f"rub_ha_{nom}_{tag}", mid, Y_h, X_h, Hc, SW * 0.58, STRAP_CORE, "choco", ends=(False, True))
    if zs < 0:      # nœud de satin devant
        kn = bot + V(0, 0, zs * 0.5)
        bloc(armure, f"noeud_{tag}", kn, V(1, 0, 0), V(0, 1, 0), 0.62, 0.72, 0.5, "perle")
        for side in (-1, 1):
            dX = unit(V(side * s * 1.0, 0.42, zs * 0.32 * side))
            dY = unit(np.cross(V(0, 0, 1), dX) * side)
            plate(armure, f"boucle{'g' if side < 0 else 'd'}_{tag}", kn + dX * (BL / 2 - 0.05) + V(0, 0, zs * 0.05), dX, dY, BL + 0.05, 1.64, "boucle")
    else:           # perle de sucre derrière
        bar(armure, f"perle_{tag}", bot + V(-0.4, 0, zs * 0.34), bot + V(0.4, 0, zs * 0.34), 0.38, "perle", turn=22.5)
    y = y_band
    cx = s * x_bot
    parent = armure
    for j, (tile, H) in enumerate((("rub_m", RUB_H["rub_m"] * k_tail), ("rub_b", RUB_H["rub_b"] * k_tail))):
        g = group(f"ruban{j}_{nom}_{tag}", [cx, y, z], parent=parent)
        Xj = unit(X_ + V(0, 0, (1 if j == 0 else -1) * math.tan(math.radians(5))))
        y0 = y - (0.15 if j == 0 else 0.0)
        Hj = H - (0.15 if j == 0 else 0.0)
        plate(g, f"rub{j}_{nom}_{tag}", V(cx, y0 - Hj / 2, z), Xj, V(0, 1, 0), SW + 0.2, Hj + 0.2, tile)
        h_core = Hj * (1 if j == 0 else 0.5)
        bloc(g, f"rub{j}a_{nom}_{tag}", V(cx, y0 - h_core / 2, z), V(0, 1, 0), Xj, h_core, SW * 0.58, STRAP_CORE, "choco", ends=(j == 1, j == 0))
        STRAPS.append((g, s, zs, j))
        parent = g
        y -= H


def rond(g, name, base, axis, tile, n=4, spin=0.0, ame=0.6, ref=None):
    """Volume rond : n plaques croisées autour de l'axe (silhouette peinte), âme pleine octogonale à ame x le profil."""
    R, H, prof, M = RONDS[tile]
    A = unit(np.asarray(axis, float))
    r0 = np.asarray(ref, float) if ref is not None else (V(1, 0, 0) if abs(A[0]) < 0.9 else V(0, 0, 1))
    U0 = unit(r0 - (r0 @ A) * A)
    W0 = np.cross(A, U0)
    base = np.asarray(base, float)
    c = base + A * (H / 2)
    for k in range(n):
        a = math.radians(spin + 180.0 * k / n)
        U = math.cos(a) * U0 + math.sin(a) * W0
        plate(g, f"{name}p{k}", c, U, A, 2 * (R + M), H + 2 * M, tile)
    if ame:
        ts = [0.04, 0.3, 0.55, 0.78]
        secs = []
        for a_, b_ in zip(ts[:-1], ts[1:]):
            secs.append((ame * R * min(prof(a_), prof(b_)), H * (b_ - a_)))
        core = "creme" if tile.startswith(("tourb", "ros", "pointe")) else ("fraise" if tile.startswith("fraise") else "cerise")
        etages(g, f"{name}a", base + A * H * ts[0], A, secs, core, twist=0, up=U0, first_cap=True)
    return base + A * H


def tourbillon(armure, s, tag, at, sc):
    """Chantilly pochée à la douille cannelée : quatre plaques croisées (étoile vue de dessus) autour d'une âme pleine ;
    la pointe recourbée est dans son propre groupe (elle suit avec retard)."""
    base = V(s * at[0], at[1], at[2])
    tile = f"tourb_{tag}"
    R, H, prof, M = RONDS[tile]
    g0 = group(f"tourb_{tag}", base, parent=armure)
    rond(g0, f"tourb_{tag}_", base + V(0, -0.3, 0), V(0, 1, 0), tile, n=6, spin=0, ame=0.42)
    pb = base + V(0, 0.86 * H - 0.3, 0)
    g1 = group(f"tourb_bout_{tag}", pb, parent=g0)
    tip = rond(g1, f"tourb_b_{tag}_", pb, V(s * 0.45, 1, 0.1), "pointe", n=4, spin=22.5, ame=0.55)
    GARN.append(("tourb", g0, g1, s))
    return [base + V(0, 0.5, 0), tip]


def rosette(armure, s, tag, k, at, sc):
    base = V(s * at[0], at[1], at[2])
    g = group(f"rosette{k}_{tag}", base, parent=armure)
    rond(g, f"ros{k}_{tag}_", base + V(0, -0.2, 0), V(0, 1, 0), "rosette", n=6, spin=15 * k + 10, ame=0.42)
    GARN.append(("ros", g, None, s))
    return [base, base + V(0, 1.0, 0)]


def fraise(armure, s, tag, at, axis):
    """Fraise couchée sur la crème, pointe vers l'extérieur ; calice de sépales et queue côté épaule."""
    base = V(s * at[0], at[1], at[2])
    A = unit(V(s * axis[0], axis[1], axis[2]))
    g = group(f"fraise_{tag}", base, parent=armure)
    tip = rond(g, f"fr_{tag}_", base, A, "fraise_s", n=3, spin=15, ref=V(0, 1, 0))
    up_ = unit(np.cross(A, V(0, 0, 1)) if abs(A[2]) < 0.9 else V(1, 0, 0))
    plate(g, f"calice_{tag}", base - A * 0.05, up_, np.cross(A, up_), 2.4, 2.4, "calice")
    bar(g, f"queue_{tag}", base - A * 0.1, base - A * 0.62 + V(0, 0.15, 0), 0.13, "tige")
    GARN.append(("fruit", g, None, s))
    return [base, tip]


def cerise(armure, s, tag, at):
    base = V(s * at[0], at[1], at[2])
    g = group(f"cerise_{tag}", base, parent=armure)
    top = rond(g, f"ce_{tag}_", base, V(0, 1, 0), "cerise_s", n=4, spin=10)
    gt = group(f"tige_{tag}", top - V(0, 0.1, 0), parent=g)
    p1 = top + V(s * 0.25, 0.9, 0.15)
    p2 = p1 + V(s * 0.65, 0.55, 0.1)
    bar(gt, f"tige0_{tag}", top - V(0, 0.3, 0), p1, 0.11, "tige", turn=0)
    bar(gt, f"tige1_{tag}", p1 - unit(p1 - top) * 0.05, p2, 0.1, "tige", turn=22.5, caps=(False, True))
    fd = unit(V(s * 0.9, 0.2, -0.45))
    plate(gt, f"feuille_{tag}", p1 + fd * 0.78 + V(0, 0.05, 0), fd, unit(np.cross(V(0, 1, 0.2), fd)), 1.6, 0.8, "feuille")
    GARN.append(("fruit", g, gt, s))
    return [base, top, p2]


TIPS = []


def epaulette(s, tag, azA, azB, sc, garn, x_lan, y_band, k_tail):
    arm = group("left_arm" if s < 0 else "right_arm", V(s * 5, 22, 0))
    armure = group(f"armure_{tag}", V(s * 5, 22, 0), parent=arm)
    # sous-col : tranche de génoise posée sur l'épaule, au-dessus de la seconde couche du bras, hors de la tête
    xa, xb = 5.6, 8.9
    bloc(armure, f"genoise_{tag}", V(s * (xa + xb) / 2, 24.9, 0), V(1, 0, 0), V(0, 1, 0), xb - xa, 1.0, 5.4, "genoise")
    # rang bas : tuiles de biscuit qui descendent sur le flanc du bras, en éventail vu de profil
    hb = V(s * 9.25, 24.6, 0)
    tiles = ["tuile_b", "tuile_a", "tuile_c", "tuile_a"]
    mid = (len(azB) - 1) / 2
    for i, b in enumerate(azB):
        ca, sa = math.cos(math.radians(b)), math.sin(math.radians(b))
        d = V(s * 0.32, -ca, sa)
        off = 1 - abs(i - mid) / max(mid, 1) * 0.25
        lame(armure, f"bas{i}_{tag}", hb + V(0, 0, sa * 0.5), d, V(s, 0.2, sa * 0.35), (6.6 + 0.4 * i) * sc * off, 3.4 * sc, tiles[i % 4],
             TL, TW, TM, tuile_hw, "biscuit_tr", ofs=0.25 * (len(azB) - abs(i - mid)), peau=0.4)
    # rang haut : nappage qui coiffe l'épaule et coule vers l'avant, l'extérieur et l'arrière
    hh = V(s * 6.0, 26.05, 0)
    mid = (len(azA) - 1) / 2
    naps = ["nappe_a", "nappe_b", "nappe_c", "nappe_b"]
    for i, a in enumerate(azA):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        d = V(s * ca, -0.42, sa)
        lame(armure, f"haut{i}_{tag}", hh, d, V(s * 0.42, 1, sa * 0.42), (6.2 if abs(a) < 35 else 5.7) * sc, 4.0 * sc, naps[i % 4],
             NL, NW, NM, nappe_hw, "glace_tr", ofs=0.2 * (len(azA) - abs(i - mid)), peau=0.42)
    for kind, args in garn:
        TIPS.append(kind(armure, s, tag, *args))
    ruban(armure, s, tag, -1, "av", x_lan[0][0], x_lan[0][1], 24.25, y_band, k_tail)
    ruban(armure, s, tag, 1, "ar", x_lan[1][0], x_lan[1][1], 24.25, y_band, k_tail)
    return arm


# gauche : plus chargée (grand tourbillon, fraise, deux rosettes) ; droite : tourbillon plus petit, cerise, deux rosettes
epaulette(-1, "l", (-56, -20, 16, 52), (-48, -17, 12, 38), 1.0,
          [(tourbillon, ((7.7, 25.75, -0.35), 1.0)),
           (fraise, ((8.4, 26.4, 1.55), (0.72, 0.3, 0.5))),
           (rosette, (0, (9.1, 25.55, -2.0), 1.0)),
           (rosette, (1, (6.85, 26.35, 2.0), 0.85))],
          ((5.6, 7.0), (5.6, 6.9)), 20.3, 1.0)
epaulette(1, "r", (-46, -4, 40), (-40, -6, 28), 0.9,
          [(tourbillon, ((7.7, 25.7, 0.55), 0.82)),
           (cerise, ((9.0, 25.6, -1.4),)),
           (rosette, (0, (9.1, 25.5, 1.95), 0.9)),
           (rosette, (1, (6.9, 26.3, -1.85), 0.8))],
          ((5.6, 6.8), (5.6, 7.0)), 20.7, 0.85)


# ------------------------------------------------------------------ contrôles de distance (pose de base)
def corners(e):
    """Points à contrôler : coins du cube, ou, pour une plaque découpée, les texels opaques de son image (deux faces)."""
    f, t = np.array(e["from"], float), np.array(e["to"], float)
    o = np.array(e["origin"])
    rx, ry, rz = [math.radians(v) for v in e.get("rotation", [0, 0, 0])]
    Rx = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Ry = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Rz = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    R = Rz @ Ry @ Rx
    if e["faces"]["east"]["uv"] == CLEAR and e["faces"]["south"]["uv"] != CLEAR:
        u0, v0, u1, v1 = [int(round(v)) for v in e["faces"]["south"]["uv"]]
        a = ALPHA[v0:v1, u0:u1] > 0
        jj, ii = np.where(a)
        lx = f[0] + (ii + 0.5) / a.shape[1] * (t[0] - f[0])
        ly = t[1] - (jj + 0.5) / a.shape[0] * (t[1] - f[1])
        pts = []
        for z in (f[2], t[2]):
            P_ = np.stack([lx, ly, np.full_like(lx, z)], 1) - o
            pts.extend(list(o + P_ @ R.T))
        return pts
    return [o + R @ (np.array([a, b, c]) - o) for a in (f[0], t[0]) for b in (f[1], t[1]) for c in (f[2], t[2])]


def visible(e):
    return any(fc["uv"] != CLEAR for fc in e["faces"].values())


for e in elements:
    if not visible(e):
        continue
    for p in corners(e):
        if p[1] > 24.0:
            assert abs(p[0]) >= 4.62, f"{e['name']} trop près de la tête : {p}"
        ax = abs(p[0])
        if 3.87 < ax < 8.37 and p[1] < 24.37 and abs(p[2]) < 2.37 and not e["name"].startswith(("genoise",)):
            raise AssertionError(f"{e['name']} dans la seconde couche du bras : {p}")
for tr in TIPS:
    for p in tr[1:]:
        assert abs(p[0]) >= 5.8, f"garniture trop près de la tête : {p}"


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node("right_arm"), bone_node("left_arm")]


# ------------------------------------------------------------------ animations
# MIROIR D'AXES (guide, section 3) : +X = le haut part vers l'arrière ; +Z = le côté droit monte, donc le haut part vers la gauche.
# out > 0 penche la garniture vers l'extérieur (loin de la tête) ; back > 0 bascule son haut vers l'arrière.
def rot_out(s, out, back):
    return back, 0.0, -s * out


def ruban_rot(s, zs, swing, sway):
    """swing >= 0 décolle le pan du bras (devant : vers l'avant, derrière : vers l'arrière)."""
    return -zs * swing, 0.0, s * sway


def squash(k):
    return 1 / math.sqrt(k), k, 1 / math.sqrt(k)


def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def anim(name, length, tracks, kps=10, loop="loop", sons=()):
    """tracks : {groupe: {canal: f(t)}}."""
    n = max(8, int(round(length * kps)))
    times = [i * length / n for i in range(n + 1)]
    A = {}
    for g, chans in tracks.items():
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(ch, t, f(t)) for ch, f in chans.items() for t in times]}
    if sons:
        A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
            {"channel": "sound", "data_points": [{"effect": nm, "file": ""}], "time": t} for t, nm in sons]}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


def boing(t, t0, amp=1.0):
    """Rebond amorti qui part de 0 à t0 (≈ 0 au bout de 1,5 s)."""
    if t < t0:
        return 0.0
    u = t - t0
    return amp * math.exp(-u * 4.0) * math.sin(TAU * 2.4 * u)


def state(name, L, cyc, k0, kA, lean0, leanA, back0, backA, rib0, ribA, boings=(), kps=10):
    tr = {}
    for i, (kind, g0, g1, s) in enumerate(GARN):
        ph0 = 0.17 * i + (0.29 if s > 0 else 0)
        w = {"tourb": 1.0, "ros": 0.55, "fruit": 0.4}[kind]

        def bo(t, ph0=ph0):
            return sum(boing(t, t0 + 0.05 * ph0, a) for t0, a in boings)

        def fs(t, ph0=ph0, w=w):
            ph = TAU * (cyc * t / L - ph0)
            return squash(1 + w * (k0 + kA * math.cos(ph) - 0.11 * bo(t)))

        def fr(t, ph0=ph0, w=w, s=s):
            ph = TAU * (cyc * t / L - ph0)
            return rot_out(s, w * (lean0 + leanA * math.sin(ph)) + 3 * w * bo(t), w * (back0 + backA * math.sin(ph + 0.8)))
        ch = {"rotation": fr}
        if kind != "fruit":
            ch["scale"] = fs
        tr[g0] = ch
        if g1 is not None:
            def fb(t, ph0=ph0, s=s, w=w):
                ph = TAU * (cyc * t / L - ph0 - 0.14)
                return rot_out(s, 1.6 * leanA * math.sin(ph) + 9 * bo(t - 0.06), 1.4 * backA * math.sin(ph + 0.6))
            tr[g1] = {"rotation": fb}
    for g, s, zs, j in STRAPS:
        def fq(t, s=s, zs=zs, j=j):
            ph = TAU * (cyc * t / L - 0.15 * j - (0.2 if zs > 0 else 0) - (0.31 if s > 0 else 0))
            amp = ribA * (1 + 0.5 * j)
            return ruban_rot(s, zs, rib0 * (1 if j == 0 else 0.6) + amp * math.sin(ph), 0.7 * amp * math.sin(ph + 1.1))
        tr[g] = {"rotation": fq}
    return anim(name, L, tr, kps=kps)


idle = state("idle", 8.0, 2, 0.0, 0.025, 0.4, 1.2, 0.0, 0.8, 1.5, 0.9, boings=((4.8, 1.0),), kps=12)
walk = state("walk", 1.6, 2, 0.0, 0.045, 0.6, 1.8, 1.2, 2.6, 5.0, 2.8)
run = state("run", 1.0, 2, -0.02, 0.07, 1.0, 2.6, 6.0, 3.5, 14.0, 5.0)
sneak = state("sneak", 3.0, 1, -0.07, 0.02, 1.5, 0.6, -1.0, 0.5, 2.0, 1.0)
fall = state("fall", 1.2, 3, 0.07, 0.025, 0.8, 1.2, -2.0, 1.5, 24.0, 4.0)


def equip_anim():
    """event_equip (1,2 s) : « plop » de l'épaulette (0 -> 1,12 -> 1, rebond amorti), puis la garniture sort une à une ;
    la fraise et la cerise tombent de 5 px et rebondissent ; les pans du ruban retombent en se balançant. Dernière image : neutre."""
    LE = 1.2

    def spring(t, d, f=1.5, z=6.0):
        if t < d:
            return 0.0
        u = t - d
        v = 1 - math.exp(-z * u) * math.cos(TAU * f * u)
        return lerp(v, 1.0, sm(t, LE - 0.2, LE))
    tr = {}
    for tag in ("l", "r"):
        tr[f"armure_{tag}"] = {"scale": lambda t: (spring(t, 0.0),) * 3}
    for i, (kind, g0, g1, s) in enumerate(GARN):
        d = 0.28 + 0.09 * i % 0.4
        if kind == "fruit":
            def fy(t, d=d):
                if t < d:
                    return (0, 5.0, 0)
                u = (t - d) / 0.22
                if u < 1:
                    return (0, 5.0 * (1 - u * u), 0)
                return (0, 0.45 * max(0.0, math.sin(math.pi * min(1.0, (t - d - 0.22) / 0.2))), 0)
            tr[g0] = {"scale": lambda t, d=d: (1.0 if t >= d else 0.0,) * 3, "position": fy}
        else:
            tr[g0] = {"scale": lambda t, d=d: (spring(t, d, 1.8, 6.5),) * 3}
    for g, s, zs, j in STRAPS:
        tr[g] = {"rotation": lambda t, s=s, zs=zs, j=j: ruban_rot(s, zs, max(0.0, 20 * (1 - sm(t, 0.2, LE)) * math.cos(TAU * 1.6 * (t - 0.1 * j))), 0)}
    return anim("event_equip", LE, tr, kps=24, loop="once", sons=((0.42, "block.honey_block.place"),))


def unequip_anim():
    LU = 0.6
    f = lambda t: (1 + 0.12 * math.sin(math.pi * min(1.0, t / 0.3))) * (1 - sm(t, 0.15, LU))
    return anim("event_unequip", LU, {f"armure_{tag}": {"scale": lambda t: (f(t),) * 3} for tag in ("l", "r")}, kps=24, loop="once")


def land_anim():
    """event_land (0,7 s) : la chantilly s'écrase puis rebondit, les pans sautent ; retour au neutre."""
    LL_ = 0.7
    env = lambda t: 1 - sm(t, 0.5, LL_)
    tr = {}
    for i, (kind, g0, g1, s) in enumerate(GARN):
        w = {"tourb": 1.0, "ros": 0.6, "fruit": 0.0}[kind]
        if w:
            tr[g0] = {"scale": lambda t, w=w: squash(1 - w * 0.2 * math.sin(TAU * 2.2 * t) * math.exp(-4.5 * t) * env(t))}
        if g1 is not None:
            tr[g1] = {"rotation": lambda t, s=s: rot_out(s, 0, -10 * math.sin(TAU * 2.2 * (t - 0.04)) * math.exp(-4.5 * t) * env(t))}
    for g, s, zs, j in STRAPS:
        tr[g] = {"rotation": lambda t, s=s, zs=zs, j=j: ruban_rot(s, zs, max(0.0, 16 * math.sin(math.pi * min(1.0, t / 0.35)) * env(t) * (1 + 0.3 * j)), 0)}
    return anim("event_land", LL_, tr, kps=20, loop="once")


ANIMS = [idle, walk, run, sneak, fall, equip_anim(), unequip_anim(), land_anim()]

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
from sons import limiter_sons
from reactions import retirer_reactions
from ambiance import ajouter_ambiance
limiter_sons(model)
retirer_reactions(model)
ajouter_ambiance(model, eclat=0.0, mouille=(0.10, 0.08, 0.04))
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(model["animations"]), "anims ;",
      sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      f"densité {DENS:.1f} texels/px ; {len(CARDS)} cartes")
