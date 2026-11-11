# Élémentaires — golem, feu, glace, eau, pierre

Fiche de référence (2026-11-04). Ensemble du dépôt pour la glace : **Givre** (`.claude/styles/givre.md`, à lire d'abord). Leçons d'aura et de feu : `aura_brasier` (v1 « mec en feu », v2 « horriblement moche », v3 « ok » en jeu). Petits esprits élémentaires : `esprits-fees.md`.

## 1. Codes visuels essentiels

Un élémentaire est **un corps fait de sa matière**, organisé autour d'un **cœur** (cristal, braise, noyau, rune) qui l'anime. Paracelse attribue un esprit à chaque élément (salamandre au feu, ondine à l'eau, sylphe à l'air, gnome à la terre), repris tels quels par beaucoup d'anime (esprits contractés, cartes d'éléments).

| Élément | Forme | Ce qui le fait lire |
|---|---|---|
| **Golem / pierre** | Massif, épaules énormes, petite tête, bras longs, jambes courtes ; blocs taillés assemblés, joints visibles | **Runes gravées qui luisent**, cœur-cristal dans la poitrine, yeux qui sont des runes ; mousse et fleurs dans les joints = ancien et doux (comme le gardien de jardin des films de Miyazaki) |
| **Feu** | Formes en **S et en C** qui montent, mèches qui se détachent du corps principal | Cœur **blanc** à la base, jaune, orange, rouge au bout ; peau de magma fissurée pour un élémentaire solide |
| **Glace** | Éclats anguleux, prismes hexagonaux, arêtes vives, grappes qui rayonnent d'une base | Bord blanc givré, corps cyan translucide, cœur bleu nuit lumineux ; rien de mou |
| **Eau** | Courbes, **vagues**, gouttes ; jamais de pointes (elles se lisent comme du feu) | Reflets blancs en traits sur les crêtes, ombre sous les crêtes, bulles ; translucide |
| **Air / vent** | Spirales, rubans, traits de vitesse | Rien de solide : des volutes pâles autour d'un vide |

Variantes : **élégant** (fines incrustations lumineuses, matière polie, silhouette humaine), **mignon** (petit golem trapu et rond, grands yeux-runes, une fleur sur la tête), **menaçant** (fissures béantes, cœur qui déborde, éclats en désordre).

## 2. Silhouette et proportions (échelle du dépôt)

