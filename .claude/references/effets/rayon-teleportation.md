# Référence — Rayon de téléportation (colonne de lumière qui emporte ou dépose)

Fiche documentée (2026-11-07, pour `effet_rayon`). Étude par analogie d'une inspiration donnée par l'utilisateur (règle 5 de `CLAUDE.md`) : on décrit la grammaire visuelle d'un « rayon de transport » de vaisseau de science-fiction, jamais l'œuvre ; formes, timing et sons de nos pièces sont inventés.

## Déroulé observé (extraits à 24–30 images/s)

**Dépose (arrivée)**, mesurée image par image sur une scène d'intérieur (luminance moyenne de la zone du faisceau) :

| Temps | Ce qui se passe |
|---|---|
| 0,00–0,15 s | un **voile de lumière** apparaît d'un coup sur toute la hauteur (pas de tête qui descend : la colonne est déjà là, floue, plus large qu'un homme, ≈ 1,5 fois sa largeur) |
| 0,15–1,0 s | la colonne s'intensifie (luminance moyenne 153 → 191) ; **traits verticaux** fins qui la parcourent ; bords **bleutés** francs |
| 1,0–1,4 s | la colonne se resserre sur une **silhouette humaine pleine de lumière** (blanc au cœur, liseré bleu tout autour, 35–40 % de pixels bleus) |
| 1,4–1,8 s | la silhouette laisse voir la personne : des **stries verticales** claires restent sur le corps, plus longtemps sur les jambes ; tout est éteint à 1,8 s |

**Emport (départ)**, sur un extrait d'amateur reproduisant l'effet (personne debout dans un pré, 30 images/s) : 0,7 s en tout. Lueur qui naît au **torse**, enveloppe le corps en 0,2 s, des stries montent au-dessus de la tête ; la silhouette devient une forme blanche lumineuse, puis **se défait vers le haut** en traînées verticales qui s'effacent (le bas disparaît d'abord).

## Formes

- Colonne **verticale** et droite, sans rotation ni spirale ; plus large que la personne ; bord net d'un bleu clair, cœur plus blanc ; légère lueur diffuse autour.
- Texture interne en **fines stries verticales** qui défilent, jamais de motif géométrique.
- La personne n'est jamais rétrécie : elle est **remplacée par une silhouette de lumière** (pleine, liserée de bleu) qui se remplit ou se défait.

## Couleurs (échantillonnées sur l'extrait de dépose)

| Luminosité | Couleur moyenne |
|---|---|
| > 240 (cœur) | (247, 248, 250) blanc à peine bleuté |
| 200–240 | (205, 215, 230) |
| 160–200 | (164, 174, 203) |
| 120–160 (halo) | (128, 135, 156) |
| liseré bleu | moyenne (146, 161, 211), vif (179, 194, 242) |

Une seule teinte : blanc froid → bleu lavande clair sur les bords. Pas de couleur chaude.

## Sons (mesurés le 2026-11-07 sur deux extraits avec piste son, même son de série ; aucun échantillon gardé)

Un seul événement d'environ **2,2 s** (2,2 et 2,3 s sur les deux extraits), en trois couches :

