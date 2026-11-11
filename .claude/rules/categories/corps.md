---
paths:
  - "cosmetiques/queues/**"
  - "cosmetiques/epaules/**"
  - "cosmetiques/sacs/**"
  - "cosmetiques/armes/**"
  - "cosmetiques/outils/**"
  - "cosmetiques/blocs/**"
---

# Queues, épaules, sacs, armes, outils, blocs — règles et avis

Réactions (`animation.md`, « Attaque et blessé ») : queues, épaules, sacs : ni `attack` ni `hurt` ; armes : `attack` seul (c'est l'objet qui frappe) ; outils, blocs : libres. Queues : les 10 états hors `attack` et `hurt`.

Distances (détail : `.claude/references/procedures/remise-aux-regles.md`) : pièces de corps (platine de queue, brassard) à ≥ 2,37 px du centre du torse ou de l'axe du bras (seconde couche du skin à 2,25) ; pièce posée sur l'épaule à y ≥ 24,35 (seconde couche du bras à 24,25). Deux armes animées ensemble : mesurer la distance entre les bras pendant l'attaque. Collier : dans `body` en haut du torse (`categories/tete.md`, Ensemble Cuir v1). Chaîne, laisse, pendentif et pièce posée sur le corps : `retours-en-jeu.md`, Recettes.

## Avis de l'utilisateur

| Pièce | Avis | À retenir |
|---|---|---|
| `queue_abyssale_v1` | « trop dragon, créature » | Vertèbres, épines et membrane font bête ; pour un ensemble d'allure élégante, préférer `queue_abyssale` |
| `epaulieres_givre` v1 → v2 (2026-11-08) | v1 « moche » (« sauf la démoniaque qui est bien réussie ») ; v2 pas encore vue en jeu | Coque d'argent à dentelle : abat-jour. v2 : écailles de glace en coque + jupe autour du bras, cristaux qui montent, d'après `epaulieres_abyssales` (`.claude/styles/givre.md`, Épaulières v2) |
| `epaulieres_steampunk` v1 → v2 (2026-11-08) | v1 « moche de ouf » (bloc doré qui entourait le bras) ; v2 **pas encore vue en jeu** | Lames d'épaulière à arête médiane (langage des lames des ailes Steampunk : acier / laiton / cuivre alternés), rang haut sur l'épaule + jupe de lames en cône autour du bras, moyeu à engrenage, cheminées (droite) et manomètre (gauche) qui montent au-dessus de l'épaule, d'après `epaulieres_abyssales` (`.claude/styles/steampunk.md`, Épaulières v2) |
| `epaulettes_patisserie` v1 → v2 (2026-11-08) | v1 « moche de ouf » (guimauve à visage posée sur l'épaule) ; v2 « Épaulettes fraise chantilly » **pas encore vue en jeu** | Nappage fraise qui coule sur l'épaule + tuiles de pâte sablée sur le flanc du bras, chantilly pochée (anneaux sur plaques croisées), fraise, cerise, rubans de chocolat noués, d'après `epaulieres_abyssales` (`.claude/styles/patisserie.md`, Épaulettes v2) |
| `harnais_cuir` v2 → v3 (2026-11-08) | v2 (sangles en X fines, collier, laisse, ceinture, bracelets à chaînes) : épaules « moches de ouf » ; v3 pas encore vue en jeu | Harnais de torse réel (bretelles, barre de poitrine à deux anneaux en O, X dans le dos, sangles sous les bras), épaulières de latex moulé à joncs chromés, brassards, cadenas `phys_…_g100` ; latex = noir + un reflet blanc net et étroit (`.claude/references/objets/harnais.md`) |
| `queue_steampunk` v3 (2026-11-08) | Pas encore vue en jeu (refonte après « mécanique revoir tout sauf aile et hibou ») | Colonne à câbles : 9 cloisons de laiton sur rotules d'acier, 4 câbles de cuivre enroulés par les tambours du boîtier, 2 vérins télescopiques calculés, empennage en losange + buse. Onde progressive fluide (retard croissant vers la pointe), décharge à 16 s sur 20 s. À juger : lisibilité à 10 blocs, lumière du témoin de nuit |
