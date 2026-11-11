# Types de familiers : où ils se tiennent, comment ils bougent

Fiche de référence (recherche du 2026-11-05), écrite après le retour sur `familier_givre` v2 : « un familier ne vole pas forcément : il peut être au sol comme un vrai renard, ou sur l'épaule s'il est volant, ça dépend s'il est magique ou non, de son type ». Complète `.claude/styles/familiers.md` (principes, Molang de hasard), qui reste la règle, et les fiches d'animaux (`../animaux/`) et de créatures (`../creatures/`).

## 1. Ce qu'est un familier

- **Folklore européen** (Moyen Âge, début de l'époque moderne) : un esprit, une fée ou un démon sous forme d'animal, rarement humaine, qui aide une sorcière ou un guérisseur (protection, divination, objets perdus). Formes citées dans les procès : chats, rats, chiens, furets, oiseaux, grenouilles, crapauds, lièvres ; plus rarement guêpes, papillons, porcs, moutons, chevaux. Ils portaient des surnoms affectueux et **vivaient dans des pots ou des paniers garnis de laine**. Point clé : l'animal n'est pas un animal, c'est un esprit qui en a pris la forme ; il se comporte en animal mais peut trahir sa nature (regard, lumière, apparition).
- **Japon** : le *shikigami* est un esprit serviteur invoqué par un onmyōji, sans forme stable (animal, ombre, objet, souvent un talisman de papier découpé qui s'anime). Le *tsukumogami* est un objet qui a pris une âme (lanterne, parapluie). Le *kitsune* bon (*zenko*, messager d'Inari) porte un joyau lumineux au bout de la queue et produit du feu de renard (*kitsunebi*), cousin du feu follet.
- **Alchimie et kabbale** : homoncule (petit humanoïde fabriqué, souvent en fiole) et golem (argile animée, fort, sans volonté propre).
- **Fiction et jeu** : compagnon lié par un pacte (D&D : espion, messager), mascotte de *magical girl* qui donne ses pouvoirs à l'héroïne et la guide, « créature liée » qui choisit son humain, fée qui guide le joueur (« Exposition Fairy »), mini-dragon d'épaule (« Shoulder-Sized Dragon »), animal sur l'épaule (« Parrot Pet Position », perroquet de pirate). Le chat noir reste le familier de sorcière par excellence.

## 2. Les types, un par un

Pour chaque type : où il se tient, comment il bouge, **pourquoi** (la cause physique qu'on doit voir), comportement, codes visuels anime. Les noms de placement renvoient à la section 3.

| Type | Placement | Locomotion et cause | Comportement | Codes visuels |
|---|---|---|---|---|
| **Animal réel compagnon** (chien, chat, renard, lapin, furet) | **Au sol à côté** ; petit animal : **épaule**, **capuche/sac**, **dans les bras** | Marche, trotte, galope : il a du poids et pas de magie. En l'air, il ne peut que sauter ou être porté | Celui de l'espèce (`../animaux/`) : renifle, s'assoit, se couche, joue, suit le regard | Anatomie juste, pelage, aucun effet. L'animal est crédible ou il n'est rien |
| **Familier de sorcière** (chat noir, crapaud, corbeau, hibou, rat, lièvre) | Chat : **au sol** ou **épaule / drapé sur la nuque** ; oiseau : **épaule**, **tête** ; crapaud, rat : **épaule**, **poche, chapeau, panier** | Comme l'animal ; l'oiseau vole pour de vrai (battements), le reste marche | Animal, avec un signe d'esprit discret : yeux qui luisent la nuit, regard trop humain, apparition dans une fumée | Couleurs sombres, yeux vifs (`_e`), collier ou grelot, symboles (lune, étoile) en petit |
| **Animal-esprit** (renard spectral, loup d'esprit, kitsune) | **Au sol** tant que le joueur est au sol (il marche « sur l'air », à 0,2–0,5 px du sol) ; s'élève quand le joueur quitte le sol | Marche d'animal, mais la magie l'autorise à monter : la cause doit se voir (flammes sous les pattes, brume, traînée) | Animal, plus calme et plus « noble » ; peut se dissoudre et réapparaître | Translucide aux extrémités (`trans_`), feu de renard, joyau, queues multiples, marques peintes |
| **Esprit, spectre, feu follet, âme** | **Flotte** à côté de l'épaule ou derrière, **orbite** lente | Lévite : pas de poids. Mouvement en dérive, en 8 lents, retard sur le joueur ; la traînée dit la vitesse | Curieux, joueur, fuit puis revient ; sursaute à la blessure | Corps qui s'efface vers le bas en traînée, lueur, yeux simples (points ou ovales), pas de pattes ou pattes atrophiées |
| **Invocation, shikigami, créature de pacte** | **Flotte** près de l'épaule ; papier : plane comme une feuille | Apparaît par un cercle, un talisman, une fumée (`event_equip`) ; flotte sans effort | Formel, obéissant, se tient en garde ; disparaît dans son talisman au repos (option) | Talisman, cercle magique, couleurs d'encre, bords découpés comme du papier |
| **Mascotte magique** (type *magical girl*) | **Flotte à hauteur du visage**, se cache derrière la tête ou l'épaule ; se pose **sur la tête** | Lévite par magie ; ses petites ailes sont décoratives : battements rapides et petits, sans rapport avec la portance | Bavarde, expressive, réagit à tout, gesticule | Tête énorme (1:1 avec le corps), ronde, gemme au front, oreilles longues, queue en ruban |
| **Élémentaire** (feu, eau, vent, pierre, givre) | Léger (feu, vent, eau, givre) : **flotte** ; lourd (pierre, métal) : **au sol** | Feu et vent ondulent, eau rebondit ou coule, pierre marche lourdement (rebond lent, pas sonores) | Trahit son élément : le feu crépite et grandit à la colère, l'eau se fige au froid, la pierre s'endort | Matière lisible avant la forme : flamme sans contour sombre (`.claude/rules/categories/auras.md`), eau en `trans_`, pierre à runes |
| **Mini-dragon, créature ailée** (dragonnet, wyverne, griffon) | **Épaule** (griffes plantées, queue enroulée autour du bras ou du cou) ou **tête** ; vole quand le joueur vole | Vrai battement d'ailes, décollage, plané ; au repos, il se perche | Fier, joueur, crache une petite flamme, se blottit dans le cou | Ailes de chauve-souris repliées, cornes couchées (`../creatures/dragons.md`) |
| **Oiseau, chauve-souris, insecte** | **Épaule** (gauche d'abord, comme le perroquet), **tête**, bras ; chauve-souris : suspendue sous le bras ou au col ; papillon : voltige | Vol réel ; se perche dès que le joueur s'arrête | Saccades de tête, s'ébouriffe, se lisse les plumes | `../animaux/oiseaux.md`, `chauves-souris.md`, `insectes.md` |
| **Fée, lucioles, pixie** | **Orbite** rapide autour de la tête, se pose **sur l'épaule** ou la tête au repos | Vol d'insecte (ailes `trans_` en éventail), trajectoire nerveuse | Guide, montre du doigt, tinte | Lumière, poussière en particules, ailes d'insecte |
| **Golem, automate, drone, homoncule** | Petit golem : **au sol** ; automate volant : **flotte** près de l'épaule ; homoncule : **épaule** ou fiole | Golem : pas lourds, balancement ; volant : cause mécanique visible (rotor, réacteur, vapeur, `.claude/rules/essentiel.md`) | Programmé : gestes répétitifs, tête qui pivote d'un coup, pannes et redémarrages | Rivets, lentille (`_e`), vapeur ; homoncule : humanoïde minuscule, disproportionné |
| **Objet animé** (lanterne, livre, parapluie, épée, chapeau) | **Flotte** ou **sautille** au sol sur un pied | Livre : plane en feuilletant ; parapluie : saute ; lanterne : balance comme suspendue | Mimiques d'objet : s'ouvre, se ferme, clignote | L'objet reste reconnaissable, on ajoute des yeux et une bouche ou une seule lueur |
| **Slime, blob, nuage** | **Au sol** (rebonds) ou **sur la tête / l'épaule** (s'étale) | Rebond avec écrasement-étirement ; nuage : flotte | Tremblote, s'aplatit à la chute, avale des choses | `../creatures/slimes-mascottes.md` |
| **Créature marine** (poisson, méduse) | **Flotte** dans une bulle ou dans l'air humide | Nage dans l'air : il faut une cause (bulle, magie de l'eau) | Pulse, tourne autour | `../animaux/marins.md` |
| **Mort-vivant** (crâne, squelette d'animal) | Crâne : **flotte** ; squelette d'animal : **au sol** | Crâne : lévitation ; squelette : marche cliquetante, saccadée | Claque des mâchoires, se démonte et se remonte | `../creatures/morts-vivants.md` |

Constat général dans les jeux (section du même nom dans `familiers-cosmetiques-jeux.md`) : les compagnons **terrestres marchent** à côté ou derrière (Pokémon qui suivent leur dresseur, familiers de MapleStory, loup de Minecraft), les **oiseaux se perchent sur l'épaule** (perroquet de Minecraft), les **êtres magiques flottent à hauteur d'épaule ou d'yeux** (allay de Minecraft, mascotte guide de Genshin Impact, fées guides). Dans MapleStory, seuls les familiers ailés flottent au-dessus du sol.

## 3. Placements possibles dans le mod

**Mise à jour du 2026-11-05** : le mod a maintenant un mode familier (`docs/guide-cosmetiques.md`, section 6.6) qui fait suivre le joueur sur le vrai sol, avec quatre modes : `sol` (animal réel), `vol` (près de l'épaule), `nage`, `perche` (sur l'épaule gauche). Le type ci-dessous donne le mode (`.claude/styles/familiers.md`). Avant ce mode, et encore sans bloc `familier`, un familier « au sol » est attaché au torse (`body`), pieds à la hauteur du sol, et c'est l'animation qui fait croire qu'il marche.

| Placement | Groupe de premier niveau | Position (px, repère du joueur) | Atouts | Limites dans le mod |
|---|---|---|---|---|
| **Au sol à côté** | `body` | pieds à y = 0, x ≈ ±8 à ±12, z de −2 à +4 | Le plus crédible pour un animal terrestre, se lit comme un vrai compagnon | Suit le torse : il faut la **contre-rotation** quand le torse s'incline (sneak, nage, sommeil, élytres) ; pas de pathfinding, il tourne autour du joueur avec lui ; le sol réel n'est pas connu (escaliers, dalles) |
| **Sur l'épaule** | `body` (pas le bras : il balance en marche) | sur le dessus de l'épaule : y ≈ 24, x ≈ ±5 à ±7 | Code universel (perroquet, dragonnet) ; toujours visible ; aucune contre-rotation debout | Petit (6 à 9 px de long) ; clipping avec la tête quand elle tourne ; en sneak il bascule avec le torse (contre-rotation partielle) |
| **Sur la tête** | `head` | y ≥ 32 | Suit le regard (le perroquet regarde où regarde le joueur) | Tout petit ; gêne la vue en première personne : le cacher avec `q.is_first_person` |
| **Flotte à côté** | `body` | x ≈ ±9 à ±12, y ≈ 24 à 30, un peu en arrière | Simple, toujours visible | Exige une cause (magie, ailes, rotor) ; sinon « un renard qui vole » (retour du 2026-11-05) |
| **Orbite** | `body` ou `head` | rayon 8 à 12 px | Fée, feu follet, petits esprits | Rotation continue dans un `overlay_` (règles d'animation) |
| **Derrière, dans le dos** | `body` | z ≈ +4 à +8 | Plané en élytres (il suit dans le sillage), sac porte-familier | On le voit mal de face |
| **Dans un sac, une capuche, une poche** | `body` (sac au dos, poche de poitrine) ou `head` (capuche) | tête qui dépasse | Animal minuscule, logique en l'air comme au sol | Les bras du joueur balancent devant la poitrine : poche de poitrine petite |
| **Dans les bras** | `body` | devant la poitrine, y ≈ 16 à 20, z ≈ −3 | Logique quand le joueur vole ou plane | Les bras du joueur ne l'entourent pas et balancent à travers lui : seulement en vol, en élytres et en monture, où les bras bougent peu (à vérifier en jeu) |

## 4. Arbre de décision

```
Le familier a-t-il une cause visible pour flotter ?
(esprit, spectre, fée, élémentaire léger, mascotte magique, objet animé, drone à rotor)
├── OUI → FLOTTE (A) : à côté de l'épaule, derrière ou en orbite.
│         Pattes repliées ou pendantes, jamais « marchant dans le vide ».
└── NON → A-t-il de vraies ailes et une petite taille (≤ 9 px) ?
          ├── OUI → PERCHÉ (B) : épaule (gauche d'abord) ou tête ; vole quand le joueur quitte le sol.
          └── NON → Animal terrestre ou créature lourde.
                    ├── Minuscule (≤ 6 px : souris, lézard, furet, crapaud, hamster) → PORTÉ (D) :
                    │   épaule, capuche, poche, sac.
                    └── Sinon (renard, chat, chien, loup, petit golem) → AU SOL (C) :
                        à côté du joueur ; en l'air, il saute dans ses bras, sur son épaule, ou dans son sac (E).
Animal-esprit (renard spectral, kitsune) : C au sol, A dès que le joueur quitte le sol (la magie le prend en charge).
```

### Placement → états du mod

| État | A — flotte | B — perché (volant) | C — au sol (terrestre) | D — porté (minuscule) |
|---|---|---|---|---|
| `idle` | dérive lente, comportements au hasard | perché, saccades, toilette | assis, couché, debout ; flaire, s'étire, se gratte (`familiers.md`) | sort la tête, regarde, se cache |
| `walk` | suit avec retard, penché dans le mouvement | perché, équilibre au rythme du pas | **trot** synchronisé (`q.ground_speed`) | balancé par le pas |
| `run` | traînée plus longue, plus loin derrière | s'envole et vole à côté, ou se cramponne, ailes entrouvertes | **galop en bonds** | se cramponne, oreilles au vent |
| `sneak` | descend, se fait petit | se tasse | **contre-rotation** du torse ; posture de chasse (avant bas, oreilles en avant) | se cache |
| `fly` (créatif) | monte avec lui | **vole** à côté (vrai battement) | **saute dans les bras ou sur l'épaule** (`event_enter_fly`), ou se cramponne au dos | reste porté |
| `glide` (élytres) | plane dans le sillage | vole derrière, ailes tendues | **accroché au dos** ou dans le sac, contre-rotation inutile (il suit le torse couché) | dans le sac |
| `fall` | monte un peu (inertie) | ailes ouvertes pour freiner | saute avec lui (`event_jump`), pattes en avant pour l'atterrissage (`event_land`) | se cramponne |
| `swim` | au-dessus de l'eau | perché sur le dos du joueur ou au-dessus | **nage** à côté, tête hors de l'eau (contre-rotation du corps couché), ou monte sur le dos | sur la tête, hors de l'eau |
| `mount` | à côté | perché | sur l'épaule ou en croupe (la hauteur de la monture n'est pas connue) | porté |
| `sleep` | s'endort en boule en lévitation basse | perché, tête sous l'aile | **roulé en boule** au pied du lit (contre-rotation du corps couché) | dort dans sa poche |
| `attack` | fonce et revient | s'envole, piqué | bond, aboie, grogne | sort et crie |
| `hurt` | sursaute, s'écarte | s'envole d'un coup (le perroquet quitte l'épaule à la blessure) | sursaute, oreilles plaquées, regarde le joueur | se cache |

Le perroquet de Minecraft quitte l'épaule quand le joueur prend un coup, tombe de plus de 0,75 bloc, monte une marche de 0,5 bloc, entre dans l'eau, vole en créatif, plane en élytres ou dort : c'est la liste des moments où un familier perché doit réagir (s'envoler, se cramponner).

## 5. Pièges

- « Renard qui vole » : un animal sans magie ni ailes ne flotte pas. Si la direction artistique veut qu'il flotte, la cause doit se voir (brume sous lui, flammes, gemme qui brille) et ses pattes pendent ou se replient.
- Pattes qui marchent dans le vide en lévitation : illogique (`.claude/rules/essentiel.md`).
- Mascotte à hauteur des yeux qui gêne la vue en première personne : la reculer ou la cacher avec `q.is_first_person`.
- Familier perché attaché au bras : il balance avec le bras en marche. Le mettre dans `body`, au-dessus de l'épaule.
- Familier au sol sans contre-rotation : en sneak il recule de plus de 10 px et s'enfonce ; en nage et en élytres il se retrouve couché à l'horizontale (recette « familier qui marche au sol » de `../../styles/familiers.md`).
- Un type par familier : un renard de givre est un **animal-esprit** (C au sol, A en l'air), pas une mascotte qui flotte en permanence.
- Pas de copie d'un compagnon protégé (mascottes d'anime, Pokémon, compagnons de jeu cités) : codes génériques seulement (CLAUDE.md, règle 5).

## 6. Sources

- [Wikipedia, Familiar](https://en.wikipedia.org/wiki/Familiar)
- [Encycloreader, Familiar](https://encycloreader.org/r/wikipedia.php?q=Familiar)
- [Medium, Familiars in folklore and modern witchcraft](https://medium.com/@AncientPathways/familiars-in-folklore-and-modern-witchcraft-57552d5ea0a4)
- [Wikipedia, Shikigami](https://en.wikipedia.org/wiki/Shikigami)
- [Japan Italy Bridge, Shikigami](https://japanitalybridge.com/en/2025/02/shikigami-spiritual-guardians-and-powerful-entities-of-japanese-folklore)
- [Superpower Wiki, Tsukumogami physiology](https://powerlisting.fandom.com/wiki/Tsukumogami_Physiology)
- [Wikipedia, Kitsune](https://en.wikipedia.org/wiki/Kitsune)
- [Wikipedia, Will-o'-the-wisp](https://en.wikipedia.org/wiki/Will-o%27-the-wisp)
- [Wikipedia, Homunculus](https://en.wikipedia.org/wiki/Homunculus)
- [TV Tropes, Animal Mentor](https://tvtropes.org/pmwiki/pmwiki.php/Main/AnimalMentor)
- [TV Tropes, Bond Creature](https://tvtropes.org/pmwiki/pmwiki.php/Main/BondCreature)
- [TV Tropes, All Witches Have Cats](https://tvtropes.org/pmwiki/pmwiki.php/Main/AllWitchesHaveCats)
- [TV Tropes, Shoulder-Sized Dragon](https://www.tvtropes.org/pmwiki/pmwiki.php/Main/ShoulderSizedDragon)
- [TV Tropes, Fairy Companion](https://tvtropes.org/pmwiki/pmwiki.php/Main/FairyCompanion)
- [TV Tropes, Shoulder Pet](https://tvtropes.org/pmwiki/pmwiki.php/Main/ShoulderPet), [Head Pet](https://tvtropes.org/pmwiki/pmwiki.php/Main/HeadPet)
- [Tropedia, Parrot Pet Position](https://tropedia.fandom.com/wiki/Parrot_Pet_Position)
- [All The Tropes, Familiar](https://AllTheTropes.org/wiki/Familiar)
- [Popheist, Best magical girl mascots](https://popheist.com/best-magical-girl-mascots)
- [Minecraft Wiki, Parrot](https://minecraft.wiki/w/Parrot)
- [Minecraft Wiki, Allay](https://minecraft.wiki/w/Allay)
- [Minecraft Wiki (fandom miroir), Wolf](https://breezewiki.discard.no/minecraft/wiki/Wolf)
- [Bulbapedia, Walking Pokémon](https://bulbapedia.bulbagarden.net/wiki/Walking_Pokemon)
- [StrategyWiki, MapleStory pets](https://strategywiki.org/wiki/MapleStory/Pets)
- [Wikipedia, Paimon (Genshin Impact)](https://en.wikipedia.com/wiki/Paimon_(Genshin_Impact))
