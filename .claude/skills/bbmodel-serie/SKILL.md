---
name: bbmodel-serie
description: Créer plusieurs cosmétiques d'un coup ou compléter un ensemble (« fais-moi tout ça », plusieurs pièces assorties) avec un sous-agent par pièce, puis valider et livrer le lot.
---

# Créer une série de cosmétiques

## 1. Préparer
- Lister les pièces, leur catégorie, leur ensemble et le thème de l'ensemble (thème large > ensemble précis, ex. Mignon > Kawaii, Pâtisserie). Le nom d'une pièce contient le mot de son ensemble (`abyssal`, `berenice`…), sinon lui donner un champ `"ensemble"` dans son `fiche.json`. Un nouvel ensemble s'ajoute dans `cosmetiques/ensembles.json` (nom, titre, thème, accroche, lore, couleur) et son mot dans `MOTS` de `tools/gen_index.py`.
- Créer d'abord les catégories manquantes, dans `CLAUDE.md`, `README.md` et le skill `bbmodel-cosmetic`.

- **Nouvel ensemble** : sa fiche `.claude/styles/<ensemble>.md` contient une section « Références d'ambiance » : les codes visuels étudiés (formes, couleurs, timing, mouvements) traduits en version originale, **sans nommer d'œuvre** (approche par analogie, consigne du 2026-11-06 ; détail dans `/bbmodel-cosmetic`, 1 bis), sources techniques à l'appui. Pas d'ensemble sans recherche réelle.
- **Se documenter d'abord** : fiches de `.claude/references/`, puis WebSearch pour ce qui manque (et écrire la fiche manquante), sur chaque sujet : anatomie, objet réel, comportement, matière. Mettre ce qui est appris et les sources dans la fiche de style et dans chaque demande de sous-agent (« Recherche faite »), et exiger que le sous-agent liste ses sources dans son rapport.

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
Un tableau : pièce, ensemble, cubes, poids, point faible. Dire ce qui n'est pas testé en jeu, et rappeler la limite de 3 cosmétiques portés. Ajouter les pièces à la liste « Livrés sans retour en jeu » de `.claude/references/historique-livraisons.md`, puis noter les avis dans `.claude/rules/categories/<catégorie>.md` selon les retours.
