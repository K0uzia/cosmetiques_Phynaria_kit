"""Arbalète à vapeur : skin d'objet (guide 14) pour toutes les arbalètes du joueur, ensemble Steampunk (thème Mécanique). Design original.
Écrit skin_arbalete_steampunk.png, skin_arbalete_steampunk_e.png et .build/skin_arbalete_steampunk_brut.bbmodel à côté de ce script.
Version en vrai volume (2026-11-10) ; la version en barres octogonales et plaques empilées est gardée dans .build/gen_avant.py
(et la toute première, avant la rotation du repère, dans .build/gen_avant_v1.py).

Même design, nom, fiche, repère, taille, étapes et Display que la version validée en jeu (sens et taille : captures 23.24.54–23.25.08).
Retour de l'utilisateur sur toute la série : « faut te baser sur les modèles Minecraft … pour avoir de vrais modèles 3D, pas des
couches empilées ; le manche de l'épée par exemple est bien ». Langage du set : skin_epee_steampunk (référence), ligne « Langage » de
sets-objets-2026-11-08.md, .claude/styles/steampunk.md (métal propre : laiton, cuivre, acier bruni ; bois sombre).

Pièces (mêmes cotes qu'avant) :
- arc en **lames de ressort** de laiton : trois lames étagées par branche (plus courtes et un peu plus basses vers l'arrière), chaque
  tronçon d'une lame = **plaque fermée biseautée** (plats, biseaux à pente unique, chant fermé ; faces échantillonnées texel par texel,
  découpées par l'alpha, recouvrement 0,08) ; la lame suit sa courbe par tronçons de 1,45–1,9 px qui plient à chaque étape ;
  tétons d'acier en tours aux bouts, câble d'acier en tour à 6 pans ;
- **plaques fermées biseautées** pour les pièces plates : crosse de bois à talon (section octogonale par ses biseaux), poignée,
  plaque de couche de laiton, rails de la rainure, étrier de l'arc riveté, noix, griffe, pontet, détente, étrier de pied, pennes ;
- **tours** (couronnes de pans peints, découpés en trapèze par l'alpha) pour les pièces rondes : fût octogonal de bois, bagues
  rivetées, nez, réservoir de cuivre à fonds bombés et cerclages, tuyau et vanne, col, boîtier et lunette du manomètre, tambour,
  moyeu, manivelle et sa poignée, lentille de la noix, carreau (fût, virole, pointe), fusée (papier, bagues, coiffe) ;
- engrenage de remontage : deux faces découpées par l'alpha (jante, fenêtres, rayons, moyeu), flanc à 16 pans, 14 dents en boîtes ;
- nouveau, petit : **soupape** sur le réservoir (d'où part le jet de vapeur au tir).

Étapes (groupes à la racine, guide 14 ; le groupe `arbalete` est toujours dessiné) : `repos`, `bande_1`, `bande_2`, `bande_3` (la corde
recule avec la griffe, les lames plient, la manivelle et l'engrenage tournent, l'aiguille monte), `chargee` (carreau d'acier empenné de
cuivre, lentille allumée, aiguille dans la zone rouge), `chargee_fusee` (fusée de papier rouge cerclée de laiton).

Repère du skin d'objet (validé en jeu) : dans le bloc 16 × 16 × 16, comme l'image de l'arbalète de Minecraft vue depuis +Z : crosse en
bas à droite, arc en haut à gauche, dessus du fût vers +Z. a = le long du fût (vers l'avant), w = travers (le long de l'arc), t = dessus.
Display : celui de l'arbalète de Minecraft (objet.affichage("arbalete")), inchangé.

Objet vivant (guide 14), sobre :
- `item_idle` (8 s) : l'aiguille avance de deux crans et retombe (servo : échelon, dépassement, rappel) ; chargée, elle tremble dans
  le rouge ; points de vapeur coupés (ctrl_emit −1) ; aucun son ;
- `item_use` (boucle 0,5 s) : pendant le chargement, l'aiguille tremble de plus en plus (q.use_progress) et la soupape laisse fuir
  un peu de vapeur (`emit_mc_white_smoke` + `ctrl_emit` = 3·use_progress − 1) ; aucun son ;
- `event_charged` (0,6 s) : la noix prend la corde, l'aiguille saute dans le rouge avec un dépassement ; aucun son ;
- `event_release` (0,8 s) : le carreau part ; la soupape se soulève et lâche un jet de vapeur `trans_jet` qui **monte** (seul
  dépliage par scale de ce groupe, fondu `ctrl_alpha`), `emit_mc_white_smoke` (+4), l'aiguille retombe à zéro ; **seul son** du
  skin : `tir_vapeur` embarqué (sons/tir_vapeur.py, original, repris de skin_arc_steampunk), clé à 0,04 s.
Aucun son sur event_use_start ni event_enter_* (il n'y en a pas). Jet caché au repos : géométrie F_GEO / K enfouie dans le chapeau de
la soupape. Superposition (guide 6.4) : les événements s'ajoutent à l'état.

Fonctions avancées : `trans_jet`, `ctrl_alpha`, `emit_mc_white_smoke`, `ctrl_emit`, calque _e (verre ambre du cadran, lentille de la
noix allumée, fentes du foyer sous le réservoir), son embarqué `tir_vapeur`, Molang `q.use_progress`. Non simulés par le renderer :
ctrl_emit, particules, animations d'objet en main, Molang des objets (à juger en jeu, `/cosmetique apercu`).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

AVEC_E = True
NOM = "skin_arbalete_steampunk"
TEX = 512
TAU = 2 * math.pi
K = 12.0            # facteur de réduction du jet au repos
F_GEO = 1.0         # géométrie F_GEO / K, clés scale ≤ K / F_GEO

# Repère validé en jeu (version d'avant) : arc en HAUT À GAUCHE, crosse en bas à droite
A_ = np.array((-1.0, 1.0, 0.0)) / math.sqrt(2)    # le long du fût, vers l'avant
W_ = np.array((-1.0, -1.0, 0.0)) / math.sqrt(2)   # travers, le long de l'arc
T_ = np.array((0.0, 0.0, 1.0))                     # dessus du fût (vu dans l'inventaire)
A_MIN, A_MAX = -9.85, 7.95
O_ = np.array((8.0, 8.0, 8.0)) - A_ * (A_MIN + A_MAX) / 2


def P(a, w=0.0, t=0.0):
    return O_ + A_ * a + W_ * w + T_ * t


def lerp(a, b, k):
    return a + (b - a) * k


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    x = (t - a) / (b - a)
    return x * x * (3 - 2 * x)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def Af(c):
    return np.array(c, np.float32)


BRASS = dict(hi=Af((236, 196, 112)), base=Af((190, 142, 64)), low=Af((112, 76, 32)))
COPPER = dict(hi=Af((232, 150, 96)), base=Af((176, 92, 52)), low=Af((98, 46, 26)))
STEEL = dict(hi=Af((136, 140, 150)), base=Af((78, 82, 92)), low=Af((38, 40, 48)))
WOOD = dict(hi=Af((122, 78, 46)), base=Af((84, 50, 30)), low=Af((40, 22, 14)))
PAPER = dict(hi=Af((222, 84, 64)), base=Af((176, 42, 34)), low=Af((96, 20, 16)))
CREME = Af((236, 222, 190))
FIL = Af((220, 224, 232))
POLI = Af((176, 180, 190))
AMBRE = Af((255, 210, 120))
AMBRE_B = Af((220, 150, 50))
VAPEUR = Af((250, 250, 248))
VAPEUR_B = Af((220, 224, 228))


# ------------------------------------------------------------------ repères de plaques (plan local s, h ; épaisseur z)
class Cadre:
    """Repère direct : point local (s, h, z) -> O + U s + V h + N z, avec N = U × V."""

    def __init__(self, O, U, V):
        self.O, self.U = np.asarray(O, float), unit(U)
        V = np.asarray(V, float)
        self.V = unit(V - (V @ self.U) * self.U)
        self.N = np.cross(self.U, self.V)

    def p(self, s, h=0.0, z=0.0):
        return self.O + self.U * s + self.V * h + self.N * z

    def v(self, s, h=0.0, z=0.0):
        return self.U * s + self.V * h + self.N * z


def F_COTE(w0=0.0, a0=0.0, t0=0.0):
    """Plan (a, t), épaisseur selon w (N = −W_)."""
    return Cadre(P(a0, w0, t0), A_, T_)


def F_DESSUS(t0=0.0, a0=0.0, w0=0.0):
    """Plan (a, w), épaisseur selon t (N = +T_)."""
    return Cadre(P(a0, w0, t0), A_, W_)


def F_DOS(a0):
    """Plan (w, t), épaisseur selon a (N = +A_)."""
    return Cadre(P(a0), W_, T_)


# ------------------------------------------------------------------ géométrie 2D
def in_poly(Pp, poly):
    x, y = Pp[..., 0], Pp[..., 1]
    ins = np.zeros(x.shape, bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1)
        ins ^= c
    return ins


def subdiv(pts, maxlen=0.9):
    out = []
    for i in range(len(pts) - 1):
        p, q = np.array(pts[i], float), np.array(pts[i + 1], float)
        n = max(1, int(math.ceil(np.linalg.norm(q - p) / maxlen)))
        for k in range(n):
            out.append((p + (q - p) * k / n, p + (q - p) * (k + 1) / n, k == 0, k == n - 1))
    return out


def d_stack(Pp, segs):
    out = []
    for p, q, *_ in segs:
        ab = q - p
        t = np.clip(((Pp - p) @ ab) / (ab @ ab), 0, 1)
        out.append(np.linalg.norm(Pp - (p + t[..., None] * ab), axis=-1))
    return np.stack(out)


def bande_poly(pts, hw):
    """Contour fermé d'une bande de demi-largeur hw le long d'une polyligne (onglets aux coudes, bouts carrés)."""
    pts = [np.array(p, float) for p in pts]
    g, d = [], []
    for i, p in enumerate(pts):
        if i == 0:
            t = unit(pts[1] - p)
            no, k = np.array((-t[1], t[0])), 1.0
        elif i == len(pts) - 1:
            t = unit(p - pts[i - 1])
            no, k = np.array((-t[1], t[0])), 1.0
        else:
            t1, t2 = unit(p - pts[i - 1]), unit(pts[i + 1] - p)
            n1, n2 = np.array((-t1[1], t1[0])), np.array((-t2[1], t2[0]))
            no = unit(n1 + n2)
            k = 1.0 / max(no @ n1, 0.3)
        g.append(tuple(p + no * hw * k))
        d.append(tuple(p - no * hw * k))
    return g + d[::-1]


def rect(s0, s1, h0, h1, ch=0.0):
    if ch <= 0:
        return [(s0, h0), (s1, h0), (s1, h1), (s0, h1)]
    return [(s0 + ch, h0), (s1 - ch, h0), (s1, h0 + ch), (s1, h1 - ch), (s1 - ch, h1), (s0 + ch, h1), (s0, h1 - ch), (s0, h0 + ch)]


# ------------------------------------------------------------------ cubes différés (monde)
TH = 0.3
DF = 16.0
RECOUV = 0.08
TILES = {}          # nom -> (rgba, rgba_e | None)
TRANS = set()
CUBES = []
CACHE = {}          # nom de tuile -> True (peinte) / False (vide) : tuiles partagées entre étapes et côtés
SIX = ("north", "south", "east", "west", "up", "down")


def tuile(nom, rgba, e=None):
    assert nom not in TILES, nom
    TILES[nom] = (rgba, e)
    return nom


def finir(col, al, em, masque):
    rgba = np.zeros(col.shape[:2] + (4,), np.uint8)
    rgba[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    rgba[..., 3] = 255 * masque
    rgba[~masque] = 0
    e = None
    if em is not None:
        on = masque & (em.max(axis=-1) > 0)
        if on.any():
            e = np.zeros_like(rgba)
            e[..., :3] = np.clip(em, 0, 225).astype(np.uint8)
            e[..., 3] = on * 255
            e[~on] = 0
    return rgba, e


def repere(X, Y):
    X = unit(X)
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    return X, Y, np.cross(X, Y)


def boite(g, nom, c, X, Y, s, faces):
    """Cube monde : centre c, axes X, Y (Z = X × Y), tailles s ; faces = {face: tuile}, les autres transparentes."""
    X, Y, Z = repere(X, Y)
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float), "R": np.column_stack([X, Y, Z]),
                  "half": np.asarray(s, float) / 2, "faces": dict(faces)})


def points_face(c, X, Y, Z, s, face, dens=DF):
    sx, sy, sz = s
    dims = {"south": (sx, sy), "north": (sx, sy), "down": (sx, sz), "up": (sx, sz), "east": (sz, sy), "west": (sz, sy)}[face]
    W, H = max(2, int(round(dims[0] * dens))), max(2, int(round(dims[1] * dens)))
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    U_, V_ = np.meshgrid(u, v)
    if face == "south":
        x, y, z = -sx / 2 + U_ * sx, sy / 2 - V_ * sy, np.full_like(U_, sz / 2)
    elif face == "north":
        x, y, z = sx / 2 - U_ * sx, sy / 2 - V_ * sy, np.full_like(U_, -sz / 2)
    elif face == "down":
        x, y, z = -sx / 2 + U_ * sx, np.full_like(U_, -sy / 2), sz / 2 - V_ * sz
    elif face == "up":
        x, y, z = -sx / 2 + U_ * sx, np.full_like(U_, sy / 2), -sz / 2 + V_ * sz
    elif face == "east":
        x, y, z = np.full_like(U_, sx / 2), sy / 2 - V_ * sy, sz / 2 - U_ * sz
    else:
        x, y, z = np.full_like(U_, -sx / 2), sy / 2 - V_ * sy, -sz / 2 + U_ * sz
    return c + x[..., None] * X + y[..., None] * Y + z[..., None] * Z


def spec(groupe, nom, c, X, Y, s, peintures, F, cle):
    """Cube dans le plan local (s, h, z) du cadre F ; chaque face peinte est échantillonnée texel par texel et découpée par
    l'alpha ; tuile nommée par `cle` (partagée par toutes les pièces de même forme locale)."""
    X, Y, Z = repere(X, Y)
    c = np.asarray(c, float)
    faces = {}
    for f, fn in peintures.items():
        tn = f"{cle}_{f}"
        if tn not in CACHE:
            Pp = points_face(c, X, Y, Z, s, f)
            col, al, em, m = fn(Pp)
            CACHE[tn] = bool(m.any())
            if CACHE[tn]:
                tuile(tn, *finir(col, al, em, m))
        if CACHE[tn]:
            faces[f] = tn
    if faces:
        CUBES.append({"groupe": groupe, "nom": nom, "c": F.p(*c), "R": np.column_stack([F.v(*X), F.v(*Y), F.v(*Z)]),
                      "half": np.asarray(s, float) / 2, "faces": faces})


