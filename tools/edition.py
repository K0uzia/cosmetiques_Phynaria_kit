#!/usr/bin/env python3
"""Mode édition du Vestiaire (tools/serve_vestiaire.py, serveur local 127.0.0.1 seulement) : fiche d'une pièce, statut en jeu,
ensembles. Bibliothèque standard seule (le serveur tourne aussi avec un Python sans numpy).

Ce qu'écrit « Enregistrer » :
- pièce : cosmetiques/<cat>/<nom>/fiche.json (champs gérés seulement, les autres clés sont gardées), cosmetiques/statuts.json,
  puis la fiche réembarquée dans le livrable <nom>.bbmodel (tools/fiche.py, rien d'autre ne change), l'export
  livrables/<Ensemble>/<Nom>.bbmodel refait (tools/exporter.py) et l'ancien export retiré s'il a changé de nom ou d'ensemble ;
- ensemble : cosmetiques/ensembles.json ; un changement de nom affiché réembarque et réexporte les pièces de l'ensemble.
Chaque fichier modifié est d'abord copié en <fichier>.bak. Écritures limitées à cosmetiques/ et livrables/."""
import json, os, re, shutil, sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import gen_index  # noqa: E402
import prix as grille  # noqa: E402

ROOT = gen_index.ROOT
COS = gen_index.COS
LIVRABLES = os.path.join(ROOT, "livrables")
LIMITES = {"nom": 40, "description": 300, "lore": 500}           # guide 10 bis (rareté : liste de la grille)
LIMITES_ENS = {"nom": 40, "titre": 80, "theme": 40, "accroche": 300, "lore": 1000}
AVIS_MAX = 600
PRIX_MAX = 10_000_000
COULEUR = re.compile(r"^#[0-9a-fA-F]{6}$")


class Refus(ValueError):
    """Erreur montrée telle quelle à l'utilisateur."""


# ------------------------------------------------------------------------------------------------ fichiers
def _sous(chemin, *racines):
    c = os.path.normcase(os.path.realpath(chemin))
    return any(c == os.path.normcase(os.path.realpath(r)) or c.startswith(os.path.normcase(os.path.realpath(r)) + os.sep) for r in racines)


def _autorise(chemin):
    if not _sous(chemin, COS, LIVRABLES):
        raise Refus(f"écriture refusée hors de cosmetiques/ et livrables/ : {chemin}")


def sauvegarder(chemin):
    """Copie <fichier>.bak avant écriture (la précédente est remplacée)."""
    _autorise(chemin)
    if os.path.isfile(chemin):
        shutil.copy2(chemin, chemin + ".bak")


def ecrire_json(chemin, d):
    _autorise(chemin)
    sauvegarder(chemin)
    tmp = chemin + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, chemin)


def lire_json(chemin, defaut):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defaut


def _texte(v, cle, n, requis=False):
    if v is None:
        v = ""
    if not isinstance(v, str):
        raise Refus(f"{cle} : texte attendu")
    v = v.replace("\r\n", "\n").strip()
    if requis and not v:
        raise Refus(f"{cle} : obligatoire")
    if len(v) > n:
        raise Refus(f"{cle} : {len(v)} caractères, {n} au plus")
    return v


def _entier(v, cle):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != int(v) or not 0 <= v <= PRIX_MAX:
        raise Refus(f"{cle} : nombre entier entre 0 et {PRIX_MAX:,} attendu".replace(",", " "))
    return int(v)


# ------------------------------------------------------------------------------------------------ pièce
def dossier_piece(nom):
    if not isinstance(nom, str) or not re.fullmatch(r"[a-z0-9_]{1,80}", nom):
        raise Refus("nom de pièce invalide")
    d = gen_index.dossier_de(nom)
    if not d or not os.path.isfile(os.path.join(d, nom + ".bbmodel")):
        raise Refus(f"pièce introuvable : {nom}")
    return d


