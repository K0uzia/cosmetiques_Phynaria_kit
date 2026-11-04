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
              import_mb=16, stored_mb=8, rotation=360.0, inflate=8.0, name=64, uv_res=4096, anim_length=600.0, molang=512, sons=32)

def _nom_groupe(n):
    return n.get("name", "") if isinstance(n, dict) else ""


def _groupes(n):
    if not isinstance(n, dict):
        return []
    return [n] + [g for c in n.get("children", []) for g in _groupes(c)]


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
    # textures : une principale, en premier, plus au plus une _e (lumière), une _r (masque de reflets), une _m (matcap) (guide, sections 5 à 5 quater)
    all_texs = m.get("textures", [])
    suffixe = lambda t: next((x for x in ("_e", "_r", "_m") if os.path.splitext(t.get("name", ""))[0].endswith(x)), "")
    is_e = lambda t: suffixe(t) != ""
    texs = [t for t in all_texs if not is_e(t)]
    e_texs = [t for t in all_texs if suffixe(t) in ("_e", "_r")]
    m_texs = [t for t in all_texs if suffixe(t) == "_m"]
    nb = collections.Counter(suffixe(t) for t in all_texs if is_e(t))
    check(len(texs) == 1 and all(v <= 1 for v in nb.values()),
          f"{len(texs)} texture(s) principale(s) + calques {dict(nb) or 'aucun'} (attendu 1 + au plus une _e, une _r, une _m)")
    check(not all_texs or not is_e(all_texs[0]), "texture principale en premier")
    for t in m_texs:
        im_m = Image.open(io.BytesIO(base64.b64decode(t["source"].split(",", 1)[1])))
        check(max(im_m.size) <= 256, f"matcap _m {im_m.size[0]}x{im_m.size[1]} (≤ 256)")
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
        a_trans = any(_nom_groupe(n).startswith("trans_") for n in m.get("outliner", []) for n in _groupes(n))
        if a_trans and semi:
            print(f"[INFO] pixels semi-transparents : {semi}, permis dans les groupes trans_ (guide 4 bis ; à garder sur les seules faces trans_)")
        else:
            check(semi == 0, f"pixels semi-transparents : {semi}")
        for t in e_texs:
            ie = Image.open(io.BytesIO(base64.b64decode(t["source"].split(",", 1)[1])))
            check(ie.size == im.size, f"calque {suffixe(t)} {ie.size} = texture {im.size}")
    # structure
    els = m["elements"]
    if len(all_texs) > 1:
        main_i = all_texs.index(texs[0]) if texs else 0
        bad_tex = sum(1 for e in els for fd in e["faces"].values() if fd.get("texture") not in (None, main_i))
        check(bad_tex == 0, f"faces assignées à un calque (_e, _r, _m) : {bad_tex}")
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
    # emit_mc_<id> et ctrl_<…> peuvent se répéter (guide 5 ter et 4 bis) ; les autres noms restent uniques
    uniques = [n for n in gnames if not n.startswith(("emit_mc_", "ctrl_"))]
    check(len({n[:LIMITS["name"]] for n in uniques}) == len(uniques), "noms de groupes uniques (après coupure ; emit_mc_ et ctrl_ exceptés)")
    # particules (guide, section 5 ter)
    roots = [n.get("name", "") for n in m["outliner"] if isinstance(n, dict)]
    kinds = {n[len("particle_"):] for n in gnames if n.startswith("particle_")}
    bad_part = [n for n in gnames if n.startswith("particle_") and n not in roots]
    check(not bad_part, f"groupes particle_ à la racine : {len(bad_part)} hors racine")
    emits = [g for g in gnodes if g.get("name", "").startswith("emit_")]
    emit_kind = lambda name: name[len("emit_"):].rstrip("0123456789").rstrip("_")
    # emit_mc_<identifiant> : particule vanilla (fonction anticipée, .claude/rules/conventions-anticipees.md), sans particle_ associée
    orphans = sorted({g["name"] for g in emits if not g["name"].startswith("emit_mc_") and emit_kind(g["name"]) not in kinds})
    check(not orphans, f"points emit_ sans particule : {orphans or 'aucun'}")
    missing = sorted(kinds - {emit_kind(g["name"]) for g in emits})
    check(not missing, f"particules sans point emit_ : {missing or 'aucune'}")
    check(len(kinds) <= 4, f"{len(kinds)} sorte(s) de particules (≤ 4)")
    check(len(emits) <= 32, f"{len(emits)} points emit_ (≤ 32)")
    check(all(not g.get("children") or all(isinstance(c, dict) and c.get("name", "").startswith("ctrl_") for c in g["children"]) for g in emits),
          "points emit_ vides (hors groupes ctrl_)")
    ctrls = [g for g in gnodes if g.get("name", "").startswith("ctrl_")]
    check(all(not g.get("children") for g in ctrls), f"groupes ctrl_ vides : {len(ctrls)}")
    CTRL_OK = ("ctrl_alpha", "ctrl_teinte", "ctrl_lumiere", "ctrl_uv")
    bad_ctrl = sorted({g["name"] for g in ctrls if g["name"] not in CTRL_OK})
    check(not bad_ctrl, f"groupes ctrl_ connus du mod ({', '.join(CTRL_OK)}) : {bad_ctrl or 'tous'}")
    mc = sorted({g["name"] for g in emits if g["name"].startswith("emit_mc_")})
    check(len(mc) <= 4, f"{len(mc)} sorte(s) de particules Minecraft (≤ 4)")
    check(not [n for n in mc if n[-1].isdigit() and not n.startswith("emit_mc_dust_")], f"emit_mc_ sans chiffre au bout (le chiffre fait partie du nom de la particule) : {mc or 'aucun'}")
    # fonctions avancées (guide 4 bis, 5 quater, 6.4, 6.5) : le renderer simule add_ et trans_, pas le reste
    avance = sorted({p for n in gnames for p in ("add_", "trans_", "cam_", "camy_", "ctrl_", "phys_", "emit_mc_") if n.startswith(p)}
                    | {p for an in m.get("animations", []) for p in ("overlay_", "event_") if an.get("name", "").split(".")[-1].startswith(p)})
    if avance:
        print(f"[INFO] fonctions avancées : {', '.join(avance)} (aperçu : add_, trans_, cam_ et camy_ simulés ; le reste se juge avec /cosmetique apercu)")
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
    bad_ch = collections.Counter(k["channel"] for an in anims for b in an["animators"].values() for k in b["keyframes"]
                                 if k["channel"] not in ("rotation", "position", "scale") and not (k["channel"] == "sound" and b.get("type") == "effect"))
    check(not bad_ch, f"canaux non supportés par le mod : {dict(bad_ch) or 'aucun'}")
    sons = [(an["name"], sum(1 for b in an["animators"].values() for k in b["keyframes"] if k["channel"] == "sound")) for an in anims]
    trop = [n for n, c in sons if c > LIMITS["sons"]]
    check(not trop, f"sons ≤ {LIMITS['sons']} par animation" + (f" : {trop}" if trop else ""))
    names = [an["name"] for an in anims]
    short = {n.split(".")[-1] for n in names}
    for need in ("idle", "fly", "glide", "run", "sneak"):
        check(need in short, f"animation '{need}' présente", warn=True)
    check(all(len(n) <= 64 for n in names), "noms d'animation ≤ 64 caractères")
    too_long = [an["name"] for an in anims if float(an["length"]) > LIMITS["anim_length"]]
    check(not too_long, f"durée des animations ≤ {LIMITS['anim_length']:.0f} s" + (f" : {', '.join(too_long)}" if too_long else ""))
    exprs = [v for an in anims for b in an["animators"].values() if b.get("type") != "effect" for k in b["keyframes"] for dp in k.get("data_points", []) for v in dp.values() if isinstance(v, str)]
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
            # faces cachées par ctrl_alpha (ramenées à l'origine) à l'un des deux instants : hors comparaison
            vis = ~((np.abs(pa).max(axis=1) < 1e-9) | (np.abs(pb).max(axis=1) < 1e-9)) if len(pa) else np.zeros(0, bool)
            gap = float(np.abs(pa[vis] - pb[vis]).max()) if vis.any() else 0.0
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
