"""Harnais de latex (refonte du 2026-11-08) : harnais de torse à barre de poitrine, anneaux en O chromés, cadenas qui pend,
épaulières de latex moulé et brassards. Ensemble Cuir (thème Fétiche, pièce réservée au grade admin). Accessoire de mode
porté par-dessus le skin, rien d'explicite. Design original. Fiche de style : .claude/styles/cuir.md ; références réelles :
.claude/references/objets/harnais.md. Écrit harnais_cuir.png, harnais_cuir_e.png et .build/harnais_cuir_brut.bbmodel.

Retour de l'utilisateur (2026-11-08) : « les épaules sont juste moches de ouf sauf la démoniaque ». L'ancienne version
(sangles en X fines, collier, laisse, ceinture, bracelets à chaînes) se lisait comme des traits blancs pointillés sur le
corps, avec des chaînes qui flottaient. Refonte d'après la construction des vrais harnais de torse (dits « bulldog ») :
- devant : deux bretelles verticales descendent des épaules jusqu'à deux anneaux en O, reliés par une barre de poitrine ;
  de chaque anneau, une sangle file sous le bras vers le dos ; bouts repliés sur les anneaux et tenus par des doubles
  rivets ; boucle à ardillon sur chaque bretelle, bout percé (œillets cerclés) qui remonte par-dessus ;
- dos : grand anneau en O entre les omoplates, quatre sangles en X (deux vers les épaules, deux vers les côtés, raccord
  vertical au bord du torse avec la sangle sous le bras), pression chromée sur chaque sangle ;
- épaulières (la pièce est de la catégorie épaules) : coque de latex moulé sur le deltoïde (dessus, arrondi de 90° en
  6 pans, flanc au bord bas en arc), joncs chromés sur les tranches avant et arrière (le profil de l'épaule se lit de
  face), 4 rivets ronds ; elle tient par une sangle verticale qui descend jusqu'à un anneau en D cousu sur un brassard
  de biceps (boucle à l'avant, bout percé) ;
- cadenas chromé (trou de serrure) pendu à un petit anneau sous une patte au milieu de la barre de poitrine.
Matière : latex noir profond, arête biseautée qui accroche la lumière, une bande de reflet blanche nette et continue par
sangle, second reflet discret ; sur les coques, reflet calculé par la normale (bande blanche qui suit l'arrondi).
Proportions : sangles de 1,2 px (≈ 6 cm à l'échelle du joueur, harnais lourd), latex en vrai volume de 0,35 px, face
intérieure à 2,37 px du centre du torse et de l'axe du bras (0,12 px au-dessus de la seconde couche du skin), anneaux
d'environ 1,9 px (devant) et 2,2 px (dos), quincaillerie posée 0,1 px au-dessus des sangles.

Contrôles (règle : rien à moins de 0,3 px du corps ni à moins de 0,1 px d'une autre face parallèle qui la recouvre) :
contrôle automatique texel par texel en fin de géométrie. Les sangles qui partent d'un même anneau se partagent le dessous
du fil par secteurs angulaires (voronoi) : elles se touchent sans se recouvrir.

Fonctions avancées (à juger en jeu avec /cosmetique apercu) :
- phys_cadenas_g100_a60 : le cadenas pend vers le bas du monde (gravité du mod) et balance avec du retard ; le renderer
  ne le simule pas (aperçus : petites clés de balancement seulement) ;
- calque harnais_cuir_e.png : petits éclats sur les reflets du chrome, reflet du latex très discret ;
- tools/ambiance.py : ctrl_teinte et ctrl_lumiere dans chaque groupe de premier niveau, couche overlay_ambiance.
- réglage du staff conseillé : Armure → Par-dessus (le harnais est collé au corps, un plastron le cache sinon).
Sons : un seul, à l'équipement (item.armor.equip_leather). Aucun son dans les états (boucle idle de 8 s < 20 s).
Pas d'attack ni de hurt (pièce portée). Pas de particules, pas de reflets _r.
"""
import base64, hashlib, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

AVEC_E = True       # calque _e embarqué (correctif du mod annoncé le 2026-11-03, à vérifier en jeu)
NOM = "harnais_cuir"
TEX = 512
TAU = 2 * math.pi

# ------------------------------------------------------------------ palette (.claude/styles/cuir.md, révision latex)
LATEX, LATEX_HI, LATEX_MID, LATEX_RIM = (12, 12, 16), (200, 204, 214), (84, 86, 96), (3, 3, 5)
LATEX_2 = (40, 42, 50)          # second reflet, discret, vers le bas de la sangle
TRANCHE = (9, 9, 12)
ARG_HI, ARG, ARG_LO = (236, 238, 244), (168, 172, 184), (78, 80, 92)
E_FOCAL = 0.16                  # anneau du collier : léger éclat dans _e

