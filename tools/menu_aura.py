"""Menu Apparence des auras.

**Depuis le guide du 2026-11-06 (soir), demandes 5** : le mod tourne lui-même `cam_` et `camy_` vers la caméra dans l'aperçu
du menu, y compris quand le joueur fait tourner le personnage (guide 4 bis) ; « le contournement par query.is_in_menu n'est
plus utile ». ADAPTER_MENU = False : adapter_menu() ne fait plus que retirer les anciennes cachettes (`1-q.is_in_menu`, groupes
`menu_seul`) ; il n'enveloppe plus les `cam_` dans des `vm_` tournés, qui feraient une double rotation. Ne pas repasser à True.

Historique (mod 1.4.0, avant le correctif) :

Ce que fait le mod 1.4.0 dans l'aperçu du menu (rendu marqué id = -424242) :
- `add_` : dessiné avec le même pipeline additif qu'en jeu, sur une copie de la texture dont l'alpha vaut max(R, G, B)
  (texels sous 26 jetés) : plus de carré noir, la lueur s'ajoute (CosmeticMatcap.menuAdditive, CosmeticLayer.submit) ;
- `cam_` / `camy_` : pas de caméra, le groupe est dessiné tel qu'il est modélisé (CosmeticLayer.visit).
Nos plaques `cam_` sont reculées en z local négatif (côté opposé à la caméra une fois orientées) : sans orientation, elles
passeraient devant le personnage (−Z = devant).

Vue par défaut du menu (bytecode de AppearancePage$Preview, mod 1.4.0, 2026-11-05) : bodyRot = 180 + rotY avec rotY = 30
au départ, inclinaison rotateX(rotX) avec rotX = −5 au départ, tête alignée sur le corps (yRot = xRot = 0) ; glisser à la
souris : rotY −= dx/2,5, rotX −= dy/2,5 (borné à ±40). Soit une caméra devant-gauche du joueur, lacet 30°, vue de 5° au-dessus
(conforme à la capture 2026-11-05_20.36.18).

Méthode « camera » (défaut, 2026-11-05) : chaque groupe `cam_`/`camy_` le plus extérieur est enveloppé dans un groupe neutre
`vm_<nom>` (même pivot) qui, dans le menu seulement, tourne de (−tangage, lacet − 180, 0) × q.is_in_menu (`camy_` : lacet seul) :
le groupe est orienté face à la caméra du menu comme le mod l'orienterait en jeu, ses plaques reculées le long de l'axe de vue,
derrière le corps. L'enveloppe porte la rotation pour que les rotations propres du `cam_` (vrille z des overlay_) restent autour
de l'axe de vue. ECHELLE_MENU > 1 agrandit l'enveloppe dans le menu (1 = comme en jeu). En jeu, q.is_in_menu = 0 : rien ne change.
Limite : quand le joueur fait tourner le personnage à la souris, l'orientation ne suit pas (demande au mod :
docs/dev/demandes_mod_5.md §1).
Méthode « retourne » (ancienne, test a du 2026-11-05) : le `cam_` lui-même tourne de 180° en Y (`q.is_in_menu*180`).

adapter_menu(model, cacher=False) :
- cacher=True : ancien contournement gardé tel quel (groupes cachés par q.is_in_menu, `menu_seul` de remplacement) ;
- cacher=False : retire les cachettes (`1-q.is_in_menu` → 1, `*(1-q.is_in_menu)` → rien), supprime les groupes
  `menu_seul` et leurs cubes, puis oriente les groupes `cam_`/`camy_` pour le menu (méthode ci-dessus) dans les états
  (boucles hors overlay_). Les overlay_ et event_ se jouent par-dessus l'état (rotations ajoutées) : ils ne reçoivent pas
  la rotation, sinon elle compterait deux fois.
- methode="retourne" (ou METHODE_MENU) : ancien retournement de 180° ; lacet, tangage, echelle, recul : réglages de la méthode
  « camera ».
"""

import math
import uuid as _uuid

