# Demandes au mod — cosmétiques plus vivants : transparence, lumière, reflets, particules, animation

Tu travailles sur le mod Phynaria Utilities (Minecraft 26.1.2, NeoForge). Les cosmétiques sont des `.bbmodel` importés par le staff (`guide-cosmetiques.md`, qui décrit l'existant). Ce document liste ce qui nous manque pour aller plus loin, **par ordre de priorité**, avec pour chaque point : le besoin constaté, ce qu'on propose dans le `.bbmodel` pour que ça reste faisable dans Blockbench, et des pistes de rendu. Les conventions proposées ne sont que des propositions : garde la forme qui t'arrange, du moment qu'elle s'écrit dans Blockbench.

Contexte : nos derniers essais d'aura façon anime (énergie lumineuse autour du joueur) ont tous échoué sur les mêmes limites, sans semi-transparence, sans rendu additif et sans plaque toujours tournée vers la caméra. Une flamme en plaque découpée se voit par la tranche, et un liseré lumineux en plaques fixes traverse le joueur dès qu'on tourne autour.

## Résumé

| # | Demande | Ce que ça débloque | Priorité |
|---|---|---|---|
| 1 | Rendu **additif** par groupe | Lueurs, halos vaporeux, auras, énergie, feu « léger » | Haute |
| 2 | **Semi-transparence** par groupe, avec tri | Verre, glace, fumée, hologrammes, voiles, ailes de fée | Haute |
| 3 | Groupes **face caméra** (billboard) | Flammes, auras, halos, éclats qui ne se voient plus par la tranche | Haute |
| 4 | Particules **vanilla** depuis les `emit_` | Feu, âme, étincelles électriques, enchantement, poussière colorée… | Haute |
| 5 | Particules du mod plus riches | Additif, face caméra, fondu, direction, rafales sur attaque | Haute |
| 6 | **Opacité et teinte animées** | Apparitions en fondu, pulsations de couleur, clignotements | Moyenne |
| 7 | **Textures animées** (images successives, défilement d'UV) | Énergie qui coule, runes qui défilent, feu qui vacille | Moyenne |
| 8 | **Reflets** (matcap, ou cartes LabPBR pour les shaders) | Métal, cristal, armure, verre brillant | Moyenne |
| 9 | Animations superposées et événements | Rotation continue sans à-coup, saut, atterrissage, mise en place | Moyenne |
| 10 | Molang étendu | Virage, regard, fusée, météo, hasard par joueur, variables | Moyenne |
| 11 | Os à ressort (physique secondaire) | Queues, capes, oreilles, chaînes qui réagissent au mouvement | Basse, mais très visible |
| 12 | Aperçu local en jeu | Tester un fichier sans import du staff : itérations bien plus rapides | Haute pour nous |
| 13 | Confort | Masquer en vue à la première personne, limites, sons | Basse |

---

## 1. Rendu additif par groupe (priorité haute)

**Besoin.** Une lueur, c'est de la lumière qui s'ajoute à ce qu'il y a derrière : noir = invisible, couleur = lumière, sans bord dur ni fond opaque. Aujourd'hui, une aura est faite de plaques opaques (le noir reste noir), et le calque `_e` ne s'ajoute qu'à la surface déjà opaque du cosmétique.

**Proposition dans le `.bbmodel`.** Un groupe dont le nom commence par `add_` (ex. `add_aura`, `add_halo`) : tous ses cubes, et ceux de ses sous-groupes, sont dessinés en additif avec leur texture normale. Le reste du modèle ne change pas.

**Pistes de rendu.** Mélange `ONE, ONE` (ou `SRC_ALPHA, ONE`), test de profondeur actif, **écriture de profondeur coupée**, dessiné après les parties opaques, pleine lumière (comme les yeux des araignées, le rayon de balise ou l'armure chargée du creeper). Le tri est inutile puisque l'addition est commutative. Sous Iris, la passe translucide ou émissive.

**Critère.** Une plaque `add_` à texture en dégradé noir → rouge laisse voir le décor derrière, ne montre aucun rectangle noir, et brille la nuit.

## 2. Semi-transparence par groupe, avec tri (priorité haute)

**Besoin.** Le verre, la glace, la fumée, un voile, une aile de fée, un hologramme. Aujourd'hui, l'alpha est en tout ou rien (*cutout*).

**Proposition.** Un groupe `trans_<nom>` : l'alpha de la texture (1 à 254) est respecté pour ses cubes. Le reste du modèle reste en *cutout*, donc aucun changement pour les cosmétiques existants.

**Pistes de rendu.** Un type de rendu translucide d'entité, faces des groupes `trans_` triées de l'arrière vers l'avant (centre de chaque face dans le repère caméra), dessinées après l'opaque. Un tri par cosmétique suffit : on accepte de petits défauts entre deux cosmétiques translucides qui se croisent.

**Critère.** Deux plaques à 50 % d'opacité qui se croisent s'affichent dans le bon ordre sous tous les angles, sans trou.

## 3. Groupes face caméra (priorité haute)

**Besoin.** Une flamme, un éclat, une lueur en plaque disparaît par la tranche. Il faut aujourd'hui croiser des plaques, ce qui fait des « X » visibles et des barres qui traversent le joueur (constaté sur nos auras).

**Proposition.**
- `cam_<nom>` : le groupe tourne autour de son pivot pour que son plan avant (face `south`, +Z) regarde la caméra (billboard sphérique) ;
- `camy_<nom>` : rotation autour de l'axe vertical seulement (billboard cylindrique : flammes, colonnes d'énergie, qui restent debout).

L'animation du groupe s'applique ensuite dans ce repère : on peut faire onduler ou grandir une flamme qui reste face à nous.

**Critère.** Une plaque `camy_` reste visible de face quand on tourne autour du joueur, et reste verticale.

## 4. Particules vanilla depuis les points `emit_` (priorité haute)

**Besoin.** Les particules de Minecraft sont déjà belles, animées et bien rendues (`flame`, `soul_fire_flame`, `electric_spark`, `end_rod`, `glow`, `enchant`, `portal`, `cherry_leaves`, `snowflake`, `dust`…). Aujourd'hui, les pistes d'effets de Blockbench sont ignorées, et seules nos particules modélisées sont possibles.

**Proposition.** Un groupe vide `emit_mc_<identifiant>` lance la particule vanilla du même nom (ex. `emit_mc_soul_fire_flame`, `emit_mc_electric_spark`). Pour celles qui ont des paramètres, un suffixe : `emit_mc_dust_ff2040_15` (couleur hexadécimale, taille × 10). Réglages du staff identiques à ceux de nos particules (quand, nombre par seconde), avec la même limite par joueur.

**Critère.** Un `emit_mc_flame` au bout d'une baguette fait monter des flammes vanilla à cet endroit, et suit l'animation.

## 5. Particules du mod plus riches (priorité haute)

**Besoin.** Nos particules ne savent que tomber, flotter ou monter, puis rétrécir. Pour une aura, des étincelles ou une traînée, il manque l'orientation, le fondu et la direction.

**Propositions, par sorte de particule (réglages du staff, ou suffixes de nom) :**
- **rendu** additif ou translucide (comme les points 1 et 2) ;
- **face caméra** : la particule regarde toujours la caméra (aujourd'hui, une plaque vue par la tranche disparaît) ;
- **fin de vie** en fondu d'opacité au lieu du rétrécissement ;
- **direction et vitesse de départ** : le long de l'axe +Y du groupe `emit_` (on oriente le groupe dans Blockbench), avec une dispersion en degrés ;
- **gravité** réglable, négative comprise, et freinage de l'air ;
- **variation aléatoire** de taille, de rotation et de durée de vie ;
- **rafale sur événement** : N particules d'un coup à l'attaque, à la blessure, au saut ou à l'atterrissage ;
- **traînée** : particules qui gardent la vitesse du joueur à 0 % (sillage immobile) ou à 100 % (suivent le joueur) ;
- **limite par joueur** relevée, ou réglable par le staff pour les cosmétiques rares (64 aujourd'hui).

## 6. Opacité et teinte animées (priorité moyenne)

**Besoin.** Faire apparaître ou disparaître une pièce en fondu (et non par `scale` à 0), faire pulser une couleur, clignoter une rune. Le `.bbmodel` n'a pas de canal d'opacité ni de couleur.

**Proposition : des groupes de contrôle.** Un groupe vide nommé `ctrl_alpha` ou `ctrl_teinte`, placé dans un groupe, pilote ce groupe parent par sa **position animée** (canal déjà lu par le mod, Molang compris) :
- `ctrl_alpha` : `x` = opacité de 0 à 1 (utile avec `trans_` et `add_`) ;
- `ctrl_teinte` : `x`, `y`, `z` = multiplicateurs rouge, vert, bleu (1 = inchangé) ;
- `ctrl_lumiere` : `x` = intensité du calque `_e` pour ce groupe (0 = éteint, 1 = normal, plus = plus fort).
- `ctrl_emit`, placé dans un point `emit_` : `x` = facteur de cadence de ce point (0 = coupé, 1 = réglage du staff, 3 = trois fois plus). Ainsi l'animation synchronise les particules avec le geste (un jet de vapeur au moment exact de la décharge d'une soupape).

Ça reste dans les trois canaux actuels et ça s'écrit dans Blockbench sans plugin.

## 7. Textures animées (priorité moyenne)

**Besoin.** De l'énergie qui coule le long d'une aile, des runes qui défilent, un feu qui vacille, un œil qui cligne, sans multiplier les cubes.

**Propositions.**
- **Images successives** : Blockbench sait déjà animer une texture faite d'images empilées verticalement (propriétés `frame_time`, `frame_order`, `frame_interpolate` de la texture). Les lire comme un `.mcmeta`. La limite de 512 × 512 deviendrait par image, ou bien le nombre d'images serait limité.
- **Défilement d'UV** : `ctrl_uv` (même principe que le point 6) : `x`, `y` = décalage des UV du groupe parent, en texels, animable en Molang. Avec `math.mod`, on obtient un défilement continu.

## 8. Reflets (priorité moyenne)

**Besoin.** Le métal, le cristal, une armure, du verre ne brillent pas : tout est éclairé de façon mate.

**Propositions (l'une ou l'autre, ou les deux) :**
- **Pour les shaders** : accepter, comme `_e`, des textures `<texture>_n.png` (normales) et `<texture>_s.png` (spéculaire, convention LabPBR) embarquées, et les transmettre à Iris. Les joueurs sous shader auraient de vrais reflets.
- **Sans shader** : un reflet de type *matcap*, avec un masque `<texture>_r.png` (0 = mat, 255 = miroir) et une image de reflet fournie par le mod (ou embarquée) mélangée selon l'orientation de la face par rapport à la caméra. Même sans réalisme, un liseré qui glisse quand on tourne suffit à faire lire « métal » ou « verre ».

## 9. Animations superposées et événements (priorité moyenne)

**Besoin.**
- Une pièce qui tourne en continu (halo, anneau) saute ou tourbillonne au fondu entre deux états, parce que chaque animation d'état a sa propre phase.
- Il n'existe pas d'animation de saut, d'atterrissage ou de mise en place du cosmétique.

**Propositions.**
- **Couche permanente** : une animation nommée `overlay_<nom>`, en boucle, jouée en permanence **par-dessus** l'animation d'état, sans fondu ni remise à zéro. Ce serait le bon endroit pour les rotations continues et les pulsations.
- **Animations d'événement** en `once`, jouées par-dessus comme `attack` et `hurt` : `jump` (départ du saut), `land` (atterrissage, avec la vitesse de chute en Molang), `equip` (quand on met le cosmétique), et les changements d'état (`enter_glide`, `exit_glide`, `enter_sneak`…).

## 10. Molang étendu (priorité moyenne)

Variables qu'on utiliserait tout de suite :
- `query.yaw_speed` (vitesse de rotation du corps) : les ailes et les queues s'inclinent dans les virages ;
- `query.head_x_rotation`, `query.head_y_rotation` : un familier ou des oreilles qui suivent le regard ;
- `query.is_boosting` (fusée active en élytres) : aujourd'hui, nous l'approchons par un seuil de vitesse ;
- `query.time_of_day`, `query.moon_phase`, `query.is_in_rain`, `query.is_in_water`, `query.is_in_lava` : un cosmétique qui change la nuit ou sous la pluie ;
- `query.hurt_time`, `query.attack_time` (0 à 1 pendant l'événement) ;
- `query.instance_seed` (nombre fixe par joueur) et `math.random(a, b)` : deux joueurs avec le même cosmétique ne bougent pas en même temps ;
- `query.distance_to_camera` et `query.is_first_person` ;
- **variables mémorisées** (`variable.x = …;` d'une image à l'autre) : lissage, inertie, accélération. Aujourd'hui, toute variable vaut 0.

## 11. Os à ressort (priorité basse, mais très visible)

**Besoin.** Une queue, une cape, des oreilles, une chaîne ou un pompon qui réagissent aux mouvements du joueur (élan, arrêt, virage), au lieu d'une animation fixe.

**Proposition.** Un groupe `phys_<nom>` (ou une chaîne de groupes `phys_` imbriqués) se comporte comme un ressort amorti autour de sa pose animée. Raideur et amortissement en suffixe (`phys_queue_r40_a60`) ou réglés par le staff. La pose d'animation reste la cible : on garde la main sur le style.

## 12. Aperçu local en jeu (priorité haute pour nous)

**Besoin.** Chaque essai passe aujourd'hui par un import du staff. Un rendu hors jeu ne montre ni le shader, ni l'éclairage, ni les particules : il nous faut le jeu pour juger, et beaucoup d'allers-retours.

**Proposition.** Une commande réservée aux créateurs (ex. `/cosmetique apercu <fichier>`) qui charge un `.bbmodel` depuis un dossier local, côté client, visible par soi seul. Mêmes contrôles et même rapport d'import que l'import du staff, rechargement automatique quand le fichier change.

## 13. Confort (priorité basse)

- **Vue à la première personne** : masquer un cosmétique, ou certains groupes (`fp_cache_<nom>`), quand on joue à la première personne (une aura ou un chapeau qui gêne la vue).
- **Limites** : 4 textures `_x` au lieu de 2 si les points 7 et 8 arrivent ; préciser le point de mesure des 64 px (pieds ou centre du joueur).
- **Sons** (facultatif) : lire les pistes de sons de Blockbench (battement d'ailes, tintement), avec un volume réglé par le staff et une option joueur pour les couper.

---

## Ce qu'on peut fournir

Pour chaque point retenu, on fait un modèle de test minimal : une plaque `add_`, deux plaques `trans_` croisées, une flamme `camy_`, un `emit_mc_flame`, un `ctrl_alpha` qui fait 0 → 1 → 0 en 2 s… Avec la capture attendue, pour valider en jeu. Dis-nous l'ordre qui t'arrange, et on adapte nos conventions à ce que tu choisis.

---

## 14. Suite (après la mise à jour du guide du 2026-11-03)

Merci pour la mise à jour : tout ce qui était demandé ci-dessus est utilisé dans l'ensemble Steampunk. Il reste trois points, nés de l'usage :

- **`ctrl_reflet`** (groupe de contrôle, « 1 + position » comme les autres) : intensité des reflets `_r` du groupe. Besoin : un cosmétique qui devient brillant sous la pluie (`query.is_in_rain`), comme du métal mouillé. Aujourd'hui on ne peut qu'assombrir la teinte et renforcer le calque `_e`, pas faire briller les reflets.
- **`ctrl_emit`** (déjà au point 6) : cadence d'émission pilotée par l'animation. Besoin concret : un jet de vapeur au moment exact où la soupape décharge, et pas en continu.
- **Condition météo pour les particules** : un choix « Sous la pluie » dans le réglage *Quand* (gouttes qui coulent des ailes quand il pleut, vapeur qui fume plus).

- **`event_unequip`** : animation jouée quand on retire le cosmétique, avec un court délai avant qu'il disparaisse (le temps de l'animation, 5 s au plus). Besoin : des ailes qui se replient et rentrent dans leur sac avant de disparaître, symétrique de `event_equip`.
- **`ctrl_alpha` en partie opaque** : en jeu (capture `2026-11-04_01.44.04`), un groupe opaque dont le `ctrl_alpha` vaut −1 reste visible (le sac dorsal des ailes ne disparaît pas), alors que le guide annonce qu'il disparaît sous 10 %. Contournement actuel : échelle.
