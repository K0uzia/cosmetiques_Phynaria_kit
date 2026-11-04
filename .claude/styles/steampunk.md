# Style — Steampunk (thème Mécanique, ensemble Steampunk)

Fiche de référence pour toute pièce de l'ensemble. Pièce existante à reprendre pour les matières : `cosmetiques/ailes/ailes_mecaniques/gen_ailes_mecaniques.py` (laiton patiné, cuivre, acier sombre, vert-de-gris, rivets, engrenages découpés par alpha, longerons octogonaux, vérin à tige coulissante).

## Esprit

Victorien industriel : de l'artisanat d'horloger et de chaudronnier, pas de la science-fiction. Tout ce qu'on voit doit avoir l'air de **servir à quelque chose** (un tuyau relie deux pièces, un engrenage entraîne un autre, une vanne est sur un tuyau). Les éléments-signatures : laiton et cuivre, rivets, engrenages qui s'entraînent, pistons et vérins, manomètres à aiguille, soupapes, cheminées, sifflets, lunettes à lentilles, ressorts, chaînes, cuir cousu, verre de couleur ambre.

## Palette

| Matière | Clair | Base | Ombre | Usage |
|---|---|---|---|---|
| Laiton | (236, 196, 112) | (190, 142, 64) | (112, 76, 32) | Structure, cadres, engrenages |
| Cuivre | (232, 150, 96) | (176, 92, 52) | (98, 46, 26) | Tuyaux, chaudières, rivets |
| Acier bruni | (136, 140, 150) | (78, 82, 92) | (38, 40, 48) | Axes, tiges, ressorts |
| Vert-de-gris | (132, 186, 160) | (82, 138, 116) | | Patine dans les creux, jamais dominante |
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
- **Jet modélisé** (synchronisé avec l'animation) : plaques `trans_` en dégradé d'opacité, croisées (ou `camy_`), qui jaillissent (`scale` de 0 à 1 en 0,1 s) puis s'étirent et s'effacent (`ctrl_alpha` de 0 à −1). Sortie par une buse visible. Son : `block.fire.extinguish` au moment de la décharge.
- **Reflets** : masque `_r` clair sur le laiton et le cuivre polis, sombre sur le cuir et le bois (lu par face).
- **Engrenages qui tournent en continu** : dans une animation `overlay_` ; ceux qui avancent par crans restent dans les états.
- **Vapeur qui reste** : `emit_mc_white_smoke` (ou `cloud`, `poof`) à la buse. Sa cadence ne se pilote pas par l'animation (pas de `ctrl_emit`) : le staff règle *Quand*, *Nombre* et *Rafale* (attaque, saut…). Le jet modélisé porte la synchronisation.
- Sifflet ou cheminée : petites bouffées régulières au repos, comme une machine sous pression qui respire.

## Pièces de l'ensemble

| Pièce | Idée maîtresse |
|---|---|
| `ailes_mecaniques` | Ailes articulées à lames, vérins, manomètres aux épaules, buses de décharge au poignet |
| `haut_de_forme_mecanique` | Haut-de-forme à lunettes basculantes, engrenages sur le ruban, petite cheminée qui fume |
| `epaulieres_mecaniques` | Épaulières asymétriques : cheminées d'échappement à droite, manomètre et engrenage à gauche |
| `queue_mecanique` | Queue en anneaux de laiton articulés, ressorts entre les segments, mouvement à cliquet, soupape au bout |
| `familier_hibou_mecanique` | Hibou automate à clé de remontage, ailes qui battent par tics, yeux à lentilles ambre |
| `pistolet_mecanique` | Tromblon à vapeur : chaudière, manomètre, canon évasé, décharge de vapeur à l'attaque |

## Sources

- Mécanique d'échappement (tic, arrêt, impulsions régulières) : https://www.firgelliauto.com/blogs/mechanisms/antique-clock-escapement , https://hackaday.com/2016/11/15/the-little-mechanism-that-made-precise-time-keeping-possible
- Dépassement et stabilisation d'un servo : https://www.motioncontroltips.com/how-to-address-overshoot-in-servo-control
- Mouvement « robotique » et suite d'un mouvement : https://playbooks.com/skills/dylantarre/animation-principles/follow-through-overlapping , https://roblox-stepper-motor-script.pages.dev
- Soupape et manomètre : https://www.steamlocomotive.com/appliances/safetyvalve.php , https://locomotive.fandom.com/wiki/Safety_Valve
- Ailes steampunk articulées : https://boingboing.net/2013/02/26/articulated-flapping-steampun.html , https://hackaday.com/2011/11/11/steampunk-wings-bigger-heavier-and-steampunkier/
- Accessoires (haut-de-forme et lunettes, épaulières, bras mécanique) : https://vintagedancer.com/steampunk/steampunk-accessories/ , https://recyclenation.com/2011/09/incredible-suits-steampunk-recycle-armor/
- Particules vanilla de fumée (`white_smoke`, `cloud`, `poof`, `campfire_cosy_smoke`) : https://docs.rs/mcproto-types/0.5.0/mcproto_types/entity_metadata/enum.Particle.html