def proposition_grille(nom, dossier=None):
    """Rareté et prix que donnerait la grille (python tools/prix.py) pour cette pièce, et le prix de chaque rareté."""
    d = dossier or dossier_piece(nom)
    g = grille.charger()
    cubes = gen_index.lire_modele(os.path.join(d, nom + ".bbmodel"))["cubes"]
    r = grille.rarete_auto(g, os.path.basename(os.path.dirname(d)), cubes)
    return {"rarete": r, **grille.prix_de(g, r)}, {k: grille.prix_de(g, k) for k in g["ordre_raretes"]}, g


def raretes(g):
    """[(clé, libellé)] : raretés de la grille, puis celles du guide hors grille (mythique : prix manuel seulement)."""
    import fiche
    out = [[k, g["raretes"][k]["libelle"]] for k in g["ordre_raretes"]]
    return out + [[k, k.replace("_", " ").capitalize() + " (hors grille)"] for k in fiche.RARETES if k not in g["raretes"]]


def lire_piece(nom):
    d = dossier_piece(nom)
    fj = lire_json(os.path.join(d, "fiche.json"), {}) or {}
    auto, par_rarete, g = proposition_grille(nom, d)
    st, avis = gen_index.statut_de(nom)
    infos = gen_index.infos_ensembles()
    return {
        "nom": nom, "categorie": os.path.basename(os.path.dirname(d)),
        "fiche": {"nom": fj.get("nom") or "", "rarete": fj.get("rarete") or auto["rarete"],
                  "prix": fj.get("prix") or {"pv": auto["pv"], "phynarium": auto["phynarium"]},
                  "prix_manuel": bool(fj.get("prix_manuel")), "en_vente": fj.get("en_vente", True) is not False,
                  "description": fj.get("description") or "", "lore": fj.get("lore") or ""},
        "ensemble": gen_index.ensemble_de(nom, d), "ensemble_deduit": gen_index.ensemble_deduit(nom),
        "ensemble_force": bool(str(fj.get("ensemble") or "").strip()),
        "statut": st, "avis": avis, "grille": auto, "prix_par_rarete": par_rarete,
        "raretes": raretes(g),
        "ensembles": [[k, (i or {}).get("nom") or k] for k, i in infos.items()],
        "statuts": list(gen_index.STATUTS_LIBELLES.items()), "limites": {**LIMITES, "avis": AVIS_MAX},
    }


def reembarquer(dossier):
    """Fiche (et réglages) réembarquées dans le livrable et ses modèles associés ; rien d'autre ne change."""
    import fiche
    nom = os.path.basename(dossier)
    notes = []
    for f in sorted(os.listdir(dossier)):
        if f == nom + ".bbmodel":
            chemin = os.path.join(dossier, f)
            _autorise(chemin)
            sauvegarder(chemin)
            notes += [f"{f} : {n}" for n in fiche.embarquer_fichier(chemin, dossier) if "raccourci" in n or "absent" in n]
    return notes


def reexporter(dossier, anciennes):
    """Refait l'export de la pièce et retire les anciens exports qui ne correspondent plus (nom, ensemble, refus)."""
    import exporter
    nouvelles = []
    try:
        for source, cible, titre in exporter.cibles_piece(dossier):
            _autorise(cible)
            exporter.copier_renomme(source, cible, titre)
            nouvelles.append(cible)
    except SystemExit as e:          # copier_renomme s'arrête si la copie diffère au-delà du nom
        raise Refus(str(e))
    garde = {os.path.normcase(c) for c in nouvelles}
    retires = []
    for c in anciennes:
        if os.path.normcase(c) not in garde and os.path.isfile(c):
            _autorise(c)
            os.remove(c)
            retires.append(c)
            parent = os.path.dirname(c)
            if _sous(parent, LIVRABLES) and os.path.normcase(parent) != os.path.normcase(LIVRABLES) and not os.listdir(parent):
                os.rmdir(parent)
    rel = lambda p: os.path.relpath(p, ROOT).replace(os.sep, "/")
    return [f"exporté : {rel(c)}" for c in nouvelles] + [f"ancien export retiré : {rel(c)}" for c in retires]


