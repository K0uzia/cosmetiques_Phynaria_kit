# Demandes au mod (3) — bras fins, gravité, armure, sons personnalisés

Tu travailles sur le mod Phynaria Utilities. Ce document ne contient que les **nouvelles demandes** du 2026-11-04, nées de l'ensemble Cuir et des essais en jeu. Tout ce qui figurait dans `demandes_mod_2.md` a été fait ou est suivi dans `bugs_rendu_detail.md` ; il n'est pas repris ici, sauf le point 5, toujours en défaut après le correctif du 2026-11-04.

> **État (2026-11-05)** : toutes les demandes ci-dessous ont été acceptées et faites par le développeur (message de l'utilisateur). Syntaxe exacte à lire dans le guide mis à jour dès qu'il est dans `docs/` ; d'ici là, ne pas deviner les noms.

## Résumé

| # | Demande | Ce que ça débloque | Priorité |
|---|---|---|---|
| 1 | `query.is_slim_arms` (bras fins) | Bracelets et manchettes qui collent au bras sur un skin Alex | Moyenne |
| 2 | Gravité pour `phys_` (ou angles des membres) | Chaînes, laisses, pendentifs qui pendent vers le sol | Haute |
| 3 | Requêtes d'armure ou option « Par-dessus l'armure » | Harnais et pièces de torse visibles avec un plastron | Moyenne |
| 4 | Sons personnalisés | Bruitages propres au cosmétique (claquement de fouet, carillon divin…) | Moyenne |
| 5 | **Vérifier les auras avec un pack de shaders** (`add_`, `_e`) | Toutes les auras et lueurs : aujourd'hui elles disparaissent avec shader | **Haute** |

---

## 1. Bras fins (modèle Alex) — 2026-11-04

**Besoin.** Un bracelet, une manchette ou une menotte est fait pour un bras de 4 px. Sur un skin à bras fins (3 px), il flotte autour du bras avec 1 px de vide (constaté en jeu sur `harnais_cuir`, captures `2026-11-04_16.52.37` et `16.52.43`).

**Proposition.** Une requête Molang **`query.is_slim_arms`** (1 si le skin du joueur a des bras fins, 0 sinon), pour réduire ou décaler les pièces des bras par l'animation (`scale` x = `1 - 0.25 * query.is_slim_arms`, `position`). Encore mieux : que le mod ajuste lui-même les groupes `right_arm` / `left_arm` (même décalage que le bras du joueur), comme pour l'armure.

## 2. Chaînes, laisses, pendentifs : une vraie gravité (2026-11-04)

**Constat en jeu** (`harnais_cuir`, chaînes qui pendent des bracelets). Une chaîne portée par le bras suit l'orientation du bras : quand on s'accroupit ou qu'on balance le bras, elle reste dans l'axe du bras, comme une tige raide, alors qu'une vraie chaîne pend vers le bas. Le modèle ne peut pas compenser : il ne connaît ni l'angle des bras, ni la phase du pas. `phys_` est un ressort autour de la pose animée, il ne tire pas vers le sol.

**La physique attendue (pendule amorti).** Chaque maillon est un pendule accroché au bout du précédent.
- **Gravité** : le maillon est tiré vers le **bas du monde** (pas vers le bas du bras). Couple de rappel ∝ (g / L) · sin(θ − θ_bas), avec θ l'angle du maillon dans le monde.
- **Inertie** : quand le point d'accroche accélère (bras qui balance, joueur qui démarre, s'arrête ou tourne), le maillon est entraîné en sens inverse de l'accélération. C'est ce qui le fait balancer avec du retard.
- **Amortissement** : il revient au repos en quelques oscillations. Période propre T ≈ 2π · √(L / g), soit environ 0,5 à 0,8 s pour une chaîne de 6 à 12 px.
- **Chaîne de maillons** : chaque maillon suit le précédent, le retard augmente vers le bout, et le dernier balance le plus.
- **Limites** : un angle maximum par articulation (ex. 60°) évite les tours complets. Une collision simple avec le corps, ou au moins un plan devant et derrière le torse, évite qu'elle traverse le joueur.

**Proposition, au choix :**
1. Une option de **gravité** pour `phys_`, avec un suffixe `_g<0-100>` (0 = ressort actuel, 100 = pendule pur vers le bas du monde), par exemple `phys_chaine_g100_a40`. Des groupes imbriqués forment une chaîne.
2. À défaut, des requêtes Molang pour compenser nous-mêmes :
   - `query.body_x_rotation` (penché en sneak) ;
   - `query.right_arm_x_rotation` et `query.left_arm_x_rotation`, `..._z_rotation` (angles réels des bras, avec le balancement du pas) ;
   - ou au moins `query.limb_swing` et `query.limb_swing_amount` (phase et ampleur du pas).

   Avec ça, une contre-rotation garde la chaîne verticale, mais sans inertie vraie.

