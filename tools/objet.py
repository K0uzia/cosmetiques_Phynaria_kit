"""Skins d'objets (guide, section 14) : modèle, réglages Display, étapes, matrices d'aperçu.

Un skin d'objet remplace l'apparence de tous les objets d'un type (épées, arbalètes…) tenus par le joueur qui le porte.
Recette et pièges : `.claude/rules/categories/objets.md`. Exemple : `cosmetiques/objets/skin_epee_givre/`.

    import objet
    aff = objet.affichage("epee", gui={"scale": [0.9, 0.9, 0.9]})        # préréglage vanilla du type, retouches par contexte
    model = objet.modele("skin_epee_givre", "epee", elements, outliner, textures, (512, 512), affichage=aff)
    objet.etape("bande_1")                                               # nom de groupe d'étape (contrôlé pour le type)

Lu dans le mod 1.4.0 (`phynariautilities-26.1.2-1.4.0.jar`, classes `JavaBlockConverter`, `ModelSettings`, `ItemSkins`,
`ItemSkinRenderer`, javap du 2026-11-05) :
- `phynaria.objet.affichage` (réglages Display au format de Blockbench) est lu **quel que soit le format** du fichier ; un
  fichier `java_block` y voit recopier son bloc racine `display` à l'import. Chaque contexte manquant : `_lefthand` prend
  `_righthand`, puis le défaut du mod (= `item/handheld` de Minecraft), puis `gui`. Translation bornée à ±80 px, échelle à ±4.
- `java_block` : textures fusionnées en une seule **à leur taille** (512 au plus), `_e` et `_r` gardés comme calques
  (guide 9, 2026-11-06 soir ; avant : réduites à 256² et `_e` sans lumière). Blockbench n'y enregistre pas d'animations.
  Coordonnées gardées telles quelles (bloc 0..16), origine par défaut (8, 8, 8).
- `free` (ou `modded_entity`) : lu tel quel dans le même espace (bloc 0..16), texture 512, `_e`, `trans_`, `add_` gardés.
  → **Format par défaut ici : `free` + `phynaria.objet.affichage`**, seul format qui porte des animations (objets vivants,
  guide 14 du 2026-11-06 soir : `item_idle`, `item_use`, `item_swing`, `item_ground`, `item_gui`, `event_swing`…,
  `overlay_`, particules, sons ; passer `animations=[...]` à modele()). `java_block` pour un objet figé qu'on veut retoucher
  dans le panneau Display de Blockbench.
Supposé (pas vu en jeu) : le dessin suit `ItemTransform` de Minecraft (main gauche : rotation Y et Z et translation X
inversées) ; d'où des réglages `_lefthand` toujours écrits en entier, copiés sur les fichiers vanilla.

Bibliothèque standard + numpy (matrices d'aperçu)."""
import copy, math, re, unicodedata

try:
    import numpy as np   # calcul des matrices (aperçus) ; absent : types et étapes restent lisibles (Vestiaire lancé par un autre Python)
except ImportError:
    np = None

# type -> étapes (groupes à la racine, guide 14) ; même table que tools/fiche.py
ETAPES = {
    "epee": ("repos",), "pioche": ("repos",), "hache": ("repos",), "pelle": ("repos",), "houe": ("repos",),
    "lance": ("repos", "leve", "lance"), "arc": ("repos", "bande_1", "bande_2", "bande_3"),
    "arbalete": ("repos", "bande_1", "bande_2", "bande_3", "chargee", "chargee_fusee"),
    "trident": ("repos", "leve", "lance"), "bouclier": ("repos", "bloque"), "masse": ("repos",), "canne": ("repos", "lancee"),
}
# contextes lus par le mod (ItemSkins.CONTEXTS)
CONTEXTES = ("thirdperson_righthand", "thirdperson_lefthand", "firstperson_righthand", "firstperson_lefthand",
             "gui", "head", "ground", "fixed", "on_shelf")


def _d(r=(0, 0, 0), t=(0, 0, 0), s=(1, 1, 1)):
    return {"rotation": list(r), "translation": list(t), "scale": list(s) if not isinstance(s, (int, float)) else [s] * 3}


