# Référence — braises, chaleur et mirage

Fiche documentée (2026-11-08) pour `aura_brasier` v4. À lire avec `auras.md` (recette d'aura qui marche en jeu), `elements.md` (Feu) et `principes-fx-anime.md`.

## Le vrai sujet

- **Couleur de corps noir** : une braise rougeoie par sa seule chaleur. Rouge sombre vers 800 K, orange vif vers 1 200 K, jaune blanc au plus chaud ; une petite hausse de température change beaucoup la couleur et l'éclat. Une braise qui refroidit passe donc du jaune blanc à l'orange, au rouge, puis s'éteint (cendre).
- **Braises détachées** : légères, elles montent dans l'air chaud en S (tourbillons), rapetissent et pâlissent en 0,5 à 2 s.
- **Mirage** : l'air chaud fait onduler ce qui est derrière lui ; on le voit au-dessus d'un feu, d'une route en été. En dessin et en anime, il se code par des lignes ondulées fines au-dessus de la source, qui montent et s'effacent.
- **Sol** : sous une forte chaleur, le sol noircit et se fend ; les fentes rougeoient (coulée de lave refroidie, braises d'un foyer).

## Codes de style (VFX de jeu, anime)

- Braises : du blanc or vers l'orange puis le rouge, dérive sur un champ tourbillonnaire, fondu en cendre ; distorsion par réfraction (ici impossible : on la suggère par les ondulations).
- Chaleur d'un personnage : liseré chaud au bord de la silhouette, air qui tremble au-dessus de la tête, sol qui se fend sous les pieds, braises qui s'échappent. Pas de langues de flamme opaques (c'est un incendie, « mec en feu »).

## Traduction dans le mod (`aura_brasier` v4)

| Élément | Construction |
|---|---|
| Liseré | disques `add_` en `cam_` reculés derrière chaque partie du corps (recette v3), dégradé serré or clair → orange → rouge sombre, bord haut étiré |
| Filets de chaleur | colonnes `add_` en `camy_` derrière le joueur, fond rouge très sombre + 2 ou 3 filets ondulés de 2 texels, film de 8 images (`ctrl_uv`) |
| Mirage | plaque `add_` en `camy_` derrière la tête, arcs ondulés or pâle qui montent (film `ctrl_uv`) |
| Braises | plaques `add_` de 1 à 1,6 px dans le `camy_`, montée en S en Molang (`math.mod`), échelle qui baisse, couleur par `ctrl_uv` (4 images : or blanc, or, orange, rouge) ; + `particle_braise` (Monte, Fondu) |
| Sol | brûlure `trans_` sombre légère (alpha ≤ 95 : contraste de jour), fissures de Voronoï `add_` (traits de 3 texels), anneau de chaleur dentelé `add_` qui tourne |
| De jour | doubles `trans_` orangés (alpha 90–95) plus loin que tous les `add_` |

## Sources

- [Wikipedia : A smoldering ember (pyrométrie)](https://en.wikipedia.com/wiki/File:A_smoldering_ember_pyrometry.png)
- [College Physics : braises d'un foyer et rayonnement](https://collegephysicsanswers.com/openstax-solutions/log-fireplace-burns-nearly-hour-which-point-it-consists-mostly-small-hot-embers)
- [80.lv : feu de camp VFX (braises, distorsion de chaleur)](https://80.lv/articles/creating-a-campfire-vfx-in-ue4)
- [BlenderNation : distorsion de chaleur et étincelles](https://www.blendernation.com/2022/05/25/blender-vfx-heat-distortion-and-sparks-full-tutorial/)
- [Toon Boom forum : air chaud qui ondule en animation 2D](https://forums.toonboom.com/t/hot-wevy-air-effect/753)
