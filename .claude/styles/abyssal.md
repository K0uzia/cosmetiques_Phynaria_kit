# Style — Abyssal (thème Démoniaque, ensemble Abyssal)

Pièces de référence, **validées en jeu** : `cosmetiques/ailes/ailes_abyssales/gen_ailes_abyssales.py` (« juste incroyable », 3D et textures) et les cornes de `cosmetiques/chapeaux/cornes_abyssales/gen_cornes_abyssales.py` (tracé repris de `bandeau_abyssal`, « incroyable », position « niquel » ; le bandeau lui-même a été retiré le 2026-11-08, « fixette sur des couronnes et bandeaux », archivé dans `archives/chapeaux/`). Reprendre leurs constantes de couleur, leurs fonctions de peinture (veines, griffes, os) et leur recette de volume avant d'inventer. Pièce de tête : `cornes_abyssales` (cornes, racines d'os soudées au crâne, demi-masque d'os au regard vert ; pas encore vue en jeu). Archivées : `chapeau_abyssal`, `masque_abyssal`, `bandeau_abyssal`. Autres pièces : `queue_abyssale` (préférée à `queue_abyssale_v1`, « trop dragon, créature »), `skin_epee_abyssal` (« Croc de l'Abysse », skin d'épée qui remplace `lames_abyssales`, archivées le 2026-11-08), `skin_hache_abyssal` (« Mâchoire de l'Abysse », skin de hache), `epaulieres_abyssales`, `aura_abyssale`, `familier_abyssal`. Nom des pièces : `<type>_abyssal(e)`. Fiche du sujet : `.claude/references/creatures/demons.md`.

## Esprit

**Chasseur de démons élégant**, pas bête ni monstre : silhouette humaine intacte, attributs fins et lisses (cornes en crochet, ailes de chauve-souris aux os fins, griffes recourbées), un regard vert qui brille dans l'ombre. Sombre, sec, anguleux, mais propre. Une seule couleur vive : le **vert acide**, réservé aux veines, aux fentes du regard, aux pointes et aux fissures. Tout le reste est charbon et pourpre-noir.

Éléments-signatures : membrane pourpre-noir d'un seul tenant, veines vert acide contrastées qui se ramifient, déchirures en encoche sur les bords de fuite, os octogonaux effilés et légèrement courbes (charbon à reflet violacé), griffes recourbées en peau + âme à pointe verte, cornes à bagues de croissance (base sombre, pointe plus claire), cuir sombre à reflet lilas, oreilles pointues.

À éviter (retours en jeu) : vertèbres, épines dorsales et membrane sur une queue (« trop dragon, créature ») ; rouge et noir + clous pointus (« gothique », leçon Cuir) ; langues de feu à contour sombre pour une aura (« mec en feu ») ; masque d'os intégral présenté comme « chasseur de démons ».

## Palette (constantes communes des générateurs)

| Matière | Clair | Base | Ombre | Usage |
|---|---|---|---|---|
| Membrane / pourpre-noir | `C_RIM` (122, 42, 124) liseré, `C_HIGH` (82, 28, 104) | `C_BASE` (42, 16, 60) | `C_DARK` (17, 7, 26) | Membranes, panneaux, chapeau ; le bord s'éclaircit |
| Halo des veines | | `C_AURA` (22, 66, 40) | | Lueur sombre autour de chaque veine (flou) |
| Veine vert acide | `C_VCORE` (150, 244, 70) cœur | `C_VEIN` (96, 200, 44) | | Veines maîtresses 0,50 px, branches 0,36 px (`WM`, `WB`) |
| Os / corne charbon | (98, 72, 132) reflet violacé | (54, 48, 66) → (26, 22, 34) | (12, 8, 16) | Os, cornes à bagues, griffes ; pointe qui vire au vert (132, 240, 58) |
| Charbon du masque | `C_REFLET` (116, 86, 156) | `C_CHAR` (28, 24, 36), `C_CHAR2` (58, 48, 76) | `C_OMBRE` (11, 8, 16) | Plaques d'os du masque |
| Cuir sombre | (132, 98, 176) reflet lilas | (54, 48, 66) | (26, 22, 34) | Bandeau, sangles |
| Lueur `_e` | (206, 255, 118) | (132, 255, 72) | (10, 34, 12) | Veines, fentes du regard, pointes ; fond `_e` noir |

Pas de rouge, pas d’orange, pas de blanc pur (la braise des ailes est elle aussi vert acide). Le vert ne couvre jamais une grande surface.

## Matières et volume

- **Membrane** : peinte une seule fois dans le plan de l'aile (carte « monde »), puis découpée en plaques (alpha 0/255, tranches transparentes) portées par les doigts. Veines contrastées, déchirures en encoche, bord éclairci.
- **Os** : tronçons octogonaux (deux cubes à 45°) qui s'effilent et se courbent ; couleur continue le long de l'os.
- **Griffes, cornes, oreilles** : peau découpée (contour rond, crochet) + âme pleine plus étroite (recette Aurelion/Bérénice).
- **Cornes** : sur le dessus de la tête, au-dessus des tempes, elles balaient vers l'arrière puis reviennent en crochet (tracé de `bandeau_abyssal`, repris tel quel dans `cornes_abyssales`). Elles sortent du crâne : meule de nodules au pied, racines d'os **aplaties et soudées** (jamais des tubes écartés de la tête).
- Densité HD : 18 texels/px pour la carte de membrane, 24–40 pour les petites pièces.

