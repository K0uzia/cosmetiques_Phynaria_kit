# Démons — cornes, queue, ailes membraneuses, démon élégant ou bête

Fiche de référence (2026-11-04). Pièces livrées du thème (chasseur de démons, ensemble Abyssal) : `ailes_abyssales` (validées, **référence de style**), `cornes_abyssales` (2026-11-08, remplace `bandeau_abyssal`, archivé : mêmes cornes validées), `queue_abyssale`, `lames_abyssales`, `epaulieres_abyssales`, `aura_abyssale`, `chapeau_abyssal`, `familier_abyssal`. Lire leurs générateurs avant toute pièce démoniaque.

## 1. Codes visuels essentiels

Dans l'anime, un personnage à cornes est presque toujours un **oni** (folklore japonais) ou un **démon** (*akuma*, *mazoku*). Les cornes (*tsuno*) s'accompagnent d'un **petit croc**, d'**oreilles pointues**, d'une **queue** (souvent à pointe en cœur ou en flèche) et d'**ailes de chauve-souris**. Ces attributs « bougent tout seuls » : la queue et les oreilles trahissent l'émotion.

| Registre | Ce qui le définit |
|---|---|
| **Démon élégant** (le registre du dépôt) | Silhouette humaine intacte, attributs **fins et lisses** : cornes en crochet ou en courbe, queue-fouet sans vertèbres, ailes membraneuses aux os fins, regard lumineux. Cuir, métal sombre, une seule couleur d'accent vive |
| **Oni** | Une ou deux cornes **coniques et droites** qui sortent du front ou du sommet, teint rouge ou bleu, motif tigré, massue. Version mignonne : petites cornes, croc, sourire |
| **Démon mignon** (*onikko*, *tsunokko*) | Petites cornes rondes ou en spirale, queue à pointe en cœur qui remue, petites ailes au bas du dos, couleurs pastel ou rose et noir |
| **Bête / démon majeur** | Cornes multiples, épines, vertèbres apparentes, griffes, membranes déchirées, yeux multiples : il fait **créature** |

Cornes de **mouton enroulées** = sagesse ancienne, démon noble ; **cornes en crochet** vers l'arrière puis vers l'avant = chasseur, guerrier ; **cornes droites** = oni.

## 2. Silhouette et proportions (échelle du dépôt)

