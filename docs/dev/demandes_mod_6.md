# Demandes au mod (6) — effets de téléportation

Tu travailles sur le mod Phynaria Utilities. Ce document fait suite à la demande 5 (toutes faites dans le guide du 2026-11-06 soir) ; il commence le 2026-11-07.

**État (2026-11-08)** : les 5 demandes sont faites dans le guide du 2026-11-08 (« demandes 6 ») : 1 copie du départ à l'échelle (section 15), 2 aperçu `depart` / pause / `arrivee` en boucle (sections 13 et 15, option bonus comprise), 3 écrit dans la section 4 bis (pas d'option sans écriture de profondeur), 4 mipmaps (section 5), 5 `add_` et `_e` × alpha (sections 4 bis et 5 bis).

## Résumé

| # | Demande | Ce que ça débloque | Priorité |
|---|---|---|---|
| 1 | **Effets de téléportation : appliquer l'échelle du groupe `joueur` à la copie du départ** (section 1) | Le joueur rétrécit en étant aspiré dans un vortex, un portail ou un anneau, comme le guide l'annonce | Haute |
| 2 | **Menu *Apparence* : aperçu d'un effet de téléportation qui joue `depart` en boucle**, pas `charge` (section 2) | On voit le vrai spectacle de l'effet avant de l'acheter ou de l'équiper | Moyenne |
| 3 | **Guide 4 bis : dire qu'une face `trans_` cache les `add_` et les particules placés derrière elle** (section 3), option : `trans_` sans écriture de profondeur | On évite des effets entiers invisibles en jeu (lumière enfermée dans une gaine translucide) | Basse |
| 4 | **Textures des cosmétiques : mipmaps ou filtre adouci au loin** (section 4) | Les traits fins (fissures, étincelles, runes) restent visibles à quelques blocs au lieu de disparaître ou de faire des escaliers | Moyenne |
| 5 | **`add_` dégradé par l'alpha de la texture** (section 5) | Des lueurs qui s'estompent en douceur sur leurs bords, au lieu de devoir peindre le dégradé dans la couleur | Basse |

## 1. Échelle de la copie du joueur au départ (2026-11-07)

### Constat
La section 15 du guide dit qu'au départ « une copie du joueur suit le groupe `joueur` » et peut rétrécir. En jeu (effet « Vortex spatial », captures du 2026-11-07 16.43), la copie ne rétrécit pas : elle reste à sa taille normale pendant que nos clés d'échelle passent de 1 à 0.

Dans le code de la 1.4.0 (`TeleportEffects.submit`), la copie du **départ** suit seulement la **position** du groupe `joueur` ; son échelle n'est jamais appliquée. À l'**arrivée** et pendant la **charge**, l'échelle est bien appliquée (et rien n'est dessiné sous 0,05).

### Ce qui est demandé
1. **Appliquer l'échelle du groupe `joueur` à la copie du départ**, comme à l'arrivée et pendant la charge (échelle 0 = copie plus dessinée).
2. Le dire dans le guide (section 15), pour qu'on sache que les trois animations se comportent pareil.

Nos effets gardent déjà des clés d'échelle de 1 à 0 au départ : ils rétréciront dès que ce sera corrigé (le Vortex passera alors une option pour remettre la copie qui monte en rétrécissant).

## 2. Aperçu d'un effet de téléportation dans le menu *Apparence* (2026-11-07)

### Constat
Dans le menu *Apparence* (et la boutique), l'aperçu d'un effet de téléportation joue l'animation `charge` en boucle. C'est le moment le plus calme de l'effet : quelques runes ou lueurs autour du joueur. Le vrai spectacle (portail qui s'ouvre, vortex qui aspire, faille dans le ciel) est dans `depart` et `arrivee`, que le joueur ne voit qu'en se téléportant.

### Ce qui est demandé
1. Dans l'aperçu d'un effet, **jouer `depart` en boucle** (relancé à la fin, avec une courte pause de 0,5 à 1 s) au lieu de `charge`. Si l'effet n'a pas de `depart`, jouer `arrivee`, puis `charge` en dernier recours.
2. Option bonus : alterner `depart` puis `arrivee` à chaque tour, pour montrer les deux moitiés de l'effet.
3. Le groupe `joueur` s'applique comme en jeu (position et, si la demande 1 est faite, échelle), pour qu'on voie le joueur disparaître et réapparaître.
4. Le dire dans le guide (sections 13 et 15).

## 3. Une face `trans_` cache les `add_` derrière elle (2026-11-07)

### Constat
Effet « Rayon de téléportation » (captures du 2026-11-07 18.23–18.24) : une colonne de lumière `add_` (coques, traits, silhouette du joueur, éclats) entourée d'une fine gaine `trans_` presque transparente (alpha ≤ 46). En jeu, on ne voyait que la gaine pâle et ce qui était en dehors d'elle (anneaux, cercle au sol) ; la lumière et la plupart des particules avaient disparu, avec et sans shader.

Dans le code de la 1.4.0, les passes sont dessinées dans l'ordre OPAQUE, TRANSLUCENT, ADDITIVE ; `trans_` utilise `entityTranslucent`, qui écrit la profondeur, et `add_` (pipeline `cosmetic_additive`) est testé contre elle. Une face `trans_`, même presque invisible, masque donc tout `add_` (et les particules) qui se trouve derrière elle. C'est logique, mais le guide ne le dit pas, et un créateur pense qu'une surface à alpha 30 laisse voir ce qu'il y a derrière.

### Ce qui est demandé
1. **Le dire dans le guide (4 bis)** : « une face `trans_` écrit la profondeur et est dessinée avant `add_` : ce qui est `add_` derrière elle n'est pas dessiné ; ne pas enfermer de la lumière `add_` dans une enveloppe `trans_` ».
2. Option, si c'est simple : pour les faces `trans_` d'alpha faible (par exemple sous 64), ne pas écrire la profondeur, ou dessiner les `add_` avant les `trans_`. Pas indispensable : nous avons corrigé le modèle (gaine retirée).

## 4. Textures des cosmétiques vues de loin (2026-11-07)

### Constat
Dans le code (1.4.0 et Minecraft 26.1.2), les textures des cosmétiques sont lues au pixel le plus proche, sans réduction progressive au loin. À 3–12 blocs, un trait de 1 à 2 pixels de texture est tout simplement sauté d'une image à l'autre : les fissures, étincelles et runes fines disparaissent ou font des escaliers (captures du 2026-11-07, effets « Cercle d'étincelles » et « Déchirure du Néant »). Nous contournons en dessinant ces traits en géométrie, ce qui coûte beaucoup de cubes.

### Ce qui est demandé
1. Activer des mipmaps (ou un filtre adouci au loin) sur les textures des cosmétiques, comme pour les blocs de Minecraft.
2. Le dire dans le guide (section 5).

## 5. `add_` dégradé par l'alpha (2026-11-07)

### Constat
Le mélange additif utilise `ONE, ONE` : l'alpha de la texture est ignoré, seule la couleur compte. Pour une lueur qui s'estompe sur ses bords, il faut peindre le dégradé vers le noir dans la couleur elle-même.

### Ce qui est demandé
1. Utiliser `SRC_ALPHA, ONE` pour `add_` (une texture sans alpha, à 255 partout, donne le même résultat qu'aujourd'hui), pour que l'alpha serve de fondu.
2. Le dire dans le guide (section 4 bis).
