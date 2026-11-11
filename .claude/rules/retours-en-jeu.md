---
paths:
  - "cosmetiques/**"
---

# Règles — leçons des retours en jeu (index)

Erreurs et réussites constatées sur de vrais cosmétiques. Les appliquer **dès la première version**. Ajouter chaque leçon confirmée par une capture ou un avis de l'utilisateur, et supprimer ce qui se révèle faux. « Validé » veut dire vu en jeu ou explicitement approuvé.

## Où sont les avis

| Sujet | Fichier |
|---|---|
| Le rendu ne suffit pas, méthode de travail (sons rares, lumière, logique physique, particules qui tombent, vapeur, générateurs de départ) | `essentiel.md` |
| Ailes (`ailes_abyssales`, Bérénice, fusée en `glide`, `ailes_steampunk`, `ailes_orage` v1–v4) ; lames d'éventail, os | `categories/ailes.md` |
| Familiers (`familier_givre` v2–v10, `familier_kawaii_mochi`, `familier_kawaii_chat`) | `categories/familiers.md` |
| Effets de téléportation (`effet_givre`, `effet_berenice`, `effet_admin`, cercles au sol) | `categories/effets.md` |
| Skins d'objets (`skin_epee_givre`, `skin_arbalete_steampunk`, `skin_lance_orage`) | `categories/objets.md` |
| Auras (`aura_brasier` v1–v3, `aura_berenice`, menu Apparence) | `categories/auras.md` |
| Tête (`bandeau_abyssal`, `masque_abyssal`, Ensemble Cuir v1) ; corne, sangles | `categories/tete.md` |
| Queues, épaules, sacs, armes (`queue_abyssale_v1`) | `categories/corps.md` |
| Shader, `_e`, `_r`, menu Apparence, `emit_mc_`, `ctrl_alpha` (rendus avancés en jeu) | `.claude/references/mod/rendus-avances.md` |
| Pièces livrées sans retour en jeu | `.claude/references/historique-livraisons.md` |

Chaque avis ajouté se reporte dans `cosmetiques/statuts.json` (badge « Validé en jeu » / « Refusé » du Vestiaire ; aussi modifiable depuis le Vestiaire, bouton « Modifier la fiche »).

## Avis communs à plusieurs pièces

| Pièce | Avis | À retenir |
|---|---|---|
| Ensemble Givre (en jeu, 2026-11-04) | « c'est très [bien] », transparence « bien même si légère » ; familier « passif, il fait rien » | Glace en `trans_` (alpha 140–220) validée, avec et sans shader. Familier : `categories/familiers.md` |
| Ensemble Bérénice avec shader (en jeu, 2026-11-05 vers 20 h, captures `20.00.55` à `20.01.10`) | « avec le fix de la demande 3, tout a l'air de bien fonctionner » | Ailes, diadème et aura s'affichent avec Complementary : `add_` et `_e` visibles (`.claude/references/mod/rendus-avances.md`). Vu aussi dans la boutique du mod aux prix de notre grille. Interface du mod (textes coupés, pas de lore dans *Apparence*) : `docs/dev/demandes_mod_4.md` §6 |

## Recettes communes

| Élément | À éviter (constaté en jeu) | À faire |
|---|---|---|
| Anneau, halo | Segments décalés : pointillés. Segments chevauchés : créneaux sombres sous `_e` | Une seule plaque de 0,15 px, anneau découpé par alpha, même forme plus étroite dans `_e` |
| Particule | Barreaux : bâtons. Sections : « bonbon » et double couche. 0,06 px : fragments à distance. Trop près du sol : scintillement | Un seul cube de 0,3 px, y ≥ 0,3 au-dessus du pivot, face `up` seule, courbure peinte dans l'image |
| Lueur | Lueur vive sur un dégradé : orange violent | Fines lignes lumineuses et fond additif très sombre ; rien de vif hors du point focal |
| Usure du métal | Vert-de-gris en taches et coulures : « on dirait des bugs de texture ». Brossé à fort contraste (±22 %) : « petits traits jaunes partout ». Carénage plat de 3 px sur l'avant-bras : « bloc entre les deux engrenages » (`ailes_steampunk`, 2026-11-04) | Métal propre : brossé à ±6 % au plus, pas de taches de patine ; os nus et fins entre les articulations |
| Chaîne, laisse, pendentif | Chaîne enfant du bras : elle reste dans l'axe du bras en sneak, « pas de vraie physique » (`harnais_cuir`, 2026-11-04) | Contre-rotation du premier maillon dans chaque état où l'inclinaison du membre est connue (`pose_joueur`), pendule amorti (T ≈ 2π·√(2L/3g)), retard croissant vers le bout. **Depuis le guide du 2026-11-04 (soir)** : `phys_<maillon>_g100` imbriqués, pivot en haut de chaque maillon (gravité du mod, guide 4 bis), à essayer en jeu avant de retirer les contre-rotations des pièces livrées |
| Pièce posée sur le corps | Sangles à 0,4 px : cachées par un plastron (armure gonflée d'environ 1 px), seuls anneaux et boucles dépassent (2026-11-04) | Réglage du staff **Armure → Par-dessus** (guide 10 : pièces de `head`, `body`, bras et jambes écartées comme l'armure portée ; vérifié par le développeur) à demander pour toute pièce collée au corps ; sinon `q.has_chestplate` etc. pour écarter ou cacher (guide 6.3). À voir en jeu sur `harnais_cuir` |
| Couleur de nuit | Sans `_e` : saumon et mate sous éclairage chaud | Base plus blanche et fond `_e` léger, ou option « Lumineux » du staff |

## À ranger

Nouveaux avis ajoutés en fin de session ; les déplacer ensuite dans le fichier de leur catégorie.
