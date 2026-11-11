# Référence — Anneau d'étincelles (porte tracée à la main)

Fiche documentée (2026-11-07, pour `effet_etincelles`). Étude par analogie d'une inspiration donnée par l'utilisateur (règle 5 de `CLAUDE.md`) : on décrit la grammaire visuelle, jamais l'œuvre ; glyphes, sceaux et motifs de nos pièces sont inventés.

## Déroulé observé (extrait à 8 images/s)

| Temps | Durée mesurée | Ce qui se passe |
|---|---|---|
| Geste | 1–3 s | la main tendue décrit des cercles ; un petit nœud d'étincelles naît devant elle, crachote, hésite (flammèches en forme de crochet), grandit par à-coups |
| Tracé | ≈ 0,4 s | un arc d'étincelles part d'un point (souvent en haut) et court le long du cercle ; l'anneau est fermé en 3 images |
| Tenue | 0,5–1 s | l'anneau tourne sur lui-même, crache en continu des étincelles **tangentes**, plus longues dehors que dedans ; au bas, elles pleuvent au sol et s'y accumulent |
| Ouverture | 0,5–1 s | l'intérieur passe d'un voile chaud trouble (air brûlant) à l'image d'un autre lieu |
| Passage | 0,3–0,5 s | le personnage traverse le plan ; gerbe d'étincelles sur lui, quelques-unes le suivent |
| Fermeture | 0,3–0,6 s | l'anneau se resserre en accélérant, pluie de braises qui tombent, puis plus rien |

## Formes

- Anneau **fin** (≈ 3–5 % du diamètre) au bord intérieur net et clair, bord extérieur hérissé (traits courts, longueurs très inégales).
- Les étincelles sont des **traits** (flou de mouvement), pas des points : tête vive, queue qui s'éteint ; penchées dans le sens de la rotation.
- Taille : à peu près la hauteur d'un homme, bas de l'anneau au ras du sol.
- Le nœud du début : une boule d'étincelles irrégulière, quelques flammèches courbes, qui saute plutôt qu'elle ne grandit régulièrement.

## Couleurs (échantillonnées sur l'extrait)

| Luminosité | Couleur moyenne |
|---|---|
| > 240 (cœur) | (248, 172, 103), blanc jaune au centre du filet |
| 200–240 | (217, 140, 77) |
| 150–200 (bord) | (172, 110, 60) |
| 100–150 (voile) | (121, 80, 55) |

Orange doré, une seule teinte ; cœur presque blanc ; voile intérieur brun chaud très sombre.

## Sons (à l'oreille, pour la synthèse de nos sons originaux)

Grésillement aigu et dense (métal chauffé, cierge magique), souffle qui monte à l'ouverture, bouffée d'air au passage, claquement bref et braises qui pétillent à la fermeture.

## Traduction dans le mod (`effet_etincelles`)

- v2 (après le retour en jeu du 2026-11-07, `categories/effets.md`) : porte **fixe** de 3 blocs (plan XY), tube de 160 segments (âme opaque + `_e`, gaine `add_`), 5 couronnes de traits en poutres pleines qui tournent à des vitesses différentes, 240 traits de gerbes tangentes et 56 étincelles qui rebondissent au sol (Molang). v1 (porte `camy_`, chevelure peinte) : effacée par les mipmaps en jeu.
- Le tracé en arc devient : porte minuscule (nœud) qui grandit en tournant vite, une pointe claire sur son bord trace la spirale.
- Particules : traits d'étincelles (points d'émission dans le plan monde, +Y tangent penché dehors, tournent avec le bord), braises lourdes qui se posent, `emit_mc_wax_on`, `emit_mc_small_flame`. Pas d'`end_rod`.
- Le joueur franchit la porte en rétrécissant vers son centre (groupe `joueur`, y = 22·(1 − échelle)).
- Pièges : un anneau en segments chevauchés fait des créneaux ; des traits fins peints à moins de 5 texels/px font des escaliers au plus proche (leçon des fissures, `categories/effets.md`).

## Sources

- Extrait vidéo étudié : compilation YouTube `_UFiGPk1tHs` (images extraites à 1 et 8 im/s, couleurs mesurées par seuils de luminosité).
- Articles de making-of des studios d'effets (framestore.com, sidefx.com, artofvfx.com) : étincelles simulées une à une pour paraître physiques, palette jaune orange, éclairage LED autour de l'anneau sur le plateau.
