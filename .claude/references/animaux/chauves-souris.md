# Chauves-souris : petites insectivores, roussettes (« renards volants »)

Fiche de référence (recherche du 2026-11-04). Familiers, chapeaux (oreilles), ailes à membrane. Pour une paire d'ailes portée par le joueur : `.claude/styles/ailes-anatomie.md` et la référence validée `ailes_abyssales` (os octogonaux + membrane d'un seul tenant, `.claude/rules/categories/ailes.md`).

## 1. Silhouette et proportions

Unité : la tête (H). Au repos, une chauve-souris est un **petit corps de souris** (tête + corps ≈ 3 H) emballé dans ses ailes ; ouverte, l'envergure fait **4 à 6 fois la longueur du corps**.

| | Tête | Corps | Envergure | Oreilles | Yeux |
|---|---|---|---|---|---|
| Petite insectivore (pipistrelle, oreillard) | 1 | 2 H | 8 à 10 H | grandes : 0,8 H (oreillard : 2 H), avec un tragus (petite languette devant le conduit) | minuscules |
| Roussette (« renard volant ») | 1, **museau de renard** | 2,5 H | 10 à 12 H | petites, simples, pointues : 0,4 H | **grands**, sombres (elle voit et sent, n'écholocalise pas) |
| Chauve-souris à feuille nasale | 1 | 2 H | 8 H | grandes, mobiles | petits ; **feuille de peau** sur le nez qui dirige les cris |

Familier de 6 px de corps : tête 2 px, ailes ouvertes 12 à 16 px d'envergure (attention à l'extension), ailes repliées autour du corps : 4 px de haut.

## 2. Ce qui fait l'animal