# item/generated (sol, tête, cadre ; pas de gui = identité) : défauts du mod pour ces contextes
_GENERE = {"ground": _d(t=(0, 2, 0), s=0.5), "head": _d(r=(0, 180, 0), t=(0, 13, 7)), "fixed": _d(r=(0, 180, 0)), "gui": _d()}
# item/handheld : épée, outils (= défaut du mod en main)
_TENU = {"thirdperson_righthand": _d((0, -90, 55), (0, 4, 0.5), 0.85), "thirdperson_lefthand": _d((0, 90, -55), (0, 4, 0.5), 0.85),
         "firstperson_righthand": _d((0, -90, 25), (1.13, 3.2, 1.13), 0.68), "firstperson_lefthand": _d((0, 90, -25), (1.13, 3.2, 1.13), 0.68)}
# item/crossbow
_ARBALETE = {"thirdperson_righthand": _d((-90, 0, -60), (2, 0.1, -3), 0.9), "thirdperson_lefthand": _d((-90, 0, 30), (2, 0.1, -3), 0.9),
             "firstperson_righthand": _d((-90, 0, -55), (1.13, 3.2, 1.13), 0.68), "firstperson_lefthand": _d((-90, 0, 35), (1.13, 3.2, 1.13), 0.68)}
# item/bow
_ARC = {"thirdperson_righthand": _d((-80, 260, -40), (-1, -2, 2.5), 0.9), "thirdperson_lefthand": _d((-80, -280, 40), (-1, -2, 2.5), 0.9),
        "firstperson_righthand": _d((0, -90, 25), (1.13, 3.2, 1.13), 0.68), "firstperson_lefthand": _d((0, 90, -25), (1.13, 3.2, 1.13), 0.68)}
# item/handheld_rod (jar 26.1.2, relu le 2026-11-08 : 3e personne (0 ; 4 ; 2,5), l'ancienne valeur (0 ; 7 ; 1) était fausse)
_CANNE = {"thirdperson_righthand": _d((0, 90, 55), (0, 4, 2.5), 0.85), "thirdperson_lefthand": _d((0, -90, -55), (0, 4, 2.5), 0.85),
          "firstperson_righthand": _d((0, 90, 25), (0, 1.6, 0.8), 0.68), "firstperson_lefthand": _d((0, -90, -25), (0, 1.6, 0.8), 0.68)}
# item/handheld_mace (jar 26.1.2) : la masse n'a pas le Display de l'épée (relevé par skin_masse_orage et skin_masse_patisserie)
_MASSE = {"thirdperson_righthand": _d((0, -90, 55), (0, 4, 1), 1), "thirdperson_lefthand": _d((0, 90, -55), (0, 4, 1), 1),
          "firstperson_righthand": _d((0, -90, 25), (0, 3, 0.8), 0.9), "firstperson_lefthand": _d((0, 90, -25), (0, 3, 0.8), 0.9)}
# Lance (trident : préréglage _TRIDENT plus bas, tiré du jar) : objet modelé **pointe vers +Y**, centré dans son bloc (exigé pour le trident lancé, dessiné à sa taille sans
# Display). Point de départ calculé, pas vanilla (le trident de Minecraft est un modèle d'entité) : en main, rotation X de 90°
# = la pointe monte, poignée (centre du bloc) dans le poing. À régler sur l'aperçu (tools/apercu_objet.py).
_HAMPE = {"thirdperson_righthand": _d((90, 0, 0), (0, 0, -2), 1), "thirdperson_lefthand": _d((90, 0, 0), (0, 0, -2), 1),
          "firstperson_righthand": _d((10, -90, 0), (0, 0, -2), 0.8), "firstperson_lefthand": _d((10, 90, 0), (0, 0, -2), 0.8),
          "gui": _d((0, 0, -45), (0, 0, 0), 0.5), "ground": _d(t=(0, 2, 0), s=0.4), "fixed": _d((0, 180, -45), s=0.5)}
# Trident : Display vanilla de `item/trident_in_hand` (jar 26.1.2) recalculé pour un skin. Minecraft dessine en main le modèle
# d'entité `TridentModel` (hampe 1 × 25 × 1, base 3 × 2, dents de 4 px : y de -4 à 27, pointes vers -Y) retourné par la
# transformation (1, -1, -1) de `items/trident.json`, dans le repère du bloc (x = z = 0, pointes à y = 4, talon à y = -27).
# Le skin, lui, est modelé pointe vers +Y, axe en x = z = 8, du talon `y_bas` à la pointe `y_haut` (31 px de long par défaut :
# même taille que le trident vanilla, centré dans le bloc, y de -7,5 à 23,5). Contrôlé : en 3e personne la hampe passe à
# 0,5 px du poing calculé pour l'épée (prise à 16,7 px du talon), trident couché pointe en avant comme le vanilla.
# Main gauche : retournement de ItemTransform (rotation Y, Z et translation X) défait puis refait. `gui`, `ground`, `fixed` :
# le jeu y dessine l'image plate `item/trident` (pas le modèle) ; repris de la lance (diagonale, pointe en haut à droite).
_TRIDENT_VANILLA = {"thirdperson_righthand": ((0, 60, 0), (11, 17, -2)), "thirdperson_lefthand": ((0, 60, 0), (3, 17, 12)),
                    "firstperson_righthand": ((0, -90, 25), (-3, 17, 1)), "firstperson_lefthand": ((0, 90, -25), (13, 17, 1))}


