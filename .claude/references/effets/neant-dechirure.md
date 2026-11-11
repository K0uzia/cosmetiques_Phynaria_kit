# Référence — Ciel fêlé, yeux dans le noir, bras squelettique (et déchirure, masque : v1)

Fiche documentée (2026-11-06, pour `effet_admin_neant`, complétée pour la v2 le même jour). Codes génériques : aucune œuvre n'est citée ni reprise (règle 5 de `CLAUDE.md`, consigne de l'utilisateur). Complète `failles-portails.md` (grammaire générale des failles).

## Mains et doigts squelettiques (anatomie réelle)

- **Os** : 14 phalanges par main ; quatre doigts à trois phalanges (proximale, moyenne, distale), pouce à deux. La proximale est la plus longue et la plus épaisse, la distale la plus courte ; ordre de grandeur des longueurs 1 : 0,65 : 0,45. Le métacarpe (paume) est plus long que la proximale et plus large.
- **Articulations** : têtes osseuses renflées (« double bosse » des condyles) ; elles ne plient que dans un plan (charnières en poulie, pas de jeu de côté). C'est ce renflement aux jointures qui fait lire « os » plutôt que « bâton ».
- **Amplitudes** (moyennes cliniques) : métacarpo-phalangienne ≈ 85°, interphalangienne proximale ≈ 105°, distale ≈ 70°. Une griffe crispée : environ 40 / 70 / 45° ; un doigt tendu qui tâte : 5 / 10 / 5°.
- **Doigts inégaux** : majeur le plus long, auriculaire le plus court, pouce opposé sur le côté. Doigts légèrement écartés en éventail, l'auriculaire tourné vers l'intérieur.
- **Écarter une déchirure** : les bouts de doigts passent d'abord par la fente (seules les distales se voient), se crochettent (distale et moyenne fléchies) sur le bord, puis la main entière recule vers l'extérieur en tirant ; le poignet reste en arrière du bord, les jointures en avant. Les deux mains d'une paire tirent en sens opposé ; une main du haut et une du bas ouvrent verticalement.
- **Lecture à distance** : silhouette noire sur ciel clair ; jointures marquées (cube plus gros à chaque articulation), bouts effilés en griffe, 4 doigts + pouce bien séparés. Un liseré violet ou une lueur au bout des doigts aide de nuit.

## Déchirure dimensionnelle (VFX)

- **Couches** d'une faille en VFX temps réel : vide (fond), bord (lambeaux, liseré lumineux), distorsion autour (ondulation de l'air), débris et particules (attirés vers le vide ou éjectés).
- **Le bord se lit comme une matière qui se déchire** : bord irrégulier et effiloché (fibres), lambeaux qui **se recourbent vers l'extérieur** pendant qu'on tire, plusieurs couches de bord superposées avec une ombre entre elles. Une déchirure nette en ellipse se lit comme un portail ; des lambeaux recourbés comme un tissu arraché.
- **Avant l'ouverture** : une simple ligne (fente invisible, distorsion de l'air, scintillement), puis quelque chose pousse de l'autre côté.
- **Vide** : noir profond, opaque, avec un peu de profondeur (braises ou poussière colorée qui dérivent, très peu de lumière) ; il « aspire » les débris au départ et en recrache à l'arrivée.
- **Poussière** : fumée et cendres qui s'échappent du bord quand il s'arrache, encre noire qui goutte des lambeaux, éclats violets qui remontent vers le vide.

## Masque blanc de créature (animation japonaise, codes généraux)

- **Matière** : os poli ou bois laqué blanc, coquille lisse avec des ombres douces dans les creux ; fissures fines et quelques éclats pour l'âge.
- **Lecture** : orbites **noires et profondes** (creusées, pas peintes), qui cachent ce qui regarde ; un petit point de lumière au fond de chaque orbite suffit à donner un regard. Fente de bouche étroite ou rangée de dents sculptées. Pommettes et arcade marquées.
- **Inclinaison** : un masque neutre change d'expression avec l'angle ; tourné vers le haut, il paraît serein, **incliné vers le bas, les ombres de l'arcade et de la bouche le rendent menaçant**. Un masque géant qui regarde le joueur d'en haut doit donc pencher vers le bas.
- **Échelle** : le masque n'est pas un visage complet, il flotte devant le noir ; c'est le vide autour qui lui donne la taille d'un géant. Le faire avancer **lentement**, avec un léger tangage, comme quelque chose de très lourd.
- À éviter : long nez en bec, cornes, motifs peints reconnaissables (marques de personnages connus).

