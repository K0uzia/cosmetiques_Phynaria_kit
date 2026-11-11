# Quatre bugs de rendu encore ouverts (au 4 novembre 2026)

Pour : le développeur de Phynaria Utilities (Minecraft 26.1.2, NeoForge).
De : l'équipe cosmétiques.

La mise à jour du guide du 4 novembre corrige `ctrl_alpha` et le crash du menu, merci. Les quatre problèmes
ci-dessous n'en font pas partie et se voient toujours en jeu. Ce document les reprend un par un, de façon
plus précise que notre premier rapport (`bug_rendu_avance_pour_dev.md`).

Pour chacun, un **modèle de test minimal** est fourni dans `docs/dev/tests_rendu/`. Il ne contient que la
chose à tester, avec une pièce témoin qui, elle, s'affiche bien. Chaque test prend moins d'une minute avec
`/cosmetique apercu <fichier>` (guide, section 12).

| # | Bug | Quand | Gravité | Modèle de test |
|---|---|---|---|---|
| 1 | Avec un shader, `add_`, `trans_` et le calque `_e` ne s'affichent pas | avec shader seulement | **bloquant** : une aura disparaît entièrement | `test1_shader.bbmodel` |
| 2 | Le reflet `_r` couvre tout le rectangle de la face, y compris les pixels transparents | toujours | gênant : rectangles clairs autour des pièces découpées | `test2_reflet_decoupe.bbmodel` |
| 3 | Dans le menu Apparence, `add_` est dessiné opaque et par-dessus le personnage | menu Apparence | gênant : l'aperçu ne ressemble pas au jeu | `test3_menu_additif.bbmodel` |
| 4 | Les particules `emit_mc_` naissent à plusieurs blocs du point et ne suivent pas le joueur | toujours | bloquant pour `emit_mc_` : inutilisable | `test4_particules_mc.bbmodel` |

## Résultats après votre correctif (tests passés le 4 novembre 2026, 16 h 26 – 16 h 33)

Les quatre tests ont été passés en jeu avec votre nouvelle version : le comportement du bug 4 a changé,
donc le correctif est bien installé. Captures recadrées dans `docs/dev/tests_rendu/captures/` (heure de
la capture d'origine dans chaque titre).

| # | Sans shader | Avec shader | Verdict |
|---|---|---|---|
| 1 | Les 4 plaques s'affichent : témoin gris, disque additif orange, bleu translucide, carré jaune lumineux | Le témoin (A) et le bleu translucide (C) s'affichent. **Le disque additif (B) a disparu. La plaque D s'affiche, mais son carré jaune `_e` est éteint** | ❌ **Toujours là** pour `add_` et `_e` (✅ `trans_` marche) — `test1_sans_avec_shader.jpg` |
| 2 | **Un carré gris clair semi-transparent entoure toujours le disque avec reflet** (le disque témoin n'en a pas) | Pas de carré, mais **aucun reflet** : les deux disques sont identiques | ❌ **Toujours là** sans shader ; avec shader, les reflets sont invisibles (même cause que le bug 1, supposé) — `test2_sans_avec_shader.jpg` |
| 3 | Dans le menu Apparence : le halo est dessiné en **couleur pleine dans un carré noir**, qui couvre le torse | (non concerné) | ❌ **Toujours là** : le noir de la texture additive reste noir dans le menu, et la couleur ne s'ajoute pas. Le menu semble montrer le dos du personnage (pas d'yeux visibles) : que le halo passe devant le torse est donc peut-être normal, mais pas le carré noir — `test3_menu.jpg` |
| 4 | En vol : une flamme naît **sur le petit cube au-dessus de la tête** ; les autres flammes et les `end_rod` restent autour du joueur, à un bloc environ, là où il était passé | (même chose) | ✅ **Corrigé, semble-t-il** : les particules partent près du point au lieu de plusieurs blocs. Elles restent ensuite dans le monde pendant que le joueur vole, ce qui est le comportement normal d'une particule de Minecraft — `test4_vol.jpg` |

**Ce qu'il reste donc à corriger : les bugs 1, 2 et 3.** Pour le bug 1, la ligne de journal « Iris:
cosmetic pipeline … drawn with the entities program » a-t-elle bien été écrite dans votre essai ? Si oui,
le programme indiqué ne suffit pas avec notre pack. Si non, l'appel à l'API d'Iris n'a pas eu lieu. Le
bug 2 se voit **sans** shader, donc il ne dépend pas d'Iris.

**Notre configuration** (captures du 3 et du 4 novembre) : profil `ftb-evolution-2`, Minecraft 26.1.2,
NeoForge, Iris. Pack de shaders : *à compléter par le joueur* (Complementary, BSL…).

---

## Bug 1 — Avec un shader, les parties additives, translucides et lumineuses disparaissent

### Ce qu'on voit
- **Sans shader**, tout s'affiche comme le guide l'annonce : l'aura `aura_brasier` (faite de groupes `add_`)
  est visible autour du joueur ; les lueurs `_e` des ailes et du haut-de-forme s'allument la nuit.
- **Avec un shader**, sur le même joueur, au même endroit :
  - les groupes **`add_`** ne s'affichent pas du tout : l'aura est portée (le chat le confirme) mais on ne
    voit rien ;
  - le calque **`_e`** ne s'affiche pas : aucune lueur, ni de jour ni de nuit ;
  - les groupes **`trans_`** ne s'affichent pas non plus (supposé : le jet de vapeur des ailes, à confirmer
    avec le test) ;
  - les parties **normales** (opaques, découpées) du même cosmétique s'affichent bien.

