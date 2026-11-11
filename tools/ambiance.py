"""Ambiance d'un cosmétique selon la météo et l'heure (guide 4 bis, 6.3, 6.4), et reflets lumineux sur les arêtes polies.
Usage dans un générateur, juste avant d'écrire le modèle (après limiter_sons) :
    ajouter_ambiance(model)
Ajoute :
- dans chaque groupe de premier niveau, deux groupes vides ctrl_teinte et ctrl_lumiere ;
- une couche permanente overlay_ambiance (jouée par-dessus tous les états) qui les pilote en Molang :
  * pluie (q.is_in_rain, lissée par la variable v.pluie) : couleurs plus sombres et plus froides, comme du métal mouillé,
    et calque _e plus fort (les lampes se reflètent dans l'eau) ;
  * nuit (q.time_of_day) : calque _e plus fort ;
  * toujours : calque _e renforcé (retour « ça manque de lumineux ») ;
- dans le calque _e (créé s'il manque) : un éclat doux sur les texels très clairs et chauds (arêtes polies du laiton et du
  cuivre, têtes de rivets), visible la nuit. Les fichiers <texture>_e.png à côté du générateur sont réécrits.
Limite : le guide ne permet pas de faire varier les reflets _r ; le « brillant mouillé » passe par la teinte et la lumière.
Le renderer calcule les variables à l'état stable ; ctrl_teinte et ctrl_lumiere ne sont pas simulés (à juger en jeu)."""
import base64, io, os, uuid
import numpy as np
from PIL import Image

PLUIE = "v.pluie = math.lerp(v.pluie, q.is_in_rain, math.min(1, q.delta_time * 0.6))"
NUIT = "math.clamp((0.27 - math.abs(q.time_of_day - 0.5)) * 6, 0, 1)"


def _png(src):
    return np.array(Image.open(io.BytesIO(base64.b64decode(src.split(",", 1)[1]))).convert("RGBA"))


def _b64(arr):
    b = io.BytesIO()
    Image.fromarray(arr, "RGBA").save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


REFLETS = False   # capture du 2026-11-03 : le mod pose le reflet sur toute la face, découpe comprise (rectangles clairs) ; à remettre après correctif


def ajouter_ambiance(model, lumiere=0.3, nuit=0.5, pluie_lumiere=0.3, mouille=(0.22, 0.17, 0.06), eclat=0.30, foyer=2.4):
    if not REFLETS:
        model["textures"][:] = [t for t in model["textures"] if not os.path.splitext(t.get("name", ""))[0].endswith(("_r", "_m"))]
    # --- éclats sur les arêtes claires et chaudes, dans le calque _e
    texs = model["textures"]
    nom_e = lambda t: os.path.splitext(t.get("name", ""))[0]
    main = next(t for t in texs if not nom_e(t).endswith(("_e", "_r", "_m")))
    te = next((t for t in texs if nom_e(t).endswith("_e")), None)
    m = _png(main["source"]).astype(np.int32)
    e = _png(te["source"]).astype(np.int32) if te else np.zeros_like(m)
    r, g, b, a = m[..., 0], m[..., 1], m[..., 2], m[..., 3]
    chaud_clair = (a > 0) & (r > 200) & (r >= g) & (g > b + 25) & (r - b > 55)
    add = (m[..., :3] * eclat).astype(np.int32)
    # sources existantes (cadrans, foyers, lentilles, lampes) : lueurs déjà peintes, rendues nettes et franches
    source = (e[..., 3] > 0) & (e[..., :3].max(axis=2) > 24) & (a > 0)
    e[..., :3] = np.where(source[..., None], e[..., :3] * foyer, e[..., :3])
    e[..., :3] = np.where(chaud_clair[..., None], np.maximum(e[..., :3], add), e[..., :3])
    e[..., :3] = np.minimum(e[..., :3], 225)
    e[..., 3] = np.where((e[..., :3].max(axis=2) > 0) & (a > 0), 255, np.where(a > 0, e[..., 3], 0))
    e = e.astype(np.uint8)
    if te is None:
        te = {"name": os.path.splitext(main["name"])[0] + "_e.png", "uv_width": main.get("uv_width"), "uv_height": main.get("uv_height")}
        texs.insert(1, te)
    te["source"] = _b64(e)
    Image.fromarray(e, "RGBA").save(te["name"], optimize=True)

    # --- groupes de contrôle dans chaque groupe de premier niveau
    ctrl = []
    for n in model["outliner"]:
        if not isinstance(n, dict) or n.get("name", "").startswith("particle_"):
            continue
        for nom in ("ctrl_teinte", "ctrl_lumiere"):
            g = {"name": nom, "origin": list(n.get("origin", [0, 0, 0])), "uuid": str(uuid.uuid4()), "children": []}
            n.setdefault("children", []).append(g)
            ctrl.append(g)

    def cle(x, y, z):
        return {"channel": "position", "data_points": [{"x": x, "y": y, "z": z}], "time": 0, "interpolation": "linear"}

    A = {}
    for g in ctrl:
        if g["name"] == "ctrl_teinte":
            k = cle(*(f"{PLUIE}; {-v:g} * v.pluie" for v in mouille))
        else:
            k = cle(f"{PLUIE}; {lumiere:g} + {nuit:g} * {NUIT} + {pluie_lumiere:g} * v.pluie", "0", "0")
        A[g["uuid"]] = {"name": g["name"], "type": "bone", "keyframes": [k]}
    model["animations"].append({"uuid": str(uuid.uuid4()), "name": "overlay_ambiance", "loop": "loop", "override": False,
                                "length": 1.0, "snapping": 24, "selected": False, "animators": A})
    assert len(model["animations"]) <= 32, "32 animations au plus (guide 7, 2026-11-06 soir)"
