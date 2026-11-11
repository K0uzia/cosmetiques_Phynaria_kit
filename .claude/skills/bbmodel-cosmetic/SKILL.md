---
name: bbmodel-cosmetic
description: Créer ou refondre un cosmétique Minecraft (.bbmodel) pour le mod du serveur — ailes, tête (chapeau, cornes, masque), queue, épaules, aura, arme, familier, sac, outil, bloc, skin d'objet, effet de téléportation. Cadre la demande, génère par script, vérifie, rend, livre.
---

# Créer un cosmétique .bbmodel

Lis d'abord `CLAUDE.md`, `docs/guide-cosmetiques.md` et les règles de `.claude/rules/` (y compris `categories/<catégorie>.md` de la pièce : elles ne se chargent d'elles-mêmes qu'une fois un fichier de `cosmetiques/` ouvert), en commençant par `retours-en-jeu.md`. Ne pars jamais d'une génération « au feeling » : suis les étapes.

## 1. Cadrer (une seule passe de questions, uniquement si nécessaire)

Déduis du message ce que tu peux ; ne demande que ce qui change réellement le résultat :
- **Type** (ailes, tête, queue, épaules, aura, arme, familier, sac, outil, bloc, skin d'objet, effet de téléportation ; « chapeau » veut dire tout ce qui se porte sur la tête ou le visage) et **ambiance** (3 mots : ex. « céleste, ivoire, or »).
- **Design original** : si l'utilisateur fournit une référence protégée (personnage, jeu, marque), dis-le en une phrase et propose un design original dans le même esprit. Ne reproduis pas, ne « t'inspire pas de près ».
- **États à animer** : par défaut les 12 du mod (voir `rules/animation.md`). Pas d'animation = statique.
- **Nombre de paires / silhouette** pour des ailes : par défaut une grande paire ; une petite paire basse si « archange/imposant ».
- **Contrainte de taille** : la texture max du mod (512), la limite de distance au repos (128 px porté ou familier, 320 px effet, 64 px skin d'objet ; guide 3).

## 1 bis. Se documenter (obligatoire, demande de l'utilisateur du 2026-11-04)

Avant d'écrire une ligne : lire la fiche du sujet dans `.claude/references/` (`animaux/`, `creatures/`, `effets/`, index dans chaque `README.md`). Si elle manque ou ne couvre pas le besoin, chercher sur le web (WebSearch) **le vrai sujet** (anatomie de l'animal, objet réel, matière, comportement, mouvement) et des références de style **pour l'ambiance**. Pour les ailes, effets, auras et la magie, partir de la manière dont l'anime les représente : **identifier des œuvres populaires précises** (anime, isekai, jeux) dont les personnages ont ce genre de capacité ou d'objet, et noter dans la fiche de l'ensemble une section « Références d'ambiance » (œuvre → codes génériques retenus, sources). Rien ne se crée « de nulle part » (consigne du 2026-11-05) ; les œuvres donnent l'ambiance, jamais un design à copier. Écrire ou compléter la fiche de `.claude/references/` (même gabarit, sources), et noter dans le docstring du générateur et dans la fiche `.claude/styles/<ensemble>.md` : ce qui a été appris (proportions, détails qui font la matière, gestes caractéristiques), avec les sources. Une référence protégée sert à cerner l'ambiance, jamais à copier (règle 5 de `CLAUDE.md`). **Approche par analogie (consigne du 2026-11-06, après le refus de l'effet admin v1 « pas documenté, nul en vrai »)** : quand l'utilisateur donne une inspiration (scène, personnage, effet d'une œuvre), l'étudier vraiment, pas « pour l'ambiance » en une ligne : déroulé plan par plan, formes et volumes, couleurs, timing, sons, ce qui rend le moment spectaculaire. Puis la **traduire en spécifications techniques d'une version 100 % originale** (structure des cubes et groupes, keyframes, style de texture, particules, sons). **Ne jamais citer l'œuvre** dans les fiches `.claude/`, le générateur, la fiche du cosmétique ni le rapport : décrire la grammaire visuelle (« masque blanc en os poli, orbites creuses »), pas sa source. Les sources notées sont des articles techniques (anatomie, VFX, animation). Contrôle avant livraison : rendus regardés depuis le sol et de 3/4 ; si le résultat ne se lit pas comme l'intention, recommencer. Exemples de ce qu'on aurait évité : masque Cuir « Zorro » faute de connaître les harnais réels, renard au museau de chien faute des proportions du renard polaire.

