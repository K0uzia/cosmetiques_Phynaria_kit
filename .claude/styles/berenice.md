# Style — Bérénice (thème Divin, ensemble Bérénice)

Ancien ensemble « Céleste », renommé le 2026-11-04 à la demande de l'utilisateur : `ailes_berenice` (ex-`aurelion_wings`), `diademe_berenice` (ex-`diademe_celeste`), `aura_berenice` (ex-`aura_celeste`). Nom des pièces : `<type>_berenice`.

Nom tiré de la constellation de la Chevelure de Bérénice : des **étoiles** et des **rayons fins comme des cheveux d'or**, autour de plumes ivoire. Design original, aucune référence à un personnage ou à un jeu.

## Esprit

Divin, lumineux, apaisé. Le sacré vient de la **lumière** (rayons, halo, poussière d'étoiles qui monte), pas de l'objet. Ivoire et or doux, jamais jaune vif ; le blanc est chaud, l'ombre est champagne, pas grise. Mouvements lents, amples, sans à-coup : tout flotte et respire.

Éléments-signatures : plumes rondes ivoire à pointe dorée (recette peau + âme validée), filets d'or, petites étoiles à quatre branches, rayons fins qui partent d'un point, halo en anneau découpé.

## Palette

| Matière | Clair | Base | Ombre | Usage |
|---|---|---|---|---|
| Ivoire | (255, 254, 250) | (244, 238, 224) | (150, 138, 116) | Plumes, pierre |
| Or doux | (252, 232, 176) | (232, 198, 122) | (176, 138, 78) | Liserés, bandeau, pointes |
| Lumière divine | (255, 250, 232) | (255, 226, 150) | (200, 150, 60) | `add_`, `_e`, rayons ; noir au bord en additif seulement |
| Bleu d'aube | (210, 228, 255) | (150, 180, 235) | | Touches discrètes (étoiles, cœur de halo), jamais en surface |

## Lumière et nuit

Sources nettes : la pierre du diadème, les pointes des primaires, le cœur du halo. Avec shader, `add_` et `_e` restent invisibles (bug du mod, `docs/dev/bugs_rendu_detail.md`) : doubler ce qui doit se voir avec shader par une version `trans_` plus discrète, ou une base claire dans la texture.

## Mouvement

Ailes : biomécanique d'oiseau (`.claude/rules/categories/ailes.md`), apparition par `event_equip` (les ailes se déploient depuis le dos) et retrait par `event_unequip`. Aura : la lumière monte et pulse lentement (4 à 8 s). Sons (2026-11-05) : sons embarqués originaux, tous en **mi majeur** pour que les trois pièces s'accordent quand elles s'équipent ensemble, un seul par pièce, à l'apparition (`tools/sons.py`) : ailes `souffle_plumes` (souffle d'air qui enfle avec l'ouverture de l'éventail, froissement de plumes, tintement de mi 6 très bas ; 1,3 s, clé à 0,75 s), diadème `carillon_celeste` (mi 6, sol dièse 6, si 6 en arpège de verre, tonique grave en halo ; 1,7 s, clé à 0,9 s, la pierre s'allume), aura `lueur_celeste` (nappe mi 5 + si 5 qui enfle avec la lumière, scintillements pentatoniques ; 2,0 s, clé à 0,8 s). Sources : `sons/<nom>.py` de chaque pièce. Avant : `block.amethyst_block.chime`.

## Effet de téléportation (`effet_berenice`, « Ascension de Bérénice », v2 du 2026-11-06, à revoir en jeu)

v1 : « pas mal pour un premier test d'effet de tp, mais ça manque un peu de visuel de particules et d'animation » ; consigne v2 : « être imaginatif et s'inspirer des animes ». Idée retenue : **des ailes de lumière enveloppent le joueur en cocon, qui s'élève et éclate en plumes** ; à l'arrivée, **le ciel s'ouvre** et il descend ailes déployées, qui se dissipent en plumes quand il se pose.

- **Cercle v4 (2026-11-06, « toujours bugué » : 8 arcs en « nid » en jeu)** : le cercle extérieur est **une plaque entière** de 36 px (`cercle` 212², lueur `cercle_g` 88²), motif invariant par miroirs et transposition (huit étoiles à 22,5° + 45°·k, seize points à 8° et 37° + 45°·k) ; anneaux des colonnes et du ciel à huit étoiles. À l'arrivée : rosace qui grandit (1,6–2,0 s), puis cercle extérieur de 0,3 à 1 avec fondu `ctrl_alpha` (1,85–2,45 s) et éclat des étoiles. Calibration de l'UV des faces horizontales : `docs/dev/tests_rendu/test_uv_up.bbmodel`.
- **Cercle v3 (retour en jeu du 2026-11-06 : « souci sur les cercles magiques »)** : rayon 18 px (2,25 blocs) ; tracé or en `trans_` (alpha ≤ 230 : visible de jour) avec `_e` (arcs × 0,26, rosace × 0,18) sous une lueur `add_` floue en basse résolution (`arc_g` 112 texels, `rosace_g` 96) ; trois filets pleins de 8 à 17 texels, huit grosses étoiles et seize points dans la bande, rosace à huit rayons épais. Même traitement pour le cercle du ciel (faces `down`, vu d'en dessous ; il s'efface avant le contact). Simulation à la taille en jeu : `.build/sim_jeu.py` (mipmaps par face, sol clair, nuit).
- **Charge** (loop 4 s, tout périodique, rien ne s'éteint) : cercle d'étoiles qui respire, huit étoiles `cam_` qui scintillent dans la bande sombre (pas au-dessus des étoiles peintes : cumul vu de dessus), deux anneaux qui montent du cercle, colonne basse et six rayons `add_` qui tournent (un tour par boucle), six plumes ivoire en spirale.
- **Départ** (3,6 s) : ailes de lumière qui jaillissent du dos et s'ouvrent (le cercle se contracte puis s'embrase), se referment en cocon (mains croisées devant le corps, lueur `cam_` devant lui), frémissent ; colonne pleine et vortex de rayons ; le cocon monte en accélérant (copie du joueur avec lui) et éclate à 2,1 s : étoile `cam_`, onde de choc horizontale, gerbe de seize plumes qui retombent en tournoyant ; la colonne se pince à l'éclat puis monte en fil et s'efface.
- **Arrivée** (4,5 s) : cercle magique en l'air (y = 50) qui s'ouvre avec un éclair ; colonne et rayons qui descendent ; joueur de y = 150 à 0 (posé à 3,0 s), ailes ouvertes autour de lui dès y ≈ 22 avec battement lent ; cercle qui se trace au sol ; au contact, ailes relevées puis dissipées en plumes, onde dorée au sol.
- **Ailes de lumière en `trans_`** (or pâle, alpha ≤ 235), pas en `add_` : en `add_`, les rémiges qui se croisent et les deux ailes vues de profil montaient à 460 de cumul. Bras + main + groupe `plie_` (repli de l'éventail dans le plan, appliqué avant la rotation de la main). Racines à x = ±6, z = 4,3 : en cocon, le bras passe derrière le bras du joueur (z ≥ 2,25). Calque `_e` limité aux rémiges (couleur × alpha × 0,38) et aux plumes ivoire (× 0,22) : visibles de nuit ; rien sous les plaques `add_`.
- **Particules** (26 points `emit_`, chacun avec son `ctrl_emit` animé, −1 à +7) : `plume` (bouts des ailes, cœur du cocon), `etoile` (cercle), `etincelle` (cocon, ras du sol), `lueur` (colonne), `emit_mc_dust_ffd27a_10` (cercle, racines des ailes). Les points de la gerbe sont dans un groupe `gerbe` jamais mis à l'échelle 0 (sinon ils tombent au sol) ; les ailes rétrécissent autour du haut du dos (`trans_ailes`, pivot (0, 24, 3,5)). Élan 0 % (effet posé au sol). Aide visuelle : `.build/aide_emit.py <opt> <copie>` marque les points actifs (couleur par sorte, trait le long de +Y), puis rendu `INSTANTS=` de la copie.
- **Sons originaux** (`sons/`, mi majeur) : `envol_celeste` (souffle qui monte, arpège de verre qui accélère, accord et étincelles à l'éclat ; clé à 0,4 s) ; `descente_celeste` (scintillement qui descend, deux battements d'ailes, cloche grave au contact ; clé à 1,8 s).
- **Cumul additif** (`.build/cumul_frais.py`, quads rechargés à chaque vue ; `AVEC_E=1` compte le calque `_e`) : ≤ 255 de face, de dos, de 3/4, de profil et de dessus, `_e` compris (248 vu de dessus à 1,2 s). Gains : lueur du cercle 0,20, rosace 0,16, anneaux 0,14, éclat 0,32, lueur de colonne 0,22, cocon 0,18. `.build/cumul.py` (v1) rend toutes les vues sur les mêmes quads : les vues suivantes héritent, semble-t-il, de l'orientation `cam_` de la précédente (écart mesuré 241 contre 274) ; ne plus s'y fier pour les vues après la première.
- À juger en jeu : densité et cadence des particules (`ctrl_emit` par point), lisibilité du cocon, ailes `trans_` vues de jour et de nuit, fondus `ctrl_alpha`, volume des deux sons.
