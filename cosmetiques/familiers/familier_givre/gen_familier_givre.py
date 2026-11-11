"""Familier de givre v10 (2026-11-06) : la v4 (géométrie, texture, proportions, palette, silhouette inchangées ; générateur
.build/gen_v4_sneak.py) passée en FAMILIER VIVANT au sol (guide 6.6), après le refus en jeu de la refonte v9 en facettes
(« extrêmement moche, l'ancien modèle était 10x mieux » ; générateur gardé dans .build/gen_v9_refuse.py). Seuls la racine,
le placement et les animations changent : bloc unhandled_root_fields.phynaria.familier {"mode": "sol", "distance": 3,
"vitesse": 1}, racine « renard » à l'origine (pattes à y = 0, tête vers −Z), aucun groupe du corps, plus de contre-rotation
ni de place sur l'épaule, le dos ou la poitrine. Animations : pet_idle (28 s, 14 comportements au hasard de la v4),
pet_walk / pet_run (amplitude × q.ground_speed du familier), pet_sit, pet_sleep (en boule au sol), pet_swim, pet_fall,
pet_jump, pet_land, overlay_givre (regard, oreilles, pluie, eau qui le fait s'ébrouer, nuit, pleine lune, vie basse du maître
par q.owner_health, queue qui remue quand le maître s'approche, décalage à gauche quand il est porté : q.is_pet = 0, menu
Apparence), event_equip, event_teleport, event_owner_hurt, event_exit_sleep.
À juger en jeu (/cosmetique apercu) : allure à la vitesse réelle du familier, pet_swim (hauteur dans l'eau), event_owner_hurt.

Familier de givre v4 (2026-11-05, après relecture de la v3 : grappes de boîtes aux oreilles, joues et culotte en plaques,
truffe en boîte noire, liserés aux jonctions du tronc, queue en 4 blocs) : oreilles peau + âme, plaques retirées, truffe en
ardoise arrondie, masses du tronc de largeur proche, queue en 6 segments à roulis alterné, ombrage sur enveloppe arrondie
(proxy_normal), réactions à l'eau (q.is_in_water) et à la pleine lune (q.moon_phase). Le reste ci-dessous (v3) tient toujours.

Familier de givre v3 : renard polaire, esprit du froid, qui marche au sol à gauche du joueur comme un vrai renard.
Ensemble Givre (thème Éléments), fiche .claude/styles/givre.md. Design original (pas de créature existante).
Écrit familier_givre.png, familier_givre_e.png et .build/familier_givre_brut.bbmodel à côté de ce script.

Refonte complète du 2026-11-05 (retour en jeu sur la v2 : « grands carrés », « assemblage de formes », « plus détaillé :
visage, sourcils, corps, fourrure », « un renard est au sol comme un vrai renard ») selon
.claude/references/familiers/modelisation-organique.md et .claude/styles/familiers.md (recette du familier au sol) :
  - squelette : bassin > taille > poitrail > cou > tête, chaque masse dans une feuille (respiration) ; la courbe vient des
    groupes, les cubes sont alignés dans leur groupe ; sections rondes en croix chanfreinées (2 ou 3 boîtes alignées, plus
    de jumeau tourné à 45°) ; chaque partie commence dans son parent (cou dans le poitrail, museau dans le crâne, cuisse
    dans le bassin, queue dans la croupe) ;
  - peinture en espace monde : chaque texel est peint selon sa position et sa normale au repos (zones, dos clair et
    ventre bleuté, lumière douce, occlusion aux contacts, mèches et touffes dans le sens du poil) ; mêmes couleurs de part
    et d'autre des jointures ; faces cachées sur un texel transparent, texels enfouis dans un cube du même groupe
    transparents ; UV partagées gauche/droite (le côté droit est le miroir du gauche) ;
  - visage construit : crâne, front bombé, arcades-sourcils animables (groupes sourcil_l/r), yeux enfoncés dans des
    orbites découpées (plaque d'oeil 0,25 px sous la surface, iris, pupille, deux reflets, cerne), paupières (échelle y),
    museau en deux parties court et effilé, truffe sculptée, bouche (fente entre museau et mâchoire), mâchoire et langue ;
  - oreilles courtes et rondes de renard polaire en trois boîtes, creux intérieur découpé avec une plaque en retrait ;
  - pattes en trois segments, zigzag arrière (cuisse, jambe, jarret, pied) ; 11 mèches en volume couchées sur la surface ;
  - queue touffue de renard polaire (6 segments, sections en croix) d'où sortent 5 cristaux trans_ nets vers le bout.

Placement et locomotion (fiche familiers.md, recette au sol ; .claude/references/familiers/types-familiers.md) :
  body > fam_sol (contre-rotation et placement d'état) > fam_saut (événements) > fam_pos > fam_rot > bassin…
  Au sol à gauche (x ≈ −11, un peu en arrière), pieds à y = 0. Pattes posées par IK (calcul en Python) dans chaque état.
  walk : petit galop bondissant à 3,5 Hz ; run : galop allongé à 4 Hz ; sneak : contre-rotation du torse, marche de
  chasse basse à 2 Hz ; fly : assis sur l'épaule gauche (event_enter_fly / event_exit_fly : le saut) ; fall : bond, brume
  sous les pattes (l'esprit lévite un instant) et, en chute longue, il glisse sur l'épaule par un lissage (q.vertical_speed) ;
  glide : cramponné au dos (event_enter_glide) ; swim : debout sur le dos ; sleep : roulé en boule sur la poitrine.
  Monture : pas d'animation (16 au plus) : le staff choisit « fly » pour la case Monture.
Vivant : idle de 28 s, 14 comportements tirés au hasard par tranches de 7 s (q.life_time, q.instance_seed ; liste
COMPORTEMENTS) ; overlay_givre : regard qui suit celui du joueur, oreilles indépendantes, virages, pluie, nuit, vie basse,
réaction à l'attaque (q.attack_time : petit bond, souffle de givre) et à la blessure (q.hurt_time : sursaut, oreilles
plaquées) ; event_jump, event_land (q.land_speed), event_equip (2026-11-08 : il sort d'un tourbillon de neige en tournant,
s'ébroue de la tête à la queue, lève le museau vers son maître ; event_teleport en version courte, sans son).
Arbitrage des 16 animations : attack et hurt passent dans l'overlay (q.attack_time, q.hurt_time) pour faire place aux
trois sauts d'état ; plus d'animation de particule (la brume se règle par le staff).

Fonctions avancées (guide 4 bis, 5 ter, 6.4) : trans_ (cristaux, brume de lévitation), ctrl_alpha (brume visible en l'air),
ctrl_emit (brume en l'air et à l'arrivée, souffle à l'éternuement et à l'attaque), overlay_, event_*, calque _e (iris,
cœurs des cristaux, fond léger de la fourrure). Un seul son (event_equip, tools/sons.py).
À juger en jeu (/cosmetique apercu) : événements d'entrée et de sortie d'état (calage sur le fondu de 0,2 s),
lissage de chute longue (variables mémorisées), réactions par q.attack_time et q.hurt_time.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

AVEC_E = True
NOM = "familier_givre"
TEX = 512
TAU = 2 * math.pi
SS = 2
C = np.array((0.0, 0.0, 0.0))           # familier vivant (guide 6.6) : pattes à l'origine, tête vers −Z
I3 = np.eye(3)


def V(*a):
    return np.array(a, float)


def A(c):
    return np.array(c, np.float32)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def rot_matrix(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def euler(R):
    sy = -R[2, 0]
    if abs(sy) > 0.99999:
        ry = math.copysign(math.pi / 2, sy)
        ang = (math.degrees(math.atan2(R[0, 1], R[0, 2])) if sy > 0 else math.degrees(math.atan2(-R[0, 1], -R[0, 2]))), math.degrees(ry), 0.0
    else:
        ang = math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(math.asin(sy)), math.degrees(math.atan2(R[1, 0], R[0, 0]))
    assert np.allclose(rot_matrix(*ang), R, atol=1e-4), "euler : reconstruction fausse"
    return tuple(0.0 if abs(a) < 1e-6 else a for a in ang)


RX = lambda a: rot_matrix(a, 0, 0)
RY = lambda a: rot_matrix(0, a, 0)
RZ = lambda a: rot_matrix(0, 0, a)
M = np.diag([-1.0, 1.0, 1.0])          # miroir gauche/droite


def lerp(a, b, k):
    return a + (b - a) * k


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def smv(x, a, b):
    u = np.clip((x - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


# ================================================================== squelette
G = {}          # clé -> groupe
CUBES = []      # cubes (dict)


def grp(key, W, Rw=I3, parent=None, name=None):
    """Groupe défini par son pivot W et son orientation Rw au repos, dans le repère du joueur."""
    W = np.asarray(W, float)
    if parent:
        P = G[parent]
        o = P["o"] + P["Rw"].T @ (W - P["W"])
        R = P["Rw"].T @ Rw
    else:
        o, R = W.copy(), np.array(Rw, float)
    G[key] = {"key": key, "name": name or key, "o": o, "rest": np.array(euler(R)), "parent": parent, "W": W, "Rw": np.array(Rw, float),
              "uuid": str(_uuid.uuid4()), "ids": [], "children": []}
    if parent:
        G[parent]["children"].append(key)
    return key


def mgrp(key, keyl):
    """Groupe miroir (côté droit) d'un groupe gauche déjà créé, sous le miroir de son parent."""
    g = G[keyl]
    par = g["parent"]
    parm = par[:-2] + "_r" if par and par.endswith("_l") else par
    return grp(key, _mir(g["W"]), M @ g["Rw"] @ M, parm)


def F(x, y, z):
    return C + V(x, y, z)


def cube(g, name, lc, size, Rl=I3, mat=None, faces=None, mirror_of=None, fam=None, ao=True, carve=False, sym=False, hidden_ok=True):
    """Cube dans le groupe g : centre lc dans le repère local du groupe (relatif au pivot), taille dans ce repère (ou dans
    celui de Rl, orientation propre du cube dans le groupe). faces : faces à peindre (les autres : texel transparent)."""
    g_ = G[g]
    cu = g_["o"] + np.asarray(lc, float)
    h = np.asarray(size, float) / 2
    c = {"name": name, "g": g, "cu": cu, "frm": cu - h, "to": cu + h, "Rl": np.array(Rl, float), "mat": mat or {}, "uuid": str(_uuid.uuid4()),
         "faces": faces or ["north", "south", "east", "west", "up", "down"], "mirror_of": mirror_of, "fam": fam or g, "ao": ao,
         "carve": carve, "sym": sym, "hidden_ok": hidden_ok}
    CUBES.append(c)
    g_["ids"].append(c["uuid"])
    return c


def cubew(g, name, cw, size, Rw_cube=None, **kw):
    """Cube placé par son centre dans le repère du joueur au repos ; Rw_cube : orientation monde du cube (sinon celle du groupe)."""
    g_ = G[g]
    lc = g_["Rw"].T @ (np.asarray(cw, float) - g_["W"])
    Rl = I3 if Rw_cube is None else g_["Rw"].T @ Rw_cube
    return cube(g, name, lc, size, Rl, **kw)


def section(g, name, cw, size, n=2, chanf=0.25, long=2, Rw_cube=None, half=False, dyf=0.0, **kw):
    """Section arrondie par paliers, boîtes alignées sur les axes du groupe (ou de Rw_cube) ; size = (x, y, z) dans ce repère,
    long = axe de la longueur. Chanfrein total cc = chanf × min(section).
    half=False : boîtes en croix (1 pleine en a et réduite en b, 2 l'inverse, 3 à mi-chemin), raccourcies de 0,2 px par palier.
    half=True (axe x en travers, axe long z ou y) : moitié gauche = boîte centrale pleine en hauteur + flanc réduit en hauteur
    qui l'emboîte ; la moitié droite est son miroir (UV partagées). Aucune grande face cachée : moins de texture perdue."""
    s = np.asarray(size, float)
    a, b = [i for i in range(3) if i != long]
    cc = chanf * min(s[a], s[b])
    out = []
    if not half:
        red = [(0.0, cc), (cc, 0.0)] + ([(cc / 2, cc / 2)] if n == 3 else [])
        for k, (ra, rb) in enumerate(red):
            d = s.copy()
            d[a] -= ra
            d[b] -= rb
            d[long] -= 0.22 * k
            nm = name + ("" if k == 0 else str(k + 1)) if not name.endswith(("_l", "_r")) else name[:-2] + ("" if k == 0 else str(k + 1)) + name[-2:]
            out.append(cubew(g, nm, cw, d, Rw_cube=Rw_cube, **kw))
        return out
    assert a == 0
    Rc = G[g]["Rw"] if Rw_cube is None else Rw_cube
    xa = Rc @ V(1, 0, 0)
    assert abs(xa[0] - 1) < 1e-6, "demi-cubes : le cube doit garder l'axe x du renard"
    kw2 = dict(kw)
    kw2.pop("sym", None)
    cw = np.asarray(cw, float)
    wc = s[0] - cc                      # largeur de la boîte centrale (entière)
    ov = min(0.15, cc / 2)              # recouvrement du flanc dans la boîte centrale
    parts = []
    d = s.copy()
    d[0] = wc / 2
    parts.append(("", cw - xa * wc / 4, d))
    d = s.copy()
    d[0] = cc / 2 + ov
    d[b] = s[b] - cc
    d[long] = s[long] - 0.22
    ya = Rc @ V(0, 1, 0) if b == 1 else Rc @ V(0, 0, 1)
    parts.append(("c", cw - xa * (s[0] / 2 - d[0] / 2) + ya * dyf, d))
    for suf, cl, dl in parts:
        nm = name + suf
        out.append(cubew(g, nm + "_g", cl, dl, Rw_cube=Rw_cube, faces=[f for f in FACES6 if f != "east"], **kw2))
        out.append(cubew(g, nm + "_d", _mir(cl), dl, Rw_cube=None if Rw_cube is None else M @ Rw_cube @ M, faces=[f for f in FACES6 if f != "west"],
                         mirror_of=nm + "_g", **kw2))
    return out


def _mir(p):
    q = np.asarray(p, float) - C
    return M @ q + C


FACES6 = ["north", "south", "east", "west", "up", "down"]
# ------------------------------------------------------------------ hiérarchie du placement
grp("fam_sol", C, name="renard")          # racine du familier vivant (pas de groupe du corps)
grp("fam_saut", C, parent="fam_sol")
grp("fam_pos", C, parent="fam_saut")
grp("fam_leve", C, parent="fam_pos")
grp("fam_rot", C, parent="fam_leve")

# ------------------------------------------------------------------ tronc : trois masses (bassin, taille, poitrail), chanfrein fin de 0,12 px
# Peu de volumes, bien proportionnés, entièrement peints (renard vanilla, mods d'animaux) : le relief vient de la texture.
BEV = 0.24                    # chanfrein total (0,12 px de chaque côté), le même partout
grp("bassin", F(0, 3.75, 1.9), parent="fam_rot")
grp("bassin_m", F(0, 3.8, 2.1), parent="bassin")
grp("taille", F(0, 3.85, 0.9), RX(4), parent="bassin")
grp("taille_m", F(0, 3.95, 0.15), RX(4), parent="taille")
grp("poitrail", F(0, 4.0, -0.8), RX(9), parent="taille")
grp("poitrail_m", F(0, 4.0, -1.55), RX(9), parent="poitrail")
FUR = lambda part, **k: {"type": "fur", "part": part, **k}


def masse(g, name, cw, size, Rw_cube=None, dyf=0.0, **kw):
    """Une masse : boîte centrale + flanc chanfreiné (demi-cubes miroirs), chanfrein BEV."""
    s = np.asarray(size, float)
    return section(g, name, cw, s, chanf=BEV / min(s[0], s[1]), half=True, Rw_cube=Rw_cube, dyf=dyf, **kw)


masse("bassin_m", "hanches", F(0, 3.8, 2.1), (3.3, 2.75, 2.6), mat=FUR("tronc"), fam="tronc")
masse("taille_m", "taille", F(0, 3.98, 0.15), (2.74, 2.68, 2.5), Rw_cube=RX(4), mat=FUR("tronc"), fam="tronc")
masse("poitrail_m", "poitrail", F(0, 4.0, -1.55), (3.36, 3.25, 2.6), Rw_cube=RX(9), mat=FUR("tronc"), fam="tronc")

# cou (monte vers l'avant), tête à plat
RCOU = RX(35)
grp("cou", F(0, 4.9, -2.3), RCOU, parent="poitrail")
masse("cou", "cou", G["cou"]["W"] + RCOU @ V(0, 0.15, -0.75), (2.4, 2.2, 2.0), Rw_cube=RCOU, mat=FUR("cou"), fam="tronc")
grp("tete", F(0, 5.92, -3.41), parent="cou")
SK = F(0, 6.78, -3.75)
masse("tete", "crane", SK, (2.9, 2.5, 2.4), mat=FUR("tete"), fam="tete", carve=True)
# joues touffues, plus larges que le crâne : tête en losange (larges aux joues, étroite au sommet et au menton)
for tag, sx in (("l", -1), ("r", 1)):
    cubew("tete", f"joue_m_{tag}", F(sx * 1.32, 5.95, -3.5), (0.85, 1.15, 1.4), Rw_cube=RZ(sx * 9) @ RY(-sx * 6), mat=FUR("joue"), fam="tete",
          mirror_of=None if tag == "l" else "joue_m_l")
# museau : une boîte (chanfrein fin), truffe ronde, mâchoire
RMUS = RX(-10)
grp("museau", F(0, 6.25, -4.7), RMUS, parent="tete")
section("museau", "museau", F(0, 6.02, -5.6), (1.25, 0.95, 2.1), n=2, chanf=0.2 / 0.95, Rw_cube=RMUS, mat=FUR("museau"), fam="tete", sym=True)
NEZ_C = F(0, 6.3, -6.72)
cubew("museau", "truffe", NEZ_C, (0.5, 0.38, 0.3), Rw_cube=RX(-3), mat={"type": "nez"}, fam="nez", ao=False, sym=True)
grp("machoire", F(0, 5.55, -4.55), parent="tete")
cubew("machoire", "machoire", F(0, 6.02, -5.6) + RMUS @ V(0, -0.475 - 0.12 - 0.16, 0.32), (0.9, 0.32, 1.55), Rw_cube=RMUS, mat=FUR("machoire"), fam="tete", sym=True)

