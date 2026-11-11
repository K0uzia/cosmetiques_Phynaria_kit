# Pelles (bout rond, bêche) — référence pour les skins d'objets

Recherche du 2026-11-08 pour `skin_pelle_orage` (ensemble Orage). Sujet réel : la pelle de terrassier et la bêche. Toute autre pelle de set peut partir de cette fiche.

## Anatomie (de la poignée au fer)

| Partie | Ce que c'est | Ce qui la fait lire |
|---|---|---|
| Poignée | En **D** (boucle fermée, la main passe dedans) ou en **T** (traverse) ; sur les longues pelles, pas de poignée, seulement un bout renflé | Un D au talon du manche dit « pelle » plus qu'un simple bout |
| Manche (shaft) | Bois, fibre ou acier ; long (pelle de terrassier) ou court à poignée (bêche) | Long et fin |
| Douille (socket) | Tube du fer qui prend le manche, **ouvert** (fendu, plié) ou **plein**, souvent riveté ; parfois prolongé par des attelles (strapped socket) | Renflement conique entre manche et fer |
| Col (neck) et « frog » | Le col relie la douille au fer ; le **frog** est le renflement à la base du fer où il est soudé ou forgé | Point d'ornement naturel (notre tambour) |
| Angle de levée (lift) | Angle entre le fer et le manche : fort pour pelleter (soulever), faible pour creuser | Petit coup de levier quand la terre part |
| Marchepieds (treads) | Haut du fer replié ou roulé vers l'avant, là où le pied appuie | Bord épais sur les épaules, visible de profil |
| Fer (blade) | **Bout rond** (pointe arrondie : creuser), carré (ramasser), effilé (taper mouth) ; légèrement creux (cuillère) avec une **nervure** pressée dans l'axe | Masse large, plus claire au bout aiguisé |
| Fil | Le bout du fer, trempé et aiguisé : il coupe la terre et les racines | Bande claire sur l'avant du fer |

## Recette dans le mod (skin d'objet)

- Image vanilla (`iron_shovel.png`) : manche en diagonale du bas à gauche vers le haut à droite, fer en haut à droite, **≈ 18 px** ; `skin_pelle_patisserie` 20,4 px, `skin_pelle_orage` 21,8 px (+20 %, fer de 6 px de large, `gui` 0,86).
- Une pointe trop marquée et des épaules trop rabattues font lire une **pointe de lance** dans la case : bout rond (profil en ellipse) et fer large (demi-largeur ≥ 3 px à 20 px de long).
- Le geste : `item_swing` en boucle courte (on creuse vite), `event_break` = la pelletée (petit relevé du fer, quelque chose part vers le sol), sans son (on casse beaucoup de blocs).

## Pelle à neige / pelle d'avalanche (ajout du 2026-11-08, `skin_pelle_givre`)