- **Cornes** : sur le dessus de la tête, au-dessus des tempes (z ≈ −3 à +2), **jamais sur l'arête du front**. Elles **montent** puis s'incurvent (le dragon les couche vers l'arrière). Longueur 5–9 px, base 1,5–2 px ; `bandeau_abyssal` : position « niquel » validée, à reprendre telle quelle.
- **Oreilles pointues** : 2–3 px qui dépassent derrière la tête, peau + âme.
- **Ailes** : 52–70 px d'envergure, racine haute (y ≈ 21–23) pour un démon guerrier ; **racine basse (bas du dos, y ≈ 14–16)** pour un registre gracieux ou séducteur : repliées autour des hanches elles forment une « jupe ». Petites ailes de démon mignon : 12–20 px d'envergure.
- **Queue** : fouet de 24–30 px depuis y ≈ 12, z ≈ +2, section 1,5 px vers 0,5 px, pointe en cœur ou en flèche de 2–3 px (`queue_abyssale` : 11 segments, lame en cœur allongé).

## 3. Matières et couleurs (HD 32–40 texels/px)

- **Palette du dépôt (Abyssal)** : charbon et pourpre-noir (17, 7, 26) → (82, 28, 104), liseré (122, 42, 124), **une seule couleur vive : vert acide** (96, 200, 44) → cœur (150, 244, 70). Reprendre les constantes de `gen_bandeau_abyssal.py`.
- **Autres palettes démon** : noir et cramoisi (attention, « gothique », leçon Cuir v1), ivoire et or (démon déchu presque divin), violet et rose néon (mignon).
- **Cornes** : bagues de croissance, base sombre mate, pointe plus claire et lisse ; un filet lumineux dans les rainures pour le démon élégant.
- **Membrane** : peinte d'un seul tenant, **veines contrastées** de la couleur d'accent ; elle s'éclaircit vers le bord.
- **Peau ou cuir de la queue** : tube lisse, une seule veine lumineuse sous toute la longueur.

## 4. Mouvement, comportement, attitude

- **Queue = humeur** (code d'anime) : balancement lent et souple au repos ; fouette vite quand il est agacé ; s'enroule en point d'interrogation quand il est curieux ; se dresse raide à la surprise ; pointe en cœur qui frétille de joie.
- **Ailes** : repos serré contre le dos ; ouverture brutale et ample à l'attaque (déploiement en 0,15 s, retour en 0,6 s) ; enveloppent le corps en protection en `sneak` ou `sleep`.
- **Cornes** : rigides, ne bougent pas ; ce qui bouge, c'est la lueur (pulsation lente de 4 s, montée brève à l'attaque).
- **Apparition** : ailes qui « percent » le dos (petite échelle, puis ouverture d'un coup, comme un étirement), regard qui s'allume en dernier.

## 5. Langage anime

- **Regard qui s'allume** : yeux qui brillent dans l'ombre du visage, traînée lumineuse du regard pendant un mouvement rapide (afterimage).
- **Aura sombre** : volutes noires ou violettes qui montent du corps, **contour clair à l'extérieur**, fond sombre (l'inverse d'une aura divine). Éclairs ou fissures lumineuses au sol.
- **Plumes noires** quand le démon est un ange déchu : pluie de plumes noires à l'apparition.
- **Marques** : motifs ou sceaux qui s'éclairent sur la peau ou les cornes quand le pouvoir monte.
- **Croc** visible quand il sourit ; sourire en coin plutôt que grimace pour le démon élégant.

## 6. Traduction dans le mod

- **Cornes** : peau + âme (recette `bandeau_abyssal`), groupe `head`, filet `_e` dans les rainures.
- **Queue** : segments imbriqués, ondulation animée ; une chaîne `phys_queue_r40_a50` par-dessus pour l'élan (non simulé par le renderer, à juger en jeu). Humeur par état : `idle` souple, `run` tendue à l'horizontale, `sneak` enroulée, `hurt` dressée.
- **Ailes** : `gen_ailes_abyssales.py` (référence absolue) ; ailes basses gracieuses : même squelette, racine descendue.
- **Regard et veines** : `_e` + base claire dans la texture pour rester lisible avec shader (où `_e` et `add_` restent invisibles).
- **Aura sombre** : `trans_` en volutes sombres à bord clair (visible avec shader), `add_` en liseré lumineux par-dessus (sans shader). Recette d'enveloppe validée : disques en `cam_` reculés derrière chaque partie du corps, colonnes en `camy_` derrière le joueur (`aura_brasier` v3).
- **Particules** : braises ou fumée qui **montent** depuis les cornes ou les mains ; plumes noires qui **tombent seulement depuis des ailes à plumes** (`.claude/rules/essentiel.md`).

## 6 bis. Cornes qui percent le crâne (anatomie réelle → pièce de tête sans bandeau ni couronne, 2026-11-08)

- **Ce que dit l'anatomie** : une vraie corne est une **cheville osseuse** (processus cornual) qui prolonge l'os frontal, vascularisée et poreuse, couverte d'un étui de kératine strié ; sa surface osseuse est **ridée et poreuse**. Chez le cerf, le pied de l'andouiller (pivot) porte une **meule** : une couronne de nodules d'os.
- **Traduction (`cornes_abyssales`)** : la corne n'est pas posée, elle **sort** du crâne. Au pied, une meule de six nodules ; depuis elle, des **racines d'os aplaties et soudées** au crâne (relief de 0,4–0,6 px, pas des tubes : les tubes à distance de la tête font « pattes d'araignée », même leçon que la « cage de tubes » des harnais) qui tournent aux arêtes, fendues d'une fissure verte ; elles se referment sur les yeux en **demi-masque d'os en deux lobes** (arcades en relief, fentes découpées), d'où sort le regard vert.
- Trois pistes envisagées : (1) cornes + racines + demi-masque d'os (retenue : une seule logique, la corne qui pousse et couvre les yeux, et le regard vert garde sa place) ; (2) coiffe de cornes multiples en éventail (risque « bête / démon majeur », section 1) ; (3) demi-masque d'os seul, cornes sur le masque (trop proche du masque archivé, et cornes déplacées alors que leur position est validée).
- Sources : [WikiVet, *Horn – Anatomy & Physiology*](https://en.wikivet.net/Horn_-_Anatomy_%26_Physiology) ; [Vectree, *Bovid horn morphology*](https://vectree.io/c/bovid-horn-morphology).

## 7. Pièges

- **« Trop dragon, créature »** : vertèbres, épines dorsales, membrane sur une queue = bête. Le démon élégant garde des attributs lisses.
- **« Trop gothique »** : rouge et noir + clous pointus (leçon Cuir v1). Préférer une couleur d'accent froide ou acide.
- **Masque abyssal** : « sympa » mais hors de l'esprit chasseur de démons ; ne pas le présenter comme répondant à ce thème.
- Cornes en porte-à-faux devant le visage : ancrage sur le front. Contrôler le profil.
- Aura démoniaque en langues de feu : « mec en feu ». Une aura est de la lumière (ou de l'ombre), pas un incendie.
- Ne pas reproduire un démon ou un oni de manga identifiable (cornes + teint + motif d'un personnage).

## 8. Sources

- [Tsuno, horns in anime (Japanese with Anime)](https://www.japanesewithanime.com/2020/04/tsuno.html)
- [Oni (Japanese with Anime)](https://japanesewithanime.com/2018/03/oni.html)
- [Why Japanese oni look scary yet cute (Anime Lore Hub)](https://animelorehub.blogspot.com/2025/11/why-japanese-oni-look-scary-yet-cute.html)
- [Horned girls, devilishly cute (pixivision)](https://www.pixivision.net/ko/a/9424)
- [Horns of Villainy (TV Tropes)](https://www.tvtropes.org/pmwiki/pmwiki.php/Main/HornsOfVillainy)
- [Wings Below the Waist (TV Tropes)](https://www.tvtropes.org/pmwiki/pmwiki.php/Main/WingsBelowTheWaist)
- [Good Wings, Evil Wings (Tropedia)](https://tropedia.fandom.com/wiki/Good_Wings,_Evil_Wings)
- [Feather Motif (TV Tropes)](https://TVTropes.org/pmwiki/pmwiki.php/Main/FeatherMotif)
- [Anime succubus girls (Otaku USA)](https://otakuusamagazine.com/anime-succubus-girls/)
- [How to draw bat wings, membrane and fingers (Instructables)](https://instructables.com/Draw-Reptile-Wings)
