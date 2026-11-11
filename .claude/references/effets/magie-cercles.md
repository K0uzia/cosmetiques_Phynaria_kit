# Référence — Cercles magiques, runes, sceaux, invocations

Fiche documentée (2026-11-04). Codes génériques du « cercle magique » d'anime et de jeu ; aucun sceau, alphabet ou blason d'une œuvre n'est repris : écritures et symboles sont inventés pour chaque pièce.

## Codes visuels

- **Un cercle, des formes dedans** : presque toujours rond, avec des polygones, étoiles et anneaux de plus en plus complexes à l'intérieur. Les couches emboîtées disent l'harmonie, la grandeur, le divin (trope « Heavenly Concentric Circles »).
- **Structure type**, de l'extérieur vers le centre :
  1. double filet extérieur (un épais, un fin) ;
  2. **bande d'écriture** : une rangée de glyphes inventés entre deux filets ;
  3. polygone ou étoile (pentagramme, hexagramme, octogramme, ou triangles entrelacés) dont les pointes touchent l'anneau ;
  4. petits cercles aux sommets (nœuds), chacun avec un signe ;
  5. anneau intérieur, puis un symbole central (œil, étoile, fleur, rune maîtresse).
- **Symétrie radiale** : 5, 6 ou 8 branches. Les bandes de texte cassent la symétrie et rendent le cercle vivant.
- **Deux familles** : cercle « occidental » (anneaux, étoile, texte) et cercle « géométrique » (carrés et triangles, plus anguleux, plus technique). Les triangles et les angles vifs se lisent plus agressifs ; les anneaux et les fleurs, plus sacrés.
- **Couleur unique par lanceur** : le cercle prend la couleur de la magie de son porteur (code couleur de `elements.md`), lignes vives sur un fond presque invisible.

## Formes et couleurs

