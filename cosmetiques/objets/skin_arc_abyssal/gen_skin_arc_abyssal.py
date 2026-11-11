"""Envergure de l'Abysse : skin d'objet (guide 14) pour tous les arcs du joueur, ensemble Abyssal (thème Démoniaque).
Design original. Écrit skin_arc_abyssal.png, skin_arc_abyssal_e.png et .build/skin_arc_abyssal_brut.bbmodel.
Point de départ : gen_skin_lance_abyssal.py (os plein opaque en vrai volume, tours, griffes, peintures du set) ; repère,
prise, étapes et Display de gen_skin_arc_givre.py (S_ = avant, H_ = le long des branches, poing en (5, 10, 8)).

Anatomie d'un arc recourbé (.claude/references/objets/arcs.md) traduite dans le langage du set (ailes abyssales : os
fins et courbes, griffes recourbées à pointe verte) :
- chaque branche = un **long os d'aile** courbe, recourbé au bout, en vrai volume : plaque biseautée fermée (contour =
  ligne médiane décalée de ±1,00 -> 0,52 px, bout arrondi), section hexagonale (plats ±Z, biseaux à pente unique 55°),
  amincie 1,60 -> 0,72 px le long de la corde de la branche ; bords d'os nu à liseré violacé (une branche n'a pas de
  tranchant) ; **gouttière creusée** le long de la branche, filet vert acide + _e couché au fond ;
- au bout, une **serre** (griffe conique recourbée vers l'avant, pointe verte + _e) dans une bague d'os violacée : la
  corde s'accroche sous la bague ; deux **griffes d'aile** sur le dos de chaque branche (pointes vertes) ;
- poignée d'os à 12 pans : collets d'os où s'emboîtent les branches, bagues violacées, prise de cuir pourpre-noir en
  spirale à trois clous d'os pâle, fenêtre décalée vers -Z où passe la flèche, repose-flèche en petite griffe, une griffe
  au-dessus et une au-dessous de la prise ;
- **corde = fil de lueur verte** (_e), logique pour le set : le vert ne vit qu'aux fils, gouttières et pointes.
Pas de métal, d'or ni de rouge.

Étapes (groupes racine ; `arc` = poignée, toujours dessinée) : `repos`, `bande_1..3`. Les mêmes tuiles sont reposées à
chaque étape : la branche pivote dans son collet (0, -5, -10, -15°) et la serre se déroule (0, -9, -18, -27°) ;
branche basse = haute tournée de 180° autour de l'axe de tir. Flèche d'os à pointe verte encochée de bande_1 à bande_3.

Objet vivant (guide 14), sobre :
- item_idle (6 s) : serres et griffes d'aile respirent (±3°), la lueur souffle (ctrl_lumiere) ;
- item_use (0,5 s) : l'arc frémit avec la tension (Molang q.use_progress), la lueur monte ;
- event_enter_bande_3 (0,4 s) : les serres se crispent, éclat de la lueur ; **aucun son** ;
- event_release (0,7 s) : la corde vibre, les branches frissonnent, éclat vert, gerbe emit_mc_dust_82d335_8 (ctrl_emit,
  rafale « Au tir ») ; **le seul son** : block.sculk_sensor.clicking à 0,04 s ;
- event_select (0,7 s) : les branches sortent des collets (échelle du seul groupe `branches_repos`), les serres s'ouvrent,
  la lueur s'allume.
Fonctions avancées : calque _e, ctrl_lumiere (non simulé par le renderer), ctrl_emit + emit_mc_dust_82d335_8, Molang
q.use_progress, scale animé, event_enter_bande_3, event_release, event_select. À juger en jeu : la corde verte et les
branches dans la case, event_release et son son, ctrl_lumiere sur un objet.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

NOM = "skin_arc_abyssal"
TEX = 512
TAU = 2 * math.pi
AVEC_E = True

# ------------------------------------------------------------------ repère (celui de l'arc vanilla, skin_arc_givre)
C0 = np.array((8.0, 8.0, 8.0))
S_ = np.array((-1.0, 1.0, 0.0)) / math.sqrt(2)     # vers l'avant (flèche : haut à gauche de l'image vanilla)
H_ = np.array((1.0, 1.0, 0.0)) / math.sqrt(2)      # le long des branches (branche haute en haut à droite)
Z_ = np.array((0.0, 0.0, 1.0))                     # côté vu dans l'inventaire
SG, HG, HA = 3.55, -0.7, 0.85                      # prise (milieu du poing) -> (5, 10, 8) ; ligne de la flèche
SR = SG - 0.25                                     # axe de la poignée
ZF = 0.2                                           # la flèche passe devant la fenêtre (décalée vers -Z)


def Wp(a, b=0.0, z=0.0):
    """Plan de l'arc : a le long des branches (H_), b vers l'avant (S_), z vers +Z. Repère direct (H_ × S_ = Z_)."""
    return C0 + H_ * a + S_ * b + Z_ * z


def Wv(a, b=0.0, z=0.0):
    return H_ * a + S_ * b + Z_ * z


def P(s, h, z=0.0):
    return Wp(h, s, z)


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
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def smv(t, a, b):
    u = np.clip((np.asarray(t, float) - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


C = lambda *c: np.array(c, np.float32)
# palette Abyssal (sets-objets-2026-11-08.md, skin_epee_abyssal)
OS_CLAIR = C(58, 50, 72)
OS_BASE = C(30, 25, 40)
OS_SOMBRE = C(14, 10, 20)
ARETE = C(126, 92, 170)
REFLET = C(98, 68, 126)
AURA = C(22, 66, 40)
VEIN = C(96, 200, 44)
VCORE = C(150, 244, 70)
FIL = C(190, 255, 96)
E_COL = C(82, 211, 53)
E_VEINE = C(60, 160, 40)


# ------------------------------------------------------------------ géométrie plane
def in_poly(P2, poly):
    x, y = P2[..., 0], P2[..., 1]
    ins = np.zeros(x.shape, bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1)
        ins ^= c
    return ins


def d_poly(P2, pts):
    d = np.full(P2.shape[:-1], 1e9)
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i]), np.array(pts[i + 1])
        ab = b - a
        t = np.clip(((P2 - a) @ ab) / (ab @ ab), 0, 1)
        d = np.minimum(d, np.linalg.norm(P2 - (a + t[..., None] * ab), axis=-1))
    return d


def subdiv(pts, maxlen=2.0):
    out = []
    for i in range(len(pts) - 1):
        p, q = np.array(pts[i], float), np.array(pts[i + 1], float)
        n = max(1, int(math.ceil(np.linalg.norm(q - p) / maxlen)))
        for k in range(n):
            out.append((p + (q - p) * k / n, p + (q - p) * (k + 1) / n, k == 0, k == n - 1))
    return out


def d_stack(P2, segs):
    out = []
    for p, q, *_ in segs:
        ab = q - p
        t = np.clip(((P2 - p) @ ab) / (ab @ ab), 0, 1)
        out.append(np.linalg.norm(P2 - (p + t[..., None] * ab), axis=-1))
    return np.stack(out)


# ------------------------------------------------------------------ branche haute (plan a, b ; px), au repos
Z_E = 0.10                       # demi-épaisseur au bord
T_BIS = 1.45                     # pente unique des biseaux (55°) : branche étroite, il reste un plat pour la gouttière
TH = 0.3
DF = 16.0
RECOUV = 0.08
AL = math.atan(T_BIS)
Z_FOND = 0.16                    # fond de la gouttière
L_BR = 7.6                       # longueur de la branche (ligne médiane)
HW_R, HW_T = 1.00, 0.52          # demi-largeur : pied -> bout
H_R, H_T = 0.80, 0.36            # demi-épaisseur du plat : pied -> bout
H_HAUT, H_BAS = 3.6, -3.4        # pied des branches (dans les collets) ; axe de tir entre les deux
H_AXE = (H_HAUT + H_BAS) / 2
B_RAC = SR - 0.1
PH0, CIN, REC = 16.0, 44.0, -62.0
G0, G1, GW = 0.12, 0.84, 0.23    # gouttière : de 12 à 84 % de la branche, demi-largeur 0,23


class Branche:
    """Os d'aile courbe : ligne médiane, contour (bout arrondi), fils = tout le bord sauf le pied (dans le collet),
    plat z = h0 + k (P - O)·u le long de la corde de la branche, gouttière creusée le long de la ligne médiane."""

    def __init__(self):
        n = 380
        a, b = H_HAUT, B_RAC
        pts, phis = [(a, b)], [PH0]
        for i in range(n):
            u = (i + 0.5) / n
            phi = PH0 + CIN * min(u / 0.76, 1.0) ** 1.15 + (REC * ((u - 0.76) / 0.24) ** 1.3 if u > 0.76 else 0.0)
            a += math.cos(math.radians(phi)) * L_BR / n
            b -= math.sin(math.radians(phi)) * L_BR / n
            pts.append((a, b))
            phis.append(phi)
        self.cl, self.phis, self.n = np.array(pts), np.array(phis), n
        self.O = self.cl[0].copy()
        self.u = unit(self.cl[-1] - self.cl[0])
        # contour : dos (+n), bout arrondi, ventre (-n) ; fermé par le pied
        us = np.linspace(0, L_BR, int(round(L_BR / 0.72)) + 1)
        dos = [self.at(u)[0] + self.at(u)[2] * self.hw(u) for u in us]
        ven = [self.at(u)[0] - self.at(u)[2] * self.hw(u) for u in us]
        c, t, nr = self.at(L_BR)
        cap = [c + HW_T * (nr * math.cos(al) + t * math.sin(al)) for al in np.linspace(0, math.pi, 7)[1:-1]]
        fil = dos + cap + ven[::-1]
        self.poly = [tuple(p) for p in fil]
        self.segs = subdiv(fil, 2.0)
        s_ = (np.array(fil) - self.O) @ self.u
        self.L = float(s_.max())
        s_r = 0.6
        self.k = (H_T - H_R) / (self.L - s_r)
        self.h0 = H_R - self.k * s_r
        # gouttière en fuseau le long de la ligne médiane
        ax, gl, gr = [], [], []
        for j in range(19):
            v = j / 18
            u = (G0 + (G1 - G0) * v) * L_BR
            c, t, nr = self.at(u)
            w = GW * math.sin(math.pi * v) ** 0.6 + 0.012
            ax.append(tuple(c))
            gl.append(tuple(c + nr * w))
            gr.append(tuple(c - nr * w))
        self.gax, self.gl, self.gr = ax, gl, gr
        self.gpoly = gl + gr[::-1]
        # reflets violacés : une ligne au milieu de chaque pan, entre la gouttière et le bord
        self.centres = []
        for sg in (1, -1):
            line = []
            for u in np.linspace(0.14, 0.86, 14) * L_BR:
                c, t, nr = self.at(u)
                line.append(tuple(c + sg * nr * 0.5 * (GW + self.hw(u))))
            self.centres.append(line)

    def hw(self, u):
        return float(lerp(HW_R, HW_T, np.clip(u / L_BR, 0, 1) ** 0.9))

    def at(self, u):
        """Point, tangente, normale (côté dos, vers l'avant +b) à l'abscisse u."""
        i = int(np.clip(round(u / L_BR * self.n), 0, self.n))
        phi = math.radians(self.phis[i])
        return self.cl[i].copy(), np.array((math.cos(phi), -math.sin(phi))), np.array((math.sin(phi), math.cos(phi)))

    def h(self, P2):
        return self.h0 + self.k * ((np.asarray(P2, float) - self.O) @ self.u)

    def wb(self, P2):
        return np.maximum((self.h(P2) - Z_E) / T_BIS, 0.02)

    def dE(self, P2):
        return d_stack(P2, self.segs).min(0)

    def surf(self, P2):
        P2 = np.asarray(P2, float)
        return np.minimum(self.h(P2), Z_E + T_BIS * self.dE(P2))

    def s(self, P2):
        return np.clip(((np.asarray(P2, float) - self.O) @ self.u) / self.L, 0, 1)

    def in_g(self, P2):
        return in_poly(P2, self.gpoly)

    def d_g(self, P2):
        return d_poly(P2, list(self.gpoly) + [self.gpoly[0]])

    def d_ax(self, P2):
        return d_poly(P2, self.gax)


BR = Branche()


def bruit(P2, seed=0.0):
    s, r = P2[..., 0], P2[..., 1]
    return 0.5 * np.sin(s * 1.7 + r * 2.3 + seed) + 0.3 * np.sin(s * 4.3 - r * 3.1 + 1.0 + seed) + 0.2 * np.sin(s * 9.1 + r * 7.7 + seed)


# --- peintures (couleur, alpha None = opaque, émissif) : os nu, liseré violacé au bord, arête violacée au plat
def peint_biseau(pc, P2, d, sg):
    f = np.clip(d / pc.wb(P2), 0, 1.2)
    nz = bruit(P2, 1.0 + sg)[..., None]
    col = lerp(OS_BASE, OS_SOMBRE, np.clip((f[..., None] - 0.4) / 0.5, 0, 1) * 0.75) + nz * 5 + np.zeros(P2.shape[:-1] + (3,), np.float32)
    em = np.zeros(col.shape, np.float32)
    col[f >= 0.88] = ARETE * 0.9                                  # arête violacée entre le biseau sombre et le plat
    col[f < 0.16] = ARETE                                         # bord d'os nu à liseré violacé
    return col, None, em


def peint_fil(pc, P2, d, sg):
    col = np.zeros(P2.shape[:-1] + (3,), np.float32) + ARETE
    return col, None, np.zeros_like(col)


def peint_plat(pc, P2, d, sg):
    wb = pc.wb(P2)
    nz = bruit(P2, 2.0 + 3 * sg)
    col = lerp(OS_BASE, OS_CLAIR, np.clip(0.45 + 0.6 * nz, 0, 1)[..., None] * 0.85)
    col = col * (1 + 0.05 * np.sin(pc.s(P2) * 46.0 + nz * 2))[..., None]        # stries de croissance de l'os, en travers
    col = col * (1 - 0.22 * np.clip(1 - (pc.s(P2) * pc.L - 0.6) / 1.4, 0, 1))[..., None]   # plus sombre vers le collet
    dc = np.minimum(*[d_poly(P2, c) for c in pc.centres])
    col = lerp(col, REFLET, (np.clip(1 - dc / 0.4, 0, 1) * 0.35)[..., None])    # reflet violacé au milieu du pan
    em = np.zeros(col.shape, np.float32)
    col[d < wb + 0.05] = ARETE
    dg = pc.d_g(P2)
    col[dg < 0.09] = ARETE                                        # lèvre de la gouttière (≥ 1,5 texel : pas de pointillés)
    return col, None, em


# ------------------------------------------------------------------ cubes différés
TILES = {}
CUBES = []
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


def spec(groupe, nom, c, X, Y, s, peintures):
    """Cube dans le plan (a, b, z) ; chaque face peinte est échantillonnée texel par texel et découpée par l'alpha."""
    X, Y, Z = repere(X, Y)
    c = np.asarray(c, float)
    faces = {}
    for f, fn in peintures.items():
        Pf = points_face(c, X, Y, Z, s, f)
        col, al, em, m = fn(Pf)
        if m.any():
            faces[f] = tuile(f"{nom}_{f}", *finir(col, al, em, m))
    if faces:
        CUBES.append({"groupe": groupe, "nom": nom, "c": Wp(*c), "R": np.column_stack([Wv(*X), Wv(*Y), Wv(*Z)]),
                      "half": np.asarray(s, float) / 2, "faces": faces})


def volume(pc, groupe):
    """Plaque biseautée fermée opaque : deux biseaux par tronçon de bord (un par face), un plat incliné par face."""
    for idx, (p, q, v0, v1) in enumerate(pc.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        pm = (p + q) / 2
        cand = np.array([pm + n * 0.25, pm - n * 0.25])
        prof = np.where(in_poly(cand, pc.poly), d_poly(cand, list(pc.poly) + [pc.poly[0]]), -1.0)
        if prof[1] > prof[0]:
            n = -n
        wmax = float(max(pc.wb(p[None])[0], pc.wb(q[None])[0]))
        e0 = wmax * 1.3 if v0 else 0.04
        e1 = wmax * 1.3 if v1 else 0.04
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        sy = (wmax + 0.1) / math.cos(AL)
        for sg in (1, -1):
            Y = np.array((n[0] * math.cos(AL), n[1] * math.cos(AL), sg * math.sin(AL)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0], mid[1], sg * Z_E)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(Pf, idx=idx, sg=sg):
                P2 = Pf[..., :2]
                D = d_stack(P2, pc.segs)
                de = D.min(0)
                own = D[idx] <= de + RECOUV
                m = in_poly(P2, pc.poly) & own & (de < pc.wb(P2) + 0.03) & (de >= -0.02)
                col, al, em = peint_biseau(pc, P2, de, sg)
                return col, al, em, m

            def fil(Pf, idx=idx, n=n, sg=sg):
                P2 = Pf[..., :2] + n * 0.04
                D = d_stack(P2, pc.segs)
                own = D[idx] <= D.min(0) + RECOUV
                m = in_poly(P2, pc.poly) & own
                col, al, em = peint_fil(pc, P2, D.min(0), sg)
                return col, al, em, m

            spec(groupe, f"br_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil})
    u = pc.u
    pp_ = np.array((-u[1], u[0]))
    pa = np.array(pc.poly) - pc.O
    s_, t_ = pa @ u, pa @ pp_
    s0, s1, t0, t1 = s_.min() - 0.05, s_.max() + 0.05, t_.min() - 0.05, t_.max() + 0.05
    Pc = pc.O + u * (s0 + s1) / 2 + pp_ * (t0 + t1) / 2
    for sg in (1, -1):
        X = unit(np.array((u[0], u[1], sg * pc.k)))
        Y = sg * np.array((pp_[0], pp_[1], 0.0))
        Z = np.cross(X, Y)
        c = np.array((Pc[0], Pc[1], sg * float(pc.h(Pc)))) - Z * (TH / 2)

        def plat(Pf, sg=sg):
            P2 = Pf[..., :2]
            de = pc.dE(P2)
            m = in_poly(P2, pc.poly) & (de >= pc.wb(P2) - 0.03) & ~pc.in_g(P2)
            col, al, em = peint_plat(pc, P2, de, sg)
            return col, al, em, m

        spec(groupe, f"br_plat{'pm'[sg < 0]}", c, X, Y, ((s1 - s0) * math.sqrt(1 + pc.k ** 2), t1 - t0, TH), {"south": plat})


def gouttiere(pc, groupe):
    """Gouttière creusée : trou dans les plats (alpha), parois d'os par tronçon et par face, fond où le filet vert est couché."""
    gp = np.array(pc.gpoly)
    a0, a1 = gp[:, 0].min() - 0.15, gp[:, 0].max() + 0.15
    b0, b1 = gp[:, 1].min() - 0.15, gp[:, 1].max() + 0.15

    def fond(Pf):
        P2 = Pf[..., :2]
        m = pc.in_g(P2) | (pc.d_g(P2) < 0.1)
        dc = pc.d_ax(P2)
        col = np.zeros(Pf.shape[:-1] + (3,), np.float32) + OS_SOMBRE
        em = np.zeros_like(col)
        col[dc < 0.18] = AURA
        col[dc < 0.13] = VEIN
        col[dc < 0.07] = VCORE
        em[dc < 0.13] = E_VEINE
        em[dc < 0.07] = E_COL
        return col, None, em, m

    spec(groupe, "br_fond", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0), (a1 - a0, b1 - b0, 2 * Z_FOND),
         {"south": fond, "north": fond})
    murs = [(pts[i], pts[i + 1]) for pts in (pc.gl, pc.gr) for i in range(len(pts) - 1)]
    for j, (p, q) in enumerate(murs):
        p, q = np.asarray(p, float), np.asarray(q, float)
        Ln = float(np.linalg.norm(q - p))
        if Ln < 0.02:
            continue
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        mid = (p + q) / 2
        if pc.in_g(np.array([mid + n * 0.03]))[0]:
            n = -n                                                   # n vers l'extérieur de la gouttière
        back = [p + n * TH, q + n * TH, mid + n * TH]
        top = min(float(pc.surf(np.array([x]))[0]) for x in back + [p, q, mid]) - 0.03
        z0 = Z_FOND - 0.04
        if top - z0 < 0.06:
            continue
        for sg in (1, -1):
            zc = sg * (z0 + top) / 2
            X = np.array((d[0], d[1], 0.0))
            Y = np.array((0.0, 0.0, 1.0))
            Z = np.cross(X, Y)
            face = "south" if Z[:2] @ n < 0 else "north"

            def paroi(Pf):
                P2 = Pf[..., :2]
                dz = pc.h(P2) - np.abs(Pf[..., 2])
                col = lerp(OS_BASE, OS_SOMBRE, np.clip((dz[..., None] - 0.06) / 0.3, 0, 1)) + np.zeros(Pf.shape[:-1] + (3,), np.float32)
                col[dz < 0.07] = ARETE
                return col, None, None, np.ones(Pf.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(groupe, f"br_paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


# ------------------------------------------------------------------ tours (pièces rondes, recette de skin_epee_abyssal)
OVL, OVW = 0.04, 0.03
DENS = 16.0


def p_os(xn, t, y, r, L, ex):
    k = np.clip(0.35 + 0.45 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    col = lerp(OS_SOMBRE, OS_CLAIR, k[..., None]) * (1 + 0.06 * np.sin(y * 23 + xn))[..., None]
    col = np.where((np.abs(xn) < 0.22)[..., None], lerp(col, REFLET, 0.45), col)
    return col, None


def p_bague(xn, t, y, r, L, ex):
    k = np.clip(0.4 + 0.5 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    return lerp(OS_BASE, ARETE, k[..., None] * 0.8), None


def p_cuir(xn, t, y, r, L, ex):
    f = ((y / 0.62 + xn * 0.16) % 1.0)[..., None]
    col = lerp(C(84, 44, 98), C(38, 18, 48), f)
    col = np.where(f > 0.82, C(14, 7, 18), col)
    return col * (1 + 0.04 * np.sin(xn * 3 + y * 11))[..., None], None


def p_clou(xn, t, y, r, L, ex):
    k = (1 - np.abs(xn))[..., None]
    return lerp(C(150, 132, 160), C(214, 200, 218), k), None


def p_griffe(xn, t, y, r, L, ex):
    tg = ex["t0"] + (ex["t1"] - ex["t0"]) * t
    q = np.abs(xn)
    col = lerp(C(54, 48, 66), C(26, 22, 34), (q ** 1.2)[..., None])
    col = lerp(col, C(132, 98, 176), (np.clip(1 - q * 2.4, 0, 1) * 0.45)[..., None])
    col = col * (1 - 0.18 * (np.sin(tg * 40.0) > 0.85))[..., None]                     # bagues de croissance
    col = lerp(col, C(132, 240, 58), np.clip((tg - 0.62) / 0.25, 0, 1)[..., None])
    em = np.zeros(col.shape, np.float32)
    on = tg > 0.74
    em[on] = lerp(C(44, 110, 26), C(96, 230, 58), np.clip((tg[on] - 0.74) / 0.2, 0, 1)[..., None])
    return col, em


def p_corde(xn, t, y, r, L, ex):
    """Fil de lueur verte : cœur vif, bords plus sombres ; tout le fil brille (calque _e)."""
    col = lerp(VCORE, VEIN, np.clip(np.abs(xn), 0, 1)[..., None] * 0.8)
    em = lerp(E_COL, E_VEINE, np.clip(np.abs(xn), 0, 1)[..., None])
    return col, em


PEINTRES = {"os": p_os, "bague": p_bague, "cuir": p_cuir, "clou": p_clou, "griffe": p_griffe, "corde": p_corde}


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
    col, em = PEINTRES[mat](xn, t, y + ex.get("y0", 0.0), r, L, ex)
    return tuile(nom, *finir(col, None, em, mask))


def tour(g, nom, O, ax, ref, profil, n=12, phase=0.0, cle=None):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] le long de ax depuis O (monde) ; une couronne de n pans par tronçon.
    cle : préfixe des tuiles (mêmes tuiles pour deux tours de même profil)."""
    O, ax = np.asarray(O, float), unit(np.asarray(ax, float))
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    for i, (b0, r0, b1, r1, mat, ex) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        if L < 1e-4:
            continue
        tile = tuile_pan(f"{cle or nom}{i}", mat, L, 2 * r0 * tn, 2 * r1 * tn, r0, r1, ex)
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


def griffe(g, nom, p, X, Y, L, rmax, curve=0.30, nseg=8, n=8):
    """Griffe recourbée en tronçons coniques à 8 pans : part de p (monde) vers X, se recourbe vers Y ; pointe verte."""
    p, X = np.asarray(p, float), unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    nz = np.cross(X, Y)
    centre = lambda t: p + X * (L * (t - 0.12 * t * t)) + Y * (curve * L * t ** 2.1)
    ray = lambda t: rmax * (max(0.0, 1 - t) ** 0.8 + 0.06) / 1.06
    for i in range(nseg):
        t0, t1 = i / nseg, (i + 1) / nseg
        a, b = centre(t0), centre(t1)
        prof = [(0.0, ray(t0), float(np.linalg.norm(b - a)), ray(t1) if i < nseg - 1 else 0.0, "griffe", {"t0": t0, "t1": t1})]
        if i == 0:                                   # bouchon conique : la racine n'est jamais un anneau ouvert
            prof.insert(0, (-0.3, 0.0, 0.0, ray(0.0), "griffe", {"t0": 0.0, "t1": 0.0}))
        tour(g, f"{nom}{i}_", a, b - a, nz, prof, n=n)


def t_disque(nom, n, Ra, N=48):
    """Face d'os : os marbré, cercle violacé, bord sombre."""
    R = Ra / math.cos(math.pi / n)
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2 * R
    y = (0.5 - (yy + 0.5) / N) * 2 * R
    th = np.arctan2(y, x)
    sect = np.round(th / (TAU / n)) * (TAU / n)
    apo = x * np.cos(sect) + y * np.sin(sect)
    mask = apo <= Ra
    rr = apo / Ra
    col = lerp(OS_CLAIR, OS_BASE, rr[..., None] ** 1.3) * (1 + 0.05 * np.sin(np.hypot(x, y) * 14))[..., None]
    col[(rr > 0.70) & (rr < 0.80)] = ARETE
    col[rr > 0.92] = OS_SOMBRE
    return tuile(nom, *finir(col, None, None, mask))


def disque(g, nom, c, Nrm, up, n, Ra, tile, phase=0.0):
    Nrm = unit(Nrm)
    Y = unit(up - (up @ Nrm) * Nrm)
    X = np.cross(Y, Nrm)
    if phase:
        cph, sph = math.cos(phase), math.sin(phase)
        X, Y = cph * X + sph * Y, -sph * X + cph * Y
    R = Ra / math.cos(math.pi / n)
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float) - Nrm * TH / 2, "R": np.column_stack([X, Y, Nrm]),
                  "half": np.array((R, R, TH / 2)), "faces": {"south": tile}})


def bg(a0, a1, r_in, r_out):
    return [(a0, r_in, a0 + 0.12, r_out, "bague", {"clair": 0.1}), (a0 + 0.12, r_out, a1 - 0.12, r_out, "bague", {}),
            (a1 - 0.12, r_out, a1, r_in, "bague", {"clair": -0.1})]


# ------------------------------------------------------------------ groupes
GROUPES = []        # (clé unique, pivot, parent) ; le nom écrit est la clé sans « #… » (ctrl_lumiere répété)


def grp(nom, pivot, parent):
    GROUPES.append((nom, np.asarray(pivot, float), parent))
    return nom


# ------------------------------------------------------------------ branche haute au repos (prototype, monde)
PROTO_CORPS, PROTO_SERRE = "P_corps", "P_serre"
PROTO_EP = ("P_ep0", "P_ep1")
RACINE_W = Wp(*BR.O)
volume(BR, PROTO_CORPS)
gouttiere(BR, PROTO_CORPS)
_c, _t, _n = BR.at(L_BR)
T3, N3 = Wv(*_t), Wv(*_n)
BOUT = Wp(*_c)
# bague d'os violacée au bout, serre recourbée vers l'avant (pointe verte) ; la corde s'accroche sous la bague, côté ventre
tour(PROTO_CORPS, "bague_bout", BOUT - T3 * 0.62, T3, Z_, bg(0.0, 0.5, 0.5, 0.62), n=8, phase=math.pi / 8)
SERRE_PIV = BOUT - T3 * 0.15
griffe(PROTO_SERRE, "serre", SERRE_PIV, T3, N3, 1.95, 0.5, curve=0.45, nseg=8)
ATTACHE = BOUT - T3 * 0.36 - N3 * 0.6
# griffes d'aile sur le dos de la branche (penchées vers le bout), pointes vertes
EPERONS = []
for j, (fu, Lg, rg) in enumerate(((0.36, 1.45, 0.36), (0.64, 1.0, 0.28))):
    u = fu * L_BR
    c, t, nr = BR.at(u)
    base = Wp(*(c + nr * (BR.hw(u) - 0.3)))
    dirg = Wv(*(nr * math.cos(math.radians(42)) + t * math.sin(math.radians(42))))
    griffe(PROTO_EP[j], f"ep{j}_", base, dirg, Wv(*t), Lg, rg, curve=0.35, nseg=6)
    EPERONS.append(base)
PROTO = [cb for cb in CUBES if cb["groupe"].startswith("P_")]
CUBES[:] = [cb for cb in CUBES if not cb["groupe"].startswith("P_")]

ROT_BAS = 2 * np.outer(S_, S_) - np.eye(3)        # 180° autour de l'axe de tir (h = H_AXE)
O_BAS = P(0.0, H_AXE)


def vers_bas(p):
    return O_BAS + ROT_BAS @ (np.asarray(p, float) - O_BAS)


def tourne(p, piv, deg):
    return piv + rotm(0, 0, deg) @ (np.asarray(p, float) - piv)


# ------------------------------------------------------------------ poignée (groupe `arc`, toujours dessiné)
ARC = grp("arc", P(SG, HG), None)
grp("ctrl_lumiere#arc", P(SG, HG), ARC)
prof = ([(-4.05, 0.82, -3.92, 1.1, "bague", {"clair": 0.12}), (-3.92, 1.1, -2.98, 1.1, "os", {"clair": 0.05}),
         (-2.98, 1.1, -2.85, 0.82, "bague", {"clair": -0.05}), (-2.85, 0.82, -2.8, 0.6, "os", {})]
        + [(-2.8, 0.6, -1.95, 0.6, "os", {"y0": 1.0})] + bg(-1.95, -1.75, 0.6, 0.8)
        + [(-1.75, 0.72, 0.32, 0.72, "cuir", {})] + bg(0.32, 0.54, 0.6, 0.8))
tour(ARC, "poignee_bas", Wp(0, SR), H_, Z_, prof, n=12)
prof = (bg(2.24, 2.46, 0.6, 0.8) + [(2.46, 0.6, 2.95, 0.6, "os", {"y0": 2.0}), (2.95, 0.6, 3.0, 0.82, "os", {}),
                                    (3.0, 0.82, 3.13, 1.1, "bague", {"clair": 0.12}), (3.13, 1.1, 4.07, 1.1, "os", {"clair": 0.05}),
                                    (4.07, 1.1, 4.2, 0.82, "bague", {"clair": -0.05})])
tour(ARC, "poignee_haut", Wp(0, SR), H_, Z_, prof, n=12)
# fenêtre : montant d'os décalé vers -Z, la flèche passe devant
tour(ARC, "fenetre", Wp(0.5, SR - 0.05, -0.55), H_, Z_, [(0.0, 0.48, 1.8, 0.48, "os", {"y0": 3.0})], n=12)
TD = t_disque("disque_collet", 12, 0.8)
for nm, a, sgn in (("bas_e", -2.85, 1), ("haut_e", 2.95, -1), ("bas_x", -4.05, -1), ("haut_x", 4.2, 1)):
    disque(ARC, f"couvercle_{nm}", Wp(a, SR), H_ * sgn, Z_, 12, 0.8 if nm.endswith("e") else 0.82, TD)
# clous d'os pâle sur la prise
for k, (a, zs) in enumerate(((-1.35, 1), (-0.7, -1), (-0.05, 1))):
    tour(ARC, f"clou{k}_", Wp(a, SR, zs * 0.62), Z_ * zs, H_, [(0.0, 0.0, 0.14, 0.24, "clou", {}), (0.14, 0.24, 0.3, 0.24, "clou", {}),
                                                               (0.3, 0.24, 0.42, 0.0, "clou", {})], n=8, phase=math.pi / 8, cle="clou")
# repose-flèche (petite griffe vers l'avant) et deux griffes de poignée (au-dessus et au-dessous de la prise)
griffe(ARC, "repose", Wp(0.42, SR + 0.35, ZF), S_, H_, 0.95, 0.2, curve=0.25, nseg=5)
GR_P = []
for j, (a, sgn) in enumerate(((-2.35, -1), (2.7, 1))):
    g = grp(f"griffe_poignee_{j}", Wp(a, SR + 0.4), ARC)
    griffe(g, f"gp{j}_", Wp(a, SR + 0.4), S_ * math.cos(math.radians(28)) + H_ * sgn * math.sin(math.radians(28)), H_ * sgn,
           1.5, 0.36, curve=0.32, nseg=7)
    GR_P.append((g, sgn))
EMIT = grp("emit_mc_dust_82d335_8", P(SG + 0.9, HA, ZF), ARC)
grp("ctrl_emit", P(SG + 0.9, HA, ZF), EMIT)
EMIT_ROT = (0, 0, 45)        # +Y du point d'émission tourné vers l'avant (S_)


# ------------------------------------------------------------------ étapes : branches reposées, corde, flèche
def corde(g, a, b, nom):
    tour(g, nom, a, b - a, Z_, [(-0.05, 0.09, float(np.linalg.norm(b - a)) + 0.05, 0.09, "corde", {})], n=6)


# (nom, rotation de la branche dans son collet, déroulé de la serre, tirage de la corde depuis la prise)
ETAPES = [("repos", 0.0, 0.0, None), ("bande_1", -5.0, -9.0, 6.0), ("bande_2", -10.0, -18.0, 8.0), ("bande_3", -15.0, -27.0, 10.0)]
STAGE, BRANCHES, BR_G, SERRES, EPS, CORDE, CTRL, POINTE = {}, {}, {}, {}, {}, {}, {}, {}
for nom_e, th, ph, tir in ETAPES:
    st = grp(objet.etape(nom_e, "arc"), P(SG, HG), None)
    STAGE[nom_e] = st
    CTRL[nom_e] = grp(f"ctrl_lumiere#{nom_e}", P(SG, HG), st)
    brs = grp(f"branches_{nom_e}", P(SG, HG), st)
    BRANCHES[nom_e] = brs
    piv_s = tourne(SERRE_PIV, RACINE_W, th)
    att = tourne(tourne(ATTACHE, SERRE_PIV, ph), RACINE_W, th)
    BR_G[nom_e], SERRES[nom_e], EPS[nom_e] = [], [], []
    for cote in ("haut", "bas"):
        f = (lambda p: np.asarray(p, float)) if cote == "haut" else vers_bas
        Rf = np.eye(3) if cote == "haut" else ROT_BAS
        gb = grp(f"branche_{cote}_{nom_e}", f(RACINE_W), brs)
        gs = grp(f"serre_{cote}_{nom_e}", f(piv_s), gb)
        ge = [grp(f"griffe_aile{j}_{cote}_{nom_e}", f(tourne(EPERONS[j], RACINE_W, th)), gb) for j in range(2)]
        BR_G[nom_e].append(gb)
        SERRES[nom_e].append(gs)
        EPS[nom_e].append(ge)
        Rth, Rph = rotm(0, 0, th), rotm(0, 0, ph)
        for cb in PROTO:
            c, R = np.asarray(cb["c"], float), cb["R"]
            if cb["groupe"] == PROTO_SERRE:
                c, R = tourne(c, SERRE_PIV, ph), Rph @ R
                g = gs
            elif cb["groupe"] in PROTO_EP:
                g = ge[PROTO_EP.index(cb["groupe"])]
            else:
                g = gb
            c, R = tourne(c, RACINE_W, th), Rth @ R
            CUBES.append({"groupe": g, "nom": cb["nom"] + ("" if cote == "haut" else "_b"), "c": f(c), "R": Rf @ R,
                          "half": cb["half"], "faces": dict(cb["faces"])})
    ah, ab = att, vers_bas(att)
    gc = grp(f"corde_{nom_e}", P(SG - (tir or 0) * 0.5, HA), brs)
    CORDE[nom_e] = gc
    if tir is None:
        corde(gc, ah, ab, f"corde_{nom_e}")
        continue
    nock = P(SG - tir, HA, 0.0)
    corde(gc, ah, nock, f"corde_h_{nom_e}")
    corde(gc, ab, nock, f"corde_b_{nom_e}")
    # flèche d'os : encoche (bague violacée), fût à 8 pans, pointe = croc d'os droit à pointe verte
    fl = grp(f"fleche_{nom_e}", nock, st)
    a_n = P(SG - tir, HA, ZF)
    head = P(SG + 2.2, HA, ZF)
    tour(fl, f"fut_{nom_e}", a_n + S_ * 0.05, S_, Z_, [(0.0, 0.0, 0.08, 0.2, "bague", {}), (0.08, 0.2, 0.5, 0.2, "bague", {}),
                                                     (0.5, 0.16, float(np.linalg.norm(head - a_n)) - 0.04, 0.16, "os", {"clair": 0.2})],
         n=8, phase=math.pi / 8)
    # empennage : trois petites griffes couchées vers l'arrière (plumes d'os)
    for k in range(3):
        ang = TAU * k / 3 + math.pi / 2
        e = math.cos(ang) * Z_ + math.sin(ang) * H_
        griffe(fl, f"plume{k}_{nom_e}_", a_n + S_ * 1.4 + e * 0.1, -S_ * 0.8 + e * 0.6, -S_, 0.85, 0.16, curve=0.2, nseg=4, n=6)
    gp = grp(f"pointe_{nom_e}", head, fl)
    griffe(gp, f"pointe_{nom_e}_", head - S_ * 0.15, S_, H_, 2.0, 0.5, curve=0.0, nseg=6)
    # barbillons : deux petits crocs recourbés vers l'arrière
    for sgn in (1, -1):
        griffe(gp, f"barb{'pm'[sgn < 0]}_{nom_e}_", head + S_ * 0.35 + H_ * sgn * 0.2, -S_ * 0.5 + H_ * sgn * 0.85, -S_,
               0.75, 0.16, curve=0.3, nseg=4, n=6)
    POINTE[nom_e] = gp

print(f"branche : bout (a, b) = {tuple(np.round(BR.cl[-1], 2))} ; épaisseur {2 * H_R:.2f} -> {2 * H_T:.2f} px ; "
      f"biseau {float(BR.wb(BR.O[None])[0]):.2f} -> {float(BR.wb(BR.cl[-1][None])[0]):.2f} px")
gm = min(float(BR.h(np.array([p]))[0] - Z_FOND) for p in BR.gax)
marge = min(float(BR.dE(np.array([p]))[0] - BR.wb(np.array([p]))[0]) for p in BR.gl + BR.gr)
print(f"gouttière : profondeur mini {gm:.2f} px, marge gouttière/biseau {marge:.2f} px")


# ------------------------------------------------------------------ atlas
UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, (im, ime) in sorted(TILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1])):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, f"atlas plein ({n}, y = {y})"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    assert tex[TEX - 2, TEX - 2, 3] == 0
    assert set(np.unique(tex[..., 3])) <= {0, 255}, "semi-transparence interdite (aucun groupe trans_)"
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
    if abs(R[2, 0]) < 0.99999:
        e = (math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(math.asin(-R[2, 0])), math.degrees(math.atan2(R[1, 0], R[0, 0])))
    elif R[2, 0] < 0:
        e = (math.degrees(math.atan2(R[0, 1], R[0, 2])), 90.0, 0.0)
    else:
        e = (math.degrees(math.atan2(-R[0, 1], -R[0, 2])), -90.0, 0.0)
    assert np.allclose(rotm(*e), R, atol=1e-5), "euler"
    return e


