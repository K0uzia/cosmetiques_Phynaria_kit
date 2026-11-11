# Slimes et mascottes — slime, mascotte kawaii, créature-nuage

Fiche de référence (2026-11-04). Série du dépôt : ensembles **Kawaii** et **Pâtisserie** (2026-11-03) : `familier_kawaii_mochi` (recette de bosses arrondies et de squash-and-stretch), `oreilles_kawaii`, `ailes_kawaii_nuage`, `queue_kawaii`, `aura_kawaii`, `familier_kawaii_chat`… Comportements : `.claude/styles/familiers.md`.

## 1. Codes visuels essentiels

- **Slime** : goutte de gelée, silhouette **en goutte ou en guimauve qui fond**, base plate posée, sommet arrondi ou en pointe molle. Dans le RPG japonais, c'est le monstre le plus faible et le plus **mignon** : tension de surface forte (il garde sa forme), deux yeux, un sourire, **reflet blanc** net en haut. Translucide, parfois un objet ou un noyau visible à l'intérieur.
- **Mascotte kawaii** (*yuru-chara*, « mascotte molle ») : formes de base (**cercles**), couleurs vives ou pastel, proportions de **bébé** (schéma de Lorenz : grosse tête, grand front, yeux bas et écartés, petit nez, petite bouche, joues rondes), allure inoffensive, souvent née d'un **jeu de mots** ou d'un objet du quotidien (un nuage, un gâteau, une lanterne).
- **Créature-nuage** : bosses rondes qui se touchent, ventre plus grand qui porte le visage, petites bosses latérales comme des bras (`familier_kawaii_mochi`).

| Registre | Codes |
|---|---|
| Mignon (cœur du registre) | Yeux à reflet blanc, joues roses, bouche en « ω » ou en petit « v », pastel, rond partout |
| Élégant | Gelée cristalline, une seule couleur, noyau lumineux, pas de visage ou un visage minimal |
| Menaçant | Slime sombre qui déborde, yeux multiples, bulles qui éclatent, objets engloutis |

## 2. Silhouette et proportions (échelle du dépôt)

- **Proportions chibi** : tête/corps 1:1 à 1:2 ; pour une mascotte sans corps distinct, le visage occupe le tiers inférieur de la masse (grand front).
- **Yeux** : 1/2 à 3/4 de la hauteur de la tête en chibi ; placés **bas** et **écartés** ; un reflet blanc de 1/3 de l'œil.
- **Slime-familier** : 5–8 px de large, 4–7 px de haut au repos ; posé sur l'épaule (y ≈ 24) ou flottant à côté (x ≈ ±12).
- **Nuage-familier** : 7–10 px, 3 à 5 bosses.
- **Oreilles de mascotte** (`head`) : grosses et rondes, 3–6 px, ancrées sur le dessus de la tête ; `phys_` pour qu'elles ballottent.

## 3. Matières et couleurs (HD 32–40 texels/px)

