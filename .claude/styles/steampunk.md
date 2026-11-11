# Style — Steampunk (thème Mécanique, ensemble Steampunk)

Fiche de référence pour toute pièce de l'ensemble. Pièce existante à reprendre pour les matières : `cosmetiques/ailes/ailes_steampunk/gen_ailes_steampunk.py` (laiton, cuivre, acier sombre, rivets, engrenages découpés par alpha, longerons octogonaux, vérin à tige coulissante).

## Esprit

Victorien industriel : de l'artisanat d'horloger et de chaudronnier, pas de la science-fiction. Tout ce qu'on voit doit avoir l'air de **servir à quelque chose** (un tuyau relie deux pièces, un engrenage entraîne un autre, une vanne est sur un tuyau). Les éléments-signatures : laiton et cuivre, rivets, engrenages qui s'entraînent, pistons et vérins, manomètres à aiguille, soupapes, cheminées, sifflets, lunettes à lentilles, ressorts, chaînes, cuir cousu, verre de couleur ambre.

## Palette

| Matière | Clair | Base | Ombre | Usage |
|---|---|---|---|---|
| Laiton | (236, 196, 112) | (190, 142, 64) | (112, 76, 32) | Structure, cadres, engrenages |
| Cuivre | (232, 150, 96) | (176, 92, 52) | (98, 46, 26) | Tuyaux, chaudières, rivets |
| Acier bruni | (136, 140, 150) | (78, 82, 92) | (38, 40, 48) | Axes, tiges, ressorts |
| Vert-de-gris | (132, 186, 160) | (82, 138, 116) | | Retiré (retour du 2026-11-04 : « bugs de texture ») ; ne plus peindre de patine |
| Cuir | (150, 96, 60) | (104, 62, 36) | (60, 34, 20) | Sangles, coutures en laiton |
| Verre ambre | (255, 210, 120) | (220, 150, 50) | | Lentilles, cadrans ; calque `_e` chaud et doux |
| Vapeur | (250, 250, 248) | (220, 224, 228) | | Blanc légèrement bleuté, jamais jaune |

Contraste : grandes surfaces en laiton moyen, liserés clairs sur les arêtes, creux sombres et patinés. Un rivet = 3 texels minimum.

## Mouvement mécanique (le « saccadé réaliste »)

