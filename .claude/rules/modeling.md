---
paths:
  - "cosmetiques/**"
---

# Règles — modélisation

## Format

- `meta.model_format = "free"` ou `modded_entity`, `box_uv = false`, `format_version "4.10"`. Texture embarquée en base64, résolution déclarée = taille du PNG, alpha 0 ou 255 uniquement hors groupes `trans_`. Limites chiffrées (rotations, inflate, UV, noms) : tableau de `CLAUDE.md`.
- Groupe de premier niveau selon ce que suit la pièce : `head`, `body`, `right_arm`, `left_arm`… (guide, section 4). Pivot remplacé par l'articulation du joueur. `particle_<nom>` à la racine, jamais porté. Bras : modéliser pour le bras de 4 px (le mod resserre lui-même sur un skin à bras fins) ; une grosse pièce qui ne doit pas être resserrée va dans un sous-groupe `wide_<nom>`.
- **Familier vivant** (bloc `familier`, guide 6.6) : aucun groupe du corps à la racine, pattes à l'origine, tête vers −Z (`categories/familiers.md`). **Skin d'objet** (guide 14) : modèle Java Block/Item dans le bloc 16³, étapes en groupes racine (`repos`, `bande_1`…), sans animation (`categories/objets.md`).
- **Faces horizontales** : `up`/`down` lues comme dans Blockbench depuis le 2026-11-06 soir (guide 3) ; texte, flèche ou arc permis. Avant : retournées par le mod (`fonctions-avancees.md`, Pièges).
- Dos du joueur = **+Z**. Pointe des ailes vers l'extérieur = ±X. Épaules à y ≈ 23.
- Noms de groupes uniques et lisibles (`shoulder_l`, `p3_r`…). Les points de départ de particules sont des groupes vides `emit_<nom>`.

## Vrai volume 3D (retour en jeu, prime sur les sections suivantes)

Vue par la tranche, une aile en plaques découpées se lit comme un « tas de feuilles » empilées : les tranches transparentes laissent des lignes flottantes séparées par du vide. Modèle de référence : `cosmetiques/ailes/ailes_tentacule/ailes_tentacule.bbmodel`.
- Une plume = peau + âme : deux fines plaques au contour rond découpé par alpha 0/255, tranches transparentes, autour de cubes pleins plus étroits, invisibles de face, qui remplissent l'épaisseur. Des cubes pleins seuls donnent des marches et un aspect « trop carré » (retour en jeu). Validé : « la rondeur est bien » (ailes de Bérénice).
- Une aile doit rester un volume continu sous tous les angles : noyau osseux épais, rangées qui se touchent sans vide en profondeur.
- Budget : voir la section Budget (le nombre de cubes n'est pas une contrainte en soi).

## Volume, pas plans

- **Jamais d'épaisseur nulle** : un cube de 0 px d'épaisseur z-fight sous shader (clignotement noir). Minimum 0,3 px ; 0,5 px pour les plumes. Particule : une seule face texturée, pour ne voir qu'une couche (`retours-en-jeu.md`, Recettes).
- **Jamais deux faces coplanaires** : faces parallèles qui se chevauchent à ≥ 0,1 px (viser 0,22, `.claude/references/procedures/remise-aux-regles.md`), rangées décalées de ~0,8 px.
- Les tranches d'une plaque fine (east/west/up/down) sont **transparentes** (UV sur un texel transparent) : on ne veut pas voir les côtés des plaques.
- Les éléments structurels (os, bijoux) sont de vrais volumes texturés sur 6 faces, avec des UV distinctes par face si la forme n'est pas carrée.

## Silhouettes par transparence (la clé du « non-cubique »)

- Une plume, une écaille, un éclat = **plaque rectangulaire + texture découpée par alpha** (cutout). La forme vient de la texture, pas du cube.
- Peindre les textures par script en sur-échantillonnage (×3–4) puis LANCZOS + seuil alpha (≈110) : le résultat final ne garde que 0 ou 255. Bords propres, pas de confettis.
- Bouts **arrondis** (demi-ellipse) plutôt qu'effilés : les pointes très fines se crénelisent.
- Variantes : 4–6 textures par type de plume, attribuées en alternance pour casser la répétition.

## Lisibilité (éviter le « bloc blanc »)

- **Contraste de valeur entre rangées** : couvertures plus claires, secondaires un ton plus chaud, primaires avec pointe colorée/dorée.
- **Ombre de recouvrement** peinte à la base de chaque plume (zone cachée par la rangée du dessus) : c'est ce qui fait lire les couches.
- Détails lisibles à distance de jeu : un liseré doit faire ≥ 3–4 texels de large sur une texture 512. Depuis les mipmaps (guide 5, 2026-11-08), un trait plus fin ne disparaît plus au loin mais pâlit et s'adoucit : il reste un détail, pas un trait qui porte la forme.
- Silhouette dynamique : variation de longueur entre plumes voisines (bord de fuite en vagues), primaires nettement plus longues, éventail ouvert en bout.
- Densité : les rangées doivent **se recouvrir** (pas d'espace entre plumes). Une plume couvre ~60 % de la suivante.

Anatomie d'aile : `categories/ailes.md`. Skins d'objets : `categories/objets.md`.

## Budget

**Consigne de l'utilisateur (2026-11-05)** : « 350 cubes c'est rien, tu as droit à 8192 cubes max, 2048 groupes, 16 animations et 1000 Ko de poids max » (32 animations depuis le 2026-11-06 soir). Ne jamais sacrifier la qualité (volume organique, rondeur, détail) pour économiser des cubes : utiliser ce qu'il faut, jusqu'à plusieurs milliers, dans les limites du mod (compressé < 1 000 Ko, viser ≤ 800 Ko de marge). Les ordres de grandeur ci-dessous sont des constats, pas des plafonds.

- Ordres de grandeur livrés : ailes 275–500 cubes, queue 80–130, tête 90–150, épaules 150, arme 100, aura 35–45 (le guide conseille quelques centaines au plus). Un bone par rémige (primaires + secondaires) suffit pour l'éventail ; couvertures = cubes directs du segment.
- Taille (guide 3, 2026-11-06 soir) : au repos, cubes et pivots à 128 px au plus de l'origine (porté, familier), 320 px (effet), 64 px (skin d'objet) ; les animations peuvent sortir de cette zone (clé `position` ≤ 320 px, `scale` ≤ 16). Un grand cosmétique reste dessiné tant qu'une partie peut être à l'écran. Les tailles validées (ailes 52–70 px d'envergure) restent la référence : plus grand se réserve aux pièces rares et se juge en jeu.
- Poids : compressé < 1 000 Ko (limite du mod, fichier nettoyé par le serveur), viser ≤ 800 Ko ; brut ≤ 16 Mo (le vérificateur alerte encore au-delà de 8 Mo, ancienne limite de stockage que le guide ne cite plus).
