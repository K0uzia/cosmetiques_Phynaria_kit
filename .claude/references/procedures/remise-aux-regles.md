# Règles — remettre une pièce existante aux règles actuelles

À lire à la demande (déplacé de `.claude/rules/` le 2026-11-06 pour ne plus être chargé d'office). Règles : `.claude/rules/` ; avis de l'utilisateur : `.claude/rules/retours-en-jeu.md` (index) et `.claude/rules/categories/`.

Procédure éprouvée le 2026-11-04 (ensembles Bérénice et Givre). À suivre pour toute pièce livrée avant les dernières règles.

## Avant de toucher

1. Lire `.claude/rules/retours-en-jeu.md` et le fichier de la catégorie (`.claude/rules/categories/`) : ce qui est **validé en jeu ne change pas de design** (forme, palette, proportions validées) ; on corrige seulement ce qui viole une règle. Ce qui a été refusé ne revient pas.
2. Lire la fiche de style de l'ensemble (`.claude/styles/<ensemble>.md` ; la créer si elle manque, d'après le générateur et les retours) et les fiches de `.claude/references/` du sujet (animal, créature, effet). Chercher sur le web ce qui manque et écrire la fiche manquante.
3. Garder l'ancien générateur et l'ancien livrable dans `.build/gen_avant.py` et `.build/avant_livrable.bbmodel`. Renommer est permis (rien n'est figé en jeu, 2026-11-05), mais en une seule passe et jamais pendant qu'un sous-agent travaille sur la pièce : convention `<type>_<ensemble>`, variante seulement si deux pièces du même type.
4. Mesurer d'abord (taille, extension, faces proches, distance à la tête et au corps, cumul additif), corriger ensuite.

## Liste de contrôle

| Point | Règle | Mesure |
|---|---|---|
| Faces proches | Deux faces parallèles qui se chevauchent : ≥ 0,1 px, faces opposées comprises (« texture qui clipe ») | script `mesure_faces.py` (ex. `cosmetiques/chapeaux/diademe_berenice/.build/`) sur la pose de base et les poses principales, cible 0 |
| Tête | Face intérieure à ≥ 4,62 px du centre (seconde couche du skin à 4,5) ; rien en porte-à-faux devant le visage | idem, toutes animations |
| Ailes | Taille, racine, apparition sans sac permanent : `.claude/rules/categories/ailes.md`, Anatomie d'aile | envergure par état |
| Rotations continues | Dans un `overlay_` (`.claude/rules/animation.md`, Boucles) | — |
| Sons | `.claude/rules/essentiel.md`, Méthode (`tools/sons.py`) | — |
| Lumière | Sources nettes (`.claude/rules/essentiel.md`, Méthode) ; **pas de `_e` sur une pièce tout en `add_`** ; cumul additif ≤ 255 (mesuré sans plafond) | `NUIT=1`, script de cumul (`aura_berenice`) |
| Shader | `.claude/references/mod/rendus-avances.md` | — |
| Particules | Rien qui tombe et se pose hors des ailes ; pas d'`end_rod` ; étoile ou flocon modélisés ≤ 0,8 px, Élan 100 % ; `reglages.json` | — |
| Aura | Lumière, pas objets en orbite, pas de feu à contour sombre (`.claude/references/effets/auras.md`) | — |
| Familier | Vivant (`.claude/styles/familiers.md`) : regard, comportements au hasard, réactions ; **mode familier du guide** (6.6 : bloc `familier` dont le mode suit son type, `sol`, `vol`, `nage` ou `perche` ; animations `pet_` ; `event_owner_hurt`, `q.owner_*` ; plus de groupe `body` ni de contre-rotation) ; modèle organique (`.claude/references/familiers/modelisation-organique.md`) | Vérificateur (bloc, noms `pet_`, groupes du corps) ; suivi en jeu seulement |
| Fiche | `phynaria.fiche` embarquée (guide 10 bis) depuis `fiche.json` | Vérificateur (longueurs, rareté) |
| Texture | HD ≈ 24–40 texels/px, vrais volumes ; pas de pixel art 1:1 ni de décalque plat | densité médiane |
| Réactions | Pas d'`attack` ni de `hurt` sur une pièce portée (tête, épaules, queue, sac, aura) ; arme : `attack` seul ; ailes et familiers portés : les deux ; familier vivant : `event_owner_hurt` (`.claude/rules/animation.md`). `tools/reactions.py` (`retirer_reactions(model)`) avant l'écriture | — |
| Apparition | `event_equip` court qui a du sens (la pièce pousse, s'allume, se déploie) | — |
| Menu Apparence | Depuis le guide du 2026-11-06 soir, le mod oriente `cam_`/`camy_` dans le menu : rien à cacher ni à tourner par `q.is_in_menu`. `adapter_menu()` (`tools/menu_aura.py`, `ADAPTER_MENU = False`) retire seulement les anciennes cachettes (`1-q.is_in_menu`, `menu_seul`) ; historique du contournement `vm_` : `.claude/references/mod/rendus-avances.md` | Plus de groupe `vm_` dans le livrable ; aucune expression `is_in_menu` restante (`menu_aura.resume(model)`) |

## Leçons des passes (2026-11-05)

- **Hauteurs de contact** : une pièce posée sur le dessus de la tête touche à y ≥ 32,62 ; une pièce posée sur l'épaule part de y ≥ 24,35 (seconde couche du bras à 24,25).
- **Écarts** : viser 0,22 px entre pièces voisines (0,20 donne 0,0999 après arrondi). Bouts et dessus internes de segments qui se chevauchent : UV sur un texel transparent.
- **Dômes et anneaux** : plaques réparties à pas de normale constant, dôme terminé par un dessus plat ; un dôme en pavés croisés empilés crée des faces proches à chaque étage.
- **Tige translucide** : 8 facettes `trans_` peintes d'un seul côté autour d'une âme opaque, pas deux cubes croisés à 45°.
- **Rotations** : `euler()` (ordre Rz·Ry·Rx) des vieux générateurs perd l'angle X à Y = ±90° (barres le long de ±Z sans leur roulis de 45°, facettes aplaties) : ajouter un contrôle de reconstruction dans chaque générateur.
- **`ctrl_emit` multiples** : exactement le même nom.
- **Outils de mesure** : `mesure_faces.py` de `cosmetiques/armes/lame_givre/.build/` (accepte animation et instant, variables `MA`/`MT`) ; `cosmetiques/armes/baguette_patisserie/.build/qui_faces.py` nomme les éléments de chaque paire trop proche.
- **Tronçons d'un même os** : le recouvrement de 0,1–0,12 px entre tronçons de même texture continue est toléré (validé en jeu sur `ailes_abyssales`) ; une chaîne droite de rayon constant (sangle) se fait bout à bout (`ov = 0`).
- **Barre octogonale** (`bar`) : rentrer le cube à 45° de 0,1 px aux deux bouts (0,03 px confond ses faces de bout avec celles du cube droit).
- **Anciennes pièces de tête** (posées à 4,3–4,45 px, dans la seconde couche) : décaler la distance de base, ou agrandir toute la pièce autour de (0, 28, 0), sans refonte.
- **Plaques de 0,3 px qui se recouvrent** : écart de 0,1–0,2 px ou ≥ 0,4 px ; 0,3 px met la face d'une plaque dans le plan de la face opposée de l'autre.
- **Ailes réduites par K** : les pointes repliées remontent ; une aile au poignet haut (chauve-souris) ne revient aux mollets qu'en refaisant la pose de repos.
- **Mesurer toutes les poses** : une échelle non uniforme ou une aile qui s'ouvre rend coplanaires des faces séparées au repos. Rangées de plumes : décaler sur un cycle de trois (une sur deux ne suffit pas, un escalier aggrave). Deux ailes rigides qui pivotent en Y : décaler aussi les pivots en x (le décalage z s'annule à la fermeture). Plaques autour d'un pli : écart ≥ 0,1 + R·sin 3°.
- **Pièce cachée dans les états, montrée dans un événement ou à l'attaque** : `ctrl_alpha` −1 dans les états, +1 dans l'événement ou `attack` ; pas une échelle 0 dans l'état (elle ne se défait pas) ni une échelle de parent presque nulle (le vérificateur mesure alors jusqu'à 275 px d'extension).
- **Coque `trans_`** : creuse ; une âme opaque se voit au travers.
- **Distance à la tête** : la contrôler aussi pendant le dépassement d'échelle de `event_equip`. Aile de papillon réglementaire : son bord avant ne monte pas avant x ≈ 6,5.
- **Haut-de-forme et bord de chapeau** : trou dans le bord, face intérieure ≥ 4,62, y compris aux coins coupés (|x| + |z| ≥ 9,24 sur la face intérieure).
- **Pièces de corps** (platine de queue, brassard) : ≥ 2,37 px du centre du torse ou de l'axe du bras (seconde couche du skin à 2,25).
- **Écarteur automatique de faces** (`decoller()`, `cosmetiques/chapeaux/haut_de_forme_steampunk/gen_haut_de_forme_steampunk.py`) : efficace sur les structures épaisses ; au-delà de ~0,15 px de déplacement il déforme les petits joints serrés : les figer ou les redessiner.
- **Vapeur Steampunk** : `emit_mc_white_smoke` avec `ctrl_emit` −1 au repos et +4/+5 à la décharge (jet au moment exact), réintroduit le 2026-11-05 ; à juger en jeu.
- **`_e` et ambiance** : `ajouter_ambiance` multiplie un `_e` existant par 2,4 (puis écrête à 225) et `ctrl_lumiere` par 1,3–1,8 : un vieux `_e` pèse en jeu jusqu'à ~1,25× l'additif, et un vert vif (132, 255, 72) blanchit : peindre environ (34, 88, 22). Une pièce validée en jeu garde sa **luminosité perçue** (le plafond de 255 sert à éviter un blanc saturé qui gêne, pas à assombrir ce qui a plu) ; le cumul se mesure aussi de profil.
- **Anneaux en barres bout à bout** : couper les bouts pour qu'ils se rejoignent au coin intérieur.
- **Pièce sans générateur** (`ailes_tentacule`) : générateur qui fige la géométrie d'origine (chaîne compressée) et applique les corrections par-dessus.
- **Chaîne de prismes qui plie** : la face dont la normale suit l'axe du pli reste coplanaire avec sa voisine à tout angle ; torsion alternée de ±6° autour de l'axe (≥ 3° d'écart) ou rayons différents de 0,1 px.
- **Plaques additives** : une seule face texturée (deux faces comptent la lueur deux fois : 620 contre 188 mesurés).
- **Halos `cam_` voisins** : profondeur unique par face (à recul égal, leurs plans coïncident face à la caméra).
- **Deux armes animées ensemble** : mesurer la distance entre les bras pendant l'attaque (le test de faces parallèles ne voit pas une intersection oblique).
- **Doubles signes Molang** (`1--x`, `1+-x`) : `optimize_bbmodel.py` les normalise (2026-11-05) ; ils cassaient la visionneuse et le parseur du mod n'a jamais été vu dessus. Écrire les bons signes dans le générateur (`f"{1+a:+}"` plutôt que `f"1-{-a}"`). Renderer et visionneuse partagent maintenant un même parseur Molang (`&&`, `||`, `!`, `?:`, `return`, `t.`, valeur neutre si invalide).
- **Livraisons en parallèle** : `livrer.py` peut dépasser 10 min quand plusieurs tournent : pas de limite de temps courte.

## Livrer

Vérificateur vert, rendus regardés en pleine taille, `tools/livrer.py`, planche regardée (`.claude/rules/delivery.md`, `.claude/rules/essentiel.md`). Rapport : avant/après chiffré, ce qui est validé et n'a pas bougé, mesuré vs supposé, 2–3 points à vérifier en jeu.
