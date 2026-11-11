# Houes (houe à œil, binette) — référence pour les skins d'objets

Recherche du 2026-11-08 pour `skin_houe_orage` (ensemble Orage). Sujet réel : la houe de jardin et de champ (houe à œil, houe à col de cygne, binette). Toute autre houe de set peut partir de cette fiche.

## Anatomie (du manche à la lame)

| Partie | Ce que c'est | Ce qui la fait lire |
|---|---|---|
| Manche | Long, bois ou métal, souvent effilé pour se coincer dans l'œil | Long et fin |
| Œil (eye) ou douille | Trou forgé dans la tête où passe le manche (houe à œil), ou douille/virole (ferrule) qui prend le manche ; le bout du manche dépasse souvent un peu de l'œil | Renflement à la tête (le « bouton » de la houe vanilla) |
| Col (neck, shank), col de cygne | Tige recourbée entre l'œil et la lame (houe à col de cygne) ; parfois la lame est forgée directement sous l'œil | Le crochet : la tête part d'un seul côté |
| Lame (blade) | Plaque d'acier plate **en travers** de l'axe du manche, plus large au fil qu'à la racine | De profil (vue de l'inventaire) : une bande ; de face (en main) : un trapèze |
| Fil | Bord de la lame, aiguisé, trempé : il coupe les racines et ouvre la terre | Bande claire au bout de la lame |
| Angle de travail | Angle lame/manche : la lame est penchée vers la poignée (≈ 55–70°) ; plus aigu, elle tranche à plat sous la surface ; plus ouvert, elle pioche | Le crochet « revient » vers la main |

## Le geste

On lève, la lame pique dans la terre, puis on **tire** vers soi : la motte se retourne. Dans Minecraft, le labour (clic droit sur l'herbe) fait balancer le bras (supposé : `event_swing`) ; `event_break` quand un bloc est cassé avec la houe (feuilles, foin, mousse…) : la lame mord puis tire.

## Recette dans le mod (skin d'objet)

- Image vanilla (`iron_hoe.png`) : manche en diagonale du bas à gauche vers le haut à droite, tête courte vers le **haut à gauche** (perpendiculaire au manche, à peine penchée vers la poignée), petit bouton au bout du manche au-dessus de la tête.
- `skin_houe_orage` : 22,1 px sur la diagonale, `gui` 0,84 ; col de cygne dans le plan de l'image (vu dans l'inventaire, avec la fente de foudre), lame dans un plan perpendiculaire (son propre repère dans le générateur), vue par la tranche dans l'inventaire et à plat en main.
- Une lame en plaques découpées vue par la tranche se lit en « lames séparées » (peau sans âme au ras du bord) : fil et flancs pleins (barres de 0,3 px dans la bande de la peau).
- Un col trop long et une lame dans son prolongement (70°) se lisent comme un seul bras de pioche : col court et lame à 58° pour un vrai crochet.
- Lecture dans la case (`skin_houe_steampunk`, 2026-11-10) : la largeur de la lame passe en profondeur et n'est vue qu'à sin(`ROLL`) ; à 34° et 5,5 px de long, la lame se lit comme un éclat mince (défaut de la houe abyssale). Lame de 6 px, demi-largeur 3,5 px au fil, `ROLL` = 48° : le trapèze se lit dans la case et la lame pend, plat visible, en 3e personne. Une lame claire (acier clair, bords de laiton) se lit mieux qu'une sombre.
- `euler()` des générateurs : avec le seuil 0,99999, une pièce posée sur l'axe de la lame (bague) tombe dans la branche du blocage de cardan et perd l'angle Z ; seuil 1 − 1e-9.
- Lame à contour non trapézoïdal (`skin_houe_kawaii`, lame en cœur à deux lobes, 2026-11-11, `.build/face_roll.png`) : vue de face, la forme se lit déjà à `ROLL` 48° mais les lobes ne se détachent nettement qu'à partir d'environ 60° ; à 80°, guère mieux dans la case (le col cache la racine). Retenu 60° : forme lisible dans la case, plat encore visible quand la lame pend en main (3e personne de la planche).

## Sources

- Hoe (tool), anatomie (lame, œil, col, manche) : https://cavac.at/cavacopedia/Hoe_%28tool%29
- Brevet *Improvement in hoes* (œil forgé qui prend le manche, col et lame) : https://patents.google.com/patent/US164023A/en
- Brevet *Hoe* (col de cygne qui entre dans la virole) : https://patents.google.com/patent/US975320A/en
- Easy Digging, *Adjust hoe angle* (angle de la lame et du manche, effet sur la coupe) : https://www.easydigging.com/garden-hoes/faq/adjust-hoe-angle.html
- House Digest, *15 types of garden hoes* : https://www.housedigest.com/760574/types-of-garden-hoes-and-how-they-all-differ
