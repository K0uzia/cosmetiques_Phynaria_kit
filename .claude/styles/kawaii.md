# Style — Kawaii (thème Mignon, ensemble Kawaii, dit aussi « Nuage Guimauve »)

Pièces d'origine (série du 2026-11-03, aucune vue en jeu) : `oreilles_kawaii` (elle a fixé la palette), `ailes_kawaii_nuage`, `queue_kawaii`, `familier_kawaii_mochi`, `aura_kawaii`, `familier_kawaii_chat`, `ailes_kawaii_papillon`, `bulle_kawaii`. Ensemble voisin : Pâtisserie (`halo_patisserie`, `sac_patisserie`, `chapeau_patisserie`…), même thème. Ensemble déduit du mot `nuage` dans le nom, ou de `EXCEPTIONS` dans `tools/gen_index.py`. Remise aux règles le 2026-11-05. Revue du 2026-11-08 : `oreilles_kawaii` archivées, remplacées par `capuche_kawaii` « Capuche lapin-nuage » (ci-dessous).

## Esprit

**Yume kawaii** (« mignon de rêve ») : un monde de nuages, de bonbons et de peluches, doux et rassurant, un peu irréel. Tout est **rond** : pas un angle, pas une pointe (« l'angle vif est l'ennemi du mignon »). Formes de base simples (boules, gouttes, coussins), volumes **dodus**, proportions de bébé (*Kindchenschema* de Lorenz : grosse tête, grands yeux bas, petite bouche, joues rondes). **Simple** : trop de détails rend une chose mignonne inquiétante ; un motif fort par pièce (un nœud, un cœur, un liseré) vaut mieux que dix.

Éléments-signatures : bosses de nuage qui se touchent, guimauve mate, nœud lavande, cœurs dodus, reflet blanc en « fenêtre » sur ce qui brille (bulle, sucre), joues roses en ellipses douces, sucre translucide comme un vitrail de bonbon.

Ce n'est pas : du pixel art 1:1 (« trop Minecraft »), du plastique brillant partout, du fluo (*decora*, hors de l'ensemble), de la créature (pas de griffes, crocs, écailles, épines : « trop dragon »).

## Palette

Pastels et blanc, bases poussées vers le blanc (la lumière chaude du jeu les réchauffe), ombres **froides** (lavande grisée) qui empêchent le saumon de nuit. Un accent foncé au plus (bleu nuit des yeux), jamais de noir pur.

| Matière | Clair | Base | Ombre | Usage |
|---|---|---|---|---|
| Nuage / crème | (255, 255, 255) | (255, 249, 247) | (214, 202, 232) | Bosses, fourrure, plumes, pompon |
| Rose guimauve | (255, 226, 236) | (255, 210, 226) | (234, 152, 188) | Intérieur d'oreille, liserés, cœurs, joues |
| Lavande | (242, 236, 255) | (208, 192, 248) | (146, 124, 206) | Nœuds, bouts de plumes, creux |
| Menthe / ciel (accent rare) | (230, 252, 244) | (176, 232, 214) / (184, 220, 252) | (110, 180, 170) | Papillon, reflets irisés |
| Sucre translucide (`trans_`) | (255, 255, 255, 255) | teinte de bonbon, alpha 130–200 | teinte plus saturée, alpha 200–230 | Ailes de papillon, bulle |
| Lueur | (255, 236, 246) | (200, 170, 230) | — | `_e` en sources nettes, `add_` pour les auras |

Règle d'or : **une couleur de corps + une d'accent** par pièce (fiche `slimes-mascottes.md`).

## Matières

