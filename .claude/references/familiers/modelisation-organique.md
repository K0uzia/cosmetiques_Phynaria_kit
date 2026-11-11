# Modélisation organique en cubes : un animal, pas un assemblage

Fiche de référence (recherche du 2026-11-05), écrite après le retour sur `familier_givre` v2 : « trop buggé avec de grands carrés », « on n'est pas sur un modèle 3D mais un assemblage de formes », « plus détaillé : visage, sourcils, corps, fourrure ». Les règles du dépôt (`.claude/rules/modeling.md`, `retours-en-jeu.md`) priment ; cette fiche donne la méthode et les chiffres pour un animal de 10 à 14 px.

## 1. Diagnostic des captures du 2026-11-05 (00.09.58, 00.10.03, 00.10.10)

| Ce qu'on voit | Cause dans le modèle | Principe violé |
|---|---|---|
| Pointes blanches triangulaires qui sortent du poitrail, des cuisses, des épaules, dans toutes les directions | Touffes en plaques découpées posées **en travers** de la surface, bords en dents pointues | Une mèche suit la surface et le sens du poil ; elle ne la perce pas (section 5) |
| « Grands carrés » : flancs et cuisses en larges rectangles blancs à plat | Grandes faces d'un ton uniforme, plaques dont on voit le rectangle de profil | Aucune face de plus de 1 à 2 px sans dégradé ni mèches peintes ; ombrage continu d'une pièce à l'autre (section 4) |
| Corps morcelé, arêtes vives en diagonale | Prismes « à facettes » (un cube + son jumeau tourné de 45°) : ils font cristal, pas fourrure | Sections arrondies par paliers alignés, pas par rotation à 45° (section 3) |
| Museau et truffe en boîtes posées sur la tête | Jointures bout à bout, même ton de part et d'autre de l'arête, pas de fondu | Chevauchement de 30 à 50 % et peinture en espace monde (sections 3 et 4) |
| Pattes en bâtons | Une seule boîte fine par patte | Cuisse, jambe, pied ; jarret en zigzag (section 7) |
| Visage pauvre, regard fixe | Yeux plats posés sur la face, pas d'arcade, pas de sourcils, pas de paupière inférieure | Visage construit en relief, détail concentré (section 6) |
| Queue de cristaux en éventail, illisible de dos | 17 plaques `trans_` qui se croisent | Une masse principale lisible d'abord, détail ensuite (section 2) |

## 2. Silhouette d'abord, puis masses, puis détail

- **Hiérarchie des formes** (sculpture et modélisation de personnages) : formes primaires (grandes masses : poitrail, bassin, crâne, queue), secondaires (cuisses, museau, joues, épaules), tertiaires (mèches, griffes, plis). « Aucun détail ne sauve un modèle dont les formes primaires sont ratées. »
- **Règle des trois lectures** (jeux) : la silhouette se lit en premier, à la taille d'une icône ; puis les masses de couleur, en plissant les yeux ; puis le détail, seulement s'il renforce les deux premières. Environ 70 % de l'effet d'un design vient de sa silhouette.
- **Contrôle** : rendu en noir pur des trois vues (profil, face, dessus) à 64 px de haut. Le profil doit se reconnaître comme l'animal (renard : museau effilé, oreilles hautes, dos qui descend, queue énorme). Puis rendu à la distance de jeu (familier de 40 à 60 px de haut à l'écran).
- **Formes qui s'emboîtent** : une masse posée sur une autre s'enroule autour d'elle et y pénètre, plutôt que de se poser sur son sommet. Plus les masses sont imbriquées, plus l'ensemble paraît solide.

## 3. Volumes ronds en cubes

**Section arrondie par paliers** (au lieu du cube et de son jumeau à 45°) : deux ou trois boîtes alignées sur les axes du segment, en croix.

```
largeur L, hauteur H, chanfrein c = 20 à 30 % de min(L, H) / 2
boîte 1 : L        × (H − 2c)
boîte 2 : (L − 2c) × H
(option) boîte 3 : (L − c) × (H − c)   → profil à 12 pans, encore plus rond
```

