---
name: bbmodel-animate
description: Ajouter ou corriger les animations d'un cosmétique .bbmodel (idle, fly, glide, run, sneak…) dans la convention d'axes du mod, avec boucles fermées et biomécanique d'aile crédible.
---

# Animer un cosmétique

Lis `.claude/rules/animation.md` et la section 6 du guide avant tout. Repars des courbes de `gen_ailes_abyssales.py` ou `gen_aurelion_wings.py`, ajustées en jeu.

## Procédure

1. Identifie l'état à (re)faire et son intention (tableau des états dans la règle). Si l'utilisateur dit « c'est inversé » : c'est un signe d'axe, pas un design. Un seul signe à changer dans `mirror()`.
2. Écris les courbes comme des fonctions de t pour l'aile **gauche** : `(fx, fy, fz)` par segment (shoulder, elbow, wrist). Utilise `S(T, amp, phase, offset)` (sinus), `C(v)` (constante), `bump(t, a, b, c, d)` (impulsion). Période = durée de l'anim.
3. Cascade : déphase elbow et wrist de −25° à −45° (phase) après shoulder. Remontée = flexion : `-k * max(0, -cos(θ))` sur Y du poignet.
4. Éventail des primaires via `fan(t)` (positif = s'écartent). Secondaires à 50 %.
5. Échantillonne à 6–10 kf/s avec un keyframe final identique au premier. `optimize_bbmodel.py` simplifiera.
6. Régénère, optimise, **vérifie** (`verify_bbmodel.py` : boucles < 0,05 px, extension < 64, canaux rotation/position/scale).
7. Rends l'état en 4 vues avec `MODCONV=1` et regarde avant de livrer.

