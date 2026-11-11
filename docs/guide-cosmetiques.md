# Créer un cosmétique pour Phynaria

Guide pour les créateurs : comment faire un cosmétique Blockbench qui s'importe du premier coup et
s'affiche en jeu exactement comme dans Blockbench, animations comprises.

Mod : Phynaria Utilities. Ce guide décrit la version Minecraft 26.1.2 (NeoForge). Les cosmétiques n'ont jamais
besoin d'une mise à jour du mod : le staff les importe sur le serveur et les joueurs les téléchargent
automatiquement.

### Ce qui a changé depuis le 4 novembre 2026

**8 novembre 2026 — demandes 6** :
- **Effets de téléportation : la copie du départ suit aussi l'échelle** du groupe `joueur` (section 15), comme
  à l'arrivée et pendant la charge : elle rétrécit, grandit, et n'est plus dessinée sous 0,05. Vérifié en
  jeu, avec et sans shader, sur le portail d'exemple (clés d'échelle de 1 à 0 dans `depart`) : la copie
  passe de l'échelle 1 à 0,91, 0,67, 0,42, 0,17 puis disparaît. Sur la capture, à 0,42, elle mesure 0,44
  fois sa taille de départ.
- **Aperçu d'un effet dans le menu Apparence et la boutique** (sections 13 et 15) : il joue `depart`, une
  pause, `arrivee`, une pause, en boucle, au lieu de `charge`. Le groupe `joueur` s'applique comme en jeu :
  on voit le joueur rétrécir, disparaître puis réapparaître. Vérifié dans le menu, avec et sans shader.
- **`add_` s'estompe selon l'alpha de la texture** (sections 4 bis et 5 bis) : la couleur est multipliée par
  l'opacité du pixel avant d'être ajoutée. Une texture opaque partout (alpha 255) donne exactement le même
  résultat qu'avant. Même chose pour le calque `_e`. Vérifié en jeu et dans le menu : un disque cyan dont
  l'alpha va de 255 au centre à 0 au bord donne une lueur ronde qui s'efface sans bord net.
- **Textures vues de loin (mipmaps)** (section 5) : de loin, les textures des cosmétiques sont lues dans des
  copies réduites, comme les blocs de Minecraft. Un trait fin reste visible, adouci, au lieu de disparaître
  ou de faire des escaliers. Vérifié en jeu : une grille de traits d'un texel, vue à quelques blocs, reste
  une grille régulière ; sans mipmaps, elle se cassait en points épars.
- **`trans_` cache les `add_` placés derrière lui** (section 4 bis) : c'était déjà le cas, c'est maintenant
  écrit. N'enfermez pas une lumière `add_` dans une enveloppe `trans_`.

**6 novembre 2026 (soir) — demandes 5** :
- **Faces `up` et `down`** (section 3) : l'image se lit maintenant comme dans Blockbench. Elle était dessinée
  tournée d'un demi-tour sur `up` et en miroir sur `down`. Vérifié en jeu, vu de dessus et de dessous, avec
  une image asymétrique. Si vous retourniez vos images pour compenser, remettez-les dans le sens de Blockbench.
- **Grands modèles** (sections 3 et 7) : 320 px (20 blocs) pour un effet de téléportation, 128 px (8 blocs)
  pour un cosmétique porté ou un familier, 64 px pour un skin d'objet, mesurés au repos. Une clé `position`
  peut déplacer un groupe de 320 px. Un grand cosmétique ou familier reste dessiné tant qu'une partie peut
  être à l'écran.
- **Effets de téléportation** (section 15) : le groupe `joueur` est aussi lu pendant `charge`. Vérifié en
  jeu : le joueur lévite pendant le compte à rebours.