Les paliers font 0,3 à 0,6 px : à 32 texels/px et à distance de jeu, ils se lisent comme une courbe si la peinture est continue (section 4). Décaler les longueurs des boîtes d'au moins 0,05 px pour qu'aucune face d'extrémité ne soit coplanaire (`modeling.md`).

**Le long du corps** : des sections de 1,5 à 2,5 px de long, qui se chevauchent de 0,4 à 0,6 px, avec une variation de section de 15 à 20 % au plus entre deux voisines. Renard de 12 px : poitrail (le plus haut), taille (plus fine), bassin (plus large que la taille, moins haut que le poitrail).

**Jointures invisibles** : chaque pièce secondaire **commence dans** la masse qui la porte (cou dans le poitrail et dans le crâne, museau enfoncé de 40 % dans le crâne, cuisse enfoncée de 50 à 60 % dans le bassin, première section de queue dans la croupe). La section de l'enfant est un peu plus petite que celle du parent à la jonction, pour que l'arête soit cachée.

**Faces cachées** : les faces internes (dans une autre boîte) pointent sur un texel transparent : elles ne coûtent pas de texture et ne se battent pas avec les faces visibles.

**Rotations** : la courbe vient des **groupes** (os), pas des cubes. Cubes alignés dans leur groupe ; 5 à 15° entre deux segments d'un dos ou d'un cou, 10 à 20° pour une queue, 25° au plus pour une jointure visible. Éviter : un cube visible tourné sur deux ou trois axes à la fois (ses coins sortent en marches), les jumeaux à 45° (arêtes de cristal), une seule grande boîte inclinée pour tout un membre. Le guide de style Minecraft de Blockbench déconseille les courbes faites de cubes tournés pour le style vanilla ; notre style HD les utilise, mais par petits angles sur des segments imbriqués, jamais en escalier.

## 4. Peinture : ce qui fond les cubes en un seul animal

Dans Minecraft, tout l'ombrage est **peint dans la texture** ; trop subtil, le modèle paraît plat. Le style « peint à la main » des jeux (World of Warcraft, Dota 2) met lumière, occlusion et reflets dans la couleur.

**Peindre en espace monde** (procédure du générateur Python) : pour chaque face, pour chaque texel, calculer le point 3D P et la normale N, puis la couleur depuis des champs continus. Deux cubes voisins reçoivent alors la même couleur à leur frontière : la jointure disparaît.

| Champ | Formule de départ | Effet |
|---|---|---|
| Zones de pelage | masques selon P et N : ventre si N.y < −0,3 ou sous la ligne de ventre ; bavette, joues, bout de queue, chaussettes (y < 1,2 sur les pattes), dos des oreilles | Marques qui traversent les cubes sans couture |
| Dégradé dos/ventre | valeur +10 à +15 % en haut du dos, −20 à −30 % sous le ventre, selon P.y et N.y | Volume lu même sans éclairage ; dessus et avant plus clairs que dessous et arrière (règle des entités Minecraft) |
| Lumière clé | 0,5 + 0,5 · N·L, L venant du haut, de l'avant, un peu de gauche, ramené entre 0,8 et 1,08 | Forme, sans « ombrage oreiller » (chaque face ombrée depuis ses propres bords) ni « crêpe » (une face claire, l'opposée sombre) |
| Occlusion | distance d de P à la surface d'un autre cube ; si d < 0,6 px : × (1 − 0,35 · (1 − d / 0,6)) | Ombre douce aux contacts : sous la tête, aisselles, entre les cuisses, racine de la queue, creux de l'oreille |
| Sens du poil | champ F(P) : du museau vers la queue, vers le bas sur les flancs et les pattes, rayonnant sur les joues | Les mèches peintes suivent l'animal entier |
| Mèches | bruit étiré le long de F : mèches de 6 à 10 texels sur 1 à 2, ±6 à 8 % de valeur ; touffes de 0,5 à 1 px avec racine sombre nette (ombre portée) et pointe claire (ombre propre douce) | Fourrure lisible sans géométrie |

