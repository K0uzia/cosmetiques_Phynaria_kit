---
name: bbmodel-cosmetic
description: Créer ou refondre un cosmétique Minecraft (.bbmodel) pour le mod du serveur — ailes, tête (chapeau, cornes, masque), queue, épaules, aura, arme, familier, sac, outil, bloc. Cadre la demande, génère par script, vérifie, rend, livre.
---

# Créer un cosmétique .bbmodel

Lis d'abord `CLAUDE.md`, `docs/guide-cosmetiques.md` et `.claude/rules/*.md`, en commençant par `retours-en-jeu.md`. Ne pars jamais d'une génération « au feeling » : suis les étapes.

## 1. Cadrer (une seule passe de questions, uniquement si nécessaire)

Déduis du message ce que tu peux ; ne demande que ce qui change réellement le résultat :
- **Type** (ailes, tête, queue, épaules, aura, arme, familier, sac, outil, bloc ; « chapeau » veut dire tout ce qui se porte sur la tête ou le visage) et **ambiance** (3 mots : ex. « céleste, ivoire, or »).
- **Design original** : si l'utilisateur fournit une référence protégée (personnage, jeu, marque), dis-le en une phrase et propose un design original dans le même esprit. Ne reproduis pas, ne « t'inspire pas de près ».
- **États à animer** : par défaut les 12 du mod (voir `rules/animation.md`). Pas d'animation = statique.
- **Nombre de paires / silhouette** pour des ailes : par défaut une grande paire ; une petite paire basse si « archange/imposant ».
- **Contrainte de taille** : la texture max du mod (512), la limite de distance (64 px).

## 2. Écrire le générateur `cosmetiques/<categorie>/<nom>/gen_<nom>.py`

Catégories : `ailes`, `chapeaux`, `queues`, `epaules`, `familiers`, `sacs`, `auras`, `armes`, `outils`, `blocs`. Si le cosmétique existe déjà, reprends son dossier. Tous ses `.bbmodel` y restent (voir « Organisation » dans `CLAUDE.md`).

Pars du générateur de référence indiqué dans `retours-en-jeu.md`, en gardant `os.chdir(os.path.dirname(os.path.abspath(__file__)))` en début de script pour écrire dans le dossier du cosmétique. Dans l'ordre :
1. **Textures peintes par script** (sur-échantillonnage ×3–4, LANCZOS, seuil alpha) : silhouettes découpées, contraste de valeur entre rangées, ombres de recouvrement, détails ≥ 3–4 texels.
2. **Géométrie** : squelette en bones imbriqués, peau découpée par alpha autour d'une âme pleine, os effilés en volume, profondeur unique par élément, rangées qui se recouvrent. Particules : recette de `retours-en-jeu.md`.
3. **Animations** : fonctions périodiques → échantillonnées → `mirror()` centralise le signe droite/gauche. Canaux rotation, position, scale (guide).
4. Lueur : `AVEC_E = False` tant que le bug du calque court (`retours-en-jeu.md`).
5. Impression finale : cubes, groupes, profondeur, anims, keyframes, poids.

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

`python tools/livrer.py $D`, puis regarde `apercu/planche.png`. Message : changements point par point, chiffres, 2–3 points à vérifier en jeu, et ce qui est hors de portée du modèle, avec la raison.

## Pièges connus (ne pas refaire)

- Plans d'épaisseur 0 ou empilés : clignotement noir sous shader.
- Plumes effilées très fines : crénelage. Bouts arrondis.
- Liseré de 1–2 texels : invisible en jeu.
- Tout d'une seule teinte : « bloc ». Contraste par rangée + ombres peintes.
- Pièce centrale dorsale : fait « sac à dos ». Les ailes sortent du dos, couvertes par des scapulaires.
- Petits cubes flottants (motes) : illisibles, à supprimer.
- Plumes qui tombent en cubes portés : elles suivent le joueur → groupes `particle_<nom>` + `emit_<nom>` (guide, section 5 ter).
