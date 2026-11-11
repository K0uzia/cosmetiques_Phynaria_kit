"""Familier chat-lanterne v4 (2026-11-08) : la v3 (géométrie et texture inchangées, translation pure de -C0 à l'écriture ;
générateur et livrable d'avant dans .build/gen_avant.py et .build/avant_livrable.bbmodel) passée en FAMILIER VIVANT
(guide 6.6), mode « vol » : lanterne céleste portée par la chaleur de sa bougie, elle ne marche jamais et ne se pose pas
sur l'épaule (fiche kawaii.md) : elle vole près de son maître. Bloc phynaria.familier {"mode": "vol", "distance": 2,
"vitesse": 1, "hauteur": 1.6} : centre de la lanterne à l'origine, à la hauteur où la v3 flottait (26,5 px ≈ 1,66 bloc).
Racine « chat_lanterne » (aucun groupe du corps) ; portée (menu Apparence, deuxième familier : q.is_pet = 0), l'overlay
la replace à gauche de la tête comme la v3. Plus de contre-rotation du torse (glide, swim et sleep couchés supprimés).
Animations : pet_idle (28 s, les 11 comportements au hasard de la v3, tirage pondéré, hoquet de flamme ; le « frotte la
joue contre la tête du joueur » devient un câlin sur place), pet_fly (même vie + lanterne qui penche selon q.ground_speed),
pet_sit (même vie, posée bas en miche de pain), pet_walk, pet_run, pet_sleep, pet_swim, pet_fall ; overlay_lanterne
(regard au hasard par saccades de la tête et des pupilles, lève le nez quand son maître vient tout près : q.owner_distance ;
pluie : se blottit, tassée ; eau : s'élève ; nuit : pupilles rondes, flamme vive ; vie basse du maître par q.owner_health :
oreilles en arrière, flamme qui brûle plus fort) ; event_equip (s'allume, « plop », seul son), event_teleport (se rallume),
event_owner_hurt (sursaut, queue en goupillon, puis la flamme flambe : il veille), event_jump, event_land. Plus d'attack,
de hurt ni d'event_unequip (pas dans la table du familier). Aucune cachette q.is_in_menu.
Pas encore dans le mod pour un familier vivant : particules emit_ (le chat n'en a pas). À juger en jeu (/cosmetique apercu) :
hauteur réelle en vol, état joué à l'arrêt en mode vol (pet_idle ou pet_fly), event_owner_hurt, variables mémorisées.

Familier chat-lanterne v2 : lanterne de papier qui est devenue un chat (objet animé, esprit d'objet), qui flotte à gauche
du joueur. Ensemble Kawaii (fiche .claude/styles/kawaii.md). Design original.
Écrit familier_kawaii_chat.png, familier_kawaii_chat_e.png et .build/familier_kawaii_chat_brut.bbmodel à côté de ce script.

Placement (types-familiers.md, arbre de décision) : ce n'est pas un chat réel mais un OBJET ANIMÉ (lanterne de papier qui a
pris une âme et la forme d'un chat) : il flotte, avec une cause visible : c'est une lanterne céleste, la bougie chauffe
l'air du papier (flamme peinte au dos et sur les côtés, ouverture lumineuse en haut). Il se balance donc comme une
lanterne : pivot au sommet de l'anse (centre de portance au-dessus du centre de masse). Il ne marche jamais : ses pattes
avant pendent ou servent aux gestes de chat ; pas de saut sur l'épaule (il vole déjà).

Refonte du 2026-11-05 (familiers.md, modelisation-organique.md, felins.md) :
  - lanterne à 12 fuseaux, côtes de bambou, cerclages ronds (12 plaques de bambou + disques découpés, plus de prismes à
    45°), anse en cordelette, pompon et bout de queue en volumes arrondis ; queue en crochet de 4 segments à sections en
    croix (plus de jumeaux à 45°) ;
  - visage : yeux d'ambre à pupille fendue qui se dilate (nuit, chasse, attaque), deux reflets, paupières de papier à cils
    (clignements irréguliers, clignement lent du « bisou de chat »), bouche en ω peinte, bouche ouverte (bâillement,
    toilette) avec langue, joues roses et moustaches peintes ; oreilles en peau + âme, intérieur rose ;
  - deux pattes avant en papier (épaule, avant-bras, patte ronde à coussinets roses), qui pendent sous le visage.
Vivant : idle de 28 s, base (flottement, balancement, bout de queue, oreilles) + 10 comportements au hasard (tranches de
7 s, q.life_time, q.instance_seed ; un tiers calmes ; la nuit, les tranches calmes deviennent des bâillements) :
  6 écoute (oreilles et tête vers un son)         11 chasse une luciole (affût, frétillement, bond, elle s'échappe)
  7 bisou de chat (se tourne, clignement lent)    12 miche de pain : pattes rentrées, queue enroulée devant
  8 toilette (lèche la patte, la passe sur la face) 13 bâille et s'étire (plus souvent la nuit)
  9 pétrit l'air en ronronnant (vibration)        14 court après sa queue (un tour)
 10 vient se frotter la joue contre la tête du joueur 15 tapote son pompon
overlay_lanterne : regarde là où le joueur regarde (avec retard), saccades des pupilles, oreilles indépendantes, bout de
queue, virages ; nuit : pupilles rondes et lanterne plus vive (ctrl_lumiere) ; pluie : oreilles plaquées, flamme qui
baisse, frissons ; vie basse : oreilles en arrière, paupières inquiètes, se rapproche ; la flamme vacille en permanence.
hurt : sursaut, queue en goupillon, oreilles plaquées ; attack : pupilles dilatées, coup de patte. event_equip (2026-11-08) : la
lanterne pliée se déplie, la bougie s'allume, il ouvre les yeux en miaulant, puis regarde son maître ; event_unequip : la flamme s'éteint, il rétrécit. event_jump, event_land : la lanterne
traîne puis rebondit (q.land_speed).
v3 (2026-11-05, amélioration des familiers) :
  - yeux enfoncés dans le papier percé (orbite à liseré prune, fond d'œil fermé ◡ derrière l'iris) : plus de pile de
    plaques qui dépasse de profil ; oreilles épaissies (0,82 px) à bout arrondi ;
  - tirage pondéré sur 30 cases (un tiers calme ; écoute et toilette fréquentes, luciole et queue rares) ;
  - comportement 16 « hoquet de flamme » : la flamme saute, il sursaute, regarde sa lanterne, second hoquet, glousse ;
  - monde : sous la pluie il se blottit contre le joueur (plus près, plus bas, tassé) ; dans l'eau, il s'élève (le papier
    craint l'eau), oreilles plaquées, flamme basse ; vie basse : la flamme brûle plus fort (il veille sur lui).
Arbitrage des 16 animations : pas de « mount » (le staff met « idle » pour la case Monture).

Fonctions avancées : trans_ et cam_ (halo de la luciole), ctrl_lumiere (flamme), overlay_, event_*, calque _e (flamme,
ouverture, iris la nuit, luciole). Un seul son (event_equip). À juger en jeu : ctrl_lumiere, variables mémorisées,
signe de q.head_y_rotation, lisibilité de la luciole.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True
NOM = "familier_kawaii_chat"
TEX = 512
TAU = 2 * math.pi
SS = 3

# ------------------------------------------------------------------ forme du corps
RH, RV = 3.2, 2.95
NLON, DLON = 12, 30.0
LATS = [-64.0, -36.0, -6.0, 30.0, 62.0]
YAW = 25.0
C0 = np.array((-13.0, 26.5, 3.0))
TH = 0.3

# ------------------------------------------------------------------ couleurs
C_PAPIER = np.array((252, 250, 244), np.float32)
C_BAS = np.array((250, 242, 226), np.float32)
C_CHAUD = np.array((255, 228, 172), np.float32)
C_OMBRE = np.array((214, 196, 172), np.float32)
C_COTE = np.array((196, 160, 108), np.float32)
C_COTE_H = np.array((230, 200, 146), np.float32)
C_FIL = np.array((216, 196, 160), np.float32)
C_ROSE = np.array((248, 156, 176), np.float32)
C_ROSE_C = np.array((250, 196, 208), np.float32)
C_TRAIT = np.array((92, 52, 64), np.float32)
C_NEZ = np.array((238, 120, 146), np.float32)
C_FLAMME = np.array((255, 200, 120), np.float32)
C_FLAMME_C = np.array((255, 244, 206), np.float32)
E_CHAUD = np.array((255, 168, 80), np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def smv(x, a, b):
    u = np.clip((x - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def V(*a):
    return np.array(a, float)


def P(phi, lat, k=1.0):
    p, l = math.radians(phi), math.radians(lat)
    return V(RH * math.cos(l) * math.sin(p), RV * math.sin(l), -RH * math.cos(l) * math.cos(p)) * k


def seg_dist(px, py, pts):
    d = np.full(px.shape, 1e9, np.float32)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        vx, vy = bx - ax, by - ay
        t = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
        d = np.minimum(d, np.hypot(px - ax - t * vx, py - ay - t * vy))
    return d


# ------------------------------------------------------------------ peinture 3D du papier
EYE_X, EYE_Y = 0.98, 0.70
EYE_W, EYE_H = 1.1, 1.18
MOUTH = [(-0.40, -0.12), (-0.30, -0.27), (-0.18, -0.30), (-0.07, -0.22), (0.0, -0.13), (0.07, -0.22), (0.18, -0.30), (0.30, -0.27), (0.40, -0.12)]
FLAMMES = (90.0, 180.0, -90.0)


def papier(p):
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    rh = np.hypot(x, z)
    phi = np.degrees(np.arctan2(x, -z))
    lat = np.degrees(np.arctan2(y / RV, rh / RH))
    rel = np.mod(phi, DLON)
    dcote = np.minimum(rel, DLON - rel)
    dc_px = np.radians(dcote) * rh
    dcentre = np.abs(rel - DLON / 2) / (DLON / 2)
    c = lerp(C_PAPIER, C_BAS, smv(-lat, -10, 50)[..., None])
    g = np.exp(-((lat + 6) / 26.0) ** 2) * (0.55 + 0.45 * np.cos(np.pi * dcentre / 2) ** 2)
    c = lerp(c, C_CHAUD, (0.30 * g)[..., None])
    c = lerp(c, C_OMBRE, (0.7 * smv(np.abs(lat), 48, 63))[..., None])
    avant = z < -0.8
    fx, fy = x, y
    zone = avant & ((np.abs(fx) / 0.62) ** 2 + ((fy - 0.25) / 1.15) ** 2 < 1)
    k_cote = (dc_px < 0.13) & ~zone
    k_bord = (dc_px >= 0.13) & (dc_px < 0.36) & ~zone
    c = lerp(c, c * 0.93, k_bord[..., None] * (1 - (dc_px - 0.13) / 0.23)[..., None])
    c = np.where(k_cote[..., None], lerp(C_COTE, C_COTE_H, np.clip(1 - dc_px / 0.07, 0, 1)[..., None]), c)
    for l0 in (-36.0, 30.0):
        dl = np.abs(lat - l0) * math.pi / 180 * RV
        c = np.where(((dl < 0.06) & ~zone & ~k_cote)[..., None], C_FIL, c)
    flam = np.zeros(x.shape, np.float32)
    flam_c = np.zeros(x.shape, np.float32)
    for f0 in FLAMMES:
        dphi = (phi - f0 + 180) % 360 - 180
        dx = np.radians(dphi) * rh
        dy = y + 0.15
        wy = 0.40 * (1 - 0.55 * np.clip(dy / 0.8, 0, 1))
        q = np.sqrt((dx / np.maximum(wy, 0.05)) ** 2 + (dy / np.where(dy > 0, 0.85, 0.42)) ** 2)
        flam = np.maximum(flam, np.exp(-(dx ** 2 + (dy * 0.8) ** 2) / 0.9))
        flam_c = np.maximum(flam_c, (q < 1).astype(np.float32))
    c = lerp(c, C_FLAMME, (0.32 * flam)[..., None])
    c = np.where(flam_c[..., None] > 0, lerp(C_FLAMME, C_FLAMME_C, 0.55), c)
    # joues, moustaches, bouche en ω, nez
    d_joue = ((np.abs(fx) - 1.72) / 0.48) ** 2 + ((fy + 0.05) / 0.30) ** 2
    joue = avant & (d_joue < 1)
    c = np.where(joue[..., None], lerp(C_ROSE, C_ROSE_C, np.clip(d_joue - 0.35, 0, 1)[..., None]), c)
    mous = np.zeros(x.shape, bool)
    for s in (-1, 1):
        for k, (dy0, dy1) in enumerate(((0.10, 0.22), (-0.06, -0.04), (-0.22, -0.32))):
            pts = [(s * 1.25, -0.05 + dy0 * 0.4), (s * 2.25, -0.05 + dy1)]
            mous |= avant & (seg_dist(fx, fy, pts) < 0.035)
    bouche = avant & (seg_dist(fx, fy, MOUTH) < 0.065)
    nez = avant & ((fx / 0.17) ** 2 + ((fy - 0.0) / 0.11) ** 2 < 1)
    c = np.where(mous[..., None], lerp(c, C_TRAIT, 0.55), c)
    c = np.where(bouche[..., None], C_TRAIT, c)
    c = np.where(nez[..., None], C_NEZ, c)
    # calque _e : la flamme (point focal) et un halo serré autour, rien de diffus ailleurs
    e = np.where(flam_c > 0, 0.85, 0.0)
    e = np.maximum(e, 0.42 * np.clip((flam - 0.55) / 0.45, 0, 1) * (1 - smv(np.abs(lat), 25, 45)))
    e = np.where(k_cote | bouche | nez | mous | joue, 0.0, e)
    ergb = E_CHAUD * e[..., None]
    ergb = np.where((flam_c > 0)[..., None], np.array((255, 196, 110), np.float32) * 0.85, ergb)
    return c, ergb


FACETS = []
for j in range(len(LATS) - 1):
    for k in range(NLON):
        p0, p1 = k * DLON, (k + 1) * DLON
        l0, l1 = LATS[j], LATS[j + 1]
        v = [P(p0, l0), P(p1, l0), P(p1, l1), P(p0, l1)]
        X = unit(v[1] - v[0])
        Y = (v[2] + v[3]) / 2 - (v[0] + v[1]) / 2
        Y = unit(Y - (Y @ X) * X)
        n = np.cross(X, Y)
        cen = sum(v) / 4
        if n @ cen < 0:
            X, n = -X, -n
        pts = [((q - cen) @ X, (q - cen) @ Y) for q in v]
        xs, ys = [a for a, _ in pts], [b for _, b in pts]
        bx, by = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        cout = cen + X * bx + Y * by
        FACETS.append(dict(name=f"pap_{j}_{k}", cout=cout, c=cout - n * TH / 2, X=X, Y=Y, n=n, w=max(xs) - min(xs) + 0.08,
                           h=max(ys) - min(ys) + 0.08, poly=[(a - bx, b - by) for a, b in pts], band=j, gore=k))


def facet_at(phi, lat):
    j = max(i for i in range(4) if LATS[i] <= lat)
    k = int(phi // DLON) % NLON
    return next(f for f in FACETS if f["band"] == j and f["gore"] == k)


# yeux enfoncés (v3, 2026-11-05) : le papier est percé (ellipse à 94 % de l'iris) et l'œil est en retrait dans le trou ;
# faces visibles, de l'avant vers l'arrière : paupière +0,11, papier 0, reflet −0,11, pupille −0,22, iris −0,33, fond −0,44.
# Vu de biais, le bord du trou cache l'iris (orbite) au lieu de laisser dépasser une pile de plaques.
EYE_HOLE = 0.94


def eye_frame(s):
    f = facet_at(15.0 if s > 0 else 345.0, 10.0)
    n = f["n"]
    x0, y0 = s * EYE_X, EYE_Y
    zf = (n @ f["cout"] - n[0] * x0 - n[1] * y0) / n[2]
    base = V(x0, y0, zf)
    Yp = unit(V(0, 1, 0) - (V(0, 1, 0) @ n) * n)
    Xp = np.cross(Yp, n)
    return f, n, base, Xp, Yp


EYE_FR = {s: eye_frame(s) for s in (-1, 1)}


# ------------------------------------------------------------------ peintres
def finish(rgb_ss, mask_ss, e_ss, W, H, semi=None):
    rgb = np.array(Image.fromarray(np.clip(rgb_ss, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    if semi is None:
        al = (np.array(Image.fromarray((mask_ss * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110) * 255
    else:
        al = np.array(Image.fromarray(np.clip(semi, 0, 254).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(int)
        al = np.where(al < 10, 0, al)
    out = np.dstack([rgb, al]).astype(np.uint8)
    if (al > 0).any():
        out[al == 0, :3] = rgb[al > 0].mean(axis=0).astype(np.uint8)
    oe = np.zeros((H, W, 4), np.uint8)
    if e_ss is not None:
        ergb = np.array(Image.fromarray(np.clip(e_ss, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
        on = (al > 0) & (ergb.max(axis=2) > 18)
        oe[on, :3] = ergb[on]
        oe[on, 3] = 255
    return out, oe


def grid(W, H, w, h):
    gx = ((np.arange(W * SS) + 0.5) / (W * SS) - 0.5) * w
    gy = (0.5 - (np.arange(H * SS) + 0.5) / (H * SS)) * h
    return np.meshgrid(gx, gy)


def poly_mask(poly, grow=0.0, rond=0.0, W=1, H=1, w=1.0):
    d = W * SS / w
    m = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(m).polygon([((a + w / 2) * d, (H * SS / 2) - b * d) for a, b in poly], fill=255)
    if grow > 0:
        m = m.filter(ImageFilter.MaxFilter(2 * max(1, int(round(grow * d))) + 1))
    if rond:
        m = Image.fromarray(((np.array(m.filter(ImageFilter.GaussianBlur(rond * d)), np.float32) > 127) * 255).astype(np.uint8))
    return np.array(m, np.float32) / 255


def paint_facet(f):
    def painter(W, H):
        px, py = grid(W, H, f["w"], f["h"])
        pts = f["cout"][None, None, :] + f["X"][None, None, :] * px[..., None] + f["Y"][None, None, :] * py[..., None]
        rgb, e = papier(pts)
        m = poly_mask(f["poly"], grow=0.03, W=W, H=H, w=f["w"])
        for s, (fe, n, base, Xp, Yp) in EYE_FR.items():
            if fe is not f:
                continue
            ex, ey = (pts - base) @ Xp, (pts - base) @ Yp
            q = oeil_masque(ex / EYE_HOLE, ey / EYE_HOLE)
            m = m * (q >= 1)
            # bord de l'orbite : papier un peu ombré, liseré prune fin (lit l'œil comme enfoncé)
            rgb = lerp(rgb, lerp(rgb, C_OMBRE, 0.45), smv(-q, -1.45, -1.0)[..., None])
            rgb = np.where(((q >= 1) & (q < 1.35))[..., None], lerp(rgb, C_TRAIT, 0.6), rgb)
            e = np.where((q < 1.5)[..., None], 0, e)
        return finish(rgb, m, e, W, H)
    return painter


def oeil_masque(px, py):
    """Œil en amande arrondie, coin externe un peu relevé (vers les oreilles)."""
    return (px / (EYE_W / 2)) ** 2 + ((py - 0.08 * px * np.sign(px + 1e-9) * 0) / (EYE_H / 2)) ** 2


def paint_iris(W, H):
    px, py = grid(W, H, EYE_W, EYE_H)
    q = oeil_masque(px, py)
    t = np.clip((EYE_H / 2 - py) / EYE_H, 0, 1)
    c = lerp(np.array((150, 92, 36), np.float32), np.array((255, 196, 92), np.float32), (t ** 1.2)[..., None])     # ombre de la paupière en haut
    c = lerp(c, np.array((255, 226, 150), np.float32), (smv(-py, 0.15, 0.5) * 0.6)[..., None])
    c = lerp(c, np.array((92, 52, 40), np.float32), smv(q, 0.8, 1.0)[..., None])                                    # cerne
    e = np.zeros_like(c)
    e[...] = (120, 70, 20)
    e = e * smv(-q, -0.85, -0.2)[..., None]
    return finish(c, q < 1, e, W, H)


PUP_W, PUP_H = 0.62, 0.98


def paint_pupille(W, H):
    px, py = grid(W, H, PUP_W, PUP_H)
    q = np.hypot(px / (PUP_W / 2), py / (PUP_H / 2))
    c = np.zeros(px.shape + (3,), np.float32)
    c[...] = (40, 24, 34)
    return finish(c, q < 1, None, W, H)


def paint_reflet(W, H):
    px, py = grid(W, H, EYE_W, EYE_H)
    h1 = ((px + 0.2) / 0.17) ** 2 + ((py - 0.24) / 0.19) ** 2 < 1
    h2 = ((px - 0.22) / 0.085) ** 2 + ((py + 0.24) / 0.085) ** 2 < 1
    c = np.full(px.shape + (3,), 255, np.float32)
    e = np.zeros_like(c)
    e[h1] = (190, 186, 176)
    return finish(c, h1 | h2, e, W, H)


def paint_paupiere(side):
    """Paupière de papier : couleur du papier devant l'œil (repère du visage), cils prune au bord bas."""
    f = facet_at(15.0 if side > 0 else 345.0, 10.0)

    def painter(W, H):
        px, py = grid(W, H, EYE_W * 1.08, EYE_H * 1.08)
        q = oeil_masque(px / 1.08, py / 1.08)
        pts = np.stack([side * EYE_X + px, EYE_Y + py, np.full(px.shape, -2.9)], -1)
        c, _ = papier(pts)
        cils = (q > 0.72) & (py < 0.15 * EYE_H)
        c = np.where(cils[..., None], C_TRAIT, c)
        return finish(c, q < 1, None, W, H)
    return painter


