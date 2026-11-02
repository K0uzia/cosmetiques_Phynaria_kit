# Kit cosmétiques Minecraft (.bbmodel)

Déposer ce dossier à la racine du projet de cosmétiques. Claude Code charge automatiquement `CLAUDE.md` et `.claude/rules/*.md` ; les skills s'invoquent avec `/bbmodel-cosmetic`, `/bbmodel-animate`, `/bbmodel-verify`, `/bbmodel-calibrate`.

```
CLAUDE.md                     règles de projet (lues à chaque session)
.claude/rules/                modeling.md · animation.md · delivery.md
.claude/skills/               procédures invocables
tools/render_bbmodel.py       rendu logiciel (MODCONV=1 = convention du mod)
tools/optimize_bbmodel.py     simplification keyframes, JSON compact, PNG
tools/verify_bbmodel.py       contrôle des limites du mod + boucles + extension
ouvrir_vestiaire.bat          catalogue des cosmétiques, mis à jour automatiquement
tools/serve_vestiaire.py      serveur local du catalogue (bibliothèque standard seule)
tools/gen_index.py            génère index.html depuis tools/catalogue_modele.html
tools/gen_calib.py            modèle de calibration des axes
tools/example_wings_generator.py  générateur complet d'ailes (référence)
docs/demandes_mod.md          demandes au développeur du mod et leur statut
cosmetiques/<categorie>/<nom>/  un dossier par cosmétique, avec tous ses .bbmodel
```

Catégories : `ailes`, `chapeaux`, `queues`, `epaules`, `familiers`, `sacs`, `auras`, `armes`, `outils`, `blocs`.

Dépendances : Python 3.10+, `numpy`, `Pillow`.