- Fer **large et presque rectangulaire**, un peu évasé vers l'avant, **bord avant droit** (il glisse sous la neige, parfois renforcé d'une lame d'usure), **bords latéraux relevés** qui font une auge (la neige ne retombe pas sur les côtés), coins arrondis, peu ou pas de nervure.
- Manche plus court que la pelle de terrassier, **poignée en T** (pelle d'avalanche démontable) ou en D.
- Geste : pousser puis soulever et jeter la neige de côté : au bloc creusé, une gerbe qui sort de l'auge.
- Dans le mod : auge = plaque biseautée fermée posée sur une surface moyenne en creux (`gen_skin_pelle_givre.py`, `zc_b`), biseaux inclinés le long du fil (le fil monte avec l'auge).
- Sources : connaissance générale du matériel de déneigement et d'avalanche (pas de recherche web faite pour cet ajout : à compléter).

## Pelle en omoplate (ajout du 2026-11-09, `skin_pelle_abyssal`)

- Les premières pelles étaient des **omoplates de bœuf** (Néolithique, mines de silex et fossés : la pioche en bois de cerf ameublit, l'omoplate ramasse), en usage jusqu'à l'âge du fer au moins.
- Forme utile : os plat triangulaire, étroit à l'articulation (le col, emmanché), large et un peu arrondi à l'autre bout (le bord qui entre dans la terre) ; l'épine de l'omoplate fait une crête sur une face (chez nous retournée en gouttière creusée).
- Dans le mod : fer étroit au collet qui s'évase vers un bout large et rond (demi-largeur 3 px) : se lit comme une pelle et pas comme une lance ; vert seulement au bout (`gen_skin_pelle_abyssal.py`).
- Sources : Archaeology Data Service, monographie (outils d'excavation : pioche, pelle en omoplate, panier ; usage jusqu'à l'âge du fer ancien) : https://archaeologydataservice.ac.uk/catalogue/adsdata/arch-1416-1/dissemination/pdf/9781848021839_ALL.pdf ; liste Bonetools (omoplates employées comme outils, associées aux outils en bois de cerf) : https://listserv.niif.hu/pipermail/bonetools/2011-August/001507.html ; Museum Wales, pioches néolithiques en bois de cerf : https://museum.wales/collections/online/object/eb096c6a-4b17-3bcd-ab0e-499171bb6afe

## Pelle de terrassier en vrai volume (ajout du 2026-11-10, `skin_pelle_steampunk`)

- Silhouette qui dit « pelle » dans la case : **épaules larges presque droites** (perpendiculaires au manche, là où le pied appuie), flancs presque parallèles, **bout rond un peu pointu** ; fer d'environ 1,4 fois sa largeur. Plus long (9 × 5,8 px) et tout rond, il se lisait comme une cuillère ou une raquette ; la poignée en D au talon achève la lecture.
- Avec le Display `_TENU` (pelle, pioche, hache, houe), **+b (haut à gauche dans la case) descend en main** : tout ce qui fume ou monte (soupape, échappement) va vers −b. Mesuré au renderer (`MODCONV=1`) et sur l'aperçu de main ; à confirmer en 1re personne.
- Une nervure creusée à fond d'acier sombre se lit comme une fente noire : fond au ton du plat ou à peine plus sombre.

## Pelle de confiserie (ajout du 2026-11-11, `skin_pelle_kawaii`)

- Fer symétrique né d'un cœur (« frog ») : le col sort de l'échancrure entre les lobes ; un cœur aussi large que le fer (×1,05 de la hache, demi-largeur 2,4 px pour un fer de 3,0) ferait une seconde masse : réduit à ×0,85 (demi-largeur 1,9 px).
- Contour qui se lit « pelle » dans la case à 20,7 px : col étroit 0,7 px, épaules qui s'ouvrent sur ~1 px de long jusqu'à 2,9–3,0 px (coins arrondis), flancs presque parallèles sur ~3 px, ogive arrondie de ~2,8 px ; fer de 1,2 fois sa largeur depuis les épaules. Mesuré au rendu et sur l'aperçu de la case.
- Poignée en D en tours : deux barres rondes de la bague basse aux coins + une traverse ; les coins (où les barres se croisent) cachés sous des bosses de nuage. Avec `gui` 0,85 la poignée débordait de la case : 0,80.

## Sources

- Fiskars, *Anatomy of a shovel* (poignée, manche, douille, fer, marchepieds) : https://www.fiskars.com/en-us/pages/anatomy-of-a-shovel-1
- Homenish, *Different parts of a shovel* : https://www.homenish.com/?p=9174
- Wonkee Donkee Tools, *Hand shovel specifications* (poignées D et T, types de douille, fers) : https://www.wonkeedonkeetools.co.uk/shovels/a-buying-guide-hand-shovel-specifications
- Brevet *Shovel head* (douille → col → fer au frog, angle de douille : creuser ou pelleter) : https://patents.justia.com/patent/20220279692
