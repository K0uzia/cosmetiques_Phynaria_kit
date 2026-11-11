# Brief commun — revue de fond du 2026-11-08

Tu es un agent chargé d'**une seule pièce**. D'autres agents travaillent en parallèle sur d'autres pièces : ne touche à rien d'autre que ton dossier (et, si besoin, à une ligne d'avis dans `.claude/rules/categories/<catégorie>.md`, à la fiche de style de ton ensemble et à `cosmetiques/ensembles.json` pour ton seul ensemble). Ne commite rien. N'ouvre jamais un `.bbmodel` (base64) ni `index.html`. Générateur de plus de 500 lignes : lis-le par `grep` et plages de lignes.

## À lire d'abord
`CLAUDE.md`, `.claude/rules/essentiel.md`, `.claude/rules/retours-en-jeu.md`, `.claude/rules/delivery.md`, `.claude/rules/animation.md`, `.claude/rules/modeling.md`, `.claude/rules/fonctions-avancees.md`, le fichier de ta catégorie dans `.claude/rules/categories/`, la fiche de style de ton ensemble (`.claude/styles/`), le skill `.claude/skills/bbmodel-cosmetic/SKILL.md` (cadrage, recherche, approche par analogie), et la section du guide `docs/guide-cosmetiques.md` qui concerne ta pièce (le guide prime).

## Ce que l'utilisateur a dit (mot pour mot, 2026-11-08)
Voir la citation complète dans `.claude/references/procedures/passe-guide-2026-11-08.md`, section « Revue de fond ». Ton brief cite la partie qui te concerne.

## Méthode
1. **Se documenter vraiment** : fiches de `.claude/references/` du sujet, puis recherche web (références réelles, anime pour la magie et les effets, artistes Blockbench/Minecraft de qualité pour le style). Approche par analogie : traduire l'inspiration en spécifications d'une version 100 % originale, ne jamais citer d'œuvre dans les fichiers. Écrire ou compléter la fiche de référence, sources comprises.
2. Garder l'ancien générateur et l'ancien livrable dans `.build/gen_avant.py` et `.build/avant_livrable.bbmodel` (s'ils existent déjà, renommer les anciens en `_v<n>`, ne rien écraser).
3. Nouvelle pièce : silhouette propre à l'ensemble, belle de près **et** lisible en jeu (juger avec `apercu/jeu.png` / mode « comme en jeu », pas le rendu studio). Apparition (`event_equip`) courte qui a du sens. Sons rares (`tools/sons.py`). Lumière nette (sources logiques). Budget libre (jusqu'à 8 192 cubes, ≤ 800 Ko compressé).
4. Pipeline : générateur → `tools/optimize_bbmodel.py` → `tools/verify_bbmodel.py` (aucun FAIL) → `python tools/livrer.py <dossier>` (long : pas de limite de temps courte) → regarder `apercu/planche.png` et `apercu/jeu.png`. Une image côte à côte avant/après dans `.build/comparaison_avant_apres.png` pour une refonte.
5. Mettre à jour `fiche.json` (nom, description, lore cohérent avec le lore du set) et `reglages.json` si particules. Ajouter une ligne d'avis « pas encore vu en jeu » dans le fichier de ta catégorie.

## Rapport (6–10 lignes, en français simple)
Ce qui a changé et pourquoi, références utilisées (sans citer d'œuvre protégée dans les fichiers), chiffres (cubes, poids compressé, extension), vérificateur (WARN), 2–3 points à vérifier en jeu, chemins de `planche.png`, `jeu.png` et de la comparaison.