Règles de peinture du pelage (tutoriels de fourrure stylisée) : peindre par **touffes**, pas poil par poil ; établir d'abord les valeurs en gris, puis la couleur ; laisser des zones calmes où l'œil se repose ; varier la longueur des touffes selon la zone (courtes sur le museau et les pattes, longues aux joues, à la collerette, à la queue). Une ombre portée (sous une touffe) a un bord net, une ombre propre (sur le flanc) un bord doux.

**Densité de texels constante** : même nombre de texels par pixel de modèle partout, sinon les « mixels » (résolutions mêlées) trahissent l'assemblage. Tolérance : le visage peut monter à 1,25 fois la densité du corps, jamais plus de 1,5. Ne jamais étirer une texture (UV proportionnelles à la face).

**Budget de texture** (PNG ≤ 512², soit 262 144 texels) :

| Densité | Surface unique possible |
|---|---|
| 24 texels/px | 455 px² |
| 32 texels/px | 256 px² |
| 40 texels/px | 164 px² |

Un renard de 12 px a environ 300 à 400 px² de surface visible. À 32 texels/px, il faut donc : partager les UV des pièces symétriques (pattes, oreilles, yeux, joues : la peinture en espace monde se fait sur le côté gauche puis se recopie), réutiliser 4 à 6 textures de touffes pour toutes les mèches, faire pointer les faces cachées sur un texel transparent. Sinon, 24 à 28 texels/px pour le corps et 32 pour le visage.

## 5. Fourrure en volume : peu de mèches, couchées

