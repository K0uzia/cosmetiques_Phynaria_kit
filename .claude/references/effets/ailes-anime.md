# Référence — Ailes façon anime

Fiche documentée (2026-11-04). Complète `.claude/styles/ailes-anatomie.md` (attache, squelette, repli en Z, taille, langage des ailes) sans le répéter : ici, les **codes visuels de l'anime** par type d'aile et la mise en scène. La biomécanique et les états restent ceux de `.claude/rules/animation.md`.

## Codes visuels

- **Les ailes disent qui on est** (trope « Good Wings, Evil Wings ») : plumes blanches = ange, pureté ; plumes noires = ange déchu, deuil, menace ; membrane de chauve-souris = démon, vampire ; insecte = fée, féerie, fragilité ; énergie = puissance pure (bonne ou mauvaise), toujours à code couleur ; mécanique = invention, armure. **Mélanger** (une blanche et une noire, plumes qui deviennent membrane) dit le conflit intérieur.
- **Nombre et taille** : une paire = être ailé ; deux ou trois paires empilées = rang élevé, divin ; une seule aile = être incomplet, déchu. Les ailes de puissance sont souvent **démesurées** dans l'anime ; chez nous, la taille reste celle de `ailes-anatomie.md` (52 à 70 px déployées).
- **Ailes d'énergie et ailes « stationnaires »** : les ailes de lumière n'ont pas besoin de battre ; elles flottent derrière le dos, légèrement décollées, et ondulent. C'est l'exception qui permet un mouvement non biomécanique.
- **Mue perpétuelle** : les ailes de plumes de l'anime perdent toujours quelques plumes, surtout à l'envol ou au déploiement : pluie de plumes qui tournoient.

## Types d'aile

| Type | Forme | Couleur | Mouvement | Construction dans le dépôt |
|---|---|---|---|---|
| Plumes d'ange | rangées nettes et rondes, primaires longues en éventail | ivoire, ombre champagne, pointe or doux ; cœur lumineux près de l'os | ample, lent, majestueux | `ailes_berenice` (peau + âme, validée « la rondeur est bien ») |
| Plumes sombres | mêmes rangées, plumes plus effilées, bord déchiré | noir bleuté, reflet violet ou vert peint, liseré clair fin | plus nerveux, frémissements | même recette ; contraste par liseré peint, sinon masse noire illisible |
| Membrane démoniaque | doigts longs, membrane tendue, griffe au pouce, bord festonné | membrane sombre aux veines contrastées, lumière qui passe au travers | battement puissant, repli serré | `ailes_abyssales` (validée « juste incroyable ») |
| Énergie, lumière | plumes ou lames de lumière sans os, décollées du dos | cœur presque blanc → teinte, bord net | flottent, ondulent, pulsent ; battement lent ou absent | `add_` + double `trans_`, racine cachée, pas de contact avec le dos |
| Cristal | éclats prismatiques en éventail, facettes | translucide, arêtes blanches, cœur coloré | rigide, pivote par éclat, scintille | `ailes_givre` (`trans_`, âme opaque fine) |
| Fée, insecte | deux paires, contour fin, nervures, très peu d'épaisseur | translucide irisé (bleu → vert → rose vers la pointe), nervures plus foncées | vibration rapide (8–12 Hz, irréalisable : faire un tremblé de 0,1 s), peu de repli | `trans_` alpha 60–160, nervures peintes ; voir aussi `ailes_kawaii_papillon` (construction à relire avant de la reprendre) |
| Mécanique | longerons, lames d'éventail, pivots, vérins | métal propre, lumières nettes | « saccadé réaliste » par paliers | `ailes_steampunk` (validée pour la taille et les couches) |

## Mouvement et timing

- **Déploiement dramatique (le plan-signature)** : les ailes poussent depuis les omoplates, s'ouvrent **rangée par rangée**, les primaires se séparent en dernier ; le tout dans un coup de vent, avec une pluie de plumes. Découpage : 0,2 s d'anticipation (épaules qui se ramassent, ailes encore serrées), 0,3 s d'ouverture brusque (dépassement de 5–10° au-delà de la pose), 0,5–1 s de stabilisation, plumes qui tombent pendant 2–3 s.
- **Envol** : un battement très ample vers le bas (0,3 s), puis remontée poignet replié ; plumes lâchées au premier coup.
- **Poses anime** : ailes grandes ouvertes **en V relevé** derrière le personnage (puissance, révélation) ; **enveloppantes** autour du corps (protection, cocon) ; **tombantes** jusqu'au sol (défaite, fatigue) ; **une aile repliée en bouclier** devant (défense).
- **Ailes d'énergie** : décollées de 1 à 3 px du dos, ondulation 2–4 s, chaque plume déphasée de 0,1–0,2 s ; scintillements le long du bord.
- Cadence : l'anime anime les ailes de puissance assez lentement (sur 2 ou 3) avec des poses tenues ; chez nous, garder la biomécanique d'`animation.md` et réserver les poses tenues au déploiement.

