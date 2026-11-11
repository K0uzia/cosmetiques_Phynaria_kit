#!/usr/bin/env python3
"""Grille de prix des cosmétiques (proposition à valider par le staff) : cosmetiques/prix.json.
Usage : python tools/prix.py            applique la grille à chaque cosmetiques/<categorie>/<nom>/fiche.json
                                         (sauf "prix_manuel": true) et met à jour le bloc « calcule » de prix.json
        python tools/prix.py --montrer  affiche la grille et les prix sans rien écrire
Utilisé aussi par tools/gen_index.py (jours de vote, euros, prix des lots). Bibliothèque standard seule."""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COS = os.path.join(ROOT, "cosmetiques")
PRIX = os.path.join(COS, "prix.json")
ENSEMBLES = os.path.join(COS, "ensembles.json")


def charger():
    with open(PRIX, encoding="utf-8") as f:
        return json.load(f)


def pv_par_vote(g):
    h = g["hypotheses"]
    chances = h["chances_par_vote"]
    if h.get("interpretation") == "normalisees":
        total = sum(c["chance"] for c in chances)
        return sum(c["pv"] * c["chance"] for c in chances) / total
    return sum(c["pv"] * c["chance"] for c in chances)


def rythme(g):
    """PV moyens par vote, par jour, par semaine, par mois."""
    h = g["hypotheses"]
    vote = pv_par_vote(g)
    jour = vote * h["sites_de_vote"] * h["votes_par_site_et_par_jour"]
    return {"pv_par_vote": round(vote, 2), "votes_par_jour": h["sites_de_vote"] * h["votes_par_site_et_par_jour"],
            "pv_par_jour": round(jour, 2), "pv_par_semaine": round(jour * 7), "pv_par_mois": round(jour * h["jours_par_mois"])}


def jours_de_vote(g, pv):
    return round(pv / rythme(g)["pv_par_jour"], 1)


def euros(g, phynarium):
    """Coût minimal en euros pour obtenir au moins `phynarium` avec les packs de la boutique."""
    packs = g["packs_phynarium"]
    pas = 100
    n = -(-phynarium // pas)
    cout = [0.0] + [float("inf")] * n
    for i in range(1, n + 1):
        for p in packs:
            k = p["phynarium"] // pas
            cout[i] = min(cout[i], cout[max(0, i - k)] + p["euros"])
    return round(cout[n], 2)


def rarete_auto(g, categorie, cubes):
    ordre = g["ordre_raretes"]
    base = g["rarete_par_categorie"].get(categorie, ordre[0])
    i = ordre.index(base)
    seuil = g["complexite"]["seuil_cubes"].get(categorie)
    if seuil is not None and cubes >= seuil:
        i = min(i + 1, len(ordre) - 1)
    return ordre[i]


def prix_de(g, rarete):
    r = g["raretes"][rarete]
    return {"pv": r["pv"], "phynarium": r["phynarium"]}


def detail(g, prix):
    """Prix enrichi pour l'affichage : jours de vote et euros."""
    if not prix:
        return None
    return dict(prix, jours=jours_de_vote(g, prix["pv"]), euros=euros(g, prix["phynarium"]))


def lot(g, prix_pieces):
    """Prix d'un ensemble complet à partir des prix des pièces en vente, ou None s'il y en a trop peu."""
    l = g["lot"]
    if len(prix_pieces) < l["pieces_min"]:
        return None
    k = 1 - l["remise"]
    arr = lambda v, a: int(round(v / a) * a)
    pv = arr(sum(p["pv"] for p in prix_pieces) * k, l["arrondi_pv"])
    ph = arr(sum(p["phynarium"] for p in prix_pieces) * k, l["arrondi_phynarium"])
    return dict(detail(g, {"pv": pv, "phynarium": ph}), pieces=len(prix_pieces), remise=l["remise"],
                sans_remise={"pv": sum(p["pv"] for p in prix_pieces), "phynarium": sum(p["phynarium"] for p in prix_pieces)})


def cubes_de(modele):
    with open(modele, encoding="utf-8") as f:
        return len(json.load(f).get("elements", []))


def pieces():
    """(categorie, nom, dossier, modele) de chaque pièce livrée."""
    for categorie in sorted(os.listdir(COS)):
        base = os.path.join(COS, categorie)
        if not os.path.isdir(base):
            continue
        for nom in sorted(os.listdir(base)):
            modele = os.path.join(base, nom, nom + ".bbmodel")
            if os.path.isfile(modele):
                yield categorie, nom, os.path.join(base, nom), modele


def ecrire_json(chemin, d):
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")


def appliquer(ecrire=True):
    g = charger()
    lignes, par_ens = [], {}
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from gen_index import ensemble_de
    for categorie, nom, dossier, modele in pieces():
        chemin = os.path.join(dossier, "fiche.json")
        if not os.path.isfile(chemin):
            lignes.append(f"  {nom} : pas de fiche.json")
            continue
        with open(chemin, encoding="utf-8") as f:
            fiche = json.load(f)
        if not fiche.get("prix_manuel"):
            fiche["rarete"] = rarete_auto(g, categorie, cubes_de(modele))
            fiche["prix"] = prix_de(g, fiche["rarete"])
            if ecrire:
                ecrire_json(chemin, fiche)
        if fiche.get("en_vente", True) and fiche.get("prix"):
            par_ens.setdefault(ensemble_de(nom), []).append(fiche["prix"])
        p = detail(g, fiche.get("prix"))
        vente = "" if fiche.get("en_vente", True) else "  (hors vente)"
        lignes.append(f"  {fiche.get('nom', nom)} [{fiche.get('rarete')}] : {p['pv']} PV ≈ {p['jours']} j de vote, "
                      f"{p['phynarium']} Phynarium ≈ {p['euros']} €{vente}")
    calc = {"rythme": rythme(g),
            "raretes": {r: detail(g, prix_de(g, r)) for r in g["ordre_raretes"]},
            "lots": {e: l for e, ps in sorted(par_ens.items()) if (l := lot(g, ps))}}
    if ecrire:
        g["calcule"] = calc
        ecrire_json(PRIX, g)
    return calc, lignes


if __name__ == "__main__":
    calc, lignes = appliquer(ecrire="--montrer" not in sys.argv)
    r = calc["rythme"]
    print(f"Rythme supposé : {r['pv_par_vote']} PV par vote, {r['votes_par_jour']} votes par jour, "
          f"{r['pv_par_jour']} PV par jour, {r['pv_par_semaine']} par semaine, {r['pv_par_mois']} par mois")
    for k, v in calc["raretes"].items():
        print(f"  {k} : {v['pv']} PV ≈ {v['jours']} j, {v['phynarium']} Phynarium ≈ {v['euros']} €")
    print("\n".join(lignes))
    for e, l in calc["lots"].items():
        print(f"  Lot {e} ({l['pieces']} pièces) : {l['pv']} PV ≈ {l['jours']} j, {l['phynarium']} Phynarium ≈ {l['euros']} €")
