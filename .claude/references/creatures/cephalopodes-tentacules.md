# Céphalopodes — anatomie d'un tentacule (bras de pieuvre, tentacule de calmar)

Fiche de référence (recherche du 2026-11-08, pour la refonte de `ailes_tentacule`). Complète `marines-mythiques.md` (kraken, bioluminescence) et `.claude/references/animaux/marins.md` (pieuvre familier). Pièces concernées : ailes-tentacules, queues, épaules, chapeaux à tentacules, familiers marins.

## 1. Codes visuels essentiels

- **Hydrostat musculaire** : aucun os. Le bras plie n'importe où, s'allonge, se tord ; il ne casse jamais en « coude ». Un tentacule qui plie comme un bras articulé se lit faux.
- **Effilé continu** : épais à la base, fin au bout, sans étranglement ni anneau ; la pointe est très fine et très mobile.
- **Ventouses sur une seule face** (face orale, l'intérieur de la courbe) : chez la pieuvre, deux rangées en quinconce de part et d'autre d'un sillon, une seule rangée vers la pointe ; elles **rapetissent régulièrement** vers le bout (ventouses « immatures » sur la partie distale). Le calmar porte surtout ses ventouses sur la massue au bout de ses deux longs tentacules.
- **Une ventouse** = deux parties : l'*infundibulum*, le disque extérieur visible bordé d'un **anneau** plissé (stries radiales et circulaires), et l'*acetabulum*, la cupule creusée dans le bras. Lecture à distance : anneau clair, cupule sombre, orifice noir.
- **Toile** (membrane interbrachiale) entre les bases des bras chez la pieuvre.

## 2. Silhouette et proportions (échelle du dépôt)

- Ailes-tentacules : 3 tentacules par côté, longueurs 38 / 29 / 21 px, rayon 2,1 → 0,3 px ; envergure 56 à 60 px (règle des ailes, 52–70).
- Segments de longueurs décroissantes (suite géométrique, rapport ≈ 0,91) : les derniers segments sont courts, ce qui permet une spirale serrée au bout.
- Effilé un peu conique (rayon en (1 − u)^1,25) : la base porte la masse, la pointe s'affine vite.

## 3. Matières et couleurs

- **Peau** : dos sombre et moucheté (chromatophores : taches brunes, rouges, noires qui s'ouvrent et se ferment), flancs plus clairs, face orale pâle (chair, rose). Petites papilles sur le dos.
- **Peau humide** : la peau est couverte de mucus ; elle donne des **reflets nets et étroits** (traînées claires, interrompues, petits points) sur les faces tournées vers la lumière. Peints en rose très pâle et froid, jamais dans le calque `_e` (un reflet n'est pas une source).
- Rides transversales fines (contraction des muscles), jamais d'anneaux réguliers.

## 4. Mouvement

- **Propagation d'une flexion** (« bend propagation ») : la pieuvre crée une courbe près de la base et la **pousse jusqu'à la pointe** ; une onde d'activation musculaire court juste devant la courbe et rigidifie le bras. Vitesse de pointe mesurée ≈ 30 cm/s. Dans le mod : onde de la base vers la pointe, retard de phase constant par segment (35 à 55°), amplitude croissante vers le bout.
- **Enroulement depuis la pointe**, vers la face des ventouses (les muscles longitudinaux de ce côté gardent les ventouses tournées vers l'intérieur).
- Bras qui bougent **séparément** (déphasage d'un bras à l'autre), jamais en bloc.
- Attaque : le bras se roule (armé), puis se déroule d'un coup, l'onde court jusqu'au bout (fouet), brève tenue, retour.
- Peur, coup : les pointes se roulent serrées, le bras se rétracte.

## 5. Traduction dans le mod

- Tube octogonal : deux cubes à 45° autour de l'axe (comme les os des ailes abyssales), le second à 0,94 du premier ; segments imbriqués qui débordent d'un demi-rayon sur le suivant (continu dans les courbes) ; décalage de 6° d'un segment à l'autre (jamais deux faces parallèles confondues).
- Teinte par face selon l'angle à la face orale : orale, bas du flanc, flanc, haut du flanc (reflets), dos (reflets).
- Ventouse = deux cubes courts (le second tourné de 45° autour de sa normale, 0,12 px plus bas) : disque peint sur la face extérieure, flancs pâles ; diamètre 0,72 × rayon du bras (1,5 px au plus, 0,36 au moins).
- Boucles en Molang (une clé par groupe : sinus de période fermée, `math.pow(math.max(0, sin), 3)` pour une impulsion douce comme l'étirement), animations `once` échantillonnées.

## 6. Pièges

- Coude net, anneaux réguliers, ventouses de taille constante, ventouses sur deux faces : faux.
- Traînées de reflet trop nombreuses : « petits traits » partout (voir l'usure du métal, `retours-en-jeu.md`) ; une par face suffit.
- Bras tous en phase : mécanique, pas vivant.

## 7. Sources

- Wang, Chang et al., « Control-oriented Modeling of Bend Propagation in an Octopus Arm » : https://ar5iv.labs.arxiv.org/html/2110.07211
- « A Sensory Feedback Control Law for Octopus Arm Movements » : https://arxiv.org/pdf/2204.00717
- « Topology, dynamics, and control of an octopus-analog muscular hydrostat » : https://arxiv.org/pdf/2304.08413
- Structure des ventouses (infundibulum, acetabulum, anneau) : https://pmc.ncbi.nlm.nih.gov/articles/PMC4275869 , https://pugno.dicam.unitn.it/NP_PDF/237-RSFS15-octopussuckers.pdf
- Ventouses immatures sur la partie distale : https://hal.sorbonne-universite.fr/hal-03103551v1/document
- Morphologie comparée des bras de céphalopodes : https://tonmo.com/articles/comparative-morphology-of-cephalopod-armature.27/page/continued.1/
