# Familiers — ce qui les rend vivants

Retour de l'utilisateur (2026-11-04, `familier_givre`) : « il est juste passif, il fait rien. C'est un familier, donc un petit être vivant ami avec le joueur : il faut de l'interaction avec ce qui l'entoure et le joueur, pas forcément en continu, mais de façon aléatoire. » S'applique à tout familier, quel que soit l'ensemble.

## Principes (sources en bas)

1. **Boucle de base vivante** : respiration, flottement, petits déplacements du poids, et surtout un **regard qui bouge** (petites saccades de la tête, oreilles qui pivotent indépendamment). Clignements irréguliers.
2. **Comportements ponctuels tirés au hasard** qui interrompent la base : 6 à 10, pondérés, à écarts irréguliers (jamais à intervalle fixe), un seul à la fois, avec des pauses calmes entre deux. Deux joueurs ne doivent pas être synchronisés (`q.instance_seed`).
3. **Lien avec le joueur** : il le regarde, regarde là où il regarde (`q.head_x_rotation`, `q.head_y_rotation`, avec retard), saute avec lui (`event_jump`), rebondit à l'atterrissage (`event_land`, `q.land_speed`), se penche dans les virages (`q.yaw_speed`), s'inquiète quand la vie est basse (`q.health / q.max_health`), sursaute puis le regarde quand il est blessé (`q.hurt_time`), se réjouit après une attaque.
4. **Lien avec le monde** : pluie (`q.is_in_rain` : oreilles plaquées, s'ébroue), nuit (`q.time_of_day` : bâille, se blottit, yeux mi-clos), eau, vitesse.
5. **Logique physique** (`.claude/rules/essentiel.md`) : chaque mouvement a une cause (il lévite par magie, un rotor porte, des ailes battent pour de vrai).
6. **Visage expressif** : yeux avec reflet blanc et paupières (cligner, plisser), sourcils ou taches, oreilles en volume. Le visage est ce que le joueur regarde : c'est là que va le détail.
7. **Proportions documentées** : chercher l'anatomie réelle de l'animal avant de modéliser (renard polaire : corps compact, pattes courtes, museau court et effilé, oreilles plus petites et arrondies que le renard roux, queue très touffue).
8. **Un animal, pas un assemblage** (retour du 2026-11-05 sur `familier_givre` v2 : « grands carrés », « assemblage de formes ») : silhouette d'abord ; masses qui s'emboîtent de 30 à 50 % ; sections arrondies par paliers alignés (pas de jumeau tourné à 45°) ; peinture en espace monde (zones de pelage, dégradé dos clair / ventre sombre, occlusion aux contacts, mèches dans le sens du poil) qui efface les jointures ; quelques mèches en volume **couchées** sur la surface, jamais de plaques en pointe ; visage construit (arcades, paupières, sourcils animables, truffe, bouche, mâchoire) ; pattes en trois segments avec le zigzag arrière. Méthode, chiffres et budget : `.claude/references/familiers/modelisation-organique.md`.

## Placement et locomotion

Où se tient le familier et comment il bouge dépend de **son type** (« un familier ne vole pas forcément », 2026-11-05), qui donne son `mode` (règle ci-dessous) : un animal réel marche au sol à côté du joueur, un oiseau ou un mini-dragon se perche sur l'épaule, un esprit ou une mascotte magique flotte, un animal minuscule se porte (épaule, capuche, sac). Un animal-esprit (renard de givre, kitsune) marche au sol tant que le joueur est au sol et ne s'élève que quand le joueur le quitte, avec une cause visible. Catalogue des types, placements possibles dans le mod, arbre de décision et tableau des états : `.claude/references/familiers/types-familiers.md`. Ce qui marche et ce qui lasse dans les jeux : `.claude/references/familiers/familiers-cosmetiques-jeux.md`.

### Règle : familier vivant (mode du guide, section 6.6, depuis le 2026-11-05)

Tout nouveau familier, et tout familier refait, est un **familier vivant** : il quitte le joueur et le suit comme un loup apprivoisé (vrai sol, marches, téléportation à 20 blocs ou coincé 3 s).
- **Déclaration** dans le générateur : `fiche.bloc(model)["familier"] = {"mode": …, "distance": …, "vitesse": …, "hauteur": …}` (`tools/fiche.py` ; `livrer.py` garde ce bloc en y ajoutant fiche et réglages). Modes : `sol` (animal réel : renard, chat), `vol` (vole près de l'épaule : esprit, mochi, crâne), `nage`, `perche` (se pose sur l'épaule gauche, s'envole quand le joueur court, saute, vole ou nage : hibou, petit dragon). `distance` 1,5/2/3/4/5/6/8 blocs (3 par défaut), `vitesse` 0,5/0,75/1/1,25/1,5/2, `hauteur` 0,5 à 3 blocs (`vol` et `perche`, 1,8 par défaut).
- **Modèle** : pattes à l'origine (0, 0, 0), tête vers −Z, échelle du joueur ; **aucun groupe du corps** (`head`, `body`…) à la racine (le vérificateur échoue sinon) ; ses propres groupes, pivot à la jointure. Perché : origine posée sur l'épaule gauche (1,42 bloc du sol, 1,15 accroupi), modéliser l'animal assis, pattes à l'origine.
- **Animations** : `pet_idle`, `pet_walk`, `pet_run`, `pet_sit`, `pet_sleep`, `pet_swim`, `pet_fly`, `pet_fall`, `pet_jump`, `pet_land` (tableau et replis : `.claude/rules/categories/familiers.md`, Familier vivant), `overlay_` pour la vie de fond (regard, clignements, tirages au hasard), événements `event_teleport`, `event_perch`, `event_owner_hurt`, `event_jump`, `event_land`, `event_enter_sit`… Plus de contre-rotation du torse, plus de saut vers l'épaule par `event_enter_fly` : le mod gère la place, l'animation gère l'allure.
- **Lien avec le joueur** par `q.owner_distance` (queue qui remue quand il approche), `q.owner_is_sneaking`, `q.owner_is_sprinting`, `q.owner_is_sleeping`, `q.owner_health / q.owner_max_health` (inquiet quand la vie est basse), `q.owner_ground_speed`, `event_owner_hurt` (sursaute, regarde le joueur). `q.is_sitting`, `q.is_perched`, `q.is_pet` pour adapter une expression commune. Les requêtes de la section 6.3 (`q.ground_speed`, `q.is_in_rain`, `q.time_of_day`…) parlent du familier.
- **Pas encore dans le mod** pour un familier vivant : particules `emit_` (non lancées), `phys_` (sans ressort), ombre avec shader. Ne pas compter dessus : mouvement des oreilles et de la queue animé à la main.
- **Aperçu** : le renderer et le Vestiaire le montrent **porté**, à l'origine du modèle, c'est-à-dire entre les pieds du joueur pour `sol`/`vol`/`nage` (à décaler mentalement de `distance` blocs) et sur l'origine pour `perche` (en jeu : sur l'épaule). Le joueur affiché ne sert que d'échelle ; les états du joueur (`ANIM=pet_walk`, etc.) se rendent par leur nom. Le menu Apparence du jeu le montre aussi porté (animation jouée alors non précisée par le guide : mettre `pet_idle` en premier dans la liste des animations, supposé). Le comportement de suivi se juge **seulement en jeu** : `/cosmetique apercu` (le familier y est vivant).
- **Un seul familier vivant par joueur** (le premier porté) ; un second est porté sur le joueur comme avant : garder une pose portée lisible n'est pas exigé.

### Repli : familier porté qui marche au sol (avant le 2026-11-05, pièces déjà livrées)

Sans bloc `familier` (ou `"mode": "aucun"`), le familier est dans `body` et suit le torse : c'est l'animation qui le pose au sol. Recette gardée pour les familiers livrés avant le mode du guide, et pour un cas où le mode vivant ne convient pas. Tout ce qui suit se règle au rendu `MODCONV=1` (plan du sol visible) et **se vérifie en jeu** : la pose du joueur du renderer (`pose_joueur`) est une approximation du vanilla.

**Hiérarchie** : `body` > `fam_sol` (contre-rotation, pivot au pivot du torse (0, 24, 0)) > `fam_saut` (événements : épaule, bras, dos) > `fam_pos` > `fam_rot` > corps de l'animal. Pieds à **y = 0**, à **x ≈ −8 à −12** (côté gauche, comme le perroquet ; ±8 au moins pour sortir du balancement du bras), z de 0 à +2 (un peu en arrière, hors du champ de la caméra en première personne vers l'avant).

