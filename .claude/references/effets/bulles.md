# Référence : bulles (savon, gomme) et leur éclatement

Fiche documentée le 2026-11-08 pour `bulle_kawaii` v3. Codes génériques seulement. À lire avec `auras.md` et `principes-fx-anime.md`.

## Ce que montre le vrai

- **Une bulle se lit par son bord et ses reflets**, pas par son centre : le film est plus fin et plus transparent face à l'œil et plus dense, plus coloré, sur le pourtour (effet de Fresnel). Le reflet le plus clair est une **fenêtre** (rectangle arrondi ou ovale, l'image de la source de lumière), en haut, du côté de la lumière ; un petit contre-reflet en croissant de l'autre côté.
- **Irisation** : fines bandes de couleur près du bord (magenta, vert, bleu) qui changent avec l'épaisseur du film. En dessin, quelques traits fins de couleur au bord suffisent.
- **Gomme et savon** : la bulle de gomme est plus épaisse et plus opaque, d'une seule couleur franche (rose), avec des reflets plus mats ; elle gonfle par bouffées (on souffle plusieurs fois) et se tend avant d'éclater.
- **Éclatement** : très rapide. Le trou s'ouvre depuis un point, le film se rétracte à environ 10 m/s (une bulle d'1 cm disparaît en environ 1 ms, rétraction en environ 3 ms) ; le bord qui recule se défait en gouttelettes. La gomme, elle, ne disparaît pas : elle se déchire en lambeaux qui retombent ou se recollent.

## Codes du dessin animé

- **Gonfler** : squash-and-stretch à volume constant, petites bouffées qui dépassent puis se posent ; juste avant l'éclat, la bulle se tend (un peu plus grosse) et tremble.
- **Pop** : la bulle disparaît d'une image à l'autre (pas de fondu) ; à sa place, un éclair bref (anneau et traits rayonnants, « traits de pop »), quelques éclats ou lambeaux qui partent en étoile, en 0,2 à 0,4 s. Le son tombe exactement sur l'image où la bulle disparaît.
- **Bulle de sommeil** : une bulle qui gonfle et dégonfle au rythme de la respiration, sans éclater (ou en éclatant au réveil).

## Traduction dans le mod (`bulle_kawaii` v3)

- Bulle = **plaque face caméra** (`cam_`) peinte comme une sphère : rond parfait sous tous les angles, sans facettes (la v2 en 72 pastilles se lisait facettée et terne).
- Film en `trans_`, **couleur franche** (rose (255, 74, 162), alpha 0,70 au centre à 0,95 au bord, bord plus clair) : un rose pastel très clair en `trans_` se lit blanc en jeu (avis du set Kawaii). Reflet en fenêtre presque opaque, contre-reflet, liseré menthe.
- Calque `_e` : seulement les reflets et un liseré rose fin au bord, pour que le contour se lise la nuit.
- Placement : derrière la nuque, reculée de 10 à 11 px dans le `cam_` (toujours derrière la tête, jamais devant le visage) ; les `add_` de la lueur sont plus près de la caméra que les bulles (un `trans_` cache l'additif placé derrière lui).
- Éclat : échelle de la bulle à 0 en une image ; éclair `add_` qui s'ouvre (0,7 → 1,6) et s'efface par `ctrl_alpha` en 0,32 s ; lambeaux `trans_` (position radiale et échelle) en 0,5 s ; un seul son embarqué (`pop_gomme`), une fois par boucle de 20 s.
- Échelles cachées dans un état et superposition : un `event_unequip` ne peut pas montrer des lambeaux cachés par l'échelle 0 de l'état (les échelles se multiplient) ; au retrait, les bulles se tendent puis disparaissent, sans lambeaux.

## Sources

- [Physics World : les films de savon éclatent comme des drapeaux qui claquent](https://physicsworld.com/a/soap-films-burst-like-flapping-flags/)
- [Science News Explores : le « pop » des bulles de savon](https://snexplores.org/?p=172866)
- [Bird et al. 2010, cascades de bulles filles au repli d'un film rompu](https://www.bu.edu/fluidlab/files/2017/10/Bird_et_al-2010-Daughter_bubble_cascades_produced_by_folding_of_ruptured_thin_films-with_supplement.pdf)
- [Bursting of rigid bubbles (arXiv)](https://arxiv.org/pdf/1310.3129)
- [Clip Studio Tips : dessiner ce qui est transparent](https://tips.clip-studio.com/en-us/articles/3416)
- [Josh Comeau : squash and stretch](https://joshwcomeau.com/animation/squash-and-stretch)
- [Clip Studio : les 12 principes de l'animation](https://www.clipstudio.net/en/animation/12-principles/)
