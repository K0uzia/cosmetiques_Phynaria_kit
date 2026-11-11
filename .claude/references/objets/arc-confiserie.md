# Arc de confiserie (arc, guimauve, codes de l'arc magique « mignon ») — référence pour les skins d'arc

Recherche du 2026-11-08 pour `skin_arc_kawaii` (ensemble Kawaii). Sujet réel : l'arc (à poulies exclues) et les confiseries qui en donnent la matière. Toute autre pièce de tir « bonbon » peut partir de cette fiche.

## Anatomie de l'arc (ce qui doit rester lisible)

| Partie | Ce que c'est | Ce qui la fait lire |
|---|---|---|
| Poignée (riser) | Partie centrale rigide que la main tient ; porte le repose-flèche | Masse la plus épaisse, au milieu : c'est là qu'on met le motif fort |
| Branches (limbs) | Les deux bras souples au-dessus et au-dessous de la poignée, qui plient et stockent l'énergie ; sur un arc recourbé, les bouts se recourbent vers l'avant | Deux longues courbes symétriques qui s'affinent vers les bouts |
| Bouts et encoches (nocks) | Rainures au bout des branches où s'accroche la corde | Un petit renflement au bout : on peut le remplacer par un ornement (nuage) |
| Corde | Relie les deux bouts ; le **tranchefil** (serving) la protège au point d'encochage et aux boucles | Trait fin et droit au repos, en V quand l'arc est bandé |
| Point d'encochage (nocking point) | L'endroit de la corde où s'encoche la flèche, à peu près au milieu | Sommet du V, l'encoche de la flèche y touche |
| Band (brace height) | Distance poignée–corde au repos | La corde ne touche jamais la poignée |
| Flèche | Fût, pointe à l'avant, encoche et empennage (2–3 plumes) à l'arrière | Pointe = deuxième point focal quand l'arc est bandé |

## Repère vanilla (images du jar 26.1.2, mesurées)

- `bow.png` vu depuis +Z : branche du haut le long du bord haut, branche du bas le long du bord gauche, poignée vers (5, 10) dans le bloc ; corde du coin haut droit au coin bas gauche.
- `bow_pulling_0..2.png` : la flèche va du bas à droite (encoche) vers le **haut à gauche** (pointe), la corde tirée jusqu'au coin bas droit (≈ 9 px derrière la poignée le long de la flèche).
- Donc S_ (vers la cible) = (−1, 1, 0)/√2, H_ (branche du haut) = (1, 1, 0)/√2 ; bouts à ≈ ±8,5–9 px de la poignée le long de H_, reculés d'environ 6 px. Display `item/bow` gardé (`tools/objet.py`).

## Matières de confiserie

- **Guimauve torsadée** (bâtons de guimauve vendus en confiserie) : deux brins, un rose (fraise) et un blanc, tordus en corde ; surface mate et poudrée, rayures en spirale régulières, bouts coupés nets. Les deux couleurs franches se lisent de loin comme un bonbon, pas comme du bois.
- **Sucre cuit (cœur)** : brillant, un grand reflet blanc net en fenêtre et un petit contre-reflet (fiche `.claude/styles/kawaii.md`, Matières) ; couleur saturée (framboise), ombre froide.
- **Nuage** : bosses rondes qui se touchent, blanc ombré de lilas (pas de gris).
- **Bâton de sucre** (fût de la flèche) : crème à fines rayures en spirale.

## Codes de l'arc magique « mignon » (anime, magical girl ; traduits en spécifications originales)

- Arc rose et lumineux, **cœur** au centre ; la corde est une ligne de lumière.
- La flèche « se charge » : elle absorbe des cœurs ou de la lumière pendant qu'on bande, et ne part qu'une fois pleine. → pointe en cœur qui grossit et s'allume d'une étape de bande à l'autre.
- Au tir, une traînée de cœurs et de paillettes, jamais d'impact violent. → rafale de cœurs « Au tir » et petit nuage de sucre pailleté qui monte et s'efface.
- Retenu pour Phynaria : un cœur percé d'une flèche (la flèche traverse le cœur de la poignée), branches de guimauve torsadée, nuages aux bouts. Aucune forme reprise d'une œuvre.

## Sources

- [Lancaster Archery, A basic guide to the parts of a bow](https://lancasterarchery.com/blogs/guides-and-information/a-basic-guide-to-the-parts-of-a-bow)
- [Legend Archery, Parts of a recurve bow](https://legendarchery.com/blogs/archery-bowhunting-blog/parts-of-a-recurve-bow)
- [Start Archery, How do I set up my recurve bow (brace height, nocking point)](https://startarchery.co.uk/learn/how-do-i-tune-my-bow/how-do-i-setup-my-recurve-bow)
- [Candy Warehouse, Jumbo marshmallow twists (deux brins rose et blanc tordus)](https://candywarehouse.com/strawberry-puffy-poles-jumbo-marshmallow-twists-1kg-bag)
- [Tropedia, Energy Bow (codes de l'arc de lumière)](https://tropedia.fandom.com/wiki/Energy_Bow)