def paint_fond_oeil(side):
    """Fond de l'orbite, derrière l'iris : papier ombré et trait d'œil fermé (◡). Visible seulement quand l'œil se plisse
    (clignement, yeux fermés de bonheur) : le trou ne montre jamais l'intérieur de la lanterne."""
    def painter(W, H):
        px, py = grid(W, H, EYE_W * 1.1, EYE_H * 1.1)
        pts = np.stack([side * EYE_X + px, EYE_Y + py, np.full(px.shape, -2.9)], -1)
        c, _ = papier(pts)
        q = oeil_masque(px, py)
        c = lerp(c, C_OMBRE, (0.25 + 0.2 * smv(q, 0.3, 1.0))[..., None])
        arc = np.abs(py - 0.1 + 0.22 * (1 - (px / (EYE_W * 0.42)) ** 2)) < 0.055
        arc &= np.abs(px) < EYE_W * 0.42
        c = np.where(arc[..., None], C_TRAIT, c)
        return finish(c, np.ones(px.shape, np.float32), None, W, H)
    return painter


MO_W, MO_H = 1.0, 0.78


def paint_bouche_o(W, H):
    px, py = grid(W, H, MO_W, MO_H)
    pts = np.stack([px, py - 0.18, np.full(px.shape, -3.0)], -1)
    c, _ = papier(pts)
    fond = np.hypot(px / 0.5, py / 0.39) < 1
    m = np.hypot(px / 0.27, (py + 0.02) / 0.31) < 1
    c = np.where(m[..., None], np.array((120, 50, 70), np.float32), c)
    lang = m & (np.hypot(px / 0.17, (py + 0.2) / 0.12) < 1)
    c = np.where(lang[..., None], np.array((250, 140, 168), np.float32), c)
    c = np.where((np.abs(np.hypot(px / 0.27, (py + 0.02) / 0.31) - 1) < 0.12)[..., None], C_TRAIT, c)
    c = np.where(((px / 0.17) ** 2 + ((py - 0.18) / 0.11) ** 2 < 1)[..., None], C_NEZ, c)
    return finish(c, fond, None, W, H)


