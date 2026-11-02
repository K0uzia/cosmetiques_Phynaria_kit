# Règles — modélisation

## Format

- `meta.model_format = "free"`, `box_uv = false`, `format_version "4.10"`. Texture unique embarquée en base64, résolution déclarée = taille du PNG.
- Outliner : `body (origin 0,24,0) > item (origin 0,0,0) > …`. Les cosmétiques du serveur utilisent cette racine ; la respecter.
- Dos du joueur = **+Z**. Pointe des ailes vers l'extérieur = ±X. Épaules à y ≈ 23.
- Noms de groupes ≤ 64 caractères (le mod coupe au-delà), uniques, lisibles (`shoulder_l`, `p3_r`…). Les points de départ de particules sont des groupes vides `emit_<nom>`.
- Rotations de base des cubes et groupes ≤ ±360°, rotations de face multiples de 90°, inflate ≤ ±8, résolution UV ≤ 4096.

## Vrai volume 3D (retour en jeu, prime sur la méthode « plaque + cutout » ci-dessous)

Vue par la tranche, une aile en plaques découpées se lit comme un tas de feuilles empilées : les tranches transparentes laissent des lignes flottantes séparées par du vide. Modèle de référence : `cosmetiques/ailes/aile_tentacule_demoniaque.bbmodel`.
- Une plume = peau + âme : deux fines plaques au contour rond découpé par alpha 0/255, tranches transparentes, autour de cubes pleins plus étroits, invisibles de face, qui remplissent l'épaisseur. Des cubes pleins seuls donnent des marches et un aspect « trop carré » (retour en jeu).
- Une aile doit rester un volume continu sous tous les angles : noyau osseux épais, rangées qui se touchent sans vide en profondeur.
- Budget : quelques centaines de cubes, selon le guide du mod.

## Volume, pas plans

- **Jamais d'épaisseur nulle** : un cube de 0 px d'épaisseur z-fight sous shader (clignotement noir). Minimum 0,3 px ; 0,5 px pour les plumes. Exception : une plaque à une seule couche voulue (plume-particule), à 0,06 px, car à 0,3 px ses deux faces se lisent comme deux couches.
- **Jamais deux faces coplanaires** : décaler chaque élément d'une rangée d'au moins 0,03 px en profondeur, et chaque rangée de ~0,8 px.
- Les tranches d'une plaque fine (east/west/up/down) sont **transparentes** (UV sur un texel transparent) : on ne veut pas voir les côtés des plaques.
- Les éléments structurels (os, bijoux) sont de vrais volumes texturés sur 6 faces, avec des UV distinctes par face si la forme n'est pas carrée.

## Silhouettes par transparence (la clé du « non-cubique »)

- Une plume, une écaille, un éclat = **plaque rectangulaire + texture découpée par alpha** (cutout). La forme vient de la texture, pas du cube.
- Peindre les textures par script en sur-échantillonnage (×3–4) puis LANCZOS + seuil alpha (≈110). Bords propres, pas de confettis.
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
- Pas de « motes » / petits cubes volants : illisible en jeu.

## Budget

- Viser 150–300 cubes, 40–90 groupes pour des ailes. Un bone par rémige (primaires + secondaires) suffit pour l'éventail ; couvertures = cubes directs du segment.
- Extension max : rester < 60 px pour garder une marge (limite 64 par axe, point de mesure non confirmé).
- Poids : < 1 Mo brut, < 200 Ko compressé après optimisation.

## Interdits

- Reproduire un design protégé ou s'en « inspirer de près » (Tyrael, personnages, logos). Design original.
- Livrer une « v+1 » à l'aveugle quand l'utilisateur dit que c'est inversé : d'abord vérifier la convention avec le modèle de calibration.