def affichage_trident(y_bas=-7.5, y_haut=23.5, x=8.0, z=8.0):
    """Réglages Display des mains pour un trident modelé pointe vers +Y (axe en x, z ; talon y_bas, pointe y_haut), calculés
    depuis `item/trident_in_hand` : le skin occupe en main la place du trident vanilla (échelle = 31 px / sa longueur)."""
    k = 31.0 / (y_haut - y_bas)
    b = (x, y_bas, z)
    out = {}
    for ctx, (r, t) in _TRIDENT_VANILLA.items():
        gauche = ctx.endswith("_lefthand")
        r = [r[0], -r[1], -r[2]] if gauche else list(r)
        t = [-t[0], t[1], t[2]] if gauche else list(t)
        R = _rxyz(r)[:3, :3]
        dv = [-k * b[0] - 8 + 8 * k, -k * b[1] - 27 - 8 + 8 * k, -k * b[2] - 8 + 8 * k]
        tp = [t[i] + sum(R[i][j] * dv[j] for j in range(3)) for i in range(3)]
        if gauche:
            r, tp = [r[0], -r[1], -r[2]], [-tp[0], tp[1], tp[2]]
        out[ctx] = _d([float(v) + 0.0 for v in r], [round(float(v), 3) + 0.0 for v in tp], round(k, 4))
    return out


# valeurs de affichage_trident() par défaut (écrites en dur : ce module se charge aussi sans numpy)
_TRIDENT = {"thirdperson_righthand": _d((0, 60, 0), (0.072, -2.5, 0.928), 1), "thirdperson_lefthand": _d((0, 60, 0), (0.072, -2.5, 1.072), 1),
            "firstperson_righthand": _d((0, -90, 25), (5.0, -4.054, 1.991), 1), "firstperson_lefthand": _d((0, 90, -25), (5.0, -4.054, 1.991), 1),
            "gui": _d((0, 0, -45), (0, 0, 0), 0.55), "ground": _d(t=(0, 2, 0), s=0.4), "fixed": _d((0, 180, -45), s=0.5)}
PREREGLAGES = {"epee": _TENU, "pioche": _TENU, "hache": _TENU, "pelle": _TENU, "houe": _TENU, "masse": _MASSE,
               "arbalete": _ARBALETE, "arc": _ARC, "canne": _CANNE, "lance": _HAMPE, "trident": _TRIDENT, "bouclier": {}}


def affichage(type_, **retouches):
    """Réglages Display complets (8 contextes) pour un type : vanilla du type, puis retouches par contexte
    (affichage("epee", gui={"scale": [0.9] * 3}) remplace seulement la clé donnée du contexte)."""
    if type_ not in ETAPES:
        raise ValueError(f"type d'objet inconnu : {type_!r} ({'/'.join(ETAPES)})")
    aff = copy.deepcopy(_GENERE)
    aff.update(copy.deepcopy(_TENU))
    aff.update(copy.deepcopy(PREREGLAGES[type_]))
    for ctx, d in retouches.items():
        if ctx not in CONTEXTES:
            raise ValueError(f"contexte Display inconnu : {ctx}")
        aff.setdefault(ctx, _d()).update(copy.deepcopy(d))
    return {c: aff[c] for c in CONTEXTES if c in aff}


