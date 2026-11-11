# Pioches de mineur et marteaux pneumatiques (référence d'objet)

Pour un skin de pioche (guide 14) ou tout outil de frappe mécanique. Écrit le 2026-11-08 pour `skin_pioche_steampunk`.

## Pic de mineur (le vrai outil)
- Fer d'acier forgé à **œil** central traversé par le manche (chêne, frêne), coin enfoncé au-dessus de l'œil pour le serrer.
- Deux bras : **pointe** (casser, attaquer la roche) et, selon le modèle, seconde pointe ou **tranchant plat** (pic-hache) ; les bras se recourbent vers le manche (croissant), comme l'image vanilla.
- Pic à charbon : fer plus léger et droit, pointes amovibles dans des douilles (brevets de la fin du XIXe siècle).

## Piolet d'alpiniste (lien avec la glace)
- Tête en trois parties : **pic** (crochet pointu, dents sous le pic pour mordre la glace), **panne** (herminette : lame large à fil droit, pour tailler des marches) ou marteau de l'autre côté, trou de mousqueton ; **manche**, **pique** au pied (équilibre sur la glace), **dragonne** (sangle réglable qui tient l'outil au poignet).
- Courbure du pic : **classique** (positive, vers le manche : arrêt de glissade, piolet de marche), **inversée** (outils techniques, se retire mieux de la glace), neutre.
- Traduction (`skin_pioche_givre`, 2026-11-08) : pic à courbure classique et quatre dents en dents de scie côté manche, panne évasée à fil bombé dans le plan de l'image (perpendiculaire en vrai, mais lue par la tranche dans la case), pique de cristal, dragonne en boucle de l'anneau sous la tête à la virole haute.

## Marteau pneumatique (pic-marteau, marteau-piqueur)
- Un **piston libre** fait l'aller-retour dans un cylindre ; l'air pousse le piston contre la **queue de l'outil** (pointerolle, burin), puis une soupape inverse le flux et le renvoie ; 15 à 50 coups par seconde.
- La pointerolle est tenue dans le **nez** par un ressort de retenue (« ruche ») qui lui laisse 6 à 12 mm de jeu : elle recule contre la roche, avance au coup.
- Outil soulevé de la roche : le piston amortit sur l'air et s'arrête (pas de frappe à vide).
- Échappement de l'air à chaque coup : bouffées courtes et sèches.

## Traduction pour Minecraft (analogie, design original)
- Silhouette du croissant vanilla gardée (manche bas-gauche → haut-droite, fer en travers), un bras devient cylindre de frappe + pointerolle qui coulisse ; l'autre reste un pic recourbé.
- `item_swing` : martèlement rapide (deux frappes par 0,25 s, lisibles ; le vrai rythme est trop rapide pour une animation) ; `event_swing` : un coup franc ; `event_break` : bouffée d'échappement qui monte.
- Une chaudière au manche fournit la pression (logique mécanique), manomètre et foyer = sources de lumière nettes.

## Sources
- Piolet (pic, panne, pique, dragonne, courbures) : https://en.wikipedia.org/wiki/Ice_axe , https://www.rei.com/learn/expert-advice/ice-axe.html , https://www.bikatadventures.com/Home/Blog/all-you-need-to-know-about-an-ice-axe
- Fonctionnement, retenue de l'outil, cadence : https://www.firgelliauto.com/blogs/mechanisms/pneumatic-hammer , https://www.firgelliauto.com/blogs/mechanisms/compressed-air-hammer
- Brevets de pics de mineur (œil, douilles, pointes amovibles) : https://patents.google.com/patent/US32249A/en , https://patents.google.com/patent/US1076103A/en , https://patents.google.com/patent/US899455
- Objets de musée (pics de mineur) : https://collection.sciencemuseumgroup.org.uk/search/object_type/pickaxe
- Œil formé à la forge, oreilles de part et d'autre de l'œil, pic « pointe et ciseau » (2026-11-08, `skin_pioche_orage`) : https://patents.google.com/patent/US827432A/en , https://patents.google.com/patent/US153228 , https://www.cromwell.co.uk/shop/hand-tools/axes/pick-axe-head-3-17kg-7lb-chisel-and-point/p/SSF5226510A

## Mesuré sur `skin_pioche_kawaii` (2026-11-10)
- Œil en pièce bombée à biseaux (cœur « coussin ») : deux bras qui se rejoignent au centre ressortent dans l'échancrure et à travers les biseaux de l'œil (un plat incliné reste haut près de la racine). Mettre la racine de chaque bras à l'intérieur de l'œil, du côté du bras, amincir le bras à la racine, et vérifier numériquement que la surface du bras reste sous celle de l'œil le long de la coupe de racine.
- Bout de bras « mignon » : demi-cercle biseauté comme le reste du fil (rayon 0,55 px), lisible dans la case comme une pointe arrondie.
