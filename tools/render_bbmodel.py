"""Rendu logiciel (numpy) d'un .bbmodel cubes-only + mannequin joueur, pour aperçu."""
import sys, json, base64, io, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def rot_matrix(rx, ry, rz):
    """Rotation Euler Blockbench (ordre ZYX appliqué : X puis Y puis Z)."""
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

FACE_CORNERS = {
    # (TL, TR, BR, BL) en fonction de (x0,y0,z0,x1,y1,z1)
    "north": lambda a, b: [(b[0], b[1], a[2]), (a[0], b[1], a[2]), (a[0], a[1], a[2]), (b[0], a[1], a[2])],
    "south": lambda a, b: [(a[0], b[1], b[2]), (b[0], b[1], b[2]), (b[0], a[1], b[2]), (a[0], a[1], b[2])],
    "east":  lambda a, b: [(b[0], b[1], b[2]), (b[0], b[1], a[2]), (b[0], a[1], a[2]), (b[0], a[1], b[2])],
    "west":  lambda a, b: [(a[0], b[1], a[2]), (a[0], b[1], b[2]), (a[0], a[1], b[2]), (a[0], a[1], a[2])],
    "up":    lambda a, b: [(a[0], b[1], a[2]), (b[0], b[1], a[2]), (b[0], b[1], b[2]), (a[0], b[1], b[2])],
    "down":  lambda a, b: [(a[0], a[1], b[2]), (b[0], a[1], b[2]), (b[0], a[1], a[2]), (a[0], a[1], a[2])],
}

class _MolangMath:
    @staticmethod
    def sin(d): return math.sin(math.radians(d))
    @staticmethod
    def cos(d): return math.cos(math.radians(d))
    @staticmethod
    def clamp(v, a, b): return max(a, min(b, v))
    @staticmethod
    def abs(v): return abs(v)
    @staticmethod
    def max(a, b): return max(a, b)
    @staticmethod
    def min(a, b): return min(a, b)
    @staticmethod
    def sqrt(v): return math.sqrt(v)
    # Autres fonctions du guide (section 6.3), mêmes définitions que tools/visionneuse.js.
    @staticmethod
    def mod(v, d): return math.fmod(v, d)
    @staticmethod
    def floor(v): return math.floor(v)
    @staticmethod
    def ceil(v): return math.ceil(v)
    @staticmethod
    def round(v): return math.floor(v + 0.5)
    @staticmethod
    def trunc(v): return math.trunc(v)
    @staticmethod
    def pow(a, b): return math.pow(a, b)
    @staticmethod
    def lerp(a, b, k): return a + (b - a) * k
    @staticmethod
    def atan(v): return math.degrees(math.atan(v))
    @staticmethod
    def atan2(y, x): return math.degrees(math.atan2(y, x))
    @staticmethod
    def exp(v): return math.exp(v)
    pi = math.pi
class _Q:
    """Variables Molang. Simuler un état : MOLANG_QUERY="ground_speed=33,vertical_speed=0,is_gliding=1". Inconnue = 0, comme le mod."""
    def __init__(self, t):
        self.anim_time = t
        self.life_time = t
        import os
        for kv in filter(None, os.environ.get("MOLANG_QUERY", "").split(",")):
            k, v = kv.split("=")
            setattr(self, k.strip(), float(v))
    def __getattr__(self, name): return 0.0
class _V:
    """Variables mémorisées (v.nom) : jamais écrite = 0."""
    def __getattr__(self, name): return 0.0


def molang(expr, t):
    """Expression Molang du guide (6.3). Avec des instructions « ; » ou des variables v.… : l'aperçu n'a pas d'image
    précédente, on calcule donc l'état stable (80 images de 0,05 s), comme après quelques secondes en jeu."""
    try: return float(expr)
    except ValueError: pass
    e = expr.replace("query.", "q.").replace("Math.", "math.").replace("variable.", "v.")
    if ";" not in e and "v." not in e:
        return float(eval(e, {"__builtins__": {}}, {"math": _MolangMath, "q": _Q(t)}))
    import re
    q, v = _Q(t), _V()
    if not getattr(q, "delta_time", 0):
        q.delta_time = 0.05
    instr = [s.strip() for s in e.split(";") if s.strip()]
    val = 0.0
    for _ in range(80):
        for s in instr:
            s = re.sub(r"^return\s+", "", s)
            m = re.match(r"^v\.(\w+)\s*=(?!=)\s*(.+)$", s)
            if m:
                setattr(v, m.group(1), float(eval(m.group(2), {"__builtins__": {}}, {"math": _MolangMath, "q": q, "v": v})))
                val = getattr(v, m.group(1))
            else:
                val = float(eval(s, {"__builtins__": {}}, {"math": _MolangMath, "q": q, "v": v}))
    return val

