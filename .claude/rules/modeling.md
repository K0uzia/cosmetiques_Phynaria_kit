# Règles — modélisation

## Format

- `meta.model_format = "free"` ou `modded_entity`, `box_uv = false`, `format_version "4.10"`. Texture embarquée en base64, résolution déclarée = taille du PNG, alpha 0 ou 255 uniquement.
- Groupe de premier niveau selon ce que suit la pièce : `head`, `body`, `right_arm`, `left_arm`… (guide, section 4). Pivot remplacé par l'articulation du joueur. `particle_<nom>` à la racine, jamais porté.
- Dos du joueur = **+Z**. Pointe des ailes vers l'extérieur = ±X. Épaules à y ≈ 23.
- Noms de groupes ≤ 64 caractères (le mod coupe au-delà), uniques, lisibles (`shoulder_l`, `p3_r`…). Les points de départ de particules sont des groupes vides `emit_<nom>`.
- Rotations de base des cubes et groupes ≤ ±360°, rotations de face multiples de 90°, inflate ≤ ±8, résolution UV ≤ 4096.

## Vrai volume 3D (retour en jeu, prime sur les sections suivantes)

Vue par la tranche, une aile en plaques découpées se lit comme un tas de feuilles empilées : les tranches transparentes laissent des lignes flottantes séparées par du vide. Modèle de référence : `cosmetiques/ailes/aile_tentacule_demoniaque/aile_tentacule_demoniaque.bbmodel`.
- Une plume = peau + âme : deux fines plaques au contour rond découpé par alpha 0/255, tranches transparentes, autour de cubes pleins plus étroits, invisibles de face, qui remplissent l'épaisseur. Des cubes pleins seuls donnent des marches et un aspect « trop carré » (retour en jeu).
- Une aile doit rester un volume continu sous tous les angles : noyau osseux épais, rangées qui se touchent sans vide en profondeur.
- Budget : quelques centaines de cubes, selon le guide du mod.

## Volume, pas plans

- **Jamais d'épaisseur nulle** : un cube de 0 px d'épaisseur z-fight sous shader (clignotement noir). Minimum 0,3 px ; 0,5 px pour les plumes. Particule : une seule face texturée, pour ne voir qu'une couche (`retours-en-jeu.md`).
- **Jamais deux faces coplanaires** : décaler chaque élément d'une rangée d'au moins 0,03 px en profondeur, et chaque rangée de ~0,8 px.
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
- Détails lisibles à distance de jeu : un liseré doit faire ≥ 3–4 texels de large sur une texture 512, sinon il disparaît.
- Silhouette dynamique : variation de longueur entre plumes voisines (bord de fuite en vagues), primaires nettement plus longues, éventail ouvert en bout.
- Densité : les rangées doivent **se recouvrir** (pas d'espace entre plumes). Une plume couvre ~60 % de la suivante.

## Anatomie d'aile (base pour tout être ailé)

- Humérus court qui monte en arrière, avant-bras long, main courte qui porte les primaires.
- Primaires sur la main (éventail radial), secondaires perpendiculaires au bord de fuite sur l'avant-bras, tertiaires près du corps, 2–3 rangs de couvertures côté dorsal, scapulaires qui couvrent la racine.
- Les ailes **sortent du dos** : pas de plaque/sac à dos. Racine basse et proche de la colonne (x ≈ ±3, y ≈ 23), couverte par des scapulaires.
- Pas de petits cubes volants portés par le modèle : illisibles. Utiliser des particules, ou des éclats de 3 px au moins.

## Budget

- Ordres de grandeur livrés : ailes 275–500 cubes, queue 80–130, tête 90–150, épaules 150, arme 100, aura 35–45 (le guide conseille quelques centaines au plus). Un bone par rémige (primaires + secondaires) suffit pour l'éventail ; couvertures = cubes directs du segment.
- Extension max : rester < 60 px pour garder une marge (limite 64 par axe, point de mesure non confirmé).
- Poids : < 1 Mo brut, < 200 Ko compressé après optimisation (limite du mod : 1 000 Ko).

## Interdits

- Reproduire un design protégé ou s'en « inspirer de près » (personnages, logos, armes de jeux). Design original.
- Refaire le design quand le souci est une inversion d'axe : vérifier d'abord le signe dans `mirror()`.