**Critère.** Une chaîne de 5 maillons sous un bracelet reste verticale quand on s'accroupit, balance avec un peu de retard quand on marche, et oscille puis se calme à l'arrêt.

## 3. Cosmétiques et armure (2026-11-04)

**Constat en jeu** (captures `2026-11-04_17.02.23`, `.27` et `.32`). Avec un plastron en diamant, les sangles de `harnais_cuir`, posées à 0,4 px du torse, sont **cachées sous l'armure**, qui est gonflée d'environ 1 px. Seuls l'anneau central, la boucle et les bracelets dépassent, ce qui donne des pièces qui flottent sur l'armure. Poser les sangles à plus de 1 px du corps les ferait flotter quand le joueur ne porte pas d'armure.

**Proposition, au choix :**
1. Des requêtes Molang `query.has_helmet`, `query.has_chestplate`, `query.has_leggings` et `query.has_boots` (1 si la pièce est portée et visible, 0 sinon), pour écarter le cosmétique de l'armure par `position` ou `scale`, ou le cacher par `ctrl_alpha`.
2. Ou une option du staff par cosmétique, **« Par-dessus l'armure »** : le mod écarte lui-même les groupes `body`, `right_arm`, `left_arm`, `head`, etc. de l'épaisseur de l'armure portée à cet endroit.
3. Ou une option **« Cacher l'armure »** par cosmétique (comme les capes ou les mods de cosmétiques qui masquent le plastron).

## 4. Sons personnalisés (2026-11-04)

**Constat.** Le guide (6.5) n'accepte que les noms de sons de Minecraft. Pour certaines pièces, aucun son du jeu ne convient : un fouet n'a pas de claquement, une aura divine n'a qu'un carillon d'améthyste. On combine des sons du jeu, mais le rendu reste approximatif.

**Proposition, au choix (la première est la plus simple pour toi) :**
1. **Sons d'un pack de ressources du serveur.** Accepter dans la piste *Effets* les noms d'un autre espace de noms que `minecraft:`, par exemple `phynaria:fouet_claque`, déclarés dans le `sounds.json` d'un pack de ressources imposé par le serveur. Le mod n'a qu'à ne plus rejeter ces noms (et à les signaler dans le rapport seulement s'ils sont absents du pack chargé). Les sons restent hors du `.bbmodel`, téléchargés une fois avec le pack.
2. **Sons embarqués dans le `.bbmodel`**, comme les textures : fichiers OGG en base64 dans un champ du modèle (Blockbench garde le champ `file` des clés de son), extraits par le mod et envoyés aux joueurs avec le cosmétique. Limites proposées : 8 sons au plus, 100 Ko chacun, mono, 5 s au plus, comptés dans les 1 000 Ko compressés.

Dans les deux cas, garder ce qui existe : volume du staff (0 à 100 %), coupure par chaque joueur, 32 sons par animation, et le repli silencieux si un son manque.

**Critère.** Une clé de son `phynaria:fouet_claque` (ou un OGG embarqué) est entendue par les joueurs proches au moment de l'attaque, au volume réglé par le staff.

## 5. Auras et shaders : à vérifier de ton côté (2026-11-04, priorité haute)

**Constat en jeu, après le correctif Iris annoncé dans le guide (« Nouveautés et corrections », bug 1).** Nous suivons le guide à la lettre : groupes `add_` (section 4 bis), `cam_` / `camy_`, `trans_`, calque `_e`. **Sans shader, l'aura s'affiche bien. Avec shader, il n'y a aucune différence avant/après le correctif : tout ce qui est `add_` et `_e` reste invisible**, il ne reste que les parties `trans_`, très pâles.

