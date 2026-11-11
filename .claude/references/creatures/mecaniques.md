# Êtres mécaniques — automates, golems mécaniques, steampunk

Fiche de référence (2026-11-04). Ensemble du dépôt : **Steampunk** (`.claude/styles/steampunk.md`, à lire d'abord : palette, mouvement en paliers, cycle de pression, vapeur). Pièces : `ailes_steampunk` (taille et couches validées en jeu), `familier_steampunk`, `queue_steampunk`, `haut_de_forme_steampunk`, `epaulieres_steampunk`, `pistolet_steampunk`. Cette fiche ajoute ce qui fait d'une machine un **être**.

## 1. Codes visuels essentiels

- **Automate d'horloger** (*karakuri ningyō*, Japon, XVIIe–XIXe s.) : poupée de bois sculpté d'environ 30 cm, mue par **ressorts en fanon de baleine, cames et leviers**. La poupée qui sert le thé avance quand on pose la tasse, **s'incline** devant l'invité, s'arrête quand il prend la tasse, **fait demi-tour** quand elle revient sur le plateau. C'est le modèle d'un être mécanique attachant : **un geste poli et lisible, déclenché par une cause**.
- **Gardien ancien** (comme les robots des films de Miyazaki sur les cités volantes) : massif, **ancien plutôt que lisse**, rayures sur l'armure, **mousse et fleurs dans les joints**, un œil unique ; il « pèse » à chaque pas. La tendresse vient du contraste entre arme ancienne et geste doux (offrir une fleur, abriter un oiseau).
- **Automate steampunk** : laiton, cuivre, rivets, **clé de remontage** dans le dos, lentilles ambre pour les yeux, engrenages visibles par une fenêtre, soupapes.
- **Golem mécanique** : golem (`elementaires.md`) dont le cœur est une chaudière ou un ressort, et les runes des cadrans.

| Registre | Codes |
|---|---|
| Élégant | Laiton poli, verre, façade de porcelaine ou de bois laqué, mouvements précis d'horloger |
| Mignon | Petit robot rond, grands yeux-lentilles, antenne, clé de remontage trop grande, bruit de tic-tac |
| Menaçant | Œil rouge unique, armure épaisse, vapeur noire, mouvements trop rapides |

## 2. Silhouette et proportions (échelle du dépôt)

- **Automate-familier** : 8–11 px ; tête 3–4 px avec des yeux-lentilles de 1–1,5 px ; clé de remontage 2–3 px dans le dos (elle tourne).
- **Gardien-familier** : 10–12 px, épaules larges, petite tête, un œil ; jambes courtes et lourdes.
- **Ailes mécaniques** : envergure 59–69 px (réduction K = 0,62 autour de l'épaule, validée) ; lames sur une grille de 0,2 px, âmes cachées.
- **Queue mécanique** (v3, 2026-11-08) : comme une queue robotique à câbles : cloisons (bulkheads) qui diminuent vers la pointe, joint universel entre deux cloisons (tangage et lacet découplés), câbles ancrés au bout et passés dans des œillets, enroulés par des tambours à la base ; un vérin pour la première articulation. Mouvement : onde progressive du robot serpent (amplitude et retard croissants vers la pointe). Pointe utile : gouvernail (empennage) + buse d'échappement.
- Pièces de structure à 0,05 px au moins des faces des lames ; rivets ≥ 3 texels.

## 3. Matières et couleurs (HD 32–40 texels/px)

- Palette Steampunk (laiton, cuivre, acier bruni, cuir, verre ambre, vapeur blanc bleuté).
- **Métal propre** : brossé à ±6 % au plus, **pas de vert-de-gris ni de taches** (« bugs de texture ») ; l'âge se lit au bord et aux rivets, ou par de la **mousse** en plaques découpées (gardien ancien) plutôt que par de la rouille.
- **Bois laqué** (automate japonais) : laque rouge ou noire à reflet net, visage de porcelaine blanc mat, cheveux en laque noire.
- **Yeux-lentilles** : verre ambre ou cyan, iris à lamelles peintes, reflet blanc ; source de lumière **nette**, petite, vive (150–225 en `_e`).

## 4. Mouvement, comportement, attitude

- **Saccadé réaliste** (`steampunk.md`) : tic, arrêt, tic ; dépassement puis rappel (1–2 rebonds) ; articulations l'une après l'autre ; **déformation du temps en paliers** sur toute la pose, nombre entier de paliers par boucle.
- **Le moteur explique le geste** : la pression monte, la soupape tremble, la vapeur sort après ; l'effort se fait pendant la décharge. Un appareil à rotor ne bat pas des ailes (leçon du hibou).
- **Ce qui le rend vivant** (`familiers.md`) : il **salue** (inclinaison polie, comme l'automate à thé, 1 s), penche la tête avec un clic, ses lentilles **font la mise au point** (iris qui se ferme puis s'ouvre), il se remonte lui-même (clé qui tourne plus vite) quand il est « fatigué » (nuit, vie basse) ; il s'arrête net, puis repart.
- **Gardien** : très lent, poids visible, ne se presse jamais ; geste doux et rare (tend la main, se penche vers le joueur).
- **Apparition (`event_equip`)** : il se **déplie** depuis un boîtier (recette des ailes mécaniques : réservoir cylindrique riveté, hublots à iris), puis s'allume : lentilles d'abord, puis vapeur.

## 5. Langage anime

- **Yeux qui s'allument** avec un petit éclat à l'activation, **se mettent au rouge** en mode combat.
- **Lignes lumineuses** qui parcourent le corps (circuits, rainures) au démarrage.
- **Vapeur** en jets nets et blancs à la décharge ; petites bouffées régulières au repos (machine qui respire).
- **Gardien ancien** : oiseaux posés sur lui, fleurs, lumière douce de jardin ; la machine immobile au milieu de la nature.
- Expression par les **lentilles et les antennes** (pas de bouche) : iris qui se rétracte (surprise), antenne qui retombe (tristesse).

## 6. Traduction dans le mod

- **Mouvement** : fonction `palier(t)` appliquée à toute la pose, échantillonnage ≥ 24 keyframes/s, l'optimiseur simplifie les arrêts.
- **Engrenages, clé de remontage, rotor** : rotation continue dans `overlay_<nom>` (360°·k par boucle) ; ceux qui avancent par crans restent dans les états.
- **Lentilles et cadrans** : `_e` net (150–225) + couleur claire dans la texture (shader) ; `ctrl_lumiere` pour la mise au point ou l'éveil (non simulé par le renderer).
- **Vapeur** : jet modélisé en plaques `trans_` (visible avec shader), `scale` 0 → 1 en 0,1 s puis effacement par `ctrl_alpha` ; `emit_mc_white_smoke` à la buse (de nouveau utilisable depuis le correctif du 2026-11-04 : à réintroduire avec prudence et à juger en jeu), `ctrl_emit` −1 puis +4 pendant la décharge. **La vapeur monte, ne retombe jamais en nuage.**
- **Mousse du gardien** : plaques découpées par alpha dans les joints, légèrement décollées (≥ 0,03 px) des faces de métal.
- **Reflets `_r`** : retirés (`REFLETS = False`) tant que le bug de la découpe persiste.
- **Sons** (rares) : `block.piston.extend`, `ui.button.click`, `block.fire.extinguish` à la décharge ; un son au repos seulement si la boucle dure 20 s ou plus.

## 7. Pièges

- Âmes qui dépassent des lames empilées : « texture qui clipe entre les plumes » ; une couche par lame sur une grille régulière.
- Carénage plat entre deux engrenages : « bloc entre les deux engrenages » ; os nus et fins entre les articulations.
- Mouvement souple comme un muscle : il perd son identité de machine. Mouvement sans cause (vapeur avant la pression, ailes qui battent sous un rotor) : « pas logique ».
- Nuage de vapeur qui tombe : « pas logique ».
- Patine, rouille en taches, brossé contrasté : « bugs de texture ».
- Lumières trop faibles : « je ne vois aucune lumière sur le set » ; des sources nettes et logiques.
- Reproduire un robot de film reconnaissable (silhouette + œil + mousse d'un personnage) : s'en tenir au principe (arme ancienne devenue douce).

## 8. Sources

- [Karakuri puppet (Wikipedia)](https://www.wikipedia.com/wiki/Karakuri_ningyo)
- [Tea-serving doll, mécanisme (Kyoto University Museum)](https://www.museum.kyoto-u.ac.jp/english/materials/chakumiDolleng.html)
- [A history of robotics: tea serving karakuri (Salvius)](https://blog.salvius.org/2014/01/a-history-of-robotics-tea-serving.html)
- [Chahakobi ningyō, tea serving doll (Kamm Teapot Foundation)](https://kammteapotfoundation.org/chahakobi-ningyo-tea-serving-doll/)
- [Japan's first robots are older than you think (Gizmodo)](https://gizmodo.com/5849242/japans-first-robots-are-older-than-you-think)
- [Traditional Japanese automaton build (Atlas Obscura)](https://assets.atlasobscura.com/articles/traditional-japanese-automaton-build)
- [Castle in the Sky (Wikipedia)](https://en.wikipedia.org/wiki/Castle_in_the_Sky)
- [Retrofuturism is Miyazaki's not-so-secret weapon (Dust on the VCR)](https://dustonthevcr.substack.com/p/castleinthesky)
- [Castle in the Sky at 30 (Den of Geek)](https://www.denofgeek.com/movies/studio-ghibli-s-castle-in-the-sky-at-30/)
- Sources mécaniques (échappement, servo, soupape) : voir `.claude/styles/steampunk.md`.
- [Cable length invariant robotic tail, universal joint (NSF PAR)](https://par.nsf.gov/biblio/10155499-cable-length-invariant-robotic-tail-using-circular-shape-universal-joint-mechanism)
- [TALE-teller, tendon-actuated linked element tail (arXiv)](https://arxiv.org/html/2410.21445v1)
- [Serpenoid gait function (robot serpent)](https://api.emergentmind.com/topics/serpenoid-gait-function)