# yeux en amande, grands et ouverts : plaque d'oeil 0,25 px sous la surface du crâne, orbite découpée dans le crâne
EYE_C = V(-0.78, 7.0, -4.95)            # centre de l'orbite sur la face avant du crâne (repère du renard)
EYE_R = (0.56, 0.47)                    # demi-axes de l'orbite
CARVES = []


def _orbite(P):
    x = np.abs(P[..., 0]) - abs(EYE_C[0])
    y = P[..., 1] - EYE_C[1]
    # amande : coin interne plus bas et plus fin, coin externe un peu relevé
    yy = y - 0.1 * x / EYE_R[0]
    r = (x / EYE_R[0]) ** 2 + (yy / (EYE_R[1] * (1 + 0.12 * x / EYE_R[0]))) ** 2
    return (r < 1.0) & (P[..., 2] < -4.75)


CARVES.append(_orbite)
LID_H = 0.14
LID_TOP = EYE_C[1] + EYE_R[1] + 0.1
LID_K = (LID_TOP - (EYE_C[1] - EYE_R[1] - 0.05)) / LID_H - 1       # échelle y en plus pour fermer
for tag, s in (("l", -1), ("r", 1)):
    Ec = C + V(s * abs(EYE_C[0]), EYE_C[1], EYE_C[2])
    if tag == "l":
        grp("oeil_l", Ec + V(0, 0, 0.25), parent="tete")
        cubew("oeil_l", "oeil_l", Ec + V(0, 0, 0.4), (1.45, 1.22, 0.3), mat={"type": "oeil"}, fam="oeil", faces=["north"], ao=False)
        grp("paupiere_l", V(Ec[0], C[1] + LID_TOP, Ec[2] - 0.05), parent="tete")
        cubew("paupiere_l", "paupiere_l", V(Ec[0], C[1] + LID_TOP - LID_H / 2, Ec[2]), (0.9, LID_H, 0.3), mat=FUR("paupiere"), fam="paupiere",
              faces=["north", "down", "up", "east", "west"], ao=False)
        grp("sourcil_l", V(Ec[0] + 0.05, C[1] + LID_TOP + 0.08, Ec[2]), parent="tete")
        cubew("sourcil_l", "sourcil_l", V(Ec[0], C[1] + LID_TOP + 0.125, Ec[2] + 0.08), (0.9, 0.24, 0.58), mat=FUR("sourcil"), fam="sourcil", ao=False)
    else:
        for k in ("oeil", "paupiere", "sourcil"):
            mgrp(f"{k}_r", f"{k}_l")
BROW_Y = LID_TOP + 0.125

# oreilles courtes et rondes : deux boîtes, creux intérieur (faces avant découpées, plaque claire en retrait)
REAR = RZ(16) @ RX(-6)
grp("oreille_l", F(-0.95, 7.88, -3.45), REAR, parent="tete")
# Peau + âme (recette des plumes, validée « la rondeur est bien ») : deux plaques de 0,3 px au contour de triangle arrondi
# découpé par alpha (avant : creux clair ; arrière : fourrure), autour de trois âmes pleines en paliers qui remplissent
# l'épaisseur. Plus de grappe de boîtes (retour v2/v3).
EAR_H, EAR_HW = 1.45, 0.76
for nm, (y0, y1, hw, hz) in (("oreille_l", (-0.25, 0.52, 0.55, 0.3)), ("oreille_l2", (0.47, 0.97, 0.38, 0.27)), ("oreille_l3", (0.92, 1.22, 0.22, 0.24))):
    cube("oreille_l", nm, (0, (y0 + y1) / 2, 0.0), (2 * hw, y1 - y0, 2 * hz), mat=FUR("oreille"), fam="oreille", faces=["east", "west", "up", "down"])
cube("oreille_l", "oreille_l_creux", (0, 0.72, -0.27), (2 * EAR_HW, 1.5, 0.3), mat={"type": "oreille_plaque", "face": "int"}, fam="oreille_int",
     faces=["north"], ao=False)
cube("oreille_l", "oreille_l_dos", (0, 0.72, 0.27), (2 * EAR_HW, 1.5, 0.3), mat={"type": "oreille_plaque", "face": "dos"}, fam="oreille",
     faces=["south"], ao=False)


def _creux(P, Wl, Rl):
    q = (P - Wl) @ Rl
    x, y, z = q[..., 0], q[..., 1], q[..., 2]
    hw = 0.44 * np.clip(1 - (y - 0.1) / 1.0, 0, 1) ** 0.7
    return (np.abs(x) < hw) & (y > 0.1) & (y < 1.05) & (z < -0.1)


EAR_W, EAR_R = G["oreille_l"]["W"].copy(), G["oreille_l"]["Rw"].copy()
mgrp("oreille_r", "oreille_l")

# ------------------------------------------------------------------ pattes : une boîte par segment, zigzag arrière
LEG = {}


def segment_frame(d, tw=0.0):
    d = unit(d)
    th = math.degrees(math.atan2(-d[2], -d[1]))
    R = RX(th) @ RY(tw)
    assert np.allclose(R @ V(0, -1, 0), d, atol=1e-6)
    return R


def patte_avant():
    S, Eb, Wr = F(-0.86, 3.75, -1.8), F(-0.86, 2.2, -1.65), F(-0.86, 0.6, -1.75)
    R1 = segment_frame(Eb - S)
    grp("epaule_l", S, R1, parent="poitrail")
    L1 = np.linalg.norm(Eb - S)
    cubew("epaule_l", "bras_l", S + R1 @ V(0, -(L1 - 0.4) / 2 + 0.2, 0), (0.7, L1 + 0.4, 1.1), Rw_cube=R1, mat=FUR("patte"), fam="jambe_av_l")
    R2 = segment_frame(Wr - Eb, 5)
    grp("coude_l", Eb, R2, parent="epaule_l")
    L2 = np.linalg.norm(Wr - Eb)
    cubew("coude_l", "avbras_l", Eb + R2 @ V(0, -L2 / 2 + 0.11, 0), (0.66, L2 + 0.42, 0.74), Rw_cube=R2, mat=FUR("patte"), fam="jambe_av_l")
    grp("poignet_l", Wr, RY(-5), parent="coude_l")
    cubew("poignet_l", "pied_av_l", F(-0.86, 0.27, -2.0), (0.74, 0.46, 1.06), Rw_cube=RY(-5), mat=FUR("pied"), fam="jambe_av_l")
    LEG["av_l"] = ["epaule_l", "coude_l", "poignet_l"]


def patte_arriere():
    H, K, J, Ak = F(-1.1, 3.55, 2.45), F(-1.1, 2.1, 1.75), F(-1.1, 1.15, 2.6), F(-1.1, 0.5, 2.45)
    R1 = segment_frame(K - H)
    grp("hanche_l", H, R1, parent="bassin")
    L1 = np.linalg.norm(K - H)
    # cuisse ronde (section en croix), enfoncée dans le bassin : elle ne dépasse du flanc que de 0,25 px
    section("hanche_l", "cuisse_l", H + V(-0.22, 0, 0) + R1 @ V(0, -L1 / 2 + 0.25, 0.1), (1.3, L1 + 1.0, 1.6), n=2, chanf=0.3, long=1, Rw_cube=R1 @ RY(5),
            mat=FUR("cuisse"), fam="jambe_ar_l")
    R2 = segment_frame(J - K, -5)
    grp("genou_l", K, R2, parent="hanche_l")
    L2 = np.linalg.norm(J - K)
    cubew("genou_l", "jambe_l", K + R2 @ V(0, -L2 / 2 + 0.05, 0), (0.72, L2 + 0.4, 0.74), Rw_cube=R2, mat=FUR("patte"), fam="jambe_ar_l")
    R3 = segment_frame(Ak - J)
    grp("jarret_l", J, R3, parent="genou_l")
    L3 = np.linalg.norm(Ak - J)
    cubew("jarret_l", "jarret_l", J + R3 @ V(0, -L3 / 2, 0), (0.58, L3 + 0.35, 0.6), Rw_cube=R3, mat=FUR("patte"), fam="jambe_ar_l")
    grp("pied_ar_l", Ak, RY(5), parent="jarret_l")
    cubew("pied_ar_l", "pied_ar_l", F(-1.1, 0.25, 2.02), (0.78, 0.46, 1.1), Rw_cube=RY(5), mat=FUR("pied"), fam="jambe_ar_l")
    LEG["ar_l"] = ["hanche_l", "genou_l", "jarret_l", "pied_ar_l"]


patte_avant()
patte_arriere()
for k in LEG["av_l"] + LEG["ar_l"]:
    mgrp(k[:-2] + "_r", k)
LEG["av_r"] = [k[:-2] + "_r" for k in LEG["av_l"]]
LEG["ar_r"] = [k[:-2] + "_r" for k in LEG["ar_l"]]

# ------------------------------------------------------------------ queue basse et très touffue : 4 gros segments, plus large au milieu, bout rond
# Elle part du bassin vers l'arrière, descend un peu, puis se relève légèrement au bout (canides.md : renard polaire).
TAIL = []
QL = [1.1, 1.15, 1.2, 1.2, 1.1, 0.95]
QA = [28, 18, 9, 0, -8, -16]                        # pente sous l'horizontale (degrés) : 8 à 10° entre segments
QS = [(1.5, 1.45), (1.92, 1.82), (2.3, 2.15), (2.55, 2.35), (2.38, 2.2), (1.95, 1.8)]   # ≤ 20 % d'un segment au suivant
p = F(0, 4.55, 3.0)
par = "bassin"
for i in range(6):
    R = RX(-QA[i])
    key = f"queue{i + 1}"
    grp(key, p, R, parent=par)
    w, h = QS[i]
    Lq = QL[i]
    z0, z1 = -0.45, Lq + 0.05
    # section en croix, roulis alterné de ±2,5° (remise-aux-regles.md, chaîne de prismes) : les flancs de deux segments voisins
    # ne sont jamais parallèles, donc jamais confondus
    section(key, f"queue{i + 1}_", p + R @ V(0, 0, (z0 + z1) / 2), (w, h, z1 - z0), n=2, chanf=0.25, Rw_cube=R @ RZ(2.5 if i % 2 == 0 else -2.5),
            mat=FUR("queue", seg=i), fam="queue", sym=True)
    TAIL.append(key)
    p = p + R @ V(0, 0, Lq)
    par = key
# bout arrondi (dans le dernier segment)
_Rq = G["queue6"]["Rw"]
section("queue6", "queue_bout", p + _Rq @ V(0, 0.02, 0.38), (1.42, 1.3, 0.9), n=2, chanf=0.36, Rw_cube=_Rq @ RZ(2.5), mat=FUR("queue", seg=6), fam="queue", sym=True)

CRISTAUX = [  # (segment, point local relatif au pivot, direction locale, longueur, section) : couchés dans le sens de la queue
    (5, (0, 0.55, 0.75), (0, 0.45, 0.89), 2.2, 0.56),
    (5, (-0.55, 0.22, 0.8), (-0.4, 0.3, 0.87), 2.0, 0.52),
    (5, (0.55, 0.22, 0.8), (0.4, 0.3, 0.87), 2.0, 0.52),
    (5, (0, 0.0, 1.05), (0, 0.14, 1.0), 2.6, 0.64),
]
EMIT_SCINT = []
for j, (seg, pl, dl, Lc, wc) in enumerate(CRISTAUX):
    gq = TAIL[seg]
    gt = grp(f"trans_cristal{j + 1}", G[gq]["W"], G[gq]["Rw"], parent=gq)
    Rw_ = G[gq]["Rw"]
    d = unit(Rw_ @ V(*dl))
    ref = V(1, 0, 0) if abs(d[0]) < 0.9 else V(0, 0, 1)
    Yc = d
    Xc = unit(np.cross(Yc, ref))
    Zc = np.cross(Xc, Yc)
    roll = math.radians(25 + 17 * j)
    Xr, Zr = math.cos(roll) * Xc + math.sin(roll) * Zc, -math.sin(roll) * Xc + math.cos(roll) * Zc
    Rc = np.column_stack([Xr, Yc, Zr])
    base = G[gq]["W"] + Rw_ @ V(*pl)
    cubew(gt, f"cristal{j + 1}", base + d * (Lc / 2 - 0.55), (wc, Lc, wc), Rw_cube=Rc, mat={"type": "cristal", "L": Lc}, fam="cristal", ao=False,
          faces=["north", "south", "east", "west"])
    cubew(gq, f"cristal{j + 1}_ame", base + d * (0.62 * Lc / 2 - 0.4), (0.2, 0.62 * Lc, 0.2), Rw_cube=Rc @ RY(45), mat={"type": "ame"}, fam="cristal", ao=False)
    if j in (0, 3):
        EMIT_SCINT.append((gq, base + d * (Lc - 0.75)))

# ------------------------------------------------------------------ mèches en volume, couchées sur la surface (peau 0,5 px + âme pleine)
MECHES = []


def meche(g, name, root, along, out, w, Lm, lobes=3, twin=None):
    Y = unit(along)
    Z = unit(np.asarray(out, float) - (np.asarray(out, float) @ Y) * Y)
    X = np.cross(Y, Z)
    rr = math.radians(7 if twin is None else -7)          # le jumeau droit tourne en miroir
    X, Z = math.cos(rr) * X + math.sin(rr) * Z, -math.sin(rr) * X + math.cos(rr) * Z
    Rm = np.column_stack([X, Y, Z])
    c = cubew(g, name, np.asarray(root, float) + Y * (Lm / 2), (w, Lm, 0.5), Rw_cube=Rm, mat={"type": "meche", "lobes": lobes, "L": Lm, "w": w},
              fam="meche", faces=["south", "north"], ao=False, mirror_of=twin)
    MECHES.append(c)
    cubew(g, name.replace("_l", "_ame_l").replace("_r", "_ame_r") if name.endswith(("_l", "_r")) else name + "_ame", np.asarray(root, float) + Y * (Lm * 0.4),
          (w * 0.8, Lm * 0.8, 0.26), Rw_cube=Rm, mat=FUR("meche"), fam="meche", ao=False, mirror_of=None if twin is None else twin.replace("_l", "_ame_l"),
          hidden_ok=False)
    return c


def meche_loc(g, name, root, along, out, w, Lm, lobes=3, tilt=14, twin=None, gref=None):
    gr = G[gref or g]
    Y = unit(np.asarray(along, float))
    Nn = unit(np.asarray(out, float) - (np.asarray(out, float) @ Y) * Y)
    t = math.radians(tilt)
    Y2 = math.cos(t) * Y + math.sin(t) * Nn
    N2 = -math.sin(t) * Y + math.cos(t) * Nn
    return meche(g, name, gr["W"] + gr["Rw"] @ np.asarray(root, float), gr["Rw"] @ Y2, gr["Rw"] @ N2, w, Lm, lobes, twin=twin)


# joues : touffes qui débordent des joues vers l'extérieur et l'arrière (losange du renard polaire)
for tag, sx in (() if True else (("l", -1), ("r", 1))):      # retirées (v4) : plaques qui pendaient sur l'épaule, lues comme des panneaux
    tw = None if tag == "l" else "joue_l"
    meche_loc("tete", f"joue_{tag}", (sx * 1.72, -0.65, 0.1), (sx * 0.55, -0.35, 0.76), (sx, 0, -0.4), 1.2, 1.45, 3, tilt=10, twin=tw)
    tw = None if tag == "l" else "joue_bas_l"
    meche_loc("tete", f"joue_bas_{tag}", (sx * 1.3, -1.25, -0.2), (sx * 0.4, -0.7, 0.6), (sx, -0.4, -0.2), 1.05, 1.25, 3, tilt=10, twin=tw)
meche_loc("cou", "collerette", (0, -0.85, -1.55), (0, 0, 1), (0, -1, 0), 1.95, 1.85, 4, tilt=12)
meche_loc("cou", "nuque", (0, 1.1, -1.45), (0, 0, 1), (0, 1, 0), 1.8, 1.65, 4, tilt=12)
# culotte retirée (v4) : plaque sur l arrière de la cuisse, lue comme un panneau
# meche_loc("hanche_l", "culotte_l", (-0.08, -0.75, 0.72), (0, -1, 0.1), (0, 0, 1), 1.15, 1.35, 3, tilt=14)

# ------------------------------------------------------------------ brume de lévitation, points d'émission
grp("trans_brume", C + V(0, 0.15, 0.2), parent="fam_rot")
grp("ctrl_alpha#brume", C + V(0, 0.15, 0.2), parent="trans_brume", name="ctrl_alpha")
for i, (y, sc, w) in enumerate(((-0.25, 1.0, 5.4), (0.95, 0.72, 4.0))):
    cubew("trans_brume", f"brume{i + 1}", C + V(0, y - 0.15 * 0, 0.2), (w, 0.3, w * 1.35 if i == 0 else w * 1.2), Rw_cube=RY(31 * i), mat={"type": "brume"}, fam="brume",
          faces=["up", "down"], ao=False)
grp("emit_brume", C + V(0, 0.4, 0.4), parent="fam_rot")
grp("ctrl_emit#brume", C + V(0, 0.4, 0.4), parent="emit_brume", name="ctrl_emit")
grp("emit_souffle", F(0, 5.6, -6.6), RX(-90), parent="tete")
grp("ctrl_emit#souffle", F(0, 5.6, -6.6), parent="emit_souffle", name="ctrl_emit")
for i, (gq, pw) in enumerate(EMIT_SCINT):
    grp(f"emit_scintille{i + 1 if i else ''}", pw, parent=gq)