def sample(keyframes, channel, t, default):
    kfs = sorted([k for k in keyframes if k["channel"] == channel], key=lambda k: k["time"])
    if not kfs:
        return np.array(default, float)
    def val(k): return np.array([molang(k["data_points"][0][a], t) for a in "xyz"])
    if t <= kfs[0]["time"]: return val(kfs[0])
    if t >= kfs[-1]["time"]: return val(kfs[-1])
    for a, b in zip(kfs, kfs[1:]):
        if a["time"] <= t <= b["time"]:
            f = (t - a["time"]) / max(1e-9, b["time"] - a["time"])
            return val(a) * (1 - f) + val(b) * f
    return val(kfs[-1])

# ---------------------------------------------------------------- pose du joueur selon l'état
# Groupes de premier niveau qui suivent une partie du corps (guide, section 4) ; tout le reste suit le torse.
PARTIES = {"head": "head", "hat": "head", "helmet": "head", "body": "body", "torso": "body", "chest": "body",
           "rightarm": "right_arm", "armright": "right_arm", "leftarm": "left_arm", "armleft": "left_arm",
           "rightleg": "right_leg", "legright": "right_leg", "leftleg": "left_leg", "legleft": "left_leg"}
# Articulations du joueur (guide, section 4).
PIVOTS = {"head": (0, 24, 0), "body": (0, 24, 0), "right_arm": (5, 22, 0), "left_arm": (-5, 22, 0),
          "right_leg": (2, 12, 0), "left_leg": (-2, 12, 0)}
CENTRE = np.array([0.0, 16.0, 0.0])   # pivot du corps entier quand il est couché


def partie_de(nom):
    n = "".join(c for c in nom.lower() if c.isalnum())
    return PARTIES.get(n, "body")


def etat_de(anim_name):
    """Dernière partie du nom d'animation, ramenée à un état du guide (section 6.2)."""
    if not anim_name:
        return "idle"
    mot = anim_name.split(".")[-1].lower()
    if mot.startswith(("overlay_", "event_")):
        return "idle"          # couches et événements (guide 6.4) : jamais un état ; « engrenages » contient « nage »
    for etat, mots in (("glide", ("glide", "elytra", "plane")), ("swim", ("swim", "nage")), ("sleep", ("sleep", "dort", "dodo")),
                       ("mount", ("ride", "mount", "monture")), ("sneak", ("sneak", "crouch", "accroupi")),
                       ("run", ("sprint", "run", "cours", "course")), ("walk", ("walk", "marche"))):
        if any(m in mot for m in mots):
            return etat
    return "idle"


