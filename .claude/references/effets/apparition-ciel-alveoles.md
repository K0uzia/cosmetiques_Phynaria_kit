# Apparition par un ciel d'alvéoles et du sang qui se condense

Grammaire visuelle d'une apparition « le monde lui-même parle » : le ciel se recouvre d'un plafond d'alvéoles, la lumière vire au rouge, un liquide sombre suinte des jointures et se condense en présence géante. Décrite plan par plan d'après une scène de référence fournie par l'utilisateur (non citée, consigne du 2026-11-06), puis traduite en version originale dans le mod (`effet_admin` v3). Aucun texte, logo ni glyphe de la référence n'est repris.

## Déroulé (plan par plan)

| Temps | Ce qu'on voit | Lecture |
|---|---|---|
| 1 | Ciel normal, nuageux, lumière chaude | calme avant l'annonce |
| 2 | **Une** alvéole hexagonale rouge-rose lumineuse apparaît, petite, dans le ciel | le signe : on lève les yeux |
| 3 | D'autres s'ajoutent en **grappe** serrée autour d'elle (6 à 8) | ça se propage |
| 4 | Elles **pavent tout le ciel** en vague, plafond en dôme vu en contre-plongée, et toute la lumière vire au rouge | enfermement, plus d'horizon |
| 5 | Gros plan : cadres clairs, fonds roses translucides, inscription sombre au centre, **jointures sombres** entre les cadres | l'ordre, le système |
| 6 | Aux jointures, un **liquide rouge sombre suinte** (gouttes qui pendent), puis une **grosse goutte** se forme au centre | le malaise : la machine saigne |
| 7 | La goutte pend et coule en **longs filets visqueux** (silhouette de méduse) | tension, attente |
| 8 | Les filets **s'ouvrent en couronne de pointes** recourbées autour d'une masse aplatie | éclosion |
| 9 | La masse se **solidifie en présence géante** qui flotte au-dessus de la foule, vue d'en bas, bras écartés | révélation, domination |

La référence dure plusieurs dizaines de secondes. Un effet de téléportation la compresse en 5 s : 1,5 s d'alvéoles, 1 s de sang, 1 s de révélation, 1,5 s de retour au calme.

## Formes et matières

- **Alvéole** : hexagone à côté plat, cadre clair épais (≈ 12 % du rayon), fond rose-rouge translucide plus clair au centre, signe sombre au centre. Jointure : un mince vide sombre entre les cadres. Grandes et nombreuses : vues d'en bas, elles se lisent par le rythme du pavage, pas par le détail.
- **Plafond** : un dôme bas, pas un plan (les bords descendent vers l'horizon) ; le pavage se lit mieux sur une courbe.
- **Sang** : rouge très sombre (≈ 100, 8, 18), reflet humide clair et étroit, jamais d'orange. Gouttes rondes, filets épais à la racine, effilés au bout, qui ondulent lentement (viscosité : rien de rapide sauf l'ouverture).
- **Couronne** : 8 à 14 pointes qui partent d'un anneau sous la masse aplatie et se recourbent vers le haut.
- **Lumière** : tout vire au rouge : sol éclairé en rouge, voile rouge derrière la scène.

## Mouvement et son

- Allumage : un clic par alvéole au début, puis la vague (impossible à suivre une à une) ; extinction en vague depuis le premier point.
- Sang : gonfle (respiration lente), pend (étirement), coule (cascade du haut vers le bas), s'ouvre d'un coup (dépassement), se rétracte.
- Sons : bips graves à deux tons qui se resserrent (alvéoles) ; écoulement épais et petites bulles qui descendent (suintement) ; inspiration grave qui enfle puis éclat mouillé (révélation).

## Mesures sur la scène (images extraites pleine taille, 2026-11-06)

- **Panneau** : hexagone **allongé**, côtés haut et bas plats et horizontaux, **pointes à gauche et à droite**. Largeur pointe à pointe / hauteur ≈ 2,7 (350 × 131 px sur un gros plan) ; chaque pointe ≈ 10–12 % de la largeur ; coins à peine cassés. Ce n'est pas un hexagone régulier.
- **Pavage** : colonnes de panneaux empilés, une colonne sur deux décalée d'une demi-hauteur ; pas entre colonnes = largeur − une pointe. Vu de loin, une quinzaine de panneaux dans la largeur du ciel : petits et très nombreux.
- **Palette** (pixels échantillonnés, plafond peu éclairé) : fond pêche-saumon au centre ≈ (252, 155, 115), plus rouge vers les bords ≈ (245, 115, 100) ; bande de bord rose-rouge ≈ (240, 90, 100) ; liseré rose lavande ≈ (255, 140, 178) de part et d'autre de la jointure ; jointure prune-mauve ≈ (205, 65, 85), épaisse d'environ 7 % de la hauteur ; petit motif d'alvéoles plus clair dans le fond ; texte rouge ≈ (205–230, 55–75, 40–60), une grosse ligne et une petite dessous. Sous la lumière rouge, tout tire vers (250, 100, 85).
- **Sang** : naît en **petites taches sombres aux sommets et le long des jointures**, qui grossissent et **remplissent les jointures** (bourrelets arrondis), puis pendent en **gouttes à bout renflé** et en filets qui s'étirent ; reflet clair étroit. Ensuite de longs filets lisses descendent du plafond et **convergent en bulbe** (oignon renversé), dont le bas se remplit en **masse arrondie** ; les filets s'élargissent en nappes luisantes. Couleurs : ombre ≈ (55–70, 15, 10), base ≈ (105, 30, 22), éclairé ≈ (175, 50, 45), reflet ≈ (255, 165, 135) : rouge brun très sombre, jamais orange.

## Traduction dans le mod (`effet_admin` v4)

