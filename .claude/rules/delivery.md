# Règles — vérification et livraison

## Avant toute livraison (dans cet ordre)

Dans ces commandes, `D=cosmetiques/<categorie>/<nom>`. Le livrable `$D/<nom>.bbmodel` est un fichier unique, mis à jour sur place : on travaille dans `$D/.build/` et on ne l'écrase qu'une fois tout validé.

1. `python3 $D/gen_<nom>.py` — doit imprimer cubes / groupes / profondeur / anims / keyframes.
2. `python3 tools/optimize_bbmodel.py $D/.build/<nom>_brut.bbmodel $D/.build/<nom>_opt.bbmodel`
3. `python3 tools/verify_bbmodel.py $D/.build/<nom>_opt.bbmodel` — **tout doit passer** :
   - JSON valide, format free, 1 texture PNG embarquée ≤ 512², résolution = PNG, résolution UV ≤ 4096
   - cubes ≤ 8192, groupes ≤ 2048, profondeur ≤ 64, anims ≤ 16, keyframes ≤ 32768
   - rotations de base des cubes et groupes ≤ ±360°, rotations de face multiples de 90°, inflate ≤ ±8
   - noms de groupes et d'animations ≤ 64 caractères, noms de groupes uniques
   - aucune épaisseur nulle, aucun élément strictement superposé
   - canaux `rotation`/`position`/`scale` uniquement, durée ≤ 600 s, expressions Molang ≤ 256 caractères (complexité non mesurable, à tester en jeu)
   - boucles fermées (écart début/fin < 0,05 px) pour toutes les anims `loop`
   - extension max < 64 px par axe sur toutes les anims (alerte si > 60)
   - poids brut et compressé (zlib) affichés ; brut ≤ 16 Mo (alerte si > 8 Mo : la taille nettoyée par le serveur n'est pas mesurable ici) ; compressé < 1 000 Ko (estimation : le mod compresse le fichier nettoyé)
4. Rendus de contrôle en **convention du mod** :
   `MODCONV=1 ANIM=idle T=1.0 python3 tools/render_bbmodel.py $D/.build/<nom>_opt.bbmodel idle.png 1.5`
   idem pour `fly` (T=0.6), `run` (T=0.3), `sneak` (T=0.5), `glide` (T=0.9). Assembler en planche. **Regarder la planche** avant d'envoyer.
5. Livrer dans `$D` : copier `.build/<nom>_opt.bbmodel` sur `<nom>.bbmodel`, avec `<nom>.png`, `apercu/planche.png` et `apercu/animations.gif`, regroupant toutes les animations. Si la vérification échoue, le livrable précédent reste intact.

## Dans le message de livraison

- Ce qui a changé par rapport à la version précédente, en réponse aux retours (point par point).
- Chiffres : cubes, groupes, poids brut/compressé, extension max.
- **Ce qu'il faut vérifier en jeu** (2–3 points max) et ce qui est connu comme non faisable côté modèle, avec la raison.
- Ne jamais affirmer qu'un rendu correspondra en jeu si la convention n'a pas été calibrée sur ce mod.

## Quand l'utilisateur renvoie une capture

- La capture a raison. Diagnostiquer précisément (quel axe, quel état) avant de toucher au code.
- Si le diagnostic est une inversion d'axe : un seul signe dans `anim()`, pas une refonte.
- Si plusieurs retours à la fois : les lister, traiter chacun, et dire lesquels sont hors de portée du modèle (→ `docs/demandes_mod.md`).

## Pas de « v+1 » cosmétique

Avant de relancer une génération complète, se demander : le problème est-il dans la **convention** (→ calibrer), dans l'**outil** (renderer/vérificateur), ou dans le **design** ? Ne refaire le design que si c'est le design.
