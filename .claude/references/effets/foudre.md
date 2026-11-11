# Référence — Foudre (vraie foudre, effets d'anime, ailes de foudre)

Fiche documentée (2026-11-08, refonte d'`ailes_orage` : « de vraies ailes en foudre, pas un matériau qui forme les ailes »). Complète la section Foudre d'`elements.md` et les ailes d'énergie d'`ailes-anime.md`.

## La vraie foudre

- **Traceur par bonds** : le chemin se construit par bonds d'environ 50 m (1 µs chacun, ~50 µs entre deux), en ~20–50 ms en tout ; il est faiblement lumineux. Ses ramifications qui n'atteignent pas le sol deviennent les **branches** de l'éclair.
- **Arc en retour** : dès la jonction, le courant remonte le canal (~100 µs) : c'est lui qu'on voit. Les branches s'éclairent avec le canal, plus fines et plus ternes.
- **Scintillement** : 3 à 4 arcs en retour sur le même canal, séparés de **40 à 60 ms** (jusqu'à 26 arcs en 2 s) : l'œil voit l'éclair clignoter. Les traceurs suivants (« dart leaders ») ne se ramifient pas : le canal principal clignote, les branches s'éteignent en premier.
- **Forme** : zigzag à angles vifs, tronçons de longueurs irrégulières ; ramification fractale (motif qui se répète en plus petit), branches dirigées dans le sens de la décharge, toujours plus fines que le canal qui les porte.
- **Couleur** : canal à ~30 000 K, si intense que l'œil sature : **blanc** ; l'azote ionisé émet surtout dans le bleu et l'ultraviolet : halo **bleu-violet**. Jaune, rouge : poussière, distance (à éviter : couleur du Givre et de Bérénice chez nous).

## Codes de l'anime et des effets temps réel

- Dessin à 12 images/s (« sur 2 »), formes tracées vite et au hasard puis épaissies par endroits ; images vides intercalées pour le stroboscope ; l'éclair se dissipe très vite.
- **Fondu non uniforme** : les petites branches disparaissent d'abord, le canal principal tient plus longtemps (forum d'effets temps réel). Hasard maximal : pas de vagues régulières, pas de cadence prévisible.
- Formes contrastées d'une image à l'autre (silhouettes fortes) plutôt que des intermédiaires mous.
- **Ailes d'énergie** : elles n'ont pas besoin de battre comme des ailes de chair, mais une aile de foudre lisible garde un **bord d'attaque** (canal continu) et un **bord de fuite** dessiné par les pointes des ramifications ; l'énergie crépite le long des bords, flambe aux moments forts.

## Traduction dans le mod

- **Trait = géométrie**, jamais 1–2 texels peints : cube allongé (section losange, roulis différent à chaque tronçon pour éviter les faces coplanaires aux jointures), de 1,05 px (canal près du dos) à 0,3 px (fourches).
- **Lisible de jour** : cœur **opaque** blanc à bord bleu + calque `_e` net (lumière jour comme nuit). La gaine `add_` (halo bleu-violet, 2,2 fois le cœur) ne compte que la nuit et sur ciel sombre : sur ciel clair elle délave. **Aucune `trans_`** autour de l'`add_` (elle le cacherait).
- **Scintillement** : `ctrl_alpha` en Molang sur `q.life_time` (+ `q.instance_seed`), tirage par tranche à 4–14 Hz ; deux jeux de petites fourches `add_` par trait, allumés en alternance (jamais la même forme deux fois de suite) ; arc en retour = trois fenêtres de 60 ms séparées de 60 ms, tirées toutes les 1,4–6 s selon l'état ; gerbe `ctrl_emit` au même instant.
- **Apparition** : le traceur dessine le canal depuis le point de départ (échelle en cascade le long de la chaîne d'os), les ramifications partent du canal une à une, puis les arcs en retour flambent.
- Étincelles : particule modélisée ≤ 0,6 px ; `emit_mc_electric_spark` discret. Sons : jamais de tonnerre du jeu (trop fort).

## Ailes de métal forgé où court la foudre (`ailes_orage` v7, 2026-11-08)

Direction choisie par l'utilisateur après la v6 en traits d'éclair (« je n'aime pas du tout ») : vraie aile d'oiseau en plumes de métal sombre, la foudre sur les bords.
- **Type d'aile « rapide »** (faucon, martinet) : longue, étroite, pointue ; la pointe est formée par la 2e et la 3e primaire depuis l'extérieur, la plus extérieure un peu plus courte ; rémiges raides, droites et effilées, très peu d'échancrures (la primaire est déjà étroite). Secondaires courtes et égales : bord de fuite droit. C'est ce qui sépare la silhouette de l'aile ronde et large (Bérénice) et des éventails (givre, steampunk).
- **Acier qui se lit comme une lame** : corps bleu-noir martelé (grain doux, ±5 %), **fil** poli clair sur le bord extérieur (2,5 texels), puis **couleurs de revenu** de l'acier, cuivre puis violet (l'oxyde de trempe passe du bronze au bleu-violet en chauffant), liseré d'or sur le bord intérieur ; bout taillé en biseau, pointe côté bord d'attaque.
- **La foudre a une cause** : le métal conduit, le rachis de chaque rémige est un filet de foudre captive (peint clair + `_e`, lumière de jour) ; le trait d'éclair en géométrie (cœur opaque + `_e`, gaine `add_`) suit la crête du bord d'attaque de l'épaule à la pointe ; une décharge court section par section (0,04 s par os) puis saute de pointe en pointe des primaires (arcs portés par la primaire de départ : elles s'écartent ensemble, l'arc reste en place à 0,3 px près).
- Sources : [Auk, ailes des faucons (primaires, échancrures)](https://sora.unm.edu/sites/default/files/journals/auk/v005n04/p0418-p0421.pdf), [Condor, forme des ailes de rapaces](https://sora.unm.edu/sites/default/files/journals/condor/v029n01/p0017-p0018.pdf), [All About Birds, faucon pèlerin](https://www.allaboutbirds.org/guide/Peregrine_Falcon/id), [Phylogenetics and ecomorphology of emarginate primary feathers](https://umimpact.umt.edu/en/publications/phylogenetics-and-ecomorphology-of-emarginate-primary-feathers/), [couleurs de revenu de l'acier (BladeHQ)](https://www.bladehq.com/blog/coloring-damascus-knives-how-its-done), [bleuissage de l'acier (Microtech)](https://microtechknives.com/blogs/news/microtechs-blueing-process).

## Sources

- [Britannica, Cloud-to-ground lightning](https://britannica.com/science/thunderstorm/Cloud-to-ground-lightning)
- [Luther College, séquence de l'éclair](https://faculty.luther.edu/~bernatzr/Courses/Sci123/Chapter12/lightningSequence.html)
- [NOAA, types d'éclairs](https://noaa.gov/node/10764)
- [UW–Madison, Why is lightning white?](https://wxguys.ssec.wisc.edu/page/78/?cat=-1)
- [Couleur des éclairs (violet, azote)](https://brainbound.blog/purple-lightning-explained-science-spectacle)
- [Clip Studio, effets animés : foudre](https://tips.clip-studio.com/es-es/articles/7688?org=1)
- [Real Time VFX, Elemental effects](https://realtimevfx.com/t/elemental-effects/5094)
- Fiches internes : `elements.md`, `ailes-anime.md`, `.claude/styles/orage.md`
