# Haches (bûcheron, barbue, d'armes) — référence pour les skins d'objets

Recherche du 2026-11-08 pour `skin_hache_abyssal` (ensemble Abyssal). Sujet réel : la hache à une main et ses variantes historiques. Toute autre hache de set peut partir de cette fiche.

## Anatomie (du talon du manche au fil)

| Partie | Ce que c'est | Ce qui la fait lire |
|---|---|---|
| Fer (tête) | Coin de métal percé d'un **œil** où passe le manche | Masse sombre au bout, nettement plus large que le manche |
| Fil (bit) | Le tranchant, souvent légèrement **convexe** ; ses deux coins : le **talon** (heel, en haut) et la **pointe** (toe, en bas) | Ligne claire et nette : le point focal |
| Joues (cheeks) | Les flancs du fer ; épais vers l'œil, minces vers le fil (le fer est un coin) ; un **biseau** marque l'affûtage | Une arête parallèle au fil, plus claire |
| Barbe (beard) | Le bas du fil prolongé sous la largeur du dos, vers la main : long fil pour peu de masse, crochet pour tirer un bouclier ou une arme | Pointe qui descend le long du manche, gorge creuse au-dessus |
| Dos (poll) | L'arrière du fer, en face du fil : plat (marteau) sur une hache de bûcheron, parfois une pointe ou un bec sur une hache d'armes | Petit bloc ou crochet derrière l'œil |
| Gorge (throat) | La courbe qui relie le fer au manche sous l'œil | Creux entre la barbe et le manche |
| Attelles (langets) | Bandes de métal clouées sous la tête le long du manche, contre les coups qui le coupent | Deux traits fins sous l'œil |
| Manche (haft, helve) | Bois, souvent un peu courbe ; **ventre** (belly) et **renflement au talon** (knob) pour la prise | Long, fin, un renflement au bout |

## Variantes utiles

- **Hache de bûcheron** : fer en coin assez ouvert (fend le bois), dos plat, fil peu courbé.
- **Hache barbue** : barbe marquée, fer plus léger ; au XVe siècle elle devient une hache à une main avec un marteau au dos.
- **Grande hache d'armes à deux mains (types L et M de Petersen)** : fil de 20 à 30 cm, fer d'1 à 2 kg, **forgé très mince** (2 mm au corps, comme un couperet), « cornes » marquées au talon et à la pointe (type L : pointe lancée vers l'avant pour trancher en tirant) ; manche de 0,9 à 1,2 m.
- Fil en acier plus dur rapporté sur un corps plus doux (fer « à fil rapporté ») : idée d'un fil d'une autre matière que la joue.

## Recette dans le mod (skin d'objet)

- Image vanilla (`iron_axe.png`, Minecraft 26.1) : manche en diagonale du bas à gauche vers le haut à droite, fer en haut, **fil vers le haut à gauche**, dos vers le bas à droite. Axe du manche sur x − y = 1 (bloc vu de +Z), du talon (x + y ≈ 3) au haut du fer (x + y ≈ 27) : **≈ 17 px** ; fil à ≈ 4 px de l'axe du manche. Viser +10 à +20 % (`skin_hache_abyssal` : 20 px de manche, fer réduit pour tenir à peu près dans le carré vanilla de la 1re personne).
- Fer = peau découpée par alpha + tranches en travers dont les faces reprennent l'image peinte (coin épais à l'œil, mince au fil), fil en volume ; dos plein (un crochet fin isolé se perd dans la case de 16 px).
- Display `item/handheld` vanilla ; `gui` 0,76 pour faire tenir griffes et barbe.

## Sources

- Wikipédia, *Axe* (parties : bit, toe, heel, beard, cheek, eye, poll, haft, throat, belly, shoulder, knob, langets) : https://en.wikipedia.org/wiki/Axe
- Wikipédia, *Bearded axe* (barbe : long fil pour peu de masse, crochet ; marteau au dos au XVe siècle) : https://en.wikipedia.org/wiki/Bearded_axe
- Wikipédia, *Dane axe* (types L et M, fil de 20–30 cm, 1–2 kg, 2 mm d'épaisseur, cornes, manche 0,9–1,2 m) : https://en.wikipedia.org/wiki/Dane_axe

## Hache barbue de l'Orage (`skin_hache_orage`, 2026-11-08)

- Hache barbue à une main (skeggøx : fil de 10–20 cm, fer de 15–23 cm, 0,5–1,2 kg, manche de 60–90 cm) : barbe taillée en marches d'éclair, joue fendue par une fente en zigzag où court un trait de foudre en géométrie, talon en éperon. Fer en trois plaques (fil 0,36 px, joue 0,84, renfort 1,3 à l'œil) autour d'une âme en tranches de 0,4 px ; 19 px sur la diagonale, `gui` 0,86.
- Sources complémentaires : [Outdoor Life, anatomy of an ax](https://outdoorlife.com/articles/hunting/2014/04/visual-glossary-components-axes-and-hatchets), [USDA Forest Service, An Ax to Grind](https://fs.usda.gov/t-d/pubs/pdfpubs/pdf18232812P/Part04_Anatomy.pdf), [Medievalists.net, Viking axe](https://www.medievalists.net/2022/11/viking-axe/)

## Hache de chaudronnier (`skin_hache_steampunk`, 2026-11-10)

- Fer serti dans une roue dentée (œil) : la racine du fer et le bout du manche disparaissent dans l'épaisseur de la roue (demi-épaisseur 1,0 > demi-épaisseur du fer à la racine 0,8) ; fil biseauté seulement au-delà du rayon de la roue − 0,45 px. Dos en marteau (cylindre le long de −b), barbe courte : la silhouette reste celle de la hache de bûcheron vanilla.
- Fer « serti » : même biseau partout, mais couleur du fil (poli) seulement sur le tranchant, laiton sur le dos et la gorge (poids `actif()` de la classe `Fer`).

## Hache de sucre (`skin_hache_kawaii`, 2026-11-11)

- Fer en **une seule spline** (racine → dos → talon arrondi → fil convexe → pointe de barbe arrondie → gorge → racine) rééchantillonnée à 0,6 px : aucun sommet vif entre dos, fil et gorge (langage « pas d'angle vif »). Gouttière en croissant décalée de 1,32–1,44 px du tranchant (catmull des seuls points talon → pointe).
- Racine plongée dans un œil en plaque biseautée (cœur) : au lieu d'amincir le fer, **masquer chaque face du fer là où la surface de l'œil passe au-dessus** (`cache()` : surface de l'œil ≥ surface du fer) ; vérifier numériquement que l'œil couvre la coupe de racine (marge mesurée 0,18 px). Le fil s'arrête où le contour entre à plus de 0,35 px dans l'œil.
- À 1,05 × la garde de l'épée, le cœur-œil pèse autant que le fer dans la case : fer d'environ 7 × 6 px pour rester lu comme une hache.

