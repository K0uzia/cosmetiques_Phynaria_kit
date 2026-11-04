# Règles — leçons des retours en jeu

Erreurs et réussites constatées sur de vrais cosmétiques. Les appliquer **dès la première version**. Ajouter chaque leçon confirmée par une capture ou un avis de l'utilisateur, et supprimer ce qui se révèle faux.

## Le rendu ne suffit pas

- Le renderer ne montre ni le shader, ni l'éclairage de nuit, ni l'émissif, ni les particules, ni le suivi de tête, ni le balancement des membres. Un rendu propre et un vérificateur vert ne prouvent pas le résultat en jeu : ne jamais l'affirmer.
- Contrôler aussi : de face à hauteur des yeux, par la tranche, de dessous, de profil, et de nuit dès qu'il y a du calque `_e`.
- Ne pas présenter un constat comme « vérifié » s'il vient d'un seul test de notre côté : `scale` et `position` ont été déclarés ignorés à tort.
- Lire les captures et le guide avant de coder. « Je les veux plates » a d'abord été compris à l'envers : reformuler chaque demande ambiguë avant de lancer une refonte.

## Ce que l'utilisateur a validé

« Validé » veut dire vu en jeu ou explicitement approuvé. Le reste figure plus bas.

| Pièce | Avis | À retenir |
|---|---|---|
| `ailes_abyssales` | « juste incroyable », 3D et textures | Référence de style pour tout cosmétique à os et membrane |
| `bandeau_abyssal` | « incroyable », position des cornes ensuite « niquel » | Référence pour le thème chasseur de démons : bandeau, regard vert, cornes, oreilles |
| Aurelion : forme et rondeur | « la rondeur est bien » | Plume peau + âme |
| Plume-particule d'Aurelion | « ok » | Recette de particule |
| Fusée en `glide` | confirmée en jeu | V0 = 26, DV = 5, exclusion des piqués |
| `masque_abyssal` | « sympa », « base réutilisable » | Hors de l'esprit chasseur de démons : ne pas le présenter comme répondant à ce thème |
| `queue_abyssale` | « trop dragon, créature » | Vertèbres, épines et membrane font bête ; pour un ensemble d'allure élégante, préférer `queue_abyssale_v2` |
| `aura_brasier` (vu dans le Vestiaire) | « ça fait mec en feu », « pas du tout un effet d'aura » | Des langues de feu à contour sombre se lisent comme un incendie, même en dégradé. Une aura, c'est de la lumière, pas du feu |
| `aura_brasier` v2 (vue 3D du Vestiaire) | « horriblement moche » | Plaques croisées au cœur des membres : hors de face, elles traversent la tête et le corps (barre blanche devant le visage). Abandonné |
| `aura_brasier` v3 (en jeu, sans shader) | « une fois équipée, ok » | Recette d'aura qui marche : disques `add_` en `cam_` reculés derrière chaque partie du corps, colonnes `add_` en `camy_` derrière le joueur, anneau au sol. Menu Apparence et shaders : bugs du mod |

Livrés sans retour en jeu à ce jour : `queue_abyssale_v2`, `lames_abyssales`, `epaulieres_abyssales`, `aura_abyssale`, `familier_crane`, `diademe_celeste`, `aura_celeste`, `ailes_givre`, `ailes_mecaniques`, `chapeau_abyssal` ; série kawaii du 2026-11-03 (ensembles Kawaii et Pâtisserie, calque `_e` embarqué) : `oreilles_lapin_nuage`, `ailes_nuage_guimauve`, `queue_pompon_nuage`, `familier_nuage_mochi`, `aura_coeurs_nuage`, `familier_chat_lanterne`, `ailes_papillon_bonbon`, `aura_bulle_chewing_gum`, `halo_donut`, `sac_cupcake`, `chapeau_macaron`, `baguette_sucre_orge`, `epaulettes_guimauve` ; test d'aura enveloppe du 2026-11-03 : `aura_brasier` ; ensemble Steampunk du 2026-11-03 (paliers mécaniques, cycle de pression, fonctions avancées du guide) : `ailes_mecaniques` refaites, `haut_de_forme_mecanique`, `epaulieres_mecaniques`, `queue_mecanique`, `familier_hibou_mecanique`, `pistolet_mecanique`.

## Recettes

| Élément | À éviter (constaté en jeu) | À faire |
|---|---|---|
| Plume d'aile | Plaque seule : « tas de feuilles » par la tranche. Cubes pleins seuls : « trop carré », marches | Peau ronde découpée par alpha autour d'une âme pleine plus étroite |
| Os d'aile à plumes | Barres droites apparentes, blocs à la base | Volume effilé, couvert d'écailles rondes dessus et dessous |
| Os et membrane | | Os octogonaux effilés et courbes ; membrane peinte d'un seul tenant, découpée en plaques par alpha, veines contrastées |
| Anneau, halo | Segments décalés : pointillés. Segments chevauchés : créneaux sombres sous `_e` | Une seule plaque de 0,15 px, anneau découpé par alpha, même forme plus étroite dans `_e` |
| Particule | Barreaux : bâtons. Sections : « bonbon » et double couche. 0,06 px : fragments à distance. Trop près du sol : scintillement | Un seul cube de 0,3 px, y ≥ 0,3 au-dessus du pivot, face `up` seule, courbure peinte dans l'image |
| Corne | Ancrée sur l'arête du front : base en porte-à-faux devant le visage | Ancrée sur le dessus de la tête, au-dessus des tempes (z ≈ −3 à +2) ; contrôler le profil |
| Lueur | Lueur vive sur un dégradé : orange violent | Fines lignes lumineuses et fond additif très sombre ; rien de vif hors du point focal |
| Couleur de nuit | Sans `_e` : saumon et mate sous éclairage chaud | Base plus blanche et fond `_e` léger, ou option « Lumineux » du staff |
| Aura | Objets en orbite : « pas une aura ». Langues de feu à contour sombre : « mec en feu ». Liseré en plaques croisées dans les membres : « horriblement moche », il traverse la tête et le corps hors de face | Essai en cours (`aura_brasier` v3, à juger en jeu) : halo de disques `add_` dans des groupes `cam_` reculés derrière chaque partie du corps et vides au centre (le corps cache le reste), colonnes d'énergie `add_` en `camy_` derrière le joueur avec `ctrl_uv`, anneau au sol, étincelles en particules. Un dégradé dans `_e` seul ne se voit pas de jour : le mettre aussi dans la texture |