def nuid():
    return str(_uuid.uuid4())


def nom_ecrit(cle):
    return cle.split("#")[0]


elements, groups = [], {}
for nom, piv, parent in GROUPES:
    assert nom not in groups and len(nom) <= 64, nom
    groups[nom] = {"origin": [round(float(v), 4) for v in piv], "uuid": nuid(), "ids": [], "parent": parent,
                   "rotation": list(EMIT_ROT) if nom == EMIT else [0, 0, 0]}
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
    return {"name": nom_ecrit(name), "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


RACINES = [n for n, gg in groups.items() if gg["parent"] is None]
outliner = [bone_node(n) for n in RACINES]


# ------------------------------------------------------------------ animations
def s_(v):
    return v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")


def kf(ch, t, x, y=None, z=None, interp="linear"):
    y = x if y is None else y
    z = x if z is None else z
    return {"channel": ch, "data_points": [{"x": s_(x), "y": s_(y), "z": s_(z)}], "time": round(t, 4), "interpolation": interp}


def rot(t, z):
    return kf("rotation", t, 0, 0, z)


def lum(t, x):
    return kf("position", t, x, 0, 0)


def anim(name, length, loop="once"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "item_idle", "animators": {}}


def piste(an, g, keys):
    an["animators"][groups[g]["uuid"]] = {"name": nom_ecrit(g), "type": "bone", "keyframes": keys}


def echant(L, n):
    return [round(L * i / n, 4) for i in range(n + 1)]


SGN = (1, -1)       # branche haute / basse : la basse est la haute tournée de 180° autour de l'axe de tir (z inversé)

# item_idle (6 s) : serres et griffes d'aile respirent à contretemps (±3°), la lueur souffle ; gerbe coupée.
L_IDLE = 6.0
idle = anim("item_idle", L_IDLE, "loop")
for j, g in enumerate(SERRES["repos"]):
    piste(idle, g, [rot(t, SGN[j] * 3.0 * math.sin(TAU * (t / L_IDLE - 0.5 * j))) for t in echant(L_IDLE, 24)])
for j, ge in enumerate(EPS["repos"]):
    for k, g in enumerate(ge):
        piste(idle, g, [rot(t, SGN[j] * 2.5 * math.sin(TAU * (t / L_IDLE - 0.25 * k - 0.5 * j))) for t in echant(L_IDLE, 24)])
for j, (g, sgn) in enumerate(GR_P):
    piste(idle, g, [rot(t, sgn * 2.0 * math.sin(TAU * (t / L_IDLE + 0.3 * j))) for t in echant(L_IDLE, 24)])
for g in (CTRL["repos"], "ctrl_lumiere#arc"):
    piste(idle, g, [lum(t, 0.35 * math.sin(TAU * 2 * t / L_IDLE)) for t in echant(L_IDLE, 24)])
piste(idle, "ctrl_emit", [kf("position", 0, -1, 0, 0), kf("position", L_IDLE, -1, 0, 0)])

# item_use (0,5 s en boucle) : l'arc frémit de plus en plus avec la tension, la lueur monte ; gerbe coupée.
TREM = "math.sin(q.anim_time * 360 * 14) * 0.7 * q.use_progress * q.use_progress"
LUM_USE = "0.2 + 0.7 * q.use_progress"
use = anim("item_use", 0.5, "loop")
for e in ("bande_1", "bande_2", "bande_3"):
    piste(use, STAGE[e], [kf("rotation", 0, 0, 0, TREM), kf("rotation", 0.5, 0, 0, TREM)])
    piste(use, CTRL[e], [kf("position", 0, LUM_USE, 0, 0), kf("position", 0.5, LUM_USE, 0, 0)])
piste(use, "ctrl_lumiere#arc", [kf("position", 0, LUM_USE, 0, 0), kf("position", 0.5, LUM_USE, 0, 0)])
piste(use, "ctrl_emit", [kf("position", 0, -1, 0, 0), kf("position", 0.5, -1, 0, 0)])

# event_enter_bande_3 (0,4 s) : les serres se crispent (-6° de plus puis retour), éclat de la lueur ; aucun son.
L_E3 = 0.4
enter3 = anim("event_enter_bande_3", L_E3)
for j, g in enumerate(SERRES["bande_3"]):
    piste(enter3, g, [rot(t, -SGN[j] * 6 * bump(t, 0.0, 0.06, 0.12, 0.38)) for t in echant(L_E3, 16)])
piste(enter3, CTRL["bande_3"], [lum(t, 0.9 * bump(t, 0.0, 0.05, 0.1, 0.38)) for t in echant(L_E3, 16)])

# event_release (0,7 s) : la corde revient et vibre, les branches frissonnent, les serres claquent vers l'avant, éclat
# vert et gerbe de poussière verte (ctrl_emit) ; **le seul son** (block.sculk_sensor.clicking à 0,04 s).
L_REL = 0.7
rel = anim("event_release", L_REL)
vib = lambda t, amp, f, tau: amp * math.sin(TAU * f * t) * math.exp(-t / tau) * sm(t, 0.0, 0.02)
ts_rel = [round(v, 4) for v in np.linspace(0, L_REL, 43)]
piste(rel, CORDE["repos"], [kf("position", t, *(S_ * vib(t, 0.45, 16, 0.14) * 1.0).round(4).tolist()) for t in ts_rel])
for j, g in enumerate(BR_G["repos"]):
    piste(rel, g, [rot(t, SGN[j] * vib(t, 1.6, 11, 0.12)) for t in ts_rel])
for j, g in enumerate(SERRES["repos"]):
    piste(rel, g, [rot(t, SGN[j] * 7 * bump(t, 0.0, 0.04, 0.08, 0.4)) for t in ts_rel])
piste(rel, CTRL["repos"], [lum(t, 1.4 * sm(t, 0.0, 0.03) * (1 - sm(t, 0.06, 0.6))) for t in ts_rel])
piste(rel, "ctrl_emit", [kf("position", t, 6 * bump(t, 0.0, 0.02, 0.1, 0.18) - 1, 0, 0) for t in np.round(np.linspace(0, L_REL, 22), 4)])

# event_select (0,7 s) : les branches sortent des collets (échelle du seul groupe `branches_repos`), les serres s'ouvrent,
# la lueur s'allume.
L_SEL = 0.7
sel = anim("event_select", L_SEL)
piste(sel, BRANCHES["repos"], [kf("scale", t, 0.3 + 0.7 * sm(t, 0.0, 0.3) + 0.05 * bump(t, 0.24, 0.3, 0.34, 0.48)) for t in echant(L_SEL, 21)])
for j, g in enumerate(SERRES["repos"]):
    piste(sel, g, [rot(t, -SGN[j] * 30 * (1 - sm(t, 0.25 + 0.06 * j, 0.5 + 0.06 * j))) for t in echant(L_SEL, 21)])
piste(sel, CTRL["repos"], [lum(t, -1 + 1 * sm(t, 0.3, 0.45) + 0.8 * bump(t, 0.4, 0.48, 0.52, 0.7)) for t in echant(L_SEL, 21)])

ANIMS = [idle, use, enter3, rel, sel]


# ------------------------------------------------------------------ écriture
assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})