- **L'aile est une main** : bras court, avant-bras long, et **quatre doigts très longs** qui tendent la membrane (patagium, double peau fine), qui rejoint le flanc et la patte arrière, souvent la queue. Le **pouce reste libre**, avec une griffe, au bord d'attaque (au « coude » visible de l'aile repliée). Les doigts sont l'armature visible à travers la membrane.
- **Pattes arrière tournées vers l'arrière**, petites griffes recourbées : elle pend la tête en bas sans effort (des tendons verrouillent la prise).
- Fourrure dense sur le corps seulement, membrane nue et sombre, parfois veinée.
- **Roussette ≠ petite chauve-souris** : museau long de petit chien ou de renard, grands yeux, oreilles simples ; collerette de fourrure plus claire et dorée autour du cou. Une petite chauve-souris : face écrasée, oreilles énormes, yeux perles.

## 3. Mouvement et comportement

**Base de repos** (pendue ou posée) : respiration rapide, **oreilles qui frémissent et pivotent** (plus de 20 muscles, changement de forme en un dixième de seconde), nez qui se plisse, ailes serrées en cape.

**Comportements ponctuels** :

| Geste | Durée | Détail |
|---|---|---|
| S'envelopper dans ses ailes | 1 s | les ailes se referment en cape autour du corps : froid, sommeil, sécurité |
| S'éventer | 2 à 4 s | une aile ouverte à moitié qui bat lentement contre le corps (roussette par temps chaud) |
| Toilette | 3 à 5 s | lèche la membrane, l'étire doigt par doigt ; se gratte avec le pied arrière ; nettoie les oreilles avec le pouce |
| Étirer une aile | 1,5 s | une aile s'ouvre entière, doigts écartés, puis se replie en accordéon |
| Bâillement | 1 s | petite gueule rose, crocs visibles |
| Pivot d'oreilles | 0,2 s | les deux oreilles vers un son, puis indépendantes |
| Se suspendre | 1,5 s | se retourne tête en bas en s'accrochant par les pieds |
| Ramper | 1 à 2 s | sur les pouces et les pieds, ailes repliées, allure de petit animal à quatre pattes |
| Décollage | 0,5 s | se laisse tomber et ouvre les ailes (pendue), ou saut appuyé sur les poignets (au sol) |

**Langage du corps** :
- Calme : pendue, enveloppée, yeux mi-clos, oreilles détendues.
- Curiosité : oreilles en avant et qui pivotent vite, nez qui frétille, tête qui se tourne en saccades.
- Peur, menace : ailes à demi ouvertes, gueule ouverte, crocs montrés, petits cris.
- Joie (familier) : à inventer à partir du jeu : battements courts, petits saltos en vol.
- Sommeil : enveloppée, tête rentrée, respiration lente ; tremblements au réveil (elle se réchauffe avant de voler).

**Vol** : battement ample, l'aile se replie à moitié à la remontée (la membrane se détend), frappe complète à la descente ; trajectoire en zigzags et virages serrés. Un familier lisible : 4 à 6 battements par seconde.

## 4. Version anime / stylisée

- **Proportions** : corps rond comme une boule de poils (tête et corps fondus), **oreilles énormes** (1 à 1,5 fois la tête), ailes réduites à deux éventails à trois festons, petites pointes au bout des doigts et au pouce. Pattes presque absentes.
- **Visage** : grands yeux (même pour une insectivore), petits crocs blancs qui dépassent de la bouche fermée (un ou deux : marque « malicieux mais gentil »), truffe minuscule en cœur ou en pointe.
- **Couleurs** : fourrure sombre douce (violet, gris bleuté, brun chaud), intérieur des oreilles et membrane d'un ton plus clair ou rosé, ventre plus clair. Les ambiances « mignonne effrayante » (Halloween kawaii) jouent sur le noir + rose pastel.
- **Expressions** : ailes ramenées devant la bouche (timidité), enveloppement total en « burrito » (bouderie, sommeil), oreilles qui tombent (tristesse), suspendue la tête en bas en regardant le joueur (curiosité, gag).

## 5. Traduction dans le mod

- **Hiérarchie** : `fam_*` > `corps` > `tete` (> `oreille_l/r` > `tragus`, `oeil_*`, `paupiere_*`, `machoire`) ; `bras_l` > `avantbras_l` > `doigt2_l`, `doigt3_l`, `doigt4_l`, `doigt5_l` (chacun un groupe), `pouce_l` ; idem à droite ; `patte_l/r`.
- **Membrane** : recette validée d'`ailes_abyssales` réduite : os fins octogonaux effilés (0,4 à 0,6 px pour un familier) et **membrane peinte d'un seul tenant**, découpée en plaques par alpha entre deux doigts, bord de fuite en festons, veines contrastées. Membrane en plaque fine (0,3 px), tranches transparentes. Pour une membrane translucide en contre-jour : groupe `trans_` (alpha 180 à 220), qui marche avec shader.
- **Repli** : faire tourner chaque doigt vers l'avant-bras (repli en éventail) et réduire l'échelle x de chaque plaque de membrane en même temps que les doigts se rapprochent, sinon la membrane traverse les doigts.
- **Tête en bas** : état `idle` alternatif impossible à forcer (pas de plafond) ; le faire en comportement ponctuel « suspendu au bras du joueur » ou à l'envers dans le vide sous le bras : rotation x de 180° du familier entier, ailes enveloppées.
- **Molang** : oreilles qui pivotent en saccades rapides (0,2 s) par tirage ; nuit (`q.time_of_day` entre 0,25 et 0,75) : éveillée, vole autour ; jour : enveloppée, endormie, se réveille quand le joueur court (`q.ground_speed`). Pluie : s'enveloppe.
- **Événements** : `event_equip` (sort d'une ombre ou d'un tourbillon et déplie les ailes), `event_jump` (petit battement), `hurt` (ailes qui se ferment d'un coup, cri : un seul son, `tools/sons.py`).

## 6. Pièges

- Membrane plate entre des os droits : « aile de dragon » ou parapluie. Les doigts sont courbes, la membrane se creuse entre eux, le bord de fuite fait des festons.
- Oublier le pouce griffu : on ne lit plus une main.
- Membrane qui ne rejoint pas la patte arrière : aile d'oiseau plaquée.
- Roussette avec face de petite chauve-souris (ou l'inverse) : mélange d'espèces qui se voit.
- Envergure ouverte trop grande pour un familier : extension > 60 px et collisions avec la tête du joueur. Garder 12 à 16 px.
- Battement de la membrane en entier comme une planche : il faut le repli à la remontée.

## 7. Sources

- [Animal Diversity Web, Bat wings](https://animaldiversity.org/collections/mammal_anatomy/bat_wings/)
- [Britannica, Bat: form and function](https://www.britannica.com/animal/bat-mammal/Form-and-function)
- [Encyclopedia.com, Bats: Chiroptera](https://www.encyclopedia.com/science/encyclopedias-almanacs-transcripts-and-maps/bats-chiroptera)
- [Ranger Rick, The body of a bat](https://rangerrick.org/zoobooks/the-body-of-a-bat-is-perfectly-suited-for-flying)
- [Visual Dictionary, Morphology of a bat](https://www.visualdictionaryonline.com/animal-kingdom/flying-mammal/bat/morphology-bat.php)
- [Discover Wildlife, Flying foxes](https://discoverwildlife.com/animal-facts/mammals/flying-foxes)
- [KQED Quest, Notes on fruit bats](https://www.kqed.org/quest/880/reporters-notes-for-cool-critters-fruit-bats)
- [Wikipedia, Nose-leaf](https://en.wikipedia.org/wiki/Nose-leaf)
- [Journal of Experimental Biology, Roundleaf bats coordinate noseleaf and ear](https://cob.silverchair.com/jeb/article/222/18/jeb213686/223518/Great-roundleaf-bats-coordinate-noseleaf-and-ear)
- [Indiana Public Media, Active hearing in bats](https://indianapublicmedia.org/amomentofscience/active-hearing-bats/)
- [Tuts+, How to draw a cute bat character](https://design.tutsplus.com/tutorials/how-to-draw-a-cute-bat-character-in-adobe-illustrator--cms-29432)
- [Easy Drawing Guides, How to draw a cute bat](https://easydrawingguides.com/how-to-draw-a-cute-bat/)
