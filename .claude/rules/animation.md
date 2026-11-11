---
paths:
  - "cosmetiques/**"
---

# Règles — animations

## Axes

`docs/guide-cosmetiques.md` prime sur ce fichier. Convention des axes : `essentiel.md`, Axes. Aile : `mirror()` et biomécanique dans `categories/ailes.md`.

Autres points du guide : `air` n'est pas reconnu (utiliser `fall`) ; `attack` et `hurt` en `once`, avec les seuls groupes concernés ; les keyframes n'ont pas la limite de ±360°. Superposition (overlay, `event_*`) : `fonctions-avancees.md`, Pièges.

## Molang

- Variables mémorisées (`v.x = …;`, 16 instructions par clé, 512 caractères) et requêtes (`q.is_boosting`, `q.yaw_speed`, `q.head_*`, `q.instance_seed`, `q.delta_time`, armure `q.has_*`, `q.body_x_rotation`, angles des bras, `q.limb_swing`, familier `q.owner_*` : liste dans `fonctions-avancees.md`) : guide 6.3 et 6.6. Une chaîne ou un pendentif : `phys_…_g100` (gravité du mod) plutôt qu'une contre-rotation par état. Le battement à la fusée validé en jeu utilise un seuil de vitesse (exclut les piqués), resté en place sur les ailes livrées ; `q.is_boosting` (vaut 1 pendant la poussée d'une fusée en élytres, correctif du 2026-11-04) est l'alternative directe, à essayer avec `/cosmetique apercu`.
- Le renderer ne simule pas les variables mémorisées : une expression qui en dépend se juge en jeu.
- Simuler dans le renderer : `MOLANG_QUERY="ground_speed=33,vertical_speed=0"`, puis regarder aussi la taille dans cet état (l'extension animée n'est plus limitée par le mod, mais reste à juger en jeu).
- `math.sin` et `math.cos` sont en degrés. Période fermée : `q.anim_time * 360 * k / durée`.

## Canaux

- **`rotation`, `position` et `scale` sont supportés** (CLAUDE.md, règle 6). Vérifier en jeu le premier usage de `position` et `scale` sur une pièce.
- `position` : +Y monte, +X va vers la droite du joueur (guide, section 3).
- Halo qui flotte ou pulse, élément qui apparaît ou disparaît → possible dans le modèle.
- Éléments détachés du joueur (plumes qui se posent au sol) → groupes `particle_<nom>` et `emit_<nom>`, animations `particle_<nom>_fall` et `_rest` (guide, section 5 ter).
- En vol créatif, le joueur reste debout : un plan à 90° se voit par la tranche de face (bascule d'environ 40°, sans plainte depuis, mais pas de validation explicite ; `fall` environ 26°). En élytres et en nage, le corps est couché et le cosmétique le suit : le plan du dos est déjà horizontal dans le monde (déduit du fonctionnement du mod).

## Boucles

- Toute animation `loop` doit avoir **la même pose à t=0 et t=length**. Le vérificateur le mesure (< 0,05 px).
- Construire les courbes avec des fonctions périodiques de période = durée (sin/cos), ou des impulsions `bump()` qui reviennent à 0 avant la fin.
- Pour l'interpolation `catmullrom`, **ne pas mettre de keyframe à t=length** : la boucle se referme sur t=0. Pour `linear`, en mettre un identique au premier.
- Une pièce qui tourne en continu (engrenages, rotors, halos) va dans une animation `overlay_<nom>` (guide 6.4) : jouée en permanence par-dessus l'état, elle ne saute plus au changement d'état. Elle fait exactement 360°·k par boucle.
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

**Attaque et blessé (consigne de l'utilisateur, 2026-11-05)** : « pas logique qu'un équipement réagisse à une attaque ou à des dégâts ; à la limite le visuel peut changer suivant la barre de vie ». Pas d'`attack` ni de `hurt` sur les pièces portées (tête, épaules, queue, sac, aura). **Exceptions** : les ailes les gardent (« liées au corps, c'est normal ») ; les armes gardent `attack` ; les familiers gardent leur réaction (être vivant). À la place, si utile, un aspect qui suit la vie en continu et en douceur dans les états (`query.health / query.max_health`, guide 6.3) : vie basse = effet plus instable ou plus terne, jamais un changement brutal de forme ou de pose. `attack` reste pour les armes (c'est l'objet qui frappe). `tools/reactions.py` (`retirer_reactions(model)`) avant l'écriture.

Mots reconnus et repli d'un état manquant : guide, section 6.2 (élytres → vol, course → marche, sinon `idle`). Seuls ces noms sont joués d'office (le vérificateur alerte sur un nom libre comme `ondulation`, que seul un choix manuel du staff ferait jouer). Événements d'une pièce portée : `event_jump`, `event_land`, `event_equip`, `event_unequip`, `event_enter_<état>`/`event_exit_<état>` avec les états **en anglais du guide** : idle, walk, **sprint**, sneak, fly, glide, swim, fall, **ride**, sleep (pas `run` ni `mount`). Ailes : les 12 états. Queues : les 10 états hors `attack` et `hurt`. Pièces discrètes (tête, épaules, armes, auras) : seulement les états utiles.

Familier vivant (états `pet_`) : `categories/familiers.md`. Effet de téléportation (`charge`, `depart`, `arrivee`) : `categories/effets.md`.

## Échantillonnage

- Écrire les courbes en Python, échantillonner à 6–10 keyframes/s, puis laisser `optimize_bbmodel.py` simplifier (RDP, tolérance 0,3–1°).
- Durées : idle 8 s, fly 2,4 s, glide 3,6 s, walk 1,6 s, run 1,0 s, sneak/sleep/mount 3–4 s, attack/hurt 0,8 s.
