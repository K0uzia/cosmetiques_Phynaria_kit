# Passe de mise au guide actuel (2026-11-08)

Demande de l'utilisateur : repasser toutes les pièces pour les mettre au guide actuel, 3 retouches à la fois au plus, liste validée au fur et à mesure. Procédure : `remise-aux-regles.md`. Pièces refusées (`masque_cuir`, `ailes_cuir`) : laissées telles quelles.

État de départ (vérificateur sur les 61 livrables) : 4 échecs (clés `scale` > 16), 5 pièces avec d'anciennes cachettes `is_in_menu` (inutiles depuis le guide du 2026-11-06 soir), 4 familiers encore portés (pas de mode familier vivant, guide 6.6), presque aucun `apercu/jeu.png`.

Légende : [ ] à faire · [~] en cours · [x] fait (vérificateur vert, livré, planche regardée)

## Lot 1 — échecs du vérificateur (échelle > 16 fois)
- [x] `baguette_patisserie` : `attack/cam_eclat` 18,4 → 13,8 (cube 12× au lieu de 16×), rendu identique
- [x] `lame_givre` : étoile de pointe 20,8 → 15,4 (géométrie ×1,35), rendu identique ; flash d’apparition à voir en jeu
- [x] `pistolet_steampunk` : bouffée 26 → 13, jet du tir 25 → 12,5 (géométrie ×2), rendu identique

## Lot 2 — anciennes cachettes du menu Apparence (`is_in_menu`)
- [x] `ailes_orage` : `1-q.is_in_menu` retiré (décharges, volutes `cam_nuage_*`) ; à voir dans le menu
- [x] `lance_orage` : facteur `1-q.is_in_menu` retiré des décharges ; à voir dans le menu (`/cosmetique apercu`)
- [x] `couronne_orage` : facteur `1-q.is_in_menu` retiré des arcs ; à voir dans le menu

## Lot 3 — familiers en mode vivant (guide 6.6), même apparence
- [x] `familier_steampunk` : familier vivant perché sur l’épaule gauche (s’envole sur son rotor), apparence identique, paupière 20 → 15 ; place perchée à voir en jeu
- [x] `familier_abyssal` : familier vivant en vol (2 blocs, hauteur 1,8), apparence identique (comparaison), plus d’is_in_menu ; hauteur et état à l’arrêt à voir en jeu
- [x] `familier_kawaii_mochi` : familier vivant en vol (2 blocs, hauteur 1,6), apparence identique, humeurs météo gardées, orage boudeur → `event_owner_hurt`

## Lot 4
- [x] `familier_kawaii_chat` : familier vivant en vol (2 blocs, hauteur 1,6), apparence identique, 11 comportements au hasard gardés
- [x] `ailes_kawaii_nuage` : croisement en sneak 4,55 → 2,49 px (épaule 50° → 40°, écart 1,4 px) ; même défaut corrigé en course (3,6 → 2,4)

## Lot 5 — re-livraison des autres pièces (script en tâche de fond, sans agent)
- [x] re-livraison des pièces gardées telles quelles (27 OK : 13 du premier passage + 15 du second ; les pièces à refaire sont sorties de la liste) : `apercu/jeu.png`, fiche et réglages embarqués à jour, vérificateur relancé

## En dernier, à proposer
- [ ] Skins d'objets vivants (guide 14 du 2026-11-06 soir : `item_idle`, `event_swing`, `event_hit`…) sur `skin_epee_givre`, `skin_arbalete_steampunk`, `skin_lance_orage` : ajout de comportements, pas une mise en conformité ; pièces validées en jeu

## Lot 5 bis — pièces sans `.build/<nom>_opt.bbmodel` (livrer.py échoue « introuvable »)
- [x] `ailes_steampunk` regénérée puis livrée ; `ailes_kawaii_papillon` et `ailes_tentacule` sont refaites en R6

---

# Revue de fond demandée le 2026-11-08 (après les re-livraisons)

