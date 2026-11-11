# Créatures marines mythiques — sirène, kraken, léviathan

Fiche de référence (2026-11-04). Pièces concernées : queue ou nageoires (`queues`), couronne de corail ou de coquillages (`chapeaux`), familier marin, aura aquatique, tentacules portés (`ailes_tentacule` : modèle de vrai volume à reprendre pour un tentacule). Eau et élémentaires : `elementaires.md`. Serpent marin : voir aussi le dragon oriental (`dragons.md`).

## 1. Codes visuels essentiels

| Être | Ce qui le fait reconnaître | Variantes |
|---|---|---|
| **Sirène** | Haut humain, **queue de poisson** à partir de la taille, écailles, **nageoire caudale** large en éventail, nageoires fines aux hanches ou aux avant-bras, cheveux qui flottent, coquillages et perles | Le *ningyo* japonais ancien était tout autre : un poisson à visage humain, inquiétant ; l'image moderne (belle jeune femme) vient de l'Occident (conte d'Andersen). Mignonne : poisson rouge à visage rond (comme la fillette-poisson de Miyazaki : yeux grands, cheveux rouges, joues rondes). Élégante : voiles de nageoires translucides, nacre |
| **Kraken** | Céphalopode géant (pieuvre ou calmar), **longs tentacules à ventouses**, gros œil, bec ; né des récits de calmars géants | Mignon : petite pieuvre ronde aux yeux immenses. Menaçant : tentacules qui sortent de l'eau, sans corps visible |
| **Léviathan / serpent de mer** | Serpent immense qui ondule, **dos qui émerge par arches** au-dessus de l'eau, nageoires dorsales en crête, gueule de poisson des profondeurs | Bioluminescent : points de lumière le long des flancs. Majestueux : écailles nacrées, nageoires en voiles |
| **Umibōzu** (yōkai) | Silhouette noire géante et lisse qui sort de la mer, tête ronde, yeux clairs | Masse sombre, pas de détails : l'horreur par le vide |

## 2. Silhouette et proportions (échelle du dépôt)

- **Queue de sirène** (`queues`, ou portée à la taille) : la vraie queue remplacerait les jambes, impossible ; en cosmétique, c'est une **nageoire caudale** qui sort du bas du dos (y ≈ 12, z ≈ +2), 14–22 px, ou des **voiles de nageoires** aux hanches (6–10 px) et aux avant-bras (4–6 px).
- **Nageoires** : rayons (arêtes fines) qui partent d'une base et s'écartent en éventail, membrane entre eux ; bord libre en festons.
- **Tentacules** (dos ou épaules) : 18–30 px, section 2,5 px à la base vers 0,5 px, ventouses sur une seule face (l'intérieur de la courbe) ; 2 à 4 tentacules suffisent.
- **Kraken-familier** : 6–9 px, tête ronde ≈ 60 % de la masse, 6–8 petits tentacules de 3–5 px.
- **Couronne marine** (`head`) : corail en branches ou coquillages, 3–6 px, ancrés au-dessus des tempes.
- **Serpent de mer** (aura) : corps de 40–50 px en arches autour du joueur, section 2 px ; extension < 60 px.

## 3. Matières et couleurs (HD 32–40 texels/px)

- **Écailles de poisson** : petites (4–6 texels), en quinconce, **reflet nacré** (irisé rose → vert → bleu) qui court en bande sur le flanc, ventre plus clair (contre-ombrage du poisson : dos foncé, ventre clair).
- **Nageoires** : membrane translucide à rayons plus opaques, teinte plus vive au bord.
- **Peau de céphalopode** : lisse, mouchetée (chromatophores), dégradé de teinte, ventouses en anneaux clairs à centre sombre.
- **Bioluminescence** : presque toujours **bleu-vert** (≈ 470 nm, la lumière qui porte le plus loin sous l'eau) ; points lumineux (photophores) en rangées régulières le long des flancs et des tentacules, sur un corps sombre.
- **Palettes** : lagon (turquoise, corail, sable), abysses (bleu nuit, points cyan), perle (blanc nacré, rose pâle, or).

## 4. Mouvement, comportement, attitude

- **Nageoire caudale** : battement **vertical** (de haut en bas, comme un dauphin) chez la sirène d'anime, **ondulation** gauche-droite chez le poisson ; période 1,2–2 s au repos, plus rapide en `swim`. Les voiles de nageoires traînent derrière avec retard.
- **Cheveux, nageoires** : flottent comme dans l'eau, même hors de l'eau (code de l'être marin).
- **Tentacules** : chacun suit une **onde de la base vers la pointe**, déphasé de ses voisins ; ils s'enroulent (pointe qui se roule) et se déroulent ; à l'attaque, ils se tendent d'un coup puis claquent.
- **Kraken mignon** : flotte en propulsion (corps qui se contracte, tentacules qui se resserrent puis s'écartent, 1–1,5 s), crache une petite bulle d'encre quand il a peur.
- **Serpent de mer** : arches qui avancent en onde lente (4–6 s), tête qui émerge et regarde.
- **Nage** (`swim`) : c'est l'état où ces pièces brillent ; corps couché, ondulation ample.
- **Apparition** : éclaboussure, les nageoires s'ouvrent comme un éventail.

## 5. Langage anime

- **Bulles** qui montent, **reflets de surface** qui dansent (caustiques), cheveux en apesanteur.
- **Vagues stylisées** à la manière des estampes (crêtes en griffes, écume en perles), reprises dans les tempêtes magiques.
- **Points lumineux** des profondeurs dans le noir, pupilles qui brillent.
- **Chant** : notes de musique ou ondes concentriques autour de la sirène.
- **Perles, coquillages** comme bijoux ; collier de perles, diadème de corail.

## 6. Traduction dans le mod

- **Nageoires** : `trans_` (membrane alpha 120–200, rayons à 255), âme fine opaque le long des rayons principaux ; visible avec shader.
- **Queue, tentacules** : segments imbriqués, onde animée (déphasage constant par segment) ; vrai volume par peau ronde découpée autour d'une âme pleine (modèle `ailes_tentacule`) ; `phys_` par-dessus pour l'élan (non simulé, à juger en jeu).
- **Bioluminescence** : photophores en `_e` (petits points nets, 150–225) + couleur claire dans la texture ; avec shader, `_e` est invisible.
- **Caustiques, reflets qui dansent** : `ctrl_uv` qui fait défiler une texture de reflets sur une plaque `add_` (sans shader) ou `trans_` (avec shader).
- **Bulles** : particule modélisée qui **monte** (une face, 0,3 px, cercle peint avec reflet) depuis la couronne, les nageoires ou la bouche ; `emit_mc_bubble` possible (à juger en jeu). Gouttes qui tombent : seulement si la pièce est une aile.
- **Nacre** : dégradé irisé peint (les reflets `_r` sont retirés jusqu'au correctif du mod).
- **États** : soigner `swim` et `glide` (corps couché) ; ailleurs, ondulation calme.
- **Sons** (rares) : `entity.dolphin.splash`, `block.bubble_column.upwards_ambient` au plus, une fois par boucle de 20 s.

## 7. Pièges

- **Tentacules sur une pièce élégante** : ils font vite « créature » (leçon « trop dragon, créature »). Les réserver à un registre qui l'assume, ou les réduire à des rubans lisses sans ventouses.
- Nageoires opaques : elles deviennent des feuilles de plastique.
- Écailles trop grosses : la sirène devient un poisson ; garder des écailles fines et un reflet nacré.
- Tentacules synchrones : mécanique, pas vivant ; déphaser chacun.
- Bioluminescence rouge ou jaune partout : peu crédible (le bleu-vert domine sous l'eau) ; un accent rouge rare peut servir de signal.
- Reprendre une sirène ou un kraken de film identifiable (couleur de queue + cheveux + bijou d'un personnage) : composer à partir des codes.

## 8. Sources

- [Merfolk (Wikipedia)](https://en.wikipedia.org/wiki/Merfolk)
- [Mermaids in Japan, from harbingers to enchantresses (The Conversation)](https://theconversation.com/mermaids-in-japan-from-hideous-harbingers-of-violence-to-beautiful-enchantresses-179251)
- [The bizarre tales of Japanese mermaids, ningyo (Tokyo Weekender)](https://www.tokyoweekender.com/art_and_culture/japanese-culture/the-bizarre-and-violent-tales-of-japanese-mermaids-or-ningyo/)
- [Ningyo took Westerners by storm (Art Critique)](https://www.art-critique.com/en/2020/08/how-the-ningyo-or-mermaid-took-westerners-by-storm-in-the-1800s/)
- [Ponyo (Wikipedia)](https://en.wikipedia.org/wiki/Ponyo)
- [Art of Ponyo (Character Design References)](https://characterdesignreferences.com/art-of-animation-1/art-of-ponyo)
- [Giant Squid (TV Tropes)](https://TVTropes.org/pmwiki/pmwiki.php/Main/GiantSquid)
- [From mythos to monsters: the kraken (EN World)](https://www.enworld.org/threads/from-mythos-to-monsters-the-kraken.720398/)
- [Colour in the deep sea (Gakuran)](https://gakuran.com/colour-in-the-deep-sea/)
- [Why most deep-sea creatures glow blue (Strange Animals)](https://strangeanimals.info/marine-life/deep-sea/bioluminescence-how-deep-sea-creatures-create-their-own-light)
- [How to draw water: reflections, ripples, waves (Skyrye Design)](https://skyryedesign.com/art/drawing/how-to-draw-water/)
