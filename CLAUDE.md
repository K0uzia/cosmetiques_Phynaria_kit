# Cosmétiques Minecraft — génération de modèles .bbmodel

Ce dépôt génère des cosmétiques (ailes, chapeaux, sacs, auras, armes…) au format Blockbench `.bbmodel`
pour le mod de cosmétiques du serveur. Les modèles sont **toujours produits par script Python** (pas à la main),
pour pouvoir itérer, vérifier et optimiser de façon reproductible.

## Règles non négociables

1. **Ne jamais livrer un modèle sans l'avoir vérifié** avec `tools/verify_bbmodel.py` (limites du mod, boucles, superpositions, extension). Un modèle qui échoue la vérification n'est pas livré.
2. **Ne jamais livrer sans rendu de contrôle** dans la convention du mod (`MODCONV=1`), en 4 vues, sur au moins idle + fly + run + sneak. Regarder le rendu avant d'envoyer.
3. **Toujours passer par `tools/optimize_bbmodel.py`** avant livraison (keyframes simplifiées, JSON compact, PNG optimisé).
4. **Axes : `docs/guide-cosmetiques.md`, section 3.** Le jeu lit le `.bbmodel` comme la vue 3D de Blockbench ; seul l'export Bedrock inverse X et Y. Résumé dans `.claude/rules/animation.md`. En cas de doute sur une nouvelle version : `/bbmodel-calibrate`, ne pas deviner.
5. **Ne jamais reproduire un design protégé** (Tyrael/Diablo, personnages, logos). Proposer un design original dans le même esprit. Une référence fournie par l'utilisateur sert à cerner l'ambiance, pas à copier.
6. **`scale` et `position` fonctionnent dans le mod** (confirmé par le développeur : l'échec constaté venait de notre modèle de test, cause non identifiée). Les effets détachés du joueur (plumes qui tombent) passent par les groupes `particle_<nom>` et `emit_<nom>` (guide, section 5 ter).
7. Quand l'utilisateur donne une capture in-game, **la croire plutôt que le rendu**. Si les deux divergent, le renderer ou la convention est faux : corriger l'outil d'abord.

## Organisation

- `tools/` : renderer, optimiseur, vérificateur, `livrer.py` (vérifie, crée les aperçus, met à jour le livrable), Vestiaire, calibration. La vue 3D du Vestiaire (`tools/visionneuse.js`) reprend les calculs du renderer : après toute retouche de `render_bbmodel.py` (pose, Molang, transformations), reporter le changement et lancer `python tools/test_visionneuse.py`.
- `.claude/rules/` : règles par domaine (chargées automatiquement).
- `.claude/skills/` : procédures invocables (`/bbmodel-cosmetic`, `/bbmodel-animate`, `/bbmodel-verify`, `/bbmodel-calibrate`, `/bbmodel-retour-jeu`, `/bbmodel-serie`).
- `docs/` : guide officiel du mod (`guide-cosmetiques.md`, prime sur nos règles, ne pas le modifier), demandes au développeur (`dev/`), exemples (`exemples/`).
- `.claude/rules/retours-en-jeu.md` : ce que l'utilisateur a validé ou refusé et les recettes qui marchent, à lire en premier.
- `.claude/styles/<ensemble>.md` : fiches de style documentées (palette, matières, mouvement, idées, sources), à lire avant toute pièce de l'ensemble. En créer une pour chaque nouvel ensemble.
- `.claude/rules/fonctions-avancees.md` : groupes spéciaux (`add_`, `trans_`, `cam_`, `phys_`, `ctrl_`), reflets, particules Minecraft, couches, sons : résumé du guide et pièges.
- `ouvrir_vestiaire.bat` : catalogue local, mis à jour automatiquement. L'ensemble d'une pièce se déduit de son nom, et chaque ensemble appartient à un thème (`ENSEMBLES` dans `tools/gen_index.py`).
- `cosmetiques/<categorie>/<nom>/` : **un dossier par cosmétique**, avec tous ses `.bbmodel`. Catégories : `ailes`, `chapeaux` (tout ce qui se porte sur la tête ou le visage : chapeau, cornes, masque…), `queues`, `epaules`, `familiers`, `sacs`, `auras`, `armes`, `outils`, `blocs`.
- Contenu du dossier d'un cosmétique (`<nom>` en minuscules, sans espace ni accent) :
  - `gen_<nom>.py` : le générateur, qui écrit `<nom>.png` à côté de lui et sa sortie brute dans `.build/` (`os.chdir(os.path.dirname(os.path.abspath(__file__)))` en début de script) ;
  - `<nom>.bbmodel` + `<nom>.png` : le livrable optimisé et sa texture, **un seul fichier mis à jour sur place**, pas de nouveau fichier à chaque itération ;
  - `<nom>_<piece>.bbmodel` : les modèles associés (ex. `aurelion_feather.bbmodel`) ;
  - `apercu/` : `planche.png` et `animations.gif`, chacun regroupant toutes les animations, écrasés à chaque mise à jour ;
  - `.build/` : fichiers intermédiaires, jamais livrés.

## Limites du mod (version courante)

| Limite | Valeur |
|---|---|
| Fichier importé / stocké / envoyé compressé | 16 Mo / 8 Mo / 1 000 Ko |
| Cosmétiques portés en même temps | 3 |
| Cubes (pas de mesh) | 8 192 |
| Groupes / profondeur | 2 048 / 64 |
| Distance au joueur (par axe) | 64 px |
| Rotation d'un cube ou d'un groupe | ±360° (pas de limite sur les keyframes, voir `docs/guide-cosmetiques.md`, qui prime sur ces règles) |
| Rotation d'une face | multiple de 90° |
| Inflate | ±8 |
| Nom d'un groupe | 64 caractères (coupé au-delà) |
| Texture | 1 principale (+ 1 `_e`, 1 `_r` de même taille, 1 `_m` ≤ 256²), PNG ≤ 512×512, embarquée ; semi-transparence seulement dans les groupes `trans_` ; images empilées pour une texture animée |
| Résolution UV | 4 096 max |
| Animations / keyframes | 16 / 32 768 |
| Durée / nom d'une animation | 600 s (10 min) / 64 caractères |
| Molang | 512 caractères, 16 instructions par clé, 64 variables |
| Canaux d'animation | rotation, position, scale |
| Émissif | calque `<texture>_e.png` embarqué, jamais assigné aux faces, ou option « Lumineux » du staff. **Calque réactivé le 2026-11-03 (correctif du clignotement annoncé côté mod), non encore vérifié en jeu** |
| Particules | 4 sortes modélisées + 4 de Minecraft (`emit_mc_`), 32 points `emit_`, 64 à 256 par joueur (`docs/guide-cosmetiques.md`, section 5 ter) |
| Sons | 32 par animation, noms de sons Minecraft |

## Workflow standard

1. Cadrer : type, ambiance, états à animer, contraintes (voir `/bbmodel-cosmetic`).
2. Écrire/adapter le générateur (textures peintes → géométrie → animations).
3. Avec `D=cosmetiques/<categorie>/x` : `python $D/gen_x.py` → `python tools/optimize_bbmodel.py $D/.build/x_brut.bbmodel $D/.build/x_opt.bbmodel`.
4. `python tools/verify_bbmodel.py $D/.build/x_opt.bbmodel` et rendus de contrôle (`MODCONV=1 ANIM=<état> T=<t> python tools/render_bbmodel.py …`). Regarder et corriger le générateur.
5. `python tools/livrer.py $D` : revérifie, crée `apercu/`, met à jour `$D/x.bbmodel` et le Vestiaire. Regarder `apercu/planche.png`, puis dire ce qui est à vérifier en jeu.
