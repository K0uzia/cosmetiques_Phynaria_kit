# Style — Pâtisserie (thème Mignon, ensemble Pâtisserie)

Série du 2026-11-03, remise aux règles le 2026-11-05. Revue du 2026-11-08 (« les trucs kawaii sont tous bof ») : `sac_patisserie`, `baguette_patisserie`, `halo_patisserie` et `chapeau_patisserie` (macaron) archivés ; restent `beret_patisserie` « Béret tartelette » (refonte de la tête) et `epaulettes_patisserie`. Aucune pièce vue en jeu à ce jour. Ensemble voisin : Kawaii (nuages, guimauve, bonbons, `.claude/references/creatures/slimes-mascottes.md`). Les noms ne suivent pas un suffixe commun : l'ensemble est donné par `EXCEPTIONS` dans `tools/gen_index.py`.

## Esprit

Des gâteaux de vitrine, pas des jouets en plastique : **appétissant** avant d'être mignon. Trois parfums qui reviennent sur toutes les pièces : **fraise** (rose, rouge confiture), **vanille** (crème, points de vanille), **chocolat** (brun chaud). Formes rondes et dodues, bords adoucis, jamais d'arête vive ni de pointe. Un visage kawaii est permis sur les pièces « personnage » (guimauves, étoile de la baguette), pas sur les gâteaux portés (donut, macaron, cupcake).

Éléments-signatures : glaçage qui coule en gouttes rondes, vermicelles multicolores, cerise brillante, collerette du macaron, spirale de sucre d'orge, poudre de sucre.

## Ce qui rend une pâtisserie appétissante (recherche du 2026-11-05)

- **La brillance d'abord** : « plus c'est brillant, plus ça donne faim » (CLIP STUDIO TIPS). Glaçage, confiture, cerise, sucre d'orge : **reflet net et blanc** (forme de fenêtre ou de virgule), contraste franc entre reflet et ombre. Le mat (pâte, coque de macaron, guimauve poudrée) se lit par des transitions douces et un contraste faible : c'est l'opposition des deux qui fait lire les matières.
- **Couleurs plus saturées que le vrai** : l'anime peint la nourriture avec un chroma plus haut que la réalité pour suggérer la fraîcheur, et sort volontiers de la palette du reste de l'image (rendu « plus délicieux que le vrai », exposition « Delicious! » du musée Ghibli). Mais pastel ≠ délavé : base claire, ombres colorées et saturées.
- **Ombres colorées et plus froides, lumière chaude** : lumière jaune chaud sur le dessus, ombres d'une teinte plus froide ou de la couleur de l'objet (rose foncé sous le glaçage, brun doré sous la pâte), jamais grises (80.lv, « The craft of hand-painted food for games »). La lumière est peinte dans la texture depuis une source fixe en haut.
- **Contours colorés** : pas de noir ; le liseré prend une version foncée et saturée de la couleur de base.
- **Couches et coupe** : on doit lire l'empilement (coque / ganache / coque ; pâte / glaçage ; caissette / crème). Ombre de recouvrement peinte sous chaque couche qui déborde.
- **Détails qui disent « fait main »** : vermicelles posés au hasard mais sans se toucher (≥ 3–4 texels de large), coulures de longueurs inégales, grain léger de la coque, bulles de la collerette (*pied*), points de vanille. Pas trop : un modèle « bruité » perd l'appétit (80.lv).
- **Macaron** : dôme lisse et mat à peine brillant, **collerette (*pied*) froissée** plus claire et régulière à la base de chaque coque, garniture (ganache, crème au beurre, confiture) un peu en retrait ou débordant légèrement. Contraste croquant / moelleux / crémeux.
- **Sucre d'orge, bonbon dur** : verre de sucre, **translucide** (le sucre refroidi vite ne cristallise pas) ; il se rend comme un verre dépoli : cœur plus saturé, bords plus clairs, reflet net, rayures opaques (crème) dans une masse translucide (fraise).
- **Guimauve** : mate, poudrée (petits points clairs), arêtes arrondies, ombre douce de contact, pas de reflet net.
- **Effets** : paillettes et petites étoiles, vapeur blanche douce qui monte (gâteau chaud), gouttes de condensation sur le froid ; les étincelles kawaii se lisent comme « magique » (CLIP STUDIO TIPS).

