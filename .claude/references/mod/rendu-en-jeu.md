# Rendu en jeu : ce que font vraiment le mod et Minecraft

À lire à la demande. Mesuré le 2026-11-07 dans le bytecode de Phynaria Utilities 1.4.0 (`CosmeticRenderTypes`, `CosmeticLayer.passes/cube/drawn`, `TeleportEffects.submit`, `CosmeticEffects`, `CosmeticParticles$Fall`) et de Minecraft 26.1.2 (NeoForge, client non obfusqué : `RenderPipelines`, `BlendFunction`, `DynamicTexture`, shaders `entity.vsh/fsh`, `light.glsl`, `lightmap.fsh`). Réglages du joueur lus dans `profiles/ftb-evolution-2/options.txt`. Reproduit par le mode « comme en jeu » (`tools/visionneuse.js`, `render_bbmodel.py` avec `JEU=1`) ; calibration : `docs/dev/tests_rendu/calibration_jeu.png` (script à côté).

## Les six différences qui trompaient (rendu studio contre jeu)

1. **Le fond.** Studio : fond presque noir. En jeu : ciel clair de jour (gris couvert ≈ 170–200, bleu ≈ 120/167/255). `add_` et `_e` s'**ajoutent** au fond (ONE, ONE) : un additif à 60–130 sur un ciel à 180 donne du blanc délavé, sans couleur. Ce qui brille dans le Vestiaire peut disparaître en jeu de jour.
2. **La distance et la densité de pixels.** Studio : champ de 30°, cadrage serré, anticrénelage (MSAA, sur-échantillonnage × 2 dans le renderer). En jeu : champ de 70°, écran de 2560 × 1369 du joueur, pièce à 3 blocs (« Essayer ») ou 5–12 blocs, **aucun lissage**. Un trait de 1–2 texels, une plaque fine, une lueur floue en basse résolution deviennent escaliers, pointillés ou carrés (fissures « pixel », étincelles v1 effacées).
3. **Mipmaps depuis le guide du 2026-11-08 (demandes 6).** De près, lecture au plus proche (texel par texel). De loin, quand un texel devient plus petit qu'un pixel d'écran, le jeu lit des copies réduites (jusqu'à 4 niveaux, réglage vidéo « Niveaux de mipmap » du joueur, lu au chargement du cosmétique ; à 0 : aucune) : un trait de 1–2 texels reste visible, **plus pâle et adouci**, au lieu de disparaître ou de faire des escaliers (vérifié par le développeur sur une grille de traits d'un texel). Texture animée : les niveaux s'arrêtent avant de mélanger deux images. Avant (1.4.0, mesuré le 2026-11-07) : `DynamicTexture` à 1 niveau, NEAREST, un trait fin était sauté ; les leçons « trait fin effacé » d'avant le 2026-11-08 (`effet_berenice` v1–v2, étincelles v1, rayon v1) viennent de là. Supposé (pas encore vu en jeu) : de loin, les îlots voisins de l'atlas et le transparent autour d'une découpe se mélangent au bord (moyenne 2 × 2, 4 × 4… jusqu'à 16 × 16 texels) ; garder une marge ou répéter la couleur du bord autour des îlots fins. Le mode « comme en jeu » choisit un niveau par triangle (approché ; `MIPMAPS=0` pour les couper).
4. **La lumière des faces.** Minecraft : deux lumières fixes `(0.2, 1, −0.7)` et `(−0.2, 1, 0.7)`, `min(1, (max(0,n·L0)+max(0,n·L1))·0,6 + 0,4)` : dessus 1,0, nord/sud 0,74, est/ouest 0,50, **dessous 0,40** ; recto et verso éclairés chacun (`PER_FACE_LIGHTING`, aucune face éliminée en opaque ni en `trans_`). Puis × lumière du monde (lightmap du bloc où est le joueur ou l'effet). Studio : 0,55 à 1,0, beaucoup plus doux.
5. **La nuit.** Sans shader, avec la luminosité « Lumineux » du joueur (`gamma:1.0`), la lightmap du ciel nocturne vaut ≈ 0,6 (le monde reste lisible, captures `16.44.*`) ; le Vestiaire studio multipliait par 0,16 et faisait tout « briller ». Avec shader (Complementary + Euphoria) : bien plus sombre, brume et halo ; pas reproductible exactement.
6. **Les particules.** Studio : lancées tout le temps, 64 au plus, chute lente. En jeu : réglage **Quand** (défaut **En vol** : rien au repos !), limite par joueur 64/128/256, mouvement du mod (ci-dessous), `emit_mc_` dessinées par Minecraft ; aucune particule de son propre cosmétique en 1re personne. Un effet de téléportation ignore Quand (sauf Jamais).

Aussi : `trans_` écrit la profondeur (un `add_` ou une particule derrière une face `trans_` n'est pas dessiné ; écrit dans le guide 4 bis le 2026-11-08) ; la copie du joueur au départ suit position **et échelle** depuis le guide du 2026-11-08 (coupée sous 0,05, comme `charge` et `arrivee` : `categories/effets.md`).

## Passes et pipelines (mod 1.4.0)

| Passe (ordre) | Cubes | Pipeline | Mélange | Profondeur | Faces | Lumière |
|---|---|---|---|---|---|---|
| OPAQUE | hors `trans_`/`add_` | `entityCutout` (alpha < 0,1 jeté) | aucun | test + écriture | recto et verso | faces × lightmap du lieu (`Lumineux` du staff : pleine) |
| TRANSLUCENT | `trans_` | `entityTranslucent`, trié (sortOnUpload) | SRC_ALPHA, 1−SRC_ALPHA | test + **écriture** | recto et verso | idem |
| ADDITIVE | `add_` | `phynariautilities:pipeline/cosmetic_additive` (core/entity, `EMISSIVE`, `NO_CARDINAL_LIGHTING`, ALPHA_CUTOUT 0,1) | ONE, ONE en 1.4.0 ; **couleur × alpha du texel** depuis le guide du 2026-11-08 (alpha 0 seul jeté) | test ≤, sans écriture | aucune éliminée | aucune |
| GLOW | tout sauf `add_`, texture `_e` | même additif | ONE, ONE | test ≤, sans écriture | — | aucune ; **jour comme nuit** (aucun test d'heure) |
| REFLECT | cubes à reflet `_r` | même additif | ONE, ONE | — | — | — |

Couleur de sommet (`CosmeticLayer.cube`) : `ctrl_alpha` (produit des groupes parents, borné 0–1) ; `ctrl_teinte` (0–4) ; `ctrl_lumiere` (0–8, sur `_e`). ADDITIVE : RGB = teinte × alpha ; GLOW : teinte × alpha × lumière ; opaque : caché sous alpha 0,1 ; translucide : alpha × alpha. Effets de téléportation : lumière = lightmap à leur position (`LevelRenderer.getLightCoords`), même chemin que les cosmétiques portés (`submitPet` → `passes`). Menu Apparence : `add_` et `_e` passent par une copie (alpha = max(R,G,B)), voir `rendus-avances.md`.

Nos textures `add_` sont peintes alpha 255 et intensité dans le RGB (mesuré sur rayon, étincelles, portail v1) : rien ne change pour elles. **Depuis le guide du 2026-11-08** : chaque texel `add_` (et `_e`) ajoute *couleur × alpha* ; une lueur peut s'estomper par l'alpha (couleur gardée, alpha vers 0) au lieu d'un dégradé peint vers le noir, les deux se combinent ; seul l'alpha 0 est jeté (avant : alpha ignoré, texels sous 26 jetés). Un `_e` à alpha 225 brille 12 % de moins qu'avant.

## Particules modélisées (CosmeticParticles$Fall, blocs/s)

| Mouvement | gravité | vitesse limite | balancement |
|---|---|---|---|
| Légère | 1,2 | 0,9 (14 px/s) | 0,6 |
| Normale | 6 | 4 | 0,2 |
| Lourde | 16 | 20 | 0 |
| Flotte | 0 | 0 | 0,15 |
| Monte | −0,8 | 0,8 vers le haut | 0,3 |

`emit_mc_` : dessinées par Minecraft (feuilles de particules vanilla, taille ≈ 0,1–0,25 bloc, durées propres) ; le mode « comme en jeu » les approche par des carrés colorés (table `PARTS_MC` de `visionneuse.js`).

## Réglages du joueur (options.txt, 2026-11-07)

`fov:0.0` (70°), `gamma:1.0` (Lumineux), `mipmapLevels:4` et `textureFiltering:1` (RGSS : terrain seulement, pas les textures du mod), `particles:0` (toutes), `renderClouds:false`, écran 2560 × 1369, Sodium 0.9.2, Iris 1.11.4 (shader Complementary Unbound r5.9.3 + Euphoria, actif sur certaines captures).

## Ce que le mode « comme en jeu » ne reproduit pas

Shaders (Iris : ombres, brume, halo, bloom ; la case « nuit + shader » est une approximation sombre), lumière exacte du lieu (torches, grottes, pluie), brouillard lointain, particules Minecraft exactes, `ctrl_teinte`, reflets `_r`, ombre du joueur, skin du joueur (mannequin gris).

## À demander au développeur (si on veut changer le comportement)

- Option pour que `add_` reste visible derrière un `trans_` (passe additive avant l'écriture de profondeur du translucide, ou translucide sans écriture) : non retenue (guide du 2026-11-08 : « n'enfermez pas une lumière `add_` dans une enveloppe `trans_` »).
- Faits dans le guide du 2026-11-08 (`docs/dev/demandes_mod_6.md`) : mipmaps, `add_` et `_e` dégradés par l'alpha, échelle de la copie du départ, aperçu `depart`/`arrivee` dans le menu.
