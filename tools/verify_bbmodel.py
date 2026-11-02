#!/usr/bin/env python3
"""Vérifie un .bbmodel contre les limites du mod de cosmétiques + les règles du projet.
Usage : python3 tools/verify_bbmodel.py modele.bbmodel [--max-ext 64] [--strict]
Code retour 0 si tout passe, 1 sinon."""
import sys, os, json, base64, io, zlib, math, collections, argparse
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("MODCONV", "1")
import render_bbmodel as rb

LIMITS = dict(cubes=8192, groups=2048, depth=64, anims=16, keyframes=32768, tex=512, compressed_kb=1000, ext=64.0,
              import_mb=16, stored_mb=8, rotation=360.0, inflate=8.0, name=64, uv_res=4096, anim_length=600.0, molang=256)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path"); ap.add_argument("--max-ext", type=float, default=LIMITS["ext"]); ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    ok = True
    def check(cond, msg, warn=False):
        nonlocal ok
        tag = "OK " if cond else ("WARN" if warn else "FAIL")
        if not cond and not warn: ok = False
        print(f"[{tag}] {msg}")

    raw = open(a.path, "rb").read()
    try:
        m = json.loads(raw)
    except Exception as e:
        print("[FAIL] JSON invalide :", e); return 1
    check(m.get("meta", {}).get("model_format") in ("free", "modded_entity"), f"format = {m.get('meta', {}).get('model_format')} (attendu free ou modded_entity)")
    # texture : une principale, en premier, plus au plus un calque lumineux `_e` (guide, section 5 bis)
    all_texs = m.get("textures", [])
    is_e = lambda t: os.path.splitext(t.get("name", ""))[0].endswith("_e")
    texs = [t for t in all_texs if not is_e(t)]
    e_texs = [t for t in all_texs if is_e(t)]
    check(len(texs) == 1 and len(e_texs) <= 1, f"{len(texs)} texture(s) principale(s) + {len(e_texs)} calque(s) _e (attendu 1 + 0 ou 1)")
    check(not all_texs or not is_e(all_texs[0]), "texture principale en premier")
    if texs:
        src = texs[0].get("source", "")
        if not src.startswith("data:image/png;base64,"):
            print("[FAIL] texture non embarquée en PNG base64"); return 1
        im = Image.open(io.BytesIO(base64.b64decode(src.split(",", 1)[1])))
        res = (m["resolution"]["width"], m["resolution"]["height"])
        check(im.format == "PNG", f"texture au format {im.format} (attendu PNG)")
        check(max(res) <= LIMITS["uv_res"], f"résolution UV {res} (≤ {LIMITS['uv_res']})")
        check(im.size[0] <= LIMITS["tex"] and im.size[1] <= LIMITS["tex"], f"texture {im.size[0]}x{im.size[1]} (≤ {LIMITS['tex']})")
        check(tuple(map(float, im.size)) == tuple(map(float, res)), f"résolution déclarée {res} = PNG {im.size}")
        alpha = np.array(im.convert("RGBA"))[:, :, 3]
        semi = int(((alpha > 0) & (alpha < 255)).sum())
        check(semi == 0, f"pixels semi-transparents : {semi}")
        for t in e_texs:
            ie = Image.open(io.BytesIO(base64.b64decode(t["source"].split(",", 1)[1])))
            check(ie.size == im.size, f"calque _e {ie.size} = texture {im.size}")
    # structure
    els = m["elements"]
    if len(all_texs) > 1:
        main_i = all_texs.index(texs[0]) if texs else 0
        bad_tex = sum(1 for e in els for fd in e["faces"].values() if fd.get("texture") not in (None, main_i))
        check(bad_tex == 0, f"faces assignées au calque _e : {bad_tex}")
    def walk(n, d=1):
        if isinstance(n, str): return 0, d - 1
        g, dm = 1, d
        for c in n.get("children", []):
            gg, dd = walk(c, d + 1); g += gg; dm = max(dm, dd)
        return g, dm
    groups, depth = 0, 0
    for n in m["outliner"]:
        g, d = walk(n); groups += g; depth = max(depth, d)
    check(len(els) <= LIMITS["cubes"], f"{len(els)} cubes (≤ {LIMITS['cubes']})")
    check(all(e.get("type", "cube") == "cube" for e in els), "cubes uniquement (pas de mesh)")
    check(groups <= LIMITS["groups"], f"{groups} groupes (≤ {LIMITS['groups']})")
    check(depth <= LIMITS["depth"], f"profondeur {depth} (≤ {LIMITS['depth']})")
    def group_nodes(n):
        if isinstance(n, str): return []
        return [n] + [g for c in n.get("children", []) for g in group_nodes(c)]
    gnodes = [g for n in m["outliner"] for g in group_nodes(n)]
    gnames = [g.get("name", "") for g in gnodes]
    check(all(len(n) <= LIMITS["name"] for n in gnames), f"noms de groupes ≤ {LIMITS['name']} caractères")
    check(len({n[:LIMITS["name"]] for n in gnames}) == len(gnames), "noms de groupes uniques (après coupure)")
    # particules (guide, section 5 ter)
    roots = [n.get("name", "") for n in m["outliner"] if isinstance(n, dict)]
    kinds = {n[len("particle_"):] for n in gnames if n.startswith("particle_")}
    bad_part = [n for n in gnames if n.startswith("particle_") and n not in roots]
    check(not bad_part, f"groupes particle_ à la racine : {len(bad_part)} hors racine")
    emits = [g for g in gnodes if g.get("name", "").startswith("emit_")]
    emit_kind = lambda name: name[len("emit_"):].rstrip("0123456789").rstrip("_")
    orphans = sorted({g["name"] for g in emits if emit_kind(g["name"]) not in kinds})
    check(not orphans, f"points emit_ sans particule : {orphans or 'aucun'}")
    missing = sorted(kinds - {emit_kind(g["name"]) for g in emits})
    check(not missing, f"particules sans point emit_ : {missing or 'aucune'}")
    check(len(kinds) <= 4, f"{len(kinds)} sorte(s) de particules (≤ 4)")
    check(len(emits) <= 32, f"{len(emits)} points emit_ (≤ 32)")
    check(all(not g.get("children") for g in emits), "points emit_ vides")
    over_rot = [x.get("name", "?") for x in els + gnodes if any(abs(v) > LIMITS["rotation"] for v in x.get("rotation", [0, 0, 0]))]
    check(not over_rot, f"rotations de base ≤ ±{LIMITS['rotation']:.0f}° : {len(over_rot)} hors limite" + (f" ({', '.join(over_rot[:5])}…)" if over_rot else ""))
    bad_face = [e["name"] for e in els if any(fd.get("rotation", 0) % 90 for fd in e["faces"].values())]
    check(not bad_face, f"rotations de face multiples de 90° : {len(bad_face)} hors règle" + (f" ({', '.join(bad_face[:5])}…)" if bad_face else ""))
    over_inf = [e["name"] for e in els if abs(e.get("inflate", 0)) > LIMITS["inflate"]]
    check(not over_inf, f"inflate ≤ ±{LIMITS['inflate']:.0f} : {len(over_inf)} hors limite" + (f" ({', '.join(over_inf[:5])}…)" if over_inf else ""))
    thin = [e["name"] for e in els if any(abs(e["to"][i] - e["from"][i]) < 1e-6 for i in range(3))]
    check(not thin, f"épaisseur nulle : {len(thin)} élément(s)" + (f" ({', '.join(thin[:5])}…)" if thin else ""))
    cnt = collections.Counter((tuple(e["from"]), tuple(e["to"]), tuple(e.get("rotation", [0, 0, 0]))) for e in els)
    dup = sum(v - 1 for v in cnt.values() if v > 1)
    check(dup == 0, f"éléments strictement superposés : {dup}")
    for e in els:
        for f, fd in e["faces"].items():
            if fd.get("texture") is not None and len(fd["uv"]) == 4 and (fd["uv"][0] == fd["uv"][2] or fd["uv"][1] == fd["uv"][3]):
                check(False, f"UV dégénérée sur {e['name']}.{f}", warn=True); break
    # animations
    anims = m.get("animations", [])
    check(len(anims) <= LIMITS["anims"], f"{len(anims)} animations (≤ {LIMITS['anims']})")
    nk = sum(len(b["keyframes"]) for an in anims for b in an["animators"].values())
    check(nk <= LIMITS["keyframes"], f"{nk} keyframes (≤ {LIMITS['keyframes']})")
    bad_ch = collections.Counter(k["channel"] for an in anims for b in an["animators"].values() for k in b["keyframes"] if k["channel"] not in ("rotation", "position", "scale"))
    check(not bad_ch, f"canaux non supportés par le mod : {dict(bad_ch) or 'aucun'}")
    names = [an["name"] for an in anims]
    short = {n.split(".")[-1] for n in names}
    for need in ("idle", "fly", "glide", "run", "sneak"):
        check(need in short, f"animation '{need}' présente", warn=True)
    check(all(len(n) <= 64 for n in names), "noms d'animation ≤ 64 caractères")
    too_long = [an["name"] for an in anims if float(an["length"]) > LIMITS["anim_length"]]
    check(not too_long, f"durée des animations ≤ {LIMITS['anim_length']:.0f} s" + (f" : {', '.join(too_long)}" if too_long else ""))
    exprs = [v for an in anims for b in an["animators"].values() for k in b["keyframes"] for dp in k.get("data_points", []) for v in dp.values() if isinstance(v, str)]
    longest = max(map(len, exprs), default=0)
    check(longest <= LIMITS["molang"], f"expression Molang la plus longue : {longest} caractères (≤ {LIMITS['molang']})")
    # boucles et extension (évaluées avec le renderer en convention mod)
    ext = 0.0; ext_where = None
    for an in anims:
        L = float(an["length"])
        if an.get("loop") == "loop":
            qa, _ = rb.load_model(a.path, anim_time=0.0, anim_name=an["name"])
            qb, _ = rb.load_model(a.path, anim_time=L - 1e-6, anim_name=an["name"])
            pa = np.array([p for q in qa for p in q[0]]); pb = np.array([p for q in qb for p in q[0]])
            gap = float(np.abs(pa - pb).max()) if len(pa) else 0.0
            check(gap < 0.05, f"boucle '{an['name']}' fermée (écart {gap:.3f} px)")
        for t in np.linspace(0, L, 9):
            q, _ = rb.load_model(a.path, anim_time=float(t), anim_name=an["name"])
            P = np.array([p for qq in q for p in qq[0]])
            if not len(P): continue
            e = max(abs(P[:, 0]).max(), abs(P[:, 2]).max(), P[:, 1].max(), -P[:, 1].min())
            if e > ext: ext, ext_where = e, (an["name"], round(float(t), 2))
    check(ext < a.max_ext, f"extension max {ext:.1f} px dans {ext_where} (< {a.max_ext})")
    if ext >= 60 and ext < a.max_ext: check(False, "extension > 60 px : peu de marge", warn=True)
    # poids
    comp = len(zlib.compress(raw, 9)) // 1024
    print(f"[INFO] poids brut {len(raw) // 1024} Ko | compressé {comp} Ko | texture {len(texs[0]['source']) // 1024 if texs else 0} Ko")
    check(comp < LIMITS["compressed_kb"], f"compressé {comp} Ko (< {LIMITS['compressed_kb']})")
    check(len(raw) <= LIMITS["import_mb"] * 1024 * 1024, f"fichier importé ≤ {LIMITS['import_mb']} Mo")
    check(len(raw) <= LIMITS["stored_mb"] * 1024 * 1024, f"brut ≤ {LIMITS['stored_mb']} Mo (limite stockée ; taille nettoyée par le serveur non mesurable ici)", warn=True)
    if a.strict: check(len(raw) < 1_000_000, "brut < 1 Mo (strict)", warn=True)
    print("\nRÉSULTAT :", "OK — livrable" if ok else "ÉCHEC — ne pas livrer")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
