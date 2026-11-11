# Référence — Traînées d'arme, impacts, éclats (armes et animations `attack`)

Fiche documentée (2026-11-04). Pour les pièces d'`armes/` et pour l'état `attack` (et `hurt`) de toute pièce. À lire avec `principes-fx-anime.md` (timing en trois temps, smear).

## Codes visuels

- **La traînée (slash)** : un croissant, **une seule courbe bien ronde**, peu d'irrégularités, en forme de **drapeau** : la tête (côté lame) épaisse et la plus claire, la queue de plus en plus fine. Elle reste suspendue un instant le long de l'arc après le passage de la lame, puis **s'efface de la queue vers la tête**.
- **L'impact** : une étoile ou un éclatement radial (pointes de longueurs variées), un anneau d'onde qui s'agrandit, des éclats et étincelles projetés, parfois une **image d'impact** (1 à 3 images à couleurs franches : noir, blanc, rouge, ou inversées) qui « coupe » l'action.
- **Les lignes de vitesse** : traits droits qui convergent vers le point d'impact ou suivent la trajectoire.
- **Hiérarchie** : le flash est la valeur la plus haute de tout l'effet et la plus courte ; la traînée en valeurs moyennes ; les éclats petits et vifs.

## Formes et couleurs

- Traînée : cœur blanc teinté sur le bord d'attaque (côté tranchant), teinte de l'arme ou de l'élément, queue qui se fond dans la teinte puis disparaît. Doubler éventuellement par une seconde traînée plus large et plus pâle, plus courte en durée.
- Impact : centre presque blanc, pointes de la teinte, éclats de la couleur du matériau (étincelles jaunes pour le métal, éclats cyan pour la glace).
- Palette de l'élément : `elements.md`.

## Mouvement et timing

| Temps | Durée (sur une `attack` de 0,8 s) | Ce qui se passe |
|---|---|---|
| Anticipation | 0,1–0,2 s | l'arme recule ou se lève, petit éclat de charge |
| Coup | 0,05–0,1 s | la lame traverse l'arc, la traînée naît en entier (smear) |
| Impact, gel | 0,05–0,15 s | flash, pointes de l'étoile, arrêt quasi complet de la lame (hitstop) |
| Dissipation | 0,3–0,5 s | la traînée s'efface de la queue vers la tête, éclats qui tombent, retour en pose |

Repères chiffrés des jeux de combat (60 images/s) : gel de 2–4 images pour un coup léger (0,03–0,07 s), 6–10 images pour un coup lourd (0,1–0,17 s), jusqu'à 20–24 pour un coup critique. Une image d'impact anime dure 1 à 3 images (0,04–0,12 s). Trop court : le coup paraît mou ; trop long : lourdeur.

## Langage anime

| Code | Lecture |
|---|---|
| Traînée blanche fine et nette | maîtrise, coupe parfaite |
| Traînée large, colorée, à bord déchiré | puissance, élément |
| Plusieurs croissants qui se croisent | enchaînement, vitesse surhumaine |
| Image d'impact à couleurs inversées | coup décisif |
| Étoile d'impact à pointes inégales et anneau | choc physique |
| Débris cubiques qui volent | destruction (école des « débris cubiques » des explosions d'anime) |

## Traduction dans le mod

- **Traînée** : une plaque découpée en croissant (texture en drapeau), enfant du groupe qui porte l'arme (`right_arm` → `prise` → `coup`), dans le plan du geste. Échelle 0 hors attaque ; à l'`attack`, échelle 0 → 1 en *step* au moment du coup (smear : elle apparaît en entier), puis effacement de la queue vers la tête par `ctrl_uv` (la texture glisse hors de la découpe) ou par 2–3 plaques de longueurs décroissantes qu'on éteint l'une après l'autre (`ctrl_alpha`).
- **Se voir de face** : une traînée plate disparaît par la tranche ; en jeu on voit son propre bras de côté, les autres sous tous les angles. Soit accepter le plan du geste (les autres joueurs le voient bien de côté), soit une **seconde plaque perpendiculaire** très discrète ; `cam_` déforme le croissant (il pivote autour de son pivot), à réserver à l'étoile d'impact.
- **Rendu** : traînée en `add_` (lumière) + double `trans_` (visible avec shader) ; ou `trans_` seule pour une traînée de vent ou d'eau.
- **Étoile d'impact** : plaque `add_` en `cam_` au bout de la lame, échelle 0 → 1,2 → 0 en 0,1–0,15 s ; anneau d'onde : plaque fine qui grandit de 0,3 à 1,5 en 0,2 s avec `ctrl_alpha` qui baisse.
- **Gel** : deux clés identiques sur 0,05–0,1 s au moment de l'impact (interpolation *linear* ou *step*), puis retour en *catmullrom*.
- **Flash d'arme** : `ctrl_lumiere` à +1 pendant 0,1 s sur le calque `_e` de la lame (pièce non additive), ou `ctrl_teinte`.
- **Éclats** : `particle_eclat` (un cube de 0,3 px, une face) avec Rafale « À l'attaque » (8 d'un coup), ou `ctrl_emit` à +4 sur 0,1 s ; `emit_mc_crit`, `emit_mc_enchanted_hit`, `emit_mc_electric_spark` en appoint, à juger en jeu.
- **`q.attack_time`** (0 à 1 pendant le coup) : pour caler la traînée sur le geste du joueur si l'animation `attack` ne suffit pas.
- **Règles de l'état** : `attack` et `hurt` en `once`, 0,8 s, **avec les seuls groupes concernés** et retour à 0 (superposition : rotations et positions s'ajoutent, échelles se multiplient). Une traînée cachée par échelle 0 dans l'état reste cachée : animer son échelle dans `attack` lui-même.
- **Son** : un seul à l'attaque, et seulement pour une arme (`tools/sons.py`) : `entity.player.attack.sweep`, `item.trident.throw`, `block.amethyst_block.chime` (glace, cristal).