- **Menu Apparence** : `cam_` et `camy_` sont tournés vers vous dans l'aperçu, de face, de dos et de profil,
  y compris quand vous faites tourner le personnage (vérifié dans l'aperçu ; l'inclinaison à la souris
  n'a pas pu être vérifiée automatiquement).
- **Skins d'objets vivants** (section 14) : animations par état (`item_idle`, `item_use`, `item_swing`,
  `item_ground`, `item_gui`), événements (`event_swing`, `event_hit`, `event_break`, `event_use_start`,
  `event_use_stop`, `event_select`, `event_release`, `event_charged`, `event_enter_<étape>`), `overlay_`,
  particules (*Quand* « À l'utilisation », rafale « Au tir ») et sons ; requêtes `q.use_progress`,
  `q.item_durability`, `q.is_enchanted`, `q.hand`, `q.in_first_person`. Option joueur « Animations des
  skins d'objets ». 32 animations par modèle au lieu de 16.
- **Java Block/Item** (section 9) : textures gardées à leur taille (512 au plus) et calques `_e` / `_r` gardés.
- **Vignettes 3D** (sections 10 bis et 13) : chaque carte de cosmétique ou d'effet montre la pièce seule,
  vue de trois quarts ; la tuile d'une catégorie montre sa pièce la plus rare. Champ facultatif
  `vignette` dans le fichier.
- **Nouvelle requête** `query.hit_by_entity` (section 6.3) : 1 pendant 0,5 s quand un joueur, un monstre ou
  un projectile vous touche, **même sans dégât** (bouclier, créatif, demi-seconde après un coup, protection) ;
  0 pour une chute, le feu, la noyade… Vérifiée en jeu avec un coup qui fait mal puis un coup ignoré par
  Minecraft : elle reste active 0,5 s après le second. Le bouclier et le créatif ne sont pas encore essayés.
- **Boutique** (section 13) : les catégories sont des tuiles, comme les cosmétiques.

**6 novembre 2026 — effets de téléportation** (section 15) :
- Un modèle joué là où le joueur part et là où il arrive, vu par tous autour : `/tpa`, homes, warps,
  spawn, retour, rassemblement de groupe et `/tp` (pas le RTP).
- Trois animations : `charge` (en boucle pendant le compte à rebours), `depart` et `arrivee`.
- Un groupe vide `joueur` montre le joueur à sa façon : il tombe du ciel, sort d'un portail… Au départ,
  une copie du joueur suit ce groupe.
- Particules et sons comme pour un cosmétique. Un effet par joueur, nouvel onglet **Effets** dans
  Apparence, option « Effets de téléportation des autres » dans Paramètres.

**5 novembre 2026 (soir) — skins d'objets** (section 14) :
- Un skin d'objet remplace, pour tout le monde, l'apparence de tous les objets d'un type tenus par le
  joueur : épées, pioches, haches, pelles, houes, lances, arcs, arbalètes, tridents, boucliers, masses et
  cannes à pêche, **de tous les matériaux et de tous les mods** (reconnus par leurs tags).
- Un par type, en plus des 3 cosmétiques. Modèle Java Block/Item avec ses réglages *Display*.
- Étapes par groupes : arc bandé (`bande_1` à `bande_3`), arbalète chargée, trident levé et lancé,
  bouclier qui bloque, canne lancée.
- Visible en main, au sol (objet jeté), pour le trident lancé et dans votre inventaire.
- Nouvel onglet **Objets** dans Apparence, et option « Skins d'objets des autres » dans Paramètres.
- Pour le staff : `/puadmin skin itemtype`, et la liste `[itemSkins] types` de la config pour les objets
  mal tagués.

**5 novembre 2026 — demandes 4** :
- **Réglages écrits dans le fichier** (section 5 ter, point 6) : les réglages des particules que vous
  mettez dans `unhandled_root_fields.phynaria` du `.bbmodel` remplissent maintenant les fenêtres du staff
  à l'import. Le staff peut toujours les changer. Une valeur inconnue ou hors limites est remplacée par
  la plus proche (ou par le réglage par défaut) et signalée dans le rapport d'import.
- **Fiche de l'objet** (section 10 bis) : nom, ensemble, rareté, description et lore. Vous pouvez les
  écrire dans le fichier (`fiche`). Le staff les retrouve pré-remplis à l'import et les modifie plus tard
  avec le crayon de la fiche.
- **Familiers vivants** (section 6.6) : un cosmétique avec un bloc `familier` quitte le corps du joueur
  et le suit comme un loup apprivoisé. Quatre modes : au sol, en vol, à la nage ou perché sur l'épaule.
  Il a ses propres animations (`pet_idle`, `pet_walk`, `pet_sit`…), ses événements, et de nouvelles
  requêtes Molang (`q.owner_distance`, `q.owner_is_sneaking`, `q.owner_health`…). Sans bloc `familier`,
  rien ne change : le cosmétique est porté comme avant. Vérifié en jeu, avec et sans shader, sur un renard
  d'exemple dans les quatre situations : il attend, il suit en marchant, il s'assoit quand on
  s'accroupit, il vole à côté de l'épaule, il se pose sur l'épaule.
- **Interface refaite** (section 13) :
  - les cosmétiques sont présentés en **cartes** (rareté, état, prix) ;
  - un clic ouvre la **fiche de l'objet**, avec l'aperçu 3D, le bouton « Essayer », la rareté,
    l'ensemble, la description, le lore en italique, ce qu'il fait, son prix et les autres pièces de son
    ensemble ;
  - le bouton « Porter l'ensemble » met toutes les pièces d'un ensemble en un clic ;
  - la boutique montre la description sur **deux lignes** (160 caractères au lieu de 64) et un bouton
    qui ouvre la fiche ;
  - plus aucun texte n'est coupé sans recours : un texte coupé s'affiche en entier au survol ;
  - les onglets prennent la largeur de leur texte, et les libellés du menu latéral passent sur deux
    lignes.
- **Corrigé** : un domaine de données qui ne pouvait pas être enregistré (une erreur dans un seul
  fichier) empêchait la sauvegarde de tous les autres. Les autres sont maintenant enregistrés, et le
  domaine en erreur est réessayé à la sauvegarde suivante.

### Historique (jusqu'au 4 novembre 2026)

**4 novembre 2026 — nouveautés** (demandes de l'équipe Steampunk) :
- `ctrl_reflet` : force des reflets animée, par exemple plus brillant sous la pluie (sections 4 bis et
  5 quater) ;
- `ctrl_emit` : cadence d'un point de particules animée, pour un jet au moment exact du geste
  (sections 4 bis et 5 ter) ;
- *Quand* → **Sous la pluie** dans les réglages des particules (section 5 ter) ;
- `event_unequip` : animation jouée quand on retire le cosmétique, qui reste affiché jusqu'à 5 s
  (section 6.4).

**4 novembre 2026 — bugs corrigés** :
- **`ctrl_alpha` sur une partie opaque** : à −1, la partie restait visible (sac dorsal des ailes, capture
  du 4 novembre à 01:44). Elle disparaît maintenant sous 10 %, avec son calque `_e` et ses reflets,
  comme le guide l'annonçait (section 4 bis). Le contournement par l'échelle n'est plus nécessaire.
- **Crash à l'ouverture du menu** : un skin ou un cosmétique réservé à un rôle qui n'existe plus
  (supprimé ou renommé depuis), ou le menu ouvert avant l'arrivée des données du serveur, faisait
  planter le jeu dans l'onglet Apparence. Le menu affiche maintenant « Réservé : » suivi du nom du rôle
  tel qu'il est enregistré. Pour le staff : redonnez le bon rôle au skin avec `/puadmin skin role`.

**4 novembre 2026 (soir) — demandes 3** :
- **Auras et shaders, vérifié en jeu** : nous avons refait votre test 1 dans le jeu, avec Iris 1.11.4,
  Sodium 0.9.2 et Complementary Unbound r5.9.3 + Euphoria Patches 1.10.5. Les plaques `add_` et le calque
  `_e` s'affichent avec le shader comme sans shader. Deux causes de votre constat :
  - le jar installé dans votre profil (15 h 47) date d'avant le correctif Iris (16 h 11) : votre partie
    de 15 h 52 n'avait donc pas le correctif, d'où l'absence de la ligne « Iris: … » dans le journal ;
  - il manquait aussi la passe d'ombre d'Iris, d'où l'erreur « Missing program … in override list ».
    Elle est corrigée : le journal affiche maintenant « Found fine program match for
    phynariautilities:pipeline/cosmetic_additive: ENTITIES_CUTOUT » (et `SHADOW_ENTITIES_CUTOUT`), puis
    « Iris: cosmetic pipeline … drawn with the entities programs (main and shadow) », dès le chargement
    des mods. Plus d'erreur « Missing program ».

  **Mettez à jour le jar** (celui de ce soir) et refaites votre test : si `add_` disparaît encore,
  envoyez-nous le `latest.log`. Nouveau : `query.has_shader_pack` (section 6.3).
- **Gravité pour `phys_`** : réglage `_g0` à `_g100` (section 4 bis). Vérifié en jeu : une chaîne de
  5 maillons pend droit vers le sol avec `_g100` quand le repère du bras est tourné de 90°, et reste
  raide dans l'axe avec `_g0`.
- **Nouvelles requêtes** (section 6.3) : `query.is_slim_arms`, `query.has_helmet`, `has_chestplate`,
  `has_leggings`, `has_boots`, `query.body_x_rotation`, les angles des bras, `query.limb_swing` et
  `query.limb_swing_amount`.
- **Sons d'un pack de ressources du serveur** (section 6.5) : `phynaria:fouet_claque` est joué s'il est
  déclaré dans le `sounds.json` d'un pack chargé. Pas encore entendu en jeu : nos essais se font son coupé.
- **Bras fins, automatique** (section 4) : sur un skin à bras fins, `right_arm` et `left_arm` sont
  resserrés comme le bras de Minecraft (côté extérieur rentré de 1 px). Vérifié en jeu : un bracelet fait
  pour le bras de 4 px colle au bras de 3 px ; un groupe `wide_` garde sa taille.
- **Armure** (section 10, réglage du staff « Armure ») : **Par-dessus** écarte les pièces comme l'armure
  portée, **Cachée** ne dessine pas l'armure. Vérifié en jeu avec une armure en diamant : la sangle de
  test, cachée sous le plastron en mode Normale, passe par-dessus en mode Par-dessus ; l'armure disparaît
  en mode Cachée. Essai : `/cosmetique armure`.
- **Sons embarqués dans le `.bbmodel`** (section 6.5) : `/cosmetique sons <fichier>` embarque vos OGG
  mono (8, 100 Ko et 5 s au plus). Vérifié en jeu (son coupé) : la commande a embarqué le son, et le
  moteur de son du jeu l'a lu à chaque tour de l'animation. Pas encore écouté avec le son.

**4 novembre 2026 — rapport « quatre bugs de rendu encore ouverts »** :
- **Particules `emit_mc_` loin du point et immobiles** (bug 4) : le mod donnait à Minecraft une vitesse
  en blocs par seconde, que Minecraft applique à chaque tick. Les particules partaient donc 20 fois trop
  vite (avec l'*Élan* à 40 % en vol, autour de 80 blocs par seconde). Elles partent maintenant du point,
  à la bonne vitesse. Avec Iris, rien n'est plus lancé pendant le dessin des ombres, qui redessine le
  monde depuis le soleil.
- **Reflet `_r` en rectangle autour des pièces découpées** (bug 2) : le reflet était dessiné sur toute
  la face. Il suit maintenant la découpe de la texture principale (section 5 quater). Vérifié au pixel :
  plus rien ne change autour d'un disque découpé.
- **Menu Apparence : `add_` opaque, avec du noir** (bug 3) : le menu dessine le personnage dans une image
  transparente, où un ajout de couleur devenait une couleur pleine, et le noir un carré noir. `add_` et
  le calque `_e` y utilisent maintenant une copie de leur texture faite pour ça : plus de noir, et la
  lueur s'ajoute au personnage comme en jeu (section 4 bis). Nouveau : `query.is_in_menu` (section 6.3).
  Dans notre essai, le halo placé derrière le torse restait bien derrière ; si une pièce passe encore
  devant le personnage dans le menu, envoyez-nous le modèle.
- **Avec un shader, `add_`, `_e` et les reflets invisibles** (bug 1) : Iris ne dessine un rendu que s'il
  sait par quel programme le remplacer, et il ne connaissait pas celui du mod. Le mod le lui indique
  maintenant au démarrage, avec l'API d'Iris (programme des entités, comme l'aura du creeper chargé).
  Le journal du jeu le confirme par la ligne « Iris: cosmetic pipeline … drawn with the entities
  program ». Vérifié depuis (voir « demandes 3 » ci-dessus). Les groupes
  `trans_` utilisent déjà le rendu translucide de Minecraft, qu'Iris connaît : s'ils disparaissent encore,
  dites-le-nous.

**Corrections précédentes** (rapport « le calque `_e` clignote », captures du 2 novembre 2026) :
- **Calque lumineux `_e` qui clignotait** : selon l'image, le cosmétique était normal, très sombre ou à
  moitié sombre, avec ou sans shader. Deux causes, corrigées toutes les deux : le calque était dessiné
  en mélange translucide (il recouvrait la texture au lieu de s'y ajouter), et les deux passes (texture
  puis calque) ne calculaient pas l'animation au même instant (le calque passait parfois derrière la
  texture). Maintenant, le calque s'**ajoute** à la couleur (un calque noir ne change rien) et chaque
  image d'un cosmétique est calculée **une seule fois** pour toutes ses passes (section 5 bis).
- **`query.is_boosting`** : il fallait l'approcher par un seuil de vitesse. Il vaut maintenant 1 pendant
  qu'une fusée pousse le vol en élytres (section 6.3).
- **Modèle d'exemple** : le chemin donné par le guide était faux. Le fichier est
  `docs/exemple_particules.bbmodel`.

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
- **Skins d'objets** : épées, outils, arcs… remplacés pour tout le monde, un par type (section 14).
- **Effets de téléportation** : un modèle joué au départ et à l'arrivée d'une téléportation (section 15).
- **Familiers** : un bloc `familier` dans le fichier, et le cosmétique suit le joueur au lieu d'être
  porté (section 6.6).
- **Réglages et fiche dans le fichier** : particules (5 ter), fiche de l'objet (10 bis) et familier (6.6)
  peuvent être écrits dans `unhandled_root_fields.phynaria` : le staff les retrouve pré-remplis.
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

**Faces du dessus et du dessous** (`up`, `down`) : l'image se lit comme dans Blockbench (gauche de l'image
vers −X sur les deux faces ; haut de l'image vers −Z sur `up`, vers +Z sur `down`), rotations de face
comprises. Avant le 6 novembre 2026 (soir), ces faces étaient dessinées tournées ou en miroir : si vous aviez
retourné vos images pour compenser, remettez-les dans le sens de Blockbench.

**Zone autorisée** : tout (cubes, pivots) doit rester, sur chaque axe, à moins de :

| Type | Distance à l'origine |
|---|---|
| Cosmétique porté, familier | **128 px** (8 blocs) |
| Effet de téléportation | **320 px** (20 blocs) |
| Skin d'objet | 64 px (4 blocs) |

La limite se mesure sur le modèle **au repos**. Les animations peuvent ensuite déplacer un groupe de
320 px au plus par clé (`position`) et l'agrandir jusqu'à 16 fois (`scale`). Un grand cosmétique reste
dessiné tant qu'une partie peut être à l'écran, même quand le joueur ne l'est pas.
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
- **Bras fins (skin Alex, 3 px)** : modélisez toujours pour le bras normal de 4 px. Sur un joueur à bras
  fins, le mod resserre lui-même `right_arm` et `left_arm` comme Minecraft le fait pour le bras : le côté
  extérieur rentre de 1 px, l'épaule ne bouge pas. Un bracelet ou une manchette reste donc collé au bras.
  Pour une grosse pièce qui ne doit pas être resserrée (un bouclier, une aile portée au bras), mettez-la
  dans un sous-groupe dont le nom commence par **`wide_`** (`wide_bouclier`). N'utilisez plus
  `query.is_slim_arms` pour réduire un bracelet : l'ajustement serait fait deux fois.
- **Attention au sens des x** : dans Blockbench, le bras **droit** du joueur est du côté des x
  **positifs** (vu de face, à gauche de l'écran).
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
| `add_<nom>` | **Additif** : la couleur, multipliée par l'opacité du pixel, s'ajoute à ce qu'il y a derrière (noir ou transparent = invisible), en pleine lumière, sans cacher ce qui est derrière | lueurs, halos vaporeux, auras, énergie, feu « léger » |
| `trans_<nom>` | **Semi-transparent** : l'opacité de la texture (1 à 254) est respectée, faces triées. **Cache les `add_` et les particules placés derrière lui**, même presque invisible (voir plus bas) | verre, glace, fumée, voiles, hologrammes, ailes de fée |
| `cam_<nom>` | **Face caméra** : le groupe tourne autour de son pivot pour que sa face avant (`south`, +Z) regarde la caméra | éclats, lueurs rondes |
| `camy_<nom>` | **Face caméra, debout** : il ne tourne qu'autour de l'axe vertical | flammes, colonnes d'énergie |
| `phys_<nom>` | **Ressort** : il balance autour de sa pose animée selon l'élan, l'arrêt et les virages du joueur | queues, capes, oreilles, chaînes, pompons |

Détails :
- **Le reste du modèle ne change pas** : sans ces préfixes, tout est dessiné comme avant (opaque, pixel
  tout ou rien).
- **`add_` et l'opacité** : chaque pixel ajoute *sa couleur × son opacité*. Pour une lueur qui s'estompe sur
  ses bords, gardez la couleur et faites baisser l'alpha vers 0 : plus besoin de peindre le dégradé vers le
  noir. Les deux façons se combinent. Une texture opaque partout (alpha 255) donne exactement le même
  résultat qu'avant ; seuls les pixels entièrement transparents (alpha 0) ne sont pas dessinés du tout.
  Jusqu'au 7 novembre, l'alpha était ignoré : un pixel à alpha 30 ajoutait toute sa couleur, et un pixel
  sous 26 n'ajoutait rien.
- **`trans_` cache ce qui est `add_` derrière lui.** Une face `trans_` écrit la profondeur, comme une face
  opaque, et elle est dessinée **avant** `add_` et les particules. Tout ce qui est `add_` (ou une
  particule) **derrière** une face `trans_` n'est donc pas dessiné, même si cette face est presque invisible
  (alpha 30). Ce qui est **devant** elle se voit normalement. Donc **n'enfermez pas une lumière `add_` dans
  une enveloppe `trans_`** (une colonne de lumière dans une gaine de verre, une flamme dans une lanterne
  translucide) : vu de l'extérieur, seule l'enveloppe s'affiche. Mettez plutôt l'enveloppe en `add_` aussi
  (une couleur sombre et un alpha faible donnent un voile léger), ou laissez une ouverture.
- **`cam_` et `camy_`** : l'animation du groupe s'applique *après* l'orientation vers la caméra, donc une
  flamme peut onduler ou grandir en restant face à vous. Dans le menu Apparence, ces groupes
  sont tournés vers vous comme en jeu, y compris quand vous faites tourner le personnage à la souris
  (`camy_` reste debout quand vous l'inclinez). Le contournement par `query.is_in_menu` n'est plus utile. Dans le menu, `add_`
  et le calque `_e` s'ajoutent comme en jeu sur le personnage ; sur le fond du menu, le résultat est
  très proche (le fond est à peine assombri sous les zones les plus vives).
- **`phys_`** : réglages dans le nom, facultatifs : `phys_queue_r40_a60`. **r** = raideur (0 très souple,
  100 raide), **a** = amortissement (0 rebondit longtemps, 100 sans rebond) ; 50 par défaut. Des groupes
  `phys_` imbriqués (une chaîne) se suivent avec un peu de retard. La pose de l'animation reste la cible.
  **g** = gravité (0 par défaut) : de 0 (ressort autour de la pose animée) à 100 (le groupe pend vers le
  **bas du monde**, quel que soit l'angle du bras ou du corps, comme une chaîne ou un pendentif). Les
  réglages se mettent dans n'importe quel ordre : `phys_chaine_g100_a40` = `phys_chaine_a40_g100`.
  Pour une chaîne, imbriquez un groupe `phys_…_g100` par maillon, pivot en haut du maillon : chacun
  pend sous le précédent, balance avec du retard quand on marche ou balance le bras, et se calme à
  l'arrêt. Une raideur basse (`r20`) donne une période d'environ 0,6 s. La gravité suit l'orientation du
  corps et des bras, pas celle du joueur couché (nage, élytres) ; pas de collision avec le corps.
- **Groupes de contrôle** : un groupe **vide** placé dans un groupe pilote ce groupe (et ses sous-groupes)
  par sa **position animée** (canal *position*, Molang compris). Au repos (position 0), rien ne change :
  la valeur lue est **1 + la position**.

  | Groupe vide | Pilote | Valeurs |
  |---|---|---|
  | `ctrl_alpha` | l'opacité | x = −1 : invisible, −0,5 : à moitié, 0 : normal |
  | `ctrl_teinte` | la couleur | x, y, z = rouge, vert, bleu : −1 retire la couleur, 0 normal, +1 double |
  | `ctrl_lumiere` | la force du calque `_e` | x = −1 éteint, 0 normal, +1 deux fois plus fort |
  | `ctrl_uv` | le décalage de la texture | x, y = décalage en texels (défilement avec `math.mod`) |
  | `ctrl_reflet` | la force des reflets `_r` | x = −1 mat, 0 normal, +1 deux fois plus brillant, +3 quatre fois (section 5 quater) |
  | `ctrl_emit` | la cadence d'un point `emit_` (placé **dans** le groupe `emit_`) | x = −1 coupé, 0 réglage du staff, +2 trois fois plus (section 5 ter) |

  L'opacité fait un vrai fondu dans un groupe `trans_` ou `add_`. Dans une partie opaque, en dessous de
  10 % la partie disparaît d'un coup, avec son calque `_e` et ses reflets (pas de demi-mesure possible en
  rendu opaque) : `ctrl_alpha` à −1 cache bien un sac dorsal, sans passer par l'échelle.

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
- **Vue de près**, la texture est lue pixel par pixel, sans flou, comme dans Blockbench. **Vue de loin**,
  quand un texel devient plus petit qu'un pixel de l'écran, le jeu lit des copies réduites de la texture
  (*mipmaps*, jusqu'à 4 niveaux, comme les blocs). Un trait d'un ou deux texels (fissure, étincelle, rune)
  reste donc visible à quelques blocs, plus pâle et adouci, au lieu de disparaître d'une image à l'autre ou
  de faire des escaliers. Plus besoin de dessiner ces traits avec des cubes. Les copies suivent le réglage
  vidéo **Niveaux de mipmap** du joueur (à 0 : pas de mipmaps). Il est lu au chargement du cosmétique.
  Sur une texture animée, les niveaux s'arrêtent avant que deux images ne se mélangent.

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
- **Noir = aucun effet** et transparent = aucun effet. Chaque valeur s'ajoute, multipliée par l'opacité du
  pixel : un fond opaque à (40, 39, 35) éclaircit toute la zone d'environ 40, c'est une lueur douce et
  visible, pas un fond invisible. Pour que rien ne brille à un endroit, peignez-le en noir pur ou
  laissez-le transparent. Une couleur vive donne une lueur forte ; un alpha à moitié la divise par deux.
- Avec un pack de shaders (Iris), le mod indique à Iris de dessiner ce rendu avec ses programmes des
  entités, comme l'aura du creeper chargé (même chose pour `add_` et les reflets). Vérifié en jeu avec
  Complementary Unbound r5.9.3 + Euphoria Patches 1.10.5 : le calque et `add_` restent visibles, comme
  sans shader. L'intensité peut varier selon le pack.
- **Une seule texture `_e` par modèle.** Le rapport d'import confirme qu'elle a été trouvée.

**2. Option « Lumineux » (tout le cosmétique)**
- Réglée par le staff dans la fenêtre *Catégorie et animations* (à l'import ou avec la roue dentée).
- Le cosmétique entier est dessiné **en pleine lumière** : il ne s'assombrit plus dans les grottes ou la
  nuit, mais il ne « rayonne » pas comme un calque `_e`.
- Pratique pour un halo, des ailes d'énergie, un objet magique entièrement lumineux.

> 💡 Pour un effet de néon : texture principale sombre + calque `_e` avec des lignes vives.
>
> 💡 Pour une aura qui laisse voir le joueur : un groupe `add_` (section 4 bis), dont la texture va du
> transparent (ou du noir) à la couleur voulue, plutôt qu'un calque `_e`, qui ne s'ajoute qu'aux parties
> opaques.

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
- Le reflet suit la **découpe de la texture principale** : là où elle est transparente (alpha sous
  10 %), rien n'est dessiné. Une lame ou un disque découpé dans une plaque brille sans rectangle autour.
- Les reflets s'ajoutent à la couleur (comme le calque `_e`) : ils éclaircissent, ils n'assombrissent
  jamais.
- **Animer la brillance** : un groupe vide **`ctrl_reflet`** dans un groupe règle la force de ses reflets
  (1 + position x, de 0 à 8, plafonnée au miroir). Exemple, du métal mouillé : position x =
  `query.is_in_rain * 2` (trois fois plus brillant sous la pluie). Il renforce le masque `_r` : une face
  noire dans le masque reste mate.
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
- **Cadence animée** : un groupe vide **`ctrl_emit`** placé **dans** un groupe `emit_` règle la cadence
  de ce point par sa position x animée, comme les autres contrôles : −1 = coupé, 0 = réglage du staff,
  +2 = trois fois plus (jusqu'à +7). Exemple, un jet de vapeur au moment exact où la soupape décharge :
  x reste à −1 et passe à +4 pendant 0,3 s. Le *Nombre* du staff est partagé entre les points, chacun selon
  son `ctrl_emit`. Les rafales partent des points dont la cadence n'est pas coupée. Ça marche aussi pour
  `emit_mc_`.

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
| Quand | En vol, En l'air, En mouvement, À l'arrêt, Toujours, Sous la pluie (quoi que fasse le joueur, quand il pleut sur lui : pas sous un toit, ni dans un biome sec), À l'utilisation (skins d'objets : pendant que l'objet est utilisé ; sur un cosmétique porté : jamais), Jamais | En vol |
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
| Rafale | Aucune, À l'attaque (skin d'objet : à chaque coup donné avec), Blessé, Au saut, À l'atterrissage, Au tir (skins d'objets : flèche, carreau ou trident qui part) : 8 d'un coup quand ça arrive | Aucune |
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

**6. Écrire les réglages dans le fichier (facultatif)**

Pour que le staff n'ait rien à régler, écrivez vos réglages dans le `.bbmodel`. Ils remplissent les
fenêtres à l'import ; le staff peut encore les changer.

- Blockbench garde tel quel tout champ racine qu'il ne connaît pas, rangé dans
  **`unhandled_root_fields`**, quand vous rouvrez et réenregistrez le fichier. Ajoutez-le une fois avec un
  éditeur de texte (le `.bbmodel` est du JSON), à la racine du fichier :

```json
"unhandled_root_fields": {
  "phynaria": {
    "version": 1,
    "particules": {
      "plume": {"quand": "vol", "nombre": 2, "duree": 6, "mouvement": "legere", "au_sol": "pose",
                "rendu": "opaque", "sens": "libre", "fin_de_vie": "retrecit", "depart": "poussee",
                "dispersion": 15, "elan": 40, "variation": "legere", "rafale": "aucune", "limite": 64},
      "mc_white_smoke": {"quand": "arret", "nombre": 1}
    }
  }
}
```

- La clé d'une particule est son nom : `plume` pour `particle_plume`, `mc_flame` pour `emit_mc_flame`.
- Chaque réglage est facultatif : ce qui manque garde la valeur par défaut du tableau ci-dessus.
- Valeurs, en minuscules et sans accent :

  | Clé | Valeurs |
  |---|---|
  | `quand` | `vol`, `air`, `mouvement`, `arret`, `toujours`, `pluie`, `utilisation` (skins d'objets), `jamais` |
  | `nombre` | 0,5, 1, 2, 4, 6 ou 10 (par seconde) |
  | `duree` | 1, 3, 6, 10, 15 ou 20 (secondes) |
  | `mouvement` | `legere`, `normale`, `lourde`, `flotte`, `monte` |
  | `au_sol` | `pose`, `disparait` |
  | `rendu` | `opaque`, `lumineux`, `translucide` |
  | `sens` | `libre`, `camera` |
  | `fin_de_vie` | `retrecit`, `fondu` |
  | `depart` | `poussee`, `lent`, `moyen`, `rapide` |
  | `dispersion` | 0, 15, 45 ou 180 (degrés) |
  | `elan` | 0, 40 ou 100 (%) |
  | `variation` | `aucune`, `legere`, `forte` |
  | `rafale` | `aucune`, `attaque`, `blesse`, `saut`, `atterrissage`, `tir` (skins d'objets) |
  | `limite` | 64, 128 ou 256 |

- Un nombre est ramené au pas le plus proche (`"nombre": 7` donne 6), et le rapport le signale
  s'il sort des limites. Une valeur inconnue garde la valeur par défaut, avec une ligne dans le rapport.
- Pour une particule de Minecraft (`mc_…`), seuls `quand`, `nombre`, `depart`, `dispersion`, `rafale`
  et `limite` sont lus, comme dans la fenêtre du staff.
- Le même bloc `phynaria` porte aussi la fiche de l'objet (`fiche`, section 10 bis) et le familier
  (`familier`, section 6.6). Le serveur le garde dans le fichier nettoyé.

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
| `query.is_in_menu` | 1 dans l'aperçu du menu Apparence (sans joueur ni caméra), 0 en jeu : pour cacher ce que le menu ne sait pas montrer |
| `query.has_shader_pack` | 1 si un pack de shaders est actif **chez celui qui regarde** (Iris), 0 sinon |
| `query.is_slim_arms` | 1 si le skin du joueur a des bras fins (modèle Alex, 3 px), 0 sinon. Les groupes de bras sont déjà resserrés par le mod (section 4) : à utiliser pour autre chose (cacher une pièce, changer d'animation) |
| `query.has_helmet`, `query.has_chestplate`, `query.has_leggings`, `query.has_boots` | 1 si la pièce d'armure est portée (une élytre n'est pas un plastron), 0 sinon : pour écarter une pièce de l'armure (`position`, `scale`) ou la cacher (`ctrl_alpha`) |
| `query.body_x_rotation` | inclinaison du torse en degrés (environ 29 accroupi, 0 debout) |
| `query.right_arm_x_rotation`, `query.right_arm_z_rotation`, `query.left_arm_x_rotation`, `query.left_arm_z_rotation` | angles réels des bras en degrés (balancement du pas, coup, objet tenu), avant l'animation du cosmétique |
| `query.limb_swing`, `query.limb_swing_amount` | phase du pas (avance avec la distance parcourue) et ampleur (0 à l'arrêt, environ 1 en courant) |
| `query.hurt_time`, `query.attack_time` | de 0 à 1 pendant un coup reçu / un coup porté, 0 sinon |
| `query.hit_by_entity` | 1 pendant 0,5 s quand un joueur, un monstre ou un projectile vous touche, **même sans dégât** : coup bloqué au bouclier, en créatif, coup reçu dans la demi-seconde qui suit un autre coup, coup annulé par une protection. 0 pour une chute, le feu, la noyade… (`query.hurt_time`, lui, ne réagit qu'aux coups qui font mal) |
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
  | `event_unequip` | on retire le cosmétique : il reste affiché le temps de l'animation (**5 s au plus**), qui garde sa dernière image jusqu'à la fin, puis il disparaît |
  | `event_enter_<état>`, `event_exit_<état>` | il entre dans un état ou en sort : `event_enter_glide`, `event_exit_glide`, `event_enter_sneak`… (états de la section 6.2, en anglais : idle, walk, sprint, sneak, fly, glide, swim, fall, ride, sleep) |

- Les rotations et positions de ces animations s'**ajoutent** à celles de l'état, les échelles se
  multiplient.
- **`event_unequip`**, symétrique de `event_equip` : des ailes qui se replient et rentrent dans leur sac.
  Faites durer l'animation le temps du geste (au-delà de 5 s, le cosmétique part quand même). Pour que
  la pièce disparaisse à la fin, terminez par un `ctrl_alpha` à −1 ou une échelle à 0 : la dernière image
  est gardée jusqu'au départ. Si le joueur le remet avant la fin, `event_unequip` s'arrête et
  `event_equip` est rejouée. Les autres joueurs voient la même chose.
- Elles ne sont jamais proposées pour les états du joueur.

### 6.5 Sons

- Dans Blockbench, ajoutez des **clés de son** dans la piste *Effets* de l'animation. Le champ *Effet* doit
  contenir le **nom d'un son de Minecraft** : `entity.phantom.flap`, `block.amethyst_block.chime`,
  `item.armor.equip_elytra`… (`minecraft:` facultatif).
- **Sons à vous** : déclarez-les dans le `sounds.json` d'un **pack de ressources du serveur** (imposé aux
  joueurs), sous un autre espace de noms, par exemple `phynaria:fouet_claque`, et mettez ce nom dans la
  clé de son. Les sons restent hors du `.bbmodel` et sont téléchargés une fois avec le pack. Un joueur
  qui n'a pas le pack n'entend rien (pas d'erreur). `/cosmetique apercu` signale les sons que votre jeu
  ne connaît pas.
- **Sons embarqués dans le `.bbmodel`** : vos propres fichiers OGG voyagent avec le cosmétique, sans
  pack de ressources.
  1. Dans Blockbench, choisissez le fichier OGG de la clé de son (Blockbench garde son chemin) et donnez
     à la clé un nom simple dans *Effet* : `fouet_claque` (minuscules, chiffres, `_`, 32 caractères).
     Sinon, le nom du fichier est pris.
  2. Mettez le `.bbmodel` dans le dossier d'aperçu (section 12) et tapez **`/cosmetique sons
     <fichier>`**. Le mod lit les OGG (au chemin enregistré par Blockbench, ou du même nom dans le
     dossier d'aperçu), les vérifie et écrit une copie **`<fichier>_sons.bbmodel`** qui les contient.
     C'est **cette copie** qu'il faut essayer et envoyer au staff.
  3. Limites : **8 sons** par modèle, **OGG Vorbis mono** (un seul canal, pour être entendu là où est le
     joueur), **100 Ko** et **5 secondes** au plus chacun ; ils comptent dans les 1 000 Ko compressés.
     Un son hors limites est refusé, avec la raison dans le chat (et dans le rapport d'import).
  4. En jeu, le son est joué par le moteur de son de Minecraft, comme les autres : volume du staff, à
     16 blocs, catégorie *Joueurs*, coupé par l'option « Sons des cosmétiques ». Un son embarqué passe
     avant un son de Minecraft du même nom.
  - Format, pour ceux qui écrivent le fichier eux-mêmes : un champ racine
    `"phynaria_sounds": {"fouet_claque": "data:audio/ogg;base64,…"}`, et `fouet_claque` dans la clé.
- Le son est joué quand l'animation passe sur la clé, à chaque tour pour une animation en boucle. Il est
  entendu autour du joueur, par chacun dans son jeu.
- Le staff règle le **volume** du cosmétique (0, 25, 50 ou 100 %) dans la fenêtre *Catégorie et
  animations*. Chaque joueur peut couper les sons des cosmétiques dans ses Paramètres.
- 32 sons au plus par animation. Un nom invalide est ignoré et signalé dans le rapport.

### 6.6 Familiers vivants

Un familier peut quitter le corps du joueur et le **suivre tout seul**, comme un loup apprivoisé : il
marche à côté de lui, court pour le rattraper, saute sur une marche, s'assoit, s'endort, nage ou se pose
sur son épaule.

**1. Le déclarer : un bloc `familier`**

Dans `unhandled_root_fields.phynaria` (section 5 ter, point 6) :

```json
"familier": {"mode": "sol", "distance": 3, "vitesse": 1, "hauteur": 1.8}
```

| Clé | Valeurs | Par défaut |
|---|---|---|
| `mode` | `sol` (marche à côté), `vol` (vole près de l'épaule), `nage` (nage avec le joueur dans l'eau, marche sur terre), `perche` (se pose sur l'épaule gauche, s'envole quand le joueur court, saute, vole ou nage), `aucun` | `aucun` |
| `distance` | 1,5, 2, 3, 4, 5, 6 ou 8 blocs : la distance à laquelle il s'arrête | 3 |
| `vitesse` | 0,5, 0,75, 1, 1,25, 1,5 ou 2 : multiplie sa vitesse de marche et de vol | 1 |
| `hauteur` | 0,5 à 3 blocs : la hauteur de vol au-dessus des pieds du joueur (`vol` et `perche`) | 1,8 |

- **Sans bloc `familier`, ou avec `"mode": "aucun"`, rien ne change** : le cosmétique est porté sur le
  joueur comme avant. Une valeur inconnue fait de même, avec une ligne dans le rapport.
- Le rapport d'import confirme : « familier lu dans le modèle (mode sol) ».

**2. Le modèle**

- Construisez l'animal **les pattes à l'origine (0, 0, 0)**, la tête vers le **nord (−Z)**, comme le
  joueur (section 3). Il est dessiné à la même échelle que le joueur.
- N'utilisez **pas** les groupes du corps (`head`, `body`…) : un familier vivant ne suit pas le corps.
  Rangez ses morceaux dans vos propres groupes (`renard`, `queue`, `tete`…), pivot à la jointure.
- Tout le reste marche comme pour un cosmétique porté : `add_`, `trans_`, `cam_`, `ctrl_`, `_e`,
  reflets, textures animées, sons.
- **Perché** : l'origine du modèle est posée sur l'épaule gauche (1,42 bloc du sol, 1,15 accroupi) :
  modélisez l'animal assis, les pattes à l'origine.

**3. Ses animations, choisies par leur nom**

Le mod regarde la dernière partie du nom : `animation.renard.pet_walk` → `pet_walk`. Le préfixe `pet_`
est conseillé, `walk` seul marche aussi, et les mots français aussi.

| État | Quand | Noms reconnus | Sinon |
|---|---|---|---|
| Repos | il attend près du joueur | `pet_idle`, `idle`, `repos`, `immobile` | — |
| Marche | il suit | `pet_walk`, `walk`, `marche` | Repos |
| Course | il est loin ou le joueur court | `pet_run`, `run`, `sprint`, `cours`, `course` | Marche |
| Assis | le joueur s'accroupit à côté, ou rien ne bouge depuis 20 s ; perché sur l'épaule | `pet_sit`, `sit`, `assis`, `perch` | Repos |
| Sommeil | le joueur dort, ou rien ne bouge depuis 60 s | `pet_sleep`, `sleep`, `dort`, `dodo` | Assis |
| Nage | il est dans l'eau | `pet_swim`, `swim`, `nage` | Marche |
| Vol | il vole (modes `vol` et `perche`) | `pet_fly`, `fly`, `vol`, `flap` | Repos |
| Chute | il tombe | `pet_fall`, `fall`, `chute` | Vol |
| Saut | il saute sur une marche | `pet_jump`, `jump`, `saut` | Chute |
| Atterrissage | il retombe au sol (0,3 s) | `pet_land`, `land`, `atterri` | Repos |

- Les changements d'état sont fondus pendant 0,2 s. Sans aucune de ces animations, il joue
  l'animation du cosmétique (section 6.2, « Rien de choisi pour Immobile »).
- **`overlay_<nom>`** est joué tout le temps par-dessus, comme pour un cosmétique porté.
- **`event_<événement>`**, joué une fois par-dessus :

  | Nom | Quand |
  |---|---|
  | `event_equip` | il apparaît |
  | `event_jump`, `event_land` | il saute sur une marche, il retombe |
  | `event_teleport` | trop loin (20 blocs) ou coincé 3 s : il revient à côté du joueur |
  | `event_perch` | il se pose sur l'épaule |
  | `event_owner_hurt` | son maître prend un coup |
  | `event_enter_<état>`, `event_exit_<état>` | il entre dans un état ou en sort : `event_enter_sit`, `event_exit_sleep`… (idle, walk, run, sit, sleep, swim, fly, fall, jump, land) |

**4. Molang**

Pour un familier vivant, les requêtes de la section 6.3 parlent **du familier** : `query.ground_speed`
(sa vitesse), `query.vertical_speed`, `query.is_on_ground`, `query.is_swimming`, `query.is_flying`,
`query.is_sleeping`, `query.is_in_water`, `query.yaw_speed`, `query.distance_to_camera`,
`query.time_of_day`, `query.is_in_rain`, `query.instance_seed`, `query.anim_time`, `query.life_time`…
Nouvelles requêtes :

| Variable | Valeur |
|---|---|
| `query.is_pet` | 1 pour un familier vivant, 0 sinon |
| `query.is_perched` | 1 sur l'épaule |
| `query.is_sitting` | 1 assis |
| `query.owner_distance` | distance à son maître (blocs) |
| `query.owner_is_sneaking`, `query.owner_is_sprinting`, `query.owner_is_sleeping` | 1 si vrai, 0 sinon |
| `query.owner_health`, `query.owner_max_health` | vie de son maître |
| `query.owner_ground_speed` | vitesse de son maître (blocs par seconde) |

Exemple, une queue qui remue plus vite quand le maître s'approche :
`math.sin(query.anim_time * (360 + math.max(0, 6 - query.owner_distance) * 120)) * 25`.

**5. En jeu**

- **Un seul familier vivant par joueur** : le premier porté. Un deuxième cosmétique avec un bloc
  `familier` est porté sur le joueur comme avant.
- Il est calculé par le jeu de chaque joueur qui le voit : **aucun coût pour le serveur**. Deux joueurs
  peuvent le voir à des endroits très légèrement différents.
- Il ne traverse pas les murs : il saute sur une marche d'un bloc, et revient à côté du joueur quand il
  est coincé 3 s ou à plus de 20 blocs. Un familier qui vole passe au-dessus des blocs.
- Il est dessiné aussi quand vous jouez à la première personne (pas encore vérifié en jeu).
- Il disparaît quand son maître est invisible ou spectateur. Il n'est pas dessiné à plus de 64 blocs.
- Le menu Apparence le montre porté, comme avant.

**Ce qui ne marche pas encore pour un familier vivant** :
- ses particules (`emit_`) ne sont pas lancées ;
- les groupes `phys_` restent sur leur pose animée, sans ressort ;
- avec un pack de shaders, il ne projette pas d'ombre (le joueur, si) ;
- les autres joueurs ne peuvent pas interagir avec lui : ce n'est pas une vraie entité.

> 🧪 Vérifié en jeu, avec et sans shader, sur un renard d'exemple :
> - au sol : il attend à 2 blocs, suit en marchant quand le joueur avance, s'assoit quand il
>   s'accroupit ;
> - en vol : il reste à côté de l'épaule ;
> - perché : il reste sur l'épaule gauche pendant la marche, plus bas quand on s'accroupit.
>
> Les modes ont aussi des tests automatiques (marche sur une marche, retour quand il est trop loin,
> envol de l'épaule, nage sous la surface). Le mode `nage` n'a été testé que par ces tests
> automatiques, pas encore dans l'eau
> en jeu.

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
| Sons | 32 clés par animation ; 8 sons embarqués, OGG Vorbis mono, 100 Ko et 5 s chacun |
| Instructions Molang (`;`) | 16 par clé, 64 variables par cosmétique et par joueur |
| Distance à l'origine (cubes, pivots, au repos) | 128 px sur chaque axe (cosmétique, familier), 320 px (effet de téléportation), 64 px (skin d'objet) |
| Déplacement d'un groupe par une clé `position` | 320 px |
| Rotation de base d'un cube ou d'un groupe | ±360° |
| *Inflate* | −8 à 8 |
| Animations | 32 |
| Clés d'animation (total) | 32 768 |
| Durée d'une animation | 600 s |
| Expression Molang | 512 caractères |
| Nom d'une catégorie | 24 caractères |
| Cosmétiques portés en même temps par un joueur | 3 |
| Sortes de particules par cosmétique | 4 modélisées + 4 de Minecraft |
| Points de départ de particules (`emit_`) | 32 |
| Familiers vivants par joueur | 1 (les autres sont portés) |
| Skins d'objets portés par un joueur | 1 par type d'objet (12 types), en plus des cosmétiques |
| Effet de téléportation | 1 par joueur ; départ et arrivée 5 s au plus ; vu à 64 blocs |
| Fiche : nom, ensemble, rareté | 40, 40 et 24 caractères |
| Fiche : description, lore | 300 et 500 caractères |
| Description d'un article de la boutique | 160 caractères |

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
- Plusieurs textures sont fusionnées en une seule, à leur taille d'origine (512 × 512 au plus pour
  l'ensemble). Pour une texture animée, seule la première image est gardée.
- Les calques d'une texture restent des calques : `lame_e` (lumineux) et `lame_r` (masque de reflet) vont
  avec `lame`, et sont fusionnés de la même façon, chacun dans la case de sa texture. Avec une seule
  texture, son unique `_e` va avec elle quel que soit son nom. `_m` est gardé tel quel. Avant le
  6 novembre 2026 (soir), tout était réduit à 256 × 256 et `_e` perdait sa lumière.

---

## 10. Import par le staff

1. **Importer** : onglet Apparence, bouton *Importer…*, puis choisir le fichier.
2. **Catégorie** : Chapeaux, Visage, Dos et ailes, Mains, Familiers, Autres, ou un nom libre.
3. **Lumineux** : « Oui » pour dessiner tout le cosmétique en pleine lumière (section 5 bis).
   **Volume des sons** si le modèle en a (section 6.5).
   **Armure** : comment le cosmétique se comporte quand le joueur porte une armure :
   - **Normale** : dessiné comme modélisé (une pièce collée au corps passe sous l'armure, qui est
     gonflée d'environ 1 px) ;
   - **Par-dessus** : les parties des groupes `head`, `body`, bras et jambes sont **écartées comme
     l'armure portée à cet endroit** (casque, plastron et manches de 1 px, jambières de 0,5 px, bottes de
     1 px). Une sangle posée à 0,4 px du torse passe alors par-dessus le plastron, et reste collée au corps
     sans armure. Fait pour les pièces proches du corps (harnais, sangles, bracelets) : une pièce loin du
     corps s'écarte aussi un peu ;
   - **Cachée** : l'armure du joueur n'est pas dessinée pendant qu'il porte ce cosmétique (il la porte
     toujours, elle le protège ; une élytre reste visible).
   Commande équivalente : `/puadmin skin armor <skin> normal|over|hide`.
   Si le modèle a des particules, une fenêtre par sorte suit (section 5 ter), **pré-remplie avec les
   réglages écrits dans le fichier** (point 6).
4. **Animations par état** : déjà pré-remplies si les noms suivent la section 6.2. Clic pour
   l'animation suivante, clic droit pour la précédente, « Aucune » pour aucune.
5. **Fiche de l'objet** (dernière fenêtre) : nom, ensemble, description, lore et rareté, pré-remplis
   avec la `fiche` du fichier (section 10 bis). *Importer* envoie tout.
6. **Rapport d'import** : nombre de cubes et de groupes, profondeur, clés par canal, taille de la
   texture et taille compressée, ce qui a été lu dans le fichier (réglages de particules, fiche,
   familier), plus un avertissement pour chaque élément ignoré :
   - cubes ou groupes masqués ;
   - pistes d'effets ;
   - canaux non pris en charge ;
   - clés bezier ;
   - expressions Molang non comprises ;
   - noms coupés ;
   - réglages du fichier inconnus ou hors limites (la valeur gardée est indiquée).

Un cosmétique peut être réservé à un rôle (VIP, etc.) : seuls les joueurs qui ont ce rôle peuvent le
porter.

Après l'import, tout se change depuis la **fiche de l'objet** (clic sur sa carte) : le crayon pour la
fiche et le nom, la roue dentée pour la catégorie, les animations, l'armure et les particules, la
couronne pour le rôle, la corbeille pour le supprimer.

---

## 10 bis. Fiche de l'objet (nom, ensemble, rareté, description, lore)

Chaque skin et cosmétique a une fiche, que les joueurs voient en cliquant sur sa carte (section 13).

| Champ | Contenu | Maximum |
|---|---|---|
| Nom | le nom affiché partout | 40 caractères |
| Ensemble | le nom de l'ensemble dont il fait partie (« Garde du dragon ») : les pièces du même ensemble sont réunies sur la fiche | 40 caractères |
| Rareté | `commun`, `peu_commun`, `rare`, `epique`, `legendaire`, `mythique` (couleurs : gris, vert, bleu, violet, or, rouge), ou un mot à vous, gardé tel quel | 24 caractères |
| Description | ce qu'il est, en quelques phrases | 300 caractères |
| Lore | son histoire, affichée en italique | 500 caractères |

- **Dans le fichier** (facultatif), dans le même bloc que les particules (section 5 ter, point 6) :

```json
"fiche": {"nom": "Ailes d'orage", "ensemble": "Orage", "rarete": "epique",
          "description": "Deux ailes qui crépitent quand tu voles.",
          "lore": "Forgées dans la foudre.\nElles ne s'ouvrent que pour les braves."}
```

  `\n` va à la ligne. La rareté est mise en minuscules, sans accents, espaces et tirets changés en `_`
  (`Peu commun` → `peu_commun`, `Épique` → `epique`). Un texte trop long est coupé et signalé dans le
  rapport.
- **Dans le jeu** : la dernière fenêtre de l'import, puis le crayon de la fiche. Dans les champs d'une
  ligne, tapez `\n` pour aller à la ligne. Le nom donné ici renomme le skin.
- Un ensemble se compose en donnant le **même nom d'ensemble** à plusieurs skins et cosmétiques
  (majuscules ignorées).
- **Vignette de la carte** (facultatif, dans le même bloc) : la carte montre la pièce seule, vue de trois
  quarts, au repos et cadrée sur sa boîte. Pour choisir autrement :

```json
"vignette": {"angle": [30, 45], "zoom": 1.2, "etat": "idle", "temps": 1.0}
```

  | Clé | Sens | Par défaut |
  |---|---|---|
  | `angle` | `[vue d'en haut, rotation]` en degrés : −90 à 90 pour la première | `[25, 35]` |
  | `zoom` | 0,25 à 4 fois le cadrage automatique | 1 |
  | `etat` | état (`idle`, `fly`…) ou nom d'animation dont prendre la pose | son animation par défaut |
  | `temps` | instant de cette animation, 0 à 60 s ; sans `temps`, la pièce est au repos | au repos |

---

## 11. Check-list avant d'envoyer un cosmétique

- [ ] Format *Modded Entity* (ou *Generic Model*), fichier `.bbmodel`
- [ ] Que des cubes, aucun mesh
- [ ] Une seule texture, PNG ≤ 512 × 512, enregistrée dans le fichier
- [ ] Si quelque chose doit briller : une texture `<nom>_e` de même taille, non assignée aux faces
- [ ] Le modèle est placé autour d'un joueur, les pieds à (0, 0, 0)
- [ ] Rien à plus de 128 px de l'origine (320 px pour un effet de téléportation, 64 px pour un skin d'objet)
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
- [ ] Sons : noms de sons de Minecraft dans la piste *Effets*, ou vos OGG mono embarqués avec
  `/cosmetique sons` (envoyez la copie `_sons.bbmodel`)
- [ ] Pièces des bras modélisées pour le bras de 4 px (le mod les resserre sur les bras fins) ; grosses
  pièces des bras dans un groupe `wide_`
- [ ] Fiche remplie dans le fichier (`fiche` : nom, ensemble, rareté, description, lore), section 10 bis
- [ ] Familier vivant : bloc `familier` avec son mode, animal construit les pattes à l'origine et la tête
  vers −Z, animations `pet_idle`, `pet_walk`, `pet_sit`… (section 6.6)
- [ ] Réglages des particules écrits dans le fichier si vous voulez éviter au staff de les régler
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
5. `/cosmetique lumineux` active ou coupe l'option « Lumineux » de l'aperçu ; `/cosmetique armure`
   passe d'un réglage d'armure à l'autre (Normale, Par-dessus, Cachée) ; `/cosmetique apercu stop`
   l'enlève.
6. `/cosmetique sons <fichier>` embarque les sons OGG de vos clés de son dans une copie du modèle
   (section 6.5).

Dans l'aperçu, les animations d'état sont choisies d'après leurs noms (section 6.2), les particules ont
les réglages écrits dans le fichier (sinon ceux par défaut), et le volume des sons est de 50 %. Un
familier (section 6.6) y est vivant : il vous suit. Le cosmétique apparaît aussi dans le menu Apparence.
Il n'est envoyé à personne : les autres joueurs ne le voient pas.

---

## 13. L'interface (menu Apparence et boutique)

Ce que voient les joueurs, pour savoir comment vos fiches seront présentées.

**Menu Apparence**
- **Cartes** : chaque skin et cosmétique d'une catégorie est une carte, avec une bande de la couleur de
  sa rareté, son nom sur deux lignes, sa rareté, et une ligne d'état : *Porté*, son prix en boutique, le
  rôle qui le réserve, ou son type. Survoler une carte montre l'objet sur le personnage à gauche.
- **Vignette 3D** : la carte d'un cosmétique ou d'un effet montre la pièce **seule**, sans le personnage,
  figée au repos et vue de trois quarts, cadrée sur sa boîte. La tuile d'une catégorie montre la pièce la
  plus rare que le joueur peut porter (sinon la plus rare de la catégorie). Pour choisir l'angle, le
  cadrage ou l'instant d'animation, écrivez un bloc `vignette` dans le fichier (section 10 bis).
- **Aperçu d'un effet de téléportation** (survol de sa carte ou fiche ouverte) : l'effet joue autour du
  personnage, **`depart` puis `arrivee`, en boucle**, avec une pause de 0,75 s après chacun. Le groupe
  `joueur` s'applique comme en jeu (position et échelle) : on voit le joueur entrer dans le portail ou
  rétrécir, disparaître pendant la pause, puis arriver. Un effet sans `arrivee` rejoue `depart`, et
  inversement ; un effet sans les deux joue `charge` en boucle. L'aperçu est muet et sans particules, comme
  celui des cosmétiques, et cadré sur le personnage : la partie d'un très grand effet qui sort du cadre est
  coupée.
- **Fiche de l'objet** (clic sur une carte) :
  - à gauche, l'**aperçu 3D**, à tourner à la souris ;
  - le nom en gras, la rareté, la catégorie et l'ensemble ;
  - la description, puis le **lore en italique** (barre violette à gauche), en entier ;
  - **Ce qu'il fait** : catégorie, états animés, particules, sons, familier, lumineux, armure ;
  - **L'obtenir** : son prix en boutique, ou le rôle qui le réserve, ou *Débloqué* ;
  - **Ensemble** : les autres pièces (bouton pour ouvrir leur fiche ; survol = aperçu) et **Porter
    l'ensemble**. Ce bouton met toutes les pièces que le joueur possède : un skin et jusqu'à 3
    cosmétiques. S'il faut de la place, il retire d'abord les autres cosmétiques. Survoler la ligne
    montre l'ensemble entier sur le personnage ;
  - en bas, **Essayer** : le joueur porte l'objet **15 secondes, lui seul le voit**, même s'il ne l'a pas
    encore acheté. Le menu se ferme pour qu'il se voie (touche F5). Puis **Porter** / **Retirer**, ou un
    bouton par prix pour l'acheter.
- **Staff** : en haut de la fiche, le crayon (fiche et nom), la roue dentée (réglages), la couronne
  (rôle) et la corbeille.

**Boutique**
- Les catégories sont des **tuiles**, comme les cosmétiques : un clic ouvre les articles de la catégorie,
  « ← Catégories » ramène aux tuiles. Avec une seule catégorie, les articles s'affichent directement.
- La description d'un article tient sur **deux lignes** (160 caractères au plus). Plus longue, elle se
  termine par « … » et s'affiche en entier au survol.
- Un article qui vend un skin ou un cosmétique a un bouton **Voir la fiche** : la fiche s'ouvre dans
  l'onglet Apparence, et *Retour* ramène à la boutique.

**Partout**
- Un texte coupé par « … » s'affiche **en entier au survol**.
- Les onglets prennent la largeur de leur texte.
- Les libellés du menu latéral passent sur deux lignes quand il y a la place.

---

## 14. Skins d'objets (épées, outils, arcs…)

Un skin d'objet remplace, **pour tout le monde**, l'apparence de tous les objets d'un type tenus par le
joueur qui le porte. Par exemple, la « Lame de feu » remplace toutes ses épées, du bois à la netherite,
y compris les épées des autres mods.

**Les types**

| Type | Id | Objets reconnus |
|---|---|---|
| Épées | `epee` | tag `#minecraft:swords` |
| Pioches | `pioche` | `#minecraft:pickaxes` |
| Haches | `hache` | `#minecraft:axes` |
| Pelles | `pelle` | `#minecraft:shovels` |
| Houes | `houe` | `#minecraft:hoes` |
| Lances | `lance` | `#minecraft:spears` |
| Arcs | `arc` | `#c:tools/bow`, ou tout arc pour le jeu |
| Arbalètes | `arbalete` | `#c:tools/crossbow`, ou toute arbalète |
| Tridents | `trident` | `#c:tools/trident`, ou tout trident |
| Boucliers | `bouclier` | `#c:tools/shield`, ou tout bouclier |
| Masses | `masse` | `#c:tools/mace`, ou toute masse |
| Cannes à pêche | `canne` | `#c:tools/fishing_rod`, ou toute canne |

- **Les objets des mods** (étain, bronze, acier…) sont reconnus par ces tags, que les mods utilisent :
  depuis la 1.21, une épée qui n'est pas dans `#minecraft:swords` ne prend même pas Tranchant à la table
  d'enchantement. Un arc d'un mod sans tag est reconnu quand même s'il est un arc pour le jeu.
- **Pour un objet mal reconnu**, le staff ajoute une ligne dans la config du serveur
  (`phynariautilities-server.toml`, section `[itemSkins]`, liste `types`) :
  `"monmod:faux = houe"`, `"#autremod:dagues = epee"`, ou `"monmod:baton = aucun"` (jamais de skin). Ces
  lignes passent avant les tags.
- **`/puadmin skin itemtype`**, en tenant un objet : affiche son type et pourquoi (quel tag, quelle ligne).

**Le modèle**

- Format **Java Block/Item** de Blockbench (comme un modèle d'objet de pack de ressources), en
  **cubes**. L'objet est construit **dans le bloc 16 × 16 × 16** (de 0 à 16 sur chaque axe ; jusqu'à
  64 px de l'origine est accepté).
- **Réglages *Display*** de Blockbench : ils placent l'objet en main droite et gauche, à la première et à la
  troisième personne, dans l'inventaire (`gui`), au sol (`ground`), dans un cadre (`fixed`), sur la tête.
  Ils sont repris tels quels. Sans réglage, l'objet est tenu comme un outil de Minecraft
  (`item/handheld`) : faites alors l'objet **en diagonale, pointe en haut à droite** vu de face, comme
  l'image d'une épée.
- Plusieurs textures sont acceptées : elles sont fusionnées en une seule, à leur taille (section 9).
  `_e` (lumineux), `add_`, `trans_` et les textures animées marchent comme pour un cosmétique.
- Un autre format (Modded Entity, Generic…) est lu tel quel, dans le même espace d'objet, sans réglages
  *Display* (sauf ceux écrits dans `objet.affichage`). C'est le format conseillé pour un objet animé : le
  format Java Block/Item de Blockbench n'a pas d'animations.

**Objets vivants : animations, particules et sons**

Un skin d'objet joue ses animations comme un cosmétique (canaux `rotation`, `position`, `scale`, Molang,
groupes `ctrl_*`), ses particules (`particle_`, `emit_`, `emit_mc_`, `ctrl_emit`) et ses sons. Les noms
se lisent sur la dernière partie (`item_idle` = `animation.epee.item_idle`).

| Animation | Quand | Si elle manque |
|---|---|---|
| `item_idle` | tenu en main, en boucle | aucune animation (ou l'animation du modèle, voir plus bas) |
| `item_use` | pendant l'utilisation : arc bandé, arbalète qui se charge, bouclier levé, trident ou lance levés, nourriture | `item_idle` |
| `item_swing` | pendant que la main qui le tient donne un coup ou mine | `item_idle` |
| `item_ground` | jeté au sol | `item_idle` |
| `item_gui` | dans l'inventaire, la barre d'action et les menus | figé (première image) |
| `event_swing` | à chaque coup donné avec lui | — |
| `event_hit` | le coup touche une entité (vous seul : le jeu ne dit pas aux autres ce que leurs coups touchent) | — |
| `event_break` | un bloc cassé avec lui (vous seul, pour la même raison) | — |
| `event_use_start`, `event_use_stop` | début et fin de l'utilisation | — |
| `event_select` | il arrive en main (changement d'objet) | — |
| `event_release` | la flèche, le carreau ou le trident part | — |
| `event_charged` | l'arbalète vient d'être chargée | — |
| `event_enter_<étape>` | une étape commence (`event_enter_chargee`, `event_enter_bande_3`…) | — |
| `overlay_<nom>` | tout le temps, par-dessus le reste, aussi sur le trident en vol | — |

- Les **étapes** (groupes `repos`, `bande_1`…) restent : l'animation joue sur le groupe de l'étape dessinée.
  Un passage animé entre deux étapes se fait avec `event_enter_<étape>`.
- **Un modèle fait comme un cosmétique** (aucune animation `item_…` ni `event_…` d'objet) joue son
  animation à lui en main et au sol : un cosmétique animé devenu objet garde son mouvement.
- **Requêtes Molang** en plus de celles du joueur qui le tient (vitesse, `q.is_in_rain`,
  `q.time_of_day`…) :

  | Requête | Valeur |
  |---|---|
  | `query.use_progress` | 0 à 1 pendant l'utilisation (arc : bandé en entier à 1 s ; arbalète : chargée à 1) |
  | `query.item_durability` | usure : 0 neuf, 1 près de casser (0 pour un objet incassable) |
  | `query.is_enchanted` | 1 si l'objet est enchanté |
  | `query.is_first_person` (ou `query.in_first_person`) | 1 quand il est dessiné à la 1ʳᵉ personne |
  | `query.hand` | 0 main droite, 1 main gauche |
  | `query.is_in_menu` | 1 dans l'inventaire et les menus |

- **Particules** : réglées comme pour un cosmétique (section 5 ter, fenêtres du staff ou bloc
  `particules` du fichier). Sur un objet, *Quand* vaut « toujours » sauf **Jamais** et **À l'utilisation**
  (`utilisation` : seulement pendant que l'objet est utilisé). Rafales : **À l'attaque** à chaque coup,
  **Au tir** (`tir`) quand la flèche, le carreau ou le trident part. Elles partent de l'objet en main, à la
  1ʳᵉ et à la 3ᵉ personne. Au sol, dans l'inventaire et en vol : pas de particules.
- **Sons** : mêmes règles que la section 6.5 (32 clés par animation, 8 sons embarqués), joués là où est le
  joueur qui tient l'objet ; en main seulement.
- **Où ça joue** : en main (1ʳᵉ et 3ᵉ personne, pour vous et pour les autres) ; au sol, l'état
  `item_ground` et les `overlay_` seulement ; dans l'inventaire, seulement `item_gui` ; le trident en vol,
  ses `overlay_`.
- **Option joueur** : « Animations des skins d'objets », dans Paramètres. Désactivée, les skins d'objets
  restent figés comme avant.

**Les étapes (arc bandé, arbalète chargée…)**

Un groupe **à la racine** nommé d'après une étape n'est dessiné que pendant cette étape. Un modèle sans
groupe d'étape est toujours dessiné en entier.

| Objet | Étapes (noms des groupes) | Si l'étape manque |
|---|---|---|
| Arc | `repos`, `bande_1`, `bande_2`, `bande_3` (comme les 3 images de l'arc de Minecraft) | l'étape d'avant, puis `repos` |
| Arbalète | `repos`, `bande_1`, `bande_2`, `bande_3`, `chargee`, `chargee_fusee` | `chargee_fusee` → `chargee` → `bande_3`… |
| Trident, lance | `repos`, `leve` (prêt à lancer), `lance` (trident en vol) | `lance` → `leve` → `repos` |
| Bouclier | `repos`, `bloque` | `repos` |
| Canne à pêche | `repos`, `lancee` | `repos` |
| Autres | `repos` | — |

Majuscules, accents, espaces et tirets sont ignorés : `Bandé 1` = `bande_1`.

**Le trident lancé** : dessiné avec l'étape `lance` (sinon `leve`, sinon `repos`), la pointe en avant.
Faites le trident **pointe vers le haut (+Y)**, centré dans son bloc : il est dessiné à sa taille, sans
réglages *Display*.

**Dans le fichier** (facultatif), le type et le placement, dans le bloc `phynaria` (section 5 ter,
point 6) :

```json
"objet": {"type": "epee"}
```

Les réglages *Display* du modèle Java sont recopiés là (`"affichage"`) quand le serveur nettoie le fichier.

**Import et port**

1. Onglet Apparence, **Objets**, *Importer…* : identifiant et nom, puis le **type d'objet** (pré-rempli
   depuis le fichier), puis la fiche (section 10 bis).
2. Le type se change avec la roue dentée de la fiche, ou `/puadmin skin itemtype <skin> <type>`. Un joueur
   qui le porte le garde, pour le nouveau type.
3. Commande d'import : `/puadmin skin import <id> item <fichier>` (ou `add … item <lien>`).
4. Les joueurs le portent depuis sa fiche : **un skin par type**. En porter un autre pour le même type
   remplace le premier. Les skins d'objets ne comptent pas dans les 3 cosmétiques.
5. Comme les autres skins : libre, réservé à un rôle, ou vendu en boutique. « Essayer » le met 15 s sur
   vos objets, vu par vous seul.

**En jeu**

- Vu par tout le monde : en main (1ʳᵉ et 3ᵉ personne), au sol (objet jeté par le joueur, avec Q ou
  depuis l'inventaire), trident lancé. Dans **votre** inventaire, votre barre d'action et les coffres
  que vous ouvrez, les objets s'affichent avec **vos** skins.
- Un objet tombé à la mort, posé dans un cadre ou tenu par un monstre garde son apparence de Minecraft.
- Options joueur, dans Paramètres : « Skins d'objets des autres » (vos skins restent toujours visibles) et
  « Animations des skins d'objets ».

> 🧪 Vérifié en jeu sans pack de shaders, avec une épée, un arc et un trident d'exemple :
> - épée en main à la 1ʳᵉ et à la 3ᵉ personne, et dans la barre d'action ;
> - arc bandé : étape `bande_3` choisie ;
> - épée jetée au sol ;
> - trident levé, puis lancé ;
> - onglet Objets du menu, avec les vrais objets dessinés.
> - épée animée d'exemple : elle se balance en main (`item_idle`), fait un tour complet au coup
>   (`event_swing`, 1ʳᵉ personne) et lance des étincelles `end_rod` (3ᵉ personne). Pas encore vérifiés en
>   jeu : `event_hit`, `event_break`, `event_release`, `event_charged` et les sons d'un objet.
>
> **Avec un pack de shaders, pas encore vérifié** : dans notre monde de test, Iris 1.11.4
> (Complementary Unbound) plante dès que le joueur tient une épée et un arc, même avec les skins
> d'objets désactivés. Le problème ne vient donc pas des skins d'objets, mais nous n'avons pas pu les voir
> avec ce pack.

---

## 15. Effets de téléportation

Un effet de téléportation est un modèle Blockbench joué **là où le joueur part** et **là où il arrive**
quand il se téléporte, vu par tous les joueurs autour. Ça peut être n'importe quoi : un portail qui
s'ouvre et qu'on traverse, une arrivée du ciel, une colonne de lumière, un nuage de fumée…

**Quand il se joue** : `/tpa`, les homes, les warps, le spawn, le retour (`/back`, `/spawnback`), le
rassemblement de groupe, la téléportation du staff vers le home d'un joueur, et **`/tp`** (y compris
quand le staff téléporte quelqu'un d'autre : c'est l'effet du joueur déplacé qui se joue). **Pas** sur le
RTP, ni avec une perle de l'Ender ou un portail. Rien non plus pour un joueur en vanish ou spectateur.

**Les animations**, trouvées par la dernière partie de leur nom (`animation.portail.arrivee`), accents
et majuscules ignorés :

| Animation | Jouée | Durée |
|---|---|---|
| `charge` (facultative) | en boucle **pendant le compte à rebours** (incantation, cercle qui se forme…), là où se tient le joueur ; elle s'arrête s'il bouge et que la téléportation est annulée | tant que dure le compte à rebours (`/tp` n'en a pas) |
| `depart` | à l'endroit quitté : elle continue après le départ du joueur | sa longueur, **5 s au plus** |
| `arrivee` | à destination | sa longueur, **5 s au plus** |

Mettez `depart` et `arrivee` en *once*, et `charge` en *loop*. Une couche `overlay_` joue tout le temps
par-dessus, comme pour un cosmétique.

**Le modèle**
- Construit autour d'un joueur debout, les pieds à l'origine, face au nord (−Z), comme un cosmétique :
  l'effet est posé à l'endroit et dans la direction du joueur.
- **Taille** : jusqu'à **320 px (20 blocs)** de l'origine sur chaque axe (section 3) : une faille dans le
  ciel, une colonne jusqu'aux nuages, un cercle sur toute une place. L'effet n'est jamais écarté parce que son
  origine sort de l'écran ou passe derrière un mur : il reste dessiné tant qu'il se joue près de vous.
- Les groupes du corps (`head`, `body`…) ne servent pas : l'effet n'est pas porté.
- `add_`, `trans_`, `cam_`, `ctrl_`, `_e`, reflets, textures animées, **particules** (`emit_`, lancées tant
  que l'effet joue, selon leur *Nombre* ; les rafales ne servent pas) et **sons** (clés de son, sons
  embarqués) marchent comme pour un cosmétique.

**Le groupe `joueur` : montrer le joueur à sa façon**

Un groupe **vide** nommé `joueur`, placé où vous voulez, représente le joueur pendant l'animation :
- pendant la **charge** (compte à rebours), le joueur est dessiné, lui aussi, à la position et à la taille
  de ce groupe : il peut léviter pendant l'incantation, s'enfoncer peu à peu dans un portail au sol ou se
  figer avant de partir. Laissez le groupe sans clé dans `charge` pour qu'il reste debout à sa place. Si le
  compte à rebours est annulé (le joueur bouge), son image revient aussitôt à sa vraie place ;
- à l'**arrivée**, le joueur est dessiné **à la position de ce groupe**, à sa **taille** (échelle). À
  l'échelle 0, il n'est pas dessiné du tout. Pour une arrivée du ciel, animez la position du groupe de
  `y = 160` (10 blocs) à `0`. Pour sortir d'un portail, partez de derrière le portail, échelle 0, puis
  passez à 1 en le traversant ;
- au **départ**, une **copie du joueur**, avec son skin, reste sur place et suit ce groupe, **position et
  échelle** : elle entre dans le portail, s'envole, est aspirée par un vortex en rétrécissant jusqu'à
  disparaître (échelle 0)…
- **les trois animations se comportent pareil** : position et taille du groupe, mises à l'échelle depuis les
  pieds ; sous l'échelle 0,05, le joueur (ou la copie) n'est pas dessiné du tout. Jusqu'au 7 novembre, la
  copie du départ ne suivait que la position et gardait sa taille ;
- **c'est purement visuel** : pour le serveur, le joueur est déjà arrivé. Il peut bouger et se battre
  normalement ; seule son image suit le groupe pendant l'animation. Son ombre reste à sa vraie place.
- La rotation du groupe n'est pas reprise (seulement sa position et sa taille). La copie du départ porte
  le skin du joueur, sans ses cosmétiques.
- Sans groupe `joueur`, l'effet est simplement posé au sol et le joueur apparaît normalement.

**Import et port**
- Onglet Apparence, **Effets**, *Importer…* : identifiant et nom, puis la fiche (section 10 bis).
  Commande : `/puadmin skin import <id> effect <fichier>`.
- **Un seul effet par joueur**, en plus des cosmétiques et des skins d'objets. En porter un autre le
  remplace.
- Libre, réservé à un rôle ou vendu en boutique. **« Essayer »** joue le départ à 3 blocs derrière vous et
  l'arrivée sur vous, vu par vous seul.
- **Aperçu dans le menu** (Apparence et boutique, section 13) : `depart`, une pause de 0,75 s, `arrivee`,
  une pause, en boucle, avec le groupe `joueur` comme en jeu. Pendant la pause qui suit le départ, le
  joueur n'est pas affiché (il est parti). `charge` n'y est jouée que si l'effet n'a ni `depart` ni
  `arrivee`. Soignez donc ces deux animations : ce sont elles que les joueurs voient avant d'acheter.
- Vu par les joueurs à moins de 64 blocs du départ ou de l'arrivée. Option joueur dans Paramètres :
  « Effets de téléportation des autres » (les vôtres restent toujours visibles).

> 🧪 Vérifié en jeu sans pack de shaders, avec un portail d'exemple : la charge tourne pendant le compte
> à rebours ; au départ, le portail s'ouvre et la copie du joueur entre dedans ; à l'arrivée, le portail
> s'ouvre et le joueur tombe du ciel. Pendant la charge, le joueur lévite (groupe `joueur` animé dans
> `charge`). Pas encore essayé : `/tp` (ni en jeu, ni par un test
> automatique), l'annulation du compte à rebours en bougeant, et un pack de
> shaders.
>
> 🧪 8 novembre, avec et sans shader (Iris 1.11.4 + Complementary Unbound r5.9.3) : au départ, la copie du
> joueur rétrécit avec le groupe `joueur` (échelle 1 → 0 entre 0,9 et 1,1 s) puis disparaît. Dans le menu,
> l'aperçu joue le départ (le joueur rétrécit avec le portail), la pause (joueur caché), puis l'arrivée
> (le joueur tombe dans le portail).
