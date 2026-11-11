# Style — Admin (thème Staff, ensemble Admin)

Pièces réservées au staff (`en_vente: false`, rareté mythique). Nom des pièces : `<type>_admin`.

Historique : `effet_admin` v1 « Faille hors du temps » **refusée** le 2026-11-06 (non documentée, plate ; `.build/gen_avant.py`). v2 « Avatar du Maître du Jeu » (manteau rouge et blanc géant, `.build/gen_v2_cape.py`) **abandonnée** : « tu as pas compris ce que je voulais, c'est toute cette scène que je veux », puis « toute la partie hexagone, le ciel rouge, le sang c'est ça qu'il faut ; ce qui apparaît c'est le joueur à la place ». v3 « Ciel d'alvéoles » refusée (« l'hexagone est pas le même », palette, texte, sang en tentacules ; `.build/gen_v3.py`). v4 : hexagones allongés mesurés sur la scène, « ALERTE SYSTÈME », sang liquide ; `.claude/references/effets/apparition-ciel-alveoles.md`. v5 en jeu (2026-11-06 22.42) : dôme validé, sang refusé (« pas lisse, pas fluide ») ; v6 : sang en surfaces lisses (`categories/effets.md`), v5 dans `.build/gen_v5.py` ; v6 en jeu (23.22) : « ballon de baudruche, effet plastique » ; v7 : sang presque noir, petits reflets nets, poche en oignon irrégulière couverte de brins, filets cassés en gouttes (v6 dans `.build/gen_v6.py`). L'autre piste (créature du néant) est `effet_admin_neant`.

Règle de l'ensemble (consigne de l'utilisateur, 2026-11-06) : version 100 % originale par analogie ; **aucune œuvre citée** dans le code, les fiches, le lore ni les rapports.

## Esprit

Le monde lui-même prend la parole : le ciel se couvre d'alvéoles écarlates, la lumière vire au rouge, du sang suinte des jointures et se condense, et c'est le joueur qui en sort, un instant géant. Solennel et inquiétant, jamais gore : pas de chair, pas de blessure, un liquide sombre et brillant.

Éléments-signatures : plafond en dôme d'alvéoles hexagonales (cadre clair, fond rose translucide, glyphes originaux : losange et point d'alerte, œil, trois traits) ; grosse goutte de sang sous le centre ; filets visqueux en méduse ; couronne de pointes ; joueur révélé géant ; lueur rouge au sol.

## Palette

| Matière | Clair | Base | Ombre | Usage |
|---|---|---|---|---|
| Cadre d'alvéole | (255, 208, 200) | — | filet (225, 178, 170) | `trans_` alpha ≈ 236 |
| Fond d'alvéole | (246, 120, 124) au centre | (226, 64, 80) | — | `trans_` alpha ≈ 170 |
| Glyphe | — | (118, 10, 26) | — | alpha ≈ 236 |
| Sang (v7) | (140, 22, 22) ; minces (170, 26, 22) | (76, 9, 11) ; minces (112, 12, 12) | (22, 3, 5) | opaque, reflets en petits traits (255, 222, 214), pas de `_r`/`_m` |
| Lumière (`add_`) | (255, 70, 64) × gain | — | — | lueur d'alvéole 0,26, sol 0,42, voile 0,2 |

## Mouvement et sons

Allumage : une alvéole, une grappe, puis une vague depuis le premier point ; pulsation des lueurs en vague (`overlay_alveoles`). Sang : gonfle, pend, coule en cascade, s'ouvre d'un coup, se rétracte. Sons embarqués originaux (`sons/*.py`) : `alveoles_alarme` (bips graves à deux tons qui se resserrent), `sang_suinte` (écoulement épais, bulles), `sang_revele` (inspiration grave, éclat mouillé). Rien pendant la charge.

## Taille

v5 (2026-11-06, limite de 320 px au repos ; consigne « hauteur max et taille max pour les hexagones ») : dôme y 222 → 300, rayon 280 (17,5 blocs), 145 panneaux de 72 × 27,5 px (4,5 × 1,7 blocs) ; poche de y 299 à 60 (le joueur qui arrive la voit d'en dessous) ; joueur révélé `ECHELLE_GEANT` 6,2, pieds à `Y_GEANT` 80 (tête à y ≈ 278), visible seulement après la déchirure, puis descente à l'échelle 1 ; lévitation de 3 px pendant la charge. v4 (64 px) : `.build/gen_v4.py`, `.build/v4_livrable.bbmodel`. Vues de contrôle : `.build/vues_v5.py` (œil, témoin à 10 blocs, loin), comparaison `.build/comparaison_scene_v5.png`.

## Sources

`.claude/references/effets/apparition-ciel-alveoles.md`, `principes-fx-anime.md`.
