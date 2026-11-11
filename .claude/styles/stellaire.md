# Style — Stellaire (thème Cosmique, ensemble « Les Portes stellaires »)

Entrée `Stellaire` de `cosmetiques/ensembles.json` : « Bien avant Phynaria, un peuple de bâtisseurs disparu reliait les étoiles par des passages de métal et de lumière. Leurs anneaux dorés dorment encore sous certaines ruines, leurs faisceaux traversent parfois le ciel, et leurs grandes portes s'éveillent quand on sait composer la bonne adresse. » Pièces : `effet_stellaire_anneaux` (validé), `effet_stellaire_rayon` (validé v2), `effet_stellaire_porte` (pièce phare, 2026-11-07). Nom des pièces : `<type>_stellaire_<objet>`.

## Esprit

Technologie ancienne de bâtisseurs disparus : du **métal doré** et de la **pierre** usée, gravés de glyphes inventés (cercles, points en constellation, barres, chevrons), qui s'éveillent par une **lumière bleue froide** et des **lentilles d'or ambré**. Mécanique lourde et précise (anneaux qui tournent, crans qui se verrouillent), jamais magique « en volutes ». Le voyage a le froid de l'espace : bleu pâle, blanc, éclats nets.

## Palette

| Matière | Clair | Base | Ombre | Usage |
|---|---|---|---|---|
| Or des bâtisseurs | (255, 222, 150) | (204, 146, 64) | (62, 34, 10) | anneaux, crans, montures |
| Pierre ancienne | (150, 150, 158) | (104, 104, 114) | (46, 46, 54) | cadre de la porte |
| Lumière d'or (lentilles, liserés) | (255, 240, 200) | (255, 180, 80) | (120, 60, 10) | `_e`, `add_` des crans |
| Lumière stellaire | (230, 251, 255) | (120, 200, 255) | (26, 64, 140) | rayon, eau de la porte, glyphes `_e` |

## Recettes validées (en jeu)

- Anneaux en vrais volumes de 64 segments, frise gravée sur la face extérieure, liseré `_e` + gaine `add_` (`effet_stellaire_anneaux`).
- Jamais de gaine `trans_` autour d'une lumière `add_` : elle la cache ; faisceau `add_` qui sature, silhouette `trans_` bleue + `_e` (`effet_stellaire_rayon` v2).
- Courbes lisses par phase, 30 clés/s ; sons embarqués originaux (`tools/synthe.py`), rien pendant la charge (exception demandée pour la porte : clac à chaque cran + grondement). **Compte à rebours du serveur = 3 s** : toute la charge se joue en ≈ 3 s.

## Particules

Éclats de lumière bleue (modélisés, ≥ 0,5 px), étincelles d'or au contact du métal, `emit_mc_electric_spark`, `emit_mc_wax_on`, `emit_mc_glow` ; jamais d'`end_rod`.

## Sources

Fiches `.claude/references/effets/anneaux-transport.md`, `rayon-teleportation.md`, `porte-etoiles.md`.
