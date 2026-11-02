#!/usr/bin/env python3
"""Génère index.html, le « Vestiaire » : catalogue des cosmétiques, à partir de tools/catalogue_modele.html.
Usage : python tools/gen_index.py
La mise à jour automatique passe par tools/serve_vestiaire.py, qui relit le dossier en continu. Bibliothèque standard seule."""
import json, os, sys, zlib
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COS = os.path.join(ROOT, "cosmetiques")
MODELE = os.path.join(ROOT, "tools", "catalogue_modele.html")
LABELS = {"ailes": "Ailes", "chapeaux": "Tête", "queues": "Queues", "epaules": "Épaules", "armes": "Armes", "auras": "Auras",
          "familiers": "Familiers", "sacs": "Sacs", "outils": "Outils", "blocs": "Blocs"}
ETATS = ["idle", "walk", "run", "sneak", "fly", "glide", "fall", "swim", "mount", "sleep", "attack", "hurt"]
# Ensemble déduit du nom ; les exceptions se déclarent ici. Une nouvelle pièce « ..._abyssal... » se range donc toute seule.
EXCEPTIONS = {"familier_crane": "Abyssal", "aurelion_wings": "Céleste"}
MOTS = [("abyssal", "Abyssal"), ("celeste", "Céleste"), ("givre", "Givre"), ("mecanique", "Mécanique")]
TEINTES = {"Abyssal": "#9fe04e", "Céleste": "#e6c675", "Givre": "#7fd3ef", "Mécanique": "#d69a62", "Autres": "#b9a7e8"}
_cache = {}


def ensemble_de(nom):
    if nom in EXCEPTIONS:
        return EXCEPTIONS[nom]
    return next((e for mot, e in MOTS if mot in nom), "Autres")


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

    infos = {
        "cubes": len(m.get("elements", [])),
        "groupes": sum(groupes(n) for n in m.get("outliner", [])),
        "anims": [a["name"].split(".")[-1] for a in m.get("animations", [])],
        "lueur": any(os.path.splitext(t.get("name", ""))[0].endswith("_e") for t in m.get("textures", [])),
        "ko_compresse": len(zlib.compress(brut, 6)) // 1024,
    }
    _cache[cle] = infos
    return infos


def fiche(categorie, nom, modele, dossier):
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

    etats = [a for a in i["anims"] if not a.startswith("particle_")]
    gif = fichier("apercu", "animations.gif")
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
        "nom": nom, "categorie": categorie, "ensemble": ensemble_de(nom),
        "bbmodel": url(modele), "fichier": os.path.basename(modele),
        "gif": gif, "planche": fichier("apercu", "planche.png"), "nuit": fichier("apercu", "nuit.png"),
        "texture": fichier(nom + ".png"), "calque": fichier(nom + "_e.png"),
        "lueur": i["lueur"], "cubes": i["cubes"], "groupes": i["groupes"], "etats": etats, "apercu_etats": apercu_etats,
        "particules": sorted({a.split("_")[1] for a in i["anims"] if a.startswith("particle_") and a.count("_") >= 2}),
        "ko_compresse": i["ko_compresse"], "ko": os.path.getsize(modele) // 1024,
    }
    d["version"] = int(max(dates))
    return d


def collecter():
    fiches = []
    for categorie in sorted(os.listdir(COS)):
        base = os.path.join(COS, categorie)
        if not os.path.isdir(base):
            continue
        for entree in sorted(os.listdir(base)):
            chemin = os.path.join(base, entree)
            modele = os.path.join(chemin, entree + ".bbmodel")
            try:
                if os.path.isdir(chemin) and os.path.isfile(modele):
                    fiches.append(fiche(categorie, entree, modele, chemin))
                elif entree.endswith(".bbmodel"):
                    fiches.append(fiche(categorie, entree[:-8], chemin, None))
            except (ValueError, KeyError, OSError) as e:
                # Fichier en cours d'écriture ou invalide : on le reprend au prochain passage.
                print(f"ignoré : {entree} ({e})", file=sys.stderr)
    return fiches


def donnees():
    fiches = collecter()
    signature = "|".join(f"{f['nom']}:{f['version']}" for f in fiches)
    return {"fiches": fiches, "labels": LABELS, "teintes": TEINTES, "signature": signature}


def ecrire_index(d=None):
    d = d or donnees()
    with open(MODELE, encoding="utf-8") as f:
        page = f.read()
    page = page.replace("/*DONNEES*/", json.dumps(d, ensure_ascii=False).replace("</", "<\\/"))
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    return d


if __name__ == "__main__":
    d = ecrire_index()
    print(f"index.html : {len(d['fiches'])} cosmétiques")
    for x in d["fiches"]:
        print(f"  {x['ensemble']} / {x['categorie']} / {x['nom']} : {x['cubes']} cubes, aperçus={'oui' if x['gif'] else 'non'}")
