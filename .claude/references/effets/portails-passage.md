# Référence — Portail de passage (ovale de lumière qu'on traverse)

Fiche documentée (2026-11-07, pour `effet_portail`). Étude par analogie d'un portail de retour classique du jeu d'action en vue de dessus (ovale vertical bleu qu'on ouvre, qu'on traverse, qui se referme) : grammaire visuelle, mesures et timing relevés image par image sur deux vidéos de jeu (extraits en 360p, 4 à 8 images/s), couleurs échantillonnées sur les pixels. L'œuvre n'est pas nommée ici ni dans les livrables (règle 5 de `CLAUDE.md`) ; notre version est originale (runes inventées, éclats de pierre, déchirure, sons synthétisés).

## Déroulé observé (plan par plan)

| Temps | Durée mesurée | Ce qu'on voit |
|---|---|---|
| Incantation | ≈ 4 s (barre de progression) | une petite boule bleue tourbillonne dans les mains du lanceur ; d'autres variantes : viseur de glyphes bleus au sol, filets qui s'enroulent autour du corps |
| Départ : flash | 0,12–0,25 s | le lanceur disparaît dans une **sphère blanche** saturée (cœur 255,255,255) au halo bleu, de la taille d'un corps |
| Départ : anneaux | 0,25 s | deux anneaux bleu-blanc **elliptiques et inclinés** tournent autour de la boule qui rétrécit (gyroscope) |
| Départ : extinction | 0,25 s | un voile bleuté, puis plus rien ; aucune trace au sol |
| Arrivée : flash | 0,3 s | sphère blanc-**violet** (lavande) à l'endroit du portail |
| Arrivée : ouverture | 0,15 s | la sphère devient l'**ovale vertical** ; le joueur en sort déjà, devant, entouré d'un filet bleu |
| Portail ouvert | tant qu'il existe | ovale debout, posé presque au sol, bord épais vivant, centre sombre ; il tourbillonne lentement |
| Variante : jet | 0,3 s | sur une autre classe, l'ovale part du lanceur comme une comète (traînée), puis se fige |
| Fermeture (variante) | 0,3 s | l'ovale se contracte en boule bleue, puis disparaît |

## Formes et mesures

- **Ovale vertical** : largeur / hauteur ≈ 0,6 ; hauteur ≈ 1,7 à 2 fois celle du personnage ; le bas frôle le sol.
- **Bord** : anneau épais (≈ 12–15 % du rayon), **plus lumineux d'un côté** (croissant blanc qui tourne), bord extérieur en **flammèches** floues (pas un trait net).
- **Centre** : bleu marine sombre, un peu transparent (on devine le décor), avec un tourbillon à peine plus clair. C'est le contraste centre sombre / bord blanc qui fait lire « passage ».
- Rien d'autre : pas de cadre solide. La lisibilité vient de la silhouette ovale et du contraste.

## Couleurs (échantillonnées)

| Zone | RGB |
|---|---|
| Cœur du bord | 219,236,246 → 226,247,254 (blanc bleuté) |
| Bord, teinte | 159,236,255 (cyan) puis 118,153,250 (bleu clair) |
| Liseré intérieur | 50,97,196 → 44,64,163 |
| Centre | 22,37,93 → 26,47,109 (marine) |
| Flash d'arrivée | blanc, halo lavande ≈ 200,190,255 |

Une seule teinte (bleu) ; le blanc et le marine en sont les extrêmes ; le violet seulement dans le flash.

## Sons (relevés : enveloppe et centroïde spectral par 0,1 s)

- Incantation : bourdonnement doux continu (≈ −27 dB, centroïde ≈ 800 Hz), une note tenue vers 780 Hz.
- Départ : **souffle scintillant aigu** bref (0,4 s, centroïde ≈ 5 kHz), comme un « fwiish » cristallin, puis queue qui s'éteint en 0,5 s.
- Entrée dans le portail : son **tonal** court (0,6 s, pic 890–1030 Hz, décroissance régulière) : chime soufflé.
- Arrivée : **« whoum »** grave et plein (le plus fort, −11 dB, centroïde 1 kHz qui descend à 500 Hz en 0,8 s).
- Rien de métallique ni de percussif : des souffles et des tons doux.

## Traduction dans notre version (`effet_portail`, originale)

- **Différences voulues** : le portail **se déchire** (fente verticale qui s'écarte avec un dépassement) au lieu de naître d'une boule ; **cadre de runes inventées** qui tourne autour de l'ovale ; **éclats de pierre** arrachés au sol qui orbitent ; tunnel en profondeur (anneaux de part et d'autre) ; fermeture en **implosion** (runes et éclats aspirés, point de lumière).
- **Ovale** : tout est dessiné en « espace cercle » (rayon 16 px) dans un groupe mis à l'échelle (1 ; 1,6) par l'animation : une spirale qui tourne dans ce groupe devient un tourbillon elliptique. Runes : position tournée puis étirée, contre-rotation pour rester droites, plaques dessinées 1,5 fois moins hautes.
- **Couleurs** : bord `trans_` blanc-cyan (visible de jour) + `_e` ; centre `trans_` marine semi-opaque (+ `_e` faible) ; spirales et halos en `add_` (cumul ≤ 255 mesuré) ; flash blanc à frange lavande.
- **Sons** (synthétisés, `tools/synthe.py`) : ouverture = déchirure crépitante + souffle qui monte ; passage = chime soufflé vers 900 Hz ; fermeture = aspiration inversée + « whoum » grave. Rien pendant la charge.
- **Joueur** : il marche vers le portail, lévite un peu, puis se réduit vers le centre en le traversant (échelle 1 → 0) ; à l'arrivée, il naît au centre du portail derrière lui, avance et descend jusqu'au sol.

## Sources

- Vidéos de jeu étudiées (extraits basse résolution, gardés hors du dépôt) : un départ et une arrivée vus de dessus (12 s) ; une compilation des variantes par classe (2 min 30 s).
- Wikis de joueurs sur ce portail (apparence, variantes par classe et par ensemble cosmétique) : consultés, non cités pour ne pas nommer l'œuvre.
- [TV Tropes : Thinking Up Portals](https://tvtropes.org/pmwiki/pmwiki.php/Main/ThinkingUpPortals) (grammaire générale du portail).
- Principes FX : `principes-fx-anime.md` (anticipation, ouverture, tenue, fermeture) ; failles : `failles-portails.md`.