# ================================================================== miroirs : cubes du côté droit (copies des cubes gauches)
LEFT_GROUPS = [k for k in G if k.endswith("_l")]
for c in list(CUBES):
    gl = c["g"]
    if not gl.endswith("_l") or c["name"].endswith("_r") or c["mirror_of"]:
        continue
    gr = gl[:-2] + "_r"
    # centre et orientation en monde, miroir, puis dans le groupe droit
    gL = G[gl]
    cw = gL["W"] + gL["Rw"] @ (c["cu"] - gL["o"])
    Rw_c = gL["Rw"] @ c["Rl"]
    size = c["to"] - c["frm"]
    nm = c["name"].replace("_l", "_r")
    cubew(gr, nm, _mir(cw), size, Rw_cube=M @ Rw_c @ M, mat=c["mat"], faces=c["faces"], mirror_of=c["name"], fam=c["fam"].replace("_l", "_r"), ao=c["ao"], carve=c["carve"],
          hidden_ok=c["hidden_ok"])

BYNAME = {c["name"]: c for c in CUBES}
assert len(BYNAME) == len(CUBES), "noms de cubes en double"


# ================================================================== cinématique (même convention que le renderer et le mod)
def chain(g, upto=None):
    out = []
    while g is not None and g != upto:
        out.append(g)
        g = G[g]["parent"]
    return out


def aff(g, pose, upto=None):
    """Affine (R, t) du groupe g dans le repère de `upto` (exclu) : p_monde = R p_unrot + t."""
    # composition de l'extérieur vers l'intérieur
    Rt, tt = I3.copy(), np.zeros(3)
    for k in reversed(chain(g, upto)):
        gg = G[k]
        a = pose.get(k, {})
        Rk = rot_matrix(*(gg["rest"] + np.asarray(a.get("rotation", (0, 0, 0)), float)))
        Sk = np.asarray(a.get("scale", (1, 1, 1)), float)
        pk = np.asarray(a.get("position", (0, 0, 0)), float)
        # T_k(p) = Rk (Sk (p - o)) + o + pk
        Lk = Rk @ np.diag(Sk)
        tk = -Lk @ gg["o"] + gg["o"] + pk
        tt = Rt @ tk + tt
        Rt = Rt @ Lk
    return Rt, tt


def cube_world_rest(c):
    """(R, t) monde au repos d'un cube (unrot -> monde), avec sa rotation propre."""
    gg = G[c["g"]]
    Rg = gg["Rw"]
    # monde = W + Rw (Rl (p - cu) + cu - o)
    R = Rg @ c["Rl"]
    t = gg["W"] + Rg @ (c["cu"] - gg["o"]) - R @ c["cu"]
    return R, t


# ================================================================== peinture en espace monde
FACE_CORNERS = {
    "north": lambda a, b: [(b[0], b[1], a[2]), (a[0], b[1], a[2]), (a[0], a[1], a[2]), (b[0], a[1], a[2])],
    "south": lambda a, b: [(a[0], b[1], b[2]), (b[0], b[1], b[2]), (b[0], a[1], b[2]), (a[0], a[1], b[2])],
    "east": lambda a, b: [(b[0], b[1], b[2]), (b[0], b[1], a[2]), (b[0], a[1], a[2]), (b[0], a[1], b[2])],
    "west": lambda a, b: [(a[0], b[1], a[2]), (a[0], b[1], b[2]), (a[0], a[1], b[2]), (a[0], a[1], a[2])],
    "up": lambda a, b: [(a[0], b[1], a[2]), (b[0], b[1], a[2]), (b[0], b[1], b[2]), (a[0], b[1], b[2])],
    "down": lambda a, b: [(a[0], a[1], b[2]), (b[0], a[1], b[2]), (b[0], a[1], a[2]), (a[0], a[1], a[2])],
}
FACES6 = ["north", "south", "east", "west", "up", "down"]
SWAP = {"east": "west", "west": "east"}

for c in CUBES:
    R, t = cube_world_rest(c)
    c["R"], c["t"] = R, t
    c["corners"] = {f: np.array([R @ np.array(p) + t for p in FACE_CORNERS[f](c["frm"], c["to"])]) for f in FACES6}
    c["half"] = (c["to"] - c["frm"]) / 2
    c["cw"] = R @ c["cu"] + t


def sdf_box(c, P):
    """Distance signée de P (…,3) monde à la boîte du cube c."""
    q = (P - c["cw"]) @ c["R"]
    d = np.abs(q) - c["half"]
    out = np.linalg.norm(np.maximum(d, 0), axis=-1)
    ins = np.minimum(np.max(d, axis=-1), 0)
    return out + ins


# ------------------------------------------------------------------ bruit
def hash3(ix, iy, iz, seed):
    h = np.sin(ix * 127.1 + iy * 311.7 + iz * 74.7 + seed * 19.19) * 43758.5453
    return h - np.floor(h)


def vnoise(P, seed=0.0):
    i = np.floor(P)
    f = P - i
    u = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (u[..., 0] if dx else 1 - u[..., 0]) * (u[..., 1] if dy else 1 - u[..., 1]) * (u[..., 2] if dz else 1 - u[..., 2])
                out = out + w * hash3(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz, seed)
    return out


def anis(P, Fl, f_across, f_along):
    """Coordonnées étirées le long du sens du poil Fl (…,3)."""
    a = np.sum(P * Fl, axis=-1, keepdims=True)
    return P * f_across + Fl * a * (f_along - f_across)


# ------------------------------------------------------------------ palette (fiche Givre)
F_HI, F_BASE, F_SH, F_DEEP = A((255, 255, 255)), A((240, 247, 255)), A((178, 204, 234)), A((128, 160, 206))
GIVRE = A((150, 200, 236))
G_HI, G_BASE, G_LOW = A((244, 253, 255)), A((120, 208, 238)), A((8, 34, 70))
L_HI, L_BASE, L_LOW = A((210, 245, 255)), A((150, 226, 255)), A((40, 110, 170))
NUITC = A((14, 34, 64))
E_FUR = 0.12
LIGHT = unit(V(0, 0.78, -0.62))

# rangement : coordonnées du renard (repère local au sol, côté gauche pour les miroirs)


def local_fox(P):
    return P - C


def flow(part, Pl, N, c):
    """Sens du poil (unitaire) selon la partie."""
    sh = Pl.shape[:-1]
    one = np.ones(sh)
    if part in ("tronc", "cuisse"):
        Fv = np.stack([0 * one, -0.25 - 0.6 * np.abs(N[..., 0]), one], -1)
    elif part in ("cou",):
        Fv = np.stack([0 * one, -0.8 * one, 0.6 * one], -1)
    elif part in ("tete", "joue", "museau", "paupiere", "sourcil", "machoire"):
        side = np.sign(Pl[..., 0]) * np.abs(N[..., 0])
        Fv = np.stack([0.45 * side, -0.2 - 0.3 * np.abs(N[..., 0]), one], -1)
    elif part in ("patte", "pied"):
        Fv = np.stack([0 * one, -one, 0.15 * one], -1)
    elif part == "queue":
        ax = G[c["g"]]["Rw"] @ V(0, 0, 1)
        Fv = np.broadcast_to(ax, sh + (3,)).copy()
    elif part == "oreille":
        ax = G[c["g"]]["Rw"] @ V(0, 1, 0)
        Fv = np.broadcast_to(ax, sh + (3,)).copy()
    else:
        Fv = np.stack([0 * one, -0.3 * one, one], -1)
    return Fv / np.linalg.norm(Fv, axis=-1, keepdims=True)


TUFT = {"joue": 0.8, "tronc": 0.75, "cou": 0.9, "tete": 0.5, "museau": 0.3, "machoire": 0.35, "patte": 0.4, "pied": 0.3, "cuisse": 0.8, "queue": 1.0, "oreille": 0.4,
        "paupiere": 0.3, "sourcil": 0.3, "meche": 0.9}


PROXY = []          # (W, Rw, centre local, demi-axes) : un superellipsoïde par os, englobant ses cubes de fourrure


def _proxies():
    by = {}
    for o in CUBES:
        if o["mat"].get("type") != "fur" or o["mat"].get("part") in ("paupiere", "sourcil", "meche") or o["fam"] == "meche":
            continue
        by.setdefault(o["g"], []).append(o)
    for g, cs in by.items():
        W, Rw = G[g]["W"], G[g]["Rw"]
        pts = np.concatenate([np.array(list(o["corners"].values())).reshape(-1, 3) for o in cs])
        q = (pts - W) @ Rw
        lo, hi = q.min(0), q.max(0)
        PROXY.append((W, Rw, (lo + hi) / 2, np.maximum((hi - lo) / 2 * 1.12, 0.2)))


def proxy_normal(P, N):
    """Normale lissée : gradient de l'union douce des superellipsoïdes (p = 2,6). Deux cubes voisins, et les paliers d'une
    même section, reçoivent la même lumière à leur frontière : les arêtes ne se lisent plus en « grands carrés »."""
    if not PROXY:
        _proxies()
    def field(X):
        acc = None
        for W, Rw, cc, r in PROXY:
            q = ((X - W) @ Rw - cc) / r
            d = (np.sum(np.abs(q) ** 2.6, -1) ** (1 / 2.6) - 1) * r.min()
            acc = d if acc is None else -0.3 * np.log(np.exp(-acc / 0.3) + np.exp(-d / 0.3))
        return acc
    e = 0.04
    g = np.stack([field(P + e * V(*ax)) - field(P - e * V(*ax)) for ax in np.eye(3)], -1)
    n = np.linalg.norm(g, axis=-1, keepdims=True)
    Ns = np.where(n > 1e-6, g / np.maximum(n, 1e-9), N)
    Ns = np.where((np.sum(Ns * N, -1) < 0)[..., None], N, Ns)        # jamais à contre-sens de la face
    Nb = 0.3 * N + 0.7 * Ns
    return Nb / np.linalg.norm(Nb, axis=-1, keepdims=True)


def fur_color(P, N, part, c, ao):
    """Fourrure peinte en espace monde (P au repos, N normale) : mèches fines dans le sens du poil, dégradé doux
    (dos blanc, ventre et dessous bleutés), liseré d'occlusion entre les masses, marques givrées."""
    Pl = local_fox(P)
    Ps = Pl.copy()
    Ps[..., 0] = np.abs(Ps[..., 0])                     # champ symétrique (UV partagées gauche/droite)
    Fl = flow(part, Pl, N, c)
    Fs = Fl.copy()
    Fs[..., 0] = Fl[..., 0] * np.where(Pl[..., 0] < 0, -1.0, 1.0)
    # lumière douce sur l'enveloppe arrondie : dessus et avant plus clairs, flancs qui tournent
    if part not in ("paupiere", "sourcil"):
        N = proxy_normal(P, N)
    k = 0.5 + 0.5 * np.sum(N * LIGHT, -1)
    lum = 0.85 + 0.19 * k
    # dégradé dos / ventre : la normale et la hauteur dans la masse
    down = np.clip(-N[..., 1], 0, 1)
    side = 1 - np.abs(N[..., 1])
    ventre = 0.75 * down
    if part in ("tronc", "cuisse"):
        ventre = ventre + side * 0.55 * smv(3.6 - Pl[..., 1], 0.0, 1.2)
    if part == "cou":
        ventre = ventre + 0.35 * np.clip(-N[..., 2], 0, 1) * smv(5.6 - Pl[..., 1], 0, 0.9)
    if part in ("tete", "joue", "machoire"):
        ventre = ventre + side * 0.4 * smv(6.0 - Pl[..., 1], 0.0, 0.8)
    if part == "queue":
        ventre = ventre * 0.6
    lum = lum * (1 - 0.2 * np.clip(ventre, 0, 1))
    # mèches fines dans le sens du poil (deux octaves), touffes à peine marquées
    st = (vnoise(anis(Ps, Fs, 26.0, 1.9), 3.0) - 0.5) + 0.5 * (vnoise(anis(Ps, Fs, 52.0, 3.6), 11.0) - 0.5)
    st = np.sign(st) * np.abs(st) ** 0.8
    Lt = TUFT.get(part, 0.7)
    ph = np.sum(Ps * Fs, -1) / Lt + vnoise(anis(Ps, Fs, 3.0 / Lt, 0.3), 7.0) * 0.7
    fr = ph - np.floor(ph)
    tuft = smv(fr, 0.0, 0.9) - 0.5
    calm = 0.55 if part in ("museau", "paupiere", "sourcil", "machoire") else 1.0
    var = calm * (0.085 * st + 0.025 * tuft)
    lum = lum * (1 + var) * ao
    col = np.where((lum >= 1)[..., None], lerp(F_BASE, F_HI, np.clip((lum - 1) / 0.06, 0, 1)[..., None]),
                   lerp(F_BASE, F_SH, np.clip((1 - lum) / 0.24, 0, 1)[..., None]))
    col = np.where((lum < 0.76)[..., None], lerp(F_SH, F_DEEP, np.clip((0.76 - lum) / 0.2, 0, 1)[..., None]), col)
    # marques givrées : dos des bouts d'oreilles, chaussettes, bout de queue, sourcils
    m = np.zeros(P.shape[:-1])
    if part == "oreille":
        m = smv(Pl[..., 1], 8.5, 9.1) * 0.8 * np.clip(0.4 + N[..., 2] * 0.8, 0, 1)
    if part in ("patte", "pied"):
        m = smv(-Pl[..., 1], -1.2, -0.35) * 0.14
    if part == "queue":
        seg = c["mat"].get("seg", 0)
        m = np.full(P.shape[:-1], 0.0) + (seg >= 4) * 0.15 + (seg >= 5) * 0.15 + (seg >= 6) * 0.2
    if part == "sourcil":
        ex = (np.abs(Pl[..., 0]) - abs(EYE_C[0])) / 0.55
        yc = BROW_Y + 0.03 * (1 - ex * ex) - 0.03 * ex
        th = 0.08 * (1 - 0.5 * np.clip(ex, 0, 1)) * (np.abs(ex) < 0.95)
        m = 0.8 * ((np.abs(Pl[..., 1] - yc) < th) | ((N[..., 1] > 0.5) & (np.abs(ex) < 0.9 - 0.3 * np.clip(ex, 0, 1)))).astype(float)
    if part == "tete":
        ex = (np.abs(Pl[..., 0]) - abs(EYE_C[0])) / 0.62
        ey = (Pl[..., 1] - (LID_TOP + 0.03)) / 0.1
        m = np.maximum(m, 0.3 * np.clip(1 - ex * ex - ey * ey, 0, 1) * (Pl[..., 2] < -4.8))
    col = lerp(col, GIVRE * np.clip(lum, 0.7, 1.05)[..., None], np.clip(m, 0, 1)[..., None])
    return col


def visage(P, N, col, part):
    """Détails peints du visage (repère du renard) : paupière inférieure, larmier, bouche fermée, coussinets et moustaches."""
    Pl = local_fox(P)
    x, y, z = np.abs(Pl[..., 0]), Pl[..., 1], Pl[..., 2]
    ex0, ey0 = abs(EYE_C[0]), EYE_C[1]
    if part == "tete":
        dx = (x - ex0) / (EYE_R[0] + 0.03)
        yb = ey0 - 0.1 * (x - ex0) / EYE_R[0] - (EYE_R[1] + 0.02) * np.sqrt(np.clip(1 - dx * dx, 0, 1))
        front = z < -4.8
        trait = front & (np.abs(dx) < 1.0) & (np.abs(y - (yb - 0.025)) < 0.03)
        col = np.where(trait[..., None], lerp(col, A((70, 100, 150)), 0.7), col)
        bour = front & (np.abs(dx) < 0.95) & (y < yb - 0.06) & (y > yb - 0.2)
        col = np.where(bour[..., None], np.minimum(col * 1.04, 255), col)
        coin = front & (np.abs((x - 0.24) - (ey0 - 0.1 - y) * 0.45) < 0.035) & (y < ey0 - 0.12) & (y > ey0 - 0.42)
        col = np.where(coin[..., None], lerp(col, A((120, 150, 195)), 0.55), col)
    if part == "museau":
        side = np.abs(N[..., 0]) > 0.5
        front = N[..., 2] < -0.5
        pts = np.zeros_like(x, bool)
        for (zz, yy) in ((-6.25, 5.92), (-6.05, 5.86), (-6.3, 5.78), (-6.1, 5.72), (-5.9, 5.8)):
            pts |= (np.hypot(z - zz, y - yy) < 0.04)
        col = np.where((side & pts)[..., None], A((110, 140, 185)), col)
        for (y0, pente) in ((5.92, 0.2), (5.82, 0.04), (5.72, -0.12)):
            mo = side & (np.abs(y - (y0 + pente * (z + 6.1))) < 0.02) & (z > -6.45) & (z < -5.0)
            col = np.where(mo[..., None], lerp(col, A((160, 188, 225)), 0.75), col)
        # bouche fermée : un trait fin au bas du museau, qui remonte en sourire vers l'arrière ; philtrum sous la truffe
        ybot = 5.55 + 0.17 * np.clip((z + 6.65) / 2.1, 0, 1)
        levre = side & (np.abs(y - (ybot + 0.05 + 0.12 * smv(z, -5.6, -4.9))) < 0.025) & (z < -4.8)
        col = np.where(levre[..., None], lerp(col, A((70, 92, 136)), 0.75), col)
        ph = front & (x < 0.028) & (y < 6.12) & (y > 5.62)
        bouche = front & (np.abs(y - (5.62 - 0.08 * np.clip(x / 0.3, 0, 1) ** 2 + 0.1 * smv(x, 0.3, 0.55))) < 0.025) & (x < 0.55)
        col = np.where((ph | bouche)[..., None], lerp(col, A((70, 92, 136)), 0.75), col)
    if part == "machoire":
        haut = N[..., 1] > 0.5
        col = np.where(haut[..., None], A((52, 64, 98)), col)                       # intérieur de la gueule (vu seulement ouverte)

    if part == "paupiere":
        bord = N[..., 1] < -0.5
        col = np.where(bord[..., None], A((44, 66, 108)), col)                       # cils
    return col


