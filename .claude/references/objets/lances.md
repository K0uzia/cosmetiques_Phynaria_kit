# Lances (skins de lance, type `lance`, guide 14)

## La lance de Minecraft (26.x, `#minecraft:spears`)

- Deux attaques : **estoc** (clic d'attaque rapide, faible, seulement jauge pleine) et **charge** (clic droit maintenu : la lance est tenue levée en avant ; les dégâts dépendent de la vitesse du joueur, très forts à cheval ou en élytres). Les deux minuteries sont séparées. Elle n'est pas lancée comme le trident.
- Pour le mod : `item_use` = lance levée pendant la charge ; `event_use_start`/`_stop` au début et à la fin ; `event_swing` à l'estoc, `event_hit` quand il touche. Étapes du type `repos`, `leve`, `lance` (la dernière sert au trident en vol : une lance ne vole pas, supposé). `q.use_progress` d'une lance : inconnu (l'utilisation n'a pas de fin, comme le trident) : ne pas s'y fier, préférer une boucle `item_use` + un événement `event_use_start` sur un autre groupe.
- Repère et Display : `skin_lance_orage` (pointe vers +Y, centrée, y de −9 à 25 ; réglages recalculés depuis `item/spear_in_hand`, validés en jeu le 2026-11-05). Reprendre `A_MIN`, `A_MAX`, la prise et `display_vanilla()` tels quels.

## Les vraies lances (pour le design)

- **Fer en feuille à section losange** : lame à deux tranchants, étroite et effilée, arête centrale (pas de table), sur une **douille conique** robuste.
- **Lance à ailes / lance à sanglier** : deux **ailettes (oreilles)** triangulaires sur la douille, derrière le fer ; elles empêchent la bête blessée de remonter le long de la hampe et l'arme de trop s'enfoncer. Silhouette très lisible : fer + petite croix à la base.
- Hampe longue, prise gainée (cuir, lanières, clous) ; talon ferré ou pointe de talon pour planter la lance au sol.

## Traduction en cubes

- Losange en vrai volume (`volume-3d.md`) : même `Piece`/`Bras` qu'une lame, mais la hauteur du « plat » suit la largeur (`h = Z_E + pente × (demi-largeur + 0,06)`) : les quatre biseaux se rejoignent sur l'arête, aucun plat n'est créé. Pente unique faible (27°, tan 0,5) pour garder 1,7 px à l'épaule et 0,2 px au bout.
- Contour convexe : prolonger les tronçons de 0,15 px aux sommets saillants, de 1,6 × la largeur du biseau seulement aux sommets rentrants (test : le prolongement du fil retombe-t-il dans le contour ?).

- **Effets qui doivent monter en main** (vapeur, fumée) : avec le Display de la lance d'orage, en 3e personne +a part devant et **+b descend** (−b monte) ; en 1re personne +a monte vers l'avant et −b descend. Une direction (0,5 a ; −0,87 b) monte en 3e personne et reste à peu près horizontale en 1re (`skin_lance_steampunk`, buse qui crache). Mesure : `objet.matrice_main(aff['thirdperson_righthand'])` et `objet.matrice_premiere(...)` appliquées aux axes du modèle.

- **Hampe longue en tours** (`skin_lance_kawaii`, 2026-11-11) : 22 px de guimauve en tours à 12 pans = tuiles hautes de ~350 texels, atlas 512 plein. Couper la hampe en tronçons d'une longueur multiple du pas de la spirale, posés sur des multiples du pas : même phase, donc **mêmes tuiles** (nom identique) ; seul le reste a les siennes. Pièce symétrique (ailes, ailettes) : l'autre côté = miroir des cubes (X' = −M X) et UV inversée en u, aucune tuile de plus (mesuré : 215 000 → 188 000 texels).

## Sources

- Wiki Minecraft, Spear / Java Edition 25w41a (estoc, charge, dégâts selon la vitesse) : https://minecraft.wiki/w/Java_Edition_25w41a , https://minecraft.fandom.com/wiki/Spear
- Bear spear, Boar spear (oreilles, fonction) : https://en.wikipedia.org/wiki/Bear_spear , https://military-history.fandom.com/wiki/Boar_spear
- Winged spearhead (fer en feuille à section losange, douille conique, deux petites ailes) : https://worcester.emuseum.com/objects/49439/winged-spearhead
- Pièces : `cosmetiques/objets/skin_lance_givre/gen_skin_lance_givre.py` (2026-11-08), `skin_lance_steampunk` (buses en ailettes, 2026-11-10).