# ------------------------------------------------------------------ plaques fermées biseautées (pièces plates)
class Plaque:
    """Plaque fermée dans le plan local (z = 0) : contour fermé poly, plats à ±h, biseaux à pente unique t_bis du bord
    (demi-épaisseur z_e) au plat, chant qui ferme le bord ; mat = peintures {biseau, plat, chant}."""

    def __init__(self, nom, poly, h, z_e, t_bis, mat, seg=0.9, cle=None):
        self.nom, self.poly, self.mat = nom, [tuple(map(float, p)) for p in poly], mat
        self.cle = cle or nom
        self.h_, self.ze, self.tb = h, z_e, t_bis
        self.al = math.atan(t_bis)
        self.segs = subdiv(self.poly + [self.poly[0]], seg)

    def wb(self, Pp):
        return np.maximum((np.full(np.shape(Pp)[:-1], self.h_) - self.ze) / self.tb, 0.02)

    def dE(self, Pp):
        return d_stack(Pp, self.segs).min(0)


def volume_plaque(pc, groupe, F):
    for idx, (p, q, v0, v1) in enumerate(pc.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        pm = (p + q) / 2
        if not in_poly(np.array([pm + n * 0.03]), pc.poly)[0]:
            n = -n                                                 # n vers l'intérieur
        wmax = float(pc.wb(p[None])[0])
        e0 = wmax * 1.6 + 0.04 if v0 else 0.04
        e1 = wmax * 1.6 + 0.04 if v1 else 0.04
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        sy = (wmax + 0.1) / math.cos(pc.al)
        for sg in (1, -1):
            Y = np.array((n[0] * math.cos(pc.al), n[1] * math.cos(pc.al), sg * math.sin(pc.al)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0], mid[1], sg * pc.ze)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(Pp, idx=idx, sg=sg):
                P2 = Pp[..., :2]
                D = d_stack(P2, pc.segs)
                de = D.min(0)
                own = D[idx] <= de + RECOUV
                wb = pc.wb(P2)
                m = in_poly(P2, pc.poly) & own & (de < wb + 0.03) & (de >= -0.02)
                col, em = pc.mat["biseau"](P2, np.clip(de / wb, 0, 1.2), sg)
                return col, None, em, m

            spec(groupe, f"{pc.nom}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut}, F, f"{pc.cle}_bis{'pm'[sg < 0]}{idx}")
        no = -n
        X = np.array((d[0], d[1], 0.0))
        Y = np.array((0.0, 0.0, 1.0))
        Z = np.cross(X, Y)
        face = "south" if Z[:2] @ no > 0 else "north"
        c = np.array((pm[0], pm[1], 0.0)) - np.array((no[0], no[1], 0.0)) * (TH / 2)

        def chant(Pp, idx=idx, n=n):
            P2 = Pp[..., :2] + n * 0.04
            D = d_stack(P2, pc.segs)
            own = D[idx] <= D.min(0) + RECOUV
            col, em = pc.mat["chant"](P2, Pp[..., 2] / max(pc.ze, 1e-3))
            return col, None, em, own

        spec(groupe, f"{pc.nom}_chant{idx}", c, X, Y, (float(np.linalg.norm(q - p)) + 0.08, 2 * pc.ze + 0.08, TH), {face: chant}, F,
             f"{pc.cle}_chant{idx}")
    Pq = np.array(pc.poly)
    s0, s1 = Pq[:, 0].min() - 0.05, Pq[:, 0].max() + 0.05
    h0, h1 = Pq[:, 1].min() - 0.05, Pq[:, 1].max() + 0.05
    for sg in (1, -1):
        X = np.array((1.0, 0.0, 0.0))
        Y = np.array((0.0, float(sg), 0.0))
        Z = np.cross(X, Y)
        c = np.array(((s0 + s1) / 2, (h0 + h1) / 2, sg * pc.h_)) - Z * (TH / 2)

        def plat(Pp, sg=sg):
            P2 = Pp[..., :2]
            de = pc.dE(P2)
            wb = pc.wb(P2)
            m = in_poly(P2, pc.poly) & (de >= wb - 0.03)
            col, em = pc.mat["plat"](P2, de, wb, sg)
            return col, None, em, m

        spec(groupe, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, (s1 - s0, h1 - h0, TH), {"south": plat}, F, f"{pc.cle}_plat{'pm'[sg < 0]}")


def brosse(P2, ax=(1.0, 0.0), seed=0.0):
    """Brossé fin (±4 %) le long de ax."""
    ax = np.asarray(ax, float)
    s = P2 @ ax
    r = P2 @ np.array((-ax[1], ax[0]))
    return (np.sin(s * 41.0 + r * 3.0 + seed) * 0.5 + np.sin(s * 17.0 + r * 0.6 + seed * 3) * 0.5) * 0.04


def z3(P2):
    return np.zeros(P2.shape[:-1] + (3,), np.float32)


def rivets_sur(col, P2, rivets, metal=COPPER):
    for (rs, rh, rr) in rivets:
        dd = np.hypot(P2[..., 0] - rs, P2[..., 1] - rh)
        col = np.where((dd < rr)[..., None], metal["low"] + z3(P2), col)
        col = np.where((dd < rr * 0.72)[..., None], metal["base"] + z3(P2), col)
        col = np.where((np.hypot(P2[..., 0] - rs + rr * 0.25, P2[..., 1] - rh - rr * 0.25) < rr * 0.3)[..., None], metal["hi"] + z3(P2), col)
    return col


def mat_laiton(rivets=(), rainure=None, ax=(1.0, 0.0), chant_riv=None):
    """Laiton brossé : biseau clair, arête sombre au plat, rainure gravée et rivets de cuivre en option ; chant plus sombre."""
    def biseau(P2, f, sg):
        col = lerp(BRASS["hi"], BRASS["base"], np.clip((f - 0.2) / 0.7, 0, 1)[..., None]) * (1 + brosse(P2, ax, 1 + sg))[..., None]
        col = np.where((f < 0.14)[..., None], lerp(BRASS["hi"], FIL, 0.25) + z3(P2), col)
        col = np.where((f >= 0.9)[..., None], BRASS["low"] + z3(P2), col)
        return col, None

    def plat(P2, d, wb, sg):
        col = (BRASS["base"] * 1.04 + z3(P2)) * (1 + brosse(P2, ax, 2 + 3 * sg))[..., None]
        if rainure is not None:
            r0, r1 = rainure
            col = np.where(((d >= wb + r0) & (d < wb + r1))[..., None], BRASS["low"] + z3(P2), col)
            col = np.where(((d >= wb + r1) & (d < wb + r1 + 0.05))[..., None], BRASS["hi"] + z3(P2), col)
        return rivets_sur(col, P2, rivets), None

    def chant(P2, zn):
        k = np.clip(0.62 - 0.32 * np.abs(zn), 0, 1)[..., None]
        col = lerp(BRASS["low"], BRASS["base"], k) * (1 + brosse(P2, ax, 5))[..., None]
        return col, None

    return dict(biseau=biseau, plat=plat, chant=chant)


def mat_lame(rivet_s=None):
    """Lame de ressort : le chant (vu de face et de dos) est la grande face polie, liseré clair en haut ; biseaux clairs ;
    dessus brossé, un rivet d'acier à la racine."""
    def biseau(P2, f, sg):
        col = lerp(lerp(BRASS["hi"], FIL, 0.2), BRASS["base"], np.clip(f / 0.9, 0, 1)[..., None]) + z3(P2)
        return np.where((f >= 0.9)[..., None], BRASS["low"] + z3(P2), col), None

    def plat(P2, d, wb, sg):
        col = (BRASS["base"] * (1.06 if sg > 0 else 0.8) + z3(P2)) * (1 + brosse(P2, (1.0, 0.0), 3 + sg))[..., None]
        if rivet_s is not None:
            col = rivets_sur(col, P2, ((rivet_s, 0.0, 0.14),), STEEL)
        return col, None

    def chant(P2, zn):
        k = np.clip(0.5 + 0.42 * zn, 0, 1)[..., None]                     # plus clair en haut (lumière du dessus)
        col = lerp(BRASS["low"], BRASS["hi"], k) * (1 + brosse(P2, (1.0, 0.0), 7))[..., None]
        col = np.where((zn > 0.86)[..., None], lerp(BRASS["hi"], FIL, 0.35) + z3(P2), col)
        col = np.where((zn < -0.86)[..., None], BRASS["low"] * 0.8 + z3(P2), col)
        return col, None

    return dict(biseau=biseau, plat=plat, chant=chant)


def mat_acier_poli():
    def biseau(P2, f, sg):
        col = lerp(FIL, POLI, np.clip((f - 0.1) / 0.5, 0, 1)[..., None]) + z3(P2)
        return np.where((f >= 0.9)[..., None], STEEL["base"] + z3(P2), col), None

    def plat(P2, d, wb, sg):
        return (POLI * 0.92 + z3(P2)) * (1 + brosse(P2, (0.3, 1.0), sg))[..., None], None

    def chant(P2, zn):
        return lerp(STEEL["hi"], STEEL["base"], np.abs(zn)[..., None]) + z3(P2), None

    return dict(biseau=biseau, plat=plat, chant=chant)


def mat_acier():
    def biseau(P2, f, sg):
        col = lerp(STEEL["hi"], STEEL["base"], np.clip(f / 0.8, 0, 1)[..., None]) + z3(P2)
        return np.where((f >= 0.9)[..., None], STEEL["low"] + z3(P2), col), None

    def plat(P2, d, wb, sg):
        return (STEEL["base"] * 1.08 + z3(P2)) * (1 + brosse(P2, (1.0, 0.0), sg))[..., None], None

    def chant(P2, zn):
        return lerp(STEEL["base"], STEEL["low"], np.abs(zn)[..., None]) + z3(P2), None

    return dict(biseau=biseau, plat=plat, chant=chant)


def bois_grain(P2, ax, seed=0.0):
    ax = np.asarray(ax, float)
    a, r = P2 @ ax, P2 @ np.array((-ax[1], ax[0]))
    g = np.sin(r * 9.0 + np.sin(a * 1.3 + seed) * 1.8 + seed * 2)
    k = np.clip(0.45 + 0.16 * g + 0.08 * np.sin(a * 0.7 + r * 3.0 + seed), 0, 1)
    col = lerp(WOOD["low"], WOOD["hi"], k[..., None])
    vein = np.sin(r * 23.0 + np.sin(a * 2.1 + seed) * 2.5) > 0.9
    return np.where(vein[..., None], col * 0.78, col)


def mat_bois(ax=(1.0, 0.0), seed=0.0):
    """Bois sombre veiné (fil le long de ax) ; biseau un peu plus clair (usé), trait d'ombre au bord du plat."""
    def biseau(P2, f, sg):
        col = bois_grain(P2, ax, seed + 1) * (1.12 - 0.12 * np.clip(f, 0, 1))[..., None]
        return np.where((f >= 0.92)[..., None], WOOD["low"] * 0.85 + z3(P2), col), None

    def plat(P2, d, wb, sg):
        col = bois_grain(P2, ax, seed + 2 * sg)
        return np.where((d - wb < 0.05)[..., None], WOOD["low"] * 0.85 + z3(P2), col), None

    def chant(P2, zn):
        return bois_grain(P2, ax, seed + 3) * 1.08, None

    return dict(biseau=biseau, plat=plat, chant=chant)


def mat_cuivre_penne():
    def biseau(P2, f, sg):
        return lerp(COPPER["hi"], COPPER["base"], np.clip(f, 0, 1)[..., None]) + z3(P2), None

    def plat(P2, d, wb, sg):
        col = lerp(COPPER["hi"], COPPER["low"], np.clip(P2[..., 1] / 0.9, 0, 1)[..., None]) + z3(P2)
        col = np.where((np.abs(P2[..., 1] - 0.1) < 0.05)[..., None], BRASS["hi"] + z3(P2), col)
        return col, None

    def chant(P2, zn):
        return COPPER["low"] * 1.1 + z3(P2), None

    return dict(biseau=biseau, plat=plat, chant=chant)


# ------------------------------------------------------------------ tours (pièces rondes)
OVL, OVW = 0.04, 0.03
DENS = 16.0


def p_laiton(xn, t, y, r, L, ex):
    k = np.clip(0.3 + 0.55 * (1 - np.abs(xn) ** 1.4) + ex.get("clair", 0.0), 0, 1)
    col = lerp(BRASS["low"], BRASS["hi"], k[..., None])
    if ex.get("riv"):
        dx = xn * ex.get("demi", 0.25)
        dd = np.hypot(dx, y - L / 2)
        col = np.where((dd < 0.12)[..., None], COPPER["low"] * 0.8, col)
        col = np.where((dd < 0.085)[..., None], COPPER["base"], col)
        col = np.where((np.hypot(dx + 0.025, y - L / 2 - 0.025) < 0.04)[..., None], COPPER["hi"], col)
    if ex.get("arete"):
        col = np.where(((y < 0.05) | (y > L - 0.05))[..., None], BRASS["low"] * 0.85, col)
    return col, None


def p_cuivre(xn, t, y, r, L, ex):
    k = np.clip(0.3 + 0.55 * (1 - np.abs(xn) ** 1.4) + ex.get("clair", 0.0), 0, 1)
    col = lerp(COPPER["low"], COPPER["hi"], k[..., None])
    if ex.get("riv"):
        pas = ex["riv"]
        yy = (y + ex.get("y0", 0.0)) % pas - pas / 2
        dx = xn * ex.get("demi", 0.25)
        dd = np.hypot(dx, yy)
        col = np.where((dd < 0.12)[..., None], COPPER["low"] * 0.7, col)
        col = np.where((dd < 0.085)[..., None], BRASS["base"], col)
        col = np.where((np.hypot(dx + 0.025, yy - 0.025) < 0.04)[..., None], BRASS["hi"], col)
    if ex.get("arete"):
        col = np.where(((y < 0.05) | (y > L - 0.05))[..., None], COPPER["low"] * 0.85, col)
    return col, None


def p_acier(xn, t, y, r, L, ex):
    k = np.clip(0.25 + 0.6 * (1 - np.abs(xn) ** 1.3) + ex.get("clair", 0.0), 0, 1)
    return lerp(STEEL["low"], STEEL["hi"], k[..., None]), None


def p_poli(xn, t, y, r, L, ex):
    k = np.clip(0.2 + 0.7 * (1 - np.abs(xn) ** 1.2) + ex.get("clair", 0.0), 0, 1)
    col = lerp(STEEL["base"], POLI, k[..., None])
    return np.where((np.abs(xn) < 0.18)[..., None], lerp(col, FIL, 0.5), col), None


def p_bois(xn, t, y, r, L, ex):
    s = ex.get("seed", 0.0)
    g = np.sin(xn * 5.0 + np.sin(y * 1.1 + s) * 1.6 + s)
    k = np.clip(0.42 + 0.14 * g + 0.22 * (1 - np.abs(xn) ** 1.5) - 0.1, 0, 1)
    col = lerp(WOOD["low"], WOOD["hi"], k[..., None])
    vein = np.sin(xn * 13.0 + np.sin(y * 2.3 + s) * 2.2) > 0.9
    return np.where(vein[..., None], col * 0.78, col), None


def p_papier(xn, t, y, r, L, ex):
    k = np.clip(0.3 + 0.6 * (1 - np.abs(xn) ** 1.3), 0, 1)
    col = lerp(PAPER["low"], PAPER["hi"], k[..., None])
    tours = ((y * 5.0 + xn * 0.6) % 1.0) < 0.12
    return np.where(tours[..., None], col * 0.84, col), None


def p_creme(xn, t, y, r, L, ex):
    col = lerp(CREME * 0.72, CREME, np.clip(1 - np.abs(xn) ** 1.4, 0, 1)[..., None])
    col = np.where((np.abs(y - L / 2) < 0.04)[..., None] & (np.abs(xn) < 0.6)[..., None], Af((120, 40, 30)), col)
    return col, None


def p_ambre(xn, t, y, r, L, ex):
    q = np.abs(xn + 0.25)
    col = lerp(Af((255, 236, 180)), AMBRE_B, np.clip(q / 1.2, 0, 1)[..., None] ** 0.9)
    em = lerp(Af((225, 170, 80)), Af((160, 100, 30)), np.clip(np.abs(xn), 0, 1)[..., None])
    return col, em


def p_ambre_eteint(xn, t, y, r, L, ex):
    q = np.abs(xn + 0.25)
    return lerp(Af((176, 120, 52)), Af((92, 56, 22)), np.clip(q / 1.2, 0, 1)[..., None] ** 0.9), None


PEINTRES = {"laiton": p_laiton, "cuivre": p_cuivre, "acier": p_acier, "poli": p_poli, "bois": p_bois, "papier": p_papier,
            "creme": p_creme, "ambre": p_ambre, "ambre_eteint": p_ambre_eteint}


def tuile_pan(nom, mat, L, w0, w1, r0, r1, ex):
    """Tuile d'un pan trapézoïdal : rangée 0 = bout P1 (haut de la face south)."""
    if nom in TILES:
        return nom
    wm = max(w0, w1) + 2 * OVW
    Lf = L + 2 * OVL
    Wt, Ht = max(2, int(math.ceil(wm * DENS))), max(2, int(math.ceil(Lf * DENS)))
    yy, xx = np.mgrid[0:Ht, 0:Wt]
    x = ((xx + 0.5) / Wt - 0.5) * wm
    y = Lf * (1 - (yy + 0.5) / Ht) - OVL
    t = np.clip(y / max(L, 1e-6), 0, 1)
    hw = (w0 + (w1 - w0) * t) / 2 + OVW
    mask = np.abs(x) <= hw
    xn = np.clip(x / np.maximum(hw - OVW, 1e-3), -1, 1)
    r = r0 + (r1 - r0) * t
    ex = dict(ex)
    ex.setdefault("demi", max(w0, w1) / 2)
    col, em = PEINTRES[mat](xn, t, y, r, L, ex)
    return tuile(nom, *finir(col, None, em, mask))


def tour(g, nom, O, ax, ref, profil, n=12, phase=0.0):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] le long de ax depuis O (monde) ; une couronne de n pans par tronçon.
    Les tuiles sont nommées par `nom` : deux tours de même nom et même profil partagent leurs tuiles."""
    O, ax = np.asarray(O, float), unit(ax)
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    for i, (b0, r0, b1, r1, mat, ex) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        if L < 1e-4:
            continue
        tile = tuile_pan(f"{nom}{i}", mat, L, 2 * r0 * tn, 2 * r1 * tn, r0, r1, ex)
        db, dr = (b1 - b0) / L, (r1 - r0) / L
        wm = max(2 * r0 * tn, 2 * r1 * tn) + 2 * OVW
        for k in range(n):
            th = phase + TAU * k / n
            e = math.cos(th) * ref + math.sin(th) * w3
            Pa, Pb = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(Pb - Pa)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            CUBES.append({"groupe": g, "nom": f"{nom}{i}_{k}", "c": (Pa + Pb) / 2 - N * TH / 2, "R": np.column_stack([X, Y, N]),
                          "half": np.array((wm / 2, L / 2 + OVL, TH / 2)), "faces": {"south": tile}})


def bague(b, r_in, r_out, long, mat="laiton", ex=None):
    ex = dict(ex or {})
    fl = {k: v for k, v in ex.items() if k != "riv"}
    return [(b, r_in, b, r_out, mat, dict(fl)), (b, r_out, b + long, r_out, mat, dict(ex, arete=True)), (b + long, r_out, b + long, r_in, mat, dict(fl))]


def tige(g, nom, p, q, r, mat="acier", n=6, bouts=True, ref=T_):
    """Tige ronde (tour à n pans) de p à q, bouts fermés en option."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    Ln = float(np.linalg.norm(q - p))
    ax = q - p
    if abs(unit(ax) @ unit(ref)) > 0.95:
        ref = A_ if abs(unit(ax) @ A_) < 0.9 else W_
    prof = []
    if bouts:
        prof.append((0.0, 0.0, 0.0, r, mat, {"clair": 0.1}))
    prof.append((-0.0 if bouts else -0.06, r, Ln + (0.0 if bouts else 0.06), r, mat, {}))
    if bouts:
        prof.append((Ln, r, Ln, 0.0, mat, {"clair": 0.1}))
    tour(g, nom, p, ax, ref, prof, n=n, phase=math.pi / n)


# ------------------------------------------------------------------ tuiles peintes (cadran, engrenage, foyer, vapeur)
def disque_t(n, fn, ss=4):
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    X, Y = (xx + 0.5 - N / 2) / (N / 2), -(yy + 0.5 - N / 2) / (N / 2)
    R = np.hypot(X, Y)
    res = fn(X, Y, R)
    col, em = res[0], res[1]
    m = res[2] if len(res) > 2 else R < 0.985
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.LANCZOS)).astype(np.float32)
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((n, n), Image.LANCZOS)) > 110
    e = None
    if em is not None:
        e = np.array(Image.fromarray(np.clip(em, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.NEAREST)).astype(np.float32)
    return finir(rgb, None, e, al)


def f_cadran(X, Y, R):
    """Cadran : verre ambre, 13 crans (-120° à +120° depuis le haut, sens horaire), zone rouge en haut de l'échelle, reflet."""
    col = lerp(BRASS["hi"], BRASS["low"], np.clip(0.5 - 0.5 * Y, 0, 1)[..., None] * 0.8) * np.ones(R.shape + (1,), np.float32)
    em = np.zeros(R.shape + (3,), np.float32)
    ang = np.degrees(np.arctan2(X, Y))
    glass = R < 0.86
    col[(R > 0.86) & (R < 0.92)] = BRASS["low"] * 0.7
    g = lerp(AMBRE, AMBRE_B, np.clip(R / 0.86, 0, 1)[..., None] ** 1.5)
    col[glass] = g[glass]
    em[glass] = (190, 126, 40)
    red = glass & (R > 0.52) & (R < 0.78) & (ang > 84) & (ang < 124)
    col[red] = (176, 44, 30)
    em[red] = (150, 30, 14)
    for k in range(13):
        a = -120 + 20 * k
        r0 = 0.52 if k % 2 == 0 else 0.64
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        along = X * sa + Y * ca
        across = np.abs(X * ca - Y * sa)
        tick = glass & (along > r0) & (along < 0.8) & (across < (0.065 if k % 2 == 0 else 0.045))
        col[tick] = (58, 32, 18)
        em[tick] = 0
    hl = glass & (np.abs(R - 0.68) < 0.04) & (ang < -40) & (ang > -95)
    col[hl] = lerp(AMBRE, VAPEUR, 0.7)
    return col, em


def f_engrenage(X, Y, R):
    """Face de l'engrenage (jante à 16 pans au-delà) : jante polie, quatre fenêtres découpées, rayons, moyeu d'acier."""
    th = np.arctan2(Y, X)
    win = (R > 0.36) & (R < 0.70)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        dd = np.abs(-X * math.sin(a) + Y * math.cos(a))
        along = X * math.cos(a) + Y * math.sin(a)
        win &= ~((dd < 0.12) & (along > 0))
    sh = X * -0.6 + Y * 0.8
    col = BRASS["base"] * np.ones(R.shape + (3,), np.float32)
    col = lerp(col, BRASS["hi"], (np.clip(sh, 0, 1) * 0.5)[..., None])
    col = lerp(col, BRASS["low"], (np.clip(-sh, 0, 1) * 0.45)[..., None])
    col[(R > 0.70) & (R < 0.76)] = BRASS["low"] * 0.85
    col[(R > 0.31) & (R < 0.36)] = BRASS["low"] * 0.85
    col[R > 0.93] = BRASS["hi"]
    col[R < 0.2] = STEEL["base"]
    col[R < 0.09] = STEEL["low"]
    return col, None, (R < 0.995) & ~win


def t_unie(c0, c1, W=16, H=8, bord=None):
    col = lerp(c0, c1, np.linspace(0, 1, H)[:, None, None] * np.ones((1, W, 1), np.float32))
    if bord is not None:
        col[0] = col[-1] = bord
        col[:, 0] = col[:, -1] = bord
    return finir(col, None, None, np.ones((H, W), bool))


def t_aiguille():
    c = np.zeros((16, 4, 3), np.float32) + Af((34, 28, 26))
    c[:6] = (190, 44, 30)
    c[:, :1] *= 1.5
    return finir(c, None, None, np.ones((16, 4), bool))


def t_foyer(W=28, H=12):
    """Porte de foyer sous le réservoir : cadre d'acier, 3 fentes rougeoyantes (_e vif)."""
    c = STEEL["base"] * np.ones((H, W, 3), np.float32)
    c[:2], c[:, :2] = STEEL["hi"], STEEL["hi"]
    c[-2:], c[:, -2:] = STEEL["low"], STEEL["low"]
    e = np.zeros((H, W, 3), np.float32)
    for x0 in (6, 12, 18):
        c[3:H - 3, x0:x0 + 3] = (255, 150, 52)
        c[4:H - 4, x0 + 1] = (255, 214, 120)
        e[3:H - 3, x0:x0 + 3] = (225, 112, 28)
        e[4:H - 4, x0 + 1] = (225, 170, 70)
    return finir(c, None, e, np.ones((H, W), bool))


def cell_noise(h, w, cy, cx, seed):
    r = np.random.default_rng(seed)
    a = (r.random((cy + 2, cx + 2)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((w, h), Image.BICUBIC), np.float32) / 255


def t_vapeur(W, H, seed):
    """Jet de vapeur en dégradé d'opacité (alpha 1–254), blanc légèrement bleuté ; u = 0 à la soupape, 1 au bout du jet."""
    ss = 3
    yy, xx = np.mgrid[0:H * ss, 0:W * ss]
    u = (xx + 0.5) / (W * ss)
    v = (yy + 0.5) / (H * ss) * 2 - 1
    n1 = cell_noise(H * ss, W * ss, 4, 9, seed)
    n2 = cell_noise(H * ss, W * ss, 9, 22, seed + 1)
    lump = 0.78 + 0.32 * n1 + 0.12 * n2
    hw = lerp(0.24, 0.96, u ** 0.55) * (0.82 + 0.25 * n1)
    prof = np.clip(1 - (np.abs(v) / np.maximum(hw, 1e-3)) ** 2, 0, 1) ** 0.6
    along = np.clip(u / 0.05, 0, 1) * np.clip(1 - u ** 1.7, 0, 1)
    a = np.clip(250 * prof * along * lump, 0, 254)
    c = lerp(VAPEUR_B, VAPEUR, np.clip(1 - np.abs(v) * 0.8, 0, 1)[..., None])
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(a.astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(np.int32)
    al[al < 10] = 0
    al = np.clip(al, 0, 254)
    out = np.dstack([rgb, al]).astype(np.uint8)
    out[al == 0, :3] = VAPEUR_B.astype(np.uint8)
    return out, None


TILES["cadran"] = disque_t(26, f_cadran)
TILES["engrenage"] = disque_t(40, f_engrenage)
TILES["aiguille"] = t_aiguille()
TILES["foyer"] = t_foyer()
TILES["dent"] = t_unie(BRASS["hi"], BRASS["base"], W=8, H=8, bord=BRASS["low"])
TILES["acier_b"] = t_unie(STEEL["hi"], STEEL["low"], bord=STEEL["low"])
TILES["jet"] = t_vapeur(112, 52, 71)
TRANS.add("jet")


# ------------------------------------------------------------------ conception (cotes de la version d'avant)
GROUPES = []        # (nom, pivot monde, parent, rotation)


def grp(nom, pivot, parent, rotation=(0.0, 0.0, 0.0)):
    GROUPES.append((nom, np.asarray(pivot, float), parent, rotation))
    return nom


T_RAIL = 1.32              # dessus des rails
T_STR = 1.45               # hauteur de la corde
T_BOLT = 1.55              # axe du carreau
A_PROD = 4.5               # racine de l'arc
T_LEAF = 0.2               # plan médian des lames
A_GEAR = -5.4
A_LENS = -3.52
A_DIAL, W_RES = -1.0, -2.1
A_SOUP = 1.0               # soupape (dessus du réservoir)
T_DIAL = 1.36              # dessus du verre du cadran
A_LATCH = -2.25

# lames de ressort (version d'avant) : tronçons, demi-hauteurs, lames étagées
SEG_L = (1.9, 1.75, 1.6, 1.45)
HALF_T = (0.86, 0.75, 0.64, 0.53)
FEUILLES = [(0, 0.0, (1, 1, 1, 1)), (1, 0.45, (1, 1, 0.5)), (2, 0.9, (1, 0.45))]
DEMI_EP = 0.3              # demi-épaisseur d'une lame (vue de dessus)
ETAPES = [("repos", 0.0, 180, 0.0, False, None), ("bande_1", 0.33, 300, 0.33, False, None), ("bande_2", 0.66, 60, 0.62, False, None),
          ("bande_3", 1.0, 165, 0.86, False, None), ("chargee", 1.0, 180, 1.0, True, "carreau"), ("chargee_fusee", 1.0, 180, 1.0, True, "fusee")]


def pliage(d):
    return [b * (1 + 1.05 * d) for b in (3.0, 9.0, 15.0, 21.0)]


def lames(g, s, d):
    """Une branche (côté s = ±1) : trois lames étagées vers l'arrière ; chaque tronçon = plaque fermée biseautée dans son propre
    cadre (tuiles partagées entre côtés et étapes) ; renvoie le bout de la lame maîtresse (a, w)."""
    phis = pliage(d)
    tip = None
    for j, back, parts in FEUILLES:
        p = np.array((A_PROD, s * 0.25))
        for k, frac in enumerate(parts):
            phi = math.radians(phis[k])
            dv = np.array((-math.sin(phi), s * math.cos(phi)))          # (a, w), vers le bout
            nv = np.array((math.cos(phi), s * math.sin(phi)))           # vers l'avant
            L = SEG_L[k] * frac
            q = p + dv * L
            c2 = (p + q) / 2 - nv * back
            last = k == len(parts) - 1
            e0 = 0.0 if k == 0 else 0.1
            e1 = 0.0 if last else 0.1
            U = A_ * dv[0] + W_ * dv[1]
            F = Cadre(P(c2[0], c2[1], T_LEAF), U, np.cross(T_, U))
            h = HALF_T[k] - 0.06 * j
            poly = rect(-L / 2 - e0, L / 2 + e1, -DEMI_EP, DEMI_EP, ch=0.08 if last else 0.0)
            pc = Plaque(f"lame{j}{k}_{'dg'[s < 0]}", poly, h, h - 0.16, 1.0, mat_lame(rivet_s=(-L / 2 + 0.3) if k == 0 else None),
                        seg=2.2, cle=f"lame{j}{k}")
            volume_plaque(pc, g, F)
            p = q
        if j == 0:
            tip = p
    return tip


OUT = {}


def conception():
    fixe = grp("arbalete", (8, 8, 8), None)
    FC = F_COTE()

    # --- bois : crosse à talon, poignée (plaques fermées biseautées, section octogonale) ; fût octogonal en tour
    CROSSE = [(-5.5, 1.15), (-9.45, 1.15), (-9.45, -1.55), (-9.15, -1.92), (-6.05, -1.15), (-5.5, -1.15)]
    volume_plaque(Plaque("crosse", CROSSE, 1.15, 0.48, 1.0, mat_bois(seed=1.0), seg=1.4), fixe, FC)
    POIGNEE = bande_poly([(-4.95, -0.55), (-5.4, -1.8), (-5.9, -3.0)], 0.55)
    volume_plaque(Plaque("poignee", POIGNEE, 0.55, 0.25, 1.0, mat_bois(ax=tuple(unit((-0.9, -2.4))), seed=4.0), seg=1.0), fixe, FC)
    tour(fixe, "fut", P(-5.85), A_, T_, [(0.0, 0.9, 12.1, 0.9, "bois", {"seed": 2.0})], n=8, phase=0.0)
    # plaque de couche de laiton rivetée (plan w, t)
    volume_plaque(Plaque("plaque_couche", rect(-1.7, 1.7, -1.7, 0.9, ch=0.35), 0.275, 0.12, 1.0,
                         mat_laiton(rivets=((-1.15, 0.4, 0.13), (1.15, 0.4, 0.13), (-1.15, -1.2, 0.13), (1.15, -1.2, 0.13)), rainure=(0.12, 0.17))),
                  fixe, F_DOS(-9.575))
    # bagues rivetées sur le fût et la crosse, nez de laiton
    for nm, a0, a1, r_in, r_out in (("bague_crosse", -5.75, -5.4, 1.15, 1.27), ("bague_fut", 1.3, 1.65, 0.88, 1.02), ("bague_nez", 5.55, 5.85, 0.88, 1.02)):
        tour(fixe, nm, P(0), A_, T_, bague(a0, r_in, r_out, a1 - a0, "laiton", {"riv": True}), n=8, phase=0.0)
    tour(fixe, "nez", P(0), A_, T_, [(6.0, 0.88, 6.0, 1.05, "laiton", {}), (6.0, 1.05, 6.5, 1.05, "laiton", {"arete": True}),
                                     (6.5, 1.05, 6.6, 0.8, "laiton", {"clair": 0.1}), (6.6, 0.8, 6.6, 0.0, "laiton", {"clair": 0.2})], n=8, phase=0.0)
    # étrier de pied d'acier (plaque en U dans le plan a, w)
    ETRIER = [(6.25, 1.02), (8.12, 1.02), (8.12, -1.02), (6.25, -1.02), (6.25, -0.68), (7.78, -0.68), (7.78, 0.68), (6.25, 0.68)]
    volume_plaque(Plaque("etrier_pied", ETRIER, 0.17, 0.08, 1.0, mat_acier(), seg=1.0), fixe, F_DESSUS(-0.6))
    # rails de laiton (rainure du carreau)
    for s in (1, -1):
        volume_plaque(Plaque(f"rail_{'dg'[s < 0]}", rect(-3.2, 6.3, 0.75, T_RAIL, ch=0.08), 0.15, 0.07, 1.0, mat_laiton(), seg=2.5, cle="rail"),
                      fixe, F_COTE(w0=s * 0.55))
    # étrier de l'arc : bloc de laiton riveté (plan a, w), lames et fût le traversent
    volume_plaque(Plaque("etrier_arc", rect(3.05, 5.25, -1.3, 1.3, ch=0.2), 1.25, 1.0, 1.0,
                         mat_laiton(rivets=((3.45, 0.95, 0.13), (4.85, 0.95, 0.13), (3.45, -0.95, 0.13), (4.85, -0.95, 0.13)), rainure=(0.1, 0.15))),
                  fixe, F_DESSUS(-0.05))
    # noix : boîtier de laiton (la lentille est dans les étapes)
    volume_plaque(Plaque("noix", rect(-3.95, -3.1, 0.55, 2.3, ch=0.12), 1.05, 0.85, 1.0, mat_laiton(rivets=((-3.52, 1.0, 0.12),), rainure=(0.08, 0.12))),
                  fixe, FC)
    # tambour du remontage (sous l'engrenage)
    tour(fixe, "tambour", P(A_GEAR, 0, 0.7), T_, A_, [(0.0, 0.55, 1.15, 0.55, "acier", {})], n=8, phase=math.pi / 8)
    # détente d'acier poli, pontet de laiton
    volume_plaque(Plaque("detente", bande_poly([(-3.88, -0.6), (-3.72, -1.15), (-3.52, -1.65)], 0.12), 0.12, 0.05, 1.0, mat_acier_poli(), seg=0.6), fixe, FC)
    volume_plaque(Plaque("pontet", bande_poly([(-2.85, -0.7), (-3.15, -2.0), (-5.05, -2.15), (-5.25, -1.85)], 0.13), 0.13, 0.06, 1.0,
                         mat_laiton(ax=(1.0, 0.0)), seg=0.9), fixe, FC)

    # --- réservoir de vapeur de cuivre (flanc gauche) : fonds bombés de laiton, cerclages, pattes, tuyau à vanne, manomètre
    rs = [(-1.98, 0.0, -1.95, 0.3, "laiton", {"clair": 0.2}), (-1.95, 0.3, -1.8, 0.5, "laiton", {"clair": 0.1}), (-1.8, 0.5, -1.6, 0.56, "laiton", {}),
          (-1.6, 0.56, -1.6, 0.78, "cuivre", {}), (-1.6, 0.78, 2.4, 0.78, "cuivre", {}),
          (2.4, 0.78, 2.4, 0.56, "cuivre", {}), (2.4, 0.56, 2.6, 0.5, "laiton", {}), (2.6, 0.5, 2.75, 0.3, "laiton", {"clair": 0.1}),
          (2.75, 0.3, 2.78, 0.0, "laiton", {"clair": 0.2})]
    tour(fixe, "reservoir", P(0, W_RES), A_, T_, rs, n=12, phase=math.pi / 12)
    for nm, a0 in (("cercle_ar", -0.2), ("cercle_av", 1.5)):
        tour(fixe, nm, P(0, W_RES), A_, T_, bague(a0, 0.78, 0.9, 0.35, "laiton", {"riv": True}), n=12, phase=math.pi / 12)
    for nm, a0 in (("patte_ar", -0.02), ("patte_av", 1.68)):
        tige(fixe, nm, P(a0, -1.4), P(a0, -0.6), 0.15, "laiton", n=6, bouts=False)
    # porte de foyer sous le réservoir (face -T_) : fentes rougeoyantes vues de dessous et en main
    boite(fixe, "foyer", P(0.4, W_RES, -0.84), A_, -W_, (1.3, 0.56, 0.08), {"south": "foyer"})
    # tuyau de cuivre vers le boîtier du tambour, vanne de laiton, coude
    tige(fixe, "tuyau", P(-1.7, W_RES), P(-4.7, W_RES), 0.2, "cuivre", n=8, bouts=False)
    tige(fixe, "coude", P(-4.7, W_RES - 0.2), P(-4.7, -0.6), 0.28, "cuivre", n=8, bouts=False)
    tour(fixe, "coude_c", P(-4.7, W_RES), W_, T_, [(-0.32, 0.0, -0.32, 0.3, "cuivre", {"clair": 0.15})], n=8, phase=math.pi / 8)
    tour(fixe, "vanne", P(0, W_RES), A_, T_, bague(-3.3, 0.2, 0.34, 0.3, "laiton", {}), n=8, phase=math.pi / 8)
    # manomètre sur le dessus : col de cuivre, boîtier et lunette de laiton à 16 pans, cadran ambre (aiguille dans les étapes)
    tour(fixe, "col_cadran", P(A_DIAL, W_RES), T_, A_, [(0.6, 0.28, 0.98, 0.28, "cuivre", {})], n=8, phase=math.pi / 8)
    tour(fixe, "manometre", P(A_DIAL, W_RES), T_, A_,
         [(0.95, 0.28, 0.95, 0.76, "laiton", {}), (0.95, 0.76, 1.2, 0.76, "laiton", {}), (1.2, 0.76, 1.2, 0.86, "laiton", {}),
          (1.2, 0.86, 1.36, 0.86, "laiton", {"arete": True}), (1.36, 0.86, 1.38, 0.74, "laiton", {"clair": 0.2})], n=16, phase=math.pi / 16)
    boite(fixe, "cadran", P(A_DIAL, W_RES, T_DIAL - 0.06), -W_, A_, (1.5, 1.5, 0.12), {"south": "cadran"})
    boite(fixe, "cadran_moyeu", P(A_DIAL, W_RES, T_DIAL + 0.05), -W_, A_, (0.14, 0.14, 0.08), {f: "acier_b" for f in SIX})

    # --- soupape (dessus du réservoir) : tige d'acier, chapeau de laiton mobile, jet caché dedans
    vb = P(A_SOUP, W_RES, 0.74)
    tour(fixe, "soupape_tige", vb, T_, A_, [(0.0, 0.13, 0.42, 0.13, "acier", {})], n=8)
    soup = grp("soupape", vb + T_ * 0.4, fixe)
    tour(soup, "soupape_chapeau", vb, T_, A_, [(0.36, 0.13, 0.36, 0.28, "laiton", {}), (0.36, 0.28, 0.58, 0.28, "laiton", {"arete": True}),
                                               (0.58, 0.28, 0.62, 0.12, "laiton", {}), (0.62, 0.12, 0.72, 0.12, "laiton", {"clair": 0.1}),
                                               (0.72, 0.12, 0.75, 0.0, "laiton", {"clair": 0.2})], n=8)
    jb = vb + T_ * 0.38
    jet = grp("trans_jet", jb, soup)
    JL, JW = 4.2, 2.2
    for k in range(3):
        ang = math.radians(60 * k)
        Yp = A_ * math.cos(ang) + W_ * math.sin(ang)
        boite(jet, f"jet{k}", jb + T_ * (JL / 2 * F_GEO / K), T_, Yp, np.array((JL, JW, 0.3)) * F_GEO / K, {"south": "jet", "north": "jet"})
    grp("ctrl_alpha", jb, jet)
    # vapeur de Minecraft à la soupape : +Y du groupe vers T_ (rotation X +90°)
    em_s = grp("emit_mc_white_smoke", jb + T_ * 0.3, soup, rotation=(90, 0, 0))
    grp("ctrl_emit", jb + T_ * 0.3, em_s)

    # ================================================================== étapes
    stage, aig = {}, {}
    for nom_e, d, crank, level, lit, charge in ETAPES:
        g = grp(objet.etape(nom_e, "arbalete"), (8, 8, 8), None)
        stage[nom_e] = g
        tips = {}
        for s in (1, -1):
            tip = lames(g, s, d)
            tips[s] = tip
            tour(g, "teton", P(tip[0], tip[1], T_LEAF - 0.8), T_, A_,
                 [(0.0, 0.0, 0.0, 0.3, "poli", {}), (0.0, 0.3, 2.6, 0.3, "acier", {}), (2.6, 0.3, 2.65, 0.18, "poli", {}),
                  (2.65, 0.18, 2.7, 0.0, "poli", {"clair": 0.2})], n=8, phase=math.pi / 8)
        a_s = tips[1][0] - 0.05 if d == 0 else lerp(tips[1][0] - 0.05, A_LATCH, d)
        # corde (câble d'acier)
        if d == 0:
            tige(g, f"corde_{nom_e}", P(tips[-1][0], tips[-1][1], T_STR), P(tips[1][0], tips[1][1], T_STR), 0.12, "acier", n=6, bouts=False)
        else:
            for s in (1, -1):
                tige(g, f"corde_{nom_e}_{'dg'[s < 0]}", P(tips[s][0], tips[s][1], T_STR), P(a_s, 0, T_STR), 0.12, "acier", n=6, bouts=False)
        # griffe de laiton derrière la corde, câble vers le tambour
        ag = a_s - 0.425 - (0.12 if d == 0 else 0.0)
        volume_plaque(Plaque(f"griffe_{nom_e}", rect(-0.275, 0.275, -0.4625, 0.4625, ch=0.08), 0.3, 0.18, 1.0, mat_laiton(), cle="griffe"),
                      g, F_COTE(a0=ag, t0=1.5125))
        tige(g, f"cable_{nom_e}", P(ag - 0.2, 0, 1.5), P(A_GEAR + 0.5, 0, 1.5), 0.08, "acier", n=6, bouts=False)
        # engrenage (axe vertical), moyeu, manivelle : tournent ensemble
        ang = math.radians(crank)
        Xc = A_ * math.cos(ang) + W_ * math.sin(ang)
        ce = P(A_GEAR, 0, 1.85)
        boite(g, "eng_face", ce, np.cross(Xc, T_), Xc, (2.5, 2.5, 0.4), {"south": "engrenage", "north": "engrenage"})
        tour(g, "eng_flanc", P(A_GEAR, 0, 1.66), T_, Xc, [(0.0, 1.2, 0.38, 1.2, "laiton", {"arete": True})], n=16, phase=math.pi / 16)
        for k in range(14):
            th = TAU * (k + 0.5) / 14
            e_ = Xc * math.cos(th) + np.cross(T_, Xc) * math.sin(th)
            boite(g, "dent", ce + e_ * 1.35, np.cross(T_, e_), e_, (0.32, 0.34, 0.34), {f: "dent" for f in SIX})
        tour(g, "moyeu", P(A_GEAR, 0, 2.03), T_, Xc, [(0.0, 0.42, 0.32, 0.42, "laiton", {"arete": True}), (0.32, 0.42, 0.36, 0.0, "laiton", {"clair": 0.2})],
             n=8, phase=math.pi / 8)
        hc = P(A_GEAR, 0, 0) + Xc * 1.35
        tige(g, "manivelle", P(A_GEAR, 0, 2.3), hc + T_ * 2.3, 0.13, "laiton", n=6, bouts=False)
        tour(g, "poignee_manivelle", hc + T_ * 2.2, T_, Xc, [(0.0, 0.25, 0.9, 0.25, "bois", {"seed": 5.0}),
                                                            (0.9, 0.25, 0.95, 0.0, "laiton", {"clair": 0.15})], n=8, phase=math.pi / 8)
        # aiguille du manomètre (−120° au repos, +120° bandée à fond) : groupe qui tourne autour de T_
        c0 = P(A_DIAL, W_RES, T_DIAL + 0.04)
        ga = grp(f"aiguille_{nom_e}", c0, g)
        th_n = math.radians(-120 + 240 * level)
        dn = A_ * math.cos(th_n) - W_ * math.sin(th_n)
        boite(ga, "aiguille", c0 + dn * 0.26, np.cross(dn, T_), dn, (0.11, 0.62, 0.05), {f: "aiguille" for f in SIX})
        aig[nom_e] = ga
        # lentille de la noix : éteinte, puis allumée une fois chargée
        mat = "ambre" if lit else "ambre_eteint"
        tour(g, "lentille_" + ("on" if lit else "off"), P(A_LENS, 0, 2.1), T_, A_,
             [(0.0, 0.3, 0.32, 0.3, "laiton", {}), (0.32, 0.3, 0.32, 0.45, "laiton", {}), (0.32, 0.45, 0.42, 0.45, "laiton", {"arete": True}),
              (0.42, 0.45, 0.42, 0.33, "laiton", {"clair": 0.1}), (0.42, 0.33, 0.5, 0.22, mat, {}), (0.5, 0.22, 0.54, 0.0, mat, {})],
             n=12, phase=math.pi / 12)
        if charge == "carreau":
            ca = [(-2.75, 0.0, -2.75, 0.16, "acier", {}), (-2.75, 0.16, 6.3, 0.16, "acier", {})]
            ca += bague(6.25, 0.16, 0.28, 0.65, "laiton")
            ca += [(6.9, 0.16, 6.9, 0.4, "poli", {}), (6.9, 0.4, 7.8, 0.0, "poli", {"clair": 0.1})]
            tour(g, "carreau", P(0, 0, T_BOLT), A_, T_, ca, n=6, phase=0.0)
            PEN = [(-2.25, 0.0), (-2.25, 0.2), (-1.7, 0.8), (-1.0, 0.8), (-0.6, 0.0)]
            volume_plaque(Plaque("penne_haut", PEN, 0.1, 0.04, 1.0, mat_cuivre_penne(), seg=0.8, cle="penne"), g, F_COTE(t0=T_BOLT + 0.12))
            for s in (1, -1):
                Fp = Cadre(P(0, s * 0.12, T_BOLT - 0.05), A_, W_ * s)
                volume_plaque(Plaque(f"penne_{'dg'[s < 0]}", PEN, 0.1, 0.04, 1.0, mat_cuivre_penne(), seg=0.8, cle="penne"), g, Fp)
        elif charge == "fusee":
            tf = 1.9
            fu = [(-2.7, 0.0, -2.7, 0.42, "papier", {})]
            for b0, b1, m in ((-2.7, -2.46, "papier"), (-2.46, -2.22, "laiton"), (-2.22, -1.5, "papier"), (-1.5, -0.95, "creme"),
                              (-0.95, -0.1, "papier"), (-0.1, 0.14, "laiton"), (0.14, 0.3, "papier")):
                fu.append((b0, 0.42 if m != "laiton" else 0.46, b1, 0.42 if m != "laiton" else 0.46, m, {"arete": m == "laiton"}))
            fu += [(0.3, 0.42, 0.75, 0.25, "papier", {}), (0.75, 0.25, 1.15, 0.0, "papier", {})]
            tour(g, "fusee", P(0, 0, tf), A_, T_, fu, n=8, phase=math.pi / 8)
            tige(g, "meche", P(-2.65, 0, tf), P(-3.05, 0, tf - 0.2), 0.07, "acier", n=4, bouts=True)
    OUT.update(stage=stage, aig=aig, soupape=soup, jet=jet)


conception()


# ------------------------------------------------------------------ atlas
def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, (im, ime) in sorted(TILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1], it[0])):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, f"atlas plein ({n}, y = {y})"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None and AVEC_E:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    assert tex[TEX - 2, TEX - 2, 3] == 0
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    zone = np.zeros(semi.shape, bool)
    for n in TRANS:
        u0, v0, u1, v1 = UV[n]
        zone[v0:v1, u0:u1] = True
    assert not (semi & ~zone).any(), "semi-transparence hors des tuiles trans_"
    assert set(np.unique(tex_e[..., 3])) <= {0, 255}
    print(f"atlas : {len(TILES)} tuiles, rangées jusqu'à y = {y + shelf}")
    res = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        res.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return res


tex_b64, tex_e_b64 = atlas()


def euler(R):
    """Angles (X, Y, Z) tels que R = Rz Ry Rx ; blocage de cardan (Y = ±90°) : tout l'angle sur X."""
    if abs(R[2, 0]) < 1 - 1e-9:
        e = (math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(math.asin(-R[2, 0])), math.degrees(math.atan2(R[1, 0], R[0, 0])))
    elif R[2, 0] < 0:
        e = (math.degrees(math.atan2(R[0, 1], R[0, 2])), 90.0, 0.0)
    else:
        e = (math.degrees(math.atan2(-R[0, 1], -R[0, 2])), -90.0, 0.0)
    assert np.allclose(rotm(*e), R, atol=1e-5), "euler"
    return e


def nuid():
    return str(_uuid.uuid4())


elements, groups = [], {}
for nom, piv, parent, r in GROUPES:
    assert nom not in groups and len(nom) <= 64, nom
    groups[nom] = {"origin": [round(float(v), 4) for v in piv], "uuid": nuid(), "ids": [], "parent": parent,
                   "rotation": [round(float(v), 3) for v in r]}
for cb in CUBES:
    c, h = cb["c"], cb["half"]
    R = cb["R"]
    assert abs(np.linalg.det(R) - 1) < 1e-6, cb["nom"]
    rot = euler(R)
    e = {"name": cb["nom"], "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in c - h],
         "to": [round(float(v), 4) for v in c + h], "origin": [round(float(v), 4) for v in c], "box_uv": False,
         "faces": {f: {"uv": list(UV[cb["faces"][f]]) if f in cb["faces"] else CLEAR, "texture": 0} for f in SIX}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[cb["groupe"]]["ids"].append(e["uuid"])


def bone_node(name):
    g = groups[name]
    return {"name": name.split("@")[0], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node(n) for n, gg in groups.items() if gg["parent"] is None]


# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def kf(t, x, y, z, ch="rotation"):
    f = lambda v: v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, tracks, fps=24, loop="loop"):
    """tracks : {(groupe, canal): f(t) -> (x, y, z)} échantillonné, ou (x, y, z) constant (Molang permis)."""
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A__ = {}
    for (g, ch), f in tracks.items():
        ks = [kf(t, *f(t), ch=ch) for t in times] if callable(f) else [kf(0.0, *f, ch=ch), kf(length, *f, ch=ch)]
        A__.setdefault(groups[g]["uuid"], {"name": g.split("@")[0], "type": "bone", "keyframes": []})["keyframes"] += ks
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": False, "animators": A__}


def step(tau, rise=0.05, over=0.28):
    """Échelon de servo : montée courte, dépassement puis rappel amorti (un rebond)."""
    if tau <= 0:
        return 0.0
    v = sm(tau, 0.0, rise)
    if tau > rise * 0.6:
        x = tau - rise * 0.6
        v += over * math.sin(TAU * x / 0.15) * math.exp(-x / 0.045)
    return v


def le_long(v, d):
    w = np.asarray(d, float) * v
    return float(w[0]), float(w[1]), float(w[2])


def needle(dl):
    """Rotation de l'aiguille pour un écart de niveau dl (1 = 240° ; monter = sens horaire vu de +Z = z négatif)."""
    return 0.0, 0.0, -240.0 * dl


AIG, SOUP, JET = OUT["aig"], OUT["soupape"], OUT["jet"]
CE = "ctrl_emit"

# --- item_idle (8 s) : deux crans puis retour (servo) ; chargée : tremblement dans le rouge ; vapeur coupée
L_IDLE = 8.0


def idle_level(t):
    return 0.05 * (step(t - 1.2) + step(t - 2.4)) - 0.1 * step(t - 5.6, rise=0.08, over=0.12)


idle_tracks = {(CE, "position"): (-1, 0, 0)}
for e in ("repos", "bande_1", "bande_2", "bande_3"):
    idle_tracks[(AIG[e], "rotation")] = lambda t: needle(idle_level(t))
for e in ("chargee", "chargee_fusee"):
    idle_tracks[(AIG[e], "rotation")] = lambda t: needle(0.012 * math.sin(TAU * 12 * t / L_IDLE) * math.sin(TAU * 3 * t / L_IDLE))
item_idle = anim("item_idle", L_IDLE, idle_tracks, fps=20)

# --- item_use (boucle 0,5 s) : le chargement ; l'aiguille tremble de plus en plus, la soupape fuit
TREM = "math.sin(q.anim_time * 360 * 18) * 6 * q.use_progress * q.use_progress"
VIB = "math.sin(q.anim_time * 360 * 22) * 0.04 * q.use_progress"
use_tracks = {(CE, "position"): ("q.use_progress * 3 - 1", 0, 0), (SOUP, "position"): (0, 0, VIB)}
for e in ("repos", "bande_1", "bande_2", "bande_3"):
    use_tracks[(AIG[e], "rotation")] = (0, 0, TREM)
item_use = anim("item_use", 0.5, use_tracks)

# --- event_charged (0,6 s) : la noix prend la corde, l'aiguille saute de 0,86 à 1 (zone rouge) avec un dépassement
ch_tracks = {}
for e in ("chargee", "chargee_fusee"):
    ch_tracks[(AIG[e], "rotation")] = lambda t: needle(-0.14 * (1 - step(t - 0.03, rise=0.06, over=0.35)))
event_charged = anim("event_charged", 0.6, ch_tracks, fps=40, loop="once")

# --- event_release (0,8 s) : le carreau part ; la soupape se soulève, jet de vapeur qui monte, l'aiguille retombe à zéro


def jet_scale(t):
    w = sm(t, 0.03, 0.11) * (1 + 0.3 * sm(t, 0.11, 0.45)) * (1 - sm(t, 0.55, 0.68))
    k = (1 + (K - 1) * w) / F_GEO
    return k, k, k


def jet_pos(t):
    return le_long(0.9 * sm(t, 0.12, 0.62) * (1 - sm(t, 0.66, 0.7)), T_)


def jet_alpha(t):
    return -sm(t, 0.32, 0.64) * (1 - sm(t, 0.72, 0.76)), 0.0, 0.0


def soup_lift(t):
    return le_long(0.2 * (step(t - 0.02, rise=0.035, over=0.2) - step(t - 0.3, rise=0.05, over=0.3)), T_)


rel_tracks = {(JET, "scale"): jet_scale, (JET, "position"): jet_pos, ("ctrl_alpha", "position"): jet_alpha,
              (SOUP, "position"): soup_lift, (CE, "position"): lambda t: (5 * bump(t, 0.04, 0.08, 0.4, 0.5), 0.0, 0.0),
              (AIG["repos"], "rotation"): lambda t: needle(1 - step(t - 0.035, rise=0.06, over=0.08))}
event_release = anim("event_release", 0.8, rel_tracks, fps=60, loop="once")
event_release["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "tir_vapeur", "file": ""}], "time": 0.04}]}

ANIMS = [item_idle, item_use, event_charged, event_release]
ANIMS[0]["selected"] = True


# ------------------------------------------------------------------ écriture
def coins():
    Pl = []
    for e in elements:
        f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rotm(*e.get("rotation", (0, 0, 0)))
        for i in range(8):
            c = np.array([(f, t)[(i >> k) & 1][k] for k in range(3)])
            Pl.append(R @ (c - o) + o)
    return np.array(Pl)


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
Pc = coins()
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
AFFICHAGE = objet.affichage("arbalete")       # Display de l'arbalète de Minecraft, inchangé (validé en jeu)
model = objet.modele(NOM, "arbalete", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import embarquer_sons  # noqa: E402
embarquer_sons(model, {"tir_vapeur": "sons/tir_vapeur.ogg"})   # son original synthétisé (tools/synthe.py), seul son du skin
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))
print("boîte :", Pc.min(0).round(2).tolist(), "->", Pc.max(0).round(2).tolist())
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
