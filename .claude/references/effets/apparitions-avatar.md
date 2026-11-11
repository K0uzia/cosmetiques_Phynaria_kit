# Référence — Apparitions d'avatar : cape géante, drapé, entité sans visage

Fiche documentée (2026-11-06, pour `effet_admin` v2). Codes génériques de l'« apparition divine » et de l'entité à capuche vide dans l'animation japonaise et le dessin de drapé ; aucune scène, aucun personnage, aucun costume d'une œuvre n'est repris (règle 5 de `CLAUDE.md`). Une inspiration donnée par l'utilisateur se traduit par analogie, sans être nommée dans les fiches ni dans les livrables.

## Codes visuels

- **Le vêtement est le personnage** : une robe ou une cape géante, capuche vide, manches sans mains. L'absence de visage dit « au-dessus des hommes » ; le tissu porte toute l'expression (gonfle, flotte, se referme).
- **Capuche vide = ombre profonde** : l'intérieur de la capuche est très sombre (noir ou bordeaux presque noir) dès le bord, avec un bord clair (liseré) qui découpe l'ouverture. C'est ce contraste qui empêche la capuche de se lire comme un « autocollant plat » : il suggère un monde intérieur. Pas d'yeux, pas de masque.
- **Contre-jour sacré** : une lumière derrière la tête ou le corps (disque, anneau, gloire) rend la silhouette nette et la rend « divine ». La puissance vient de ce qu'on devine (lueur, ombre), pas de ce qu'on montre.
- **Échelle** : la silhouette dépasse tout ce qui l'entoure ; elle se réduit ensuite à taille humaine pour déposer quelqu'un (« le maître descend parmi les siens »).
- **Lisible en tout petit** : une seule grande forme (cloche de la robe + pointe de capuche), une couleur dominante, des bordures claires épaisses qui dessinent les bords.

## Drapé (ce qui fait lire un tissu lourd)

