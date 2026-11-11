# Harnais de torse (latex, cuir) — référence pour les pièces de corps

Recherche du 2026-11-08 pour `harnais_cuir` (ensemble Cuir, thème Fétiche). Sujet réel : le harnais de torse de mode fétiche, dit « bulldog », et ses variantes à épaulières et brassards.

## Construction

| Partie | Ce que c'est | Ce qui la fait lire |
|---|---|---|
| Bretelles | Deux sangles passent sur les épaules (trapèzes) et descendent droit devant et derrière ; coupe « droite » devant et dans le dos | Deux verticales franches qui encadrent le sternum |
| Barre de poitrine | Sangle horizontale qui relie les deux bretelles devant, par deux anneaux en O | Le « H » du devant : c'est la signature du modèle |
| Sangles de côté | De chaque anneau du devant, une sangle file **sous le bras** (aisselle) jusqu'au dos | Disparaît sous le bras : rien ne flotte |
| Anneau du dos | Grand anneau en O entre les omoplates, où se croisent les quatre sangles du dos (deux vers les épaules, deux vers les côtés) | Le « X » du dos |
| Réglages | Boucles à ardillon sur chaque bretelle (devant) et sur les côtés ; pressions dans le dos | Boucle = cadre + ardillon, bout de sangle percé d'œillets qui repasse par-dessus |
| Bouts | Chaque sangle se replie autour du fil de l'anneau et se fixe sur elle-même par deux rivets | Doubles rivets juste après l'anneau |
| Variantes | Épaulières (coque ou plaque sur le deltoïde), brassards de biceps reliés par une courte sangle, collier, anneau à cadenas | Épaulières : volume et silhouette à distance |

Proportions réelles : sangles de 3,2 à 5 cm (1,25 à 2 pouces), les harnais lourds jusqu'à 6 cm ; anneaux en O soudés de 5 à 7,5 cm de diamètre, nickelés ou chromés, fil de 6 à 10 mm. À l'échelle du joueur (torse de 8 px ≈ 40–45 cm, 1 px ≈ 5,5 cm) : sangle de 1 à 1,2 px, anneau de 1,6 à 2,2 px.

## Matière

- **Latex** : noir profond, sans couture (les pièces sont collées), surface lisse et tendue ; ce qui fait la matière, c'est **un reflet blanc net et étroit** qui suit la forme (une ligne par sangle, une bande qui épouse l'arrondi d'une épaulière), le reste reste presque noir. Un reflet large ou gris se lit comme du chrome ou du plastique.
- **Cuir** (variante) : tranches brunies, coutures sellier, mat ; non retenu pour l'ensemble (« trop gothique » en rouge et noir).
- **Métal** : acier nickelé ou chromé, anneaux soudés qui ne se déforment pas, rivets ronds, boucles à ardillon ou à rouleau.

## Recette dans le mod (`harnais_cuir`, 2026-11-08)

- Sangles en vrai volume (0,35 px), face intérieure à 2,37 px du centre du torse ou de l'axe du bras, quincaillerie à 0,1 px au-dessus ; les sangles qui partent d'un anneau se partagent le dessous du fil par secteurs angulaires (pas de faces coplanaires).
- Le torse n'a pas de dessus libre (la tête de 8 px le couvre) : les bretelles finissent sous la tête, à y = 23,62 (0,12 px sous la seconde couche du casque). Les côtés du torse sont cachés par les bras : la sangle de côté est dans le volume du bras, elle n'apparaît que quand le bras s'écarte.
- Épaulières dans `right_arm` / `left_arm` : coque à 0,37 px au-dessus de la seconde couche du bras, arrondi de 90° en 6 pans, joncs chromés sur les tranches (de face, on ne voit d'une coque que son profil).
- Cadenas : `phys_…_g100` (gravité du mod) ; il pend sous un petit anneau.
- Piège mesuré : une plaque dont l'axe X local est selon ±Z monde tombe en blocage de cardan dans la conversion en angles (rotation perdue, pièce invisible) ; `euler()` du générateur le traite (rx = 0).

## Sources

- The Homo Culture, « The Essential Leather Bulldog Harness » : https://thehomoculture.com/30335/
- Fiche produit d'un harnais « bulldog » (anneaux en O devant et dans le dos, coupe droite) : https://www.galaxus.at/en/s17/product/the-red-premium-leder-harness-bulldog-m-s-fetish-clothing-costumes-56951240
- Fiches produit de harnais de torse (bretelles, boucles sur les côtés et les épaules, rivets, anneaux nickelés) : https://store.nastypig.com/products/anvil-leather-bulldog-harness, https://www.huntingholsters.com/men-s-handmade-leather-chest-harness-bulldog-collar