## Calque `_e` : correctif à vérifier

Le calque clignotait aussi sans shader et pouvait assombrir la texture (`docs/dev/bug_emissif_pour_dev.md`). Le correctif côté mod est annoncé pour le 2026-11-03 : `AVEC_E = True` dans tous les générateurs et calques embarqués depuis ce jour, **sans retour en jeu à ce stade**. Si le clignotement persiste en jeu : repasser `AVEC_E = False`, relivrer, et ne pas retoucher le modèle pour ce symptôme.

## Rendus avancés : constats en jeu (2026-11-03, `docs/dev/bug_rendu_avance_pour_dev.md`)

- **Sans shader** : `add_`, `cam_`/`camy_`, calque `_e` la nuit et `ctrl_teinte` sous la pluie marchent (aura visible, métal assombri).
- **Avec shader** : ni les parties `add_`, ni (à supposer) `trans_`, ni **le calque `_e`** ne s'affichent : une aura tout en `add_` disparaît, les lumières des ailes et du haut-de-forme aussi. Signalé au développeur, rien à corriger dans le modèle.
- **Reflets `_r`** : posés sur toute la face, découpe comprise : rectangles clairs autour des plaques découpées. Retirés de tous les modèles (`REFLETS = False` dans `tools/ambiance.py`) jusqu'au correctif.
- **Menu Apparence** : l'additif y est opaque ; le noir des textures `add_` faisait des carrés noirs. Les textures additives sont transparentes là où elles sont presque noires.

- **Particules Minecraft (`emit_mc_`)** : en jeu, elles partent à plusieurs blocs du point prévu et ne suivent pas le cosmétique (souffle du hibou, vapeur des ailes, 2026-11-04). Remplacées partout par une vapeur modélisée (`remplacer_emit_mc` dans `tools/particules.py`). Ne plus utiliser `emit_mc_` avant le correctif du mod.

## Orientation selon l'état

- En vol créatif, le joueur reste debout : pas de plan d'aile à 90°, il se voit par la tranche. Bascule d'environ 40°, sans plainte depuis, mais pas de validation explicite.
- En élytres et en nage, le corps est couché et le cosmétique le suit : ailes presque dans le plan du dos. Déduit du fonctionnement du mod.
- `fall` : bascule d'environ 26°, joueur debout.

## Méthode de travail

- **Sons** : « encore un peu trop fréquents » avec un son par boucle de 8 s. Règle : un son au repos seulement si la boucle dure 20 s ou plus, à l'attaque seulement pour une arme, jamais en mouvement (`tools/sons.py`).
- **Lumière** : « je ne vois aucune lumière sur le set » avec des calques `_e` faibles (presque rien au-dessus de 120) et des éclats diffus. Il faut des **sources nettes et logiques** (lentilles, cadrans, fentes de foyer, filets de verre ambré sur les nervures), vives (150 à 225) sur de petites surfaces, visibles de face comme de dos. Contrôler avec `NUIT=1` (rendu de nuit) et le panneau « De nuit » de la livraison.
- **Logique physique** : un appareil qui a un rotor ne vole pas en battant des ailes (hibou). Chaque mouvement doit avoir une cause mécanique plausible : le rotor porte, les ailes stabilisent, la vapeur sort après la pression.
- Particules qui tombent et se posent, comme les plumes d'Aurelion : **sur les ailes seulement**, jamais sur la tête, la queue ou les autres pièces, sauf demande explicite (consigne de l'utilisateur, 2026-11-03).
- Et seulement pour ce qui tombe vraiment (plumes, pétales, feuilles, éclats). **La vapeur ne retombe jamais en nuage** : elle jaillit et monte (jet modélisé, `emit_mc_white_smoke`). Nuage de vapeur qui tombait des `ailes_mecaniques` : « pas logique » (2026-11-03).
- Le fichier livrable reste unique, et les aperçus aussi : une planche PNG et un GIF regroupant toutes les animations.
- Un retour porte souvent sur une seule pièce : citer ce qui est validé et ne doit pas bouger.
- Point de départ des générateurs : `gen_ailes_abyssales.py` pour os et membrane, `gen_aurelion_wings.py` pour des plumes, `gen_bandeau_abyssal.py` pour la tête. Jamais `tools/example_wings_generator.py`, qui contient les défauts corrigés depuis.
- Tout ce qui n'est pas prouvé en jeu se présente comme à vérifier, avec une cause « mesurée » ou « supposée ».