- Trois principes : **gravité**, **points d'appui** (épaules, tête), **intention** (vent, mouvement). Un tissu lourd tombe droit depuis ses appuis et s'évase vers l'ourlet.
- Types de plis : **tuyau** (pipe : cylindres verticaux qui tombent d'un appui, le pli de base d'une robe) ; **zigzag** (tissu comprimé, coude, tissu replié ou posé au sol) ; **spirale** (autour d'un membre) ; **demi-boucle** (pli brisé) ; **goutte** (drop : cascade d'un point d'appui) ; **feston** (diaper : entre deux appuis) ; **inerte** (tissu affaissé, à éviter, sans vie).
- **Lumière d'un pli tuyau** : clair sur la crête, sombre au creux, demi-teinte sur les flancs ; l'ombre portée dans le creux suit toute la hauteur du pli. Les plis **s'approfondissent vers l'ourlet** (le tissu s'évase).
- Tissu lourd (velours, laine épaisse) : peu de plis, larges, arêtes franches, ombres marquées ; tissu léger (soie) : plis nombreux et fins, transitions douces.
- L'intérieur d'une cape se voit à l'ouverture et par-dessous : plus sombre, d'une teinte voisine (doublure).
- Superposer les couches : robe intérieure claire, manteau foncé par-dessus, collet ou pèlerine sur les épaules ; une étole ou une bande centrale guide l'œil de haut en bas.

## Mouvement et timing

- **Mouvement secondaire et chevauchement** : le tissu suit le corps avec retard ; chaque niveau de la hiérarchie se décale de 2 à 4 images à 24 i/s (racine, puis principal, puis secondaire, puis tertiaire : 0,08 à 0,15 s par niveau). Quand le corps s'arrête, le tissu continue jusqu'au bout de son élan, dépasse, puis se pose.
- **Déroulé** (bannière, drapeau, parchemin) : un tissu roulé ou plié est rigide et ne flotte pas ; il ne bouge librement qu'une fois déroulé. L'onde part du point fixe vers le bout libre ; le bout libre bouge plus que le bord tenu (amplitude croissante vers l'ourlet). Une onde = une amplitude et une longueur d'onde constantes, phase décalée par rang.
- **Apparition divine** (grammaire d'anime) :

| Temps | Durée | Ce qui se passe |
|---|---|---|
| Signe | 0,2–0,5 s | un point de lumière unique dans le ciel, silence ou note tenue, le sol réagit (cercle, poussière qui monte) |
| Éclosion | 0,3–0,5 s | le point grossit d'un coup (dépassement), flash bref |
| Déploiement | 1–1,5 s | la forme s'ouvre depuis le point, en cascade : ce qui est près du point d'abord, le reste avec retard ; dépassement puis retour |
| Révélation | 0,6–1,2 s | on **tient** l'image : la silhouette flotte, contre-jour au plus fort, chœur grave |
| Descente | 0,6–1 s | elle se rapproche, se resserre, se réduit à taille humaine |
| Dépôt | 0,2–0,4 s | contact au sol, onde légère, poussière |
| Dissipation | 0,6–1 s | la forme se défait en fragments (pétales, plumes, éclats) qui montent et s'éteignent, du bas vers le haut |

## Couleurs

- Rouge profond (cramoisi, bordeaux à l'ombre) + blanc cassé + or pour les bordures : couleurs de cérémonie, sans référence à une œuvre. Le rouge domine dehors, le blanc dessine les bords et les couches intérieures, l'or reste un liseré.
- Intérieur presque noir teinté de rouge. Lumière : blanc chaud au cœur, or au bord, une touche de rouge au liseré extérieur.

## Traduction dans le mod

- **Robe en vrai volume** : une colonne par bande de tissu, autour d'une section ondulée (crêtes et creux) ; chaque colonne est une chaîne d'articulations (pivot en haut de chaque segment) qui s'évase vers l'ourlet. La lumière du pli est **peinte** (dégradé en cosinus continu d'une colonne à la suivante, 4 colonnes par pli) : les tuyaux se lisent même sous l'éclairage plat du jeu. Faces intérieures sombres.
- **Déroulé** : chaque articulation repliée en accordéon (±168°, pli zigzag, jamais 180° : faces coplanaires) se déplie de haut en bas avec 0,12–0,17 s de retard et un dépassement ; l'ondulation est une rotation en Molang dont la phase recule d'un rang à l'autre (onde qui descend).
- **Depuis un point** : groupe pivoté sur le point lumineux, échelle 0,02 → 1 ; puis un second groupe pivoté au sol pour la descente et le resserrement autour du joueur.
- **Contre-jour** : disque `add_` dans un `cam_`, reculé derrière la capuche ; capuche vide = plaque opaque presque noire dans l'ouverture.
- **Dissipation** : échelle 0 des segments du bas vers le haut, pétales modélisés et particules qui montent.
- Limite de 64 px par axe : tout tient sous y = 58 (`ECHELLE_ZONE`).

## Sources

- [Swinton's Art : 7 kinds of fabric folds](https://swintonsart.com/post/7-kinds-of-fabric-folds-that-are-good-for-painting) (tuyau, goutte, feston, zigzag, spirale, demi-boucle, inerte)
- [Pluralsight : the 6 fold types every illustrator should know](https://pluralsight.com/blog/creative-professional/the-6-fold-types-every-illustrator-should-know-for-drawing-clothing) (gravité, appuis, intention)
- [Clip Studio Tips : drawing clothes and fabrics](https://tips.clip-studio.com/en-us/articles/6809) (tissu lourd et léger, ombres)
- [Pixune : follow-through and overlapping action](https://pixune.com/blog/follow-through-and-overlapping-action/) et [Toon Boom Learn : follow-through](https://learn.toonboom.com/modules/animation-principles/topic/follow-through-principle) (cape qui suit avec retard, dépasse, se pose)
- [Playbooks : follow-through & overlapping, décalages par niveau](https://playbooks.com/skills/dylantarre/animation-principles/follow-through-overlapping) (2 à 4 images par niveau à 24 i/s)
- [Outerspace Software : unrolling waving flag](https://www.outerspace-software.com/community/5229/unrolling-waving-flag) (un drapeau roulé est rigide ; onde après le déroulé)
- [TV Tropes : Holy Backlight](https://tvtropes.org/pmwiki/pmwiki.php/Main/HolyBacklight) et [Pillar of Light](https://www.tvtropes.org/pmwiki/pmwiki.php/Main/PillarOfLight) (contre-jour divin, colonne de lumière)
- [High Altitude Science : la puissance des êtres divins vient de ce qu'on devine](https://tools.highaltitudescience.com/post/why-every-major-animes-best-angels-are-behind-screens-only--angels-of-anime-exposed) (lueur, ombre, présence suggérée)
- Morphic, « faceless » (figure à capuche : l'ombre profonde de la capuche suggère un monde intérieur, lisible en petit)