## Avec shader

Les traînées et étoiles `add_` disparaissent ; garder une **traînée `trans_`** (alpha 60–150) et une lame dont la forme se lit sans lueur. Les particules *Lumineux* sont à supposer invisibles aussi ; préférer *Translucide* ou *Opaque* pour les éclats.

## Pièges

- Traînée en arc de cercle parfait à épaisseur constante : « tuyau » ; il faut le drapeau (tête épaisse, queue fine).
- Traînée qui reste trop longtemps : encombre et cache le joueur. 0,3–0,5 s au total.
- Flash `add_` trop grand qui recouvre la tête du joueur : garder l'étoile au bout de la lame, ≤ 6 px.
- Cumul additif : traînée + étoile + `_e` sur la même zone ; mesurer ≤ 255.
- Petits cubes volants portés par le modèle : illisibles ; particules ou éclats de 3 px au moins.
- Animation d'`attack` qui bouge tout le modèle : seuls les groupes concernés.

## Sources

- [Slash FX, tutoriel 2 : fondamentaux de la forme du slash (courbe unique, drapeau)](https://jasontomlee.itch.io/slashfx/devlog/629732/tutorial-2-slash-shape-fundamentals)
- [Real Time VFX : question générale sur les slashs (ruban ou arc, axe bloqué face au joueur)](https://realtimevfx.com/t/general-question-about-sword-slash-vfx/26396)
- [Real Time VFX : traînées d'arme, maillages ou traînées dynamiques](https://realtimevfx.com/t/ue4-weapon-slash-meshes-vs-animtrail-data/5628)
- [Real Time VFX : WIP Sword Slash Attack](https://realtimevfx.com/t/wip-sword-slash-attack/1272)
- [Traînée procédurale : tête plus brillante, fondu après le coup](https://marketplace.unity.com/packages/vfx/procedural-slash-trail-313445)
- [CG Wire : smears et images d'impact](https://blog.cg-wire.com/smear-frames/)
- [Blender Artists : images d'impact d'anime](https://blenderartists.org/t/impact-frames-from-anime-in-blender/1279454)
- [Sakurai sur le hitstop (Source Gaming)](https://sourcegaming.info/2015/11/11/thoughts-on-hitstop-sakurais-famitsu-column-vol-490-1/)
- [TV Tropes : Hit Stop](https://tvtropes.org:443/pmwiki/pmwiki.php/Main/HitStop)
- [Godot : hitstop, ralentir seulement l'instant de l'impact](https://uhiyama-lab.com/en/notes/godot/hit-feedback-hitstop/)
- [VFX Apprentice : guide de style VFX de League of Legends (timing en trois temps, effets courts)](https://www.vfxapprentice.com/blog/10-league-of-legends-vfx-design-tips)