def pose_joueur(etat, t=0.0, duree=1.0):
    """Transformations du mannequin, à la manière du jeu vanilla (approchées) : partie -> fonction point -> point.
    Couché en élytres et en nage (face vers le sol), sur le dos en sommeil, assis en monture, penché accroupi,
    bras et jambes qui balancent en marche et en course. Les autres états : debout."""
    rot = {k: np.zeros(3) for k in PIVOTS}
    dep = {k: np.zeros(3) for k in PIVOTS}
    G = np.eye(3)
    if etat in ("walk", "run"):
        a = (28 if etat == "walk" else 55) * math.sin(2 * math.pi * t / max(duree, 1e-6))
        rot["right_leg"][0], rot["left_leg"][0] = a, -a          # +X : la jambe part vers l'avant
        rot["right_arm"][0], rot["left_arm"][0] = -a * 0.8, a * 0.8
    elif etat == "sneak":
        rot["body"][0] = -28.6                                    # le haut du torse vers l'avant
        dep["body"][1] = -3.2
        dep["head"][1] = -4.2
        for c in ("right_arm", "left_arm"):
            rot[c][0], dep[c][1] = 23, -3.2
        for c in ("right_leg", "left_leg"):
            dep[c][2], dep[c][1] = 4.0, -0.2
    elif etat == "mount":
        for c, y in (("right_leg", -18), ("left_leg", 18)):
            rot[c][0], rot[c][1] = 81, y
        for c in ("right_arm", "left_arm"):
            rot[c][0] = 36
    elif etat in ("swim", "glide"):
        G = rot_matrix(-90, 0, 0)                                 # couché, face vers le sol, dos vers le ciel
    elif etat == "sleep":
        G = rot_matrix(90, 0, 0)                                  # sur le dos
    fonctions = {}
    for k, piv in PIVOTS.items():
        R, piv, d = rot_matrix(*rot[k]), np.array(piv, float), dep[k]
        fonctions[k] = (lambda p, R=R, piv=piv, d=d: G @ (R @ (p - piv) + piv + d - CENTRE) + CENTRE)
    return fonctions


def load_model(path, anim_time=None, anim_name=None, pose=None):
    """pose : None (cosmétique seul, dans le repère du joueur debout) ou résultat de pose_joueur()."""
    m = json.load(open(path))
    animators = {}
    if anim_time is not None and m.get("animations"):
        an = next((a for a in m["animations"] if a["name"] == anim_name), m["animations"][0])
        t = anim_time % float(an["length"]) if an.get("loop") == "loop" else anim_time
        animators = {k: (v["keyframes"], t) for k, v in an["animators"].items()}
    tex = None
    if m.get("textures"):
        src = m["textures"][0]["source"].split(",", 1)[1]
        tex = Image.open(io.BytesIO(base64.b64decode(src))).convert("RGBA")
        # calque lumineux _e (guide 5 bis) : ajouté à la couleur dans render(), comme en jeu et dans le Vestiaire
        te = next((t for t in m["textures"][1:] if t.get("name", "").rsplit(".", 1)[0].endswith("_e") and t.get("source")), None)
        if te is not None:
            tex.calque = Image.open(io.BytesIO(base64.b64decode(te["source"].split(",", 1)[1]))).convert("RGBA")
    tw = m["resolution"]["width"]; th = m["resolution"]["height"]
    by_id = {e["uuid"]: e for e in m["elements"]}

    quads = []  # (4 points world, 4 uv (0..1), couleur, ou None / "add" / "trans" pour une face texturée)

    def transform_chain(chain):
        def f(p):
            p = np.array(p, dtype=float)
            for origin, R, S, pos in chain:   # élément d'abord, puis groupes parents
                p = R @ (S * (p - origin)) + origin + pos
            return p
        return f

    def cache_alpha(node):
        """Opacité pilotée par un enfant ctrl_alpha (« 1 + position x ») < 10 % : le groupe disparaît (guide 4 bis)."""
        for c in node.get("children", []):
            if isinstance(c, dict) and c.get("name") == "ctrl_alpha" and c.get("uuid") in animators:
                kfs, t = animators[c["uuid"]]
                if 1 + sample(kfs, "position", t, [0, 0, 0])[0] < 0.1:
                    return True
        return False

    def walk2(node, parents, partie="body", mode=None, bill=None, cache=False):
        if isinstance(node, str):
            e = by_id[node]
            R = rot_matrix(*e.get("rotation", [0, 0, 0]))
            ch = [(np.array(e["origin"], float), R, np.ones(3), np.zeros(3))] + list(reversed(parents))
            T = transform_chain(ch)
            inf = e.get("inflate", 0)
            a, b = [v - inf for v in e["from"]], [v + inf for v in e["to"]]
            for fname, fdata in e["faces"].items():
                if fdata.get("texture") is None:
                    continue
                u1, v1, u2, v2 = fdata["uv"]
                if u1 == u2 or v1 == v2:
                    continue
                pts = [T(p) for p in FACE_CORNERS[fname](a, b)]
                if pose is not None:
                    pts = [pose[partie](p) for p in pts]
                if cache:
                    pts = [np.zeros(3) for _ in pts]
                uvs = [(u1 / tw, v1 / th), (u2 / tw, v1 / th), (u2 / tw, v2 / th), (u1 / tw, v2 / th)]
                quads.append((pts, uvs, {"mode": mode, "bill": bill} if bill else mode))
        else:
            rot = np.array(node.get("rotation", [0, 0, 0]), float)
            S, pos = np.ones(3), np.zeros(3)
            if node.get("uuid") in animators:
                kfs, t = animators[node["uuid"]]
                ar = sample(kfs, "rotation", t, [0, 0, 0])
                import os
                if os.environ.get("MODCONV") == "1":
                    rot = rot + ar                               # convention du mod : rotations appliquées telles quelles
                else:
                    rot = rot + np.array([-ar[0], -ar[1], ar[2]])   # convention Blockbench (x,y inversés)
                S = sample(kfs, "scale", t, [1, 1, 1])
                pos = sample(kfs, "position", t, [0, 0, 0])
            R = rot_matrix(*rot)
            # fonctions anticipées (.claude/rules/conventions-anticipees.md) : add_ = additif, trans_ = translucide
            nom = node.get("name", "")
            m2 = "add" if nom.startswith("add_") else "trans" if nom.startswith("trans_") else mode
            suite = parents + [(np.array(node.get("origin", [0, 0, 0]), float), R, S, pos)]
            b2 = bill
            if nom.startswith(("cam_", "camy_")):
                # face caméra (guide 4 bis) : pivot et orientation monde du groupe sans son animation de rotation ;
                # render() tourne ces faces vers chaque caméra, l'animation s'applique ensuite
                o = np.array(node.get("origin", [0, 0, 0]), float)
                base = parents + [(o, rot_matrix(*node.get("rotation", [0, 0, 0])), S, pos)]
                Tb = transform_chain(list(reversed(base)))
                P0 = Tb(o)
                f = (lambda q: pose[partie](q)) if pose is not None else (lambda q: q)
                Pw = f(P0)
                cols = [f(Tb(o + e)) - Pw for e in np.eye(3)]
                Rw = np.column_stack([c / max(np.linalg.norm(c), 1e-9) for c in cols])
                b2 = ("camy" if nom.startswith("camy_") else "cam", Pw, Rw)
            c2 = cache or cache_alpha(node)
            for c in node.get("children", []):
                walk2(c, suite, partie, m2, b2, c2)

    for n in m["outliner"]:
        if isinstance(n, dict) and n.get("name", "").startswith("particle_"):
            continue   # modèle de particule : pas porté par le joueur
        walk2(n, [], partie_de(n.get("name", "")) if isinstance(n, dict) else "body")
    return quads, tex

