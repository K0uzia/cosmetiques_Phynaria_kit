# Référence — Éléments façon anime (forme, couleur, mouvement, particules)

Fiche documentée (2026-11-04). Palettes en RVB : **cœur** (le plus clair, petite surface), **teinte** (la couleur de l'élément), **bord** (plus foncé, plus saturé ; en `add_` il tend vers le noir, donc invisible). Les fiches d'ensemble (`.claude/styles/*.md`) priment pour leurs pièces (par exemple Givre pour la glace).

Codes généraux : rouge/orange = feu, bleu = eau, cyan/blanc = glace, jaune = foudre (pour la distinguer de la glace et former la triade primaire), vert = vent ou nature, brun/ocre = terre, or/blanc = lumière, noir/violet = ombre. **Poison : vert en Occident, violet au Japon** ; choisir selon l'ambiance et le dire.

## Tableau de synthèse

| Élément | Forme | Cœur | Teinte | Bord | Mouvement | Rendu conseillé |
|---|---|---|---|---|---|---|
| Feu | gouttes, S, crochets, braises détachées | (255, 246, 214) | (255, 140, 40) | (200, 40, 20) | monte, vacille vite (cadence « sur 2 ») | `add_` + forme `trans_` |
| Glace | prismes, éclats anguleux, givre en dentelle | (244, 253, 255) | (120, 208, 238) | (8, 34, 70) | rigide, pousse, scintille ; brume qui retombe | `trans_` (alpha 140–220) |
| Eau | rubans ronds, vortex, bulles décroissantes | (235, 250, 255) | (60, 160, 235) | (20, 70, 160) | coule, s'enroule, éclabousse | `trans_` + reflets peints |
| Foudre | zigzag anguleux, fourches fines | (255, 255, 240) | (255, 230, 80) ou (150, 210, 255) | (120, 80, 255) | flash 2–3 images, irrégulier | `add_` + `cam_` |
| Vent | croissants, spirales, filets parallèles | (250, 255, 250) | (190, 240, 210) | (90, 170, 140) | balaie, tourbillonne, s'efface par la queue | `trans_` très léger |
| Terre | blocs, éclats cubiques, poussière | (236, 214, 170) | (150, 110, 70) | (70, 48, 30) | lourd, lent, retombe, tremble | opaque + poussière |
| Lumière | rayons fins, halo, étoiles à quatre branches | (255, 250, 232) | (255, 226, 150) | (200, 150, 60) | rayonne, pulse lentement, monte | `add_` + double `trans_` |
| Ombre | volutes, filaments, fissures | (accent) | (40, 20, 60) | (10, 5, 20) | rampe, stagne, saccadé | `trans_` sombre + accent `add_` |
| Nature | feuilles, pétales, lianes, spores | (240, 255, 210) | (110, 200, 90) | (40, 110, 50) | ondule, pousse, pétales qui volent | opaque découpé + `trans_` |
| Poison | bulles, gouttes épaisses, vapeur basse | (230, 255, 160) ou (240, 200, 255) | (140, 220, 40) ou (160, 70, 220) | (40, 80, 10) ou (60, 20, 90) | bouillonne, goutte, fume vers le bas | `trans_` + bulles |
| Cosmique | fond sombre étoilé, nébuleuse, anneaux | (255, 255, 255) points | (110, 90, 230) | (20, 10, 60) | dérive très lente, étoiles qui scintillent | `trans_` sombre + étoiles `add_` |

## Feu

- **Forme** : base large, sommet effilé ; une ligne en S donne le sens du vent, des C creusent la masse, des crochets font les pointes ; des gouttes détachées au-dessus donnent la vitesse (sans elles, le feu « colle »). Deux écoles : géométrique (pointes nettes) et « liquide » (grandes plages qui ondulent).
- **Mouvement** : les langues montent en se doublant les unes les autres ; cadence nerveuse (8–12 images/s), cycle 0,4–0,8 s ; braises qui montent et s'éteignent en 0,5–1,5 s.
- **Particules** : braise modélisée (0,3 px, une face, *Monte*, fondu) ; `emit_mc_flame`, `emit_mc_small_flame`, `emit_mc_soul_fire_flame` (bleu) à juger en jeu.
- **Piège** : **contour sombre = « mec en feu »** (`aura_brasier` v1). Pour une aura, le feu se transpose en lumière (rouge, rose clair) ; une vraie flamme ne va que sur une source logique (torche, cheminée, lame). Lueur vive sur dégradé : « orange violent ».

## Glace

- **Forme** : prismes hexagonaux pointus, facettes en paliers, arêtes blanches, fissures fines ; le cristal pousse en grappes depuis une base.
- **Mouvement** : ne plie pas ; pousse (échelle 0 → 1 depuis la base, en cascade), tremble, scintille (étoile 0,1 s) ; l'air froid descend : brume qui retombe et glisse au sol.
- **Particules** : flocon modélisé ≤ 0,8 px une face ; `emit_mc_snowflake` discret, à juger en jeu.
- **Validé** : glace en `trans_` alpha 140–220, avec et sans shader (ensemble Givre). Âme opaque fine pour garder le volume.

## Eau

- **Forme** : rien d'anguleux, bords ronds ; rubans en S, vortex à la base, mousse festonnée, bulles qui rapetissent vers l'extérieur et vont dans le sens du flux. Quatre signes de l'eau : transparence, reflet, bulles, ondulations.
- **Mouvement** : coule en continu (`ctrl_uv` qui défile le long du ruban), éclaboussure en couronne qui retombe (0,3–0,6 s).
- **Particules** : gouttes modélisées (*Lourde*, Au sol : Disparaît) ; `emit_mc_dripping_water`, `emit_mc_splash`, `emit_mc_bubble` à essayer (sans réglages, à confirmer en jeu).
- **Piège** : reflets `_r` retirés (bug de la découpe) : peindre les reflets dans la texture.

## Foudre

- **Forme** : zigzag à angles vifs et irréguliers, fourches plus fines que le canal principal ; cœur blanc, halo coloré.
- **Mouvement** : **flash de 2 à 3 images (0,08–0,15 s)**, puis rien ; deux formes alternées en *step* ; rafales irrégulières (Molang `q.life_time`, `q.instance_seed`). Un éclair continu se lit comme un néon.
- **Traduction** : plaques `add_` découpées en `cam_` (pour ne jamais se voir par la tranche), échelle 0 entre deux éclairs dans un `overlay_` ; arcs entre deux points d'une pièce plutôt que dans le vide. Version `trans_` blanche pour les shaders.
- **Particules** : `emit_mc_electric_spark` (le plus adapté), `emit_mc_dust_<couleur>` ; `ctrl_emit` pour une rafale au moment du flash.

## Vent

- **Forme** : croissants et filets parallèles, spirales ; formes transparentes qui ne cachent rien.
- **Mouvement** : balayage 0,3–0,6 s, la forme se révèle par la tête et s'efface par la queue ; feuilles ou pétales emportés.
- **Traduction** : plaques `trans_` très légères (alpha 30–90) courbées, `ctrl_uv` pour faire courir les filets, `ctrl_alpha` pour le fondu. Le vent n'a de sens qu'avec quelque chose qui bouge : plumes, rubans, cheveux (`phys_`).
- **Piège** : sans contraste, invisible de jour. Limiter aux mouvements (`run`, `fly`, `attack`).

## Terre

- **Forme** : blocs, éclats cubiques qui volent (technique des débris cubiques des explosions d'anime), poussière en nuages ronds ; rochers à arêtes biseautées.
- **Mouvement** : lourd (cadence « sur 3 », 8 images/s), impact puis tremblement amorti, poussière qui retombe lentement.
- **Traduction** : vrais volumes opaques (le cube est ici un atout), poussière `trans_` ; `emit_mc_dust_<ocre>` ; éclats modélisés de 3 px au moins.

## Lumière

- **Forme** : rayons fins qui partent d'un point (gloire), halo en anneau découpé, étoiles à quatre branches, poussière d'étoiles qui monte.
- **Mouvement** : très lent ; rotation d'un tour en 30–60 s, pulsation 4–8 s ; rien ne s'agite.
- **Traduction** : recette `aura_berenice` : `add_` + double `trans_` ; palette arrêtée à l'or clair ; cumul additif ≤ 255 ; pas de `_e` sur une pièce tout en `add_`.
- **Piège** : blanc pur saturé en grand = disque opaque ; `end_rod` = grosse étoile qui dérive.

## Ombre

- **Forme** : volutes irrégulières, filaments en vrilles, fissures ; l'anime « maudit » garde une palette éteinte et laisse **un seul** accent (violet, rouge sang, cyan électrique) porter la lecture, sur les bords et dans les fissures.
- **Mouvement** : rampe, stagne, accélère par à-coups ; fumée qui tombe ou reste au sol.
- **Traduction** : le noir est invisible en `add_` : volutes en `trans_` sombre (alpha 80–180) ou opaque découpé, accent en `add_` (fines lignes) ; `ctrl_teinte` pour assombrir. `emit_mc_smoke`, `emit_mc_squid_ink`, `emit_mc_portal` à juger en jeu.
- **Piège** : sombre sur sombre de nuit : illisible sans l'accent ; un dégradé noir → violet vif fait « néon bon marché ». Référence de style à os et membrane : `ailes_abyssales` (validée).

## Nature

- **Forme** : feuilles et pétales découpés (variantes 4–6), lianes qui s'enroulent, bourgeons qui s'ouvrent, spores lumineuses.
- **Mouvement** : pousse (échelle depuis la base, en spirale), ondule (sinus lents déphasés), pétales emportés.
- **Particules** : pétale ou feuille modélisé qui tombe et se pose **seulement depuis des ailes** ; ailleurs, spores qui montent ; `emit_mc_cherry_leaves` à juger en jeu.

## Poison

- **Forme** : bulles qui gonflent et éclatent, gouttes épaisses qui pendent, vapeur lourde qui coule vers le sol.
- **Mouvement** : bouillonnement irrégulier (bulles 0,5–1,5 s), gouttes qui s'étirent puis tombent.
- **Traduction** : bulles `trans_` (bord clair, centre transparent), vapeur `trans_` basse ; `emit_mc_dust_<vert>`, `emit_mc_witch` (violet) à juger en jeu.

## Cosmique

- **Forme** : fond très sombre parsemé de points blancs, nébuleuse en nuages colorés, anneaux planétaires, constellations reliées par des filets.
- **Mouvement** : dérive très lente (`ctrl_uv` lent sur la nébuleuse), étoiles qui scintillent au hasard.
- **Traduction** : texture opaque ou `trans_` sombre avec étoiles au calque `_e` (pièce non additive) ; anneaux en plaques de 0,15 px ; étoiles modélisées ≤ 0,6 px ; `emit_mc_end_rod` **non** (grosse étoile), `emit_mc_portal` possible.

## Avec shader

Seul `trans_` s'affiche (et l'opaque). Glace, eau, vent, ombre et poison se prêtent bien au `trans_` ; feu, foudre et lumière dépendent de l'additif : leur donner une **forme `trans_` ou opaque claire** qui reste lisible quand l'additif disparaît.

## Sources

- [TV Tropes : Color-Coded Elements](https://TVTropes.org/pmwiki/pmwiki.php/Main/ColorCodedElements) et [All The Tropes : Color-Coded Elements](https://allthetropes.fandom.com/wiki/Colour_Coded_Elements)
- [TV Tropes : Elemental Powers, anime et manga](https://tvtropes.org/pmwiki/pmwiki.php/ElementalPowers/AnimeAndManga)
- [EN World : « What Color is Your Damage? »](https://www.enworld.org/threads/rpg-evolution-what-color-is-your-damage.685206/latest)
- [VFX Apprentice : feu stylisé](https://www.vfxapprentice.com/blog/how-to-draw-stylized-fire-flames) et [eau stylisée](https://www.vfxapprentice.com/blog/how-to-draw-stylized-water)
- [Anime Outline : explosions, fumée et feu](https://www.animeoutline.com/how-to-draw-explosions-smoke-fire-step-by-step/)
- [MediBang : dessiner le feu](https://medibangpaint.com/en/use/2020/08/effect-for-expressing-fire)
- [Animétudes : le style Kanada (éclairs anguleux, feu liquide)](https://animetudes.com/2021/07/09/the-kanada-style-now/)
- [Clip Studio Assets : éclairs affichés 3 images](https://assets.clip-studio.com/en-us/detail?id=2040112)
- [80.lv : éclairs stylisés sur plans croisés](https://80.lv/articles/stylized-lighting-vfx-created-in-blender-with-procedural-textures)
- Fiches internes : `.claude/styles/givre.md`, `.claude/styles/berenice.md`