def p_oeil(P, c):
    """Oeil en amande, grand et ouvert : iris cyan en dégradé, pupille, deux reflets, ombre de la paupière, cerne fin."""
    Pl = local_fox(P)
    x = -(np.abs(Pl[..., 0]) - abs(EYE_C[0])) / EYE_R[0]          # x > 0 : vers le museau
    y = (Pl[..., 1] - EYE_C[1]) / EYE_R[1]
    r = np.hypot(x * 0.9, y + 0.04)
    ir = np.clip(r / 0.86, 0, 1)
    col = lerp(L_HI, L_BASE, smv(ir, 0.0, 0.55)[..., None])
    col = lerp(col, A((50, 130, 190)), smv(ir, 0.6, 1.0)[..., None] * 0.85)
    col = lerp(col, A((30, 70, 130)), smv(y, 0.25, 1.0)[..., None] * 0.5)
    iris = r < 0.86
    blanc = lerp(A((236, 246, 255)), A((190, 214, 238)), smv(y, 0.0, 1.0)[..., None])
    col = np.where(iris[..., None], col, blanc)
    pup = np.hypot(x * 0.95, (y + 0.06) * 0.85) < 0.36
    col = np.where(pup[..., None], lerp(NUITC, A((26, 56, 100)), smv(r, 0.1, 0.36)[..., None]), col)
    cerne = (r > 0.86) & (r < 0.95)
    col = np.where(cerne[..., None], A((36, 64, 104)), col)
    hl1 = np.hypot(x + 0.28, y - 0.32) < 0.2
    hl2 = np.hypot(x - 0.3, y + 0.34) < 0.09
    col = np.where((hl1 | hl2)[..., None], A((255, 255, 255)), col)
    e = lerp(A((90, 180, 230)), A((30, 90, 150)), ir[..., None]) * iris[..., None]
    e = np.where(pup[..., None] | cerne[..., None], A((6, 14, 30)), e)
    e = np.where((hl1 | hl2)[..., None], A((225, 225, 225)), e)
    return col, np.ones(P.shape[:-1], bool), e


def p_nez(P, N):
    """Truffe ronde peinte : coins arrondis (découpe), dégradé, narines, reflet."""
    q = P - (NEZ_C)
    x, y, z = np.abs(q[..., 0]), q[..., 1], q[..., 2]
    col = lerp(A((66, 80, 108)), A((24, 30, 46)), smv(-y, -0.17, 0.17)[..., None])
    col = np.where((N[..., 1] > 0.5)[..., None], lerp(A((52, 62, 86)), A((36, 44, 64)), smv(np.abs(z), 0.0, 0.15)[..., None]), col)
    front = N[..., 2] < -0.5
    top = N[..., 1] > 0.5
    hl = top & (np.hypot(x / 1.8, z + 0.05) < 0.08)
    hl |= front & (np.abs(y - 0.11) < 0.035) & (x < 0.16)
    col = np.where(hl[..., None], lerp(col, A((176, 200, 230)), 0.8), col)
    nar = front & (np.hypot((x - 0.1) / 0.06, (y + 0.03) / 0.045) < 1)
    col = np.where(nar[..., None], A((10, 14, 26)), col)
    # coins arrondis : la face avant et les faces latérales découpées en superellipse
    mask = np.ones(x.shape, bool)
    fm = ((x / 0.25) ** 2.4 + (np.abs(y) / 0.19) ** 2.4) < 1.0
    mask = np.where(front, fm, mask)
    sm_ = ((np.abs(z) / 0.15) ** 2.4 + (np.abs(y) / 0.19) ** 2.4) < 1.0
    mask = np.where(np.abs(N[..., 0]) > 0.5, sm_, mask)
    tm = ((x / 0.25) ** 2.4 + (np.abs(z) / 0.15) ** 2.4) < 1.0
    mask = np.where(np.abs(N[..., 1]) > 0.5, tm, mask)
    return col, mask


def p_langue(P, N):
    Pl = local_fox(P)
    col = lerp(A((236, 150, 168)), A((200, 108, 132)), smv(np.abs(Pl[..., 0]), 0.0, 0.28)[..., None])
    sil = np.abs(Pl[..., 0]) < 0.03
    return np.where(sil[..., None], A((190, 98, 122)), col)


def p_oreille_int(P, c, N):
    """Intérieur de l'oreille : fourrure blanche en touffes, ombre bleutée au fond."""
    Wl = EAR_W if (P[..., 0] - C[0]).mean() < 0 else _mir(EAR_W)
    Rl = EAR_R if (P[..., 0] - C[0]).mean() < 0 else M @ EAR_R @ M
    q = (P - Wl) @ Rl
    x, y = q[..., 0], q[..., 1]
    if (P[..., 0] - C[0]).mean() > 0:
        x = -x
    hw = 0.44 * np.clip(1 - (y - 0.1) / 1.0, 0, 1) ** 0.7
    k = np.clip(np.abs(x) / np.maximum(hw, 1e-3), 0, 1)
    fond = (1 - k) * smv(-y, -1.0, -0.15)
    col = lerp(A((246, 250, 255)), A((150, 182, 224)), (0.8 * fond)[..., None])
    meche = (np.abs(np.sin(x * 40 - y * 9)) > 0.86) & (y < 0.75)
    col = np.where(meche[..., None], lerp(col, A((255, 255, 255)), 0.8), col)
    return col


def p_oreille_plaque(P, N, c, ao):
    """Plaque d'oreille (peau) : triangle arrondi ; face avant = creux clair à fond bleuté et touffes, liseré de fourrure ;
    face arrière = fourrure, pointe givrée."""
    droite = (P[..., 0] - C[0]).mean() > 0
    Wl = _mir(EAR_W) if droite else EAR_W
    Rl = M @ EAR_R @ M if droite else EAR_R
    q = (P - Wl) @ Rl
    x, y = np.abs(q[..., 0]), q[..., 1]
    hw = EAR_HW * np.clip(1 - y / EAR_H, 0, 1) ** 0.6
    mask = (x < hw) & (y > -0.05)
    if c["mat"]["face"] == "dos":
        return fur_color(P, N, "oreille", c, ao), mask
    col = fur_color(P, N, "oreille", c, ao)
    hin = np.clip(hw - 0.14, 0, None)
    k = np.clip(x / np.maximum(hin, 1e-3), 0, 1)
    inner = (x < hin) & (y > 0.12) & (y < EAR_H - 0.28)
    fond = (1 - k) * smv(-y, -1.15, -0.1)
    ci = lerp(A((246, 250, 255)), A((150, 182, 224)), (0.85 * fond)[..., None])
    meche = (np.abs(np.sin(x * 34 - y * 8)) > 0.88) & (y < 0.7)
    ci = np.where(meche[..., None], lerp(ci, A((255, 255, 255)), 0.85), ci)
    return np.where(inner[..., None], ci, col), mask


def p_cristal(P, c):
    """Cristal trans_ : coordonnées le long de l'axe (v) et en travers (d), pointe en biseau."""
    q = (P - c["cw"]) @ c["R"]
    L = c["mat"]["L"]
    hw = c["half"][0]
    v = q[..., 1] / L + 0.5                 # 0 base, 1 pointe
    d = np.maximum(np.abs(q[..., 0]), np.abs(q[..., 2])) / hw
    d2 = np.minimum(np.abs(q[..., 0]), np.abs(q[..., 2])) / hw
    lat = np.where(np.abs(q[..., 0]) > np.abs(q[..., 2]) - 1e-6, np.abs(q[..., 2]), np.abs(q[..., 0])) / hw
    taper = np.where(v < 0.6, 1.0, np.clip((1.0 - v) / 0.4, 0, 1) ** 0.85)
    mask = lat < taper * 1.0
    cen = np.clip(1 - lat / np.maximum(taper, 1e-3), 0, 1)
    k = 0.2 + 0.7 * v + 0.1 * (1 - cen)
    col = np.where((k < 0.5)[..., None], lerp(G_LOW, G_BASE, (k * 2)[..., None]), lerp(G_BASE, G_HI, ((k - 0.5) * 2)[..., None]))
    arete = lat > taper - 0.22
    col = np.where(arete[..., None], lerp(col, G_HI, 0.85), col)
    chev = np.mod(v * L * 3.2 + lat * 1.2, 1.0) < 0.1
    col = np.where((chev & ~arete)[..., None], lerp(col, G_HI, 0.45), col)
    al = 150 + 60 * cen * (1 - 0.4 * v)
    al = np.where(arete, 220, al)
    e = lerp(A((50, 130, 190)), A((140, 220, 255)), np.clip(v * 1.1, 0, 1)[..., None]) * (0.6 + 0.4 * cen[..., None])
    return col, mask, al, e


def p_meche(P, c, N, ao):
    """Mèche : contour en lobes arrondis au bout libre ; couleur du champ de fourrure sous elle, racine plus sombre."""
    q = (P - c["cw"]) @ c["R"]
    L, w = c["mat"]["L"], c["mat"]["w"]
    t = q[..., 1] / L + 0.5                 # 0 racine, 1 bout
    x = q[..., 0] / (w / 2)                 # −1..1
    n = c["mat"]["lobes"]
    lob = 0.5 + 0.5 * np.cos(np.pi * (x * n / 2 * 2 - 0) % (2 * np.pi) - np.pi)
    xs = (x + 1) / 2 * n
    fr = xs - np.floor(xs)
    bord = 0.78 + 0.22 * np.sqrt(np.clip(1 - (2 * fr - 1) ** 2, 0, 1))
    env = np.sqrt(np.clip(1 - x * x, 0, 1)) ** 0.35
    mask = (t < bord * (0.6 + 0.4 * env)) & (np.abs(x) < 0.98)
    outer = (N @ np.zeros(3) + np.sum(N * (c["R"] @ V(0, 0, 1)), -1)) > 0
    col = fur_color(P, N, "meche", c, ao)
    col = np.where(outer[..., None], col, col * 0.9)
    return col, mask


def p_brume(P, c):
    q = (P - c["cw"]) @ c["R"]
    x, z = q[..., 0] / c["half"][0], q[..., 2] / c["half"][2]
    r, th = np.hypot(x, z), np.arctan2(z, x)
    sw = 0.5 + 0.5 * np.sin(3 * th + 6 * r)
    a = 120 * np.exp(-((r - 0.55) / 0.26) ** 2) * (0.5 + 0.5 * sw) + 40 * np.exp(-(r / 0.45) ** 2)
    a = np.where(r < 0.97, a, 0)
    col = lerp(A((200, 232, 250)), A((255, 255, 255)), sw[..., None])
    return col, a > 16, np.clip(a, 16, 140)


# ------------------------------------------------------------------ faces : taille, visibilité, UV
DENS_TETE = 1.18          # visage un peu plus fin que le corps (≤ 1,25, fiche modélisation organique)
DENS_QUEUE = 0.88         # queue un peu moins (écart ≤ 1,25 avec la croupe)


def face_info(c, f):
    P4 = c["corners"][f]
    w = np.linalg.norm(P4[1] - P4[0])
    h = np.linalg.norm(P4[3] - P4[0])
    n = np.cross(P4[3] - P4[0], P4[1] - P4[0])
    n = n / max(np.linalg.norm(n), 1e-9)
    return P4, w, h, n


def same_bone_hidden(c, f):
    """Face entièrement enfouie dans d'autres cubes opaques du même groupe (au repos) ?"""
    P4, w, h, n = face_info(c, f)
    s, t = np.meshgrid(np.linspace(0.0, 1.0, 7), np.linspace(0.0, 1.0, 7))
    P = P4[0] + (P4[1] - P4[0]) * s[..., None] + (P4[3] - P4[0]) * t[..., None] + n * 0.002
    hid = np.zeros(s.shape, bool)
    for o in CUBES:
        if o is c or (o["g"] != c["g"] and not (o["fam"] == c["fam"] and c["fam"] in ("tronc", "queue"))) or o["mat"].get("type") not in ("fur", "nez"):
            continue
        hid |= sdf_box(o, P) < -0.004
    return hid.all()


USED = []
for c in CUBES:
    c["uv"] = {}
    c["paint"] = {}
for c in CUBES:
    if c["mirror_of"]:
        continue
    if c["mat"].get("type") == "brume":
        continue
    for f in c["faces"]:
        if c["mat"].get("type") in ("fur", "nez") and same_bone_hidden(c, f):
            continue
        if c["sym"] and f == "east":
            continue                     # cube centré : face est = miroir de la face ouest
        P4, w, h, n = face_info(c, f)
        k = DENS_TETE if c["fam"] in ("tete", "oeil", "paupiere", "sourcil", "nez", "oreille", "oreille_int") else DENS_QUEUE if c["fam"] in ("queue", "cristal") else 1.0
        c["paint"][f] = (w, h, k)
TOTAL = sum(w * h * k * k for c in CUBES for (w, h, k) in c["paint"].values())


def pack(dens):
    items = []
    for c in CUBES:
        for f, (w, h, k) in c["paint"].items():
            items.append((c["name"], f, max(1, int(round(w * dens * k))), max(1, int(round(h * dens * k)))))
    items.append(("_clair", "x", 2, 2))
    for nm, W in (("brume", 24), ("souffle", 20), ("scintille", 16)):
        items.append(("_part_" + nm, "x", W, W))
    items.append(("_brume", "x", 40, 40))
    items.sort(key=lambda it: (-it[3], -it[2]))
    uv, x, y, shelf = {}, 0, 0, 0
    for nm, f, w, h in items:
        if x + w > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        if y + h > TEX or w > TEX:
            return None
        uv[(nm, f)] = (x, y, x + w, y + h)
        x += w + 1
        shelf = max(shelf, h)
    return uv


DENS = 34.0
while (UVR := pack(DENS)) is None:
    DENS -= 0.25
FILL = sum((r[2] - r[0]) * (r[3] - r[1]) for r in UVR.values()) / TEX ** 2
CLEAR = list(UVR[("_clair", "x")])

tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
TRANS_RECTS = []
OCC = [o for o in CUBES if o["mat"].get("type") in ("fur", "nez") and o["ao"]]
AO_PAIRS_OFF = {("tronc", "tronc"), ("tete", "tete")}


def ao_field(c, P, n):
    """Occlusion : distance aux autres masses (pas celles de la même famille), au repos."""
    ao = np.ones(P.shape[:-1])
    cen = P.reshape(-1, 3).mean(0)
    rad = np.linalg.norm(P.reshape(-1, 3) - cen, axis=1).max()
    for o in OCC:
        if o is c or o["fam"] == c["fam"] or (c["fam"], o["fam"]) in AO_PAIRS_OFF:
            continue
        if np.linalg.norm(o["cw"] - cen) > rad + np.linalg.norm(o["half"]) + 0.7:
            continue
        d = sdf_box(o, P + n * 0.02)
        st = 0.34 if o["fam"] in ("tete", "tronc", "queue") else 0.3
        ao = np.minimum(ao, 1 - st * np.clip(1 - np.maximum(d, 0) / 0.42, 0, 1) ** 1.5)      # liseré net entre les masses
    return ao


def paint_face(c, f, rect):
    P4, w, h, n = face_info(c, f)
    u0, v0, u1, v1 = rect
    W, H = u1 - u0, v1 - v0
    s = (np.arange(W * SS) + 0.5) / (W * SS)
    t = (np.arange(H * SS) + 0.5) / (H * SS)
    S_, T_ = np.meshgrid(s, t)
    P = P4[0] + (P4[1] - P4[0]) * S_[..., None] + (P4[3] - P4[0]) * T_[..., None]
    N = np.broadcast_to(n, P.shape).copy()
    typ = c["mat"].get("type")
    alpha = np.ones(S_.shape, bool)
    aval = None
    e = None
    if typ == "fur":
        ao = ao_field(c, P, n)
        col = fur_color(P, N, c["mat"]["part"], c, ao)
        col = visage(P, N, col, c["mat"]["part"])
        e = col * E_FUR
    elif typ == "nez":
        col, alpha = p_nez(P, N)
    elif typ == "oeil":
        col, alpha, e = p_oeil(P, c)
    elif typ == "langue":
        col = p_langue(P, N)
    elif typ == "oreille_int":
        col = p_oreille_int(P, c, N)
        e = col * E_FUR
    elif typ == "oreille_plaque":
        col, alpha = p_oreille_plaque(P, N, c, ao_field(c, P, n))
        e = col * E_FUR
    elif typ == "cristal":
        col, alpha, aval, e = p_cristal(P, c)
    elif typ == "ame":
        q = (P - c["cw"]) @ c["R"]
        v = np.clip(q[..., 1] / (2 * c["half"][1]) + 0.5, 0, 1)
        col = lerp(L_LOW, L_HI, v[..., None])
        e = lerp(A((70, 150, 200)), A((170, 230, 252)), v[..., None])
    elif typ == "meche":
        col, alpha = p_meche(P, c, N, np.ones(S_.shape))
        e = col * E_FUR
    elif typ == "brume":
        col, alpha, aval = p_brume(P, c)
    else:
        raise ValueError(typ)
    if typ == "fur" and c["mat"]["part"] == "sourcil":
        Pl = local_fox(P)
        ex = (np.abs(Pl[..., 0]) - abs(EYE_C[0])) / 0.55
        th = 0.23 - 0.12 * np.clip((ex + 1) / 2, 0, 1) ** 1.2
        yc = BROW_Y + 0.05 * (1 - ex * ex) - 0.05 * ex
        top, bot = yc + th / 2, yc - th / 2
        alpha &= (Pl[..., 1] < top + 0.003) & (Pl[..., 1] > bot - 0.003) & (ex < 0.97) & (ex > -0.97)
    # orbites et creux d'oreilles découpés ; texels enfouis dans un cube opaque du même groupe : transparents
    if c["carve"]:
        Pm = P.copy()
        if (P[..., 0] - C[0]).mean() > 0:
            Pm[..., 0] = 2 * C[0] - Pm[..., 0]
        Pl = local_fox(P)
        alpha &= ~_orbite(Pl)
        if c["fam"] == "oreille":
            alpha &= ~_creux(Pm, EAR_W, EAR_R)
    if typ in ("fur", "nez"):
        for o in CUBES:
            if o is c or (o["g"] != c["g"] and not (o["fam"] == c["fam"] and c["fam"] in ("tronc", "queue"))) or o["mat"].get("type") not in ("fur", "nez") or not c["hidden_ok"]:
                continue
            alpha &= ~(sdf_box(o, P + N * 0.002) < -0.004)
    # sous-échantillonnage
    col_s = col.reshape(H, SS, W, SS, 3).mean((1, 3))
    al_s = alpha.reshape(H, SS, W, SS).mean((1, 3)) >= 0.5
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(col_s, 0, 255).astype(np.uint8) & 0xFC
    if aval is not None:
        av = aval.reshape(H, SS, W, SS).mean((1, 3))
        out[..., 3] = np.where(al_s, np.clip(av, 1, 254), 0).astype(np.uint8)
        TRANS_RECTS.append(rect)
    else:
        out[..., 3] = np.where(al_s, 255, 0)
    out[..., :3] *= (out[..., 3:] > 0)
    tex[v0:v1, u0:u1] = out
    if e is not None:
        e_s = e.reshape(H, SS, W, SS, 3).mean((1, 3))
        oe = np.zeros((H, W, 4), np.uint8)
        on = al_s & (e_s.max(-1) > 6)
        oe[..., :3] = np.where(on[..., None], np.clip(e_s, 0, 225), 0).astype(np.uint8)
        oe[..., 3] = np.where(on, 255, 0)
        tex_e[v0:v1, u0:u1] = oe


