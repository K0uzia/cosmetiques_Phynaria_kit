# Demandes au mod (7) — skins d'objets : utilisation, sons, projectiles

Tu travailles sur le mod Phynaria Utilities. Ce document fait suite à la demande 6 (2026-11-07) ; il commence le 2026-11-08, après le premier essai en jeu d'un set complet de skins d'objets vivants (ensemble Orage : bouclier, canne à pêche, arc, arbalète, trident).

Retour du joueur, mot pour mot : « c'est styler mais niveau sonore et animations y a des soucis par exemple quand ont bloque avec le bouclier ca bug ca reste pas en garde ca fait que s'enlever et ce remettre et le sons spam, pareil pour la canne a peche quand ont lance pour pecher le sons spam et le flotteur et fils sont pas custome, pour les arme a distance pareil la fleche tirer es pas custom et le sont je pensais que c'etait quand ont tirer la fleche mais non c'est que quand la fleche touche une entité » ; puis « le trident au lancé l'orientation es pas bonne ».

Ce qui suit vient de la lecture du code de la 1.4.0 installée (`ItemSkinRenderer.live`, `stage`, `holdsRodIn`, `submitTrident` ; `CosmeticAnimator.computeItem`, `soundsAt`). Nous ne voyons pas le jeu tourner : les déclencheurs exacts sont des suppositions, signalées comme telles.

**État (2026-11-08, guide de 21 h 38)** : aucune de ces demandes n'est traitée. La mise à jour du guide répond aux demandes 6 (effets de téléportation, mipmaps, `add_` × alpha) ; la section 14 est inchangée (trident lancé toujours annoncé « pointe vers le haut (+Y) », rien sur la flèche, le flotteur, la ligne, le *Display* par étape ni le moment des événements). Demandes toujours à envoyer.

## Résumé

| # | Demande | Ce que ça débloque | Priorité |
|---|---|---|---|
| 1 | **Utilisation et étapes plus robustes** : ne plus comparer la pile par identité, et ignorer les coupures d'un ou deux ticks (section 1) | Le bouclier reste en garde, la canne reste lancée, les sons d'événement ne se répètent plus | Haute |
| 2 | **Trident lancé : la pointe (+Y du modèle) dans le sens du vol**, comme le dit le guide (section 2) | Trident en vol orienté correctement | Haute |
| 3 | **Flèche, carreau, flotteur et ligne personnalisables** depuis le skin de l'arc, de l'arbalète et de la canne (section 3) | Le projectile et la ligne vont avec le skin | Moyenne |
| 4 | **Réglages *Display* par étape** (au moins `bloque` pour le bouclier, comme `item/shield_blocking.json`) (section 4) | Pose de garde du bouclier sans Molang, identique en 1re et 3e personne | Moyenne |
| 5 | **Pose calculée séparément pour la 1re et la 3e personne** dans la même image (section 5) | `q.in_first_person` fiable quand le joueur est dessiné deux fois (pack de shaders, ombre) | Moyenne |
| 6 | **Son à 0 s d'un événement joué dès le premier déclenchement** (section 6) | Le premier tir, le premier coup après avoir pris l'objet sonnent aussi | Basse |
| 7 | **Guide 14 : dire quand partent `event_release` et les autres événements**, et ce qui n'est pas personnalisable (section 7) | On place les sons au bon moment du premier coup | Basse |

## 1. Utilisation et étapes : comparaison par identité (2026-11-08)

### Constat
En jeu : en tenant le clic droit avec le bouclier, la garde « s'enlève et se remet » et le son de `event_use_start` se répète ; la canne lancée rejoue le son de `event_enter_lancee` en boucle.

Dans le code de la 1.4.0 :
- `using = holder.isUsingItem() && holder.getUseItem() == stack` (la pile dessinée, comparée **par identité**) ; même test dans `stage()` pour `bloque`, `leve`, `bande_*`.
- `lancee` = `player.fishing != null && holdsRodIn(player, stack)`, et `holdsRodIn` compare aussi `getMainHandItem() == stack` par identité.
- Les événements sont recalculés une fois par milliseconde pour chaque main (`HeldKey`) : dès qu'une seule image voit `using` faux, on a `use_stop`, puis `use_start` à l'image suivante, plus `enter_repos` / `enter_bloque` ; l'animation `item_use` repart de 0 avec un fondu de 200 ms depuis `item_idle`.

