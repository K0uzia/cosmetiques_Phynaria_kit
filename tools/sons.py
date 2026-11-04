"""Garde les sons rares (retour de l'utilisateur : « infernal » quand chaque mouvement siffle, plusieurs fois de suite).
Usage dans un générateur, juste avant d'écrire le modèle :
    limiter_sons(model)
Règle (.claude/rules/fonctions-avancees.md) :
- états en mouvement (walk, run, fly, glide, fall, swim, sneak, mount…) : aucun son ;
- repos (idle, sleep) : au plus un son par boucle, et seulement si la boucle dure au moins PERIODE_MIN secondes ;
- attack : au plus un son, seulement pour une arme (attaque=True) ; event_equip (rare) : au plus un ; hurt et autres événements : aucun ;
- couches permanentes (overlay_…) : aucun son (elles tournent en même temps que l'état).
Le modèle est modifié sur place."""

PERIODE_MIN = 20.0       # « encore un peu trop fréquent » à 8 s (2e retour)
REPOS = ("idle", "sleep")
PONCTUELS = ("attack", "hurt")


def limiter_sons(model, attaque=False):
    for an in model["animations"]:
        effets = an.get("animators", {}).get("effects")
        if not effets:
            continue
        nom = an["name"].split(".")[-1]
        sons = sorted((k for k in effets["keyframes"] if k["channel"] == "sound"), key=lambda k: k["time"])
        if nom in REPOS:
            garde = sons[:1] if float(an["length"]) >= PERIODE_MIN else []
        elif (nom == "attack" and attaque) or nom == "event_equip":
            garde = sons[:1]
        else:
            garde = []
        effets["keyframes"] = [k for k in effets["keyframes"] if k["channel"] != "sound"] + garde
        if not effets["keyframes"]:
            del an["animators"]["effects"]