Une machine ne bouge pas comme un muscle. Repères (mécanique d'échappement d'horloge, servomoteurs) :
- **Tic, arrêt, tic** : l'échappement d'une horloge bloque puis relâche le mouvement par impulsions régulières. Un engrenage avance d'une dent, s'arrête, repart.
- **Dépassement et rappel** : un servo qui arrive en position dépasse un peu sa cible puis s'y stabilise (oscillation amortie courte, 1 ou 2 rebonds).
- **Pas tous en même temps** : les articulations bougent l'une après l'autre (le moteur entraîne l'épaule, puis le coude suit), et ce qui est porté continue un instant après l'arrêt du porteur.
- **Le moteur explique le geste** : l'aile monte parce que le vérin pousse ; la pression monte avant l'effort ; la vapeur sort après.
- Recette de génération : une **déformation du temps en paliers** appliquée à toute la pose (`palier(t)` : transitions courtes, arrêts, léger dépassement), avec un nombre entier de paliers par boucle pour que la boucle reste fermée. Échantillonner fin (≥ 24 keyframes/s), laisser l'optimiseur simplifier les arrêts.

## Vapeur et pression

- **Cycle** : la pression monte (aiguille du manomètre qui grimpe par à-coups), la soupape tremble, puis **décharge** : jet de vapeur bref et puissant, l'aiguille retombe. Le geste fort (battement, frappe, course) se fait pendant la décharge.
- **Jet modélisé** (synchronisé avec l'animation) : plaques `trans_` en dégradé d'opacité, croisées (ou `camy_`), qui jaillissent (`scale` de 0 à 1 en 0,1 s) puis s'étirent et s'effacent (`ctrl_alpha` de 0 à −1). Sortie par une buse visible. Son : `block.fire.extinguish` au moment de la décharge ; pistolet (2026-11-05, repris le 2026-11-08 par `skin_arc_steampunk` au tir, clé à 0,02 s de `event_release`) : son embarqué original `tir_vapeur` (double déclic de laiton, gâchette puis soupape, puis jet de vapeur qui monte de 1,8 à 5 kHz et s'efface avec le jet modélisé ; 0,8 s, clé à 0,03 s, `cosmetiques/objets/skin_arc_steampunk/sons/tir_vapeur.py`).
- **Reflets** : masque `_r` clair sur le laiton et le cuivre polis, sombre sur le cuir et le bois (lu par face).
- **Engrenages qui tournent en continu** : dans une animation `overlay_` ; ceux qui avancent par crans restent dans les états.
- **Vapeur qui reste** : `emit_mc_white_smoke` (ou `cloud`, `poof`) à la buse, cadence pilotée par `ctrl_emit` depuis le 2026-11-04 (−1 au repos, +4/+5 à la décharge, `fonctions-avancees.md`) ; le jet modélisé double la synchronisation.
- Sifflet ou cheminée : petites bouffées régulières au repos, comme une machine sous pression qui respire.

## Pièces de l'ensemble

| Pièce | Idée maîtresse |
|---|---|
| `ailes_steampunk` | Ailes articulées à lames, vérins, manomètres aux épaules, buses de décharge au poignet |
| `haut_de_forme_steampunk` (refonte du 2026-11-08) | Haut-de-forme rond posé sur la tête, feutre brun, ruban de cuir ; calotte-chaudière : porte de foyer rougeoyante au dos, manomètre à droite, cheminée à soupape sur le dessus, moteur à vapeur sur le bord avant dont le pignon fait basculer les lunettes d'aviateur par l'avant en sneak, puis deux loupes d'horloger devant le verre droit. Pas encore vu en jeu |
| `epaulieres_steampunk` (v2, 2026-11-08) | Épaulières d'armure en éventail : rang haut de 5 lames sur l'épaule, jupe de 5 lames en cône autour du bras, moyeu à roue de 12 dents + pignon et lentille-témoin ; chaudière, foyer et deux cheminées à droite, accumulateur, manomètre et sifflet à gauche (détail : section Épaulières v2). Pas encore vues en jeu |
| `queue_steampunk` | v3 (2026-11-08) : colonne de 9 cloisons de laiton sur rotules d'acier, 4 câbles de cuivre tirés par les tambours du boîtier dorsal (tangage sur les flancs, lacet dessus), 2 vérins latéraux télescopiques, manomètre ; la vapeur passe dans la colonne et sort par la buse d'un empennage en losange à bague-témoin ambre. Onde fluide (robot serpent), raidissement sous pression puis décharge. Pas encore vue en jeu |
| `familier_steampunk` | Hibou automate perché sur l'épaule gauche, clé de remontage, yeux-lentilles ambre à diaphragme ; vole sur un rotor de calotte (ailes raides en gouvernes, jamais de battement pour voler) |
| `skin_arc_steampunk` (objets, 2026-11-08) | « Pistolet à vapeur », skin de tous les arcs (remplace l'arme portée `pistolet_steampunk`, archivée) : crosse verticale de bois sombre, carcasse de laiton, chaudière de cuivre à manomètre ambre, soupape, canon coulissant sur ressort, pavillon évasé. Étapes de bande = montée en pression : chien d'acier armé par crans (repos, demi-cran, armé), aiguille qui grimpe jusqu'au rouge, fléchette d'acier visible dans le pavillon, lentille-témoin ambre allumée à `bande_3`. Tir (`event_release`) : chien qui tombe, recul, jet `trans_` qui monte, poof + white_smoke, son `tir_vapeur`. Display vanilla `item/bow`. Pas encore vu en jeu |
| `skin_arbalete_steampunk` (objets, 2026-11-05) | « Arbalète à vapeur », skin de toutes les arbalètes : arc en trois lames de ressort de laiton étagées, câble d'acier, fût de bois sombre à rails, engrenage de remontage à manivelle sur tambour (la griffe tire la corde jusqu'à la noix), réservoir de cuivre à manomètre sur le flanc gauche. Étapes : la corde recule, les lames plient, l'engrenage tourne, l'aiguille grimpe ; chargée, lentille ambre `_e` de la noix allumée. Display vanilla (`item/crossbow`). Pas encore vue en jeu |
| `skin_pioche_steampunk` (objets, 2026-11-08) | « Pic à vapeur », skin de toutes les pioches : croissant vanilla gardé ; manche de bois sombre, poignée de cuir cousu, chaudière de cuivre rivetée au manche (manomètre ambre +Z, foyer à fentes au dos, soupape), tuyau à vanne jusqu'au fer ; bras avant = cylindre de frappe de laiton, nez de retenue, pointerolle d'acier poli qui coulisse ; bras arrière = pic recourbé ; lentille-témoin. Vivant : `item_idle` 24 s (pression par crans, deux décharges, un son), `item_swing` (martèlement), `event_swing`, `event_break` (jet d'échappement + white_smoke), `event_select`. Référence : `.claude/references/objets/pioches-marteaux-pneumatiques.md`. Pas encore vu en jeu |

## Sources

- Mécanique d'échappement (tic, arrêt, impulsions régulières) : https://www.firgelliauto.com/blogs/mechanisms/antique-clock-escapement , https://hackaday.com/2016/11/15/the-little-mechanism-that-made-precise-time-keeping-possible
- Dépassement et stabilisation d'un servo : https://www.motioncontroltips.com/how-to-address-overshoot-in-servo-control
- Mouvement « robotique » et suite d'un mouvement : https://playbooks.com/skills/dylantarre/animation-principles/follow-through-overlapping , https://roblox-stepper-motor-script.pages.dev
- Soupape et manomètre : https://www.steamlocomotive.com/appliances/safetyvalve.php , https://locomotive.fandom.com/wiki/Safety_Valve
- Ailes steampunk articulées : https://boingboing.net/2013/02/26/articulated-flapping-steampun.html , https://hackaday.com/2011/11/11/steampunk-wings-bigger-heavier-and-steampunkier/
- Accessoires (haut-de-forme et lunettes, épaulières, bras mécanique) : https://vintagedancer.com/steampunk/steampunk-accessories/ , https://recyclenation.com/2011/09/incredible-suits-steampunk-recycle-armor/
- Queue à câbles, joint universel à longueur de câble constante, cloisons dégressives : https://par.nsf.gov/biblio/10155499-cable-length-invariant-robotic-tail-using-circular-shape-universal-joint-mechanism , https://arxiv.org/html/2410.21445v1
- Onde du robot serpent (angle = A·sin(ωt − k·s), retard constant entre articulations) : https://api.emergentmind.com/topics/serpenoid-gait-function
- Pic de mineur et marteau pneumatique (piston libre, pointerolle, retenue) : `.claude/references/objets/pioches-marteaux-pneumatiques.md`
- Particules vanilla de fumée (`white_smoke`, `cloud`, `poof`, `campfire_cosy_smoke`) : https://docs.rs/mcproto-types/0.5.0/mcproto_types/entity_metadata/enum.Particle.html

## Retours de l'utilisateur (2026-11-04)

- Pas de vert-de-gris ni de brossé contrasté : ils se lisent comme des bugs de texture. Métal propre, usure suggérée par le bord et les rivets seulement.
- Contenant dorsal d'apparition : réservoir cylindrique de chaudière (cuivre riveté, cerclages et dômes de laiton, hublots à iris), choisi à la place du coffre.

## Familier (hibou automate, 2026-11-05)

Ce qui le rend vivant, à garder pour tout automate de l'ensemble (`cosmetiques/familiers/familier_steampunk/gen_familier_steampunk.py`) :
- **Regard d'automate** : la tête pivote par crans (overlay, regard du joueur par pas de 15° avec retard), pupilles-diaphragmes qui font la mise au point par crans, iris à crans qui tourne, paupière-volet ; yeux fixes dans la tête (hibou : c'est la tête qui bouge).
- **Comportements tirés au hasard** (tranches de 13 s, début décalé de 0 à 3 s, tirage pondéré sur 16 cases dont 3 calmes) : tête retournée à 200° ou 240° clic par clic, hochement de triangulation, lissage des lames de l'aile, battement d'équilibre, petit vol sur le rotor jusqu'à l'épaule droite, remontage de la clé (paupières qui tombent, clé par quarts de tour, réveil d'un coup), cycle de pression (soupape qui tremble, jet `trans_` + `emit_mc_white_smoke` par `ctrl_emit` à la décharge, s'ébroue), picore la joue du joueur (seulement si celui-ci regarde devant), somnole le jour.
- **Monde et joueur** : pluie ou eau, le métal chaud fume (`ctrl_emit` +2) et il s'ébroue ; nuit, lentilles plus vives et pupilles dilatées (rapace nocturne) ; vie basse, tassé, tourné vers le joueur, lentilles qui baissent par à-coups (panne de pression) ; virages (`q.yaw_speed`), saut, atterrissage, blessure.
- **Logique physique** : il marche perché, décolle sur son rotor pour la course, le vol, les élytres et les vraies chutes ; les ailes ne battent que pour l'équilibre.

## Épaulières v2 (2026-11-08)

v1 refusée (« moche de ouf ») : un bloc doré uniforme qui entourait le bras, sans silhouette. Référence de réussite donnée par l'utilisateur : `epaulieres_abyssales` (plaques en éventail qui débordent de l'épaule, éléments qui montent, attache nette).
- **Construction d'armure réelle traduite en machine** : une épaulière se fait de lames à arête médiane qui se recouvrent, tenues par des cuirs et des rivets coulissants (le rivet glisse dans une fente : la lame bouge sans se détacher). Ici : lames découpées par alpha + arête en losange (volume et reflet), rang haut sur l'épaule, jupe en cône (chaque lame tournée vers l'extérieur du bras : lisible de face comme de profil), sangles de cuir cousu avant et arrière.
- **Même langage que les ailes validées** : lames acier / laiton / cuivre alternées, liseré clair, joint sombre, bout d'une autre matière, rivets de 4 texels ; métal propre.
- **Fonction de chaque pièce** : la roue du moyeu porte la jupe (elle tourne quand l'éventail s'ouvre à l'apparition) et arme la pompe d'un cran par tic ; la pression monte (aiguille à gauche, levier de soupape à droite), tremble, puis décharge (jet `trans_` qui monte + `emit_mc_white_smoke` piloté par `ctrl_emit`) et les lames claquent d'un cran.
- **Lumière** : cadran ambre (face), lentilles-témoins des moyeux et de l'accumulateur (flancs), porte du foyer à fentes (dos et flanc droit). Peu de lumière vue de face à droite (à voir en jeu).
- Sources : construction des épaulières (lames à arête, cuirs, rivets coulissants) : https://data.fitzmuseum.cam.ac.uk/id/object/18634 , https://worcester.emuseum.com/objects/50182/left-pauldron , https://myarmoury.com/talk/viewtopic.php?p=344999 ; costumes à plaques rivetées et jauges : https://recyclenation.com/2011/09/incredible-suits-steampunk-recycle-armor/