def coins(ids=None):
    pts = []
    for e in elements:
        if ids is not None and e["uuid"] not in ids:
            continue
        lo, hi, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rotm(*e.get("rotation", (0, 0, 0)))
        for c in range(8):
            p = np.array([(lo, hi)[(c >> k) & 1][k] for k in range(3)])
            pts.append(R @ (p - o) + o)
    return np.array(pts)


def ids_de(name):
    g = groups[name]
    return set(g["ids"]).union(*[ids_de(n) for n, gg in groups.items() if gg["parent"] == name])


_P = coins()
_lo, _hi = _P[:, :2].min(0), _P[:, :2].max(0)
_c = (_lo + _hi) / 2
GUI_S = round(min(1.0, 15.4 / float(max(_hi - _lo))), 3)
GUI_T = [round(float((8 - _c[0]) * GUI_S), 2), round(float((8 - _c[1]) * GUI_S), 2), 0]
AFFICHAGE = objet.affichage("arc", gui={"scale": [GUI_S] * 3, "translation": GUI_T})
model = objet.modele(NOM, "arc", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son
limiter_sons(model)
# Un seul son, au tir (event_release), à 0,04 s (une clé à 0,0 s est muette au premier tir) : ajouté après limiter_sons,
# qui ne connaît pas encore les événements d'objet.
rel["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "block.sculk_sensor.clicking")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


Pr = coins(ids_de(ARC) | ids_de(STAGE["repos"]))
print("boîte :", _P.min(0).round(2).tolist(), "->", _P.max(0).round(2).tolist(), "; gui", GUI_S, GUI_T)
print(f"repos : de pointe à pointe {float((Pr @ H_).max() - (Pr @ H_).min()):.1f} px le long des branches")
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