def mannequin(pose=None):
    """Joueur gris (Steve). Face avant = -z (nord), dos = +z. pose : résultat de pose_joueur(), debout si None."""
    quads = []
    def box(a, b, col, partie, front_col=None):
        f = pose[partie] if pose else (lambda p: p)
        for fname, fn in FACE_CORNERS.items():
            c = front_col if (fname == "north" and front_col) else col
            quads.append(([f(np.array(p, float)) for p in fn(a, b)], None, c))
    g1, g2, g3 = (120, 120, 128), (100, 100, 108), (88, 88, 96)
    box((-4, 24, -4), (4, 32, 4), g1, "head", (135, 135, 143))   # tête
    box((-4, 12, -2), (4, 24, 2), g2, "body")                    # torse
    box((4, 12, -2), (8, 24, 2), g3, "right_arm"); box((-8, 12, -2), (-4, 24, 2), g3, "left_arm")   # bras (droite du joueur = +x)
    box((0, 0, -2), (4, 12, 2), g2, "right_leg"); box((-4, 0, -2), (0, 12, 2), g3, "left_leg")      # jambes
    # yeux
    f = pose["head"] if pose else (lambda p: p)
    for x in (-2.5, 1.0):
        quads.append(([f(np.array(p, float)) for p in [(x, 29, -4.01), (x + 1.5, 29, -4.01), (x + 1.5, 27.5, -4.01), (x, 27.5, -4.01)]], None, (30, 30, 40)))
    return quads