## Traduction dans le mod

- **Apparition** : `event_equip` (pousse depuis le dos, ouverture rangée par rangée, dépassement puis stabilisation) ; retrait `event_unequip` ≤ 5 s, fini par `ctrl_alpha` −1 ou échelle 0.
- **Pluie de plumes** : `particle_plume` (un cube de 0,3 px, face `up` seule, courbure peinte, y ≥ 0,3 au-dessus du pivot), `emit_plume` aux pointes des primaires ; animation `particle_plume_fall` qui tournoie ; Rafale « Au saut » ou `ctrl_emit` à +4 pendant le déploiement et l'envol, −1 le reste du temps pour ne pas faire de « mue » continue. Les plumes qui tombent et se posent : **sur les ailes seulement**.
- **Ailes d'énergie** : groupes `add_` pour le cœur, `trans_` pour la forme (seule visible avec shader) ; pas de calque `_e` si tout est additif ; mesurer le cumul ≤ 255 là où les plumes se recouvrent (les plumes d'énergie se chevauchent beaucoup).
- **Fée, insecte** : `trans_` sur des plaques à une seule couche ; deux paires décalées de 0,8 px en profondeur ; tremblé en `overlay_` (±3° à 0,1 s, *linear*) seulement en vol ; reflet irisé peint (les reflets `_r` sont retirés).
- **Ailes sombres** : éviter la masse noire uniforme ; liseré clair de 3–4 texels, reflet coloré peint sur le rachis, lueur `_e` fine dans les veines (pièce non additive).
- **Réaction aux virages** : `q.yaw_speed` lissé (`v.x = math.lerp(...)`) pour incliner les ailes dans les virages.

## Avec shader

Plumes et membranes opaques restent visibles ; les lueurs `_e` et `add_` disparaissent. Ailes d'énergie : la forme `trans_` doit à elle seule dessiner l'aile. Ailes de cristal et de fée en `trans_` : visibles (validé sur Givre).

## Pièges

- Plaques seules : « tas de feuilles » par la tranche ; cubes pleins seuls : « trop carré » (`modeling.md`, peau + âme).
- Âmes qui dépassent des lames voisines : clipping (`ailes_steampunk`, grille de 0,2 px).
- Ailes d'énergie collées au dos par une plaque : on voit la jonction ; les décoller et cacher la racine dans un éclat.
- Pluie de plumes continue : lourde, et coûteuse avec 3 cosmétiques ; la réserver aux moments forts.
- Ailes démesurées « comme dans l'anime » : au-delà de 60 px par axe, refusé par nos règles ; le dire.
- Plumes de 1,4 px ou plus en particule : se voient comme de gros objets loin du joueur.

## Sources

- [TV Tropes : Good Wings, Evil Wings](https://tvtropes.org/pmwiki/pmwiki.php/Main/GoodWingsEvilWings) et [Tropedia](https://tropedia.fandom.com/wiki/Good_Wings,_Evil_Wings)
- [TV Tropes : Power Gives You Wings, anime et manga](https://www.tvtropes.org/pmwiki/pmwiki.php/PowerGivesYouWings/AnimeAndManga)
- [TV Tropes : Stationary Wings](https://tvtropes.org/pmwiki/pmwiki.php/Main/StationaryWings)
- [TV Tropes : Perpetual Molt](https://www.tvtropes.org/pmwiki/pmwiki.php/Main/PerpetualMolt) et [Tropedia : Feather Motif](https://tropedia.fandom.com/wiki/Feather_Motif)
- [TV Tropes : Hot Wings](https://tvtropes.org/pmwiki/pmwiki.php/Main/HotWings), [Razor Wings](https://www.tvtropes.org/pmwiki/pmwiki.php/Main/RazorWings)
- [Dessiner des ailes de fée (nervures, translucidité, irisation)](https://craftwhack.com/how-to-draw-fairy-wings/)
- [SIGGRAPH : effets d'ailes de cinématiques de jeu (ailes de lumière)](https://history.siggraph.org/?p=139820)
- Fiche interne : `.claude/styles/ailes-anatomie.md`
