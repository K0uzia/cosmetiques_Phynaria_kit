#!/usr/bin/env python3
"""Exporte les livrables sous leur nom propre : livrables/<Ensemble>/<Nom propre>.bbmodel.
Usage : python tools/exporter.py                          toutes les pièces (et retire les anciens exports orphelins)
        python tools/exporter.py cosmetiques/<categorie>/<nom>   une seule pièce (appelé à la fin de tools/livrer.py)

Le nom propre vient de <dossier>/fiche.json (« nom »), le nom d'ensemble de cosmetiques/ensembles.json (« nom ») ;
l'ensemble est le champ « ensemble » de fiche.json s'il existe, sinon il se déduit du nom du dossier (gen_index.ensemble_de).
Seul le champ « name » du modèle change : le reste est identique au livrable vérifié (contrôlé après écriture).
Les modèles associés <nom>_<piece>.bbmodel suivent : « <Nom propre> (<piece>).bbmodel », ou le nom donné par
« pieces » dans fiche.json ({"plume": "Plume de Bérénice"}). Les pièces refusées (cosmetiques/statuts.json) ne sont pas exportées.
Bibliothèque standard seule."""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COS = os.path.join(ROOT, "cosmetiques")
SORTIE = os.path.join(ROOT, "livrables")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_index import ensemble_de, statut_de  # noqa: E402

INTERDITS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def nom_fichier(texte):
    """Nom lisible et valide sous Windows : accents et espaces gardés, caractères interdits retirés."""
    t = INTERDITS.sub("", texte).strip().rstrip(". ")
    if not t or t.upper() in RESERVES:
        raise ValueError(f"nom de fichier invalide : {texte!r}")
    return t


def lire_json(chemin, defaut=None):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return defaut


def dossier_ensemble(nom):
    ens = ensemble_de(nom)
    infos = (lire_json(os.path.join(COS, "ensembles.json"), {}) or {}).get(ens, {})
    return nom_fichier(infos.get("nom") or ens)


def copier_renomme(source, cible, nouveau_nom):
    """Écrit `cible` = `source` avec seulement le champ racine « name » changé, au même format que l'optimiseur
    (JSON compact, ASCII échappé). Vérifie ensuite que le reste est identique."""
    with open(source, encoding="utf-8") as f:
        brut = f.read()
    m = json.loads(brut)
    compact = lambda d: json.dumps(d, separators=(",", ":"))
    if compact(m) != brut:
        print(f"  note : {os.path.basename(source)} n'est pas au format compact de l'optimiseur, réécrit au même contenu")
    m["name"] = nouveau_nom
    os.makedirs(os.path.dirname(cible), exist_ok=True)
    tmp = cible + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(compact(m))
    # Contrôle : relu, seul « name » diffère du livrable vérifié.
    with open(tmp, encoding="utf-8") as f:
        relu = json.load(f)
    orig = json.loads(brut)
    if relu.get("name") != nouveau_nom or {k: v for k, v in relu.items() if k != "name"} != {k: v for k, v in orig.items() if k != "name"}:
        os.remove(tmp)
        sys.exit(f"ÉCHEC de l'export : {cible} diffère du livrable au-delà du nom.")
    os.replace(tmp, cible)


def cibles_piece(dossier):
    """[(source, cible, nom dans le modèle)] des exports d'une pièce, sans rien écrire ; [] si elle n'est pas exportée."""
    dossier = os.path.abspath(dossier)
    nom = os.path.basename(dossier)
    modele = os.path.join(dossier, nom + ".bbmodel")
    if not os.path.isfile(modele) or statut_de(nom)[0] == "refuse":
        return []
    fiche = lire_json(os.path.join(dossier, "fiche.json"), {}) or {}
    propre = fiche.get("nom") or nom
    base = os.path.join(SORTIE, dossier_ensemble(nom))
    out = [(modele, os.path.join(base, nom_fichier(propre) + ".bbmodel"), propre)]
    noms_pieces = fiche.get("pieces", {})
    for f in sorted(os.listdir(dossier)):
        if f.startswith(nom + "_") and f.endswith(".bbmodel"):
            piece = f[len(nom) + 1:-len(".bbmodel")]
            titre = noms_pieces.get(piece) or f"{propre} ({piece.replace('_', ' ')})"
            out.append((os.path.join(dossier, f), os.path.join(base, nom_fichier(titre) + ".bbmodel"), titre))
    return out


def exporter_piece(dossier):
    """Exporte une pièce ; renvoie la liste des fichiers écrits (vide si la pièce n'est pas exportée)."""
    dossier = os.path.abspath(dossier)
    nom = os.path.basename(dossier)
    if not os.path.isfile(os.path.join(dossier, nom + ".bbmodel")):
        return []
    if statut_de(nom)[0] == "refuse":
        print(f"  {nom} : refusé, non exporté")
        return []
    if not (lire_json(os.path.join(dossier, "fiche.json"), {}) or {}).get("nom"):
        print(f"  {nom} : pas de fiche.json avec « nom », exporté sous son nom interne")
    ecrits = []
    for source, cible, titre in cibles_piece(dossier):
        copier_renomme(source, cible, titre)
        ecrits.append(cible)
    for c in ecrits:
        print(f"  {os.path.relpath(c, ROOT)}")
    return ecrits


def exporter_tout():
    ecrits = set()
    for categorie in sorted(os.listdir(COS)):
        base = os.path.join(COS, categorie)
        if os.path.isdir(base):
            for nom in sorted(os.listdir(base)):
                ecrits.update(os.path.normcase(p) for p in exporter_piece(os.path.join(base, nom)))
    # Anciens exports (pièce renommée, retirée ou refusée) : supprimés.
    for racine, dossiers, fichiers in os.walk(SORTIE, topdown=False):
        for f in fichiers:
            p = os.path.join(racine, f)
            if f.endswith(".bbmodel") and os.path.normcase(p) not in ecrits:
                os.remove(p)
                print(f"  retiré : {os.path.relpath(p, ROOT)}")
        if racine != SORTIE and not os.listdir(racine):
            os.rmdir(racine)
    return ecrits


if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.exit(__doc__)
    n = len(exporter_piece(sys.argv[1])) if len(sys.argv) == 2 else len(exporter_tout())
    print(f"Export : {n} fichier(s) dans {os.path.relpath(SORTIE, ROOT)}{os.sep}")
