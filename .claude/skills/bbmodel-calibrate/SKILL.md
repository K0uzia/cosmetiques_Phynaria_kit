---
name: bbmodel-calibrate
description: Mesurer la convention d'axes et les canaux d'animation supportés par le mod de cosmétiques avec un modèle de calibration, puis mettre à jour les règles. À faire avant tout travail sur un nouveau mod ou une nouvelle version.
---

# Calibrer le mod

Ne jamais deviner la convention de rotation d'après Blockbench ou d'après des captures d'un modèle complexe. Mesurer.

## 1. Générer et faire importer le modèle de test
```bash
python tools/gen_calib.py      # -> calibration_axes.bbmodel
```
Barres : **rouge = +X**, **verte = +Y (haut)**, **bleue = +Z** (doit pointer vers l'arrière du joueur). 5 animations d'1 s : `rot_x`, `rot_y`, `rot_z` (+45° sur l'axe), `scale_test` (→ 0), `pos_test` (+8 px en Y).

Si le mod ne permet de choisir qu'une animation par état, générer aussi des fichiers à une seule animation nommée `idle` (un par test) : `python - <<'PY' … PY` en filtrant `animations`.

## 2. Demander à l'utilisateur, pour chaque test, ce qui bouge et dans quel sens
- `rot_x` : la barre **verte** bascule vers la bleue (arrière) ou l'opposé ?
- `rot_y` : la barre **rouge** tourne vers la bleue ou l'opposé ?
- `rot_z` : la barre **rouge** monte ou descend ?
- `scale_test` / `pos_test` : quelque chose bouge ? (si non → canal non supporté)
- La barre **bleue** pointe-t-elle vers l'arrière au repos ?

## 3. Traduire en convention et l'écrire dans `.claude/rules/animation.md`
- Pour chaque axe, note « valeur positive = <effet> » tel qu'observé.
- Compare avec la section 3 du guide. Si le jeu diverge, signale-le au développeur et aligne le renderer sur ce qui est observé.
- Mets à jour la table des canaux supportés et `verify_bbmodel.py` (liste des canaux autorisés) si scale/position deviennent supportés.

## 4. Valider sur un vrai modèle
Rendre `fly` et `run` avec le renderer, faire importer, comparer aux captures. Si ça diverge encore, le renderer a un bug : corriger `render_bbmodel.py` (fonction `rot_matrix`, ordre des axes), pas les animations.

## Résultat de la dernière calibration (mod serveur, nov. 2026)
- Le guide (section 3) fait référence pour les axes, et le renderer `MODCONV=1` concorde avec lui.
- `scale` et `position` : supportés d'après le guide. `calibration_axes.bbmodel` les avait montrés sans effet, pour une cause non identifiée : ce test n'est pas fiable pour ces deux canaux.
- Une texture principale embarquée, plus un calque `_e` facultatif ; cubes uniquement.
