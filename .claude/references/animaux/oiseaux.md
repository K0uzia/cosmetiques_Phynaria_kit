# Oiseaux : petits passereaux, hibou et chouette, corbeau, rapaces (aigle, faucon)

Fiche de référence (recherche du 2026-11-04). Familiers, chapeaux, épaulières. Pour les ailes portées par le joueur, la fiche qui prime est `.claude/styles/ailes-anatomie.md` (squelette, types d'aile, repli) ; recette de plume : `modeling.md` (peau + âme).

## 1. Silhouette et proportions

Unité : la tête (H). Un oiseau perché se lit comme **une goutte** (tête + corps) posée sur des pattes courtes, ailes rangées le long du corps, queue dans le prolongement.

| | Tête | Corps (sans queue) | Queue | Pattes visibles | Bec |
|---|---|---|---|---|---|
| Passereau (moineau, mésange) | 1, ronde | 1,8 H, boule | 1 à 2,5 H (mésange à longue queue : 3 H) | 0,4 H, fines | 0,3 H, court, conique |
| Hibou, chouette | 1, énorme, presque aussi large que le corps | 1,5 H | 0,5 H, courte | cachées dans les plumes, serres seules | petit, crochu, enfoui dans le disque facial |
| Corbeau | 1 | 2,2 H | 1,8 H, **en coin** (grand corbeau) ou **en éventail** (corneille) | 0,8 H, fortes | 0,8 H, massif, plumes sur la base |
| Aigle | 1 | 2,5 H, massif | 1,2 H, large | 0,6 H, « culottes » de plumes, serres énormes | 0,7 H, très crochu |
| Faucon | 1, ronde | 2 H, compact | 1,3 H | 0,5 H | 0,4 H, crochu, avec dent |

Familier de 8 px (oiseau perché sur l'épaule) : tête 2,5 px, corps 3,5 px, queue 2 px, pattes 0,8 px. Hibou de 8 px de haut : tête 3,5 px de large.

Envergure réelle ≈ 1,5 à 2,2 fois la longueur du corps ; aile ouverte d'un familier : 6 à 9 px par aile.

## 2. Ce qui fait l'animal

- **Passereau** : boule, bec court, queue relevée, pattes très fines. La **mésange à longue queue** d'Hokkaidō (« fée des neiges », très populaire au Japon) : boule blanche de coton, minuscule bec, queue longue et fine, yeux noirs ronds.
- **Hibou, chouette** : **disque facial** (plumes en coupelle qui dirigent le son), **yeux fixes de face** (tubulaires, ils ne bougent pas dans l'orbite : toute la direction du regard passe par la tête), tête qui tourne jusqu'à 270°. Hibou = aigrettes (« oreilles » de plumes, qui ne sont pas des oreilles) ; chouette = tête ronde sans aigrettes.
- **Corbeau** : tout noir à reflets bleus et violets, bec épais et long, **plumes ébouriffées de la gorge** (hackles, « barbe » quand il croasse), tête plus « hirsute » que la corneille lisse ; queue en coin chez le grand corbeau.
- **Aigle** : **arcade sourcilière** saillante au-dessus de l'œil (regard sévère), bec très crochu, ailes larges et rectangulaires à primaires écartées en doigts, pattes emplumées.
- **Faucon** : ailes longues et pointues, « moustache » noire sous l'œil, grand œil sombre, pas d'arcade marquée, **dent tomiale** (petite pointe sur le bord du bec).

## 3. Mouvement et comportement

**Base de repos** : respiration rapide chez les petits (gorge et ventre, 0,5 à 1 s), **saccades de tête** (immobile, puis tourne d'un coup, immobile), queue qui bat de haut en bas par à-coups (alerte), clignement par la troisième paupière (membrane qui passe **horizontalement** de l'avant vers l'arrière de l'œil, rapide).

**Comportements ponctuels** :

| Geste | Durée | Détail |
|---|---|---|
| S'ébouriffer (« rouse ») | 0,8 à 1 s | toutes les plumes se dressent (le corps grossit de 20 à 40 %), secousse, puis tout se replace ; souvent avant de changer d'activité |
| Se lisser | 2 à 4 s | bec qui passe dans les plumes du flanc ou de l'aile, tête tournée en arrière |
| Étirement aile + patte | 1,5 à 2 s | une aile et la patte du même côté tendues vers l'arrière et le bas, puis l'autre côté |
| Croiser les ailes (« warbling ») | 1 s | les deux ailes levées et croisées au-dessus du dos, après s'être ébouriffé |
| Essuyer le bec (« feaking ») | 1 s | bec frotté de chaque côté sur le perchoir (l'épaule du joueur) |
| Hochement du hibou | 1 à 2 s | tête qui oscille de côté et de haut en bas pour mesurer la distance (triangulation) |
| Tête retournée du hibou | 1,5 s | rotation lente à 180°, pause, retour |
| Sautillement (passereau) | 0,2 s par saut | il saute à pieds joints, ne marche pas ; le corbeau, lui, marche en se dandinant et sautille quand il se presse |
| Tête penchée (corbeau) | 1 s | un œil vers l'objet, curiosité ; il collectionne et cache des objets brillants |
| Protéger sa proie (rapace, « mantling ») | 2 s | ailes étendues en cape au-dessus de ce qu'il tient |
| Battement sur place | 1 à 2 s | ailes ouvertes qui battent sans décoller : joie ou équilibre |

Battements réels : moineau 20 à 30 par seconde, colibri 50 à 75 ; grands oiseaux 2 à 4. Un familier lisible bat à **4 à 8 Hz** (au-delà, une keyframe sur deux tombe mal).

**Langage du corps** :
- Joie : plumes lisses, gazouillis (bec qui s'ouvre), petits sautillements, battements.
- Curiosité : tête penchée, cou allongé, saccades.
- Peur : plumes plaquées (oiseau mince), yeux grands ouverts, prêt à s'envoler ; hibou : se fait **mince et allongé**, aigrettes dressées.
- Menace : plumes et ailes gonflées, bec ouvert, queue étalée ; hibou : ailes en demi-cercle autour de lui, claquement du bec.
- Froid, repos : **boule** (plumes gonflées), une patte repliée sous le ventre.
- Sommeil : tête tournée vers l'arrière, bec dans les plumes du dos, yeux fermés.

## 4. Version anime / stylisée

- **Proportions** : oiseau = une sphère (tête et corps fondus en un seul volume), ailes réduites à deux petites palettes, pattes deux traits, bec minuscule triangulaire. Hibou : une sphère avec deux énormes yeux qui occupent la moitié de la face.
- **Visage** : yeux noirs ronds avec un reflet (passereau), ou grands yeux d'or à pupille large (hibou) ; joues rouges en ovales pour les passereaux ; sourcils peints au-dessus de l'arcade pour l'aigle sévère.
- **Expressions** : ailes qui se lèvent comme des bras (surprise, joie), plumes dressées en épis (colère, réveil), boule qui gonfle (contentement, froid), plumes de tête en épi qui retombe (tristesse).
- **Ambiance japonaise** : la chouette porte-bonheur (*fukurō*, jeu de mots « sans souci », « le bonheur vient »), la fée des neiges d'Hokkaidō, corbeaux messagers des contes. Motifs, pas personnages.

## 5. Traduction dans le mod

- **Hiérarchie** : `fam_elan` > `fam_pos` > `fam_rot` > `corps` (échelle : respiration, s'ébouriffer) > `tete` (> `bec_haut`, `bec_bas`, `oeil_l`, `oeil_r`, `paupiere_*`, `aigrette_l/r`) ; `aile_l` > `main_l` (deux segments suffisent pour un familier) ; `queue` ; `patte_l`, `patte_r`.
- **Plumage** : corps en volumes arrondis (boîte + jumeau à 45°) couverts d'écailles de plumes en peau découpée (bords ronds) ; rémiges en peau + âme comme `aurelion` ; disque facial du hibou = une plaque ronde découpée, légèrement concave (2 ou 3 plaques étagées).
- **Clignement** : paupière inférieure qui remonte (beaucoup d'oiseaux) ou membrane latérale : petite plaque `trans_` (alpha 120 à 180) qui glisse en x devant l'œil. Pour un style mignon, paupière classique.
- **Tête qui tourne** : rotation y de la tête **seule** jusqu'à ±180° (hibou), corps immobile, en saccades (keyframes en marches, interpolation `linear` sur 0,1 s).
- **S'ébouriffer** : échelle de `corps` 1 → 1,3 en 0,15 s, tremblement 8 à 10 Hz pendant 0,5 s, retour en 0,2 s ; les écailles de plumes peuvent avoir leur propre petit groupe pour se soulever.
- **Particules** : plumes qui tombent en s'ébouriffant : **non** sur un familier (consigne : particules qui tombent sur les ailes seulement, `.claude/rules/essentiel.md`), sauf demande.
- **Molang** : saccades de tête par tirage `math.floor(q.life_time / 1.3 + q.instance_seed * 7)` ; regarde là où regarde le joueur (`q.head_y_rotation`, retard) ; pluie : boule ébouriffée ; nuit (`q.time_of_day`) : le hibou s'éveille (yeux grands, aigrettes dressées), le passereau dort tête dans le dos.
- **Événements** : `event_jump` (ailes ouvertes pour l'équilibre), `event_land` (battement de rattrapage), `event_equip` (arrive en vol et se pose, 1,5 s).

## 6. Pièges

- Yeux de hibou qui bougent dans la tête : faux ; c'est la tête qui bouge.
- Hibou sans disque facial : n'importe quel oiseau rond. Aigrettes sur une chouette : erreur d'espèce.
- Rotation de tête lisse et continue : les oiseaux bougent la tête **par saccades**, c'est leur signature.
- Ailes collées comme des plaques sur les flancs : « carton ». Les ailes rangées couvrent le flanc et se croisent sur le croupion, les primaires dépassent au-dessus de la queue.
- Passereau qui marche en alternant les pattes : il sautille. Corbeau : il marche.
- Battement trop rapide pour l'échantillonnage : saccadé ou figé. Rester à 4 à 8 Hz.
- Bec en cube plein : « bec de canard en lego ». Deux pièces (haut, bas) effilées, le haut qui recouvre le bas, bout crochu pour les rapaces.

## 7. Sources

- [Audubon, Why do owls bob their heads](https://www.audubon.org/magazine/why-do-owls-bob-their-heads)
- [Shortform, What an Owl Knows (Ackerman)](https://www.shortform.com/summary/what-an-owl-knows-summary-jennifer-ackerman)
- [Birdfact, Displays and postures](https://birdfact.com/bird-behavior/communication/displays-and-postures)
- [BirdNote, tail flicking](https://birdnote.org/node/16866)
- [Birds Outside My Window, Nictitating membrane](https://birdsoutsidemywindow.org/?p=15839)
- [All About Birds, Singing wings (fréquence des battements)](https://academy.allaboutbirds.org/singing-wings-behavior/)
- [RSPB, How to identify a raven](https://web-cdn.rspb.org.uk/birds-and-wildlife/raven)
- [Corvid Research, Raven behavior](https://corvidresearch.blog/category/raven-behavior/)
- [Birdfy, Crow vs raven](https://www.birdfy.com/blogs/blogs/how-to-identify-a-crow-and-a-raven-key-features-explained)
- [Raptor Center UMN, Hooked beaks](https://raptor.umn.edu/about-us/news/what-makes-raptor-part-1-hooked-beaks)
- [Peregrine Fund, Curved beaks](https://peregrinefund.org/curved-beaks)
- [Vedantu, Falcon vs eagle](https://www.vedantu.com/evs/difference-between-falcon-and-eagle)
- [CSU Falcon Cam, Glossary (mantling, rouse, feaking, warbling)](https://science-health.csu.edu.au/falconcam/common-questions/glossary)
- [BirdLife, Snow fairies (shima-enaga)](https://birdlife.org/news/2023/02/01/snow-fairies-in-a-winter-wonderland)
- [Nomura Kakejiku, Owls that bring happiness](https://nomurakakejiku.com/kakejiku-art-blog/post-8725.html)
