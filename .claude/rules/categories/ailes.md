---
paths:
  - "cosmetiques/ailes/**"
---

# Ailes — règles, avis et recettes

Fiche documentée, à lire avant toute pièce ailée : `.claude/styles/ailes-anatomie.md`. Ailes d'anime : `.claude/references/effets/ailes-anime.md`. Intentions par état : `animation.md`, tableau des états. Réactions : les ailes gardent `attack` et `hurt` (« liées au corps, c'est normal »).

## Anatomie d'aile (base pour tout être ailé)

La fiche `ailes-anatomie.md` détaille : attache dans le haut du dos derrière l'épaule du bras, pli en Z, types d'aile, langage des ailes, apparition par `event_equip`. **Taille** : envergure déployée de 1,6 à 2,2 fois la taille du joueur (52 à 70 px), pointes repliées entre mollets et chevilles (demande de l'utilisateur, 2026-11-04).

- Humérus court qui monte en arrière, avant-bras long, main courte qui porte les primaires.
- Primaires sur la main (éventail radial), secondaires perpendiculaires au bord de fuite sur l'avant-bras, tertiaires près du corps, 2–3 rangs de couvertures côté dorsal, scapulaires qui couvrent la racine.
- Les ailes **sortent du dos** : pas de plaque ni de sac à dos permanents. Racine basse et proche de la colonne (x ≈ ±3, y ≈ 23), couverte par des scapulaires. Un boîtier dorsal n'est permis que pendant l'apparition et le retrait (`event_equip`, `event_unequip`), caché le reste du temps (échelle et recul dans le torse, éprouvés ; ou `ctrl_alpha` −1, voir `fonctions-avancees.md`).
- Pas de petits cubes volants portés par le modèle : illisibles. Utiliser des particules, ou des éclats de 3 px au moins.
- Pointe des ailes vers l'extérieur = ±X. Épaules à y ≈ 23.

## Biomécanique (pour que ça ait l'air d'une aile)

Pour une aile : écrire une seule fois l'intention dans une fonction, et centraliser le signe dans `mirror()`. Modèle : `cosmetiques/ailes/ailes_berenice/gen_ailes_berenice.py`.

- Squelette = bras : épaule → coude → poignet → bout. Bones imbriqués, chaque plume rattachée au segment qui la porte.
- Au repos : plan vertical, plumes qui pendent, léger balayage arrière en Z (humérus arrière, avant-bras revient, main repart).
- En vol : le plan bascule (voir le tableau des états d'`animation.md`) ; descente = extension complète, primaires écartées ; remontée = poignet et coude fléchis, primaires serrées.
- Cascade : coude et poignet déphasés de 0,1–0,2 cycle après l'épaule.
- Une seconde paire (plus petite) suit la grande à ~80 % d'amplitude avec un léger retard.
- Pas d'angle droit : répartir le repli sur les 3 articulations (ex. course : −30 / +18 / −22, pas 40/40/46).
- **Ne se croisent jamais** (`ailes_orage` v4 ci-dessous) : le vérificateur le mesure (`outils.md`).

## Avis de l'utilisateur

| Pièce | Avis | À retenir |
|---|---|---|
| `ailes_abyssales` | « juste incroyable », 3D et textures | Référence de style pour tout cosmétique à os et membrane |
| Ailes de Bérénice (ex-Aurelion) : forme et rondeur | « la rondeur est bien » | Plume peau + âme |
| Plume-particule des ailes de Bérénice | « ok » | Recette de particule |
| Fusée en `glide` | confirmée en jeu | V0 = 26, DV = 5, exclusion des piqués |
| `ailes_steampunk` : taille et couches (2026-11-04) | « clipping disparu », « la taille est parfaite, bien équilibrée » | Envergure 59–69 px (réduction K = 0,62 autour de l'épaule) ; lames sur une grille de 0,2 px, âmes cachées, nervure peinte |
| `ailes_orage` v1 (Vestiaire, 2026-11-05) | « reprend la structure et la silhouette du givre, faut changer la forme » ; effets d'attaque et de blessé « à revoir » | Générateur bâti sur celui d'une autre pièce : même silhouette, seule la couleur change. **Chaque ensemble a sa silhouette propre**, reconnaissable sans la couleur : comparer la planche aux ailes existantes avant de livrer. Effets d'`attack`/`hurt` : des éclairs en icônes qui flottent dans le vide et un petit sursaut ne disent rien ; l'effet naît d'un point de la pièce et la parcourt, avec anticipation, coup, gel, retour (`impacts-attaques.md`) ; clé-er tous les `ctrl_alpha` dans les animations `once` (aperçu seul juste) |
| `ailes_orage` v2 (Vestiaire, 2026-11-05) | forme ouverte « me va » ; bascule de vol ~6° « l'angle est bien, faut savoir s'adapter » ; repos en boucle « panier », texture en quadrillage de zigzags « filet », points dorés des âmes pendant `hurt` : à reprendre | Les 40° de vol d'`animation.md` sont un défaut, pas une loi : une aile dont le bras monte au-dessus de la tête bascule moins (sinon elle passe devant le visage). Pendant une coupure (`hurt`), ce qui reste visible doit rester sobre : pas de bagues dorées en « antennes perlées » |
| `ailes_orage` v4 (Vestiaire, 2026-11-05) | repos en X refusé : « les ailes fusionnent en X, hors de la logique : si j'imagine une physique, ce n'est pas possible » | **Physique plausible** : deux ailes (ou deux parties) ne se traversent jamais, ni au repos ni pendant les transitions ; chaque aile reste de son côté de la colonne. Repli d'oiseau ou d'éventail fermé, pas de croisement |
| `ailes_orage` v5 → v6 (2026-11-08) | « revoir tout, même les ailes : tu peux faire de vraies ailes en foudre directement et pas via une espèce de matériau qui forme les ailes » ; v6 **pas encore vue en jeu** | Une aile d'élément se construit **avec l'élément lui-même** (traits d'éclair en géométrie : cœur opaque + `_e`, gaine `add_`), pas avec une matière (cristal, métal) qui en a la forme. Garder l'anatomie lisible (canal = bord d'attaque, nœuds aux articulations, ramifications = rémiges) |
| `ailes_orage` v6 → v7 (2026-11-08) | v6 en traits d'éclair : « refait les ailes de d'orage je n'aime pas dutout » ; direction choisie : aile d'oiseau en métal + éclairs ; v7 **pas encore vue en jeu** | Aile « rapide » de faucon (7 primaires-lames, la 2e et la 3e depuis l'extérieur les plus longues, secondaires courtes et égales, pas de petite paire) en acier bleu-noir : fil poli, bande de revenu cuivre puis violet, liseré d'or, rachis en filet de foudre (lumière de jour) ; virgules d'or sur les seules scapulaires (or partout = trop chargé de dos). Foudre en géométrie sur la crête du bord d'attaque, décharge qui court de l'épaule à la pointe puis saute de pointe en pointe (arcs portés par la primaire de départ) |
| `ailes_tentacule` refonte (2026-11-08) | « tentacule a revoir » ; nouvelle version **pas encore vue en jeu** | Paire de 3 tentacules par côté autour d'un œil central (avant : une seule aile droite de 5 tentacules fins). Tube octogonal effilé, ventouses en relief en quinconce, onde base → pointe, pointes en crosse (`.claude/references/creatures/cephalopodes-tentacules.md`) |
| `ailes_kawaii_papillon` refonte (2026-11-08) | « les truc kawaii sont tous bof pas tres beau ou nul » ; nouvelle version **pas encore vue en jeu** | Vraie forme d'aile de papillon (antérieure triangulaire, postérieure festonnée à queue), cellule discale + nervures droites en volume, couleurs franches (fraise → lilas → ciel) en `trans_` à alpha 205–236, bordure prune à pois et frange blanche, un cœur par aile ; vol en 3 battements + plané ; apparition = éclosion d'une chrysalide (`.claude/references/animaux/insectes.md`, section 8) |
| `ailes_kawaii_nuage` refonte (2026-11-08) | « les truc kawaii sont tous bof pas tres beau ou nul » ; nouvelle version **pas encore vue en jeu** | Avant : six rangées de gouttes rose pâle et blanches de même taille et de même valeur, masse floue. Après : trois bandes de valeur seulement (nuage blanc / couvertures rose framboise / rémiges lilas ; dessous rose et lilas clair), liseré coloré franc de 4 texels, plumes larges à bout rond (aile chibi elliptique). Bosses de nuage = dôme de 3 disques (même boule recadrée) + âme continue en prisme le long du bras et bosses tournées vers le haut : des âmes séparées par bosse font une « palissade » de profil, des disques croisés des traits en croix |

## Recettes

| Élément | À éviter (constaté en jeu) | À faire |
|---|---|---|
| Lames d'éventail empilées | Âmes de 0,7 px qui dépassent des plaques espacées de 0,14 px : elles traversent les lames voisines, faces à 0,02 px, « texture qui clipe entre les plumes » en jeu et dans le Vestiaire (`ailes_steampunk`, 2026-11-04) | Une couche par lame sur une grille régulière (pas 0,2 px, plaques 0,3 px : faces toujours à 0,1 px), âme cachée dans l'épaisseur de sa plaque, nervure peinte sur la lame ; les deux sections d'une lame bout à bout dans la même couche ; pièces de structure à 0,05 px au moins des faces des lames. Les faces opposées comptent aussi (Vestiaire et, à supposer, le mod les dessinent des deux côtés) |
| Os d'aile à plumes | Barres droites apparentes, blocs à la base | Volume effilé, couvert d'écailles rondes dessus et dessous |
| Os et membrane | | Os octogonaux effilés et courbes ; membrane peinte d'un seul tenant, découpée en plaques par alpha, veines contrastées |

Leçons de remise aux règles propres aux ailes (ailes réduites par K, rangées de plumes, ailes rigides qui pivotent, aile de papillon) : `.claude/references/procedures/remise-aux-regles.md`.
