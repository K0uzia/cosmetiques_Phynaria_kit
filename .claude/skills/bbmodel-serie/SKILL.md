---
name: bbmodel-serie
description: Créer plusieurs cosmétiques d'un coup ou compléter un ensemble (« fais-moi tout ça », plusieurs pièces assorties) avec un sous-agent par pièce, puis valider et livrer le lot.
---

# Créer une série de cosmétiques

## 1. Préparer
- Lister les pièces, leur catégorie et leur ensemble. Le nom d'une pièce contient le mot de son ensemble (`abyssal`, `celeste`…), sinon la déclarer dans `EXCEPTIONS` de `tools/gen_index.py`.
- Créer d'abord les catégories manquantes, dans `CLAUDE.md`, `README.md` et le skill `bbmodel-cosmetic`.

## 2. Lancer un sous-agent Opus par pièce, en parallèle
Chaque demande contient :
- **Lectures :** `CLAUDE.md`, `docs/guide-cosmetiques.md`, `.claude/rules/retours-en-jeu.md`, puis les autres règles.
- **Python à utiliser**, avec `numpy` et `Pillow`, et `PYTHONIOENCODING=utf-8`, `PYTHONDONTWRITEBYTECODE=1`, `MODCONV=1`.
- **Référence de style :** les générateurs à inspecter et les matières à reprendre.
- **Design précis :** forme, tailles en px, couleurs, groupe de premier niveau, budget de cubes, états attendus.
- **Interdits de la pièce :** ce que l'utilisateur a refusé (ex. « pas de vertèbres »), et aucune reproduction d'un design protégé.
- **Sortie :** générateur, `.build/<nom>_opt.bbmodel`, vérificateur vert, rendus regardés en pleine taille. Ne créer ni `<nom>.bbmodel` ni `apercu/`, ne toucher ni à `tools/` ni à `.claude/` ni aux autres pièces.
- **Rapport :** états, chiffres, verdict, mesuré ou supposé, défauts restants.

## 3. Valider
Chaque rapport reste une affirmation à contrôler. Pour chaque pièce : `python tools/livrer.py cosmetiques/<categorie>/<nom>`, puis regarder `apercu/planche.png` soi-même. Renvoyer au sous-agent ce qui ne va pas. Une alerte du vérificateur sur un état non demandé (`fly`, `glide`) est normale : la signaler.

## 4. Annoncer
Un tableau : pièce, ensemble, cubes, poids, point faible. Dire ce qui n'est pas testé en jeu, et rappeler la limite de 3 cosmétiques portés. Ajouter les pièces à la liste « Livrés sans retour en jeu » de `retours-en-jeu.md`, puis les déplacer vers « validé » selon les retours.