## 2. Écrire le générateur `cosmetiques/<categorie>/<nom>/gen_<nom>.py`

Catégories : `ailes`, `chapeaux`, `queues`, `epaules`, `familiers`, `sacs`, `auras`, `armes`, `outils`, `blocs`, `objets` (skins d'objets, guide 14), `effets` (effets de téléportation, guide 15 : `effet_<ensemble>`). Si le cosmétique existe déjà, reprends son dossier. Tous ses `.bbmodel` y restent (voir « Organisation » dans `CLAUDE.md`).

Pars du générateur de référence indiqué dans `essentiel.md` (Méthode de travail), en gardant `os.chdir(os.path.dirname(os.path.abspath(__file__)))` en début de script pour écrire dans le dossier du cosmétique. Dans l'ordre :
1. **Textures peintes par script** (sur-échantillonnage ×3–4, LANCZOS, seuil alpha) : silhouettes découpées, contraste de valeur entre rangées, ombres de recouvrement, détails ≥ 3–4 texels.
2. **Géométrie** : squelette en bones imbriqués, peau découpée par alpha autour d'une âme pleine, os effilés en volume, profondeur unique par élément, rangées qui se recouvrent. Particules : recette de `retours-en-jeu.md`.
3. **Animations** : fonctions périodiques → échantillonnées → `mirror()` centralise le signe droite/gauche. Canaux rotation, position, scale (guide).
4. Lueur : `AVEC_E = True` depuis le correctif annoncé le 2026-11-03, à confirmer en jeu (`.claude/references/mod/rendus-avances.md`).
5. Familier : mode familier du guide (bloc `familier` par `tools/fiche.py`, animations `pet_`, aucun groupe du corps), `.claude/styles/familiers.md`. Pas de groupe `body` porté pour un nouveau familier.
6. Effet de téléportation : posé au sol, pas de groupe du corps ; `charge` (loop), `depart` et `arrivee` (once, ≤ 5 s), groupe vide `joueur` animé en position et échelle (`.claude/rules/categories/effets.md`).
7. Impression finale : cubes, groupes, profondeur, anims, keyframes, poids.

## 3. Produire et vérifier

```bash
D=cosmetiques/<categorie>/<nom>
python $D/gen_<nom>.py
python tools/optimize_bbmodel.py $D/.build/<nom>_brut.bbmodel $D/.build/<nom>_opt.bbmodel
python tools/verify_bbmodel.py $D/.build/<nom>_opt.bbmodel      # doit finir par "OK — livrable"
```
Si FAIL : corrige le générateur, pas le fichier. Le livrable `$D/<nom>.bbmodel` n'est écrasé qu'une fois tout validé.

## 4. Rendre et regarder

```bash
for a in idle:1.0 fly:0.6 glide:0.9 run:0.3 sneak:0.5; do IFS=: read n t <<< "$a"
  MODCONV=1 ANIM=$n T=$t python tools/render_bbmodel.py $D/.build/<nom>_opt.bbmodel $D/.build/pose_$n.png 1.5; done
```
Regarde ces rendus **en pleine taille**, plus le profil et la vue par la tranche. Vérifie : pas de bloc uniforme, rangées lisibles, rien qui traverse le corps, course = vers l'arrière, vol = basculé à 40°, sneak = replié dans le dos.

## 5. Livrer

Écris `$D/fiche.json` (et `$D/reglages.json` s'il y a des particules) : `livrer.py` les embarque dans le modèle (`phynaria.fiche`, `phynaria.particules`, lus par le mod à l'import). `python tools/livrer.py $D`, puis regarde `apercu/planche.png`. Message : changements point par point, chiffres, 2–3 points à vérifier en jeu, et ce qui est hors de portée du modèle, avec la raison.

## Pièges connus (ne pas refaire)

- Plans d'épaisseur 0 ou empilés : clignotement noir sous shader.
- Plumes effilées très fines : crénelage. Bouts arrondis.
- Liseré de 1–2 texels : invisible en jeu.
- Tout d'une seule teinte : « bloc ». Contraste par rangée + ombres peintes.
- Pièce centrale dorsale : fait « sac à dos ». Les ailes sortent du dos, couvertes par des scapulaires.
- Petits cubes flottants (motes) : illisibles, à supprimer.
- Plumes qui tombent en cubes portés : elles suivent le joueur → groupes `particle_<nom>` + `emit_<nom>` (guide, section 5 ter).