## Lumière et shader

- Le vert des veines est **déjà dans la texture de base** (`C_VEIN`, `C_VCORE`) : la pièce reste lisible avec shader, où `_e` et `add_` sont invisibles (bug du mod). Le calque `_e` (veines, fentes, pointes, 132–255 en vert) n'est qu'un plus, de nuit et sans shader.
- Sources nettes et petites : veines fines, fentes du regard, pointes des griffes. Rien de vif en aplat.
- Aura (`aura_abyssale` v3, 2026-11-08) : tout en lumière `add_` : disques violets (64, 18, 98) → (186, 126, 228), traits vert acide (80, 190, 46) → (170, 250, 110) : couronne de crocs recourbés derrière la nuque, veines ramifiées qui montent, sceau au sol (croissants, losanges, fissures). Les volutes `trans_` sombres de la v2 se lisaient grises de jour (« nul »).

## Mouvement

- Ailes : repos menaçant à demi fermé, étirement ample périodique, ouverture brutale à l'attaque (0,15 s) et retour lent ; repliées serrées en `sneak`, tombantes en `sleep`. Un battement de chauve-souris : l'éventail des doigts se ferme à la remontée.
- Cornes : rigides. Ce qui bouge, ce sont les oreilles et le regard (clignement au repos, plissé en `sneak`).
- Apparition (`event_equip`) : les ailes **percent le dos** (petites et repliées, puis ouverture d'un coup, comme un étirement) ; le regard s'allume en dernier.
- Sons rares (`tools/sons.py`) : `entity.phantom.flap` (un battement à l'apparition), `entity.wither.ambient` ou `block.sculk.spread` à très faible fréquence ; aucun en mouvement.

## Familier (`familier_abyssal`, crâne flottant)

Esprit qui lévite par sa flamme d'âme (cause visible), à droite du joueur à hauteur de tête (x = 12, y = 28,5). Caractère : espiègle et un peu sinistre, jamais bête ni monstre. Regard : orbites vertes qui suivent celui du joueur avec retard, saccades des pupilles, clignement de la flamme ; il **se tourne vers le joueur quand celui-ci tourne la tête vers lui** (> 25°, sens de `q.head_y_rotation` supposé : `SIGNE_TETE`). Dix comportements pondérés par tranches de 6 s (regarder autour ×3, regarder le joueur et s'approcher curieux ×2, claquer des dents, rire silencieux, tourner sur lui-même, s'assoupir, cracher une flammèche, faire peur puis rire, faire le tour du joueur ×1 ; 10 tranches calmes sur 24). Monde : flamme tassée et ébrouement sous la pluie, tassée sous l'eau, qui flambe dans la lave, plus haute et plus vive la nuit (`ctrl_lumiere`), un peu plus encore à la pleine lune ; vie basse : il se rapproche, yeux qui vacillent. Il ricane après sa morsure (`attack`). Pas de retour en jeu (2026-11-05).

## Particules

- Braises vert acide modélisées (éclat de 3,2 px, une face) (`particle_braise`), qui tombent **seulement depuis les ailes** (bout des doigts, bord de la membrane).
- Ailleurs : fumée ou braises qui **montent** (cornes, mains), jamais qui se posent.

## Arme (skin d'objet `skin_epee_abyssal`)

Sabre d'os à un seul tranchant : fil vert sur le côté convexe (la courbe concentre la coupe sur une petite portion du fil), lame qui s'amincit vers la pointe (diminution distale), éperon d'os sur le dos près du talon ; garde en griffes recourbées, cuir cousu à clous d'os. Vivant et sobre : l'os « respire » (griffes ±2,5°, fil qui souffle par `ctrl_lumiere`), la lame sort de la garde à la prise en main, les griffes serrent la poignée au coup, le fil s'embrase quand il touche ; un seul son, au coup qui touche (clé à 0,04 s). **Vrai volume** (2026-11-08, `volume-3d.md`) : section à un seul tranchant (plat incliné, biseau à pente unique 32° côté fil, dos en mur plein), gouttière creusée près du dos où la lueur verte est couchée, griffes et poignée en tours de pans ; c'est la référence de matière des objets du set. Sources : Wikipedia, *Blade geometry* (https://en.wikipedia.org/wiki/Blade_geometry) ; BladeForums, *What is a distal taper?* (https://bladeforums.com/threads/what-is-a-distal-taper.130907).

## Hache (skin d'objet `skin_hache_abyssal`)

Hache barbue d'os charbon : fer en croissant à cornes, barbe en crochet vers la main, fil vert acide en volume sur tout le croissant, biseau marqué d'une arête violacée, veines qui remontent du fil vers l'œil ; dos en marteau d'os plein d'où part une griffe recourbée vers le manche ; collier d'os à l'œil, deux attelles d'os, manche d'os, poignée de cuir cousu à clous d'os, renflement et petite griffe au talon (même pommeau que l'épée). Vivant sobre : griffes qui respirent et fil qui souffle (`item_idle`), le fer pousse de l'œil (`event_select`), le fil s'avive au coup (`event_swing`), éclat et seul son au coup qui touche (`event_hit`), le fil « boit » quand un bloc tombe (`event_break`, sans son). Fiche du sujet : `.claude/references/objets/haches.md`.
