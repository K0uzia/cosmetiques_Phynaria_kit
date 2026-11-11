# Arcs réels (skins d'arc)

Fiche écrite le 2026-11-08 pour `skin_arc_givre` (« Arc de givre »). Sujet : l'anatomie d'un arc recourbé et la façon dont il se tend, pour qu'un skin d'arc ait des proportions crédibles et que ses étapes `bande_1..3` montrent une vraie montée en tension.

## Ce qu'il faut savoir

- **Poignée (riser)** : partie centrale rigide, la seule qu'on tient. Elle porte la prise (souvent gainée), le **repose-flèche** juste au-dessus de la main et la **fenêtre de visée** : la poignée est creusée d'un côté pour que la flèche passe dans le plan de l'arc, au ras du bois ou du métal. Elle est **défléchie** : la prise est en avant, les logements des branches en arrière. La prise est sous le milieu de l'arc (la flèche passe au milieu).
- **Branches (limbs)** : flexibles, larges et minces (plus larges perpendiculairement au plan de l'arc qu'épaisses dans ce plan), effilées vers les pointes. Sur un arc **recourbé**, les pointes se retournent vers l'avant (loin de l'archer) ; au tirage, la recourbure se déroule d'abord, puis le ventre de la branche se cintre. C'est ce qui donne plus de puissance pour une même longueur.
- **Poupées (nocks)** : encoches au bout des branches où s'attache la corde ; sur un arc recourbé au repos, la corde repose sur le ventre de la recourbure sur quelques centimètres.
- **Corde** : tendue entre les poupées ; **tranche-fil** (serving) au milieu, où la corde s'use, et **point d'encoche** où se pose la flèche. **Hauteur de bandage** (brace height) : distance de la prise à la corde au repos, environ 12–13 % de la longueur de l'arc. Allonge (draw) : environ 40 % de la longueur à pleine tension.
- **Flèche** : fût, pointe, empennage de trois plumes près de l'encoche.

## Traduction dans le mod

| Réel | Skin d'arc (guide 14) |
|---|---|
| Arc bandé, corde droite | `repos` : branches au repos, recourbures marquées |
| Début, milieu, fin du tirage | `bande_1`, `bande_2`, `bande_3` : branches plus cintrées, pointes qui reculent et se rapprochent, recourbures qui se déroulent ; corde en V vers le point d'encoche |
| Flèche encochée | une flèche par étape (le jeu ne dessine pas la sienne : l'image vanilla la contient) ; pleine allonge à `bande_3` |
| Tension dans les bras | `item_use` : frémissement qui croît avec `q.use_progress` |
| Lâcher : corde qui revient et vibre, branches qui frissonnent | `event_release` |

Repère : comme `bow.png` / `bow_pulling_*.png` (vus depuis +Z), flèche vers le **haut à gauche**, pointe haute des branches en haut à droite ; poing vers (5, 10, 8) (Display `item/bow`). Mesures sur les images vanilla (px du bloc) : 18,4 px de pointe à pointe ; au repos la corde est à ≈ 4,5 px derrière le dos de la prise (vanilla plus profond que le réel, c'est le sprite qui fait lire « arc ») ; à `bow_pulling_2`, encoche à ≈ 12,7 px derrière la prise, en (12, 4).

## Sources

- Lancaster Archery, *How to set up a takedown recurve bow* (poignée, branches, hauteur de bandage, point d'encoche) : https://lancasterarchery.com/blogs/guides-and-information/how-to-set-up-a-takedown-recurve-bow
- Legend Archery, *Parts of a recurve bow* : https://legendarchery.com/blogs/archery-bowhunting-blog/parts-of-a-recurve-bow
- Wikipédia, *Recurve bow* (recourbure, puissance, déroulement au tirage) : https://en.wikipedia.org/wiki/Recurve_bow
- Archery Australia, *Recurve bow setup* (PDF : brace height, nocking point, repose-flèche) : https://assets.sportstg.com/assets/console/document/documents/recurvebowsetup.pdf
