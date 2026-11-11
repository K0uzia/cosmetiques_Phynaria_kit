# Demandes au mod (4) — réglages des particules, interface, familiers apprivoisés, guide complet

Tu travailles sur le mod Phynaria Utilities. Ce document contient quatre demandes, du 2026-11-05, et un retour sur la demande 3.

**Merci pour le correctif des shaders (demande 3, §5)** : vu en jeu le 2026-11-05 vers 20 h avec Complementary Unbound + Euphoria Patches, l'ensemble de Bérénice (ailes, diadème, aura) s'affiche bien : halo et rayons `add_`, lueurs du calque `_e` sur les plumes, anneau au sol, particules (captures `2026-11-05_20.00.55`, `20.00.58`, `20.01.07`, `20.01.10`).

## Résumé

| # | Demande | Ce que ça débloque | Priorité |
|---|---|---|---|
| 1 | À l'import, lire les réglages des particules écrits dans le `.bbmodel` et **pré-remplir** les fenêtres de réglages | Le staff n'a plus à recopier 6 à 14 valeurs par sorte de particule ; moins d'erreurs ; même rendu sur tous les serveurs | Haute |
| 2 | **Interface** : textes coupés partout, descriptions coupées dans la boutique, aucune description ni lore dans *Apparence* ; quitte à refaire une meilleure interface (section 6) | Les joueurs voient ce qu'ils achètent et ce qu'ils portent ; le lore des ensembles sert enfin | Haute |
| 3 | **Familiers « apprivoisés »** : le familier devient une entité qui vit autour du joueur et le suit, comme un loup apprivoisé, au lieu d'être collé au torse (section 7) | Familiers crédibles : ils marchent sur le vrai sol, ne flottent plus dans le vide, ne rentrent plus dans le sol en accroupi | Haute |
| 4 | **Renvoyer le guide complet à jour** : tout le fonctionnement des cosmétiques et de l'interface du mod, dans la version livrée (section 8) | Nous travaillons d'après le guide : ce qui n'y est pas, nous le devinons (les sons embarqués, par exemple, ont été lus dans le `.jar`) | Haute |

---

## 1. Contexte

Aujourd'hui, après la fenêtre *Catégorie et animations*, une fenêtre par sorte de particule demande au staff *Quand*, *Nombre*, *Durée*, *Mouvement*, *Au sol*, *Rendu*, *Sens*, *Fin de vie*, *Départ*, *Dispersion*, *Élan*, *Variation*, *Rafale*, *Limite* (guide, section 5 ter §5). Ces valeurs sont décidées par le créateur du modèle, en même temps que la forme de la particule : une vapeur doit **monter** en **translucide** avec un **fondu**, une plume **tomber**, **se poser**, **rétrécir**. Nous les livrons dans un fichier à part (`reglages.json`), que le staff recopie à la main : 27 cosmétiques ont des particules, jusqu'à 3 sortes chacun.

## 2. Où sont les réglages dans le fichier

Dans un objet **`unhandled_root_fields.phynaria`** à la racine du `.bbmodel`.

Pourquoi là : Blockbench efface toute clé qu'il ne connaît pas, à la racine comme dans `meta`, quand on ouvre puis enregistre le fichier (`compile()` de `js/formats/bbmodel.js` reconstruit le modèle). `unhandled_root_fields` est une propriété du projet (`ModelProject`, `js/io/project.ts`, type `object`, sans condition) : Blockbench la lit à l'ouverture et la réécrit telle quelle à l'enregistrement. Le staff ou un graphiste peut donc retoucher le modèle dans Blockbench sans perdre les réglages. (Vérifié dans le code source actuel de Blockbench ; une très vieille version de Blockbench pourrait encore les perdre.)

```json
{
  "meta": { "format_version": "4.10", "model_format": "free", "box_uv": false },
  "unhandled_root_fields": {
    "phynaria": {
      "version": 1,
      "particules": {
        "plume": {
          "quand": "vol", "nombre": 1, "duree": 6, "mouvement": "legere", "au_sol": "pose",
          "rendu": "opaque", "sens": "libre", "fin_de_vie": "retrecit", "depart": "poussee",
          "dispersion": 15, "elan": 40, "variation": "legere", "rafale": "aucune", "limite": 64
        },
        "mc_white_smoke": {
          "quand": "toujours", "nombre": 2, "depart": "lent", "dispersion": 15, "rafale": "aucune", "limite": 64
        }
      }
    }
  },
  "elements": [], "outliner": [], "textures": [], "animations": []
}
```