def A(c):
    return np.array(c, np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


def smooth(x, a, b):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def V(*a):
    return np.array(a, float)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def euler(R):
    """Angles (X, Y, Z) tels que R = Rz Ry Rx (ordre du mod et du renderer)."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(R[2, 0]) > 1 - 1e-9:      # blocage de cardan (axe X local selon ±Z monde) : rx = 0, tout passe dans rz
        out = (0.0, math.degrees(ry), math.degrees(math.atan2(-R[0, 1], R[1, 1])))
    else:
        out = (math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0])))
    rx, ry_, rz = (math.radians(v) for v in out)
    Rx = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Ry = np.array([[math.cos(ry_), 0, math.sin(ry_)], [0, 1, 0], [-math.sin(ry_), 0, math.cos(ry_)]])
    Rz = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    assert np.allclose(Rz @ Ry @ Rx, R, atol=1e-6), "euler"
    return out


def frame(X, Y):
    """Repère direct : X exact, Y rendu orthogonal, Z = X ^ Y."""
    X = unit(X)
    Y = unit(np.asarray(Y, float) - (np.asarray(Y, float) @ X) * X)
    return np.column_stack([X, Y, np.cross(X, Y)])


# Faces d'un cube, coins (TL, TR, BR, BL) comme tools/render_bbmodel.py (et le jeu) : uv (u0, v0) = TL.
FACE_CORNERS = {
    "north": lambda a, b: [(b[0], b[1], a[2]), (a[0], b[1], a[2]), (a[0], a[1], a[2]), (b[0], a[1], a[2])],
    "south": lambda a, b: [(a[0], b[1], b[2]), (b[0], b[1], b[2]), (b[0], a[1], b[2]), (a[0], a[1], b[2])],
    "east": lambda a, b: [(b[0], b[1], b[2]), (b[0], b[1], a[2]), (b[0], a[1], a[2]), (b[0], a[1], b[2])],
    "west": lambda a, b: [(a[0], b[1], a[2]), (a[0], b[1], b[2]), (a[0], a[1], b[2]), (a[0], a[1], a[2])],
    "up": lambda a, b: [(a[0], b[1], a[2]), (b[0], b[1], a[2]), (b[0], b[1], b[2]), (a[0], b[1], b[2])],
    "down": lambda a, b: [(a[0], a[1], b[2]), (b[0], a[1], b[2]), (b[0], a[1], a[2]), (a[0], a[1], a[2])],
}
NORMALE = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}

# ------------------------------------------------------------------ registre : groupes, cubes, images de faces
elements, groups, TILES, FACES = [], {}, {}, []


def nuid():
    return str(_uuid.uuid4())


def group(name, origin, parent=None):
    assert name not in groups, name
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent}
    return name


def add_tile(rgba, e):
    k = hashlib.md5(rgba.tobytes() + e.tobytes() + bytes(rgba.shape[:2])).hexdigest()
    TILES.setdefault(k, (rgba, e))
    return k


def box(g, name, c, R, size, painter, D, tag=None):
    """Cube centré en c, axes locaux = colonnes de R, taille selon X, Y, Z locaux. painter(face, P local (N,3), demi-tailles)
    -> (rgba uint8 (N,4), e uint8 (N,3)). Chaque face reçoit son image ; une face toute transparente pointe sur CLEAR."""
    c = np.asarray(c, float)
    s = np.asarray(size, float) / 2
    faces = {}
    for f, corners in FACE_CORNERS.items():
        TL, TR, BR, BL = (np.array(p, float) for p in corners(-s, s))
        nu = max(1, int(round(np.linalg.norm(TR - TL) * D)))
        nv = max(1, int(round(np.linalg.norm(BL - TL) * D)))
        jj, ii = np.mgrid[0:nv, 0:nu]
        P = TL + ((ii + 0.5) / nu)[..., None] * (TR - TL) + ((jj + 0.5) / nv)[..., None] * (BL - TL)
        rgba, e = painter(f, P.reshape(-1, 3), s)
        rgba, e = rgba.reshape(nv, nu, 4), e.reshape(nv, nu, 3)
        if not (rgba[..., 3] > 0).any():
            faces[f] = None
            continue
        key = add_tile(rgba, e)
        faces[f] = key
        FACES.append(dict(el=name, tag=tag or g, key=key, W=[c + R @ np.array(p) for p in (TL, TR, BR, BL)], n=R @ np.array(NORMALE[f], float),
                          alpha=rgba[..., 3] > 0))
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in c - s], "to": [round(float(v), 3) for v in c + s],
         "origin": [round(float(v), 3) for v in c], "box_uv": False, "faces": faces}
    rot = euler(R)
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])
    return e




# ------------------------------------------------------------------ matières
def plate_painter(fn, edge=None, back=True, clear=()):
    """Plaque fine dans le plan XY local : fn(u, v, côté) -> (rgb float (N,3), alpha bool (N,), e float (N,3)).
    Grandes faces (south +1, north -1) : l'image ; tranches : le bord de l'image (même découpe), teinte `edge`.
    clear : faces rendues transparentes (ex. dessous du collier)."""
    eps = 0.03

    def painter(f, P, s):
        if f in clear or (f == "north" and not back):
            return np.zeros((len(P), 4), np.uint8), np.zeros((len(P), 3), np.uint8)
        if f in ("south", "north"):
            rgb, a, e = fn(P[:, 0], P[:, 1], 1 if f == "south" else -1)
        else:
            u = np.clip(P[:, 0], -s[0] + eps, s[0] - eps)
            v = np.clip(P[:, 1], -s[1] + eps, s[1] - eps)
            rgb, a, e = fn(u, v, 0)
            if edge is not None:
                rgb = np.broadcast_to(A(edge), rgb.shape).copy()
            e = e * 0
        out = np.zeros((len(P), 4), np.uint8)
        out[:, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        out[:, 3] = np.where(a, 255, 0)
        ee = np.where(a[:, None], np.clip(e, 0, 255), 0).astype(np.uint8)
        return out, ee
    return painter


def chrome_flat(du, dv, r):
    """Rivet rond plat : disque chromé, arête claire en haut à gauche, sombre en bas à droite, point de reflet."""
    q = np.hypot(du, dv) / r
    k = np.clip((-du * 0.6 + dv * 0.8) / r, -1, 1)
    col = np.tile(A(ARG), (len(du), 1))
    rim = q > 0.72
    col[rim & (k > 0.15)] = A(ARG_HI)
    col[rim & (k < -0.15)] = A(ARG_LO)
    col[(np.hypot(du + 0.3 * r, dv - 0.3 * r) < 0.22 * r)] = A((252, 252, 254))
    return col, q < 1


def latex_fn(L, H, D, cut=None, rivets=(), oeillets=(), seed=0.0):
    """Sangle de latex : u le long de la sangle, v en travers (+v = bord haut). Noir profond, bande de reflet blanche
    franche et large qui suit la longueur (un peu ondulée : la sangle épouse le corps), second reflet discret en bas,
    fin liseré sombre aux deux bords. cut(u, v) -> bool : partie gardée."""
    def fn(u, v, side):
        n = len(u)
        vv = v / (H / 2)
        dt, db = (H / 2 - v) * D, (v + H / 2) * D
        rgb = np.tile(A(LATEX), (n, 1))
        c = 0.30 + 0.07 * np.sin(u * 0.8 + seed)               # centre de la bande de lumière
        hw = 0.24 + 0.04 * np.sin(u * 0.5 + 1.7 * seed)
        d = np.abs(vv - c) * (H / 2) * D                         # en texels
        hwt = hw * (H / 2) * D
        rgb[d < hwt + 1.3] = A(LATEX_MID)
        rgb[d < hwt] = A(LATEX_HI)
        rgb[np.abs(vv + 0.58) * (H / 2) * D < 0.9] = A(LATEX_2)
        rgb[(dt < 1) | (db < 1)] = A(LATEX_RIM)
        e = np.zeros((n, 3), np.float32)
        for (ru, rv, r) in rivets:
            col, m = chrome_flat(u - ru, v - rv, r)
            rgb[m] = col[m]
        for (ou, ov, r) in oeillets:                             # trou de réglage cerclé de chrome
            dd = np.hypot(u - ou, v - ov)
            rgb[(dd < r) & (dd >= r * 0.6)] = A(ARG)
            rgb[(dd < r) & (dd >= r * 0.6) & (v - ov > 0)] = A(ARG_HI)
            rgb[dd < r * 0.6] = A((2, 2, 3))
        a = np.ones(n, bool) if cut is None else cut(u, v)
        return rgb, a, e
    return fn


def chrome(nx, ny, nz):
    """Chrome : environnement clair en haut, bande sombre à l'horizon, reflet blanc net."""
    L = unit((-0.42, 0.74, 0.52))
    diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    Hh = unit(L + V(0, 0, 1))
    spec = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1) ** 28
    env = np.where(ny > -0.12, 0.5 + 0.5 * smooth(ny, -0.12, 0.55), 0.18 + 0.2 * smooth(ny, -1.0, -0.12))
    val = np.clip(0.55 * env + 0.45 * diff, 0, 1)
    col = np.where((val < 0.5)[:, None], lerp(A(ARG_LO), A(ARG), (val * 2)[:, None]), lerp(A(ARG), A(ARG_HI), (val * 2 - 1)[:, None]))
    return col + (255 - col) * (spec * 0.9)[:, None]


def latex_shade(nx, ny, nz):
    """Latex sur une forme ronde : noir, reflet blanc franc là où la normale regarde la lumière."""
    Hh = unit(unit((-0.42, 0.74, 0.52)) + V(0, 0, 1))
    k = nx * Hh[0] + ny * Hh[1] + nz * Hh[2]
    col = np.tile(A(LATEX), (len(nx), 1))
    col[k > 0.62] = A(LATEX_MID)
    col[k > 0.74] = A(LATEX_HI)
    return col


