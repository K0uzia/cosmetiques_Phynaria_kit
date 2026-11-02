# Mod cosmétiques — fonctionnalités manquantes constatées

> **Statut (retour du développeur, nov. 2026)** : l'ensemble des demandes est traité. Le point 1 fonctionnait déjà : le problème venait de notre modèle. Convention de rotation, émissif, particules et rapport d'import sont décrits dans `guide-cosmetiques.md`, qui fait référence.

Contexte : création d'ailes animées (.bbmodel, format Blockbench « free », 512×512, 12 animations). Les points ci-dessous ont été constatés en jeu ou par un modèle de calibration dédié (3 barres colorées X/Y/Z + 5 animations d'1 s).

## 1. Animations — canaux non supportés (constat erroné : déjà fonctionnel, le problème venait de notre modèle)

| Canal Blockbench | Constat | Impact |
|---|---|---|
| `scale` (échelle) | Aucun effet (test : un cube passant de 1 à 0 sur 1 s ne bouge pas) | Impossible de faire apparaître/disparaître un élément (plumes qui tombent, effets qui se dissolvent, halo qui pulse) |
| `position` (translation) | Aucun effet (test : +8 px en Y sur 1 s, rien) | Impossible de faire flotter un halo, dériver des particules, décaler une pièce |

Demande : lire et appliquer les keyframes `scale` et `position` des bones, comme `rotation`. Ce sont les trois canaux standards d'un `.bbmodel`.

## 2. Convention des rotations — à documenter

Constat : le mod applique les valeurs de rotation telles quelles. Blockbench, lui, inverse X et Y à l'affichage (convention Bedrock). Résultat : un modèle qui a l'air correct dans Blockbench est inversé en jeu, et inversement.

Mesuré en jeu : X+ = le haut du bone bascule vers l'arrière, Y+ = pivote vers l'arrière (côté gauche), Z+ = la pointe monte (côté gauche). Les modèles livrés sont construits dans cette convention.

Demande (au choix) :
- soit appliquer la convention Blockbench/Bedrock (négation de X et Y) pour que ce qu'on voit dans Blockbench soit ce qu'on voit en jeu ;
- soit documenter clairement la convention actuelle pour les créateurs.

## 3. Rendu émissif / fullbright (bloquant pour l'effet « lumineux »)

Constat : avec Complementary (ou tout shader), rien ne brille. Un `.bbmodel` ne peut pas porter d'information d'émission : c'est au rendu de la déclarer.

Demande : au moins une des deux options par cosmétique
- un flag « fullbright / émissif » (lightmap forcée à 15, rendu dans une couche compatible shaders : entity emissive ou équivalent) ;
- le chargement d'une texture émissive `<texture>_e.png` (même convention qu'OptiFine/Iris : la luminance de `_e` = intensité d'émission).

Idéalement les deux, avec le flag réglable à l'import.

## 4. Entités spawnables pour effets (plumes qui tombent)

Constat : des éléments détachés du joueur (plumes qui tombent et se posent au sol) ne peuvent pas être dans le modèle : ils suivent le joueur. Et sans `scale`/`position`, ils ne peuvent pas non plus être animés dans le modèle.

Demande : un système d'« émetteur » par cosmétique :
- un mini-modèle `.bbmodel` associé (ex. `aurelion_feather.bbmodel`) ;
- des points d'émission définis par nom de bone (ex. `p0_l`, `p7_r` = pointes des primaires) ;
- paramètres : fréquence, états concernés (immobile → se posent au sol X s puis disparaissent ; vol → tombent et disparaissent en l'air), durée de vie, gravité, animation jouée (`tumble` en chute, `rest` au sol) ;
- raycast vers le bas pour choisir « pose au sol » ou « disparition en l'air ».

## 5. Transparence et z-fighting

Constat : des plans sans épaisseur (0) ou superposés exactement clignotent en noir sous shader. Contournement côté modèle : épaisseur 0,3–0,5 px et décalage de profondeur par élément.

Demande : documenter cette contrainte ; si possible, appliquer un léger polygon offset ou un tri par profondeur sur les faces `cutout` du cosmétique.

## 6. Profil d'import / retours d'erreur

Constats :
- un modèle de 3,4 Mo passe, mais on ne sait pas quelle partie pèse (texture, keyframes, géométrie) ;
- pas de retour si une animation est ignorée (canal non supporté, nom trop long, etc.).

Demande : à l'import, afficher un résumé (cubes, groupes, profondeur, keyframes par canal, taille texture, taille compressée) et un avertissement explicite pour chaque élément ignoré (« 412 keyframes `scale` ignorées »).

## 3 bis. Calque `_e` instable (bloquant pour l'effet lumineux)

Constat sur `aurelion_wings`, même fichier et même état, avec shader : le calque s'affiche ou non d'une capture à l'autre, à une seconde d'écart et quasiment sans changer d'angle. Captures : `2026-11-02_20.40.49` (seule la petite paire brille) et `20.40.50` (tout brille) ; le halo fait de même sur `20.37.52` (éteint) et `20.37.56` (allumé).

Le modèle ne peut pas choisir quels groupes s'allument d'une image à l'autre, donc la cause semble être au rendu. Pistes supposées : passe `_e` avec une pose d'animation ou un temps légèrement différents de la passe principale, ce qui ferait échouer le test de profondeur ; ou ordre des passes sous Iris.

Test sans shader (`20.57.03`, `20.57.05`, `20.58.56`, `20.58.59`) : le clignotement continue, et les ailes peuvent devenir presque noires. Le shader n'est donc pas la cause. Texte complet pour le développeur : `bug_emissif_pour_dev.md`.

## 7. Mineur / confort

- **Détection de la propulsion** : ajouter une variable Molang `query.is_boosting` (fusée active en élytres), ou `query.acceleration`. Aujourd'hui, seul un seuil de vitesse permet d'approcher un battement à la fusée, ce qui reste imprécis.

- **Limite de distance 64 px** (par axe) : préciser si elle est mesurée depuis les pieds (0,0,0) ou le centre du joueur. Ça change l'envergure possible.
- **Limite de rotation ±360°** : préciser si elle s'applique aussi aux keyframes d'animation, ou seulement aux rotations de base des cubes et des groupes. Un halo qui tourne en continu dépasse 360° dès qu'il fait plus d'un tour par boucle.
- **Interpolation** : confirmer que `catmullrom` est interprété (sinon tout est joué en linéaire et les boucles sont moins fluides).
- **Molang** : confirmer les `query.*` disponibles (`anim_time`, `life_time`, vitesse horizontale/verticale, santé…). Avec la vitesse, on peut moduler la fréquence du battement ; avec `life_time`, rendre l'idle apériodique.
- **Meshes Blockbench** (format « generic »/mesh) : non supportés. Pas indispensable, mais ce serait le seul moyen d'avoir des formes vraiment courbes.
- **Textures multiples** : une seule texture embarquée. Une texture séparée (`_e`, normal map) serait utile pour les shaders.