- **Golem-familier** : 9–12 px de haut, tête 2–3 px seulement (le poids est dans les épaules et les bras), poings de 2,5–3 px. Version mignonne : tête plus grosse (40 %), bras courts.
- **Épaulières élémentaires** : blocs ou éclats qui sortent des épaules, 4–8 px, sans dépasser 6 px au-dessus de l'épaule pour ne pas masquer la tête de profil.
- **Couronne élémentaire** (`head`) : éclats ou flammes sur le dessus de la tête, 3–7 px, ancrés au-dessus des tempes comme des cornes.
- **Aura** : recette validée (disques en `cam_` derrière chaque partie du corps, colonnes en `camy_`, anneau au sol). Rayon de l'anneau 10–14 px.
- **Cœur** : 1,5–3 px, toujours au centre de masse (poitrine du golem, base d'une grappe de cristaux).

## 3. Matières et couleurs (HD 32–40 texels/px)

- **Pierre** : grandes masses de valeur moyenne, **arêtes claires** (biseau de 2–3 texels), joints sombres de 3–4 texels ; grain fin à ±5 % au plus (le bruit contrasté se lit comme un bug, leçon `ailes_steampunk`). Runes : traits de 3–4 texels, cœur clair et bord saturé, dans des rainures plus sombres.
- **Feu** (tutoriels de dessin d'effets) : du centre vers le bord, blanc → jaune pâle → orange → rouge, le blanc le plus petit et à la base ; mèches secondaires qui se détachent. **Pas de contour sombre.**
- **Glace** : palette Givre (bord (244, 253, 255), corps (120, 208, 238), cœur (8, 34, 70)), chevrons de facettes peints, fissures blanches fines.
- **Eau** : bleus du clair au profond, **reflets blancs en traits** qui suivent les crêtes, ombre sous les crêtes, bulles rondes à reflet ; teinte plus claire et plus opaque au bord.
- **Magma** : croûte noire à fissures orange qui s'élargissent vers le cœur.

## 4. Mouvement, comportement, attitude

- **Pierre** : lourde et lente ; chaque pas « pèse » (petit tassement à l'appui, 0,1 s) ; tête qui pivote lentement, avec un arrêt. Repos : immobile, seule la lueur des runes **respire** (4–6 s). Attaque : armer lentement (0,4 s), frapper vite (0,1 s), poussière au sol.
- **Feu** : ne s'arrête jamais ; ondulations rapides et irrégulières (0,3–0,6 s), mèches qui montent et se détachent ; il grandit à l'attaque et se tasse sous la pluie (`q.is_in_rain`).
- **Glace** : rigide, petits tremblements, éclats qui pivotent autour de leur base ; brume froide qui **retombe** et glisse au sol (l'air froid descend). Apparition : la glace **pousse** depuis la base, en cascade.
- **Eau** : ondulation continue en vague, gouttes qui se détachent et retombent dans le corps ; elle s'étire et se tasse (squash-and-stretch) à chaque mouvement.
- **Apparition (`event_equip`)** : le golem s'assemble (blocs qui montent du sol et se placent), le feu s'allume depuis une braise, l'eau jaillit et prend forme.

## 5. Langage anime

- **Cercle magique** élémentaire sous les pieds au moment du pouvoir, aux runes de la couleur de l'élément, qui tourne puis s'efface.
- **Énergie qui pulse** : charge (la lueur monte, particules aspirées vers le cœur), puis décharge (éclat, onde de choc).
- **Couleur = élément** : rouge-orange feu, cyan-blanc glace, bleu eau, vert ou ambre terre, blanc-vert pâle vent. Un élémentaire = une couleur dominante, un accent au plus.
- **Feu « léger »** en anime : formes stylisées en volutes, très lumineuses, sans fumée noire.

## 6. Traduction dans le mod

- **Runes et cœur** : calque `_e` sur les runes (150–225, petites surfaces nettes, `.claude/rules/essentiel.md` : « je ne vois aucune lumière » avec des `_e` faibles) + couleur claire dans la texture pour le shader. `ctrl_lumiere` pour faire respirer les runes (non simulé par le renderer).
- **Glace, eau** : **`trans_`** (seul mode visible avec shader) avec une âme opaque fine pour le volume ; reflets peints. Eau qui ondule : `ctrl_uv` qui fait défiler la texture des vagues (`math.mod`), à juger en jeu.
- **Feu** : `add_` en `camy_` (flammes debout face caméra, qui ondulent par l'animation du groupe), textures transparentes là où elles sont presque noires ; doubler d'un `trans_` pâle pour le shader. Plutôt des **lueurs** que des langues de feu détaillées.
- **Particules** : braises, étincelles, vapeur qui **montent** ; gouttes qui tombent et brume froide qui glisse vers le sol sont **hors ailes** donc à éviter sauf demande (règle : seules les ailes font tomber des particules). `emit_mc_` de nouveau utilisable (`flame`, `snowflake`, `dripping_water`, à juger en jeu, discret).
- **Golem** : blocs = cubes pleins à vraies faces texturées sur 6 côtés (structure), arêtes biseautées peintes ; mousse en plaques découpées par alpha dans les joints.
- **Sons** (rares) : `block.amethyst_block.chime` (glace, cristal), `block.fire.ambient` (feu), `block.stone.place` (golem) ; un seul par boucle de 20 s au repos.

## 7. Pièges

- **Aura en langues de feu à contour sombre** : « mec en feu ». Une aura est de la lumière, pas un incendie.
- **Plaques croisées au cœur des membres** : elles traversent la tête et le corps hors de face (`aura_brasier` v2).
- Lumière seulement en `add_` ou `_e` : invisible avec shader.
- Eau à pointes : lue comme du feu. Glace molle ou ronde : lue comme de l'eau ou du verre.
- Golem en cubes pleins nus : « trop carré ». Biseauter, sculpter des joints, casser la symétrie.
- Bruit de texture fort sur la pierre : « bugs de texture ».
- Feu qui ne réagit pas à la pluie : occasion manquée (`q.is_in_rain`).

## 8. Sources

- [Elemental, Paracelse (Wikipedia)](https://en.wikipedia.org/wiki/Elemental)
- [Sylph (Wikipedia)](https://en.wikipedia.org/wiki/Sylph)
- [Elemental Embodiment (Tropedia)](https://tropedia.fandom.com/wiki/Elemental_Embodiment)
- [Black Clover, esprits élémentaires (Honey's Anime)](https://honeysanime.com/black-clover-what-is-the-last-elemental-spirit-you-heard-it-here-first-spoiler-alert)
- [Golem robot de Castle in the Sky, mousse et poids (Wikipedia)](https://en.wikipedia.org/wiki/Castle_in_the_Sky)
- [Retrofuturism in Castle in the Sky (Dust on the VCR)](https://dustonthevcr.substack.com/p/castleinthesky)
- [Magical stone golem, runes et cœur (itch.io)](https://kostas3d.itch.io/magical-stone-golem-3d-game-asset)
- [Golems species (World Anvil)](https://www.worldanvil.com/w/vanthelia-ritterwolf/a/golems-species)
- [Draw fire, a comprehensive tutorial (Clip Studio)](https://tips.clip-studio.com/en-us/articles/8097)
- [Basic guide on drawing various forms of flame (Clip Studio)](https://tips.clip-studio.com/en-us/articles/8114)
- [How to paint water: droplet, flowing water, waves (Clip Studio)](https://tips.clip-studio.com/es-es/articles/6179?org=1)
- [Effect for expressing water (MediBang)](https://medibangpaint.com/en/use/2020/09/effect-for-expressing-water)
- [Recognisable characters with strong silhouettes (Creative Bloq)](https://www.creativebloq.com/art/character-design/how-to-design-instantly-recognisable-characters-using-strong-silhouettes)
- [How to animate a magical energy attack (blog)](https://wxndiipng.blogspot.com/2025/03/how-to-animate-magical-energy-attack.html)