EAR_W, EAR_H, EAR_Y0 = 1.8, 2.0, -0.4
EAR_POLY = [(-0.9, -0.4), (0.9, -0.4), (0.24, 1.5), (-0.24, 1.5)]   # bout arrondi (v3 : plus de pointe)


def paint_ear(face):
    def painter(W, H):
        px, py = grid(W, H, EAR_W, EAR_H)
        py = py + (EAR_Y0 + EAR_H / 2)
        poly = [(a, b - (EAR_Y0 + EAR_H / 2)) for a, b in EAR_POLY]
        m = poly_mask(poly, rond=0.32, W=W, H=H, w=EAR_W)
        bord = 1 - np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.09 * W * SS / EAR_W)), np.float32) / 255
        c = np.zeros(px.shape + (3,), np.float32)
        c[...] = C_PAPIER
        c = lerp(c, C_BAS, smv(-py, -1.4, 0.2)[..., None] * 0.6)
        if face:
            inner = poly_mask([(-0.55, -0.1), (0.55, -0.1), (0.07, 1.12), (-0.07, 1.12)], rond=0.18, W=W, H=H, w=EAR_W)
            c = lerp(c, C_ROSE_C, inner[..., None])
            c = lerp(c, C_ROSE, (inner * smv(-py, -0.9, 0.1))[..., None] * 0.7)
        c = lerp(c, C_COTE, np.clip(bord * 3.0, 0, 1)[..., None] * (m[..., None] > 0))
        c = lerp(c, C_OMBRE, smv(-py, -0.25, 0.25)[..., None] * 0.8)
        return finish(c, m, None, W, H)
    return painter


def strip(W, H, fn):
    u, v = np.meshgrid((np.arange(W * SS) + 0.5) / (W * SS), (np.arange(H * SS) + 0.5) / (H * SS))
    c, e = fn(u, v)
    return finish(c, np.ones(u.shape, np.float32), e, W, H)


def bois(u, v):
    q = np.abs(v - 0.5) * 2
    c = lerp(np.array((238, 210, 150), np.float32), np.array((200, 160, 102), np.float32), (q ** 1.6)[..., None])
    c = c * (1 + 0.04 * np.sin(u * 40 + np.sin(u * 9) * 2))[..., None]
    c = np.where((np.abs(v - 0.5) < 0.09)[..., None], np.array((246, 160, 178), np.float32), c)
    return c, None


def disque_bois(ouvert):
    def painter(W, H):
        px, py = grid(W, H, 1.0, 1.0)
        r = np.hypot(px, py) * 2
        m = r < 0.99
        c = lerp(np.array((240, 212, 154), np.float32), np.array((204, 164, 106), np.float32), smv(r, 0.45, 1.0)[..., None])
        c = c * (1 + 0.04 * np.sin(r * 40))[..., None]
        e = None
        if ouvert:
            c = np.where((r < 0.5)[..., None], np.array((126, 86, 52), np.float32), c)
            c = np.where((r < 0.4)[..., None], np.array((255, 222, 160), np.float32), c)
            e = np.where((r < 0.4)[..., None], np.array((255, 190, 110), np.float32) * 0.7, 0 * c)
        return finish(c, m, e, W, H)
    return painter


def cordon(u, v):
    q = np.abs(v - 0.5) * 2
    c = lerp(np.array((250, 176, 194), np.float32), np.array((210, 110, 138), np.float32), (q ** 1.4)[..., None])
    c = c * (1 - 0.10 * (np.sin((u * 14 + v * 1.2) * TAU) > 0.4))[..., None]
    return c, None


def queue_bande(u, v):
    q = np.abs(v - 0.5) * 2
    c = lerp(C_PAPIER, np.array((226, 210, 186), np.float32), (q ** 1.5)[..., None])
    c = lerp(c, C_ROSE_C, smv(u, 0.80, 0.9)[..., None])
    return c, None


def ame(u, v):
    c = np.zeros(u.shape + (3,), np.float32)
    c[...] = (255, 214, 146)
    return c, E_CHAUD * 0.3 + 0 * c


def uni(rgb):
    return lambda u, v: (np.array(rgb, np.float32) + 0 * u[..., None], None)


# luciole : halo translucide (trans_, face caméra) + noyau opaque lumineux
def paint_halo(W, H):
    px, py = grid(W, H, 1.0, 1.0)
    r = np.hypot(px, py) * 2
    c = lerp(np.array((250, 255, 200), np.float32), np.array((200, 240, 120), np.float32), np.clip(r, 0, 1)[..., None])
    a = 200 * np.clip(1 - r, 0, 1) ** 1.6
    e = c * 0.6 * np.clip(1 - r * 1.3, 0, 1)[..., None]
    return finish(c, r < 1, e, W, H, semi=a)


# ------------------------------------------------------------------ boîtes peintes en espace monde (pattes, pompon)
def peint_papier_patte(P, n):
    """Papier des pattes : blanc, plus sombre dessous, coussinets roses sous la patte, doigts marqués."""
    c = np.zeros(P.shape[:-1] + (3,), np.float32)
    c[...] = C_PAPIER
    lum = 0.5 + 0.5 * (n @ unit(V(-0.3, 1.0, -0.6)))
    c = lerp(C_OMBRE, c, (0.35 + 0.65 * lum)[..., None])
    c = lerp(c, C_OMBRE, smv(P[..., 1], -0.25, 0.1)[..., None] * 0.5)
    return c


TILES = {}


def tile(name, w, h, painter, fixed=False):
    TILES[name] = (w, h, painter, fixed)


BOXES = []        # (groupe, nom, centre, demi-tailles, fonction couleur(P, n) -> rgb, nom de base des tuiles)
FACE_AX = {"north": (0, 1, -1, 2), "south": (0, 1, 1, 2), "east": (2, 1, 1, 0), "west": (2, 1, -1, 0), "up": (0, 2, 1, 1), "down": (0, 2, -1, 1)}


def face_points(c, h, f, W, H):
    """Points 3D (repère local de la lanterne) des texels d'une face de boîte, dans l'ordre des UV du renderer."""
    u, v = np.meshgrid((np.arange(W * SS) + 0.5) / (W * SS), (np.arange(H * SS) + 0.5) / (H * SS))
    a, b = c - h, c + h
    P = np.zeros(u.shape + (3,))
    nrm = np.zeros(3)
    if f == "north":
        P[..., 0], P[..., 1], P[..., 2] = b[0] - u * 2 * h[0], b[1] - v * 2 * h[1], a[2]; nrm[2] = -1
    elif f == "south":
        P[..., 0], P[..., 1], P[..., 2] = a[0] + u * 2 * h[0], b[1] - v * 2 * h[1], b[2]; nrm[2] = 1
    elif f == "east":
        P[..., 2], P[..., 1], P[..., 0] = b[2] - u * 2 * h[2], b[1] - v * 2 * h[1], b[0]; nrm[0] = 1
    elif f == "west":
        P[..., 2], P[..., 1], P[..., 0] = a[2] + u * 2 * h[2], b[1] - v * 2 * h[1], a[0]; nrm[0] = -1
    elif f == "up":
        P[..., 0], P[..., 2], P[..., 1] = a[0] + u * 2 * h[0], a[2] + v * 2 * h[2], b[1]; nrm[1] = 1
    else:
        P[..., 0], P[..., 2], P[..., 1] = a[0] + u * 2 * h[0], b[2] - v * 2 * h[2], a[1]; nrm[1] = -1
    return P, nrm


DIMS = {"north": (0, 1), "south": (0, 1), "east": (2, 1), "west": (2, 1), "up": (0, 2), "down": (0, 2)}


def boite(g, name, c, h, fn, faces=("north", "south", "east", "west", "up", "down")):
    c, h = np.asarray(c, float), np.asarray(h, float)
    BOXES.append((g, name, c, h, faces))
    for f in faces:
        i, j = DIMS[f]

        def painter(W, H, f=f):
            Pp, nrm = face_points(c, h, f, W, H)
            col = fn(Pp, np.broadcast_to(nrm, Pp.shape))
            return finish(col, np.ones(Pp.shape[:2]), None, W, H)
        tile(f"{name}_{f}", 2 * h[i], 2 * h[j], painter)


# patte avant : épaule (dans le papier), avant-bras, patte ronde ; sections en croix ; repère local de la lanterne
PATTE_ATT = {s: V(s * 0.78, -1.75, -2.35) for s in (-1, 1)}


def couleur_patte(s):
    def fn(Pp, n):
        c = peint_papier_patte(Pp - PATTE_ATT[s], n)
        # coussinets : dessous de la patte (n.y < 0) près du bout
        loc = Pp - PATTE_ATT[s]
        pad = (n[..., 1] < -0.5) & (np.hypot((loc[..., 0]) / 0.2, (loc[..., 2] + 0.06) / 0.17) < 1)
        c = np.where(pad[..., None], C_ROSE, c)
        for dx in (-0.18, 0.0, 0.18):
            toe = (n[..., 1] < -0.5) & (np.hypot((loc[..., 0] - dx) / 0.07, (loc[..., 2] + 0.36) / 0.06) < 1)
            c = np.where(toe[..., None], C_ROSE, c)
        fente = (n[..., 2] < -0.5) & (np.abs(np.abs(loc[..., 0]) - 0.12) < 0.022) & (loc[..., 1] < -0.85)
        c = np.where(fente[..., None], lerp(c, C_TRAIT, 0.55), c)
        return c
    return fn


def boule_croix(g, name, c, r, fn, k=0.62, ry=1.0):
    """Petite boule : trois boîtes en croix alignées (section arrondie par paliers) ; sur chaque axe, trois demi-tailles
    distinctes (1, 0,78, 0,56 du rayon) : aucune face parallèle à moins de 0,1 px d'une autre (dès r ≥ 0,45)."""
    a, b = 0.78, 0.56
    boite(g, f"{name}_x", c, V(r, r * a * ry, r * b), fn)
    boite(g, f"{name}_y", c, V(r * b, r * ry, r * a), fn)
    boite(g, f"{name}_z", c, V(r * a, r * b * ry, r), fn)


for s, tag in ((-1, "l"), (1, "r")):
    A = PATTE_ATT[s]
    fn = couleur_patte(s)
    boite(f"bras_{tag}", f"bras_{tag}_a", A + V(0, -0.3, -0.12), V(0.2, 0.42, 0.2), fn, faces=("north", "east", "west", "south"))
    boule_croix(f"bras_{tag}", f"patte_{tag}", A + V(0, -0.86, -0.12), 0.55, fn, ry=0.86)


def couleur_pompon(c0, c1, ctr):
    def fn(Pp, n):
        d = np.linalg.norm(Pp - ctr, axis=-1)
        c = lerp(np.array(c0, np.float32), np.array(c1, np.float32), np.clip(d / 0.7, 0, 1)[..., None])
        c = c * (1 + 0.06 * np.sin(Pp[..., 0] * 50 + Pp[..., 1] * 37 + Pp[..., 2] * 41))[..., None]
        return lerp(c, c * 1.08, np.clip(n[..., 1], 0, 1)[..., None])
    return fn


Y_TOP = RV * math.sin(math.radians(64))
POMPON_C = V(0, -Y_TOP - 1.6, 0)
QUEUE_BOUT = None   # défini après la queue


boule_croix("pompon", "pompon", POMPON_C, 0.55, couleur_pompon((255, 200, 214), (232, 124, 154), POMPON_C))
Y_ANSE = 4.3
PERLE_C = V(0, Y_ANSE, 0)
boule_croix("lanterne", "perle", PERLE_C, 0.47, couleur_pompon((255, 216, 226), (222, 110, 140), PERLE_C))

# queue : 4 segments en crochet (dos +Z, remonte, se recourbe vers l'avant), sections en croix ; bout rose duveteux
Q0 = V(0, -1.2, 2.5)
NQ, LQ = 4, 3.6
QP = [Q0]
for i in range(NQ):
    s_ = (i + 0.5) / NQ
    a = math.radians(-14 + 178 * s_ ** 1.35)
    QP.append(QP[-1] + V(0, math.sin(a), math.cos(a)) * (LQ / NQ))
