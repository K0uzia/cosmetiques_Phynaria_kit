"""Retire d'un modèle les particules qui tombent et se posent, réservées aux ailes (.claude/rules/essentiel.md, Méthode de travail).
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
        # chute / montée : lente rotation sur elle-même, et la bouffée qui s'étale ; sans place (32 animations), la particule
        # n'a pas d'animation et se balance toute seule (guide 5 ter §3)
        if len(model["animations"]) >= 15:       # une place gardée pour overlay_ambiance (tools/ambiance.py)
            continue
        L = 2.0
        cles = [{"channel": "rotation", "data_points": [{"x": "0", "y": str(round(360 * t / L, 1)), "z": "0"}], "time": t, "interpolation": "linear"} for t in (0, L / 2, L)]
        cles += [{"channel": "scale", "data_points": [{"x": "math.lerp(0.7, 1.5, math.mod(q.anim_time, 2) / 2)", "y": "1", "z": "math.lerp(0.7, 1.5, math.mod(q.anim_time, 2) / 2)"}],
                  "time": 0, "interpolation": "linear"}]
        model["animations"].append({"uuid": str(uuid.uuid4()), "name": f"particle_{sorte}_fall", "loop": "loop", "override": False, "length": L,
                                    "snapping": 24, "selected": False, "animators": {gid: {"name": f"particle_{sorte}", "type": "bone", "keyframes": cles}}})
    assert len(model["animations"]) <= 32, "32 animations au plus (guide 7, 2026-11-06 soir)"
    b = io.BytesIO()
    Image.fromarray(img, "RGBA").save(b, "PNG", optimize=True)
    tex0["source"] = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
    Image.fromarray(img, "RGBA").save(tex0["name"], optimize=True)


# ---------------------------------------------------------------- réglages des particules embarqués dans le modèle
# Lus par le mod depuis le 2026-11-05 (demandes 4, guide 5 ter §6) : ils pré-remplissent les fenêtres du staff à l'import.
# Format exact du guide : identifiants en minuscules sans accent ; nombre et durée ramenés au pas le plus proche.
# Les réglages sont écrits dans `unhandled_root_fields.phynaria` (même bloc que fiche et familier, tools/fiche.py) : Blockbench
# garde ce champ à l'ouverture et à l'enregistrement d'un .bbmodel (propriété `unhandled_root_fields` de ModelProject,
# js/io/project.ts), alors qu'une clé inconnue à la racine ou dans `meta` est perdue (compile() de js/formats/bbmodel.js).
#     notes = embarquer_reglages(model, "cosmetiques/ailes/ailes_berenice/reglages.json")
#     embarquer_fichier(".build/x_opt.bbmodel", dossier)   # livrer.py : réécrit le fichier si reglages.json existe
# Clés : <sorte> pour particle_<sorte> (points emit_<sorte>, emit_<sorte>2…), mc_<id> pour emit_mc_<id>.
import re as _re
import unicodedata as _ud

FORMAT_VERSION = 1
# clé : (libellé du guide, {identifiant: libellé}, défaut, demandé aussi pour une particule Minecraft)
CHOIX = {
    "quand": ("Quand", {"vol": "En vol", "air": "En l'air", "mouvement": "En mouvement", "arret": "À l'arrêt", "toujours": "Toujours",
                        "pluie": "Sous la pluie", "utilisation": "À l'utilisation", "jamais": "Jamais"}, "vol", True),
    "mouvement": ("Mouvement", {"legere": "Légère", "normale": "Normale", "lourde": "Lourde", "flotte": "Flotte", "monte": "Monte"}, "legere", False),
    "au_sol": ("Au sol", {"pose": "Se pose", "disparait": "Disparaît"}, "pose", False),
    "rendu": ("Rendu", {"opaque": "Opaque", "lumineux": "Lumineux", "translucide": "Translucide"}, "opaque", False),
    "sens": ("Sens", {"libre": "Libre", "camera": "Face caméra"}, "libre", False),
    "fin_de_vie": ("Fin de vie", {"retrecit": "Rétrécit", "fondu": "Fondu"}, "retrecit", False),
    "depart": ("Départ", {"poussee": "Poussée", "lent": "Lent", "moyen": "Moyen", "rapide": "Rapide"}, "poussee", True),
    "variation": ("Variation", {"aucune": "Aucune", "legere": "Légère", "forte": "Forte"}, "legere", False),
    "rafale": ("Rafale", {"aucune": "Aucune", "attaque": "À l'attaque", "blesse": "Blessé", "saut": "Au saut", "atterrissage": "À l'atterrissage",
                          "tir": "Au tir"},
               "aucune", True),
}
# clé : (libellé, valeurs permises (intervalle (min, max) ou liste), défaut, demandé aussi pour une particule Minecraft)
NOMBRES = {
    "nombre": ("Nombre", [0.5, 1, 2, 4, 6, 10], 2, True),       # par seconde (pas du guide 5 ter §6)
    "duree": ("Durée", [1, 3, 6, 10, 15, 20], 6, False),        # secondes
    "dispersion": ("Dispersion", [0, 15, 45, 180], 15, True),   # degrés
    "elan": ("Élan", [0, 40, 100], 40, False),                  # pour cent
    "limite": ("Limite", [64, 128, 256], 64, True),             # particules par joueur
}
ORDRE = ["quand", "nombre", "duree", "mouvement", "au_sol", "rendu", "sens", "fin_de_vie", "depart", "dispersion", "elan", "variation",
         "rafale", "limite"]
MINECRAFT = [k for k in ORDRE if (CHOIX.get(k) or NOMBRES.get(k))[3]]


def _norm(s):
    s = _ud.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return _re.sub(r"[^a-z0-9]+", " ", s).strip()


def _cle_libelle(lib):
    n = _norm(lib)
    for k, d in list(CHOIX.items()) + list(NOMBRES.items()):
        if _norm(d[0]) == n or n == k:
            return k
    return None


def _convertir(cle, texte, notes, ou):
    """Libellé français de reglages.json → identifiant ou nombre ; valeur hors des choix = la plus proche, avec une note."""
    if cle in CHOIX:
        valeurs = CHOIX[cle][1]
        n = _norm(texte)
        for ident, lib in valeurs.items():
            if n == _norm(lib) or n.startswith(_norm(lib) + " ") or n == ident:
                if n not in (_norm(lib), ident):
                    notes.append(f"{ou} : « {texte} » lu comme {ident}")
                return ident
        notes.append(f"{ou} : « {texte} » inconnu, défaut {CHOIX[cle][2]}")
        return CHOIX[cle][2]
    lib, permis, defaut, _ = NOMBRES[cle]
    if isinstance(texte, (int, float)):
        nb = [float(texte)]
    else:
        nb = [float(x.replace(",", ".")) for x in _re.findall(r"\d+(?:[.,]\d+)?", str(texte))]
    if not nb:
        notes.append(f"{ou} : « {texte} » sans nombre, défaut {defaut}")
        return defaut
    v = sum(nb) / len(nb)               # « 2 à 3 par seconde » → 2,5
    if isinstance(permis, tuple):
        w = min(max(v, permis[0]), permis[1])
    else:
        w = min(permis, key=lambda p: abs(p - v))
    w = int(w) if float(w).is_integer() else round(w, 2)
    if len(nb) > 1 or abs(w - v) > 1e-9:
        notes.append(f"{ou} : « {texte} » ramené à {w}")
    return w


def sortes(model):
    """Sortes de particules du modèle : {'plume': 'modelisee', 'mc_white_smoke': 'minecraft'} (guide 5 ter)."""
    out = {}

    def w(n):
        if not isinstance(n, dict):
            return
        nom = n.get("name", "")
        if nom.startswith("particle_"):
            out[nom[len("particle_"):]] = "modelisee"
        elif nom.startswith("emit_mc_"):
            out[nom[len("emit_"):]] = "minecraft"
        for c in n.get("children", []):
            w(c)
    for n in model.get("outliner", []):
        w(n)
    return out


def _est_mc(entree):
    return "minecraft" in _norm(entree.get("particule", "")) or str(entree.get("groupe", "")).startswith(("mc_", "emit_mc_"))


def _sorte_de(entree, presentes, prises):
    """Sorte du modèle décrite par une entrée de reglages.json : champ facultatif « groupe » (particle_x, emit_x, emit_mc_y),
    puis premier mot de « particule », puis un emit_<nom> cité dans le texte."""
    g = entree.get("groupe")
    if g:
        g = g[len("emit_"):] if g.startswith("emit_") else g[len("particle_"):] if g.startswith("particle_") else g
        g = g if g.startswith("mc_") else g.rstrip("0123456789").rstrip("_")
        return g if g in presentes else None
    texte = entree.get("particule", "")
    mot = _norm(texte.split("(")[0]).replace(" ", "_")
    if _est_mc(entree) and "mc_" + mot in presentes:
        return "mc_" + mot
    if mot in presentes and not _est_mc(entree):
        return mot
    for m in _re.findall(r"emit_(\w+)", texte + " " + entree.get("role", "")):
        k = m if m.startswith("mc_") else m.rstrip("0123456789").rstrip("_")
        if k in presentes and k not in prises:
            return k
    return None


def embarquer_reglages(model, chemin_json):
    """Écrit model["unhandled_root_fields"]["phynaria"] = {"version": 1, "particules": {sorte: {réglages}}} d'après reglages.json.
    Retourne les notes (conversions, entrées sans sorte). Une sorte du modèle sans entrée n'est pas inventée : le vérificateur
    la signale."""
    import json
    with open(chemin_json, encoding="utf-8") as f:
        entrees = json.load(f).get("particules", [])
    presentes, notes, choisies, restes = sortes(model), [], {}, []
    for e in entrees:
        k = _sorte_de(e, presentes, choisies)
        if k is None or k in choisies:
            restes.append(e)
        else:
            choisies[k] = e
    # une seule entrée et une seule sorte de même nature restées sans partenaire (ex. « flocon » pour particle_givre)
    for mc in (False, True):
        r = [e for e in restes if _est_mc(e) == mc]
        libres = [k for k in presentes if k not in choisies and (presentes[k] == "minecraft") == mc]
        if len(r) == 1 and len(libres) == 1:
            choisies[libres[0]] = r[0]
            restes.remove(r[0])
            notes.append(f"« {r[0].get('particule')} » attribué à la seule sorte restante : {libres[0]}")
    for e in restes:
        notes.append(f"« {e.get('particule')} » : aucune sorte de particule du modèle ne correspond, ignorée")
    particules = {}
    for k in sorted(choisies):
        e = choisies[k]
        cles = MINECRAFT if presentes[k] == "minecraft" else ORDRE
        r = {}
        for lib, texte in e.get("reglages", {}).items():
            c = _cle_libelle(lib)
            if c is None:
                notes.append(f"{k} : réglage « {lib} » inconnu, ignoré")
            elif c in cles:
                r[c] = _convertir(c, texte, notes, f"{k}.{c}")
        for c in cles:                       # réglage absent = défaut du guide, écrit pour être explicite
            r.setdefault(c, CHOIX[c][2] if c in CHOIX else NOMBRES[c][2])
        particules[k] = {c: r[c] for c in cles}
    racine = model.setdefault("unhandled_root_fields", {})
    b = racine.setdefault("phynaria", {})            # fusion : fiche, familier et objet restent (tools/fiche.py)
    b.setdefault("version", FORMAT_VERSION)
    b["particules"] = particules
    return notes


def embarquer_fichier(chemin_modele, dossier):
    """Embarque <dossier>/reglages.json dans un .bbmodel sur disque (JSON compact). None si la pièce n'a pas de reglages.json.
    livrer.py passe par tools/fiche.py (embarquer_fichier), qui embarque aussi la fiche."""
    import json, os
    rj = os.path.join(dossier, "reglages.json")
    if not os.path.isfile(rj):
        return None
    with open(chemin_modele, encoding="utf-8") as f:
        m = json.load(f)
    notes = embarquer_reglages(m, rj)
    with open(chemin_modele, "w", encoding="utf-8") as f:
        json.dump(m, f, separators=(",", ":"))
    return notes


def valider_reglages(model):
    """(erreurs, alertes) sur les réglages embarqués : format, une entrée par sorte présente, valeurs connues."""
    erreurs, alertes = [], []
    presentes = sortes(model)
    racine = model.get("unhandled_root_fields")
    d = racine.get("phynaria") if isinstance(racine, dict) else None
    p = d.get("particules") if isinstance(d, dict) else None
    if p is None:
        if presentes:
            alertes.append(f"particules sans réglages embarqués ({', '.join(sorted(presentes))}) : écrire reglages.json à côté du générateur")
        return erreurs, alertes
    if d.get("version") != FORMAT_VERSION or not isinstance(p, dict):
        return [f"format attendu {{'version': {FORMAT_VERSION}, 'particules': {{…}}}}"], alertes
    for k in sorted(set(presentes) - set(p)):
        erreurs.append(f"{k} : sorte présente sans réglages")
    for k in sorted(set(p) - set(presentes)):
        erreurs.append(f"{k} : réglages sans particle_/emit_mc_ correspondant")
    for k, r in p.items():
        if not isinstance(r, dict):
            erreurs.append(f"{k} : objet attendu")
            continue
        cles = MINECRAFT if presentes.get(k) == "minecraft" or k.startswith("mc_") else ORDRE
        for c, v in r.items():
            if c not in cles:
                erreurs.append(f"{k}.{c} : réglage inconnu" + (" pour une particule Minecraft" if c in ORDRE else ""))
            elif c in CHOIX and v not in CHOIX[c][1]:
                erreurs.append(f"{k}.{c} = {v!r} : attendu {'/'.join(CHOIX[c][1])}")
            elif c in NOMBRES:
                permis = NOMBRES[c][1]
                bon = isinstance(v, (int, float)) and not isinstance(v, bool) and (permis[0] <= v <= permis[1] if isinstance(permis, tuple) else v in permis)
                if not bon:
                    erreurs.append(f"{k}.{c} = {v!r} : attendu {permis}")
    return erreurs, alertes
