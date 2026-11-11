# Règles — l'essentiel (toute pièce)

Leçons transversales tirées des retours en jeu. Avis détaillés et recettes : `retours-en-jeu.md` (index) et `categories/<catégorie>.md`. Ajouter chaque leçon confirmée par une capture ou un avis de l'utilisateur, et supprimer ce qui se révèle faux.

## Axes

`docs/guide-cosmetiques.md` prime. Le jeu lit les rotations telles quelles, comme la vue 3D de Blockbench ; seul l'export Bedrock inverse X et Y. Le renderer `tools/render_bbmodel.py` les reproduit avec `MODCONV=1`.

Le joueur regarde −Z, sa droite est +X. Valeurs de keyframe :
- **+X** : le haut du groupe bascule vers l'arrière.
- **+Y** : le côté droit (+X) avance.
- **+Z** : le côté droit monte, donc le côté gauche descend.

Canal `position` : +Y monte, +X va vers la droite du joueur (guide, section 3). Dos du joueur = **+Z**.

## Le rendu ne suffit pas

- Le renderer ne montre ni le shader, ni l'éclairage de nuit, ni l'émissif, ni les particules, ni le suivi de tête, ni le balancement des membres. Un rendu propre et un vérificateur vert ne prouvent pas le résultat en jeu : ne jamais l'affirmer ; tout ce qui n'est pas prouvé en jeu se présente comme à vérifier, avec une cause « mesurée » ou « supposée ».
- **Juger une pièce (surtout un effet) avec le mode « comme en jeu »** (Vestiaire, `apercu/jeu.png`), jamais avec le rendu studio : fond sombre, cadrage serré et lissage y rendent beaux des additifs ternes et des traits fins que le jeu pâlit (mipmaps depuis le 2026-11-08 : un trait fin s'adoucit au loin au lieu de disparaître ; `.claude/references/mod/rendu-en-jeu.md`).
- Contrôler aussi : de face à hauteur des yeux, par la tranche, de dessous, de profil, et de nuit dès qu'il y a du calque `_e`.
- Ne pas présenter un constat comme « vérifié » s'il vient d'un seul test de notre côté : `scale` et `position` ont été déclarés ignorés à tort.
- Lire les captures et le guide avant de coder. « Je les veux plates » a d'abord été compris à l'envers : reformuler chaque demande ambiguë avant de lancer une refonte.

## Méthode de travail

- **Sons rares** : « infernal » quand chaque mouvement siffle, à répétition ; puis « encore un peu trop fréquents » avec un son par boucle de 8 s. Règle : aucun son dans les états en mouvement ni dans les `overlay_` ; au repos, un seul, et seulement si la boucle dure 20 s ou plus ; un seul à un événement (équipement) et à l'attaque, à l'attaque seulement pour une arme ; aucun à la blessure (`tools/sons.py`). Penser que 3 cosmétiques peuvent sonner ensemble. Appliquer `tools/sons.py` ; noms et format : `fonctions-avancees.md`. Les sons embarqués (2026-11-05) suivent la même règle.
- **Lumière** : « je ne vois aucune lumière sur le set » avec des calques `_e` faibles (presque rien au-dessus de 120) et des éclats diffus. Il faut des **sources nettes et logiques** (lentilles, cadrans, fentes de foyer, filets de verre ambré sur les nervures), vives (150 à 225) sur de petites surfaces, visibles de face comme de dos. Contrôler avec `NUIT=1` (rendu de nuit) et le panneau « De nuit » de la livraison.
- **Logique physique** : un appareil qui a un rotor ne vole pas en battant des ailes (hibou). Chaque mouvement doit avoir une cause mécanique plausible : le rotor porte, les ailes stabilisent, la vapeur sort après la pression.
- Particules qui tombent et se posent, comme les plumes des ailes de Bérénice : **sur les ailes seulement**, jamais sur la tête, la queue ou les autres pièces, sauf demande explicite (consigne de l'utilisateur, 2026-11-03).
- Et seulement pour ce qui tombe vraiment (plumes, pétales, feuilles, éclats). **La vapeur ne retombe jamais en nuage** : elle jaillit et monte (jet modélisé, `emit_mc_white_smoke`). Nuage de vapeur qui tombait des `ailes_steampunk` : « pas logique » (2026-11-03). Vapeur, fumée, étincelles qui montent ou se dissipent : partout.
- Un retour porte souvent sur une seule pièce : citer ce qui est validé et ne doit pas bouger.
- Point de départ des générateurs : `gen_ailes_abyssales.py` pour os et membrane, `gen_ailes_berenice.py` pour des plumes, `gen_bandeau_abyssal.py` pour la tête. Jamais `tools/example_wings_generator.py`, qui contient les défauts corrigés depuis.
- Pièce existante livrée avant les dernières règles : `.claude/references/procedures/remise-aux-regles.md`.

## Livraison : le message

- Ce qui a changé par rapport à la version précédente, en réponse aux retours (point par point).
- Chiffres : cubes, groupes, poids brut/compressé, extension max.
- Familier vivant : le dire (mode, distance), et que les aperçus le montrent porté à l'origine ; le suivi se juge en jeu (`/cosmetique apercu`).
- **Ce qu'il faut vérifier en jeu** (2–3 points max) et ce qui est connu comme non faisable côté modèle, avec la raison.
- Ne jamais affirmer qu'un rendu correspondra en jeu : dire ce qui est mesuré, ce qui est supposé et ce qui reste à voir.
- Lister les fonctions avancées utilisées (dans le docstring du générateur aussi), avec ce qui se juge seulement en jeu (`/cosmetique apercu`).

## Quand l'utilisateur renvoie une capture

- La capture a raison. Diagnostiquer précisément (quel axe, quel état) avant de toucher au code.
- Si le diagnostic est une inversion d'axe : un seul signe dans `mirror()`, pas une refonte.
- Si plusieurs retours à la fois : les lister, traiter chacun, et dire lesquels sont hors de portée du modèle (→ `docs/dev/demandes_mod.md`).

## Pas de « v+1 » cosmétique

Avant de relancer une génération complète, se demander : le problème est-il dans la **convention** (→ calibrer), dans l'**outil** (renderer/vérificateur), ou dans le **design** ? Ne refaire le design que si c'est le design.
