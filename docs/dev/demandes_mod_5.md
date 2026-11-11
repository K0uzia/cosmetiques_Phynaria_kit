# Demandes au mod (5) — aperçu du menu identique au jeu

Tu travailles sur le mod Phynaria Utilities. Ce document fait suite à la demande 4 (déjà envoyée) ; il commence le 2026-11-05.

## Résumé

**Toutes faites** (guide du 2026-11-06 soir, « demandes 5 ») : `cam_`/`camy_` orientés dans le menu, skins d'objets vivants (section 14), vignettes 3D (10 bis, 13), `joueur` lu pendant `charge` (15), faces `up`/`down` comme Blockbench (3 ; c'était un demi-tour sur `up` et un miroir sur `down`), zone de 128 / 320 / 64 px au repos (3, 7). En plus : 32 animations, `java_block` à taille réelle avec `_e`/`_r` (9), `query.hit_by_entity` (6.3).

| # | Demande | Ce que ça débloque | Priorité | État |
|---|---|---|---|---|
| 1 | Dans l'aperçu du menu *Apparence*, orienter `cam_` et `camy_` vers la caméra de l'aperçu | Les auras et les plaques face caméra s'affichent dans le menu comme en jeu | Moyenne | **Faite** (guide du 2026-11-06 soir) |
| 2 | **Skins d'objets vivants** : jouer animations (avec `ctrl_`), particules et sons sur un skin d'objet, comme sur un cosmétique (section 2) | Une épée de givre qui scintille, une lance d'orage qui crépite, un pistolet qui souffle sa vapeur au tir | Haute | **Faite** (guide du 2026-11-06 soir) |
| 3 | **Visuels des cartes** du menu *Apparence* : vue 3D figée de chaque cosmétique, et de catégorie (section 3) | On reconnaît une pièce sans ouvrir sa fiche | Moyenne | **Faite** (guide du 2026-11-06 soir) |
| 4 | **Effets de téléportation** : dire dans le guide (section 15) ce que fait le groupe `joueur` pendant `charge` | Savoir si l'on peut animer le joueur pendant le compte à rebours (lévitation, il s'enfonce dans le sol) | Basse | **Faite** (guide du 2026-11-06 soir) |
| 5 | **Faces `up` et `down` : image en miroir sur X** par rapport à Blockbench (section 5) | Cercles magiques, sols, plafonds, dessus de chapeaux : ce qui est dessiné dans Blockbench s'affiche pareil en jeu | Haute | **Faite** (guide du 2026-11-06 soir) |
| 6 | **Grands effets de zone** : relever la limite de 64 px (4 blocs) qui s'applique aujourd'hui à tout modèle, surtout pour les effets de téléportation (section 6) | Faille immense dans le ciel, colonne jusqu'aux nuages, cercle sur toute une place, grandes ailes rares, grands familiers | Haute | **Faite** (guide du 2026-11-06 soir) |

---

## 1. Aperçu du menu *Apparence* identique au jeu

Dans l'aperçu du menu, les groupes `cam_` et `camy_` ne sont pas tournés vers la caméra (constaté le 2026-11-05, captures `20.36.18` et `20.36.20` : une aura `cam_` reste plaquée derrière le dos et n'apparaît qu'en liseré, alors qu'en jeu elle enveloppe la silhouette). Merci d'orienter `cam_` (face caméra) et `camy_` (face caméra, debout) vers la caméra de l'aperçu, y compris quand le joueur fait tourner le personnage à la souris, comme en jeu. En attendant, nos auras le simulent pour la vue par défaut du menu (`q.is_in_menu`), ce qui ne tient plus dès qu'on tourne le personnage.

