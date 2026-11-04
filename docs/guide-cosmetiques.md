# Créer un cosmétique pour Phynaria

Guide pour les créateurs : comment faire un cosmétique Blockbench qui s'importe du premier coup et
s'affiche en jeu exactement comme dans Blockbench, animations comprises.

Mod : Phynaria Utilities. Ce guide décrit la version Minecraft 26.1.2 (NeoForge). Les cosmétiques n'ont jamais
besoin d'une mise à jour du mod : le staff les importe sur le serveur et les joueurs les téléchargent
automatiquement.

---

## 1. En bref

- **Logiciel** : Blockbench, format **Modded Entity** (ou *Generic Model*).
- **Que des cubes** : pas de mesh.
- **Une seule texture**, PNG, 512 × 512 au maximum, enregistrée **dans** le fichier `.bbmodel`
  (plus, si besoin, une texture lumineuse `_e` : section 5 bis).
- **Placement** : le modèle se construit autour d'un joueur debout, les pieds à l'origine (0, 0, 0).
- **Groupes du corps** : un groupe de premier niveau nommé `head`, `body`, `right_arm`, `left_arm`,
  `right_leg` ou `left_leg` suit cette partie du corps. Tout le reste suit le torse.
- **Animations** : onglet *Animate* de Blockbench. Le jeu choisit l'animation selon ce que fait le
  joueur (repos, marche, vol…).
- **Effets** : groupes additifs, transparents, face caméra, à ressort et de contrôle (section 4 bis),
  texture lumineuse `_e` (5 bis), textures animées (5), reflets (5 quater), particules modélisées ou de
  Minecraft (5 ter), couches, événements et sons d'animation (6.4, 6.5).
- **Tester soi-même** : `/cosmetique apercu <fichier>` (section 12).
- **Fichier envoyé** : le `.bbmodel` lui-même, pas un export `.json`.

---

## 2. Format et outils

| Point | À faire |
|---|---|
| Format Blockbench | *Modded Entity* (recommandé) ou *Generic Model* |
| Fichier à livrer | `.bbmodel` (*Fichier › Enregistrer*), 16 Mo maximum |
| Éléments | Cubes uniquement. Un mesh fait refuser le fichier |
| UV | *Box UV* et UV par face sont acceptés tous les deux |
| Rotation | Rotation des cubes, des groupes et des faces prise en charge |
| *Inflate* | Accepté, entre −8 et 8 |

Les modèles **Java Block/Item** (chapeaux et objets réglés avec `display`) sont aussi acceptés : voir
la section 9.

---

## 3. Repères : ce qu'on voit dans Blockbench = ce qu'on voit en jeu

Le mod lit le `.bbmodel` dans les mêmes repères que la vue 3D de Blockbench, **sans inversion**. Ces
repères ont été vérifiés en jeu avec un modèle de calibration.

- Le sol est à **y = 0**, entre les pieds du joueur. La tête va de **y = 24 à y = 32**.
- Le joueur regarde vers le **nord (−Z)**. Sa droite est du côté **+X**.
- Rotation **+X** : le haut du groupe bascule vers l'arrière. **+Y** : le côté droit avance.
  **+Z** : le côté droit monte.
- Position **+Y** : monte. **+X** : vers la droite du joueur.

> ⚠️ Seul l'export Bedrock `.json` de Blockbench inverse X et Y. N'utilisez pas d'export : envoyez le
> `.bbmodel`.

**Zone autorisée** : tout (cubes, pivots) doit rester à moins de **64 px** de l'origine sur chaque axe.
Les rotations de base des cubes et des groupes sont limitées à ±360°. Les **clés d'animation** n'ont
pas cette limite : un halo peut faire plusieurs tours.

---

## 4. Suivre le corps du joueur

