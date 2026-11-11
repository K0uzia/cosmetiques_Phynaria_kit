"""Ancien contournement des faces horizontales (up, down), devenu inutile : MIROIR_X_JEU = False.

Corrigé par le mod (guide, « 6 novembre 2026 (soir) — demandes 5 », section 3) : l'image des faces up et down se lit comme
dans Blockbench, rotations de face comprises. Avant, le mod la dessinait tournée d'un demi-tour sur up et en miroir sur down
(selon le guide ; notre test du 2026-11-06, docs/dev/tests_rendu/test_uv_up.bbmodel, l'avait lu comme un miroir sur X).

L'outil reste pour mémoire : avec MIROIR_X_JEU = False, uv_pour_jeu est l'identité et retourner_pour_jeu ne change rien.
Les générateurs qui l'appellent peuvent le garder ou retirer l'appel. Ne pas repasser à True.
"""

MIROIR_X_JEU = False         # corrigé par le mod (guide du 2026-11-06 soir) : plus rien n'est retourné
FACES = ("up", "down")


def uv_pour_jeu(uv):
    """UV [u0, v0, u1, v1] d'une face up/down, à écrire dans le modèle pour que le jeu l'affiche comme Blockbench l'aurait
    affiché sans retouche. Identité si MIROIR_X_JEU est faux."""
    if not MIROIR_X_JEU:
        return list(uv)
    u0, v0, u1, v1 = uv
    return [u1, v0, u0, v1]


def retourner_pour_jeu(model, filtre=None):
    """Applique uv_pour_jeu à toutes les faces up/down des éléments du modèle (ou de ceux dont le nom passe filtre(nom)).
    Retourne le nombre de faces modifiées. Une face avec une rotation non nulle est laissée telle quelle (non testé en jeu)."""
    if not MIROIR_X_JEU:
        return 0
    n = 0
    for e in model.get("elements", []):
        if filtre is not None and not filtre(e.get("name", "")):
            continue
        for k in FACES:
            f = e.get("faces", {}).get(k)
            if not f or f.get("uv") is None or f.get("rotation"):
                continue
            f["uv"] = uv_pour_jeu(f["uv"])
            n += 1
    return n