Captures : `2026-11-03_23.59.52` (avec shader, aura invisible), `2026-11-04_00.00.55` et `00.02.53` (sans
shader, aura visible), `2026-11-04_00.30.55` (avec shader, aucune lueur `_e` sur les ailes).

### Comment reproduire (1 minute)
1. Mettre `test1_shader.bbmodel` dans le dossier d'aperçu, puis `/cosmetique apercu test1_shader`.
2. Se mettre en vue à la troisième personne, de dos (F5 deux fois). Quatre plaques carrées sont alignées
   dans le dos, de gauche à droite :

   | Plaque | Groupe | Ce qu'elle doit montrer |
   |---|---|---|
   | A | aucun (opaque) | un carré gris : **témoin** |
   | B | `add_test` | une tache ronde rouge-orangé qui brille, sans bord noir |
   | C | `trans_test` | un carré bleu **à moitié transparent** : on voit le décor à travers |
   | D | aucun, calque `test1_shader_e.png` | un carré gris foncé avec un carré **jaune lumineux** au centre, visible même de nuit |

3. Sans shader : les quatre plaques s'affichent comme dans le tableau.
4. Activer un pack de shaders (Iris).

### Résultat attendu
Les quatre plaques restent visibles avec le shader, comme sans shader.

### Résultat constaté (sur nos cosmétiques, à confirmer avec ce test)
Seule la plaque A (témoin) reste visible. B, C et le carré jaune de D disparaissent.

### Pistes (supposées, non vérifiées)
- Les types de rendu utilisés pour `add_`, `trans_` et `_e` ne sont pas pris en charge par le pipeline
  d'Iris (pas de correspondance de programme), ou sont dessinés dans une passe que le shader ne compose pas.
- Repère utile : les rendus vanilla comparables restent visibles sous Iris : l'armure chargée du creeper
  (`energySwirl`, additif), les yeux d'araignée et d'enderman (`eyes`), le rayon de balise, les entités
  translucides (`entityTranslucent`). Utiliser ces types de rendu, ou les mêmes réglages, devrait suffire.
