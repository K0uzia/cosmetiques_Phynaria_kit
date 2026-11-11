# Référence — Anneaux de transport (colonne d'anneaux empilés)

Fiche documentée (2026-11-07, pour `effet_stellaire_anneaux`). Étude par analogie d'une inspiration donnée par l'utilisateur (règle 5 de `CLAUDE.md`) : on décrit la grammaire visuelle, jamais l'œuvre ; gravures, motifs et palette de nos pièces sont inventés.

## Déroulé observé (deux extraits, images à 2, 8 et 12 im/s)

| Temps | Durée mesurée | Ce qui se passe |
|---|---|---|
| Arrivée des anneaux | ≈ 1,7 s pour 5 anneaux | les anneaux arrivent **un par un**, à 0,17–0,25 s d'écart : du plafond (extrait 1) ou d'une fosse sous le sol (extrait 2) ; le premier va le plus loin (en bas s'ils descendent, en haut s'ils montent) ; chacun ralentit fort juste avant sa place et s'arrête net, sans rebond visible ; ils ne tournent pas |
| Colonne | 0,3–1 s | 5 anneaux horizontaux empilés autour des personnages, écart vertical ≈ 0,7 × hauteur d'un anneau ; colonne ≈ hauteur d'un homme × 1,1, diamètre ≈ 1,5 × la hauteur de la colonne |
| Éclair | 0,5–0,75 s | une bande de lumière **monte du bas** de la colonne (extrait 1) ou toutes les faces intérieures s'allument (extrait 2) ; cœur blanc chaud, lumière qui fuit **à l'horizontale** entre les anneaux en longues stries ; au sommet, la lumière jaillit vers le haut ; les personnages disparaissent (ou apparaissent) au plus fort |
| Départ des anneaux | ≈ 1,3 s | ils repartent d'où ils sont venus, **le dernier arrivé part le premier**, un par un, en accélérant |

## Formes

- Anneau épais, section presque carrée (hauteur ≈ 8 % du diamètre, épaisseur radiale semblable) ; dessus **nervuré** (crans réguliers), face extérieure chargée de reliefs et de cartouches ; intérieur plus sombre.
- Au sol, une plaque ronde au motif concentrique, un peu plus large que les anneaux (fond de la fosse dans l'extrait 2, allumée d'une lueur pâle avant l'arrivée).

## Couleurs (échantillonnées)

| Zone | Couleur moyenne |
|---|---|
| Métal ombré | (25, 11, 2), (56, 34, 18) |
| Métal éclairé | (101, 73, 52), (155, 122, 93) |
| Reflets du métal | (212, 188, 165) |
| Éclair : cœur > 240 | (253, 231, 202) blanc chaud |
| Éclair : 200–240 | (216, 184, 149) |
| Stries de l'éclair | (148, 175, 140) vert pâle (reflet d'objectif) |

Ces teintes brun-orangé viennent de l'éclairage chaud de la pièce (extrait 1). **Mesures v2 (2026-11-07)**, quantiles de luminosité sur les anneaux, images fixes à 640 × 360 :

| Éclairage | Sombre (5–30 %) | Moyen (40–70 %) | Clair (85–97 %) | Reflet (99 %) |
|---|---|---|---|---|
| Chaud (extrait 1, 4 images) | (18, 5, 0) | (39, 21, 7), teinte 26°, sat. 0,8 | (93, 67, 46) | (145–182, 120–151, 95–125) |
| Neutre (extrait 2) | (33, 30, 31) | (44, 45, 46), **sat. 0,03** | (111, 108, 111) | (203, 213, 224) |

Le métal est donc un **acier sombre presque neutre**, poli (reflets nets et étroits), qui prend la couleur de la lumière ambiante. Éclair de l'extrait 2 (image la plus claire) : cœur (251, 249, 248) **blanc neutre**, 200–250 : (217, 210, 209), stries de côté (171, 163, 170) légèrement bleu-lavande ; l'éclair « blanc chaud » de l'extrait 1 est l'éclairage de la pièce.

**Profil** (extrait 1, anneaux posés, agrandi ×3) : face extérieure lisse et sombre traversée par une **nervure médiane** polie (filet de reflet continu) ; **plots rectangulaires en relief** au bord haut et au bord bas, alternés (≈ 36–40 par tour), chacun avec un petit **rivet** clair ; dessus à plots comme des dents ; **presque pas de gravures** (surface mécanique : plaques, plots, rivets, joints).

Notre version v1 : or ambré à grands cartouches gravés (refusée : « ils ne sont pas comme ça dans la série »). **v2** : acier sombre légèrement chaud (creux 20, foncé 56, moyen 86, clair 138, reflet 214 ; un peu plus clair que la référence pour rester lisible en jeu), arête haute claire, nervure médiane polie à filet de reflet, plots alternés haut (segments pairs) et bas (impairs) peints avec rivet et ombre portée, et repris en géométrie au-dessus et au-dessous (1,5 × 0,45 × 2,2 px, 64 par anneau), une marque gravée inventée tous les 8 segments ; liseré et filets `_e` bleutés ; toutes les lumières `add_` en blanc neutre à reflets bleutés (palette 34,42,66 → 128,148,192 → 208,218,240 → 255).

## Sons (à l'oreille, pour nos sons originaux)

Glissement métallique grave et chuintant pendant l'arrivée des anneaux, petits chocs sourds quand chacun se pose ; montée d'un bourdonnement puis onde brillante à l'éclair ; souffle métallique qui remonte au départ des anneaux.

