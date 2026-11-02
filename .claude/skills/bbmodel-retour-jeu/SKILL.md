---
name: bbmodel-retour-jeu
description: Traiter un retour de l'utilisateur sur un cosmétique en jeu (captures, « ça bug », « c'est moche ») — lire les captures, diagnostiquer, corriger sans casser ce qui est validé, livrer, puis noter la leçon.
---

# Traiter un retour en jeu

## 1. Lire
- Captures : `C:\Users\kouzi\AppData\Roaming\.phynaria\profiles\ftbe2\screenshots`. Lister par date et ouvrir **toutes** les nouvelles.
- Lire `docs/guide-cosmetiques.md` s'il a changé, et `.claude/rules/retours-en-jeu.md`.
- Reformuler les demandes. Si une phrase a deux sens opposés (« fait les plates »), vérifier sur les captures avant de coder.

## 2. Trier
Pour chaque point, noter : pièce, état, angle, heure de jeu, et s'il est à corriger ou validé.

| Symptôme | Piste d'abord |
|---|---|
| Inversion d'axe | Un seul signe dans `mirror()` |
| Pointillés, créneaux, clignotement | Faces coplanaires, chevauchements, UV en bord de calque `_e` |
| Lignes flottantes par la tranche | Plaques sans âme |
| Trop carré, marches | Cubes pleins visibles au lieu d'un contour alpha |
| Couches doubles sur une plaque | Épaisseur visible entre les deux faces |
| Couleur fausse la nuit | Éclairage, pas la texture : calque `_e` |

## 3. Corriger
- Modifier le générateur du cosmétique, jamais le `.bbmodel`.
- Citer dans la demande ce qui est validé et ne doit pas bouger.
- Limite du mod (ex. pas d'accélération en Molang) : le dire, faire l'approximation la plus proche, et l'ajouter à `docs/demandes_mod.md`.

## 4. Valider
Dans l'ordre : `.build/`, optimiseur, vérificateur, rendus incluant une vue de chaque défaut signalé. Regarder ces vues en pleine taille. Puis mettre à jour le fichier unique et `apercu/planche.png` + `apercu/animations.gif`.

## 5. Livrer et apprendre
- Message : point par point, ce qui est corrigé, cause mesurée ou supposée, 2–3 vérifications en jeu.
- Quand une capture suivante confirme ou infirme une recette, mettre à jour `.claude/rules/retours-en-jeu.md`.