def enregistrer_piece(donnees):
    """donnees = {nom, fiche: {nom, ensemble, rarete, prix: {pv, phynarium}, prix_manuel, en_vente, description, lore},
    statut, avis}. Renvoie la liste des notes."""
    import exporter
    if not isinstance(donnees, dict) or not isinstance(donnees.get("fiche"), dict):
        raise Refus("données invalides")
    nom = donnees.get("nom")
    d = dossier_piece(nom)
    f = donnees["fiche"]
    auto, par_rarete, g = proposition_grille(nom, d)
    infos = gen_index.infos_ensembles()

    propre = _texte(f.get("nom"), "Nom", LIMITES["nom"], requis=True)
    if not exporter.INTERDITS.sub("", propre).strip():
        raise Refus("Nom : il faut au moins une lettre")
    description = _texte(f.get("description"), "Description", LIMITES["description"])
    lore = _texte(f.get("lore"), "Lore", LIMITES["lore"])
    manuel = f.get("prix_manuel") is True
    en_vente = f.get("en_vente") is not False
    if manuel:
        rarete = f.get("rarete")
        if rarete not in {k for k, _ in raretes(g)}:
            raise Refus(f"Rareté inconnue : {rarete!r}")
        p = f.get("prix") or {}
        prix_ = {"pv": _entier(p.get("pv"), "Prix PV"), "phynarium": _entier(p.get("phynarium"), "Prix Phynarium")}
    else:                            # sans prix manuel : la grille décide (comme python tools/prix.py), valeurs montrées avant
        rarete, prix_ = auto["rarete"], {"pv": auto["pv"], "phynarium": auto["phynarium"]}
    ens = f.get("ensemble", "")
    if ens not in ("", "Autres") and ens not in infos:
        raise Refus(f"Ensemble inconnu : {ens!r}")
    statut = donnees.get("statut", "a_tester")
    if statut not in gen_index.STATUTS_LIBELLES:
        raise Refus(f"Statut inconnu : {statut!r}")
    avis = _texte(donnees.get("avis"), "Note de statut", AVIS_MAX)

    anciennes = [c for _, c, _ in exporter.cibles_piece(d)]
    chemin = os.path.join(d, "fiche.json")
    fj = lire_json(chemin, {}) or {}
    fj.update({"nom": propre, "description": description, "lore": lore, "rarete": rarete, "prix": prix_,
               "prix_manuel": manuel, "en_vente": en_vente})
    # Ensemble : écrit seulement s'il diffère de la déduction par le nom (sinon le champ est retiré).
    voulu = ens or "Autres"
    if voulu == gen_index.ensemble_deduit(nom):
        fj.pop("ensemble", None)
    else:
        fj["ensemble"] = voulu
    ecrire_json(chemin, fj)

    table = lire_json(gen_index.STATUTS_JSON, {}) or {}
    avant = table.get(nom) or {}
    if avant.get("statut", "a_tester") != statut or avant.get("avis", "") != avis or (nom not in table and nom in gen_index.STATUTS):
        if statut == "a_tester" and not avis:
            table.pop(nom, None)
        else:
            table[nom] = {"statut": statut, "avis": avis}
        ecrire_json(gen_index.STATUTS_JSON, table)

    notes = reembarquer(d)
    notes += reexporter(d, anciennes)
    gen_index.ecrire_index()
    return notes


# ------------------------------------------------------------------------------------------------ ensembles
def lire_ensembles():
    infos = gen_index.infos_ensembles()
    fiches = pieces_par_ensemble()
    return {"ensembles": [{"cle": k, "nom": i.get("nom") or k, "titre": i.get("titre") or "", "theme": i.get("theme") or "",
                           "accroche": i.get("accroche") or "", "lore": i.get("lore") or "",
                           "couleur": i.get("couleur") or gen_index.TEINTE_DEFAUT, "en_vente": i.get("en_vente", True) is not False,
                           "pieces": fiches.get(k, [])} for k, i in infos.items()],
            "themes": gen_index.themes(), "limites": LIMITES_ENS}


def pieces_par_ensemble():
    out = {}
    for categorie in sorted(os.listdir(COS)):
        base = os.path.join(COS, categorie)
        if not os.path.isdir(base):
            continue
        for nom in sorted(os.listdir(base)):
            d = os.path.join(base, nom)
            if os.path.isfile(os.path.join(d, nom + ".bbmodel")):
                out.setdefault(gen_index.ensemble_de(nom, d), []).append(nom)
    return out


