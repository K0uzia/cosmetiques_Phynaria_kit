# Dragons — occidental, oriental, wyverne, bébé dragon

Fiche de référence (2026-11-04). Pièces concernées : ailes, cornes (`chapeaux`), queue, familier, aura serpentine. Pièce proche déjà livrée : `ailes_abyssales` (membrane validée « juste incroyable »), à reprendre pour toute membrane de dragon.

## 1. Codes visuels essentiels

| Type | Ce qui le fait reconnaître | Variantes |
|---|---|---|
| **Occidental** | Quatre pattes **et** une paire d'ailes de chauve-souris, corps trapu, cornes qui partent vers l'arrière, crête d'épines dorsales, plaques ventrales | Élégant : cou long, tête fine, cornes lisses, peu d'épines. Menaçant : mâchoire lourde, cornes multiples, épines partout |
| **Oriental (ryū, long)** | Serpent sans ailes, **andouillers de cerf**, moustaches longues de poisson-chat, crinière qui flotte, petites pattes à **3 griffes** (Japon) ou 4–5 (Chine), perle tenue dans la griffe | Il vole sans ailes, par magie : il « nage » dans l'air. Associé à l'eau, à la pluie, à la sagesse, bienveillant |
| **Wyverne** | Deux pattes arrière seulement, les **ailes sont les bras** (doigts-griffes au poignet), queue souvent terminée en dard ou en lame | Plus oiseau que lézard, plus petite, plus nerveuse. C'est la « bête volante » des jeux de chasse japonais |
| **Bébé dragon** | Tête énorme, museau court, grands yeux, ventre rond, ailes minuscules qui ne pourraient pas porter, queue courte et épaisse | Toujours mignon : cornes en boutons arrondis, pas d'épines, griffes absentes ou molles |

