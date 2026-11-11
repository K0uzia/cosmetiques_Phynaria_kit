#!/usr/bin/env python3
"""Génère index.html, le « Vestiaire » : catalogue des cosmétiques, à partir de tools/catalogue_modele.html.
Usage : python tools/gen_index.py
La mise à jour automatique passe par tools/serve_vestiaire.py, qui relit le dossier en continu. Bibliothèque standard seule."""
import json, os, sys, threading, time, zlib
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prix as grille  # noqa: E402  (cosmetiques/prix.json : rareté, prix, jours de vote, euros, lots)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COS = os.path.join(ROOT, "cosmetiques")
MODELE = os.path.join(ROOT, "tools", "catalogue_modele.html")
VISIONNEUSE = os.path.join(ROOT, "tools", "visionneuse.js")
INDEX = os.path.join(ROOT, "index.html")
ENSEMBLES_JSON = os.path.join(COS, "ensembles.json")   # nom affiché, titre, thème, lore de chaque ensemble
LABELS = {"ailes": "Ailes", "chapeaux": "Tête", "queues": "Queues", "epaules": "Épaules", "armes": "Armes", "auras": "Auras",
          "familiers": "Familiers", "sacs": "Sacs", "outils": "Outils", "blocs": "Blocs", "objets": "Objets",   # objets : skins d'objets (guide 14)
          "effets": "Effets de téléportation"}   # effets : guide 15, posés au sol au départ et à l'arrivée
ETATS = ["idle", "walk", "run", "sneak", "fly", "glide", "fall", "swim", "mount", "sleep", "attack", "hurt"]
# Thème (large) > ensemble (set précis). Les ensembles (titre, thème, accroche, lore, couleur de l'onglet) sont dans
# cosmetiques/ensembles.json, modifiables depuis le Vestiaire (mode édition, tools/edition.py) ; l'ordre du fichier est l'ordre affiché.
# L'ensemble d'une pièce : champ « ensemble » de son fiche.json s'il existe, sinon déduit du nom (MOTS) : une nouvelle pièce
# « ..._abyssal... » se range toute seule. Les pièces se nomment <type>_<ensemble>[_<variante>] (2026-11-05) ;
# EXCEPTIONS reste pour un cas qui ne suit pas la règle.
THEMES = ["Démoniaque", "Divin", "Éléments", "Mignon", "Mécanique", "Fétiche", "Staff", "Cosmique"]   # ordre ; un thème nouveau d'ensembles.json s'ajoute à la fin
TEINTE_DEFAUT = "#b9a7e8"
EXCEPTIONS = {}
MOTS = [("abyssal", "Abyssal"), ("berenice", "Bérénice"), ("givre", "Givre"), ("orage", "Orage"), ("steampunk", "Steampunk"),
        ("kawaii", "Kawaii"), ("patisserie", "Pâtisserie"), ("tentacule", "Tentacule"), ("cuir", "Cuir"), ("brasier", "Brasier"), ("admin", "Admin"), ("stellaire", "Stellaire")]
# Retours en jeu (.claude/rules/retours-en-jeu.md), affichés en badge et filtrables dans le Vestiaire : cosmetiques/statuts.json
# ({"<nom>": {"statut": "valide" | "a_tester" | "refuse", "avis": "avis court"}}), modifiable depuis le Vestiaire.
# Une pièce absente est « à tester ». STATUTS ci-dessous : ancien emplacement, lu seulement pour une pièce absente du fichier.
STATUTS_JSON = os.path.join(COS, "statuts.json")
STATUTS_LIBELLES = {"valide": "Validé en jeu", "a_tester": "À tester", "refuse": "Refusé"}
STATUTS = {}
_cache = {}


def infos_ensembles():
    """cosmetiques/ensembles.json : {clé: {nom, titre, theme, accroche, lore, couleur, en_vente}}, dans l'ordre d'affichage."""
    d = lire_json(ENSEMBLES_JSON, {})
    return d if isinstance(d, dict) else {}


def themes():
    """Ordre des thèmes : THEMES, puis ceux d'ensembles.json qui n'y sont pas, dans l'ordre du fichier."""
    t = list(THEMES)
    for i in infos_ensembles().values():
        th = (i or {}).get("theme")
        if th and th not in t:
            t.append(th)
    return t


def cle_ensemble(texte, infos=None):
    """Clé d'ensembles.json pour une clé ou un nom affiché (majuscules ignorées) ; « Autres » pour aucun ; le texte s'il est inconnu."""
    t = str(texte or "").strip()
    if not t or t.lower() in ("autres", "aucun"):
        return "Autres"
    infos = infos_ensembles() if infos is None else infos
    if t in infos:
        return t
    for k, i in infos.items():
        if t.lower() in (k.lower(), str((i or {}).get("nom") or "").lower()):
            return k
    return t


