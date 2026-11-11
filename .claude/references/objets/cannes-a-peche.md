# Cannes à pêche — fiche de référence (skins de canne, guide 14)

## Anatomie d'une vraie canne (à mouche, la plus lisible en petit)
Du talon à la pointe : **bouchon de talon** (butt cap) ; **porte-moulinet** (reel seat : fût fileté, une coiffe fixe et une bague
de serrage) avec le moulinet **sous** la canne ; **poignée** (liège, la main la tient au-dessus du moulinet) ; **bague d'arrêt**
(winding check) qui finit la poignée ; **scion** (blank) qui s'affine du talon à la pointe (la conicité, taper, fait l'action
de la canne), en brins joints par des **viroles** (ferrules) ; **anneaux** (guides) ligaturés, de plus en plus petits vers la
pointe, du même côté que le moulinet ; **anneau de tête** (tip top) au bout, par où la ligne sort.
Moulinet à mouche : tambour à axe perpendiculaire à la canne, deux flasques, bobine entre elles, manivelle sur la face.
Au lancer, le scion se charge en arrière puis fouette en avant ; la ligne se dévide du moulinet.

## Canne de glace (pêche au trou dans la banquise)
Canne **courte** (50 à 105 cm ; 50 cm pour pêcher à vue dans un abri), raide, poignée trapue ; **moulinet en ligne** (inline :
bobine à axe en travers comme un moulinet à mouche, peu de pièces qui gèlent, ligne moins vrillée) ou petit moulinet à tambour
fixe ; **anneaux surdimensionnés** (acier ou alu) pour que la glace ne les bouche pas ; parfois un « spring bobber » (ressort
détecteur de touche) au bout. Leurre type : cuillère ou jig en goutte, perle, hameçon simple.

## Dans Minecraft (jar 26.1.2)
- Images `fishing_rod.png` (talon en bas à gauche, pointe en (14 ; 15) vue de +Z, ligne qui pend du bout à droite et s'enroule
  en bas) et `fishing_rod_cast.png` (même canne sans ligne). Le jeu dessine sa ligne depuis le bout : garder la pointe au coin
  haut droit du bloc.
- Display `item/handheld_rod` : 3e personne rotation (0, ±90, ±55), translation (0 ; 4 ; 2,5), échelle 0,85 ; 1re personne
  (0, ±90, ±25), (0 ; 1,6 ; 0,8), 0,68 (préréglage `_CANNE` de `tools/objet.py`, corrigé le 2026-11-08).
- En 3e personne, le côté bas-droit de l'image (−b, perpendiculaire à la canne) est le **bas** : moulinet et anneaux de ce côté ;
  la face vue dans l'inventaire (+Z) regarde vers l'extérieur (droite du joueur).
- Étapes `repos` / `lancee` (guide 14), passage par `event_enter_lancee` / `event_enter_repos`.

## Pièces
- `skin_canne_cuir` (fouet), `skin_canne_orage` (canne à mouche en volume, moulinet-tambour), `skin_canne_givre` (canne de glace courte, moulinet en ligne à flocon, anneaux surdimensionnés).
- `skin_canne_abyssal` (épine d'os, moulinet-vertèbre), `skin_canne_steampunk` (chaudière sur le porte-moulinet, moulinet à flasques dentées entraîné par un pignon à manivelle, manomètre au moyeu fixe).
- **Deux copies d'étape** (`repos`, `lancee`) : un groupe à préfixe (`trans_`, `add_`) copié dans les deux étapes doit avoir un nom propre à l'étape (`trans_jet_repos`, `trans_jet_lancee`), sinon FAIL « noms de groupes uniques » ; `ctrl_` et `emit_mc_` peuvent se répéter.
- Moulinet qui tourne : ce qui doit rester fixe (cadran, aiguille, cadre) va dans un groupe à part de la bobine ; rotation d'`event_select` choisie selon la symétrie de la bobine (flasque à 6 trous et 16 dents : 180°) pour ne pas sauter à la fin.

## Sources
- Wikipédia, « Fly rod building » : https://en.wikipedia.org/wiki/Fly_rod_building
- Dummies, « Anatomy of a Fly Rod » : https://www.dummies.com/article/home-auto-hobbies/sports-recreation/fishing/anatomy-of-a-fly-rod-274722/
- Okuma, « Anatomy of a Fishing Rod » : https://okumafishingusa.com/blogs/news/anatomy-of-a-fishing-rod-okuma-tune-up-tuesday
- Visual Dictionary, « flyfishing » : https://visualdictionaryonline.com/sports-games/outdoor-leisure/fishing/flyfishing_2.php
- Take Me Fishing, « Consider the ice fishing inline reel » : https://takemefishing.org/blog/december-2020/consider-the-ice-fishing-inline-reel
- Cast & Spear, « Best Ice Fishing Rod and Reel Combos » (longueurs, anneaux surdimensionnés) : https://castandspear.com/best-ice-fishing-combos/
- Outdoor Life, « How to rig your ice fishing rods and reels » : https://www.outdoorlife.com/story/fishing/how-to-rig-your-ice-fishing-rods-and-reels-for-any-fish.md
