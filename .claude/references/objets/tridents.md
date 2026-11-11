# Tridents (skin `trident`, guide 14)

Fiche écrite le 2026-11-08 pour `skin_trident_orage`. À lire avant tout skin de trident.

## Le trident de Minecraft (jar 26.1.2, mesuré)

- En main, Minecraft ne dessine pas une image mais le modèle d'entité `TridentModel` (`items/trident.json` : modèle spécial `minecraft:trident`, transformation (1, −1, −1)) : hampe 1 × 25 × 1, base 3 × 2 × 1, trois dents de 1 × 4 (la centrale 1 px plus haute, les latérales à ±2 px). Après retournement : pointes à y = 4, talon à y = −27, axe en x = z = 0 (coin du bloc). **31 px de long, tête de 5 px de large.**
- Display : `item/trident_in_hand.json` (3e personne (0, 60, 0) / (11, 17, −2), 1re personne (0, −90, 25) / (−3, 17, 1)) ; levé pour lancer : `item/trident_throwing.json` (3e personne (0, 90, 180) / (8, −17, 9)). Inventaire, sol, cadre : l'image plate `item/trident` (diagonale, pointe en haut à droite).
- Le mod a **un seul jeu de réglages** par skin : la pose « levé pour lancer » de Minecraft (`trident_throwing`) n'est pas reprise (supposé, comme le bouclier) ; l'étape `leve` se dessine avec les réglages en main. À voir en jeu.
- `tools/objet.py` : `affichage_trident(y_bas, y_haut)` recalcule `trident_in_hand` pour un skin modelé pointe vers +Y, axe en x = z = 8 (préréglage `_TRIDENT` = 31 px centré, y de −7,5 à 23,5). Contrôle : en 3e personne la hampe passe à 0,5 px du poing calculé pour l'épée, à 16,7 px du talon ; le trident est couché, pointes en avant, comme le vanilla.
- Étapes : `repos`, `leve` (prêt à lancer), `lance` (en vol, dessiné à sa taille sans Display, pointe en avant). En vol, seuls les `overlay_` jouent ; `event_release` au départ, particules « Au tir ».

- **Sens en main** (mesuré le 2026-11-10 par `objet.matrice_main` / `matrice_premiere` sur `affichage_trident()`, `skin_trident_steampunk`) : en 3e personne +a part devant et **+b monte** (≈ 0,86) ; en 1re personne +a monte vers l'avant (0,9) et +b descend vers l'avant (−0,42). Une vapeur ou une fumée qui doit monter part vers +b avec un peu de +a (65° : monte en 3e personne, horizontale en 1re). C'est l'inverse de la lance (`lances.md` : +b descend avec le Display de la lance d'orage).

## Le trident réel (fouëne, harpon à dents)

- Fouëne de pêche (leister) : tête forgée en fer, dents fines de section carrée chanfreinée (octogonale), **ardillons tournés vers le bas** le long des dents pour que le poisson ne glisse pas ; la dent centrale donne la force et la précision, les latérales retiennent. Nombre et taille des dents selon le poisson.
- Fourche de harpon moderne : trois dents d'acier forgé à pointe en losange, montées sur une douille vissée ou soudée.
- Pour un skin : la fourche se lit à sa **silhouette en ψ** (croissant + trois dents) dans la case ; les ardillons doivent être larges (≥ 0,6 px), sinon ils se lisent comme des éclats blancs (premier jet de `skin_trident_orage`).

## Packs 3D de la communauté (style, pas de copie)

Modèles de trident « vanilla en mieux » faits dans Blockbench (souvent par OptiFine CEM ou EMF, puisque le vanilla est un modèle d'entité) : dents en 3D au lieu de plaques, nouvelle icône d'inventaire, garde ou base plus travaillée. Ce qu'on en retient : dents en volume, base marquée, image d'inventaire nette.

## Recette (vrai volume)

`volume-3d.md` : fourche = une plaque biseautée fermée (croissant + trois dents dans un seul contour), pente unique **52°** (à 40° des dents de 1,1–1,6 px n'ont plus de plat), amincie vers les pointes (section en losange au bout), gouttières seulement là où le plat a la place (dent centrale, bras du croissant ; marge mesurée par le générateur). Pivot des éclairs repliés caché dans le croissant.

## Sources

- Jar Minecraft 26.1.2 : `assets/minecraft/items/trident.json`, `models/item/trident_in_hand.json`, `trident_throwing.json`, classe `TridentModel` (constantes relues le 2026-11-08).
- Sport Antiques, « Antique Fishing, Salmon Spear » (leister forgé, dents à ardillons) : https://sportantiques.co.uk/fishing/general-6/antique-fishing-salmon-spear
- Encycloreader, « Leister » : https://encycloreader.org/r/wikipedia.php?q=Leister
- University of Aberdeen, « Leister Fish Spear » : https://exhibitions.abdn.ac.uk/university-collections/document/18749
- Packs : « Rethoughted Trident » https://modrinth.com/resourcepack/rethoughted-trident ; « Trident Fusion » (variantes à dents plates ou en 3D) https://www.modpackindex.com/resourcepack/140505/trident-fusion