def dossier_de(nom):
    """cosmetiques/<categorie>/<nom>/ s'il existe, sinon None."""
    try:
        for categorie in os.listdir(COS):
            d = os.path.join(COS, categorie, nom)
            if os.path.isdir(d):
                return d
    except OSError:
        pass
    return None


def ensemble_deduit(nom):
    """Ensemble déduit du seul nom du dossier (EXCEPTIONS, puis MOTS)."""
    if nom in EXCEPTIONS:
        return EXCEPTIONS[nom]
    return next((e for mot, e in MOTS if mot in nom), "Autres")


def ensemble_de(nom, dossier=None):
    """Champ « ensemble » de fiche.json s'il est rempli (prime), sinon déduit du nom."""
    d = dossier or dossier_de(nom)
    if d:
        e = (lire_json(os.path.join(d, "fiche.json"), {}) or {}).get("ensemble") if os.path.isfile(os.path.join(d, "fiche.json")) else None
        if isinstance(e, str) and e.strip():
            return cle_ensemble(e)
    return ensemble_deduit(nom)


def theme_de(ensemble, infos=None):
    i = (infos_ensembles() if infos is None else infos).get(ensemble)
    return (i or {}).get("theme") or "Autres"


def teintes(infos=None):
    infos = infos_ensembles() if infos is None else infos
    return {k: (i or {}).get("couleur") or TEINTE_DEFAUT for k, i in infos.items()} | {"Autres": TEINTE_DEFAUT}


def statuts():
    """{nom: (statut, avis)} : cosmetiques/statuts.json, complété par l'ancienne table STATUTS pour les pièces absentes."""
    d = lire_json(STATUTS_JSON, {})
    out = {k: (v.get("statut", "a_tester"), v.get("avis", "")) for k, v in (d if isinstance(d, dict) else {}).items() if isinstance(v, dict)}
    return {**STATUTS, **out}


def statut_de(nom, table=None):
    st, note = (statuts() if table is None else table).get(nom, ("a_tester", ""))
    return st if st in STATUTS_LIBELLES else "a_tester", note


def url(path):
    return quote(os.path.relpath(path, ROOT).replace(os.sep, "/"))


def lire_modele(modele):
    """Lecture coûteuse (zlib sur tout le fichier) : mise en cache tant que le fichier ne change pas."""
    cle = (modele, os.path.getmtime(modele), os.path.getsize(modele))
    if cle in _cache:
        return _cache[cle]
    with open(modele, "rb") as f:
        brut = f.read()
    m = json.loads(brut)

    def groupes(n):
        return 0 if isinstance(n, str) else 1 + sum(groupes(c) for c in n.get("children", []))

    phy = (m.get("unhandled_root_fields") or {}).get("phynaria") or {}
    fam = phy.get("familier") if isinstance(phy.get("familier"), dict) else {}
    obj = phy.get("objet") if isinstance(phy.get("objet"), dict) else {}
    import objet as _objet   # types et étapes des skins d'objets (guide 14)
    etapes = [e for e in _objet.ETAPES.get(obj.get("type"), ()) if e in {_objet.normal(n.get("name", "")) for n in m.get("outliner", []) if isinstance(n, dict)}]
    sons = set()
    for a in m.get("animations", []):
        for an in (a.get("animators") or {}).values():
            for k in an.get("keyframes", []):
                if k.get("channel") == "sound":
                    sons.update(d.get("effect") for d in k.get("data_points", []) if d.get("effect"))
    infos = {
        # familier vivant (guide 6.6) : mode, distance, vitesse, hauteur ; skin d'objet (guide 14) : type et étapes modelées
        "familier": {k: fam[k] for k in ("mode", "distance", "vitesse", "hauteur") if k in fam} if fam.get("mode") in ("sol", "vol", "nage", "perche") else None,
        "objet": {"type": obj["type"], "etapes": etapes} if obj.get("type") in _objet.ETAPES else None,
        "sons": sorted(sons), "sons_embarques": sorted((m.get("phynaria_sounds") or {}).keys()),
        # sortes de particules modélisées : groupes particle_<nom> à la racine (guide 5 ter), animés ou non
        "groupes_particules": [n["name"][9:] for n in m.get("outliner", []) if isinstance(n, dict) and str(n.get("name", "")).startswith("particle_")],
        "cubes": len(m.get("elements", [])),
        "groupes": sum(groupes(n) for n in m.get("outliner", [])),
        "anims": [a["name"].split(".")[-1] for a in m.get("animations", [])],
        "lueur": any(os.path.splitext(t.get("name", ""))[0].endswith("_e") for t in m.get("textures", [])),
        "ko_compresse": len(zlib.compress(brut, 6)) // 1024,
    }
    _cache[cle] = infos
    return infos


