# Morts-vivants — squelette, spectre, crâne, liche

Fiche de référence (2026-11-04). Pièce livrée proche : `familier_abyssal` (petit crâne cornu abyssal qui flotte, os charbon, reflets violets, vert acide), à reprendre pour tout crâne. Démons : `demons.md`.

## 1. Codes visuels essentiels

| Être | Ce qui le fait reconnaître | Variantes |
|---|---|---|
| **Squelette** | Os blancs ou ivoire, cage thoracique, **orbites vides avec une lueur** au fond | Mignon (chibi) : crâne énorme, os ronds, sourire. Guerrier : armure rouillée, cape déchirée |
| **Crâne** (familier, ornement) | Orbites, arcades, pommettes, mâchoire qui claque ; **flamme** qui sort du crâne comme une chevelure | Cornu (démon), couronné (roi), fendu, cristallisé |
| **Spectre / fantôme japonais** (*yūrei*) | **Kimono blanc** d'enterrement, longs cheveux noirs défaits, **poignets mous** qui pendent, **pas de pieds** (le bas s'efface), triangle blanc sur le front (*hitaikakushi*), **flammes-âmes** (*hitodama*) qui l'accompagnent | Fantôme mignon (*obake*) : drap arrondi, timide, curieux, maladroit ; couleurs pastel |
| **Liche** | Mage mort-vivant : crâne, **couronne ou heaume orné**, robe ample, bâton, **phylactère** (réceptacle de l'âme) qui flotte près de lui, regard bleu ou violet ; dans l'anime d'isekai, c'est souvent un roi-sorcier squelette en robe somptueuse | Élégante : or, joyaux, robe brodée. Menaçante : armure gravée de runes, yeux « comme un feu mourant » |

Couleurs dominantes : **os ivoire** + **une seule lueur** (cyan, violet ou vert spectral). Le contraste robe sombre / os clair / flamme néon fait toute la lisibilité.

## 2. Silhouette et proportions (échelle du dépôt)

- **Crâne-familier** : 4–6 px (`familier_abyssal`), qui flotte à hauteur d'épaule (y ≈ 27, x ≈ ±15) ; mâchoire séparée (pivot sous l'oreille) pour qu'elle claque.
- **Fantôme-familier** : 6–9 px, tête ronde qui se prolonge en drap, **le bas se termine en pointe ou en festons qui s'effacent**, deux petits bras sans mains.
- **Couronne de liche** (`head`) : cercle de 9–10 px qui ceint la tête (au-dessus des oreilles, y ≈ 30–31), pointes de 2–4 px, joyau central sur le front.
- **Phylactère** : 2–3 px (fiole, gemme, cage), qui flotte à 6–10 px du joueur.
- **Épaulières d'os** : crânes ou vertèbres stylisés de 3–5 px, sans dépasser vers la tête.
- **Ailes squelettiques** : os seuls (membrane en lambeaux ou absente), même squelette de chauve-souris que les ailes membraneuses ; 52–70 px.

## 3. Matières et couleurs (HD 32–40 texels/px)

- **Os** : ivoire chaud, jamais blanc pur ; ombres **dans** les orbites, les fosses nasales et sous les pommettes ; sutures du crâne en lignes fines ; légère usure aux arêtes. Version abyssale : os charbon (54, 47, 68), reflet violet (146, 92, 186) (`familier_abyssal`).
- **Orbites** : fond noir profond, **point de lumière** au centre (3–5 texels), halo de la même couleur autour.
- **Spectre** : blanc bleuté translucide, plus opaque au centre, qui s'efface vers le bas et les bords ; cheveux noir bleuté en mèches longues.
- **Liche** : robe velours (pourpre, bleu nuit, noir), broderies or de 3–4 texels, joyaux à reflet blanc, métal gravé.
- **Flamme spectrale** : cœur blanc, corps cyan ou vert, bord saturé ; pas de contour sombre.

## 4. Mouvement, comportement, attitude

- **Crâne** : flotte en 8 lent (4–6 s), mâchoire qui claque au hasard (2–3 claquements en 0,4 s), tête inclinée qui regarde le joueur ; attaque : fonce, mâchoire grande ouverte.
- **Fantôme** : **flotte sans poids**, ondulation du bas en continu (drap au vent, période 1,5–2 s), bras qui pendent mollement ; il **disparaît et réapparaît** (fondu) ; mignon : sursaute, se cache derrière le joueur, rougit.
- **Squelette** : mouvements secs, articulations qui cliquettent, tête qui tombe un peu en avant au repos.
- **Liche** : lente, majestueuse, flotte un peu au-dessus du sol ; phylactère qui orbite lentement (8–12 s) ; incantation : lueur qui monte des mains, cercle sous les pieds.
- **Apparition** : le crâne s'allume (orbites d'abord), le fantôme apparaît en fondu depuis le bas, la liche par une flamme-âme qui grandit.

