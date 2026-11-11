---
paths:
  - "cosmetiques/chapeaux/**"
---

# Tête (chapeaux, cornes, masques) — règles, avis et recettes

« Chapeau » = tout ce qui se porte sur la tête ou le visage. Point de départ : `gen_bandeau_abyssal.py`. Pas d'`attack` ni de `hurt` (pièce portée, `animation.md`).

Distances (détail : `.claude/references/procedures/remise-aux-regles.md`) : face intérieure à ≥ 4,62 px du centre de la tête (seconde couche du skin à 4,5) ; rien en porte-à-faux devant le visage ; une pièce posée sur le dessus de la tête touche à y ≥ 32,62 ; haut-de-forme et bord de chapeau : trou dans le bord, |x| + |z| ≥ 9,24 sur la face intérieure aux coins coupés.

## Avis de l'utilisateur

| Pièce | Avis | À retenir |
|---|---|---|
| `bandeau_abyssal` | « incroyable », position des cornes ensuite « niquel » | Référence pour le thème chasseur de démons : bandeau, regard vert, cornes, oreilles |
| `cornes_abyssales` (2026-11-08, remplace `bandeau_abyssal`, archivé : « bandeau à revoir », « fixette sur des couronnes et bandeau ») | pas encore vu en jeu | Mêmes cornes et oreilles ; bandeau remplacé par une meule de nodules au pied des cornes, des racines d'os **aplaties** soudées au crâne (des tubes octogonaux faisaient « pattes d'araignée » au rendu) et un demi-masque d'os en deux lobes au regard vert (plaque à part : clignement, plissé en `sneak`, allumé en dernier). Le dos d'une racine plate doit être clair et uni : un dégradé sombre aux bords la fait lire comme un fil |
| `masque_abyssal` | « sympa », « base réutilisable » | Hors de l'esprit chasseur de démons : ne pas le présenter comme répondant à ce thème |
| Ensemble Cuir v1 (en jeu, 2026-11-04) | « trop gothique, pas du tout BDSM », masque « trop Zorro », collier à problème | Rouge et noir + coutures rouges + clous pointus = gothique. Direction retenue : latex noir brillant, chrome, harnais de tête. Collier : dans `body` en haut du torse, pas dans `head` (bandeau sous le menton) |
| `haut_de_forme_steampunk` (refonte du 2026-11-08 : « mécanique revoir tout sauf aile et hibou ») | pas encore vu en jeu | Chapeau **posé** sur la tête (dessous du bord à y ≥ 32,62, jupe de feutre à 4,75 px qui cache le jour) : la calotte peut être ronde (16 pans) au lieu de l'octogone presque carré qu'imposaient les coins de la tête. Une seule machine logique (foyer → manomètre → cheminée et moteur → charnière des lunettes) ; lunettes qui basculent par l'avant du bord, loupes d'horloger. Inclinaisons du chapeau ≤ 3° (sinon le bord entre dans la seconde couche) |
| `capuche_kawaii` (2026-11-08, remplace `oreilles_kawaii`, archivées : « les trucs kawaii sont tous bof ») | pas encore vu en jeu | Oreilles seules = deux plaques pâles, blanches et minuscules en jeu. Une capuche donne la masse ronde et colorée : corps en **un seul superellipsoïde** (p = 3, boîte arrondie) découpé autour de la tête par transparence + doublure aux faces de la découpe (x, z = ±4,62, y 32,62) ; plusieurs bouffées pour le corps faisaient « sac de boules ». Bordure de nuage en petites bouffées crème autour du visage, qui reste dégagé |
| `casque_orage` (2026-11-08, remplace `couronne_orage`, archivée) | « fixette sur des couronnes et bandeau » ; pas encore vu en jeu | Varier les types de pièce de tête d'un ensemble à l'autre (casque, capuche, cornes, masque partiel…). Ailettes plates : les orienter à 30–40° de la paroi et les tailler larges (≥ 35 % de leur hauteur), sinon on ne voit que leur tranche de face comme de dos |
| `beret_patisserie` (2026-11-08, remplace `chapeau_patisserie`, archivé : « les trucs kawaii sont tous bof », « revois les têtes ») | pas encore vu en jeu | Pièce de tête = une vraie coiffe dont la matière est le dessert (béret dont la galette est une tartelette), pas un gâteau posé. Demi-fraises **couchées** en rosace vers une fraise centrale (debout, elles faisaient une couronne de pointes rouges). À hauteur des yeux on ne voit que la paroi : monter la garniture en dôme (≈ 2 fois la hauteur de la paroi). Paroi « tombée » sur un côté : cassures en marches au coin de la tête (zone ≥ 32,62), incliner plutôt la crête et le plateau |
| `ramure_givre` (2026-11-08, remplace `couronne_givre`, archivée : « fixette sur des couronnes et bandeau ») | pas encore vu en jeu | Bois de cerf en glace : merrain de 5 tronçons de prisme `trans_` à âme cyan, nœuds de givre opaques aux jointures, 6 andouillers pointus **dans le plan du front** (vers le haut, un peu en avant : lisibles de face), meule en rosette posée à y ≥ 32,66. Merrain trop fin et andouillers tournés vers l'avant (1er essai) : « deux brindilles » de face ; il faut un pivot court presque droit, puis un merrain qui part franchement vers l'extérieur (lyre) |

## Recettes

| Élément | À éviter (constaté en jeu) | À faire |
|---|---|---|
| Corne | Ancrée sur l'arête du front : base en porte-à-faux devant le visage | Ancrée sur le dessus de la tête, au-dessus des tempes (z ≈ −3 à +2) ; contrôler le profil |
| Sangles sur la tête (harnais, masque) | Sangles en cubes à 0,6 px de la tête : « giga mal fait » (cage de tubes). Décalque lisse à 32 texels/px : « c'est moche », dessin vectoriel plaqué sur un skin à 1 texel/px (mixels, guide de style Minecraft de Blockbench) (2026-11-04) | Pixel art à la résolution du skin : « trop Minecraft », hors du style du dépôt. Recette retenue : **proportions réelles** (sangle 2,5 cm = 1,2 px, boule 4 cm = 2 px), sangles en vrai volume (0,35 px) collées à la tête (face intérieure à 4,62), tournant aux arêtes, cuir verni HD à bords biseautés et coutures, quincaillerie lourde (anneaux en O épais, boucles à rouleau et passant, doubles rivets bombés) (`gen_masque_cuir.py`, `gen_harnais_tete_cuir.py`). Pas encore vu en jeu |