## Traduction dans le mod

- **Mains** : un groupe par phalange imbriqué (métacarpe → proximale → moyenne → distale), pivot à la jointure, flexion sur un seul axe ; os = prismes noirs opaques à 6 faces, tête renflée à chaque jointure, distale effilée en griffe. 2 à 4 mains.
- **Bords** : 3 couches de lambeaux décalées de ≥ 0,22 px, découpées par alpha, pivot sur la ligne de fente, rotation vers l'extérieur et vers le spectateur pendant l'ouverture (ils se recourbent) ; liseré violet peint + `_e`.
- **Vide** : plaque opaque noire (lisible de jour), braises violettes dans `_e` et particules.
- **Masque** : vrai volume (cubes empilés en coque bombée), orbites en creux noirs, lueurs en `add_` petites, fissures peintes, groupe qui avance en z et s'incline vers le bas.
- **Particules** : `emit_mc_reverse_portal` (aspiré), `smoke`, `ash`, `squid_ink` (pas d'`end_rod`).

## v2 : ciel fêlé comme une vitre (demande de l'utilisateur, 2026-11-06)

Retour sur la v1 : « plus craquelure ; pas de visage, juste des yeux rouges qui apparaissent avec un coup de pulsation vive, et le bras qui sort pour attraper ». Image de référence fournie : grammaire seulement (aucune créature ni masque repris).

- **Craquelure** : le ciel se lit comme une **vitre ou une coquille percée** : un trou noir opaque irrégulier, au contour en **éclats aigus** (pointes et creux alternés, quelques longues pointes), des **esquilles noires détachées** autour du bord, et de **longues fissures noires fines et ramifiées** qui partent du trou et courent loin (angles cassés, branches qui s'affinent jusqu'à disparaître ; pas de motif régulier en toile d'araignée, pas d'anneaux fermés). Noir sur ciel, jamais des traits lumineux (sinon ils se lisent comme des éclairs) ; au plus un cœur violet très sombre sur les troncs épais.
- **Propagation** : une vitre se fend **par à-coups** (chaque craquement fait avancer les fissures d'un coup, petite secousse), puis cède : le trou s'ouvre en paliers et des **éclats de ciel** (face bleu clair, arête blanche) tombent en tournant. Fermeture : le trou se résorbe, puis les fissures s'effacent de l'extérieur vers le centre.
- **Yeux sans visage** : deux amandes rouges inclinées (coin intérieur plus bas = regard dur), seules dans le noir ; elles s'allument d'un coup avec **2–3 pulsations vives** (lueur qui grossit puis retombe, comme un battement), puis restent allumées. Une seule plaque de lueur derrière les deux yeux (cumul additif borné), cachée par l'œil opaque en son centre.
- **Bras qui attrape** : un long bras d'os (humérus, coude renflé, radius et cubitus, poignet, main à 4 doigts de 3 phalanges + pouce, ongles pointus clairs bien visibles) **sort du trou en glissant**, descend devant le joueur, la paume vers lui, doigts écartés (pas en peigne), puis se referme autour du torse et remonte. Les ongles pâles font la lecture à distance sur un bras sombre. Une ou deux mains plus petites crochètent le bord du trou, doigts posés sur le ciel.

### Traduction dans le mod (v2)

- Fissures peintes d'un seul tenant par marche au hasard (troncs larges qui s'affinent, branches rares), découpées en **tuiles cutout** non vides (texture économe), une profondeur par étape de propagation (écart 0,22 px) ; étapes = longueur parcourue le long de la fissure ; révélées par échelle 0/1 aux craquements.
- Trou = 3 plaques noires opaques de plus en plus grandes, **recadrées sur leur contenu** (la boîte transparente compte dans l'extension).
- Tout le ciel en `camy_` (face à celui qui regarde, 12 px derrière le joueur) ; le bras est dans le même groupe : il vise le joueur sous tous les angles.
- Bras : cinématique inverse à deux os dans le générateur (épaule animée qui recule dans le noir pour garder le bras presque tendu) ; contrôle que le bras ne traverse le plan du ciel qu'à l'intérieur du trou (sinon on le verrait derrière le ciel).
- Sons : fêlure par à-coups (son original), `block.glass.break` quand le trou cède, battements graves des yeux (son original).

## v4 : vitre fêlée sans « araignée », bras d'os lisible (2026-11-06)

Retour en jeu de la v3 : de jour, trou noir hérissé + fissures noires de même largeur toutes issues du centre = araignée ; de nuit, noir sur noir, rien.
- **Verre fêlé** (observation générale du verre trempé et feuilleté) : fissures radiales presque droites, cassées à angle net, épaisses seulement près de l'impact ; **fissures concentriques** courtes qui relient deux radiales voisines et forment des cellules, plus nombreuses près de l'impact ; fêlures isolées plus loin ; une arête qui accroche la lumière d'un côté ; petits éclats manquants au bord des grosses fissures ; morceaux de vitre légèrement décalés le long des fissures.
- **Nuit** : tout ce qui est noir dans le ciel a besoin d'une lueur `add_` sombre (violet ≤ 110) floue autour, discrète de jour.
- **Bras** : humérus (tête ronde, tubercule, épicondyles et deux condyles au coude), olécrâne du cubitus derrière le coude, radius et cubitus séparés par un vide et croisés (le radius passe par-dessus et finit large au poignet, le cubitus finit fin), 8 carpes en deux rangées, métacarpes, phalanges à base renflée et tête en double bosse, griffes pâles recourbées vers la paume ; ombre de cylindre et bouts plus sombres peints sur l'os.

## Sources

- [Wikipedia : Phalanx bone](https://en.wikipedia.org/wiki/Phalanx_bone) et [Kenhub : The phalanges](https://mta-sts.kenhub.com/en/library/anatomy/the-phalanges) (nombre, longueurs relatives, tête et base)
- [Radiopaedia : Phalanges of the hand](https://radiopaedia.org/articles/phalanges-of-the-hands?lang=gb)
- [Thieme, Indian J Plast Surg 2024 : amplitude normale des doigts](https://thieme-connect.de/products/ejournals/abstract/10.1055/s-0044-1788593) (MCP, PIP, DIP)
- [Dessiner une main squelettique](https://wrdsclassroom.wharton.upenn.edu/how-to-draw-a-skeleton-hand_59773.html) (condyles en « double bosse », griffe, segments courts)
- [80.lv : effet de déchirure dimensionnelle en 3D](https://80.lv/articles/spectacular-dimensional-rift-effect-made-in-3d) (deux mondes, débris en particules)
- [Real-Time VFX : exercices d'effets](https://realtimevfx.com/t/other-visual-effects-exercises/1482) (couches : vide, bord, distorsion, débris attirés)
- [Clip Studio : bords déchirés](https://tips.clip-studio.com/en-us/articles/12283) et [Photoshop Roadmap : effet papier déchiré](https://photoshoproadmap.com/how-to-create-a-torn-paper-portrait-effect-in-photoshop) (fibres, couches, bords recourbés)
- [Nohgaku : les masques](https://www.nohgaku.or.jp/en/guide/nō-masks) (masque neutre dont l'expression change avec l'inclinaison : vers le bas = sombre)
- Recherche générale sur les masques blancs de créature (coque lisse, orbites noires creusées, fissures) : boutiques et tutoriels d'accessoires, codes génériques seulement.
- Observation générale du verre fêlé et du verre trempé brisé (étoilement, fissures radiales qui se ramifient, fissures concentriques rares, éclats qui tombent) : codes génériques.
