# Sets complets en objets — suivi (2026-11-08)

Demande de l'utilisateur (mot pour mot) : « 7. va si, refait les ailes de d'orage je n'aime pas dutout, complete chaque set qui ont des ailes en objets donc tu fait tout les outils et armes de vanilia de minecraft épée arc masse lance arbalette pioche pelle hache houe bouclier je crois c'est tout »
Réponses : **un agent à la fois** (pas de parallèle), todo à jour pour reprendre si le PC est coupé ; Bérénice et Tentacule inclus ; trident et canne à pêche inclus (12 types du guide §14) ; ailes d'orage : « aile d'oiseau en métal + éclairs ». Pâtisserie exclue (pas d'ailes).

## Reprise après coupure
**Pour une nouvelle session (2026-11-08, ~22 h)** : lire ce fichier, puis `brief-revue-2026-11-08.md`. Un agent à la fois (consigne de l'utilisateur). Prochaine pièce : la première case `[~]` ou `[ ]` (langage du set sous `### Abyssal`). Pour chaque pièce : agent neuf avec un brief court qui renvoie à ce fichier (Brief objets + Langage du set + recette `.claude/references/objets/volume-3d.md` + pièges de `categories/objets.md`), puis regarder soi-même la planche (ou la comparaison pour une refonte), cocher avec une ligne de bilan. À l'utilisateur : `docs/dev/demandes_mod_7.md` est à envoyer au développeur ; ses fichiers en jeu étaient d'anciennes versions (réimporter `livrables/`). Rien n'est commité.
Prendre la première case `[ ]` (« refaire en 3D » : garder design, nom et animations, refaire lames/fers/branches en vrai volume selon `.claude/references/objets/volume-3d.md`). Si une case est `[~]` (en cours), regarder son dossier : livré (`apercu/planche.png` récent et vérificateur vert) → regarder la planche puis cocher ; sinon relancer un agent neuf sur cette pièce (garder ce qui existe dans `.build/`). Une ligne de bilan par pièce après la case. Brief commun : `brief-revue-2026-11-08.md` + section « Brief objets » ci-dessous.

## Brief objets (en plus du brief commun)
- Lire `.claude/rules/categories/objets.md`, `tools/objet.py` (préréglages Display par type), guide §14, et **les objets déjà livrés du même set** (`cosmetiques/objets/skin_*_<set>/fiche.json` + `apercu/planche.png`) : même langage de matière, de couleurs et de lumière, chaque objet reconnaissable du set sans la couleur. Regarder aussi les ailes du set (pièce phare).
- Proportions de l'objet vanilla respectées (prise en main, 1re personne), distance ≤ 64 px au repos ; animations vivantes du guide (`item_idle/use/swing`, événements) avec sons rares.
- Nom : `cosmetiques/objets/skin_<type>_<set>/`. Fiche avec nom, ensemble, lore cohérent avec `cosmetiques/ensembles.json`. Ne toucher à aucune autre pièce.
- Bérénice : ne rien modifier aux pièces existantes du set. Cuir : latex noir brillant + chrome, rien de gothique. Tentacule : chair, ventouses, œil d'ambre (fiche `creatures/cephalopodes-tentacules.md`).

- **Échelles superposées** : `event_swing` et `event_hit` (et l'état) jouent ensemble, leurs échelles se multiplient : un groupe n'est déplié (échelle) que par **une seule** animation ; les autres n'y touchent pas. Le vérificateur l'alerte (« échelles superposées », WARN, avec le cumul mesuré).

- **Sons et événements (diagnostic F5, code du mod)** : jamais de clé de son à 0,0 s (muette au premier passage) → 0,04 s au moins ; aucun son sur `event_use_start` ni `event_enter_<étape>` (rejoués quand le mod croit l'objet lâché) ; bouclier : pose de garde aussi dans `item_idle` ; flèche, carreau, flotteur et ligne ne sont pas personnalisables ; trident lancé : attendre le développeur pour l'orientation de `lance`. Détail : `categories/objets.md`, « Retour en jeu 2026-11-08 soir ».

## Tâches
Outil à corriger plus tard : `livrer.py` annonce `apercu/jeu.png` pour les objets mais ne le crée pas (houe, lance, arc abyssaux).
- [x] F7 Mise à jour du guide (2026-11-08 21 h 38) → demandes 6 toutes appliquées, aucune des demandes 7 (à envoyer) ; objets inchangés ; règles, renderer, visionneuse et vérificateur mis à jour (copie du départ à l'échelle, add_ × alpha, mipmaps).
- [x] F8 Effets touchés par le guide : `effet_vortex` (`COPIE_ECHELLE_LUE = True`, l. 724, relivrer), relivrer les aperçus de tous les effets (renderer changé) ; `effet_admin` (copie géante ×6,2 maintenant appliquée) à revoir en jeu.
  → fait : vortex relivré (copie qui rétrécit au centre), 9 autres effets relivrés, vérificateur OK ; effet_admin : copie géante cachée dans la poche et le dôme de 3/4, visible peut-être de dessous (à voir en jeu).
- [x] F6 Correctifs F5 (recettes dans `categories/objets.md`, section « Retour en jeu 2026-11-08 soir ») : boucliers Orage/Givre/Cuir (garde aussi dans `item_idle`, plus de son à `event_use_start`), cannes Orage/Cuir (plus de son à `event_enter_lancee`), clés de son à 0,0 s → 0,04 s (`event_release` arc/arbalète/trident Orage, trident Givre, tous les `event_hit` à 0,0). Tridents lancés : attendre le développeur (`docs/dev/demandes_mod_7.md`).
  → fait : 24 pièces relivrées (garde dans item_idle, sons retirés de event_use_start/event_enter_lancee, clés de son 0,0 → 0,04 s) ; tridents lancés non touchés.
**Retour en jeu (2026-11-08 soir, set Orage complet testé)** : « c'est styler mais niveau sonore et animations y a des soucis par exemple quand ont bloque avec le bouclier ca bug ca reste pas en garde ca fait que s'enlever et ce remettre et le sons spam, pareil pour la canne a peche quand ont lance pour pecher le sons spam et le flotteur et fils sont pas custome, pour les arme a distance pareil la fleche tirer es pas custom et le sont je pensais que c'etait quand ont tirer la fleche mais non c'est que quand la fleche touche une entité ».
- [x] F5 Diagnostic (guide §14 + code du mod) : bouclier qui ne tient pas la garde + son en boucle ; canne : son en boucle au lancer ; arc/arbalète/trident : son joué à l'impact sur une entité au lieu du tir ; flèche, flotteur et ligne non personnalisés (possible ou demande au développeur ?). Puis correctifs sur toutes les pièces touchées (boucliers, cannes, arcs, arbalètes, tridents de tous les sets).
  → diagnostic fait (code du mod 1.4.0) : utilisation et étapes comparées par identité de la pile, chaque coupure rejoue `event_use_start`/`enter_<étape>` et relance `item_use` (fondu 200 ms) : garde qui retombe et sons répétés (déclencheur supposé côté serveur) ; clés de son à 0,0 s muettes au premier déclenchement ; rien à l'impact (son entendu = vanilla) ; flèche/carreau/flotteur/ligne non personnalisables ; trident lancé : +X = sens du vol dans le code (guide : +Y). Recettes et liste par pièce : `objets.md`, « Retour en jeu 2026-11-08 soir » ; demande `docs/dev/demandes_mod_7.md`.
**Retour en jeu (2026-11-08 14 h 22, captures `14.22.36` à `14.22.59`)** : « pour les items faut revoir les modèles, c'est pas 3D, c'est des couches, ce qui pas ouf ; faut te baser sur les modèles Minecraft ou d'autres qui existent peut-être sur le web pour avoir de vrais modèles 3D, pas des couches empilées ; le manche de l'épée par exemple est bien ». Constat sur les captures : lames et fers = plaques plates empilées (bord, bande, fil), lisibles comme des feuilles par la tranche ; les manches en volume (fusée tressée, bagues) sont bons. **Toutes les pièces d'objets attendent la recette 3D (F3)** ; les objets déjà livrés seront refaits après validation.
- [x] F3 Recette « vrai volume » des objets + prototype sur `skin_epee_orage`, à faire valider par l'utilisateur avant de continuer la liste.
  → prototype livré (section hexagonale, biseaux inclinés à 40°, gouttière creusée ; 415 cubes, 97 Ko), recette `.claude/references/objets/volume-3d.md`. **Validé en jeu** (15 h 05 : « c'est bien mieux »). Suite : refaire en 3D tous les objets livrés avant la recette (cases `[ ] … (refaire en 3D)`), puis la liste.
- [x] F1 `skin_epee_orage` : arcs dépliés à la fois par `event_swing` et `event_hit` (échelles multipliées → ×100 au coup qui touche) ; corriger (signalé par l'agent de la pioche).
  → corrigé : un jeu d'arcs par événement, pire cumul ×1 000 → ×10 (= ×1 replié) ; 289 cubes, 77 Ko.
- [x] F2 Même défaut possible ailleurs (scan : `skin_arc_kawaii` coeur, `skin_bouclier_cuir` éclats, `skin_bouclier_givre` crêtes, `skin_masse_patisserie` creme/cage, `skin_pelle_patisserie` nappage) : alerte du vérificateur + correctif là où le cumul est réel.
  → alerte « échelles superposées » ajoutée au vérificateur ; corrigé `skin_bouclier_cuir` (×5,8 → ×2,4) ; autres ≤ ×1,3, laissés. `familier_abyssal` signalé (cumul improbable), non touché.
- [x] T1 Bérénice — appliquer les 2 propositions validées : `aura_berenice` (`reglages.json` : durée sur un pas du guide, rafale « À l'attaque » → Aucune) ; `effet_berenice` (charge alignée sur le compte à rebours de 3 s, la pose ne doit plus sauter ; vérifier que le cocon `trans_` ne cache pas la lumière `add_`). Rien d'autre.
  → fait : aura durée 3 s, rafale Aucune ; charge 3 s, plumes sans saut ; lueur du cocon avancée (encore cachée de profil). Planches regardées.
- [x] T2 `ailes_orage` v7 — « je n'aime pas du tout » la v6 (ailes faites en traits d'éclair). Direction choisie : **vraie aile d'oiseau à plumes de métal sombre forgé**, foudre qui court sur les bords et les rémiges. Garder l'anatomie, silhouette propre (pas celle du givre), ne se croisent jamais.
  → v7 livrée : aile de faucon en acier forgé bleu-noir, liserés cuivre/or, âme de foudre, décharges au hasard épaule → pointes ; 547 cubes, 151 Ko. Comparaison regardée.

### Orage
Langage : ailes v7 (acier forgé bleu-noir martelé, fil poli clair, bande cuivre/violet de trempe, liseré or, âme de foudre au centre des lames, virgules d'or ponctuelles ; foudre en géométrie cœur clair + `_e`, gaine `add_`, née d'une pointe ou d'un fer). Famille des outils (épée, pioche, pelle) : tambour d'or à trois virgules, fusée de cuir bleu nuit entre bagues d'or, pommeau à pointe de cristal, fente en zigzag où court la foudre, arcs repliés à 1/10 au repos.
- [x] `skin_epee_orage` — « Lame du tonnerre », 199 cubes, 66 Ko, planche regardée
- [x] `skin_pioche_orage` (refaire en 3D) — « Pic de l'orage », 212 cubes, 61 Ko, planche regardée — refait en 3D : fer biseauté (pente 52°), gouttière creusée, 345 cubes, 87 Ko ; comparaison regardée
- [x] `skin_hache_orage` (refaire en 3D) — refaite en 3D : fer biseauté 1,6 → 0,6 px, gouttière, frange corrigée ; 271 cubes, 84 Ko ; comparaison regardée
- [x] `skin_pelle_orage` (refaire en 3D) — « Pelle de l'orage », 222 cubes, 74 Ko, planche regardée — refaite en 3D : cuillère creuse 1,56 → 0,56 px, biseaux 40°, gouttière ; 333 cubes, 89 Ko ; comparaison regardée
- [x] `skin_houe_orage` (refaire en 3D) — « Houe de l'orage », 233 cubes, 63 Ko ; lame vue par la tranche en inventaire, à juger — refaite en 3D : col octogonal, lame biseautée tournée de 28° (plat visible en inventaire) ; 398 cubes, 92 Ko ; comparaison regardée
- [x] `skin_lance_orage` (refaire en 3D) — refaite en 3D : fer de cristal biseauté hexagone→losange, cristal opaque (fiche dit encore « translucide »), 566 cubes, 121 Ko ; **sans animations vivantes** (pièce ancienne) : à ajouter plus tard
- [x] `skin_arc_orage` — « Arc de l'orage », branches en ailes de faucon en volume, corde qui se charge, 1 051 cubes, 145 Ko ; planche regardée
- [x] `skin_arbalete_orage` — « Arbalète de l'orage », faucon qui plonge, ailes d'acier en volume, 1 546 cubes, 199 Ko ; vues de volume regardées (étrier d'or un peu chargé)
- [x] `skin_trident_orage` — « Trident de l'orage », fourche biseautée 52°, arcs entre les pointes levé, 867 cubes, 159 Ko ; préréglage _TRIDENT ajouté à tools/objet.py ; planche regardée
- [x] `skin_bouclier_orage` — « Écu de l'orage », ailes repliées autour du tambour, bombé, 1 526 cubes, 241 Ko ; blocage en Molang (technique givre), décharge sur q.hit_by_entity / usure ; vues regardées
- [x] `skin_masse_orage` (refaire en 3D) — refait en 3D : pièces rondes en plaques de révolution (16 pans), gouttière autour du tambour ; 919 cubes, 103 Ko ; bug euler() à ±90° corrigé ; comparaison regardée
- [x] `skin_canne_orage` — « Canne du paratonnerre », moulinet tambour, scion qui s'affine, 1 367 cubes, 135 Ko ; préréglage _CANNE corrigé (3e pers. du jar (0;4;2,5)) : à vérifier sur skin_canne_cuir à sa refonte ; planche regardée. **Set Orage complet (12/12).**

### Givre
Langage : `.claude/styles/givre.md` ; épée refaite en volume = référence du set (glace : peau `trans_` mince sur âme opaque de même forme, bande transparente au fil ; flocons en relief en barres à section losange, gemme hexagonale `_e` ; fusée bleu nuit cloutée ; cristaux hexagonaux pointus).
- [x] `skin_epee_givre` (refaire en 3D) — refaite en 3D : lame hexagonale, peau trans_ sur âme opaque, garde en flocons en relief ; 303 cubes, 60 Ko ; comparaison regardée
- [x] `skin_pioche_givre` — « Piolet de givre », pic à dents + panne, glace peau/âme, 620 cubes, 106 Ko ; planche regardée
- [x] `skin_hache_givre` — « Hache de givre », hache barbue du nord, fougère de givre lumineuse, 453 cubes, 94 Ko ; planche regardée
- [x] `skin_pelle_givre` — « Pelle de congère », pelle à neige en auge, poignée en T, 576 cubes, 118 Ko ; planche regardée
- [x] `skin_houe_givre` — « Houe de givre », lame en croissant tournée de 34°, 452 cubes, 85 Ko ; planche regardée
- [x] `skin_lance_givre` — « Lance de givre », fer en losange à quatre biseaux, oreilles de cristal, collier d'épines à la charge ; 570 cubes, 79 Ko ; petits traits blancs aux raccords des facettes (non corrigés) ; vues regardées
- [x] `skin_arc_givre` (refaire en 3D) — refait en 3D : branches courbes biseautées 50°, peau/âme, flocon en relief ; 2 360 cubes, 253 Ko ; traits blancs des raccords corrigés (peau qui déborde de 0,05 px) ; comparaison regardée
- [x] `skin_arbalete_givre` — « Arbalète de givre », arc court en glace, fût d'argent, carreau givré chargé ; 3 791 cubes, 374 Ko ; planche regardée
- [x] `skin_trident_givre` — « Trident de givre », croissant d'argent + trois dents de glace hexagonales, 1 182 cubes, 143 Ko ; planche regardée
- [x] `skin_bouclier_givre` (refaire en 3D) — refait en 3D : glace en facettes sur âme, orle roulé, umbo bombé ; son de event_use_start retiré ; blocage en attente du diagnostic F5 ; 925 cubes, 198 Ko ; comparaison regardée
- [x] F4 `skin_lance_givre` : traits blancs aux raccords de la peau de glace → appliquer le correctif de l'arc de givre (chaque tronçon de peau déborde de 0,05 px sur le précédent) — fait, gros plan avant/après regardé
- [x] `skin_masse_givre` — « Masse de givre », grappe de cristaux sur noyau d'argent, 1 255 cubes, 139 Ko ; son à 0,04 s ; planche regardée
- [x] `skin_canne_givre` — « Canne de banquise », canne de pêche sur glace, moulinet à flocon, 1 101 cubes, 118 Ko ; son sur event_swing à 0,04 s ; planche regardée. **Set Givre complet (12/12).**

### Abyssal (Démoniaque)
Langage : os charbon taillé (plat d'os marbré (30,25,40)→(58,50,72), biseaux plus sombres (14,10,20), arêtes et lèvres en liseré violacé (126,92,170), reflet (98,68,126) au milieu des dos et des pans) ; cuir pourpre-noir enroulé en spirale (84,44,98)→(38,18,48) à clous d'os pâle (168,150,176) ; **vert acide seulement au fil, dans les gouttières creusées et aux pointes** (fil (190,255,96) + `_e` (82,211,53), veines (96,200,44) qui montent du fil, halo sombre (22,66,40)) ; ornements récurrents : griffes recourbées en tours coniques à pointe verte + `_e` (garde, pommeau, éperon), bagues d'os violacées, collet d'os ; pas de métal, d'or ni de rouge ; vivant sobre : griffes qui respirent, fil qui souffle (`ctrl_lumiere`), un seul son (`block.sculk.break`, 0,04 s) au coup qui touche. Référence : `skin_epee_abyssal` (vrai volume).
- [x] `skin_epee_abyssal` (refaire en 3D) — refaite en 3D : sabre à un tranchant, biseaux 32°, gouttière verte, garde en tours ; 634 cubes, 81 Ko ; comparaison regardée
- [x] `skin_pioche_abyssal` — « Pic de l'Abysse », deux crocs d'os en croissant, vrai volume (pente 51°, gouttière verte), 604 cubes, 89 Ko, aucun WARN ; planche et vues de volume regardées (bords des biseaux un peu crénelés de près)
- [x] `skin_hache_abyssal` (refaire en 3D) — refaite en 3D : fer en plaque biseautée fermée (40°, 1,60 → 0,54 px), gouttière en croissant, marteau octogonal ; 576 cubes, 81 Ko ; comparaison regardée (fil vert plus fin qu'avant, à juger en jeu)
- [x] `skin_pelle_abyssal` — « Pelle de l'Abysse », fer en omoplate d'os à bout rond, plaque biseautée 40°, gouttière axiale ; 579 cubes, 83 Ko, aucun WARN ; planche et vues regardées (risque de lecture « raquette » dans la case, à juger en jeu)
- [x] `skin_houe_abyssal` — « Serre de l'Abysse », mandibule d'os + lame à 58° tournée de 34°, épines au col ; 797 cubes, 93 Ko, aucun WARN ; planche et vues regardées (**tête petite et sombre dans la case à taille réelle** : à grossir si l'utilisateur le confirme)
- [x] `skin_lance_abyssal` — « Dard de l'Abysse », fer d'os en feuille large à fils verts, barbes de harpon en griffes, repère/Display de la lance Orage ; 925 cubes, 104 Ko, aucun WARN ; planche et vues regardées (bonne lecture dans la case)
- [x] `skin_arc_abyssal` — « Envergure de l'Abysse », branches en os d'aile courbes (gouttière verte), corde de lueur verte, flèche d'os ; repère/Display de l'arc de givre, `gui` 0,88 ; 3 948 cubes, 344 Ko, aucun WARN ; planche (4 étapes) et vues regardées (corde en pointillé dans la case à taille réelle)
- [x] `skin_arbalete_abyssal` — « Échine de l'Abysse », arbrier en échine de 8 vertèbres, arc court en os d'aile sorti d'un crâne, étrier en mâchoire, corde de lueur verte, carreau d'os pâle ; 6 étapes ; 5 613 cubes, 472 Ko, aucun WARN ; planche (6 étapes) et vues regardées (sens vanilla correct en 1re personne)
- [x] `skin_trident_abyssal` — « Fouëne de l'Abysse », fourche d'os d'une pièce (pente 52°), ardillons vers le bas, gorges élargies, `gui` 0,6 ; `lance` non couchée (attente du développeur) ; 903 cubes, 135 Ko, aucun WARN ; planche et vues regardées (ψ net dans la case)
- [x] `skin_bouclier_abyssal` — « Égide de l'Abysse », écaille d'os en écu cornu bombée sur quille, umbo à griffe, 3 gouttières par moitié ; garde dans `item_idle` et `item_use` (écart 0,0007 px au vanilla), aucun son à la levée ; 2 614 cubes, 316 Ko, aucun WARN ; planche et vues regardées
- [x] `skin_masse_abyssal` — « Gueule de l'Abysse », masse à ailettes : 6 crocs d'os biseautés autour d'un nœud, croc au sommet ; 1 320 cubes, 138 Ko, aucun WARN ; planche et vues regardées (couronne nette dans la case)
- [x] `skin_canne_abyssal` — « Leurre de l'Abysse », épine dorsale de poisson des grands fonds : moulinet en vertèbre, scion d'os à 3 épines, leurre lumineux qui pend au repos, ligne de lueur verte ; aucun son au lancer, un seul sur `event_swing` ; 2 402 cubes, 195 Ko, aucun WARN ; prix aligné sur le set (épique 850/300) ; planche regardée. **Set Abyssal complet (12/12).**

### Steampunk (Mécanique)
Langage : `.claude/styles/steampunk.md` ; métal propre (brossé ±5 % au plus, ni vert-de-gris ni taches). Laiton (236,196,112)→(190,142,64)→(112,76,32) pour la structure, les gardes, les bagues et les engrenages ; cuivre (232,150,96)→(176,92,52)→(98,46,26) pour les chaudières, tuyaux et cerclages rivetés ; acier bruni (136,140,150)→(78,82,92)→(38,40,48) pour les fers, tiges et axes, fil poli clair (220,224,232) ; bois sombre (122,78,46)→(40,22,14) et cuir cousu de laiton (150,96,60)→(60,34,20) aux poignées. **Lumière `_e` seulement sur des sources qui ont une raison d'éclairer**, petites et vives (150–225) : verre ambre (255,210,120)→(220,150,50) des cadrans de manomètre (aiguille et zone rouge (176,44,30)), lentilles-témoins et tubes de niveau ; fentes de foyer orange (255,150,52), `_e` (225,112,28). Ornements récurrents : engrenages à dents en volume, rivets de 3–4 texels, cerclages de laiton, manomètre ambre sur la face +Z (vue dans l'inventaire), soupape, volant de vanne ; chaque pièce sert à quelque chose (un tuyau relie deux pièces, la pression pousse). Vivant sobre, en « saccadé mécanique » : la pression monte par crans (échelon, dépassement, rappel), l'aiguille grimpe, l'engrenage avance d'une dent ; la décharge est un jet de vapeur `trans_` qui **monte** (plaques croisées dépliées par `scale`, fondu `ctrl_alpha`) + `emit_mc_white_smoke` par `ctrl_emit` ; jamais de vapeur qui retombe. Son unique : `block.fire.extinguish` (décharge de vapeur), à 0,04 s au coup qui touche pour les armes de mêlée ; outils : une décharge au repos (boucle ≥ 20 s) ; armes à distance : au tir (`tir_vapeur` embarqué, `skin_arc_steampunk`). Référence : `skin_epee_steampunk` (vrai volume).
- [x] `skin_epee_steampunk` — « Lame de pression », référence du set : roue dentée de laiton à manomètre ambre, lame d'acier bruni en vrai volume à tube de niveau ambré, pommeau-chaudière ; 820 cubes, 91 Ko ; son `block.fire.extinguish` à `event_hit` (0,04 s). À voir : volant de vanne peu visible dans la case, garde de main en 3e personne.
- [x] `skin_pioche_steampunk` (refaire en 3D) — pic d'acier en plaque biseautée fermée à gouttière, pièces rondes en tours, cylindre penché à 15° (croissant lisible dans la case) ; 1 014 cubes, 122 Ko ; son unique dans `item_idle` (24 s). Avant/après : `.build/comparaison_avant_apres.png`. À voir : pic par la tranche, cylindre moins lisible dans la case.
- [x] `skin_hache_steampunk` — « Fendeuse à pression » : fer d'acier bruni en vrai volume serti dans une roue dentée à manomètre ambre, marteau à vapeur de cuivre au dos, pommeau-chaudière ; 819 cubes, 111 Ko ; son `block.fire.extinguish` à `event_hit` (0,04 s, comme les haches des autres sets). À voir : roue très présente dans la case, tuyau près de la poignée en 3e personne.
- [x] `skin_pelle_steampunk` — « Pelle de chauffe » : fer d'acier bruni en vrai volume à bords de laiton et nervure creusée, roue dentée à manomètre, chaudière sur le manche, poignée en D ; 654 cubes, 97 Ko ; son unique dans `item_idle` (24 s). Noté : en 3e personne, +b de l'image passe en bas (soupape et vapeur vers −b, `pelles.md`). À voir : bouffée en 1re personne, lecture du fer dans la case.
- [x] `skin_houe_steampunk` — « Binette à pression » : œil en roue dentée à manomètre, col de cygne d'acier, lame trapèze en vrai volume à flancs de laiton (58°, tournée de 48° : plat lisible dans la case), chaudière sous la tête ; 815 cubes, 111 Ko ; son unique dans `item_idle` (24 s). À voir : sens du labour (`event_swing`/`event_break`), lame dans la case.
- [x] `skin_lance_steampunk` — « Pique à pression » : fer d'acier en feuille en vrai volume serti dans une roue dentée à manomètre, buses de cuivre en V à la place des ailettes, réservoir sur la hampe ; Display de la lance d'orage ; 882 cubes, 113 Ko ; son `block.fire.extinguish` à `event_hit` (0,04 s). À voir : fer gris face à la roue jaune dans la case, `item_use` et estoc.
- [x] `skin_arc_steampunk` (refaire en 3D) — pièces rondes en tours (chaudière, manomètre, canon bagué, pavillon, ressort), crosse/carcasse/pontet en plaques biseautées fermées, porte de foyer `_e` ajoutée côté −Z ; aiguille dans le sens horaire ; double dépliage de la bouffée corrigé ; son `tir_vapeur` 0,02 → 0,04 s ; 1 724 cubes, 182 Ko. Avant/après : `.build/comparaison_avant_apres.png`. À voir : sens en visée, `event_release` et son son.
- [x] `skin_arbalete_steampunk` (refaire en 3D) — repère, taille, 6 étapes et Display validés en jeu gardés (silhouette identique dans toutes les vues, contrôlé) ; lames de ressort, crosse, étriers en plaques biseautées fermées, pièces rondes en tours, engrenage à 14 dents en volume, vanne et porte de foyer `_e` ajoutées ; 4 animations ajoutées (n'en avait pas), seul son `tir_vapeur` à `event_release` (0,04 s) ; 4 559 cubes, 448 Ko. Avant/après : `.build/comparaison_avant_apres.png`. À voir : `event_release` et son son, jet en main, lames vues par la tranche dans la case.
- [x] `skin_trident_steampunk` — « Harpon à vapeur » : fourche ψ d'acier bruni d'une pièce en vrai volume (gorges bordées de laiton), roue dentée à manomètre, buse unique, chaudière au talon, hampe en tube d'acier ; étapes `repos`/`leve`/`lance` (non couchée, recette 5) ; 1 190 cubes, 170 Ko ; son `block.fire.extinguish` à `event_release` (0,04 s). À voir : `item_use`, jet en 1re personne, traînée en vol.
- [x] `skin_bouclier_steampunk` — « Rondache de chaudière » : porte de chaudière ronde sur roue dentée de 24 dents (12 secteurs biseautés fermés), dôme d'acier riveté, manomètre ambre ; dos : chaudière, foyer `_e`, vanne, soupape, poignée et sangle ; garde dans `item_idle` et `item_use` (écart 0,0007 px, 4 cas) ; seul son `block.fire.extinguish` à `event_hit` (0,04 s), rien à la levée ; 2 430 cubes, 219 Ko. À voir : garde tenue 5 s, dents fines dans la case, `q.hit_by_entity` en parade.
- [x] `skin_masse_steampunk` — « Pilon de chaudière » : tête dans l'axe (foyer d'acier à fentes `_e`, couronne de laiton à 8 dents en prismes fermés, ballon de cuivre à manomètre double face, pilon d'acier poli) ; 779 cubes, 80 Ko ; son `block.fire.extinguish` à `event_hit` (0,04 s). À voir : jet d'`event_hit` pas repéré au rendu (cadrage ?), tête surtout dorée dans la case.
- [x] `skin_canne_steampunk` — « Canne à vapeur » : scion d'acier bruni en 3 brins à viroles et anneaux de laiton, chaudière rivetée sur le porte-moulinet (foyer `_e`), moulinet à flasques dentées, pignon et manomètre double face, leurre-hélice au repos ; 2 019 cubes, 181 Ko ; seul son `block.fire.extinguish` à `event_swing` (0,04 s ; lancer + remontée = 2 sifflements), rien à `event_enter_*`. À voir : moulinet = point jaune dans la case, ligne du jeu à la pointe.

**Set Steampunk complet (12/12).**

### Kawaii
Langage : `.claude/styles/kawaii.md` (yume kawaii : tout est rond et dodu, « l'angle vif est l'ennemi du mignon ») ; sucre et guimauve **mats et opaques**, en vrai volume. Trois valeurs franches + blanc, jamais de pastel presque blanc sur les grandes surfaces : **sucre lilas** (232,220,255)→(184,160,244)→(120,92,200) pour les lames, fers et branches (plaque biseautée fermée, biseaux larges et doux, fil crème (255,246,240) sans lumière, bande rose bonbon (255,170,206) entre fil et biseau, liseré lilas foncé (130,86,210) à l'arête du plat), **cœur de sucre framboise** (255,128,176)/(226,52,118)/(150,22,78) avec un grand reflet blanc en fenêtre et un petit contre-reflet, **nuage** blanc ombré de lilas (255,249,247)→(214,202,232) ; poignées et manches en **guimauve torsadée** rose bonbon (242,104,166) / crème (252,240,244) en spirale continue (comme l'arc), bagues lavande (208,192,248). Pointes en **ogive arrondie**, bouts ronds, pièces rondes en tours de pans (bosses de nuage = sphères de pans qui se touchent). Ornements récurrents : **cœur de sucre dodu** en plaque biseautée fermée « coussin », droit dans la case ; **bosses de nuage** aux bouts (garde, quillons, pommeau, talon) ; gouttière creusée où sont serties des **dragées-cœurs**. Lumière `_e` seulement sur de petites sources nettes (150–225) : dragées-cœurs (255,196,228), `_e` (225,140,196), et le petit contre-reflet du cœur ; jamais de fond `_e`. Vivant doux et rebondi (squash-and-stretch, rebonds amortis) : le cœur bat (double battement, `item_idle` 8 s, seul dépliage par `scale` de ce groupe), dragées qui s'avivent au battement (`ctrl_lumiere`), nuages en « plop » à `event_select` (seul dépliage par `scale` des nuages), nuages en retard à `event_swing` ; au coup qui touche, bouffée de cœurs de sucre `trans_` qui monte et s'efface (`ctrl_alpha`) + `emit_mc_heart` par `ctrl_emit`. Son unique : `pof_sucre` embarqué (pof de guimauve + note de célesta, original), à 0,04 s à `event_hit` pour les armes de mêlée ; armes à distance : au tir (`paillettes`, `skin_arc_kawaii`) ; outils : `event_hit` aussi (pas de son au repos). Référence : `skin_epee_kawaii` (vrai volume).
- [x] `skin_epee_kawaii` — « Lame Câline », référence du set : lame de sucre lilas en vrai volume (section hexagonale creusée, fil crème, bande rose), 4 dragées-cœurs `_e` serties dans la gouttière, garde en cœur framboise dodu, quillons et pommeau en nuages, fusée en guimauve torsadée ; 987 cubes, 150 Ko ; son embarqué `pof_sucre` à `event_hit` (0,04 s), cœurs `trans_` + `emit_mc_heart`. À voir : garde petite dans la case, dragées presque blanches de nuit.
- [x] `skin_pioche_kawaii` — « Pic Câlin » : œil en gros cœur framboise coussin, croissant de deux bras de sucre lilas en vrai volume (plaques biseautées fermées, bouts en ogive), dragées-cœurs `_e` dans la gouttière, manche en guimauve torsadée, pommeau nuage ; 866 cubes, 161 Ko ; son `pof_sucre` une fois dans `item_idle` (20,04 s / 24 s, soupir de cœurs). À voir : son au repos, `item_swing`/`event_break` au minage, dragées dans la case.
- [x] `skin_hache_kawaii` — « Coupe-Nuage » : fer unique de sucre lilas en vrai volume (plaque biseautée fermée, pente 40°, talon et barbe arrondis), gouttière en croissant à 3 dragées-cœurs `_e`, œil en cœur framboise coussin, nuage au dos, manche guimauve, pommeau nuage ; 1 001 cubes, 166 Ko ; son `pof_sucre` à `event_hit` (0,04 s). À voir : fer un peu en éventail (forme d'entonnoir de profil 3/4), cœurs à `event_hit`.
- [x] `skin_pelle_kawaii` — « Pelle Câline » : fer de terrassier en sucre lilas en vrai volume (épaules larges arrondies, bout en ogive), nervure creusée à 3 dragées-cœurs `_e`, cœur framboise au col, manche guimauve, poignée en D à nuages ; 909 cubes, 159 Ko ; son `pof_sucre` une fois dans `item_idle` (20,04 s / 24 s). À voir : sens de la pelletée à `event_break` (`SIGNE_B`), son au repos.
- [x] `skin_houe_kawaii` — « Binette Câline » : œil en cœur framboise à bouton-nuage, col de cygne en crosse de sucre d'orge, lame-cœur de sucre lilas en vrai volume (58°, tournée de 60° : cœur lisible dans la case), nervure à 2 dragées `_e`, manche guimauve, pommeau nuage ; 1 065 cubes, 172 Ko ; son `pof_sucre` une fois dans `item_idle` (20,04 s / 24 s). À voir : sens du labour, dragées dans la case.
- [x] `skin_lance_kawaii` — « Pique-Cœur » : fer-feuille de sucre lilas en vrai volume (nervure à 3 dragées `_e`), cœur framboise ailé (ailes de chérubin aux trois bandes des ailes du set) à la place des ailettes, hampe guimauve à bagues, talon nuage ; Display de la lance d'orage ; 1 075 cubes, 167 Ko ; son `pof_sucre` à `event_hit` (0,04 s). À voir : battement d'ailes à `item_use`, sens de la bouffée à `event_hit`.
- [x] `skin_arc_kawaii` (refaire en 3D) — cœur de poignée en cœur framboise coussin du set (plaque biseautée fermée, plus de tranches empilées), branches guimauve en tours de 12 pans à spirale continue, bagues lavande à dragée `_e`, nuages en sphères (blancs comme le set), flèche en volume ; nom, fiche, repère, étapes, Display et `gui` gardés (case identique, contrôlé) ; son `paillettes` 0,02 → 0,04 s à `event_release` ; 200 → 1 976 cubes, 60 → 267 Ko. Avant/après : `.build/comparaison_avant_apres.png`. À voir : cœur et dragées de nuit, `event_release`.
- [x] `skin_arbalete_kawaii` — « Tire-Bisou » : cœur framboise coussin posé droit, bras de sucre lilas recourbés en vrai volume (plaques biseautées fermées, dragée `_e` par face, perle au bout), étrier lavande en U, arbrier guimauve, talon nuage ; carreau rayé à pointe-cœur, fusée lilas à coiffe framboise ; repère et Display vanilla ; 4 175 cubes, 456 Ko ; son `paillettes` à `event_release` (0,04 s). À voir : `event_charged`/`event_release`, pointe-cœur et dragées de nuit.
- [~] `skin_trident_kawaii`
- [ ] `skin_bouclier_kawaii`
- [ ] `skin_masse_kawaii`
- [ ] `skin_canne_kawaii`

### Cuir (Fétiche)
- [ ] `skin_epee_cuir`
- [ ] `skin_pioche_cuir`
- [ ] `skin_hache_cuir`
- [ ] `skin_pelle_cuir`
- [ ] `skin_houe_cuir`
- [ ] `skin_lance_cuir`
- [ ] `skin_arc_cuir`
- [ ] `skin_arbalete_cuir`
- [ ] `skin_trident_cuir`
- [ ] `skin_bouclier_cuir` (refaire en 3D)
- [ ] `skin_masse_cuir`
- [ ] `skin_canne_cuir` (refaire en 3D ; préréglage _CANNE changé le 2026-11-08 : vérifier sa 3e personne)

### Pâtisserie (objets déjà livrés seulement)
- [ ] `skin_masse_patisserie` (refaire en 3D)
- [ ] `skin_pelle_patisserie` (refaire en 3D)

### Bérénice
- [ ] `skin_epee_berenice`
- [ ] `skin_pioche_berenice`
- [ ] `skin_hache_berenice`
- [ ] `skin_pelle_berenice`
- [ ] `skin_houe_berenice`
- [ ] `skin_lance_berenice`
- [ ] `skin_arc_berenice`
- [ ] `skin_arbalete_berenice`
- [ ] `skin_trident_berenice`
- [ ] `skin_bouclier_berenice`
- [ ] `skin_masse_berenice`
- [ ] `skin_canne_berenice`

### Tentacule
- [ ] `skin_epee_tentacule`
- [ ] `skin_pioche_tentacule`
- [ ] `skin_hache_tentacule`
- [ ] `skin_pelle_tentacule`
- [ ] `skin_houe_tentacule`
- [ ] `skin_lance_tentacule`
- [ ] `skin_arc_tentacule`
- [ ] `skin_arbalete_tentacule`
- [ ] `skin_trident_tentacule`
- [ ] `skin_bouclier_tentacule`
- [ ] `skin_masse_tentacule`
- [ ] `skin_canne_tentacule`