**Allure en `walk` et `run`** (synchronisée sur `q.ground_speed`, en blocs/s) :
- Vitesses du joueur : marche 4,317, course 5,612, accroupi 1,295 blocs/s, soit 69, 90 et 21 px/s de sol qui défile.
- Un renard de quelques kilos change du trot au galop vers 2 m/s, à une fréquence de foulée d'environ 3,5 Hz (loi de Heglund et Taylor, f ≈ 4,48 · M^−0,14 Hz au changement d'allure) : à la vitesse de marche du joueur, un vrai renard **galope déjà**. Allure retenue : `walk` en petit galop bondissant à 3,5 Hz, `run` en galop allongé à 4 Hz, `sneak` en marche de chasse à 2 Hz.
- Le sol avance de 16·v/f px par foulée (environ 20 px en marche) : une patte de 3 px ne peut pas le couvrir en restant au sol. D'où le **bond** : appui court (15 à 20 % du cycle), corps qui monte de 0,6 à 1,2 px pendant la suspension, pattes balancées de ±35 à 45°, paire avant puis paire arrière. Pendant l'appui, le pied recule toujours (jamais vers l'avant : c'est ce qui ferait « patiner »). Le glissement restant est inévitable sans ancrage au monde : le rythme et la suspension le masquent.
- Durée de boucle = nombre entier de foulées (walk : 3 foulées à 3,5 Hz = 0,857 s). Amplitude × `math.clamp(q.ground_speed / 4.3, 0.3, 1.3)` pour les marches lentes (eau, dalles, toiles). Pour une fréquence qui suit vraiment la vitesse, une phase accumulée `v.ph = v.ph + q.delta_time * 360 * f;` (variable mémorisée : non simulée par le renderer, à juger en jeu).
- Virages : le torse tourne et emporte le familier autour du joueur ; l'incliner dans le virage (`q.yaw_speed`, roulis de ±10°) et ajouter un petit pas de côté.

