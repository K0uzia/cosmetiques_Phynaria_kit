# Référence — Principes de l'effet anime (sakuga d'effets) traduits pour le mod

Fiche documentée (2026-11-04). Demande de l'utilisateur : « base-toi principalement sur les animes pour tout ce qui est ailes, effets, aura, magie ». Les œuvres citées le sont pour l'ambiance ; on n'en reprend que des codes génériques (règle 5 de `CLAUDE.md`). Le guide du mod (`docs/guide-cosmetiques.md`) et `.claude/rules/retours-en-jeu.md` priment sur cette fiche.

## Codes visuels

- **Un effet anime est une forme dessinée, pas une simulation.** L'animation d'effets (« effects animation », エフェクト作画) dessine les phénomènes naturels (feu, eau, fumée, lumière, explosions) sans squelette : ils apparaissent, s'épaississent, s'amincissent et se dissipent. Trois qualités attendues : **puissance, singularité, texture** (fullfrontal.moe).
- **Géométrie franche** (héritage de Yoshinori Kanada) : éclairs anguleux, explosions qui partent d'un simple cercle puis éclatent dans toutes les directions, formes très affirmées. L'autre pôle, le « feu liquide » : de grandes plages de couleur qui ondulent comme des vagues.
- **Contrastes de nature** : fumée sombre contre lumière vive, trajectoires rondes contre lignes droites. Un effet lisible oppose toujours deux choses.
- **Formes de base** : la goutte (base pleine, pointe effilée), le **S** (ligne directrice qui donne le sens du vent ou du mouvement), le **C** et le **crochet** (creusent la masse pour qu'elle ne fasse pas « boule »), et des **morceaux détachés** au-dessus de la masse : sans eux, l'effet a l'air collé (VFX Apprentice).
- **Couleur en couches** : cœur presque blanc → teinte saturée → bord plus foncé et plus saturé (pas noir). Deux ou trois couleurs par effet au plus ; une dominante, un accent rare.
- **Ombre portée de l'effet** (kage) : l'anime pose un aplat d'ombre net dans l'effet lui-même (« ombres wakame » de l'école Kanada : des lignes dans l'effet pour garder le détail). Le relief vient de deux tons francs, pas d'un dégradé mou.
- **Less is more** : les formes portent l'effet, la teinte ne passe pas au travers du chaos ; la valeur (clair/sombre) fait la hiérarchie. Garder les pics de blancheur pour l'instant du flash ; le corps de l'effet reste en valeurs moyennes (guide de style VFX de League of Legends).

## Formes et couleurs

| Couche | Rôle | Dans une texture du dépôt |
|---|---|---|
| Cœur | point le plus chaud, petit | presque blanc teinté (jamais blanc pur sur de grandes surfaces) |
| Teinte | la couleur de l'élément | saturée, valeur moyenne-haute |
| Bord | sépare l'effet du fond | même teinte plus foncée et plus saturée ; noir **seulement** en additif (où il devient invisible) |
| Détachés | gouttes, braises, éclats | petits, au-dessus ou en avant de la masse, de plus en plus petits vers l'extérieur |

Contour plein contre dégradé : l'anime choisit l'un ou l'autre selon l'intention. **Plein** (aplats découpés) pour un effet solide, rapide, menaçant ; **dégradé** (lueur) pour la lumière, le sacré, le calme. Le même effet mélange souvent un noyau plein et un halo doux autour.

## Mouvement et timing

- **Trois temps** : anticipation (petite, en dessous du geste), impact ou pic (court, dans le premier quart de la durée), dissipation (la plus longue, qui ralentit). Courbe non linéaire.
- **Ordres de grandeur** (24 images/s en anime, 60 en jeu de combat) :
  - flash ou image d'impact : 1 à 3 images, **0,04 à 0,12 s** ;
  - « smear » (étirement le long de la trajectoire) : 1 à 2 images, **0,04 à 0,08 s** ;
  - gel à l'impact (hitstop) : 0,07 à 0,15 s pour un coup léger, 0,2 à 0,4 s pour un coup lourd ;
  - dissipation : 0,3 à 1 s pour une attaque, plusieurs secondes pour une aura calme.
- **Modulation de cadence** : l'anime passe d'une image sur une (fluide, nerveux) à une sur trois (8 images/s, lourd) dans le même plan. Les effets sont souvent animés plus vite que les personnages ; une cadence basse donne du poids, une image tenue donne de l'impact.
- **Pas de répétition visible** : chaque flamme, chaque goutte un peu différente ; varier taille, angle, rythme.
- **Effet court** : « si l'effet te paraît long, il est beaucoup trop long ». Au repos, préférer une respiration lente à une agitation continue.

## Langage anime

| Code | Lecture |
|---|---|
| Image d'impact (couleurs inversées, noir/blanc/rouge, 1 à 3 images) | le choc, l'instant de vérité |
| Smear et lignes de vitesse | la vitesse, la trajectoire |
| Formes anguleuses, cadence irrégulière | danger, électricité, violence |
| Formes rondes, lentes, lumineuses | sacré, soin, calme |
| L'effet qui épouse la pose du personnage | le personnage *est* l'élément (pas « il utilise » le feu) |
| Vêtements et cheveux soulevés dans le sens du flux | l'énergie a une direction physique |

## Traduction dans le mod

| Principe | Outil du mod | Recette |
|---|---|---|
| Forme découpée nette | plaque fine + texture découpée par alpha (cutout) | peinte ×3–4, LANCZOS, seuil ≈ 110 (`modeling.md`) |
| Lueur, cœur blanc | groupe `add_` (noir = invisible) | dégradé noir → teinte → cœur clair ; **cumul de toutes les couches ≤ 255** par canal |
| Voile, glace, fumée | groupe `trans_` (alpha 1–254) | seul rendu visible avec shader aujourd'hui |
| Effet qui doit se voir de partout | `cam_` (face caméra) / `camy_` (debout) | disque, étoile, flamme, colonne ; face `south` (+Z) vers la caméra |
| Flash, image d'impact | `ctrl_alpha`, `ctrl_lumiere`, échelle | 1 à 2 clés en *step* sur 0,05–0,1 s, puis retour |
| Smear | échelle sur l'axe du mouvement | plaque étirée ×2–3 pendant 0,05 s (*step*), puis rétractée |
| Cadence « sur 3 » | interpolation *step* | clés tous les 0,125 s : mouvement saccadé volontaire (feu, éclair) |
| Feu qui vacille, énergie qui coule | `ctrl_uv` en pas entiers (`math.floor`, `math.mod`) sur un film d'images posées côte à côte | recette `aura_brasier` : la forme reste fixe, seules les traînées défilent |
| Texture animée (images empilées) | `frame_time` en ticks, pas d'interpolation | toute la texture principale est empilée : 512² × 4 images au plus ; réservé aux petites textures |
| Morceaux détachés, braises | `particle_<nom>` + `emit_<nom>` | un seul cube de 0,3 px, une face, réglage *Monte* ; étoile ≤ 0,6 px avec Élan 100 % |
| Particules Minecraft | `emit_mc_<id>` | `dust_<rrggbb>_<taille>`, `electric_spark`, `enchant`, `soul_fire_flame` à juger en jeu ; **pas `end_rod`** |
| Rotation continue | `overlay_<nom>` | 360°·k par boucle, ne saute pas entre deux états |
| Apparition, retrait | `event_equip`, `event_unequip` (≤ 5 s) | pousse ou s'allume en cascade ; finir par `ctrl_alpha` −1 |
| Mouvement irrégulier par joueur | Molang `q.life_time`, `q.instance_seed` | deux sinus de périodes non multiples |

Ce que l'anime fait et que le mod ne fait pas : flou de mouvement, distorsion de l'image, inversion des couleurs de l'écran, éclairage du décor par l'effet. Les remplacer par une forme (smear peint, lignes de vitesse découpées, flash `add_`).

## Avec shader

Aujourd'hui (tests du 2026-11-04), **seul `trans_` s'affiche avec un pack de shaders** ; `add_` et le calque `_e` disparaissent (correctif Iris non appliqué, `fonctions-avancees.md`). Tout effet important doit donc avoir une **forme visible en `trans_` ou en opaque**, l'additif ne faisant que l'embellir. Les particules en rendu *Lumineux* sont à supposer dans le même cas.

## Pièges

- **Contour sombre** : en anime, le bord est foncé mais saturé ; chez nous un bord sombre visible (opaque ou `trans_`) autour d'une flamme a donné « mec en feu ». En `add_`, le noir est invisible : le bord doit être une teinte profonde, pas du noir, si on veut qu'il se voie.
- **Lueur vive sur un dégradé** : « orange violent ». Fines lignes lumineuses et fond additif très sombre ; rien de vif hors du point focal.
- **Cumul additif** : des disques qui se chevauchent s'additionnent ; avec le calque `_e` en plus, cumul mesuré jusqu'à ~980 (disque blanc opaque). Pièce tout en `add_` : pas de `_e`, mesurer la somme.
- **Plaques croisées fixes** dans le corps : hors de face, elles traversent la tête. Utiliser `cam_`/`camy_` reculés derrière la partie du corps.
- Petits cubes volants portés par le modèle : illisibles. Particules, ou éclats de 3 px au moins.
- Le renderer ne montre ni additif réel, ni shader, ni particules, ni `ctrl_*` : un effet se juge en jeu (`/cosmetique apercu`).

## Sources

- [Sakuga Expresso : Arcadia of My Youth (Kanada, effets)](https://fullfrontal.moe/sakuga-expresso-16-arcadia-of-my-youth/) et [article fullfrontal sur la puissance, la singularité et la texture des effets](https://fullfrontal.moe/?p=1106)
- [Animétudes : « The Kanada style now »](https://animetudes.com/2021/07/09/the-kanada-style-now/), [« Yoshinori Kanada and the nature of animation »](https://animetudes.com/2021/07/21/yoshinori-kanada-and-the-nature-of-animation/)
- [Wave Motion Cannon : « An Introduction to Framerate Modulation »](https://wavemotioncannon.com/2016/12/31/an-introduction-to-framerate-modulation/)
- [Wave Motion Cannon : les flammes de Mob Psycho 100](https://wavemotioncannon.com/2016/09/18/articulating-mob-psychos-flames/)
- [VFX Apprentice : dessiner le feu stylisé (S, C, crochets)](https://www.vfxapprentice.com/blog/how-to-draw-stylized-fire-flames)
- [VFX Apprentice : 10 conseils du guide de style VFX de League of Legends](https://www.vfxapprentice.com/blog/10-league-of-legends-vfx-design-tips) et [le guide original (PDF)](https://nexus.leagueoflegends.com/wp-content/uploads/2017/10/VFX_Styleguide_final_public_hidpjqwx7lqyx0pjj3ss.pdf)
- [VFX Apprentice : principes artistiques des VFX de jeu](https://www.vfxapprentice.com/blog/five-artistic-principles-gaming-vfx)
- [Images d'impact et smears (CG Wire)](https://blog.cg-wire.com/smear-frames/)
- [Hitstop dans les jeux de combat (Sakurai, Source Gaming)](https://sourcegaming.info/2015/11/11/thoughts-on-hitstop-sakurais-famitsu-column-vol-490-1/)
- [Animer en un, deux ou trois (ANN Lexicon)](https://AnimeNewsNetwork.com/encyclopedia/lexicon.php?id=61)
- [80.lv : VFX stylisés anime et manga](https://80.lv/articles/animemanga-stylized-vfx)
- [Livre « アニメーションのエフェクト作画テクニック » (Genkōsha)](https://ebookjapan.yahoo.co.jp/books/163873/A002244366/)
