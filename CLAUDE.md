# Cosmétiques Minecraft — génération de modèles .bbmodel

Ce dépôt génère des cosmétiques (ailes, chapeaux, sacs, auras, armes…) au format Blockbench `.bbmodel`
pour le mod de cosmétiques du serveur. Les modèles sont **toujours produits par script Python** (pas à la main),
pour pouvoir itérer, vérifier et optimiser de façon reproductible.

## Règles non négociables

1. **Ne jamais livrer un modèle sans l'avoir vérifié** avec `tools/verify_bbmodel.py` (limites du mod, boucles, superpositions, extension). Un modèle qui échoue la vérification n'est pas livré.
2. **Ne jamais livrer sans rendu de contrôle** dans la convention du mod (`MODCONV=1`), en 4 vues, sur au moins idle + fly + run + sneak. Regarder le rendu avant d'envoyer.
3. **Toujours passer par `tools/optimize_bbmodel.py`** avant livraison (keyframes simplifiées, JSON compact, PNG optimisé).
4. **Convention d'axes = celle mesurée par calibration**, jamais celle de Blockbench. Voir `.claude/rules/animation.md`. En cas de doute sur un nouveau mod/version : refaire la calibration (`/bbmodel-calibrate`), ne pas deviner.
5. **Ne jamais reproduire un design protégé** (Tyrael/Diablo, personnages, logos). Proposer un design original dans le même esprit. Une référence fournie par l'utilisateur sert à cerner l'ambiance, pas à copier.
6. **`scale` et `position` fonctionnent dans le mod** (confirmé par le développeur : l'échec constaté venait de notre modèle de test, cause non identifiée). Sens de `position` à calibrer avant tout usage sur X ou Z. Les effets détachés du joueur (plumes qui tombent) passent par les groupes `particle_<nom>` et `emit_<nom>` (guide, section 5 ter).
7. Quand l'utilisateur donne une capture in-game, **la croire plutôt que le rendu**. Si les deux divergent, le renderer ou la convention est faux : corriger l'outil d'abord.

## Organisation

- `tools/` : renderer (`render_bbmodel.py`), optimiseur, vérificateur, modèle de calibration, générateur d'exemple.
- `.claude/rules/` : règles par domaine (chargées automatiquement).
- `.claude/skills/` : procédures invocables (`/bbmodel-cosmetic`, `/bbmodel-animate`, `/bbmodel-verify`, `/bbmodel-calibrate`, `/bbmodel-retour-jeu`).
- `docs/guide-cosmetiques.md` : guide officiel du mod, prime sur nos règles. `.claude/rules/retours-en-jeu.md` : leçons des retours en jeu, à lire en premier.
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
| Cubes (pas de mesh) | 8 192 |
| Groupes / profondeur | 2 048 / 64 |
| Distance au joueur (par axe) | 64 px |
| Rotation d'un cube ou d'un groupe | ±360° (pas de limite sur les keyframes, voir `docs/guide-cosmetiques.md`, qui prime sur ces règles) |
| Rotation d'une face | multiple de 90° |
| Inflate | ±8 |
| Nom d'un groupe | 64 caractères (coupé au-delà) |
| Texture | 1 principale (+ 1 calque `_e` facultatif), PNG ≤ 512×512, embarquée, sans semi-transparence |
| Résolution UV | 4 096 max |
| Animations / keyframes | 16 / 32 768 |
| Durée / nom d'une animation | 600 s (10 min) / 64 caractères |
| Molang | 256 caractères, complexité limitée |
| Canaux d'animation | rotation, position, scale |
| Émissif | calque `<texture>_e.png` embarqué, jamais assigné aux faces, ou option « Lumineux » réglée par le staff (non vérifié sous shader par le mod) |
| Particules | 4 sortes, 32 points `emit_`, 64 par joueur (`docs/guide-cosmetiques.md`, section 5 ter) |

## Workflow standard

1. Cadrer : type, ambiance, états à animer, contraintes (voir `/bbmodel-cosmetic`).
2. Écrire/adapter le générateur (textures peintes → géométrie → animations).
3. Avec `D=cosmetiques/<categorie>/x` : `python3 $D/gen_x.py` → `python3 tools/optimize_bbmodel.py $D/.build/x_brut.bbmodel $D/.build/x_opt.bbmodel`.
4. `python3 tools/verify_bbmodel.py $D/.build/x_opt.bbmodel` → doit être tout vert.
5. `MODCONV=1 ANIM=<état> T=<t> python3 tools/render_bbmodel.py $D/.build/x_opt.bbmodel out.png 1.5` pour idle, fly, run, sneak. Regarder.
6. Seulement si tout est bon : copier `.build/x_opt.bbmodel` sur `$D/x.bbmodel`, mettre à jour `$D/apercu/` (planche + GIF uniques), le Vestiaire se met à jour tout seul si `ouvrir_vestiaire.bat` tourne, sinon relancer `python tools/gen_index.py`. Dire ce qui est à vérifier en jeu.
