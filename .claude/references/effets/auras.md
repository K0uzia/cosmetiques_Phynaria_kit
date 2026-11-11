# Référence — Auras façon anime

Fiche documentée (2026-11-04). À lire avec `principes-fx-anime.md` (couleurs en couches, timing) et `elements.md` (palettes). Les pièces du dépôt `aura_brasier` (v3), `aura_berenice` et `aura_givre` sont les recettes de référence ; leurs docstrings détaillent la construction.

## Codes visuels

- **Une aura, c'est de la lumière autour d'une silhouette, pas un objet** (retours en jeu : objets en orbite « pas une aura », langues de feu « mec en feu »). L'anime la dessine comme une enveloppe qui épouse la pose ; la zone au contact du corps est la plus propre et la plus claire, ce qui suffit à faire « briller » sans dessiner de halo.
- **Elle a une direction** : elle monte (chaleur, puissance), rayonne (sacré), rampe et retombe (froid, malédiction). Cheveux et vêtements se soulèvent dans le même sens.
- **Elle dit le niveau de puissance** : dans les séries de combat, l'aura grossit par paliers jusqu'à colorer le décor. Une aura de cosmétique reste au palier « calme » au repos et ne s'embrase qu'à l'attaque.
- **Code couleur** (tropes « Battle Aura », « Color-Coded Elements ») : or ou bleu = héroïque, sacré ; rouge = colère, violence ; noir, violet sombre = maudit, corrompu ; vert = poison, radiation, nature ; blanc = pureté, limite ultime.

## Types d'aura

| Type | Forme | Couleur (cœur → teinte → bord) | Mouvement |
|---|---|---|---|
| Flamme d'énergie (combat) | langues étroites qui montent en crochets, plus hautes au-dessus de la tête et des épaules | blanc teinté → teinte vive → teinte profonde | rapide (cadence « sur 2 », 8–12 images/s), traînées qui montent en 0,3–0,6 s |
| Aura qui monte (calme, concentration) | colonnes douces derrière le corps, filets verticaux | cœur clair, teinte pâle | lente, 4–8 s de respiration, filets qui montent en 1–2 s |
| Divine, lumière | rayons fins depuis un point derrière la nuque (gloire), halo, poussière d'étoiles qui monte | blanc chaud → or clair → or doux (s'arrêter à l'or clair) | très lente : rotation d'un tour en 30–60 s, pulsation 8 s |
| Sombre, maudite | volutes et filaments irréguliers qui rampent, cassures, fumée qui tombe ou stagne | fond sombre, **un seul** accent (violet, rouge sang, cyan électrique) sur les bords et les fissures | irrégulière (Molang sur `q.life_time`), saccades, fumée lente |
| Élémentaire | l'aura prend la forme de l'élément : cristaux au sol, brume, étincelles, feuilles | palette de `elements.md` | selon l'élément |
| Explosive (éveil) | onde de choc au sol, colonne verticale, éclats | flash presque blanc puis teinte | 0,1 s de flash, 0,3 s d'expansion, 1 s de retombée |
| Éclairs dans l'aura | petites décharges anguleuses qui courent sur l'enveloppe | blanc bleuté ou de la couleur de l'aura | 2 à 3 images (0,1–0,15 s) toutes les 1–3 s, au hasard |

**Calme contre explosive** : la calme est symétrique, lente, peu contrastée, collée au corps ; l'explosive est asymétrique, rapide, contrastée, avec des morceaux détachés et une onde au sol. Un cosmétique porté en permanence doit être calme au repos (on le voit des heures).

## Mouvement et timing (états du mod)

| État | Intention |
|---|---|
| `idle` | respiration 4 à 8 s, filets qui montent lentement |
| `walk`, `run` | l'énergie part vers l'arrière, plus haute et plus vive en course |
| `sneak` | contenue : plus basse, plus serrée, plus faible |
| `fly`, `fall` | étirée vers le haut ou l'arrière |
| `glide`, `swim` | corps couché : colonnes `camy_` rentrées, il reste le halo et la traîne de particules |
| `sleep` | presque éteinte |
| `attack` (`once`, 0,8 s) | flash 0,05–0,1 s, embrasement 0,3 s, retour en 0,4 s |
| `hurt` (`once`, 0,8 s) | vacille et baisse, tremblement amorti |
| `event_equip` | s'allume des pieds vers la tête en 2–2,5 s |

## Traduction dans le mod (recette qui marche)