- **Où** : seulement là où le vrai pelage casse la silhouette : joues, collerette (sous le cou), nuque, arrière des cuisses (« culotte »), coudes, bout de queue. 8 à 14 mèches pour un renard de 12 px.
- **Comment** : plaque de 0,3 px (peau découpée par alpha, tranches transparentes, `modeling.md`), **presque tangente** à la surface (15 à 25° au plus), orientée dans le sens du poil (vers l'arrière et le bas), bord intérieur enfoui d'au moins 0,5 px dans la masse, bord extérieur qui dépasse de 0,3 à 1,2 px. Contour : 3 à 5 touffes **arrondies** au bord libre seulement (pas de dents en triangle). Couleur : la même que la surface sous elle (même champ peint en espace monde), avec racine plus sombre.
- **Âme** : si la mèche dépasse de plus de 0,8 px, une âme pleine plus étroite dans son épaisseur évite l'effet « feuille » vu par la tranche (recette peau + âme des plumes).
- **Jamais** : plaques perpendiculaires à la surface, plaques en croix, pointes effilées (crénelage), mèches qui partent dans toutes les directions (pics, retour du 2026-11-05).

## 6. Visage

Le visage est ce que le joueur regarde : c'est là que vont le détail et la plus forte densité de cubes. Chiffres pour une tête de renard de 2,8 px de large (familier de 12 px, proportions anime : tête un peu agrandie).

| Élément | Construction | Dimensions de départ |
|---|---|---|
| Crâne | section arrondie (section 3), front bombé (boîte haute plus courte) | 2,8 × 2,4 × 2,4 |
| Arcades | petite boîte au-dessus de chaque œil, qui dépasse de 0,1 px : elle fait l'ombre sur l'œil | 0,9 × 0,25 × 0,3 |
| Yeux | plaque enfoncée de 0,05 à 0,1 px sous la surface (orbite) ; iris en dégradé plus sombre en haut (ombre de la paupière), pupille, deux reflets (grand en haut, petit en bas à l'opposé), cerne sombre de 1 à 2 texels | 0,85 × 0,65 (anime : 1,0 à 1,2 de large) |
| Paupières | supérieure : cube de 0,12 px devant le haut de l'œil, groupe animé en échelle y (clignement) et en rotation (plisser, s'inquiéter) ; inférieure : trait peint et léger bourrelet | 0,95 × 0,35 × 0,12 |
| Sourcils | marque peinte (pelage plus clair ou plus sombre) sur l'arcade + petite mèche de 0,3 px dans un groupe `sourcil_l` / `sourcil_r` qui tourne en z de ±15° (curieux, inquiet, fâché) | 0,7 × 0,3 |
| Museau | deux sections : base large enfoncée de 0,5 px dans le crâne, bout plus étroit ; arête du nez plus claire, côtés plus sombres | base 1,4 × 1,0, bout 1,0 × 0,8, long 1,3 |
| Truffe | cube sombre au bout, un peu en avance sur le dessus ; narines peintes, reflet brillant | 0,55 × 0,4 × 0,25 |
| Bouche | philtrum et lèvre peints (trait sombre de 2 à 3 texels qui descend de la truffe puis remonte au coin) ; mâchoire inférieure en groupe, pivot à la charnière ; langue en plaque dedans pour bâiller et haleter | mâchoire 1,0 × 0,35 × 1,1 |
| Coussinets des moustaches | zone plus claire et points sombres peints ; moustaches en 2 ou 3 traits peints, ou en plaque très fine découpée | — |
| Joues | 2 mèches tangentes de chaque côté (section 5) | — |
| Oreilles | deux ou trois boîtes empilées qui rétrécissent (cône), pointe en peau arrondie ; intérieur en plaque enfoncée de 0,1 px (creux) avec dégradé rosé, touffes claires peintes à la base ; dos sombre ; pivot à la base | 1,0 × 1,2 × 0,4 (renard polaire : plus courtes et rondes) |

Expressions : combiner paupières, sourcils, oreilles et mâchoire (curieux : sourcils levés, oreilles en avant, tête penchée ; content : paupières à demi fermées en arc, bouche entrouverte ; inquiet : sourcils obliques, oreilles plaquées).

## 7. Pattes à volume

Squelette du quadrupède : la patte avant est presque droite (épaule, coude, poignet), la patte arrière fait un **zigzag** (cuisse vers l'avant, jambe vers l'arrière, jarret, métatarse presque vertical). C'est ce zigzag qui fait « animal » et pas « table ».

| Segment | Avant | Arrière |
|---|---|---|
| Haut | épaule enfoncée dans le poitrail, 1,2 à 1,4 px de large | cuisse ronde enfoncée de 50 à 60 % dans le bassin, 1,5 × 1,8 × 1,6 |
| Milieu | avant-bras 0,7 × 0,7 × 1,4, presque vertical | jambe 0,7 px, inclinée de 25 à 30° vers l'arrière (groupe genou) |
| Bas | poignet puis pied | métatarse 0,6 px, presque vertical (groupe jarret) |
| Pied | 0,8 × 0,5 × 1,0, un peu aplati ; doigts peints (2 traits sombres), coussinet dessous | 0,8 × 0,5 × 1,1 |

Pivots aux articulations (hanche, genou, jarret ; épaule, coude), pour que la marche plie les pattes au lieu de faire tourner des bâtons.

## 8. Courbes : dos, cou, queue

- **Dos** : trois masses (poitrail, taille, bassin) dans des groupes en chaîne, 5 à 10° entre elles (le dos du renard descend doucement vers la queue).
- **Cou** : deux segments, 10 à 15° chacun, le second plus étroit, enfoncés dans le poitrail et dans le crâne.
- **Queue** : 4 à 6 segments de 1,5 à 2 px, 10 à 20° entre eux, chaque segment commencé 0,3 à 0,5 px dans le précédent. Section en croix (section 3) qui grossit jusqu'aux deux tiers puis s'arrondit au bout ; mèches peintes dans la longueur, 2 à 4 mèches tangentes sur les bords, bout de couleur différente. Ondulation en cascade, déphasage de 0,1 à 0,2 cycle par segment (`../animaux/canides.md`).

## 9. Budget de cubes (renard de 12 px)

| Partie | Cubes |
|---|---|
| Tête (crâne, arcades, yeux, paupières, sourcils, museau, truffe, mâchoire, langue, oreilles, joues) | 25 à 35 |
| Corps (trois masses de 2 ou 3 boîtes, cou) | 10 à 16 |
| Pattes (4 × 4 segments) | 16 |
| Queue | 12 à 20 |
| Mèches en volume | 8 à 14 |
| **Total** | **70 à 100** (le guide du mod conseille quelques centaines au plus pour une pièce) |

Plus de cubes ne rend pas plus organique : c'est l'emboîtement, les sections arrondies et la peinture continue qui le font.

## 10. Liste de contrôle avant livraison

1. Silhouette noire des trois vues reconnaissable.
2. Aucune jointure visible à distance de jeu : rendu de près sur le cou, le museau, les cuisses, la racine de la queue.
3. Aucune plaque qui sort de la surface en pointe ; mèches tangentes seulement, vérifiées de profil et de dessus.
4. Aucune face de plus de 1 à 2 px d'un ton uniforme.
5. Densité de texels mesurée (écart ≤ 1,25 entre pièces voisines).
6. Visage : arcade, paupières, sourcils, truffe, bouche, reflets des yeux, lisibles sur `apercu/planche.png`.
7. Pattes en trois segments, zigzag arrière visible de profil.
8. Vue par la tranche et de dessous : un volume continu, pas de « tas de feuilles » (`modeling.md`).

## 11. Sources

- [Blockbench, Minecraft Style Guide](https://www.blockbench.net/wiki/guides/minecraft-style-guide) (mixels, rotations, ombrages à éviter, dessus et avant plus clairs)
- [Blockbench, Overview & Tips](https://www.blockbench.net/wiki/guides/blockbench-overview-tips) (pivots aux articulations, hiérarchie du centre vers l'extérieur, inflate, UV par face)
- [Bedrock Wiki, Bedrock Modeling](https://wiki.bedrock.dev/visuals/bedrock-modeling) (cubes d'au moins 1 unité en vanilla, z-fighting, transparence)
- [Microsoft Learn, Blockbench pour Minecraft](https://learn.microsoft.com/en-us/minecraft/creator/documents/blockbench)
- [ModelEngine, Creating a Model](https://wiki.mythiccraft.io/modelengine/Modeling/Creating-a-Model) (limites de rotation des cubes d'objet, os sans limite)
- [Cobblemon, Creating a model](https://wiki.cobblemon.com/index.php/Tutorials/Creating_A_Model) (modèles d'entité Bedrock, noms d'animations sol / eau / air)
- [Sketchfab, Viking Shield : stylized textures using baked maps](https://sketchfab.com/blogs/community/viking-shield-creating-stylized-textures-using-baked-maps) (occlusion et dégradé du haut vers le bas peints dans la couleur)
- [Medium, Hand painted textures without painting](https://medium.com/@lettier/how-to-create-hand-painted-textures-without-painting-aa7374fef815)
- [80.lv, WoW diorama : textures, painting, lighting](https://80.lv/articles/002mrs-crafting-a-wow-diorama-textures-painting-lighting)
- [Polycount, Stylized fur](https://polycount.com/discussion/192116/stylized-fur), [Texturing fur](https://polycount.com/discussion/61314/texturing-fur)
- [Creative Bloq, How to paint fur](https://www.creativebloq.com/digital-art/master-art-painting-fur-31514473), [Furry cartoon characters](https://www.creativebloq.com/how-to/how-to-create-furry-cartoon-characters/2)
- [Draw a Box, Lesson 5 : construction appliquée aux animaux](https://drawabox.com/community/submission/TYXMVGR) (masses qui s'enroulent et s'imbriquent)
- [PressReader / 3D World, formes primaires, secondaires, tertiaires](https://www.pressreader.com/australia/3d-world/20170517/281608125351033)
- [Bugnet, Readable game art](https://bugnet.io/blog/readable-game-art-why-clarity-beats-detail) (règle des trois lectures)
- [Rocketbrush, Shape language in game character design](https://rocketbrush.com/blog/shape-language-in-game-character-design-how-to-make-characters-readable-and-consistent)
- [Medium, Character readability in TF2 and Overwatch](https://medium.com/@xavierck/character-readability-in-team-fortress-2-and-overwatch-68c41d454465)
- [Mappings.dev, FoxEntityModel](https://mappings.dev/1.14.3/net/minecraft/client/render/entity/model/FoxEntityModel.html) (structure du renard vanilla : tête, oreilles, nez, corps, 4 pattes, queue)
- [Modrinth, Alex's Mobs](https://modrinth.com/mod/2cMuAZAp), [CurseForge, Naturalist](https://www.curseforge.com/minecraft/mc-mods/naturalist/files/7985022) (mods d'animaux réputés, modèles et animations soignés ; techniques non documentées publiquement)

## 12. Leçons de la refonte v5 de `familier_givre` (2026-11-05, en cours)

Méthode « loft » (`station()` / `loft()` dans `gen_familier_givre.py`) : chaque masse = suite de stations de 0,3 à 0,5 px le long de son axe, section elliptique en 2 ou 3 boîtes (`SF3` = boîte large w × 0,58h, boîte haute 0,58w × h, boîte d'angle 0,86w × 0,86h), profil interpolé dans une table. À distance de jeu, la queue en fuseau et le tronc se lisent nettement plus organiques que la v4 ; de près, on voit des terrasses de 0,05 à 0,1 px (sculpture en voxels), plus des boîtes.

Ce qui a échoué, à ne pas refaire :
- **Bascule alternée des stations (±2 à 3,2°)** pour éviter les faces parallèles : chaque station montre son bord, « tuiles » et « écailles » sur le dos.
- **Largeurs forcées à ≥ 0,1 px d'écart entre voisines** : nervures tous les 0,5 px.
- **Boîtes de longueurs différentes dans une station (L − 0,44)** : la boîte d'angle devient plus courte que le pas, « briques » détachées le long du dos.
- **Demi-boîtes gauche/droite qui se touchent sur l'axe** avec un lacet en miroir : dessus coplanaires à la jonction.
- **Chanfrein fixe (0,22 à 0,44 px) sur de grandes sections** : la tête et le tronc restent des pavés aux coins cassés ; il faut une section proportionnelle (≈ 40 % de chaque demi-axe).

Ce qui marche :
- Dans un même os, stations **bout à bout** (pas = longueur), même orientation : flancs dans le prolongement (aucune face superposée, couture invisible avec la peinture en espace monde), bouts accolés enfouis (sonde de dégagement à 0,012 px le long de la normale, `same_bone_hidden` et `paint_face`), donc ni texture ni conflit.
- Chaque sorte de boîte **décalée de ±0,11 px le long de l'axe** (`STAG`) : jointures et bouts des trois sortes jamais dans le même plan.
- Changement d'os : recouvrement de 0,24 px et **lacet propre à l'os** (±1,6° en alternance d'un os au voisin, ±4,8° pour bavette et joues) : un tangage seul ne fait pas tourner les flancs (faces est/ouest restent parallèles).
- Paliers ≥ 0,1 px entre boîtes d'une station, sinon section simplifiée automatiquement (3 → 2 → 1 boîte).
- Boîte haute entière au centre (`sym`), boîtes large et d'angle en flancs miroirs qui ne se touchent pas : UV partagées sans conflit sur l'axe.
- Densité réduite sur les faces dont on ne voit qu'une bande (dessus de la boîte large, flancs de la boîte haute : × 0,62) et sur les bouts accolés (× 0,4) : 22 à 27 texels/px pour ~350 cubes.
- Compensation de l'éclairage par face dans la peinture (`face_shade`) : les bandes de palier tournées vers le haut assombries vers le ton du flanc.

État au 2026-11-05 soir : 350 cubes, faces proches 154 paires (99 au même texel), surtout entre pièces différentes (tronc / cuisse, tronc / bras, joues, museau). Reste aussi : tête encore carrée de face (section du crâne à arrondir davantage autour des yeux), pattes fines.

Ajouts v6 (2026-11-05, soir) :
- **Retouche automatique des stations voisines** (`loft()`) : pour chaque station d'un même os, recherche de la plus petite retouche (largeur, hauteur, centre vertical, ±0,16 px) qui garde ≥ 0,1 px entre deux sortes de boîtes différentes, décalage des centres compris ; simplification de section refaite après. Avec le lacet ±4,8° des membres contre le tronc : 154 → 16 paires, 0 au même texel.
- **Bouts de station** : un texel à moitié recouvert par la station voisine devient transparent (sinon les deux bouts accolés gardent un texel opaque au même endroit).
- **Allure × vitesse** : clés `immobile + écart·math.clamp(q.ground_speed/d,0,1)`, à simplifier dans le générateur (l'optimiseur ne touche pas aux clés Molang).
- Échec : agrandir la station avant du crâne pour couvrir yeux et sourcils rend la face encore plus carrée.


## 13. Technique « peau en facettes » (v7–v8 de `familier_givre`, 2026-11-05) — ce qui a marché

Première version lue comme « un vrai renard » par l'utilisateur (crâne rond, museau effilé, truffe ronde, collerette, corps galbé, queue en fuseau).
- **Surfaces implicites** : chaque masse = union douce (`smin`) d'ellipsoïdes et de cônes arrondis dans le repère de l'animal ; on ne modélise plus des boîtes, on décrit la forme.
- **Maillage par lancer de rayons** : anneaux autour d'un axe (`fusee`), calottes (`calotte`), surface étoilée autour d'un centre (`boule`, la tête entière d'un seul tenant). Anneaux tous les 0,2 px (tête) à 0,32–0,4 px (corps).
- **Une plaque de 0,12 px par quadrilatère**, tournée dans son plan, seule la face north peinte, découpée par alpha sur le quadrilatère : aucune marche, aucun bord visible. Pôles fermés par une plaque plate. Moitié gauche + miroir (UV partagées).
- **Faces proches** : bascule de chaque facette de 0 à 4,8° (25 choix) pour rester à ≥ 3,3° de ses voisines : même colonne sur les **trois bandes précédentes**, diagonales, deux colonnes de la bande courante, **couture du miroir** (colonnes 0–1 et leurs miroirs) et, aux **jointures** (pattes, queue), toutes les bandes du segment parent (`plaques(hist0=...)`). 1 454 → 76 (v7) → 2 paires (v8, texels transparents). Une calotte très aplatie (œil) : peu d'anneaux près du pôle, sinon ses facettes sont presque parallèles au bouchon.
- **Peinture** : normale lisse = gradient de la surface, occlusion par `f(q + N·0,35)`, compensation de l'éclairage par facette `(shade(N lisse)/shade(N facette))` bornée 0,64–1,36 (0,74–1,24 laissait des bandes).
- **Oreilles** : cône aplati (0,5 en épaisseur) large à la base (0,62) et arrondi au bout (0,17), 16 côtés ; intérieur peint (conque rosée, touffe blanche) sur la face avant. Un cylindre (rayons 0,5/0,3) se lit comme un tube.
- **Yeux** : calotte derrière un trou en amande ; peindre une **marge couleur fourrure à l'ombre** autour de l'amande au lieu de la laisser transparente (sinon on voit l'intérieur de la tête par le bord du trou, de biais).
- **Pieds** : ellipsoïde arrondi, doigts suggérés par trois sillons peints et griffes pâles.
- Chiffres v8 : ~3 700 cubes, 62 groupes, ~2,9 Mo optimisé, compressé ≈ 650–700 Ko (sous 1 000 Ko ; le budget de cubes n'a pas de plafond chez nous, le poids compressé fait la limite). Génération ≈ 5 min.
- Reste à améliorer : bords d'orbite encore marqués vus de dessous et de 3/4 haut (croissant sombre sous l'œil), bandes légères sur le front et le poitrail de face.

### Leçon des jointures (v9, 2026-11-06)

- Une peau en facettes coupée en os rigides tient au repos, pas aux grands angles : chaque jointure pliée ouvre un coin côté extérieur (largeur ≈ rayon × angle) et montre l'envers des plaques (« pile de tonneaux », disques plats). Trois règles : **≤ 20° par jointure** (répartir la courbe sur tous les segments, refaire la pose plutôt que plier fort : un sommeil en boule à 35° par jointure est impossible proprement) ; **coupe de la peau exactement dans le plan du pivot** (une plaque derrière le pivot tourne à contresens) ; **rotule** : perle centrée sur le pivot, rentrée de 0,25 px, peinte comme la peau qui la recouvre (même point ramené à la surface, sinon elle sort bleutée, couleur d'ombre).
- Le haut d'un membre qui sort du tronc quand il se replie doit être fermé (calotte), sinon son bord coupé se voit.
- Les faces proches se mesurent aussi en pose pliée : deux plaques voisines de part et d'autre d'une jointure deviennent coplanaires à un angle donné (10 à 33 paires mesurées sur les poses animées de la v9, 4 au repos).
