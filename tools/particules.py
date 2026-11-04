"""Retire d'un modèle les particules qui tombent et se posent, réservées aux ailes (.claude/rules/retours-en-jeu.md).
Usage dans un générateur, juste avant d'écrire le modèle :
    retirer_particules(model)                 # retire groupes particle_<nom>, points emit_<nom> et animations particle_*
    retirer_particules(model, montantes=True) # garde des particules qui montent : retire seulement les animations _rest (posées au sol)
Le modèle est modifié sur place (listes vidées et remplies), pour que les décomptes imprimés ensuite restent justes."""


def retirer_particules(model, montantes=False):
    anims = model["animations"]
    if montantes:
        anims[:] = [a for a in anims if not (a["name"].startswith("particle_") and a["name"].endswith("_rest"))]
        return
    retires, cubes = set(), set()

    def tout(n):
        """uuid des groupes et des cubes d'un nœud, pour les retirer avec lui."""
        if isinstance(n, str):
            cubes.add(n)
            return
        retires.add(n["uuid"])
        for c in n.get("children", []):
            tout(c)

    def filtrer(enfants):
        garde = []
        for c in enfants:
            if isinstance(c, dict) and c.get("name", "").startswith(("particle_", "emit_")):
                tout(c)
                continue
            if isinstance(c, dict):
                c["children"] = filtrer(c.get("children", []))
            garde.append(c)
        return garde

    model["outliner"][:] = filtrer(model["outliner"])
    model["elements"][:] = [e for e in model["elements"] if e["uuid"] not in cubes]
    anims[:] = [a for a in anims if not a["name"].startswith("particle_")]
    for a in anims:
        a["animators"] = {k: v for k, v in a.get("animators", {}).items() if k not in retires}


# ---------------------------------------------------------------- vapeur modélisée à la place des particules Minecraft
# Constat en jeu (2026-11-04, docs/dev/bug_rendu_avance_pour_dev.md, point 4) : les points emit_mc_… lancent leurs particules
# à plusieurs blocs du cosmétique, sans suivre l'animation. Les particules modélisées (particle_<nom> + emit_<nom>) sont,
# elles, bien placées (validé sur Aurelion). remplacer_emit_mc() convertit les points emit_mc_<id> en points emit_<nom>
# d'une particule modélisée (bouffée douce peinte dans une zone libre de la texture), en gardant leur place et leur
# orientation (+Y = direction de départ).
#     remplacer_emit_mc(model, {"white_smoke": "vapeur", "white_ash": "souffle", "poof": "vapeur"})
# À appeler juste avant d'écrire le modèle. Les fichiers PNG à côté du générateur sont réécrits.
SORTES = {
    # nom : (taille en px, couleur claire, couleur d'ombre, opacité au centre)
    "vapeur": (2.6, (248, 250, 252), (196, 204, 212), 230),
    "souffle": (1.4, (236, 242, 248), (180, 192, 206), 170),
}


def _bouffee(n, clair, ombre, a_max, seed):
    import numpy as np
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:n, 0:n]
    u, v = (xx + 0.5) / n * 2 - 1, (yy + 0.5) / n * 2 - 1
    d = np.full((n, n), 9.0)
    for _ in range(6):                      # quelques lobes : bord arrondi irrégulier, pas un disque
        cx, cy, r = rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(0.45, 0.62)
        d = np.minimum(d, np.hypot(u - cx, v - cy) / r)
    a = np.clip(1 - d, 0, 1) ** 0.8
    lum = np.clip(1 - np.hypot(u + 0.3, v + 0.35) / 1.4, 0, 1)
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = (np.array(ombre) + (np.array(clair) - np.array(ombre)) * lum[..., None]).astype(np.uint8)
    out[..., 3] = np.where(a > 0.06, np.clip(a * a_max * 1.25, 1, 254), 0).astype(np.uint8)
    return out