Demande de l'utilisateur, mot pour mot : « apres les re livraison des 43, tu pensera a améliorer les appariation des petes etc a regarder si tu peut faire mieux et plus logique sur ce qui existe deja revoir les aura sauf la bérénice qui es bien les autre nul, les truc kawaii sont tous bof pas tres beau ou nul surtout la baguette les deux aura et la queue inutile elle, revois les tete et epaule car tu a fait une fixette sru des couronnes et bandeau et les epaule sont jsute moche de ouf sauf la demoniaque qui es bien reussi, le set bérénice es parfait pas besoins d'y toucher pour l'instant normalement mais ca fait pas de mal une vérif,demonique masque a degager, chapeau aussi, bandeau a revoir, tentacule a revoir, la foudre revoir tout meme les ailes je me dit mtn tu peut faire de vrai aile en foudre directement et pas via un espece de matériaux qui forme les ailes jsp,sac a dos cupcake ca degage, baguette surcre aussin dunot aussi, menacnique recvoir tout sauf aile et hibou, ce qui es en arme doit passé en objet peut importe le set, fétiche les tetes a degager, fouet a améliore en animation et sons et tu t'arrete et que ta pas de nouvelle de moi apres 30min tu vois pour completer les sets avec les différents outils armes et ce qu'il manque etc, pense a te renseigner a te baser sur des références etc »

Interprétations (à confirmer par l'utilisateur) : « dégager » = retirer du catalogue en déplaçant le dossier dans `archives/` (réversible, rien n'est effacé) ; « apparitions des petes » = apparitions (`event_equip`, `event_teleport`) des familiers (« pets ») et des pièces en général ; « arme → objet » = refaire la pièce en skin d'objet (guide 14), l'arme portée est retirée quand un skin du même set existe déjà.

Méthode : une pièce par agent, jusqu'à 10 à la fois (accord de l'utilisateur, nuit du 2026-11-08) ; brief commun `brief-revue-2026-11-08.md` ; refonte = recherche de références d'abord (`/bbmodel-cosmetic`, approche par analogie), comparaison avec l'ancienne version, rien de validé ne change sans raison.

## R1 — retirer (archives/)
- [x] `masque_abyssal`, `chapeau_abyssal` (démoniaque)
- [x] `sac_patisserie` (sac cupcake), `baguette_patisserie`, `halo_patisserie` (donut)
- [x] `queue_kawaii` (« inutile »)
- [x] `masque_cuir`, `harnais_tete_cuir` (têtes du set Fétiche)
- [x] `lame_givre`, `lance_orage` : armes portées en double d'un skin d'objet existant (`skin_epee_givre`, `skin_lance_orage`)

## R2 — armes → skins d'objets (guide 14, skins vivants)
- [x] `lames_abyssales` → `skin_epee_abyssal` « Croc de l'Abysse » (sabre courbe, vivant) ; sens du tranchant en 3e pers. à juger
- [x] `pistolet_steampunk` → `skin_arc_steampunk` « Pistolet à vapeur » (bander = monter en pression, tir = jet de vapeur) ; visée à voir en jeu
- [x] `fouet_cuir` → `skin_canne_cuir` « Fouet de cuir verni » (vague, claquement, son embarqué) ; événements et son à voir en jeu

## R3 — Orage, tout revoir
- [x] `ailes_orage` (v6 faites de foudre : canal-éclair, nœuds de plasma, 9 ramifications) : de vraies ailes faites de foudre, pas un matériau en forme d'ailes
- [x] `aura_orage` (v2 feu de Saint-Elme : couronne de filaments, éclairs aux extrémités ; traits fins à juger de loin)
- [x] `couronne_orage` → `casque_orage` (casque à lamelles, cimier-éclair, arcs au hasard)
- [x] `skin_lance_orage` : re-livré, vérificateur vert (validé en jeu, inchangé)

## R4 — auras (sauf Bérénice)
- [x] `aura_abyssale` (v3 tout en lumière : crocs, veines, sceau au sol) · [x] `aura_brasier` (v4 braise : palette or→rouge, braises qui montent, sol fendu ; risque « mec en feu » de nuit à juger) · [x] `aura_givre` (rosace, piliers de lumière, givre au sol) · [x] `aura_kawaii` (v3 cœur de sucre qui bat, gloire de nuage, cœurs au sol) · [x] `bulle_kawaii` (v3 grappe de bulles qui gonflent et éclatent, rond de bulles au sol)

