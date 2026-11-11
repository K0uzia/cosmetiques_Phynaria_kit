# Kit cosmétiques Phynaria (.bbmodel)

Génération de cosmétiques Minecraft (ailes, couvre-chefs, queues, épaulières, auras, armes, familiers…) au format Blockbench `.bbmodel`, pour le mod Phynaria Utilities (Minecraft 26.1.2, NeoForge).

Les modèles ne se font pas à la main : chaque cosmétique est produit par un script Python, ce qui permet de l'itérer, de le vérifier et de l'optimiser de façon reproductible. Le dépôt est conçu pour être utilisé avec Claude Code, qui charge `CLAUDE.md` et `.claude/rules/` automatiquement, mais les outils s'utilisent aussi seuls.

## Installation

Python 3.10+ avec `numpy` et `Pillow` :

```
pip install numpy pillow
```

Le Vestiaire (`gen_index.py`, `serve_vestiaire.py`) n'utilise que la bibliothèque standard.

## Le Vestiaire

Double-cliquer sur `ouvrir_vestiaire.bat` ouvre le catalogue de tous les cosmétiques, servi en local. La page se met à jour seule dès qu'un cosmétique est ajouté ou modifié. Sans le serveur, `python tools/gen_index.py` régénère `index.html`.

## Organisation

```
CLAUDE.md                 règles du projet et limites du mod
.claude/rules/            règles par domaine : modélisation, animation, livraison, retours en jeu
.claude/skills/           procédures invocables (voir plus bas)
docs/                     guide du mod, exemples, demandes au développeur (voir docs/README.md)
tools/                    renderer, optimiseur, vérificateur, calibration, Vestiaire
cosmetiques/<categorie>/  un dossier par cosmétique
index.html                catalogue généré
ouvrir_vestiaire.bat      lance le Vestiaire
```

`docs/guide-cosmetiques.md` est le guide officiel du mod : il prime sur toutes nos règles. `.claude/rules/retours-en-jeu.md` est l'index des leçons tirées des essais en jeu (avis par catégorie dans `.claude/rules/categories/`), à lire avant de commencer.

### Outils

| Fichier | Rôle |
|---|---|
| `tools/verify_bbmodel.py` | Contrôle les limites du mod, les boucles, les superpositions, l'extension et le poids |
| `tools/optimize_bbmodel.py` | Simplifie les keyframes, compacte le JSON, optimise le PNG |
| `tools/render_bbmodel.py` | Rendu logiciel de contrôle ; `MODCONV=1` applique la convention du mod |
| `tools/livrer.py` | Vérifie un cosmétique, crée ses aperçus, met à jour le livrable et le Vestiaire |
| `tools/gen_calib.py`, `tools/calibration_axes.bbmodel` | Modèle de calibration des axes |
| `tools/gen_index.py`, `tools/serve_vestiaire.py`, `tools/catalogue_modele.html` | Vestiaire |
| `tools/example_wings_generator.py` | Ancien exemple d'ailes, qui contient des défauts corrigés depuis ; partir plutôt de `gen_ailes_berenice.py` |

### Dossier d'un cosmétique

Catégories : `ailes`, `chapeaux` (tout ce qui se porte sur la tête ou le visage), `queues`, `epaules`, `familiers`, `sacs`, `auras`, `armes`, `outils`, `blocs`.

```
cosmetiques/<categorie>/<nom>/
  gen_<nom>.py          générateur
  <nom>.bbmodel         livrable optimisé, mis à jour sur place
  <nom>.png             texture (avec <nom>_e.png pour un calque lumineux)
  <nom>_<piece>.bbmodel modèles associés, par exemple une particule
  apercu/               planche.png et animations.gif, écrasés à chaque mise à jour
  .build/               fichiers intermédiaires, non versionnés
```

Comme `.build/` n'est pas versionné, il se recrée en relançant le générateur.

## Créer ou modifier un cosmétique

Avec `D=cosmetiques/<categorie>/<nom>` :

```
python $D/gen_<nom>.py
python tools/optimize_bbmodel.py $D/.build/<nom>_brut.bbmodel $D/.build/<nom>_opt.bbmodel
python tools/verify_bbmodel.py $D/.build/<nom>_opt.bbmodel
MODCONV=1 ANIM=idle T=1.0 python tools/render_bbmodel.py $D/.build/<nom>_opt.bbmodel idle.png 1.5
```

La vérification ne doit contenir aucun échec. Rendre au moins `idle`, `fly`, `run` et `sneak` en 4 vues et regarder le résultat, puis livrer avec `python tools/livrer.py $D`. Le détail est dans `.claude/rules/delivery.md`.

Un rendu propre et une vérification verte ne prouvent pas le résultat en jeu : le renderer ne montre ni le shader, ni l'éclairage de nuit, ni l'émissif, ni les particules. Quand une capture en jeu et le rendu divergent, c'est la capture qui a raison.

## Procédures Claude Code

| Commande | Usage |
|---|---|
| `/bbmodel-cosmetic` | Créer ou refondre un cosmétique, du cadrage à la livraison |
| `/bbmodel-animate` | Ajouter ou corriger des animations |
| `/bbmodel-verify` | Vérifier un modèle avant livraison et rendre ses poses clés |
| `/bbmodel-calibrate` | Mesurer la convention d'axes d'un nouveau mod ou d'une nouvelle version |
| `/bbmodel-retour-jeu` | Traiter un retour en jeu à partir de captures |
| `/bbmodel-serie` | Créer plusieurs cosmétiques ou un ensemble, avec un sous-agent par pièce |

## Règles à connaître

- Les axes suivent le guide du mod, section 3 : le jeu lit le `.bbmodel` comme la vue 3D de Blockbench (`.claude/rules/essentiel.md`, Axes).
- Aucune reproduction de design protégé (personnages, logos) : une référence sert à cerner l'ambiance, le design reste original.
- Les limites du mod (cubes, groupes, textures, animations, particules) sont listées dans `CLAUDE.md`.