Le cosmétique bouge avec le joueur quand ses cubes sont rangés dans un **groupe de premier niveau**
(directement à la racine de l'*Outliner*) nommé d'après une partie du corps.

| Groupe | Suit | Autres noms acceptés |
|---|---|---|
| `head` | la tête (elle tourne avec le regard) | `hat`, `helmet` |
| `body` | le torse | `torso`, `chest` |
| `right_arm` | le bras droit | `rightarm`, `arm_right` |
| `left_arm` | le bras gauche | `leftarm`, `arm_left` |
| `right_leg` | la jambe droite | `rightleg`, `leg_right` |
| `left_leg` | la jambe gauche | `leftleg`, `leg_left` |

Majuscules, espaces et tirets sont ignorés : `Right Arm` et `right-arm` marchent aussi.

À savoir :
- **Seul le premier niveau compte.** Un groupe `head` rangé dans un autre groupe ne suit pas la tête.
- **Le pivot de ces groupes est remplacé par l'articulation du joueur** : le cou pour la tête, l'épaule
  (y = 22) pour les bras, la hanche (y = 12) pour les jambes. Inutile de le régler à la main.
- **Tout groupe ou cube qui n'a pas un de ces noms suit le torse.**
- **Pour animer un morceau à part** (une aile, une queue, une oreille), mettez-le dans **son propre
  sous-groupe**, avec le pivot placé à la jointure. Exemple :
  ```
  body
  ├── wing_left    (pivot à la base de l'aile)
  └── wing_right   (pivot à la base de l'aile)
  ```

---

## 4 bis. Groupes spéciaux (lumière, transparence, face caméra, contrôles, ressorts)

Le nom d'un groupe peut changer la façon dont il est dessiné ou bouge. Tous ces noms se mettent sur
n'importe quel groupe, à n'importe quelle profondeur, et s'appliquent aussi à ses sous-groupes.

| Préfixe | Effet | Pour |
|---|---|---|
| `add_<nom>` | **Additif** : la couleur s'ajoute à ce qu'il y a derrière (noir = invisible), en pleine lumière, sans cacher ce qui est derrière | lueurs, halos vaporeux, auras, énergie, feu « léger » |
| `trans_<nom>` | **Semi-transparent** : l'opacité de la texture (1 à 254) est respectée, faces triées | verre, glace, fumée, voiles, hologrammes, ailes de fée |
| `cam_<nom>` | **Face caméra** : le groupe tourne autour de son pivot pour que sa face avant (`south`, +Z) regarde la caméra | éclats, lueurs rondes |
| `camy_<nom>` | **Face caméra, debout** : il ne tourne qu'autour de l'axe vertical | flammes, colonnes d'énergie |
| `phys_<nom>` | **Ressort** : il balance autour de sa pose animée selon l'élan, l'arrêt et les virages du joueur | queues, capes, oreilles, chaînes, pompons |

Détails :
- **Le reste du modèle ne change pas** : sans ces préfixes, tout est dessiné comme avant (opaque, pixel
  tout ou rien).
- **`cam_` et `camy_`** : l'animation du groupe s'applique *après* l'orientation vers la caméra, donc une
  flamme peut onduler ou grandir en restant face à vous. Dans le menu Apparence, il n'y a pas de caméra :
  ces groupes y sont montrés tels quels.
- **`phys_`** : réglages dans le nom, facultatifs : `phys_queue_r40_a60`. **r** = raideur (0 très souple,
  100 raide), **a** = amortissement (0 rebondit longtemps, 100 sans rebond) ; 50 par défaut. Des groupes
  `phys_` imbriqués (une chaîne) se suivent avec un peu de retard. La pose de l'animation reste la cible.
- **Groupes de contrôle** : un groupe **vide** placé dans un groupe pilote ce groupe (et ses sous-groupes)
  par sa **position animée** (canal *position*, Molang compris). Au repos (position 0), rien ne change :
  la valeur lue est **1 + la position**.

  | Groupe vide | Pilote | Valeurs |
  |---|---|---|
  | `ctrl_alpha` | l'opacité | x = −1 : invisible, −0,5 : à moitié, 0 : normal |
  | `ctrl_teinte` | la couleur | x, y, z = rouge, vert, bleu : −1 retire la couleur, 0 normal, +1 double |
  | `ctrl_lumiere` | la force du calque `_e` | x = −1 éteint, 0 normal, +1 deux fois plus fort |
  | `ctrl_uv` | le décalage de la texture | x, y = décalage en texels (défilement avec `math.mod`) |

  L'opacité fait un vrai fondu dans un groupe `trans_` ou `add_`. Dans une partie opaque, en dessous de
  10 % la partie disparaît d'un coup (pas de demi-mesure possible en rendu opaque).

---

## 5. Texture

- **Une texture principale** dans le fichier, plus, si besoin, **une de chaque** : `<nom>_e` (lumineuse,
  section 5 bis), `<nom>_r` et `<nom>_m` (reflets, section 5 quater). Plusieurs textures principales font
  refuser le fichier.
- **PNG, 512 × 512 au maximum.** Les textures HD (UV plus petits que l'image) sont gérées.
- Elle doit être **enregistrée dans le `.bbmodel`**. Si Blockbench indique un chemin vers un fichier sur
  votre disque sans l'avoir intégrée, réenregistrez le modèle.
- **Opacité** : en dehors des groupes `trans_`, un pixel est soit opaque, soit invisible (rendu *cutout*).
  Un pixel à moitié transparent y devient opaque, ou disparaît s'il est presque transparent. Pour du verre
  ou de la fumée, utilisez un groupe `trans_` (section 4 bis).
- Une face sans texture n'est pas affichée, comme dans Blockbench. Le rapport d'import le signale.

**Textures animées** (énergie qui coule, runes, feu qui vacille, œil qui cligne) :
- Comme dans Blockbench : les images sont **empilées de haut en bas** dans la même texture (une texture
  16 × 64 pour 4 images de 16 × 16), et Blockbench l'anime tout seul.
- Le mod lit les réglages de la texture : **`frame_time`** (durée d'une image, en ticks de 1/20 s) et
  **l'ordre des images** (`frame_order`, ou boucle / à l'envers / aller-retour).
- *Interpoler* n'est pas fait : les images passent une à une (le rapport le signale).
- Limites : 64 images, 512 × 512 par image, et 1 048 576 pixels en tout (4 images de 512 × 512, 16 de
  256 × 256…). Les textures `_e` et `_r` suivent les mêmes images.
- Pour faire **défiler** une texture sans images, utilisez un `ctrl_uv` (section 4 bis).

---

## 5 bis. Faire briller un cosmétique

Deux façons, qui peuvent se combiner.

**1. Texture lumineuse `_e` (ce qui brille est choisi pixel par pixel)**
- Dans Blockbench, ajoutez une **deuxième texture** au modèle dont le nom finit par **`_e`** :
  `ailes.png` + `ailes_e.png`. C'est la même convention qu'OptiFine et Iris.
- **Même taille** que la texture principale, et **enregistrée dans le `.bbmodel`**.
- Elle sert de **calque lumineux** : peignez en couleur ce qui doit briller, en noir ou en transparent
  tout le reste. N'assignez **pas** cette texture aux faces : les faces gardent la texture principale,
  le mod superpose le calque `_e` tout seul.
- En jeu, ce calque est dessiné par-dessus le cosmétique, en pleine lumière, avec le même rendu que
  l'aura d'un creeper chargé : sa couleur **s'ajoute** à celle de la texture. Il reste visible dans le
  noir.
- **Noir = aucun effet** et transparent = aucun effet. Chaque valeur s'ajoute telle quelle : un fond à
  (40, 39, 35) éclaircit toute la zone d'environ 40, c'est une lueur douce et visible, pas un fond
  invisible. Pour que rien ne brille à un endroit, peignez-le en noir pur ou laissez-le transparent.
  Une couleur vive donne une lueur forte.
- Avec un pack de shaders (Iris, Complementary…), le calque est dessiné par le même rendu que l'aura du
  creeper chargé. Le résultat dépend du pack, et ça n'a pas encore été vérifié en jeu.
- **Une seule texture `_e` par modèle.** Le rapport d'import confirme qu'elle a été trouvée.

**2. Option « Lumineux » (tout le cosmétique)**
- Réglée par le staff dans la fenêtre *Catégorie et animations* (à l'import ou avec la roue dentée).
- Le cosmétique entier est dessiné **en pleine lumière** : il ne s'assombrit plus dans les grottes ou la
  nuit, mais il ne « rayonne » pas comme un calque `_e`.
- Pratique pour un halo, des ailes d'énergie, un objet magique entièrement lumineux.

> 💡 Pour un effet de néon : texture principale sombre + calque `_e` avec des lignes vives.
>
> 💡 Pour une aura qui laisse voir le joueur : un groupe `add_` (section 4 bis), dont la texture va du
> noir (invisible) à la couleur voulue, plutôt qu'un calque `_e`, qui ne s'ajoute qu'aux parties opaques.

---

## 5 quater. Reflets (métal, cristal, verre)

- Ajoutez une texture **`<nom>_r`** (même taille que la texture principale) : c'est le **masque de
  reflets**, du noir (mat) au blanc (miroir).
- En jeu, une **image de reflet** est ajoutée par-dessus les faces concernées, selon la direction où
  regarde chaque face par rapport à la caméra : le reflet **glisse** quand on tourne autour du joueur.
- Par défaut, le mod fournit son image (une sphère éclairée en haut à gauche, avec un liseré). Pour un
  autre rendu, ajoutez votre propre image **`<nom>_m`** (256 × 256 au plus) : c'est une *matcap*, une
  image ronde où chaque point est le reflet vu dans une direction (le centre = face tournée vers vous).
- Le masque est lu **face par face** (moyenne sur la face), pas pixel par pixel : pour qu'une partie
  brille et pas une autre, mettez-les sur des faces différentes.
- Les reflets s'ajoutent à la couleur (comme le calque `_e`) : ils éclaircissent, ils n'assombrissent
  jamais.
- **Avec les shaders** : les cartes LabPBR (`_n`, `_s`) ne sont **pas** prises en charge. Iris les
  cherche dans les packs de ressources, pas dans les textures créées par un mod.

---

## 5 ter. Particules (plumes, pétales, étincelles, fumée…)

Un cosmétique peut lancer des petits objets qui se détachent de lui : des plumes qui tombent d'ailes,
des pétales d'une couronne, des flocons d'un bonnet, des étincelles d'une baguette, de la fumée d'un
chapeau de sorcier… La forme, l'endroit d'où elles partent et leurs animations se font dans Blockbench.
Le staff règle ensuite quand et comment elles sont lancées.

**1. La forme : un groupe `particle_<nom>` à la racine**
- Par exemple `particle_plume`, `particle_petale` ou `particle_etincelle`. Le nom n'utilise que des
  lettres sans accent, des chiffres et `_`.
- Il contient les cubes d'**une seule** particule, avec la texture du cosmétique (et la texture `_e`
  si elle doit briller).
- **Le pivot du groupe** est le point autour duquel elle tourne, et celui qui touche le sol quand elle
  se pose : mettez-le sous la particule pour qu'elle repose dessus.
- Ce groupe n'est **pas porté** par le joueur : placez-le où vous voulez dans la scène, il ne sert que de
  modèle.
- **Jusqu'à 4 sortes** de particules par cosmétique.

**2. Les points de départ : des groupes vides `emit_<nom>`**
- Le nom doit correspondre à la particule : `emit_plume` lance des `particle_plume`.
- Placez-les **n'importe où dans le cosmétique** (bout des ailes, couronne, main, cheminée du chapeau…).
  Ils suivent les animations de leur groupe.
- **Le pivot du groupe** est l'endroit exact d'où part la particule.
- Pour avoir plusieurs points, ajoutez un chiffre : `emit_plume`, `emit_plume2`, `emit_plume_3`… À chaque
  particule, le mod en choisit un au hasard.
- **32 points de départ au plus** par cosmétique.

**3. Les animations de la particule (facultatives)**
- **`particle_<nom>_fall`** : jouée en boucle pendant qu'elle tombe ou monte (une plume qui tournoie, une
  étincelle qui pulse…). Animez le groupe `particle_<nom>` ou ses sous-groupes.
- **`particle_<nom>_rest`** : jouée une fois qu'elle est posée au sol.
- Sans animation de chute, la particule se balance toute seule en tombant.
- Ces animations ne sont jamais proposées pour les états du joueur.

**4. Particules de Minecraft : des groupes vides `emit_mc_<id>`**
- Un groupe vide **`emit_mc_flame`** lance la particule `flame` de Minecraft à cet endroit, et suit
  l'animation. Pas besoin de groupe `particle_` : c'est le jeu qui dessine et fait bouger la particule.
- Exemples : `emit_mc_soul_fire_flame`, `emit_mc_electric_spark`, `emit_mc_end_rod`, `emit_mc_glow`,
  `emit_mc_enchant`, `emit_mc_portal`, `emit_mc_cherry_leaves`, `emit_mc_snowflake`.
- **Poussière colorée** : `emit_mc_dust_<couleur>_<taille>`, couleur en hexadécimal et taille × 10 :
  `emit_mc_dust_ff2040_15` = rouge rosé, taille 1,5.
- Seules les particules **sans réglages** sont possibles, plus `dust`. Une particule inconnue, ou qui
  demande d'autres réglages (bloc, objet…), n'est pas lancée (une ligne dans le journal du jeu).
- Plusieurs points : donnez le même nom à plusieurs groupes (Blockbench l'accepte). Pas de chiffre au
  bout ici, il ferait partie du nom de la particule.
- **4 sortes** de particules Minecraft au plus par cosmétique, en plus des 4 sortes modélisées.

**5. Les réglages, par le staff, dans le jeu**

Après la fenêtre *Catégorie et animations*, une fenêtre par sorte de particule demande :

| Réglage | Choix | Par défaut |
|---|---|---|
| Quand | En vol, En l'air, En mouvement, À l'arrêt, Toujours, Jamais | En vol |
| Nombre | 0,5 à 10 par seconde | 2 / s |
| Durée | 1 à 20 s | 6 s |
| Mouvement | Légère, Normale, Lourde (elles tombent), Flotte (reste sur place), Monte (s'élève) | Légère |
| Au sol | Se pose, Disparaît (pour Légère, Normale et Lourde) | Se pose |
| Rendu | Opaque, Lumineux (additif, comme `add_`), Translucide (comme `trans_`) | Opaque |
| Sens | Libre, Face caméra (une plaque ne se voit plus par la tranche) | Libre |
| Fin de vie | Rétrécit, Fondu (fondu en Lumineux ou Translucide) | Rétrécit |
| Départ | Poussée (petite poussée au hasard), ou Lent / Moyen / Rapide **le long de l'axe +Y du groupe `emit_`** (orientez-le dans Blockbench) | Poussée |
| Dispersion | 0°, 15°, 45°, 180° autour de cette direction | 15° |
| Élan | part de la vitesse du joueur gardée : 0 % (sillage immobile), 40 %, 100 % (suit le joueur) | 40 % |
| Variation | Aucune, Légère, Forte : différences de taille, de rotation et de durée | Légère |
| Rafale | Aucune, À l'attaque, Blessé, Au saut, À l'atterrissage : 8 d'un coup quand ça arrive | Aucune |
| Limite | 64, 128 ou 256 particules par joueur (pour les cosmétiques rares) | 64 |

Pour les particules Minecraft, seuls *Quand*, *Nombre*, *Départ*, *Dispersion*, *Rafale* et *Limite* sont
demandés. Ces réglages se changent à tout moment avec la roue dentée, sans réimporter le modèle.

**En jeu**
- Chaque particule part de son point avec la vitesse choisie, dérive au hasard, puis tombe (ou monte).
- Si elle touche un bloc, elle se pose dessus ou disparaît. À la fin de sa durée, elle rétrécit (ou fond)
  puis disparaît.
- Elles sont calculées par le jeu de chaque joueur : **aucun coût pour le serveur**, et tout le monde
  les voit.
- Limites pour rester fluide : la limite par joueur choisie, 1 024 à l'écran, et aucune lancée par un
  joueur à plus de 48 blocs. Chaque joueur peut les couper dans ses Paramètres (« Particules des
  cosmétiques »).
- En vue à la première personne, votre propre cosmétique n'est pas dessiné par le jeu : il ne lance donc
  pas de particules pour vous à ce moment-là (les autres joueurs les voient).
- Le rapport d'import indique combien de points de départ chaque particule a. Il prévient aussi en cas
  d'oubli : une particule sans point de départ, ou un point de départ dont le nom ne correspond à
  aucune particule.

> 📁 Exemple prêt à importer : `docs/exemple_particules.bbmodel` (ailes qui lancent des plumes
> depuis le bout de chaque aile, avec une animation de chute).

---

## 6. Animations

### 6.1 Ce qui est joué

Les animations de l'onglet **Animate** sont jouées en jeu :

- **Canaux** : rotation, position et échelle des groupes.
- **Interpolations** : *linear*, *catmullrom* (courbe lissée) et *step*. Une clé *bezier* est lue comme
  *linear*.
- **Mode de boucle** (*Loop Mode*) : *loop* pour une animation en boucle. Avec *once* comme avec *hold*,
  l'animation est jouée une fois puis reste sur sa dernière image.
- **Sons** : les clés de son de la piste d'effets sont jouées (section 6.5).
- **Non joués** : les clés de particules et de script de la piste d'effets (ignorées et signalées dans le
  rapport). Pour des particules, utilisez les groupes `particle_<nom>` ou `emit_mc_` (section 5 ter).
- Une piste est rattachée à son groupe par identifiant, sinon par nom, comme dans Blockbench.

### 6.2 Une animation par état du joueur

Le staff choisit, pour chaque état, quelle animation est jouée. Pour que tout soit **pré-rempli
automatiquement à l'import**, nommez vos animations avec un de ces mots. Le mod regarde la dernière
partie du nom : `animation.ailes.vol` → `vol`.

| État | Quand | Mots reconnus |
|---|---|---|
| Immobile | le joueur ne bouge pas | `idle`, `repos`, `immobile` |
| Marche | il marche | `walk`, `marche` |
| Course | il court | `sprint`, `run`, `cours`, `course` |
| Accroupi | il est accroupi | `sneak`, `crouch`, `accroupi` |
| Vol | il vole (vol créatif) | `fly`, `vol`, `flap` |
| Élytres | il plane avec des élytres | `glide`, `elytra`, `plane` |
| Nage | il nage | `swim`, `nage` |
| En l'air | il saute ou tombe | `fall`, `jump`, `chute`, `saut` |
| Monture | il est sur une monture | `ride`, `mount`, `monture` |
| Sommeil | il dort | `sleep`, `dort`, `dodo` |
| Attaque | il frappe (joué **une fois par-dessus**) | `attack`, `swing`, `hit`, `coup` |
| Blessé | il prend un coup (joué **une fois par-dessus**) | `hurt`, `damage`, `degat`, `dégât` |

Comment le jeu choisit :
- **L'état le plus précis l'emporte** : élytres avant vol, vol avant course, course avant marche.
- **Un état sans animation** joue celle d'un état proche (élytres → vol, course → marche), sinon celle
  d'Immobile.
- **Pas d'à-coups** : un changement d'état n'est pris en compte qu'après 0,12 s, et les deux animations
  sont fondues pendant 0,2 s.
- **Rien de choisi pour Immobile** : le cosmétique joue en boucle l'animation en boucle nommée `idle`,
  sinon la première animation en boucle, sinon la première animation.

Conseils :
- Mettez les animations d'état en **loop**, et *Attaque* et *Blessé* en **once**. Une animation d'état
  sans boucle s'arrête sur sa dernière image et y reste.
- Pour attaque et blessé, animez seulement les groupes concernés : l'animation se joue par-dessus
  l'animation d'état.
- Évitez qu'un mot reconnu apparaisse par hasard dans un autre nom : `runes_idle` contient `run` et
  serait proposé pour la course. Le staff peut toujours corriger le choix à la main.

### 6.3 Molang (expressions dans les clés)

Une valeur de clé peut être un nombre ou une expression Molang, 512 caractères au maximum.

**Opérations** : `+ - * /`, parenthèses, comparaisons (`<`, `>`, `==`…), `&&`, `||`, `!`, `condition ? a : b`.

**Fonctions** : `math.sin`, `math.cos` (en degrés), `math.abs`, `math.sqrt`, `math.floor`,
`math.ceil`, `math.round`, `math.trunc`, `math.min`, `math.max`, `math.mod`, `math.pow`,
`math.clamp`, `math.lerp`, `math.atan`, `math.atan2`, `math.exp`, `math.random(a, b)`,
`math.random_integer(a, b)`, et la constante `math.pi`. `math.random` donne une nouvelle valeur à chaque
image : pour un hasard fixe par joueur, utilisez `query.instance_seed`.

**Variables mémorisées** : plusieurs instructions séparées par `;`. `v.nom = …;` (ou `variable.nom`)
garde une valeur d'une image à l'autre, et la valeur de la clé est celle de la dernière instruction
(`return` facultatif). Une variable jamais écrite vaut 0. Elles sont calculées une fois par image et par
joueur. Exemple de lissage :
```
v.angle = math.lerp(v.angle, query.yaw_speed * 0.3, 0.1); v.angle
```

**Variables** (préfixe `q.` accepté à la place de `query.`) :

| Variable | Valeur |
|---|---|
| `query.anim_time` | temps écoulé dans l'animation (secondes) |
| `query.life_time` | temps depuis que le cosmétique est porté (ne boucle pas : utile pour un mouvement irrégulier) |
| `query.ground_speed` | vitesse au sol (blocs par seconde) |
| `query.vertical_speed` | vitesse verticale (blocs par seconde) |
| `query.health` / `query.max_health` | vie actuelle et vie maximale |
| `query.is_on_ground`, `query.is_sneaking`, `query.is_flying`, `query.is_sprinting`, `query.is_swimming`, `query.is_gliding`, `query.is_riding`, `query.is_sleeping` | 1 si vrai, 0 sinon |
| `query.is_boosting` | 1 pendant qu'une fusée pousse le vol en élytres, 0 sinon |
| `query.yaw_speed` | vitesse de rotation du corps (degrés par seconde) : ailes et queues qui s'inclinent dans les virages |
| `query.head_x_rotation`, `query.head_y_rotation` | regard : haut/bas, et rotation de la tête par rapport au corps (degrés) |
| `query.time_of_day` | heure : 0 à midi, 0,25 au coucher, 0,5 à minuit, 0,75 au lever |
| `query.moon_phase` | phase de la lune, 0 (pleine) à 7 |
| `query.is_in_rain`, `query.is_in_water`, `query.is_in_lava`, `query.is_first_person` | 1 si vrai, 0 sinon |
| `query.hurt_time`, `query.attack_time` | de 0 à 1 pendant un coup reçu / un coup porté, 0 sinon |
| `query.instance_seed` | nombre fixe de 0 à 1, différent pour chaque joueur : deux joueurs ne bougent pas en même temps |
| `query.distance_to_camera` | distance à la caméra (blocs) |
| `query.land_speed` | vitesse de chute au dernier atterrissage (blocs par seconde), pour `event_land` |
| `query.delta_time` | secondes depuis l'image précédente, pour des lissages réguliers |

Une variable inconnue vaut 0. Une expression invalide est remplacée par la valeur neutre (0, ou 1 pour
l'échelle) et signalée dans le rapport d'import.

Exemples :
```
math.sin(query.anim_time * 360) * 10                    // balancement de ±10° par seconde
math.clamp(query.ground_speed * 8, 0, 30)               // les ailes s'ouvrent avec la vitesse
query.is_sneaking ? 15 : 0                              // se replie quand on s'accroupit
math.sin(query.life_time * 90) * math.sin(query.life_time * 37) * 5   // flottement irrégulier
1 + (query.health / query.max_health) * 0.2             // échelle qui suit la vie
math.sin(query.anim_time * 360 + query.instance_seed * 360) * 10   // même mouvement, décalé par joueur
query.time_of_day > 0.25 && query.time_of_day < 0.75 ? 1 : 0       // seulement la nuit
```

### 6.4 Couche permanente et événements

- **`overlay_<nom>`** : animation **jouée tout le temps, par-dessus** l'animation d'état, sans fondu ni
  remise à zéro quand l'état change. C'est la bonne place pour une rotation continue (halo, anneau) ou une
  pulsation : elle ne saute plus entre deux états. Mettez-la en *loop*. Plusieurs couches sont possibles.
- **`event_<événement>`** : animation **jouée une fois par-dessus** quand l'événement arrive :

  | Nom | Quand |
  |---|---|
  | `event_jump` | le joueur saute |
  | `event_land` | il atterrit (`query.land_speed` = vitesse de chute) |
  | `event_equip` | le cosmétique apparaît (mis, ou joueur qui arrive) |
  | `event_enter_<état>`, `event_exit_<état>` | il entre dans un état ou en sort : `event_enter_glide`, `event_exit_glide`, `event_enter_sneak`… (états de la section 6.2, en anglais : idle, walk, sprint, sneak, fly, glide, swim, fall, ride, sleep) |

- Les rotations et positions de ces animations s'**ajoutent** à celles de l'état, les échelles se
  multiplient.
- Elles ne sont jamais proposées pour les états du joueur.

### 6.5 Sons

- Dans Blockbench, ajoutez des **clés de son** dans la piste *Effets* de l'animation. Le champ *Effet* doit
  contenir le **nom d'un son de Minecraft** : `entity.phantom.flap`, `block.amethyst_block.chime`,
  `item.armor.equip_elytra`… (`minecraft:` facultatif). Le mod ne peut pas jouer de fichiers son à vous :
  le jeu ne les a pas.
- Le son est joué quand l'animation passe sur la clé, à chaque tour pour une animation en boucle. Il est
  entendu autour du joueur, par chacun dans son jeu.
- Le staff règle le **volume** du cosmétique (0, 25, 50 ou 100 %) dans la fenêtre *Catégorie et
  animations*. Chaque joueur peut couper les sons des cosmétiques dans ses Paramètres.
- 32 sons au plus par animation. Un nom invalide est ignoré et signalé dans le rapport.

---

## 7. Limites

| Élément | Maximum |
|---|---|
| Fichier `.bbmodel` à l'import | 16 Mo |
| Fichier une fois nettoyé et compressé par le serveur | 1 000 Ko |
| Cubes | 8 192 |
| Groupes | 2 048 |
| Niveaux d'imbrication des groupes | 64 |
| Texture | 1 principale, PNG 512 × 512 (+ 1 `_e` et 1 `_r` de même taille, + 1 `_m` de 256 × 256) |
| Texture animée | 64 images, 512 × 512 par image, 1 048 576 pixels en tout |
| Sons | 32 par animation |
| Instructions Molang (`;`) | 16 par clé, 64 variables par cosmétique et par joueur |
| Distance à l'origine (cubes, pivots) | 64 px sur chaque axe |
| Rotation de base d'un cube ou d'un groupe | ±360° |
| *Inflate* | −8 à 8 |
| Animations | 16 |
| Clés d'animation (total) | 32 768 |
| Durée d'une animation | 600 s |
| Expression Molang | 512 caractères |
| Nom d'une catégorie | 24 caractères |
| Cosmétiques portés en même temps par un joueur | 3 |
| Sortes de particules par cosmétique | 4 modélisées + 4 de Minecraft |
| Points de départ de particules (`emit_`) | 32 |

Un fichier hors limites est refusé avec un message qui dit pourquoi.

> 💡 Un cosmétique s'affiche chez **tous les joueurs proches**. Pour un cosmétique courant, visez
> **quelques centaines de cubes**. Les très gros modèles sont à garder pour des pièces rares.

---

## 8. Bonnes pratiques de rendu

- **Pas de faces superposées ni de plans d'épaisseur 0** : elles clignotent, surtout avec des shaders.
  Donnez 0,3 à 0,5 px d'épaisseur aux plans (plumes, feuilles) et décalez légèrement les faces qui se
  chevauchent.
- **Cubes et groupes masqués** (œil barré dans Blockbench) : ils sont **ignorés**. Supprimez ce qui ne
  sert pas, ou réaffichez-le.
- **Semi-transparence** : seulement dans les groupes `trans_`. Deux groupes `trans_` de deux cosmétiques
  différents qui se croisent peuvent parfois se dessiner dans le mauvais ordre ; dans un même cosmétique,
  les faces sont triées.
- **Additif (`add_`, `_e`, reflets)** : ça ne fait qu'éclaircir. Sur un fond très clair (neige, ciel de
  midi), une lueur se voit moins : c'est normal pour de la lumière.
- **Le nettoyage est automatique** : le serveur réécrit le fichier en ne gardant que ce qui sert
  (métadonnées supprimées, animations conservées). Inutile d'optimiser le JSON à la main.
- **Pour vérifier les repères**, comparez avec la vue 3D de Blockbench : une rotation de +30° en X dans
  Blockbench donne la même chose en jeu.

---

## 9. Modèles « Java Block/Item » (chapeaux, objets tenus)

Un modèle Java Block/Item est converti automatiquement à l'import et placé exactement comme Minecraft
le ferait, grâce à ses réglages **Display** :

- **`display.head`** → porté sur la tête, ou **dans le dos** si le réglage descend l'objet sous le cou
  (ailes, jetpack, coffre…).
- Sinon, **`display.thirdperson_righthand`** → tenu dans la main droite.
- Le staff peut forcer l'emplacement (`head`, `back` ou `hand`).
- Plusieurs textures sont fusionnées en une seule. Pour une texture animée, seule la première image est
  gardée.

---

## 10. Import par le staff

1. **Importer** : onglet Apparence, bouton *Importer…*, puis choisir le fichier.
2. **Catégorie** : Chapeaux, Visage, Dos et ailes, Mains, Familiers, Autres, ou un nom libre.
3. **Lumineux** : « Oui » pour dessiner tout le cosmétique en pleine lumière (section 5 bis).
   **Volume des sons** si le modèle en a (section 6.5).
   Si le modèle a des particules, une fenêtre par sorte suit (section 5 ter).
4. **Animations par état** : déjà pré-remplies si les noms suivent la section 6.2. Clic pour
   l'animation suivante, clic droit pour la précédente, « Aucune » pour aucune.
5. **Rapport d'import** : nombre de cubes et de groupes, profondeur, clés par canal, taille de la
   texture et taille compressée, plus un avertissement pour chaque élément ignoré :
   - cubes ou groupes masqués ;
   - pistes d'effets ;
   - canaux non pris en charge ;
   - clés bezier ;
   - expressions Molang non comprises ;
   - noms coupés.

Un cosmétique peut être réservé à un rôle (VIP, etc.) : seuls les joueurs qui ont ce rôle peuvent le
porter.

---

## 11. Check-list avant d'envoyer un cosmétique

- [ ] Format *Modded Entity* (ou *Generic Model*), fichier `.bbmodel`
- [ ] Que des cubes, aucun mesh
- [ ] Une seule texture, PNG ≤ 512 × 512, enregistrée dans le fichier
- [ ] Si quelque chose doit briller : une texture `<nom>_e` de même taille, non assignée aux faces
- [ ] Le modèle est placé autour d'un joueur, les pieds à (0, 0, 0)
- [ ] Rien à plus de 64 px de l'origine
- [ ] Les parties qui doivent suivre le corps sont dans des groupes **de premier niveau** nommés
  `head`, `body`, `right_arm`…
- [ ] Les morceaux animés à part (ailes, queue) ont leur propre sous-groupe, pivot à la jointure
- [ ] Les animations sont nommées avec les mots de la section 6.2 (`idle`, `walk`, `fly`…)
- [ ] Animations d'état en *loop*, attaque et blessé en *once*
- [ ] Aucun cube ou groupe masqué oublié, pas de faces superposées ni de plans d'épaisseur 0
- [ ] Pas de semi-transparence dans la texture, sauf pour les cubes d'un groupe `trans_`
- [ ] Un nombre de cubes raisonnable (quelques centaines pour un cosmétique courant)
- [ ] Particules : un groupe `particle_<nom>` à la racine (pivot sous la particule) et au moins un groupe vide
  `emit_<nom>` avec le même nom ; animations nommées `particle_<nom>_fall` et `particle_<nom>_rest`
- [ ] Rotations continues et pulsations dans une animation `overlay_<nom>` (pas dans les animations d'état)
- [ ] Groupes `ctrl_…` vides, placés **dans** le groupe qu'ils pilotent ; valeurs en « 1 + position »
- [ ] Sons : noms de sons de Minecraft dans la piste *Effets*
- [ ] Essayé en jeu avec `/cosmetique apercu` avant de l'envoyer au staff (section 12)

---

## 12. Essayer un cosmétique soi-même (`/cosmetique apercu`)

Pour tester sans passer par le staff, avec l'éclairage, les shaders et les particules du jeu :

1. **Droit** : la permission `phynariautilities.skin.preview` (ou celle de gérer les skins), donnée par le
   staff.
2. **Dossier** : mettez le `.bbmodel` dans `<dossier du jeu>/phynariautilities/apercu/`.
   `/cosmetique dossier` affiche le chemin exact.
3. **`/cosmetique apercu <fichier>`** (Tab complète le nom) : vous portez le cosmétique, **vous seul le
   voyez**, dans votre jeu. Le fichier passe les mêmes contrôles que l'import et son rapport s'affiche
   dans le chat.
4. **Modifiez et enregistrez dans Blockbench** : il est rechargé automatiquement en une seconde, avec son
   nouveau rapport.
5. `/cosmetique lumineux` active ou coupe l'option « Lumineux » de l'aperçu ; `/cosmetique apercu stop`
   l'enlève.

Dans l'aperçu, les animations d'état sont choisies d'après leurs noms (section 6.2), les particules ont
leurs réglages par défaut, et le volume des sons est de 50 %. Le cosmétique apparaît aussi dans le menu
Apparence. Il n'est envoyé à personne : les autres joueurs ne le voient pas.
