# Style — Cuir (thème Fétiche, ensemble Cuir)

> **Révision du 2026-11-04 (retour de l'utilisateur, prime sur la suite)** : la première version était « trop gothique, pas du tout BDSM », et le loup « trop Zorro ». Nouvelle direction choisie : **latex noir brillant**.
> - Surfaces lisses et luisantes : noir profond (12, 12, 16) avec des **reflets blancs nets et larges** peints (bandes de lumière courbes qui suivent la forme, (200, 204, 214) au cœur), comme du latex ou du vinyle. C'est le reflet qui fait la matière.
> - **Plus de coutures rouges, plus de clous pointus, plus de rouge** : le rouge et noir lisait gothique. Coutures, s'il en faut, en noir à peine plus clair.
> - Quincaillerie **chrome** franche : anneaux en O et en D, boucles à ardillon, rivets ronds plats, mousquetons, maillons.
> - Tête : **harnais de sangles** (`harnais_tete_cuir` : front, sommet, menton, anneaux en O aux tempes). `masque_cuir` : harnais de tête + bâillon-boule rouge, d'après l'image de référence de l'utilisateur (demande explicite, serveur privé adulte, grade admin), sans cagoule.
> - Collier sur le **haut du torse** (pas sur la tête : il se lisait comme un bandeau sous le menton), avec une **laisse** accrochée à l'anneau.
> - Bras fins (modèle Alex, 3 px) : le guide ne permet pas de le savoir, les bracelets sont faits pour 4 px (demande `query.is_slim_arms` au développeur).
> - Ailes : retirées de l'ensemble par l'utilisateur.

Ensemble demandé le 2026-11-04 pour un serveur privé entre adultes, pièces réservées au grade admin. Registre « mode fétiche » : cuir, sangles, clous, anneaux, chaînes. **Rien d'explicite ni de sexuel dans la représentation** (pas de nudité, pas d'objet sexuel, pas de bâillon) : des accessoires de mode, portés par-dessus le skin.

## Esprit

Élégant et dur : le cuir verni est **tendu et net**, cousu avec soin, avec des pièces de métal brillant qui ont une fonction (une boucle ferme une sangle, un anneau relie deux sangles, un clou tient une couture). Pas de cuir usé, pas de patine, pas de taches : tout est propre et brillant (leçon `ailes_steampunk` : les taches et le brossé contrasté se lisent comme des bugs de texture).

Éléments-signatures : sangles de 1 à 1,5 px de large avec une couture rouge de chaque côté, boucles rectangulaires à ardillon, anneaux ronds (O-ring) et en D, clous ronds ou pyramidaux, rivets doubles, chaînes à maillons alternés (un maillon de face, le suivant de profil).

## Palette

| Matière | Clair | Base | Ombre | Usage |
|---|---|---|---|---|
| Cuir verni noir | (92, 92, 104) | (34, 32, 38) | (14, 12, 16) | Sangles, masque, membrane. Le reflet du vernis = un liseré clair net en haut de chaque sangle, pas un dégradé |
| Argent chromé | (236, 238, 244) | (168, 172, 184) | (78, 80, 92) | Boucles, anneaux, clous, maillons, ossature |
| Rouge sang | (214, 52, 64) | (150, 22, 36) | (82, 10, 20) | Coutures (2 texels au moins), doublure, liserés, lueur `_e` sobre |

Grandes surfaces sombres, points de métal clairs et petits, rouge en filets : jamais de grande surface rouge vive. Un clou = 3 texels au moins, un liseré de couture = 3 à 4 texels sur une texture 512.

## Lumière et nuit

Calque `_e` discret : coutures rouges faiblement lumineuses (80 à 140 dans `_e`) et un point focal par pièce au plus (l'anneau du collier, les yeux du masque). Le cuir noir doit rester lisible de nuit : liseré clair du vernis dans la texture, `tools/ambiance.py` comme partout (pluie : cuir mouillé plus sombre et plus brillant).

## Mouvement

Le cuir est souple mais tendu : petites ondulations amorties, rien de mou. Les chaînes pendent (gravité), balancent avec un léger retard sur ce qui les porte, et tintent rarement (sons : `tools/sons.py`, `block.chain.step` ou `block.chain.hit`, un par boucle de 20 s au plus au repos). Le métal ne se déforme pas.

## Harnais v3 (2026-11-08)

Refonte après « les épaules sont juste moches » : harnais de torse construit comme un vrai (`.claude/references/objets/harnais.md`) : bretelles + barre de poitrine en H devant (deux anneaux en O), X dans le dos autour d'un grand anneau, sangles qui passent sous les bras ; épaulières de latex moulé (coque arrondie, reflet blanc qui suit l'arrondi, joncs chromés sur les tranches, rivets ronds) tenues par une sangle et un anneau en D sur un brassard de biceps bouclé ; cadenas chromé qui pend (`phys_…_g100`). Plus de collier, de laisse ni de chaînes qui flottent. Latex : noir presque partout, **une** ligne de reflet blanche nette par sangle (un reflet large se lisait comme du chrome).

## Pièces de l'ensemble (2026-11-04)

`harnais_cuir` (épaules : harnais de torse, épaulières et brassards, cadenas ; v3 du 2026-11-08), `masque_cuir` et `harnais_tete_cuir` (tête, archivés le 2026-11-08), `fouet_cuir` (arme, archivée le 2026-11-08 → skin de canne à pêche `skin_canne_cuir` « Fouet de cuir verni » : tresse noire à reflet blanc, pommeau et bagues chrome, claquoir nacré, claquement synthétisé), `skin_bouclier_cuir` « Rondache de latex » (skin de bouclier, 2026-11-08 : latex tendu sur armature chromée à 8 rayons, umbo rond, bordure rivetée, sangles à anneau en O et boucle devant, poignée tressée et sangles en H au dos), `ailes_cuir` (ailes de chauve-souris en cuir tendu sur ossature d'argent noirci).
