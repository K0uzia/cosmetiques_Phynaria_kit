# Familiers cosmétiques dans les jeux : ce qui marche

Fiche de référence (recherche du 2026-11-05). Codes génériques tirés des jeux cités ; aucun design n'est à reprendre (CLAUDE.md, règle 5). Complète `types-familiers.md` (placement selon le type) et `.claude/styles/familiers.md` (règle du dépôt).

## 1. Panorama

| Jeu ou système | Ce que c'est | Placement, déplacement | Ce qui est retenu |
|---|---|---|---|
| **World of Warcraft**, mascottes de combat | Centaines de petits animaux et créatures, sans effet sur le jeu | Suivent le joueur au sol ; volants en l'air | Animations de repos variées (bâiller, s'asseoir, se coucher, gratter le sol, danser) ; les joueurs cherchent celles qui **réagissent** : réponse aux émotes du joueur (/wave en le ciblant), chats qui viennent se lover sur les genoux du joueur assis. Le site WarcraftPets a un filtre « interactivité » : c'est un critère d'achat |
| **Final Fantasy XIV**, mini-compagnons (*minions*) | Collection de plusieurs centaines, à peu près tous de la même petite taille | Trois comportements : **indépendant** (suit, puis se promène au repos), **obéissant** (suit et reste près du joueur au repos), **immobile** | Interactions entre deux compagnons et avec le joueur très appréciées ; certains se posent sur la tête des personnages de petite race au lieu de l'épaule |
| **MapleStory**, familiers | Animaux qui ramassent les objets | Marchent derrière le joueur et peinent à suivre s'il va vite ; les ailés flottent au-dessus du sol | Retard et effort pour suivre : il a l'air vivant |
| **Lost Ark**, familiers | Compagnons qui ramassent le butin | Suivent toujours le joueur | Utilité discrète, présence constante |
| **Path of Exile**, familiers de boutique | Purement cosmétiques, jusqu'à deux à la fois | Suivent, errent dans le repaire | Reproches : encombrement de l'écran, bruits pénibles, un familier qui fait trembler l'écran |
| **Pokémon HeartGold / SoulSilver** (et suivants) | Le premier de l'équipe marche derrière le dresseur | Au sol derrière, à un pas ; on se retourne pour lui parler, il exprime une humeur | Un compagnon qui « marche avec toi » crée l'attachement ; les grands et les volants posent des problèmes de taille et de placement |
| **Fortnite**, sacs-familiers (*pets*) | Animal porté **dans un sac-porteur au dos** | Il ne marche pas : il réagit depuis le sac | Réactions aux événements de la partie (planer depuis le bus, victoire…), on peut le caresser ; c'est l'équivalent le plus proche de notre mod, attaché au torse |
| **Genshin Impact**, compagnon guide | Petite créature magique qui flotte | À hauteur d'épaule, à côté du personnage | Code de la fée ou de l'orbe de fantaisie : flotter est logique pour un être magique |
| **Roblox** (Adopt Me, simulateurs de familiers) | Familiers à élever, à habiller, qui apprennent des tours | Suivent au sol, se portent dans les bras, se montent ; potions pour les faire voler | Tours et réactions (nourriture, jouets), animations débloquées en montant de niveau |
| **Minecraft vanilla** | Loup, chat, perroquet, allay | Loup : erre près du maître, le suit au-delà de 10 blocs, se téléporte au-delà de 12 ; perroquet : **sur l'épaule** (gauche d'abord), regarde là où regarde le joueur ; allay : vole à hauteur d'yeux, **danse** près d'un jukebox | Le perroquet descend de l'épaule aux bons moments (coup, chute, eau, vol, élytres, sommeil) ; l'allay a une texture lumineuse visible dans le noir |
| **Serveurs Minecraft** (extensions HeadPets, Entity Pet, Simple Pets) | Têtes de joueur ou vraies entités qui suivent | Flottent près du joueur (tête sur un porte-armure invisible) ou suivent au sol | Purement cosmétiques, ne prennent pas de dégâts ; la tête flottante est la version pauvre |
| **Petlings** (mod client Minecraft) | 42 espèces de familiers côté client | Suivent avec un chemin lissé, se promènent, s'assoient, jouent, regardent ; **après 30 s sans bouger, ils se roulent en boule et dorment** | 19 émotes en 5 familles : salut (signe, hochement, révérence), danse (tourner, sautiller, se tortiller), expression (saut de joie, perplexe, triste, colère, cœurs), action (s'asseoir, mendier, se rouler, faire le mort, dormir), tour (salto, équilibre, rapporter) ; accessoires animés, textures selon l'humeur |

