# Bug à corriger : le calque lumineux `_e` des cosmétiques clignote

Tu travailles sur le mod Phynaria Utilities (Minecraft 26.1.2, NeoForge). Corrige le rendu du calque lumineux `_e` des cosmétiques (section 5 bis du guide créateurs).

## Symptôme

Sur un cosmétique animé qui possède un calque `_e`, le rendu clignote en permanence, **sans shader comme avec shader**, même à l'arrêt et quasiment sans bouger la caméra. D'une image à l'autre, et parfois entre deux parties d'un même modèle, on observe l'un de ces trois états :

1. **Rendu normal sans lueur** : texture principale correctement éclairée, calque absent.
2. **Texture principale très sombre** : on ne voit presque plus que le calque, comme si la texture était remplacée par lui ou éclairée à zéro. Le fond du calque, censé s'ajouter très légèrement, ressort comme une couleur sombre et opaque sur les plumes.
3. **Rendu mixte** : une partie du modèle est normale et une autre sombre, ou seule une partie brille.

Attendu d'après le guide : le calque est dessiné par-dessus le cosmétique et **s'ajoute** à sa couleur, de façon stable à chaque image. Une zone noire ou transparente du calque ne change rien au rendu.

## Modèle de test

`aurelion_wings.bbmodel` (fourni) : 504 cubes, texture principale 512×512 `aurelion_wings.png` et calque `aurelion_wings_e.png` de même taille, embarqué en second. Aucune face n'est assignée au calque (`texture: 0` partout). Alpha 0 ou 255 uniquement. Le calque contient :
- un fond très sombre, autour de (40, 39, 35), sur toutes les plumes ;
- des lignes et des pointes plus claires ;
- un anneau vif (255, 220, 120) pour le halo.

Le même clignotement apparaît sur le halo, qui est **une seule plaque** sans chevauchement, et sur les ailes, qui ont plusieurs centaines de cubes. La géométrie du modèle n'explique donc pas le problème.

## Captures fournies

Ce sont des captures en jeu du même modèle, prises à quelques secondes d'intervalle :

| Capture | Shader | Ce qu'on voit |
|---|---|---|
| `2026-11-02_20.57.03` | non | État 2 : ailes presque noires, lignes claires, halo allumé |
| `2026-11-02_20.57.05` | non | État 3 : ailes normales, centre du dos sombre |
| `2026-11-02_20.58.56` | non | Halo très lumineux |
| `2026-11-02_20.58.59` | non | Même halo presque invisible, ailes sans lueur |
| `2026-11-02_20.40.49` | oui | Seule la petite paire d'ailes brille |
| `2026-11-02_20.40.50` | oui | Une seconde après : toute l'aile brille |

## Pistes à vérifier dans le code

Ce sont des hypothèses, aucune n'est confirmée. Cherche la vraie cause dans le code et ne suppose pas que l'une d'elles est juste.

1. **Partage d'état entre les deux passes** : lumière (lightmap, packed light), overlay ou couleur appliqués à la passe principale et modifiés par la passe `_e`, ce qui expliquerait une texture principale noire. Vérifier en particulier un tampon de sommets, une pose ou un objet réutilisés entre les passes ou entre les modèles.
2. **Ordre de soumission des passes** : ordre instable entre le type de rendu principal et le type `_e` (lots, tri, soumission différée de la version 26.1).
3. **Type de rendu du calque** : mélange réellement additif, pas d'écriture de profondeur, test de profondeur compatible avec une géométrie identique.
4. **Pose différente entre les passes** : temps d'animation ou interpolation (`partialTick`) recalculés pour la seconde passe, ce qui ferait échouer le test de profondeur par endroits. Calculer la pose une seule fois par image et par cosmétique, et la réutiliser.
5. **Précision de profondeur** : si la géométrie est bien identique, ajouter un léger décalage de profondeur à la passe `_e`.
6. **Plusieurs joueurs et plusieurs cosmétiques** : vérifier que l'état d'un cosmétique ne fuit pas vers le suivant, car un autre joueur portant un cosmétique était parfois présent.

## Critères de réussite

- Modèle de test porté, sans shader, joueur et caméra immobiles, pendant 60 s : aucun clignotement de la texture ni du calque.
- Même test en marchant, en volant, et avec un second joueur portant un cosmétique.
- Même test avec Iris et Complementary.
- Un calque entièrement noir ne change rien au rendu, et un modèle sans `_e` rend exactement comme avant.
- De nuit, le calque reste visible et s'ajoute à la texture.

Donne en retour la cause trouvée, le correctif et les tests réellement effectués. Mets à jour la section 5 bis du guide si le comportement change, notamment sa mention « pas encore vérifié avec un pack de shaders ».

## Demande annexe

Ajouter une variable Molang `query.is_boosting` (fusée active en élytres), pour déclencher exactement le battement d'ailes à la fusée, aujourd'hui approché par un seuil de vitesse.