- Panneaux : 217 hexagones allongés 11 × 4,2 px (rapport 2,62, pointes 12 %), pavés en colonnes décalées sur un dôme bas (y 46 → 58,5), 3 hauteurs (0,22 px) en coloriage axial pour que deux voisins ne soient jamais coplanaires ; texture 320 × 122 : palette ci-dessus, texte original « ALERTE / SYSTÈME » (police grasse, traits 10 et 8 texels). Texte orienté pour le joueur qui arrive (haut des lettres vers −Z), retourné par `tools/uv_horizontal.py` ; contrôle : `.build/controle_texte_jeu.png`, modèle « comme en jeu » `.build/effet_admin_commejeu.bbmodel`.
- Sang : veines aplaties le long des arêtes (face `down` découpée en bourrelets) et perles à 16 pans qui s'étirent en gouttes (Molang) ; 12 nappes de 14 segments autour d'un noyau à 16 pans : filets effilés vers le haut (échelles multipliées le long de la chaîne) qui convergent sous la masse, puis s'élargissent en poche fermée qui tremble ; déchirure = petite ouverture et fonte rapide du bas vers le haut (une grande ouverture se lit comme des tentacules ou une araignée).
- Comparaison aux mêmes instants : `.build/comparaison_scene_v4.png`.

## Traduction du sang, v6 (après le refus de la v5 en jeu)

- Un liquide se lit par une **silhouette ronde continue et un reflet doux**, pas par des pièces : poche en surface de révolution (32 × 40 facettes, profil d'oignon, fond fermé par une calotte), brins ronds sur ses méridiens, gouttes renflées aux sommets, bourrelets en demi-tubes sous les jointures, une seule peau peinte partagée.
- Mouvement : brins qui descendent en s'étirant (dépassement amorti), colonne fine qui gonfle en poche, tremblement anisotrope, goutte qui s'étire puis revient d'un coup quand elle se détache ; déchirure = la poche se vide vers le haut pendant que six filets tombent jusqu'au sol et font une flaque lisse (rien ne traverse la caméra du joueur au centre).
- Comparaison : `cosmetiques/effets/effet_admin/.build/comparaison_v6.png`.

## Traduction du sang, v7 (après « ballon de baudruche, effet plastique » sur la v6)

Recherche (peinture de sang et de liquide visqueux, 2026-11-07) : le sang n'est pas un rouge vif, il paraît presque noir là où il est épais et rouge profond là où il est mince ; ses reflets sont **très concentrés** (petits, nets) : un reflet trop large le rend métallique ou plastique, trop de reflets le rendent gélatineux, des clairs et sombres trop forts le rendent « cireux » et solide. Sources : [Painting blood step by step (CG Cookie)](https://www.deviantart.com/cgcookie/art/Tip%3A-Painting-Blood-Step-by-Step-408006854), [How do you paint blood? (CMON)](https://www.coolminiornot.com/forums/threads/how-do-you-paint-blood.258/), [Making blood look wet (Bolter and Chainsword)](https://bolterandchainsword.com/topic/306499-making-blood-look-wet), [Blood blood glorious blood (CMON)](https://www.coolminiornot.com/forums/threads/blood-blood-glorious-blood.8446/).

- Ce qui faisait plastique (captures v6) : œuf de révolution parfait, valeur claire uniforme (saumon de nuit), grand reflet doux du matcap `_m`, filets en tiges droites.
- v7 : `_r`/`_m` coupés ; masse ≈ (22–76, 3–9, 5–11), brins et filets ≈ (42–170, 4–26, 6–22) ; reflets en traits de 1–2 texels, cassés, blanc rosé (255, 222, 214) ; poche en oignon (col fin, ventre bas), bosses et deux lobes, axe qui penche ; 14 brins posés dessus ; 3 gouttes pendantes qui s'étirent ; balancement lent ; filets épais en haut, ondulés, renflés, cassés en gouttes qui tombent. `_e` rouge sombre (≈ 0,5 × la texture).
- Comparaison : `cosmetiques/effets/effet_admin/.build/comparaison_v7.png`.

## Historique de la traduction
### v3 (refusée : hexagones réguliers, palette, glyphes, sang en tentacules)

- Plafond : ≈ 140 plaques hexagonales `trans_` (texture 64 × 56 : cadre, fond alpha ≈ 170, glyphe original : losange et point d'alerte, œil, trois traits) sur un dôme y 44 → 59 (rayon 53, limite de 64 px), inclinées selon la normale du dôme ; lueur `add_` par alvéole pilotée par `ctrl_alpha` en Molang (`overlay_alveoles`, pulsation en vague) ; calque `_e` sur cadres et fonds. **Faces horizontales en miroir X dans le mod** : glyphes symétriques gauche-droite.
- Allumage par alvéole en une seule clé Molang d'échelle (`math.clamp((q.anim_time-on)/0.12,0,1)*math.clamp((off-q.anim_time)/0.16,0,1)`) : peu de keyframes.
- Sang : nœuds en prismes à 8 pans aux sommets proches du centre ; goutte en tranches à 16 pans (pans alternés à 22,5° contre les faces coplanaires) accrochée au plafond (pivot en haut : l'aplatir la remonte) ; 14 filets en chaînes de 6 prismes dont l'échelle Y s'ouvre en cascade, la racine pivote à ≈ 98° pour la couronne.
- La présence géante est **le joueur** (demande de l'utilisateur) : groupe vide `joueur` à l'échelle 1,35, pieds à y = 13 (tête sous la goutte, le plafond restant sous 64 px), puis descente à l'échelle 1.
- Piège : l'optimiseur ramène les clés à la grille de 1/24 s ; une marche (0 puis 1) doit avoir ses deux clés à ≥ 0,05 s d'écart, sinon elle disparaît.
