# Esprits et fées — fée, feu follet, esprit élémentaire, kitsune

Fiche de référence (2026-11-04). Pièces concernées : ailes de fée, familiers-esprits, auras, oreilles et queues de renard. Pour tout familier, lire aussi `.claude/styles/familiers.md` (comportements au hasard, lien avec le joueur).

## 1. Codes visuels essentiels

| Être | Ce qui le fait reconnaître | Variantes |
|---|---|---|
| **Fée** | Ailes d'**insecte** translucides à nervures (libellule, papillon), deux paires, poussière lumineuse qui flotte autour | Élégante : ailes longues de libellule, teintes irisées. Mignonne : ailes rondes de papillon (`ailes_kawaii_papillon`). Sombre : ailes de phalène, teintes de nuit |
| **Feu follet** (*onibi*, *hitodama*) | Boule de flamme **bleue ou bleu-blanc**, petite, qui flotte ; l'*onibi* vient en groupes de 20 à 30, près de l'eau ; le *hitodama* (âme) a une **longue queue de lumière** et rampe bas | Version mignonne : flamme en goutte avec deux yeux. Version inquiétante : flammes sans visage qui tournent lentement |
| **Esprit élémentaire** | Petit être fait de sa matière (goutte, flamme, feuille, cristal, souffle), contour simple, cœur lumineux ; les quatre de Paracelse (salamandre, ondine, sylphe, gnome) sont repris par l'anime | Voir `elementaires.md` pour les grands élémentaires |
| **Esprit de la forêt** | Silhouette **ultra simple** (corps blanc, tête ronde, trois points pour le visage), qui apparaît en nombre, tête qui pivote avec un cliquetis | L'anime a montré qu'on gagne en dépouillant : les premiers croquis détaillés ont été simplifiés jusqu'au minimum |
| **Esprit lumineux, « mushi »** | Organisme presque microscopique (plancton, cellule, larve) qui luit doucement, flux de lumière verte qui coule | Effets retenus, ambiance plutôt que spectacle |
| **Kitsune** | Renard **blanc** (messager d'Inari, blanc = monde des esprits), **plusieurs queues** (une par siècle, neuf au plus), **feu de renard** (*kitsunebi*) en orbes bleus, rouges ou orangés ; attributs : **joyau** qui exauce, clé, masque blanc à liserés vermillon, cordon rouge, torii vermillon | Élégante : queues en éventail, flammes bleues. Mignonne : grosse queue unique, oreilles immenses. Rusée : sourire en coin, yeux plissés |

## 2. Silhouette et proportions (échelle du dépôt)

- **Ailes de fée** : plus petites que des ailes d'oiseau : 30–44 px d'envergure suffisent (elles ne portent pas un corps lourd), deux paires, la supérieure plus grande. Racine haute dans le dos (y ≈ 21–23, x ≈ ±1,5–2,5, z ≈ +2,2), presque collées l'une à l'autre au centre. **Pas d'articulation** : elles ne se plient pas, elles pivotent depuis la racine.
- **Feu follet** (familier ou particule) : 2–4 px, queue de lumière de 3–6 px pour un *hitodama*.
- **Esprit-familier** : 6–9 px, tête ronde ≈ 50–60 % du volume.
- **Kitsune, oreilles** (`head`) : triangles de 3–4 px de haut, base 2,5 px, intérieur clair ; ancrées sur le dessus de la tête comme les cornes (z ≈ −2 à +1). **Queues** : 14–20 px chacune, larges (3–4 px au milieu), en éventail de 3 à 9 depuis le bas du dos (y ≈ 12, z ≈ +2). Au-delà de 5 queues, réduire chacune pour rester sous le budget de cubes et l'extension.
- **Kitsune-familier** : renard compact, pattes courtes, museau court, oreilles plus grandes que nature (registre mignon), queue aussi grosse que le corps (proportions du renard polaire, `familiers.md`).

## 3. Matières et couleurs (HD 32–40 texels/px)

- **Aile de fée** : membrane presque transparente, **nervures** foncées fines (3 texels) qui partent de la racine et se ramifient, reflet **irisé** (rose → cyan → or) qui glisse en diagonale, bord plus opaque. Des taches de couleur aux bouts pour la mignonne.
- **Feu follet** : cœur **blanc**, puis bleu clair, puis bleu profond au bord ; pas de contour sombre (sinon « feu »).
- **Fourrure de kitsune** : blanc chaud ou crème, pointes des queues et des oreilles teintées (or, vermillon, bleu nuit) ; mèches peintes en flammèches qui suivent la courbe ; ombre de recouvrement entre les queues. Marques rouges stylisées sur le front ou les joues (motif original).
- **Esprit de forêt** : blanc cassé lisse, visage en trous noirs, aucune texture.

## 4. Mouvement, comportement, attitude

- **Fée** : battement **très rapide** (insecte : boucle de 0,2–0,3 s, faible amplitude, 15–25°), les deux paires en opposition de phase ; au repos, ailes **dressées et jointes** dans le dos, avec un frémissement de temps en temps. Elle ne vole pas comme un oiseau : elle flotte et dérive.
- **Feu follet** : flotte en **8** lent (3–5 s), monte et descend, se rapproche quand le joueur est immobile ; s'agite et se scinde quand il court. Groupe : chacun déphasé (`q.instance_seed` ou phases différentes).
- **Esprit de forêt** : immobile longtemps, puis **pivot brusque de la tête** (0,1 s) avec un temps d'arrêt ; il regarde le joueur, puis ailleurs.
- **Kitsune** : queues qui ondulent l'une après l'autre (onde décalée), s'ouvrent en éventail à l'attaque ou à l'émotion, se replient autour du corps au repos ; oreilles qui pivotent vers les sons, se couchent quand il est inquiet ; play bow, bond « mousing » (`familiers.md`).
- **Apparition** : la fée sort d'un petit éclat de poussière ; la kitsune s'allume par ses flammes, puis les queues s'ouvrent une à une.

## 5. Langage anime

- **Poussière de fée** : petits points lumineux qui **flottent** et scintillent, traînée de paillettes derrière un mouvement.
- **Kitsunebi** : orbes de flamme bleu et blanc qui **tournent** autour, ou qui s'allument un par un en ligne (comme une rangée de lanternes) ; queues faites de brume blanche à étincelles rouges dans les transformations.
- **Esprits** : lueur douce, contours flous, apparition par fondu, cliquetis ou carillon.
- **Masque de renard** porté sur le côté de la tête (accessoire de fête), clochette, cordon tressé rouge.

## 6. Traduction dans le mod

- **Ailes de fée** : la cible idéale de **`trans_`** (visible avec shader) : membrane alpha 90–170, nervures opaques (alpha 255) peintes dans la même texture ; âme fine opaque le long de la nervure principale pour le volume. Battement dans les états ; frémissement en `overlay_` si on veut qu'il ne saute pas.
- **Irisation** : `ctrl_uv` qui fait glisser lentement un dégradé sur la membrane (non simulé, à juger en jeu), ou deux variantes de teinte peintes sur l'aile avant et l'aile arrière.
- **Feu follet** : disque `add_` en `cam_` (sphère lumineuse) + noyau `trans_` blanc pour le shader ; queue du *hitodama* en plaque `camy_` étirée. Bleu et blanc, jamais de contour sombre (leçon `aura_brasier`).
- **Poussière** : particule modélisée de 0,3 px, face `up` seule, qui **monte** ou flotte (pas qui tombe, sauf depuis des ailes). `emit_` aux bouts des ailes et au centre du dos, `ctrl_emit` plus fort pendant le vol.
- **Queues de kitsune** : chaque queue est une chaîne de segments imbriqués, ondulation animée décalée d'une queue à l'autre, `phys_queue_N_r30_a40` par-dessus (non simulé, à juger en jeu). Volume : peau ronde découpée par alpha (touffe) autour d'une âme pleine, comme `queue_kawaii`.
- **Familier-esprit** : recette `familier_kawaii_mochi` (bosses arrondies, squash-and-stretch) ou `familier_kawaii_chat` (lanterne qui luit) ; regard qui suit `q.head_y_rotation` avec retard.

## 7. Pièges

- Ailes de fée articulées comme des ailes d'oiseau : elles se lisent comme une erreur. Elles pivotent, frémissent, ne se plient pas.
- Ailes de fée trop grandes (> 50 px) : on dirait un papillon géant porté, plus une fée.
- Feu follet à contour sombre ou orangé : il devient une torche.
- Trop de queues détaillées : budget de cubes et extension ; 3 à 5 queues bien faites valent mieux que 9 maigres.
- Particules qui tombent depuis la tête, les queues ou un familier : interdit sans demande explicite.
- Esprit de forêt qui copie un esprit de film reconnaissable (corps blanc + tête à trois trous + cliquetis) : s'en tenir au principe (dépouillement), changer la forme.
- Masque de renard d'un personnage précis : dessiner un motif original.

## 8. Sources

- [Onibi (Wikipedia)](https://en.wikipedia.org/wiki/Onibi)
- [Hitodama (yokai.jp)](https://yokai.jp/en/yokai/hitodama)
- [Ghost Lights (Tropedia)](https://tropedia.fandom.com/wiki/Ghost_Lights)
- [All about yokai onibi (Substack)](https://odessasilver.substack.com/p/all-about-yokai-onibi)
- [Inari fox (The Japan Box)](https://thejapanbox.com/blogs/japanese-mythology/inari-fox)
- [Foxes of Inari (Traditional Kyoto)](https://traditionalkyoto.com/culture/figures/inari-foxes/)
- [What is a kitsune (A-Z Animals)](https://a-z-animals.com/blog/what-is-a-kitsune-animals-it-is-made-of-and-cultural-meaning)
- [Kodama, esprits de la forêt simplifiés (Den of Geek, personnages Ghibli)](https://www.denofgeek.com/?p=130448)
- [The real yokai hidden in Ghibli films (Wallango)](https://wallango.com/blogs/news/the-real-yokai-hidden-in-studio-ghibli-films)
- [Mushishi, esprits lumineux (Threadless)](https://blog.threadless.com/mushishi-is-your-next-binge-worthy-anime/)
- [Elemental, Paracelse (Wikipedia)](https://en.wikipedia.org/wiki/Elemental)
- [Fairy effect, ailes translucides et poussière (Morphic)](https://morphic.com/resources/vfx/fairy-effect)
- [Painting a fantasy manga female, ailes translucides (Creative Bloq)](https://www.creativebloq.com/digital-art/how-paint-fantasy-manga-female-101517378/2)
