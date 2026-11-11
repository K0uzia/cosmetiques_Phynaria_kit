# Armes à pression et platines anciennes (skins d'arc, d'arbalète, armes de tir mécaniques)

Fiche écrite le 2026-11-08 pour `skin_arc_steampunk` (« Pistolet à vapeur »). Sujet : comment une arme à air ou à vapeur stocke et lâche sa pression, et comment s'arme une platine ancienne, pour que chaque étape d'un skin d'arc ou d'arbalète ait une cause mécanique lisible.

## Ce qu'il faut savoir

- **Réservoir** : les fusils à air du XVIIIe siècle gardaient l'air comprimé dans un réservoir de métal (souvent la crosse), rempli à la pompe à étrier (environ 1 500 coups pour 55 bar). Une charge donne une trentaine de tirs : à chaque tir, une petite part de la pression part, la suivante est plus faible. Joints de cuir à garder humides (sinon fuite).
- **Platine à deux crans** : le chien a un **demi-cran** (sûreté : la détente ne le fait pas tomber) puis un **cran d'armé** (second déclic) ; la détente libère la gâchette, le chien tombe et frappe. Deux clics distincts, puis une chute sèche : le rythme parfait pour trois étapes de bande.
- **Lecture de la pression** : manomètre à tube (aiguille qui monte par à-coups, zone rouge au maximum) ; soupape de sûreté qui tremble puis lâche quand la pression dépasse.
- **Après le tir** : le canon recule, le gaz sort d'un coup par la bouche puis s'élève et se dissipe (jamais il ne retombe).

## Traduction dans le mod

| Moment réel | Skin d'arc (guide 14) |
|---|---|
| Arme au repos, chien abattu, pression basse | étape `repos` ; `item_idle` : la pression remonte par crans, la soupape lâche de petites bouffées |
| Demi-cran, puis armé, pression qui monte | `bande_1` (demi-cran, aiguille au milieu, projectile chargé), `bande_2` (armé, aiguille haute) |
| Pression au maximum, prêt | `bande_3` : aiguille dans le rouge, lentille-témoin allumée (`_e`) ; `item_use` : la soupape vibre et fuit (`q.use_progress`) |
| Détente : chute du chien, décharge | `event_release` : chien qui tombe, recul sur ressort, jet `trans_` + `emit_mc_poof`/`white_smoke`, un son |
| Arme qui arrive en main | `event_select` : canon qui coulisse en place, tour d'essai de l'aiguille, sans son |

Repère de l'arc : la flèche de `bow_pulling_*.png` va du bas à droite vers le haut à gauche, la poignée de l'arc est vers (5, 10) ; la main tient l'objet vers (5, 10, 7) (inverse de `objet.matrice_main`) ; en visée, la branche basse de l'arc pointe vers le bas (une crosse de pistolet s'y place).

## Sources

- Fusil à air à réservoir (pression, nombre de tirs, joints) : https://en.wikipedia.org/wiki/Girardoni_air_rifle , https://www.rockislandauction.com/riac-blog/girardoni-air-rifle
- Armes à air en général : https://en.wikipedia.org/wiki/Air_gun
- Platine à silex, demi-cran et cran d'armé : https://en.wikipedia.org/wiki/Flintlock_mechanism , https://science.howstuffworks.com/flintlock2.htm