- **Clé d'une sorte** : le nom après `particle_` pour une particule modélisée (`particle_plume` → `plume`, ses points `emit_plume`, `emit_plume2`…), `mc_<id>` pour une particule de Minecraft (`emit_mc_white_smoke` → `mc_white_smoke`, `emit_mc_dust_ff2040_15` → `mc_dust_ff2040_15`). C'est le nom du groupe `emit_` sans `emit_` (ni le chiffre final pour une particule modélisée).
- **Valeurs** : des identifiants stables, en minuscules, sans accent (pas les libellés affichés, qui peuvent changer ou être traduits), et des nombres pour les réglages chiffrés.
- **`version`** : 1. Si un jour la forme change, nous passerons à 2.

## 3. Correspondance complète

| Clé | Réglage | Valeurs | Défaut (guide) | Particules Minecraft |
|---|---|---|---|---|
| `quand` | Quand | `vol` En vol, `air` En l'air, `mouvement` En mouvement, `arret` À l'arrêt, `toujours` Toujours, `pluie` Sous la pluie, `jamais` Jamais | `vol` | oui |
| `nombre` | Nombre | nombre de 0,5 à 10 (par seconde) | `2` | oui |
| `duree` | Durée | nombre de 1 à 20 (secondes) | `6` | non |
| `mouvement` | Mouvement | `legere` Légère, `normale` Normale, `lourde` Lourde, `flotte` Flotte, `monte` Monte | `legere` | non |
| `au_sol` | Au sol | `pose` Se pose, `disparait` Disparaît | `pose` | non |
| `rendu` | Rendu | `opaque` Opaque, `lumineux` Lumineux, `translucide` Translucide | `opaque` | non |
| `sens` | Sens | `libre` Libre, `camera` Face caméra | `libre` | non |
| `fin_de_vie` | Fin de vie | `retrecit` Rétrécit, `fondu` Fondu | `retrecit` | non |
| `depart` | Départ | `poussee` Poussée, `lent` Lent, `moyen` Moyen, `rapide` Rapide | `poussee` | oui |
| `dispersion` | Dispersion | `0`, `15`, `45`, `180` (degrés) | `15` | oui |
| `elan` | Élan | `0`, `40`, `100` (pour cent) | `40` | non |
| `variation` | Variation | `aucune` Aucune, `legere` Légère, `forte` Forte | `legere` | non |
| `rafale` | Rafale | `aucune` Aucune, `attaque` À l'attaque, `blesse` Blessé, `saut` Au saut, `atterrissage` À l'atterrissage | `aucune` | oui |
| `limite` | Limite | `64`, `128`, `256` (particules par joueur) | `64` | oui |

Nombres : entier ou décimal JSON (`1`, `2.5`). Si ton curseur a des crans (par exemple 0,5 / s pour *Nombre*), prends le cran le plus proche.

## 4. Comportement attendu

1. **À l'import**, pour chaque sorte de particule trouvée, la fenêtre de réglages s'ouvre comme aujourd'hui, mais **pré-remplie** avec les valeurs du fichier. Le staff peut tout corriger avant de valider. Il ne doit pas y avoir d'import « silencieux » : la fenêtre reste affichée.
2. **Réglage absent** (ou pas de `phynaria` du tout) : la valeur par défaut d'aujourd'hui, sans message.
3. **Valeur inconnue** (identifiant inconnu, nombre hors bornes, mauvais type) : la valeur par défaut (ou, pour un nombre, la borne ou le cran le plus proche), **et une ligne dans le rapport d'import** : `particule plume : quand = "volant" inconnu, défaut « En vol »`.
4. **Clé de sorte sans particule correspondante** dans le modèle, ou **clé de réglage inconnue** : ignorée, une ligne dans le rapport d'import.
5. **Particule Minecraft** : seuls `quand`, `nombre`, `depart`, `dispersion`, `rafale`, `limite` sont lus ; les autres clés sont ignorées sans message (ce sont celles que la fenêtre ne demande pas).
6. La roue dentée (changement des réglages sans réimporter) reste la même : les valeurs du fichier ne servent qu'à l'import. *Facultatif* : un bouton « Reprendre les réglages du fichier » dans cette fenêtre.
7. Une ligne dans le rapport d'import par sorte réglée depuis le fichier : `particule plume : réglages lus dans le modèle (14)`.