QUEUE_BOUT = QP[-1] + unit(QP[-1] - QP[-2]) * 0.15
boule_croix("queue4", "queue_bout", QUEUE_BOUT, 0.47, couleur_pompon((252, 204, 218), (236, 138, 164), QUEUE_BOUT))

for f in FACETS:
    tile(f["name"], f["w"], f["h"], paint_facet(f))
tile("iris", EYE_W, EYE_H, paint_iris)
tile("pupille", PUP_W, PUP_H, paint_pupille)
tile("reflet", EYE_W, EYE_H, paint_reflet)
tile("paup_l", EYE_W * 1.08, EYE_H * 1.08, paint_paupiere(-1))
tile("paup_r", EYE_W * 1.08, EYE_H * 1.08, paint_paupiere(1))
tile("bouche_o", MO_W, MO_H, paint_bouche_o)
tile("fond_l", EYE_W * 1.1, EYE_H * 1.1, paint_fond_oeil(-1))
tile("fond_r", EYE_W * 1.1, EYE_H * 1.1, paint_fond_oeil(1))
tile("oreille_av", EAR_W, EAR_H, paint_ear(True))
tile("oreille_ar", EAR_W, EAR_H, paint_ear(False))
tile("bois", 64, 18, lambda W, H: strip(W, H, bois), fixed=True)
tile("disque_h", 48, 48, disque_bois(True), fixed=True)
tile("disque_b", 48, 48, disque_bois(False), fixed=True)
tile("cordon", 48, 10, lambda W, H: strip(W, H, cordon), fixed=True)
tile("queue", 96, 16, lambda W, H: strip(W, H, queue_bande), fixed=True)
tile("ame", 16, 16, lambda W, H: strip(W, H, ame), fixed=True)
tile("oreille_ame", 12, 12, lambda W, H: strip(W, H, uni(lerp(C_BAS, C_OMBRE, 0.35))), fixed=True)
tile("halo", 40, 40, paint_halo, fixed=True)
tile("noyau", 8, 8, lambda W, H: finish(np.full((H * SS, W * SS, 3), (250, 255, 190), np.float32), np.ones((H * SS, W * SS)),
                                         np.full((H * SS, W * SS, 3), (220, 235, 120), np.float32), W, H), fixed=True)

UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def atlas():
    def pack(dens):
        items = []
        for n, (w, h, _, fx) in TILES.items():
            items.append((n, w, h) if fx else (n, max(2, int(math.ceil(w * dens))), max(2, int(math.ceil(h * dens)))))
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

    dens = 48.0
    while (uv := pack(dens)) is None:
        dens -= 0.25
    UV.update(uv)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, (w, h, painter, fx) in TILES.items():
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1], tex_e[v0:v1, u0:u1] = painter(u1 - u0, v1 - v0)
    assert tex[TEX - 3, TEX - 3, 3] == 0
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    ok = np.zeros(semi.shape, bool)
    u0, v0, u1, v1 = UV["halo"]
    ok[v0:v1, u0:u1] = True
    assert not (semi & ~ok).any(), "semi-transparence hors trans_"
    b64 = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        b64.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return dens, b64


DENS, (tex_b64, tex_e_b64) = atlas()

# ------------------------------------------------------------------ cubes et groupes
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def rot_matrix(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def euler(R):
    sy = -R[2, 0]
    if abs(sy) > 0.99999:
        ry = math.copysign(math.pi / 2, sy)
        ang = (math.degrees(math.atan2(R[0, 1], R[0, 2])) if sy > 0 else math.degrees(math.atan2(-R[0, 1], -R[0, 2]))), math.degrees(ry), 0.0
    else:
        ang = math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(math.asin(sy)), math.degrees(math.atan2(R[1, 0], R[0, 0]))
    assert np.allclose(rot_matrix(*ang), R, atol=1e-4), "euler"
    return ang


def group(name, origin, parent=None, rotation=(0, 0, 0), nm=None):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(float(v), 2) for v in rotation], "name": nm or name}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def L(p):
    return C0 + np.asarray(p, float)


def plate(g, name, c, X, Y, tilename, w, h, th=TH, side="s"):
    X = unit(X)
    Y = unit(np.asarray(Y, float) - (np.asarray(Y, float) @ X) * X)
    u0, v0, u1, v1 = UV[tilename]
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = L(c)
    south = [u0, v0, u1, v1] if side in "sb" else CLEAR
    north = [u1, v0, u0, v1] if side in "nb" else CLEAR
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": south, "north": north, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def frame_from_axis(X):
    ref = V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0)
    Y = unit(ref - (ref @ X) * X)
    return Y, np.cross(X, Y)


def bar(g, name, p, q, r, tilename, u0=0.0, u1=1.0, croix=True, ov=0.08, roll=0.0):
    """Tronçon le long de p→q : section en croix alignée (deux boîtes, chanfrein 28 %) ou losange seul (cordelette)."""
    p, q = L(p), L(q)
    Ln = np.linalg.norm(q - p)
    X = unit(q - p)
    Y, Z_ = frame_from_axis(X)
    if roll:
        cr_, sr_ = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        Y, Z_ = cr_ * Y + sr_ * Z_, -sr_ * Y + cr_ * Z_
    bu0, bv0, bu1, bv1 = UV[tilename]
    ua = lerp(bu0, bu1, u0)
    ub = max(lerp(bu0, bu1, u1), ua + 2)
    lg = [ua, bv0, ub, bv1]
    mid = (bv0 + bv1) / 2
    end = [ub - 2, mid - 2, ub, mid + 2]
    faces = {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}
    if croix:
        R0 = np.column_stack([X, Y, Z_])
        cube(g, name, p + (-ov, -r, -r * 0.58), p + (Ln + ov, r, r * 0.58), p, euler(R0), faces)
        cube(g, name + "c", p + (-ov + 0.12, -r * 0.58, -r), p + (Ln + ov - 0.12, r * 0.58, r), p, euler(R0), faces)
    else:
        c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
        R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
        cube(g, name, p + (-ov, -r, -r), p + (Ln + ov, r, r), p, euler(R45), faces)


def prisme(g, name, y0, y1, a):
    s = UV["ame"]
    for i, (k, ang) in enumerate(((1.0, 0.0), (0.97, 45.0))):
        d = 0.12 * i
        c = L(V(0, (y0 + y1) / 2, 0))
        cube(g, f"{name}{'o' if i else ''}", L(V(-a * k, y0 + d, -a * k)), L(V(a * k, y1 - d, a * k)), c, (0, ang, 0), {f: list(s) for f in ("north", "south", "east", "west", "up", "down")})