for c in CUBES:
    for f in c["paint"]:
        paint_face(c, f, UVR[(c["name"], f)])


def _brume_tile():
    u0, v0, u1, v1 = UVR[("_brume", "x")]
    W = u1 - u0
    s_ = (np.arange(W) + 0.5) / W
    u, v = np.meshgrid(s_, s_)
    x, z = u * 2 - 1, v * 2 - 1
    r, th = np.hypot(x, z), np.arctan2(z, x)
    sw = 0.5 + 0.5 * np.sin(3 * th + 6 * r)
    a = 120 * np.exp(-((r - 0.55) / 0.26) ** 2) * (0.5 + 0.5 * sw) + 40 * np.exp(-(r / 0.45) ** 2)
    a = np.where(r < 0.97, a, 0)
    col = lerp(A((200, 232, 250)), A((255, 255, 255)), sw[..., None])
    out = np.zeros((W, W, 4), np.uint8)
    out[..., :3] = (col.astype(np.uint8) & 0xFC) * (a > 16)[..., None]
    out[..., 3] = np.where(a > 16, np.clip(a, 16, 140), 0).astype(np.uint8)
    tex[v0:v1, u0:u1] = out
    TRANS_RECTS.append((u0, v0, u1, v1))


_brume_tile()


def uv_of(c, f):
    """UV d'une face : propre, miroir de la face ouest (cube centré), ou miroir du jumeau gauche ; sinon texel transparent."""
    if c["mat"].get("type") == "brume":
        return list(UVR[("_brume", "x")])
    if c["mirror_of"]:
        tw = BYNAME[c["mirror_of"]]
        f2 = SWAP.get(f, f)
        r = uv_of(tw, f2)
        if r == CLEAR:
            return CLEAR
        return [r[2], r[1], r[0], r[3]]
    if c["sym"] and f == "east" and "west" in c["paint"]:
        r = UVR[(c["name"], "west")]
        return [r[2], r[1], r[0], r[3]]
    if f in c["paint"]:
        return list(UVR[(c["name"], f)])
    return CLEAR


