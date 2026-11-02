---
name: bbmodel-cosmetic
description: Créer ou refondre un cosmétique Minecraft (.bbmodel) pour le mod du serveur — ailes, chapeau, sac, aura, arme, outil, bloc. Cadre la demande, génère par script, vérifie, rend, livre.
---

# Créer un cosmétique .bbmodel

Lis d'abord `CLAUDE.md`, `docs/guide-cosmetiques.md` et `.claude/rules/*.md`, en commençant par `retours-en-jeu.md`. Ne pars jamais d'une génération « au feeling » : suis les étapes.

## 1. Cadrer (une seule passe de questions, uniquement si nécessaire)

Déduis du message ce que tu peux ; ne demande que ce qui change réellement le résultat :
- **Type** (ailes / chapeau / sac / aura / arme / outil / bloc) et **ambiance** (3 mots : ex. « céleste, ivoire, or »).
- **Design original** : si l'utilisateur fournit une référence protégée (personnage, jeu, marque), dis-le en une phrase et propose un design original dans le même esprit. Ne reproduis pas, ne « t'inspire pas de près ».
- **États à animer** : par défaut les 12 du mod (voir `rules/animation.md`). Pas d'animation = statique.
- **Nombre de paires / silhouette** pour des ailes : par défaut une grande paire ; une petite paire basse si « archange/imposant ».
- **Contrainte de taille** : la texture max du mod (512), la limite de distance (64 px).

## 2. Écrire le générateur `cosmetiques/<categorie>/<nom>/gen_<nom>.py`

Catégories : `ailes`, `chapeaux`, `queues`, `epaules`, `familiers`, `sacs`, `auras`, `armes`, `outils`, `blocs`. Si le cosmétique existe déjà, reprends son dossier. Tous ses `.bbmodel` y restent (voir « Organisation » dans `CLAUDE.md`).

Pars de `cosmetiques/ailes/aurelion_wings/gen_aurelion_wings.py` pour des ailes (recettes validées en jeu, voir `retours-en-jeu.md`), en gardant `os.chdir(os.path.dirname(os.path.abspath(__file__)))` en début de script pour écrire dans le dossier du cosmétique. Dans l'ordre :
1. **Textures peintes par script** (sur-échantillonnage ×3–4, LANCZOS, seuil alpha) : silhouettes découpées, contraste de valeur entre rangées, ombres de recouvrement, détails ≥ 3–4 texels.
2. **Géométrie** : squelette en bones imbriqués (épaule→coude→poignet), plaques d'épaisseur ≥ 0,3 avec tranches transparentes, profondeur unique par élément, rangées qui se recouvrent.
3. **Animations** : fonctions périodiques → échantillonnées → `anim()` fait le miroir droite/gauche dans la convention du mod. Canaux rotation, position, scale (guide).
4. Impression finale : cubes, groupes, profondeur, anims, keyframes, poids.

## 3. Produire et vérifier

```bash
D=cosmetiques/<categorie>/<nom>
python3 $D/gen_<nom>.py
python3 tools/optimize_bbmodel.py $D/.build/<nom>_brut.bbmodel $D/.build/<nom>_opt.bbmodel
python3 tools/verify_bbmodel.py $D/.build/<nom>_opt.bbmodel      # doit finir par "OK — livrable"
```
Si FAIL : corrige le générateur, pas le fichier. Le livrable `$D/<nom>.bbmodel` n'est écrasé qu'une fois tout validé.

## 4. Rendre et regarder

```bash
for a in idle:1.0 fly:0.6 glide:0.9 run:0.3 sneak:0.5; do IFS=: read n t <<< "$a"
  MODCONV=1 ANIM=$n T=$t python3 tools/render_bbmodel.py $D/.build/<nom>_opt.bbmodel $D/.build/pose_$n.png 1.5; done
```
Assemble la planche `$D/apercu/planche.png` et **regarde-la**. Vérifie : pas de bloc uniforme, rangées lisibles, rien qui traverse le corps, course = vers l'arrière, vol = horizontal, sneak = replié dans le dos.

## 5. Livrer

Copie `.build/<nom>_opt.bbmodel` sur `$D/<nom>.bbmodel` (fichier unique, mis à jour sur place) + `<nom>.png` + `apercu/planche.png` + `apercu/animations.gif` (toutes les animations sur une seule planche). Message : changements point par point, chiffres, 2–3 points à vérifier en jeu, et ce qui est hors de portée du modèle, avec la raison.

## Pièges connus (ne pas refaire)

- Faire confiance au rendu Blockbench : il inverse X/Y par rapport au mod.
- Plans d'épaisseur 0 ou empilés : clignotement noir sous shader.
- Plumes effilées très fines : crénelage. Bouts arrondis.
- Liseré de 1–2 texels : invisible en jeu.
- Tout en blanc ivoire : « bloc blanc ». Contraste par rangée + ombres peintes.
- Pièce centrale dorsale : fait « sac à dos ». Les ailes sortent du dos, couvertes par des scapulaires.
- Petits cubes flottants (motes) : illisibles, à supprimer.
- Plumes qui tombent en cubes portés : elles suivent le joueur → groupes `particle_<nom>` + `emit_<nom>` (guide, section 5 ter).