def bone_node(name):
    g = groups[name]
    return {"name": g["name"], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


group("chat_lanterne", C0)                  # racine du familier vivant (origine du modèle après décalage de -C0)
group("fam_elan", C0, "chat_lanterne")
group("fam_reac", C0, "fam_elan")
group("fam_pos", C0, "fam_reac")
group("fam_cr", C0, "fam_pos")
group("fam_comp", C0, "fam_cr")
group("fam_comp2", C0, "fam_comp")
group("fam_swing", L(V(0, Y_ANSE, 0)), "fam_comp2")
group("fam_snap", C0, "fam_swing")
group("fam_sq", L(V(0, -RV, 0)), "fam_snap")
group("lanterne", C0, "fam_sq", rotation=(0, YAW, 0))
group("ctrl_lumiere#l", C0, "lanterne", nm="ctrl_lumiere")

for f in FACETS:
    plate("lanterne", f["name"], f["c"], f["X"], f["Y"], f["name"], f["w"], f["h"])


def ame_max(y0, y1, marge=0.06):
    def ok(a):
        for ang in (0.0, 45.0):
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            for sx in (-a, a):
                for sz in (-a, a):
                    for yy in (y0, y1):
                        q = V(sx * ca + sz * sa, yy, -sx * sa + sz * ca)
                        if max(f["n"] @ q - f["n"] @ f["cout"] for f in FACETS) > -marge:
                            return False
        return True
    a = 0.2
    while ok(a + 0.02):
        a += 0.02
    return a


prisme("lanterne", "ame_m", -0.9, 0.9, ame_max(-0.9, 0.9, 0.62))
prisme("lanterne", "ame_h", 1.02, 1.9, ame_max(1.02, 1.9, 0.62))
prisme("lanterne", "ame_b", -1.9, -1.02, ame_max(-1.9, -1.02, 0.4))

# cerclages ronds : 12 plaques de bambou + disque découpé (ouverture lumineuse en haut)
R_RING = 1.68
for tag, y0, y1, disk_y, disk in (("h", Y_TOP - 0.3, Y_TOP + 0.42, Y_TOP + 0.42, "disque_h"), ("b", -Y_TOP - 0.42, -Y_TOP + 0.3, -Y_TOP - 0.42, "disque_b")):
    wd = 2 * R_RING * math.tan(math.radians(15)) + 0.03
    for k in range(12):
        a = math.radians(k * 30 + 15)
        n = V(math.sin(a), 0, -math.cos(a))
        X = V(math.cos(a), 0, math.sin(a))
        plate("lanterne", f"cercle_{tag}{k}", n * (R_RING - 0.15) + V(0, (y0 + y1) / 2, 0), X, V(0, 1, 0), "bois", wd, y1 - y0, side="s")
    rd = R_RING / math.cos(math.radians(15)) + 0.02
    sgn = 1 if tag == "h" else -1
    plate("lanterne", f"disque_{tag}", V(0, disk_y - sgn * 0.15, 0), V(1, 0, 0), V(0, 0, -sgn), disk, 2 * rd, 2 * rd, side="s")

ANSE = [V(-0.8, Y_TOP + 0.42, 0), V(-0.6, Y_TOP + 1.2, 0), V(0, Y_ANSE - 0.05, 0), V(0.6, Y_TOP + 1.2, 0), V(0.8, Y_TOP + 0.42, 0)]
for i in range(4):
    bar("lanterne", f"anse{i}", ANSE[i], ANSE[i + 1], 0.16, "cordon", i / 4, (i + 1) / 4, croix=False, ov=0.06)

# yeux : iris, pupille (échelle x : fente / ronde), reflets, paupière (échelle y, pivot en haut), parallèles à la facette
EYES, PUPS, LIDS = {}, {}, {}
for s, tag in ((-1, "l"), (1, "r")):
    f, n, base, Xp, Yp = EYE_FR[s]
    plate("lanterne", f"fond_{tag}", base + n * (-0.44 - TH / 2), Xp, Yp, f"fond_{tag}", EYE_W * 1.1, EYE_H * 1.1)
    EYES[tag] = group(f"oeil_{tag}", L(base - n * 0.2), "lanterne")
    plate(EYES[tag], f"iris_{tag}", base + n * (-0.33 - TH / 2), Xp, Yp, "iris", EYE_W, EYE_H)
    PUPS[tag] = group(f"pupille_{tag}", L(base - n * 0.22), EYES[tag])
    plate(PUPS[tag], f"pupille_{tag}", base + n * (-0.22 - TH / 2) + Yp * 0.02, Xp, Yp, "pupille", PUP_W, PUP_H)
    plate(EYES[tag], f"reflet_{tag}", base + n * (-0.11 - TH / 2), Xp, Yp, "reflet", EYE_W, EYE_H)
    LIDS[tag] = group(f"paup_{tag}", L(base + n * 0.11 + Yp * (EYE_H * 0.54)), EYES[tag])
    plate(LIDS[tag], f"paup_{tag}", base + n * (0.11 - TH / 2), Xp, Yp, f"paup_{tag}", EYE_W * 1.08, EYE_H * 1.08)

# bouche ouverte (bâillement, toilette), parallèle à la facette du bas du visage, cachée par l'échelle hors usage
fa, fb = facet_at(0.5, -5.0), facet_at(359.5, -5.0)
nb_ = unit(fa["n"] + fb["n"])
zb = (fa["n"] @ fa["cout"] - fa["n"][1] * (-0.18)) / fa["n"][2]
BO = V(0, -0.18, zb)
Ypb = unit(V(0, 1, 0) - (V(0, 1, 0) @ nb_) * nb_)
group("bouche_o", L(BO + Ypb * 0.18), "lanterne")
plate("bouche_o", "bouche_o", BO + nb_ * (0.11 - TH / 2), np.cross(Ypb, nb_), Ypb, "bouche_o", MO_W, MO_H)

# oreilles
EARS = {}
for s, tag in ((-1, "l"), (1, "r")):
    b = P(s * 40.0, 50.0, 0.93)
    Yu = unit(V(s * 0.55, 1.0, 0.12))
    n0 = unit(V(s * 0.42, 0.0, -1.0))
    Xe = unit(np.cross(Yu, n0))
    ne = np.cross(Xe, Yu)
    EARS[tag] = group(f"oreille_{tag}", L(b), "lanterne")
    cy = EAR_Y0 + EAR_H / 2
    plate(EARS[tag], f"oreille_{tag}_av", b + Yu * cy + ne * 0.26, Xe, Yu, "oreille_av", EAR_W, EAR_H, side="s")
    plate(EARS[tag], f"oreille_{tag}_ar", b + Yu * cy - ne * 0.26, Xe, Yu, "oreille_ar", EAR_W, EAR_H, side="n")
    R_ = np.column_stack([Xe, Yu, ne])
    for i, (wc, y0c, y1c) in enumerate(((0.86, -0.3, 0.62), (0.40, 0.62, 1.06))):
        cc = b + Yu * ((y0c + y1c) / 2)
        hw, hh = wc / 2, (y1c - y0c) / 2
        fz = {f_: list(UV["oreille_ame"]) for f_ in ("north", "south", "east", "west", "up", "down")}
        fz["up" if i == 0 else "down"] = CLEAR          # jointure des deux âmes : faces coplanaires transparentes
        cube(EARS[tag], f"oreille_{tag}_ame{i}", L(cc) - (hw, hh, 0.2), L(cc) + (hw, hh, 0.2), L(cc), euler(R_), fz)

# queue
QG = ["queue1", "queue2", "queue3", "queue4"]
par = "lanterne"
for i, gq in enumerate(QG):
    group(gq, L(QP[i]), par)
    par = gq
for i in range(NQ):
    bar(QG[i], f"queue_s{i}", QP[i], QP[i + 1], lerp(0.38, 0.28, i / (NQ - 1)), "queue", i / NQ, (i + 1) / NQ, croix=True, ov=0.12, roll=(5 if i % 2 else -5))

# pompon
group("pompon", L(V(0, -Y_TOP - 0.42, 0)), "lanterne")
bar("pompon", "pompon_fil", V(0, -Y_TOP - 0.3, 0), V(0, -Y_TOP - 1.35, 0), 0.15, "cordon", 0.0, 0.5, croix=False)

# pattes avant
for s, tag in ((-1, "l"), (1, "r")):
    group(f"bras_{tag}", L(PATTE_ATT[s]), "lanterne")

# luciole (chassée au comportement 11) : hors de la lanterne, cachée par l'échelle hors usage
LUC0 = V(-3.6, 1.2, -3.2)
group("luciole", L(LUC0), "fam_pos")
group("cam_luciole", L(LUC0), "luciole")
group("trans_luciole", L(LUC0), "cam_luciole")
plate("trans_luciole", "halo", LUC0, V(1, 0, 0), V(0, 1, 0), "halo", 1.8, 1.8, side="s")
u0, v0, u1, v1 = UV["noyau"]
cube("luciole", "noyau", L(LUC0 - 0.3), L(LUC0 + 0.3), L(LUC0), (0, 0, 0), {f_: [u0, v0, u1, v1] for f_ in ("north", "south", "east", "west", "up", "down")})

# boîtes peintes
for g, name, c, h, faces in BOXES:
    fs = {f: (list(UV[f"{name}_{f}"]) if f in faces else CLEAR) for f in ("north", "south", "east", "west", "up", "down")}
    cube(g, name, L(c - h), L(c + h), L(c), (0, 0, 0), fs)


# ------------------------------------------------------------------ animations
# Guide, section 3 : +X = le haut part vers l'arrière ; +Y = le côté droit (+X) avance ; +Z = le côté droit monte.
# Le chat est à gauche du joueur (−X) : son visage (−Z) se tourne vers le joueur (+X) par une rotation −Y.
def fmt(v):
    return v if isinstance(v, str) else str(round(float(v) + 0.0, 4))


def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": fmt(v[0]), "y": fmt(v[1]), "z": fmt(v[2])}], "time": round(t, 3), "interpolation": "linear"}


def anim(name, length, tracks=None, n_kf=None, loop="loop", molang=None):
    A = {}
    if tracks:
        n = n_kf or max(8, int(round(length * 10)))
        times = [i * length / n for i in range(n + 1)]
        for g, chans in tracks.items():
            A.setdefault(groups[g]["uuid"], {"name": groups[g]["name"], "type": "bone", "keyframes": []})["keyframes"] += \
                [kf(ch, t, f(t)) for ch, f in chans.items() for t in times]
    for g, chans in (molang or {}).items():
        A.setdefault(groups[g]["uuid"], {"name": groups[g]["name"], "type": "bone", "keyframes": []})["keyframes"] += \
            [kf(ch, 0.0, v) for ch, v in chans.items()]
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "pet_idle", "animators": A}


def S(T, k, ph=0.0):
    return lambda t: math.sin(TAU * k * t / T + ph)


def ear_rot(side, tx, tz):
    """Intention écrite pour l'oreille droite (+X) : tz > 0 = la pointe part vers l'extérieur."""
    return (tx, 0.0, -side * tz)


def flick(t, a, amp=1.0):
    return amp * (bump(t, a, a + 0.07, a + 0.12, a + 0.22) - 0.35 * bump(t, a + 0.18, a + 0.24, a + 0.26, a + 0.36))


def clin(t, *ts, dur=0.22):
    v = 1.0
    for a in ts:
        v -= 0.95 * bump(t, a, a + dur * 0.35, a + dur * 0.5, a + dur)
    return v


PUP_JOUR = 0.42


def etat(name, T, pos, swing, regard=None, ears=None, oeil=None, paup=None, tail=None, pompon=None, bras=None, cr=None, pup=None, n_kf=None):
    tr = {"fam_pos": {"position": pos}, "fam_swing": {"rotation": swing}, "bouche_o": {"scale": lambda t: (0.001,) * 3},
          "luciole": {"scale": lambda t: (0.001,) * 3}}
    if cr:
        tr["fam_cr"] = {"rotation": cr}
    if regard:
        tr["lanterne"] = {"rotation": regard}
    if ears:
        tr[EARS["l"]] = {"rotation": lambda t: ear_rot(-1, *ears(t, -1))}
        tr[EARS["r"]] = {"rotation": lambda t: ear_rot(1, *ears(t, 1))}
    for tag in ("l", "r"):
        tr[EYES[tag]] = {"scale": (lambda t: (1, oeil(t) if oeil else 1, 1))}
        tr[LIDS[tag]] = {"scale": (lambda t: (1, paup(t) if paup else 0.0, 1))}
        tr[PUPS[tag]] = {"scale": (lambda t: (pup(t) if pup else PUP_JOUR, 1, 1))}
    if tail:
        base, amp_y, amp_x, cyc, lag = tail
        for i, g in enumerate(QG):
            def f(t, i=i):
                ph = TAU * (cyc * t / T - lag * i)
                w = (0.6, 0.85, 1.05, 1.25)[i]
                return (base[i] + amp_x * w * math.sin(ph + 1.2), amp_y * w * math.sin(ph), 0)
            tr[g] = {"rotation": f}
    if pompon:
        tr["pompon"] = {"rotation": pompon}
    if bras:
        tr["bras_r"] = {"rotation": lambda t: bras(t, 1)}
        tr["bras_l"] = {"rotation": lambda t: bras(t, -1)}
    return anim(name, T, tr, n_kf=n_kf)


def pend(T, base=0.0, amp=8.0, k=1, ph=0.0):
    return lambda t, s: (base + amp * math.sin(TAU * k * t / T + ph + (0.6 if s < 0 else 0)), 0, 0)


# états du familier vivant (guide 6.6, mode vol) : le mod règle sa place (vol près du maître) ; les états ne règlent que
# l'allure (balancement de lanterne, oreilles, queue, pattes), plus aucune contre-rotation du torse ni place sur le joueur.
TW = 1.6
walk = etat("pet_walk", TW, lambda t: (0.3 * S(TW, 1)(t), 0.45 * S(TW, 2, 0.5)(t), 0),
            lambda t: (-6 + 3 * S(TW, 2)(t), 0, 4 * S(TW, 1, 0.6)(t)),
            ears=lambda t, s: (8 + 3 * S(TW, 2, 0.8)(t), 6), oeil=lambda t: clin(t, 1.1),
            tail=([4, -2, -4, -4], 14, 6, 1, 0.14), pompon=lambda t: (8 - 4 * S(TW, 2, -0.8)(t), 0, -5 * S(TW, 1, -0.4)(t)),
            bras=pend(TW, -10, 10, 2), n_kf=16)
TR = 1.0
run = etat("pet_run", TR, lambda t: (0.3 * S(TR, 1)(t), 0.5 * S(TR, 2, 0.5)(t), 0),
           lambda t: (-16 + 3.5 * S(TR, 2)(t), 0, 5 * S(TR, 1, 0.6)(t)),
           ears=lambda t, s: (24 + 3 * S(TR, 2, 0.8)(t), 10), paup=lambda t: 0.25,
           tail=([12, 16, 18, 20], 10, 5, 1, 0.14), pompon=lambda t: (22 - 4 * S(TR, 2, -0.8)(t), 0, -6 * S(TR, 1, -0.4)(t)),
           bras=pend(TR, -35, 6, 2), n_kf=12)
TN = 3.2
# pet_swim : le papier craint l'eau ; il nage en se hissant (pattes qui pagaient), oreilles plaquées, flamme basse
swim = etat("pet_swim", TN, lambda t: (0, 1.2 + 0.5 * S(TN, 1)(t), 0),
            lambda t: (-6 + 7 * S(TN, 1)(t), 0, 6 * S(TN, 1, 1.4)(t)),
            ears=lambda t, s: (16 + 4 * S(TN, 1)(t), 22), oeil=lambda t: clin(t, 2.0), paup=lambda t: 0.3,
            tail=([-14, -10, -6, -6], 20, 8, 1, 0.16), pompon=lambda t: (-6 + 8 * S(TN, 1, -1.0)(t), 0, -6 * S(TN, 1, 0.4)(t)),
            bras=pend(TN, -20, 30, 2), n_kf=24)
swim["animators"][groups["ctrl_lumiere#l"]["uuid"]] = {"name": "ctrl_lumiere", "type": "bone", "keyframes": [kf("position", 0.0, (-0.35, 0, 0))]}
TA = 1.2
fall = etat("pet_fall", TA, lambda t: (0, 0.3 * S(TA, 1)(t), 0),
            lambda t: (5 + 2.5 * S(TA, 1)(t), 0, 3 * S(TA, 1, 0.8)(t)),
            ears=lambda t, s: (-8, 14 + 3 * S(TA, 2)(t)), pup=lambda t: 0.9,
            tail=([-22, -10, 0, 0], 8, 4, 1, 0.12), pompon=lambda t: (-18 + 4 * S(TA, 1, -0.8)(t), 0, -4 * S(TA, 1, 0.1)(t)),
            bras=lambda t, s: (-50 + 8 * math.sin(TAU * t / TA + (1 if s < 0 else 0)), 0, s * 12), n_kf=12)
