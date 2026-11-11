# Marteaux de guerre et masses d'armes — référence pour les skins d'objets

Recherche du 2026-11-08 pour `skin_masse_orage` (ensemble Orage). Sujet réel : le marteau de guerre (fin du Moyen Âge) et la masse à ailettes, pour la grammaire des formes ; aucune arme de jeu ni de film reproduite.

## Anatomie (du talon à la tête)

| Partie | Ce que c'est | Ce qui la fait lire |
|---|---|---|
| Talon, pommeau | Bouton ou calotte de fer bombée au bout du manche, parfois une courte pointe | Petit volume net qui ferme la silhouette |
| Poignée | Bois gainé de cuir ou de corde, parfois une dragonne | Plus épaisse que le manche, tours serrés |
| Manche (haft) | Bois de 60 cm à 1,2 m (marteau à une main : 50–80 cm) | Fin, droit ; c'est la tête qui donne la masse |
| Attelles (langets) | Bandes de fer qui descendent de la douille le long du manche, rivetées : le manche ne casse pas sous un coup paré | Filets clairs sous la tête, rivets |
| Douille | Collet qui reçoit la tête | Bague plus large juste sous la tête |
| Tête de marteau | Bloc court et lourd, face de frappe plate ou un peu bombée, souvent striée ou en « pointes de diamant » pour mordre l'armure | Face nette, carrée ou octogonale, plus large que le manche |
| Bec (beak) | À l'opposé de la face : pointe courte à quatre pans (perce) ou crochet | Asymétrie de la tête |
| Pointe de tête | Pointe dans l'axe du manche, au-dessus de la tête (estoc) | Prolonge la ligne du manche |
| Masse à ailettes | Tête de 6 à 8 ailettes triangulaires à bord concave, qui concentrent le coup sur un point | Étoile vue de dessus, contour en dents |

Le marteau de guerre sert contre l'armure de plates : la face assomme, le bec perce. La masse à ailettes répond à la même armure (XIIe–XVe siècle).

## Ce qu'on en garde pour le mod

- **Silhouette en T** : manche fin, tête lourde en travers, pointe dans l'axe ; une face plate d'un côté, un motif différent de l'autre (asymétrie qui se lit dans la case d'inventaire).
- Attelles rivetées et douille : détail réaliste peu coûteux (4 plaques fines, rivets peints).
- La tête doit rester **dans l'esprit de la masse vanilla** (tête en haut à droite, manche en bas à gauche, `mace.png`) et pas beaucoup plus large qu'elle : en 1re personne, une tête de 13,5 px de large débordait nettement du carré vanilla ; 12 px se tient.
- Display : `item/handheld_mace` (3e personne échelle 1, 1re personne 0,9), plus grand que l'épée : à prendre du jar, pas de `item/handheld`.

## Masse à ailettes en vrai volume (`skin_masse_abyssal`, 2026-11-09)

- Six ailettes à 60° autour d'un noyau en tour : chaque ailette est une plaque biseautée fermée (`volume-3d.md`) posée dans son plan (a le long du manche, rayon e_j, épaisseur selon A × e_j) ; même géométrie dans chaque plan, donc **mêmes tuiles** pour les six (texture 31 Ko).
- Contour qui se lit comme une masse à ailettes : **deux bords concaves** qui se rejoignent en une pointe portée vers le haut (bord bas long et creusé, bord haut court et raide). Un bord extérieur convexe qui monte jusqu'au sommet se lit comme une tulipe ou une coupe (essai écarté).
- Racines cachées dans le noyau : à 60°, deux ailettes de 1,2 px d'épaisseur se touchent sous 1,4 px de rayon ; garder le noyau plus large que ça (apothème 1,55–1,72).
- Lecture dans la case : les plats des ailettes du plan de l'image se voient de face et font l'essentiel de la tête ; un plat d'os sombre donne un losange noir. Reflet violacé large sur le plat, liseré violacé large au biseau et filet de gouttière plus large rendent la tête lisible.

## Sources

- [Worcester Art Museum, Warhammer](https://worcester.emuseum.com/objects/49924/warhammer), [Warhammer for a Horseman](https://worcester.emuseum.com/objects/49647/warhammer-for-a-horseman), [Flanged mace](https://worcester.emuseum.com/objects/48728/flanged-mace)
- [The Met, War Hammer](https://www.metmuseum.org/art/collection/search/33853)
- [Medieval Collectibles, anatomie des armes](https://www.medievalcollectibles.com/glossary/terminology/anatomy-of-weapons/)
- [Periodic Table of Weapons, war hammer](https://periodic-table-of-weapons.pages.dev/blog/war-hammer-weapon)
- Masse à ailettes : [Kult of Athena](https://www.kultofathena.com/?p=37849), [Dark Knight Armoury](https://www.darkknightarmoury.com/product/flanged-medieval-mace/)
- Foudre : `.claude/references/effets/foudre.md`

## Masse à couronne dentée en vrai volume (`skin_masse_steampunk`, 2026-11-10)

- Les ailettes deviennent les **dents d'un engrenage** autour de l'axe : anneau en tour (16 pans) + 8 dents, chacune un **prisme fermé** : contour (r, t) à 6 sommets (pied 2 × 0,55, sommet 2 × 0,36 chanfreiné de 0,13), un cube de 0,3 px par côté posé dans le plan du côté (face extérieure peinte), deux bouts perpendiculaires à l'axe découpés par l'alpha ; le pied reste dans l'anneau (pas de face). Fonction `dent()` de `gen_skin_masse_steampunk.py`, réutilisable pour tout prisme extrudé le long d'un axe.
- Décaler les dents de 22,5° : avec une dent face à la case, elle se lit comme un pavé plat ; décalées, deux dents se voient de 3/4 et le profil fait une étoile.
- Rotation d'une couronne autour de l'axe du manche : `euler(axe_angle(A_, deg))` ; avancer d'une dent par événement (360/8) ne fait pas de saut à la fin (symétrie).
