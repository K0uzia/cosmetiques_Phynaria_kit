---
paths:
  - "cosmetiques/**"
---

# Règles — dossier d'un cosmétique, vérification et livraison

## Dossier d'un cosmétique

`cosmetiques/<categorie>/<nom>/` (`<nom>` en minuscules, sans espace ni accent) :
- `gen_<nom>.py` : le générateur, qui écrit `<nom>.png` à côté de lui et sa sortie brute dans `.build/` (`os.chdir(os.path.dirname(os.path.abspath(__file__)))` en début de script) ;
- `<nom>.bbmodel` + `<nom>.png` : le livrable optimisé et sa texture, **un seul fichier mis à jour sur place**, pas de nouveau fichier à chaque itération ;
- `<nom>_<piece>.bbmodel` : les modèles associés (ex. `ailes_berenice_plume.bbmodel`) ;
- `apercu/` : `planche.png` et `animations.gif`, chacun regroupant toutes les animations, écrasés à chaque mise à jour ;
- `fiche.json` : **obligatoire pour toute nouvelle pièce** : nom propre (« Diadème de Bérénice »), description (1–2 phrases : animations, réactions, effets), lore (2–4 phrases, original, cohérent avec le lore du set), rareté et prix (grille `cosmetiques/prix.json`, proposition à valider par le staff : `python tools/prix.py`). Lore du set dans `cosmetiques/ensembles.json` (à compléter pour tout nouvel ensemble). `livrer.py` l'embarque dans le modèle (`unhandled_root_fields.phynaria.fiche`, guide 10 bis, `tools/fiche.py`) avec les réglages des particules, puis copie le livrable sous son nom propre dans `livrables/<Ensemble>/` (`tools/exporter.py`, seul le champ `name` change ; non versionné) ;
- `.build/` : fichiers intermédiaires, jamais livrés.

## Avant toute livraison (dans cet ordre)

Dans ces commandes, `D=cosmetiques/<categorie>/<nom>`. Le livrable `$D/<nom>.bbmodel` est un fichier unique, mis à jour sur place : on travaille dans `$D/.build/` et on ne l'écrase qu'une fois tout validé.

1. `python $D/gen_<nom>.py` — doit imprimer cubes / groupes / profondeur / anims / keyframes.
2. `python tools/optimize_bbmodel.py $D/.build/<nom>_brut.bbmodel $D/.build/<nom>_opt.bbmodel`
3. `python tools/verify_bbmodel.py $D/.build/<nom>_opt.bbmodel` — **tout doit passer** (aucun FAIL ; les WARN sont à mentionner). Liste de ce qu'il contrôle : `outils.md`, Vérificateur.
4. Rendus de contrôle en **convention du mod** :
   `MODCONV=1 ANIM=idle T=1.0 python tools/render_bbmodel.py $D/.build/<nom>_opt.bbmodel idle.png 1.5`
   idem pour `fly` (T=0.6), `run` (T=0.3), `sneak` (T=0.5), `glide` (T=0.9). Assembler en planche. **Regarder la planche** avant d'envoyer.
5. Livrer : `python tools/livrer.py $D`. Il revérifie avec et sans fusée, crée `apercu/planche.png`, `apercu/animations.gif` et `apercu/etats.json`, met à jour `<nom>.bbmodel` et `index.html`. Si la vérification échoue, le livrable reste intact. Regarder la planche.

6. Particules : écrire `$D/reglages.json` (`{"particules": [{"particule", "role", "reglages": {Quand, Nombre, Départ, Dispersion, Rafale, Limite… }}]}`), affiché dans la fiche du Vestiaire (« Réglages des particules (staff) »). Les particules Minecraft n'ont que Quand, Nombre, Départ, Dispersion, Rafale et Limite. Libellés et valeurs du guide (5 ter §5 et §6), pas d'intervalle ni de valeur intermédiaire : `Nombre` 0,5/1/2/4/6/10 par seconde, `Durée` 1/3/6/10/15/20 s. `livrer.py` les **embarque** dans le modèle (`unhandled_root_fields.phynaria.particules`, identifiants du guide) ; **le mod les lit à l'import** et pré-remplit les fenêtres du staff (guide 5 ter §6) ; le vérificateur les contrôle (alerte si des particules n'ont pas de réglages).
7. Fiche : `$D/fiche.json` (`nom` propre, `description`, `lore`, `rarete`, `prix` {`pv`, `phynarium`}, `en_vente` ; facultatif : `vignette` {angle, zoom, etat, temps} pour la carte du menu, guide 10 bis, recopiée dans `phynaria.vignette`) avant `livrer.py`, puis `python tools/prix.py` (rareté et prix par la grille `cosmetiques/prix.json`, sauf `"prix_manuel": true`). Nouvel ensemble : son entrée dans `cosmetiques/ensembles.json` (nom, titre, thème, accroche, lore, couleur) ; pièce rangée hors de l'ensemble de son nom : `"ensemble"` dans `fiche.json`. `livrer.py` embarque la fiche dans le modèle (`phynaria.fiche` : `nom`, `ensemble` = « nom » de `ensembles.json`, `rarete`, `description`, `lore`, guide 10 bis ; `tools/fiche.py`, qui raccourcit à la fin d'une phrase un texte trop long et le signale), puis exporte `livrables/<Ensemble>/<Nom propre>.bbmodel` (`tools/exporter.py`, identique au livrable sauf `name`) ; `python tools/exporter.py` refait tout l'export.
8. **Skins d'objets** : `categories/objets.md`, Livraison. **Effets de téléportation** : `categories/effets.md`, Livraison.

Message de livraison, retour par capture, pas de « v+1 » : `essentiel.md`.