# pet_sleep (maître endormi, ou 60 s sans bouger) : la lanterne descend et somnole, penchée, flamme basse
TZ = 4.0
sleep = etat("pet_sleep", TZ, lambda t: (0, -3.0 + 0.3 * S(TZ, 1)(t), 0),
             lambda t: (2 + 1.5 * S(TZ, 1)(t), 0, 3 * S(TZ, 1, 1.2)(t)),
             regard=lambda t: (8, YAW - 10, 8 + 2 * S(TZ, 1, 0.5)(t)), ears=lambda t, s: (4, 34 + 2 * S(TZ, 1)(t)), paup=lambda t: 1.0,
             tail=([-10, -18, -22, -22], 4, 2, 1, 0.12), pompon=lambda t: (8 - 1.5 * S(TZ, 1, -0.8)(t), 0, -3 * S(TZ, 1, 0.2)(t)),
             bras=lambda t, s: (-60, 0, 0), n_kf=20)
sleep["animators"][groups["ctrl_lumiere#l"]["uuid"]] = {"name": "ctrl_lumiere", "type": "bone", "keyframes": [kf("position", 0.0, (-0.5, 0, 0))]}

# event_owner_hurt (son maître prend un coup ; l'ancien hurt) : sursaut, queue en goupillon, oreilles plaquées, pupilles
# fendues ; puis la flamme flambe : il veille sur lui
owner_hurt = anim("event_owner_hurt", 1.2, {
    "fam_elan": {"position": lambda t: (-0.6 * bump(t, 0.0, 0.06, 0.2, 0.6) * math.sin(TAU * t * 7), 1.2 * bump(t, 0.0, 0.08, 0.16, 0.65), 2.6 * bump(t, 0.0, 0.08, 0.16, 0.65))},
    "fam_snap": {"rotation": lambda t: (16 * bump(t, 0.0, 0.08, 0.16, 0.65), 0, 10 * bump(t, 0.0, 0.05, 0.2, 0.66) * math.sin(TAU * t * 6))},
    "luciole": {"scale": lambda t: (0.001,) * 3}, "bouche_o": {"scale": lambda t: (0.001,) * 3},
    LIDS["l"]: {"scale": lambda t: (1, 0, 1)}, LIDS["r"]: {"scale": lambda t: (1, 0, 1)},
    "queue1": {"rotation": lambda t: (-30 * bump(t, 0.0, 0.08, 0.4, 0.8), 0, 0), "scale": lambda t: (1 + 0.35 * bump(t, 0.0, 0.06, 0.45, 0.85),) * 3},
    EARS["l"]: {"rotation": lambda t: ear_rot(-1, 20 * bump(t, 0.0, 0.05, 0.45, 0.8), 30 * bump(t, 0.0, 0.05, 0.45, 0.8))},
    EARS["r"]: {"rotation": lambda t: ear_rot(1, 20 * bump(t, 0.0, 0.05, 0.45, 0.8), 30 * bump(t, 0.0, 0.05, 0.45, 0.8))},
    PUPS["l"]: {"scale": lambda t: (1 - 0.4 * bump(t, 0.0, 0.05, 0.4, 0.7), 0.85 + 0.15 * (1 - bump(t, 0.0, 0.05, 0.4, 0.7)), 1)},
    PUPS["r"]: {"scale": lambda t: (1 - 0.4 * bump(t, 0.0, 0.05, 0.4, 0.7), 0.85 + 0.15 * (1 - bump(t, 0.0, 0.05, 0.4, 0.7)), 1)},
    "ctrl_lumiere#l": {"position": lambda t: (0.6 * bump(t, 0.3, 0.45, 0.85, 1.15), 0, 0)},
}, n_kf=30, loop="once")
# ------------------------------------------------------------------ idle : base vivante + 10 comportements au hasard (Molang)
TI, SL, NB = 28.0, 7.0, 30
# tirage pondéré (v3) : 30 cases, 10 calmes (0–9, un tiers) ; chaque comportement occupe un nombre de cases selon sa fréquence voulue :
# les gestes courants (écoute, toilette) reviennent souvent, les plus spectaculaires (luciole, queue, hoquet) restent rares.
POIDS = {6: 3, 8: 3, 7: 2, 9: 2, 12: 2, 15: 2, 10: 1, 11: 1, 13: 1, 14: 1, 16: 2}
SLOTS, _a = {}, 10
for _n, _w in POIDS.items():
    SLOTS[_n] = (_a, _a + _w)
    _a += _w
assert _a == NB, _a


def COND(n):
    a, b = SLOTS[n]
    return f"(v.i=={a})" if b - a == 1 else f"(v.i>={a})*(v.i<{b})"


PRE = (f"v.s=q.life_time/{SL:g}+q.instance_seed*13;v.i=math.floor(math.mod(math.sin(math.floor(v.s)*127+71)*517+517,1)*{NB});"
       f"v.u=math.mod(v.s,1)*{SL:g};v.e=math.clamp(math.min(v.u-0.7,6.3-v.u)/0.7,0,1)")
NUIT_BAILLE = f"v.i=v.i+(v.i<3)*(q.time_of_day>0.3)*(q.time_of_day<0.7)*({SLOTS[13][0]}-v.i)"
COTE = "(math.mod(math.floor(v.s),2)*2-1)"


def E(a, d):
    return f"math.sin(math.clamp((v.u-{a})/{d},0,1)*180)"


def EP(a, b, r=0.4):
    return f"math.clamp(math.min(v.u-{a},{b}-v.u)/{r},0,1)"


def relais(g):
    k = g + "_b"
    if k in groups:
        return k
    gg = groups[g]
    group(k, gg["origin"], g, nm=gg["name"] + "_b")
    groups[k]["ids"], gg["ids"] = gg["ids"], []
    for n, x in groups.items():
        if x["parent"] == g and n != k:
            x["parent"] = k
    return k


TERMS = {}


def T(g, ch, ax, n, expr):
    TERMS.setdefault((g, ch, ax), []).append((n, expr))


def ears_T(n, tx, tz, side_only=None):
    for side, tag in ((-1, "l"), (1, "r")):
        if side_only and side != side_only:
            continue
        rx, _, rz = ear_rot(side, 1, 1)
        if tx:
            T(EARS[tag], "rotation", 0, n, f"{tx}")
        if tz:
            T(EARS[tag], "rotation", 2, n, f"{-side}*({tz})")


# 6 écoute : tête et oreilles vers un son, d'un côté puis de l'autre
T("fam_comp", "rotation", 1, 6, f"22*v.e*{COTE}")
T("fam_comp", "rotation", 2, 6, f"-8*v.e*{COTE}")
ears_T(6, "-14*v.e", f"-10*v.e")
T(PUPS["l"], "scale", 0, 6, "0.6*v.e")
T(PUPS["r"], "scale", 0, 6, "0.6*v.e")
# 7 bisou de chat : se tourne vers le joueur, clignement lent, queue en crochet
T("fam_comp", "rotation", 1, 7, "-34*v.e")
T("fam_comp", "position", 0, 7, "0.8*v.e")
for tag in ("l", "r"):
    T(LIDS[tag], "scale", 1, 7, f"0.62*{EP(2.2, 4.4, 0.5)}")
T("queue3", "rotation", 0, 7, "-20*v.e")
T("queue4", "rotation", 0, 7, "-25*v.e")
ears_T(7, "-8*v.e", None)
# 8 toilette : patte droite à la bouche, langue, puis passée sur la face
G8 = EP(0.9, 5.6, 0.5)
T("bras_r", "rotation", 0, 8, f"{G8}*(118+10*math.sin(v.u*700))-30*{E(3.6, 1.6)}")
T("bras_r", "rotation", 2, 8, f"-22*{G8}-18*{E(3.6, 1.6)}")
T("bouche_o", "scale", 0, 8, f"({EP(1.2, 3.5, 0.2)}>0.5)")
T("bouche_o", "scale", 1, 8, f"({EP(1.2, 3.5, 0.2)}>0.5)*(0.5+0.25*math.sin(v.u*700))")
T("bouche_o", "scale", 2, 8, f"({EP(1.2, 3.5, 0.2)}>0.5)")
EYEB = {tag: relais(EYES[tag]) for tag in ("l", "r")}
for tag in ("l", "r"):
    T(EYEB[tag], "scale", 1, 8, f"-0.95*{G8}")
T("fam_comp", "rotation", 0, 8, f"8*{G8}")
T("fam_comp", "rotation", 2, 8, f"10*{E(3.6, 1.6)}")
# 9 pétrit en ronronnant (vibration)
G9 = EP(0.8, 6.0, 0.5)
T("bras_r", "rotation", 0, 9, f"{G9}*(35+28*math.sin(v.u*400))")
T("bras_l", "rotation", 0, 9, f"{G9}*(35-28*math.sin(v.u*400))")
T("fam_comp2", "position", 0, 9, f"0.035*math.sin(v.u*9000)*{G9}")
T("fam_comp2", "position", 1, 9, f"0.03*math.sin(v.u*7300)*{G9}")
for tag in ("l", "r"):
    T(LIDS[tag], "scale", 1, 9, f"0.7*{G9}")
ears_T(9, None, f"8*{G9}")
# 10 câlin : il penche la tête et frotte sa joue dans le vide, yeux plissés de plaisir (porté, il se frottait contre la tête
# du joueur ; familier vivant, sa place est réglée par le mod : plus de déplacement vers le joueur)
G10 = EP(1.0, 5.6, 0.8)
T("fam_comp", "position", 1, 10, f"{G10}*(0.9+0.3*math.sin(v.u*420))")
T("fam_comp", "rotation", 1, 10, f"38*{G10}")
T("fam_comp", "rotation", 2, 10, f"{G10}*(-10+8*math.sin(v.u*420))")
for tag in ("l", "r"):
    T(EYEB[tag], "scale", 1, 10, f"-0.9*{G10}")
ears_T(10, f"18*{G10}", f"14*{G10}")
T("queue1", "rotation", 0, 10, f"-22*{G10}")
# 11 luciole : elle arrive, il l'observe (pupilles rondes), frétille, bondit ; elle s'échappe vers le haut
G11 = EP(0.6, 6.4, 0.3)
LX = f"(-1.2*math.sin(v.u*70)-0.4*math.sin(v.u*190))"
T("luciole", "scale", 0, 11, f"{G11}")
T("luciole", "scale", 1, 11, f"{G11}")
T("luciole", "scale", 2, 11, f"{G11}")
T("luciole", "position", 0, 11, f"{G11}*{LX}")
T("luciole", "position", 1, 11, f"{G11}*(0.6*math.sin(v.u*110)+3*math.clamp((v.u-4.2)/1.6,0,1))")
T("luciole", "position", 2, 11, f"{G11}*0.5*math.sin(v.u*50)")
T("fam_comp", "rotation", 1, 11, f"v.e*(28+14*math.sin(v.u*70))")
T("fam_comp", "rotation", 0, 11, f"-6*v.e-14*{E(4.2, 1.6)}")
T("fam_comp2", "rotation", 2, 11, f"5*math.sin(v.u*1600)*{EP(2.8, 3.6, 0.2)}")
T("fam_comp2", "position", 0, 11, f"-1.6*{E(3.6, 0.7)}")
T("fam_comp2", "position", 1, 11, f"1.0*{E(3.6, 0.7)}")
T("fam_comp2", "position", 2, 11, f"-1.6*{E(3.6, 0.7)}")
T("bras_r", "rotation", 0, 11, f"95*{E(3.5, 0.8)}")
T("bras_l", "rotation", 0, 11, f"95*{E(3.55, 0.8)}")
T(PUPS["l"], "scale", 0, 11, f"1.3*{G11}")
T(PUPS["r"], "scale", 0, 11, f"1.3*{G11}")
ears_T(11, f"-16*v.e", None)
# 12 miche de pain : pattes rentrées, queue enroulée devant, yeux mi-clos, descend un peu
G12 = EP(0.8, 6.2, 0.7)
T("bras_r", "rotation", 0, 12, f"-55*{G12}")
T("bras_l", "rotation", 0, 12, f"-55*{G12}")
T("queue1", "rotation", 0, 12, f"34*{G12}")
T("queue1", "rotation", 1, 12, f"40*{G12}")
T("queue2", "rotation", 1, 12, f"50*{G12}")
T("queue3", "rotation", 1, 12, f"45*{G12}")
T("queue4", "rotation", 1, 12, f"35*{G12}")
T("fam_comp", "position", 1, 12, f"-0.7*{G12}")
T("fam_sq", "scale", 1, 12, f"-0.05*{G12}")
T("fam_sq", "scale", 0, 12, f"0.03*{G12}")
T("fam_sq", "scale", 2, 12, f"0.03*{G12}")
for tag in ("l", "r"):
    T(LIDS[tag], "scale", 1, 12, f"0.5*{G12}")