def lire_json(chemin, defaut):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defaut


def grille_prix():
    try:
        return grille.charger()
    except (OSError, ValueError):
        return None


def textes(categorie, dossier, cubes, g):
    """Nom propre, description, lore, rareté et prix : <dossier>/fiche.json, prix complétés par la grille (cosmetiques/prix.json)."""
    fj = lire_json(os.path.join(dossier, "fiche.json"), {}) if dossier else {}
    rarete, prix = fj.get("rarete"), fj.get("prix")
    if g and (not rarete or not prix):
        rarete = rarete or grille.rarete_auto(g, categorie, cubes)
        prix = prix or grille.prix_de(g, rarete)
    return {"titre": fj.get("nom") or "", "description": fj.get("description") or "", "lore": fj.get("lore") or "",
            "rarete": rarete or "", "prix": grille.detail(g, prix) if g and prix else None,
            "en_vente": fj.get("en_vente", True), "note_vente": fj.get("note_vente") or ""}


def telechargement(nom, modele, dossier):
    """Le bouton Télécharger donne la copie sous son nom propre (livrables/, tools/exporter.py) quand elle existe :
    le mod nomme le cosmétique d'après le fichier importé (« aura_brasier » sinon)."""
    if dossier:
        from exporter import dossier_ensemble, nom_fichier  # import tardif : exporter importe ce module
        propre = (lire_json(os.path.join(dossier, "fiche.json"), {}) or {}).get("nom")
        if propre:
            cible = os.path.join(ROOT, "livrables", dossier_ensemble(nom), nom_fichier(propre) + ".bbmodel")
            if os.path.isfile(cible) and os.path.getmtime(cible) >= os.path.getmtime(modele):
                return {"bbmodel": url(cible), "fichier": os.path.basename(cible)}
    return {"bbmodel": url(modele), "fichier": os.path.basename(modele)}


def fiche(categorie, nom, modele, dossier, g=None):
    i = lire_modele(modele)
    dates = [os.path.getmtime(modele)]

    def fichier(*chemin):
        if not dossier:
            return None
        p = os.path.join(dossier, *chemin)
        if os.path.isfile(p):
            dates.append(os.path.getmtime(p))
            return url(p)
        return None

    ens = ensemble_de(nom, dossier) if dossier else ensemble_deduit(nom)
    st = statut_de(nom)
    etats = [a for a in i["anims"] if not a.split(".")[-1].startswith(("particle_", "overlay_", "event_"))]
    gif = fichier("apercu", "animations.gif")
    # réglages à donner au staff pour les particules (fenêtre « une par sorte », guide 5 ter §5) : <dossier>/reglages.json
    fichier("fiche.json")   # sa date entre dans la version : modifier une fiche met à jour le Vestiaire
    reglages = []
    if dossier and fichier("reglages.json"):
        try:
            with open(os.path.join(dossier, "reglages.json"), encoding="utf-8") as fr:
                reglages = json.load(fr).get("particules", [])
        except (OSError, ValueError):
            reglages = []
    # Ordre des cases du GIF : apercu/etats.json s'il existe, sinon l'ordre standard des outils d'aperçu.
    apercu_etats = []
    if gif:
        chemin = os.path.join(dossier, "apercu", "etats.json")
        try:
            with open(chemin, encoding="utf-8") as f:
                apercu_etats = json.load(f)
        except (OSError, ValueError):
            apercu_etats = [e for e in ETATS if e in etats]
    d = {
        "nom": nom, "categorie": categorie, "ensemble": ens, "theme": theme_de(ens),
        **telechargement(nom, modele, dossier),
        "gif": gif, "planche": fichier("apercu", "planche.png"), "vignette": fichier("apercu", "vignette.png"),
        "anims_etat": {e: u for e in etats if (u := fichier("apercu", "etats", e + ".webp"))}, "nuit": fichier("apercu", "nuit.png"), "jeu": fichier("apercu", "jeu.png"),
        "texture": fichier(nom + ".png"), "calque": fichier(nom + "_e.png"),
        "lueur": i["lueur"], "reglages": reglages, "cubes": i["cubes"], "groupes": i["groupes"], "etats": etats, "apercu_etats": apercu_etats,
        "particules": sorted({a.split("_")[1] for a in i["anims"] if a.startswith("particle_") and a.count("_") >= 2} | set(i.get("groupes_particules", []))),
        "ko_compresse": i["ko_compresse"], "ko": os.path.getsize(modele) // 1024,
        "statut": st[0], "avis": st[1],
        "familier": i.get("familier"), "objet": i.get("objet"), "effet": categorie == "effets", "sons": i.get("sons", []), "sons_embarques": i.get("sons_embarques", []),
        "evenements": [a for a in i["anims"] if a.startswith("event_")], "couches": [a for a in i["anims"] if a.startswith("overlay_")],
    }
    d.update(textes(categorie, dossier, i["cubes"], g))
    d["version"] = int(max(dates))
    return d


