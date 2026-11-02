# Règles — animations

## Convention d'axes du mod (mesurée par calibration, ne pas « corriger » d'après Blockbench)

`docs/guide-cosmetiques.md` prime sur ce fichier. Le jeu lit les rotations telles quelles, comme la vue 3D de Blockbench ; seul l'export Bedrock inverse X et Y. Le renderer `tools/render_bbmodel.py` les reproduit avec `MODCONV=1`.

Le joueur regarde −Z, sa droite est +X. Valeurs de keyframe :
- **+X** : le haut du groupe bascule vers l'arrière.
- **+Y** : le côté droit (+X) avance.
- **+Z** : le côté droit monte, donc le côté gauche descend.

Pour une aile : écrire une seule fois l'intention dans une fonction, et centraliser le signe dans `mirror()`. Modèle : `cosmetiques/ailes/aurelion_wings/gen_aurelion_wings.py`.

Autres points du guide : `air` n'est pas reconnu (utiliser `fall`) ; `attack` et `hurt` en `once`, avec les seuls groupes concernés ; les keyframes n'ont pas la limite de ±360°.

## Molang

- Pas d'accélération ni de variable mémorisée : un effet « à la fusée » s'approche par un seuil de vitesse (`q.ground_speed`, `q.vertical_speed`), qui exclut les piqués.
- Simuler dans le renderer : `MOLANG_QUERY="ground_speed=33,vertical_speed=0"`, puis vérifier aussi l'extension dans cet état.
- `math.sin` et `math.cos` sont en degrés. Période fermée : `q.anim_time * 360 * k / durée`.

## Canaux

- **`rotation`, `position` et `scale` sont supportés** (confirmé par le développeur du mod). Notre ancien constat « ignorés » venait de notre modèle de test ; la cause exacte n'est pas identifiée, donc vérifier en jeu le premier usage de ces canaux.
- La convention de signe de `position` n'est pas mesurée : `/bbmodel-calibrate` avant de l'utiliser sur X ou Z.
- Halo qui flotte ou pulse, élément qui apparaît ou disparaît → possible dans le modèle.
- Éléments détachés du joueur (plumes qui se posent au sol) → groupes `particle_<nom>` et `emit_<nom>`, animations `particle_<nom>_fall` et `_rest` (guide, section 5 ter).
- En vol créatif, le joueur reste debout : un plan à 90° se voit par la tranche de face. En élytres et en nage, le corps est couché et le cosmétique le suit : le plan du dos est déjà horizontal dans le monde.

## Boucles

- Toute animation `loop` doit avoir **la même pose à t=0 et t=length**. Le vérificateur le mesure (< 0,05 px).
- Construire les courbes avec des fonctions périodiques de période = durée (sin/cos), ou des impulsions `bump()` qui reviennent à 0 avant la fin.
- Pour l'interpolation `catmullrom`, **ne pas mettre de keyframe à t=length** : la boucle se referme sur t=0. Pour `linear`, en mettre un identique au premier.
- Un halo qui tourne en continu doit faire exactement 360°·k par boucle, sinon il saute.
- Pas de `uuid` dans les keyframes : l'optimiseur les retire, Blockbench les régénère.

## États du mod et animations attendues

| Case du mod | Nom | Intention |
|---|---|---|
| Immobile | `idle` | respiration lente (période 4 s) + **étirement** périodique (ouverture ample ~2 s) — boucle 8 s |
| Marche | `walk` | ailes un peu ramenées vers l'arrière, balancement au rythme du pas |
| Course | `run` | nettement vers l'arrière, repliées en S, abaissées (profil) — **pas** écartées sur les côtés |
| Accroupi | `sneak` | repliées serrées contre le dos, pointes qui remontent vers les épaules (« rangées », style Lucifer) |
| Vol | `fly` | plan **horizontal** (X négatif), battement ample, descente étendue / remontée poignet replié |
| Élytres | `glide` | horizontal, grandes ouvertes, **battement lent et ample** (pas une pose figée) |
| En l'air | `air` | demi-basculées, relevées, ouvertes (freinage) |
| Nage | `swim` | profilées vers l'arrière, ondulation |
| Monture | `mount` | repos relevé, respiration ample |
| Sommeil | `sleep` | repliées, tombantes, respiration très lente |
| Attaque | `attack` | impulsion : déploiement brusque puis retour (0,8 s) |
| Blessé | `hurt` | impulsion : sursaut vers l'arrière + tremblement amorti (0,8 s) |

Si un état n'a pas d'animation, le mod joue `idle`. Toujours fournir au minimum idle, fly, glide, run, sneak.

## Biomécanique (pour que ça ait l'air d'une aile)

- Squelette = bras : épaule → coude → poignet → bout. Bones imbriqués, chaque plume rattachée au segment qui la porte.
- Au repos : plan vertical, plumes qui pendent, léger balayage arrière en Z (humérus arrière, avant-bras revient, main repart).
- En vol : le plan **bascule à l'horizontale** ; descente = extension complète, primaires écartées ; remontée = poignet et coude fléchis, primaires serrées.
- Cascade : coude et poignet déphasés de 0,1–0,2 cycle après l'épaule.
- Une seconde paire (plus petite) suit la grande à ~80 % d'amplitude avec un léger retard.
- Pas d'angle droit : répartir le repli sur les 3 articulations (ex. course : −30 / +18 / −22, pas 40/40/46).

## Échantillonnage

- Écrire les courbes en Python, échantillonner à 6–10 keyframes/s, puis laisser `optimize_bbmodel.py` simplifier (RDP, tolérance 0,3–1°).
- Durées : idle 8 s, fly 2,4 s, glide 3,6 s, walk 1,6 s, run 1,0 s, sneak/sleep/mount 3–4 s, attack/hurt 0,8 s.