ETAT_EXCLUS = ("overlay_", "event_", "particle_")
ROT_MENU = "q.is_in_menu*180"     # méthode « retourne »
METHODE_MENU = "camera"           # "camera" : face à la caméra du menu ; "retourne" : ancien retournement de 180°
MENU_LACET = 30.0                 # caméra du menu : devant-gauche du joueur (rotY par défaut du mod)
MENU_TANGAGE = 5.0                # vue d'au-dessus, en degrés (rotX = −5 par défaut)
ECHELLE_MENU = 1.0                # agrandissement des groupes cam_ dans le menu (1 = comme en jeu)
PREFIXE = "vm_"
ADAPTER_MENU = False              # le mod oriente cam_/camy_ dans le menu (guide 2026-11-06 soir) : plus de vm_


def _fois_menu(v):
    """v × q.is_in_menu, sans double signe."""
    v = round(float(v), 4)
    if v == 0:
        return "0"
    t = f"{abs(v):g}"
    return f"q.is_in_menu*{t}" if v > 0 else f"-q.is_in_menu*{t}"


def rotation_menu(camy=False, lacet=None, tangage=None):
    """Rotation (x, y, z) en degrés qui oriente un groupe cam_ (z local + vers la caméra) face à la caméra du menu."""
    lacet = MENU_LACET if lacet is None else lacet
    tangage = MENU_TANGAGE if tangage is None else tangage
    return (0.0 if camy else -tangage, lacet - 180.0, 0.0)


def _retirer_cachettes(expr):
    if not isinstance(expr, str) or "is_in_menu" not in expr:
        return expr
    e = expr.replace("*(1-q.is_in_menu)", "").replace("(1-q.is_in_menu)*", "")
    if e.strip() == "1-q.is_in_menu":
        return "1"
    return e


