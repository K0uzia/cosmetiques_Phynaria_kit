"""Bloc `unhandled_root_fields.phynaria` du modèle (guide, sections 5 ter §6, 6.6, 10 bis, 14) : fiche de l'objet,
réglages des particules, familier vivant, skin d'objet.

    notes = embarquer_fichier(".build/x_opt.bbmodel", dossier)   # livrer.py : fiche.json + reglages.json embarqués
    notes = embarquer_fiche(model, dossier)                       # dans un générateur ou un script
    erreurs, alertes = valider_phynaria(model)                    # vérificateur

Le bloc est **fusionné** : chaque fonction n'écrit que sa clé (`fiche`, `particules`) et garde les autres (`familier` écrit
par un générateur, `objet`). Format de la fiche (guide 10 bis) :
    "fiche": {"nom": ≤ 40, "ensemble": ≤ 40, "rarete": ≤ 24, "description": ≤ 300, "lore": ≤ 500}
`\\n` va à la ligne. Rareté : commun, peu_commun, rare, epique, legendaire, mythique (ou un mot à soi, gardé tel quel).
Vignette 3D de la carte (guide 10 bis et 13, 2026-11-06 soir), facultative, clé `vignette` du bloc, recopiée depuis la clé
`vignette` de fiche.json si elle y est (jamais écrite par défaut : sans elle, le mod cadre la pièce seule de trois quarts, au repos) :
    "vignette": {"angle": [vue d'en haut -90..90, rotation], "zoom": 0,25..4, "etat": "idle" ou nom d'animation, "temps": 0..60 s}
Ensemble : champ « nom » de cosmetiques/ensembles.json (même nom = même ensemble, majuscules ignorées) ; l'ensemble de la
pièce est le champ « ensemble » de fiche.json s'il existe (clé ou nom d'ensembles.json, « Autres » = aucun), sinon déduit du nom.
Un texte trop long serait coupé par le mod : on le raccourcit ici à la fin d'une phrase ou d'un mot, avec une note.
Bibliothèque standard seule."""
import json, os, re, sys, unicodedata

ICI = os.path.dirname(os.path.abspath(__file__))
COS = os.path.join(os.path.dirname(ICI), "cosmetiques")
VERSION = 1
CLES = ("version", "particules", "fiche", "familier", "objet", "vignette")                 # clés du bloc connues du guide
LIMITES = {"nom": 40, "ensemble": 40, "rarete": 24, "description": 300, "lore": 500}   # guide 10 bis et 7
RARETES = ("commun", "peu_commun", "rare", "epique", "legendaire", "mythique")

# familier vivant (guide 6.6)
MODES = ("sol", "vol", "nage", "perche", "aucun")
DISTANCES = (1.5, 2, 3, 4, 5, 6, 8)
VITESSES = (0.5, 0.75, 1, 1.25, 1.5, 2)
HAUTEUR = (0.5, 3.0)
# skins d'objets (guide 14) : type -> étapes (groupes à la racine)
OBJETS = {
    "epee": ("repos",), "pioche": ("repos",), "hache": ("repos",), "pelle": ("repos",), "houe": ("repos",),
    "lance": ("repos", "leve", "lance"), "arc": ("repos", "bande_1", "bande_2", "bande_3"),
    "arbalete": ("repos", "bande_1", "bande_2", "bande_3", "chargee", "chargee_fusee"),
    "trident": ("repos", "leve", "lance"), "bouclier": ("repos", "bloque"), "masse": ("repos",), "canne": ("repos", "lancee"),
}


def bloc(model, creer=True):
    """model["unhandled_root_fields"]["phynaria"], créé au besoin avec "version": 1."""
    racine = model.get("unhandled_root_fields")
    if not isinstance(racine, dict):
        if not creer:
            return None
        racine = model["unhandled_root_fields"] = {}
    b = racine.get("phynaria")
    if not isinstance(b, dict):
        if not creer:
            return None
        b = racine["phynaria"] = {}
    b.setdefault("version", VERSION)
    return b


def rarete_normale(r):
    """Comme le mod : minuscules, sans accents, espaces et tirets changés en « _ » (« Peu commun » → peu_commun)."""
    r = unicodedata.normalize("NFKD", str(r)).encode("ascii", "ignore").decode().lower().strip()
    return re.sub(r"[\s-]+", "_", r)


def raccourcir(texte, n):
    """Texte ≤ n caractères : coupé à la fin de la dernière phrase entière, sinon au dernier mot, avec « … »."""
    if len(texte) <= n:
        return texte
    tete = texte[:n]
    fins = [m.end() for m in re.finditer(r"[.!?…](?=\s|$)", tete)]
    if fins and fins[-1] >= n * 0.6:
        return tete[:fins[-1]].rstrip()
    return tete[:n - 1].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"


def _lire(chemin, defaut=None):
    try:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return defaut