| Temps (depuis l'attaque) | Mesure | Ce qu'on entend |
|---|---|---|
| 0–0,02 s | attaque franche | « whoomp » : 55 à 94 % de l'énergie sous 250 Hz, crête vers 60–100 Hz |
| 0–1,0 s | niveau −21 → −30 dB (≈ −9 dB en 0,9 s) ; centroïde 350–950 Hz | **nappe de souffle large bande** (jusqu'à ~15 kHz) et, dedans, des **partiels fixes inharmoniques** qui papillotent (raies tenues relevées sur les deux extraits : ≈ 212, 590, 1 610, 2 356, 4 330, 7 040, 7 890, 8 370 Hz) : grésillement électrique |
| ≈ 1,0–1,45 s | centroïde 6,8 → 4,5 → 2,1 kHz par pas de 0,1 s ; part > 7 kHz 60 % → 2 % | **« zip » descendant** : une bande de bruit (~1–2 kHz de large, deux traces parallèles) tombe de ~16 kHz vers ~2,5 kHz en ralentissant (≈ 16 k → 8 k en 0,15 s, 4 k à 0,3 s, 2,5 k à 0,45 s) ; c'est l'instant où la personne apparaît ou part |
| 1,4–2,2 s | 3–7 kHz = 35–55 % de l'énergie ; −24 → −45 dB | traîne scintillante aiguë qui s'éteint |

Aucun bruit mécanique, pas de mélodie. Notre synthèse (sons v2 de `effet_stellaire_rayon`, `sons/_faisceau.py`, original) :
`nappe()` (bruit filtré 150 Hz–15 kHz + bosse 2,5–6 kHz), `scintillement()` (9 sinus fixes inharmoniques, amplitude modulée par un bruit lissé à 14–45 Hz), `coup()` (sinus qui glisse de 170 à 62 Hz), `zip_descendant()` (bruit à bande étroite modulé par une porteuse f = 1,5 k + 14,5 k·e^(−t/0,17), seconde trace à 0,8 f). Répartition dans nos animations (instants inchangés) : `stellaire_rayon_eclair` à 0 s (souffle de chute, puis whoomp + nappe à l'impact 0,35 s), `stellaire_rayon_montee` 1 s avant la disparition / l'apparition (la nappe enfle, le zip tombe au sommet, traîne 2–7 kHz), `stellaire_rayon_extinction` à la coupure du faisceau (zip bref 11 → 2 kHz, nappe coupée, coup mat, traîne). Comparaison : `cosmetiques/effets/effet_stellaire_rayon/.build/sons_comparaison.png`. v1 (« d'après le genre », sans écoute) gardée dans `sons/v1/`.

## Traduction dans le mod (`effet_rayon`)

- Spectacle de 3–5 s (règle des effets) : la colonne **tombe du ciel** (tête lumineuse qui descend en 0,35 s, impact au sol), tient pendant la transformation, puis **s'éteint d'un coup** (resserrement en 0,1 s et éclat).
- Colonne en couches `add_` concentriques (coques à facettes, intensité croissante vers le centre) + bord net en `trans_` bleu (lisible de jour), stries verticales qui défilent ; anneaux en segments (poutres) qui descendent le long du faisceau.
- Silhouette de lumière en géométrie : enveloppe `add_` du corps en tranches horizontales + nuage de points-éclats sur la peau ; au départ elle se défait de bas en haut, les éclats montent dans le faisceau (copie du joueur cachée < 0,05 quand la silhouette est la plus vive : son échelle n'est pas appliquée au départ) ; à l'arrivée les éclats descendent, la silhouette se remplit de bas en haut, le joueur apparaît dedans à sa taille, puis elle s'efface en laissant des stries.
- Pièges : trait fin peint sur grande plaque = effacé par les mipmaps (`categories/effets.md`) ; tout est en poutres pleines en travers.

## Sources

- Extrait d'amateur reproduisant l'effet (YouTube `u9sgC5Ft6zA`) : départ image par image (30 im/s).
- Extrait de série télévisée (YouTube `aEh3Bs_mAEk`, 91–94 s) : arrivée image par image (23,8 im/s), couleurs mesurées par seuils de luminosité.
- Sons : quatre courts extraits YouTube avec piste son (`Yg5MDOwAicQ`, `v6JPRs8IroM`, `LUnre-EDEO4`, `1bm3H0HtiUY`), mesurés par spectrogramme, enveloppe et bandes d'énergie ; deux (`Yg5MDOwAicQ`, `v6JPRs8IroM`) portent le son de série seul et ont servi aux mesures.
- Encyclopédies de fans de la série (transport par faisceau) : téléportation instantanée sans plate-forme, rayon de lumière mobile.
