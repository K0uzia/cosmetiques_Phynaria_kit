# Fouets (fouet long, fouet de dresseur) — référence pour les skins d'objets

Recherche du 2026-11-08 pour `skin_canne_cuir` (ensemble Cuir). Sujet réel : le fouet long tressé (bullwhip) et son claquement.

## Anatomie (du poing à la pointe)

| Partie | Ce que c'est | Ce qui la fait lire |
|---|---|---|
| Manche (handle) | Court, rigide, bois ou âme métallique couverte de cuir tressé ; souvent un pommeau (bouton) et une dragonne ou un anneau au bout, surtout pour l'accrocher | Plus épais que tout le reste, tresse serrée, bouts nets (bagues) |
| Corps (thong) | La plus grande longueur : lanières tressées (8 à 16 brins et plus) autour d'une ou deux âmes (« bellies ») ; il **s'effile** régulièrement du manche à la pointe | Tresse en chevrons, diamètre qui diminue sans à-coup |
| Attache (fall hitch) | Suite de demi-clés qui noue la mèche au bout du corps | Petit renflement juste avant la mèche |
| Mèche (fall) | Une seule lanière lisse de 25 à 75 cm, remplaçable (c'est elle qui s'use) | Lisse, plus fine, d'une autre matière que la tresse |
| Claquoir (cracker, popper) | Brins de ficelle ou de nylon effilochés noués au bout de la mèche, souvent d'une couleur claire | Petit pinceau pâle : le point focal |

Longueur d'un fouet long : 1 à 6 m (mesurée du talon du manche à la fin de la tresse).

## Le claquement (physique mesurée)

- Le geste du bras crée une **boucle** qui roule le long du fouet. Comme le fouet s'effile, la boucle **accélère** (facteur 10 environ), le bout léger ajoute un facteur 2 à 3 : la pointe va jusqu'à plus de 30 fois la vitesse du poignet, environ Mach 2.
- Le bang est un petit **bang supersonique** émis quand la boucle arrive au bout et s'ouvre : le claquoir se retourne brutalement, la pointe reste supersonique environ 1,2 ms, puis ralentit sous Mach 1 en une vingtaine de centimètres.
- Son : onde de choc de quelques millisecondes (2 à 5 ms), énergie surtout entre 1 et 5 kHz (souvent autour de 1,3 kHz), puis échos jusqu'à 100–200 ms. Juste avant : le sifflement de la lanière qui fend l'air.

## Mouvement (ce qu'il faut animer)

- Toujours du **manche vers la pointe** : chaque segment suit le précédent avec un retard ; le retard grandit vers la pointe mais de moins en moins vite (la vague accélère).
- L'amplitude grandit vers la pointe (le bout léger dépasse), puis tout se calme en oscillations amorties.
- Le temps fort est **à la fin** : armé (le bras recule), coup sec, arrêt du poignet ; le bang arrive après l'arrêt du manche, pas pendant.
- Au repos, tenu en main : la tresse près du manche garde un peu de raideur, la mèche pend ; une main qui bouge à peine suffit à faire courir une petite vague.

## Recette dans le mod (skin d'objet)

- Type `canne` : seul objet qui « se lance » au bout d'une ligne ; l'image vanilla (perche en diagonale, ligne qui pend du bout) donne la silhouette du repos ; étape `lancee` = lanière tendue jusqu'au coin du bloc, d'où le jeu fait partir sa ligne.
- Un groupe par segment, imbriqués, pivot à la jointure, repère droit + rotations de base. Une simulation à contraintes (chaîne, ressorts de courbure) a été essayée : elle tourbillonne et ne se règle pas ; une cinématique écrite (retard, gain, boucle qui roule, retournement amorti de la mèche) se lit mieux et revient exactement à 0.
- Son : synthèse originale (sifflement balayé, onde en N de 1,4 ms, éclat 2–7 kHz, écho à 55 ms), une clé par geste, rien en boucle.

## Sources

- Wikipédia, *Bullwhip* (anatomie : handle, thong, bellies, fall hitch, fall 25–75 cm, cracker) : https://en.wikipedia.org/wiki/Bullwhip
- A. Goriely, T. McMillen, *Shape of a cracking whip*, Phys. Rev. Lett. 88 (2002), résumés : https://www.eurekalert.org/news-releases/510158 , https://www.americanscientist.org/node/502 , https://www.scientificamerican.com/article/true-cause-of-whips-crack
- P. Krehl et al., mesures du bang (pointe supersonique ≈ 1,2 ms, ralentie en 20 cm), Fraunhofer : https://publica.fraunhofer.de/handle/publica/193228
- Oxford, *Whip waves* (vague qui accélère quand le rayon diminue) : https://advancedmaterials.web.ox.ac.uk/node/4487246
