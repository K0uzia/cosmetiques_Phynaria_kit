# Style — Anatomie des ailes (toute pièce ailée : ailes, familiers, chapeaux à ailerons…)

Fiche de référence documentée (2026-11-04). Elle complète la section « Anatomie d'aile » de `.claude/rules/modeling.md`, qui reste la règle courte.

## Où l'aile s'attache

- **Une deuxième épaule, derrière la première.** Chez un humanoïde ailé, l'épaule du bras reste devant et un peu bas ; l'épaule de l'aile est placée **plus en arrière, derrière le torse**, sur une omoplate longue et étroite (l'omoplate du bras est plus triangulaire). Ce n'est pas un appendice collé sur l'omoplate du bras.
- Squelette ajouté : une **fourchette** (clavicules soudées, en V) qui remonte du milieu du torse vers les omoplates de l'aile, et une **carène** (bréchet), crête au centre du sternum où s'ancrent les muscles du vol.
- **Muscles** : un grand pectoral abaisse l'aile (coup vers le bas) ; un second muscle, sous le pectoral, passe en poulie autour de l'épaule et s'attache au dos de l'aile pour la relever. Résultat visible : **un haut du torse massif**, des épaules larges, un dos peu musclé.
- **Pour un cosmétique Minecraft** : racine de l'aile **dans le haut du dos**, près de la colonne et un peu sous les épaules du joueur (x ≈ ±2,5 à ±3, y ≈ 21 à 23, z ≈ +2,5) ; jamais sur le dessus des épaules ni sur les bras. Un volume (scapulaires, carénage, petit boîtier) **couvre la jonction** : on ne voit jamais où l'aile « est collée ».

## Squelette de l'aile (oiseau, chauve-souris)

- **Bras** : humérus **court** et épais (près du corps), avant-bras **long** (radius et cubitus), main **courte** soudée. Les articulations : épaule, coude, poignet.
- **Oiseau** : les rémiges primaires (les plus longues) partent de la main, en éventail ; les secondaires de l'avant-bras ; les tertiaires près du corps ; plusieurs rangs de couvertures sur le dessus ; l'alule (petit pouce à plumes) au poignet.
- **Chauve-souris** : la membrane est tendue entre des **doigts très longs** ; le pouce reste libre, avec une griffe ; la membrane rejoint le flanc, parfois la jambe.
- **Insecte** : pas d'os ni d'articulation ; deux paires (souvent), des nervures ; elles battent très vite et ne se plient presque pas.
- **Mécanique** : la même logique (longerons = os, articulations = pivots motorisés), avec ce qui fait bouger chaque segment visible (vérins, câbles, engrenages).

## Repli au repos

- **Pli en Z** : l'humérus part vers l'arrière, l'avant-bras revient vers l'avant le long du corps, la main repart vers l'arrière. Les primaires se rangent par-dessus et vont vers le bas, au-dessus des mollets ou des chevilles.
- Repliée, l'aile tient **contre le dos**, ne dépasse pas beaucoup la largeur des épaules, et ne traîne pas au sol.

## Taille

- **Pour voler réellement**, un humain de 70 kg aurait besoin d'environ 6 m d'envergure (3 à 4 fois sa taille), et des ailes si grandes seraient elles-mêmes trop lourdes : aucune proportion « réaliste » n'est jouable telle quelle.
- **Formule de dessinateur** (tutoriel « Winged People Anatomy ») : envergure ≈ taille × coefficient du type d'aile + largeur du dos. Le coefficient dépend du type : court pour une aile manœuvrable, grand pour une aile de vol plané.
- **Règle du dépôt** (demande de l'utilisateur, 2026-11-04 : « dimension logique par rapport à la taille du corps, voire légèrement plus grande ») :
  - **déployées** : envergure de **1,6 à 2,2 fois la taille du joueur** (52 à 70 px pour 32 px), une seule aile ≈ la taille du corps ;
  - **repliées** : pointes entre les mollets et les chevilles, rien sous les pieds ;
  - au-delà (pièces rares et spectaculaires), le dire et ne pas dépasser l'extension de 60 px par axe.

## Types d'aile (forme selon l'usage)

| Type | Forme | Effet recherché |
|---|---|---|
| Elliptique | Courte, large, arrondie, rémiges écartées au bout | Agile, forêt, décollage rapide (moineau, corbeau) |
| Rapide | Pointue, effilée, étroite | Vitesse, piqué (faucon, martinet) |
| Vol plané actif | Très longue, très étroite | Endurance au-dessus de la mer (albatros) |
| Vol plané passif | Longue, large, primaires écartées en doigts | Majesté, rapace (aigle, vautour) |
| Vol stationnaire | Petite, battements très rapides | Familier, insecte, colibri |

Choisir le type avant de dessiner : il fixe la longueur des primaires, la largeur et le battement.

## Comportement (ce qui rend une aile vivante)

- Les ailes sont **là en permanence** : elles réagissent à tout (le joueur qui s'accroupit, qui court, qui prend un coup).
- **Langage** : ailes relevées et ouvertes = menace ou excitation ; serrées contre le dos = peur, froid, discrétion ; tombantes = fatigue, tristesse ; petits frémissements = nervosité ; ailes ramenées autour du corps = protection.
- **Gestes du quotidien** : s'ébrouer, se lisser les plumes, s'étirer (une aile après l'autre), replier avec soin.
- Le mouvement a une cause : on bat des ailes pour monter, on plane pour descendre, on freine ailes grandes ouvertes avant de se poser. Un appareil porté par un rotor ne bat pas des ailes (retour sur le hibou).

## Apparition (`event_equip`)

Quand on équipe des ailes, elles n'apparaissent pas d'un coup : elles **se déploient** (guide 6.4, `event_equip`). Recette (ailes mécaniques) : un boîtier dorsal visible seulement pendant l'apparition (`ctrl_alpha`), qui s'ouvre ; les ailes en sortent à petite échelle et repliées, grandissent, se déplient de l'épaule vers les primaires, puis le boîtier se referme et disparaît. Pour des ailes organiques : un dos qui se gonfle, des ailes qui sortent pliées et s'ouvrent d'un coup, comme un étirement.

## Sources

- Fantasy Anatomy Analyst, squelette d'humanoïde ailé : https://www.tumblr.com/fantasy-anatomy-analyst/636117560294866944/feather-edition-intro-over-here-starting-with
- Fantasy Anatomy Analyst, musculature : https://www.tumblr.com/fantasy-anatomy-analyst/636418341850038272/previous-post-discussed-the-skeleton-combining
- Fantasy Anatomy Analyst (tag « winged humanoid ») : https://www.tumblr.com/fantasy-anatomy-analyst/tagged/winged%20humanoid
- Ahaviel, « Tips On How to Write Characters with Wings » : https://ahaviel-selah.tumblr.com/post/184376739345/tips-on-how-to-write-characters-with-wings-for (copie lisible : https://www.wattpad.com/426302979-writing-tips-tips-on-how-to-write-characters-with)
- Formule d'envergure : https://www.deviantart.com/blue-hearts/art/Winged-People-Anatomy-Wing-Design-495418997
- Envergure nécessaire pour voler : https://gigazine.net/gsc_news/en/20250215-humans-fly-big-wings , https://www.yalescientific.org/2013/03/qa-why-cant-humans-fly/