- Pack : **Complementary Unbound r5.9.3 + Euphoria Patches 1.10.5** (Iris).
- Modèles : `aura_berenice.bbmodel` (joint ; halo de disques `add_` en `cam_`, gloire de rayons `add_` doublée en `trans_`, anneau au sol), `aura_brasier.bbmodel`, et le test minimal `tests_rendu/test1_shader.bbmodel` (`bugs_rendu_detail.md`, test 1).
- Captures (même endroit, même pose, à quelques secondes d'écart) :
  - sans shader : `2026-11-04_21.49.32`, `21.37.13`, `21.37.33` — halo doré, rayons, anneau visibles ;
  - avec shader : `2026-11-04_21.49.41`, `21.49.56`, `21.37.22`, `21.37.31` — seuls les rayons et l'anneau `trans_` se devinent, le halo `add_` et le calque `_e` ont disparu.

**Configuration (d'après `latest.log`, session du 2026-11-04, 15 h 52 → 21 h 59).**

| | |
|---|---|
| Mod | **Phynaria Utilities 1.4.0** (`mods/phynariautilities-26.1.2-1.4.0.jar`) — merci de confirmer que c'est bien la version qui contient le correctif Iris |
| Jeu | Minecraft 26.1.2, NeoForge (FancyModLoader 11.0.15), LWJGL 3.4.1 |
| Rendu | **Iris 1.11.4+mc26.1.2**, **Sodium 0.9.2+mc26.1.2**, ImmediatelyFast 1.15.3 (compatibilité Iris activée) |
| Pack de shaders | ComplementaryUnbound_r5.9.3 + EuphoriaPatches_1.10.5 |
| Matériel | NVIDIA GeForce RTX 3070 Ti, pilote 617.14 (OpenGL 3.3.0), i9-12900KF, Windows 11. Sodium applique le contournement `NVIDIA_THREADED_OPTIMIZATIONS_BROKEN` |

**Ce que montre le journal, ligne par ligne.**

1. **Au chargement des mods, Iris liste les programmes des autres mods, mais jamais celui de Phynaria.** Les autres mods qui ont leur propre rendu y sont associés à un programme du pack de shaders :
   ```
   [15:52:55.218] [Iris/] WARN: Found fine program match for shatterlib:trail: ENTITIES_TRANSLUCENT
   [15:53:25.989] [Iris/] WARN: Found *decent* program match for geckolib:pipeline/emissive: SPS
   [15:53:25.989] [Iris/] WARN: Found *decent* program match for geckolib:pipeline/emissive: SHADOW_ENTITIES_CUTOUT
   ```
   Il y a 22 lignes « program match » dans la session, et **aucune** pour `phynariautilities:…`.
2. **Le mod n'écrit rien sur Iris.** Aucune ligne de Phynaria Utilities ne parle d'Iris, de pipeline ou de programme. La ligne « Iris: cosmetic pipeline … drawn with the entities program » annoncée par le guide n'apparaît **jamais**, ni au démarrage ni aux changements de shader.
3. **Premier chargement du pack, puis erreur trois secondes plus tard** :
   ```
   [15:54:29.221] [Iris/] INFO: Using shaderpack: ComplementaryUnbound_r5.9.3 + EuphoriaPatches_1.10.5
   [15:54:32.644] [Iris/] ERROR: Missing program phynariautilities:pipeline/cosmetic_additive in override list. This is not a critical problem, but it could lead to weird rendering.
   ```
   Iris n'écrit cette erreur qu'une fois par programme. Elle ne revient donc pas aux 21 activations du pack qui suivent (16 h 06 → 21 h 59), mais l'aura reste invisible à chacun d'eux.
4. **Aucun autre programme de Phynaria n'est cité.** Le calque `_e` et les reflets passent donc sans doute par ce même `cosmetic_additive`, ou par un programme qu'Iris remplace sans erreur mais ne dessine pas. À confirmer de ton côté.
5. Les erreurs `[Iris/FATAL] Missing program minecraft:pipeline/lines_translucent`, `outline_no_cull` et `entity_outline/0-3` concernent Minecraft lui-même, pas le mod.

**Notre lecture.** L'association du programme `cosmetic_additive` à un programme d'Iris (`assignPipeline` de l'API d'Iris, ou l'équivalent que tu utilises) ne se fait pas. Trois causes possibles :
- l'appel n'est pas exécuté dans la 1.4.0 ;
- il est fait trop tard, ou sur une autre instance du pipeline que celle qui dessine ;
- il porte un autre nom que `phynariautilities:pipeline/cosmetic_additive`.

Il faudrait au moins une ligne de journal du mod qui confirme l'appel et son résultat. Avec cet appel en place, le journal devrait afficher une ligne comme celles de geckolib, ou plus d'erreur du tout. Le journal complet est disponible si tu en as besoin.

**Ce qu'on te demande :**
1. **Refaire le test toi-même avec un pack de shaders** (Complementary ou BSL), sur `test1_shader.bbmodel` et `aura_berenice.bbmodel`, et nous dire ce que tu vois. Le guide précise lui-même que le correctif n'a « pas encore été vérifié avec un pack de shaders ».
2. Vérifier l'enregistrement auprès d'Iris (voir ci-dessus) et ajouter une ligne de journal qui le confirme.
3. **Si une aura `add_` s'affiche chez toi avec shader**, envoie-nous ce modèle : c'est alors notre fichier qui est en cause, et nous le corrigerons. **Si elle ne s'affiche pas**, le bug est côté mod et rien ne peut le compenser dans le modèle.
4. En attendant, une requête Molang **`query.has_shader_pack`** (1 si un pack de shaders est actif chez celui qui regarde) nous permettrait de renforcer la version `trans_` seulement avec shader, au lieu de la garder pâle pour ne pas doubler la lueur sans shader.

**Critère.** Avec Complementary, le halo `add_` de `aura_berenice` et le carré lumineux de `test1_shader` sont visibles, comme sans shader (l'intensité peut varier selon le pack).