## 2. Ce que les joueurs aiment

1. **Il réagit** à ce que fait le joueur (émotes, saut, coup reçu, victoire) et à ce qui l'entoure (musique pour l'allay, pluie, nuit). C'est le premier argument des familiers de Fortnite, des mascottes de WoW et des compagnons de FFXIV.
2. **Il a une vie propre au repos** : il s'assoit, se promène un peu, s'endort si le joueur ne bouge plus (Petlings : au bout de 30 s). Le comportement « indépendant » de FFXIV (se promener au repos) se distingue d'« obéissant » (reste à côté).
3. **Il suit avec effort** : retard, petite course pour rattraper (MapleStory), pas de translation rigide.
4. **Il touche le joueur** : il se pose sur l'épaule ou la tête, se love sur ses genoux, se fait caresser. Le contact crée l'attachement.
5. **Il est mignon et lisible** : tête grosse, yeux expressifs, silhouette simple (`../animaux/README.md`, schéma du bébé).
6. **Il exprime une humeur** : joie, tristesse, perplexité, colère, cœurs (Petlings, Pokémon qui suivent).

## 3. Ce que les joueurs reprochent

- **Encombrement visuel** : trop grand, ailes larges qui couvrent un atelier (ESO), écran plein de familiers en ville et en combat (WoW, City of Heroes, Guild Wars 2) ; beaucoup demandent une option pour cacher ceux des autres.
- **Bruit** : sons répétés « pénibles » (Path of Exile). Même constat chez nous : « infernal » quand chaque mouvement siffle (`.claude/rules/essentiel.md`, Sons rares).
- **Effets agressifs** : tremblement d'écran, lumières vives, particules en continu.
- **Familier qui ne suit pas** ou se téléporte sans transition (forums de Conan Exiles : compagnons qui ne marchent ni ne courent, ils se téléportent).
- **Passivité** : un familier qui ne fait rien (notre propre retour du 2026-11-04 sur `familier_givre`).

## 4. Taille, placement et lisibilité

- **Taille** : les jeux gardent les familiers à l'échelle d'un petit animal, autour d'un tiers à la moitié de la hauteur du personnage au plus (FFXIV : tous à peu près de la même taille). Chez nous : 10 à 14 px de long (corps et tête), 6 à 9 px pour un familier d'épaule, pour un joueur de 32 px. Au-delà, il encombre (reproche n° 1).
- **Placement** : à côté et un peu en arrière du joueur, jamais devant le visage ni dans l'axe de la caméra en troisième personne (dos du joueur). Le côté gauche du joueur est celui du perroquet de Minecraft.
- **Lisibilité à distance** : la silhouette porte l'essentiel (environ 70 % de l'effet d'un design vient de sa silhouette selon les guides de conception de personnages) ; tester en noir sur blanc, en petit, puis la répartition des masses de couleur, puis le détail seulement s'il renforce les deux premiers niveaux. Le visage reste le point focal : yeux grands, contraste fort, reflet blanc.
- **Une seule source de lumière vive** (yeux, gemme) : l'allay se voit dans le noir sans éclairer ; une lueur forte partout fait « effet de feu » (`.claude/rules/categories/auras.md`).

## 5. Animations attendues

