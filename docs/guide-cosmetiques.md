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
- **Effets** : texture lumineuse `_e` (section 5 bis) et particules qui se détachent du cosmétique,
  plumes, pétales, étincelles… (section 5 ter).
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

## 5. Texture

- **Une seule texture** dans le fichier : 0 texture ou plusieurs textures font refuser le fichier. Seule
  exception : la texture lumineuse `_e` (section 5 bis).
- **PNG, 512 × 512 au maximum.** Les textures HD (UV plus petits que l'image) sont gérées.
- Elle doit être **enregistrée dans le `.bbmodel`**. Si Blockbench indique un chemin vers un fichier sur
  votre disque sans l'avoir intégrée, réenregistrez le modèle.
- **Pas de semi-transparence** : un pixel est soit opaque, soit invisible (rendu *cutout*). Un pixel à
  moitié transparent ne s'affiche pas comme dans Blockbench : il devient opaque, ou disparaît s'il est
  presque transparent.
- Une face sans texture n'est pas affichée, comme dans Blockbench. Le rapport d'import le signale.

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
- En jeu, ce calque est dessiné par-dessus le cosmétique en lumière émise, comme les yeux des araignées :
  il **s'ajoute** à la couleur de la texture. Il reste visible dans le noir. Les shaders comme Iris traitent
  normalement ce type de rendu comme émissif (pas encore vérifié avec un pack de shaders). Une couleur
  sombre dans le calque donne une lueur douce, une couleur vive une
  lueur forte.
- **Une seule texture `_e` par modèle.** Le rapport d'import confirme qu'elle a été trouvée.

**2. Option « Lumineux » (tout le cosmétique)**
- Réglée par le staff dans la fenêtre *Catégorie et animations* (à l'import ou avec la roue dentée).
- Le cosmétique entier est dessiné **en pleine lumière** : il ne s'assombrit plus dans les grottes ou la
  nuit, mais il ne « rayonne » pas comme un calque `_e`.
- Pratique pour un halo, des ailes d'énergie, un objet magique entièrement lumineux.

> 💡 Pour un effet de néon : texture principale sombre + calque `_e` avec des lignes vives.

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

**4. Les réglages, par le staff, dans le jeu**

Après la fenêtre *Catégorie et animations*, une fenêtre par sorte de particule demande :

| Réglage | Choix | Par défaut |
|---|---|---|
| Quand | En vol, En l'air, En mouvement, À l'arrêt, Toujours, Jamais | En vol |
| Nombre | 0,5 à 10 par seconde | 2 / s |
| Durée | 1 à 20 s | 6 s |
| Mouvement | Légère, Normale, Lourde (elles tombent), Flotte (reste sur place), Monte (s'élève) | Légère |
| Au sol | Se pose, Disparaît (pour Légère, Normale et Lourde) | Se pose |

Ces réglages se changent à tout moment avec la roue dentée, sans réimporter le modèle.

**En jeu**
- Chaque particule part avec un peu de l'élan du joueur, dérive au hasard, puis tombe (ou monte).
- Si elle touche un bloc, elle se pose dessus ou disparaît. À la fin de sa durée, elle rétrécit puis
  disparaît.
- Elles sont calculées par le jeu de chaque joueur : **aucun coût pour le serveur**, et tout le monde
  les voit.
- Limites pour rester fluide : 64 particules par joueur, 512 à l'écran, et aucune lancée par un joueur à
  plus de 48 blocs. Chaque joueur peut les couper dans ses Paramètres (« Particules des cosmétiques »).
- Le rapport d'import indique combien de points de départ chaque particule a. Il prévient aussi en cas
  d'oubli : une particule sans point de départ, ou un point de départ dont le nom ne correspond à
  aucune particule.

> 📁 Exemple prêt à importer : `docs/exemples/exemple_particules.bbmodel` (ailes qui lancent des plumes
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
- **Non joués** : les pistes d'effets, de sons et de particules de Blockbench (ignorées et signalées dans le
  rapport). Pour des particules, utilisez les groupes `particle_<nom>` (section 5 ter).
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

Une valeur de clé peut être un nombre ou une expression Molang, 256 caractères au maximum.

**Opérations** : `+ - * /`, parenthèses, comparaisons (`<`, `>`, `==`…), `&&`, `||`, `!`, `condition ? a : b`.

**Fonctions** : `math.sin`, `math.cos` (en degrés), `math.abs`, `math.sqrt`, `math.floor`,
`math.ceil`, `math.round`, `math.trunc`, `math.min`, `math.max`, `math.mod`, `math.pow`,
`math.clamp`, `math.lerp`, `math.atan`, `math.atan2`, `math.exp`, et la constante `math.pi`.

**Variables** (préfixe `q.` accepté à la place de `query.`) :

| Variable | Valeur |
|---|---|
| `query.anim_time` | temps écoulé dans l'animation (secondes) |
| `query.life_time` | temps depuis que le cosmétique est porté (ne boucle pas : utile pour un mouvement irrégulier) |
| `query.ground_speed` | vitesse au sol (blocs par seconde) |
| `query.vertical_speed` | vitesse verticale (blocs par seconde) |
| `query.health` / `query.max_health` | vie actuelle et vie maximale |
| `query.is_on_ground`, `query.is_sneaking`, `query.is_flying`, `query.is_sprinting`, `query.is_swimming`, `query.is_gliding`, `query.is_riding`, `query.is_sleeping` | 1 si vrai, 0 sinon |

Une variable inconnue (`variable.x`, autre `query`…) vaut 0. Une expression invalide est remplacée par
la valeur neutre (0, ou 1 pour l'échelle) et signalée dans le rapport d'import.

Exemples :
```
math.sin(query.anim_time * 360) * 10                    // balancement de ±10° par seconde
math.clamp(query.ground_speed * 8, 0, 30)               // les ailes s'ouvrent avec la vitesse
query.is_sneaking ? 15 : 0                              // se replie quand on s'accroupit
math.sin(query.life_time * 90) * math.sin(query.life_time * 37) * 5   // flottement irrégulier
1 + (query.health / query.max_health) * 0.2             // échelle qui suit la vie
```

---

## 7. Limites

| Élément | Maximum |
|---|---|
| Fichier `.bbmodel` à l'import | 16 Mo |
| Fichier une fois nettoyé et compressé par le serveur | 1 000 Ko |
| Cubes | 8 192 |
| Groupes | 2 048 |
| Niveaux d'imbrication des groupes | 64 |
| Texture | 1 seule, PNG 512 × 512 (+ 1 texture lumineuse `_e` de même taille) |
| Distance à l'origine (cubes, pivots) | 64 px sur chaque axe |
| Rotation de base d'un cube ou d'un groupe | ±360° |
| *Inflate* | −8 à 8 |
| Animations | 16 |
| Clés d'animation (total) | 32 768 |
| Durée d'une animation | 600 s |
| Expression Molang | 256 caractères |
| Nom d'une catégorie | 24 caractères |
| Cosmétiques portés en même temps par un joueur | 3 |
| Sortes de particules par cosmétique | 4 |
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
- **Pas de semi-transparence** : faites le verre ou la fumée en pixels pleins et en pixels vides.
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
- [ ] Pas de semi-transparence dans la texture
- [ ] Un nombre de cubes raisonnable (quelques centaines pour un cosmétique courant)
- [ ] Particules : un groupe `particle_<nom>` à la racine (pivot sous la particule) et au moins un groupe vide
  `emit_<nom>` avec le même nom ; animations nommées `particle_<nom>_fall` et `particle_<nom>_rest`