**Contre-rotation du torse** (comme les chaînes, `retours-en-jeu.md`) :
- `sneak` : le torse s'incline de 28,6° vers l'avant autour de (0, 24, 0) et descend de 3,2 px (approximation du renderer) ; sans correction, les pieds reculent de plus de 11 px et quittent le sol. `fam_sol` reçoit la rotation opposée et la remontée, à ajuster jusqu'à ce que les pieds restent sur le plan du sol. Posture : chasse (avant bas, oreilles en avant, queue tendue), marche de chasse à 2 Hz.
- `swim` : le joueur est couché. Soit il nage à côté (contre-rotation de 90°, tête hors de l'eau, pédalage des pattes avant), soit il monte sur le dos du joueur (plus simple : couché sur la face +Z du torse, qui regarde le ciel, sans contre-rotation).
- `sleep` : le joueur est sur le dos. Le familier se roule en boule **sur sa poitrine ou ses jambes** (face −Z du torse, qui regarde le ciel), sans contre-rotation, respiration lente de 3 à 4 s.

**En l'air, une logique plausible** :
- `fly` (vol créatif) : il saute **dans les bras** (devant la poitrine) ou **sur l'épaule** (x ≈ −6, y ≈ 24). Le saut est dans `event_enter_fly`, le retour au sol dans `event_exit_fly`. Les événements **s'ajoutent** à l'état (guide 6.4) : `event_enter_fly` part du décalage (position au sol − position sur l'épaule) et revient à 0 en 0,4 à 0,6 s, pendant que `fly` le tient déjà sur l'épaule ; `event_exit_fly` part de (épaule − sol) et revient à 0 pendant que `idle` le remet au sol. Le changement d'état attend 0,12 s puis se fond en 0,2 s : caler l'arc du saut sur ces délais et vérifier en jeu.
- `glide` (élytres) : accroché au dos (face +Z du torse, pattes cramponnées, oreilles couchées, queue qui flotte vers les pieds), sans contre-rotation ; saut vers le dos dans `event_enter_glide`.
- `fall` et saut : le familier monte avec le joueur (il est attaché au torse), donc il « saute » déjà. `event_jump` ajoute l'impulsion (pattes arrière qui poussent, corps étiré) ; `fall` tient la pose de bond (avant tendues vers le sol, arrière repliées, queue en balancier) ; `event_land` amortit (pattes fléchies, oreilles qui rebondissent, amplitude selon `q.land_speed`). Chute longue (`q.vertical_speed` < −10 environ) : il glisse vers l'épaule et s'y cramponne, par un lissage, jamais d'un saut instantané.
- `mount` : les pieds du joueur sont sur la monture, le sol est inconnu : sur l'épaule, ou assis devant lui.

