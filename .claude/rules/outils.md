---
paths:
  - "tools/**"
---

# Règles — outils (renderer, Vestiaire, vérificateur)

## Renderer et Vestiaire

La vue 3D du Vestiaire (`tools/visionneuse.js`) reprend les calculs du renderer : après toute retouche de `render_bbmodel.py` (pose, Molang, transformations), reporter le changement et lancer `python tools/test_visionneuse.py`. Renderer et visionneuse partagent un même parseur Molang (`&&`, `||`, `!`, `?:`, `return`, `t.`, valeur neutre si invalide). Ce que les aperçus simulent ou non : colonne « Aperçu » de `fonctions-avancees.md`. Chaque avis de l'utilisateur se reporte dans `cosmetiques/statuts.json` (badge « Validé en jeu » / « Refusé » du Vestiaire ; l'ancienne table `STATUTS` de `gen_index.py` n'est lue que pour une pièce absente du fichier).

## Mode « comme en jeu »

Vue 3D du Vestiaire, liste « Rendu » (défaut : Comme en jeu · jour ; « Rendu studio » = l'ancien rendu, flatteur) et distance (3 blocs « Essayer », 4 blocs 3e personne, 10 blocs ; molette : 1,5 à 32). Reproduit le mod 1.4.0 et Minecraft 26.1.2 : ciel et sol, lumière des faces de Minecraft × lumière du monde, `add_`/`_e` ajoutés sur le fond, `trans_` trié qui écrit la profondeur, `ctrl_alpha` progressif, image rendue à 1 369 lignes en 70° sans lissage puis réduite, mipmaps des textures (guide du 2026-11-08 ; renderer : niveau par triangle, approché, `MIPMAPS=0` pour couper), `add_`/`_e` = couleur × alpha, copie du départ d'un effet à l'échelle du groupe `joueur`, particules selon « Quand », la limite et le mouvement du mod, `emit_mc_` approchées. Renderer : `JEU=1` (planche jour / jour gris / nuit / nuit + shader à 3 et 10 blocs ; `CIEL`, `CASES=gris:3,nuit:10`) ; `livrer.py` écrit `apercu/jeu.png` (onglet « Comme en jeu »). Mesures, limites et demandes possibles au développeur : `.claude/references/mod/rendu-en-jeu.md` ; calibration : `docs/dev/tests_rendu/calibration_jeu.py`.

## Mode édition du Vestiaire

Avec le serveur local (`ouvrir_vestiaire.bat`, 127.0.0.1), l'utilisateur modifie seul (`tools/edition.py`, bibliothèque standard, marche sans numpy) :
- **Modifier la fiche** (colonne de la fiche d'une pièce) : nom, ensemble, rareté, prix (sans « Prix manuel », la grille propose et décide), en vente, description, lore, statut et note ;
- **Gérer les ensembles** (bas du panneau) : créer, modifier (nom affiché, titre, thème, accroche, lore, couleur, lot en vente), supprimer un ensemble vide.
« Enregistrer » valide (longueurs du guide), copie `<fichier>.bak`, écrit `fiche.json`, `cosmetiques/statuts.json` ou `cosmetiques/ensembles.json`, réembarque la fiche dans `<nom>.bbmodel` (`fiche.embarquer_fichier`, rien d'autre ne change), refait l'export `livrables/` (retire l'ancien) et le catalogue. Écritures limitées à `cosmetiques/` et `livrables/`, requêtes de la page locale seulement.
Ensembles : `ensembles.json` (clé = identifiant stable, `nom` = nom affiché en jeu, `theme`, `couleur`…) ; un thème nouveau s'ajoute après `THEMES`. Ensemble d'une pièce : champ `"ensemble"` de `fiche.json` (clé), qui prime sur la déduction par `MOTS`. Non modifiable depuis le Vestiaire : nom du dossier, géométrie, animations, aperçus, grille `prix.json` et `MOTS` (il faut le générateur ou le code).

## Vérificateur

`tools/verify_bbmodel.py` contrôle (**tout doit passer** avant livraison, `delivery.md`, étape 3) :
- JSON valide, format free ou modded_entity (java_block pour un skin d'objet), 1 texture PNG embarquée ≤ 512² (+ `_e`, `_r`, `_m`), semi-transparence seulement avec des groupes `trans_`, résolution = PNG, résolution UV ≤ 4096 ; `ctrl_` connus, `emit_mc_` sans chiffre final, sons ≤ 32 par animation ; sons embarqués (`phynaria_sounds`) acceptés par le mod (OGG Vorbis mono, ≤ 100 Ko, ≤ 5 s, nom `[a-z0-9_]{1,32}`, ≤ 8) et clés de son qui pointent vers un son embarqué ou un son du jeu (`.claude/references/mod/sons-embarques.md`)
- cubes ≤ 8192, groupes ≤ 2048, profondeur ≤ 64, anims ≤ 32, keyframes ≤ 32768
- rotations de base des cubes et groupes ≤ ±360°, rotations de face multiples de 90°, inflate ≤ ±8
- noms de groupes et d'animations ≤ 64 caractères, noms de groupes uniques
- aucune épaisseur nulle, aucun élément strictement superposé
- canaux `rotation`/`position`/`scale` uniquement, durée ≤ 600 s, expressions Molang ≤ 512 caractères (complexité non mesurable, à tester en jeu)
- boucles fermées (écart début/fin < 0,05 px) pour toutes les anims `loop`
- zone autorisée **au repos** (cubes et pivots, par axe ; guide 3) : 128 px porté ou familier, 320 px effet, 64 px skin d'objet (`--max-ext` pour forcer) ; clés `position` ≤ 320 px et `scale` ≤ 16 (valeurs numériques ; Molang non mesuré) ; extension animée affichée en information seulement ; requêtes Molang hors du guide en alerte
- réactions selon la catégorie (déduite du chemin `cosmetiques/<categorie>/`) : `attack`/`hurt` interdits sur `chapeaux`, `epaules`, `queues`, `sacs`, `auras` ; `hurt` interdit sur `armes` ; rien sur ailes, familiers, outils, blocs (`animation.md`, « Attaque et blessé »)
- ailes (`ailes/`) qui ne se croisent pas : poses idle, walk, run, sneak, sleep, mount à 4 instants, le centre de chaque élément reste de son côté de la colonne (côté pris en pose de base) ; FAIL au-delà de 2 px hors racine (|x| de base ≥ 6), alerte au-delà de 3 px à la racine (scapulaires) ; `cam_`, `emit_`, éléments cachés ignorés (`categories/ailes.md`, `ailes_orage` v4)
- bloc `unhandled_root_fields.phynaria` au format du guide : `version` 1, `particules` (5 ter §6 : identifiants et pas du guide, une entrée par sorte présente), `fiche` (10 bis : longueurs 40/40/24/300/500, rareté de la liste ou mot libre), `familier` (6.6 : mode, distance, vitesse, hauteur), `objet` (14 : type, étapes à la racine) ; alerte sans fiche
- noms d'animation joués (alerte sinon) : états du guide 6.2, `overlay_`, `particle_`, événements de la table 6.4 (`event_enter_sprint`, pas `_run`) ; familier vivant : états et événements de la 6.6, aucun groupe du corps à la racine (FAIL), alertes pour `emit_`, `phys_`, `attack`/`hurt` (non joués sur un familier vivant)
- skin d'objet : exige `phynaria.objet.type` et contrôle étapes, réglages Display, boîte dans le bloc, noms d'animation d'objet (`item_*`, `event_*` du guide 14, `event_enter_<étape>`) ; « À l'utilisation » / « Au tir » en alerte hors d'un objet ; `vignette` (10 bis) contrôlée ; effet de téléportation (reconnu au chemin, ou à `depart`/`arrivee`, ou au groupe `joueur`) : `depart`/`arrivee` ≤ 5 s (FAIL), modes `loop`/`once`, groupe `joueur` vide, noms joués
- **échelles superposées** (WARN, modèle à `event_*`) : un groupe (ancêtres compris) dont l'échelle s'écarte de 1 dans plusieurs animations qui jouent ensemble, cumul (pics multipliés, borne haute) ≥ 1,5 × l'état + un seul événement. Objet (guide 14) : coup = `item_idle`/`item_swing` + `select` + `swing` + `hit` ; minage = idem avec `break` ; utilisation = `item_use` + `select` + `use_start` + `charged` + une étape ; relâche = `item_idle`/`item_use` + `use_start` + `use_stop` + `release` + `charged` + une étape. Porté ou familier : état + un `exit_` + un `enter_` + `jump`/`land`/`teleport`/`perch` + `attack`/`hurt`/`owner_hurt` (`equip`/`unequip` avec l'état seul). Correctif : un groupe par animation qui le déplie (`skin_epee_orage`, `skin_bouclier_cuir`)
- poids brut et compressé (zlib) affichés ; brut ≤ 16 Mo (alerte si > 8 Mo : la taille nettoyée par le serveur n'est pas mesurable ici) ; compressé < 1 000 Ko (estimation : le mod compresse le fichier nettoyé)
