---
name: bbmodel-calibrate
description: Mesurer la convention d'axes et les canaux d'animation supportés par le mod de cosmétiques avec un modèle de calibration, puis mettre à jour les règles. À faire avant tout travail sur un nouveau mod ou une nouvelle version.
---

# Calibrer le mod

Ne jamais deviner la convention de rotation d'après Blockbench ou d'après des captures d'un modèle complexe. Mesurer.

## 1. Générer et faire importer le modèle de test
```bash
python3 tools/gen_calib.py      # -> calibration_axes.bbmodel
```
Barres : **rouge = +X**, **verte = +Y (haut)**, **bleue = +Z** (doit pointer vers l'arrière du joueur). 5 animations d'1 s : `rot_x`, `rot_y`, `rot_z` (+45° sur l'axe), `scale_test` (→ 0), `pos_test` (+8 px en Y).

Si le mod ne permet de choisir qu'une animation par état, générer aussi des fichiers à une seule animation nommée `idle` (un par test) : `python3 - <<'PY' … PY` en filtrant `animations`.

## 2. Demander à l'utilisateur, pour chaque test, ce qui bouge et dans quel sens
- `rot_x` : la barre **verte** bascule vers la bleue (arrière) ou l'opposé ?
- `rot_y` : la barre **rouge** tourne vers la bleue ou l'opposé ?
- `rot_z` : la barre **rouge** monte ou descend ?
- `scale_test` / `pos_test` : quelque chose bouge ? (si non → canal non supporté)
- La barre **bleue** pointe-t-elle vers l'arrière au repos ?

## 3. Traduire en convention et l'écrire dans `.claude/rules/animation.md`
- Pour chaque axe, note « valeur positive = <effet> » tel qu'observé.
- Compare avec Blockbench (qui affiche X et Y négués) : si le mod ne nie pas, le renderer doit tourner avec `MODCONV=1`.
- Mets à jour la table des canaux supportés et `verify_bbmodel.py` (liste des canaux autorisés) si scale/position deviennent supportés.

## 4. Valider sur un vrai modèle
Rendre `fly` et `run` avec le renderer, faire importer, comparer aux captures. Si ça diverge encore, le renderer a un bug : corriger `render_bbmodel.py` (fonction `rot_matrix`, ordre des axes), pas les animations.

## Résultat de la dernière calibration (mod serveur, nov. 2026)
- Rotations appliquées telles quelles (pas d'inversion Blockbench). Côté gauche : X− = bascule arrière/horizontale ; Y+ = pivote arrière ; Z+ = pointe monte.
- `scale` et `position` : constatés sans effet avec `calibration_axes.bbmodel`, mais **le développeur du mod confirme qu'ils fonctionnent** et que le problème venait du modèle. Cause non identifiée : ce test n'est donc pas fiable pour ces deux canaux.
- Une seule texture embarquée ; cubes uniquement.