def cadrer(points, direction, fov=28, marge=1.0, rayon_min=7.0):
    """Caméra qui centre des points (le cosmétique) vus depuis une direction : (position, cible).
    Sphère englobante prise sur la boîte des points ; rayon minimal pour garder un peu du corps en repère."""
    d = np.array(direction, float); d /= np.linalg.norm(d)
    if len(points):
        P = np.asarray(points, float); lo, hi = P.min(0), P.max(0)
        c, r = (lo + hi) / 2, max(np.linalg.norm(hi - lo) / 2, rayon_min)
    else:
        c, r = np.array([0.0, 16.0, 0.0]), 16.0
    dist = r / math.sin(math.radians(fov / 2)) * marge
    return tuple(c + d * dist), tuple(c)


def points_de(quads):
    return [p for q in quads for p in q[0]]


def render(quads, tex, cam_pos, target, size=900, fov=28, bg=(18, 14, 20)):
    S = 2  # supersampling
    W = H = size * S
    cam_pos = np.array(cam_pos, float); target = np.array(target, float)
    fwd = target - cam_pos; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    f = 1 / math.tan(math.radians(fov) / 2)
    light = np.array([-0.4, 1.0, 0.6]); light /= np.linalg.norm(light)

    import os
    jour = 0.16 if os.environ.get("NUIT") == "1" else 1.0     # comme la vue de nuit du Vestiaire
    if jour < 1:
        bg = (3, 3, 6)
    color = np.zeros((H, W, 3), np.float32); color[:] = np.array(bg) / 255
    zbuf = np.full((H, W), np.inf, np.float32)
    texarr = np.array(tex) if tex is not None else None
    earr = np.array(tex.calque) if tex is not None and getattr(tex, "calque", None) is not None and tex.calque.size == tex.size else None

    def project(p):
        d = p - cam_pos
        x, y, z = d @ right, d @ up, d @ fwd
        return np.array([(x / z) * f * 0.5 * W + W / 2, -(y / z) * f * 0.5 * H + H / 2, z])

    def face_cam(q):
        """Groupes cam_ / camy_ : faces tournées vers cette caméra autour du pivot du groupe."""
        pts, uvs, col = q
        if not isinstance(col, dict):
            return q
        kind, Pw, Rw = col["bill"]
        d = cam_pos - Pw
        yaw = math.degrees(math.atan2(d[0], d[2]))
        pitch = math.degrees(math.atan2(d[1], math.hypot(d[0], d[2]))) if kind == "cam" else 0.0
        Rt = rot_matrix(0, yaw, 0) @ rot_matrix(-pitch, 0, 0)
        C = Rt @ Rw.T
        return ([Pw + C @ (p - Pw) for p in pts], uvs, col["mode"])

    quads = [face_cam(q) for q in quads]

    def prof(q):
        return float(np.mean([(p - cam_pos) @ fwd for p in q[0]]))
    opaques = [q for q in quads if q[2] not in ("add", "trans")]
    trans = sorted((q for q in quads if q[2] == "trans"), key=prof, reverse=True)
    adds = [q for q in quads if q[2] == "add"]
    for pts, uvs, col in opaques + trans + adds:
        n = np.cross(pts[1] - pts[0], pts[3] - pts[0])
        ln = np.linalg.norm(n)
        if ln < 1e-9:
            continue
        n /= ln
        shade = 0.55 + 0.45 * abs(n @ light)
        P = np.array([project(p) for p in pts])
        if (P[:, 2] <= 0.1).any():
            continue
        for tri in ((0, 1, 2), (0, 2, 3)):
            A, B, C = P[list(tri)]
            xmin, xmax = int(max(0, np.floor(min(A[0], B[0], C[0])))), int(min(W - 1, np.ceil(max(A[0], B[0], C[0]))))
            ymin, ymax = int(max(0, np.floor(min(A[1], B[1], C[1])))), int(min(H - 1, np.ceil(max(A[1], B[1], C[1]))))
            if xmin > xmax or ymin > ymax:
                continue
            xs, ys = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
            det = (B[0] - A[0]) * (C[1] - A[1]) - (C[0] - A[0]) * (B[1] - A[1])
            if abs(det) < 1e-9:
                continue
            l1 = ((B[0] - xs) * (C[1] - ys) - (C[0] - xs) * (B[1] - ys)) / det
            l2 = ((C[0] - xs) * (A[1] - ys) - (A[0] - xs) * (C[1] - ys)) / det
            l3 = 1 - l1 - l2
            eps = -1e-4
            mask = (l1 >= eps) & (l2 >= eps) & (l3 >= eps)
            if not mask.any():
                continue
            # interpolation perspective-correcte
            iz = l1 / A[2] + l2 / B[2] + l3 / C[2]
            z = 1 / np.where(iz == 0, 1e-9, iz)
            sub_z = zbuf[ymin:ymax + 1, xmin:xmax + 1]
            mask &= z < sub_z
            special = col in ("add", "trans")
            if col is None or special:
                uvA, uvB, uvC = (np.array(uvs[i]) for i in tri)
                u = (l1 * uvA[0] / A[2] + l2 * uvB[0] / B[2] + l3 * uvC[0] / C[2]) * z
                v = (l1 * uvA[1] / A[2] + l2 * uvB[1] / B[2] + l3 * uvC[1] / C[2]) * z
                tu = np.clip((u * texarr.shape[1]).astype(int), 0, texarr.shape[1] - 1)
                tv = np.clip((v * texarr.shape[0]).astype(int), 0, texarr.shape[0] - 1)
                samp = texarr[tv, tu]
                mask &= samp[..., 3] > (0 if special else 127)
                rgb = samp[..., :3] / 255.0
                lum = (earr[tv, tu][..., :3] / 255.0) * (earr[tv, tu][..., 3:4] > 127) if earr is not None else 0.0
            else:
                rgb = np.broadcast_to(np.array(col) / 255.0, xs.shape + (3,))
                lum = 0.0
            if not mask.any():
                continue
            sub_c = color[ymin:ymax + 1, xmin:xmax + 1]
            lumf = np.broadcast_to(lum, rgb.shape) if not np.isscalar(lum) else lum
            if col == "add":
                sub_c[mask] = np.minimum(sub_c[mask] + rgb[mask], 1.0)
            elif col == "trans":
                al = (samp[..., 3:4] / 255.0)
                sub_c[mask] = np.minimum(rgb * shade * jour * al + sub_c * (1 - al) + lumf * al, 1.0)[mask]
            else:
                sub_c[mask] = np.minimum(rgb * shade * jour + lumf, 1.0)[mask]
                sub_z[mask] = z[mask]

    img = Image.fromarray((np.clip(color, 0, 1) * 255).astype(np.uint8))
    return img.resize((size, size), Image.LANCZOS)

