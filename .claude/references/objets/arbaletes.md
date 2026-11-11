# Arbalètes réelles (skins d'arbalète)

Fiche écrite le 2026-11-08 pour `skin_arbalete_orage` (« Arbalète de l'orage »). Sujet : l'anatomie d'une arbalète médiévale et la façon dont elle se charge, pour que les étapes `bande_1..3`, `chargee`, `chargee_fusee` montrent une vraie mécanique.

## Ce qu'il faut savoir

- **Arbrier (tiller, stock)** : pièce de bois (frêne, if) qui aligne le carreau et porte la noix et la détente. Sur le dessus, une **rainure** (ou deux rails) où glisse le carreau ; à l'arrière, la **crosse** qu'on cale contre l'épaule ou la joue.
- **Arc (prod, lath)** : fixé à l'horizontale en travers de l'avant de l'arbrier (ligature ou étrier de fer). D'abord en bois ou en composite, puis en **acier** (tirage beaucoup plus fort, durée de vie). Court et puissant : il plie dans le plan horizontal, ses bouts reculent vers le tireur pendant le chargement.
- **Corde** : au repos, juste derrière l'arc ; tirée jusqu'à la noix pour le chargement (allonge courte, quelques dizaines de cm).
- **Noix (nut)** : **cylindre rotatif** (os, corne, métal) logé dans l'arbrier, une encoche tient la corde, une autre reçoit la gâchette. Tant qu'elle est bloquée, la corde reste tendue sans effort.
- **Détente (trigger)** : longue clé sous l'arbrier, qui libère la noix ; la corde part et pousse le carreau.
- **Étrier (stirrup)** : boucle de métal à l'avant ; l'arbalète posée au sol, le pied dans l'étrier, on tire la corde (à la main, au crochet de ceinture, au cranequin ou au moufle).
- **Carreau (bolt, quarrel)** : plus court et plus épais qu'une flèche, empennage court (deux ou trois pennes), pointe lourde souvent en losange.

## Traduction dans le mod

| Réel | Skin d'arbalète (guide 14) |
|---|---|
| Corde au repos derrière l'arc | `repos` : corde droite, arc peu cintré |
| Tirage jusqu'à la noix | `bande_1`, `bande_2`, `bande_3` : les bouts de l'arc reculent, corde en V qui recule jusqu'à la noix |
| Corde tenue par la noix, carreau posé | `chargee` (carreau dans la rainure), `chargee_fusee` (fusée de feu d'artifice) |
| La noix prend la corde | `event_charged` |
| La détente libère | `event_release` |
| Effort du tirage | `item_use` : frémissement qui croît avec `q.use_progress` |

Repère vanilla : image `crossbow_standby.png`, arc en haut à gauche, crosse en bas à droite (vue d'inventaire) ; le repère de `skin_arbalete_steampunk` est validé en jeu et repris tel quel (`categories/objets.md`, Recette).

## Mesuré sur nos pièces

- **Ornement plan sur l'axe de tir** (`skin_arbalete_kawaii`, 2026-11-11) : l'axe de tir est à 45° dans la case ; une forme symétrique couchée dans cet axe (cœur pointe vers l'avant) y a un côté horizontal et un vertical et se lit comme un coin de boîte. La poser droite dans la case (axe de symétrie vertical), même si elle n'est plus alignée sur le tir.
- **Corde au repos et logement** : la corde passe derrière le logement de l'arc ; un logement large (cœur de 4 px) demande des bras recourbés vers l'arrière (2 px sur 6,2 px) pour que la corde ne traverse pas le logement.

## Sources

- Wikipédia (en), « Crossbow » (parties : arbrier, arc, corde, étrier, noix, détente ; arcs d'acier) : https://en.wikipedia.org/wiki/Crossbow
- Musée national de Finlande, arbalète et carreaux (description des pièces, noix rotative dans un logement sur le dessus de l'arbrier) : https://www.kansallismuseo.fi/en/digitaalinen-kokoelma/tutkijan-valinta/jalkajousia-ja-vasamia/jalkajousi
- « The Crossbow Defined » (vocabulaire, prod, lath, tiller) : https://www.thebeckoning.com/medieval/crossbow/xbow-def.html