def _champs_ensemble(e, infos, cle_actuelle=None):
    nom = _texte(e.get("nom"), "Nom de l'ensemble", LIMITES_ENS["nom"], requis=True)
    if nom.lower() in ("autres", "aucun"):
        raise Refus("« Autres » et « Aucun » sont réservés")
    for k, i in infos.items():
        if k != cle_actuelle and nom.lower() in (k.lower(), str((i or {}).get("nom") or "").lower()):
            raise Refus(f"Un ensemble s'appelle déjà « {nom} »")
    couleur = e.get("couleur") or gen_index.TEINTE_DEFAUT
    if not isinstance(couleur, str) or not COULEUR.match(couleur):
        raise Refus("Couleur : #rrggbb attendu")
    return {"nom": nom, "titre": _texte(e.get("titre"), "Titre", LIMITES_ENS["titre"]),
            "theme": _texte(e.get("theme"), "Thème", LIMITES_ENS["theme"], requis=True),
            "accroche": _texte(e.get("accroche"), "Accroche", LIMITES_ENS["accroche"]),
            "lore": _texte(e.get("lore"), "Lore", LIMITES_ENS["lore"]), "couleur": couleur.lower()}


def enregistrer_ensemble(donnees):
    """donnees = {action: creer | modifier | supprimer, cle, ensemble: {nom, titre, theme, accroche, lore, couleur, en_vente}}."""
    if not isinstance(donnees, dict):
        raise Refus("données invalides")
    action, cle = donnees.get("action"), donnees.get("cle")
    infos = gen_index.infos_ensembles()
    e = donnees.get("ensemble") if isinstance(donnees.get("ensemble"), dict) else {}
    notes = []
    if action == "creer":
        champs = _champs_ensemble(e, infos)
        cle = champs["nom"]
        infos[cle] = {**champs, "en_vente": e.get("en_vente") is not False} if e.get("en_vente") is False else champs
        ecrire_json(gen_index.ENSEMBLES_JSON, infos)
        notes.append(f"ensemble « {cle} » créé (vide : choisissez-le dans la fiche d'une pièce)")
    elif action == "modifier":
        if cle not in infos:
            raise Refus(f"Ensemble introuvable : {cle!r}")
        champs = _champs_ensemble(e, infos, cle)
        ancien_nom = infos[cle].get("nom") or cle
        membres = [n for n in pieces_par_ensemble().get(cle, [])]
        anciennes = {}
        if champs["nom"] != ancien_nom:
            import exporter
            for n in membres:
                anciennes[n] = [c for _, c, _ in exporter.cibles_piece(gen_index.dossier_de(n))]
        i = dict(infos[cle])
        i.update(champs)
        if e.get("en_vente") is False:
            i["en_vente"] = False
        else:
            i.pop("en_vente", None)
        infos[cle] = i
        ecrire_json(gen_index.ENSEMBLES_JSON, infos)
        notes.append(f"ensemble « {champs['nom']} » enregistré")
        for n in anciennes:          # nom affiché changé : il est dans la fiche embarquée et dans le dossier d'export
            d = gen_index.dossier_de(n)
            notes += reembarquer(d)
            notes += reexporter(d, anciennes[n])
    elif action == "supprimer":
        if cle not in infos:
            raise Refus(f"Ensemble introuvable : {cle!r}")
        membres = pieces_par_ensemble().get(cle, [])
        if membres:
            raise Refus(f"Ensemble non vide ({', '.join(membres)}) : changez d'abord l'ensemble de ces pièces")
        del infos[cle]
        ecrire_json(gen_index.ENSEMBLES_JSON, infos)
        notes.append(f"ensemble « {cle} » supprimé")
        if any(e2 == cle for _, e2 in gen_index.MOTS):
            notes.append(f"note : le mot de MOTS (tools/gen_index.py) qui menait à « {cle} » y reste ; une future pièce à ce nom n'aurait pas d'ensemble connu")
    else:
        raise Refus("action inconnue")
    gen_index.ecrire_index()
    return notes