## 5. Ce que nous avons déjà fait

- Tous nos cosmétiques à particules embarquent déjà ces réglages (`unhandled_root_fields.phynaria`, version 1), écrits par notre outil de livraison et contrôlés par notre vérificateur. Un mod qui ne les lit pas les ignore : rien ne casse aujourd'hui.
- Pour un test : `cosmetiques/ailes/ailes_berenice/ailes_berenice.bbmodel` (1 sorte modélisée, `plume`), `cosmetiques/ailes/ailes_orage/ailes_orage.bbmodel` (1 modélisée + 1 Minecraft, `mc_electric_spark`), `cosmetiques/familiers/familier_givre/familier_givre.bbmodel` (3 sortes).
- Une fois fait, merci d'ajouter une ligne au guide (section 5 ter §5 et section 10, étape 3), avec la syntaxe définitive si tu en choisis une autre.

## Format écarté : suffixes dans le nom du groupe `emit_`

Comme `phys_queue_r40_a60`, on aurait pu écrire `emit_plume_qvol_n1_d6…`. Écarté : 14 réglages ne tiennent pas lisiblement dans 64 caractères, un chiffre final sert déjà à numéroter les points (`emit_plume2`) et fait partie du nom de la particule pour `emit_mc_<id>`, et il faudrait répéter les réglages sur chacun des 32 points possibles (avec le risque qu'ils divergent).

---

## 6. Interface : textes coupés, descriptions et lore invisibles (2026-11-05)

Captures de l'utilisateur (dossier `screenshots` du profil, interface du mod en 2560 × 1369, échelle de l'interface par défaut) : `2026-11-05_20.00.24` (*Marché* > *Boutique*) et `2026-11-05_20.00.49` (*Apparence* > *Cosmétiques*).

### Constats

| Où | Ce qu'on voit | Problème |
|---|---|---|
| Menu de gauche | « Retour & hist… », « Administrat… » (rôle sous le pseudo) | Libellés coupés alors qu'il reste de la place ou qu'une 2e ligne suffirait |
| Onglets du *Marché* | « Hôtel des ven… » | Onglet coupé ; les quatre onglets ont la même largeur quel que soit leur texte |
| Onglets d'*Apparence* | « Cosmétiques… », « Importer… » | Idem (si les « … » sont voulus pour « Importer… », c'est ambigu avec une coupe) |
| *Boutique*, ligne d'un article | « Il fut fait de ce qui restait de la chevelure offe… », « Skin ou cosmétique, débloqué … », « L'infinie et l'eau de la ! · 1 ven… » | La description est coupée à une ligne, et les boutons de prix (PV, Phynarium) et d'administration mangent la place. **Aucun moyen de lire le texte entier** (ni survol, ni clic) |
| *Apparence* > *Cosmétiques* | Des tuiles par catégorie (« Set de Bérénice — 3 cosmétiques — porté ») | Ni nom, ni description, ni lore, ni rareté au premier niveau ; rien n'indique ce que fait le cosmétique (animations, réactions, particules) |

### Ce qui est demandé

1. **Jamais de texte coupé sans recours** :
   - le texte passe à la ligne (2 lignes) avant d'être coupé ; les onglets prennent la largeur de leur texte (ou une police un peu plus petite) ;
   - s'il reste coupé : **info-bulle au survol** avec le texte entier, partout (menu, onglets, lignes de la boutique, pseudo et rôle) ;
   - « … » réservé aux boutons qui ouvrent une fenêtre (« Importer… »), pour ne pas confondre avec une coupe.