def normal(nom):
    """Nom de groupe comme le lit le mod : majuscules, accents, espaces et tirets ignorés (« Bandé 1 » = bande_1)."""
    n = unicodedata.normalize("NFKD", str(nom)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[\s-]+", "_", n).strip("_")


def etapes_connues():
    return {e for v in ETAPES.values() for e in v}


def etape(nom, type_=None):
    """Nom d'un groupe d'étape (à la racine), contrôlé : erreur si ce n'est pas une étape (du type, s'il est donné)."""
    n = normal(nom)
    if n not in (ETAPES[type_] if type_ else etapes_connues()):
        raise ValueError(f"« {nom} » n'est pas une étape{' de ' + type_ if type_ else ''} : {ETAPES.get(type_, sorted(etapes_connues()))}")
    return n


def modele(nom, type_, elements, outliner, textures, resolution, affichage=None, format="free", animations=None):
    """Modèle .bbmodel d'un skin d'objet. Le bloc phynaria.objet porte le type et les réglages Display (affichage) ;
    en java_block, ils vont aussi dans le bloc racine `display` (panneau Display de Blockbench). animations : objet vivant
    (guide 14), format free seulement."""
    if format not in ("free", "java_block"):
        raise ValueError("format : free ou java_block")
    aff = affichage if affichage is not None else globals()["affichage"](type_)
    racine = [n for n in outliner if isinstance(n, dict)]
    for n in racine:
        if normal(n.get("name", "")) in etapes_connues():
            etape(n["name"], type_)
    m = {"meta": {"format_version": "4.10", "model_format": format, "box_uv": False}, "name": nom,
         "resolution": {"width": resolution[0], "height": resolution[1]}, "elements": elements, "outliner": outliner,
         "textures": textures, "animations": list(animations or []),
         "unhandled_root_fields": {"phynaria": {"version": 1, "objet": {"type": type_, "affichage": aff}}}}
    if format == "java_block":
        if animations:
            raise ValueError("objet animé : format free (Blockbench n'a pas d'animations en java_block)")
        m["display"] = copy.deepcopy(aff)
    return m


def type_de(model):
    o = ((model.get("unhandled_root_fields") or {}).get("phynaria") or {}).get("objet")
    return o.get("type") if isinstance(o, dict) and o.get("type") in ETAPES else None


def lire_affichage(model):
    """Réglages Display effectifs (contexte -> rotation, translation, scale) comme le mod : phynaria.objet.affichage, sinon
    `display` racine, puis repli _lefthand -> _righthand -> défaut du mod -> gui. Translation ±80, échelle ±4."""
    o = ((model.get("unhandled_root_fields") or {}).get("phynaria") or {}).get("objet") or {}
    lu = o.get("affichage") if isinstance(o.get("affichage"), dict) else model.get("display") or {}
    defaut = dict(_GENERE, thirdperson_righthand=_TENU["thirdperson_righthand"], firstperson_righthand=_TENU["firstperson_righthand"])
    out = {}
    for c in CONTEXTES:
        d = lu.get(c) or (lu.get(c.replace("_lefthand", "_righthand")) if c.endswith("_lefthand") else None) or defaut.get(c) \
            or defaut.get(c.replace("_lefthand", "_righthand")) or lu.get("gui") or defaut["gui"]
        out[c] = {"rotation": [float(v) for v in d.get("rotation", (0, 0, 0))],
                  "translation": [max(-80.0, min(80.0, float(v))) for v in d.get("translation", (0, 0, 0))],
                  "scale": [max(-4.0, min(4.0, float(v))) for v in d.get("scale", (1, 1, 1))]}
    return out


def valider_affichage(aff):
    """(erreurs, alertes) sur un bloc de réglages Display."""
    erreurs, alertes = [], []
    if not isinstance(aff, dict):
        return ["affichage : objet attendu {contexte: {rotation, translation, scale}}"], alertes
    for c, d in aff.items():
        if c not in CONTEXTES:
            alertes.append(f"affichage.{c} : contexte inconnu du mod (ignoré)")
            continue
        if not isinstance(d, dict):
            erreurs.append(f"affichage.{c} : objet attendu")
            continue
        for k in d:
            if k not in ("rotation", "translation", "scale"):
                alertes.append(f"affichage.{c}.{k} : clé inconnue (ignorée)")
        for k, lim in (("rotation", None), ("translation", 80), ("scale", 4)):
            v = d.get(k)
            if v is None:
                continue
            if not (isinstance(v, list) and len(v) == 3 and all(isinstance(x, (int, float)) for x in v)):
                erreurs.append(f"affichage.{c}.{k} : 3 nombres attendus")
            elif lim and any(abs(x) > lim for x in v):
                alertes.append(f"affichage.{c}.{k} = {v} : borné à ±{lim} par le mod")
    for c in ("thirdperson_righthand", "firstperson_righthand", "gui"):
        if c not in aff:
            alertes.append(f"affichage.{c} absent : défaut du mod (item/handheld, objet en diagonale pointe en haut à droite)")
    return erreurs, alertes


# ------------------------------------------------------------------------------------------------ matrices (aperçus)
# Affines 4×4 sur des colonnes. R() suit l'ordre Blockbench du renderer (Rz·Ry·Rx) ; Minecraft applique Display en
# rotationXYZ (Rx·Ry·Rz), d'où _rxyz().
def _T(x, y, z):
    M = np.eye(4)
    M[:3, 3] = (x, y, z)
    return M


def _S(x, y=None, z=None):
    return np.diag([x, x if y is None else y, x if z is None else z, 1.0])


def _R(axe, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    M = np.eye(4)
    i, j = {"x": (1, 2), "y": (2, 0), "z": (0, 1)}[axe]
    M[i, i], M[i, j], M[j, i], M[j, j] = c, -s, s, c
    return M


def _rxyz(r):
    return _R("x", r[0]) @ _R("y", r[1]) @ _R("z", r[2])


def matrice_display(d):
    """Objet (px du bloc 0..16) -> repère du contexte en blocs : Display de Minecraft (translate, rotationXYZ, scale)
    après le recentrage du bloc (-0,5)."""
    t = d["translation"]
    return _T(t[0] / 16, t[1] / 16, t[2] / 16) @ _rxyz(d["rotation"]) @ _S(*d["scale"]) @ _T(-0.5, -0.5, -0.5) @ _S(1 / 16)


def matrice_main(d):
    """Objet (px) -> repère du renderer (px, joueur debout, face -Z, droite +X), tenu en main droite à la 3e personne, bras
    droit au repos le long du corps (pivot 5, 22, 0). ItemInHandLayer : bras, Rx(-90), Ry(180), (1/16, 0,125, -0,625), Display.
    Modèle du joueur (y vers le bas, bras droit à x = -5) -> renderer : (-x, 24 - y, z). Même calcul dans tools/visionneuse.js."""
    modele_vers_rendu = _T(0, 24, 0) @ _S(-1, -1, 1)
    return (modele_vers_rendu @ _T(-5, 2, 0) @ _S(16) @ _R("x", -90) @ _R("y", 180) @ _T(1 / 16, 0.125, -0.625) @ matrice_display(d))


# Arbalète en 1re personne (ItemInHandRenderer.renderArmWithItem, javap du jar 26.1.2 du 2026-11-05) : pendant le chargement,
# l'arme pivote vers le centre de l'écran et s'allonge ; chargée, elle se décale de 0,64 bloc vers le centre (visée).
# Taux de chargement supposé par étape (bande_1 < 0,58 ≤ bande_2 < 1 ≤ bande_3, prédicats vanilla) ; tremblement ignoré.
_CHARGE = {"bande_1": 0.3, "bande_2": 0.75, "bande_3": 1.0}


def matrice_premiere(d, etape=None, type_=None):
    """Objet (px) -> vue de la caméra (px, regard -Z), main droite à la 1re personne, sans balancement ni coup.
    Arbalète : `etape` (bande_*, chargee*) ajoute le geste de chargement ou la visée de Minecraft."""
    M = _S(16) @ _T(0.56, -0.52, -0.72)
    if type_ == "arbalete" and etape in _CHARGE:
        l = _CHARGE[etape]
        M = (M @ _T(-0.4785682, -0.094387, 0.05731531) @ _R("x", -11.935) @ _R("y", 65.3) @ _R("z", -9.785)
             @ _T(0, 0, 0.04 * l) @ _S(1, 1, 1 + 0.2 * l) @ _R("y", -45))
    elif type_ == "arbalete" and etape and etape.startswith("chargee"):
        M = M @ _T(-0.641864, 0, 0) @ _R("y", 10)
    return M @ matrice_display(d)


def matrice_gui(d):
    """Objet (px) -> case d'inventaire (px, case = -8..8 en x et y, +Y en haut, vue depuis +Z)."""
    return _S(16) @ matrice_display(d)


def appliquer(M, p):
    return (M @ np.append(np.asarray(p, float), 1.0))[:3]


def main_de_modele(model):
    """Matrice de la main droite 3e personne du modèle (None si ce n'est pas un skin d'objet) : render_bbmodel.load_model."""
    if type_de(model) is None:
        return None
    return matrice_main(lire_affichage(model)["thirdperson_righthand"])