def tube_fn(curve, rw, focal=0.0, shade=chrome, rim=None):
    """Fil rond de rayon rw autour d'une ligne médiane (polyligne dense, plan XY local)."""
    C = np.asarray(curve, float)

    def fn(u, v, side):
        P = np.stack([u, v], 1)
        d2 = ((P[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        k = d2.argmin(1)
        d = np.sqrt(d2[np.arange(len(P)), k])
        a = d <= rw
        q = np.clip(d / rw, 0, 1)
        dirv = (P - C[k]) / np.maximum(d, 1e-9)[:, None]
        if side == 0:
            q = np.ones_like(q)
        nx, ny, nz = dirv[:, 0] * q, dirv[:, 1] * q, np.sqrt(np.clip(1 - q * q, 0, 1))
        rgb = shade(nx, ny, nz)
        if rim is not None:
            rgb[q > 0.86] = A(rim)
        return rgb, a, rgb * focal
    return fn


def solid_painter(cols):
    """Volume plein (âme d'anneau, ardillon) : une teinte par face."""
    def painter(f, P, s):
        out = np.zeros((len(P), 4), np.uint8)
        out[:, :3] = cols.get(f, cols["*"])
        out[:, 3] = 255
        return out, np.zeros((len(P), 3), np.uint8)
    return painter


ARG_SOLIDE = solid_painter({"up": ARG_HI, "down": ARG_LO, "*": ARG})

# ------------------------------------------------------------------ constructeurs
D_CUIR, D_METAL, D_MAILLON = 14, 26, 44
TH = 0.4            # épaisseur du latex
GAP = 0.4           # face intérieure -> surface du corps


def sangle(g, name, c, X, Y, L, H, th=TH, D=D_CUIR, clear=(), **kw):
    R = frame(X, Y)
    box(g, name, c, R, (L, H, th), plate_painter(latex_fn(L, H, D, **kw), edge=TRANCHE, clear=clear), D)
    return R


def sangle_bouts_clairs(g, name, c, X, Y, L, H, seed, clear=()):
    """Plaque latérale dont les bouts butent contre une autre plaque : bouts transparents."""
    fn = latex_fn(L, H, D_CUIR, seed=seed)
    box(g, name, c, frame(X, Y), (L, H, TH),
        plate_painter(lambda u, v, side, fn=fn: (lambda r: (r[0], r[1] & (np.abs(u) < L / 2 - 0.03), r[2]))(fn(u, v, side)), edge=TRANCHE, clear=clear), D_CUIR)


def circle(r, n=360):
    a = np.linspace(0, TAU, n, endpoint=False)
    return np.stack([r * np.cos(a), r * np.sin(a)], 1)


def ellipse(a_, b_, n=360):
    t = np.linspace(0, TAU, n, endpoint=False)
    return np.stack([a_ * np.cos(t), b_ * np.sin(t)], 1)


def polyline(pts, step=0.01):
    out = []
    for p, q in zip(pts, pts[1:]):
        p, q = np.asarray(p, float), np.asarray(q, float)
        k = max(1, int(np.linalg.norm(q - p) / step))
        out += [p + (q - p) * i / k for i in range(k)]
    out.append(np.asarray(pts[-1], float))
    return np.array(out)


def rect_curve(hx, hy, bars=()):
    """Cadre rectangulaire (boucle, passant) + barreaux intérieurs éventuels (segments)."""
    c = polyline([(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy), (-hx, -hy)])
    return np.vstack([c] + [polyline(b) for b in bars])


def d_curve(hw, h):
    """Anneau en D : barre droite en haut (y = 0), arrondi en bas jusqu'à y = -h."""
    top = polyline([(-hw, 0), (hw, 0)])
    t = np.linspace(0, math.pi, 200)
    arc = np.stack([hw * np.cos(t), -h * np.sin(t)], 1)
    return np.vstack([top, arc])


def anneau(g, name, c, R, curve, rw, size, th=0.5, D=D_METAL, focal=0.0, ame=None):
    """Anneau de métal : peau découpée (fil rond peint) + âme de barreaux cachée derrière la peau (vue de profil)."""
    box(g, name, c, R, (size[0], size[1], th), plate_painter(tube_fn(curve, rw, focal), edge=ARG), D)
    if ame:
        # Remise aux règles du 2026-11-05 : les barreaux voisins se recouvraient aux jonctions (faces coplanaires opaques,
        # mesure_faces.py). Chaque bout est raccourci de (largeur / 2) tan(angle / 2) : les barreaux se touchent au coin
        # intérieur, petite encoche au coin extérieur, cachée par la peau.
        segs = [(np.asarray(p, float), np.asarray(q, float)) for p, q in ame]
        w = rw * 1.25

        def bout(i, pt, d):
            """Nouveau bout : jonction J avec le voisin (milieu des deux bouts), reculée de (w / 2) tan(angle / 2)."""
            u = d / np.linalg.norm(d)                    # du bout vers l'intérieur du barreau
            proches = [(np.linalg.norm(e2 - pt), e2, d2) for j, (p2, q2) in enumerate(segs) if j != i
                       for e2, d2 in ((p2, q2 - p2), (q2, p2 - q2))]
            dist, e2, d2 = min(proches, key=lambda x: x[0]) if proches else (9, None, None)
            if dist > 0.3:
                return pt
            J = (pt + e2) / 2
            phi = math.acos(np.clip(-(d @ d2) / (np.linalg.norm(d) * np.linalg.norm(d2)), -1, 1))   # déviation entre barreaux
            return J + u * (w / 2 * math.tan(phi / 2) + 0.01)
        courts = [(bout(i, p, q - p), bout(i, q, p - q)) for i, (p, q) in enumerate(segs)]
        for i, (p, q) in enumerate(courts):
            L = np.linalg.norm(q - p)
            Xl = np.append((q - p) / L, 0.0)
            Rb = R @ frame(Xl, np.cross(V(0, 0, 1), Xl))
            mid = c + R @ np.append((p + q) / 2, 0.0)
            box(g, f"{name}_ame{i}", mid, Rb, (L, rw * 1.25, th - 0.2), ARG_SOLIDE, 12)


def ame_octo(r, rb, n=12, phase=15.0):
    """Barreaux d'un polygone de rayon médian r (12 côtés : silhouette ronde de profil ; aucun côté parallèle aux tranches)."""
    segs = []
    half = r * math.tan(math.pi / n) + rb * 0.5 * math.tan(math.pi / n)
    for i in range(n):
        a = math.radians(phase + i * 360 / n)
        m, t = np.array([math.cos(a), math.sin(a)]) * r, np.array([-math.sin(a), math.cos(a)])
        segs.append((m - t * half, m + t * half))
    return segs




def rivet(g, name, c, n_out, r=0.23, h=0.4, proud=0.15):
    """Rivet rond plat : disque chromé découpé (cube de 0,4 px), enfoncé de h - proud dans le latex."""
    n_out = unit(n_out)
    t = unit(np.cross(V(0, 1, 0), n_out)) if abs(n_out[1]) < 0.9 else V(1, 0, 0)
    R = frame(t, np.cross(n_out, t))
    if R[:, 2] @ n_out < 0:
        R = frame(-t, np.cross(n_out, -t))
    assert R[:, 2] @ n_out > 0.99
    fn = lambda u, v, side: (lambda cm: (cm[0], cm[1], np.zeros((len(u), 3), np.float32)))(chrome_flat(u, v, r))
    box(g, name, np.asarray(c, float) + n_out * (proud - h / 2), R, (2 * r + 0.04, 2 * r + 0.04, h), plate_painter(fn, edge=ARG, back=False), 40)
# ================================================================== géométrie (refonte du 2026-11-08)
ZS = 2.37                 # face intérieure des sangles : 0,12 px au-dessus de la seconde couche du skin (2,25)
TH = 0.35                 # épaisseur du latex (vrai volume)
ZO = ZS + TH              # face extérieure des sangles
Z2, TH2 = ZO + 0.1, 0.3   # couche du dessus : bouts de sangle, pattes
ZH = ZO + 0.1 + 0.25      # plan médian des pièces de métal posées sur les sangles (épaisseur 0,5)
W = 1.2                   # largeur des sangles du torse (≈ 6 cm à l'échelle du joueur : harnais lourd)
D_L = 16                  # texels par px (latex)
EDGE_L = (26, 26, 32)     # tranche du latex : un ton au-dessus du noir, l'épaisseur se lit
E_LATEX, E_CHROME = 34, 150   # calque _e : reflet du latex (très discret), éclats du chrome (petits, vifs)


def plaque(g, name, c, n, X, L, H, th, fn, D=D_L, edge=EDGE_L, back=True, clear=()):
    """Plaque d'axe normal n (face 'south' = face extérieure, image side=+1), X le long de la plaque."""
    n = unit(n)
    X = np.asarray(X, float)
    X = unit(X - (X @ n) * n)
    R = np.column_stack([X, np.cross(n, X), n])
    box(g, name, c, R, (L, H, th), plate_painter(fn, edge=edge, back=back, clear=clear), D)
    return R


def vers_monde(c, R):
    c = np.asarray(c, float)
    return lambda u, v: c[None, :] + np.outer(u, R[:, 0]) + np.outer(v, R[:, 1])


# ------------------------------------------------------------------ peintures
def latex_band(L, H, D, keep=None, oeillets=(), bout_rond=None, gain=None):
    """Sangle de latex vu de face : u le long, v en travers (+v = côté de la lumière). Noir profond, arête biseautée qui
    accroche la lumière, bande de reflet blanche nette et continue (la sangle est un peu bombée), second reflet discret,
    liseré noir aux bords. bout_rond : (u0, sens) bout arrondi en demi-ellipse. keep(u, v) -> bool."""
    def fn(u, v, side):
        n = len(u)
        rgb = np.tile(A(LATEX), (n, 1))
        e = np.zeros((n, 3), np.float32)
        if side > 0:
            vv = v / (H / 2)
            g = np.ones(n) if gain is None else gain(u)
            d = np.abs(vv - 0.36) * (H / 2) * D                 # en texels
            hwt = 1.1 + 0.3 * g
            rgb[d < hwt + 0.9] = A((46, 48, 56))
            core = d < hwt
            rgb[core] = lerp(A((150, 154, 166)), A(LATEX_HI), np.clip(0.4 + 0.6 * g, 0, 1)[:, None])[core]
            e[core] = E_LATEX
            rgb[np.abs(vv + 0.50) * (H / 2) * D < 0.7] = A((28, 29, 35))
            dt, db = (H / 2 - v) * D, (v + H / 2) * D
            rgb[(dt >= 1.0) & (dt < 1.9)] = A((34, 35, 42))
            rgb[(dt < 1.0) | (db < 1.0)] = A(LATEX_RIM)
            for (ou, ov, r) in oeillets:                     # trou de réglage cerclé de chrome
                dd = np.hypot(u - ou, v - ov)
                ring = (dd < r) & (dd >= r * 0.55)
                rgb[ring] = A(ARG)
                rgb[ring & (v - ov > 0)] = A(ARG_HI)
                rgb[dd < r * 0.55] = A((2, 2, 3))
                e[ring & (v - ov > 0)] = 0
        a = np.ones(n, bool) if keep is None else keep(u, v)
        if bout_rond is not None:
            u0, sens = bout_rond
            k = (u - u0) * sens                              # > 0 : au-delà du début de l'arrondi
            a &= ~((k > 0) & ((k / (H * 0.55)) ** 2 + (v / (H / 2)) ** 2 > 1.0))
        return rgb, a, e
    return fn


def gloss(nw, Hs):
    """Latex sur une forme ronde : couleur selon la normale (reflet blanc franc, halo gris, second reflet faible)."""
    k = nw @ Hs
    col = np.tile(A(LATEX), (len(k), 1))
    e = np.zeros((len(k), 3), np.float32)
    col[(k > 0.50) & (k < 0.56)] = A(LATEX_2)
    col[k > 0.86] = A(LATEX_MID)
    col[k > 0.905] = A(LATEX_HI)
    e[k > 0.905] = E_LATEX
    return col, e


def chrome_e(u, v, side, fn):
    rgb, a, _ = fn(u, v, side)
    e = np.where((rgb.min(axis=1) > 236)[:, None], float(E_CHROME), 0.0) * np.ones((1, 3))
    return rgb, a, e.astype(np.float32)


def metal(g, name, c, R, curve, rw, size, th=0.5, ame=None, D=D_METAL):
    """Anneau, boucle : fil de chrome peint (peau découpée) + âme de barreaux ; petits éclats dans _e."""
    fn = tube_fn(curve, rw)
    box(g, name, c, R, (size[0], size[1], th), plate_painter(lambda u, v, s: chrome_e(u, v, s, fn), edge=ARG), D)
    if ame:
        anneau_ame(g, name, c, R, ame, rw, th)


def anneau_ame(g, name, c, R, segs, rw, th):
    for i, (p, q) in enumerate(segs):
        p, q = np.asarray(p, float), np.asarray(q, float)
        L = np.linalg.norm(q - p)
        Xl = np.append((q - p) / L, 0.0)
        Rb = R @ frame(Xl, np.cross(V(0, 0, 1), Xl))
        box(g, f"{name}_ame{i}", c + R @ np.append((p + q) / 2, 0.0), Rb, (max(L - rw * 0.9, 0.05), rw * 1.2, th - 0.2), ARG_SOLIDE, 12)


R_AV = np.column_stack([V(-1, 0, 0), V(0, 1, 0), V(0, 0, -1)])     # plaque posée sur le devant (face extérieure vers -Z)
R_DOS = np.eye(3)                                                # plaque posée sur le dos (face extérieure vers +Z)


def o_ring(g, name, c, R, r, rw):
    metal(g, name, c, R, circle(r), rw, (2 * (r + rw) + 0.16, 2 * (r + rw) + 0.16), ame=ame_octo(r, rw * 1.2))


def boucle(g, name, c, R, hx, hy, rw=0.12, horizontale=True):
    """Boucle à ardillon : cadre rectangulaire, ardillon qui part du bord d'entrée et passe le bord opposé."""
    if horizontale:      # sangle verticale : cadre large, barre horizontale, ardillon vers le haut
        bars = [((0, -hy), (0, hy + rw * 0.4))]
    else:                # sangle horizontale : cadre haut, barre verticale, ardillon vers -u
        bars = [((hx, 0), (-(hx + rw * 0.4), 0))]
    ame = [((-hx, -hy), (hx, -hy)), ((hx, -hy), (hx, hy)), ((hx, hy), (-hx, hy)), ((-hx, hy), (-hx, -hy))]
    metal(g, name, c, R, rect_curve(hx, hy, bars), rw, (2 * (hx + rw) + 0.16, 2 * (hy + rw) + 0.16), ame=ame)


def sangle_plan(g, name, p0, p1, n, keep_w=None, W=W, th=TH, D=D_L, gain=None, oeillets_u=(), bout=None, lum=None):
    """Sangle droite de p0 à p1 (centres), posée à plat, normale extérieure n. keep_w(P monde) -> bool.
    lum : direction vers laquelle mettre le reflet (côté +v)."""
    p0, p1, n = np.asarray(p0, float), np.asarray(p1, float), unit(n)
    X = unit(p1 - p0)
    if lum is None:
        lum = V(-0.25 * n[2], 1.0, 0.0)
    if np.cross(n, X) @ lum < 0:
        X = -X
    L = float(np.linalg.norm(p1 - p0))
    c = (p0 + p1) / 2
    R = np.column_stack([X, np.cross(n, X), n])
    to_w = vers_monde(c, R)
    keep = None if keep_w is None else (lambda u, v: keep_w(to_w(u, v)))
    oe = [((u_ - 0.5) * L * (1 if (p1 - p0) @ X > 0 else -1), 0.0, 0.2) for u_ in oeillets_u]
    br = None
    if bout is not None:            # bout arrondi côté p1 (bout='p1') ou p0
        sgn = 1 if (p1 - p0) @ X > 0 else -1
        br = ((L / 2 - W * 0.55) * (sgn if bout == "p1" else -sgn), sgn if bout == "p1" else -sgn)
    box(g, name, c, R, (L, W, th), plate_painter(latex_band(L, W, D, keep=keep, oeillets=oe, bout_rond=br, gain=gain), edge=EDGE_L, back=False), D)
    return R


def voronoi(C, angles, mien, rmax=1.7):
    """Masque des sangles qui partent d'un même anneau : chacune garde le secteur angulaire le plus proche de son axe
    (les bouts, sous le fil de l'anneau, se touchent sans se recouvrir)."""
    C = np.asarray(C, float)
    ang = np.radians(np.asarray(angles, float))

    def keep(P):
        d = P[:, :2] - C[None, :2]
        th = np.arctan2(d[:, 1], d[:, 0])
        diff = np.abs(np.angle(np.exp(1j * (th[:, None] - ang[None, :]))))
        r = np.hypot(d[:, 0], d[:, 1])
        own = diff[:, mien]
        autres = np.delete(diff, mien, axis=1).min(1)
        return (own + 0.08 / np.maximum(r, 0.3) < autres) | (r > rmax)
    return keep


BODY = group("body", (0, 24, 0))
ARM_R = group("right_arm", (5, 22, 0))
ARM_L = group("left_arm", (-5, 22, 0))

# ------------------------------------------------------------------ devant : harnais « bulldog » à barre de poitrine
# Deux bretelles verticales descendent des épaules jusqu'à deux anneaux en O, reliés par la barre de poitrine ; de chaque
# anneau, une sangle file sous le bras vers le dos. Boucle à ardillon sur chaque bretelle (réglage), bout de sangle
# percé qui remonte par-dessus ; bouts repliés sur les anneaux et tenus par des doubles rivets.
AV = group("harnais_av", (0, 21, -2.5), BODY)
Y_R, X_R = 19.4, 2.5                 # anneaux du devant
RF, RWF = 0.72, 0.24                 # rayon médian, rayon du fil (diamètre extérieur ≈ 1,9 px)
R_END = RF - 0.1                     # les sangles finissent sous le fil
Y_TOP = 23.62                        # haut des bretelles : sous la tête, à 0,12 px de la seconde couche du casque
ZC = -(ZS + TH / 2)
NAV = V(0, 0, -1)
for s, sx in ((1, "r"), (-1, "l")):
    C = V(s * X_R, Y_R, ZC)
    angs = [90, 180 if s > 0 else 0, 0 if s > 0 else 180]
    sangle_plan(AV, f"bretelle_av_{sx}", C + V(0, R_END, 0), V(s * X_R, Y_TOP, ZC), NAV, voronoi(C, angs, 0),
                oeillets_u=())
    sangle_plan(AV, f"cote_av_{sx}", C + V(s * R_END, 0, 0), V(s * 3.98, Y_R, ZC), NAV, voronoi(C, angs, 2))
    o_ring(AV, f"anneau_av_{sx}", V(s * X_R, Y_R, -ZH), R_AV, RF, RWF)
    # doubles rivets sur chaque bout replié
    for k, (dx, dy) in enumerate(((0, 1.12), (s * 1.12, 0), (-s * 1.12, 0))):
        tx, ty = (0.3, 0) if dx == 0 else (0, 0.3)
        for j, sg in enumerate((-1, 1)):
            rivet(AV, f"rivet_av_{sx}{k}{j}", V(s * X_R + dx + sg * tx, Y_R + dy + sg * ty, -ZO), NAV, r=0.17)
    # boucle de réglage sur la bretelle, bout percé qui remonte
    YB = 21.75
    boucle(AV, f"boucle_av_{sx}", V(s * X_R, YB, -ZH), R_AV, 0.78, 0.36)
    y0 = YB + 0.36 + 0.12 + 0.1
    sangle_plan(AV, f"bout_av_{sx}", V(s * X_R, y0, -(Z2 + TH2 / 2)), V(s * X_R, 23.35, -(Z2 + TH2 / 2)), NAV, th=TH2,
                W=W - 0.1, oeillets_u=(0.30, 0.62), bout="p1")
# barre de poitrine
CR, CL = V(X_R, Y_R, ZC), V(-X_R, Y_R, ZC)
k_r, k_l = voronoi(CR, [90, 180, 0], 1), voronoi(CL, [90, 0, 180], 1)
sangle_plan(AV, "barre_poitrine", V(-X_R + R_END, Y_R, ZC), V(X_R - R_END, Y_R, ZC), NAV, lambda P: k_r(P) & k_l(P))

# cadenas : patte de latex au milieu de la barre, petit anneau, cadenas chromé qui pend (gravité du mod)
sangle_plan(AV, "patte_cadenas", V(0, Y_R + 0.15, -(Z2 + TH2 / 2)), V(0, 18.4, -(Z2 + TH2 / 2)), NAV, th=TH2, W=0.62, bout="p1",
            lum=V(1, 0.2, 0))
rivet(AV, "rivet_patte", V(0, Y_R - 0.2, -(Z2 + TH2)), NAV, r=0.15)
CAD = group("phys_cadenas_g100_a60", (0, 18.45, -3.05), AV)
RP, RWP = 0.38, 0.13
YP = 18.34 - RP - RWP                 # centre du petit anneau (son haut touche le bout de la patte)
metal(CAD, "anneau_cadenas", V(0, YP, -3.05), R_AV, circle(RP), RWP, (2 * (RP + RWP) + 0.06,) * 2, th=0.36)
Y_ANSE = YP - RP                       # fil du bas du petit anneau : l'anse passe autour
AC, LEG = Y_ANSE - 0.1, 0.55          # centre de l'arc de l'anse, longueur des pattes visibles
anse = np.vstack([polyline([(-0.28, -LEG), (-0.28, 0.0)]),
                  np.stack([0.28 * np.cos(np.linspace(math.pi, 0, 80)), 0.28 * np.sin(np.linspace(math.pi, 0, 80))], 1),
                  polyline([(0.28, 0.0), (0.28, -LEG)])])
ZA = -(3.05 + 0.25 + 0.1 + 0.15)
OFF = (LEG - 0.28) / 2                   # centre de la boîte de l'anse sous le centre de l'arc
metal(CAD, "anse_cadenas", V(0, AC - OFF, ZA), R_AV, anse + V(0, OFF), 0.11, (0.86, LEG + 0.28 + 0.4), th=0.3,
      ame=[((-0.28, -LEG + OFF + 0.1), (-0.28, OFF)), ((0.28, -LEG + OFF + 0.1), (0.28, OFF))])
Y_CORPS = AC - LEG - 0.11 + 0.04     # haut du corps du cadenas (les pattes de l'anse y entrent)
CW, CH, CD = 1.1, 1.25, 0.5


def corps_cadenas(f, P, s):
    u, v = P[:, 0], P[:, 1]
    n = len(P)
    out = np.zeros((n, 4), np.uint8)
    out[:, 3] = 255
    e = np.zeros((n, 3), np.uint8)
    if f in ("north", "south"):
        uu = -u if f == "north" else u
        k = (v + s[1]) / (2 * s[1])
        col = lerp(A(ARG_LO), A(ARG_HI), np.clip(0.25 + 0.75 * k, 0, 1)[:, None] * np.ones((1, 3)))
        bx, by = s[0] - np.abs(uu), s[1] - np.abs(v)
        bord = np.minimum(bx, by) < 0.11
        col[bord & ((v > 0) | (uu < 0))] = A(ARG_HI)
        col[bord & ~((v > 0) | (uu < 0))] = A(ARG_LO)
        col[np.hypot(uu + 0.25, v - 0.38) < 0.09] = A((252, 252, 255))
        if f == "north":                                 # trou de serrure sur la face avant
            trou = (np.hypot(uu, v - 0.05) < 0.14) | ((np.abs(uu) < 0.055) & (v < 0.05) & (v > -0.32))
            col[trou] = A((6, 6, 8))
            col[(np.hypot(uu, v - 0.05) >= 0.14) & (np.hypot(uu, v - 0.05) < 0.2) & (v > 0.05)] = A(ARG_LO)
        out[:, :3] = np.clip(col, 0, 255).astype(np.uint8)
        e[np.hypot(uu + 0.25, v - 0.38) < 0.09] = E_CHROME
    else:
        out[:, :3] = {"up": ARG_HI, "down": ARG_LO}.get(f, ARG)
    return out, e


box(CAD, "corps_cadenas", V(0, Y_CORPS - CH / 2, -3.05), np.eye(3), (CW, CH, CD), corps_cadenas, 30)

# ------------------------------------------------------------------ côtés : la sangle passe sous le bras (cachée par le bras au repos)
for s, sx in ((1, "r"), (-1, "l")):
    plaque(BODY, f"sous_bras_{sx}", V(s * (4.37 + TH / 2), Y_R, 0), V(s, 0, 0), V(0, 0, 1), 3.9, W, TH,
           latex_band(3.9, W, D_L), back=False, clear=("east", "west"))

# ------------------------------------------------------------------ dos : anneau entre les omoplates, quatre sangles en X
DOS = group("harnais_dos", (0, 21, 2.5), BODY)
XB, YBk, RB, RWB = 0.0, 20.7, 0.85, 0.27
CB = V(0, YBk, ZS + TH / 2)
NDOS = V(0, 0, 1)
ends = {"haut_r": V(X_R, Y_TOP), "haut_l": V(-X_R, Y_TOP), "bas_r": V(3.98, Y_R), "bas_l": V(-3.98, Y_R)}
angs = {k: math.degrees(math.atan2(p[1] - YBk, p[0])) for k, p in ends.items()}
names = list(ends)
for i, k in enumerate(names):
    p = ends[k]
    d = unit(V(p[0], p[1] - YBk, 0))
    p0 = CB + d * (RB - 0.1)
    if k.startswith("bas"):
        # prolongée au-delà du bord du torse puis coupée à la verticale x = ±3,98 (raccord avec la sangle sous le bras)
        p1 = CB + d * ((abs(p[0]) + 0.5) / abs(d[0]))
        vk = voronoi(CB, [angs[n] for n in names], i)
        keep = lambda P, vk=vk: vk(P) & (np.abs(P[:, 0]) <= 3.98)
    else:
        p1 = V(p[0], p[1], CB[2])
        keep = voronoi(CB, [angs[n] for n in names], i)
    sangle_plan(DOS, f"dos_{k}", p0, p1, NDOS, keep)
    # pression chromée sur chaque sangle, près de l'anneau
    rivet(DOS, f"pression_{k}", CB + d * 1.45 + V(0, 0, TH / 2), NDOS, r=0.24)
o_ring(DOS, "anneau_dos", V(0, YBk, ZH), R_DOS, RB, RWB)

# ------------------------------------------------------------------ épaulières : coque de latex sur l'épaule, brassard au biceps
# Coque moulée (latex épais) : dessus plat, arrondi de 90° en 6 pans, flanc qui descend sur le deltoïde, bord bas en arc ;
# jonc chromé sur les deux tranches (avant, arrière), rivets ronds sur l'arrondi. Elle tient par une sangle verticale qui
# descend sous le flanc jusqu'à un anneau en D cousu sur le brassard du biceps (boucle à l'avant, bout percé).
TH_C = 0.4
R_IN = 1.2
NSEG = 6
ZC_HALF = 2.6


def epauliere(s, sx, ARM):
    G = group(f"epaule_{sx}", (s * 6.5, 23.0, 0), ARM)
    Cx, Cy = s * 7.66, 23.42                       # centre de l'arrondi (la coque passe à 0,12 px du coin du bras)
    rm = R_IN + TH_C / 2
    Hs = unit(V(s * 0.45, 0.80, -0.40))            # reflet : lumière haute, de face, côté extérieur

    def peint(c, R, kind):
        to_w = vers_monde(c, R)

        def fn(u, v, side):
            P = to_w(u, v)
            if kind == "dessus":
                nw = np.stack([np.zeros(len(u)), np.ones(len(u)), 0.5 * P[:, 2] / ZC_HALF], 1)
            elif kind == "flanc":
                nw = np.stack([np.full(len(u), s), np.zeros(len(u)), 0.5 * P[:, 2] / ZC_HALF], 1)
            else:
                dx, dy = (P[:, 0] - Cx) * s, P[:, 1] - Cy
                a = np.arctan2(dy, dx)
                nw = np.stack([s * np.cos(a), np.sin(a), 0.5 * P[:, 2] / ZC_HALF], 1)
            nw /= np.linalg.norm(nw, axis=1, keepdims=True)
            if side > 0:
                col, e = gloss(nw, Hs)
            else:
                col, e = np.tile(A((18, 18, 22)), (len(u), 1)), np.zeros((len(u), 3), np.float32)
            a = np.ones(len(u), bool)
            if kind == "flanc":                       # bord bas en arc : plus bas au milieu
                a = P[:, 1] >= 21.35 + 0.45 * (P[:, 2] / ZC_HALF) ** 2
            return col, a, e
        return fn

    # dessus
    x0, x1 = s * 4.62, Cx + s * 0.05
    c = V((x0 + x1) / 2, Cy + rm, 0)
    L = abs(x1 - x0)
    R = np.column_stack([V(0, 0, 1), np.cross(V(0, 1, 0), V(0, 0, 1)), V(0, 1, 0)])
    box(G, f"coque_dessus_{sx}", c, R, (2 * ZC_HALF, L, TH_C), plate_painter(peint(c, R, "dessus"), edge=EDGE_L, clear=("east", "west")), D_L)
    # arrondi
    da = 90.0 / NSEG
    hseg = 2 * (R_IN + TH_C) * math.tan(math.radians(da / 2)) + 0.02
    for i in range(NSEG):
        a = math.radians((i + 0.5) * da)
        n = V(s * math.cos(a), math.sin(a), 0)
        c = V(Cx, Cy, 0) + n * rm
        R = np.column_stack([V(0, 0, 1), np.cross(n, V(0, 0, 1)), n])
        box(G, f"coque_arrondi_{sx}{i}", c, R, (2 * ZC_HALF, hseg, TH_C), plate_painter(peint(c, R, "arrondi"), edge=EDGE_L, clear=("east", "west")), D_L)
    # flanc
    y0, y1 = 21.3, Cy + 0.05
    n = V(s, 0, 0)
    c = V(Cx + s * rm, (y0 + y1) / 2, 0)
    R = np.column_stack([V(0, 0, 1), np.cross(n, V(0, 0, 1)), n])
    box(G, f"coque_flanc_{sx}", c, R, (2 * ZC_HALF, y1 - y0, TH_C), plate_painter(peint(c, R, "flanc"), edge=EDGE_L, clear=("east", "west")), D_L)
    # joncs chromés sur les tranches avant et arrière : le profil de l'épaule se lit de face
    prof = [(x0 + s * 1.1 - Cx, rm)] + [(s * rm * math.cos(math.radians(90 - k)), rm * math.sin(math.radians(90 - k))) for k in range(0, 91, 3)] \
        + [(s * rm, 21.45 + 0.45 - Cy)]
    prof = polyline([(p[0], p[1]) for p in prof], step=0.02)
    xs, ys = prof[:, 0], prof[:, 1]
    cx_, cy_ = (xs.max() + xs.min()) / 2, (ys.max() + ys.min()) / 2
    size = (xs.max() - xs.min() + 0.5, ys.max() - ys.min() + 0.5)
    for zs_, nm, Rj in ((-1, "av", R_AV), (1, "ar", R_DOS)):
        loc = np.stack([(xs - cx_) * (Rj[0, 0]), ys - cy_], 1)       # R_AV inverse l'axe u (X local = -x monde)
        metal(G, f"jonc_{nm}_{sx}", V(Cx + cx_, Cy + cy_, zs_ * (ZC_HALF + 0.1 + 0.15)), Rj, loc, 0.12, size, th=0.3, D=30)
    # rivets ronds sur l'arrondi
    for j, z in enumerate((-1.9, -0.65, 0.65, 1.9)):
        nr = V(s * math.cos(math.radians(45)), math.sin(math.radians(45)), 0)
        rivet(G, f"rivet_coque_{sx}{j}", V(Cx, Cy, z) + nr * (R_IN + TH_C), nr, r=0.2)

    # brassard du biceps (bras de 4 px ; pas de face côté torse : le bras touche le corps)
    B = group(f"brassard_{sx}", (s * 6, 19.6, 0), ARM)
    YBR, WB = 18.0, 1.1
    xin, xout = s * 4.0, s * (6 + ZS + TH)
    for zs_, nm in ((-1, "av"), (1, "ar")):
        nn = V(0, 0, zs_)
        sangle_plan(B, f"brassard_{nm}_{sx}", V(xin, YBR, zs_ * (ZS + TH / 2)), V(xout, YBR, zs_ * (ZS + TH / 2)), nn, W=WB)
    plaque(B, f"brassard_flanc_{sx}", V(s * (6 + ZS + TH / 2), YBR, 0), V(s, 0, 0), V(0, 0, 1), 2 * ZS, WB, TH,
           latex_band(2 * ZS, WB, D_L), back=False)
    # boucle à l'avant du brassard, bout percé vers l'intérieur
    xb = s * 6.55
    boucle(B, f"boucle_brassard_{sx}", V(xb, YBR, -ZH), R_AV, 0.32, 0.68, horizontale=False)
    xt0 = xb - s * (0.32 + 0.12 + 0.1)
    sangle_plan(B, f"bout_brassard_{sx}", V(xt0, YBR, -(Z2 + TH2 / 2)), V(s * 4.35, YBR, -(Z2 + TH2 / 2)), NAV, th=TH2, W=WB - 0.12,
                oeillets_u=(0.35, 0.7), bout="p1")
    # sangle verticale coque -> brassard, anneau en D
    xs_ = s * (6 + ZS + TH / 2)
    sangle_plan(B, f"montant_{sx}", V(xs_, YBR + 0.75, 0), V(xs_, 22.9, 0), V(s, 0, 0), W=0.9, lum=V(0, 0, -1))
    Rd = np.column_stack([V(0, 0, -s), V(0, 1, 0), V(s, 0, 0)])
    dcur = d_curve(0.48, 0.72) * V(1, -1)          # barre droite en bas (cousue au brassard), arrondi vers le haut
    metal(B, f"anneau_d_{sx}", V(s * (6 + ZO + 0.1 + 0.2), YBR + 0.42, 0), Rd, dcur - V(0, 0.36), 0.13, (1.28, 1.08), th=0.4,
          ame=[((-0.48, -0.36), (0.48, -0.36))])
    return G, B


EP_R, BR_R = epauliere(1, "r", ARM_R)
EP_L, BR_L = epauliere(-1, "l", ARM_L)

# ------------------------------------------------------------------ outliner
def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone(BODY), bone(ARM_R), bone(ARM_L)]


# ------------------------------------------------------------------ contrôle : faces parallèles proches qui se recouvrent
def corps_faces():
    """Corps de Steve (base) et seconde couche du skin (gonflée de 0,25 ; 0,5 pour la tête)."""
    out = []
    parts = {"head": ((-4, 24, -4), (4, 32, 4), 0.5), "body": ((-4, 12, -2), (4, 24, 2), 0.25),
             "right_arm": ((4, 12, -2), (8, 24, 2), 0.25), "left_arm": ((-8, 12, -2), (-4, 24, 2), 0.25),
             "right_leg": ((0, 0, -2), (4, 12, 2), 0.25), "left_leg": ((-4, 0, -2), (0, 12, 2), 0.25)}
    for nom, (a, b, infl) in parts.items():
        for couche, d, seuil in (("base", 0.0, 0.3), ("couche", infl, 0.1)):
            aa, bb = np.array(a, float) - d, np.array(b, float) + d
            for f, fc in FACE_CORNERS.items():
                W = [np.array(p, float) for p in fc(aa, bb)]
                out.append(dict(el=f"{nom}:{couche}", W=W, n=np.array(NORMALE[f], float), alpha=np.ones((8, 8), bool), seuil=seuil))
    return out


def recouvrement(fa, fb, seuil):
    """Texels opaques de fa dont la projection tombe sur un texel opaque de fb, faces parallèles à moins de `seuil`."""
    if abs(fa["n"] @ fb["n"]) < 0.999:
        return 0
    if abs((fb["W"][0] - fa["W"][0]) @ fa["n"]) >= seuil:
        return 0
    TL, TR, BR, BL = fa["W"]
    al = fa["alpha"]
    nv, nu = al.shape
    jj, ii = np.nonzero(al)
    P = TL + ((ii + 0.5) / nu)[:, None] * (TR - TL) + ((jj + 0.5) / nv)[:, None] * (BL - TL)
    TLb, TRb, _, BLb = fb["W"]
    eu, ev = TRb - TLb, BLb - TLb
    su = (P - TLb) @ eu / (eu @ eu)
    sv = (P - TLb) @ ev / (ev @ ev)
    ok = (su > 0.002) & (su < 0.998) & (sv > 0.002) & (sv < 0.998)
    if not ok.any():
        return 0
    bl = fb["alpha"]
    bu = np.clip((su[ok] * bl.shape[1]).astype(int), 0, bl.shape[1] - 1)
    bv = np.clip((sv[ok] * bl.shape[0]).astype(int), 0, bl.shape[0] - 1)
    return int(bl[bv, bu].sum())


def controle():
    pb = []
    ames = lambda n: "_ame" in n
    for i, fa in enumerate(FACES):
        for fb in FACES[i + 1:]:
            if fa["el"] == fb["el"]:
                continue
            # âme d'un anneau : barreaux jointifs, cachés derrière la peau opaque (0,1 px devant) ; hors contrôle entre eux
            if ames(fa["el"]) and ames(fb["el"]) and fa["el"].split("_ame")[0] == fb["el"].split("_ame")[0]:
                continue
            k = recouvrement(fa, fb, 0.099) + recouvrement(fb, fa, 0.099)
            if k:
                pb.append((fa["el"], fb["el"], k))
        for fb in CORPS:
            k = recouvrement(fa, fb, fb["seuil"] - 1e-3)
            if k:
                pb.append((fa["el"], fb["el"], k))
    return pb


CORPS = corps_faces()
PB = controle()
for p in PB[:40]:
    print("  recouvrement :", p)
assert not PB, f"{len(PB)} paires de faces parallèles trop proches qui se recouvrent"

# ------------------------------------------------------------------ atlas
CLEAR = [TEX - 3, TEX - 3, TEX - 2, TEX - 2]


def pack():
    items = sorted(TILES.items(), key=lambda kv: (-kv[1][0].shape[0], -kv[1][0].shape[1]))
    uv, x, y, shelf = {}, 0, 0, 0
    for k, (im, _) in items:
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 5, f"atlas plein ({len(uv)}/{len(items)} images)"
        uv[k] = (x, y, x + w, y + h)
        x += w + 1
        shelf = max(shelf, h)
    return uv, y + shelf


UV, H_USED = pack()
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
for k, (im, e) in TILES.items():
    u0, v0, u1, v1 = UV[k]
    tex[v0:v1, u0:u1] = im
    tex_e[v0:v1, u0:u1, :3] = e
    tex_e[v0:v1, u0:u1, 3] = np.where((im[..., 3] > 0) & (e.max(axis=2) > 0), 255, 0)
tex[tex[..., 3] == 0] = 0
assert tex[TEX - 3, TEX - 3, 3] == 0
assert set(np.unique(tex[..., 3])) <= {0, 255}
for el in elements:
    el["faces"] = {f: {"uv": [float(v) for v in (UV[k] if k else CLEAR)], "texture": 0} for f, k in el["faces"].items()}


def b64png(arr, fn):
    im = Image.fromarray(arr, "RGBA")
    im.save(fn, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


tex_b64, tex_e_b64 = b64png(tex, f"{NOM}.png"), b64png(tex_e, f"{NOM}_e.png")




# ================================================================== animations
FPS = 12


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 3)), "y": str(round(y + 0.0, 3)), "z": str(round(z + 0.0, 3))}],
            "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, tracks, loop="loop", fps=FPS):
    """tracks : {groupe: [(canal, f(t) -> (x, y, z))]} ; linéaire, dernier keyframe = premier pour les boucles."""
    n = max(8, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A_ = {}
    for g, chans in tracks.items():
        kfs = []
        for ch, f in chans:
            kfs += [kf(ch, t, *f(t)) for t in times]
        A_[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "idle", "animators": A_}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def S(t, L, k=1, ph=0.0):
    """Sinus de période L / k (boucle fermée sur L)."""
    return math.sin(TAU * k * t / L + ph)


# MIROIR D'AXES (guide, section 3, mesuré sur rot_matrix du renderer) : pour une pièce qui pend sous son pivot,
# rotation +X = le bas part vers l'avant (-Z), +Z = le bas part vers +X. « Vers l'extérieur » = +Z à droite, -Z à gauche.


# Le harnais est collé au corps : il suit le torse et les bras sans bouger. Seul le cadenas balance ; en jeu, c'est la
# gravité du mod (phys_…_g100_a60) qui le fait pendre et osciller ; les clés ci-dessous sont sa cible, de petits
# balancements que le renderer peut montrer (il ne simule pas phys_).
CADN = "phys_cadenas_g100_a60"


def balance(name, L, ax, az, k=2, biais_x=0.0):
    return anim(name, L, {CADN: [("rotation", lambda t: (biais_x + ax * S(t, L, k, 1.1), 0.0, az * S(t, L, k)))]})


ANIMS = [balance("idle", 8.0, 0.8, 1.6, k=2), balance("walk", 1.6, 2.5, 5.0, k=2), balance("run", 1.0, 3.0, 7.0, k=2, biais_x=-4.0),
         balance("sneak", 3.0, 0.8, 1.2, k=1), balance("fly", 2.4, 1.2, 2.0, k=1), balance("glide", 3.6, 1.0, 1.5, k=1),
         balance("fall", 1.2, 2.0, 1.0, k=1), balance("mount", 3.0, 1.0, 1.5, k=1), balance("swim", 3.0, 1.0, 1.5, k=1),
         balance("sleep", 4.0, 0.4, 0.6, k=1)]

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))


