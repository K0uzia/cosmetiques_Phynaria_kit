# Références : animaux réels

Fiches documentées par recherche (2026-11-04), pour ne pas refaire la recherche à chaque familier, queue, paire d'oreilles, chapeau ou paire d'ailes. Elles complètent `.claude/styles/familiers.md` (principes et Molang de hasard) et `.claude/styles/ailes-anatomie.md` (ailes portées), qui restent les règles. Chaque fiche : proportions à l'échelle du dépôt, détails qui font l'animal, comportements avec durées, version anime / stylisée, recette dans le mod, pièges, sources.

| Fiche | Contenu |
|---|---|
| [canides.md](canides.md) | Renard roux, renard polaire, loup, chien : museau et oreilles qui séparent renard et chien, play bow, s'ébrouer (4 à 6 Hz), kitsune en ambiance |
| [felins.md](felins.md) | Chat, lynx, grands félins : yeux en amande sur la ligne médiane, queue droite = salut, clignement lent, bouche en ω |
| [oiseaux.md](oiseaux.md) | Passereaux, hibou et chouette, corbeau, aigle et faucon : saccades de tête, disque facial, s'ébouriffer, battements lisibles 4 à 8 Hz |
| [chauves-souris.md](chauves-souris.md) | Petites insectivores et roussettes : aile = main à quatre doigts + pouce griffu, enveloppement, repli de la membrane |
| [reptiles.md](reptiles.md) | Lézard, serpent, tortue : posture étalée, pas de paupières (serpent, gecko), onde qui se propage, immobilité puis geste vif |
| [insectes.md](insectes.md) | Papillon, libellule, abeille, scarabée : trois parties, pattes sur le thorax, battement trop rapide rendu par un éventail `trans_` |
| [marins.md](marins.md) | Poisson, méduse, pieuvre, raie : cause du flottement, pulsation rapide puis lente, bras qui s'enroulent depuis le bout |
| [lapins-rongeurs.md](lapins-rongeurs.md) | Lapin, écureuil, hamster : binky avec torsion, pied arrière énorme, panache relevé, abajoues |
| [cervides-equides.md](cervides-equides.md) | Cerf, faon, cheval, poney : pattes fines articulées, oreilles baromètre, bois sur le dessus de la tête, salut de la biche de Nara |

## Ce qui revient dans toutes les fiches

- **Stylisé mignon** (schéma du bébé de Lorenz, tutoriels chibi) : tête grosse (1:1 à 1:2 avec le corps), yeux grands et **bas** sur la tête, museau et bouche petits, membres courts, formes rondes ; ne garder que les deux ou trois marques qui identifient l'animal. Langage des formes : rond = doux, carré = solide, triangle = rusé ou dangereux.
- **Symboles manga** (goutte de sueur, veine de colère, étoiles, bulle de sommeil) : faisables en petites plaques ou en particules qui montent, avec parcimonie.
- **Jamais** de copie d'un personnage protégé : les animes, jeux et mascottes cités le sont pour l'ambiance (CLAUDE.md, règle 5).
- **Logique physique** : un animal terrestre qui flotte a besoin d'une cause visible (magie, bulle, ailes) ; ses pattes ne marchent pas dans le vide.
- **Paupières** : clignement par échelle y (recette de `familier_givre`), sauf pour les animaux qui n'en ont pas (serpent, poisson, la plupart des geckos).
- **Budget** : 16 animations ; les 12 états + `overlay_` + `event_equip`, `event_jump`, `event_land` remplissent tout. Les comportements ponctuels passent par le tirage Molang de `familiers.md` dans `idle`, pas par des animations séparées.
