# Cosmétiques Minecraft — génération de modèles .bbmodel

Ce dépôt génère des cosmétiques (ailes, chapeaux, sacs, auras, armes…) au format Blockbench `.bbmodel`
pour le mod de cosmétiques du serveur. Les modèles sont **toujours produits par script Python** (pas à la main),
pour pouvoir itérer, vérifier et optimiser de façon reproductible.

## Règles non négociables

1. **Ne jamais livrer un modèle sans l'avoir vérifié** avec `tools/verify_bbmodel.py` (limites du mod, boucles, superpositions, extension). Un modèle qui échoue la vérification n'est pas livré.
2. **Ne jamais livrer sans rendu de contrôle** dans la convention du mod (`MODCONV=1`), en 4 vues, sur au moins idle + fly + run + sneak. Regarder le rendu avant d'envoyer.
3. **Toujours passer par `tools/optimize_bbmodel.py`** avant livraison (keyframes simplifiées, JSON compact, PNG optimisé).
4. **Axes : `docs/guide-cosmetiques.md`, section 3.** Le jeu lit le `.bbmodel` comme la vue 3D de Blockbench ; seul l'export Bedrock inverse X et Y. Résumé dans `.claude/rules/essentiel.md` (Axes). En cas de doute sur une nouvelle version : `/bbmodel-calibrate`, ne pas deviner.
5. **Ne jamais reproduire un design protégé** ni s'en « inspirer de près » (Tyrael/Diablo, personnages, logos, armes de jeux). Proposer un design original dans le même esprit. Une référence fournie par l'utilisateur sert à cerner l'ambiance, pas à copier. **Approche par analogie** (2026-11-06) : étudier vraiment l'inspiration (déroulé, formes, couleurs, timing, sons), la traduire en spécifications techniques d'une version 100 % originale, et ne jamais citer l'œuvre dans les fiches, générateurs, fiches de cosmétique ou rapports (`/bbmodel-cosmetic`, 1 bis).
6. **`scale` et `position` fonctionnent dans le mod** (confirmé par le développeur : l'échec constaté venait de notre modèle de test, cause non identifiée). Effets détachés du joueur (plumes qui tombent) : groupes `particle_<nom>` et `emit_<nom>` (`.claude/rules/animation.md`, Canaux).
7. Quand l'utilisateur donne une capture in-game, **la croire plutôt que le rendu**. Si les deux divergent, le renderer ou la convention est faux : corriger l'outil d'abord.

## Limites du mod (version courante)

| Limite | Valeur |
|---|---|
| Fichier importé / nettoyé et compressé par le serveur | 16 Mo / 1 000 Ko |
| Cosmétiques portés en même temps | 3 (+ 1 skin d'objet par type, 12 types, guide 14) |
| Familiers vivants (bloc `familier`) | 1 par joueur (le premier porté ; les autres sont portés sur le joueur) |
| Effet de téléportation | 1 par joueur, en plus des cosmétiques ; `depart` et `arrivee` 5 s au plus ; vu à 64 blocs (guide 15) |
| Fiche (`phynaria.fiche`) | nom, ensemble, rareté : 40, 40, 24 caractères ; description 300, lore 500 ; boutique : 160 affichés |
| Cubes (pas de mesh) | 8 192 |
| Groupes / profondeur | 2 048 / 64 |
| Distance à l'origine (par axe, cubes et pivots, **au repos**) | 128 px (porté, familier), 320 px (effet de téléportation), 64 px (skin d'objet) ; clé `position` ≤ 320 px, `scale` ≤ 16 fois ; extension animée libre (guide 3, 7) |
| Rotation d'un cube ou d'un groupe | ±360° (pas de limite sur les keyframes, voir `docs/guide-cosmetiques.md`, qui prime sur ces règles) |
| Rotation d'une face | multiple de 90° |
| Inflate | ±8 |
| Nom d'un groupe | 64 caractères (coupé au-delà) |
| Texture | 1 principale (+ 1 `_e`, 1 `_r` de même taille, 1 `_m` ≤ 256²), PNG ≤ 512×512, embarquée ; semi-transparence seulement dans les groupes `trans_` et `add_` (`add_` et `_e` : couleur × alpha, guide du 2026-11-08) ; images empilées pour une texture animée (64 images, 1 048 576 pixels en tout) |
| Résolution UV | 4 096 max |
| Animations / keyframes | 32 / 32 768 |
| Durée / nom d'une animation | 600 s (10 min) / 64 caractères |
| Molang | 512 caractères, 16 instructions par clé, 64 variables |
| Canaux d'animation | rotation, position, scale |
| Émissif | calque `<texture>_e.png` embarqué, jamais assigné aux faces, ou option « Lumineux » du staff ; état en jeu (clignotement, shader) : `.claude/references/mod/rendus-avances.md` |
| Particules | 4 sortes modélisées + 4 de Minecraft (`emit_mc_`), 32 points `emit_`, 64 à 256 par joueur (`docs/guide-cosmetiques.md`, section 5 ter) |
| Sons | 32 par animation, noms de sons Minecraft, d'un pack du serveur (`phynaria:<nom>`) ou sons embarqués (`phynaria_sounds` : 8 OGG Vorbis mono ≤ 100 Ko et ≤ 5 s, `.claude/references/mod/sons-embarques.md`) |

## Workflow standard

1. Cadrer : type, ambiance, états à animer, contraintes (`/bbmodel-cosmetic`). **Se documenter** : fiche de `.claude/references/` du sujet ; si elle manque ou est incomplète, chercher sur le web (sujet réel, anatomie, comportement, matière ; anime pour les effets et la magie) et écrire ou compléter la fiche, sources comprises.
2. Écrire/adapter le générateur (textures peintes → géométrie → animations).
3. Avec `D=cosmetiques/<categorie>/x` : générer (`gen_x.py`), optimiser, vérifier, rendre en `MODCONV=1`, corriger le générateur, puis `python tools/livrer.py $D` (revérifie, crée `apercu/`, met à jour `$D/x.bbmodel` et le Vestiaire). Commandes, contenu du dossier et critères : `.claude/rules/delivery.md`.
4. Regarder `apercu/planche.png`, puis dire ce qui est à vérifier en jeu (`.claude/rules/essentiel.md`, Livraison).

## Où trouver quoi

Chargé d'office : ce fichier, `.claude/rules/essentiel.md` (méthode, axes, sons, lumière, livraison), `.claude/rules/contexte-agents.md`.

Chargé dès qu'on lit ou écrit un fichier de `cosmetiques/` :
- `.claude/rules/retours-en-jeu.md` : index des avis de l'utilisateur, avis et recettes communs à toutes les pièces, avis récents « à ranger ». **À lire en premier.**
- `.claude/rules/animation.md` (Molang, canaux, boucles, états, attaque et blessé), `modeling.md` (format, volume, silhouettes, budget), `fonctions-avancees.md` (groupes spéciaux, pièges, sons), `delivery.md` (dossier d'un cosmétique, commandes de livraison, fiche, particules).

Chargé selon la catégorie (`.claude/rules/categories/`, avis + leçons + règles propres) : `ailes.md` (anatomie, biomécanique, croisement), `familiers.md` (familier vivant, `pet_`), `effets.md` (effets de téléportation, groupe `joueur`, cercles au sol), `objets.md` (skins d'objets), `auras.md`, `tete.md` (`chapeaux/`), `corps.md` (`queues/`, `epaules/`, `sacs/`, `armes/`, `outils/`, `blocs/`).

Chargé dès qu'on touche `tools/` : `.claude/rules/outils.md` (vérificateur, renderer, Vestiaire).

À lire à la demande (jamais chargé d'office) :
- `.claude/references/mod/rendus-avances.md` : état en jeu des rendus avancés (shader, `_e`, `_r`, menu Apparence, `emit_mc_`, `ctrl_alpha`), demandes faites au développeur, ce que le guide ne couvre pas.
- `.claude/references/mod/sons-embarques.md` : sons embarqués en détail (format, limites, préséance, lecture, Blockbench).
- `.claude/references/procedures/remise-aux-regles.md` : remettre une pièce existante aux règles actuelles (liste de contrôle, leçons des passes).
- `.claude/references/historique-livraisons.md` : pièces livrées sans retour en jeu.
- `.claude/references/` : fiches par sujet, **à lire avant de chercher sur le web** : `animaux/` (canidés, félins, oiseaux…), `creatures/` (dragons, démons, anges, esprits…), `effets/` (auras, magie, éléments, ailes et impacts, d'après l'anime), `familiers/`. Sujet absent : faire la recherche, puis écrire sa fiche au même gabarit et l'ajouter au `README.md` du dossier. Ailes, effets, auras, magie : **s'inspirer d'abord de l'anime** (demande de l'utilisateur).
- `.claude/styles/<ensemble>.md` : fiches de style documentées (palette, matières, mouvement, idées, sources), à lire avant toute pièce de l'ensemble ; en créer une pour chaque nouvel ensemble. `.claude/styles/familiers.md` : ce qui rend un familier vivant (regard, comportements au hasard, réactions) et le **mode familier du guide** (il suit le joueur comme un loup, animations `pet_`), à lire avant tout familier. `.claude/styles/ailes-anatomie.md` : avant toute pièce ailée.
- `.claude/skills/` : procédures invocables (`/bbmodel-cosmetic`, `/bbmodel-animate`, `/bbmodel-verify`, `/bbmodel-calibrate`, `/bbmodel-retour-jeu`, `/bbmodel-serie`).
- `docs/` : guide officiel du mod (`guide-cosmetiques.md`, prime sur nos règles, ne pas le modifier), demandes au développeur (`dev/`), exemples (`exemples/`).
- `tools/` : renderer, optimiseur, vérificateur, `livrer.py`, Vestiaire, calibration. `ouvrir_vestiaire.bat` : catalogue local, mis à jour automatiquement ; l'ensemble d'une pièce se déduit de son nom (ou du champ `ensemble` de `fiche.json`), et chaque ensemble appartient à un thème (`cosmetiques/ensembles.json`). **Mode édition** du Vestiaire (fiches, statuts, ensembles, sans passer par Claude) : `.claude/rules/outils.md`.
- `cosmetiques/<categorie>/<nom>/` : **un dossier par cosmétique** (contenu : `.claude/rules/delivery.md`). Catégories : `ailes`, `chapeaux` (tout ce qui se porte sur la tête ou le visage : chapeau, cornes, masque…), `queues`, `epaules`, `familiers`, `sacs`, `auras`, `armes`, `outils`, `blocs`, `objets` (skins d'objets, guide §14 : `skin_<type>_<ensemble>`, ex. `skin_epee_givre`), `effets` (effets de téléportation, guide §15 : `effet_<ensemble>`, posés au sol au départ et à l'arrivée, pas portés).