- La profondeur non écrite (normal pour l'additif) peut faire écarter la géométrie par certains packs : à
  tester avec et sans écriture de profondeur.

### Comment vérifier la correction
Le test 1 avec deux packs de shaders courants (par exemple Complementary et BSL) : les quatre plaques
visibles, la plaque D lumineuse de nuit.

---

## Bug 2 — Le reflet `_r` couvre toute la face, même là où la texture est transparente

### Ce qu'on voit
Nos ailes sont faites de plaques dont la **forme vient de la texture** : une lame est un rectangle, et les
pixels autour de la lame sont transparents (alpha 0), comme le guide le recommande. Avec un masque `_r`,
chaque lame est entourée d'un **rectangle clair semi-transparent** : le reflet est dessiné sur tout le
rectangle de la face, y compris les zones transparentes où il n'y a rien.

Captures : `2026-11-04_00.00.55`, `00.02.53` (ailes mécaniques, rectangles clairs autour de chaque lame).
Nous avons retiré tous les masques `_r` en attendant.

### Bien distinguer : ce n'est pas la moyenne par face
Le guide dit que le masque `_r` est lu **face par face** (moyenne sur la face). Nous l'avons compris et ce
n'est pas le problème : qu'une face entière brille de façon uniforme nous convient. Le problème est que le
reflet **déborde de la découpe** : il apparaît sur des pixels où la texture principale est transparente, et
qui ne devraient donc rien afficher du tout.

### Comment reproduire (1 minute)
1. `/cosmetique apercu test2_reflet_decoupe`, de dos.
2. Deux disques dorés sont dans le dos. Chacun est une plaque carrée de 8 px dont la texture est un disque
   opaque sur un fond transparent :
   - à gauche : `disque_reflet`, masque `_r` blanc (miroir) sur toute sa case ;
   - à droite : `disque_temoin`, même disque, sans reflet.
3. Tourner autour du joueur pour faire glisser le reflet.

### Résultat attendu
Le disque de gauche brille ; le reflet s'arrête au bord du disque. Autour du disque, rien : on voit le décor,
exactement comme autour du disque témoin.

### Résultat constaté (sur nos cosmétiques, à confirmer avec ce test)
Un carré clair de 8 px apparaît autour du disque de gauche : le reflet est dessiné sur tout le carré.

### Piste (supposée)
La passe de reflet n'applique pas le test d'alpha (cutout) de la texture principale. Il faudrait la même
découpe que la passe normale : ne rien dessiner là où l'alpha de la texture principale vaut 0. Le calque `_e`
a peut-être le même défaut, mais on ne le voit pas, puisque nos `_e` sont noirs hors de la découpe.

### Comment vérifier la correction
Le test 2 : aucun carré clair autour du disque de gauche, sous aucun angle.

---

## Bug 3 — Menu Apparence : l'additif est dessiné opaque et par-dessus le personnage

### Ce qu'on voit
Dans l'aperçu du menu Apparence, l'aura `aura_brasier` (groupes `add_` dans des groupes `cam_`, placés
**derrière** chaque partie du corps) donne :
- d'abord des **carrés noirs** (le noir d'une texture additive, censé être invisible, était dessiné tel
  quel) ; nous avons rendu ces pixels transparents pour contourner le problème ;
- ensuite, encore aujourd'hui, des **disques rouge plein** dessinés **par-dessus** le personnage, alors
  qu'ils sont derrière lui.

En jeu, sans shader, la même aura s'affiche correctement (halo lumineux autour de la silhouette, corps
devant). Le menu ne ressemble donc pas à ce que les joueurs verront.

Captures : `2026-11-03_23.58.59` (carrés noirs), `2026-11-04_00.30.55` (disques par-dessus le personnage).