def adapter_menu(model, cacher=False, methode=None, lacet=None, tangage=None, echelle=None, recul=None):
    """recul : {nom du groupe cam_: px} recul supplémentaire dans le menu, le long de l'axe de vue (en s'éloignant de la caméra),
    pour écarter deux plaques que la vue fixe du menu rend coplanaires (faces proches mesurées sur la copie de menu) ; clé "*" :
    valeur des autres groupes. Le menu est en vue orthographique : ce recul ne déplace rien à l'écran, il ne change que l'ordre
    de profondeur."""
    methode = methode or METHODE_MENU
    echelle = ECHELLE_MENU if echelle is None else echelle
    if cacher:
        return model
    # 1. groupes menu_seul supprimés (avec leurs cubes et leurs pistes)
    retires_g, retires_e = set(), set()

    def collecte(n):
        if isinstance(n, dict):
            retires_g.add(n["uuid"])
            for c in n.get("children", []):
                collecte(c)
        else:
            retires_e.add(n)

    def filtre(liste):
        out = []
        for n in liste:
            if isinstance(n, dict) and n["name"] == "menu_seul":
                collecte(n)
                continue
            if isinstance(n, dict):
                n["children"] = filtre(n.get("children", []))
            out.append(n)
        return out

    model["outliner"] = filtre(model["outliner"])
    model["elements"] = [e for e in model["elements"] if e["uuid"] not in retires_e]
    for an in model.get("animations", []):
        an["animators"] = {k: v for k, v in an.get("animators", {}).items() if k not in retires_g}

    # 2. cachettes retirées
    for an in model.get("animations", []):
        for k, a in list(an.get("animators", {}).items()):
            for kf in a.get("keyframes", []):
                for dp in kf.get("data_points", []):
                    for ax in ("x", "y", "z"):
                        if ax in dp:
                            dp[ax] = _retirer_cachettes(dp[ax])
            # piste d'échelle devenue neutre partout : retirée
            a["keyframes"] = [kf for kf in a.get("keyframes", []) if not (
                kf["channel"] == "scale" and all(str(dp.get(ax)) in ("1", "1.0") for dp in kf["data_points"] for ax in "xyz"))]
            if not a["keyframes"]:
                del an["animators"][k]

    if not ADAPTER_MENU:
        return model
    # 3. groupes cam_/camy_ les plus extérieurs, avec leur liste parente
    cams = []

    def cherche(n, liste, sous_cam=False):
        if not isinstance(n, dict):
            return
        est = n["name"].startswith(("cam_", "camy_"))
        if est and not sous_cam:
            cams.append((n, liste))
        for c in n.get("children", []):
            cherche(c, n["children"], sous_cam or est)

    for n in model["outliner"]:
        cherche(n, model["outliner"])
    etats = [an for an in model.get("animations", []) if an.get("loop") == "loop" and not an["name"].startswith(ETAT_EXCLUS)]

    if methode == "retourne":
        for an in etats:
            anims = an.setdefault("animators", {})
            for g, _ in cams:
                a = anims.setdefault(g["uuid"], {"name": g["name"], "type": "bone", "keyframes": []})
                rots = [kf for kf in a["keyframes"] if kf["channel"] == "rotation"]
                if rots:
                    for kf in rots:
                        for dp in kf["data_points"]:
                            dp["y"] = f"{dp.get('y', '0')}+{ROT_MENU}"
                else:
                    a["keyframes"].append({"channel": "rotation", "data_points": [{"x": "0", "y": ROT_MENU, "z": "0"}],
                                           "time": 0, "interpolation": "linear"})
        return model

    # méthode « camera » : enveloppe vm_<nom> tournée face à la caméra du menu
    pris = set()

    def tous(n):
        if isinstance(n, dict):
            pris.add(n["name"])
            for c in n.get("children", []):
                tous(c)

    for n in model["outliner"]:
        tous(n)
    enveloppes = []
    for g, liste in cams:
        base = PREFIXE + g["name"].split("_", 1)[1]
        nom, k = base, 2
        while nom in pris:
            nom, k = f"{base}{k}", k + 1
        pris.add(nom)
        env = {c: v for c, v in g.items() if c not in ("name", "uuid", "children", "rotation")}
        env.update({"name": nom, "uuid": str(_uuid.uuid4()), "origin": list(g.get("origin", [0, 0, 0])),
                    "rotation": [0, 0, 0], "children": [g]})
        liste[liste.index(g)] = env
        enveloppes.append((env, g["name"].startswith("camy_")))
    for an in etats:
        anims = an.setdefault("animators", {})
        for env, camy in enveloppes:
            rx, ry, rz = rotation_menu(camy, lacet, tangage)
            kfs = [{"channel": "rotation", "data_points": [{"x": _fois_menu(rx), "y": _fois_menu(ry), "z": _fois_menu(rz)}],
                    "time": 0, "interpolation": "linear"}]
            r = (recul or {}).get(env["children"][0]["name"], (recul or {}).get("*", 0))
            if r:
                la, ta = math.radians(MENU_LACET if lacet is None else lacet), math.radians(MENU_TANGAGE if tangage is None else tangage)
                v = (math.sin(la) * math.cos(ta) * r, -math.sin(ta) * r, math.cos(la) * math.cos(ta) * r)   # vers +X, −Y, +Z : loin de la caméra
                kfs.append({"channel": "position", "data_points": [{"x": _fois_menu(v[0]), "y": _fois_menu(v[1]), "z": _fois_menu(v[2])}],
                            "time": 0, "interpolation": "linear"})
            if abs(echelle - 1) > 1e-6:
                e = _fois_menu(echelle - 1)
                e = "1" + (e if e.startswith("-") else "+" + e)
                kfs.append({"channel": "scale", "data_points": [{"x": e, "y": e, "z": e}], "time": 0, "interpolation": "linear"})
            anims[env["uuid"]] = {"name": env["name"], "type": "bone", "keyframes": kfs}
    return model


def resume(model):
    """Expressions restantes qui citent is_in_menu (contrôle)."""
    reste = set()
    for an in model.get("animations", []):
        for a in an.get("animators", {}).values():
            for kf in a.get("keyframes", []):
                for dp in kf.get("data_points", []):
                    for ax in ("x", "y", "z"):
                        v = dp.get(ax)
                        if (isinstance(v, str) and "is_in_menu" in v and v != ROT_MENU and not v.endswith("+" + ROT_MENU)
                                and not a.get("name", "").startswith(PREFIXE)):
                            reste.add(v[:80])
    return reste