## R5 — têtes et épaules (fini les couronnes et bandeaux ; garder `epaulieres_abyssales`)
- [x] `bandeau_abyssal` → `cornes_abyssales` (cornes qui sortent du crâne, racines d'os, demi-masque) · [x] `couronne_givre` → `ramure_givre` (bois de cristal) · [x] `oreilles_kawaii` → `capuche_kawaii` « Capuche lapin-nuage » (de dos : gros volume lilas, à juger) · [x] `chapeau_patisserie` → `beret_patisserie` « Béret tartelette » (se lit surtout comme une tarte posée : à juger) · [x] `haut_de_forme_steampunk` (calotte ronde, machine logique, lunettes qui basculent en sneak)
- [x] `epaulieres_givre` (v2 écailles de glace + cristaux) · [x] `epaulieres_steampunk` (lames en éventail, chaudière et manomètre qui déchargent) · [x] `epaulettes_patisserie` → « Épaulettes fraise chantilly » (glaçage coulant, sablés, chantilly, fruits) · [x] `harnais_cuir` (v3 harnais en H/X, anneaux chromés, épaulières de latex, cadenas)

## R6 — autres refontes
- [x] `ailes_tentacule` (vraie paire, 3 tentacules par côté, ventouses, œil d'ambre)
- [ ] Steampunk sauf ailes et hibou : [x] `queue_steampunk` (colonne à rotules et câbles, empennage, décharge de vapeur), `skin_arbalete_steampunk` (re-livré, vert, inchangé) (+ haut-de-forme et épaulières en R5)
- [ ] Kawaii : [x] `ailes_kawaii_nuage` (aile de chérubin chibi : nuage blanc, couvertures framboise, rémiges lilas), [x] `ailes_kawaii_papillon` (vraie aile de papillon, nervures, cœurs, éclosion) (+ auras R4, oreilles R5)

## R7 — apparitions et logique
- [x] apparitions des familiers (renard : tourbillon de neige ; crâne : se reforme depuis sa flamme ; mochi : se condense ; lanterne : se déplie et s'allume ; hibou : arrive sur son rotor et se pose ; bug rotor ×25 corrigé) (`event_equip`, `event_teleport`) et des pièces : plus belles, plus logiques
- [x] Bérénice : vérification seulement — ailes, diadème OK ; aura : `reglages.json` Durée 2 s (hors pas) et Rafale « À l'attaque » à corriger ; effet : saut de pose charge→départ (charge 4 s vs compte à rebours 3 s) et cocon `trans_` qui peut cacher l'`add_` : **propositions à soumettre à l'utilisateur, rien modifié**

## Puis s'arrêter. Sans nouvelles après 30 min : compléter les sets
- [ ] outils, armes (skins d'objets) et pièces manquantes par set, d'après des références


## Suivi coordinateur
Planches et comparaisons regardées pour chaque [x]. Tout R1–R7 fait le 2026-11-08 (nuit). Ensuite : s'arrêter ; sans nouvelles de l'utilisateur 30 min après, compléter les sets (outils, armes en skins d'objets, pièces manquantes).

# Compléter les sets (lancé le 2026-11-08 vers 5 h 10, sans nouvelles de l'utilisateur 30 min après le bilan)

Inventaire au départ : Abyssal (ailes, aura, cornes, épaulières, familier, queue, épée) · Givre (ailes, aura, ramure, épaulières, familier, effet, épée) · Orage (ailes, aura, casque, lance) · Steampunk (ailes, haut-de-forme, épaulières, queue, hibou, arbalète, arc) · Kawaii (2 ailes, aura, bulle, capuche, 2 familiers) · Pâtisserie (béret, épaulettes) · Cuir (harnais, fouet-canne). Bérénice : ne pas toucher (« pas besoin d'y toucher pour l'instant »). Têtes du set Cuir : ne pas en refaire (« à dégager »).

Lot C1 — skins d'objets (un par agent, 10 à la fois) :
- [x] `skin_pioche_steampunk` « Pic à vapeur » · [x] `skin_bouclier_givre` « Écu de givre » · [x] `skin_arc_givre` « Arc de givre » · [x] `skin_masse_orage` « Marteau du tonnerre » (note : Display de la masse dans tools/objet.py = celui de l’épée, à corriger) · [x] `skin_hache_abyssal` « Mâchoire de l’Abysse »
- [x] `skin_arc_kawaii` « Arc de guimauve » · [x] `skin_masse_patisserie` « Fouet chantilly » (fouet ballon plutôt que rouleau) · [x] `skin_pelle_patisserie` « Pelle à tarte nappée » · [x] `skin_bouclier_cuir` « Rondache de latex » (blocage refait en Molang : à voir en jeu) · [x] `skin_hache_orage` « Hache de l’orage » (frange blanche du fil sans animation : à juger)

Idées pour la suite (non lancées) : familier Orage, épaulières Orage, effet de téléportation Abyssal / Orage / Steampunk / Kawaii, ailes et aura Pâtisserie, pioches et pelles des autres sets.

Lot C1 terminé (10/10 livrés, planches regardées). Arrêt volontaire ensuite : contexte du coordinateur trop chargé (règle contexte-agents.md) ; les idées ci-dessus restent à lancer dans une nouvelle session, après l'avis de l'utilisateur.

Suite (2026-11-08, matin) : sets complets en objets, ailes orage v7 et corrections Bérénice → `sets-objets-2026-11-08.md`.