Test : `tests_rendu/test_menu_aura_a.bbmodel` et `test_menu_aura_b.bbmodel` (mode d'emploi dans `tests_rendu/README.md`).

---

## 2. Skins d'objets : animations, particules et sons (2026-11-05)

### Constat

Le guide (section 14) dit qu'un skin d'objet accepte `_e`, `add_`, `trans_` et les textures animées, mais que **les animations (donc les groupes `ctrl_`), les particules et les sons ne sont pas joués sur un objet**. Seules les étapes (`repos`, `bande_1`, `leve`…) changent l'apparence. Nos premiers skins (épée de givre, lance d'orage, arbalète steampunk) viennent de cosmétiques animés qui perdent tout leur mouvement en devenant des objets.

### Ce qui est demandé

1. **Animations** sur un skin d'objet, avec les mêmes règles que les cosmétiques (canaux `rotation`/`position`/`scale`, Molang, `overlay_<nom>` joué en permanence, groupes `ctrl_*` : `ctrl_alpha`, `ctrl_lumiere`, `ctrl_teinte`, `ctrl_uv`, `ctrl_emit`) :
   - **états de l'objet** (noms à fixer par toi, préfixe `item_` par exemple) : `item_idle` (tenu), `item_use` (utilisé : arc bandé, bouclier levé, lance levée, canne lancée, nourriture…), `item_swing` (coup donné, minage), `item_ground` (posé au sol), `item_gui` (inventaire et menu ; par défaut figé sur la première image) ;
   - **événements** : `event_swing` (chaque coup), `event_hit` (le coup touche une entité), `event_break` (bloc cassé), `event_use_start` / `event_use_stop`, `event_select` (l'objet arrive en main), `event_release` (flèche tirée, trident lancé, carreau tiré), `event_charged` (arbalète chargée) ;
   - **les étapes** existantes restent, et une transition animée entre deux étapes serait idéale (`event_enter_<étape>`, par exemple `event_enter_chargee`).
   - **Requêtes** utiles : `q.use_progress` (0 → 1 pendant l'utilisation, arc et arbalète), `q.item_durability` (0 → 1, pour un aspect usé ou fissuré), `q.is_enchanted`, `q.in_first_person`, `q.hand` (droite / gauche), et celles du joueur qui le tient (vitesse, `q.is_in_rain`, `q.time_of_day`…).
2. **Particules** (`particle_<nom>`, `emit_<nom>`, `emit_mc_<id>`, `ctrl_emit`) avec les réglages du staff ou écrits dans le fichier (section 5 ter, point 6), plus une option *Quand* **À l'utilisation** et une **Rafale** **Au coup** / **Au tir**. Point de départ qui suit l'objet en main, en première et troisième personne.
3. **Sons** embarqués et sons Minecraft, mêmes règles que la section 6.5 (au plus 32 par animation, 8 embarqués), joués à la position du joueur ; en particulier sur `event_swing`, `event_hit`, `event_release`.
4. **Où ça joue** : en main (1re et 3e personne, pour soi et pour les autres), au sol pour l'objet jeté (états et overlay seulement), pas dans l'inventaire sauf `item_gui` (pour ne pas surcharger), trident lancé (overlay pendant le vol).
5. **Repli** : un skin sans animation reste comme aujourd'hui. Une option du joueur « Animations des skins d'objets » (à côté de « Skins d'objets des autres ») pour les couper.
6. **Format Java Block/Item** : d'après le `.jar` 1.4.0, un modèle `java_block` voit toutes ses textures, `_e` compris, fusionnées en un atlas de 256 × 256 au plus : une texture 512 est réduite de moitié et `_e` perd sa lumière, alors que le guide dit que `_e` « marche comme pour un cosmétique ». Merci de garder la taille d'origine (512) et le calque `_e` à part, ou de le dire dans le guide. En attendant, nous livrons nos skins en format `free` avec `phynaria.objet.affichage`.
7. **Guide** : merci de documenter le tout dans la section 14, avec la liste exacte des noms retenus.

Nous adapterons nos skins (scintillement de la glace, éclairs qui courent le long du fer de la lance, vapeur au tir de l'arbalète) dès que le format est fixé.

## 3. Visuels des cartes du menu *Apparence* (2026-11-06)

### Constat

Captures du 2026-11-06 (00 h 57) : dans l'onglet **Cosmétiques**, les cartes de catégorie (Chapeaux, Dos et ailes, Familiers, Auras, Set de Bérénice, Autres) n'affichent qu'une icône générique, et les cartes de cosmétique (capture 00 h 58, *Set de Bérénice* : Ailes, Aura, Diadème) n'ont qu'une petite icône de t-shirt à la couleur de la rareté, la même pour toutes les pièces. L'onglet **Objets**, lui, montre l'icône de chaque skin (épée, lance, arbalète) : c'est très lisible. Le guide (section 13) ne décrit aucun visuel de carte, et aucun champ du modèle ne permet d'en fournir un.

### Ce qui est demandé

1. **Carte d'un cosmétique** : une petite vue 3D figée de la pièce seule (sans le personnage), rendue par le mod à partir du modèle, cadrée sur sa boîte englobante, sous un angle de 3/4 (comme l'icône d'un bloc). Mise en cache à l'import.
2. **Carte d'une catégorie ou d'un ensemble** : la vue de la première pièce possédée, ou de la plus rare, à la place de l'icône générique.
3. **Facultatif, réglable par le modèle** : un champ `phynaria.vignette` (par exemple `{"angle": [30, 45], "zoom": 1.2, "etat": "idle", "temps": 1.0}`) pour choisir l'angle, le cadrage et l'instant d'animation ; sans lui, le cadrage automatique.
4. **Guide** : documenter le champ dans les sections 10 bis et 13.

## 4. Effets de téléportation : le joueur pendant `charge` (2026-11-06)

### Constat
La section 15 du guide dit ce que fait le groupe `joueur` pendant `depart` (une copie du joueur le suit) et pendant `arrivee` (le joueur est dessiné à sa position et à sa taille), mais rien pour `charge`, l'animation en boucle du compte à rebours. Nos outils supposent pour l'instant que pendant `charge` le joueur reste dessiné normalement, debout à sa place, et que le groupe `joueur` est ignoré.

### Ce qui est demandé
1. **Préciser dans le guide** ce qui se passe pendant `charge` : le joueur est-il toujours visible normalement ? Le groupe `joueur` est-il lu ?
2. Si ce n'est pas déjà le cas, **appliquer le groupe `joueur` pendant `charge` aussi** (position et échelle, purement visuel comme à l'arrivée) : le joueur pourrait léviter pendant l'incantation, s'enfoncer peu à peu dans un portail au sol ou se figer dans la glace avant de partir. Le compte à rebours étant annulé si le joueur bouge, l'image reviendrait à sa vraie place à l'annulation.

## 5. Faces horizontales (`up`, `down`) : image en miroir sur X (2026-11-06)

### Constat
Un cercle magique au sol fait de huit plaques en arc (une face `up` par arc, la courbe asymétrique dans l'image) s'affiche en jeu comme un « nid » de courbes qui se croisent, alors qu'il forme un cercle dans Blockbench (captures `2026-11-06_15.58.36`, `15.58.42`, `15.58.49`, effet « Ascension de Bérénice »).

Test fourni : `docs/dev/tests_rendu/test_uv_up.bbmodel` (effet de téléportation ; même image sur une face `up` au sol, une face `down` au-dessus de la tête et une face `north` debout devant, de contrôle : flèche vers le haut de l'image, coin rouge en haut à gauche, bleu en haut à droite, lettres O à gauche, E à droite). Captures `2026-11-06_16.13.53`, `16.14.02`, `16.14.41`.

| Face | Blockbench (code `UVToLocal` de `cube.js`, et notre aperçu) | En jeu (captures) |
|---|---|---|
| `north` | gauche de l'image vers +X, haut vers +Y | **identique** (contrôle) |
| `up` | haut de l'image (v0) vers −Z, gauche (u0) vers **−X** ; coin (u0, v0) en (−X, −Z) | haut vers −Z, gauche vers **+X** ; coin rouge en (+X, −Z) |
| `down` | haut de l'image vers +Z, gauche vers **−X** ; coin (u0, v0) en (−X, +Z) | haut vers +Z, gauche vers **+X** ; coin rouge en (+X, +Z) (vu d'en dessous, l'image se lit à l'endroit) |

```
Face up vue de dessus (−Z en haut, +X à droite)
  Blockbench :  R . . B        En jeu :   B . . R
                . ↑N  .                   .  N↑ .
                O     E                   E     O
```

Les faces horizontales sont donc dessinées **en miroir sur X** (u inversé) par rapport à Blockbench ; les faces verticales sont justes. Les rotations de face (multiples de 90°) n'ont pas été testées.

### Ce qui est demandé
1. **Lire l'UV des faces `up` et `down` comme Blockbench** (u de −X vers +X sur les deux faces ; v de −Z vers +Z sur `up`, de +Z vers −Z sur `down`), y compris avec une rotation de face.
2. Dire dans le guide (section « Repères ») quand c'est corrigé : nous retournons aujourd'hui l'image de ces faces dans nos modèles (`tools/uv_horizontal.py`) ou n'y mettons que des motifs symétriques, et retirerons ce contournement ce jour-là.

## 6. Grands effets de zone : relever la limite de taille (2026-11-06)

### Constat
Aujourd'hui, le guide (« Zone autorisée », tableau des limites) impose à **tout** modèle, effets de téléportation compris, de garder ses cubes et pivots à **moins de 64 px de l'origine sur chaque axe**, soit 4 blocs. C'est la seule limite qui nous bloque pour les grands effets : nombre de cubes, poids et animations suffisent largement. Tu nous as dit que de grands effets de zone étaient prévus : voici tous les cas où une limite plus grande servirait, pour que tu puisses choisir la règle qui les couvre.

### Scénarios
**Effets de téléportation** (posés au sol, vus à 64 blocs) :
- une faille qui s'ouvre dans le ciel, d'où l'admin descend (notre `effet_admin`, demande du staff) ;
- une colonne de lumière qui monte jusqu'aux nuages, un éclair ou un météore qui tombe de très haut ;
- un cercle magique ou un sol gelé qui couvre toute une place (10 à 20 blocs de diamètre) ;
- un portail géant, une créature qui passe (dragon, baleine céleste) et emporte le joueur ;
- une onde de choc qui balaie le sol autour de l'arrivée.

**Cosmétiques portés** :
- des ailes immenses pour des pièces rares (déployées en `event_equip` ou à la fusée) ;
- une aura de « domaine » qui recouvre le sol autour du joueur ;
- une traînée d'arme longue à l'attaque (coup de lame qui fend l'air sur plusieurs blocs).

**Familiers vivants** : un grand familier (dragon, esprit) qui vole autour du joueur.

### Ce qui est demandé
1. **Une limite plus grande pour les effets de téléportation** : idéalement 320 px (20 blocs) sur chaque axe, au moins 160 px (10 blocs) en hauteur et sur les côtés.
2. **Si possible, une limite plus grande pour les cosmétiques portés et les familiers** aussi (par exemple 128 px), ou un réglage du staff par cosmétique, réservé aux pièces rares.
3. **Dire dans le guide** la limite de chaque catégorie, et si elle se mesure sur le modèle au repos ou aussi pendant les animations (`position`, `scale`).
4. **Visibilité** : que l'effet reste dessiné tant qu'une partie est à l'écran (boîte de visibilité à sa vraie taille), même quand son point d'origine est hors de l'écran ou derrière un mur.
5. **Performance** : si un très grand effet coûte cher, une option du joueur pour réduire ou couper les grands effets (comme « Effets de téléportation » dans les paramètres) nous convient.

Notre premier effet concerné (`effet_admin`) tient pour l'instant dans 4 blocs, avec toute sa taille réglée par une seule constante : nous l'agrandirons dès que la limite sera relevée.