### Comment reproduire (1 minute)
1. `/cosmetique apercu test3_menu_additif` (le guide indique que l'aperçu apparaît aussi dans le menu).
2. **En jeu**, de face : un halo rouge-orangé dépasse autour du torse, le torse est devant et le cache au
   centre, aucun noir.
3. Ouvrir le **menu Apparence** et regarder le personnage.

### Résultat attendu
Dans le menu, le même halo qu'en jeu : additif (le noir ne se voit pas, la couleur éclaircit), **derrière**
le personnage (le corps le cache au centre).

### Résultat constaté (sur `aura_brasier`, à confirmer avec ce test)
Le disque est dessiné en couleur pleine, sans additif, et par-dessus le personnage : il cache le torse.

### Pistes (supposées)
- Le rendu du menu n'utilise pas le type de rendu additif du jeu pour les groupes `add_`.
- Les faces sont dessinées sans test de profondeur contre le personnage, ou après lui.
- Le guide dit que les `cam_` ne sont pas tournés dans le menu, faute de caméra. Ça nous va, si l'additif et
  la profondeur sont respectés. À défaut, une requête Molang `query.is_in_menu` nous permettrait de cacher
  ce que le menu ne sait pas montrer.

### Comment vérifier la correction
Le test 3 dans le menu : halo derrière le personnage, sans noir ni disque plein devant le torse.

---

## Bug 4 — Particules `emit_mc_` : loin du point de départ, et immobiles

### Ce qu'on voit
Sur le familier hibou, trois points `emit_mc_white_ash` sont placés juste sous son hélice, à environ un
demi-bloc du joueur. En jeu, les particules apparaissent **à plusieurs blocs** de là, sur le côté, et **ne
suivent pas** le hibou ni le joueur quand il se déplace. Même constat pour la vapeur des ailes.

Capture : `2026-11-04_00.31.13`. Nous avons remplacé toutes nos `emit_mc_` par des particules modélisées
(`particle_<nom>`), qui partent bien du bon point.

### Comment reproduire (1 minute)
1. `/cosmetique apercu test4_particules_mc`. Il contient deux points, chacun marqué par un **petit cube gris** :

   | Point | Où | Mouvement |
   |---|---|---|
   | `emit_mc_flame` | 2 px au-dessus du milieu de la tête, dans `head` (pivot 0 ; 34 ; 0 en pixels) | aucun : il suit seulement la tête |
   | `emit_mc_end_rod` | dans un groupe `orbite` de `body`, à 10 px du centre, à hauteur de taille (pivot 10 ; 16 ; 0) | `orbite` fait un tour complet en 4 s (animation `idle`) |

2. Laisser les réglages par défaut (*Quand* = En vol). Passer en vol créatif, puis avancer, tourner et
   regarder en l'air et en bas.

### Résultat attendu
- Les flammes naissent **sur le petit cube au-dessus de la tête**, et le suivent quand le joueur avance,
  tourne la tête ou se penche.
- Les particules `end_rod` naissent **sur le petit cube qui tourne** : elles dessinent un cercle autour du
  joueur, qui le suit quand il avance.

### Résultat constaté (sur le hibou, à confirmer avec ce test)
Les particules naissent à plusieurs blocs du cube, toujours du même côté, et restent sur place quand le
joueur bouge.

### Pistes (supposées)
- **Unités** : le pivot est en pixels du modèle (16 px = 1 bloc). S'il est lu en blocs, un point à
  0,5 bloc se retrouve à 8 blocs : c'est l'ordre de grandeur de l'écart constaté.
- **Transformation** : la position doit passer par toute la chaîne des groupes parents (pose et animation à
  l'instant de l'émission), puis par le repère du joueur (position dans le monde, rotation du corps), à
  chaque particule. Les particules modélisées (`emit_<nom>`) le font bien : les `emit_mc_` pourraient
  reprendre exactement le même calcul.
- **Instant** : la position semble calculée une seule fois (au chargement, ou à l'origine de l'entité) au
  lieu de l'être à chaque émission.

### Comment vérifier la correction
Le test 4 : les flammes partent du cube de la tête et le suivent, et les `end_rod` tracent un cercle autour
du joueur, même quand il avance.

---

## Ce qui marche (pour situer le problème)

Constaté en jeu, sans shader :
- `add_`, `cam_` et `camy_` : l'aura s'affiche comme prévu (halo, colonnes, anneau au sol) ;
- le calque `_e` : les lueurs sont visibles la nuit, sans clignotement ;
- `ctrl_teinte` piloté par `query.is_in_rain` : le métal s'assombrit sous la pluie ;
- les particules modélisées (`particle_<nom>` + `emit_<nom>`) partent du bon point et suivent le joueur.

## Fichiers fournis

- `docs/dev/tests_rendu/test1_shader.bbmodel` (+ calque `_e` embarqué)
- `docs/dev/tests_rendu/test2_reflet_decoupe.bbmodel` (+ masque `_r` embarqué)
- `docs/dev/tests_rendu/test3_menu_additif.bbmodel`
- `docs/dev/tests_rendu/test4_particules_mc.bbmodel`
- `docs/dev/tests_rendu/gen_tests_rendu.py` : le script qui les écrit, si vous voulez changer une valeur.

Les quatre passent nos contrôles d'import (limites du guide). Nous pouvons faire d'autres tests si un
résultat ne correspond pas à ce qui est décrit ici.
