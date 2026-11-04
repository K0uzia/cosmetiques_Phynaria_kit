# Règles — animations

## Axes

`docs/guide-cosmetiques.md` prime sur ce fichier. Le jeu lit les rotations telles quelles, comme la vue 3D de Blockbench ; seul l'export Bedrock inverse X et Y. Le renderer `tools/render_bbmodel.py` les reproduit avec `MODCONV=1`.

Le joueur regarde −Z, sa droite est +X. Valeurs de keyframe :
- **+X** : le haut du groupe bascule vers l'arrière.
- **+Y** : le côté droit (+X) avance.
- **+Z** : le côté droit monte, donc le côté gauche descend.

Pour une aile : écrire une seule fois l'intention dans une fonction, et centraliser le signe dans `mirror()`. Modèle : `cosmetiques/ailes/aurelion_wings/gen_aurelion_wings.py`.

Autres points du guide : `air` n'est pas reconnu (utiliser `fall`) ; `attack` et `hurt` en `once`, avec les seuls groupes concernés ; les keyframes n'ont pas la limite de ±360°. Superposition (overlay, `event_*`) : rotations et positions s'ajoutent, échelles se multiplient (`fonctions-avancees.md`).

## Molang

- Variables mémorisées (`v.x = …;`, 16 instructions par clé, 512 caractères) et nouvelles requêtes (`q.is_boosting`, `q.yaw_speed`, `q.head_*`, `q.instance_seed`, `q.delta_time`…) : guide 6.3. Le battement à la fusée validé en jeu utilise un seuil de vitesse (exclut les piqués) ; `q.is_boosting` est l'alternative directe, à essayer avec `/cosmetique apercu`.
- Le renderer ne simule pas les variables mémorisées : une expression qui en dépend se juge en jeu.
- Simuler dans le renderer : `MOLANG_QUERY="ground_speed=33,vertical_speed=0"`, puis vérifier aussi l'extension dans cet état.
- `math.sin` et `math.cos` sont en degrés. Période fermée : `q.anim_time * 360 * k / durée`.

## Canaux

- **`rotation`, `position` et `scale` sont supportés.** Vérifier en jeu le premier usage de `position` et `scale` sur une pièce.
- `position` : +Y monte, +X va vers la droite du joueur (guide, section 3).
- Halo qui flotte ou pulse, élément qui apparaît ou disparaît → possible dans le modèle.
- Éléments détachés du joueur (plumes qui se posent au sol) → groupes `particle_<nom>` et `emit_<nom>`, animations `particle_<nom>_fall` et `_rest` (guide, section 5 ter).
- En vol créatif, le joueur reste debout : un plan à 90° se voit par la tranche de face. En élytres et en nage, le corps est couché et le cosmétique le suit : le plan du dos est déjà horizontal dans le monde.

## Boucles

- Toute animation `loop` doit avoir **la même pose à t=0 et t=length**. Le vérificateur le mesure (< 0,05 px).
- Construire les courbes avec des fonctions périodiques de période = durée (sin/cos), ou des impulsions `bump()` qui reviennent à 0 avant la fin.
- Pour l'interpolation `catmullrom`, **ne pas mettre de keyframe à t=length** : la boucle se referme sur t=0. Pour `linear`, en mettre un identique au premier.
- Une pièce qui tourne en continu va dans une animation `overlay_<nom>` (guide 6.4) : jouée en permanence par-dessus l'état, elle ne saute plus au changement d'état. Elle fait exactement 360°·k par boucle.
- Pas de `uuid` dans les keyframes : l'optimiseur les retire, Blockbench les régénère.

## États du mod et animations attendues

| Case du mod | Nom | Intention |
|---|---|---|
| Immobile | `idle` | respiration lente (période 4 s) + **étirement** périodique (ouverture ample ~2 s) — boucle 8 s |
| Marche | `walk` | ailes un peu ramenées vers l'arrière, balancement au rythme du pas |
| Course | `run` | nettement vers l'arrière, repliées en S, abaissées (profil) — **pas** écartées sur les côtés |
| Accroupi | `sneak` | repliées serrées contre le dos, pointes qui remontent vers les épaules |
| Vol | `fly` | plan basculé d'environ **40°** (joueur debout, jamais 90°), battement ample, descente étendue / remontée poignet replié |
| Élytres | `glide` | presque dans le plan du dos (corps couché), grandes ouvertes, battement lent, ample à la fusée |
| En l'air | `fall` | demi-basculées (environ 26°), relevées, ouvertes (freinage) |
| Nage | `swim` | presque dans le plan du dos (corps couché), ondulation |
| Monture | `mount` | repos relevé, respiration ample |
| Sommeil | `sleep` | repliées, tombantes, respiration très lente |
| Attaque | `attack` | `once` : déploiement brusque puis retour à 0 (0,8 s), groupes concernés seuls |
| Blessé | `hurt` | `once` : sursaut vers l'arrière + tremblement amorti, retour à 0 (0,8 s) |

Mots reconnus et repli d'un état manquant : guide, section 6.2 (élytres → vol, course → marche, sinon `idle`). Ailes et queues : les 12 états. Pièces discrètes (tête, épaules, armes, auras) : seulement les états utiles.

## Biomécanique (pour que ça ait l'air d'une aile)

- Squelette = bras : épaule → coude → poignet → bout. Bones imbriqués, chaque plume rattachée au segment qui la porte.
- Au repos : plan vertical, plumes qui pendent, léger balayage arrière en Z (humérus arrière, avant-bras revient, main repart).
- En vol : le plan bascule (voir le tableau) ; descente = extension complète, primaires écartées ; remontée = poignet et coude fléchis, primaires serrées.
- Cascade : coude et poignet déphasés de 0,1–0,2 cycle après l'épaule.
- Une seconde paire (plus petite) suit la grande à ~80 % d'amplitude avec un léger retard.
- Pas d'angle droit : répartir le repli sur les 3 articulations (ex. course : −30 / +18 / −22, pas 40/40/46).

## Échantillonnage

- Écrire les courbes en Python, échantillonner à 6–10 keyframes/s, puis laisser `optimize_bbmodel.py` simplifier (RDP, tolérance 0,3–1°).
- Durées : idle 8 s, fly 2,4 s, glide 3,6 s, walk 1,6 s, run 1,0 s, sneak/sleep/mount 3–4 s, attack/hurt 0,8 s.
