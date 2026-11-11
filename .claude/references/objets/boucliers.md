# Boucliers (rondache, umbo, sangles) — référence pour les skins de bouclier

Recherche du 2026-11-08 pour `skin_bouclier_cuir` (ensemble Cuir). Un autre agent fait un bouclier de givre le même jour : compléter ce fichier plutôt que d'en créer un second.

## Le vrai objet

| Partie | Ce que c'est | Ce qui la fait lire |
|---|---|---|
| Rondache (rouelle aux XIIe–XIIIe s.) | Bouclier rond et léger, porté au poing ou à l'avant-bras, pour aller au contact : parer et frapper | Disque, de 30 cm (fer ou cuir bouilli, XIIIe s.) à 45–60 cm (répliques et pièces de musée : 45,5 et 48 cm) |
| Umbo | Bosse de métal bombée au centre, rivetée sur une collerette ; creuse, la main tient la poignée derrière elle (assez profonde pour une main gantée) ; elle dévie les coups du centre | Dôme brillant au centre, collerette rivetée |
| Peau, âme | Planches ou lattes collées, couvertes de cuir ou de toile ; parfois du cuir bouilli seul | Surface tendue, légèrement bombée |
| Bordure | Jonc de cuir cru ou de métal sur la tranche, cloué ou riveté : il tient la peau et encaisse les coups de taille | Cercle clair qui ferme la silhouette |
| Enarmes | Au dos : poignée (sous l'umbo) et sangle d'avant-bras rivetées, longueur prévue pour le gant et le gambison | Barre et sangles au dos, avec boucles |
| Guige | Longue sangle qui passe autour du cou ou de l'épaule : porter le bouclier en marche, le soutenir au combat | Sangle qui traverse le dos, anneaux |

## Le bouclier de Minecraft (jar 26.1.2, mesuré)

- Modèle d'entité (`ShieldModel`) : plaque 12 × 22 × 1, poignée 2 × 6 × 6 ; dessiné **autour du coin 0 du bloc** (après le recentrage −0,5 puis `scale (1, −1, −1)` de `items/shield.json`) : dans le repère du bloc, plaque x −6..6, y −11..11, z 1..2, **face peinte vers +Z**, poignée x −1..1, y −3..3, z −5..1. D'où les grandes translations de `item/shield.json` (10 ; 6 ; −4…).
- En 1re personne, on voit le **dos** du bouclier (rotation Y 180° du Display) : la poignée, les sangles du dos et la bordure ; la face se voit en 3e personne, dans l'inventaire et au sol.
- Blocage : Minecraft passe à `item/shield_blocking.json` (3e personne : basculé de 45°, tourné de 65° vers l'avant ; 1re personne : roulis de 10° et décalé de 2,8 px vers le centre, monté de 2,4). Le mod n'a qu'un jeu de réglages Display par skin : recréer ce passage dans l'étape `bloque` (voir `categories/objets.md`, recette du bouclier).

## Traduction dans le style du dépôt

- Le cuir (ou la peau) tendu sur une armature à rayons se lit comme une ombrelle : pans **plans** d'un rayon à l'autre, cône très plat (≈ 10°), reflet peint en coordonnées du bouclier (le même arc traverse tous les pans).
- Umbo : gradins **ronds** (paroi en segments + dessus en disque découpé). Des carrés tournés empilés donnent une étoile à pointes (leur union, pas leur intersection) : à éviter, surtout dans un set qui ne doit pas lire « clous pointus ».
- Diamètre ≈ 18 px pour la même surface que la vanilla (12 × 22) : une vraie rondache (≈ 9 px à l'échelle du joueur) paraîtrait minuscule à côté des boucliers vanilla.

## Sources

- Faits d'Armes, targe synthétique de 48 cm, umbos d'acier : https://faitsdarmes.com/en/synthetic-targes/253-synthetic-soldiers-targe.html, https://faitsdarmes.com/en/bosses/571-steel-umbo-m.html
- Louvre, rondache (45,5 cm) : https://collections.louvre.fr/en/ark:/53355/cl010327094
- Umbos (dôme, rivets, profondeur pour la main gantée) : https://www.darkknightarmoury.com/product/medieval-steel-shield-umbo/
- Inrap, umbo de bouclier (fouilles) : https://galeriemuseale.inrap.fr/index.php/Detail/objects/152631?lang=en_US
- Rondache, enarmes et guige : https://tirsportifchabris.fr/blog/arme-ancienne-bouclier-vente
- Minecraft : `assets/minecraft/items/shield.json`, `models/item/shield.json`, `models/item/shield_blocking.json` (jar 26.1.2), `cosmetiques/objets/skin_bouclier_cuir/.build/vanille.py`.

## L'écu (heater shield) et la glace — ajouté pour `skin_bouclier_givre` (2026-11-08)

| Partie | Ce que c'est | Ce qui la fait lire |
|---|---|---|
| Écu (« heater », XIIIe s.) | Bord haut droit, flancs droits puis deux arcs qui se rejoignent en pointe ; bois mince couvert de cuir, **corps bombé** (courbe horizontale) | Silhouette en fer à repasser, pointe en bas |
| Umbo sur l'écu | Sur les boucliers à poignée centrale, il protège le poing ; quand les enarmes ont remplacé la poignée, il est devenu surtout décoratif | Bosse au centre : point focal |
| Orle | Bord renforcé de métal ou de cuir cru cousu, contre les coups de hache et de masse qui fendent le bois | Liseré clair continu |
| Dos | Traverses en travers du fil du bois, qui portent la poignée ; enarmes et guige | Barres horizontales, poignée |

Glace réelle (pour la peinture) : la glace claire n'a pas de bulles (gelée d'un côté vers l'autre) ; la glace blanche est pleine de bulles qui diffusent la lumière. Le givre (gelée blanche) pousse sur les arêtes et les aspérités en aiguilles et en plumes de petits prismes hexagonaux qui partent les uns des autres en biais : c'est pourquoi le givre se peint en dentelle sur les bords, pas en aplat.

Traduction (`skin_bouclier_givre`) : écu bombé en trois pales (flancs repliés de 15° autour de l'arête avant, sinon les couches s'écartent à l'arête), glace `trans_` devant une âme bleu nuit, taille en étoile autour d'un umbo hexagonal, givre en plumes le long de l'orle, crête de cristaux en haut (lisible à 16 px). Fissures cachées dans l'épaisseur de l'âme, sorties par `position` le long de la normale de la pale (jamais d'échelle 0, qui resterait cachée en superposition).

Sources :
- Écu, enarmes, guige, construction : https://en.wikipedia.org/wiki/Heater_shield
- Umbo (protège le poing, devient décoratif sur l'écu) : https://en.wikipedia.org/wiki/Shield_boss ; boucliers ronds à poignée centrale, bord en cuir cru : https://wiki.vikingsonline.org.uk/Round_shield
- Givre en plumes et aiguilles : https://glossary.ametsoc.org/wiki/Ice_feathers , https://glossary.ametsoc.org/wiki/Crystalline_frost , https://atoptics.co.uk/blog/hoar-frost-crystals-opod/
- Glace claire et glace blanche (bulles) : https://www.scienceabc.com/eyeopeners/why-are-some-ice-cubes-cloudy-while-others-are-clear.html

## L'écaille cornue — ajouté pour `skin_bouclier_abyssal` (2026-11-09)

| Partie | Réel | Traduction |
|---|---|---|
| Écaille, ostéoderme | Plaques osseuses dans la peau (crocodiliens, tatous, ankylosaures) : surface marquée de sillons vasculaires et de stries de croissance concentriques | Écu d'os charbon, stries peintes en anneaux autour de l'umbo, sillons = gouttières creusées où court le vert |
| Carène | Un écu bombé dévie les coups vers les bords ; une arête médiane le raidit | Deux demi-plaques tournées de 12° autour d'une quille octogonale |
| Umbo à pointe | Certains umbos se terminent par une pointe (boss à épine) qui sert aussi à frapper | Collet d'os + griffe conique à pointe verte, qui sort à `event_select` |

Sources :
- Ostéodermes (structure, sillons vasculaires, croissance) : https://en.wikipedia.org/wiki/Osteoderm
- Umbo, variantes à pointe : https://en.wikipedia.org/wiki/Shield_boss

## La porte de chaudière et la roue dentée — ajouté pour `skin_bouclier_steampunk` (2026-11-10)

Analogie : la porte ronde d'une boîte à fumée de locomotive (tôle bombée, rivetée, cerclée) sertie dans un engrenage ; une rondache ronde se lit mieux que l'écu pour un engrenage.

Recettes réutilisables :
- **Pièce à symétrie de rotation en plaque biseautée** (roue dentée, couronne crénelée) : construire **un secteur** (ici 30°, deux dents) comme une `Plaque` fermée (contour = profil des dents, arc intérieur caché sous le dôme et le dos, coupes radiales prolongées de 0,06 px), puis le poser N fois par la matrice `XF` : les tuiles sont partagées (`SPEC_CACHE` par nom), les cubes reçoivent un suffixe de secteur (`NSUF`). Atlas : 38 000 texels pour tout le bouclier.
- **Joints une arête sur deux** sur un tour à pans nombreux : deux tuiles alternées par parité du pan (option `alt` de `tour()`), joint et demi-rivet d'un seul côté ; 24 joints rayonnants se lisent comme une ombrelle.
- Plats de la roue masqués sous le cerclage (r ≥ 7,15) et sous le bord du dos (r ≥ 7,35) ; dos et cerclage démarrent par une petite paroi cylindrique enfoncée dans la roue (pas de faces presque coplanaires).
- Placer le jet de vapeur dans le clapet de la soupape avec F_GEO/KJ = 1/15 (caché au repos, échelle maximale 15 ≤ 16).

Sources : boîte à fumée et porte (tôle bombée, rivets, verrou central) : https://en.wikipedia.org/wiki/Smokebox ; soupape de sûreté : https://www.steamlocomotive.com/appliances/safetyvalve.php
