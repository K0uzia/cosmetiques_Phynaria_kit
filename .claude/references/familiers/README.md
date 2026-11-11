# Références : familiers

Fiches documentées par recherche (2026-11-05), après le retour en jeu sur `familier_givre` v2 (« assemblage de formes », « grands carrés », « un familier ne vole pas forcément »). Elles complètent `.claude/styles/familiers.md` (principes, Molang de hasard, recette du familier au sol), qui reste la règle, et les fiches d'animaux (`../animaux/`) et de créatures (`../creatures/`).

| Fiche | Contenu |
|---|---|
| [types-familiers.md](types-familiers.md) | Ce que peut être un familier (folklore, anime, jeu) : animal réel, familier de sorcière, animal-esprit, spectre, shikigami, mascotte magique, élémentaire, mini-dragon, fée, golem, objet animé ; placements possibles dans le mod ; arbre de décision type → placement → états |
| [familiers-cosmetiques-jeux.md](familiers-cosmetiques-jeux.md) | WoW, FFXIV, MapleStory, Fortnite, Pokémon, Roblox, Minecraft et ses serveurs, Petlings : ce que les joueurs aiment (réactions, vie au repos, contact), ce qu'ils reprochent (encombrement, bruit), taille et animations attendues |
| [modelisation-organique.md](modelisation-organique.md) | Animal en cubes qui ne fait pas assemblage : silhouette, sections arrondies par paliers, emboîtement, peinture en espace monde, mèches couchées, visage, pattes en zigzag, courbes, budget de texels et de cubes |

## À retenir

- **Le type décide du placement** : terrestre au sol à côté, volant perché, magique en lévitation, minuscule porté. Un animal qui flotte sans cause visible est un défaut.
- **Depuis le 2026-11-05, le mod a un mode familier** (guide 6.6) : un bloc `familier` (`sol`, `vol`, `nage`, `perche`) le fait suivre le joueur sur le vrai sol, avec ses animations `pet_`. C'est la règle (`.claude/styles/familiers.md`) ; l'ancienne recette (dans `body`, pieds à y = 0, contre-rotation du torse, saut vers l'épaule par `event_enter_*`) n'est plus qu'un repli pour les pièces portées.
- **Organique** = masses imbriquées + peinture continue (zones, dégradé, occlusion, sens du poil) + peu de mèches couchées + visage construit.
