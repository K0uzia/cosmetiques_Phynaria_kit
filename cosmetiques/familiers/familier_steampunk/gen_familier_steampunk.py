"""Hibou Steampunk, FAMILIER VIVANT perché (2026-11-08, guide 6.6) : géométrie et texture de la version portée inchangées
(150 cubes, texture et _e au pixel près ; ancien générateur .build/gen_avant.py, ancien livrable .build/avant_livrable.bbmodel,
comparaison .build/comparaison_avant_apres.png). Seuls changent : la racine (plus de groupe body, fam_racine à la racine), la
translation finale de -ORIG (origine = centre du dessus de l'épaule gauche, serres à (-1,8 ; 0,42 ; 0) pour garder l'écart à la
tête du joueur mesuré), la paupière (lame de base 0,08 px au lieu de 0,06 : fermée à x15, limite 16) et les animations.
Bloc phynaria.familier {"mode": "perche", "distance": 2, "vitesse": 1, "hauteur": 1.8} : un oiseau se pose sur l'épaule ; il
s'envole sur son rotor quand le joueur court, saute, vole ou nage (le mod décide), ce que faisait déjà l'ancienne version.
Animations : pet_idle et pet_sit (perché : les 10 comportements au hasard de 120 s ; en pet_idle sans être perché, rotor sorti et
serres repliées par q.is_perched), pet_walk / pet_run / pet_fly (en l'air sur le rotor, ailes raides en gouvernes, sans décalage :
le mod le place), pet_fall (rotor à fond, ailes en aérofreins), pet_sleep (perché, tête rentrée), overlay_mecanisme (regard par
crans tiré au hasard, vie basse du maître par q.owner_health : tourné vers lui, lentilles en panne ; maître accroupi
(q.owner_is_sneaking) : mince et allongé ; maître qui marche, perché : il compense le pas (q.owner_ground_speed) ; pluie, nuit,
virages ; porté (q.is_pet = 0, menu Apparence) : recalé sur l'épaule gauche), event_equip (un son), event_teleport, event_perch,
event_owner_hurt, event_jump, event_land. Plus d'attack ni de hurt, plus de walk/sneak/glide/swim du joueur.
À juger en jeu (/cosmetique apercu) : place exacte de l'origine perchée (centre de l'épaule supposé), état joué perché
(pet_sit ou pet_idle), recouvrement des échelles du rotor si event_equip tombe pendant un vol, vapeur emit_ (pas encore lancée
par le mod sur un familier vivant).

Version portée (2026-11-05), ci-dessous :
Familier hibou mécanique : automate de laiton perché sur l'épaule gauche du joueur, qui décolle sur un rotor de tête.
Ensemble Steampunk (thème Mécanique) : .claude/styles/steampunk.md, .claude/styles/familiers.md, .claude/references/familiers/,
.claude/references/animaux/oiseaux.md (hibou), .claude/references/creatures/mecaniques.md. Design original.
Écrit familier_steampunk.png, familier_steampunk_e.png et .build/familier_steampunk_brut.bbmodel.
Ancienne version (flottait à droite sur une hélice carénée) : .build/gen_avant.py, .build/avant_livrable.bbmodel.

Placement (types-familiers.md, arbre de décision) : un petit oiseau se PERCHE sur l'épaule, à gauche comme le perroquet. Le hibou a
un rotor, mais il se pose pour économiser sa vapeur ; il ne décolle que quand le joueur quitte le sol (vol créatif, élytres, vraie
chute) ou pour un court vol au hasard. Centre au-dessus du bord extérieur de l'épaule (x = -7,8) : la tête du joueur, qui tourne,
balaie un cylindre de 5,66 px de rayon (mesuré par .build/mesure.py sur toutes les animations).

Modèle : corps en oeuf et grosse tête (8 fuseaux) en peaux de laiton de 0,3 px autour d'âmes pleines, peints en espace monde
(lumière, joints rivetés, plumes gravées en écailles qui traversent les facettes) ; métal propre (brossé ±5 %, aucune patine).
Disque facial en deux coupelles rayonnantes à liseré de cuivre, sourcils de cuivre mobiles, grands yeux-lentilles (verre ambre
lumineux, pupille-diaphragme, iris à crans, paupière-volet), bec crochu, aigrettes. Plastron d'écailles de cuivre couchées, ailes
repliées en lames à nervure, queue courte en éventail, cuisses emplumées, serres d'acier qui agrippent le dessus de l'épaule (le
pied extérieur passe une griffe par-dessus le bord du bras). Mécanique visible : collier denté sur lequel tourne la tête, clé de
remontage, rotor télescopique dans un dôme sur la calotte (au-dessus du centre de gravité, il porte le hibou : les ailes restent
raides en gouvernes, elles ne battent jamais pour voler), soupape, foyer à hublot.

Vie (idle, Molang sans variable mémorisée, calculé par le renderer) : tranches de 13 s décalées par q.instance_seed, début décalé de
0 à 3 s par tranche (écarts de 10 à 16 s), un tirage pondéré par tranche (3 cases sur 16 sans rien), un seul comportement à la fois
et le reste de la tranche calme :
tête retournée à 200° ou 240° par crans, tête penchée et hochement de triangulation, se lisser l'aile, battre des ailes pour
l'équilibre, petit vol autour de la tête par derrière jusqu'à l'épaule droite, se remonter quand il est fatigué, jet de vapeur,
picorer la joue du joueur (seulement si sa tête regarde devant), somnoler le jour (hibou nocturne). Base : respiration, mise au
point des lentilles par crans, clignements irréguliers, petits tics d'aigrettes et de queue.

Fonctions avancées : overlay_mecanisme (regard du joueur par crans de 15° avec retard, virages, vie basse, pluie/eau, nuit :
pupilles et lentilles plus vives, aigrettes dressées ; vie basse : lentilles qui baissent par à-coups, tassé, tourné vers le joueur) ; ctrl_lumiere (lentilles, foyer) ; ctrl_emit dans emit_mc_white_smoke (coupé
au repos, jet à la décharge, fumée sous la pluie) ; trans_vapeur (bouffée modélisée) ; event_jump, event_land (q.land_speed),
event_equip (2026-11-08 : arrive en courbe sur son rotor, se cabre, se pose, range le rotor, lentilles, regard
vers le maître ; un son), event_perch et event_teleport (même atterrissage, sans son) ; fall : décolle si q.vertical_speed < -9. Variables mémorisées (v.hx, v.hy, v.vz)
seulement dans overlay_mecanisme : à juger en jeu.

Hiérarchie (body = torse) : fam_racine (orbite) > fam_vol (décollage, contre-rotation) > fam_elan (événements) > fam_cap (cap en vol)
> fam_virage (overlay) > fam_snap (hasard, attaque, blessure) > corps, pattes ; corps > tete_suivi (overlay) > tete (états) >
tete_hasard (idle) > yeux, sourcils, aigrettes, rotor_mat > rotor, soupape, trans_vapeur.
"""
import base64, io, json, math, os, zlib, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # calque _e embarqué en seconde texture (correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu)
NOM = "familier_steampunk"
TEX = 512
TAU = 2 * math.pi
SS = 3

# ------------------------------------------------------------------ palette (fiche de style Steampunk)
BRASS = dict(hi=(236, 196, 112), base=(190, 142, 64), low=(112, 76, 32))
COPPER = dict(hi=(232, 150, 96), base=(176, 92, 52), low=(98, 46, 26))
STEEL = dict(hi=(136, 140, 150), base=(78, 82, 92), low=(38, 40, 48))
AMBRE_C = np.array((255, 210, 120), np.float32)
AMBRE = np.array((220, 150, 50), np.float32)
E_AMBRE = np.array((214, 132, 48), np.float32)      # lueur chaude et douce : couleur moyenne, pas vive

# Perché sur l'épaule GAUCHE (code du perroquet). Le centre est au-dessus du bord extérieur de l'épaule : la tête du joueur, qui
# tourne, balaie un cylindre de rayon 4·√2 = 5,66 px ; tout le hibou reste à |x| ≥ 5,7 (mesuré, .build/mesure.py).
ORIG = np.array((-6.0, 24.0, 0.3))  # perché (guide 6.6) : origine du modèle = centre du dessus de l'épaule gauche (translation en fin de script)
P0 = np.array((-7.8, 24.0, 0.3))   # point d'appui des serres (dessus de l'épaule : y = 24, seconde couche à 24,25)
C0 = P0 + np.array((0.0, 2.15, 0.0))


def A(c):
    return np.array(c, np.float32)


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


def seg_dist(px, py, pts):
    d = np.full(px.shape, 1e9, np.float32)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        vx, vy = bx - ax, by - ay
        t = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
        d = np.minimum(d, np.hypot(px - ax - t * vx, py - ay - t * vy))
    return d


def rodrigues(v, k, ang):
    k = unit(k)
    a = math.radians(ang)
    return v * math.cos(a) + np.cross(k, v) * math.sin(a) + k * (k @ v) * (1 - math.cos(a))


# ------------------------------------------------------------------ polyèdres : corps (oeuf) et tête
class Ovo:
    """Surface de révolution facettée : rh(lat) = rh * cos(lat) * (1 - taper * sin(lat)), y = rv * sin(lat). Repère local, avant = -Z."""

    def __init__(self, tag, rh, rv, lats, nlon=8, taper=0.0):
        self.tag, self.rh, self.rv, self.lats, self.nlon, self.taper = tag, rh, rv, lats, nlon, taper
        self.dlon = 360.0 / nlon
        self.facets = []
        for j in range(len(lats) - 1):
            for k in range(nlon):
                p0, p1, l0, l1 = k * self.dlon, (k + 1) * self.dlon, lats[j], lats[j + 1]
                v = [self.P(p0, l0), self.P(p1, l0), self.P(p1, l1), self.P(p0, l1)]
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
                w, h = max(xs) - min(xs) + 0.08, max(ys) - min(ys) + 0.08
                poly = [(a - bx, b - by) for a, b in pts]
                self.facets.append(dict(name=f"{tag}_{j}_{k}", cout=cout, X=X, Y=Y, n=n, w=w, h=h, poly=poly, band=j, gore=k))

    def k(self, lat):
        return 1 - self.taper * math.sin(math.radians(lat))

    def P(self, phi, lat, s=1.0):
        p, l = math.radians(phi), math.radians(lat)
        r = self.rh * math.cos(l) * self.k(lat)
        return V(r * math.sin(p), self.rv * math.sin(l), -r * math.cos(p)) * s

    def normal(self, p):
        """Normale lissée (ellipsoïde approché) : sert à la peinture continue d'une facette à l'autre."""
        return p / np.array((self.rh ** 2, self.rv ** 2, self.rh ** 2), np.float32)

    def facet(self, band, gore):
        return next(f for f in self.facets if f["band"] == band and f["gore"] == gore % self.nlon)


BODY = Ovo("corps", 1.7, 1.95, [-66.0, -30.0, 5.0, 42.0], taper=0.10)
HEAD = Ovo("tete", 1.75, 1.45, [-48.0, -12.0, 24.0, 58.0])
HY = 2.25                # centre de la tête au-dessus du centre du corps (tête presque aussi large que le corps : hibou)
NECK_Y = 1.28            # pivot du cou = collier denté
TH = 0.3                 # épaisseur d'une peau

# yeux : centre de la facette avant de la bande médiane de la tête
EYES = {}
for s, tag in ((1, "r"), (-1, "l")):
    f = HEAD.facet(1, 0 if s > 0 else 7)
    axe = unit(f["n"] + V(0, 0, -1.0) * 1.1)        # entre la normale et l'avant : regard franc, léger écart
    EYES[tag] = dict(s=s, c=f["cout"].copy(), axe=axe)
EX, EY = abs(EYES["r"]["c"][0]), EYES["r"]["c"][1]

LUM = unit(V(-0.45, 0.85, -0.45)).astype(np.float32)


# ------------------------------------------------------------------ outils de peinture
def grid(W, H, w, h, ss=SS):
    gx = ((np.arange(W * ss) + 0.5) / (W * ss) - 0.5) * w
    gy = (0.5 - (np.arange(H * ss) + 0.5) / (H * ss)) * h
    return np.meshgrid(gx, gy)