def ensemble_de_dossier(nom, dossier=None):
    """Nom d'ensemble affiché (ensembles.json, « nom ») ; None hors ensemble. Le champ « ensemble » de fiche.json prime
    sur la déduction par le nom du dossier (gen_index.ensemble_de)."""
    sys.path.insert(0, ICI)
    from gen_index import ensemble_de
    cle = ensemble_de(nom, dossier)
    infos = (_lire(os.path.join(COS, "ensembles.json"), {}) or {}).get(cle)
    return (infos or {}).get("nom") or (cle if cle != "Autres" else None)


def fiche_de(dossier):
    """(fiche au format du guide, notes) d'après <dossier>/fiche.json ; (None, notes) sans fiche.json."""
    nom = os.path.basename(os.path.abspath(dossier))
    fj = _lire(os.path.join(dossier, "fiche.json"))
    if not fj:
        return None, [f"{nom} : pas de fiche.json, fiche non embarquée"]
    notes, out = [], {}
    valeurs = {"nom": fj.get("nom"), "ensemble": ensemble_de_dossier(nom, dossier), "rarete": fj.get("rarete"),
               "description": fj.get("description"), "lore": fj.get("lore")}
    for cle, v in valeurs.items():
        if not v:
            if cle != "ensemble":                  # pièce hors ensemble (« Autres » du Vestiaire) : champ omis, guide 10 bis
                notes.append(f"{cle} absent")
            continue
        v = str(v).strip()
        if cle == "rarete":
            v = rarete_normale(v)
            if v not in RARETES:
                notes.append(f"rareté « {v} » hors de la liste du guide (gardée telle quelle, sans couleur connue)")
        court = raccourcir(v, LIMITES[cle])
        if court != v:
            notes.append(f"{cle} raccourci de {len(v)} à {len(court)} caractères (≤ {LIMITES[cle]})")
        out[cle] = court
    return out, notes


def embarquer_fiche(model, dossier):
    f, notes = fiche_de(dossier)
    if f:
        bloc(model)["fiche"] = f
    v = (_lire(os.path.join(dossier, "fiche.json")) or {}).get("vignette")
    if v is not None:
        bloc(model)["vignette"] = v
        notes.append("vignette embarquée (guide 10 bis)")
    return notes


def valider_vignette(v):
    """Bloc vignette (guide 10 bis) : angle [-90..90, rotation], zoom 0,25..4, etat texte, temps 0..60."""
    erreurs, alertes = [], []
    if not isinstance(v, dict):
        return ["vignette : objet attendu"], alertes
    num = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)
    for cle in v:
        if cle not in ("angle", "zoom", "etat", "temps"):
            alertes.append(f"vignette.{cle} : clé inconnue du guide (ignorée)")
    a = v.get("angle")
    if a is not None and not (isinstance(a, list) and len(a) == 2 and all(map(num, a)) and -90 <= a[0] <= 90):
        erreurs.append(f"vignette.angle = {a!r} : attendu [vue d'en haut -90..90, rotation]")
    if "zoom" in v and not (num(v["zoom"]) and 0.25 <= v["zoom"] <= 4):
        erreurs.append(f"vignette.zoom = {v['zoom']!r} : attendu 0,25 à 4")
    if "etat" in v and not isinstance(v["etat"], str):
        erreurs.append("vignette.etat : texte attendu (état ou nom d'animation)")
    if "temps" in v and not (num(v["temps"]) and 0 <= v["temps"] <= 60):
        erreurs.append(f"vignette.temps = {v['temps']!r} : attendu 0 à 60 s")
    return erreurs, alertes


def embarquer_fichier(chemin_modele, dossier):
    """Embarque fiche.json et reglages.json (s'ils existent) dans un .bbmodel sur disque, au format compact de
    l'optimiseur. Renvoie les notes. Les autres clés du bloc phynaria (familier, objet) sont gardées."""
    sys.path.insert(0, ICI)
    import particules
    with open(chemin_modele, encoding="utf-8") as f:
        m = json.load(f)
    notes = [f"fiche : {n}" for n in embarquer_fiche(m, dossier)]
    rj = os.path.join(dossier, "reglages.json")
    if os.path.isfile(rj):
        notes += [f"réglages : {n}" for n in particules.embarquer_reglages(m, rj)]
    # Écrit à côté puis remplace d'un coup : un modèle lu pendant l'écriture (Vestiaire) n'est jamais à moitié écrit.
    tmp = chemin_modele + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(m, f, separators=(",", ":"))
    os.replace(tmp, chemin_modele)
    return notes