# 13 bâille et s'étire
B13 = EP(2.3, 4.2, 0.4)
T("bouche_o", "scale", 0, 13, f"({B13}>0.3)*1.1")
T("bouche_o", "scale", 1, 13, f"({B13}>0.3)*(0.6+0.6*{B13})")
T("bouche_o", "scale", 2, 13, f"({B13}>0.3)")
T("bras_r", "rotation", 0, 13, f"80*{E(1.0, 1.6)}")
T("bras_l", "rotation", 0, 13, f"80*{E(1.0, 1.6)}")
T("fam_sq", "scale", 1, 13, f"0.07*{E(1.0, 1.6)}-0.04*{E(2.5, 1.4)}")
T("fam_comp", "rotation", 0, 13, f"8*{E(2.2, 2.2)}")
for tag in ("l", "r"):
    T(EYEB[tag], "scale", 1, 13, f"-0.95*math.max({EP(2.2, 4.6, 0.3)},0.5*{E(1.0, 1.4)})")
ears_T(13, f"22*{E(2.2, 2.2)}", f"10*{E(2.2, 2.2)}")
# 14 court après sa queue : un tour, queue fouettée, puis s'arrête (pupilles rondes)
T("fam_comp2", "rotation", 1, 14, "(v.u<4.4)*(180-180*math.cos(math.clamp((v.u-1.6)/2.6,0,1)*180))")
T("queue1", "rotation", 1, 14, f"-30*{E(1.4, 3.0)}")
T("queue2", "rotation", 1, 14, f"-25*{E(1.4, 3.0)}")
T(PUPS["l"], "scale", 0, 14, f"1.2*{E(1.2, 3.4)}")
T(PUPS["r"], "scale", 0, 14, f"1.2*{E(1.2, 3.4)}")
T("bras_r", "rotation", 0, 14, f"40*{E(1.6, 2.6)}")
T("bras_l", "rotation", 0, 14, f"30*{E(1.7, 2.6)}")
# 15 tapote son pompon
T("fam_comp", "rotation", 0, 15, "-14*v.e")
T("bras_r", "rotation", 0, 15, f"v.e*(22+26*math.max(0,math.sin(v.u*330)))")
T("bras_r", "rotation", 2, 15, f"v.e*(10+12*math.max(0,math.sin(v.u*330)))")
T("pompon", "rotation", 2, 15, f"v.e*-24*math.sin(v.u*330-60)")
T("pompon", "rotation", 0, 15, f"v.e*10*math.sin(v.u*165)")
# 16 hoquet de flamme (propre à la lanterne) : la flamme saute d'un coup, il sursaute (yeux ronds, oreilles dressées),
# regarde sa propre lanterne, un second petit hoquet, puis il glousse, yeux plissés de rire
H1, H2 = E(1.2, 0.35), E(3.3, 0.3)
T("ctrl_lumiere#l", "position", 0, 16, f"0.6*{H1}+0.4*{H2}")
T("fam_comp2", "position", 1, 16, f"0.7*{E(1.25, 0.45)}+0.4*{E(3.35, 0.4)}")
T("fam_comp", "rotation", 0, 16, f"16*{EP(1.7, 3.2, 0.3)}")
T(PUPS["l"], "scale", 0, 16, f"1.2*{E(1.2, 2.4)}")
T(PUPS["r"], "scale", 0, 16, f"1.2*{E(1.2, 2.4)}")
for tag in ("l", "r"):
    T(EYEB[tag], "scale", 1, 16, f"0.12*{E(1.2, 0.9)}-0.85*{EP(4.2, 6.0, 0.25)}")
ears_T(16, f"-18*{E(1.2, 1.2)}-10*{E(3.3, 0.8)}", None)
T("fam_comp2", "rotation", 2, 16, f"7*math.sin(v.u*1100)*{EP(4.2, 6.0, 0.3)}")
T("bras_l", "rotation", 0, 16, f"60*{EP(4.2, 6.0, 0.3)}")
T("bras_r", "rotation", 0, 16, f"60*{EP(4.25, 6.0, 0.3)}")
T(PUPS["l"], "scale", 0, 15, "0.9*v.e")
T(PUPS["r"], "scale", 0, 15, "0.9*v.e")

BLINK = ("v.b=q.life_time/3.1+q.instance_seed*5;"
         "v.c=math.sin(math.clamp((math.mod(v.b,1)-math.mod(math.floor(v.b)*0.618,0.75))*19,0,1)*180)")
BASE = {
    ("fam_pos", "position"): ("0.25*math.sin(q.anim_time*12.857)", "0.6*math.sin(q.anim_time*25.714)+0.2*math.sin(q.anim_time*12.857+57)", 0),
    ("fam_swing", "rotation"): ("2.5*math.sin(q.anim_time*38.57+23)", 0, "5*math.sin(q.anim_time*25.714+52)"),
    ("fam_comp", "position"): (0, 0, 0), ("fam_comp", "rotation"): (0, 0, 0),
    ("fam_comp2", "position"): (0, 0, 0), ("fam_comp2", "rotation"): (0, 0, 0),
    ("fam_sq", "scale"): (1, 1, 1), ("ctrl_lumiere#l", "position"): (0, 0, 0),
    ("bras_r", "rotation"): ("-8+4*math.sin(q.anim_time*25.714)", 0, 0), ("bras_l", "rotation"): ("-8+4*math.sin(q.anim_time*25.714+40)", 0, 0),
    ("bouche_o", "scale"): (0.001, 0.001, 0.001), ("luciole", "scale"): (0.001, 0.001, 0.001), ("luciole", "position"): (0, 0, 0),
    ("pompon", "rotation"): ("-3*math.sin(q.anim_time*38.57-34)", 0, "-5*math.sin(q.anim_time*25.714+6)"),
}
for i, g in enumerate(QG):
    BASE[(g, "rotation")] = (f"{(-6, -4, -4, -4)[i]}+{round(4 + 2 * i, 1)}*math.sin(q.anim_time*25.714-{25 * i})", f"{round(8 + 3 * i, 1)}*math.sin(q.anim_time*51.43-{30 * i})", 0)
for tag, s in (("l", -1), ("r", 1)):
    BASE[(EARS[tag], "rotation")] = (f"3*math.sin(q.anim_time*25.714+{40 if s < 0 else 0})", 0, f"{-s * 4}")
    BASE[(LIDS[tag], "scale")] = (1, 0, 1)
    BASE[(PUPS[tag], "scale")] = (PUP_JOUR, 1, 1)
    BASE[(EYEB[tag], "scale")] = (1, 1, 1)
MOLANG_TROP = []


def ninstr(s):
    return s.count(";") + 1


def cles(base, terms, neutre):
    out, cur = [], []

    def build(ts, b):
        pre = PRE + (";" + NUIT_BAILLE if any(n == 13 for n, _ in ts) else "")
        bb = fmt(b)
        return pre + ";" + (bb if bb not in ("0", "0.0") else "") + "".join(f"+{COND(n)}*({e})" for n, e in ts)
    b = base
    for t in terms:
        if cur and len(build(cur + [t], b)) > 505:
            out.append(build(cur, b))
            cur, b = [], neutre
        cur.append(t)
    out.append(build(cur, b))
    for k in out:
        if len(k) > 512 or ninstr(k) > 16:
            MOLANG_TROP.append(f"{len(k)} car.")
    return out


idle_molang = {}


def poser(g, ch, ax, v):
    idle_molang.setdefault(g, {}).setdefault(ch, [None, None, None])[ax] = v


ADDITIF_ECHELLE = {"fam_sq"}          # termes d'échelle écrits en écart (1 + somme)
for (g, ch), base in BASE.items():
    for ax in range(3):
        neutre = 1 if ch == "scale" else 0
        terms = TERMS.get((g, ch, ax), [])
        if not terms:
            ks = [base[ax]]
        else:
            ks = cles(base[ax], terms, neutre)
        if g in (LIDS["l"], LIDS["r"]) and ax == 1 and terms:
            assert len(ks) == 1, len(ks[1])
            a, _, b = ks[0].rpartition(";")
            ks = [f"{a};math.min(1,{b})"]
        gg = g
        for i, k in enumerate(ks):
            poser(gg, ch, ax, k)
            if i + 1 < len(ks):
                gg = relais(gg)
orph = [k for k in TERMS if (k[0], k[1]) not in BASE]
assert not orph, f"comportements sans base : {orph}"
for tag in ("l", "r"):
    poser(EYES[tag], "scale", 1, f"{PRE};{BLINK};1-0.95*v.c")
for g, chans in idle_molang.items():
    for ch, v in chans.items():
        neutre = 1 if ch == "scale" else 0
        chans[ch] = tuple(neutre if x is None else x for x in v)
idle = anim("pet_idle", TI, molang=idle_molang)
# pet_fly : même vie que le repos ; la lanterne penche le haut vers l'avant et traîne le bas selon sa vitesse
# (q.ground_speed du familier), au cas où le mode vol joue pet_fly aussi à l'arrêt (supposé, guide muet)
VIT = "math.clamp(q.ground_speed/4.3,0,1.4)"
fly_molang = dict(idle_molang)
fly_molang["fam_cr"] = {"rotation": (f"-9*{VIT}", 0, 0), "position": (0, 0, 0)}
fly = anim("pet_fly", TI, molang=fly_molang)
# pet_sit (maître accroupi à côté, ou 20 s sans bouger) : même vie, la lanterne descend se poser bas « en miche de pain »
sit_molang = dict(idle_molang)
sit_molang["fam_cr"] = {"position": (0, -2.4, 0)}
sit = anim("pet_sit", TI, molang=sit_molang)

# ------------------------------------------------------------------ overlay_lanterne
DT = "math.min(1,q.delta_time*{})"
# familier vivant (guide 6.6) : les requêtes 6.3 parlent du familier ; le maître par q.owner_*
VIE = "(q.owner_health<q.owner_max_health*0.35)"           # vie basse du maître : il veille sur lui
PRES = "math.clamp((2.6-q.owner_distance)*1.2,0,1)"         # le maître vient tout près (il s'arrête à 2 blocs)
# regard au hasard : saccades de la tête, 10 tranches de 3,6 s ; chaque tranche part de la valeur de la précédente
HEADY = ("v.hg=math.mod(q.life_time,36)/3.6;v.hk=math.floor(v.hg);"
         "v.ha=math.mod(math.abs(math.sin((v.hk+q.instance_seed*10)*47))*263,1);"
         "v.hb=math.mod(math.abs(math.sin((math.mod(v.hk+9,10)+q.instance_seed*10)*47))*263,1);"
         "math.lerp(v.hb,v.ha,math.clamp(math.mod(v.hg,1)*4,0,1))*36-18")
NUIT = "math.clamp((0.27-math.abs(q.time_of_day-0.5))*6,0,1)"
SACC = ("v.g=math.mod(q.life_time,36)/1.8;v.k=math.floor(v.g);"
        "v.ga=math.mod(math.abs(math.sin((math.mod(v.k,20)+q.instance_seed*20)*61))*331,1);"
        "v.gb=math.mod(math.abs(math.sin((math.mod(v.k+19,20)+q.instance_seed*20)*61))*331,1);"
        "v.gv=math.lerp(v.gb,v.ga,math.clamp(math.mod(v.g,1)*6,0,1))")