## Leçon du 2026-11-08 et recette « Béret tartelette »

- Pastels trop clairs = blancs en jeu : **couleurs franches** (rouge fraise (222, 30, 52), pâte dorée (228, 152, 64) à creux bruns (138, 70, 24), crème vanille (252, 206, 104), vert de sépale et de menthe). Rose layette et crème presque blanche abandonnés.
- Une pièce portée doit être **un vêtement fait de dessert**, pas un dessert posé : béret (plateau ≈ 1,5 fois la tête, porté de travers, bord roulé, queue au centre) traduit en tartelette (bord roulé = bourrelet de pâte cannelée, galette = crème, queue = fraise entière à l'envers et sa collerette).
- Fraise : face coupée en plaque découpée (peau rouge fine, chair rose, cœur blanc, fibres) + âme rouge pleine en gradins ; peau à graines jaunes en quinconce dans de petits creux ; **reflet de nappage net** (fenêtre blanche + point), seule source du calque `_e`. Fraise entière : deux plaques croisées + âme en gradins tournée de 45° ; collerette en **sépales qui retombent** (une étoile à plat ne se voit que par la tranche de côté).
- Tarte (recherche) : pâte sablée dorée et friable, crème pâtissière vanille lisse, fraises en rosace sous un nappage brillant (sources ci-dessous).

## Épaulettes v2 « fraise chantilly » (2026-11-08, pas encore vues en jeu)

Refonte de `epaulettes_patisserie` (v1 : une guimauve à visage posée sur l'épaule, petite, pâle, sans attache, « moche de ouf »). Grammaire reprise de `epaulieres_abyssales` (seules épaules validées : « bien réussie ») et traduite en pâtisserie :
- **Rang haut** : pétales de nappage fraise (238, 92, 142) en éventail qui coiffent l'épaule et **coulent en gouttes rondes de longueurs inégales** (drip cake : la goutte garde une perle ronde au bout), reflet blanc en fenêtre + point (`_e`), vermicelles posés sans se toucher, liseré framboise foncé.
- **Rang bas** : tuiles de pâte sablée au bord festonné qui descendent sur le flanc du bras (bord plus cuit, piqûres de fourchette, cristaux de sucre) ; **tranche de génoise** en vrai volume sous la racine.
- **Garniture qui remonte** (rôle des griffes de l'abyssale) : chantilly pochée à la douille cannelée = anneaux bombés empilés (dessus éclairé, dessous en creux coloré, cannelures en biais) sur 6 plaques croisées autour d'une âme fine (vue de dessus : l'étoile de la douille) ; des étages octogonaux nus se lisent « pile de cubes », à éviter. Fraise couchée et cerise : plaques croisées + âme ; rosettes de crème.
- **Attache** : ruban de chocolat à points de crème devant et derrière le bras, nœud de satin fraise devant, perle de sucre derrière, pans libres en queue d'aronde.
- Asymétrie : gauche plus chargée (grand tourbillon, fraise), droite plus légère (cerise).
- Mouvement : squash-and-stretch de la chantilly (boing au repos, écrasement à l'atterrissage), plop à l'apparition, fruits qui tombent et rebondissent.

Sources : [Pastry Living : 30 façons de pocher à la douille étoile](https://pastryliving.com/30-ways-to-pipe-with-a-star-tip/) (rosette, « kiss », cannelures) ; [Sugar Spun Run : drip au chocolat](https://sugarspunrun.com/how-to-do-a-chocolate-drip-cake) et [The Vanilla Valley : drip cake](https://thevanillavalley.co.uk/blog/drip-cake-mastery-tips-tricks-common-pitfalls) (gouttes de longueurs variées, perle ronde au bout).

## Pelle à tarte nappée (`skin_pelle_patisserie`, 2026-11-08, pas encore vue en jeu)

Skin de pelle. Ustensile réel : pelle à tarte (lame triangulaire, bord dentelé pour couper la croûte, col coudé pour glisser sous la part) et spatule coudée à manche de bois et virole. Traduction : lame d'acier brossé (±5 %), nappage fraise (246, 108, 156) qui couvre le bout et coule vers le manche en 4 gouttes larges (0,85–1,1 px) de longueurs inégales, perle bombée au bout ; des coulées fines (0,6 px) se lisaient « pistes de circuit ». Manche de hêtre (fil dans la longueur ; des stries en travers se lisaient « épi de maïs »), bout trempé dans le chocolat. Vermicelles qui montent au bloc cassé.

Sources : [Delighted Cooking : « What is a pie server? »](https://www.delightedcooking.com/what-is-a-pie-server.htm) (lame triangulaire, bord dentelé) ; [Winco : pie server à lame coudée](https://www.katom.com/080-BWPS5.html) ; [Ateco : spatule coudée à bout rond et manche de bois](https://strataportland.com/en-de/collections/tools-prep/products/ateco-pastry-spatula-thin-4-offset-rounded-tip-wood-handle).

## Fouet chantilly (`skin_masse_patisserie`, 2026-11-08, pas encore vu en jeu)

Skin de masse : un ustensile de pâtissier plutôt qu'un gâteau (fiche `.claude/references/objets/fouet-patissier.md`). Manche de hêtre verni (pâte dorée (228, 152, 64), creux (138, 70, 24), filet de vernis), virole crème-laiton (252, 206, 104), brins gainés de silicone rouge fraise (222, 30, 52) à reflet blanc, chantilly vanille (255, 240, 200) à ombre dorée (238, 178, 112) et filet de coulis, fraise nappée (reflet = seule source `_e`). Impact : farine et sucre glace qui **montent** (`emit_mc_poof`, `particle_sucre`, `ctrl_emit` dans `event_hit`), un seul son (`block.powder_snow.break`).

## Palette

| Matière | Clair | Base | Ombre | Usage |
|---|---|---|---|---|
| Glaçage fraise | (255, 236, 244) | (255, 200, 222) | (214, 112, 156) | Donut, cupcake, coques de macaron (plus mat) |
| Confiture / cerise | (255, 150, 172) | (214, 40, 78) | (96, 6, 22) | Liserés, cerise, cœurs ; brillant |
| Vanille / crème | (255, 252, 244) | (255, 240, 210) | (226, 212, 196) | Ganache, guimauve, rayures du sucre d'orge |
| Pâte dorée | (246, 208, 140) | (232, 176, 100) | (160, 98, 50) | Beignet, caissette, fond |
| Chocolat | (156, 102, 70) | (104, 60, 40) | (58, 30, 22) | Manches, bretelles, fanions |
| Vermicelles | menthe (120, 222, 192), ciel (120, 186, 248), citron (255, 226, 104), lavande (186, 150, 248), blanc, pêche (255, 156, 112) | | | Seuls accents froids, petits |

Bases poussées vers le blanc (sinon saumon sous l'éclairage chaud de nuit, `retours-en-jeu.md`). Pas de gris, pas de noir pur.

## Matières dans le mod

- **Opaque** pour tout ce qui porte la pièce (pâte, coques, guimauve, chocolat) : visible partout, shader compris.
- **`trans_`** pour ce qui est vraiment translucide : **sucre d'orge**, nappage ou gelée, perles de sucre. Alpha 150–220, rayures et reflets plus opaques, âme opaque fine au centre pour garder le volume (recette `lame_givre`). `trans_` est le seul rendu non opaque vu avec shader (Givre, 2026-11-04).
- **Calque `_e`** : la pâtisserie n'est pas lumineuse en soi. Garder un fond `_e` noir et des **sources nettes et logiques** seulement : reflet de la cerise, filet de la fourchette, cœur d'étoile magique de la baguette, paillettes. Rien de vif sur de grandes surfaces (orange violent, « bloc blanc »). Avec shader, ces lueurs disparaissent : la pièce doit rester complète sans elles.
- Texture HD 24–40 texels/px, peinte en ×4 puis LANCZOS, alpha 0/255 hors `trans_`.

## Mouvement

Moelleux et joyeux : **squash-and-stretch** à volume constant (rebond au pas, tassement à l'accroupi, « boing » de temps en temps au repos), petit vacillement d'objet posé (macaron, donut), ballottement en retard (cerise, fanions, nœud). Rien de rigide, rien de nerveux. Rotation continue (halo donut, étoile) dans un `overlay_`.

**Apparition (`event_equip`, 0,6–1,2 s)** : « plop » gourmand : la pièce sort de rien en s'écrasant puis rebondit (échelle 0 → 1,25 → 0,9 → 1, rebond amorti), la garniture arrive ensuite (glaçage qui descend et coule, cerise qui tombe et rebondit, vermicelles). Un son au plus : `entity.item.pickup`, `block.honey_block.place`, `entity.chicken.egg` (plop), `block.amethyst_block.chime` (magique, baguette).

**Sons** (`tools/sons.py`) : aucun en mouvement ; à l'attaque seulement pour la baguette.

## Particules

Rien qui tombe et se pose (pas des ailes). Paillettes et petites étoiles sucrées qui **montent** ou flottent (un cube de 0,3 px, une face, ≤ 0,8 px), vapeur douce qui monte. Pas d'`end_rod`. Vermicelles qui tomberaient : interdit ici.

## Pièges

- Pièce de tête (donut, macaron) : face intérieure à ≥ 4,62 px du centre, donc **au-dessus de y = 32,62** pour une pièce posée sur la tête (seconde couche du skin à 32,5).
- Épaules et sac : un plastron gonfle le torse et les bras d'environ 1 px ; ce qui est collé au corps est caché (`demandes_mod_2.md` §17).
- Glaçage en plaques chevauchées : faces parallèles à moins de 0,1 px = « texture qui clipe ».
- Visage sur un gâteau porté : le rend « jouet » ; réservé aux pièces-personnages.

## Sources

- [Patissland : tarte aux fraises](https://patissland.fr/en/blogs/blog-de-recettes-patissland/recette-de-la-tarte-aux-fraises) et [Sweetly Cakes : tarte aux fraises](https://sweetlycakes.com/tarte-aux-fraises) (sablée, crème pâtissière, rosace, nappage brillant)
- [Vikidia : béret](https://fr.vikidia.org/wiki/B%C3%A9ret) et [Laulhère : bérets classiques](https://www.laulhere-france.com/en/classics-berets.html) (galette, cabillou, plateau 9 à 12 pouces, porté incliné)
- [Bedrock Wiki : Blockbench](https://wiki.bedrock.dev/guide/blockbench) (ombrage peint dans la texture)

- [CLIP STUDIO TIPS : « How to Draw Mouth-Watering Anime Food »](https://tips.clip-studio.com/en-us/articles/3745) (brillance, chroma plus haut, contours colorés, vapeur, étincelles)
- [CLIP STUDIO TIPS : « How to Draw Sweets »](https://tips.clip-studio.com/zh-tw/articles/8947?org=1)
- [80.lv : « The craft of hand-painted food for games »](https://80.lv/articles/the-craft-of-hand-painted-food-for-games/) (lumière peinte, ombres froides, détail sans bruit)
- [Musée Ghibli : exposition « Delicious! Animating Memorable Meals »](https://www.ghibli-museum.jp/en/exhibitions/013127/)
- [80.lv : plats façon Ghibli dans Blender](https://80.lv/articles/how-to-cook-scrumptious-ghibli-style-dishes-in-blender)
- [Indulge With Mimi : anatomie d'un macaron](https://www.indulgewithmimi.com/anatomy-of-a-perfect-macaron/comment-page-1) (coque, *pied*, garniture)
- [Wikipédia : Sugar glass](https://en.wikipedia.org/wiki/Sugar_glass) (sucre non cristallisé, transparent)
- [Pixar RenderMan : « Gummy candy »](https://renderman.pixar.com/gummy-candy) (translucidité des bonbons)
- [Wikipédia : couleurs pastel](https://en.wikipedia.org/wiki/Pastel_(color)) (palette kawaii)