Recette validée en jeu sans shader (`aura_brasier` v3, « une fois équipée, ok ») :
1. **Halo de silhouette** : un disque `add_` par partie du corps (1 tête, 3 torse, 3 par bras, 3 par jambe), chacun dans un groupe `cam_` **reculé de 3 à 4 px derrière le centre** de sa partie, **vide au centre**. Le corps cache le reste : rien ne passe devant le visage, sous tous les angles et dans toutes les poses.
2. **Énergie qui monte** : colonnes douces `add_` dans un seul groupe `camy_` centré sur le torse, placées **derrière le pivot** (z local < 0) ; film de 8 images côte à côte parcouru par `ctrl_uv` en pas entiers ; échelle en Molang pour le vacillement.
3. **Sol** : anneau `add_` (une plaque de 0,15 px découpée par alpha) qui tourne dans un `overlay_` ; masqué quand le corps n'est pas debout.
4. **Morceaux détachés** : `particle_etincelle` (un cube de 0,3 px, une face), réglage *Monte*, et éventuellement `emit_mc_dust_<couleur>_<taille>`.
5. **Menu Apparence** (mod 1.4.0) : l'additif y est correct ; pas de caméra, les `cam_`/`camy_` sont dessinés tels quels. `tools/menu_aura.py` les tourne, dans le menu seulement, vers la caméra par défaut du menu (lacet 30°, 5° au-dessus) : l'enveloppe entoure la silhouette comme en jeu tant qu'on ne fait pas tourner le personnage (ne plus les cacher).

Compléments :
- **Gloire divine** (`aura_berenice`) : deux plaques de rayons fins dans un `cam_` derrière la nuque (recul 7 px), qui tournent en sens contraire (un tour en 48 s) ; doublée d'une gloire `trans_` très discrète (alpha 20–95).
- **Aura élémentaire** (`aura_givre` v2, 2026-11-08) : la v1 portée au sol seul (cristaux, givre) était illisible. La v2 traduit un phénomène réel du froid : les **piliers de lumière** (cristaux de glace hexagonaux plats en suspension qui reflètent la lumière en colonnes verticales) et la **poussière de diamant** (ces cristaux près du sol, qui scintillent) → piliers fins `add_` à paillettes qui montent ; le **halo** et les **parhélies** (cercle autour de la source et deux taches vives à gauche et à droite) → cercle à deux points vifs derrière la nuque, autour d'une rosace hexagonale. Le sol (hexagone de givre, grappes `trans_`) n'est plus qu'un socle.
- **Aura démoniaque en lumière** (`aura_abyssale` v3, 2026-11-08) : la v2 en volutes `trans_` sombres se lisait grise de jour. Faire la forme en lumière violette (disques) avec un seul accent vif en traits fins (crocs recourbés derrière la nuque, veines ramifiées qui montent, sceau au sol) : l'ombre n'est que dans la palette, pas dans la matière. Cercles et glyphes qui tournent en sens contraire : code récurrent des effets de magie (source ci-dessous).
- **Aura mignonne** (`aura_kawaii` v3, 2026-11-08) : codes de la magie « mignonne » (cœurs, étincelles kira à quatre branches, rondeurs) ; un seul motif fort derrière la tête, un cœur de sucre `trans_` en couleur franche, avec une lumière `add_` douce devant lui (le `trans_` subit l'ombre du monde) et un liseré `add_` derrière (caché par le sucre, il ne se voit qu'autour). Le reste en lumière, petits cœurs au sol plutôt qu'en orbite.
- **Aura sombre** : impossible en `add_` (le noir y est invisible). Faire les volutes en `trans_` sombre (alpha 80–180) avec l'accent coloré en `add_` sur le bord, ou une texture opaque découpée très sombre avec des fissures lumineuses au calque `_e`. À essayer : jamais encore livrée.
- **Éclairs dans l'aura** : petites plaques `add_` en `cam_` à échelle 0 le reste du temps, montrées 0,1 s en *step* dans un `overlay_`, déphasées avec `q.instance_seed`. `emit_mc_electric_spark` en appoint.
- **Embrasement à l'attaque** : `ctrl_alpha` et échelle du halo, jamais de nouvelles pièces devant le corps.

## Feu de Saint-Elme (aura électrique, 2026-11-08)

Phénomène réel qui sert d'analogie à une aura d'orage calme : dans le champ électrique d'un orage, le champ se concentre sur les pointes (mâts, clochers, cornes, bouts d'ailes d'avion) et y allume une **décharge couronne continue** (décharge luminescente, pas un éclair) : lueur bleue ou violette (azote et oxygène de l'air), parfois verdâtre, en **pinceaux** de filaments, avec un grésillement ou un sifflement. Traduction dans le mod (`aura_orage` v2) : une lumière **continue qui grésille** (film `ctrl_uv` de 4 images tirées au hasard, pas de rotation, accrochée aux pointes : couronne derrière la nuque) + de **vrais éclairs brefs** au hasard aux pointes du corps (épaules, mains, pieds). Ce n'est pas un néon : la forme change sans cesse et l'intensité reste modérée ; le blanc pur est réservé aux éclairs brefs.