2. **Boutique** : description sur 2 lignes dans la liste ; **clic sur un article = fiche détaillée** : grand aperçu 3D qui tourne (comme *Apparence*), bouton « Essayer » (porter quelques secondes avant d'acheter), nom, ensemble, rareté, description complète, lore (en italique), prix, et les autres pièces du même ensemble avec le prix du lot s'il existe.
3. **Apparence** : dans chaque catégorie, une **liste ou grille de cartes** (vignette 3D, nom, rareté, « porté »), et au clic la même fiche que la boutique (sans le prix, ou avec « Possédé ») : description, lore, ce qu'il fait (états animés, réactions, particules, sons). Pour un ensemble : le **lore du set** en tête de la catégorie et un bouton « Porter l'ensemble » (dans la limite des 3 cosmétiques portés).
4. **Champs à saisir par le staff** (à l'import ou avec la roue dentée) : nom affiché, description, lore, ensemble, rareté. **Encore mieux : les lire dans le `.bbmodel`**, comme les réglages des particules (section 2), dans le même objet :

```json
"unhandled_root_fields": {
  "phynaria": {
    "version": 1,
    "fiche": {
      "nom": "Diadème de Bérénice",
      "ensemble": "Bérénice",
      "rarete": "rare",
      "description": "Fin bandeau d'or doux, avec une pierre ivoire au front…",
      "lore": "Il fut fait de ce qui restait de la chevelure offerte…"
    },
    "particules": { "…": "…" }
  }
}
```
   Nous tenons déjà ces textes à jour pour chaque pièce (`fiche.json` dans notre dépôt) et pouvons les embarquer dès que tu confirmes le format. Le staff garde la main : ce qui est lu pré-remplit les champs.
5. **Longueurs à prévoir** : nom ≤ 40 caractères, description ≤ 300, lore ≤ 500 (nos textes actuels : description 150–300, lore 200–450). Retour à la ligne automatique, accents et apostrophes français (« Cœur d'Hiver »).
6. **Si une refonte est plus simple que des retouches**, nous sommes favorables : panneau de gauche plus étroit (icônes + libellé sur 2 lignes), contenu en cartes (vignette, nom, rareté, prix ou « Possédé »), fiche détaillée commune à la boutique et à l'apparence (aperçu, description, lore en citation, prix en PV et en Phynarium, autres pièces de l'ensemble et prix du lot).

---

## 7. Familiers « apprivoisés » : une entité qui suit le joueur (2026-11-05)

### Constat en jeu

Un familier est aujourd'hui un cosmétique comme les autres : il est dans le groupe `body` et suit le torse. Nous le posons au sol par l'animation (pieds à y = 0, contre-rotation du torse en accroupi), mais le modèle ne connaît pas le monde :
- au bord d'un bloc, il marche dans le vide (capture `2026-11-05_20.09.24`) ;
- en accroupi, le torse s'incline et descend : le familier rentre dans le sol (capture `2026-11-05_20.09.09`) ;
- il tourne avec le torse, s'arrête et repart pile avec le joueur, sur les escaliers et les dalles il flotte ou s'enfonce.

L'utilisateur voudrait des familiers **comme les animaux apprivoisables de Minecraft (loup, chat, perroquet)** : pas « collés », avec une **zone de vie** autour du joueur, qui le **suivent**.

### Ce qui est demandé

1. **Un mode « familier »** (catégorie *Familiers*, ou case à l'import) : le modèle n'est plus porté par le joueur mais dessiné sur une **entité côté client** (aucun effet de jeu, aucune collision avec les autres entités, rien d'envoyé à part sa position si nécessaire), avec :
   - **suivi** comme le loup apprivoisé : il reste dans un rayon d'environ 2 à 6 blocs, se met en marche quand le joueur s'éloigne de plus de ~4 blocs, court s'il est loin, **se téléporte** à côté du joueur au-delà de ~12 blocs ou s'il est bloqué (changement de dimension, téléportation, vol) ;
   - **déplacement au sol** avec les collisions des blocs (marches, dalles, saut d'un bloc), pas dans le vide ; **errance** au hasard dans sa zone quand le joueur ne bouge pas ;
   - **type de déplacement** réglable : *au sol* (renard, chat), *volant* (hibou, crâne, mochi : vole à hauteur d'épaule, peut se poser), *nageur* ;
   - **perché** facultatif : sur l'épaule du joueur (comme le perroquet) pour les petits volants, avec descente quand le joueur saute ou court s'il le faut.
2. **Animations par état du familier** (et plus du joueur), même principe de noms que la section 6.2 : `idle`, `walk`, `run`, `sit` (assis quand le joueur est accroupi immobile, comme le loup), `sleep` (joueur couché), `swim`, `fly`, `fall`, `jump`, `land`, `event_equip`, `event_unequip`, et `overlay_` comme aujourd'hui. Vitesse de marche du familier dans `q.ground_speed` (et sa propre `q.yaw_speed`), pour caler les foulées.
3. **Requêtes** utiles dans ce mode : distance au joueur (`q.owner_distance`), le joueur le regarde (angle entre la visée et le familier), `q.owner_is_sneaking`, `q.owner_health`, et celles qui existent déjà pour le monde (pluie, nuit, eau). Le regard (`q.head_*`) devient la tête du familier qui suit le joueur ou ce qui l'entoure.
4. **Repli** : si le mode n'est pas activé, comportement actuel (porté par `body`), pour ne rien casser.
5. **Limites** : un seul familier « vivant » par joueur (les autres cosmétiques portés comptent toujours dans les 3) ; il disparaît dans le menu *Apparence* au profit de l'aperçu actuel.

Nous adapterons nos 5 familiers (renard de givre au sol, chat-lanterne et crâne qui flottent, hibou perché, mochi nuage volant) dès que le format est connu.

---

## 8. Renvoyer le guide complet à jour (2026-11-05)

Merci de nous renvoyer **la totalité du fonctionnement des cosmétiques et de l'interface du mod**, dans la version que tu livres avec ces demandes : le guide `guide-cosmetiques.md` complet et à jour (pas seulement les nouveautés), plus une section sur l'interface. Notre copie date du 2026-11-04 : depuis, le mod 1.4.0 a ajouté des choses que nous avons dû lire dans le `.jar` (sons embarqués `phynaria_sounds` : OGG Vorbis mono, 100 Ko, 5 s, 8 sons, noms `[a-z0-9_]{1,32}`), au risque de nous tromper.

Ce que le guide doit couvrir, pour chaque point : la syntaxe exacte, les limites chiffrées, ce qui se passe si c'est invalide (ignoré, avertissement, refus), et ce qui ne marche pas encore.

**Cosmétiques**
- Format et limites (cubes, groupes, textures `_e`/`_r`/`_m`, textures animées, poids, distance, rotations, Molang : fonctions et requêtes disponibles, avec les nouvelles de la demande 3 : `query.is_slim_arms`, armure, `query.has_shader_pack`, gravité de `phys_`).
- Groupes spéciaux (`add_`, `trans_`, `cam_`, `camy_`, `phys_`, `ctrl_*`, `particle_`, `emit_`, `emit_mc_`) et leur rendu **avec et sans shader, et dans le menu *Apparence*** (l'additif et `cam_` y sont-ils corrects aujourd'hui ?).
- États et animations reconnus, replis, superposition (`overlay_`, `event_*`), ordre de priorité, transitions (délais et fondus).
- Particules : réglages, et ce que tu retiens de la demande 1 (lecture dans le fichier).
- **Sons** : sons Minecraft et sons embarqués (format, limites, nom à mettre dans la clé `sound`, préséance entre un son embarqué et un son Minecraft du même nom, volume, distance d'écoute, comportement de `/cosmetique apercu` avec les `.ogg` du dossier d'aperçu), et ce qui se perd si on réenregistre le fichier dans Blockbench.
- Familiers : fonctionnement actuel, et celui de la demande 3 une fois fait.

**Interface**
- Comment le nom affiché d'un cosmétique est choisi (nom du fichier, champ `name`, saisie du staff ?), et s'il gère accents, espaces et apostrophes (« Ailes d'orage », « Cœur d'Hiver »).
- Import par le staff : chaque fenêtre et chaque champ, ce qui est pré-rempli et d'où.
- Menu *Apparence* (catégories, ensembles, porter / retirer, aperçu), *Marché* et *Boutique* (articles, prix en PV et en Phynarium, ensembles, « Possédé »), et ce que voit un joueur sans droits staff.
- Commandes (`/cosmetique apercu`, `/puadmin …`) et permissions utiles.

Une liste « ce qui a changé depuis le guide du 2026-11-04 » en tête serait idéale.
