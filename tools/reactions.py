"""Retire les réactions aux coups des pièces portées (consigne de l'utilisateur, 2026-11-05) : « pas logique qu'un équipement
réagisse à une attaque ou à des dégâts ; à la limite le visuel peut changer suivant la barre de vie ».
Usage dans un générateur, juste avant d'écrire le modèle :
    retirer_reactions(model)                     # tête, épaules, queue, sac, aura
    retirer_reactions(model, garder=("attack",)) # arme : l'objet frappe, il ne réagit pas aux dégâts
Ailes (« liées au corps ») et familiers (êtres vivants) gardent attack et hurt : ne pas l'appeler.
Règle : .claude/rules/animation.md. Le modèle est modifié sur place."""

REACTIONS = ("attack", "hurt")


def retirer_reactions(model, garder=()):
    avant = len(model["animations"])
    model["animations"] = [a for a in model["animations"] if a["name"].split(".")[-1] not in REACTIONS or a["name"].split(".")[-1] in garder]
    return avant - len(model["animations"])
