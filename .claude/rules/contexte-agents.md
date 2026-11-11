# Règles — contexte et agents

Au-delà d'environ 150k tokens de contexte, la qualité baisse (constat de l'utilisateur, 2026-11-05) : viser 80k–120k. Règle commune aux projets Kouzia : `../kouzia-modele-site/.claude/rules/contexte-agents.md`.

- **Une pièce par agent ; une itération = un agent neuf** (les ailes d'orage v2 → v4 dans un même agent : ~500k tokens). Brief autonome : état actuel, retour de l'utilisateur mot pour mot, chemins à lire, interdits de la pièce, sortie attendue (générateur, vérificateur vert, `livrer.py`, `test_visionneuse.py`).
- Le brief pointe vers `.claude/` (règles, fiches de style, références) au lieu de recopier les règles.
- Rapport de 5 à 10 lignes avec les chemins des rendus ; **regarder soi-même** la planche et les rendus clés avant de répondre à l'utilisateur.
- Générateurs de plus de 500 lignes : lire par `grep` et plages de lignes ; ne jamais ouvrir un `.bbmodel` (texture base64) ni `index.html`.
- Lots de régénération (`livrer.py` sur plusieurs pièces) : en tâche de fond, une ligne de résultat par pièce, pas de journal complet.
- Scratchpad partagé entre agents parallèles : un sous-dossier par agent.
- Contexte lourd : noter l'état dans `retours-en-jeu.md` ou la fiche de style, puis proposer `/compact` ou une nouvelle session.
