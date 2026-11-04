# Règles — fonctions avancées du mod

Le guide (`docs/guide-cosmetiques.md`, mis à jour le 2026-11-03 avec nos demandes) fait foi. Résumé et pièges, avec ce que nos outils simulent.

| Fonction | Où dans le guide | Aperçu (renderer, Vestiaire) |
|---|---|---|
| `add_<nom>` : additif, noir = invisible | 4 bis | Simulé |
| `trans_<nom>` : alpha 1–254, faces triées | 4 bis, 5 | Simulé |
| `cam_<nom>`, `camy_<nom>` : face caméra (sphérique, debout) | 4 bis | Simulé (pose du joueur ignorée pour l'orientation) |
| `phys_<nom>[_r<0-100>][_a<0-100>]` : ressort autour de la pose animée | 4 bis | Non simulé |
| `ctrl_alpha`, `ctrl_teinte`, `ctrl_lumiere`, `ctrl_uv` : groupe **vide** dans le groupe piloté | 4 bis | Non simulé |
| `<texture>_r` (masque de reflets, lu **par face**) + `_m` (matcap ≤ 256²) | 5 quater | Non simulé |
| Textures animées (images empilées, `frame_time`, `frame_order`) | 5 | Non simulé |
| `emit_mc_<id>` : particule de Minecraft, direction +Y du groupe | 5 ter §4 | Non simulé |
| `overlay_<nom>` (boucle permanente), `event_jump`, `event_land`, `event_equip`, `event_enter_<état>`, `event_exit_<état>` | 6.4 | Non simulé |
| Sons : clés `sound` de la piste *Effets* (nom de son Minecraft) | 6.5 | Non simulé |
| Molang : 512 caractères, `v.x = …;`, `q.is_boosting`, `q.yaw_speed`, `q.head_*`, `q.time_of_day`, `q.instance_seed`, `math.random`… | 6.3 | Calculé (variables mémorisées non simulées) |
| Essai en jeu sans le staff : `/cosmetique apercu <fichier>` | 12 | — |

## Pièges

- **Contrôles en « 1 + position »** : au repos x = 0. `ctrl_alpha` x = −1 invisible, −0,5 à moitié. Nom exact (`ctrl_alpha`, pas `ctrl_alpha_l`) ; plusieurs groupes peuvent porter le même nom. En partie opaque, sous 10 % la partie disparaît d'un coup : le fondu demande `trans_` ou `add_`.
- **Pas de `ctrl_emit`** : la cadence d'une particule ne se pilote pas par l'animation. À la place, les réglages du staff (*Quand*, *Nombre*, *Rafale* : attaque, blessé, saut, atterrissage). Le vérificateur le refuse.
- **`emit_mc_<id>` sans chiffre au bout** (il ferait partie du nom de la particule) : plusieurs points = même nom. Particules sans réglages seulement, plus `dust_<rrggbb>_<taille×10>`. 4 sortes au plus, en plus des 4 modélisées.
- **Superposition** (overlay, événements, et à supposer `attack`/`hurt`) : rotations et positions **s'ajoutent**, échelles **se multiplient**. Une pièce cachée par une échelle 0 dans l'état reste cachée : la cacher autrement (enfouie, petite) ou animer l'échelle dans l'état lui-même.
- **Rotations continues** (engrenages, rotors, halos) : dans une animation `overlay_`, pour ne plus sauter entre deux états.
- **Reflets** : le masque `_r` est moyenné par face ; mettre le métal brillant et le mat sur des faces différentes.
- Les shaders ne lisent pas `_n`/`_s` (LabPBR) : inutile de les peindre.
- Particules qui tombent et se posent : ailes seulement (`retours-en-jeu.md`). Vapeur, fumée, étincelles qui montent ou se dissipent : partout.
- Lister les fonctions avancées utilisées dans le docstring du générateur et dans le message de livraison, avec ce qui se juge seulement en jeu (`/cosmetique apercu`).

**Sons rares** (retour de l'utilisateur : « infernal » quand chaque mouvement siffle, à répétition) : aucun son dans les états en mouvement ni dans les `overlay_` ; au repos, un seul par boucle de 8 s au moins ; un seul à l'attaque, à la blessure ou à un événement. Appliquer `tools/sons.py` (`limiter_sons(model)`) dans le générateur. Penser que 3 cosmétiques peuvent sonner ensemble.

Sons utiles (noms Minecraft) : sifflement de vapeur `block.fire.extinguish`, `entity.generic.extinguish_fire` ; piston `block.piston.extend`, `block.piston.contract` ; cliquet `block.note_block.hat`, `ui.button.click` ; battement `entity.phantom.flap`. Format d'une clé : animateur `"effects": {"name": "Effects", "type": "effect", "keyframes": [{"channel": "sound", "data_points": [{"effect": "block.fire.extinguish", "file": ""}], "time": 1.2}]}`.
