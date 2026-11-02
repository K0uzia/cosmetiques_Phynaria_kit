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
def molang(expr, t):
    try: return float(expr)
    except ValueError: pass
    e = expr.replace("query.", "q.").replace("Math.", "math.")
    return float(eval(e, {"__builtins__": {}}, {"math": _MolangMath, "q": _Q(t)}))

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

def load_model(path, anim_time=None, anim_name=None):
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
    tw = m["resolution"]["width"]; th = m["resolution"]["height"]
    by_id = {e["uuid"]: e for e in m["elements"]}

    quads = []  # (4 points world, 4 uv (0..1), color or None)

    def transform_chain(chain):
        def f(p):
            p = np.array(p, dtype=float)
            for origin, R, S, pos in chain:   # élément d'abord, puis groupes parents
                p = R @ (S * (p - origin)) + origin + pos
            return p
        return f

    def walk2(node, parents):
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
                uvs = [(u1 / tw, v1 / th), (u2 / tw, v1 / th), (u2 / tw, v2 / th), (u1 / tw, v2 / th)]
                quads.append((pts, uvs, None))
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
            for c in node.get("children", []):
                walk2(c, parents + [(np.array(node.get("origin", [0, 0, 0]), float), R, S, pos)])

    for n in m["outliner"]:
        if isinstance(n, dict) and n.get("name", "").startswith("particle_"):
            continue   # modèle de particule : pas porté par le joueur
        walk2(n, [])
    return quads, tex

def mannequin():
    """Joueur gris (Steve). Face avant = -z (nord), dos = +z."""
    quads = []
    def box(a, b, col, front_col=None):
        for fname, fn in FACE_CORNERS.items():
            c = front_col if (fname == "north" and front_col) else col
            quads.append(([np.array(p, float) for p in fn(a, b)], None, c))
    g1, g2, g3 = (120, 120, 128), (100, 100, 108), (88, 88, 96)
    box((-4, 24, -4), (4, 32, 4), g1, (135, 135, 143))   # tête
    box((-4, 12, -2), (4, 24, 2), g2)                    # torse
    box((-8, 12, -2), (-4, 24, 2), g3); box((4, 12, -2), (8, 24, 2), g3)   # bras
    box((-4, 0, -2), (0, 12, 2), g2); box((0, 0, -2), (4, 12, 2), g3)      # jambes
    # yeux
    for x in (-2.5, 1.0):
        quads.append(([np.array(p, float) for p in [(x, 29, -4.01), (x + 1.5, 29, -4.01), (x + 1.5, 27.5, -4.01), (x, 27.5, -4.01)]], None, (30, 30, 40)))
    return quads

def render(quads, tex, cam_pos, target, size=900, fov=28, bg=(18, 14, 20)):
    S = 2  # supersampling
    W = H = size * S
    cam_pos = np.array(cam_pos, float); target = np.array(target, float)
    fwd = target - cam_pos; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    f = 1 / math.tan(math.radians(fov) / 2)
    light = np.array([-0.4, 1.0, 0.6]); light /= np.linalg.norm(light)

    color = np.zeros((H, W, 3), np.float32); color[:] = np.array(bg) / 255
    zbuf = np.full((H, W), np.inf, np.float32)
    texarr = np.array(tex) if tex is not None else None

    def project(p):
        d = p - cam_pos
        x, y, z = d @ right, d @ up, d @ fwd
        return np.array([(x / z) * f * 0.5 * W + W / 2, -(y / z) * f * 0.5 * H + H / 2, z])

    for pts, uvs, col in quads:
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
            if col is None:
                uvA, uvB, uvC = (np.array(uvs[i]) for i in tri)
                u = (l1 * uvA[0] / A[2] + l2 * uvB[0] / B[2] + l3 * uvC[0] / C[2]) * z
                v = (l1 * uvA[1] / A[2] + l2 * uvB[1] / B[2] + l3 * uvC[1] / C[2]) * z
                tu = np.clip((u * texarr.shape[1]).astype(int), 0, texarr.shape[1] - 1)
                tv = np.clip((v * texarr.shape[0]).astype(int), 0, texarr.shape[0] - 1)
                samp = texarr[tv, tu]
                mask &= samp[..., 3] > 127
                rgb = samp[..., :3] / 255.0
            else:
                rgb = np.broadcast_to(np.array(col) / 255.0, xs.shape + (3,))
            if not mask.any():
                continue
            sub_c = color[ymin:ymax + 1, xmin:xmax + 1]
            sub_c[mask] = (rgb * shade)[mask]
            sub_z[mask] = z[mask]

    img = Image.fromarray((np.clip(color, 0, 1) * 255).astype(np.uint8))
    return img.resize((size, size), Image.LANCZOS)

if __name__ == "__main__":
    path, out = sys.argv[1], sys.argv[2]
    if out.endswith(".gif"):
        frames = []
        anim_name = sys.argv[3] if len(sys.argv) > 3 else None
        m = json.load(open(path)); an = next((a for a in m["animations"] if a["name"] == anim_name), m["animations"][0])
        dur = float(an["length"]); fps = 24; n = max(12, int(round(dur * fps)))
        cam = tuple(float(v) for v in sys.argv[4].split(",")) if len(sys.argv) > 4 else (-44, 34, -56)
        tgt = tuple(float(v) for v in sys.argv[5].split(",")) if len(sys.argv) > 5 else (0, 14, 0)
        for i in range(n):
            q, tex = load_model(path, anim_time=i * dur / n, anim_name=anim_name)
            frames.append(render(q + mannequin(), tex, cam, tgt, size=480).quantize(colors=128, dither=0))
            print("frame", i + 1, "/", n, flush=True)
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0, optimize=False)
        print("ok", out); sys.exit()
    import os
    if os.environ.get("ANIM"):
        quads, tex = load_model(path, anim_time=float(os.environ.get("T", "0")), anim_name=os.environ["ANIM"])
    else:
        quads, tex = load_model(path)
    scene = quads + mannequin()
    zoom = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    target = (0, 14, 0)
    views = [
        ("Face 3/4", (-44, 34, -56)),
        ("Dos 3/4", (46, 36, 54)),
        ("Face", (0, 22, -74)),
        ("Dessus", (0.5, 85, -16)),
    ]
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
