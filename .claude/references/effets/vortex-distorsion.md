# Référence — Vortex de distorsion (l'espace se tord en spirale et aspire en un point)

Fiche documentée le 2026-11-07 pour `effet_vortex`, d'après l'étude image par image de trois extraits vidéo (une scène d'anime
de téléportation, une reconstitution amateur en prise de vue réelle qui exagère la spirale, un montage court), téléchargés en
basse résolution dans le scratchpad, plus l'écoute et le spectrogramme de la bande son. Approche par analogie (`CLAUDE.md`,
règle 5) : on garde la **grammaire visuelle** (spirale, aspiration, implosion, retour inversé), traduite en version 100 %
originale ; aucun personnage, symbole, motif d'œil ou forme empruntée. Le guide du mod et `.claude/rules/` priment.

## Déroulé observé (plan par plan)

| Temps (s) | Ce qu'on voit |
|---|---|
| 0 | Personnage immobile ; aucune annonce lumineuse (pas de cercle, pas de flash). |
| 0 – 0,5 | Le contour se met à onduler : l'air autour du corps se trouble, comme une brume de chaleur. |
| 0,5 – 2,5 | Le corps est **tiré vers un point** (pas forcément son centre) en se tordant : les membres s'étirent dans le sens de rotation, la silhouette devient une virgule. Le point d'attraction reste fixe. |
| 2,5 – 4,5 | La masse **rétrécit en accélérant** (courbe en ease-in), toujours en tournant ; elle devient une tache, puis un point. |
| ≈ 4,5 – 5 | Le point disparaît d'un coup : pas d'explosion, l'image revient au fond calme. |
| Retour | Même chose à l'envers : un point qui s'ouvre, la spirale qui tourne dans l'autre sens et rend le corps à sa taille. |

Version exagérée (reconstitution, la plus utile pour un effet de jeu) : **5 à 6 bras** en spirale logarithmique, courbés
d'environ 120 à 180°, qui tournent et se resserrent vers le centre en 4 à 5 s ; le corps est cisaillé dans les bras ; les bras
pâlissent jusqu'à un petit tourbillon au centre, puis plus rien.

## Formes et couleurs

- Spirale à **5–6 bras**, chacun plus large dehors, effilé au centre ; un **bord net** du côté qui avance et une **traîne
  floue** de l'autre (le bras « file »), plus quelques fines lignes parallèles dans le bras (impression de vitesse).
- Anneaux concentriques légèrement ondulés autour du centre (ondes de distorsion).
- La distorsion elle-même est **sans couleur** : elle tord le fond. Teintes échantillonnées sur la reconstitution : bras
  gris-mauve (≈ 141,139,137 ; 165,162,170), bords clairs (≈ 196,186,184), creux sombres (≈ 30,23,18). Notre traduction
  (le jeu ne sait pas réfracter) : bras `trans_` gris-violet sombre (26,20,42 → 78,66,110), bord clair lavande (228,218,252),
  voile léger entre les bras, trou presque noir au centre.

## Sons (spectrogramme)

Pas de musique : un **grondement grave continu** (< 300 Hz) sous un **souffle large** (0,5–12 kHz) qui **enfle** jusqu'au
moment où le corps devient un point, avec un petit transitoire (déchirement) vers le premier tiers ; puis extinction rapide.
Traduction : trois sons originaux par animation au plus (`tools/synthe.py`) : torsion (grondement qui monte en vrillant),
aspiration (souffle qui enfle, coupé net), implosion (clic + coup sourd qui tombe + onde) ; au retour : détorsion
(grondement qui descend) et expulsion (souffle qui sort + coup sourd à la pose).

## Timing

Anticipation discrète (ondulation), puis torsion lente qui **accélère** (ease-in), fin en point très brève (≤ 0,15 s), pas
d'explosion : la petite onde après l'implosion est notre ajout pour la lisibilité en jeu. Retour : ease-out (rapide puis lent).

## Traduction dans le mod (`effet_vortex` v1)

| Code | Outil | Recette |
|---|---|---|
| Spirale lisible de partout | `cam_` (face caméra), centre au torse (y = 17) | plaque devant le joueur (+5 px vers la caméra), anneaux concentriques derrière (−5 px) : le joueur est pris en sandwich |
| Bras lisses | texture à 4,9 texels/px, profils **gaussiens** (bord clair, couverture en rampe de 2 texels) | un bord d'alpha dur fait des escaliers au plus proche ; des bras découpés en anneaux qui tournent à des vitesses très différentes se cassent en lames : écart borné à 26° |
| Aspiration | rotation qui accélère dans le sens où la spirale « coule » vers le centre (spirale log : tourner = changer d'échelle) | `-(70t + 58t²)` ; le cœur prend 26° d'avance (resserrement) |
| Corps aspiré | groupe `joueur` : échelle 1 → 0 en ease-in, position y = 17·(1 − échelle) | la rotation du groupe est ignorée : la torsion se lit par la spirale autour |
| Débris | 14 cubes en orbite (orbite > rayon > culbute), points `emit_` sur un groupe qui tourne, +Y vers le centre (départ) ou le dehors (arrivée) par clés de rotation | `portal` de Minecraft converge vers son point d'émission (supposé, à voir en jeu) |
| Nuit | bords clairs dans `_e`, lueur `add_` violette des bords | tout ce qui est sombre a besoin d'une lueur (`effet_admin_neant`) |

## Sources

- Extraits vidéo étudiés (YouTube, basse résolution, non conservés dans le dépôt) : identifiants `DyPcfZ2u7Qo`
  (reconstitution en prise de vue réelle, spirale exagérée), `b2aIMicSHFQ` et `Nd1S0WzY5A0` (scène d'anime, corps aspiré en un
  point en ≈ 4,5 s).
- Description générale de l'effet (force d'attraction visible, forme tordue jusqu'à disparaître) : wiki de fans consulté le
  2026-11-07.
- `.claude/references/effets/principes-fx-anime.md` (trois temps, less is more), `failles-portails.md`.