def remplacer_emit_mc(model, conversion):
    import base64, io, os, uuid
    import numpy as np
    from PIL import Image
    tex0 = model["textures"][0]
    img = np.array(Image.open(io.BytesIO(base64.b64decode(tex0["source"].split(",", 1)[1]))).convert("RGBA"))
    H, W = img.shape[:2]
    N = 24                                   # texels par bouffée

    def place_libre():
        occ = img[..., 3] > 0
        for y in range(H - N - 6, 0, -2):
            for x in range(W - N - 6, 0, -2):
                if not occ[y - 1:y + N + 1, x - 1:x + N + 1].any():
                    return x, y
        raise AssertionError("pas de place libre dans la texture pour la bouffée")

    vus, nb = {}, {}

    def convertir(n):
        if not isinstance(n, dict):
            return
        # conversion[id] = None : le point est retiré (ex. poussière colorée d'une aura qui a déjà ses étincelles)
        n["children"] = [c for c in n.get("children", []) if not (isinstance(c, dict) and c.get("name", "").startswith("emit_mc_")
                                                                   and conversion.get(c["name"][len("emit_mc_"):], "?") is None)]
        nom = n.get("name", "")
        if nom.startswith("emit_mc_"):
            ident = nom[len("emit_mc_"):]
            sorte = conversion.get(ident)
            if sorte is None:
                raise AssertionError(f"particule Minecraft sans conversion : {ident}")
            k = nb.get(sorte, 0) + 1
            nb[sorte] = k
            n["name"] = f"emit_{sorte}" + (str(k) if k > 1 else "")
            n["children"] = [c for c in n.get("children", []) if not (isinstance(c, dict) and c.get("name", "").startswith("ctrl_"))]
            vus.setdefault(sorte, True)
        for c in n.get("children", []):
            convertir(c)

    for n in model["outliner"]:
        convertir(n)
    for i, sorte in enumerate(vus):
        taille, clair, ombre, a_max = SORTES[sorte]
        x, y = place_libre()
        img[y:y + N, x:x + N] = _bouffee(N, clair, ombre, a_max, 31 + i)
        uid, gid, tid = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        h = taille / 2
        # recette validée : un seul cube de 0,3 px, face up seule, au-dessus du pivot ; groupe trans_ pour la semi-transparence
        model["elements"].append({"name": sorte, "type": "cube", "uuid": uid, "box_uv": False, "from": [-h, 0.3, -h], "to": [h, 0.6, h],
                                  "origin": [0, 0.45, 0], "faces": {"up": {"uv": [x, y, x + N, y + N], "texture": 0}}})
        model["outliner"].append({"name": f"particle_{sorte}", "origin": [0, 0, 0], "uuid": gid,
                                  "children": [{"name": f"trans_particule_{sorte}", "origin": [0, 0, 0], "uuid": tid, "children": [uid]}]})
        # chute / montée : lente rotation sur elle-même, et la bouffée qui s'étale ; sans place (16 animations), la particule
        # n'a pas d'animation et se balance toute seule (guide 5 ter §3)
        if len(model["animations"]) >= 15:       # une place gardée pour overlay_ambiance (tools/ambiance.py)
            continue
        L = 2.0
        cles = [{"channel": "rotation", "data_points": [{"x": "0", "y": str(round(360 * t / L, 1)), "z": "0"}], "time": t, "interpolation": "linear"} for t in (0, L / 2, L)]
        cles += [{"channel": "scale", "data_points": [{"x": "math.lerp(0.7, 1.5, math.mod(q.anim_time, 2) / 2)", "y": "1", "z": "math.lerp(0.7, 1.5, math.mod(q.anim_time, 2) / 2)"}],
                  "time": 0, "interpolation": "linear"}]
        model["animations"].append({"uuid": str(uuid.uuid4()), "name": f"particle_{sorte}_fall", "loop": "loop", "override": False, "length": L,
                                    "snapping": 24, "selected": False, "animators": {gid: {"name": f"particle_{sorte}", "type": "bone", "keyframes": cles}}})
    assert len(model["animations"]) <= 16, "16 animations au plus"
    b = io.BytesIO()
    Image.fromarray(img, "RGBA").save(b, "PNG", optimize=True)
    tex0["source"] = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
    Image.fromarray(img, "RGBA").save(tex0["name"], optimize=True)