## 5. Langage anime

- **Flammes-âmes** : orbes bleus à queue de lumière qui accompagnent le spectre (voir `esprits-fees.md`, feu follet).
- **Lueur des orbites** qui laisse une **traînée** quand la tête bouge vite.
- **Aura sombre** : fumée noire ou violette au ras du sol, qui rampe.
- **Fantôme mignon** : joues roses, petite langue, expression gênée, goutte de sueur ; pastel.
- **Roi-sorcier** : silhouette encadrée par une robe immense, cercles magiques multiples, gemmes qui brillent sur la poitrine et les mains.

## 6. Traduction dans le mod

- **Crâne** : recette `familier_abyssal` (hiérarchie `fam_elan > fam_orbite > fam_pos > fam_regard > fam_snap`, mâchoire à pivot, points `emit_braise`). Volumes texturés sur 6 faces, UV distinctes par face.
- **Lueur des orbites** : plaque au fond de l'orbite en `_e` + couleur claire dans la texture (shader) ; petit disque `add_` en `cam_` devant pour le halo sans shader.
- **Fantôme** : **`trans_`** (visible avec shader), opacité dégressive vers le bas peinte dans la texture ; fondu d'apparition par `ctrl_alpha` (vrai fondu en `trans_`). Bas du drap en segments imbriqués qui ondulent, ou `phys_drap_r20_a30`.
- **Flamme qui sort du crâne** : `add_` en `camy_`, ondulation du groupe ; doublée en `trans_` pâle.
- **Phylactère en orbite** : rotation continue dans `overlay_<nom>` (360°·k par boucle).
- **Particules** : braises ou flammèches qui **montent** depuis le crâne ou les mains, fumée qui monte ; rien qui tombe (pas d'ailes). `emit_mc_soul_fire_flame` ou `soul` possibles (de nouveau utilisables, à juger en jeu).
- **Sons** (rares) : `entity.skeleton.ambient` ou `block.bone_block.place` à l'attaque au plus ; jamais en mouvement.

## 7. Pièges

- **Os blanc pur** : cartoon et plat ; ivoire et ombres dans les creux.
- Lumière des orbites seulement en `_e` : vide avec shader.
- Fantôme opaque : il devient un drap. Fantôme `add_` seul : invisible avec shader.
- Particules qui **tombent** d'un crâne ou d'une couronne : interdit sans demande.
- Trop de détails anatomiques sur un crâne de 5 px : illisibles ; garder orbites, nez, mâchoire, deux arcades.
- Reproduire un roi-sorcier squelette d'anime identifiable (robe + couronne + joyaux d'un personnage) : composer une liche originale.
- Ne pas présenter le style « Abyssal » (vert acide) comme le seul registre : un mort-vivant élégant peut être ivoire et or (liche royale) ou bleu spectral (fantôme).

## 8. Sources

- [Yūrei (Wikipedia)](https://en.wikipedia.org/wiki/Y%C5%ABrei)
- [The white kimono Japanese ghosts wear (Hyakumonogatari)](https://hyakumonogatari.com/2012/04/04/what-is-the-white-kimono-japanese-ghosts-wear/)
- [The triangle headband Japanese ghosts wear (Hyakumonogatari)](https://hyakumonogatari.com/2011/09/22/what-is-the-triangle-headband-japanese-ghosts-wear/)
- [Hitaikakushi (skdesu)](https://skdesu.com/en/hitaikakushi-the-mysterious-white-cloth-japanese/)
- [Hitodama (yokai.jp)](https://yokai.jp/en/yokai/hitodama)
- [Lich (TV Tropes)](https://tvtropes.org/pmwiki/pmwiki.php/Main/Lich)
- [Use reference to design a boss character, liche (ImagineFX via Magzter)](https://www.magzter.com/article/Entertainment/ImagineFX/Use-Reference-To-Design-A-Boss-Character)
- [Cute characters, kawaii ghosts (Super Cute Kawaii)](https://www.supercutekawaii.com/2022/10/cute-characters-kawaii-ghosts/)
- [Spooky cute Japanese Halloween, obake (ZenPop)](https://store.zenpop.jp/blogs/guide/spooky-cute-japanese-halloween-stationery)
- [Bakemono no e (Wikipedia)](https://Www.wikipedia.org/wiki/Bakemono_no_e)
- [Dragon Quest undead, bestiaire (Bogleech)](https://bogleech.com/dq/dq005undead)