Le chinois liste **neuf ressemblances** (andouillers de cerf, tête de chameau, yeux de démon, cou de serpent, ventre de palourde, écailles de carpe, griffes d'aigle, plantes de tigre, oreilles de vache) : utile pour composer une tête orientale originale à partir d'animaux réels plutôt que de copier un dragon d'œuvre.

Anime et jeu japonais : les dragons y **mélangent** les deux traditions (corps occidental, lignes calligraphiées et crinière orientales), privilégient des **lignes fluides**, des motifs d'écailles stylisés et un **visage expressif**. Comme les dragons des RPG japonais : silhouette lisible d'abord, détail ensuite.

## 2. Silhouette et proportions (échelle du dépôt)

- **Ailes de dragon portées** : bras de chauve-souris (humérus court, avant-bras long, 4 doigts très longs, pouce libre griffu au poignet, membrane tendue entre les doigts). Envergure 52–70 px, racine x ≈ ±3, y ≈ 21–23, z ≈ +2,5. Le **premier os à placer est l'humérus**, pas le bord de la membrane. Membrane : bord de fuite en festons concaves entre les doigts.
- **Cornes de dragon** (`head`) : ancrées sur le dessus de la tête, au-dessus des tempes (z ≈ −3 à +2), et elles **partent vers l'arrière** presque dans l'axe du crâne (le démon, lui, les monte). Longueur 6–10 px, base 1,5–2 px. Oriental : andouillers à 2–3 ramifications, plus fins (base 1 px), avec une crinière en plaques découpées derrière.
- **Queue de dragon** : 24–32 px depuis le bas du dos (y ≈ 12, z ≈ +2), section 3 px à la base vers 0,5 px, crête d'épines sur le dessus. Attention à la leçon `queue_abyssale_v1` (plus bas).
- **Familier** : occidental 10–12 px du museau à la croupe (queue en plus), tête 3–4 px ; **bébé** 8–10 px, tête ≈ 45 % de la hauteur (proportions chibi 1:1 à 1:2), ailes de 3–5 px par côté.
- **Serpent oriental** (familier ou aura) : corps de 40–50 px en S, section 1,5–2,5 px, qui ondule autour du joueur ; garder l'extension < 60 px par axe sur toute la boucle.

## 3. Matières et couleurs (HD 32–40 texels/px)

- **Écailles** : rangées en quinconce, chaque écaille = une demi-ellipse avec un liseré clair en haut et une ombre de recouvrement en bas (même logique que les plumes, `modeling.md`). 6–10 texels par écaille au dos, plus petites vers la tête et les pattes. Ventre : **plaques transversales** larges, plus claires, sans quinconce.
- **Membrane** : peinte d'un seul tenant (recette `ailes_abyssales`), plus sombre près des os, plus claire et un peu translucide au bord ; veines contrastées qui partent des doigts. Bord légèrement déchiré seulement pour un dragon menaçant.
- **Cornes, griffes** : dégradé de la base sombre vers une pointe claire, bagues de croissance (stries transversales tous les 6–8 texels).
- **Palettes** : feu (rouge carmin, ventre or, cornes ivoire), glace (blanc bleuté, membrane cyan), orage (bleu nuit, ventre argent, veines jaunes), oriental de jade (vert d'eau, crinière blanche, perle nacrée), noir de nuit (charbon à reflets violets, comme `ailes_abyssales`).

## 4. Mouvement, comportement, attitude

- **Ailes** : biomécanique de chauve-souris (`.claude/rules/categories/ailes.md`) ; repli en éventail des doigts vers le corps ; battement lourd, lent (fly 2,4 s), grande ouverture au freinage (`fall`).
- **Repos (idle 8 s)** : respiration lente et visible (gonflement du thorax), queue qui balaie lentement, un **bâillement** ou un **étirement des ailes** au milieu de la boucle.
- **Menace / attaque (0,8 s)** : cou rentré puis tête projetée, ailes ouvertes d'un coup, gueule ouverte, petite bouffée (fumée, étincelles).
- **Oriental** : tout le corps ondule en **onde progressive** de la tête vers la queue (déphasage régulier par segment, période 3–4 s), la crinière et les moustaches traînent derrière avec retard. Il tourne la tête vers le joueur, enroule sa queue autour de son bras.
- **Bébé** : sautille, bat des ailes trop vite (6–8 battements par seconde, en bump de 0,5 s) sans vraiment voler, éternue une étincelle, se roule en boule pour dormir.
- **Apparition (`event_equip`)** : ailes qui se déplient depuis le dos comme un étirement ; familier qui sort d'un œuf qui se fend (l'œuf se cache ensuite par `ctrl_alpha` ou échelle 0).

## 5. Langage anime

- **Yeux** : pupille fendue verticale, iris lumineux (le regard s'allume avant une attaque).
- **Souffle** : cône de feu ou faisceau, précédé d'une **lueur qui monte dans la gorge** (les écailles du cou s'éclairent par l'intérieur).
- **Dragon oriental** : nuages stylisés en volutes autour du corps, éclairs fins, gouttes de pluie, perle qui brille.
- **Majesté** : contre-jour, ailes ouvertes qui encadrent la silhouette, rafale de vent (poussière au sol).
- **Bébé** : petites étoiles ou cœurs quand il est content, goutte de sueur quand il rate son vol.

## 6. Traduction dans le mod

- **Ailes** : partir de `gen_ailes_abyssales.py` (os octogonaux effilés, membrane peinte puis découpée en plaques portées par le doigt du dessus, panneaux qui glissent sans trou). Ajouter le **pouce griffu** au poignet et une petite griffe au bout de chaque doigt (peau + âme).
- **Lueur de gorge / regard** : calque `_e` (fentes des yeux, veines de la membrane, sillon ventral). Avec shader, `_e` est invisible : donner à la texture elle-même une base claire là où la lueur doit se lire.
- **Souffle ou fumée** : particule modélisée qui **monte** (fumée, braises) depuis un `emit_` à la gueule, avec `ctrl_emit` à −1 puis +4 pendant l'attaque. `emit_mc_` est de nouveau utilisable (`campfire_cosy_smoke`, `flame` à juger en jeu). Pas de feu modélisé en langues à contour sombre (leçon `aura_brasier` : « mec en feu »).
- **Crinière, moustaches, queue d'oriental** : chaînes `phys_` (`phys_criniere_r30_a40`) par-dessus une ondulation animée ; le renderer ne simule pas `phys_` : à juger en jeu.
- **Serpent oriental en aura** : segments imbriqués, rotation continue dans `overlay_<nom>` (360°·k par boucle) pour ne pas sauter entre les états.
- **Perle, nuages stylisés** : `trans_` (visible avec shader) pour la perle nacrée et les volutes ; `add_` en plus seulement pour la lueur sans shader.
- **Familier** : hiérarchie `fam_elan > fam_pos > fam_regard > fam_snap` de `familier_abyssal`, comportements tirés au hasard (`familiers.md`).

## 7. Pièges

- **« Trop dragon, créature »** (`queue_abyssale_v1`) : vertèbres, épines et membrane font bête. Pour un ensemble élégant, une queue de dragon devient un fouet lisse et effilé (`queue_abyssale`) ; garder les épines pour un ensemble qui assume la créature.
- Cornes ancrées sur l'arête du front : base en porte-à-faux devant le visage. Toujours sur le dessus de la tête, contrôler le profil.
- Dragon oriental avec des ailes : il perd ce qui le distingue. Wyverne avec quatre pattes : c'est un dragon.
- Bébé dragon avec griffes, crocs et épines : il cesse d'être mignon.
- Copier un dragon célèbre (couleur + forme de tête + cornes d'un personnage) : interdit ; recomposer à partir des neuf ressemblances.
- Serpent qui fait le tour du joueur : vérifier qu'il ne traverse pas la tête hors de face (leçon `aura_brasier` v2).

## 8. Sources

- [Our Dragons Are Different (AllTheTropes)](https://AllTheTropes.org/wiki/Our_Dragons_Are_Different)
- [Japanese dragon (Wikipedia)](https://en.wikipedia.org/wiki/Japanese_dragon)
- [Chinese dragon, neuf ressemblances (Wikipedia)](https://en.wikipedia.org/wiki/Chinese_dragon)
- [Dragons in Japanese Buddhist art (onmarkproductions)](https://onmarkproductions.com/html/dragon.shtml)
- [Chinese vs Japanese dragon (travelofchina)](https://www.travelofchina.com/chinese-vs-japanese-dragon/)
- [Draw a Dragon Wing (Instructables)](https://www.instructables.com/Draw-a-Dragon-Wing)
- [How to draw wings and winged creatures (Clip Studio)](https://clipstudio.net/how-to-draw/archives/168451)
- [Taking flight, drawing wings (Envato Tuts+)](https://design.tutsplus.com/articles/taking-flight-a-beginners-guide-into-drawing-wings--vector-15996)
- [Our Wyverns Are Different (TV Tropes)](https://www.tvtropes.org/pmwiki/pmwiki.php/Main/OurWyvernsAreDifferent)
- [Wyvern vs Dragon (A-Z Animals)](https://a-z-animals.com/blog/wyvern-vs-dragon-discover-key-differences-between-these-mythical-creatures/)
- [How to draw your dragon (Wacom)](https://community.wacom.com/en-us/how-to-draw-your-dragon/)
- [Baby dragon chibi (how2drawanimals)](https://how2drawanimals.com/8-animals/524-draw-dragon-cartoon?start=3)
- [Divine Dragon in Sekiro, mythologie (Substack)](https://quitetherabbithole.substack.com/p/a-mythological-rabbit-hole-the-divine)
