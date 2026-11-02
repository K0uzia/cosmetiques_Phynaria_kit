# Règles — leçons des retours en jeu

Erreurs déjà commises sur de vrais cosmétiques. Les appliquer **dès la première version**. Ajouter ici chaque nouvelle leçon confirmée par une capture, avec ce qui a marché, et supprimer ce qui se révèle faux.

## Le rendu ne suffit pas

- Le renderer ne montre ni le shader, ni l'éclairage de nuit, ni l'émissif, ni les particules, ni le suivi de tête. Un rendu propre et un vérificateur vert ne prouvent pas le résultat en jeu : ne jamais l'affirmer.
- Contrôler aussi : de face à hauteur des yeux, par la tranche, de dessous, et de nuit dès qu'il y a du calque `_e`.
- Ne pas reprendre un constat comme « vérifié » s'il vient d'un seul test de notre côté : `scale` et `position` ont été déclarés ignorés à tort.
- Lire les captures et le guide avant de coder ; relire le message de l'utilisateur en cas de doute. « Fais-les plates » a été compris comme « elles sont plates » : reformuler chaque demande ambiguë avant de lancer une refonte.

## Recettes validées ou à éviter

| Élément | À éviter (constaté en jeu) | À faire |
|---|---|---|
| Plume d'aile | Plaque seule : « tas de feuilles » par la tranche. Cubes pleins seuls : « trop carré », marches | Peau ronde découpée par alpha autour d'une âme pleine plus étroite (validé pour la rondeur) |
| Os de l'aile | Barres droites apparentes, blocs à la base | Volume effilé, couvert d'écailles rondes dessus et dessous |
| Anneau, halo | Segments décalés : pointillés. Segments chevauchés : créneaux sombres sous `_e` | Une seule plaque, anneau découpé par alpha, même forme plus étroite dans `_e` (à confirmer en jeu) |
| Particule | Barreaux : bâtons. Base étranglée dans la texture et raccords à ~10° : « bonbon » (cause supposée). Plaque de 0,3 px : deux couches | Une seule plaque, courbure peinte dans l'image, face `up` seule, loin du sol (validé en jeu). Éviter les sections (l'image coupée se retourne) et les 0,06 px (fragments à distance) |
| Lueur | Lueur vive sur un dégradé : orange violent, instable | Fines lignes lumineuses et fond additif très sombre ; rien de vif hors du point focal |
| Couleur de nuit | Aile sans `_e` : saumon et mate sous éclairage chaud | Base plus blanche et fond `_e` léger, ou option « Lumineux » du staff |

## Validé en jeu

- Style à reprendre : `ailes_abyssales` (« incroyable », 3D et textures). Os octogonaux effilés et courbes, membrane découpée par alpha, peinte d'un seul tenant, veines contrastées. Partir de `gen_ailes_abyssales.py` pour un cosmétique à os et membrane.
- `masque_abyssal` : « sympa » et à conserver comme base réutilisable pour des masques (plaques d'os, orbites ouvertes, cornes segmentées, sangles), mais jugé hors de l'esprit recherché pour le thème chasseur de démons. Ne pas le présenter comme répondant à ce thème.
- `bandeau_abyssal` : « incroyable », bon esprit pour le thème chasseur de démons. Cornes à ancrer sur le dessus de la tête, au-dessus des tempes (z ≈ −3 à +2), pas sur l'arête du front : contrôler le profil.
- Plume peau + âme : rondeur et forme des ailes.
- Battement à la fusée en `glide` par seuil de vitesse (V0 = 26, DV = 5), avec exclusion des piqués.
- Plume-particule : une seule plaque, courbure peinte dans l'image, face `up` seule, au-dessus du sol.
- Halo en une plaque : plus de créneaux.
- Calque `_e` : il clignote aussi sans shader, et peut assombrir la texture. Bug à traiter côté mod (`docs/bug_emissif_pour_dev.md`) : ne pas retoucher le modèle pour ce symptôme avant son correctif.

## Orientation selon l'état

- En vol créatif, le joueur reste debout : pas de plan d'aile à 90°, il se voit par la tranche. Bascule d'environ 40°.
- En élytres et en nage, le corps est couché et le cosmétique le suit : ailes presque dans le plan du dos. Déduit du fonctionnement du mod.

## Méthode de travail

- Le fichier livrable reste unique, et les aperçus aussi : une planche PNG et un GIF regroupant toutes les animations.
- Un retour porte souvent sur une seule pièce : garder explicitement ce que l'utilisateur a validé.
- Pour un nouveau cosmétique d'ailes, partir de `gen_aurelion_wings.py`, pas de `tools/example_wings_generator.py`, qui contient les défauts corrigés depuis.
- Tout ce qui n'est pas prouvé en jeu se présente comme à vérifier, avec une cause « mesurée » ou « supposée ».