def png_b64(arr, fn):
    im = Image.fromarray(arr, "RGBA")
    im.save(fn, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


# ================================================================== éléments et outliner
elements = []
for c in CUBES:
    faces = {}
    for f in FACES6:
        uv = uv_of(c, f) if f in c["faces"] else CLEAR
        faces[f] = {"uv": [round(float(v), 2) for v in uv], "texture": 0}
    e = {"name": c["name"], "type": "cube", "uuid": c["uuid"], "from": [round(float(v), 4) for v in c["frm"]], "to": [round(float(v), 4) for v in c["to"]],
         "origin": [round(float(v), 4) for v in c["cu"]], "box_uv": False, "faces": faces}
    rr = euler(c["Rl"])
    if any(abs(r) > 1e-4 for r in rr):
        e["rotation"] = [round(float(v), 3) for v in rr]
    elements.append(e)


def bone_node(k):
    g = G[k]
    return {"name": g["name"], "origin": [round(float(v), 4) for v in g["o"]], "uuid": g["uuid"], "rotation": [round(float(v), 3) for v in g["rest"]],
            "children": list(g["ids"]) + [bone_node(ch) for ch in g["children"]]}


outliner = [bone_node("fam_sol")]

# particules modélisées (recette validée : un seul cube de 0,3 px, face up seule, au-dessus du pivot)
PART_TEX = {}


def part_tile(nom, W, painter):
    PART_TEX[nom] = (W, painter)


def _bouffee(seed, a_max, clair, ombre):
    def f(W):
        s = (np.arange(W) + 0.5) / W
        u, v = np.meshgrid(s, s)
        x, y = u * 2 - 1, v * 2 - 1
        rng = np.random.default_rng(seed)
        d = np.full(u.shape, 9.0)
        for _ in range(6):
            cx, cy, r = rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(0.45, 0.62)
            d = np.minimum(d, np.hypot(x - cx, y - cy) / r)
        a = np.clip(1 - d, 0, 1) ** 0.8 * a_max * 1.25
        lum = np.clip(1 - np.hypot(x + 0.3, y + 0.35) / 1.4, 0, 1)
        col = lerp(A(ombre), A(clair), lum[..., None])
        out = np.zeros((W, W, 4), np.uint8)
        out[..., :3] = col.astype(np.uint8)
        out[..., 3] = np.where(a > 14, np.clip(a, 14, 230), 0).astype(np.uint8)
        out[..., :3] *= (out[..., 3:] > 0)
        return out, None
    return f


def _scintille(W):
    s = (np.arange(W) + 0.5) / W
    u, v = np.meshgrid(s, s)
    x, y = np.abs(u * 2 - 1), np.abs(v * 2 - 1)
    et = (x ** 0.55 + y ** 0.55) < 0.75
    k = np.clip(1 - np.hypot(x, y), 0, 1)
    col = lerp(L_BASE, A((255, 255, 255)), k[..., None])
    out = np.zeros((W, W, 4), np.uint8)
    out[..., :3] = col.astype(np.uint8) * et[..., None]
    out[..., 3] = et * 255
    e = np.zeros((W, W, 4), np.uint8)
    e[..., :3] = (lerp(A((120, 200, 240)), A((225, 225, 225)), k[..., None]) * et[..., None]).astype(np.uint8)
    e[..., 3] = et * 255
    return out, e


PART_UV = {}
for nom, W, painter, trans in (("brume", 24, _bouffee(5, 150, (250, 253, 255), (190, 222, 240)), True),
                               ("souffle", 20, _bouffee(9, 190, (255, 255, 255), (170, 220, 245)), True),
                               ("scintille", 16, _scintille, False)):
    x0, y0, x1, y1 = UVR[("_part_" + nom, "x")]
    im, ie = painter(W)
    tex[y0:y1, x0:x1] = im
    if ie is not None:
        tex_e[y0:y1, x0:x1] = ie
    PART_UV[nom] = (x0, y0, x1, y1, trans)
tex_b64 = png_b64(tex, f"{NOM}.png")
tex_e_b64 = png_b64(tex_e, f"{NOM}_e.png")

for nom, taille in (("brume", 1.8), ("souffle", 1.1), ("scintille", 0.7)):
    u0, v0, u1, v1, trans = PART_UV[nom]
    root = {"name": f"particle_{nom}", "origin": [0, 0, 0], "uuid": str(_uuid.uuid4()), "rotation": [0, 0, 0], "children": []}
    holder = root
    if trans:
        sub = {"name": f"trans_particule_{nom}", "origin": [0, 0, 0], "uuid": str(_uuid.uuid4()), "rotation": [0, 0, 0], "children": []}
        root["children"].append(sub)
        holder = sub
    h = taille / 2
    uid = str(_uuid.uuid4())
    elements.append({"name": nom, "type": "cube", "uuid": uid, "from": [-h, 0.3, -h], "to": [h, 0.6, h], "origin": [0, 0.45, 0], "box_uv": False,
                     "faces": {"up": {"uv": [u0, v0, u1, v1], "texture": 0}}})
    holder["children"].append(uid)
    outliner.append(root)

# semi-transparence seulement dans les tuiles trans_ (cristaux, brume, particules translucides)
semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
allowed = np.zeros(semi.shape, bool)
for (u0, v0, u1, v1) in TRANS_RECTS:
    allowed[v0:v1, u0:u1] = True
for nom in ("brume", "souffle"):
    u0, v0, u1, v1, _ = PART_UV[nom]
    allowed[v0:v1, u0:u1] = True
assert not (semi & ~allowed).any(), "semi-transparence hors trans_"

# ================================================================== IK des pattes
CONTACT = {}
for side in ("l", "r"):
    for kind, leaf in (("av", f"poignet_{side}"), ("ar", f"pied_ar_{side}")):
        pcs = [c for c in CUBES if c["g"] == leaf and c["name"].startswith("pied")]
        lo = np.min([c["frm"] for c in pcs], axis=0)
        hi = np.max([c["to"] for c in pcs], axis=0)
        CONTACT[kind + "_" + side] = (leaf, V((lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2), V((lo[0] + hi[0]) / 2, lo[1], lo[2]),
                                      V((lo[0] + hi[0]) / 2, lo[1], hi[2]))


def fk_pt(g, p_unrot, pose, upto="fam_saut"):
    R, t = aff(g, pose, upto)
    return R @ p_unrot + t


def paw_state(leg, pose):
    leaf, pc, pf, pb = CONTACT[leg]
    R, t = aff(leaf, pose, "fam_saut")
    a, f, b = R @ pc + t, R @ pf + t, R @ pb + t
    d = f - b
    pitch = math.degrees(math.atan2(d[1], -d[2]))           # + : orteils relevés
    return a, pitch


def seg_angle(g, pose):
    """Angle monde (autour de x) de l'axe −Y d'un segment : 0 = vertical, + = le bas part vers l'avant."""
    R, t = aff(g, pose, "fam_saut")
    d = R @ V(0, -1, 0)
    return math.degrees(math.atan2(-d[2], -d[1]))


REST_POSE = {}
REST_FOOT = {leg: paw_state(leg, REST_POSE)[0] for leg in CONTACT}
MET_REST = {s: seg_angle(f"jarret_{s}", REST_POSE) for s in "lr"}


def solve_leg(pose, leg, target, pitch=0.0, met=None, it=60):
    """Pose les articulations de la patte (rotations x) pour que le contact du pied soit en target (y, z), pied à `pitch`.
    Arrière : angle du jarret (métatarse) vers `met` (zigzag). Damped least squares, jacobienne numérique."""
    joints = LEG[leg]
    x = np.array([pose.get(j, {}).get("rotation", (0, 0, 0))[0] for j in joints], float)

    def err(xv):
        for j, v in zip(joints, xv):
            r = list(pose.get(j, {}).get("rotation", (0, 0, 0)))
            r[0] = v
            pose.setdefault(j, {})["rotation"] = tuple(r)
        a, pt = paw_state(leg, pose)
        e = [(a[1] - target[0]) * 1.0, (a[2] - target[1]) * 1.0, (pt - pitch) * 0.02]
        if leg.startswith("ar"):
            ma = seg_angle(joints[2], pose)
            e.append(((ma - (met if met is not None else MET_REST[leg[-1]])) * 0.012))
        return np.array(e)

    lam = 2e-4
    for _ in range(it):
        e0 = err(x)
        if np.abs(e0).max() < 1e-3:
            break
        J = np.zeros((len(e0), len(x)))
        for i in range(len(x)):
            dx = x.copy()
            dx[i] += 0.5
            J[:, i] = (err(dx) - e0) / 0.5
        step = np.linalg.solve(J.T @ J + lam * np.eye(len(x)), -J.T @ e0)
        step = np.clip(step, -20, 20)
        x = x + step
    err(x)
    return pose


def foot_target(leg, dz=0.0, dy=0.0):
    p = REST_FOOT[leg]
    return (max(0.06, p[1] + dy), p[2] + dz)


def solve_all(pose, targets=None, pitches=None, mets=None):
    targets = targets or {}
    for leg in ("av_l", "av_r", "ar_l", "ar_r"):
        tg = targets.get(leg, foot_target(leg))
        solve_leg(pose, leg, tg, (pitches or {}).get(leg, 0.0), (mets or {}).get(leg))
    return pose


def lowest_y(pose, extra=0.0):
    ys = [paw_state(l, pose)[0][1] for l in CONTACT]
    return min(ys)


def copy_pose(p):
    return {k: {ch: tuple(v) for ch, v in d.items()} for k, d in p.items()}


# ================================================================== animations : outils
def fmt(v):
    if isinstance(v, (int, float, np.floating)):
        v = float(v)
        return str(round(v + 0.0, 3))
    return v


def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": fmt(v[0]), "y": fmt(v[1]), "z": fmt(v[2])}], "time": round(t, 4), "interpolation": "linear"}


TROP = []


def _rdp(ts, vs, eps):
    """Douglas-Peucker sur une piste (indices gardés)."""
    def rec(i, j):
        if j <= i + 1:
            return [i, j]
        best, idx = 0.0, None
        for k in range(i + 1, j):
            f = (ts[k] - ts[i]) / (ts[j] - ts[i])
            e = max(abs(vs[k][a] - (vs[i][a] + f * (vs[j][a] - vs[i][a]))) for a in range(3))
            if e > best:
                best, idx = e, k
        if best <= eps:
            return [i, j]
        return rec(i, idx)[:-1] + rec(idx, j)
    return rec(0, len(ts) - 1)


def vitesse_pistes(tracks, still, kexpr):
    """Allure × vitesse au sol (retour en jeu du 2026-11-05 : « en sneak il court sur place alors que je bouge pas ») :
    valeur = pose immobile + K · (allure − pose immobile), K = kexpr (0 à l'arrêt, 1 à la vitesse de l'état). Les pistes
    sont simplifiées ici (l'optimiseur garde tel quel les keyframes Molang)."""
    out = {}
    for g, chans in tracks.items():
        for ch, lst in chans.items():
            sv = still.get(g, {}).get(ch, lst[0][1])     # canal absent de la pose immobile : sa première valeur
            ts = [t for t, _ in lst]
            ds = [tuple(float(v[a]) - float(sv[a]) for a in range(3)) for _, v in lst]
            eps = {"rotation": 0.3, "position": 0.03, "scale": 0.01}[ch]
            keep = _rdp(ts, ds, eps)
            amp = [max(abs(d[a]) for d in ds) for a in range(3)]
            nl = []
            for i in keep:
                v = []
                for a in range(3):
                    if amp[a] <= eps:
                        v.append(round(float(sv[a]), 3))
                    else:
                        d = round(ds[i][a], 3)
                        v.append(f"{round(float(sv[a]), 3)}{d:+}*{kexpr}" if d else round(float(sv[a]), 3))
                nl.append((ts[i], tuple(v)))
            out.setdefault(g, {})[ch] = nl
    for g, chans in still.items():                 # canaux de la pose immobile absents de l'allure
        for ch, v in chans.items():
            out.setdefault(g, {}).setdefault(ch, [(0.0, v)])
    return out


def anim_from_samples(name, length, sampler, n, loop="loop", molang=None, include_end=True, vitesse=None):
    """sampler(t) -> pose {groupe: {canal: (x,y,z)}} ; molang : {groupe: {canal: tuple}} (une clé).
    vitesse = (pose immobile, expression K) : amplitude de l'allure × K (voir vitesse_pistes)."""
    times = [i * length / n for i in range(n + (1 if include_end else 0))]
    tracks = {}
    for t in times:
        pz = sampler(t)
        if loop == "loop" and not name.startswith("overlay_") and "ctrl_alpha#brume" in G:      # états : brume coupée sauf réglage
            pz.setdefault("ctrl_alpha#brume", {}).setdefault("position", (-1, 0, 0))
            pz.setdefault("ctrl_emit#brume", {}).setdefault("position", (-1, 0, 0))
        for g, chans in pz.items():
            for ch, v in chans.items():
                tracks.setdefault(g, {}).setdefault(ch, []).append((t, v))
    if vitesse:
        tracks = vitesse_pistes(tracks, vitesse[0], vitesse[1])
    A_ = {}
    for g, chans in tracks.items():
        kfs = []
        for ch, lst in chans.items():
            kfs += [kf(ch, t, v) for t, v in lst]
        A_[G[g]["uuid"]] = {"name": G[g]["name"], "type": "bone", "keyframes": kfs}
    for g, chans in (molang or {}).items():
        ent = A_.setdefault(G[g]["uuid"], {"name": G[g]["name"], "type": "bone", "keyframes": []})
        for ch, tup in chans.items():
            ent["keyframes"] = [k for k in ent["keyframes"] if k["channel"] != ch]
            for ax, e in enumerate(tup):
                if isinstance(e, str) and (len(e) > 512 or e.count(";") > 15):
                    TROP.append(f"{len(e)} car. {e.count(';') + 1} instr. : {name} {G[g]['name']} {ch} {'xyz'[ax]}")
            ent["keyframes"].append(kf(ch, 0.0, tup))
    return {"uuid": str(_uuid.uuid4()), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "pet_idle",
            "animators": A_}


def S(T_, k, ph=0.0):
    return lambda t: math.sin(TAU * k * t / T_ + ph)


def oreille(side, tx, tz, ty=0.0):
    """Oreille : tx > 0 = pointe vers l'arrière (plaquée), tz > 0 = vers l'extérieur, ty = pivot vers l'avant/extérieur."""
    return (tx, side * ty, -side * tz) if side > 0 else (tx, side * ty, -side * tz)


def put(pose, g, ch, v):
    d = pose.setdefault(g, {})
    if ch in d and ch != "scale":
        d[ch] = tuple(np.asarray(d[ch], float) + np.asarray(v, float))
    elif ch in d:
        d[ch] = tuple(np.asarray(d[ch], float) * np.asarray(v, float))
    else:
        d[ch] = tuple(float(x) for x in v)


def tail_wave(pose, t, T_, base, amp_y, amp_x, cyc=1, lag=0.12, w=(0.5, 0.7, 0.9, 1.0, 1.1, 1.2)):
    """Queue : base = 6 angles x (pente ajoutée par segment), ondulation en cascade (y et x)."""
    for i, g in enumerate(TAIL):
        ph = TAU * (cyc * t / T_ - lag * i)
        put(pose, g, "rotation", (base[i] + amp_x * w[i] * math.sin(ph + 1.3), amp_y * w[i] * math.sin(ph), 0))


def ears(pose, tx, tz, ty=0.0, txl=None):
    for side, k in ((-1, "oreille_l"), (1, "oreille_r")):
        put(pose, k, "rotation", oreille(side, tx if txl is None or side > 0 else txl, tz, ty))


def lids(pose, c):
    for k in ("paupiere_l", "paupiere_r"):
        put(pose, k, "scale", (1, 1 + LID_K * c, 1))


# ================================================================== poses (IK au sol, dans le repère du renard : fam_saut et fam_sol exclus)
# Conventions (guide, section 3, et renderer MODCONV=1) : rotation +X = le nez monte (pour un segment vers l'avant), le bas d'une
# patte part vers l'avant ; +Y = le côté droit avance (le museau tourne vers la gauche, −X) ; +Z = le côté droit monte.
# Queue (axe local +Z vers l'arrière) : +X = le bout descend. Mâchoire : −X = la gueule s'ouvre.
LEGS4 = ("av_l", "av_r", "ar_l", "ar_r")


def oreille(side, tx, tz, ty=0.0):
    """Oreille (side −1 gauche, +1 droite) : tx > 0 = plaquée en arrière, tz > 0 = vers l'extérieur, ty > 0 = ouverture vers l'extérieur."""
    return (tx, -side * ty, -side * tz)


def ears(pose, tx, tz=0.0, ty=0.0, d_l=None):
    for side, k in ((-1, "oreille_l"), (1, "oreille_r")):
        a, b, c_ = (tx, tz, ty) if (side > 0 or d_l is None) else d_l
        put(pose, k, "rotation", oreille(side, a, b, c_))


def brows(pose, up=0.0, inner=0.0):
    """Sourcils : up = levés (px), inner > 0 = bout intérieur relevé (inquiet), < 0 = froncés."""
    put(pose, "sourcil_l", "position", (0, up, 0))
    put(pose, "sourcil_r", "position", (0, up, 0))
    put(pose, "sourcil_l", "rotation", (0, 0, inner))
    put(pose, "sourcil_r", "rotation", (0, 0, -inner))


QMAP = [[0], [1], [2], [3], [4], [5]]


def tail(pose, xs, ys=(0,) * 6, zs=(0,) * 6):
    """Pentes écrites pour 6 tronçons, réparties sur les 4 segments (somme par tronçon)."""
    for i, g in enumerate(TAIL):
        k = QMAP[i] if len(xs) == 6 else [i]
        put(pose, g, "rotation", tuple(sum(v[j] for j in k) * (0.8 if len(k) > 1 else 1) for v in (xs, ys, zs)))


def ik(pose, targets=None, pitches=None, mets=None, legs=LEGS4):
    for leg in legs:
        tg = (targets or {}).get(leg, foot_target(leg))
        solve_leg(pose, leg, tg, (pitches or {}).get(leg, 0.0), (mets or {}).get(leg))
    return pose


def leg_angles(pose):
    return {j: pose.get(j, {}).get("rotation", (0, 0, 0)) for leg in LEGS4 for j in LEG[leg]}


def pied_min(pose):
    return min(paw_state(l, pose)[0][1] for l in LEGS4)


# ------------------------------------------------------------------ poses fixes
def pose_assis():
    """Assis : croupe au sol, pattes avant droites, arrière repliées (jarret au sol), queue enroulée devant les pattes."""
    p = {}
    put(p, "fam_pos", "position", (0, -1.5, 0.35))
    put(p, "bassin", "rotation", (27, 0, 0))
    put(p, "taille", "rotation", (4, 0, 0))
    put(p, "cou", "rotation", (-24, 0, 0))
    put(p, "tete", "rotation", (-9, 0, 0))
    tg = {"av_l": (0.06, REST_FOOT["av_l"][2] + 0.15), "av_r": (0.06, REST_FOOT["av_r"][2] + 0.15),
          "ar_l": (0.06, REST_FOOT["ar_l"][2] - 0.9), "ar_r": (0.06, REST_FOOT["ar_r"][2] - 0.9)}
    ik(p, tg, mets={"ar_l": -78, "ar_r": -78})
    tail(p, (-34, -6, 0, -2, -6, -10), (0, -22, -26, -26, -24, -18), (0, 0, 0, 0, 0, 0))
    return p


def pose_salut(prof=1.0):
    """Invitation au jeu : avant baissé (coudes près du sol), arrière haut, queue levée."""
    p = {}
    put(p, "fam_pos", "position", (0, -0.25 * prof, -0.2 * prof))
    put(p, "bassin", "rotation", (-17 * prof, 0, 0))
    put(p, "cou", "rotation", (22 * prof, 0, 0))
    put(p, "tete", "rotation", (6 * prof, 0, 0))
    tg = {"av_l": (0.06, REST_FOOT["av_l"][2] - 1.2 * prof), "av_r": (0.06, REST_FOOT["av_r"][2] - 1.2 * prof)}
    ik(p, tg, pitches={"av_l": 0, "av_r": 0})
    tail(p, (-30 * prof, -14 * prof, -8 * prof, -4 * prof, 0, 0))
    return p


def pose_affut():
    """Affût (avant le bond du mulot) : corps bas, tête penchée vers le sol."""
    p = {}
    put(p, "fam_pos", "position", (0, -0.65, 0))
    put(p, "bassin", "rotation", (-4, 0, 0))
    put(p, "cou", "rotation", (-14, 0, 0))
    put(p, "tete", "rotation", (-16, 0, 0))
    ik(p)
    return p


def pose_plonge():
    """Atterrissage du bond : museau dans la neige, avant replié, arrière haut."""
    p = {}
    put(p, "fam_pos", "position", (0, -0.35, -0.9))
    put(p, "bassin", "rotation", (-24, 0, 0))
    put(p, "cou", "rotation", (-20, 0, 0))
    put(p, "tete", "rotation", (-8, 0, 0))
    tg = {k: (0.06, REST_FOOT[k][2] - 0.9 + (-0.6 if k.startswith("av") else 0.0)) for k in LEGS4}
    ik(p, tg)
    return p


def pose_bond():
    """En l'air (bond, chute) : avant tendues vers l'avant, arrière tendues vers l'arrière."""
    p = {}
    for s_ in "lr":
        put(p, f"epaule_{s_}", "rotation", (52, 0, 0))
        put(p, f"coude_{s_}", "rotation", (-18, 0, 0))
        put(p, f"poignet_{s_}", "rotation", (-20, 0, 0))
        put(p, f"hanche_{s_}", "rotation", (-48, 0, 0))
        put(p, f"genou_{s_}", "rotation", (-10, 0, 0))
        put(p, f"jarret_{s_}", "rotation", (-12, 0, 0))
        put(p, f"pied_ar_{s_}", "rotation", (20, 0, 0))
    return p


def pose_patte_levee():
    """Se lèche la patte avant gauche : patte levée vers la gueule, tête baissée et tournée vers elle."""
    p = {}
    put(p, "cou", "rotation", (-30, 8, 0))
    put(p, "tete", "rotation", (-12, 10, 6))
    ik(p, {"av_l": (2.1, REST_FOOT["av_l"][2] - 1.25)}, pitches={"av_l": -40}, legs=("av_l",))
    return p


def pose_gratte():
    """Assis, se gratte le cou avec la patte arrière gauche, tête penchée vers elle."""
    p = pose_assis()
    put(p, "tete", "rotation", (0, 6, 16))
    put(p, "cou", "rotation", (0, 6, 0))
    solve_leg(p, "ar_l", (2.2, REST_FOOT["ar_l"][2] - 2.2), pitch=-40, met=-35)
    return p


def pose_couche_dos():
    """Cramponné à plat ventre (dos du joueur en élytres) : pattes écartées et fléchies."""
    p = {}
    put(p, "fam_pos", "position", (0, -1.7, 0))
    tg = {k: (0.06, REST_FOOT[k][2] + (-0.9 if k.startswith("av") else 0.7)) for k in LEGS4}
    ik(p, tg, mets={"ar_l": -60, "ar_r": -60})
    return p


def pose_boule():
    """Sommeil (v10) : couché à plat ventre, pattes repliées sous lui, tête posée bas et tournée vers le flanc, queue ramenée
    le long du flanc. Courbure légère répartie sur le tronc : l'ancienne boule (jusqu'à 34° par jointure) ouvrait les
    jointures des masses de la v4 une fois posée au sol."""
    p = {}
    put(p, "fam_pos", "position", (0, -1.62, 0))
    put(p, "taille", "rotation", (0, -6, 0))
    put(p, "poitrail", "rotation", (0, -6, 0))
    put(p, "cou", "rotation", (-30, -14, 0))
    put(p, "tete", "rotation", (-8, -14, 6))
    tg = {k: (0.06, REST_FOOT[k][2] + (-0.9 if k.startswith("av") else 0.7)) for k in LEGS4}
    ik(p, tg, mets={"ar_l": -60, "ar_r": -60})
    tail(p, (6, 4, 2, 0, 0, 0), (14, 18, 18, 18, 16, 12))      # vers le côté où la tête est tournée
    return p


P_ASSIS = pose_assis()
P_SALUT = pose_salut(1.0)
P_ETIRE = pose_salut(1.35)
P_AFFUT = pose_affut()
P_PLONGE = pose_plonge()
P_BOND = pose_bond()
P_PATTE = pose_patte_levee()
P_GRATTE = pose_gratte()
P_DOS = pose_couche_dos()
P_BOULE = pose_boule()


# ================================================================== allures (IK à chaque image)
def allure(t, T_, f, duty, phases, stride, lift, base_y, bob, pitch, flex, head, tailx, earx, extra=None, centre=(0.21, 0.71)):
    """Pas au sol : pied en appui qui recule toujours (jamais vers l'avant), suspension pendant laquelle le corps monte."""
    p = {}
    ph = (t * f) % 1.0
    y = base_y - bob * math.cos(TAU * 2 * (ph - centre[0]))
    put(p, "fam_pos", "position", (0, y, 0))
    put(p, "bassin", "rotation", (pitch * math.sin(TAU * (ph - 0.15)), 0, 0))
    put(p, "taille", "rotation", (flex * math.sin(TAU * (ph - 0.3)), 0, 0))
    put(p, "poitrail", "rotation", (flex * 0.8 * math.sin(TAU * (ph - 0.35)), 0, 0))
    put(p, "cou", "rotation", (head[0] - pitch * 0.6 * math.sin(TAU * (ph - 0.15)), 0, 0))
    put(p, "tete", "rotation", (head[1] - pitch * 0.3 * math.sin(TAU * (ph - 0.1)), 0, 0))
    tail(p, [tailx[i] + 6 * (0.4 + 0.15 * i) * math.sin(TAU * (ph - 0.25 - 0.08 * i)) for i in range(6)],
         [3 * (0.3 + 0.15 * i) * math.sin(TAU * (t / T_) - 0.6 * i) for i in range(6)])
    ears(p, earx + 4 * math.sin(TAU * (ph - 0.3)), 2)
    tg, pt = {}, {}
    for leg in LEGS4:
        u = (ph + phases[leg]) % 1.0
        z0, y0 = REST_FOOT[leg][2], max(0.1, REST_FOOT[leg][1])
        if u < duty:
            k = u / duty
            tg[leg] = (y0, z0 + stride * (k - 0.5))
            pt[leg] = 0.0
        else:
            k = (u - duty) / (1 - duty)
            kk = k * k * (3 - 2 * k)
            tg[leg] = (y0 + lift * math.sin(math.pi * k), z0 + stride * (0.5 - kk))
            pt[leg] = -22 * math.sin(math.pi * k)
    ik(p, tg, pt)
    if extra:
        extra(p, t, ph)
    return p


TW, FW = 3 / 3.5, 3.5          # marche : petit galop bondissant, 3 foulées à 3,5 Hz
TR, FR = 1.0, 4.0              # course : galop allongé, 4 foulées à 4 Hz
TS, FS = 1.0, 2.0              # accroupi : marche de chasse, 2 foulées à 2 Hz
PH_BOND = {"av_l": 0.0, "av_r": 0.92, "ar_l": 0.5, "ar_r": 0.42}
PH_GALOP = {"av_l": 0.0, "av_r": 0.9, "ar_l": 0.5, "ar_r": 0.4}
PH_CHASSE = {"ar_l": 0.0, "av_l": 0.75, "ar_r": 0.5, "av_r": 0.25}


def s_walk(t):
    def ex(p, t, ph):
        brows(p, 0.03, 0)
        put(p, "machoire", "rotation", (-6 - 3 * math.sin(TAU * ph), 0, 0))
    return allure(t, TW, FW, 0.38, PH_BOND, 2.5, 0.75, -0.32, 0.3, 6, 3, (-1, -2), (2, 0, 0, 0, -2, -2), 8, ex)


def s_run(t):
    def ex(p, t, ph):
        lids(p, 0.12)
        put(p, "machoire", "rotation", (-14 - 5 * math.sin(TAU * ph), 0, 0))        # il halète
    return allure(t, TR, FR, 0.32, PH_GALOP, 3.3, 0.95, -0.42, 0.38, 8, 6, (-2, 3), (-6, -4, 0, 0, 0, 0), 26, ex)


# poses immobiles des allures (vitesse au sol nulle) : debout en marche et course, à l'affût en sneak (avant bas, oreilles en avant)
def s_walk_0(t):
    def ex(p, t, ph):
        brows(p, 0.03, 0)
        put(p, "machoire", "rotation", (-6, 0, 0))
    return allure(0.0, TW, FW, 0.38, PH_BOND, 0.0, 0.0, -0.05, 0.0, 0, 0, (0, -1), (2, 0, 0, 0, -2, -2), 6, ex)


def s_run_0(t):
    def ex(p, t, ph):
        lids(p, 0.12)
        put(p, "machoire", "rotation", (-14, 0, 0))
    return allure(0.0, TR, FR, 0.32, PH_GALOP, 0.0, 0.0, -0.1, 0.0, 0, 0, (-1, 3), (-4, -2, 0, 0, 0, 0), 14, ex)


def k_vit(d):
    return f"math.clamp(q.ground_speed/{d},0,1)"


# ================================================================== états du familier vivant (guide 6.6), tous au sol à l'origine
def s_sit(t):
    """pet_sit : assis à côté du joueur (il s'accroupit, ou rien ne bouge depuis 20 s) ; respire, regarde autour de lui,
    oreilles qui pivotent, bout de queue enroulée qui bat, clignements."""
    p = copy_pose(P_ASSIS)
    T_ = 6.0
    b = math.sin(TAU * 3 * t / T_)
    put(p, "taille_m", "scale", (1 + 0.02 * b, 1 + 0.03 * b, 1))
    put(p, "poitrail_m", "scale", (1 + 0.015 * b, 1 + 0.02 * b, 1))
    put(p, "tete", "rotation", (-3 + 4 * math.sin(TAU * t / T_ + 1.2), 20 * math.sin(TAU * t / T_ + 0.6), 6 * math.sin(TAU * 2 * t / T_)))
    ears(p, 6 + 5 * math.sin(TAU * t / T_), 3, 0, (6 + 5 * math.sin(TAU * t / T_ + 2.0), 3, 0))
    lids(p, max(bump(t, 1.9, 1.98, 2.04, 2.14), bump(t, 4.5, 4.58, 4.64, 4.74)))
    for i, g in enumerate(TAIL):
        if i >= 3:
            put(p, g, "rotation", (0, 7 * math.sin(TAU * 2 * t / T_ - 0.6 * (i - 3)), 0))
    return p


def s_sleep(t):
    """pet_sleep : roulé en boule au sol, museau sous la queue, respiration lente (4 s), oreille qui tressaille."""
    p = copy_pose(P_BOULE)
    T_ = 4.0
    b = math.sin(TAU * t / T_)
    put(p, "taille_m", "scale", (1 + 0.03 * b, 1 + 0.045 * b, 1))
    put(p, "poitrail_m", "scale", (1 + 0.02 * b, 1 + 0.03 * b, 1))
    lids(p, 1.0)
    for k in ("oeil_l", "oeil_r"):         # l oeil recule sous la paupière fermée (plus de faces proches oeil/paupière)
        put(p, k, "position", (0, 0, 0.18))
    ears(p, 26, 14, 0, (26 + 10 * bump(t, 2.6, 2.7, 2.8, 3.0), 14, 0))
    put(p, "machoire", "rotation", (0, 0, 0))
    return p


def s_swim(t):
    """pet_swim : il nage en chien, le dos à fleur d'eau, tête haute, pattes avant qui pédalent, queue qui flotte."""
    p = {}
    T_ = 0.8
    ph = TAU * t / T_
    put(p, "fam_pos", "position", (0, -1.3 + 0.12 * math.sin(2 * ph), 0))
    put(p, "bassin", "rotation", (-6 + 2 * math.sin(2 * ph), 0, 0))
    put(p, "cou", "rotation", (18, 0, 0))
    put(p, "tete", "rotation", (4 + 3 * math.sin(2 * ph + 0.5), 0, 0))
    for s_, o in (("l", 0.0), ("r", math.pi)):
        put(p, f"epaule_{s_}", "rotation", (-35 + 38 * math.sin(ph + o), 0, 0))
        put(p, f"coude_{s_}", "rotation", (40 + 35 * math.sin(ph + o + 1.4), 0, 0))
        put(p, f"hanche_{s_}", "rotation", (25 + 22 * math.sin(ph + o + 0.6), 0, 0))
        put(p, f"genou_{s_}", "rotation", (-15 + 15 * math.sin(ph + o + 1.8), 0, 0))
    ears(p, -4, 4)
    brows(p, 0.06, 4)
    lids(p, 0.15)
    tail(p, [(-8, 0, 3, 4, 4, 2)[i] for i in range(6)], [8 * (0.3 + 0.15 * i) * math.sin(ph - 0.6 * i) for i in range(6)])
    return p


_pb = copy_pose(P_BOND)
put(_pb, "fam_pos", "position", (0, 0.4, 0))


def s_fall(t):
    """pet_fall : pose de bond, pattes avant tendues vers le sol, queue en balancier ; la brume de givre le porte un instant."""
    p = copy_pose(_pb)
    T_ = 1.2
    w = math.sin(TAU * t / T_)
    put(p, "bassin", "rotation", (4 + 2 * w, 0, 0))
    put(p, "cou", "rotation", (-4, 0, 0))
    put(p, "tete", "rotation", (-6 + 2 * w, 0, 0))
    ears(p, 22 + 5 * math.sin(TAU * 2 * t / T_), 8)
    brows(p, 0.08, 6)
    tail(p, [(-8, -4, 0, 0, 0, 0)[i] + 5 * (0.4 + 0.15 * i) * math.sin(TAU * t / T_ - 0.6 * i) for i in range(6)])
    put(p, "ctrl_alpha#brume", "position", (0, 0, 0))         # brume visible : il lévite (les autres états la cachent, −1)
    put(p, "ctrl_emit#brume", "position", (0, 0, 0))
    put(p, "trans_brume", "scale", (1 + 0.08 * w, 1, 1 + 0.08 * w))
    return p


def s_jump(t):
    """pet_jump : il saute sur une marche : pattes arrière qui poussent, avant repliées sous le poitrail, oreilles en arrière."""
    p = copy_pose(_pb)
    T_ = 0.6
    w = math.sin(TAU * t / T_)
    put(p, "bassin", "rotation", (-8 + 2 * w, 0, 0))
    put(p, "cou", "rotation", (0, 0, 0))          # v10 : cou à 6° = arrière du crâne contre le poitrail (0,014 px)
    for s_ in "lr":
        put(p, f"hanche_{s_}", "rotation", (-22, 0, 0))
        put(p, f"epaule_{s_}", "rotation", (24, 0, 0))
        put(p, f"coude_{s_}", "rotation", (-30, 0, 0))
    ears(p, 24, 6)
    tail(p, [(10, 6, 2, 0, 0, 0)[i] + 3 * math.sin(TAU * t / T_ - 0.6 * i) for i in range(6)])
    return p


def s_land(t):
    """pet_land (0,3 s) : il amortit, pattes fléchies, corps qui s'écrase un peu puis remonte ; oreilles et queue qui rebondissent."""
    p = {}
    b = math.sin(math.pi * min(1.0, t / 0.3))
    put(p, "fam_pos", "position", (0, -0.45 * b, 0))
    put(p, "bassin", "rotation", (-3 * b, 0, 0))
    ik(p)
    ears(p, 16 * b, 0)
    tail(p, [-4 * b * (1 if i < 2 else 0.4) for i in range(6)])
    return p


# ================================================================== idle : base vivante + 14 comportements tirés au hasard (Molang)
TI = 28.0
PRE = ("v.s=q.life_time/7+q.instance_seed*17;v.i=math.floor(math.mod(math.sin(math.floor(v.s)*109+43)*517+517,1)*21);"
       "v.u=math.mod(v.s,1)*7;v.e=math.clamp(math.min(v.u-1.2,6.1-v.u)/0.9,0,1)")
NUIT_BAILLE = "v.i=v.i+(v.i<3)*(q.time_of_day>0.3)*(q.time_of_day<0.7)*(11-v.i)"
COTE = "(math.mod(math.floor(v.s),2)*2-1)"


def E(a, d):
    return f"math.sin(math.clamp((v.u-{a})/{d},0,1)*180)"


def EP(a, b, r=0.35):
    """Plateau de a à b (rampes de r secondes)."""
    return f"math.clamp(math.min(v.u-{a},{b}-v.u)/{r},0,1)"


COMPORTEMENTS = {
    7: "écoute : oreilles et tête tournées vers un son",
    8: "curieux : tête inclinée, sourcils levés",
    9: "regarde le joueur : se tourne vers lui et lève la tête, petit remuement de queue",
    10: "flaire le sol",
    11: "bâille (plus souvent la nuit)",
    12: "s'étire (avant allongé, croupe haute)",
    13: "se lèche la patte avant gauche",
    14: "joie : petits bonds, queue haute qui remue",
    15: "s'assoit et regarde autour de lui",
    16: "bond du mulot (affût, saut en arc, museau dans la neige)",
    17: "éternue de givre (souffle à la truffe)",
    18: "invitation au jeu (avant baissé, croupe haute), puis petit bond de côté",
    19: "s'ébroue",
    20: "s'assoit et se gratte le cou avec la patte arrière",
}
TERMS = {}          # (groupe, canal, axe) -> [(numéro, expression)]


def T(g, ch, ax, n, expr):
    TERMS.setdefault((g, ch, ax), []).append((n, expr))


def pose_terms(n, pose, env, skip=(), only=None, scale=1.0):
    """Ajoute les écarts d'une pose (par rapport au repos) pondérés par l'enveloppe env (Molang)."""
    for g, chans in pose.items():
        if g in skip or (only and g not in only):
            continue
        for ch, v in chans.items():
            for ax in range(3):
                d = (v[ax] - 1.0) if ch == "scale" else v[ax]
                if abs(d) > (0.01 if ch != "rotation" else 0.3):
                    T(g, ch, ax, n, f"{round(d * scale, 1 if ch == 'rotation' else 2)}*{env}")


# 7 écoute
for side, k in ((-1, "oreille_l"), (1, "oreille_r")):
    T(k, "rotation", 1, 7, f"30*v.e*{COTE}")
T("tete", "rotation", 1, 7, f"24*v.e*{COTE}")
T("cou", "rotation", 0, 7, "6*v.e")
T("sourcil_l", "position", 1, 7, "0.07*v.e")
T("sourcil_r", "position", 1, 7, "0.07*v.e")
# 8 curieux
T("tete", "rotation", 2, 8, f"20*v.e*{COTE}")
for k in ("oreille_l", "oreille_r"):
    T(k, "rotation", 0, 8, "-12*v.e")
T("sourcil_l", "position", 1, 8, "0.11*v.e")
T("sourcil_r", "position", 1, 8, "0.11*v.e")
T("sourcil_l", "rotation", 2, 8, "8*v.e")
T("sourcil_r", "rotation", 2, 8, "-8*v.e")
# 9 regarde le joueur (à sa droite, plus haut)
T("fam_rot", "rotation", 1, 9, "-20*v.e")
T("cou", "rotation", 0, 9, "24*v.e")
T("tete", "rotation", 0, 9, "16*v.e")
T("tete", "rotation", 1, 9, "-24*v.e")
T("sourcil_l", "position", 1, 9, "0.06*v.e")
T("sourcil_r", "position", 1, 9, "0.06*v.e")
T("queue1", "rotation", 1, 9, "12*v.e*math.sin(v.u*900)")
T("queue2", "rotation", 1, 9, "10*v.e*math.sin(v.u*900-60)")
# 10 flaire le sol
T("cou", "rotation", 0, 10, "-34*v.e")
T("tete", "rotation", 0, 10, "v.e*(-16+4*math.sin(v.u*2200))")
T("cou", "rotation", 1, 10, "26*v.e*math.sin((v.u-1.2)*70)")
# 11 bâille
T("cou", "rotation", 0, 11, "16*v.e")
T("machoire", "rotation", 0, 11, "-38*" + E(2.4, 1.6))
for k in ("oreille_l", "oreille_r"):
    T(k, "rotation", 0, 11, "20*v.e")
# 12 s'étire, 18 invitation au jeu
pose_terms(12, P_ETIRE, "v.e")
T("machoire", "rotation", 0, 12, "-12*v.e")
pose_terms(18, P_SALUT, E(1.4, 2.0), skip=("fam_pos",))
pose_terms(18, P_SALUT, E(1.4, 2.0), only=("fam_pos",))
T("fam_saut", "position", 0, 18, "-1.1*" + E(3.6, 0.8))
T("fam_saut", "position", 1, 18, "0.9*" + E(3.6, 0.8))
for side, k in ((-1, "oreille_l"), (1, "oreille_r")):
    T(k, "rotation", 2, 18, f"{-side * 24}*" + E(1.4, 2.0))
T("queue1", "rotation", 1, 18, "14*math.sin(v.u*1080)*" + E(1.4, 2.0))
# 13 se lèche la patte
pose_terms(13, P_PATTE, "v.e")
T("machoire", "rotation", 0, 13, "-12*v.e*math.abs(math.sin(v.u*480))")
# 14 joie
T("fam_saut", "position", 1, 14, "0.55*v.e*math.abs(math.sin(v.u*540))")
T("queue1", "rotation", 0, 14, "-36*v.e")
T("queue2", "rotation", 0, 14, "-10*v.e")
T("queue3", "rotation", 0, 14, "18*v.e")
T("queue4", "rotation", 0, 14, "18*v.e")
T("queue1", "rotation", 1, 14, "14*v.e*math.sin(v.u*1080)")
T("queue2", "rotation", 1, 14, "10*v.e*math.sin(v.u*1080-70)")
T("machoire", "rotation", 0, 14, "-10*v.e")
for k in ("oreille_l", "oreille_r"):
    T(k, "rotation", 0, 14, "-8*v.e")
# 15 s'assoit, 20 s'assoit et se gratte
pose_terms(15, P_ASSIS, "v.e")
T("tete", "rotation", 1, 15, "22*v.e*math.sin((v.u-1.2)*62)")
pose_terms(20, P_GRATTE, "v.e")
T("hanche_l", "rotation", 0, 20, "11*v.e*math.sin(v.u*2520)")
T("genou_l", "rotation", 0, 20, "-8*v.e*math.sin(v.u*2520)")
# 16 bond du mulot : affût, saut en arc, plongeon, retour
pose_terms(16, P_AFFUT, EP(1.2, 2.95))
pose_terms(16, P_PLONGE, E(3.4, 1.4), skip=("fam_pos",))
T("fam_saut", "position", 1, 16, "2.1*" + E(2.9, 0.6))
T("fam_saut", "position", 2, 16, "-0.9*" + EP(2.95, 5.9, 0.4))
T("bassin", "rotation", 0, 16, "14*" + E(2.9, 0.3))
T("queue1", "rotation", 0, 16, "-24*" + E(2.9, 1.6))
for k in ("oreille_l", "oreille_r"):
    T(k, "rotation", 0, 16, "-14*" + EP(1.2, 2.95))
# 17 éternue de givre
T("tete", "rotation", 0, 17, "14*" + E(1.6, 1.2) + "-24*" + E(2.75, 0.35))
T("machoire", "rotation", 0, 17, "-14*" + E(1.6, 1.2) + "-18*" + E(2.75, 0.35))
T("ctrl_emit#souffle", "position", 0, 17, "6*" + E(2.75, 0.4))
for k in ("oreille_l", "oreille_r"):
    T(k, "rotation", 0, 17, "22*" + E(2.75, 0.5))
# 19 s'ébroue (secousses de 5 par seconde)
EB = E(2.0, 1.0)
T("fam_rot", "rotation", 2, 19, "11*math.sin(v.u*1800)*" + EB)
T("cou", "rotation", 2, 19, "-18*math.sin(v.u*1800-40)*" + EB)
T("tete", "rotation", 2, 19, "-14*math.sin(v.u*1800-70)*" + EB)
for k in ("oreille_l", "oreille_r"):
    T(k, "rotation", 0, 19, "18*" + EB)
T("queue1", "rotation", 1, 19, "16*math.sin(v.u*1800-90)*" + EB)
T("fam_saut", "position", 1, 19, "0.3*" + EB)
# paupières : fermeture par comportement + clignements irréguliers
BLINK = ("v.b=q.life_time/2.9+q.instance_seed*5;"
         "v.c=math.sin(math.clamp((math.mod(v.b,1)-math.mod(math.floor(v.b)*0.618,0.75))*19,0,1)*180)")
FERME = "+".join(f"{c_}*(v.i=={n})" for n, c_ in ((11, 0.95), (12, 0.7), (13, 0.5), (14, 0.35), (19, 0.85), (20, 0.6)))
LID_IDLE = f"{PRE};{BLINK};1+{round(LID_K, 2)}*math.max(v.e*({FERME})+(v.i==17)*{E(2.6, 0.6)},v.c)"

# base vivante (q.anim_time ; périodes qui divisent 28 s : 2 s, 4 s, 7 s)
BASE_IDLE = {
    ("fam_pos", "position"): ("0.06*math.sin(q.anim_time*51.43)", 0, 0),
    ("fam_saut", "position"): (0, 0, 0),
    ("fam_leve", "position"): (0, 0, 0),
    ("fam_rot", "rotation"): (0, 0, 0),
    ("bassin", "rotation"): (0, 0, 0),
    ("taille", "rotation"): (0, 0, 0),
    ("poitrail", "rotation"): (0, 0, 0),
    ("cou", "rotation"): (0, 0, 0),
    ("tete", "rotation"): ("2*math.sin(q.anim_time*25.71)", 0, 0),
    ("machoire", "rotation"): (0, 0, 0),
    ("taille_m", "scale"): ("1+0.02*math.sin(q.anim_time*180)", "1+0.03*math.sin(q.anim_time*180)", 1),
    ("poitrail_m", "scale"): ("1+0.015*math.sin(q.anim_time*180-30)", "1+0.02*math.sin(q.anim_time*180-30)", 1),
    ("ctrl_emit#souffle", "position"): (0, 0, 0),
}
for side, k in ((-1, "oreille_l"), (1, "oreille_r")):
    BASE_IDLE[(k, "rotation")] = (f"3*math.sin(q.anim_time*90+{40 if side < 0 else 0})", 0, 0)
for k in ("sourcil_l", "sourcil_r"):
    BASE_IDLE[(k, "position")] = (0, 0, 0)
    BASE_IDLE[(k, "rotation")] = (0, 0, 0)
for leg in LEGS4:
    for j in LEG[leg]:
        BASE_IDLE[(j, "rotation")] = (0, 0, 0)
for i, g in enumerate(TAIL):
    BASE_IDLE[(g, "rotation")] = (f"{round(2 + 1.5 * i * 0.3, 2)}*math.sin(q.anim_time*90-{30 * i}+60)", f"{round(4 + 1.2 * i, 2)}*math.sin(q.anim_time*90-{30 * i})", 0)


def mesure_comportements():
    """Écarte les pieds du sol : pour chaque comportement, plus petite hauteur des pieds pendant le mélange (enveloppe 0..1) ;
    correction ajoutée en position y de fam_saut (bosse 4e(1−e))."""
    out = {}
    for n, P_ in ((12, P_ETIRE), (15, P_ASSIS), (20, P_GRATTE), (18, P_SALUT), (13, P_PATTE), (16, P_AFFUT), (16.5, P_PLONGE)):
        worst = 0.0
        for e in np.linspace(0, 1, 11):
            q = {}
            for g, chans in P_.items():
                for ch, v in chans.items():
                    q.setdefault(g, {})[ch] = tuple((1 + (x - 1) * e) if ch == "scale" else x * e for x in v)
            y = pied_min(q)
            if 0 < e < 1:
                worst = max(worst, (0.06 - y) / (4 * e * (1 - e)))
        out[n] = worst
    return out


LIFT = mesure_comportements()
for n, env in ((12, "v.e"), (15, "v.e"), (20, "v.e"), (18, E(1.4, 2.0)), (13, "v.e"), (16, EP(1.2, 2.95)), (16.5, E(3.4, 1.4))):
    if LIFT[n] > 0.005:
        T("fam_leve", "position", 1, int(n), f"{round(LIFT[n] + 0.02, 2)}*4*{env}*(1-{env})")


def ind(n):
    return f"(v.i=={n})"


def molang_key(base, terms, extra_pre=()):
    pre = PRE + "".join(";" + x for x in extra_pre)
    return pre + ";" + fmt(base) + "".join(f"+{ind(n)}*({e})" for n, e in terms)


def relais(g):
    """Groupe relais g_b : même pivot que g, rotation de repos nulle, reprend les cubes et les enfants de g."""
    k = g + "_b"
    if k in G:
        return k
    gg = G[g]
    G[k] = {"key": k, "name": gg["name"] + "_b", "o": gg["o"].copy(), "rest": np.zeros(3), "parent": g, "W": gg["W"].copy(), "Rw": gg["Rw"].copy(),
            "uuid": str(_uuid.uuid4()), "ids": gg["ids"], "children": gg["children"]}
    for ch_ in gg["children"]:
        G[ch_]["parent"] = k
    for c_ in CUBES:
        if c_["g"] == g:
            c_["g"] = k
    gg["ids"], gg["children"] = [], [k]
    return k


idle_molang = {}
for (g, ch), base in BASE_IDLE.items():
    vals, vals_b = [], []
    for ax in range(3):
        terms = TERMS.get((g, ch, ax), [])
        if not terms:
            vals.append(base[ax])
            vals_b.append(1 if ch == "scale" else 0)
            continue
        extra = [NUIT_BAILLE] if any(n == 11 for n, _ in terms) else []
        k1 = len(terms)
        while len(molang_key(base[ax], terms[:k1], extra)) > 505:
            k1 -= 1
        vals.append(molang_key(base[ax], terms[:k1], extra))
        rest_ = terms[k1:]
        if rest_:
            extra2 = [NUIT_BAILLE] if any(n == 11 for n, _ in rest_) else []
            vals_b.append(molang_key(1 if ch == "scale" else 0, rest_, extra2))
        else:
            vals_b.append(1 if ch == "scale" else 0)
    idle_molang.setdefault(g, {})[ch] = tuple(vals)
    if any(isinstance(v, str) for v in vals_b):
        assert ch != "scale", "relais d'échelle non prévu"
        idle_molang.setdefault(relais(g), {})[ch] = tuple(vals_b)
orph = [k for k in TERMS if (k[0], k[1]) not in BASE_IDLE]
assert not orph, f"comportements sur un canal sans base : {orph}"
for k in ("paupiere_l", "paupiere_r"):
    idle_molang[k] = {"scale": (1, LID_IDLE, 1)}


def comportements_tranches(seed, n=8):
    out = []
    for k in range(n):
        v = k + seed * 17
        x = math.fmod(math.sin(math.radians(math.floor(v) * 109 + 43)) * 517 + 517, 1)
        out.append(int(math.floor(x * 21)))
    return out


# ================================================================== événements (s'ajoutent à l'état)
def ev_jump(t):
    p = {}
    b = bump(t, 0.0, 0.12, 0.2, 0.45)
    put(p, "bassin", "rotation", (-10 * b + 6 * bump(t, 0.3, 0.42, 0.45, 0.6), 0, 0))
    for s_ in "lr":
        put(p, f"hanche_{s_}", "rotation", (-24 * b, 0, 0))
        put(p, f"epaule_{s_}", "rotation", (28 * b, 0, 0))
    tail(p, [14 * b * (1 if i < 2 else 0.5) for i in range(6)])
    ears(p, 14 * bump(t, 0.05, 0.2, 0.35, 0.6), 0)
    put(p, "ctrl_alpha#brume", "position", (1 * bump(t, 0.0, 0.1, 0.4, 0.6), 0, 0))
    return p


AMP = "math.clamp(q.land_speed*0.1,0.4,1.4)"


def ev_land(t):
    sq = bump(t, 0.0, 0.06, 0.12, 0.3) - 0.35 * bump(t, 0.3, 0.38, 0.42, 0.55)
    def sg(k):
        """1 + k·AMP écrit sans double signe."""
        k = round(k, 4)
        return 1 if abs(k) < 1e-6 else f"1{'+' if k > 0 else '-'}{abs(k)}*{AMP}"
    p = {"fam_pos": {"scale": (sg(0.06 * sq), sg(-0.13 * sq), sg(0.06 * sq))}}
    b = bump(t, 0.0, 0.08, 0.15, 0.45)
    for side, k in ((-1, "oreille_l"), (1, "oreille_r")):
        p[k] = {"rotation": tuple(f"{round(x, 3)}*{AMP}" if abs(x) > 1e-4 else 0 for x in oreille(side, 20 * b, 0))}
    p["queue1"] = {"rotation": (f"{round(-14 * b + 10 * bump(t, 0.35, 0.45, 0.5, 0.65), 3)}*{AMP}", 0, 0)}
    return p


def _grandit(p, s):
    """Échelle s du renard autour de ses pattes (origine) : échelle sur le bassin + position qui ramène son pivot."""
    P = np.array((0.0, 3.75, 1.9))                      # pivot du bassin
    put(p, "bassin", "scale", (s, s, s))
    put(p, "bassin", "position", tuple(-(1 - s) * P))


def _tourbillon(p, t, a, b, c, d, haut, larg, tours):
    """Tourbillon de neige : les deux anneaux de brume (trans_brume) s'écartent en colonne (échelle y), tournent, puis
    retombent en anneau qui s'étale au sol et s'efface. a→b : la colonne monte ; c→d : elle retombe et s'élargit."""
    col = bump(t, a, b, c, d)
    eta = sm(t, c, d)
    put(p, "trans_brume", "scale", (0.45 + 0.55 * sm(t, a, b) + larg * eta, 1 + haut * col, 0.45 + 0.55 * sm(t, a, b) + larg * eta))
    put(p, "trans_brume", "position", (0, 0.4 * haut * col, 0))           # l'anneau du bas reste posé au sol (pivot à 0,15, anneau à −0,25)
    put(p, "trans_brume", "rotation", (0, -360 * tours * sm(t, a, d + 0.2), 0))
    put(p, "ctrl_alpha#brume", "position", (1 * bump(t, a - 0.01, a + 0.08, d - 0.1, d + 0.2), 0, 0))


def _ebroue(p, t, a, d, amp, f=5.0):
    """S'ébroue comme un chien mouillé : la secousse part de la tête et descend jusqu'à la queue (retard par segment),
    yeux plissés, oreilles qui battent."""
    e = bump(t, a, a + 0.08, d - 0.18, d)
    w = lambda lag: math.sin(TAU * f * (t - a) - lag)
    put(p, "cou", "rotation", (0, 0, amp * e * w(0)))
    put(p, "poitrail", "rotation", (0, 0, 0.4 * amp * e * w(0.9)))
    put(p, "taille", "rotation", (0, 0, 0.25 * amp * e * w(1.8)))
    put(p, "queue1", "rotation", (0, 1.2 * amp * e * w(2.6), 0))
    ears(p, 18 * e * (0.5 + 0.5 * w(0.4)), 10 * e * w(0.4))
    lids(p, 0.75 * e)


def _regarde(p, t, a, b, c, d, lever=14, pench=8):
    """Retombée : il lève le museau vers son maître, penche la tête, oreilles dressées, queue qui remue."""
    r = bump(t, a, b, c, d)
    put(p, "tete", "rotation", (lever * r, 0, pench * r))
    ears(p, -10 * r, 0)
    brows(p, 0.06 * r, 0)
    tail(p, [0] * 6, [14 * r * math.sin(TAU * 3 * (t - a)) * (0.4 + 0.12 * i) for i in range(6)])


def ev_equip(t):
    """event_equip (2,2 s) : un tourbillon de neige se lève (anneaux de brume en colonne qui tournent) ; le renard en sort en
    tournant sur lui-même, d'abord petit et ramassé ; le tourbillon retombe en anneau qui s'étale ; il s'ébroue de la tête
    à la queue (son de secousse), puis lève le museau vers son maître, oreilles dressées, queue qui remue."""
    p = {}
    _tourbillon(p, t, 0.0, 0.4, 0.75, 1.05, haut=7, larg=1.1, tours=2.2)
    s = sm(t, 0.22, 0.72) * (1 + 0.07 * bump(t, 0.6, 0.72, 0.78, 0.95))
    _grandit(p, max(0.02, s))
    put(p, "fam_rot", "rotation", (0, -200 * (1 - sm(t, 0.2, 0.85)), 0))
    put(p, "fam_pos", "position", (0, 1.2 * bump(t, 0.55, 0.72, 0.74, 0.92), 0))
    put(p, "fam_pos", "scale", (1 + 0.05 * bump(t, 0.88, 0.94, 0.96, 1.05), 1 - 0.09 * bump(t, 0.88, 0.94, 0.96, 1.05), 1 + 0.05 * bump(t, 0.88, 0.94, 0.96, 1.05)))
    ears(p, 30 * bump(t, 0.2, 0.4, 0.7, 0.95), 0)             # oreilles couchées dans le vent du tourbillon
    lids(p, 0.6 * bump(t, 0.2, 0.35, 0.75, 0.95))
    _ebroue(p, t, 1.0, 1.6, 22)
    _regarde(p, t, 1.55, 1.75, 1.95, 2.2)
    return p


def ev_teleport(t):
    """event_teleport (1,3 s) : coincé ou trop loin, il revient dans un petit tourbillon de neige, en sort d'un tour,
    secoue la tête et lève le museau vers son maître."""
    p = {}
    _tourbillon(p, t, 0.0, 0.2, 0.4, 0.65, haut=4, larg=0.8, tours=1.2)
    s = 0.15 + 0.85 * sm(t, 0.05, 0.42) + 0.05 * bump(t, 0.35, 0.42, 0.46, 0.6)
    _grandit(p, s)
    put(p, "fam_rot", "rotation", (0, -110 * (1 - sm(t, 0.05, 0.5)), 0))
    put(p, "fam_pos", "position", (0, 0.8 * bump(t, 0.3, 0.42, 0.44, 0.6), 0))
    ears(p, 24 * bump(t, 0.05, 0.2, 0.4, 0.6), 0)
    e = bump(t, 0.55, 0.62, 0.78, 0.9)
    put(p, "cou", "rotation", (0, 0, 14 * e * math.sin(TAU * 6 * (t - 0.55))))
    _regarde(p, t, 0.85, 1.0, 1.1, 1.3, lever=12, pench=6)
    return p


def ev_owner_hurt(t):
    """event_owner_hurt : son maître prend un coup : il sursaute, plaque les oreilles, rentre la queue, puis lève la tête vers lui."""
    p = {}
    b = bump(t, 0.0, 0.08, 0.16, 0.5)
    put(p, "fam_saut", "position", (0, 0.7 * b, 0.4 * b))
    ears(p, 38 * bump(t, 0.0, 0.08, 0.45, 0.9), 6 * b)
    brows(p, 0.08 * bump(t, 0.0, 0.1, 0.5, 0.9), 8 * bump(t, 0.0, 0.1, 0.5, 0.9))
    put(p, "tete", "rotation", (12 * bump(t, 0.25, 0.45, 0.7, 0.95), 0, 0))
    tail(p, [26 * bump(t, 0.0, 0.1, 0.45, 0.9) * (1 if i < 2 else 0.5) for i in range(6)])
    return p


def ev_reveil(t):
    """event_exit_sleep : au réveil, il s'étire (avant allongé, croupe haute) en bâillant."""
    e = bump(t, 0.1, 0.5, 0.95, 1.4)
    p = {}
    for g, chans in P_ETIRE.items():
        for ch, v in chans.items():
            if ch != "scale" and g not in TAIL:
                put(p, g, ch, tuple(float(x) * e for x in v))
    put(p, "machoire", "rotation", (-24 * bump(t, 0.3, 0.6, 0.9, 1.2), 0, 0))
    lids(p, 0.6 * bump(t, 0.3, 0.6, 0.9, 1.2))
    tail(p, (-12 * e, -4 * e, 0, 0, 0, 0))
    return p


# ================================================================== couche permanente (overlay_givre) : regard, réactions au joueur et au monde
DT = "math.min(1,q.delta_time*{})"
# vie basse du maître (guide 6.6 : q.owner_health) : il s'inquiète, oreilles plaquées, queue basse
VIE = "math.clamp((q.owner_max_health*0.5-q.owner_health)*0.4,0,1)"
NUIT = "math.clamp((0.27-math.abs(q.time_of_day-0.5))*6,0,1)"
EVEIL = "(1-q.is_sleeping)"
SAC = ("v.g=q.life_time/1.6+q.instance_seed*9;"
       "v.ga=math.mod(math.abs(math.sin(math.floor(v.g)*61))*331,1);v.gb=math.mod(math.abs(math.sin((math.floor(v.g)-1)*61))*331,1)")
SACV = "math.lerp(v.gb,v.ga,math.clamp(math.mod(v.g,1)*6,0,1))"
PRES = "math.clamp(2.6-q.owner_distance,0,1)"        # le maître s'approche (il s'arrête à 3 blocs) : il lève la tête, la queue remue
# pleine lune, la nuit : il hurle doucement à la lune 4 s toutes les 30 s (tête levée, gueule ouverte)
HU = f"(q.moon_phase<0.5)*{NUIT}*math.clamp(math.sin(math.mod(q.life_time+q.instance_seed*13,30)*45),0,1)"
tete_y = f"{SAC};({SACV}*30-15)*{EVEIL}"
tete_x = (f"v.hx=math.lerp(v.hx,{PRES}*12*{EVEIL},{DT.format(2)});{SAC};"
          f"v.hx+(math.mod({SACV}*7.3,1)*10-5)*{EVEIL}")
overlay_molang = {
    # porté (menu Apparence, ou deuxième familier : guide 6.6) : à gauche du joueur, un peu en arrière, comme la v4
    "fam_sol": {"position": ("(1-q.is_pet)*-11", 0, "(1-q.is_pet)*1")},
    "ctrl_emit#souffle": {"position": (-1, 0, 0)},
    "tete": {"rotation": (tete_x, tete_y, 0)},
    "fam_rot": {"rotation": (0, 0, f"v.yr=math.lerp(v.yr,math.clamp(q.yaw_speed*0.04,-6,6),{DT.format(2)});v.yr")},
    "machoire": {"rotation": (f"-16*{HU}", 0, 0)},
    "queue1": {"rotation": (f"v.w2=math.lerp(v.w2,{VIE},{DT.format(1.5)});v.r2=math.lerp(v.r2,q.is_in_rain,{DT.format(1)});22*v.w2+12*v.r2", 0, 0)},
    "queue3": {"rotation": (0, f"v.qp=math.lerp(v.qp,{PRES}*(1-q.is_sitting*0.5),{DT.format(2)});v.qp*16*math.sin(q.life_time*720)", 0)},
    "cou": {"rotation": (f"30*{HU}", 0, f"v.r1=math.lerp(v.r1,q.is_in_rain,{DT.format(1)});v.q=math.mod(q.life_time/8+q.instance_seed*11,1)*8;"
                              "v.mo=math.max(q.is_in_water,v.mo-q.delta_time/1.5);"
                              "v.r1*16*math.sin(v.q*1800)*math.sin(math.clamp(v.q/0.9,0,1)*180)+v.mo*(1-q.is_in_water)*22*math.sin(q.life_time*1700)")},
}
for side, tag, per in ((-1, "l", 0.375), (1, "r", 0.25)):
    tw = (f"v.t{tag}=q.life_time*{per}+q.instance_seed*{3 if side < 0 else 7};"
          f"(math.mod(math.floor(v.t{tag})*0.618,1)>0.35)*math.pow(math.sin(math.clamp((math.mod(v.t{tag},1)"
          f"-math.mod(math.floor(v.t{tag})*0.37,0.8))*14,0,1)*180),2)*{-side * 16}")
    overlay_molang[f"oreille_{tag}"] = {"rotation": (
        f"v.p{tag}=math.lerp(v.p{tag},math.max(math.max(q.is_in_rain,q.is_in_water)*0.9,{VIE}),{DT.format(1.5)});32*v.p{tag}", 0, tw)}
overlay_brume = lambda t: {"trans_brume": {"rotation": (0, -360 * t / 8.0, 0)}}

# ================================================================== assemblage
# familier vivant au sol (guide 6.6) : il attend à 3 blocs, comme un loup apprivoisé
FAMILIER = {"mode": "sol", "distance": 3, "vitesse": 1}
ANIMS = []
# repos : pet_idle (préfixe pet_ : le renderer et la visionneuse ne posent pas le mannequin)
ANIMS.append(anim_from_samples("pet_idle", TI, lambda t: {}, 1, molang=idle_molang))
# allures : amplitude × vitesse du familier lui-même (q.ground_speed parle du familier, guide 6.6 §4)
ANIMS.append(anim_from_samples("pet_walk", TW, s_walk, 36, vitesse=(s_walk_0(0), k_vit(4.3))))
ANIMS.append(anim_from_samples("pet_run", TR, s_run, 40, vitesse=(s_run_0(0), k_vit(5.6))))
ANIMS.append(anim_from_samples("pet_sit", 6.0, s_sit, 48))
ANIMS.append(anim_from_samples("pet_sleep", 4.0, s_sleep, 24))
ANIMS.append(anim_from_samples("pet_swim", 0.8, s_swim, 16))
ANIMS.append(anim_from_samples("pet_fall", 1.2, s_fall, 12))
ANIMS.append(anim_from_samples("pet_jump", 0.6, s_jump, 12))
ANIMS.append(anim_from_samples("pet_land", 0.3, s_land, 6))
ANIMS.append(anim_from_samples("overlay_givre", 8.0, overlay_brume, 8, molang=overlay_molang))
ev = anim_from_samples("event_equip", 2.2, ev_equip, 44, loop="once")
ev["animators"]["effects"] = {"name": "Effects", "type": "effect",
                              "keyframes": [{"channel": "sound", "data_points": [{"effect": "entity.wolf.shake", "file": ""}], "time": 1.0}]}
ANIMS.append(ev)
ANIMS.append(anim_from_samples("event_teleport", 1.3, ev_teleport, 26, loop="once"))
ANIMS.append(anim_from_samples("event_owner_hurt", 0.9, ev_owner_hurt, 18, loop="once"))
ANIMS.append(anim_from_samples("event_exit_sleep", 1.4, ev_reveil, 28, loop="once"))
assert not TROP, "Molang trop long : " + " | ".join(TROP)
outliner[0] = bone_node("fam_sol")          # racine rafraîchie, groupes particle_ gardés à côté
assert len(ANIMS) <= 16, len(ANIMS)

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS,
         "unhandled_root_fields": {"phynaria": {"version": 1, "familier": FAMILIER}}}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


nk = sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values())
lmax = max(len(v) for a in ANIMS for b in a["animators"].values() for k in b["keyframes"] for dp in k.get("data_points", []) for v in dp.values()
           if isinstance(v, str))
print(len(elements), "cubes ;", len(G) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;", nk, "keyframes ;",
      os.path.getsize(out) // 1024, "Ko ;", f"densité {DENS:.2f} texels/px (visage {DENS * DENS_TETE:.1f}, queue {DENS * DENS_QUEUE:.1f}) ;",
      f"Molang max {lmax} car. ; relevés {', '.join(f'{k}:{v:.2f}' for k, v in LIFT.items() if v > 0.005)}")
