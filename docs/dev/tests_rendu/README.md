# Tests de rendu (à essayer en jeu)

## Menu Apparence et auras (2026-11-05, mod 1.4.0)

Premier essai (captures `20.36.18` = `a`, `20.36.20` = `b`) : le retournement de 180° est le bon sens, mais dans la vue de 3/4 du menu la lueur reste plaquée derrière le dos (liseré au bord de la silhouette). Second essai, fichiers régénérés :

1. `/cosmetique apercu test_menu_aura_a`, ouvrir le menu Apparence **sans toucher au personnage** : la lueur rouge doit entourer toute la silhouette comme en jeu (colonnes et disques derrière le corps, débordant autour de la tête, des épaules, des bras et des jambes), anneau au sol. Méthode : chaque groupe `cam_`/`camy_` est tourné vers la caméra par défaut du menu (lacet 30°, vue de 5° au-dessus, lus dans le mod).
2. Même chose avec `test_menu_aura_b` (ancienne méthode, 180°) : la lueur doit déborder surtout d'un côté (à droite de l'image), comme la capture `20.36.18`.
3. Faire ensuite tourner le personnage à la souris avec `a` : la lueur se décale de nouveau (limite connue : l'orientation est figée sur la vue par défaut ; vrai correctif demandé au mod, `docs/dev/demandes_mod_5.md` §1).
4. Renvoyer une capture de `a` et de `b` dans la vue par défaut. Fichiers produits par `gen_test_menu_aura.py` à partir d'`aura_brasier`.

## Orientation de l'UV des faces horizontales (2026-11-06, effet de téléportation)

Cercle de l'Ascension de Bérénice en 8 arcs : en jeu un « nid » de courbes (captures `15.58.36`–`15.58.49`), arcs supposés retournés dans leur plaque. Le test dira comment le mod oriente l'image d'une face `up` et d'une face `down` (jamais calibré).

1. Importer `test_uv_up.bbmodel` comme **effet** (`/puadmin skin import test_uv_up effect test_uv_up.bbmodel`), le porter, puis **Essayer** (onglet *Effets*) : il se joue sur vous à l'arrivée. Se tourner face au nord (F3 : « Facing: north ») avant d'essayer.
2. Photographier, en vue à la 3e personne de derrière, d'un peu au-dessus : **la plaque au sol** (une case, sous vos pieds) et **la plaque debout devant vous** (contrôle).
3. Regarder vers le haut et photographier **la plaque à 2,5 blocs au-dessus de la tête** (vue d'en dessous).
4. Ce qu'on lit sur chaque photo : vers où pointe la flèche (devant vous = attendu), où sont le coin **rouge** (attendu : devant à gauche) et le coin **bleu** (devant à droite), et si les lettres sont à l'endroit ou en miroir (« И » au lieu de « N »). Notre aperçu montre : sol, flèche vers l'avant, E à droite ; plaque debout lisible normalement de face.

Générateur : `cosmetiques/effets/effet_berenice/.build/gen_test_uv_up.py`.

**Résultat (captures `16.13.53`, `16.14.02`, `16.14.41`)** : faces `up` et `down` en miroir sur X par rapport à Blockbench (coin rouge du côté +X), `north` juste. Demande `docs/dev/demandes_mod_5.md` §5. Contre-épreuve : `test_uv_up_retourne.bbmodel` (UV des faces up/down retournées par `tools/uv_horizontal.py`) doit montrer en jeu le coin rouge du côté −X, comme Blockbench ; à refaire aussi quand le mod sera corrigé (il devra alors redevenir faux).

Tests 1 à 4 (`test1_shader` … `test4_particules_mc`) : `gen_tests_rendu.py`, résultats dans `docs/dev/bugs_rendu_detail.md`.