- Lignes **nettes et épaisses**, deux ou trois niveaux (filet maître, filet secondaire, glyphes). **Cercle au sol : filets de 8 à 17 texels au moins** (retour en jeu du 2026-11-06, `effet_berenice` : des traits de 3–5 texels s'effacent, car une plaque vue en biais est lue à un niveau de mipmap bien plus bas que de face). Le « 3 à 4 texels » de `modeling.md` vaut pour une pièce vue de face.
- Remplissage presque nul : le cercle est un dessin de lumière ; un léger voile dans la bande de texte suffit.
- Palette : cœur des lignes presque blanc teinté, liseré de la teinte, voile très sombre de la même teinte. Les glyphes un ton plus doux que les filets.

## Mouvement et timing

- **Les couches tournent à des vitesses différentes, souvent en sens contraire** : c'est ce qui fait « mécanisme » et hypnotise. Repères : anneau de texte un tour en 20–40 s, étoile en sens inverse en 30–60 s, nœuds qui pivotent sur eux-mêmes.
- **Apparition** (0,6–1,5 s) : un point de lumière, puis le cercle extérieur se trace (ou s'agrandit de 0 à 1 avec un léger dépassement), puis les couches intérieures apparaissent l'une après l'autre (décalage 0,1–0,2 s), les glyphes s'allument en dernier. Disparition : plus rapide (0,3–0,5 s), l'échelle ou l'opacité retombent, ou le cercle se fragmente.
- **Pendant un sort** : pulsation de lumière 0,5–1 s, colonne de lumière qui monte du cercle, cercles empilés à plusieurs hauteurs (le plus petit en haut), ou cercle vertical devant la main.
- Le cercle se place **sous les pieds** (invocation, aura), **derrière le dos** (puissance, divin) ou **devant la main** (attaque).

## Langage anime

| Mise en scène | Lecture |
|---|---|
| Cercle qui naît sous les pieds | concentration, invocation, transformation |
| Cercles empilés le long d'un axe | sort puissant, canon de lumière |
| Cercle qui se brise en éclats | sort annulé, sceau rompu |
| Anneaux de lumière qui traversent le corps | transformation, éveil |
| Sceau sur la peau, sur un objet | lien, malédiction, contrat |

## Traduction dans le mod

- **Un anneau = une seule plaque de 0,15 px découpée par alpha, motif symétrique** (recette validée : des segments décalés font des pointillés, des segments chevauchés des créneaux). Une plaque par couche qui tourne, chacune dans son groupe, décalées de 0,03 px au moins en hauteur (pas de faces coplanaires).
- **Rotation** : dans un `overlay_<nom>`, exactement 360°·k par boucle (boucle commune, par exemple 48 s : anneau de texte 1 tour, étoile −1 tour, nœuds 4 tours). Elle ne saute plus entre deux états.
- **Rendu** : tracé en `trans_` or (le vrai dessin, visible de jour et avec shader) + `_e` léger, lueur `add_` douce par-dessus (noir invisible). Pas de calque `_e` sur une pièce **tout** en `add_`.
- **Sous les pieds** : groupe de `body` à plat sous le pivot, masqué quand le corps n'est pas debout (échelle 0 dans `sneak`, `glide`, `swim`, `sleep`, `mount`, `fly`) ; au moins 0,3 px au-dessus du sol pour éviter le scintillement.
- **Derrière le dos** : `cam_` centré derrière la nuque, reculé (6–8 px) pour rester derrière le corps sous tous les angles. Un cercle face caméra tourne quand même dans son plan (rotation Z de l'animation, appliquée après l'orientation).
- **Devant la main** : enfant de `right_arm`, vertical, montré seulement à l'`attack` (échelle 0 → 1 en 0,15 s, *step* ou *catmullrom*), ou en `event_` ; `q.attack_time` pour suivre le geste.
- **Apparition** : `event_equip` ; échelle des couches en cascade, `ctrl_alpha` en fondu (`add_`/`trans_` font un vrai fondu), glyphes allumés en dernier.
- **Glyphes qui changent** : `ctrl_uv` en pas entiers sur une bande d'images côte à côte (recette du film de `aura_brasier`), ou texture animée si la texture totale reste petite (toute la texture principale est empilée).
- **Colonne de lumière** : plaque `add_` en `camy_` au centre du cercle, film qui monte par `ctrl_uv`.
- **Particules** : étincelles modélisées qui montent depuis les nœuds (`emit_` aux sommets de l'étoile, Élan 100 %) ; `emit_mc_enchant` (glyphes de la table d'enchantement) en appoint discret, à juger en jeu.
- Limites : extension < 60 px par axe (un cercle au sol de 20 px de rayon reste loin de la limite) ; texture 512² partagée avec toute la pièce : un cercle de 128² découpé suffit.

## Avec shader

`add_` invisible : la version `trans_` du cercle (alpha 60–160 sur les lignes) est la seule visible. La concevoir comme le vrai dessin, l'additif étant l'éclat en plus.

## Pièges

- Cercle opaque plein : se lit comme un tapis ou une assiette. Lignes seulement.
- Trop de détails fins : à 3 blocs, un glyphe de 2 texels disparaît ; préférer peu de signes gros.
- **Tout en `add_` sombre** : un additif or brun (≈ 120) ne se voit pas sur un sol clair de jour (`effet_berenice` v1–v2, en jeu). Tracé en `trans_` or semi-opaque (alpha 150–230) + `_e` léger pour la nuit, lueur `add_` floue et basse résolution par-dessus ; mesurer le cumul `_e` compris. Contrôler avec une simulation à la taille en jeu (`cosmetiques/effets/effet_berenice/.build/sim_jeu.py`), pas seulement le rendu net.
- Cercle en l'air vu d'en dessous : faces `down`.
- **Faces horizontales en miroir sur X en jeu** (`effet_berenice` v3 : 8 arcs en « nid » ; mesuré avec `docs/dev/tests_rendu/test_uv_up.bbmodel`, `fonctions-avancees.md`, Pièges) : un cercle au sol ou en l'air se fait en **plaques entières à motif symétrique** (anneaux, motifs tous les 45° ; **validé en jeu** sur `effet_berenice` v4, 2026-11-06) ; un secteur ou un glyphe asymétrique passe par `tools/uv_horizontal.py`. Apparition : échelle depuis le centre (intérieur d'abord) et `ctrl_alpha`.
- Couches coplanaires : z-fight sous shader. Décaler chaque plaque.
- Cercle au sol visible en sneak ou en élytres : il suit le corps couché et se met debout. Le masquer.
- Lettres d'un alphabet réel ou sceau d'une œuvre connue : interdit ; inventer les glyphes (traits, arcs, points).
- Rotation dans l'état plutôt qu'en `overlay_` : saut visible à chaque changement d'état.

## Sources

- [TV Tropes : Heavenly Concentric Circles](https://tvtropes.org/pmwiki/pmwiki.php/Main/HeavenlyConcentricCircles)
- [TV Tropes : Geometric Magic](https://tvtropes.org/Main/GeometricMagic)
- [Clip Studio Tips : « How to Create Magic Circles » (règle symétrique, cercles concentriques, texte en anneau)](https://tips.clip-studio.com/en-us/articles/1910)
- [Clip Studio Tips : cercles magiques à la règle spéciale](https://tips.clip-studio.com/en-us/articles/3356) et [autre tutoriel](https://tips.clip-studio.com/en-us/articles/4553)
- [Arcane Odyssey : guide de création d'un cercle magique](https://forum.arcaneodyssey.dev/t/how-to-create-a-magic-circle-quest5s-guide/32530)
- [Cercles de transmutation procéduraux (couches et symétries)](https://blendermarket.com/products/procedural-transmutation-circles)
- [Wiki Nanoha : cercles magiques (deux familles, couleur du lanceur)](https://nanoha.fandom.com/wiki/Magic_circle)