Si la pile de la main est remplacée par une autre instance (mise à jour de l'emplacement envoyée par le serveur, par un autre mod du modpack ou une usure), le joueur local garde l'ancienne référence dans `useItem` ou dans `ItemInHandRenderer` jusqu'au tick suivant : les images dessinées entre-temps voient « plus utilisé ». Supposé : c'est ce qui arrive sur le serveur (modpack FTB Evolution), ou le serveur coupe l'utilisation, ou la canne est relancée à chaque clic tenu.

### Ce qui est demandé
1. Tester l'utilisation par la main plutôt que par l'identité : `holder.isUsingItem() && holder.getUsedItemHand() == <main de la pile>` (ou `ItemStack.isSameItem`), et pareil pour la canne (main qui tient la canne, pas l'instance).
2. **Anti-rebond** : ne déclarer `use_stop` et le changement d'étape qu'après 2 ticks sans utilisation ; ne pas rejouer `use_start`, `enter_<étape>` ni un son d'événement s'ils ont été joués il y a moins de 150 ms pour la même main.
3. Option : une commande de débogage (`/cosmetique debug objet`) qui affiche l'état, l'étape et les événements de la main, pour qu'on voie en jeu ce qui bascule.

## 2. Trident lancé : orientation (2026-11-08)

### Constat
Le guide (14) dit : « Faites le trident pointe vers le haut (+Y) […] dessiné la pointe en avant ». En jeu, l'orientation du trident lancé « n'est pas bonne ».

Dans `submitTrident` (1.4.0), la pose est `rotY(yRot − 90) · rotZ(xRot + 90) · rotZ(−90) · translate(−0,5)` : les deux rotations autour de Z s'annulent en `rotZ(xRot)`. L'axe +Y du modèle reste donc **perpendiculaire** à la trajectoire (debout pendant un lancer à l'horizontale) ; c'est l'axe **+X** du modèle qui part dans le sens du vol (comme la flèche de Minecraft). Le trident vanilla a sa pointe vers −Y et utilise `rotZ(xRot + 90)` seul : la rotation de −90° ajoutée par le mod devrait être de 180° pour une pointe vers +Y.

### Ce qui est demandé
1. Corriger pour que **+Y du modèle soit le sens du vol** (remplacer `rotZ(−90)` par `rotZ(180)`), comme le guide l'annonce ; ou bien dire dans le guide que l'étape `lance` doit être couchée, pointe vers +X.
2. Nous dire laquelle des deux est retenue : en attendant, nous ne touchons pas aux tridents livrés (une étape `lance` couchée serait fausse après le correctif).

## 3. Flèche, carreau, flotteur et ligne (2026-11-08)

### Constat
Seul le trident lancé a un crochet dans la 1.4.0 (`ThrownTridentRendererMixin`). La flèche tirée, le carreau, la fusée de l'arbalète, le flotteur et la ligne de la canne restent ceux de Minecraft : le joueur l'a remarqué tout de suite.

### Ce qui est demandé
1. **Flèche et carreau** : si le skin d'arc ou d'arbalète du tireur a une étape (groupe racine) `fleche` (arbalète : `carreau`), la dessiner à la place de la flèche, dans le repère de la flèche de Minecraft (pointe vers +X ou vers +Y, à nous dire), avec ses `overlay_` (traînée, étincelles) et ses particules en vol. Flèches à effet et flèches spectrales : même modèle (ou `fleche_effet` facultatif).
2. **Flotteur** : groupe `flotteur` du skin de canne, dessiné à la place du flotteur (centré sur le point d'accroche de la ligne), avec ses `overlay_` (le flotteur qui plonge à la touche serait un plus : `event_bite`, ou `q.is_bite`).
3. **Ligne** : couleur (et si possible épaisseur) lues dans le bloc `phynaria.objet` (`"ligne": {"couleur": "#9fd8ff", "lumineuse": true}`), le reste dessiné par le jeu.
4. Le dire dans le guide (section 14, tableau des étapes).

## 4. Réglages *Display* par étape (2026-11-08)

### Constat
Pendant le blocage, Minecraft passe le bouclier à `item/shield_blocking.json` ; le mod garde un seul jeu de réglages. Nous recréons la garde par une animation `item_use` en Molang (`q.in_first_person` × `q.hand`), ce qui dépend de la section 1 et de la section 5.

### Ce qui est demandé
Accepter dans `phynaria.objet` un jeu de réglages par étape, par exemple `"affichage_etapes": {"bloque": {…8 contextes…}}`, appliqué quand cette étape est dessinée (bouclier `bloque` ; utile aussi pour `leve` et la canne `lancee`).

## 5. Pose de la 1re et de la 3e personne dans la même image (2026-11-08)

### Constat
`computeItem` calcule les valeurs une fois par milliseconde pour une main (`HeldKey`), et les réutilise pour tous les rendus de cette milliseconde. Si le joueur est dessiné deux fois dans la même image (pack de shaders : passe d'ombre en 3e personne, puis la main en 1re personne), la pose calculée avec `q.in_first_person` du premier rendu sert au second. Supposé : une garde de bouclier qui saute entre la pose de la 1re et celle de la 3e personne avec un pack de shaders.

### Ce qui est demandé
Calculer (ou mettre en cache) la pose par main **et** par contexte (1re personne, 3e personne), les événements restant comptés une seule fois.

## 6. Son à 0 s d'un événement (2026-11-08)

### Constat
`soundsAt` mémorise le dernier temps lu de chaque animation et ne joue rien au premier échantillon (aucun temps précédent). Une clé de son à 0 s dans `event_release` ou `event_hit` est donc muette au premier déclenchement après que l'objet arrive en main (ou après 10 s sans être dessiné).

### Ce qui est demandé
Au premier échantillon d'un événement, jouer les clés dont le temps est ≤ au temps lu (0 compris). Nous mettons déjà nos clés à 0,03–0,05 s en attendant.

## 7. Guide 14 : moments des événements (2026-11-08)

À ajouter au tableau des animations, d'après le code :
- `event_release` : arc, à la fin de l'utilisation après au moins 3 ticks ; trident et lance, après au moins 10 ticks ; arbalète, quand elle passe de chargée à vide. Rien à l'impact : le son entendu quand la flèche touche est celui de Minecraft.
- `event_use_start` / `_stop` et `event_enter_<étape>` : rejoués à chaque coupure de l'utilisation (voir section 1).
- Lancer la canne déclenche aussi `event_swing` (le bras se balance) : un son sur `event_swing` sonne à chaque lancer et à chaque remontée.
- Ce qui n'est pas personnalisable : flèche, carreau, fusée, flotteur, ligne (tant que la section 3 n'est pas faite).