Cumul : un double `trans_` clair sous un anneau `add_` s'additionne au fond et sature (mesuré ~400 en bleu) ; le double `trans_` sous un additif doit être sombre et léger (alpha 30–100). Pas de filet `camy_` derrière la tête quand une couronne `add_` y est déjà.

Sources : [Wikipedia : St. Elmo's fire](https://en.wikipedia.org/wiki/St._Elmo%27s_fire), [Britannica : Saint Elmo's fire](https://www.britannica.com/science/Saint-Elmos-fire), [SKYbrary : St Elmo's Fire](https://skybrary.aero/index.php/St_Elmo%27s_Fire), [80.lv : électrocution en VFX (faisceaux qui tremblent sur un personnage)](https://80.lv/articles/learn-how-to-create-electrocuting-lightning-vfx-with-ue5-s-niagara/).

## Avec shader

`add_` et `_e` sont invisibles avec shader (bug du mod, correctif Iris non appliqué au 2026-11-04) : une aura tout en `add_` disparaît. **Doubler la forme principale en `trans_`** (gloire, anneau, brume, cristaux), discrète pour ne pas alourdir le rendu sans shader.

## Pièges (constatés chez nous)

- Langues de feu à contour sombre : « mec en feu », même en dégradé. Une aura est de la lumière.
- Objets en orbite (plumes, cœurs, orbes) : « pas une aura ».
- Plaques croisées fixes dans les membres : barre blanche devant le visage hors de face (« horriblement moche »).
- **Cumul additif** : disques + gloire + `_e` renforcé ont cumulé ~980 en rouge, disque blanc opaque autour de la tête. Pièce tout en `add_` : **pas de calque `_e`**, cumul mesuré sans plafond ≤ 255 partout, palette arrêtée à l'or clair (pas de blanc pur sur les anneaux et rayons).
- **`end_rod`** : grosse étoile blanche de taille fixe qui dérive à 2–3 blocs, boule lumineuse avec shader. Étoile modélisée ≤ 0,6 px, Élan 100 %.
- Étoile modélisée de 1,4 px vue à 3 blocs avec Élan 0 : trop grosse, détachée du joueur.
- Un dégradé dans `_e` seul ne se voit pas de jour : le mettre aussi dans la texture.
- Particules qui tombent et se posent : ailes seulement. Sur une aura, ce qui se détache monte ou se dissipe (la brume froide peut retomber lentement puis disparaître).
- Sons : un au plus à l'apparition (`block.amethyst_block.chime`), aucun en mouvement (`tools/sons.py`).

## Sources

- [Wikipédia (en) : Light pillar](https://en.wikipedia.org/wiki/Light_pillar) : plaques hexagonales horizontales, poussière de diamant, colonne verticale
- [WorldAtlas : What is a light pillar?](https://worldatlas.com/articles/what-is-a-light-pillar.html)
- [80.lv : effets de glace et de givre (cristaux, brume, cœur lumineux)](https://cdn.80.lv/articles/check-out-these-chilling-ice-frost-vfx-unveiled-by-3d-artist)

- [TV Tropes : Battle Aura](https://tvtropes.org/pmwiki/pmwiki.php/Main/BattleAura) et [Tropedia : Battle Aura](https://tropedia.fandom.com/wiki/Battle_Aura)
- [TV Tropes : Power Glow](https://tvtropes.org/pmwiki/pmwiki.php/Main/PowerGlow)
- [Anime Aura VFX Manual (nkdtr) : l'aura épouse la pose, carte de densité](https://nkdtr.hatenablog.com/entry/2022/12/21/192834)
- [Unreal Engine forum : Anime Style Auras](https://forums.unrealengine.com/t/anime-style-auras/2679755)
- [AEJuice : aura de type « super guerrier » (couches, montée)](https://aejuice.com/blog/how-to-make-a-super-saiyan-aura-in-after-effects/)
- [Animer un orbe d'énergie : formation, pulsation, libération](https://wxndiipng.blogspot.com/2025/03/how-to-animate-magical-energy-orb-step.html)
- [Clip Studio Tips : effets d'aura](https://tips.clip-studio.com/en-us/articles/1897)
- [TV Tropes : Color-Coded Elements](https://tvtropes.org/pmwiki/pmwiki.php/Main/ColorCodedElements)
- Recettes internes : `cosmetiques/auras/aura_brasier/gen_aura_brasier.py`, `cosmetiques/auras/aura_berenice/gen_aura_berenice.py`, `cosmetiques/auras/aura_givre/gen_aura_givre.py`
- [Real Time VFX : « Cute Magic » (cœurs, étincelles kira, sprites d'effets mignons)](https://realtimevfx.com/t/vulpes-vulpes-sketch-23-cute-magic/8967)
- [Fab : pack d'effets de magie, cercles et anneaux qui tournent en sens contraire](https://fab.com/s/bfe4efbba664)