### Mesures (2026-11-07, sons v2)

Analyse (spectres, enveloppes par bande à 10–25 ms, pics) d'une reconstitution 3D à la piste son propre (`yL2F_ZRUWAU`, 1,85–8,6 s) et de l'extrait 1 (`nhhBr7cvFpM`, 19,5–23,2 s, mêlé de musique). Rien n'est gardé dans le dépôt : seulement ces chiffres.

| Phase | Durée | Ce qui se mesure |
|---|---|---|
| Descente | ≈ 1 s avant les poses | ronronnement de machine : fondamentale **≈ 120 Hz**, partiels ≈ 240, **533** et 1 070 Hz ; bruit large bande dense 100 Hz–8 kHz |
| Pose de chaque anneau | 5 coups à **0,17–0,2 s** d'écart | coup sourd **≈ 55–60 Hz**, ≈ 0,1 s, +15 dB sur le fond, presque rien au-dessus de 1 kHz ; dans l'extrait 1, transitoires large bande (3–12 kHz) à 0,35–0,4 s d'écart, ton ≈ 390 Hz |
| Avant l'éclair | ≈ 0,5 s | le grave retombe (≈ −10 dB) ; sifflement en raies **≈ 3,7 et 4,9 kHz** |
| Éclair | ≈ 1,5 s | houle grave ≈ 50 Hz ; scintillement 4–8 kHz qui enfle puis s'éteint (centre de gravité du spectre de ≈ 1 à **≈ 3,5 kHz**) ; ton moyen ≈ 600 Hz |
| Retour | ≈ 1,5 s | le ronronnement ≈ 120 Hz revient, souffle 1,1–1,5 kHz ; bouffée aiguë ≈ 5 kHz à la fin |

### Recette de nos sons v2 (`effet_stellaire_anneaux/sons/`, v1 dans `sons/v1/`)

- `anneaux_descente` (2,2 s, poses à 0,65 s + 0,22 k) : ronronnement 120 Hz et partiels (×2, ×4,44, ×8,9) à grain de 31 Hz + lit de bruit 110–2 600 Hz et grondement 40–150 Hz (gain bas) ; par anneau, souffle qui glisse de 5,2 kHz à 800 Hz en enflant (0,34 s) puis « chlonk » : sinus 58 Hz qui tombe de 128 Hz (décroissance 75 ms), corps métallique inharmonique ≈ 392 Hz (×1,48, ×2,09, ×2,74), clic 2–10 kHz de 11 ms.
- `anneaux_eclair` (1,75 s, plus fort à 0,37 s) : fond de machine retombé ; sifflement en deux raies (rapport 1,317) qui monte de 1,5 à 3,7 kHz + souffle 0,7 → 6 kHz ; à l'éclair, houle 50 Hz + grondement de bruit 35–160 Hz + bruit moyen 250–3 500 Hz, souffle brillant 1,5–12 kHz ; puis scintillement 4–8 kHz qui frémit (bruit lissé à 35 Hz), crépitement 3–11 kHz, ton 608/912 Hz léger.
- `anneaux_retour` (1,8 s, départs à 0,05 s + 0,2 k) : ronronnement 124 Hz + lit de bruit ; par anneau, décrochage (65 Hz, clic, corps 392 Hz faibles) puis souffle qui monte de 800 Hz à 5 kHz, de plus en plus faible ; bouffée 3,5–7,5 kHz au dernier départ.
- Comparaison des spectrogrammes : `effet_stellaire_anneaux/.build/sons_comparaison.png` ; écoute du départ : `.build/ecoute_depart.wav`. Leçon de la v2 : la référence est **dense et large bande** ; nos premiers essais, faits de sinus purs, se lisaient en raies isolées et sonnaient « synthé » : il faut un lit de bruit filtré sous les tons.

## Traduction dans le mod (`effet_stellaire_anneaux`)

- Plaque au sol gravée (opaque, rainures ≥ 8 texels) avec lueur `add_` des rainures pendant la charge ; rideau de lumière qui monte du bord, poussière de lumière.
- 5 anneaux en vrais volumes (64 segments chacun, 5,6° entre voisins) : face extérieure en frise gravée de cartouches inventés, liseré lumineux haut et bas (`_e` + gaine `add_`), dessus nervuré. Ils descendent du ciel l'un après l'autre (choix : visible de loin en plein air, le ciel tient lieu de plafond), freinent avec un petit amorti, et repartent vers le ciel, le dernier arrivé d'abord.
- Éclair : bande `add_` qui remonte la colonne, colonne de lumière, faces intérieures allumées au passage de la bande, stries horizontales entre les anneaux (4 orientations), rayon qui jaillit vers le ciel ; la copie du joueur est cachée d'un coup au plus fort (échelle < 0,05, seule chose que le mod applique au départ).

## Sources

- Extraits vidéo étudiés (YouTube, basse résolution) : `nhhBr7cvFpM` (anneaux qui descendent du plafond, éclair qui monte, 12 im/s), `izo_wvZDD0U` (anneaux qui montent d'une fosse, faces intérieures allumées), `m8ze6Km90KM`, `yL2F_ZRUWAU` (reconstitutions 3D). Couleurs mesurées par seuils de luminosité sur les images à 640 × 360.
- gateworld.net (wiki « Transport rings ») : principe de l'échange entre deux plaques.
- Sons et couleurs v2 (2026-11-07) : mesures sur les pistes son et des images fixes des extraits ci-dessus (scripts d'analyse hors dépôt).