def down_mask(m_ss, W, H):
    return np.array(Image.fromarray((np.clip(m_ss, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110


def inset(mask, n):
    im = Image.fromarray(mask.astype(np.uint8) * 255, "L")
    d = np.zeros(mask.shape, np.float32)
    for _ in range(n):
        im = im.filter(ImageFilter.MinFilter(3))
        d += np.array(im) > 127
    return d


def noise(H, W, cells, seed):
    r = np.random.default_rng(seed)
    a = (r.random((max(2, int(cells * H / max(H, W))) + 2, max(2, int(cells * W / max(H, W))) + 2)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((W, H), Image.BICUBIC), np.float32) / 255


def finish(col, mask, e=None):
    H, W = mask.shape
    out = np.zeros((H, W, 4), np.uint8)
    c = np.clip(col, 0, 255)
    if mask.any():
        c[~mask] = c[mask].mean(axis=0)
    out[..., :3] = c.astype(np.uint8)
    out[..., 3] = mask * 255
    oe = np.zeros((H, W, 4), np.uint8)
    if e is not None:
        on = mask & (e.max(axis=2) > 2)
        oe[on, :3] = np.clip(e[on], 0, 255).astype(np.uint8)
        oe[on, 3] = 255
    return out, oe


def metal_shade(metal, lam, streak):
    """lam : éclairage 0..1. Laiton moyen dominant, clair sur les bombés, sombre dans les creux."""
    c = lerp(A(metal["low"]), A(metal["base"]), np.clip(0.30 + lam * 0.95, 0, 1)[..., None])
    c = lerp(c, A(metal["hi"]), (smv(lam, 0.70, 0.98) * 0.85)[..., None])
    return c * (1 + 0.10 * streak)[..., None]


def rivet(col, px, py, x, y, r, metal):
    """Rivet peint en coordonnées modèle : anneau sombre, tête, éclat en haut à gauche."""
    d = np.hypot(px - x, py - y)
    col[d <= r * 1.35] = A(metal["low"]) * 0.6
    col[d <= r] = A(metal["base"])
    col[np.hypot(px - x + r * 0.35, py - y - r * 0.35) <= r * 0.5] = A(metal["hi"])


def bevel(col, mask, metal, joint=True):
    d = inset(mask, 6)
    if joint:
        k = (d >= 3) & (d < 5)
        col[k] = col[k] * 0.55
    col[d < 3] = A(metal["hi"]) * 0.92
    return col


# ------------------------------------------------------------------ peaux des polyèdres
def peint_facette(ovo, f):
    est_tete = ovo is HEAD

    def painter(W, H):
        px, py = grid(W, H, f["w"], f["h"], 1)
        m = Image.new("L", (W * SS, H * SS), 0)
        d_ = W * SS / f["w"]
        ImageDraw.Draw(m).polygon([((a + f["w"] / 2) * d_, H * SS / 2 - b * d_) for a, b in f["poly"]], fill=255)
        m = m.filter(ImageFilter.MaxFilter(2 * max(1, int(round(0.03 * d_))) + 1))
        mask = down_mask(np.array(m, np.float32) / 255, W, H)
        P3 = f["cout"][None, None, :] + f["X"][None, None, :] * px[..., None] + f["Y"][None, None, :] * py[..., None]
        x, y, z = P3[..., 0], P3[..., 1], P3[..., 2]
        nr = ovo.normal(P3)
        nr = nr / np.linalg.norm(nr, axis=2, keepdims=True)
        lam = np.clip(nr @ LUM, 0, 1) * 0.85 + 0.15 * smv(y, -ovo.rv, ovo.rv)
        streak = noise(H, W, 14, zlib.crc32(f["name"].encode()) % 1000) - 0.5
        col = metal_shade(BRASS, lam, streak)
        poly = f["poly"]
        d_bas = seg_dist(px, py, [poly[0], poly[1]])
        d_haut = seg_dist(px, py, [poly[2], poly[3]])
        d_cote = np.minimum(seg_dist(px, py, [poly[1], poly[2]]), seg_dist(px, py, [poly[3], poly[0]]))
        facial = np.zeros(x.shape, bool)
        if est_tete:
            de = np.minimum(np.hypot(x - EX, y - EY), np.hypot(x + EX, y - EY))
            avant = z < -0.35
            facial = avant & (de < 1.0)
            rim = avant & (de >= 1.0) & (de < 1.15)
            # disque facial : laiton clair, plumes rayonnantes autour de chaque lentille
            ex = np.where(x > 0, EX, -EX)
            ang = np.degrees(np.arctan2(y - EY, x - ex))
            ray = (np.mod(ang, 15.0) < 4.5) & (de > 0.62)
            cf = lerp(A(BRASS["base"]), A(BRASS["hi"]), np.clip(0.35 + 0.55 * lam, 0, 1)[..., None])
            cf = np.where(ray[..., None], cf * 0.8, cf)
            col = np.where(facial[..., None], cf, col)
            col = np.where(rim[..., None], lerp(A(COPPER["low"]), A(COPPER["base"]), 0.5 * lam[..., None]), col)
        plastron = np.zeros(x.shape, bool)
        if not est_tete:
            plastron = (z < -0.45) & (y < 1.05) & (y > -1.85) & (np.abs(x) < 1.35)
            col = np.where(plastron[..., None], lerp(A(COPPER["low"]), A(COPPER["base"]), (0.25 + 0.5 * lam)[..., None]), col)
        # joints de plaques : horizontaux appuyés (rivetés), verticaux discrets
        hj = np.minimum(d_bas, d_haut)
        joint = ~facial & (hj < 0.07)
        biseau = ~facial & (hj >= 0.07) & (hj < 0.15)
        col = np.where(biseau[..., None], lerp(col, A(BRASS["hi"]), 0.55), col)
        col = np.where(joint[..., None], A(BRASS["low"]) * 0.7, col)
        col = np.where((~facial & (d_cote < 0.045))[..., None], col * 0.72, col)
        # plumes de laiton gravées en écailles (espace monde : les rangées traversent les facettes sans couture)
        if True:
            yy = y / ovo.rv
            lat = np.degrees(np.arcsin(np.clip(yy, -1, 1)))
            phi = np.degrees(np.arctan2(x, -z))
            dl, dp = (13.0, 22.0) if not est_tete else (15.0, 26.0)
            row = np.floor(lat / dl)
            du = np.mod(phi / dp + 0.5 * row, 1.0) - 0.5
            dv = np.mod(lat / dl, 1.0)
            edge = 0.18 + 1.6 * du * du
            zone = ~facial & ~plastron & (np.abs(lat) < (60 if not est_tete else 52))
            if est_tete:
                zone &= ~((z < 0.0) & (np.abs(y - EY) < 1.2))
            ligne = zone & (np.abs(dv - edge) < 0.07)
            ombre = zone & (dv < edge) & (dv > edge - 0.22)
            clair = zone & (dv > edge + 0.07) & (dv < edge + 0.30)
            col = np.where(ombre[..., None], col * 0.86, col)
            col = np.where(clair[..., None], lerp(col, A(BRASS["hi"]), 0.18), col)
            col = np.where(ligne[..., None], A(BRASS["low"]) * 0.85, col)
        # rivets le long du joint du bas
        for fr in (0.25, 0.75):
            a0 = np.array(poly[0]) + (np.array(poly[1]) - np.array(poly[0])) * fr
            a3 = np.array(poly[3]) + (np.array(poly[2]) - np.array(poly[3])) * fr
            q = a0 + (a3 - a0) * min(0.22, 0.26 / max(0.4, np.linalg.norm(a3 - a0)))
            p3 = f["cout"] + f["X"] * q[0] + f["Y"] * q[1]
            if est_tete:
                if min(math.hypot(p3[0] - EX, p3[1] - EY), math.hypot(p3[0] + EX, p3[1] - EY)) < 1.3 and p3[2] < -0.2:
                    continue
            rivet(col, px, py, q[0], q[1], 0.085, BRASS if est_tete else COPPER if (p3[2] < -0.45 and p3[1] < 1.05) else BRASS)
        return finish(col, mask)
    return painter


def peint_calotte(W, H):
    """Calotte octogonale du dessus de la tête (vue du dessus)."""
    r_ = HEAD.P(22.5, HEAD.lats[-1])
    R = math.hypot(r_[0], r_[2]) / math.cos(math.radians(22.5))
    w = 2 * R + 0.1
    px, py = grid(W, H, w, w, SS)
    ang = np.degrees(np.arctan2(py, px))
    rr = np.hypot(px, py) * np.cos(np.radians(np.mod(ang - 22.5, 45.0) - 22.5)) / math.cos(math.radians(22.5))
    mask = down_mask((rr < R * math.cos(math.radians(22.5)) + 0.05).astype(np.float32), W, H)
    px, py = grid(W, H, w, w, 1)
    r = np.hypot(px, py)
    streak = noise(H, W, 10, 31) - 0.5
    col = metal_shade(BRASS, np.clip(0.95 - 0.35 * r / R, 0, 1), streak)
    col = bevel(col, mask, BRASS)
    col[(r > 0.42) & (r < 0.5)] *= 0.6
    for a in range(8):
        aa = math.radians(a * 45 + 22.5)
        rivet(col, px, py, 0.72 * R * math.cos(aa), 0.72 * R * math.sin(aa), 0.085, BRASS)
    return finish(col, mask)


# ------------------------------------------------------------------ pièces découpées par alpha
def peint_metal(w, h, forme, metal, seed, rivets=(), r_riv=0.08, nervure=False, bout=None, patine=0, racine=False, lum=None, extra=None):
    """Plaque de métal : forme(px, py) -> bool en coordonnées modèle (x vers la droite de l'image, y vers le haut)."""
    def painter(W, H):
        gx, gy = grid(W, H, w, h, SS)
        mask = down_mask(forme(gx, gy).astype(np.float32), W, H)
        px, py = grid(W, H, w, h, 1)
        streak = noise(H, W, 12, seed) - 0.5
        l = lum(px, py) if lum else np.clip(0.55 + 0.4 * py / h + 0.1 * px / w, 0, 1)
        col = metal_shade(metal, l, streak)
        if bout is not None:
            x0, tm = bout
            band = px > x0
            col = np.where(band[..., None], metal_shade(tm, l, streak), col)
            col = np.where((band ^ (px > x0 - 0.06))[..., None], A(tm["low"]) * 0.7, col)
        if nervure:
            col = np.where((np.abs(py) < 0.05)[..., None], A(metal["low"]), col)
        # pas de patine (retour du 2026-11-04 : « bugs de texture ») : métal propre, usure au bord et aux rivets seulement
        col = bevel(col, mask, metal)
        if racine:
            col *= (0.55 + 0.45 * smv(px, -w / 2, -w / 2 + 0.6))[..., None]
        e = None
        if extra:
            col, e = extra(col, px, py, mask)
        for (rx, ry) in rivets:
            rivet(col, px, py, rx, ry, r_riv, STEEL if metal is not STEEL else BRASS)
        return finish(col, mask, e)
    return painter


def lame_forme(w, h, k_racine=0.62):
    """Lame : racine plus étroite, bout arrondi en demi-ellipse (pas de pointe fine)."""
    def f(px, py):
        u = (px + w / 2) / w
        hw = h / 2 * (k_racine + (1 - k_racine) * np.clip(u / 0.45, 0, 1))
        tip = px > w / 2 - h / 2
        ell = ((px - (w / 2 - h / 2)) / (h / 2)) ** 2 + (py / (h / 2)) ** 2 < 1
        return (np.abs(py) < hw) & (px > -w / 2) & (~tip | ell)
    return f


def ecaille_forme(w, h):
    def f(px, py):
        top = (py > 0) & (np.abs(px) < w / 2 - 0.02)
        ell = (px / (w / 2)) ** 2 + (py / (h / 2)) ** 2 < 1
        return (top | ell) & (py < h / 2 - 0.02)
    return f


def disque(rout, rin=0.0):
    def f(px, py):
        r = np.hypot(px, py)
        return (r < rout) & (r >= rin)
    return f


def strip(W, H, fn):
    u, v = np.meshgrid((np.arange(W) + 0.5) / W, (np.arange(H) + 0.5) / H)
    c = fn(u, v)
    return finish(c, np.ones(u.shape, bool))


def barre(metal, gorges=3):
    def fn(u, v):
        q = np.abs(v - 0.5) * 2
        c = lerp(A(metal["hi"]) * 0.9, A(metal["low"]), (q ** 1.2)[..., None])
        c = lerp(c, A(metal["base"]), 0.35)
        for k in range(gorges):
            c = np.where((np.abs(u - (k + 0.5) / gorges) < 0.03)[..., None], A(metal["low"]) * 0.8, c)
        return c
    return lambda W, H: strip(W, H, fn)


def plein(metal, k=0.7):
    return lambda W, H: strip(W, H, lambda u, v: lerp(A(metal["low"]), A(metal["base"]), k) * (1 - 0.1 * np.abs(v - 0.5))[..., None])


def bande_carenage(interieur=False):
    def fn(u, v):
        q = np.abs(v - 0.5) * 2
        c = lerp(A(COPPER["hi"]), A(COPPER["low"]), (q ** 1.4)[..., None])
        c = lerp(c, A(COPPER["base"]), 0.4)
        if interieur:
            return c * 0.55
        c = np.where(((v < 0.16) | (v > 0.84))[..., None], A(BRASS["base"]), c)
        c = np.where(((np.abs(v - 0.16) < 0.04) | (np.abs(v - 0.84) < 0.04))[..., None], A(BRASS["low"]) * 0.7, c)
        for x in (0.2, 0.5, 0.8):
            d = np.hypot((u - x) * 4.2, (v - 0.5))
            c = np.where((d < 0.16)[..., None], A(BRASS["low"]) * 0.6, c)
            c = np.where((d < 0.11)[..., None], A(BRASS["hi"]), c)
        return c
    return lambda W, H: strip(W, H, fn)


# ------------------------------------------------------------------ yeux
RING_D, GLASS_D = 1.36, 1.12
LID_TOP, LID_H0 = 0.60, 0.08           # paupière : mince lame logée sous la bague, agrandie par scale y depuis le haut (fermée : x15 ≤ 16)
LID_FERME = 2 * LID_TOP / LID_H0


def peint_bague(W, H):
    R = RING_D / 2
    gx, gy = grid(W, H, RING_D, RING_D, SS)
    mask = down_mask(disque(R, R * 0.80)(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, RING_D, RING_D, 1)
    r = np.hypot(px, py)
    lam = np.clip(0.6 + 0.5 * (py - px) / RING_D, 0, 1)
    col = metal_shade(BRASS, lam, noise(H, W, 10, 401) - 0.5)
    col = np.where((np.abs(r - R * 0.90) < 0.018)[..., None], A(BRASS["low"]) * 0.7, col)
    col = bevel(col, mask, BRASS, joint=False)
    for a in range(6):
        aa = math.radians(a * 60 + 30)
        rivet(col, px, py, R * 0.90 * math.cos(aa), R * 0.90 * math.sin(aa), 0.05, STEEL)
    return finish(col, mask)


def peint_verre(W, H):
    R = GLASS_D / 2
    gx, gy = grid(W, H, GLASS_D, GLASS_D, SS)
    mask = down_mask(disque(R)(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, GLASS_D, GLASS_D, 1)
    r = np.hypot(px, py) / R
    col = lerp(AMBRE_C, AMBRE, smv(r, 0.2, 1.0)[..., None])
    col = lerp(col, A((150, 84, 26)), smv(r, 0.85, 1.0)[..., None])
    hl = np.hypot(px + 0.30, py - 0.30) < 0.09
    col = np.where(hl[..., None], A((255, 246, 220)), col)
    e = lerp(E_AMBRE, E_AMBRE * 0.55, smv(r, 0.3, 1.0)[..., None])
    e = np.where(hl[..., None], A((200, 170, 120)), e)
    return finish(col, mask, e)


def peint_pupille(W, H):
    gx, gy = grid(W, H, 0.5, 0.5, SS)
    mask = down_mask(disque(0.25)(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, 0.5, 0.5, 1)
    col = np.zeros(px.shape + (3,), np.float32) + A((26, 18, 14))
    col = np.where((np.hypot(px, py) > 0.19)[..., None], A((58, 36, 20)), col)
    return finish(col, mask)


def peint_iris(W, H):
    """Iris d'acier : anneau intérieur et 3 crans qui rentrent dans le verre (on voit leur rotation)."""
    R = GLASS_D / 2

    def f(px, py):
        r = np.hypot(px, py)
        a = np.mod(np.degrees(np.arctan2(py, px)), 120.0)
        cran = (np.abs(a - 60) < 9) & (r > 0.33)
        return (r < R) & ((r > 0.47) | cran)
    gx, gy = grid(W, H, GLASS_D, GLASS_D, SS)
    mask = down_mask(f(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, GLASS_D, GLASS_D, 1)
    lam = np.clip(0.55 + 0.6 * (py - px) / GLASS_D, 0, 1)
    col = metal_shade(STEEL, lam, noise(H, W, 8, 402) - 0.5)
    col = bevel(col, mask, STEEL, joint=False)
    return finish(col, mask)


def peint_paupiere(W, H):
    """Volet de laiton : peint pour la taille fermée (le scale y l'étire depuis la lame logée sous la bague)."""
    R = GLASS_D / 2 + 0.02
    gx, gy = grid(W, H, 2 * R, 2 * R, SS)
    mask = down_mask(disque(R)(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, 2 * R, 2 * R, 1)
    col = metal_shade(BRASS, np.clip(0.75 + 0.3 * py, 0, 1), noise(H, W, 8, 403) - 0.5)
    for k in range(-2, 3):
        col = np.where((np.abs(py - k * 0.25 - 0.12) < 0.025)[..., None], A(BRASS["low"]) * 0.75, col)
    col = bevel(col, mask, BRASS, joint=False)
    return finish(col, mask)


# ------------------------------------------------------------------ clé, hélice, vapeur
KEY_W, KEY_H = 2.3, 1.15


def cle_forme(px, py):
    lob = np.zeros(px.shape, bool)
    for s in (-1, 1):
        d = np.hypot((px - s * 0.62) / 0.53, py / 0.55)
        trou = np.hypot((px - s * 0.66) / 0.22, py / 0.22) < 1
        lob |= (d < 1) & ~trou
    centre = (np.abs(px) < 0.32) & (np.abs(py) < 0.30)
    return lob | centre


def peint_cle(W, H):
    def extra(col, px, py, mask):
        col = np.where((np.hypot(px, py) < 0.17)[..., None], A(BRASS["low"]) * 0.8, col)
        return col, None
    return peint_metal(KEY_W, KEY_H, cle_forme, BRASS, 501, rivets=[(0.0, 0.0)], r_riv=0.1, patine=0,
                       lum=lambda px, py: np.clip(0.6 + 0.45 * py - 0.1 * px, 0, 1), extra=extra)(W, H)


PROP_D = 3.2          # hélice déployée ; construite à PROP_K (repliée dans le dôme) et agrandie par scale
PROP_K = 0.2


def peint_helice(W, H):
    R = PROP_D / 2

    def f(px, py):
        r = np.hypot(px, py)
        a = np.degrees(np.arctan2(py, px))
        pale = np.zeros(px.shape, bool)
        for k in range(3):
            da = (a - k * 120 - 12 * (r / R) + 180) % 360 - 180            # pales légèrement vrillées
            pale |= np.abs(da) < (14 + 18 * np.sin(np.clip(r / R, 0, 1) * math.pi) ** 0.8)
        return ((r < R) & pale & (r > 0.16)) | (r < 0.3)
    gx, gy = grid(W, H, PROP_D, PROP_D, SS)
    mask = down_mask(f(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, PROP_D, PROP_D, 1)
    r = np.hypot(px, py)
    col = metal_shade(STEEL, np.clip(0.4 + 0.5 * r / R, 0, 1), noise(H, W, 8, 502) - 0.5)
    col = np.where((r < 0.3)[..., None], metal_shade(BRASS, np.full(r.shape, 0.7), np.zeros(r.shape)), col)
    col = bevel(col, mask, STEEL, joint=False)
    return finish(col, mask)


VAP_W, VAP_H = 1.3, 1.8


def peint_vapeur(W, H):
    """Bouffée : bosses à bord net, opacité qui décroît vers le haut (trans_ ; la moitié opaque se lit en cutout)."""
    px, py = grid(W, H, VAP_W, VAP_H, 1)
    u, v = px / VAP_W + 0.5, py / VAP_H + 0.5
    dens = np.zeros(px.shape, np.float32)
    light = np.zeros(px.shape, np.float32)
    for x, y, r in ((0.5, 0.20, 0.20), (0.36, 0.40, 0.22), (0.64, 0.46, 0.21), (0.48, 0.64, 0.24), (0.58, 0.84, 0.15), (0.32, 0.78, 0.13)):
        d = np.hypot((u - x) * VAP_W, (v - y) * VAP_H) / (r * VAP_W)
        dens = np.maximum(dens, np.clip(1.6 * (1 - d), 0, 1))
        light = np.maximum(light, np.clip(1 - np.hypot((u - x + 0.25 * r) * VAP_W, (v - y - 0.3 * r) * VAP_H) / (r * VAP_W), 0, 1))
    alpha = np.clip(dens, 0, 1) * lerp(1.0, 0.25, smv(v, 0.15, 1.0))
    alpha = np.where(alpha < 0.08, 0.0, alpha)
    col = np.zeros(px.shape + (3,), np.float32) + A((214, 220, 226))
    col = np.where((light > 0.2)[..., None], A((236, 240, 244)), col)
    col = np.where((light > 0.5)[..., None], A((250, 250, 248)), col)
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = col.astype(np.uint8)
    out[..., 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    return out, np.zeros((H, W, 4), np.uint8)


# ------------------------------------------------------------------ atlas
TILES = {}


def tile(name, w, h, painter, fixed=False):
    TILES[name] = (w, h, painter, fixed)


for ovo in (BODY, HEAD):
    for f in ovo.facets:
        tile(f["name"], f["w"], f["h"], peint_facette(ovo, f))
_cr = HEAD.P(22.5, HEAD.lats[-1])
CAP_R = math.hypot(_cr[0], _cr[2]) / math.cos(math.radians(22.5))
tile("calotte", 2 * CAP_R + 0.1, 2 * CAP_R + 0.1, peint_calotte)
tile("bague", RING_D, RING_D, peint_bague)
tile("verre", GLASS_D, GLASS_D, peint_verre)
tile("pupille", 0.5, 0.5, peint_pupille)
tile("iris", GLASS_D, GLASS_D, peint_iris)
tile("paupiere", GLASS_D + 0.04, GLASS_D + 0.04, peint_paupiere)
ECW, ECH = 0.92, 1.0
tile("ecaille_a", ECW, ECH, peint_metal(ECW, ECH, ecaille_forme(ECW, ECH), COPPER, 301, rivets=[(0, 0.3)], r_riv=0.07, nervure=False, patine=0,
                                         lum=lambda px, py: np.clip(0.35 + 0.65 * (0.5 - py), 0, 1)))
tile("ecaille_b", ECW, ECH, peint_metal(ECW, ECH, ecaille_forme(ECW, ECH), COPPER, 302, rivets=[(0, 0.3)], r_riv=0.07, patine=0,
                                         lum=lambda px, py: np.clip(0.30 + 0.7 * (0.5 - py), 0, 1)))
WINGS = [(2.4, 1.3, 6.0), (2.15, 1.15, 27.0), (1.85, 1.0, 48.0)]       # longueur, largeur, angle d'éventail (vers l'arrière)
for i, (Lb, Wb, _) in enumerate(WINGS):
    tile(f"lame{i}", Lb, Wb, peint_metal(Lb, Wb, lame_forme(Lb, Wb), BRASS if i != 1 else COPPER, 311 + i,
                                         rivets=[(-Lb / 2 + 0.3, 0.0), (-Lb / 2 + 0.75, 0.0)], nervure=True, bout=(Lb / 2 - 0.55, COPPER if i != 1 else BRASS),
                                         racine=True, patine=0))
TAILS = [(1.5, 0.62, -26.0), (1.8, 0.7, 0.0), (1.5, 0.62, 26.0)]
tile("queue_c", 1.8, 0.7, peint_metal(1.8, 0.7, lame_forme(1.8, 0.7), BRASS, 321, rivets=[(-0.55, 0)], nervure=True, bout=(0.45, COPPER), racine=True))
tile("queue_s", 1.5, 0.62, peint_metal(1.5, 0.62, lame_forme(1.5, 0.62), COPPER, 322, rivets=[(-0.45, 0)], nervure=True, bout=(0.3, BRASS), racine=True))
TUFTS = [(1.45, 0.52), (1.05, 0.44)]
for i, (Lt, Wt) in enumerate(TUFTS):
    tile(f"aigrette{i}", Lt, Wt, peint_metal(Lt, Wt, lame_forme(Lt, Wt, 0.75), BRASS, 331 + i, nervure=True, bout=(Lt / 2 - 0.35, COPPER), racine=True, patine=0))
tile("moyeu", 1.0, 1.0, peint_metal(1.0, 1.0, lambda px, py: (np.hypot(px, py) < 0.48) & ((np.hypot(px, py) < 0.36) | (np.mod(np.degrees(np.arctan2(py, px)), 45) < 24)),
                                    BRASS, 341, rivets=[(0, 0)], r_riv=0.1, patine=0, lum=lambda px, py: np.clip(0.6 + 0.5 * (py - px), 0, 1)))
tile("bec", 0.56, 0.78, peint_metal(0.56, 0.78, lambda px, py: (np.abs(px) < 0.27 * np.clip((py + 0.40) / 0.55, 0.12, 1.0)) & (py < 0.37),
                                    STEEL, 351, patine=0.0, lum=lambda px, py: np.clip(0.75 + 0.3 * py - 0.4 * np.abs(px), 0, 1)))
tile("collier", 0.9, 0.9, peint_metal(0.9, 0.9, disque(0.44), COPPER, 361, rivets=[(0.27, 0), (-0.27, 0), (0, 0.27), (0, -0.27)], r_riv=0.06, patine=0))
tile("cle", KEY_W, KEY_H, peint_cle)
tile("helice", PROP_D, PROP_D, peint_helice)
tile("vapeur", VAP_W, VAP_H, peint_vapeur)
HUB_D = 0.95


def peint_hublot(W, H):
    """Hublot du foyer : bague de laiton, grille de 3 barreaux, braises derrière (calque _e vif, petite surface)."""
    R_ = HUB_D / 2
    gx, gy = grid(W, H, HUB_D, HUB_D, SS)
    mask = down_mask(disque(R_)(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, HUB_D, HUB_D, 1)
    r = np.hypot(px, py)
    rng_ = np.random.default_rng(77)
    braise = noise(H, W, 6, 78)
    col = lerp(A((70, 22, 8)), A((235, 120, 36)), np.clip(braise * 1.3 - 0.15 + 0.3 * smv(-py, -0.3, 0.3), 0, 1)[..., None])
    e = lerp(A((120, 40, 10)), A((220, 150, 60)), np.clip(braise * 1.4 - 0.2 + 0.3 * smv(-py, -0.3, 0.3), 0, 1)[..., None])
    barreau = (np.abs(np.abs(px) - 0.15) < 0.035) | (np.abs(px) < 0.035)
    anneau = r > R_ * 0.74
    col = np.where(barreau[..., None], metal_shade(BRASS, np.clip(0.6 + py, 0, 1), np.zeros(r.shape)), col)
    col = np.where(anneau[..., None], metal_shade(BRASS, np.clip(0.55 + 0.6 * py, 0, 1), noise(H, W, 6, 79) - 0.5), col)
    col = np.where((np.abs(r - R_ * 0.74) < 0.03)[..., None], A(BRASS["low"]) * 0.6, col)
    col = bevel(col, mask, BRASS, joint=False)
    e = np.where((barreau | anneau | (r > R_ * 0.70))[..., None], 0.0, e)
    for a in range(6):
        aa = math.radians(a * 60)
        rivet(col, px, py, R_ * 0.87 * math.cos(aa), R_ * 0.87 * math.sin(aa), 0.045, STEEL)
    return finish(col, mask, e)


def peint_lampe(W, H):
    """Lampe de pression : verre ambre bombé dans une cage (calque _e vif, petite surface)."""
    px, py = grid(W, H, 0.42, 0.42, 1)
    r = np.hypot(px, py) / 0.21
    col = lerp(A((255, 226, 150)), A((214, 120, 36)), smv(r, 0.1, 1.0)[..., None])
    e = lerp(A((230, 190, 110)), A((170, 90, 24)), smv(r, 0.1, 1.0)[..., None])
    cage = (np.abs(px) < 0.025) | (np.abs(py) < 0.025) | (r > 0.86)
    col = np.where(cage[..., None], A(BRASS["low"]), col)
    e = np.where(cage[..., None], 0.0, e)
    return finish(col, np.ones(px.shape, bool), e)


tile("hublot", HUB_D, HUB_D, peint_hublot)
tile("lampe", 0.42, 0.42, peint_lampe)
tile("bar_laiton", 48, 12, barre(BRASS), fixed=True)
tile("bar_acier", 48, 12, barre(STEEL, 4), fixed=True)
tile("bar_cuivre", 48, 12, barre(COPPER, 2), fixed=True)
tile("ame", 12, 12, plein(BRASS, 0.55), fixed=True)
tile("ame_acier", 12, 12, plein(STEEL, 0.8), fixed=True)
tile("chapeau", 16, 16, lambda W, H: strip(W, H, lambda u, v: lerp(A(BRASS["hi"]), A(BRASS["low"]), np.clip(np.hypot(u - 0.4, v - 0.4) * 1.6, 0, 1)[..., None])), fixed=True)
tile("tube_fond", 12, 12, plein(STEEL, 0.2), fixed=True)
tile("bar_sombre", 48, 12, barre(dict(hi=(96, 98, 108), base=(52, 54, 62), low=(24, 25, 30)), 3), fixed=True)


# ------------------------------------------------------------------ disque facial, sourcils, collier denté
LOBE_R, LOBE_TROU = 1.02, 0.66


def peint_lobe(f, interieur_x, signe):
    """Coupelle du disque facial autour d'une lentille, dans le plan de sa facette : plumes de laiton rayonnantes,
    plus sombres vers l'oeil (creux), liseré de cuivre au bord ; coupée au bord intérieur (arête du bec)."""
    w = 2 * LOBE_R

    def forme(px, py):
        r = np.hypot(px, py)
        return (r < LOBE_R) & (r > LOBE_TROU) & (signe * (px - interieur_x) < -0.03) & (py > -0.82)

    def painter(W, H):
        gx, gy = grid(W, H, w, w, SS)
        mask = down_mask(forme(gx, gy).astype(np.float32), W, H)
        px, py = grid(W, H, w, w, 1)
        r = np.hypot(px, py)
        ang = np.degrees(np.arctan2(py, px))
        k = smv(r, LOBE_TROU, LOBE_R * 0.92)
        lam = np.clip(0.35 + 0.6 * k + 0.15 * py / LOBE_R, 0, 1)
        col = metal_shade(BRASS, lam, noise(H, W, 10, 611 + (signe > 0)) - 0.5)
        plume = np.mod(ang + 7.5 * np.floor(r / 0.12), 15.0)
        col = np.where(((plume < 1.6) & (r > LOBE_TROU + 0.06))[..., None], col * 0.72, col)
        col = np.where((r > LOBE_R - 0.14)[..., None], lerp(A(COPPER["low"]), A(COPPER["base"]), (0.4 + 0.5 * lam)[..., None]), col)
        col = np.where((np.abs(r - (LOBE_R - 0.15)) < 0.025)[..., None], A(COPPER["low"]) * 0.6, col)
        col = np.where((r < LOBE_TROU + 0.07)[..., None], A(BRASS["low"]) * 0.55, col)
        return finish(col, mask)
    return painter


SRC_W, SRC_H = 0.95, 0.34


def sourcil_forme(px, py):
    """Sourcil en lame courbe : plus épais côté bec (x < 0), bout arrondi côté tempe."""
    u = (px + SRC_W / 2) / SRC_W
    c = 0.10 * np.sin(u * math.pi)
    hw = SRC_H / 2 * (1.0 - 0.45 * u)
    return (np.abs(py - c) < hw) & (u > 0) & (u < 1) & (np.hypot((px - SRC_W / 2 + 0.12) / 0.12, (py - c) / max(1e-3, SRC_H * 0.3)) < 1.4 + 9 * (u < 0.85))


LOBES = {}
for tag, gore in (("r", 0), ("l", 7)):
    f = HEAD.facet(1, gore)
    mid = (HEAD.lats[1] + HEAD.lats[2]) / 2
    ix = float((HEAD.P(0.0, mid) - f["cout"]) @ f["X"])
    LOBES[tag] = dict(f=f)
    tile(f"lobe_{tag}", 2 * LOBE_R, 2 * LOBE_R, peint_lobe(f, ix, 1.0 if ix > 0 else -1.0))
tile("sourcil", SRC_W, SRC_H, peint_metal(SRC_W, SRC_H, sourcil_forme, COPPER, 621, nervure=True,
                                         lum=lambda px, py: np.clip(0.65 + 0.8 * py, 0, 1)))
tile("sourcil_m", SRC_W, SRC_H, peint_metal(SRC_W, SRC_H, lambda px, py: sourcil_forme(-px, py), COPPER, 622, nervure=True,
                                           lum=lambda px, py: np.clip(0.65 + 0.8 * py, 0, 1)))
GEAR_R, GEAR_N = 1.42, 12


def gear_forme(px, py):
    r = np.hypot(px, py)
    a = np.mod(np.degrees(np.arctan2(py, px)) * GEAR_N / 360.0, 1.0)
    dent = np.abs(a - 0.5) < 0.26
    return (r < GEAR_R - 0.22) | ((r < GEAR_R) & dent)


tile("engrenage", 2 * GEAR_R, 2 * GEAR_R, peint_metal(2 * GEAR_R, 2 * GEAR_R, gear_forme, STEEL, 631,
                                                    lum=lambda px, py: np.clip(0.5 + 0.35 * np.hypot(px, py) / GEAR_R + 0.15 * (py - px) / GEAR_R, 0, 1)))

UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def atlas():
    def pack(dens):
        items = [(n, w, h) if fx else (n, int(math.ceil(w * dens)), int(math.ceil(h * dens))) for n, (w, h, _, fx) in TILES.items()]
        items.sort(key=lambda it: -it[2])
        uv, x, y, shelf = {}, 0, 0, 0
        for n, w, h in items:
            if x + w + 1 > TEX:
                x, y, shelf = 0, y + shelf + 1, 0
            if y + h > TEX - 6:
                return None
            uv[n] = (x, y, x + w, y + h)
            x += w + 1
            shelf = max(shelf, h)
        return uv

    dens = 56.0
    while (uv := pack(dens)) is None:
        dens -= 0.5
    UV.update(uv)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, (w, h, painter, fx) in TILES.items():
        u0, v0, u1, v1 = UV[n]
        im, ie = painter(u1 - u0, v1 - v0)
        tex[v0:v1, u0:u1] = im
        tex_e[v0:v1, u0:u1] = ie
    assert tex[TEX - 3, TEX - 3, 3] == 0
    tex[..., :3] &= 0xFE
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    u0, v0, u1, v1 = UV["vapeur"]
    semi[v0:v1, u0:u1] = False
    assert not semi.any() and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence hors de la vapeur (trans_)"
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
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx (ordre du mod et du renderer)."""
    sy = -R[2, 0]
    if abs(sy) > 0.99999:
        ry = math.copysign(math.pi / 2, sy)
        ang = (math.degrees(math.atan2(R[0, 1], R[0, 2])) if sy > 0 else math.degrees(math.atan2(-R[0, 1], -R[0, 2]))), math.degrees(ry), 0.0
    else:
        ang = math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(math.asin(sy)), math.degrees(math.atan2(R[1, 0], R[0, 0]))
    assert np.allclose(rot_matrix(*ang), R, atol=1e-4), "euler : reconstruction fausse"
    return ang


def group(name, origin, parent=None, rotation=(0, 0, 0), uniq=None):
    """uniq : plusieurs groupes de même nom (emit_mc_, ctrl_) ; la clé interne est alors « nom#uniq »."""
    key = name if uniq is None else f"{name}#{uniq}"
    assert key not in groups
    groups[key] = {"name": name, "origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [round(float(v), 2) for v in rotation]}
    return key


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def plate(g, name, c, X, Y, tilename, w, h, th=TH, side="s", tranche=None):
    """Plaque fine (coordonnées absolues du modèle) : contour par l'alpha, tranches transparentes.
    side : 's' face X x Y seule, 'n' face opposée seule, 'b' les deux. tranche : tuile des faces up/down (rebord visible)."""
    X = unit(X)
    Y = unit(np.asarray(Y, float) - (np.asarray(Y, float) @ X) * X)
    u0, v0, u1, v1 = UV[tilename]
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    south = [u0, v0, u1, v1] if side in "sb" else CLEAR
    north = [u1, v0, u0, v1] if side in "nb" else CLEAR
    ud = list(UV[tranche]) if tranche else CLEAR
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": south, "north": north, "east": CLEAR, "west": CLEAR, "up": ud, "down": ud})


def frame_from_axis(X):
    ref = V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0)
    Y = unit(ref - (ref @ X) * X)
    return Y, np.cross(X, Y)


def bar(g, name, p, q, r, tilename, octo=True, ov=0.04, bouts=None):
    """Tronçon plein de section octogonale (deux cubes à 45°) ou carrée, de p à q (coordonnées absolues)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    Ln = np.linalg.norm(q - p)
    X = unit(q - p)
    Y, Z_ = frame_from_axis(X)
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R0 = np.column_stack([X, Y, Z_])
    R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
    lg = list(UV[tilename])
    end = list(UV[bouts]) if bouts else [lg[0], lg[1], lg[0] + 6, lg[3]]
    faces = {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}
    cube(g, name, p + (-ov, -r, -r), p + (Ln + ov, r, r), p, euler(R0), faces)
    if octo:
        cube(g, name + "o", p + (-ov + 0.12, -r * 0.97, -r * 0.97), p + (Ln + ov - 0.12, r * 0.97, r * 0.97), p, euler(R45), faces)


def bloc(g, name, c, size, R_, tilename, faces_tile=None):
    """Cube plein orienté (repère R_ en colonnes), même tuile sur les 6 faces."""
    c = np.asarray(c, float)
    hs = np.asarray(size, float) / 2
    t = list(UV[tilename])
    faces = {f: t for f in ("north", "south", "east", "west", "up", "down")}
    if faces_tile:
        faces.update({k: (list(UV[v]) if v else CLEAR) for k, v in faces_tile.items()})
    cube(g, name, c - hs, c + hs, c, euler(R_), faces)


def prisme_y(g, name, cy, y0, y1, a, tilename, top=None, bottom=None):
    """Prisme octogonal vertical (deux cubes, 0° et 45°), centré sur l'axe du corps."""
    for i, (k, ang) in enumerate(((1.0, 0.0), (0.97, 45.0))):
        d = 0.12 * i
        faces = {f: list(UV[tilename]) for f in ("north", "south", "east", "west")}
        faces["up"] = list(UV[top]) if top else list(UV[tilename])
        faces["down"] = list(UV[bottom]) if bottom else list(UV[tilename])
        c = cy + V(0, (y0 + y1) / 2, 0)
        cube(g, f"{name}{'o' if i else ''}", cy + V(-a * k, y0 + d, -a * k), cy + V(a * k, y1 - d, a * k), c, (0, ang, 0), faces)


def ame_max(ovo, y0, y1, marge=0.06):
    def ok(a):
        for ang in (0.0, 45.0):
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            for sx in (-a, a):
                for sz in (-a, a):
                    for yy in (y0, y1):
                        q = V(sx * ca + sz * sa, yy, -sx * sa + sz * ca)
                        if max(f["n"] @ q - f["n"] @ f["cout"] for f in ovo.facets) > -marge:
                            return False
        return True
    a = 0.2
    while ok(a + 0.02):
        a += 0.02
    return a


def bone_node(name):
    g = groups[name]
    return {"name": g["name"], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


HC = C0 + V(0, HY, 0)          # centre de la tête (absolu)
NECK = C0 + V(0, NECK_Y, 0)

# ---------------------------------------------------------------- hiérarchie (body = torse du joueur)
g_racine = group("fam_racine", [0, 24, 0])                   # rotation Y autour de l'axe du joueur : petit vol (idle)
g_vol = group("fam_vol", P0, parent=g_racine)                 # position/rotation d'état : décollage, contre-rotation
g_elan = group("fam_elan", P0, parent=g_vol)                  # événements, attaque, blessure : position
g_cap = group("fam_cap", C0, parent=g_elan)                   # cap en vol (idle : garde le regard vers l'avant)
g_vir = group("fam_virage", P0, parent=g_cap)                 # couche permanente : virages, vie basse, pluie
g_snap = group("fam_snap", P0, parent=g_vir)                  # idle (hasard) + attaque/blessure : rotation autour des serres
g_corps = group("corps", C0, parent=g_snap)

# --- corps : peaux, âmes, plastron d'écailles
for f in BODY.facets:
    plate(g_corps, f["name"], C0 + f["cout"] - f["n"] * TH / 2, f["X"], f["Y"], f["name"], f["w"], f["h"])
prisme_y(g_corps, "ame_c1", C0, -1.20, -0.62, ame_max(BODY, -1.20, -0.62), "ame")
prisme_y(g_corps, "ame_c2", C0, -0.50, 1.00, ame_max(BODY, -0.50, 1.00), "ame")
SCALES = [(16.0, (-20.0, 20.0), 0.20, 0.92), (0.0, (-36.0, 0.0, 36.0), 0.14, 0.92), (-18.0, (-36.0, 0.0, 36.0), 0.09, 0.88), (-35.0, (-19.0, 19.0), 0.05, 0.8)]
for r_, (lat, phis, off, k) in enumerate(SCALES):
    for i, phi in enumerate(phis):
        p = BODY.P(phi, lat)
        n = unit(BODY.normal(p))
        T = unit(V(0, 1, 0) - (V(0, 1, 0) @ n) * n)
        T = unit(T - n * 0.22)                        # le bas de l'écaille se soulève : on lit le recouvrement
        X = np.cross(T, n)
        nn = np.cross(X, T)
        plate(g_corps, f"ecaille_{r_}_{i}", C0 + p + nn * (off + 0.15) - T * 0.18, X, T, "ecaille_a" if (r_ + i) % 2 else "ecaille_b", ECW * k, ECH * k, th=0.3)

# foyer : hublot à grille au bas du ventre, entre les cuisses ; sa lumière suit l'effort (vol, remontage)
g_foyer = group("foyer", C0, parent=g_corps)
g_ctrl_l = group("ctrl_lumiere", C0, parent=g_foyer, uniq="foyer")
_ph = BODY.P(0.0, -50.0)
_nh = unit(BODY.normal(_ph))
_Th = unit(V(0, 1, 0) - (V(0, 1, 0) @ _nh) * _nh)
plate(g_foyer, "hublot", C0 + _ph + _nh * 0.08, np.cross(_Th, _nh), _Th, "hublot", HUB_D * 0.72, HUB_D * 0.72, th=0.24, side="s")
# voyant de pression au dos, au-dessus de la clé : la lumière se voit aussi de dos
_pl = BODY.P(180.0, 24.0)
bloc(g_foyer, "voyant", C0 + _pl + V(0, 0, 0.12), (0.42, 0.42, 0.34), np.eye(3), "bar_laiton", {"south": "lampe", "north": None})

# --- pattes : cuisses emplumées (cuivre), tarses d'acier, serres qui agrippent le dessus de l'épaule
FOOT_Y = 24.42
PATTES = {}
for s, tag in ((1, "r"), (-1, "l")):
    F = V(C0[0] + s * 0.48, FOOT_Y, C0[2])
    bar(g_corps, f"cuisse_{tag}", C0 + V(s * 0.50, -1.36, 0.05), C0 + V(s * 0.47, -1.70, 0.0), 0.34, "bar_cuivre", bouts="ame")
    bar(g_snap, f"tarse_{tag}", F + V(0, 0.80, 0), F + V(0, 0.25, 0), 0.13, "bar_acier", octo=False)
    g_p = group(f"patte_{tag}", F, parent=g_snap)
    PATTES[tag] = g_p
    bloc(g_p, f"cheville_{tag}", F + V(0, 0.18, 0), (0.46, 0.30, 0.46), np.eye(3), "bar_acier")
    doigts = [(V(0.22, 0, -0.7), V(0, -0.08, -0.2)), (V(-0.22, 0, -0.7), V(0, -0.08, -0.2)), (V(0, 0, 0.58), V(0, -0.08, 0.18))]
    for j, (d, griffe) in enumerate(doigts):
        u_ = unit(d)
        bar(g_p, f"doigt_{tag}{j}", F + u_ * (0.38 if j < 2 else 0.34), F + d, 0.09, "bar_acier", octo=False, ov=0.0)
        bar(g_p, f"griffe_{tag}{j}", F + d + u_ * 0.2, F + d + u_ * 0.2 + griffe, 0.065, "bar_sombre", octo=False, ov=0.0)
    if s < 0:      # pied extérieur, au bord de l'épaule : un crochet passe par-dessus le bord et descend le long du bras
        g_d = group("crochet_l", F, parent=g_p)         # replié à l'horizontale quand il n'agrippe pas le bord
        bar(g_d, "crochet_doigt", F + V(-0.12, 0, 0), F + V(-0.3, -0.3, 0), 0.085, "bar_acier", octo=False, ov=0.0)
        bar(g_d, "crochet_griffe", F + V(-0.31, -0.40, 0), F + V(-0.33, -0.74, 0), 0.065, "bar_sombre", octo=False, ov=0.0)
G_CROCHET = "crochet_l"

# --- clé de remontage au dos (tics d'échappement dans les états, remontage rapide au hasard)
KEY0 = C0 + V(0, 0.1, 1.62)
g_k = group("cle", KEY0, parent=g_corps)
g_kr = group("cle_remonte", KEY0, parent=g_k)
plate(g_kr, "cle_collier", KEY0 + V(0, 0, 0.12), V(1, 0, 0), V(0, 1, 0), "collier", 0.8, 0.8, th=0.2, side="s")
KZ = KEY0 + V(0, 0, 1.18)
bar(g_kr, "cle_tige", KEY0 - V(0, 0, 0.2), KZ - V(0, 0, 0.52), 0.15, "bar_acier", octo=False, ov=0.0)
Rk = np.column_stack([V(0, 1, 0), V(0, 0, 1), V(1, 0, 0)])
plate(g_kr, "cle_anneau", KZ, Rk[:, 0], Rk[:, 1], "cle", KEY_W * 0.85, KEY_H * 0.85, th=0.22, side="b")
bloc(g_kr, "cle_ame", KZ, (0.55, 0.47, 0.68), Rk, "bar_laiton")
bloc(g_kr, "cle_barre", KZ, (1.75, 0.18, 0.44), Rk, "bar_laiton")

# --- ailes repliées : 3 lames par aile (éventail), moyeu à l'épaule. L'aile intérieure (droite, côté tête du joueur)
# ne s'ouvre jamais sur le côté : elle se lève vers l'arrière.
WINGG = {}
for s, tag in ((1, "r"), (-1, "l")):
    SH = C0 + V(s * 1.10, 0.8, 0.3)
    g_w = group(f"aile_{tag}", SH, parent=g_corps, rotation=(0, 0, s * 9.0))
    WINGG[tag] = [g_w]
    Rt = np.eye(3)
    for i, (Lb, Wb, fan) in enumerate(WINGS):
        g_l = group(f"lame_{tag}{i}", SH, parent=g_w)
        WINGG[tag].append(g_l)
        R_ = Rt @ rot_matrix(-fan, 0, 0)
        d = R_ @ V(0, -1, 0)
        Y_ = -(R_ @ V(0, 0, 1))
        n = np.cross(d, Y_)
        if n @ V(s, 0, 0) < 0:
            n = -n
        off = 0.15 + 0.2 * (len(WINGS) - 1 - i)      # recette validée : plaques de 0,3 au pas de 0,2, faces à 0,1
        plate(g_l, f"lame_{tag}{i}", SH + d * (Lb / 2 - 0.25) + n * off, d, Y_, f"lame{i}", Lb, Wb, th=0.3, side="b")
        bloc(g_l, f"lame_{tag}{i}_n", SH + d * (Lb * 0.42 - 0.25) + n * off, (Lb * 0.7, 0.16, 0.16), np.column_stack([d, Y_, np.cross(d, Y_)]), "bar_laiton",
             {"north": None, "south": None})
    plate(g_w, f"moyeu_{tag}", SH + V(s, 0, 0) * 0.88, V(0, 0, -s), V(0, 1, 0), "moyeu", 0.86, 0.86, th=0.16, side="b")

# --- queue courte en éventail (hibou)
TQ = C0 + V(0, -1.15, 1.25)
d0 = unit(V(0, -0.45, 1.0))
nt = unit(np.cross(d0, V(1, 0, 0)))
g_q = group("queue", TQ, parent=g_corps)
for i, (Lq, Wq, ang) in enumerate(TAILS):
    d = rodrigues(d0, nt, ang)
    Y_ = np.cross(nt, d)
    off = (0.0, 0.4, 0.2)[i]
    plate(g_q, f"queue{i}", TQ + d * (Lq / 2 - 0.2) + nt * off, d, Y_, "queue_c" if i == 1 else "queue_s", Lq, Wq, th=0.3, side="b")
    bloc(g_q, f"queue{i}_n", TQ + d * (Lq * 0.4 - 0.2) + nt * off, (Lq * 0.62, 0.15, 0.14), np.column_stack([d, Y_, nt]), "bar_laiton", {"north": None, "south": None})

# --- tête : suivi du regard (couche permanente) > tête d'état > tête des comportements au hasard
g_suivi = group("tete_suivi", NECK, parent=g_corps)
g_tete0 = group("tete", NECK, parent=g_suivi)
g_tete = group("tete_hasard", NECK, parent=g_tete0)
for f in HEAD.facets:
    plate(g_tete, f["name"], HC + f["cout"] - f["n"] * TH / 2, f["X"], f["Y"], f["name"], f["w"], f["h"])
Y_CAP = HEAD.P(0, HEAD.lats[-1])[1]
plate(g_tete, "calotte", HC + V(0, Y_CAP - 0.1, 0), V(1, 0, 0), V(0, 0, -1), "calotte", 2 * CAP_R + 0.1, 2 * CAP_R + 0.1, th=0.2, side="s")
prisme_y(g_tete, "ame_t", HC, -0.75, 0.72, ame_max(HEAD, -0.75, 0.72), "ame")
# collier denté du cou : la tête tourne sur une couronne (on voit les dents passer quand elle pivote)
plate(g_tete, "collier_dente", NECK, V(1, 0, 0), V(0, 0, -1), "engrenage", 2 * GEAR_R, 2 * GEAR_R, th=0.2, side="b")

# bec crochu, enfoui entre les coupelles du disque facial
BEC = HC + V(0, EY - 0.52, -1.98)
Rb = rot_matrix(-16, 180, 0)
plate(g_tete, "bec", BEC, Rb[:, 0], Rb[:, 1], "bec", 0.5, 0.7, th=0.3, side="s")
bloc(g_tete, "bec_ame", BEC + V(0, 0.08, 0.24), (0.28, 0.46, 0.36), rot_matrix(-16, 0, 0), "bar_acier")

# disque facial : deux coupelles (une par lentille) dans le plan de leur facette, et sourcils mobiles
SOURCILS = {}
for tag, L_ in LOBES.items():
    f = L_["f"]
    E = HC + f["cout"]
    plate(g_tete, f"disque_{tag}", E + f["n"] * 0.2, f["X"], f["Y"], f"lobe_{tag}", 2 * LOBE_R, 2 * LOBE_R, th=0.15, side="s")
    ix = float((HEAD.P(0.0, 6.0) - f["cout"]) @ f["X"])
    si = 1.0 if ix > 0 else -1.0
    centre_s = E + f["X"] * (si * 0.12) + f["Y"] * 0.70 + f["n"] * 0.42
    Rs = np.column_stack([f["X"], f["Y"], f["n"]]) @ rot_matrix(0, 0, -14 * si)
    g_s = group(f"sourcil_{tag}", centre_s, parent=g_tete, rotation=euler(Rs))
    plate(g_s, f"sourcil_{tag}", centre_s, V(1, 0, 0), V(0, 1, 0), "sourcil_m" if si > 0 else "sourcil", SRC_W, SRC_H, th=0.14, side="s")
    SOURCILS[tag] = (g_s, si)

# yeux : groupe tourné pour que son -Z local soit l'axe de la lentille ; couches à 0,12 px (faces visibles ≥ 0,1)
EYEG = {}
for tag, ey in EYES.items():
    E = HC + ey["c"]
    Zl = -ey["axe"]
    Xl = unit(np.cross(V(0, 1, 0), Zl))
    Yl = np.cross(Zl, Xl)
    g_e = group(f"oeil_{tag}", E, parent=g_tete, rotation=euler(np.column_stack([Xl, Yl, Zl])))
    g_el = group("ctrl_lumiere", E, parent=g_e, uniq=f"oeil_{tag}")
    R_av = rot_matrix(0, 180, 0)
    Xf, Yf = R_av[:, 0], R_av[:, 1]
    a = 0.50
    for i, (k, ang) in enumerate(((1.0, 0.0), (0.97, 45.0))):
        side = list(UV["bar_acier"])
        cube(g_e, f"tube_{tag}{'o' if i else ''}", E + V(-a * k, -a * k, -0.58 + 0.03 * i), E + V(a * k, a * k, 0.40 - 0.03 * i), E, (0, 0, ang),
             {"north": CLEAR, "south": CLEAR, "east": side, "west": side, "up": side, "down": side})
    plate(g_e, f"verre_{tag}", E, Xf, Yf, "verre", GLASS_D, GLASS_D, th=0.2, side="s")
    gp = group(f"pupille_{tag}", E + V(0, 0, -0.19), parent=g_e)
    plate(gp, f"pupille_{tag}", E + V(0, 0, -0.19), Xf, Yf, "pupille", 0.5, 0.5, th=0.06, side="s")
    gi = group(f"iris_{tag}", E + V(0, 0, -0.32), parent=g_e)
    plate(gi, f"iris_{tag}", E + V(0, 0, -0.32), Xf, Yf, "iris", GLASS_D, GLASS_D, th=0.06, side="s")
    gl = group(f"paupiere_{tag}", E + V(0, LID_TOP, -0.45), parent=g_e)
    plate(gl, f"paupiere_{tag}", E + V(0, LID_TOP - LID_H0 / 2, -0.45), Xf, Yf, "paupiere", GLASS_D - 0.04, LID_H0, th=0.06, side="s")
    plate(g_e, f"bague_{tag}", E + V(0, 0, -0.69), Xf, Yf, "bague", RING_D, RING_D, th=0.16, side="b")
    EYEG[tag] = dict(oeil=g_e, pupille=gp, iris=gi, paupiere=gl, lum=g_el)

# aigrettes : deux lames par côté, nervure pleine
TUFTG = {}
for s, tag in ((1, "r"), (-1, "l")):
    base = HC + HEAD.P(s * 40.0, 44.0, 0.96)
    g_a = group(f"aigrette_{tag}", base, parent=g_tete)
    TUFTG[tag] = g_a
    for i, ((Lt, Wt), dvec, back) in enumerate(zip(TUFTS, (V(s * 0.42, 1.0, 0.22), V(s * 0.95, 0.85, 0.42)), (0.0, 0.16))):
        d = unit(dvec)
        Y_ = unit(np.cross(V(0, 0, -1), d))
        if Y_ @ V(0, 1, 0) < 0 and abs(d[0]) > 0.5:
            Y_ = -Y_
        n = np.cross(d, Y_)
        c = base + d * (Lt / 2 - 0.2) + V(0, 0, back)
        plate(g_a, f"aigrette_{tag}{i}", c, d, Y_, f"aigrette{i}", Lt, Wt, th=0.3, side="b")
        bloc(g_a, f"aigrette_{tag}{i}_n", base + d * (Lt * 0.4 - 0.2) + V(0, 0, back), (Lt * 0.62, 0.14, 0.14), np.column_stack([d, Y_, n]), "bar_laiton", {"north": None, "south": None})

# rotor : dôme sur la calotte ; le mât télescopique monte (position) et les pales sortent (scale x 5) pour décoller.
# Rotor au-dessus du centre de gravité : il porte le hibou comme un hélicoptère ; les ailes restent raides (gouvernes).
DOME = HC + V(0, Y_CAP + 0.15, 0)
bloc(g_tete, "dome", DOME, (0.8, 0.26, 0.8), np.eye(3), "bar_laiton", {"up": "chapeau", "down": None})
g_mat = group("rotor_mat", HC + V(0, Y_CAP + 0.28, 0), parent=g_tete)
bar(g_mat, "mat", HC + V(0, Y_CAP - 0.32, 0), HC + V(0, Y_CAP + 0.80, 0), 0.09, "bar_acier", octo=False, ov=0.0, bouts="chapeau")
g_rot = group("rotor", HC + V(0, Y_CAP + 0.62, 0), parent=g_mat)
plate(g_rot, "helice", HC + V(0, Y_CAP + 0.62, 0), V(1, 0, 0), V(0, 0, -1), "helice", PROP_D * PROP_K, PROP_D * PROP_K, th=0.12, side="b")

# soupape à l'arrière de la calotte : bouffée modélisée (trans_) + vapeur de Minecraft, cadence pilotée (ctrl_emit)
VALVE = HC + V(0.0, Y_CAP - 0.1, 0.68)
g_sp = group("soupape", VALVE, parent=g_tete)
bar(g_sp, "soupape_tuyau", VALVE - V(0, 0.25, 0), VALVE + V(0, 0.55, 0), 0.14, "bar_cuivre", octo=False, ov=0.0, bouts="chapeau")
g_spc = group("soupape_cap", VALVE + V(0, 0.45, 0), parent=g_sp)
bloc(g_spc, "soupape_chapeau", VALVE + V(0, 0.55, 0), (0.52, 0.26, 0.52), np.eye(3), "bar_laiton", {"up": "chapeau", "down": "chapeau"})
g_emit = group("emit_mc_white_smoke", VALVE + V(0, 0.70, 0), parent=g_spc)
g_cemit = group("ctrl_emit", VALVE + V(0, 0.70, 0), parent=g_emit)
VP = VALVE + V(0, 0.68, 0)
g_vap = group("trans_vapeur", VP, parent=g_tete, rotation=(25, 0, 0))
VAP_K = 0.02          # bouffée modélisée à 2 % : invisible hors décharge ; idle l'agrandit (scale / VAP_K)
plate(g_vap, "vapeur_a", VP + V(0, VAP_K * VAP_H / 2, 0), V(1, 0, 0), V(0, 1, 0), "vapeur", VAP_K * VAP_W, VAP_K * VAP_H, th=VAP_K * 0.2, side="b")
plate(g_vap, "vapeur_b", VP + V(VAP_K * 0.02, VAP_K * (VAP_H / 2 + 0.03), 0), V(0, 0, 1), V(0, 1, 0), "vapeur", VAP_K * VAP_W, VAP_K * VAP_H, th=VAP_K * 0.2, side="b")

# familier vivant perché (guide 6.6) : plus de groupe du corps à la racine ; fam_racine est la racine. Le modèle est translaté
# en fin de script de -ORIG (géométrie et texture inchangées) : origine = centre du dessus de l'épaule gauche.
outliner = [bone_node(g_racine)]


# ------------------------------------------------------------------ animations
# Guide, section 3 : rotation +X = le haut part vers l'arrière ; +Y = le côté droit (+X) avance (l'avant part vers -X) ;
# +Z = le côté droit monte. Position +Y monte, +X vers la droite du joueur. Le hibou est à gauche (-X) : le joueur est
# à sa droite (+X). Tourner la face vers le joueur = rotation -Y (limitée : la tête du joueur est là).
def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}], "time": round(t, 4), "interpolation": "linear"}


def servo(tau, w=24.0, z=0.5):
    """Réponse d'un servo à un échelon : arrivée sèche, dépassement (~16 % à z = 0,5), rappel."""
    if tau <= 0:
        return 0.0
    wd = w * math.sqrt(1 - z * z)
    return 1 - math.exp(-z * w * tau) * (math.cos(wd * tau) + z / math.sqrt(1 - z * z) * math.sin(wd * tau))


def paliers(T, seq, v0=0.0, w=24.0, z=0.5):
    """Cibles successives [(t, valeur)] atteintes par paliers de servo, boucle refermée (fin de la boucle précédente comptée)."""
    def f(t):
        v, prev = v0, v0
        for ti, vi in seq:
            v += (vi - prev) * (servo(t - ti, w, z) + servo(t + T - ti, w, z) - 1)
            prev = vi
        return v
    return f


def once(T, seq, w=26.0, z=0.5):
    """Paliers d'une animation jouée une fois : part de 0 et y revient à la fin."""
    def f(t):
        v, prev = 0.0, 0.0
        for ti, vi in seq:
            v += (vi - prev) * servo(t - ti, w, z)
            prev = vi
        return v * (1 - sm(t, T - 0.1, T))
    return f


def cliquet(T, n, total=360.0, t0=0.05, w=34.0, z=0.42):
    """Échappement : n tics réguliers par boucle, total degrés (360 x k)."""
    return paliers(T, [(t0 + i * T / n, total * (i + 1) / n) for i in range(n)], 0.0, w, z)


def C(v):
    return lambda t: v


def S(T, k, ph=0.0):
    return lambda t: math.sin(TAU * k * t / T + ph)


def R3(fx=C(0.0), fy=C(0.0), fz=C(0.0)):
    return lambda t: (fx(t), fy(t), fz(t))


def anim(name, length, tracks, fps=24, loop="loop"):
    """tracks : {groupe: {canal: f(t) -> (x, y, z)}} ou {canal: ('tour', axe, degrés)} (2 clés linéaires : rotation continue)."""
    n = max(8, int(math.ceil(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A_ = {}
    for g, chans in tracks.items():
        kfs = []
        for ch, f in chans.items():
            if isinstance(f, tuple) and f[0] == "tour":
                v = [0.0, 0.0, 0.0]
                v[f[1]] = f[2]
                kfs += [kf(ch, 0.0, (0, 0, 0)), kf(ch, length, v)]
                continue
            vals = [f(t) for t in times]
            if loop == "loop":
                drift = [round(b - a) for a, b in zip(vals[0], vals[-1])]       # 360 x k sur la clé, 0 ailleurs
                vals[-1] = tuple(a + d for a, d in zip(vals[0], drift))
            kfs += [kf(ch, t, v) for t, v in zip(times, vals)]
        A_[groups[g]["uuid"]] = {"name": groups[g]["name"], "type": "bone", "keyframes": kfs}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "pet_idle", "animators": A_}


MOLANG_LONG = []


def molang(an, g, ch, xyz, t=0.0):
    """Une clé Molang (constante dans le temps) sur un canal ; remplace les clés existantes de ce canal."""
    for e in xyz:
        assert len(e) <= 512, f"Molang trop long ({len(e)}) : {groups[g]['name']} {ch}"
        assert e.count(";") <= 15, "16 instructions au plus"
        assert "*-" not in e and "+-" not in e and "--" not in e, f"signe ambigu : {e[:80]}"
        MOLANG_LONG.append(len(e))
    a = an["animators"].setdefault(groups[g]["uuid"], {"name": groups[g]["name"], "type": "bone", "keyframes": []})
    a["keyframes"] = [k for k in a["keyframes"] if k["channel"] != ch] + [
        {"channel": ch, "data_points": [{"x": xyz[0], "y": xyz[1], "z": xyz[2]}], "time": t, "interpolation": "linear"}]


def ailes(out_z=C(0.0), in_x=C(0.0), in_z=C(0.0), out_x=C(0.0), fan=C(0.0)):
    """Aile extérieure (gauche) : s'ouvre sur le côté (out_z > 0). Aile intérieure (droite, côté tête du joueur) : se lève
    vers l'arrière (in_x < 0), à peine sur le côté (in_z)."""
    tr = {WINGG["l"][0]: {"rotation": lambda t: (out_x(t), 0, -out_z(t))},
          WINGG["r"][0]: {"rotation": lambda t: (in_x(t), 0, in_z(t))}}
    for tag in ("l", "r"):
        for i, g in enumerate(WINGG[tag][1:]):
            tr[g] = {"rotation": lambda t, i=i: (-fan(t) * i * 0.5, 0, 0)}
    return tr


def yeux(pup=C(1.0), lid=C(0.0)):
    tr = {}
    for tag, gs in EYEG.items():
        tr[gs["pupille"]] = {"scale": lambda t: (pup(t), pup(t), 1)}
        tr[gs["paupiere"]] = {"scale": lambda t: (1, 1 + (LID_FERME - 1) * min(1.0, max(0.0, lid(t))), 1)}
    return tr


def aigrettes(fx):
    return {TUFTG[tag]: {"rotation": lambda t: (fx(t), 0, 0)} for tag in ("l", "r")}


def deploye(spin_tours, T):
    """Rotor sorti (mât monté, pales x 5) qui tourne : spin_tours tours par boucle de T (360° x k exact)."""
    return {g_mat: {"position": C((0, 0.8, 0))}, g_rot: {"scale": C((1 / PROP_K, 1, 1 / PROP_K)), "rotation": ("tour", 1, -360.0 * spin_tours)}}


def pattes(fx, crochet=-90.0):
    d = {PATTES[tag]: {"rotation": lambda t: (fx(t), 0, 0)} for tag in ("l", "r")}
    d[G_CROCHET] = {"rotation": C((0, 0, crochet))}
    return d


def crochet_replie():
    return {G_CROCHET: {"rotation": C((0, 0, -90.0))}}


def cle_tics(T, n):
    return {g_k: {"rotation": (lambda f: lambda t: (0, 0, -f(t)))(cliquet(T, n))}}


def fusion(*ds):
    out = {}
    for d in ds:
        for g, ch in d.items():
            out.setdefault(g, {}).update(ch)
    return out


# ---------------------------------------------------------------- idle : base vivante + comportements au hasard (Molang)
# Tranches de 13 s (q.life_time décalé par q.instance_seed : deux joueurs ne sont pas synchronisés) ; un hachage sinus par tranche
# (v.r) donne le début du comportement (décalé de 0 à 3 s : écarts de 10 à 16 s, jamais à intervalle fixe) et un tirage pondéré
# sur 16 cases (v.b) : rien 3/16, hochement, lissage et vapeur 2/16, les autres 1/16. Enveloppe commune v.e : 1,0–1,6 s montée,
# 4,4–5,0 s retour ; le reste de la tranche est calme. Aucune variable mémorisée : le Vestiaire et le renderer calculent tout.
H1, H2 = 242.2, 288      # graine 0 : les 9 premières tranches montrent 8 comportements différents (aperçu de 120 s)
TT = 13        # durée d'une tranche (s) ; début décalé de 0 à 3 s
# cases 0-15 -> comportement : [0,0,0,1,2,3,3,4,4,5,6,7,8,8,9,10]
POIDS = [0, 0, 0, 1, 2, 3, 3, 4, 4, 5, 6, 7, 8, 8, 9, 10]
PRE = (f"v.t=q.life_time+q.instance_seed*104;v.n=math.floor(v.t/{TT});v.r=math.abs(math.sin(v.n*{H1}+{H2}))*997;"
       f"v.u=v.t-v.n*{TT}-math.mod(math.floor(v.r),4);v.b=math.floor(math.mod(v.r,1)*16);v.b=math.max(0,v.b-2)-(v.b>5)-(v.b>7)-(v.b>12);"
       "v.e=math.clamp((v.u-1)*1.667,0,1)-math.clamp((v.u-4.4)*1.667,0,1);v.e=v.e*v.e*(3-2*v.e);")
COMPORTEMENTS = {1: "tête retournée à 200° (par l'extérieur), clic par clic", 2: "tête retournée à 240° et penchée",
                 3: "tête penchée d'un côté puis de l'autre, hochement de triangulation, sourcils levés",
                 4: "se lisse les lames de l'aile extérieure (petits coups de bec)", 5: "bat des ailes pour l'équilibre",
                 6: "petit vol : rotor sorti, passe derrière la tête jusqu'à l'épaule droite, revient se poser",
                 7: "fatigué, se remonte (clé qui tourne par crans), puis se réveille d'un coup",
                 8: "pression, soupape qui tremble, jet de vapeur, s'ébroue", 9: "picore affectueusement la joue du joueur",
                 10: "somnole le jour (hibou nocturne), se réveille en sursaut et regarde autour"}


def Lr(a, b):
    return f"math.clamp((v.u-{a})*{round(1 / (b - a), 3)},0,1)"


def Sm(a, b):
    return f"(0.5-0.5*math.cos({Lr(a, b)}*180))"


def B(i):
    return f"(v.b=={i})"


P_ = "(math.abs(q.head_y_rotation)<10)"               # picorer seulement si le joueur regarde devant lui (sa tête ne tourne pas vers le hibou)
D_ = "(math.abs(q.time_of_day-0.5)>0.27)"             # jour
LF = f"({Sm(1.2, 2.0)}-{Sm(7.6, 8.4)})"                 # vol : décollage / posé
FD = f"({Lr(0.6, 1.2)}-{Lr(8.4, 9.0)})"                 # vol : rotor sorti
ORB = f"180*({Sm(2.2, 4.2)}-{Sm(5.4, 7.4)})"            # vol : par derrière jusqu'à l'épaule droite, et retour
BLINK = "(math.mod(v.t,4.7)>4.55)+(math.mod(v.t,6.3)>6.15)"
FOCUS = "math.floor(math.sin(v.t*22.5)*2+math.sin(v.t*40.5))"
ROUSE = f"({Lr(3.0, 3.1)}-{Lr(3.5, 3.6)})"
DECH = f"({Lr(2.4, 2.45)}-{Lr(2.95, 3.05)})"


def M(*e):
    return tuple(PRE + x if "v." in x else x for x in e)


# repos sans être perché (il attend en l'air près du joueur) : rotor sorti, serres repliées, aigrettes couchées ; perché ou porté : rien
VOLE = "q.is_pet*(1-q.is_perched)"
TI = 120.0     # multiple de 40 (respiration, mise au point) ; tranches 0-8 complètes, la 9e commence à t = 120 (calme)
idle = anim("pet_idle", TI, {})
molang(idle, g_racine, "rotation", M("0", f"{B(6)}*{ORB}", "0"))
molang(idle, g_vol, "position", M(f"-1.0*{B(6)}*{LF}", f"{B(6)}*(4.6+0.2*math.sin(v.u*180))*{LF}", f"0.6*{B(6)}*{LF}"))
_t1, _t2 = f"({Lr(2.2, 2.6)}-{Lr(3.8, 4.2)})", f"({Lr(5.4, 5.8)}-{Lr(7.0, 7.4)})"
molang(idle, g_cap, "rotation", M(f"{B(6)}*3*math.sin(v.u*240)*{LF}", f"-{B(6)}*{ORB}", f"10*{B(6)}*({_t2}-{_t1})"))
molang(idle, g_snap, "rotation", M("0", "0", f"{B(8)}*6*math.sin(v.u*3600)*{ROUSE}-{B(9)}*3*v.e*{P_}+{B(5)}*5*v.e*math.sin(v.u*540)"))
molang(idle, g_snap, "position", M(f"{B(9)}*0.1*v.e*{P_}", "0", "0"))
_rs = f"({Lr(3.0, 3.1)}-{Lr(3.5, 3.7)})"
molang(idle, g_corps, "scale", M(f"1+0.01*math.sin(v.t*90)+{B(8)}*0.06*{_rs}", f"1+0.018*math.sin(v.t*90)+{B(8)}*0.02*{_rs}-{B(7)}*0.03*v.e",
                                 f"1+0.01*math.sin(v.t*90)+{B(8)}*0.06*{_rs}"))
_eveil = f"{Lr(5.6, 5.7)}*(1-{Lr(7.3, 7.5)})"
molang(idle, g_tete, "rotation", M(
    f"{B(3)}*v.e*7*math.sin(v.u*540)+{B(4)}*v.e*(7*math.sin(v.u*1800)-26)-{B(9)}*v.e*(8+14*math.max(0,math.sin(v.u*900)))*{P_}"
    f"-{B(7)}*v.e*18",
    f"{B(1)}*math.floor(v.e*8)*25+{B(2)}*math.floor(v.e*10)*24+{B(4)}*v.e*105-{B(9)}*v.e*52*{P_}",
    f"{B(3)}*v.e*26*math.cos(v.u*90)+{B(9)}*v.e*12*math.sin(v.u*720)*{P_}+{B(2)}*v.e*14"))
molang(idle, g_tete0, "rotation", M(f"{B(6)}*6*{LF}-{B(10)}*v.e*16*{D_}",
                                    f"{B(6)}*70*({Sm(4.0, 4.4)}-{Sm(5.2, 5.6)})", "0"))
# réveil en sursaut : regard à gauche et à droite par crans, sur le groupe du regard (s'ajoute à overlay_mecanisme en jeu ; < 512 car.)
molang(idle, g_suivi, "rotation", M("0", f"{B(10)}*{_eveil}*math.floor(math.sin(v.u*240)*2)*20", "0"))
molang(idle, g_tete, "position", M(f"{B(3)}*v.e*0.22*math.sin(v.u*540)", "0", "0"))
for tag, gs in EYEG.items():
    molang(idle, gs["paupiere"], "scale", M("1", f"1+{LID_FERME - 1:.3f}*math.min(1,{BLINK}+{B(10)}*v.e*0.8*{D_}+{B(7)}*v.e*0.5+{B(9)}*v.e*0.5"
                                                f"+{B(8)}*(v.u>2.4)*(v.u<2.75))", "1"))
    _pup = f"1+0.07*{FOCUS}+{B(7)}*({Lr(4.4, 4.6)}-{Lr(5.2, 5.8)})*0.4+{B(3)}*v.e*0.2"
    molang(idle, gs["pupille"], "scale", M(_pup, _pup, "1"))
    molang(idle, gs["iris"], "rotation", M("0", "0", f"{FOCUS}*20+{B(3)}*v.e*40"))
for tag, (g_s, si) in SOURCILS.items():
    _k = f"({B(3)}*v.e*18-{B(7)}*v.e*14+{B(9)}*v.e*10*{P_}-{B(5)}*v.e*8)"
    molang(idle, g_s, "rotation", M("0", "0", _k if si > 0 else f"-{_k}"))
_aig = (f"{B(6)}*65*(v.u>0.9)*(v.u<8.7)+{B(7)}*v.e*35+{B(10)}*v.e*25*{D_}-(math.mod(v.t,7.9)>7.6)*14"
        f"-{B(8)}*20*(v.u>2.45)*(v.u<3.05)-{B(3)}*v.e*10")
for tag in ("l", "r"):
    molang(idle, TUFTG[tag], "rotation", M(_aig, "0", "0"))
molang(idle, WINGG["l"][0], "rotation", M(f"-{B(4)}*v.e*10", "0", f"-({B(5)}*v.e*(55+20*math.sin(v.u*1080))+{B(4)}*v.e*18+{B(6)}*34*{LF})"))
molang(idle, WINGG["r"][0], "rotation", M(f"-({B(5)}*v.e*(42+15*math.sin(v.u*1080))+{B(6)}*28*{LF})", "0", f"{B(5)}*v.e*6+{B(6)}*6*{LF}"))
for tag in ("l", "r"):
    for i, g in enumerate(WINGG[tag][1:]):
        if i:
            molang(idle, g, "rotation", M(f"-{i * 0.5}*({B(5)}*v.e*20+{B(4)}*v.e*24+{B(6)}*12*{LF})", "0", "0"))
molang(idle, g_q, "rotation", M(f"{B(5)}*v.e*12*math.sin(v.u*1080)-(math.mod(v.t,5.3)>5.0)*10-{B(6)}*15*{LF}", "0", "0"))
for tag in ("l", "r"):
    molang(idle, PATTES[tag], "rotation", M(f"-{B(6)}*45*{LF}-{VOLE}*45", "0", "0"))
molang(idle, G_CROCHET, "rotation", M("0", "0", f"-{B(6)}*90*{LF}-{VOLE}*90"))
molang(idle, g_kr, "rotation", M("0", "0", f"-{B(7)}*math.floor({Lr(1.9, 4.3)}*8)*90"))
molang(idle, g_ctrl_l, "position", M(f"{B(7)}*(1.4*({Lr(4.4, 4.6)}-{Lr(5.2, 6.0)})-0.7*v.e)+{B(6)}*0.8*{FD}", "0", "0"))
_trem = f"{B(8)}*({Lr(1.0, 1.3)}-{Lr(2.3, 2.4)})*math.sin(v.u*6480)"
molang(idle, g_sp, "rotation", M(f"6*{_trem}", "0", f"3.6*{_trem}"))
molang(idle, g_spc, "position", M("0", f"{B(8)}*0.18*({Lr(2.35, 2.45)}-{Lr(2.8, 3.0)})", "0"))
_puff = f"{B(8)}*{round(1 / VAP_K - 1)}*({Lr(2.4, 2.5)}-{Lr(2.9, 3.4)})"
molang(idle, g_vap, "scale", M(f"1+{_puff}*(1+0.3*{Lr(2.45, 3.2)})", f"1+{_puff}*(1+0.7*{Lr(2.45, 3.2)})", f"1+{_puff}*(1+0.3*{Lr(2.45, 3.2)})"))
molang(idle, g_vap, "position", M("0", f"{B(8)}*0.9*{Lr(2.45, 3.3)}*(v.u<3.4)", "0"))
molang(idle, g_cemit, "position", M(f"{B(8)}*5*{DECH}", "0", "0"))
molang(idle, g_mat, "position", M("0", f"{B(6)}*0.8*{FD}+{VOLE}*0.8", "0"))
molang(idle, g_rot, "scale", M(f"1+{B(6)}*4*{FD}+{VOLE}*4", "1", f"1+{B(6)}*4*{FD}+{VOLE}*4"))
molang(idle, g_rot, "rotation", M("0", f"-{B(6)}*math.clamp(v.u-0.9,0,7.75)*1440-{VOLE}*q.anim_time*1440", "0"))

# ---------------------------------------------------------------- états du familier vivant (guide 6.6, mode perche)
# Perché (pet_sit, pet_idle, pet_sleep) : il garde la vie du repos ci-dessus. En l'air (pet_fly, pet_walk, pet_run, pet_fall) :
# le rotor sorti le porte (comme l'ancien vol), les ailes restent raides en gouvernes ; le mod gère sa place (hauteur 1,8 bloc),
# l'animation ne garde que le flottement (plus de décalage au-dessus de l'épaule ni de contre-rotation du torse).
pet_sit = json.loads(json.dumps(idle))
pet_sit["uuid"], pet_sit["name"], pet_sit["selected"] = nuid(), "pet_sit", False

TF = 2.4       # vol : sur son rotor près de l'épaule ; ailes raides en gouvernes (petites corrections), serres repliées
_corr = lambda T, base, amp, seed: paliers(T, [(0.2 + k * T / 5, base + amp * math.sin(seed + k * 2.3)) for k in range(5)] + [(T - 0.15, base)], base, w=20, z=0.4)
pet_fly = anim("pet_fly", TF, fusion(
    {g_vol: {"position": lambda t: (0.15 * math.sin(TAU * t / TF), 0.25 * math.sin(TAU * t / TF - 1.2), 0)},
     g_cap: {"rotation": lambda t: (-5 + 2 * math.sin(TAU * t / TF + 0.4), 0, 2.5 * math.sin(TAU * t / TF + 0.3))},
     g_tete0: {"rotation": R3(C(4.0), paliers(TF, [(0.4, 40), (1.1, -15), (1.7, 10), (2.1, 0)], w=26))},
     g_ctrl_l: {"position": C((0.8, 0, 0))}},
    ailes(_corr(TF, 34, 5, 0.0), _corr(TF, -28, 4, 1.0), C(6.0)), aigrettes(C(62.0)), pattes(C(-45.0)), deploye(10, TF), cle_tics(TF, 6)))

TW = 1.6       # suit le joueur en vol de croisière : nez un peu baissé, regard devant puis vers le joueur par crans
pet_walk = anim("pet_walk", TW, fusion(
    {g_vol: {"position": lambda t: (0.1 * math.sin(TAU * t / TW), 0.2 * math.sin(TAU * t / TW - 1.0), 0)},
     g_cap: {"rotation": lambda t: (-8 + 1.5 * math.sin(TAU * t / TW + 0.4), 0, 2.0 * math.sin(TAU * t / TW + 0.3))},
     g_tete0: {"rotation": R3(C(7.0), paliers(TW, [(0.5, -15), (1.1, 0)], w=26))},
     g_ctrl_l: {"position": C((0.9, 0, 0))}},
    ailes(_corr(TW, 30, 4, 0.4), _corr(TW, -25, 3, 1.4), C(5.0)), aigrettes(C(66.0)), pattes(C(-50.0)), deploye(8, TW), cle_tics(TW, 4)))

TR = 0.8       # course : il rattrape le joueur, nez baissé dans le vent, rotor à fond, aigrettes couchées, serres pendantes
pet_run = anim("pet_run", TR, fusion(
    {g_vol: {"position": lambda t: (0.1 * math.sin(TAU * t / TR), 0.15 * math.sin(TAU * 2 * t / TR), 0)},
     g_cap: {"rotation": lambda t: (-12 + 1.5 * math.sin(TAU * 2 * t / TR), 0, 2.0 * math.sin(TAU * t / TR))},
     g_tete0: {"rotation": C((10.0, 0, 0))},
     g_ctrl_l: {"position": C((1.0, 0, 0))}},
    ailes(_corr(TR, 26, 3, 0.7), _corr(TR, -22, 3, 1.7), C(5.0)), aigrettes(C(70.0)), pattes(C(-55.0)), yeux(C(0.85), C(0.3)),
    deploye(6, TR), cle_tics(TR, 4)))

TZ = 4.0       # sommeil (perché) : tête rentrée, paupières fermées, clé arrêtée, foyer en veille, respiration lente ; serres serrées
pet_sleep = anim("pet_sleep", TZ, fusion(
    {g_corps: {"scale": lambda t: (1 + 0.012 * math.sin(TAU * t / TZ), 1 + 0.025 * math.sin(TAU * t / TZ), 1 + 0.012 * math.sin(TAU * t / TZ))},
     g_tete0: {"rotation": lambda t: (-14 + 1.5 * math.sin(TAU * t / TZ - 0.6), 0, 6), "position": C((0, -0.25, 0))},
     g_ctrl_l: {"position": C((-0.6, 0, 0))}},
    aigrettes(C(30.0)), yeux(C(1.0), C(1.0))))

TA = 1.2       # chute : rotor sorti à fond pour freiner, ailes ouvertes en aérofreins, serres tendues
pet_fall = anim("pet_fall", TA, fusion(
    {g_snap: {"rotation": lambda t: (4, 0, 2 * math.sin(TAU * t / TA))}},
    ailes(_corr(TA, 40, 6, 0.3), _corr(TA, -32, 5, 1.3), C(6.0), fan=C(14.0)), yeux(C(1.25)), cle_tics(TA, 4),
    aigrettes(C(62.0)), pattes(C(-45.0)), deploye(6, TA)))


# ---------------------------------------------------------------- événements (par-dessus : rotations et positions s'ajoutent, échelles se multiplient)
THu = 1.0      # son maître prend un coup : sursaut (bond de 1,5 px), deux battements, tête vers lui, aigrettes plaquées, pupilles dilatées
_hu = once(THu, [(0.0, 1.0), (0.45, 0.0)], w=36, z=0.35)
_bat = lambda t: max(0.0, math.sin(TAU * 4 * t)) * (1 - sm(t, 0.4, 0.6))
event_owner_hurt = anim("event_owner_hurt", THu, fusion(
    {g_elan: {"position": lambda t: (0, 1.5 * math.sin(math.pi * min(1.0, t / 0.55)) * (t < 0.55), 0)},
     g_snap: {"rotation": lambda t: (10 * _hu(t), 0, 0)},
     g_tete0: {"rotation": lambda t: (0, once(THu, [(0.08, -22), (0.6, 0)], w=40, z=0.4)(t), 0)}},
    ailes(lambda t: 55 * _bat(t), lambda t: -45 * _bat(t), C(0.0)),
    aigrettes(lambda t: 40 * _hu(t)),
    {gs["pupille"]: {"scale": lambda t: (1 + 0.35 * _hu(t), 1 + 0.35 * _hu(t), 1)} for gs in EYEG.values()}), loop="once")

TPe = 1.1      # se pose sur l'épaule : arrive d'un peu plus haut et de l'extérieur, se cabre (aérofreins, serres en avant), touche,
#                serres qui se referment, écrasé puis rebond, deux petits pas de côté pour trouver l'équilibre, ailes qui se
#                rangent d'un frisson, puis tourne la tête vers son maître en la penchant (curiosité de chouette)
def _pose(T0, T1, haut, cote, recul):
    """Approche jusqu'à T0 (contact), retombée jusqu'à T1 : morceaux communs à l'arrivée, à la pose et au retour."""
    ap = lambda t: 1 - sm(t, 0.0, T0)
    cab = lambda t: bump(t, T0 - 0.3, T0 - 0.1, T0 - 0.02, T0 + 0.12)            # se cabre juste avant de toucher
    sq = once(T1, [(T0, 1.0), (T0 + 0.12, -0.35), (T0 + 0.3, 0.0)], w=36, z=0.4)
    fr = lambda t: bump(t, T0 + 0.12, T0 + 0.2, T0 + 0.32, T0 + 0.45) * math.sin(TAU * 9 * (t - T0))
    pas = lambda t: 4 * bump(t, T0 + 0.1, T0 + 0.16, T0 + 0.22, T0 + 0.28) - 4 * bump(t, T0 + 0.26, T0 + 0.32, T0 + 0.38, T0 + 0.46)
    return fusion(
        {g_elan: {"position": lambda t: (-cote * ap(t) ** 1.5, haut * ap(t) ** 2 + 0.25 * bump(t, T0 - 0.08, T0, T0, T0 + 0.1), recul * ap(t))},
         g_cap: {"rotation": lambda t: (-8 * ap(t) * (1 - cab(t)) + 20 * cab(t), 0, 8 * math.sin(math.pi * ap(t)) * (ap(t) > 0))},
         g_snap: {"rotation": lambda t: (0, 0, pas(t))},
         g_corps: {"scale": lambda t: (1 + 0.06 * sq(t), 1 - 0.1 * sq(t), 1 + 0.06 * sq(t))},
         G_CROCHET: {"rotation": lambda t: (0, 0, -90 * (1 - sm(t, T0 - 0.05, T0 + 0.12)))}},
        {PATTES[tag]: {"rotation": lambda t: (-45 * ap(t) ** 0.5 - 25 * cab(t), 0, 0)} for tag in ("l", "r")},
        ailes(lambda t: 34 * ap(t) ** 0.5 + 26 * cab(t) + 6 * fr(t), lambda t: -28 * ap(t) ** 0.5 - 22 * cab(t) - 5 * fr(t), C(0.0), fan=lambda t: 14 * cab(t)),
        aigrettes(lambda t: 55 * ap(t) ** 0.5 + 10 * cab(t)))


def _regarde(a, b, c, d, lacet=-55, penche=16):
    r = lambda t: bump(t, a, b, c, d)
    return {g_tete0: {"rotation": lambda t: (4 * r(t), lacet * r(t), penche * r(t) * sm(t, b, b + 0.2))}}


def _rotor_si_perche(an):
    """Le rotor sorti par l'événement ne compte que perché (pet_sit, rotor rentré) ; en vol, l'état l'a déjà sorti
    (échelles multipliées : sinon ×25)."""
    for g, ch in ((g_rot, "scale"), (g_mat, "position")):
        a = an["animators"].get(groups[g]["uuid"])
        for k in (a or {}).get("keyframes", []):
            if k["channel"] != ch:
                continue
            dp = k["data_points"][0]
            for ax in ("x", "y", "z"):
                v = float(dp[ax])
                if ch == "scale" and abs(v - 1) > 1e-4:
                    dp[ax] = f"1+{v - 1:.3f}*q.is_perched"
                elif ch == "position" and abs(v) > 1e-4:
                    dp[ax] = f"{v:.3f}*q.is_perched"
    return an


event_perch = anim("event_perch", TPe, fusion(_pose(0.35, TPe, 2.5, 1.5, 1.0), _regarde(0.65, 0.8, 0.95, TPe, -45, 14)), loop="once")

TTp = 1.4      # revient près du joueur (trop loin ou coincé) : il redescend d'en haut sur son rotor, se cabre, se pose, range
#                le rotor (ici sans son), puis regarde son maître
_dep_t = lambda t: 1 - sm(t, 0.75, 0.95)
event_teleport = _rotor_si_perche(anim("event_teleport", TTp, fusion(
    _pose(0.6, TTp, 6.0, 1.5, 2.0),
    {g_mat: {"position": lambda t: (0, 0.8 * _dep_t(t), 0)},
     g_rot: {"scale": lambda t: (1 + 4 * _dep_t(t), 1, 1 + 4 * _dep_t(t)), "rotation": lambda t: (0, -360.0 * 10 * sm(t, 0.0, 0.95), 0)}},
    _regarde(0.95, 1.1, 1.2, TTp, -50, 14)), loop="once"))

TJ = 0.5       # saut : il se tasse puis ouvre les ailes pour l'équilibre
event_jump = anim("event_jump", TJ, fusion(
    {g_corps: {"scale": lambda t: (1, 1 - 0.06 * once(TJ, [(0.0, 1), (0.12, 0)], w=40)(t), 1)}},
    ailes(once(TJ, [(0.05, 35), (0.3, 0)], w=34), once(TJ, [(0.05, -28), (0.3, 0)], w=34))), loop="once")

TL = 0.6       # atterrissage : écrasé puis rebond, ailes en balancier, selon la vitesse de chute (q.land_speed)
event_land = anim("event_land", TL, fusion(
    ailes(once(TL, [(0.0, 30), (0.22, 0)], w=40), once(TL, [(0.0, -24), (0.22, 0)], w=40))), loop="once")
_kl = "math.clamp(q.land_speed/10,0.3,1)"
_sq = once(TL, [(0.0, 1.0), (0.12, -0.4), (0.3, 0.0)], w=40, z=0.4)
event_land["animators"][groups[g_corps]["uuid"]] = {"name": "corps", "type": "bone", "keyframes": [
    {"channel": "scale", "data_points": [{"x": f"1+{0.08 * _sq(t):.3f}*{_kl}", "y": f"1-{0.14 * _sq(t):.3f}*{_kl}", "z": f"1+{0.08 * _sq(t):.3f}*{_kl}"}],
     "time": round(t, 3), "interpolation": "linear"} for t in np.arange(0, TL + 1e-6, TL / 12)]}

TE = 2.3       # arrivée (2026-11-08) : il arrive de derrière, d'en haut et de l'extérieur sur son rotor, en courbe (penché dans le
#                virage), se cabre ailes en aérofreins et serres en avant, se pose (serres qui se referment, deux petits pas),
#                range le rotor (son du piston), la soupape lâche la pression, ses lentilles s'allument, clignement mécanique et
#                mise au point des pupilles, puis tourne la tête vers son maître en la penchant
_dep = lambda t: 1 - sm(t, 1.15, 1.45)
_mise = lambda t: 1 - 0.45 * bump(t, 1.5, 1.6, 1.62, 1.72) + 0.25 * bump(t, 1.68, 1.76, 1.78, 1.9)
event_equip = _rotor_si_perche(anim("event_equip", TE, fusion(
    _pose(1.0, TE, 10.0, 4.0, 7.0),
    {g_mat: {"position": lambda t: (0, 0.8 * _dep(t), 0)},
     g_rot: {"scale": lambda t: (1 + 4 * _dep(t), 1, 1 + 4 * _dep(t)), "rotation": lambda t: (0, -360.0 * 18 * sm(t, 0.0, 1.45), 0)},
     g_spc: {"position": lambda t: (0, 0.18 * bump(t, 1.3, 1.36, 1.5, 1.65), 0)},
     g_sp: {"rotation": lambda t: (5 * bump(t, 1.3, 1.34, 1.5, 1.6) * math.sin(TAU * 18 * t), 0, 0)},
     g_ctrl_l: {"position": lambda t: (-1 + sm(t, 1.35, 1.7), 0, 0)}},
    {EYEG[tag]["lum"]: {"position": lambda t: (-1 + sm(t, 1.45, 1.6), 0, 0)} for tag in EYEG},
    yeux(_mise, lambda t: bump(t, 1.58, 1.63, 1.65, 1.72)),
    _regarde(1.8, 1.95, 2.1, TE)), loop="once"))
event_equip["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.piston.contract", "file": ""}], "time": 1.2}]}

# ---------------------------------------------------------------- couche permanente : regard, maître, virages, pluie, nuit
NUIT_ = "(math.abs(q.time_of_day-0.5)<0.27)"
BAS_ = "(q.owner_health<q.owner_max_health*0.3)"       # vie basse de son maître (guide 6.6)
EAU_ = "math.max(q.is_in_rain,q.is_in_water)"
ACC_ = "q.owner_is_sneaking"
overlay = anim("overlay_mecanisme", 27.0, {})        # 10 tranches de regard de 2,7 s (boucle fermée)
# porté (menu Apparence, ou second familier : guide 6.6) : sur l'épaule gauche, comme avant (q.is_pet = 0)
molang(overlay, g_racine, "position", tuple(f"(q.is_pet-1)*{-v:g}" if v < 0 else f"(1-q.is_pet)*{v:g}" for v in ORIG))
# regard d'automate : coups d'oeil par crans tirés au hasard (tranches de 2,7 s décalées par q.instance_seed, sans variable
# mémorisée) ; jamais plus de 15° vers le joueur (sa tête est là quand il est perché) ; vie basse du maître : il se tourne vers lui (-Y)
# chaque tranche part du regard de la précédente et pivote en 0,3 s (servo) : la boucle se referme (tranche 0 <- tranche 9)
_g = "v.g=q.life_time/2.7+q.instance_seed*13;v.i=math.floor(v.g);v.k=math.clamp((v.g-v.i)*9,0,1);"
_h = lambda d, m, n: f"math.floor(math.mod(math.abs(math.sin(math.mod(v.i+{d},10)*91.7))*{m},1)*{n})"
molang(overlay, g_suivi, "rotation", (
    _g + f"(math.lerp({_h(9, 1356, 3)},{_h(0, 1356, 3)},v.k)-1)*8",
    _g + f"(1-{BAS_})*(math.lerp({_h(9, 437.5, 5)},{_h(0, 437.5, 5)},v.k)-1)*15-{BAS_}*25", "0"))
# virages : il se penche dans le virage ; vie basse : tassé ; pluie ou eau : s'ébroue ; perché, le maître marche : il compense le pas
molang(overlay, g_vir, "rotation", (f"0-{BAS_}*8", "0",
                                    "v.vz=math.lerp(v.vz,math.clamp(0-q.yaw_speed*0.06,-4,12),0.1);"
                                    f"v.vz+{EAU_}*(math.mod(q.life_time,7)>6.4)*5*math.sin(q.life_time*4320)"
                                    "+q.is_perched*math.clamp(q.owner_ground_speed/4.3,0,1.3)*3*math.sin(q.life_time*600)"))
# maître accroupi : il se fait mince et allongé (camouflage du hibou), aigrettes dressées, pupilles grandes ouvertes
molang(overlay, g_corps, "scale", (f"1-0.02*{ACC_}", f"1+0.06*{ACC_}", f"1-0.02*{ACC_}"))
for tag in ("l", "r"):
    molang(overlay, TUFTG[tag], "rotation", (f"{BAS_}*30-{NUIT_}*8-{ACC_}*14", "0", "0"))
for tag, gs in EYEG.items():
    molang(overlay, gs["pupille"], "scale", (f"1+{NUIT_}*0.3+{BAS_}*0.2+{ACC_}*0.25", f"1+{NUIT_}*0.3+{BAS_}*0.2+{ACC_}*0.25", "1"))
    # nuit : lentilles plus vives (hibou nocturne) ; vie basse : elles baissent par à-coups irréguliers (panne de pression)
    molang(overlay, gs["lum"], "position", (f"{NUIT_}*0.8-{BAS_}*0.55*(math.sin(q.life_time*233)+math.sin(q.life_time*97)>1.2)", "0", "0"))
molang(overlay, g_cemit, "position", (f"3*{EAU_}-1", "0", "0"))                 # vapeur coupée, sauf pluie ou eau (métal chaud qui fume) et décharge (repos)

ANIMS = [idle, pet_sit, pet_walk, pet_run, pet_fly, pet_fall, pet_sleep, overlay, event_equip, event_teleport, event_perch, event_owner_hurt,
         event_jump, event_land]

assert 130 <= len(elements) <= 320, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
# familier vivant (guide 6.6) : tout le modèle translaté de -ORIG (serres à l'origine, centre de l'épaule gauche) ; géométrie et
# texture identiques à la version portée (la texture est peinte avant, en coordonnées absolues)
for e in elements:
    for k in ("from", "to", "origin"):
        e[k] = [round(float(v - o), 3) for v, o in zip(e[k], ORIG)]
for g in groups.values():
    g["origin"] = [round(float(v - o), 3) for v, o in zip(g["origin"], ORIG)]
outliner = [bone_node(g_racine)]
# perché sur l'épaule gauche, il s'envole quand le joueur court, saute, vole ou nage (hibou à rotor : il se pose pour
# économiser sa vapeur) ; hauteur de vol 1,8 bloc (près de l'épaule), distance 2 blocs
FAMILIER = {"mode": "perche", "distance": 2, "vitesse": 1, "hauteur": 1.8}
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS,
         "unhandled_root_fields": {"phynaria": {"version": 1, "familier": FAMILIER}}}
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
from ambiance import ajouter_ambiance
limiter_sons(model)
ajouter_ambiance(model)
assert len(model["animations"]) <= 16
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(model["animations"]), "anims ;",
      sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      f"densité {DENS:.1f} texels/px ; Molang le plus long {max(MOLANG_LONG)} car.")
_r = [abs(math.sin(math.radians(n * H1 + H2))) * 997 for n in range(16)]
print("tirages (graine 0, tranches 0-15) : comportement", [POIDS[math.floor(math.fmod(r, 1) * 16)] for r in _r], "; décalage (s)", [math.floor(r) % 4 for r in _r])