| Famille | Exemples | Dans le mod |
|---|---|---|
| Repos varié | s'asseoir, se coucher, se gratter, bâiller, s'étirer, renifler, regarder autour | `idle` avec tirage Molang (`familiers.md`), un comportement à la fois |
| Sommeil après inactivité | se rouler en boule au bout de 30 s sans bouger | `idle` : `q.life_time` ne dit pas depuis quand le joueur est immobile ; avec une variable mémorisée `v.immobile = q.ground_speed < 0.1 ? v.immobile + q.delta_time : 0` (non simulé par le renderer, à juger en jeu) |
| Suivre | trot, galop, retard, rattrapage | `walk`, `run` synchronisés sur `q.ground_speed` (`../../styles/familiers.md`, recette au sol) |
| Réactions | saut avec le joueur, sursaut au coup, joie après l'attaque, regard vers le joueur | `event_jump`, `event_land`, `hurt`, `attack` |
| Changement de posture | monter sur l'épaule quand le joueur vole, redescendre à l'atterrissage | `event_enter_fly`, `event_exit_fly`, `event_enter_glide` (guide 6.4) |
| Humeur | oreilles et queue selon la vie, la nuit, la pluie | Molang : `q.health / q.max_health`, `q.time_of_day`, `q.is_in_rain` |
| Arrivée, départ | apparaît d'un bond, d'une fumée, d'un cercle | `event_equip`, `event_unequip` |
| Émotes du joueur | répondre à un salut, danser | **Impossible** : le mod ne transmet pas les émotes du joueur (à demander au développeur si l'utilisateur le veut) |

Budget : 16 animations. Les 12 états, un `overlay_` et trois événements remplissent déjà tout (`../animaux/README.md`) ; un familier au sol qui monte sur l'épaule a besoin de `event_enter_fly` / `event_exit_fly` : retirer `mount` (repli sur `idle`) ou `swim` si nécessaire, et le dire dans la livraison.

## 6. Sources

- [Forum Blizzard, Pet surprises (emotes)](https://us.forums.blizzard.com/en/wow/t/pet-surprises-emotes/27176)
- [Blizzard Watch, Cat pets now curl up in your lap](https://blizzardwatch.com/2015/07/20/cat-pets-now-curl-lap-game/)
- [Forum Blizzard EU, Mischief special moves](https://eu.forums.blizzard.com/en/wow/t/does-mischief-have-any-special-moves/115574)
- [Forum Blizzard EU, Pets that sit on head or shoulders](https://eu.forums.blizzard.com/en/wow/t/list-of-pets-that-sit-on-head-shoulders/97260)
- [Console Games Wiki, FFXIV Minions](https://ffxiv.consolegameswiki.com/wiki/Minions)
- [Fandomspot, FFXIV cutest minions](https://www.fandomspot.com/ffxiv-cutest-minions/)
- [StrategyWiki, MapleStory pets](https://strategywiki.org/wiki/MapleStory/Pets)
- [Fextralife, Lost Ark pets](https://lostark.wiki.fextralife.com:443/Pets)
- [Path of Exile Wiki, Pet](https://pathofexile.fandom.com/wiki/Pet)
- [Steam, Path of Exile 2 discussion on pets](https://steamcommunity.com/app/2694490/discussions/0/594008672803344064)
- [Bulbapedia, Walking Pokémon](https://bulbapedia.bulbagarden.net/wiki/Walking_Pokemon)
- [Dot Esports, Fortnite pets list](https://dotesports.com/fortnite/news/fortnite-pets-list)
- [Sportskeeda, Best Fortnite pet back blings](https://www.sportskeeda.com/fortnite/5-best-fortnite-pet-back-blings-can-use-in-game)
- [Wikipedia, Paimon (Genshin Impact)](https://en.wikipedia.com/wiki/Paimon_(Genshin_Impact))
- [Adopt Me, Pet needs revamp](https://www.playadopt.me/news/pet-needs-revamp)
- [Tryhard Guides, Adopt Me playful pets update](https://tryhardguides.com/adopt-me-playful-pets-update-is-now-available/)
- [Minecraft Wiki, Parrot](https://minecraft.wiki/w/Parrot)
- [Minecraft Wiki, Allay](https://minecraft.wiki/w/Allay)
- [Modrinth, HeadPets](https://modrinth.com/plugin/headpets)
- [CurseForge, Entity Pet](https://www.curseforge.com/minecraft/mc-mods/entity-pet/install)
- [Modrinth, Petlings](https://modrinth.com/mod/petlings)
- [Forums ESO, Winged Twilight problems](https://forums.elderscrollsonline.com/en/discussion/505150/possible-way-to-lessen-winged-twilight-problems)
- [Forum Blizzard, Pets everywhere](https://us.forums.blizzard.com/en/wow/t/pets-everywhere/2183259)
- [Guild Wars 2 forum, The visual clutter problem](https://en-forum.guildwars2.com/topic/92849-the-visual-clutter-problem/)
- [Funcom forums, Following pets only teleport](https://forums.funcom.com/t/resolved-following-pet-thralls-do-not-walk-run-only-teleport/168820)
- [Bugnet, Readable game art](https://bugnet.io/blog/readable-game-art-why-clarity-beats-detail)
- [Rocketbrush, Shape language in game character design](https://rocketbrush.com/blog/shape-language-in-game-character-design-how-to-make-characters-readable-and-consistent)