- **Gelée** : dégradé de la normale (clair en haut, saturé en bas), **reflet blanc net** en haut (forme de fenêtre ou de banane, 1/5 de la largeur), **contre-reflet** plus faible en bas, **contour légèrement plus clair** (c'est ce qui fait lire la translucidité), ombre de contact sombre sous la base. Ne pas multiplier les reflets : un grand, un petit.
- **Bulles** à l'intérieur : cercles clairs à liseré, 3–6 texels.
- **Nuage, guimauve** : teinte calculée depuis la normale lissée de chaque bosse (on lit une boule, pas des plaques), ombre de contact entre bosses (`familier_kawaii_mochi`).
- **Palettes** : crème, rose, lavande, menthe, bleu ciel ; une couleur de corps + une d'accent (joues, ruban).
- **Visage** : yeux noir bleuté (pas noir pur), reflet blanc, joues roses en ellipses douces, bouche fine.

## 4. Mouvement, comportement, attitude

- **Squash-and-stretch** : tout le personnage. Avant un saut, il **s'écrase** (largeur ×1,2, hauteur ×0,8), puis **s'étire** en montant (×0,85 / ×1,2), redevient rond au sommet, s'écrase à l'atterrissage avec un rebond amorti (1–2 rebonds). **Volume constant** : ce qu'il gagne en largeur, il le perd en hauteur.
- **Repos (8 s)** : respiration en squash très léger (±3 %, 2–4 s), clignements irréguliers, petit balancement ; un comportement tiré au hasard toutes les 6 s environ (`familiers.md`) : sautiller, se tourner vers le joueur, s'étirer en hauteur, s'aplatir comme une crêpe, faire une bulle.
- **Joie** : sautille 2–3 fois vite. **Peur / blessure** : s'aplatit, tremble (gelée qui vibre 0,3 s). **Sommeil** : affaissé, yeux en arc fermé.
- **Lien avec le joueur** : saute avec lui (`event_jump`), s'écrase à l'atterrissage (`event_land`, `q.land_speed`), se colle à lui en `sneak`.
- **Apparition** : « plop » : échelle 0 → 1,3 → 0,9 → 1 en 0,4 s, avec un étoilement.

## 5. Langage anime

- **Symboles d'émotion** (*manpu*) : cœurs, étoiles, notes de musique, goutte de sueur, petites lignes de rougeur, « zzz », point d'exclamation au-dessus de la tête.
- **Yeux qui changent de forme** : arcs (content), croix (sonné), spirales (étourdi), étoiles (émerveillé).
- **Rebond** souligné par de petites lignes d'impact au sol, des paillettes.
- **Bulles** qui montent d'un slime.

## 6. Traduction dans le mod

- **Corps** : recette `familier_kawaii_mochi` (polyèdres arrondis fermés, facettes de 0,3 px découpées, âme pleine) ; groupe `fam_squash` à pivot **sous** le corps, canal `scale` (fonctionne dans le mod), volume constant (x·y·z ≈ 1).
- **Gelée translucide** : `trans_` (alpha 150–210, reflets à 255) avec un noyau opaque plus petit au centre ; visible avec shader. `add_` seulement pour une lueur intérieure en plus.
- **Clignement** : échelle y des yeux (0,1 s) à intervalles irréguliers ; **expressions** : deux ou trois plaques de visage dans le même groupe, alternées par `ctrl_alpha` (opaque : −1 cache d'un coup, correctif du 2026-11-04 à vérifier en jeu) ou par échelle 0.
- **Symboles d'émotion** : petites plaques de 1,5–2,5 px en `cam_` au-dessus de la tête, qui apparaissent par échelle pendant le comportement ; ou particules modélisées qui **montent** (cœurs, notes ; recette `aura_kawaii`).
- **Oreilles, pompons** : `phys_` (`phys_oreille_r40_a50`), non simulé par le renderer, à juger en jeu.
- **Hasard** : tirage par tranche de 6 s avec `q.instance_seed` (formule de `familiers.md`).
- **Lumière** : calque `_e` embarqué (série kawaii) ; avec shader il disparaît, donc couleurs claires dans la texture.

## 7. Pièges

- **Squash sans conservation du volume** : il « gonfle » au lieu de s'écraser.
- **Pivot du squash au centre** : il s'enfonce dans l'épaule ou décolle du sol ; pivot sous la base.
- Trop de reflets : la gelée devient du plastique ou du verre.
- **Noir pur** dans les yeux et contours : dur, pas kawaii.
- **Familier passif** (« il fait rien », `familier_givre`) : il faut des comportements au hasard et des réactions au joueur.
- Visage trop haut sur la masse : il paraît adulte.
- Reprendre une mascotte célèbre ou un slime de jeu identifiable (forme en goutte + sourire + couleur d'une licence) : composer la sienne (autre objet de départ, autre visage).

## 8. Sources

- [Yuru-kyara (Wikipedia)](https://en.wikipedia.org/wiki/Yuru-kyara)
- [Aesthetic of cuteness dimensions in a city mascot (KnE Social Sciences)](https://knepublishing.com/index.php/KnE-Social/article/view/7592)
- [Thesis on kawaii and baby schema (ZHdK, M. Galliker)](https://interactiondesign.zhdk.ch/site/assets/files/7803/thesis_manami_galliker.pdf)
- [How to draw chibi body ratio (Clip Studio)](https://tips.clip-studio.com/es-es/articles/4806?org=1)
- [Body proportion in chibi drawing (Clip Studio)](https://tips.clip-studio.com/fr-fr/articles/4829?org=1)
- [Pixelaria devlog, adorable slimes (itch.io)](https://itch.io/devlog/1120615/-pixelaria-devlog-behind-the-pixels-of-our-adorable-slimes.amp)
- [Pixel tutorial: slimes (itch.io)](https://itch.io/t/1471610/pixel-tutorial-slimes)
- [How to animate a blob monster with personality](https://learnplayteach.pages.dev/posts/content/how-to-animate-a-blob-monster-with-personality)
- [Squash and stretch mastery (Playbooks)](https://playbooks.com/skills/dylantarre/animation-principles/squash-stretch-mastery)
- [Blob Monster (TV Tropes)](https://tvtropes.org/pmwiki/pmwiki.php/Main/Blobmonster)
