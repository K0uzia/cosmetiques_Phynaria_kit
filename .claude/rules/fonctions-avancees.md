---
paths:
  - "cosmetiques/**"
---

# Règles — fonctions avancées du mod

Le guide (`docs/guide-cosmetiques.md`, mise à jour du 2026-11-08 : demandes 6) fait foi. Résumé et pièges, avec ce que nos outils simulent. Demandes faites au développeur, ce que le guide ne couvre pas, état en jeu détaillé : `.claude/references/mod/rendus-avances.md`.

| Fonction | Où dans le guide | Aperçu (renderer, Vestiaire) |
|---|---|---|
| `add_<nom>` : additif, noir ou alpha 0 = invisible ; ajoute **couleur × alpha** depuis le 2026-11-08 (lueur qui s'estompe par l'alpha, couleur gardée ; avant : alpha ignoré). Même règle pour `_e` | 4 bis, 5 bis | Simulé |
| `trans_<nom>` : alpha 1–254, faces triées | 4 bis, 5 | Simulé |
| `cam_<nom>`, `camy_<nom>` : face caméra (sphérique, debout), aussi dans le menu Apparence depuis le 2026-11-06 soir | 4 bis | Simulé (pose du joueur ignorée pour l'orientation) |
| `phys_<nom>[_r<0-100>][_a<0-100>][_g<0-100>]` : ressort autour de la pose animée ; `g` = gravité (`_g100` : pend vers le bas du monde ; chaîne = un groupe `phys_…_g100` par maillon, pivot en haut), réglages dans n'importe quel ordre | 4 bis | Non simulé |
| Bras fins : `right_arm`/`left_arm` resserrés par le mod (côté extérieur rentré de 1 px) ; modéliser pour 4 px ; grosse pièce non resserrée dans un sous-groupe `wide_<nom>` ; ne plus réduire par `q.is_slim_arms` | 4 | Non simulé |
| Réglage du staff **Armure** : Normale, **Par-dessus** (pièces de `head`, `body`, bras, jambes écartées comme l'armure : 1 px, jambières 0,5), Cachée ; essai `/cosmetique armure` | 10 | Non simulé |
| `ctrl_alpha`, `ctrl_teinte`, `ctrl_lumiere`, `ctrl_uv`, `ctrl_reflet` : groupe **vide** dans le groupe piloté | 4 bis | `ctrl_alpha` simulé (sous 10 % la partie disparaît), les autres non |
| `ctrl_emit` : groupe vide **dans** un point `emit_`, cadence animée (−1 coupé, 0 réglage du staff, +2 trois fois plus, +7 au plus) | 4 bis, 5 ter | Non simulé |
| `<texture>_r` (masque de reflets, lu **par face**) + `_m` (matcap ≤ 256²) | 5 quater | Non simulé |
| Textures animées (images empilées, `frame_time`, `frame_order`) | 5 | Non simulé |
| `emit_mc_<id>` : particule de Minecraft, direction +Y du groupe | 5 ter §4 | Non simulé |
| Réglages des particules : `unhandled_root_fields.phynaria.particules` (depuis `reglages.json`), **lus à l'import**, pré-remplis pour le staff | 5 ter §6 | Contrôlés par le vérificateur |
| **Fiche de l'objet** : `phynaria.fiche` = `nom` (≤ 40), `ensemble` (≤ 40), `rarete` (≤ 24 : `commun`, `peu_commun`, `rare`, `epique`, `legendaire`, `mythique`), `description` (≤ 300), `lore` (≤ 500, `\n` = ligne) ; embarquée par `livrer.py` depuis `fiche.json` et `ensembles.json` (`tools/fiche.py`) | 10 bis, 13 | Contrôlée par le vérificateur |
| **Vignette 3D** de la carte (facultative) : `phynaria.vignette` = `{"angle": [vue d'en haut −90..90, rotation], "zoom": 0,25..4, "etat": "idle", "temps": 0..60}` ; sans elle, pièce seule de 3/4 au repos, angle `[25, 35]`. Recopiée depuis la clé `vignette` de `fiche.json` si on l'y met (jamais par défaut) | 10 bis, 13 | Contrôlée par le vérificateur ; pas rendue |
| **Familier vivant** (`phynaria.familier`, animations `pet_*`) | 6.6 | `categories/familiers.md` |
| **Skin d'objet** (`phynaria.objet`, étapes) | 14 | `categories/objets.md` |
| **Effet de téléportation** (`charge`/`depart`/`arrivee`, groupe `joueur`) | 15 | `categories/effets.md` |
| `overlay_<nom>` (boucle permanente), `event_jump`, `event_land`, `event_equip`, `event_unequip` (5 s au plus, dernière image gardée), `event_enter_<état>`, `event_exit_<état>` | 6.4 | Joués par les boutons du Vestiaire |
| Sons : clés `sound` de la piste *Effets* : nom de son Minecraft, son d'un pack de ressources du serveur (`phynaria:<nom>`), ou **son embarqué** (`phynaria_sounds`, OGG dans le modèle) | 6.5 (ci-dessous) | Non simulé ; contrôlé par le vérificateur |
| Molang : 512 caractères, `v.x = …;`, `q.is_boosting`, `q.yaw_speed`, `q.head_*`, `q.time_of_day`, `q.instance_seed`, `math.random`… ; depuis la demande 3 : `q.is_slim_arms`, `q.has_helmet`/`has_chestplate`/`has_leggings`/`has_boots`, `q.body_x_rotation` (≈ 29 accroupi), `q.right_arm_x_rotation` (et `_z_`, et `left_arm`), `q.limb_swing`, `q.limb_swing_amount`, `q.has_shader_pack`, `q.is_in_menu`, `q.hurt_time`, `q.attack_time`, **`q.hit_by_entity`** (1 pendant un coup reçu d'un joueur, d'un monstre ou d'un projectile, 0 pour chute, feu, noyade ; pas encore vérifiée en jeu) ; skin d'objet : `q.use_progress`, `q.item_durability`, `q.is_enchanted`, `q.hand`, `q.in_first_person` ; familier vivant : `q.is_pet`, `q.is_perched`, `q.is_sitting`, `q.owner_distance`, `q.owner_is_sneaking`/`_sprinting`/`_sleeping`, `q.owner_health`, `q.owner_max_health`, `q.owner_ground_speed` | 6.3, 6.6 | Calculé (variables mémorisées non simulées ; requête inconnue = 0, réglable par `MOLANG_QUERY`) ; le vérificateur alerte sur une requête hors du guide |
| Essai en jeu sans le staff : `/cosmetique apercu <fichier>` | 12 | — |

## État en jeu, en bref

Détail, dates, captures et contournements : `.claude/references/mod/rendus-avances.md`.
- Sans shader : `add_`, `cam_`/`camy_`, `_e` la nuit, `ctrl_teinte` marchent. Avec shader : `add_` et `_e` visibles depuis le correctif de la demande 3 (2026-11-05).
- `_e` : `AVEC_E = True` ; si le clignotement revient, `AVEC_E = False` et relivrer.
- Reflets `_r` : retirés partout (`REFLETS = False`, `tools/ambiance.py`), à réessayer sur une pièce de test.
- Menu Apparence : `add_` correct ; `cam_`/`camy_` orientés par le mod depuis le 2026-11-06 soir (guide 4 bis) : notre contournement `vm_` est coupé (`ADAPTER_MENU = False`, `tools/menu_aura.py`, `categories/auras.md`).
- `emit_mc_` : résolu. `ctrl_alpha` en partie opaque : corrigé côté mod, pas encore vu en jeu.

## Pièges
- **Faces `up`/`down`** : lues comme dans Blockbench depuis le 2026-11-06 soir (guide 3), image asymétrique permise. Historique : avant, demi-tour sur `up` et miroir sur `down` (selon le guide ; notre test l'avait lu comme un miroir X) ; `tools/uv_horizontal.py` gardé, `MIROIR_X_JEU = False`.
- **Skins d'objets** (objets vivants, `java_block`) : `categories/objets.md`.
- **Mipmaps** (guide 5, 2026-11-08) : de loin, textures lues dans des copies réduites (4 niveaux, réglage vidéo du joueur) ; un trait de 1–2 texels reste visible, plus pâle. Les règles « trait fin effacé au loin » d'avant (1.4.0) ne valent plus ; supposé : les bords d'îlots d'atlas se mélangent au loin (marge ou couleur de bord répétée). Simulé par le mode « comme en jeu » (approché, `MIPMAPS=0` pour couper) ; `.claude/references/mod/rendu-en-jeu.md`.
- **`trans_` cache les `add_` derrière lui** (bytecode 1.4.0, 2026-11-07 ; écrit dans le guide 4 bis le 2026-11-08, « n'enfermez pas une lumière `add_` dans une enveloppe `trans_` » : enveloppe en `add_` sombre à alpha faible, ou une ouverture) : passes OPAQUE → TRANSLUCENT → ADDITIVE, `trans_` écrit la profondeur (coupé sous alpha 26) : un `add_` ou une particule derrière une face `trans_`, même presque transparente, n'est pas dessiné. Jamais de gaine `trans_` autour d'une lumière `add_` (`categories/effets.md`, `effet_stellaire_rayon`).
- **Contrôles en « 1 + position »** : au repos x = 0. `ctrl_alpha` x = −1 invisible, −0,5 à moitié. Nom exact (`ctrl_alpha`, pas `ctrl_alpha_l`) ; plusieurs groupes peuvent porter le même nom. En partie opaque, sous 10 % la partie disparaît d'un coup : le fondu demande `trans_` ou `add_`.
- **Bloc `phynaria`** : `livrer.py` y embarque `fiche.json` (clés `fiche` et, si présente, `vignette`) et `reglages.json` (clé `particules`) avant la vérification (`tools/fiche.py`, `embarquer_fichier`) ; les autres clés (`familier` écrit par le générateur, `objet`) sont gardées. Seul emplacement qui survit à un enregistrement dans Blockbench (une clé à la racine ou dans `meta` est effacée). Le mod les lit à l'import et pré-remplit les fenêtres du staff, qui peut encore les changer. `reglages.json` garde les libellés du guide : une valeur hors des pas (`nombre` 0,5/1/2/4/6/10, `duree` 1/3/6/10/15/20, `dispersion` 0/15/45/180, `elan` 0/40/100, « 2 à 3 ») est ramenée à la plus proche, avec une note ; pour une sorte mal nommée, champ facultatif `"groupe": "emit_givre"`.
- **`ctrl_emit`** (2026-11-04) : dans le point `emit_` qu'il règle, jamais ailleurs (le vérificateur le contrôle). Pour un jet au moment exact du geste : x à −1, puis +4 pendant la décharge. Le *Nombre* du staff est partagé entre les points selon leur `ctrl_emit`. *Quand* a aussi **Sous la pluie** (gouttes, vapeur qui fume plus).
- **`event_unequip`** : symétrique de `event_equip`, 5 s au plus ; finir par `ctrl_alpha` −1 ou une échelle 0 (la dernière image est gardée jusqu'au départ). Remis avant la fin : `event_equip` est rejouée.
- **`end_rod` à éviter** (en jeu, 2026-11-04, `aura_berenice`) : grosse étoile blanche de taille fixe qui dérive à 2–3 blocs du joueur, boule lumineuse avec shader. Pour des scintillements, une petite étoile modélisée (≤ 0,6 px, Élan 100 %).
- **`emit_mc_<id>` sans chiffre au bout** (il ferait partie du nom de la particule) : plusieurs points = même nom. Particules sans réglages seulement, plus `dust_<rrggbb>_<taille×10>`. 4 sortes au plus, en plus des 4 modélisées.
- **Superposition** (overlay, événements, et à supposer `attack`/`hurt`) : rotations et positions **s'ajoutent**, échelles **se multiplient**. Une pièce cachée par une échelle 0 dans l'état reste cachée : la cacher autrement (enfouie, petite) ou animer l'échelle dans l'état lui-même. Un groupe déplié par `scale` dans deux événements qui jouent ensemble (`event_swing` + `event_hit` au coup qui touche) est multiplié deux fois : un groupe par événement (alerte « échelles superposées » du vérificateur).
- **Reflets** : le masque `_r` est moyenné par face ; mettre le métal brillant et le mat sur des faces différentes.
- Les shaders ne lisent pas `_n`/`_s` (LabPBR) : inutile de les peindre.
- Rotations continues : `animation.md`, Boucles. Particules qui tombent, vapeur, fréquence des sons : `essentiel.md`, Méthode de travail.
- Lister les fonctions avancées utilisées dans le docstring du générateur et dans le message de livraison, avec ce qui se juge seulement en jeu (`/cosmetique apercu`).

## Sons

Sons utiles (noms Minecraft) : sifflement de vapeur `block.fire.extinguish`, `entity.generic.extinguish_fire` ; piston `block.piston.extend`, `block.piston.contract` ; cliquet `block.note_block.hat`, `ui.button.click` ; battement `entity.phantom.flap`. Format d'une clé : animateur `"effects": {"name": "Effects", "type": "effect", "keyframes": [{"channel": "sound", "data_points": [{"effect": "block.fire.extinguish", "file": ""}], "time": 1.2}]}`. Appliquer `tools/sons.py` (`limiter_sons(model)`) dans le générateur. Fréquence : `essentiel.md`, Sons rares.

**Sons embarqués** (guide 6.5 ; format, limites, préséance, lecture, Blockbench : `.claude/references/mod/sons-embarques.md`) : `"phynaria_sounds": {"<nom>": "data:audio/ogg;base64,…"}`, 8 au plus, OGG Vorbis mono, ≤ 100 Ko, ≤ 5 s, nom `[a-z0-9_]{1,32}` ; la clé de son a `"effect": "<nom>"`.
- **Fabrication** : sons **originaux** synthétisés par script (`tools/synthe.py`, numpy + `soundfile`), source `$D/sons/<nom>.py` à côté de son `.ogg` ; rien de récupéré sur le web ni extrait d'un jeu. Courts (0,3–2 s), doux, crête ≤ −6 dBFS après décodage, mono 44,1 kHz, ≤ 40 Ko. Dans le générateur : `embarquer_sons(model, {"<nom>": "sons/<nom>.ogg"})` (relance le script si le `.ogg` manque ou est plus vieux, contrôle comme le mod) puis la clé `sound` avec `"effect": "<nom>"`.
- Un son doit sonner comme ce qu'il montre (bris de glace = `block.glass.break`, `categories/effets.md`).
