# Bugs à corriger : rendus avancés des cosmétiques (shaders, reflets, menu Apparence)

Tu travailles sur le mod Phynaria Utilities (Minecraft 26.1.2, NeoForge). Les fonctions de la section 4 bis et 5 quater du guide créateurs (`add_`, `trans_`, `cam_`/`camy_`, `ctrl_…`, calque `_r`) marchent sans shader, mais trois problèmes ont été constatés en jeu le 2026-11-03 (captures `2026-11-03_23.58.59`, `23.59.52`, `2026-11-04_00.00.55`, `00.02.53`, profil `ftb-evolution-2`).

## 1. Avec un pack de shaders, les rendus avancés disparaissent (bloquant)

**Symptôme.** Avec shader (capture `23.59.52`), `aura_brasier` est porté (le chat le confirme) mais **rien n'est visible** sur le joueur. Sans shader (`00.00.55`, `00.02.53`), la même aura est visible : halo additif autour de la silhouette, colonnes, anneau au sol. Les autres cosmétiques portés au même moment (hibou, queue) restent visibles avec shader : seules les parties spéciales manquent.

**Modèle de test.** `cosmetiques/auras/aura_brasier/aura_brasier.bbmodel` : tout l'effet est dans des groupes `add_` (additif), dont la plupart sont aussi `cam_` ou `camy_`, avec des `ctrl_alpha`, `ctrl_uv` et `ctrl_lumiere`.

**Attendu.** Les groupes `add_` restent visibles sous Iris (passe translucide ou émissive, comme l'armure chargée du creeper ou le rayon de balise), ainsi que `trans_` (le jet de vapeur `trans_jet_*` de `ailes_mecaniques`) et le calque `_e`.

**Pistes supposées.** Type de rendu additif non pris en charge par la passe d'Iris, ou dessiné hors de la passe que le shader compose ; `cam_` recalculé avec une matrice de vue absente dans la passe d'ombre ou de G-buffer ; profondeur non écrite (normal en additif) mais objet écarté par un test du pipeline du shader.

## 2. Reflets `_r` : appliqués sur toute la face, découpe comprise (sans shader)

**Symptôme.** Sur `ailes_mecaniques` (captures `00.00.55`, `00.02.53`), chaque lame découpée par alpha montre un **rectangle clair semi-transparent** : le contour du cube entier. Les lames sont des plaques dont la forme vient de la texture (pixels alpha 0 autour). Le reflet est dessiné sur tout le quad, y compris là où la texture principale est transparente.

**Attendu.** Le reflet (comme le calque `_e`) ne s'ajoute que sur les pixels opaques de la texture principale : même test d'alpha (cutout) que la passe principale.

**En attendant.** Nous avons retiré les calques `_r` de tous les modèles.

## 3. Menu Apparence : l'additif y est dessiné opaque

**Symptôme.** Dans l'aperçu du menu Apparence (capture `23.58.59`), `aura_brasier` apparaît en **carrés noirs** et en taches sombres devant et derrière le joueur. Les groupes `add_` y sont dessinés comme des faces opaques : le noir, censé être invisible, couvre le personnage. Les `cam_` n'y sont pas tournés (le guide l'annonce, mais sans l'additif le résultat est illisible).

**Attendu.** Le menu utilise le même rendu additif qu'en jeu (et, si possible, oriente les `cam_` vers sa caméra fixe).

**En attendant.** Nos textures additives sont désormais transparentes là où elles sont presque noires, ce qui supprime les carrés dans le menu ; l'effet reste incomplet tant que l'additif n'y est pas rendu.

## Mise à jour du 2026-11-04 (captures `2026-11-04_00.30.55` et `00.31.13`)

- **Shader, calque `_e`** : avec shader, **aucune** lueur `_e` n'est visible, ni sur `ailes_mecaniques` (filets ambrés, fentes de foyer, cadrans), ni sur `haut_de_forme_mecanique` (lentilles) ; sans shader, toutes sont visibles. Le problème du point 1 touche donc aussi le calque `_e`, pas seulement `add_` et `trans_`.
- **Menu Apparence, toujours** : nos textures additives n'ont plus de noir, mais les disques de lueur (`add_` dans `cam_`, placés **derrière** chaque partie du corps) s'affichent **par-dessus** le personnage, en rouge plein. Le menu semble dessiner ces faces sans test de profondeur contre le joueur, ou après lui, et sans additif. Demande : dans le menu, même rendu qu'en jeu (additif, profondeur, `cam_` tourné vers la caméra du menu) ; à défaut, une requête Molang `query.is_in_menu` pour que le modèle masque ce qu'il ne peut pas y montrer.
- **En jeu, sans shader** : l'aura s'affiche comme prévu (halo, colonnes, anneau) : la conception du modèle est bonne, seuls le menu et les shaders posent problème.

## 4. Particules Minecraft (`emit_mc_…`) : loin du point de départ et immobiles

**Symptôme** (capture `2026-11-04_00.31.13`, `familier_hibou_mecanique`) : les particules `white_ash` du souffle de l'hélice apparaissent **à plusieurs blocs** du joueur, sur le côté, et **ne suivent pas** le hibou ni ses déplacements.

**Données du modèle** : trois groupes vides `emit_mc_white_ash`, rotation (180, 0, 0) pour que +Y vise le bas, chaîne `body > fam_elan > fam_inertie > fam_orbite > fam_pos > fam_virage > fam_regard > fam_snap > corps > rotor`. Pivots : (8,62 ; 24,06 ; 1,86), (7,38 ; 24,06 ; 1,86), (8 ; 24,06 ; 0,78) **en pixels**, soit à environ un demi-bloc à droite du centre du joueur, juste sous l'hélice. Ces groupes suivent les animations de leurs parents (position, rotation).

**Attendu** (guide 5 ter §2 et §4) : la particule part du pivot du groupe, en pixels (÷ 16 pour des blocs), transformé par la pose et l'animation de toute la chaîne, à chaque émission, comme pour les points `emit_<nom>` des particules modélisées.

**Pistes supposées** : pivot lu en blocs au lieu de pixels (un facteur 16 donnerait un écart de 8 blocs) ; ou transformation des groupes parents non appliquée aux points `emit_mc_` (position figée au chargement, ou au repère de l'entité sans l'animation).

## Ce qui marche (sans shader, confirmé par les mêmes captures)

- Calque `_e` : les lueurs sont visibles la nuit.
- `ctrl_teinte` piloté par `query.is_in_rain` (variable mémorisée `v.pluie`) : le métal s'assombrit sous la pluie.
- Halo additif `add_` + `cam_`, colonnes `camy_`, anneau au sol de l'aura.
