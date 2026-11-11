"""Optimise le poids d'un .bbmodel : simplification des courbes de keyframes (Ramer-Douglas-Peucker par canal),
arrondis, suppression des champs facultatifs, PNG optimisé, JSON compact."""
import re
import json, sys, base64, io, uuid
from PIL import Image

def rdp(points, eps):
    """points : [(t, (x,y,z))] ; garde les points nécessaires pour une interpolation linéaire à eps près."""
    if len(points) <= 2: return points
    (t0, v0), (t1, v1) = points[0], points[-1]
    best, idx = 0.0, -1
    for i in range(1, len(points) - 1):
        t, v = points[i]
        f = (t - t0) / (t1 - t0)
        err = max(abs(v[k] - (v0[k] + f * (v1[k] - v0[k]))) for k in range(3))
        if err > best: best, idx = err, i
    if best <= eps: return [points[0], points[-1]]
    return rdp(points[:idx + 1], eps)[:-1] + rdp(points[idx:], eps)

def simplify(keyframes, eps_rot=0.3, eps_pos=0.05, eps_scale=0.002):
    # échelle : 0,002 et 4 décimales (une échelle de 0,16 arrondie à 0,01 déplaçait de 0,8 px une main à 160 px du pivot,
    # effet_admin_neant v5)
    out = []
    for ch in ("rotation", "position", "scale"):
        kfs = sorted([k for k in keyframes if k["channel"] == ch], key=lambda k: k["time"])
        if not kfs: continue
        def is_num(v):
            try: float(v); return True
            except ValueError: return False
        if not all(is_num(k["data_points"][0][a]) for k in kfs for a in "xyz"):
            # keyframes Molang : conservés tels quels (compactés)
            for k in kfs:
                kk = {"channel": ch, "data_points": k["data_points"], "time": round(k["time"], 3)}
                if k.get("interpolation", "linear") != "linear": kk["interpolation"] = k["interpolation"]
                out.append(kk)
            continue
        pts = [(k["time"], tuple(float(k["data_points"][0][a]) for a in "xyz")) for k in kfs]
        eps = {"rotation": eps_rot, "position": eps_pos, "scale": eps_scale}[ch]
        kept = rdp(pts, eps)
        # canal constant -> un seul keyframe
        if len(kept) == 2 and all(abs(kept[0][1][k] - kept[1][1][k]) <= eps for k in range(3)):
            kept = kept[:1]
        interp = kfs[0].get("interpolation", "linear")
        for t, v in kept:
            nd = 4 if ch == "scale" else 2
            k = {"channel": ch, "data_points": [{"x": str(round(v[0], nd)), "y": str(round(v[1], nd)), "z": str(round(v[2], nd))}], "time": round(t, 3)}
            if interp != "linear": k["interpolation"] = interp
            out.append(k)
    # autres canaux (clés de son de la piste Effets, guide 6.5) : conservés tels quels
    out += [k for k in keyframes if k["channel"] not in ("rotation", "position", "scale")]
    return out

def signes_molang(expr):
    """`a--b` -> `a+b`, `a+-b` -> `a-b`, `a-+b` -> `a-b` : le second signe est unaire, le calcul ne change pas.
    Le parseur du mod n'a jamais été vu sur ces doubles signes, et `--` cassait la visionneuse (décrémentation JS)."""
    prev = None
    while prev != expr:
        prev = expr
        expr = re.sub(r"--", "+", expr)
        expr = re.sub(r"\+-|-\+", "-", expr)
        expr = re.sub(r"\+\+", "+", expr)
    return expr


def nettoyer_molang(m):
    n = 0
    for a in m.get("animations", []):
        for a2 in a.get("animators", {}).values():
            for k in a2.get("keyframes", []):
                for dp in k.get("data_points", []):
                    for ax in ("x", "y", "z"):
                        v = dp.get(ax)
                        if isinstance(v, str):
                            w = signes_molang(v)
                            if w != v:
                                dp[ax] = w; n += 1
    return n


def optimize(path_in, path_out):
    m = json.load(open(path_in))
    # les champs non traités ici passent tels quels, dont unhandled_root_fields.phynaria (réglages des particules,
    # tools/particules.py) : ne jamais reconstruire le modèle clé par clé
    nettoyer_molang(m)
    # keyframes
    before = sum(len(a2["keyframes"]) for a in m["animations"] for a2 in a["animators"].values())
    for a in m["animations"]:
        for a2 in a["animators"].values():
            a2["keyframes"] = simplify(a2["keyframes"])
        for k in ("anim_time_update", "blend_weight", "start_delay", "loop_delay"):
            if a.get(k) == "": del a[k]
    after = sum(len(a2["keyframes"]) for a in m["animations"] for a2 in a["animators"].values())
    # éléments : arrondis, faces sans texture supprimées (Blockbench les recrée vides)
    for e in m["elements"]:
        for k in ("from", "to", "origin"): e[k] = [round(v, 3) for v in e[k]]
        if "rotation" in e: e["rotation"] = [round(v, 2) for v in e["rotation"]]
        e["faces"] = {f: {"uv": [round(v, 2) for v in d["uv"]], "texture": 0} for f, d in e["faces"].items() if d.get("texture") is not None}
    # texture : PNG optimisé
    for t in m["textures"]:
        head, b64 = t["source"].split(",", 1)
        img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGBA")
        buf = io.BytesIO(); img.save(buf, "PNG", optimize=True)      # RGBA complet (budget suffisant)
        t["source"] = head + "," + base64.b64encode(buf.getvalue()).decode()
    json.dump(m, open(path_out, "w"), separators=(",", ":"))
    json.load(open(path_out))
    return before, after

if __name__ == "__main__":
    import os
    src, dst = sys.argv[1], sys.argv[2]
    b, a = optimize(src, dst)
    print(f"{src}: {os.path.getsize(src)//1024} Ko -> {dst}: {os.path.getsize(dst)//1024} Ko | keyframes {b} -> {a}")