if __name__ == "__main__":
    import os
    path, out = sys.argv[1], sys.argv[2]
    if out.endswith(".gif"):
        frames = []
        anim_name = sys.argv[3] if len(sys.argv) > 3 else None
        m = json.load(open(path)); an = next((a for a in m["animations"] if a["name"] == anim_name), m["animations"][0])
        dur = float(an["length"]); fps = 24; n = max(12, int(round(dur * fps)))
        poser = os.environ.get("MODCONV") == "1" and os.environ.get("POSE", "1") != "0"
        arg_cam = sys.argv[4] if len(sys.argv) > 4 else "-44,34,-56"
        if arg_cam.startswith("auto:"):
            # Cadrage automatique : la pièce sur 8 instants de l'animation, vue depuis la direction donnée.
            pts = []
            for k in range(8):
                tk = k * dur / 8
                pk = pose_joueur(etat_de(an["name"]), tk, dur) if poser else None
                pts += points_de(load_model(path, anim_time=tk, anim_name=anim_name, pose=pk)[0])
            cam, tgt = cadrer(pts, [float(v) for v in arg_cam[5:].split(",")], marge=1.18, rayon_min=9.0)
        else:
            cam = tuple(float(v) for v in arg_cam.split(","))
            tgt = tuple(float(v) for v in sys.argv[5].split(",")) if len(sys.argv) > 5 else (0, 14, 0)
        for i in range(n):
            pz = pose_joueur(etat_de(an["name"]), i * dur / n, dur) if poser else None
            q, tex = load_model(path, anim_time=i * dur / n, anim_name=anim_name, pose=pz)
            frames.append(render(q + mannequin(pz), tex, cam, tgt, size=480).quantize(colors=128, dither=0))
            print("frame", i + 1, "/", n, flush=True)
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0, optimize=False)
        if os.environ.get("WEBP"):
            # Animation de l'état seule, pour la fiche du Vestiaire : WebP animé, léger, 12 images/s.
            im = [f.convert("RGB").resize((400, 400), Image.LANCZOS) for f in frames[::2]]
            im[0].save(os.environ["WEBP"], save_all=True, append_images=im[1:], duration=int(2000 / fps), loop=0, quality=78, method=4)
        print("ok", out); sys.exit()
    pz = None
    if os.environ.get("ANIM"):
        if os.environ.get("MODCONV") == "1" and os.environ.get("POSE", "1") != "0":
            m = json.load(open(path)); an = next((a for a in m["animations"] if a["name"] == os.environ["ANIM"]), None)
            pz = pose_joueur(etat_de(os.environ["ANIM"]), float(os.environ.get("T", "0")), float(an["length"]) if an else 1.0)
        quads, tex = load_model(path, anim_time=float(os.environ.get("T", "0")), anim_name=os.environ["ANIM"], pose=pz)
    else:
        quads, tex = load_model(path)
    scene = quads + mannequin(pz)
    if "--seule" in sys.argv:
        # Vignette : une seule vue (caméra, cible), recadrée serrée sur ce qui n'est pas le fond, en carré.
        i = sys.argv.index("--seule")
        cam = tuple(float(v) for v in sys.argv[i + 1].split(",")); tgt = tuple(float(v) for v in sys.argv[i + 2].split(","))
        fond = (18, 14, 20)
        img = render(scene, tex, cam, tgt, size=1000, bg=fond)
        # Cadre calculé sur le cosmétique seul (sans mannequin), au moins 42 % de la vue pour garder le corps en repère.
        a = np.asarray(render(quads, tex, cam, tgt, size=1000, bg=fond)).astype(int)
        ys, xs = np.nonzero(np.abs(a - np.array(fond)).max(axis=2) > 10)
        if len(xs):
            cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
            cote = max(max(xs.max() - xs.min(), ys.max() - ys.min()) * 1.22 + 24, 420)
            boite = [int(round(v)) for v in (cx - cote / 2, cy - cote / 2, cx + cote / 2, cy + cote / 2)]
            carre = Image.new("RGB", (boite[2] - boite[0], boite[3] - boite[1]), fond)
            carre.paste(img.crop((max(0, boite[0]), max(0, boite[1]), min(1000, boite[2]), min(1000, boite[3]))), (max(0, -boite[0]), max(0, -boite[1])))
            img = carre
        img.resize((480, 480), Image.LANCZOS).save(out, optimize=True)
        print("ok", out); sys.exit()
    zoom = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    target = (0, 14, 0)
    views = [
        ("Face 3/4", (-44, 34, -56)),
        ("Dos 3/4", (46, 36, 54)),
        ("Face", (0, 22, -74)),
        ("Dessus", (0.5, 85, -16)),
    ]
    if os.environ.get("CADRAGE") == "auto":
        pts = points_de(quads)
        tiles = [render(scene, tex, *cadrer(pts, c, marge=1.1, rayon_min=13.0), size=700) for _, c in views]   # rayon minimal : le corps reste en repère
    else:
        tiles = [render(scene, tex, tuple(v * zoom for v in c), target, size=700) for _, c in views]
    canvas = Image.new("RGB", (700 * 2 + 30, 700 * 2 + 70), (18, 14, 20))
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    except Exception:
        font = ImageFont.load_default()
    for i, (t, (name, _)) in enumerate(zip(tiles, views)):
        x, y = (i % 2) * 710 + 10, (i // 2) * 720 + 40
        canvas.paste(t, (x, y))
        d.text((x + 12, y - 32), name, fill=(235, 200, 200), font=font)
    canvas.save(out)
    print("ok", out)
