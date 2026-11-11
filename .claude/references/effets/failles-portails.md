# Référence — Failles, déchirures du ciel, portails

Fiche documentée (2026-11-06, pour `effet_admin`). Codes génériques de la « déchirure du ciel » et du portail d'anime ; aucun design d'une œuvre n'est repris (règle 5 de `CLAUDE.md`). Une inspiration donnée par l'utilisateur sert à cerner l'ambiance ; elle n'est pas nommée ici.

## Codes visuels

- **Le ciel est une surface** : la scène marche parce que le ciel, normalement infini, se comporte comme du verre ou du papier qui se fend. Lignes de fracture, éclats qui tombent, bords qui se retroussent.
- **Un vide derrière** : noir ou indigo profond, souvent avec étoiles, nébuleuse ou motifs (grille, rouages, cadrans) qui disent « un autre lieu ». Le contraste vide sombre / bord incandescent fait toute la lecture.
- **Bord vivant** : le bord brille (blanc au cœur, teinte au liseré), crépite, avance par à-coups dentelés. Une ellipse lisse se lit comme un portail ; un bord dentelé, comme une déchirure.
- **Échelle** : la faille est plus grande que tout ce qui l'entoure, et ce qui en sort aussi. Une présence colossale (projection, silhouette géante) qui se réduit ensuite à taille humaine dit « maître des lieux ».
- **Direction** : amande horizontale (œil qui s'ouvre, « le ciel s'ouvre »), fente verticale (porte), étoile (impact).
- Familles : faille de **vide** (noir, étoiles), **temporelle** (cadrans, horloges, glyphes figés, éclats qui flottent), **numérique** (grille, pixels), **démoniaque** (rouge, chair).

## Timing (anime)

| Temps | Durée | Ce qui se passe |
|---|---|---|
| Anticipation | 0,3–0,8 s | ciel qui s'assombrit ou vibre, fêlures qui courent, grondement |
| Ouverture | 0,4–0,8 s | la fente s'écarte avec un léger dépassement, éclair, éclats projetés |
| Révélation | 0,5–1,5 s | ce qui est derrière apparaît (silhouette, géant) ; tenir l'image |
| Sortie, descente | 0,6–1,2 s | mouvement qui accélère vers le sol |
| Impact | 0,1–0,3 s | onde de choc, poussière, fêlures au sol, flash |
| Fermeture | 0,3–0,6 s | la faille claque, cicatrice lumineuse qui s'éteint |

## Couleurs

Cœur blanc teinté, teinte du bord (cyan, violet, or, rouge selon la famille), vide presque noir de la même famille. Une seule couleur vive.

## Traduction dans le mod

- **Faille dressée face à celui qui regarde** : plaques dans un groupe `camy_`, reculées en z local négatif (derrière le joueur sous tous les angles) ; ouverture par l'échelle (x, y) du groupe, dépassement de 6 %.
- **Vide opaque** (alpha 255) : visible de jour sans additif ; étoiles dans `_e` pour la nuit. Bord en `trans_` blanc-cyan + `_e` léger, lueur `add_` floue **fenêtrée au bord de la plaque** (sinon un rectangle se voit).
- **Fêlures** : traits ramifiés qui partent de la ligne d'ouverture (sinon, faille fermée, ils flottent détachés) ; une branche qui sort de la plaque est raccourcie, jamais écrasée contre le bord (trait droit visible).
- **Éclats** : cubes de 0,3 px à deux faces (ciel / vide), tranches transparentes ; leur chute s'arrête au-dessus du sol une fois cachés (sinon le vérificateur mesure plus de 200 px d'extension).
- **Géant** : groupe vide `joueur` (guide 15 : position et échelle, hors limite des 64 px). Torse au cœur de la faille : pieds à y = YF − 18 × échelle.
- Limite : 64 px par axe pour les cubes ; la faille tient sous y = 60.

## Sources

- [TV Tropes : Thinking Up Portals](https://tvtropes.org/pmwiki/pmwiki.php/Main/ThinkingUpPortals) (portails entre deux lieux)
- [TV Tropes : Apocalypse Wow](https://tvtropes.org/pmwiki/pmwiki.php/Main/ApocalypseWow) (ciel qui se fend, échelle du spectacle)
- [80.lv : effet de portail qui brise la réalité](https://80.lv/articles/a-reality-breaking-portal-effect-made-in-unity) et [HitFilm : « dimension rift »](https://www.manula.com/manuals/fxhome/hitfilm-pro/7/en/topic/dimension-rift) (couches : vide, bord, distorsion)