# ---------------------------------------------------------------------------------------------------- contrôles
def valider_fiche(f):
    erreurs, alertes = [], []
    if not isinstance(f, dict):
        return ["fiche : objet attendu"], alertes
    for cle in f:
        if cle not in LIMITES:
            alertes.append(f"fiche.{cle} : clé inconnue du guide (ignorée)")
    for cle, n in LIMITES.items():
        v = f.get(cle)
        if v is None:
            if cle != "ensemble":                  # pièce hors ensemble permise (« Autres » du Vestiaire)
                alertes.append(f"fiche.{cle} absent")
        elif not isinstance(v, str):
            erreurs.append(f"fiche.{cle} : texte attendu")
        elif len(v) > n:
            erreurs.append(f"fiche.{cle} : {len(v)} caractères (≤ {n}, le mod le couperait)")
    r = f.get("rarete")
    if isinstance(r, str) and rarete_normale(r) not in RARETES:
        alertes.append(f"fiche.rarete « {r} » : mot libre, sans couleur du guide ({', '.join(RARETES)})")
    # description > 160 : la fiche du jeu la montre en entier, seule la ligne de boutique la coupe (texte entier au survol)
    return erreurs, alertes


def valider_familier(fa):
    erreurs, alertes = [], []
    if not isinstance(fa, dict):
        return ["familier : objet attendu"], alertes
    for cle in fa:
        if cle not in ("mode", "distance", "vitesse", "hauteur"):
            alertes.append(f"familier.{cle} : clé inconnue du guide (ignorée)")
    mode = fa.get("mode", "aucun")
    if mode not in MODES:
        erreurs.append(f"familier.mode = {mode!r} : attendu {'/'.join(MODES)} (inconnu = porté comme avant)")
    num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
    if "distance" in fa and not (num(fa["distance"]) and fa["distance"] in DISTANCES):
        erreurs.append(f"familier.distance = {fa['distance']!r} : attendu {DISTANCES}")
    if "vitesse" in fa and not (num(fa["vitesse"]) and fa["vitesse"] in VITESSES):
        erreurs.append(f"familier.vitesse = {fa['vitesse']!r} : attendu {VITESSES}")
    if "hauteur" in fa and not (num(fa["hauteur"]) and HAUTEUR[0] <= fa["hauteur"] <= HAUTEUR[1]):
        erreurs.append(f"familier.hauteur = {fa['hauteur']!r} : attendu {HAUTEUR[0]} à {HAUTEUR[1]} blocs")
    if "hauteur" in fa and mode not in ("vol", "perche"):
        alertes.append(f"familier.hauteur ne sert qu'aux modes vol et perche (mode {mode})")
    return erreurs, alertes


def valider_objet(o):
    erreurs, alertes = [], []
    if not isinstance(o, dict):
        return ["objet : objet attendu"], alertes
    t = o.get("type")
    if t not in OBJETS:
        erreurs.append(f"objet.type = {t!r} : attendu {'/'.join(OBJETS)}")
    for cle in o:
        if cle not in ("type", "affichage"):
            alertes.append(f"objet.{cle} : clé inconnue du guide (ignorée)")
    return erreurs, alertes


def mode_familier(model):
    """Mode du familier vivant ('sol', 'vol', 'nage', 'perche') ou None (porté)."""
    b = bloc(model, creer=False) or {}
    fa = b.get("familier")
    mode = fa.get("mode") if isinstance(fa, dict) else None
    return mode if mode in MODES and mode != "aucun" else None


def type_objet(model):
    b = bloc(model, creer=False) or {}
    o = b.get("objet")
    return o.get("type") if isinstance(o, dict) and o.get("type") in OBJETS else None


def valider_phynaria(model):
    """(erreurs, alertes, résumé) sur tout le bloc phynaria, réglages des particules compris."""
    sys.path.insert(0, ICI)
    import particules
    erreurs, alertes, resume = [], [], []
    b = bloc(model, creer=False)
    er, al = particules.valider_reglages(model)
    erreurs += er
    alertes += al
    if b is None:
        alertes.append("pas de bloc unhandled_root_fields.phynaria : ni fiche ni réglages embarqués (tools/fiche.py, livrer.py)")
        return erreurs, alertes, resume
    if b.get("version") != VERSION:
        erreurs.append(f"phynaria.version = {b.get('version')!r} (attendu {VERSION})")
    for cle in b:
        if cle not in CLES:
            alertes.append(f"phynaria.{cle} : clé inconnue du guide (ignorée par le mod)")
    if "particules" in b:
        resume.append(f"{len(b['particules'])} réglage(s) de particules")
    if "fiche" in b:
        e, a = valider_fiche(b["fiche"])
        erreurs += e
        alertes += a
        resume.append("fiche")
    else:
        alertes.append("pas de fiche embarquée (fiche.json, guide 10 bis)")
    if "familier" in b:
        e, a = valider_familier(b["familier"])
        erreurs += e
        alertes += a
        resume.append(f"familier (mode {b['familier'].get('mode', 'aucun') if isinstance(b['familier'], dict) else '?'})")
    if "vignette" in b:
        e, a = valider_vignette(b["vignette"])
        erreurs += e
        alertes += a
        resume.append("vignette")
    if "objet" in b:
        e, a = valider_objet(b["objet"])
        erreurs += e
        alertes += a
        resume.append(f"objet ({b['objet'].get('type') if isinstance(b['objet'], dict) else '?'})")
    return erreurs, alertes, resume