# event_equip : les sangles se resserrent sur le corps (échelle 1,07 -> 1, jamais sous 1 : rien ne passe sous la peau), du dos
# vers le devant puis les épaules et les brassards ; un seul son de cuir.
def ajouter_equip(model, cibles, L=0.8, son="item.armor.equip_leather"):
    import uuid as _u

    def trouve(n, nom):
        if isinstance(n, dict):
            if n.get("name") == nom:
                return n
            for c in n.get("children", []):
                r = trouve(c, nom)
                if r:
                    return r
        return None

    def lisse(t, a, b):
        u = min(max((t - a) / (b - a), 0.0), 1.0)
        return u * u * (3 - 2 * u)

    A_ = {}
    for nom, t0 in cibles:
        g = next(r for r in (trouve(n, nom) for n in model["outliner"]) if r)
        cles = []
        for i in range(int(round(L / 0.05)) + 1):
            t = i * 0.05
            v = str(round(1 + 0.07 * (1 - lisse(t, t0, t0 + 0.35)), 4))
            cles.append({"channel": "scale", "data_points": [{"x": v, "y": v, "z": v}], "time": round(t, 3), "interpolation": "linear"})
        A_[g["uuid"]] = {"name": nom, "type": "bone", "keyframes": cles}
    A_["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
        {"channel": "sound", "data_points": [{"effect": son, "file": ""}], "time": 0.05}]}
    model["animations"].append({"uuid": str(_u.uuid4()), "name": "event_equip", "loop": "once", "override": False, "length": L,
                                "snapping": 24, "selected": False, "animators": A_})


ajouter_equip(model, [("harnais_dos", 0.0), ("harnais_av", 0.1), ("epaule_r", 0.22), ("epaule_l", 0.22), ("brassard_r", 0.34),
                      ("brassard_l", 0.34)])
from sons import limiter_sons
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
from ambiance import ajouter_ambiance
ajouter_ambiance(model, foyer=1.0)

os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in model["outliner"]), ";", len(model["animations"]), "anims ;",
      sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()), "keyframes ;",
      os.path.getsize(OUT) // 1024, "Ko ; atlas", H_USED, "px de haut sur", TEX, ";", len(TILES), "images")