def collecter():
    fiches, g = [], grille_prix()
    for categorie in sorted(os.listdir(COS)):
        base = os.path.join(COS, categorie)
        if not os.path.isdir(base):
            continue
        for entree in sorted(os.listdir(base)):
            chemin = os.path.join(base, entree)
            modele = os.path.join(chemin, entree + ".bbmodel")
            try:
                if os.path.isdir(chemin) and os.path.isfile(modele):
                    fiches.append(fiche(categorie, entree, modele, chemin, g))
                elif entree.endswith(".bbmodel"):
                    fiches.append(fiche(categorie, entree[:-8], chemin, None, g))
            except (ValueError, KeyError, OSError) as e:
                # Fichier en cours d'écriture ou invalide : on le reprend au prochain passage.
                print(f"ignoré : {entree} ({e})", file=sys.stderr)
    return fiches


def donnees():
    fiches = collecter()
    g = grille_prix()
    infos = infos_ensembles()
    ensembles = {}
    for e in {f["ensemble"] for f in fiches}:
        i = infos.get(e, {})
        en_vente = [f["prix"] for f in fiches if f["ensemble"] == e and f["en_vente"] and f["prix"]]
        lot = grille.lot(g, en_vente) if g and i.get("en_vente", True) else None
        ensembles[e] = {"nom": i.get("nom") or e, "titre": i.get("titre") or "", "accroche": i.get("accroche") or "",
                        "lore": i.get("lore") or "", "lot": lot}
    vente = {"statut": g["statut"], "rythme": grille.rythme(g),
             "raretes": {k: v["libelle"] for k, v in g["raretes"].items()}, "ordre_raretes": g["ordre_raretes"]} if g else None
    # Statuts, avis, ensembles et grille entrent dans la signature : les changer met à jour les pages ouvertes.
    signature = "|".join(f"{f['nom']}:{f['version']}:{f['statut']}:{f['ensemble']}" for f in fiches)         + f"|{zlib.crc32(json.dumps([infos, g, statuts()], ensure_ascii=False).encode())}"
    return {"fiches": fiches, "labels": LABELS, "teintes": teintes(infos), "themes": themes() + ["Autres"],
            "ordre_ensembles": list(infos) + ["Autres"], "statuts": STATUTS_LIBELLES, "signature": signature,
            "ensembles": ensembles, "vente": vente}


def page_index(d=None):
    """Texte de index.html, sans l'écrire (servi tel quel par tools/serve_vestiaire.py)."""
    d = d or donnees()
    with open(MODELE, encoding="utf-8") as f:
        page = f.read()
    with open(VISIONNEUSE, encoding="utf-8") as f:
        vis = f.read().replace("</", "<\\/")
    # Visionneuse d'abord : le texte des données (noms, réglages) ne peut pas contenir de marqueur interprété.
    page = page.replace("/*VISIONNEUSE*/", vis, 1)
    return page.replace("/*DONNEES*/", json.dumps(d, ensure_ascii=False).replace("</", "<\\/"), 1)


def ecrire_atomique(chemin, texte):
    """Écrit dans un fichier temporaire voisin puis le met en place d'un coup (os.replace) : deux livraisons
    simultanées, ou une page lue pendant l'écriture, ne voient jamais un fichier à moitié écrit.
    N'écrit rien si le contenu est déjà le bon. Sous Windows, un lecteur peut bloquer le remplacement
    un court instant : on réessaie. Renvoie True si le fichier a changé."""
    octets = texte.encode("utf-8")
    try:
        with open(chemin, "rb") as f:
            if f.read() == octets:
                return False
    except OSError:
        pass
    tmp = f"{chemin}.{os.getpid()}.{threading.get_ident()}.tmp"
    try:
        with open(tmp, "wb") as f:
            f.write(octets)
        for essai in range(40):
            try:
                os.replace(tmp, chemin)
                return True
            except PermissionError:
                time.sleep(0.05 + 0.01 * essai)
        os.replace(tmp, chemin)
        return True
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def ecrire_index(d=None):
    """Interface inchangée (appelée par tools/livrer.py et le serveur) : écrit index.html, renvoie les données."""
    d = d or donnees()
    ecrire_atomique(INDEX, page_index(d))
    return d


if __name__ == "__main__":
    d = ecrire_index()
    print(f"index.html : {len(d['fiches'])} cosmétiques")
    for x in d["fiches"]:
        print(f"  {x['theme']} / {x['ensemble']} / {x['categorie']} / {x['nom']} : {x['cubes']} cubes, aperçus={'oui' if x['gif'] else 'non'}")
