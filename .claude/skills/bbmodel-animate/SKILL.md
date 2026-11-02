---
name: bbmodel-animate
description: Ajouter ou corriger les animations d'un cosmétique .bbmodel (idle, fly, glide, run, sneak…) dans la convention d'axes du mod, avec boucles fermées et biomécanique d'aile crédible.
---

# Animer un cosmétique

Lis `.claude/rules/animation.md` avant tout. Les règles d'axes y sont **mesurées**, pas déduites de Blockbench.

## Procédure

1. Identifie l'état à (re)faire et son intention (tableau des états dans la règle). Si l'utilisateur dit « c'est inversé » : c'est un signe d'axe, pas un design. Un seul signe à changer dans `anim()`.
2. Écris les courbes comme des fonctions de t pour l'aile **gauche** : `(fx, fy, fz)` par segment (shoulder, elbow, wrist). Utilise `S(T, amp, phase, offset)` (sinus), `C(v)` (constante), `bump(t, a, b, c, d)` (impulsion). Période = durée de l'anim.
3. Cascade : déphase elbow et wrist de −25° à −45° (phase) après shoulder. Remontée = flexion : `-k * max(0, -cos(θ))` sur Y du poignet.
4. Éventail des primaires via `fan(t)` (positif = s'écartent). Secondaires à 50 %.
5. Échantillonne à 6–10 kf/s avec un keyframe final identique au premier. `optimize_bbmodel.py` simplifiera.
6. Régénère, optimise, **vérifie** (`verify_bbmodel.py` : boucles < 0,05 px, extension < 64, canaux rotation/position/scale).
7. Rends l'état en 4 vues avec `MODCONV=1` et regarde avant de livrer.

## Valeurs de départ qui marchent (aile gauche, convention mod)

| État | shoulder (x, y, z) | notes |
|---|---|---|
| idle | (0, ±2 sin, ±2.5 sin) période 4 s ; étirement `bump(4.6,5.4,6.0,7.2)` vers (10, −14, 14) | boucle 8 s |
| fly | (55 + 8 sin, 4 + 6 sin, 6 + 28 sin) ; wrist y = −6 + 22·max(0,−cos) | 2.4 s |
| glide | (58 + 6 cos, 8, 8 + 22 sin) | 3.6 s, battement lent |
| run | (6, 34 ± 2, −10 ± 2.5) ; elbow y −18 ; wrist y +26 | S progressif |
| sneak | (6, 44, −18) ; elbow (−30, −22) ; wrist (26, −24) | replié dans le dos, pointes vers le haut |
| attack | 28·atk, −20·atk, 16·atk | `atk = bump(0, .14, .30, .8)` |
| hurt | 0, 16·hu, 12·hu + tremblement | `hu = bump(0, .08, .22, .8)` |

Le signe de **X** dans `kf()` est négué par `anim()` (`-fx`) : donc dans les tables ci-dessus X positif = bascule vers l'horizontale. Si un test en jeu montre l'inverse, change ce seul signe et recalibre (`/bbmodel-calibrate`).
