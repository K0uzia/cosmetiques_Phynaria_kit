# Anges et êtres divins — ailes de plumes, halos, séraphins, êtres de lumière

Fiche de référence (2026-11-04). Ensemble du dépôt : **Bérénice** (`.claude/styles/berenice.md`, à lire d'abord) : `ailes_berenice` (forme et rondeur validées, plume peau + âme), `diademe_berenice`, `aura_berenice`. Anatomie : `.claude/styles/ailes-anatomie.md`.

## 1. Codes visuels essentiels

- **Ailes de plumes blanches** = bien, pureté ; **ailes noires** = ange déchu, presque toujours (code d'anime très stable). Ailes grises, une blanche et une noire, ou blanches tachées = ambiguïté, chute en cours.
- **Halo** : anneau ou disque **flottant au-dessus** de la tête, sans contact. Le jeu japonais en a fait un **signe d'identité** : chaque personnage a un halo propre (géométrique, anguleux, deux demi-cercles croisés, couronne de pointes…), dont la forme dit le caractère et peut **changer avec l'émotion**. C'est la piste la plus riche pour un halo original.
- **Séraphin** : trois paires d'ailes (une couvre le visage, une les pieds, une vole), être « brûlant », couleurs vives et métalliques. Dans l'anime, **plus il y a d'ailes, plus le personnage est puissant** (paires multiples = boss final, mentor excentrique).
- **Être de lumière** : silhouette presque effacée par la lumière, contours flous, ailes faites de rayons ou de plumes de lumière, yeux sans pupille.
- **Ailes de pouvoir** : elles apparaissent à la transformation (*Power Gives You Wings*), parfois en lumière ou en énergie plutôt qu'en plumes.

| Registre | Codes |
|---|---|
| Élégant (Bérénice) | Ivoire et or doux, plumes rondes, halo fin, rayons fins comme des cheveux, mouvement lent |
| Mignon | Petites ailes rondes (12–20 px), halo épais et doux (anneau de beignet, `halo_patisserie`), joues roses |
| Menaçant / sacré | Ailes multiples, yeux sur les plumes, anneaux concentriques qui tournent, lumière blanche aveuglante |

## 2. Silhouette et proportions (échelle du dépôt)

- **Ailes** : 52–70 px d'envergure, pointes repliées entre mollets et chevilles. Type **vol plané passif** (longues, larges, primaires écartées en doigts) pour la majesté ; **elliptique** (courtes, rondes) pour un ange mignon (`ailes-anatomie.md`, types d'aile).
- **Séraphin** : la grande paire d'abord (52–60 px), deuxième paire plus petite au-dessus (≈ 70 %), troisième plus basse (≈ 50 %), qui suivent à ~80 % d'amplitude avec retard (`.claude/rules/categories/ailes.md`, biomécanique). Budget : rester sous ~500 cubes, extension < 60 px.
- **Halo** : diamètre 6–9 px, à 1,5–3 px au-dessus du sommet de la tête (y ≈ 33,5–35), légèrement incliné vers l'arrière (10–20°). Épaisseur visuelle 0,6–1 px.
- **Couronne de rayons** (derrière la tête) : rayons de 4–8 px qui partent d'un point derrière la nuque.

## 3. Matières et couleurs (HD 32–40 texels/px)

- **Plume** : rachis (tige) clair, vexille avec un léger dégradé, **ombre de recouvrement** à la base, pointe dorée sur les primaires. Le blanc est **chaud** (ivoire), l'ombre est **champagne**, jamais grise (palette Bérénice).
- **Contraste de rangées** : couvertures plus claires, secondaires un ton plus chaud, primaires à pointe colorée ; sinon « bloc blanc ».
- **Or** : or doux (232, 198, 122), jamais jaune vif ; filets de 3–4 texels au moins.
- **Lumière divine** : (255, 250, 232) → (255, 226, 150). Touches de bleu d'aube discrètes (étoiles, cœur du halo).
- **Ange déchu** : plumes noir bleuté avec liseré gris-violet, jamais noir pur (illisible) ; une plume blanche isolée raconte la chute.

## 4. Mouvement, comportement, attitude

- **Tout flotte et respire** : mouvements lents, amples, sans à-coup ; respiration 4 s, étirement des ailes une fois par boucle de 8 s.
- **Halo** : flottement vertical de 0,3–0,5 px sur 4–6 s, rotation très lente ou balancement ; il **s'incline** quand l'ange baisse la tête (suivre `head`).
- **Attaque / pouvoir (0,8 s)** : ailes ouvertes d'un coup, halo qui s'agrandit (échelle 1 → 1,3 → 1), rayons qui s'allongent.
- **Repos tendre** : ailes ramenées autour du corps (protection), tête penchée.
- **Apparition** (`event_equip`) : ailes qui se déploient depuis le dos de l'épaule vers les primaires ; halo qui apparaît par un **éclat** (échelle 0 → 1,2 → 1 en 0,4 s) puis se pose.

## 5. Langage anime

- **Pluie de plumes** à l'apparition ou à la transformation (motif de plume, *Feather Motif*) : plumes blanches lumineuses pour un ange, noires pour un déchu.
- **Rayons** derrière le personnage (contre-jour), **colonne de lumière** qui descend du ciel.
- **Cercles magiques** ou anneaux concentriques sous les pieds, lettres ou motifs géométriques qui tournent.
- **Poussière d'étoiles** qui **monte** lentement autour du corps.
- Yeux à pupille étoilée ou sans pupille, sourire calme.

## 6. Traduction dans le mod

- **Ailes** : `gen_ailes_berenice.py` (plume peau + âme, un bone par rémige, couvertures en cubes directs). Plumes-particules qui tombent : **ailes seulement**, recette validée (un seul cube de 0,3 px, face `up` seule, y ≥ 0,3).
- **Halo** : une seule plaque de 0,15 px, anneau découpé par alpha (jamais des segments : pointillés ou créneaux) ; même forme plus étroite dans `_e`. Halo géométrique original : dessiner la forme dans la texture, pas avec des cubes. Pour qu'il se voie avec shader : version `trans_` ou base claire dans la texture, `add_` en plus pour la lueur.
- **Rotation continue du halo ou d'anneaux** : animation `overlay_<nom>`, 360°·k exacts par boucle.
- **Rayons, colonne de lumière** : plaques `add_` en `camy_` derrière le joueur (recette `aura_brasier` v3), doublées par `trans_` pâle pour le shader. Textures additives transparentes là où elles sont presque noires (menu Apparence).
- **Halo qui change avec l'émotion** : deux plaques superposées dans le même groupe, l'une cachée par `ctrl_alpha` −1 selon l'état (par ex. halo fêlé en `hurt`).
- **Séraphin** : chaque paire est une aile complète avec son propre `mirror()` ; la petite paire suit la grande avec 0,1 cycle de retard.
- **Sons** : `block.amethyst_block.chime` au plus, selon `tools/sons.py`.

## 7. Pièges

- **Bloc blanc** : plumes toutes de la même valeur ; il faut le contraste de rangées et l'ombre de recouvrement.
- **Jaune vif** au lieu d'or doux : bon marché. **Gris** dans les ombres : sale.
- **Plan à 90° en vol** : par la tranche de face ; basculer d'environ 40°.
- Halo en segments de cubes : pointillés ou créneaux sous `_e`.
- Lumière seulement en `add_`/`_e` : tout disparaît avec shader.
- Ailes multiples qui se traversent : vérifier les superpositions dans toutes les poses (vérificateur + vue par la tranche).
- Ne pas reprendre le halo exact d'un personnage de jeu : inventer une forme qui dit le caractère de la pièce.

## 8. Sources

- [Halo, système de halos propres à chaque personnage (Blue Archive Wiki)](https://bluearchive.fandom.com/wiki/Halo)
- [Good Wings, Evil Wings (Tropedia)](https://tropedia.fandom.com/wiki/Good_Wings,_Evil_Wings)
- [Power Gives You Wings, anime et manga (TV Tropes)](https://www.tvtropes.org/pmwiki/pmwiki.php/PowerGivesYouWings/AnimeAndManga)
- [Feather Motif (TV Tropes)](https://TVTropes.org/pmwiki/pmwiki.php/Main/FeatherMotif)
- [Our Angels Are Different (TV Tropes)](https://tvtropes.org/pmwiki/pmwiki.php/Main/OurAngelsAreDIfferent)
- [Celestial Paragons and Archangels (TV Tropes)](https://tvtropes.org/pmwiki/pmwiki.php/Main/CelestialParagonsAndArchangels)
- [White wings and black wings in manga and anime (Macquarie University)](https://researchers.mq.edu.au/en/publications/white-wings-and-black-wings-ambiguous-dichotomy-in-manga-and-anim/)
- [The Many-Eyed Ones, anges bibliques (TITAA)](https://arnicas.substack.com/p/titaa-25-the-many-eyed-ones-and-yearly)
- [Making illustration with magical effect (Clip Studio)](https://tips.clip-studio.com/fr-fr/articles/4591?org=1)
- [How to create magic circles (Clip Studio)](https://tips.clip-studio.com/en-us/articles/15785)