**Budget** : `event_enter_fly`, `event_exit_fly` et `event_enter_glide` comptent dans les 16 animations : retirer `mount` (repli sur `idle`, ou animation commune avec `fly`) et regrouper si nécessaire, puis le dire dans la livraison.

## Recette Molang (hasard sans variable, calculable par le renderer)

```
k = math.mod(math.floor(q.life_time / 6 + q.instance_seed * 17) * 7.31, 1)   // tirage par tranche de 6 s
```
Chaque comportement = une enveloppe (bump) dans sa tranche quand `k` tombe dans sa plage de probabilité ; la plupart des tranches restent calmes. Les variables `v.` servent aux lissages (non simulées par le renderer : juger en jeu). 512 caractères et 16 instructions par clé.

## Langage du corps (renard, transposable)

Jeu : queue en U renversé, oreilles couchées sur les côtés, « play bow » bref (avant baissé, arrière haut, 1–2 s). Bond « mousing » sur une proie imaginaire (saut en arc, pattes avant d'abord). Détendu : queue qui pend souplement. Inquiet : oreilles plaquées, queue basse. Curieux : oreilles dressées vers le son, tête inclinée.

## Sources

- Langage du corps du renard : [wildlifeonline.me.uk](https://www.wildlifeonline.me.uk/animals/article/red-fox-behaviour-fox-body-language), [robinbarefield.com](https://robinbarefield.com/how-do-red-foxes-communicate/)
- Animations de repos d'un compagnon : [mocaponline.com](https://mocaponline.com/blogs/mocap-news/idle-animation-loop), [forum Hive, idle animations for pets](https://forum.playhive.com/t/idle-animations-for-pets/94092), [dev.to, programming natural idle animations](https://dev.to/arkfuldodger/programming-natural-idle-character-animations-4l0g)
- Placement, jeux, modélisation organique : sources des fiches de `.claude/references/familiers/`
- Vitesses du joueur : [Minecraft Wiki, Walking](https://wiki.ronlab.site/content/minecraftwiki_en_all_maxi_2025-11/Walk), [Sprinting](https://minecraft-archive.fandom.com/wiki/Sprinting)
- Fréquence de foulée et changement d'allure : [Heglund et Taylor 1988, J. Exp. Biol. 138](https://cob.silverchair.com/jeb/article-pdf/2638526/jexbio_138_1_301.pdf), [Heglund, Taylor et McMahon 1974, mice to horses](https://www.scilit.net/publications/f00aff40fd63ae95b7306dcfa2bf45a2)
- Proportions du renard : [how2drawanimals.com, arctic fox](https://www.how2drawanimals.com/8-animals/77-draw-arctic-fox), [design.tutsplus.com, foxes](https://design.tutsplus.com/tutorials/how-to-draw-animals-foxes--cms-19886)

## Leçons des familiers refaits (2026-11-05)

- **Perché sur l'épaule** : rester à |x| ≥ 5,7 de l'axe de la tête (elle balaie un cylindre de 5,66 px en tournant). En course, les coins du bras qui balance montent ~1,2 px au-dessus de l'épaule : un familier perché décolle ou se décale, sinon il est traversé.
- **Deux familiers portés ensemble** : renard au sol à gauche, crâne flottant à droite, hibou perché sur l'épaule gauche — éviter de mettre deux familiers au même endroit.
- **Relais d'échelle** : quand un seul comportement joue à la fois, ses termes d'échelle peuvent se répartir sur un groupe enfant au même pivot (produit des facteurs = somme exacte, l'autre vaut 1) ; tirage pondéré par repli d'indices en surnombre (`v.i=v.i>17?(v.i<20?16:…):v.i`, `familier_abyssal`).
- **Molang de tête trop long** : répartir la rotation sur deux groupes (lacet / tangage) pour tenir sous 512 caractères.
- **`overlay_` en boucle** : fréquences de `q.life_time` multiples de 360/durée, hachages enveloppés par `math.mod(floor, N)`.
- **Sections en paliers** : bouts décalés de 0,12 px, ≥ 0,17 px entre sections successives ; choisir hauteurs et centres par script, pas à la main.
- **Hachage** : `math.mod(n * 7.31, 1)` donne un rythme presque périodique (motif tous les ~3 tirages) ; un hachage sinus (`math.mod(math.sin(n * 91.7) * 437.5, 1)`, avec `math.abs`) casse la régularité (ensemble Orage, 2026-11-05).
- **Flash ou pièce cachée montrés dans `attack`, `hurt` ou un événement** : par l'échelle de la forme, fenêtre par fenêtre, `ctrl_alpha` +1 pendant l'animation et 0 à la fin ; sinon l'aperçu de l'animation seule (planche, Vestiaire) montre tout en permanence.
- **Hasard qui ne tombe pas à intervalle fixe** (`familier_steampunk`, 2026-11-05) : un seul hachage par tranche donne le comportement (`math.mod(v.r,1)`) et le décalage de début (`math.mod(math.floor(v.r),4)`) ; pondération sans table par `v.b=math.max(0,v.b-2)-(v.b>5)-…` sur 16 cases. Le renderer et le Vestiaire prennent `q.life_time` = temps de l'animation, ramené à sa durée : allonger `idle` (120 s, multiple des périodes de base) et choisir les constantes du hachage pour que la graine 0 montre la variété dans l'aperçu.
- **Clé Molang trop longue** : un lacet de tête peut aussi passer sur le groupe du regard dans `idle` (il s'ajoute à l'`overlay_` en jeu).
- **Tirage pondéré** (`familier_kawaii_chat`, 2026-11-05) : tirer une case sur N, chaque comportement occupe un nombre de cases selon sa fréquence (`(v.i>=a)*(v.i<b)`), un tiers de cases calmes ; gestes courants souvent, gestes spectaculaires rarement.
- **Yeux sur un corps facetté ou une peau** : percer la surface par alpha et enfoncer l'œil (iris, pupille, reflet derrière ; paupière devant ; fond d'œil fermé tout au fond pour le clignement) : de profil, rien ne dépasse (`.claude/styles/kawaii.md`, Lanterne-chat).