overlay_molang = {
    "fam_reac": {
        # il lève le nez vers son maître quand il vient tout près ; sinon regarde autour de lui par saccades
        "rotation": (f"v.ax=math.lerp(v.ax,{PRES}*9,{DT.format(2.5)});v.ax+2*math.sin(q.life_time*20)",
                     HEADY,
                     f"v.az=math.lerp(v.az,math.clamp(-q.yaw_speed*0.05,-12,12),{DT.format(2)});v.rn=math.mod(q.life_time,32);"
                     f"v.az+q.is_in_rain*1.5*math.sin(v.rn*2200)*(math.mod(v.rn,5)<0.6)"),
        # pluie : il se blottit, plus bas et tassé (sa place près du maître est réglée par le mod) ;
        # eau : une lanterne de papier craint l'eau, il s'élève au-dessus (q.is_in_water)
        "position": (0,
                     f"v.wy=math.lerp(v.wy,q.is_in_rain,{DT.format(1)});v.wa=math.lerp(v.wa,q.is_in_water,{DT.format(2)});2.2*v.wa-0.6*v.wy", 0),
        "scale": (f"v.s1=math.lerp(v.s1,q.is_in_rain,{DT.format(1)});1+0.05*v.s1",
                  f"v.s2=math.lerp(v.s2,q.is_in_rain,{DT.format(1)});1-0.07*v.s2", 1),
    },
    # flamme : plus vive la nuit, baisse sous la pluie et dans l'eau ; quand la vie du joueur est basse, elle brûle plus fort
    # (il veille sur lui) ; vacille en permanence
    "ctrl_lumiere#l": {"position": (f"v.l=math.lerp(v.l,{NUIT}*0.45-q.is_in_rain*0.4-q.is_in_water*0.35+{VIE}*0.3,{DT.format(0.7)});v.f=math.mod(q.life_time,32);"
                                    f"v.l-0.25+0.07*math.sin(v.f*1300)+0.05*math.sin(v.f*2900)", 0, 0)},
}
for tag, s in (("l", -1), ("r", 1)):
    overlay_molang[PUPS[tag]] = {"scale": (f"v.n{tag}=math.lerp(v.n{tag},{NUIT},{DT.format(0.5)});1+1.3*v.n{tag}", 1, 1),
                                 "position": (f"{SACC};(v.gv*2-1)*0.12", f"{SACC};(math.mod(v.gv*7.3,1)*2-1)*0.06", 0)}
    tw = (f"v.t{tag}=math.mod(q.life_time,36)*{0.375 if s < 0 else 0.25}+q.instance_seed*{3 if s < 0 else 7};"
          f"(math.mod(math.floor(v.t{tag})*0.618,1)>0.35)*math.pow(math.sin(math.clamp((math.mod(v.t{tag},1)"
          f"-math.mod(math.floor(v.t{tag})*0.37,0.8))*14,0,1)*180),2)*{-s * 16}")
    overlay_molang[EARS[tag]] = {"rotation": (f"v.p{tag}=math.lerp(v.p{tag},math.max(math.max(q.is_in_rain,q.is_in_water),{VIE}),{DT.format(1.5)});24*v.p{tag}", 0,
                                              f"v.q{tag}=math.lerp(v.q{tag},math.max(math.max(q.is_in_rain,q.is_in_water),{VIE}),{DT.format(1.5)});{-s * 30}*v.q{tag}")}
    overlay_molang[LIDS[tag]] = {"rotation": (0, 0, f"{-s * 14}*{VIE}")}
# tressaillements d'oreille : sur un relais (l'expression reste courte)
for tag, s in (("l", -1), ("r", 1)):
    r = relais(EARS[tag])
    tw = (f"v.t{tag}=math.mod(q.life_time,36)*{0.375 if s < 0 else 0.25}+q.instance_seed*{3 if s < 0 else 7};"
          f"(math.mod(math.floor(v.t{tag})*0.618,1)>0.35)*math.pow(math.sin(math.clamp((math.mod(v.t{tag},1)"
          f"-math.mod(math.floor(v.t{tag})*0.37,0.8))*14,0,1)*180),2)*{-s * 16}")
    overlay_molang[r] = {"rotation": (0, 0, tw)}
overlay_molang[relais("queue4")] = {"rotation": (0, "6*math.sin(q.life_time*50+q.instance_seed*360)", 0)}
# porté (menu Apparence, ou deuxième familier : guide 6.6, q.is_pet = 0) : à gauche de la tête, comme la v3
overlay_molang["chat_lanterne"] = {"position": tuple(f"(1-q.is_pet)*{round(float(v), 3):g}" for v in C0)}
overlay = anim("overlay_lanterne", 36.0, molang=overlay_molang)


# ------------------------------------------------------------------ événements
# Apparition (2026-11-08) : une lanterne de papier se range PLIÉE à plat. Elle apparaît pliée et éteinte, se déplie en
# accordéon (du bas vers le haut, avec un rebond) ; la bougie s'allume (lumière qui vacille, hoquet de flamme, la
# lanterne oscille sous la chaleur) ; il ouvre les yeux en miaulant (son) : pupilles d'abord rondes, qui se fendent
# à la lumière ; oreilles qui se dressent, queue qui fouette ; puis il lève le nez vers son maître, tête penchée.
# Les paupières valent 0 dans l'état (une échelle d'événement ne peut pas les fermer) : l'œil fermé = l'œil aplati devant
# le fond d'œil fermé.
def _apparition(T0, T1, T2, T3, T4, T5):
    """T0 fin de l'apparition pliée, T1 fin du dépliage, T2 fin de l'allumage, T3 yeux ouverts, T4 début du regard, T5 fin."""
    elan = lambda t: (max(0.001, 0.3 + 0.7 * sm(t, 0.0, T0)),) * 3
    def pli(t):
        u = sm(t, T0 * 0.6, T1)
        sy = 0.14 + 0.86 * u + 0.12 * bump(t, T1 - 0.1, T1, T1 + 0.02, T1 + 0.14) - 0.06 * bump(t, T1 + 0.1, T1 + 0.16, T1 + 0.18, T1 + 0.28)
        return (1 + 0.12 * (1 - u), max(0.05, sy), 1 + 0.12 * (1 - u))
    def lumiere(t):
        on = sm(t, T1, T1 + 0.12)
        vac = 0.5 * bump(t, T1, T1 + 0.08, T2 - 0.12, T2) * abs(math.sin(TAU * 7 * (t - T1)))
        return (-1 + on * (1.0 + vac) + 0.3 * bump(t, T2 - 0.15, T2 - 0.08, T2 - 0.06, T2 + 0.1), 0, 0)
    chaleur = lambda t: (5 * bump(t, T1, T1 + 0.1, T1 + 0.2, T2 + 0.3) * math.sin(TAU * 2.2 * (t - T1)), 0,
                         4 * bump(t, T1, T1 + 0.1, T1 + 0.2, T2 + 0.3) * math.sin(TAU * 1.6 * (t - T1)) + 6 * bump(t, T4, T4 + 0.15, T5 - 0.15, T5))
    oeil = lambda t: (1, max(0.04, 0.04 + 0.96 * sm(t, T3 - 0.12, T3)) * (1 + 0.12 * bump(t, T3 - 0.02, T3, T3 + 0.02, T3 + 0.12)), 1)
    pup = lambda t: (1 + (1 / PUP_JOUR - 1) * (1 - sm(t, T3 + 0.05, T3 + 0.4)), 1, 1)      # ronde au réveil, fendue à la lumière
    def ear(side, d):
        return lambda t: ear_rot(side, 22 * (1 - sm(t, T3 + d, T3 + 0.18 + d)) - 16 * bump(t, T3 + 0.1 + d, T3 + 0.22 + d, T4, T5), 26 * (1 - sm(t, T3 + d, T3 + 0.18 + d)))
    regard = lambda t: (9 * bump(t, T4, T4 + 0.18, T5 - 0.18, T5), 0, 0)
    tr = {"fam_elan": {"scale": elan}, "fam_sq": {"scale": pli}, "ctrl_lumiere#l": {"position": lumiere},
          "fam_swing": {"rotation": chaleur}, "lanterne": {"rotation": regard},
          EARS["l"]: {"rotation": ear(-1, 0.0)}, EARS["r"]: {"rotation": ear(1, 0.05)}}
    for tag in ("l", "r"):
        tr[EYES[tag]] = {"scale": oeil}
        tr[PUPS[tag]] = {"scale": pup}
    tr["queue1"] = {"rotation": lambda t: (0, 22 * flick(t, T3 + 0.15) - 14 * flick(t, T3 + 0.45), 0)}
    return tr


equip = anim("event_equip", 2.2, _apparition(0.2, 0.6, 1.0, 1.25, 1.7, 2.2), n_kf=66, loop="once")
equip["animators"]["effects"] = {"name": "Effects", "type": "effect",
                                 "keyframes": [{"channel": "sound", "data_points": [{"effect": "entity.cat.ambient", "file": ""}], "time": 1.15}]}
# event_teleport (coincé 3 s ou à plus de 20 blocs : il revient près du joueur) : la même apparition en bref, sans son
teleport = anim("event_teleport", 1.3, _apparition(0.1, 0.3, 0.5, 0.65, 0.9, 1.3), n_kf=39, loop="once")
jump = anim("event_jump", 0.6, {"fam_elan": {"position": lambda t: (0, -0.8 * bump(t, 0.0, 0.15, 0.2, 0.5), 0)},
                                "fam_swing": {"rotation": lambda t: (8 * bump(t, 0.05, 0.2, 0.25, 0.55), 0, 0)},
                                "pompon": {"rotation": lambda t: (-14 * bump(t, 0.05, 0.18, 0.25, 0.55), 0, 0)}}, n_kf=18, loop="once")
AMP = "math.clamp(q.land_speed*0.12,0.4,1.4)"
land = anim("event_land", 0.7, loop="once")
land["animators"][groups["fam_elan"]["uuid"]] = {"name": "fam_elan", "type": "bone", "keyframes": [
    kf("position", round(t, 3), (0, f"{round(-0.9 * bump(t, 0.0, 0.08, 0.12, 0.4) + 0.3 * bump(t, 0.35, 0.45, 0.48, 0.65), 4)}*{AMP}", 0))
    for t in [i * 0.7 / 21 for i in range(22)]]}
land["animators"][groups["pompon"]["uuid"]] = {"name": "pompon", "type": "bone", "keyframes": [
    kf("rotation", round(t, 3), (f"{round(18 * bump(t, 0.0, 0.1, 0.15, 0.45) - 8 * bump(t, 0.35, 0.45, 0.5, 0.7), 3)}*{AMP}", 0, 0))
    for t in [i * 0.7 / 21 for i in range(22)]]}

# familier vivant (guide 6.6) : vol près du maître, à 2 blocs ; centre de la lanterne à 1,6 bloc (la v3 flottait à 26,5 px)
FAMILIER = {"mode": "vol", "distance": 2, "vitesse": 1, "hauteur": 1.6}
ANIMS = [idle, fly, sit, walk, run, sleep, swim, fall, overlay, equip, teleport, owner_hurt, jump, land]
assert len(ANIMS) <= 32
assert not MOLANG_TROP, "Molang trop long : " + " | ".join(MOLANG_TROP)
# translation pure de -C0 (géométrie et texture de la v3 inchangées) : centre de la lanterne à l'origine du modèle
for e in elements:
    for k in ("from", "to", "origin"):
        e[k] = [round(float(a - b), 3) for a, b in zip(e[k], C0)]
for g in groups.values():
    g["origin"] = [round(float(a - b), 3) for a, b in zip(g["origin"], C0)]
# aucun groupe du corps à la racine : racine « chat_lanterne »
outliner = [bone_node("chat_lanterne")]

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS,
         "unhandled_root_fields": {"phynaria": {"version": 1, "familier": FAMILIER}}}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


exprs = [v for a in ANIMS for b in a["animators"].values() for k in b["keyframes"] for dp in k.get("data_points", []) for v in dp.values()
         if isinstance(v, str) and any(ch.isalpha() for ch in v)]
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      f"densité {DENS:.1f} texels/px ; Molang max {max(map(len, exprs))} car., {max(map(ninstr, exprs))} instructions")