- **Nuage et guimauve** (opaques) : mats, teinte calculée depuis la normale lissée de chaque bosse (on lit une boule, pas des plaques), ombre de contact lavande entre deux bosses. Recette : peau ronde découpée par alpha autour d'une âme pleine (`queue_kawaii`, `familier_kawaii_mochi`).
- **Sucre, gelée, bulle** (translucides) : en **`trans_`** (validé en jeu sur Givre, visible avec shader), alpha 130–210, bord un peu plus clair et plus opaque (c'est le bord qui fait lire la translucidité), **un** grand reflet blanc net en haut et un petit contre-reflet ; âme ou ourlet opaque fin pour le volume.
- **Tissu (nœud, ruban)** : satin lavande, pli central plus sombre, reflet doux.
- **Lumière** : avec shader, `_e` et `add_` disparaissent (bug du mod) : les couleurs doivent être belles **dans la texture seule**. `_e` en petites sources nettes (150–225 : cœur d'un nœud, liseré de bonbon), pas de fond `_e` diffus ; pas de `_e` sur une pièce tout en `add_`.
- Texture HD 24–40 texels/px, liserés ≥ 3–4 texels.

## Mouvement

Doux, rebondi, jamais sec : **squash-and-stretch** à volume constant (s'écrase ×1,2 / ×0,8, s'étire ×0,85 / ×1,2), rebonds amortis (1–2), retard sur les bouts (oreilles, pompon). Respiration lente (4–8 s), petits frémissements de joie. Apparition (`event_equip`) en « **plop** » : échelle 0 → 1,15–1,3 → 0,92 → 1 en 0,4–0,8 s, depuis la base (la pièce pousse comme une guimauve qui gonfle). Retrait (`event_unequip`) : petite inspiration (×1,1) puis rétrécit en 0,5–1 s jusqu'à 0. Sons rares (`tools/sons.py`) : `block.amethyst_block.chime`, `entity.chicken.egg` (« plop »), `block.wool.place`, `block.honey_block.slide`.

## Effets et particules

Ce qui se détache **monte ou se dissipe** : petits cœurs, bulles, paillettes (une face, ≤ 0,8 px, Élan 100 %). Rien qui tombe et se pose hors des ailes ; depuis des ailes, quelques duvets de guimauve possibles, avec modération. Pas d'`end_rod`. Une aura kawaii est une **lueur douce** (halo pastel derrière la silhouette, voile de nuage `trans_`, sol de nuage), **jamais des objets en orbite** (refus « pas une aura »). `aura_kawaii` v3 (2026-11-08) : la v2 pastel additive était « bof » ; le motif fort est un cœur de sucre `trans_` rose franc derrière la tête, éclairé par un `add_` doux posé devant (`.claude/rules/categories/auras.md`).

## Ailes papillon (refonte du 2026-11-08)

La v2 (vitrail pastel lavande, bourrelet crème perlé, ovales) était « bof ». Refonte : vraie forme de papillon, couleurs **franches** en `trans_` (fraise (255, 88, 156) → bonbon → lilas (192, 136, 255) → ciel (132, 192, 255) vers l'apex), bordure prune (156, 44, 128) à pois blancs, frange blanche, un cœur blanc par aile (`_e` 205), chrysalide menthe à points dorés pour l'apparition. Pas encore vue en jeu.

## Ailes Nuage Guimauve (refonte du 2026-11-08)

- **Silhouette** : aile de chérubin elliptique (bras court, plumes larges à bout rond, primaires qui raccourcissent vers l'extérieur : bout rond ; bord de fuite en festons réguliers). Un nuage dodu posé sur le bras et un petit nuage à l'épaule qui cache l'attache. Différente des ailes de papillon de l'ensemble (plumes et nuage, pas de membrane).
- **Valeurs** : trois bandes seulement, lisibles à 10 blocs : nuage blanc (ombre lavande-rosée), couvertures rose framboise (248, 124, 178, liseré 204, 52, 122), rémiges lilas (204, 180, 255, liseré 130, 86, 210). Dessous : rémiges rose (255, 180, 212), sous-couvertures lilas clair. Fenêtres de reflet nettes sur le nuage et les couvertures seulement ; sur les rémiges, une bande douce (des pois sur chaque plume font « tacheté »).
- **Nuage en volume** : dôme de 3 disques empilés (0 / 0,39 / 0,70, même boule recadrée à 100 / 72 / 42 %), niveaux de profondeur en quinconce (0 / 0,49 / 0,60, calculés pour qu'aucun disque voisin ne soit à moins de 0,19 px), âme continue en prisme octogonal le long du bras, bosses tournées vers le haut sur le dessus.
- **Sources (forme d'aile chibi)** : tutoriels de dessin d'ailes d'ange simples, contour en festons et rangées qui s'allongent vers le bas, forme d'ensemble avant le détail : [Easy Drawing Guides](https://easydrawingguides.com/?p=2592665), [wikiHow, Draw Angel Wings](https://kiwix.lema.org/wikihow_en_maxi_2023-03/Draw-Angel-Wings).

## Arc de guimauve (skin d'arc, 2026-11-08)

- **Pourquoi** : arme de tir de l'ensemble, dans la même grammaire que la capuche et l'aura (couleurs franches, un motif fort : le cœur). Fiche `.claude/references/objets/arc-confiserie.md`.
- **Couleurs** : cœur framboise (150, 22, 78) / (226, 52, 118) / (255, 128, 176), brins de guimauve rose bonbon (242, 104, 166) et crème (252, 240, 244), nuages blanc ombré de lilas (150, 118, 222), plumes lilas (156, 116, 236), corde rose blanc `_e` (255, 168, 214).
- **Volume** : cœur et bosses en dôme de trois tranches de la même forme (seuils 0 / 20 / 55 % de la distance au bord, faces à 1,0 / 1,27 / 1,55 px), ombrage depuis la normale du dôme continu, âme pleine en bandes de rectangles inscrits (seules ses tranches se voient). Branches : tronçons octogonaux, phase des rayures = longueur cumulée + angle de la face, d'où une spirale continue.
- **Mouvement** : cœur qui bat (double battement, plus fort en bandant), tir en squash + twang de corde amorti, nuage de sucre qui jaillit, monte et s'efface ; arrivée en main en « plop ».

## Humeurs météo (familier nuage, 2026-11-05)

- **Arc-en-ciel** : couleurs franches et saturées, pas pastel : des bandes 186–255 en `trans_`, avec un `_e` à 55 % de la couleur, se lisent **blanches** en jeu (retour de l'utilisateur). Retenu : (232, 58, 92), (255, 140, 40), (255, 212, 40), (70, 196, 96), (50, 140, 236), (140, 84, 220), alpha ≈ 228, `_e` ≤ 30 %, pas de liseré blanc. C'est la seule exception à la palette pastel : un arc-en-ciel doit se reconnaître.
- **Humeurs** : content = arc-en-ciel (aussi en éclaircie quand la pluie cesse) ; triste ou sous la pluie = gris bleuté (`ctrl_teinte`) et crachin ; vexé (blessure) = il boude en se gonflant, petit nuage d'orage sombre, yeux plissés inclinés, mini-éclairs aux codes de l'Orage (cœur blanc, halo bleu, bord violet) arrondis aux coins. Changements en fondu, jamais brusques.
- Une pièce montrée seulement dans une humeur : `ctrl_alpha` −1 dans chaque état (et dans `attack`, pour l'aperçu), +1 là où elle apparaît.

## Lanterne-chat (familier, v3 du 2026-11-05)

- **Type** : objet animé (*tsukumogami*, lanterne qui a pris une âme), il flotte parce que la bougie chauffe l'air : il se balance comme une lanterne suspendue, ne marche jamais, ne saute pas sur l'épaule.
- **Son idée propre** : tout passe par **la flamme**. Hoquet de flamme (elle saute, il sursaute, puis glousse) ; plus vive la nuit et quand la vie du joueur est basse (il veille sur lui) ; basse sous la pluie et dans l'eau. Le papier craint l'eau : il se blottit contre le joueur sous la pluie et s'élève au-dessus de l'eau.
- **Yeux sur une surface facettée** : percer le papier (ellipse à 94 % de l'iris) et enfoncer l'œil (faces visibles : paupière +0,11, papier 0, reflet −0,11, pupille −0,22, iris −0,33, fond d'œil fermé −0,44) ; le bord du trou fait orbite et cache l'iris de biais. Une pile de plaques posée devant le papier dépasse de profil.
- **Comportements** : tirage pondéré (cases par comportement, un tiers calme) plutôt qu'uniforme.

## Capuche lapin-nuage (tête, 2026-11-08)

- **Pourquoi** : les oreilles seules (plaques pâles) se lisaient blanches et minuscules en jeu ; la capuche donne une masse ronde et colorée autour de la tête (tête plus grosse et plus ronde : schéma du bébé) et change de type de pièce (fini les accessoires posés). Les oreilles restent, et portent l'expression.
- **Couleurs franches** : corps lilas moyen (124, 98, 196) / (170, 142, 234) / (206, 188, 250), intérieur d'oreille rose bonbon (208, 86, 146) / (240, 128, 178) / (255, 178, 208), bordure crème, un cœur de sucre (`_e`) au front. Pas de pastel presque blanc sur les grandes surfaces.
- **Volume** : corps = un superellipsoïde (p = 3) circonscrit par 240 plans tangents, découpé autour de la tête par transparence, doublure lilas sombre aux faces de la découpe ; bordure = petites bouffées ellipsoïdes (90 plans) qui se fondent dans le corps (union).
- **Piège mesuré** : la compensation d'éclairage par facette (couleur × éclairage lissé ÷ éclairage de la face) **sature sur un blanc à 255** : les facettes tournées vers l'ombre ne peuvent plus s'éclaircir et la bouffée prend un aspect de dentelle grise. Garder le crème ≤ 234 (marge ×1,1) et borner la compensation des petites bouffées à 0,8–1,1.
- **Expressivité** (fiche `animaux/lapins-rongeurs.md`) : oreilles = baromètre (dressées à l'écoute, plaquées au vent et sous la pluie, basses en `sneak`, tombantes au sommeil et quand la vie baisse, `overlay_oreilles`), frémissements brefs au hasard, retard du bout (action secondaire) aux sauts et à l'atterrissage (`event_jump`, `event_land`).
- Sources : capuches et bonnets de lapin du commerce et patrons de tricot (corps + oreilles extérieur/intérieur cousus, oreilles rembourrées mais souples, cordons à pompons) : [Ravelry, Floppy Bunny Hood Bonnet](https://www.ravelry.com/patterns/library/floppy-bunny-hood-bonnet), [Lion Brand, Floppy bunny ears hat](https://www.lionbrand.com/products/floppy-bunny-ears-hat) ; action secondaire et suivi des longues oreilles : [Animation Mentor, Secondary action](https://www.animationmentor.com/blog/secondary-action-the-12-basic-principles-of-animation/), [CG Wire, Secondary action principle](https://blog.cg-wire.com/secondary-action-principle).

## Pièges

- Pointes, angles, contours sombres : plus kawaii.
- Blanc pur sur de grandes surfaces sous `_e` : tache blanche qui brûle. Garder le blanc pur aux reflets.
- Trop de couleurs à la fois (« arc-en-ciel ») : on perd la douceur ; 2 teintes + blanc.
- Plastique : multiplier les reflets ; un grand, un petit.
- Copier une mascotte connue (lapin blanc à nœud, chat à nœud rose, etc.) : composer la sienne (nuage, guimauve, bonbon).

## Sources

- [Kittl, Kawaii design guide (pastel, yume kawaii, decora)](https://www.kittl.com/blogs/kawaii-design-guide/)
- [Kore Kawaii, Yume kawaii : motifs, couleurs, matières](https://korekawaii.com/blogs/kawaii-lifestyle-blog/yume-kawaii-the-perfect-mix-of-cute-and-dreamlike)
- [Bisou Lovely, What is yume kawaii fashion](https://bisoulovely.com/blogs/bisou-blog/what-is-yume-kawaii-fashion)
- [Creative Bloq, 10 tips for kawaii character design](https://creativebloq.com/character-design/10-tips-kawaii-character-design-514833)
- [Envato Tuts+, Top tips for creating cute kawaii art](https://design.tutsplus.com/articles/10-top-tips-for-creating-cute-kawaii-art--cms-25705)
- [Thèse ZHdK (M. Galliker), kawaii et schéma du bébé](https://interactiondesign.zhdk.ch/site/assets/files/7803/thesis_manami_galliker.pdf)
- [Yuru-kyara (Wikipedia)](https://en.wikipedia.org/wiki/Yuru-kyara)
- Fiches internes : `.claude/references/creatures/slimes-mascottes.md`, `creatures/esprits-fees.md`, `animaux/lapins-rongeurs.md`, `animaux/insectes.md`, `effets/auras.md`
