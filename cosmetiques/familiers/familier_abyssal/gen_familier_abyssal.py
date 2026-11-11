"""Familier crâne v3 (2026-11-08) : la v2 (géométrie et texture inchangées, translation pure de -C0 à l'écriture ;
générateur et livrable d'avant dans .build/gen_avant.py et .build/avant_livrable.bbmodel) passée en FAMILIER VIVANT
(guide 6.6), mode « vol » : esprit qui lévite par sa flamme d'âme, il vole près de l'épaule comme l'allay.
Bloc unhandled_root_fields.phynaria.familier {"mode": "vol", "distance": 2, "vitesse": 1, "hauteur": 1.8} : centre du crâne
à l'origine, donc à hauteur de tête (1,8 bloc). Racine « esprit » (aucun groupe du corps) ; porté (menu Apparence, deuxième
familier : q.is_pet = 0), l'overlay le replace à droite de la tête comme la v2. Plus de contre-rotation ni de place sur
la poitrine. Animations : pet_idle (24 s, les 10 comportements au hasard de la v2 ; « tour du joueur » devenu une petite
ronde de 4 px), pet_fly (même vie + nez penché et flamme couchée × q.ground_speed), pet_walk, pet_run, pet_sit (l'ancien
sneak : il se fait petit), pet_sleep (somnole bas), pet_swim (flamme tassée), pet_fall, overlay_crane (flottement, regard
par saccades, pluie, eau, lave, nuit, pleine lune, vie basse du maître par q.owner_health, sourire quand le maître vient
tout près : q.owner_distance), event_equip (2026-11-08 : la flammèche s'allume au cœur du crâne, s'embrase, les os
se forment autour d'elle, cornes, yeux, claquement de dents, regard vers le maître), event_teleport (la même en bref), event_owner_hurt (sursaut puis
colère), event_exit_sleep (réveil en sursaut), event_jump, event_land. Plus d'attack, de hurt ni d'event_unequip (pas dans
la table du familier) ; plus de cachette q.is_in_menu (le mod oriente cam_/camy_ dans le menu, guide du 2026-11-06 soir).
Pas encore dans le mod pour un familier vivant : particules emit_ (braises, flammèche crachée) non lancées.
À juger en jeu (/cosmetique apercu) : hauteur réelle en vol, état joué à l'arrêt en mode vol (pet_idle ou pet_fly),
event_owner_hurt, variables mémorisées (non simulées par le renderer).

Familier crâne v2 : petit crâne démoniaque abyssal habité par une flamme d'âme vert acide, qui flotte à droite du joueur.
Ensemble Abyssal (thème Démoniaque), fiche .claude/styles/abyssal.md. Design original.
Écrit familier_abyssal.png, familier_abyssal_e.png et .build/familier_abyssal_brut.bbmodel à côté de ce script.

Refonte du 2026-11-05 selon .claude/styles/familiers.md et .claude/references/familiers/ (retours sur familier_givre :
« passif, il fait rien », « assemblage de formes ») :
  - type : esprit mort-vivant (arbre de types-familiers.md : cause visible pour flotter -> FLOTTE). La cause : une flamme
    d'âme brûle dans le crâne ; elle luit au fond des orbites, du nez et de la gorge, et s'échappe par le haut de l'occiput
    en une crête de feu qui traîne derrière lui. Plus de queue de vertèbres à épines (« trop dragon, créature », abyssal.md).
  - placement : à droite du joueur, à hauteur de tête (x = 12, y = 28, z = 1), un peu en arrière ; le renard de givre
    marche à gauche au sol : les deux familiers ne se gênent pas.
  - modèle : crâne en volumes ronds par paliers alignés (boîtes en croix, aucune boîte tournée à 45°), masses emboîtées
    (voûte, front, occiput, arcades en V, ponts nasal et orbitaires, pommettes, arcades zygomatiques, maxillaire) ;
    orbites profondes de 1,1 px avec une flamme en amande et une fente de pupille qui bouge ; mâchoire articulée
    (menton, branches, ramus, dents et crocs) ; cornes en crochet en 5 segments sur le dessus de la tête ; peinture en
    espace monde (normale lissée de la forme, os charbon à reflet violet, occlusion aux contacts, ombre des orbites et
    reflet vert de la flamme, fosse nasale, sutures, fissures vert acide asymétriques) ; texels enfouis transparents.
  - vie : couche permanente overlay_crane (flottement irrégulier, regard qui suit celui du joueur avec retard,
    saccades des pupilles, lueur qui respire, clignement de la flamme des yeux, retard dans les virages, flamme vivante ;
    pluie : la flamme se tasse et il s'ébroue ; nuit : flamme plus haute, lueur plus forte ; vie basse : il se
    rapproche, ses yeux vacillent ; menu Apparence : parties additives cachées). idle de 24 s : base lente + 10
    comportements tirés au hasard par tranches de 6 s (liste COMPORTEMENTS), un sur deux à peu près, jamais synchronisés
    entre joueurs (q.instance_seed) ; la nuit, il s'assoupit plus souvent.
  - passe du 2026-11-05 (familiers vivants, 2e pas) : comportements pondérés (regarder autour x3, regarder le joueur et
    s'approcher curieux x2, les autres x1, 10 tranches calmes sur 24) ; il remarque qu'on le regarde (le joueur tourne la
    tête vers lui au-delà de 25° : il se tourne vers lui, tête penchée, gueule entrouverte ; SIGNE_TETE) ; monde : la flamme
    se tasse sous l'eau, flambe dans la lave, plus haute les nuits de pleine lune ; il ricane après sa morsure (attack).
  - réactions : event_jump (inertie), event_land (q.land_speed), attack (il mord en avant), hurt (sursaut, puis regarde
    le joueur), event_equip (la flamme jaillit, le crâne s'y forme, les orbites s'allument en dernier), event_unequip
    (il s'éteint et se résorbe dans sa flamme).
  - états : walk / run (il suit en retard, flamme couchée par le vent), sneak (contre-rotation du torse, il descend et se
    fait petit, yeux plissés), fly (monte, flamme vive), glide et swim (corps couché : contre-rotation, il vole droit à
    côté, flamme à l'horizontale), fall (inertie : il monte, mâchoire ouverte), sleep (il somnole posé au-dessus de la
    poitrine du joueur). Monture : pas d'animation (16 au plus), repli sur idle (le joueur est assis, debout de torse).

Fonctions avancées (guide 4 bis, 5 ter, 6.4) : trans_ (flamme, visible avec shader), add_ + cam_ (halo des orbites) et
add_ + camy_ (cœur de la flamme) sans shader, camy_ (flamme face caméra), ctrl_alpha (additif caché dans le menu),
ctrl_lumiere (la nuit), ctrl_emit (crachat de flammèches), particule modélisée braise qui monte, overlay_, event_*.
Un seul son (event_equip, tools/sons.py). À juger en jeu (/cosmetique apercu) : sens de q.head_y_rotation et de
q.yaw_speed, variables mémorisées (non simulées par le renderer), camy_ dans une chaîne inclinée.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
os.environ.setdefault("MODCONV", "1")
import render_bbmodel as rb
from sons import limiter_sons

AVEC_E = True
NOM = "familier_abyssal"
TEX = 512
TAU = 2 * math.pi
SS = 2
I3 = np.eye(3)
C0 = np.array((12.0, 28.5, 1.0))        # centre du crâne au repos (repère du joueur)


def V(*a):
    return np.array(a, float)


def A(c):
    return np.array(c, np.float32)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def rot_matrix(rx, ry, rz):
    return rb.rot_matrix(rx, ry, rz)


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
M = np.diag([-1.0, 1.0, 1.0])


def mir(p):
    return C0 + M @ (np.asarray(p, float) - C0)


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


def S(x, y, z):
    """Point du crâne (repère local, nez vers −Z) -> repère du joueur au repos."""
    return C0 + V(x, y, z)


# ================================================================== squelette
G = {}
CUBES = []


def grp(key, W, Rw=I3, parent=None, name=None):
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


def cubew(g, name, cw, size, Rw_cube=None, mat=None, rig="crane", sec=None, mirror_of=None, sym=False, faces=None):
    """Cube par son centre monde cw au repos ; size dans le repère du cube (celui du groupe, ou Rw_cube)."""
    g_ = G[g]
    lc = g_["Rw"].T @ (np.asarray(cw, float) - g_["W"])
    Rl = I3 if Rw_cube is None else g_["Rw"].T @ Rw_cube
    cu = g_["o"] + lc
    h = np.asarray(size, float) / 2
    c = {"name": name, "g": g, "cu": cu, "frm": cu - h, "to": cu + h, "Rl": Rl, "mat": mat or {"type": "os", "part": "crane"}, "uuid": str(_uuid.uuid4()),
         "rig": rig, "sec": sec or name, "mirror_of": mirror_of, "sym": sym, "faces": faces or FACES6}
    CUBES.append(c)
    g_["ids"].append(c["uuid"])
    return c


FACES6 = ["north", "south", "east", "west", "up", "down"]


def paire(gl, gr, name, cw, size, Rw_cube=None, **kw):
    """Cube gauche (x < centre) et son miroir droit, UV partagées."""
    a = cubew(gl, name + "_l", cw, size, Rw_cube, **kw)
    kw2 = dict(kw)
    if "sec" in kw2 and kw2["sec"]:
        kw2["sec"] = kw2["sec"] + "_r"
    b = cubew(gr, name + "_r", mir(cw), size, None if Rw_cube is None else M @ Rw_cube @ M, mirror_of=name + "_l", **kw2)
    return a, b


def section(g, name, cw, size, long=2, chanf=0.25, n=3, Rw_cube=None, twin=None, **kw):
    """Section arrondie par paliers : boîtes alignées en croix (1 pleine en a, 2 pleine en b, 3 à mi-chemin), raccourcies
    de 0,2 px par palier le long de l'axe long."""
    s = np.asarray(size, float)
    a, b = [i for i in range(3) if i != long]
    cc = chanf * min(s[a], s[b])
    red = [(0.0, cc), (cc, 0.0), (cc / 2, cc / 2)][:n]
    out = []
    for k, (ra, rb_) in enumerate(red):
        d = s.copy()
        d[a] -= ra
        d[b] -= rb_
        d[long] -= 0.24 * k
        nm = f"{name}{k + 1}"
        if twin:
            out += paire(g, twin, nm, cw, d, Rw_cube, sec=name, **kw)
        else:
            out.append(cubew(g, nm, cw, d, Rw_cube, sec=name, **kw))
    return out


def demi_section(g, name, cw, size, chanf=0.3, partage=True, n=2, **kw):
    """Section octogonale centrée sur le plan de symétrie, axe long z : par moitié, une boîte centrale pleine en hauteur
    et un flanc réduit en hauteur qui l'emboîte ; la face intérieure (plan de symétrie) n'est pas peinte. La moitié droite
    est le miroir de la gauche (UV partagées si partage)."""
    s = np.asarray(size, float)
    cc = chanf * min(s[0], s[1])
    cw = np.asarray(cw, float)
    wc = s[0] - cc
    ov = min(0.15, cc / 2)
    parts = [("", cw - V(wc / 4, 0, 0), V(wc / 2, s[1], s[2])),
             ("f", cw - V(s[0] / 2 - (cc / 2 + ov) / 2, 0, 0), V(cc / 2 + ov, s[1] - cc, s[2] - 0.24))]
    if n == 3:
        # palier intermédiaire : la section passe de 8 à 12 pans
        parts.append(("m", cw - V(s[0] / 2 - cc / 4 - (cc / 4 + ov) / 2, 0, 0), V(cc / 4 + ov, s[1] - cc / 2, s[2] - 0.48)))
    out = []
    for suf, cl, dl in parts:
        nm = name + suf
        a = cubew(g, nm + "_l", cl, dl, sec=name, faces=[f for f in FACES6 if f != "east"], **kw)
        b = cubew(g, nm + "_r", mir(cl), dl, sec=name + ("" if partage else "_r"), faces=[f for f in FACES6 if f != "west"],
                  mirror_of=(nm + "_l") if partage else None, **kw)
        out += [a, b]
    return out


# --- hiérarchie
grp("esprit", C0)                                 # racine du familier vivant (origine du modèle après décalage de -C0)
grp("fam_etat", C0, parent="esprit")              # états du familier (allure, pose)
grp("fam_orbite", C0 + V(4.0, 0, 0), parent="fam_etat")   # retard dans les virages, petite ronde en volant (rayon 4 px)
grp("fam_ev", C0, parent="fam_orbite")            # événements, attaque, blessure
grp("fam_flot", C0, parent="fam_ev")              # couche permanente : flottement, regard
grp("fam_comp", C0, parent="fam_flot")            # comportements tirés au hasard
grp("fam_comp_b", C0, parent="fam_comp")         # relais (Molang trop long pour une clé)
grp("fam_comp_c", C0, parent="fam_comp_b")
grp("crane", C0, parent="fam_comp_c")             # attitude du crâne
grp("crane_b", C0, parent="crane")
grp("os", C0, parent="crane_b")                     # tout l'os (échelle à l'apparition)
grp("ctrl_lumiere#c", C0, parent="crane", name="ctrl_lumiere")
TMJ = S(0, -0.9, 0.15)
grp("machoire", TMJ, parent="os")
grp("machoire_b", TMJ, parent="machoire")
grp("machoire_c", TMJ, parent="machoire_b")
EYE = V(-1.3, 0.42, -2.05)
grp("oeil_l", S(*EYE), parent="os")
grp("oeil_r", mir(S(*EYE)), parent="os")
grp("oeil_l_b", S(*EYE), parent="oeil_l")       # relais (échelle : un seul comportement à la fois, produit exact)
grp("oeil_r_b", mir(S(*EYE)), parent="oeil_r")

# --- voûte (neurocrâne) : trois sections emboîtées
OSC = {"type": "os", "part": "crane"}
OSF = {"type": "os", "part": "face"}
OSM = {"type": "os", "part": "mach"}
PARTAGE_VOUTE = os.environ.get("PARTAGE", "1") == "1"
# profil arrondi : sections plus petites devant et derrière, la plus large au pariétal
# extrémités des paliers décalées de 0,12 px, et d'au moins 0,17 px d'une section à la suivante (faces proches)
for nm, z, d, w, h, y in (("vouteA", -1.2, 1.8, 5.35, 4.7, 0.95), ("vouteB", 0.45, 2.8, 5.7, 4.9, 1.15), ("vouteC", 2.175, 1.95, 5.4, 4.5, 1.2),
                          ("vouteD", 3.175, 1.35, 4.15, 3.65, 1.2), ("front", -2.075, 1.15, 4.3, 2.55, 2.2)):
    demi_section("os", nm, S(0, y, z), (w, h, d), chanf=0.36, partage=PARTAGE_VOUTE, n=2 if nm == "front" else 3, mat=OSC)

# --- face
paire("os", "os", "arcade", S(-1.3, 1.55, -2.85), (2.4, 0.7, 1.2), RZ(-14), mat=OSF)
cubew("os", "pont_nasal", S(0, 0.6, -2.6), (0.9, 2.2, 1.2), mat=OSF, sym=True)
paire("os", "os", "rebord", S(-2.45, 0.4, -2.35), (0.7, 2.0, 1.3), mat=OSF)
paire("os", "os", "pommette", S(-1.615, -0.75, -2.4), (2.13, 0.7, 1.6), mat=OSF)
paire("os", "os", "zygoma", S(-2.625, -0.55, -0.9), (0.95, 0.6, 2.2), mat=OSF)
cubew("os", "maxillaire", S(0, -1.15, -2.15), (3.4, 1.1, 1.8), mat=OSF, sym=True)
DENT = {"type": "dent", "haut": True}
cubew("os", "dents_h", S(0, -1.9, -2.85), (2.6, 0.55, 0.3), mat=DENT, sym=True, faces=["north", "south"])
paire("os", "os", "dents_hc", S(-1.45, -1.9, -2.0), (0.3, 0.55, 1.3), mat=dict(DENT, cote=True), faces=["east", "west"])
paire("os", "os", "croc", S(-0.95, -2.0, -3.1), (0.4, 0.9, 0.4), mat={"type": "croc", "haut": True}, sec="croc")
paire("os", "os", "croc_p", S(-0.95, -2.45, -3.1), (0.18, 0.4, 0.18), mat={"type": "croc", "haut": True}, sec="croc")
cubew("os", "gorge", S(0, -1.8, -1.4), (2.4, 0.6, 2.0), mat={"type": "gorge"}, sym=True, faces=["north", "down"])

# --- yeux : flamme en amande au fond de l'orbite (opaque : visible avec shader)
for s_, g in (("l", "oeil_l"), ("r", "oeil_r")):
    p = S(*EYE) if s_ == "l" else mir(S(*EYE))
    cubew(g + "_b", f"oeil_{s_}", p, (1.6, 1.4, 0.3), mat={"type": "oeil", "side": -1 if s_ == "l" else 1}, rig=f"oeil_{s_}",
          mirror_of="oeil_l" if s_ == "r" else None, faces=["north"])

# --- mâchoire (fermée au repos)
section("machoire_c", "menton", S(0, -2.75, -2.1), (3.0, 0.8, 1.3), long=0, chanf=0.3, n=2, mat=OSM, rig="mach")
paire("machoire_c", "machoire_c", "branche", S(-1.6, -2.55, -1.2), (0.6, 0.7, 2.6), mat=OSM, rig="mach")
paire("machoire_c", "machoire_c", "ramus", S(-1.8, -1.7, -0.05), (0.55, 1.3, 0.8), mat=OSM, rig="mach")
cubew("machoire_c", "dents_b", S(0, -2.17, -2.72), (2.4, 0.5, 0.3), mat={"type": "dent", "haut": False}, rig="mach", sym=True, faces=["north", "south"])
paire("machoire_c", "machoire_c", "dents_bc", S(-1.3, -2.17, -1.85), (0.3, 0.5, 1.3), mat={"type": "dent", "haut": False, "cote": True}, rig="mach",
      faces=["east", "west"])

# --- cornes : sur le dessus de la tête, au-dessus des tempes ; montent, balaient vers l'arrière, crochet vers le haut
# même tracé que bandeau_abyssal (validé en jeu) : vers l'arrière et le haut, puis la pointe revient vers l'avant en crochet
CORNE_D, CORNE_L, CORNE_W = [], [1.35, 1.2, 1.05, 0.9, 0.75], [1.3, 1.05, 0.82, 0.6, 0.4]
_ang, _xd = 38.0, 0.75
for i in range(5):
    CORNE_D.append(unit(V(-_xd, math.sin(math.radians(_ang)), math.cos(math.radians(_ang)))))
    _ang += 27 + 3 * i
    _xd *= 0.6
CORNE_PTS = [S(-1.75, 3.0, -0.6)]
for d_, L_ in zip(CORNE_D, CORNE_L):
    CORNE_PTS.append(CORNE_PTS[-1] + d_ * L_)
CORNE_LEN = sum(CORNE_L)


def frame_y(d):
    """Repère dont l'axe Y suit d, X proche de l'axe X du monde."""
    Y = unit(d)
    X = unit(V(1, 0, 0) - (V(1, 0, 0) @ Y) * Y)
    return np.column_stack([X, Y, np.cross(X, Y)])


acc = 0.0
for i, (d_, L_, w_) in enumerate(zip(CORNE_D, CORNE_L, CORNE_W)):
    Rw = frame_y(d_)
    p0 = CORNE_PTS[i]
    gl = grp(f"corne{i + 1}_l", p0, Rw, parent="os")
    gr = grp(f"corne{i + 1}_r", mir(p0), M @ Rw @ M, parent="os")
    ov = 0.28 if i else 0.55
    ln = L_ + ov + (0.06 if i < 4 else 0.0)
    c = p0 + d_ * ((L_ - ov) / 2 + (0.03 if i < 4 else 0.0))
    mat = {"type": "corne", "t0": acc / CORNE_LEN}
    for k, (fx, fz, dl) in enumerate(((1.0, 0.74, 0.0), (0.74, 1.0, -0.24)) if w_ >= 0.7 else ((1.0, 1.0, 0.0),)):
        paire(gl, gr, f"corne{i + 1}{'ab'[k]}", c, (w_ * fx, ln + dl, w_ * fz), Rw, mat=mat, sec="corne")
    acc += L_

# --- flamme d'âme : trois bouffées face caméra le long d'une chaîne qui se couche avec la vitesse
F1 = S(0, 2.9, 2.6)
F2 = F1 + V(0, 1.5, 0.55)
F3 = F2 + V(0, 1.25, 0.5)
PUFFS = [("1", F1, (3.0, 3.4), 1.45, None, 7), ("2", F2, (2.4, 2.9), 1.15, "flamme1", 12), ("3", F3, (1.7, 2.3), 0.85, "flamme2", 17)]
for k, piv, (w_, h_), up, par, ang in PUFFS:
    grp(f"flamme{k}", piv, parent=par or "crane")
    pc = piv + V(0, up, 0)
    # orientation de repos un peu tournée (en jeu, camy_ la remplace) : aucune face parallèle aux faces du crâne ni des autres bouffées
    grp(f"camy_flamme{k}", pc, RY(ang), parent=f"flamme{k}")
    grp(f"trans_flamme{k}", pc, RY(ang), parent=f"camy_flamme{k}")
    cubew(f"trans_flamme{k}", f"flamme{k}", pc, (w_, h_, 0.3), mat={"type": "flamme", "k": int(k), "w": w_, "h": h_}, rig=f"fl{k}", faces=["south"])
    grp(f"add_flamme{k}", pc, RY(ang), parent=f"camy_flamme{k}")
    grp(f"ctrl_alpha#f{k}", pc, RY(ang), parent=f"add_flamme{k}", name="ctrl_alpha")
    cubew(f"add_flamme{k}", f"coeur{k}", pc + V(0, -0.12 * h_, 0) + RY(ang) @ V(0, 0, 0.35), (w_ * 0.62, h_ * 0.62, 0.3), mat={"type": "coeur", "k": int(k)}, rig=f"fl{k}",
          faces=["south"])

# --- halo des orbites (sans shader) : disques additifs face caméra devant chaque orbite
for s_ in ("l", "r"):
    p = S(-1.3, 0.42, -3.5) if s_ == "l" else mir(S(-1.3, 0.42, -3.5))
    grp(f"cam_halo_{s_}", p, parent="os")
    grp(f"add_halo_{s_}", p, parent=f"cam_halo_{s_}")
    grp(f"ctrl_alpha#h{s_}", p, parent=f"add_halo_{s_}", name="ctrl_alpha")
    cubew(f"add_halo_{s_}", f"halo_{s_}", p, (1.1, 1.1, 0.3), mat={"type": "halo"}, rig=f"halo_{s_}", faces=["south"], mirror_of="halo_l" if s_ == "r" else None)

# --- points de départ des particules : braises qui montent de la flamme, crachat de flammèches à la gueule
grp("emit_braise", F2 + V(0, 0.6, 0), parent="flamme2")
grp("emit_braise2", F3 + V(0, 1.4, 0), parent="flamme3")
grp("emit_braise3", S(0, -1.95, -3.45), RX(-90), parent="os")
grp("ctrl_emit#c", S(0, -1.95, -3.45), RX(-90), parent="emit_braise3", name="ctrl_emit")

# ================================================================== repère monde au repos des cubes
FACE_CORNERS = rb.FACE_CORNERS
SWAP = {"east": "west", "west": "east"}
BYNAME = {c["name"]: c for c in CUBES}
for c in CUBES:
    g_ = G[c["g"]]
    R = g_["Rw"] @ c["Rl"]
    t = g_["W"] + g_["Rw"] @ (c["cu"] - g_["o"]) - R @ c["cu"]
    c["R"], c["t"] = R, t
    c["corners"] = {f: np.array([R @ np.array(p) + t for p in FACE_CORNERS[f](c["frm"], c["to"])]) for f in FACES6}
    c["half"] = (c["to"] - c["frm"]) / 2
    c["cw"] = R @ c["cu"] + t

OPAQUE = ("os", "dent", "croc", "gorge", "corne")


def sdf_box(c, P):
    q = (P - c["cw"]) @ c["R"]
    d = np.abs(q) - c["half"]
    return np.linalg.norm(np.maximum(d, 0), axis=-1) + np.minimum(np.max(d, axis=-1), 0)


def face_info(c, f):
    P4 = c["corners"][f]
    n = np.cross(P4[3] - P4[0], P4[1] - P4[0])
    return P4, np.linalg.norm(P4[1] - P4[0]), np.linalg.norm(P4[3] - P4[0]), n / max(np.linalg.norm(n), 1e-9)


def buried(c, P, n):
    """Texels enfouis dans un autre cube opaque du même ensemble rigide (au repos)."""
    hid = np.zeros(P.shape[:-1], bool)
    if c["mat"]["type"] not in OPAQUE:
        return hid
    for o in CUBES:
        if o is c or o["rig"] != c["rig"] or o["mat"]["type"] not in OPAQUE:
            continue
        hid |= sdf_box(o, P + n * 0.002) < -0.004
    return hid


# ================================================================== palette (ailes_abyssales, bandeau_abyssal)
C_OMBRE = A((11, 8, 16))
C_OS = A((54, 47, 68))
C_HAUT = A((132, 106, 172))
C_RIM = A((146, 92, 186))
C_AURA = A((22, 66, 40))
C_VEIN = A((96, 200, 44))
C_VCORE = A((150, 244, 70))
C_CREUX = A((13, 9, 19))
E_VERT = A((120, 225, 64))
LK = unit(V(-0.3, 0.85, -0.45))     # lumière clé : du haut, de l'avant, un peu de gauche


def hash3(ix, iy, iz, seed):
    return np.mod(np.sin(ix * 127.1 + iy * 311.7 + iz * 74.7 + seed * 13.3) * 43758.5453, 1.0)


def vnoise(P, f, seed=0.0):
    Q = P * f
    i = np.floor(Q)
    r = Q - i
    r = r * r * (3 - 2 * r)
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (r[..., 0] if dx else 1 - r[..., 0]) * (r[..., 1] if dy else 1 - r[..., 1]) * (r[..., 2] if dz else 1 - r[..., 2])
                out = out + w * hash3(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz, seed)
    return out


ELLI = {"crane": (V(0, 1.15, 0.8), V(2.95, 2.6, 3.2)), "face": (V(0, -0.1, -1.7), V(2.95, 2.3, 1.75)), "mach": (V(0, -2.5, -1.3), V(2.0, 0.85, 1.9))}


def smooth_normal(Pl, n, part):
    ce, r = ELLI[part]
    g = (Pl - ce) / (r * r)
    g = g / np.maximum(np.linalg.norm(g, axis=-1, keepdims=True), 1e-9)
    N = 0.82 * g + 0.18 * n
    return N / np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-9)


# fissures : polylignes posées sur la surface (rayon depuis le centre de la voûte)
CC = S(0, 1.15, 0.6)
OCC_CR = [c for c in CUBES if c["rig"] == "crane" and c["mat"]["type"] == "os"]


def surf(p):
    d = unit(np.asarray(p, float) - CC)
    ts = np.linspace(0.5, 5.0, 400)
    P = CC + d[None] * ts[:, None]
    inside = np.zeros(len(ts), bool)
    for o in OCC_CR:
        inside |= sdf_box(o, P) < 0
    k = np.nonzero(inside)[0]
    return P[k.max()] if len(k) else P[0]


def crack(pts, w):
    pts = [S(*p) for p in pts]
    out = []
    for a, b in zip(pts, pts[1:]):
        n = max(2, int(np.linalg.norm(b - a) / 0.04))
        for k in range(n):
            out.append(surf(a + (b - a) * k / n))
    out.append(surf(pts[-1]))
    return np.array(out), w


CRACKS = [
    crack([(-1.0, 3.7, 0.3), (-1.8, 3.4, 0.7), (-2.6, 2.6, 0.9), (-2.9, 1.7, 0.5), (-2.9, 0.7, 1.0)], 0.075),
    crack([(-2.9, 1.7, 0.5), (-2.9, 1.25, -0.3)], 0.055),
    crack([(-1.8, 3.4, 0.7), (-1.5, 3.7, 1.5)], 0.05),
    crack([(-0.05, 3.1, 3.4), (-0.8, 2.2, 3.9), (-1.25, 1.0, 3.9)], 0.065),
]


def crack_field(P):
    """Distance aux fissures (px) ; inf si loin."""
    d = np.full(P.shape[:-1], 9.0)
    lo, hi = P.reshape(-1, 3).min(0) - 0.5, P.reshape(-1, 3).max(0) + 0.5
    for pts, w in CRACKS:
        sel = pts[np.all((pts > lo) & (pts < hi), axis=1)]
        if not len(sel):
            continue
        Pf = P.reshape(-1, 3)
        dd = np.full(len(Pf), 9.0)
        for ch in range(0, len(sel), 64):
            q = sel[ch:ch + 64]
            dd = np.minimum(dd, np.linalg.norm(Pf[:, None, :] - q[None], axis=-1).min(1))
        d = np.minimum(d, (dd / (w / 0.075)).reshape(d.shape))
    return d


OCC_ALL = [c for c in CUBES if c["mat"]["type"] in ("os", "corne")]


def ao_field(c, P, n):
    ao = np.ones(P.shape[:-1])
    cen = P.reshape(-1, 3).mean(0)
    rad = np.linalg.norm(P.reshape(-1, 3) - cen, axis=1).max()
    for o in OCC_ALL:
        if o is c or o["sec"] == c["sec"] or (o["mirror_of"] and o["mirror_of"] == c["name"]) or (c["mirror_of"] and c["mirror_of"] == o["name"]):
            continue
        if np.linalg.norm(o["cw"] - cen) > rad + np.linalg.norm(o["half"]) + 0.8:
            continue
        d = sdf_box(o, P + n * 0.03)
        ao = np.minimum(ao, 1 - 0.38 * np.clip(1 - np.maximum(d, 0) / 0.7, 0, 1))
    return ao


def os_color(c, P, n):
    Pl = P - C0
    part = c["mat"]["part"]
    if part == "mach":
        part_ = "mach"
    else:
        part_ = part
    N = smooth_normal(Pl, n, part_)
    lum = np.clip(0.5 + 0.5 * (N @ LK), 0, 1)
    lum = lum * (0.9 + 0.16 * vnoise(Pl, 1.6, 1.0)) * (0.96 + 0.06 * vnoise(Pl, 6.0, 2.0))
    col = lerp(C_OMBRE, C_OS, np.clip(lum / 0.55, 0, 1)[..., None])
    col = lerp(col, C_HAUT, (np.clip((lum - 0.6) / 0.3, 0, 1) * 0.85)[..., None])
    col = lerp(col, C_RIM, (np.clip((N[..., 1] - 0.55) * 2.0, 0, 1) * 0.3)[..., None])
    # dessous plus sombre (règle des entités : dessus et avant clairs)
    col = col * (1 - 0.25 * np.clip(-N[..., 1], 0, 1))[..., None]
    col = col * ao_field(c, P, n)[..., None]
    ax = np.abs(Pl[..., 0])
    # orbites : ombre profonde et reflet vert de la flamme
    if part in ("face", "crane"):
        ex = (ax - 1.3) / 0.95
        ey = (Pl[..., 1] - 0.42) / 0.85
        r = np.sqrt(ex * ex + ey * ey)
        prof = np.clip((Pl[..., 2] + 3.2) / 0.45, 0, 1) * (Pl[..., 2] < -1.3)
        sock = np.clip((1.25 - r) / 0.35, 0, 1) * prof
        col = lerp(col, C_CREUX, (sock * 0.92)[..., None])
        dE = np.sqrt((ax - 1.3) ** 2 + (Pl[..., 1] - 0.42) ** 2 + (Pl[..., 2] + 2.05) ** 2)
        col = col + (A((30, 90, 24)) * (np.clip(1 - dE / 1.05, 0, 1) ** 1.5)[..., None])
    # fosse nasale (cœur renversé) avec la braise au fond
    if part == "face":
        y = Pl[..., 1]
        lobe = ((ax - 0.2) / 0.27) ** 2 + ((y + 0.62) / 0.36) ** 2 < 1
        tri = (y < -0.62) & (y > -1.38) & (ax < 0.47 * (y + 1.38) / 0.76)
        front = Pl[..., 2] < -3.0
        nez = (lobe | tri) & front
        col = np.where(nez[..., None], lerp(C_CREUX, A((26, 70, 30)), np.clip(1 - np.sqrt(ax ** 2 + (y + 0.8) ** 2) / 0.5, 0, 1)[..., None]), col)
        bord = (~nez) & front & ((((ax - 0.2) / 0.36) ** 2 + ((y + 0.62) / 0.45) ** 2 < 1) | ((y < -0.6) & (y > -1.5) & (ax < 0.6 * (y + 1.5) / 0.9)))
        col = np.where(bord[..., None], col * 0.6, col)
    # sutures (voûte) : fines lignes sombres
    if part == "crane":
        sag = (np.abs(Pl[..., 0] - 0.06 * np.sin(Pl[..., 2] * 9)) < 0.035) & (Pl[..., 1] > 2.6) & (Pl[..., 2] > -1.4) & (Pl[..., 2] < 2.9)
        cor = (np.abs(Pl[..., 2] + 0.7 - 0.07 * np.sin(Pl[..., 0] * 10)) < 0.035) & (Pl[..., 1] > 1.8)
        lam = (np.abs(Pl[..., 2] - 2.6 + 0.25 * np.abs(Pl[..., 0]) - 0.06 * np.sin(Pl[..., 0] * 11)) < 0.035) & (Pl[..., 1] > 0.6) & (Pl[..., 1] < 3.0)
        col = np.where((sag | cor | lam)[..., None], col * 0.55, col)
    e = np.zeros(col.shape, np.float32)
    if part in ("crane", "face"):
        d = crack_field(P)
        col = lerp(col, C_OMBRE, np.clip((0.22 - d) / 0.08, 0, 1)[..., None] * 0.8)
        col = lerp(col, C_AURA, np.clip((0.3 - d) / 0.2, 0, 1)[..., None] * 0.5)
        col = lerp(col, C_VEIN, np.clip((0.085 - d) / 0.02, 0, 1)[..., None])
        col = lerp(col, C_VCORE, np.clip((0.04 - d) / 0.015, 0, 1)[..., None])
        e = np.where((d < 0.085)[..., None], E_VERT * 0.85, e)
    return col, e


def dent_color(c, P, n):
    Pl = P - C0
    haut = c["mat"]["haut"]
    y = Pl[..., 1]
    along = Pl[..., 2] if c["mat"].get("cote") else Pl[..., 0]
    if haut:
        top, Lt = -1.7, 0.42
        h = (top - y) / Lt                  # 0 à la racine, 1 à la pointe
    else:
        top, Lt = -1.95, 0.34
        h = (y - top) / Lt
    pas = 0.36
    k = along / pas
    u = (k - np.floor(k) - 0.5) * 2         # -1..1 dans la dent
    prof = 0.92 * np.sqrt(np.clip(1 - np.clip(h, 0, 2) ** 2.4, 0, 1))
    inside = (np.abs(u) < prof) & (h < 1.0)
    racine = h < 0.12
    alpha = (inside | racine) & (h > -0.6)
    t = np.clip(h, 0, 1)
    col = lerp(A((58, 50, 74)), A((168, 150, 196)), (t ** 0.7)[..., None])
    col = col * (0.85 + 0.15 * (1 - np.abs(u)))[..., None]
    col = np.where((racine & ~(inside & (h > 0.05)))[..., None], A((22, 16, 30)), col)
    col = lerp(col, C_OMBRE, (np.clip((np.abs(u) - prof + 0.12) / 0.12, 0, 1) * inside)[..., None] * 0.6)
    return col, alpha


def croc_color(c, P, n):
    Pl = P - C0
    y = Pl[..., 1]
    if c["mat"]["haut"]:
        t = np.clip((-1.9 - y) / 1.0, 0, 1)
    else:
        t = np.clip((y + 2.5) / 0.75, 0, 1)
    lum = np.clip(0.55 + 0.45 * (n @ LK), 0, 1)
    col = lerp(A((40, 34, 52)), A((176, 158, 204)), (lum * (0.5 + 0.5 * t))[..., None])
    col = lerp(col, A((196, 182, 222)), np.clip((t - 0.75) / 0.25, 0, 1)[..., None] * 0.6)
    return col, None


def corne_color(c, P, n):
    pts = np.array(CORNE_PTS) if (P[..., 0].mean() < C0[0]) else np.array([mir(p) for p in CORNE_PTS])
    Pf = P.reshape(-1, 3)
    best = np.full(len(Pf), 9.0)
    tt = np.zeros(len(Pf))
    rad = np.zeros((len(Pf), 3))
    acc_ = 0.0
    for i in range(len(CORNE_L)):
        a, b = pts[i], pts[i + 1]
        ab = b - a
        s = np.clip(((Pf - a) @ ab) / (ab @ ab), 0, 1)
        q = a + s[:, None] * ab
        d = np.linalg.norm(Pf - q, axis=1)
        ok = d < best
        best[ok] = d[ok]
        tt[ok] = (acc_ + s[ok] * CORNE_L[i]) / CORNE_LEN
        rad[ok] = (Pf - q)[ok]
        acc_ += CORNE_L[i]
    rn = rad / np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-9)
    N = 0.7 * rn + 0.3 * n
    N = N / np.linalg.norm(N, axis=1, keepdims=True)
    lum = np.clip(0.5 + 0.5 * (N @ LK), 0, 1)
    t = tt.reshape(P.shape[:-1])
    lum = lum.reshape(t.shape)
    base = lerp(A((22, 18, 30)), A((60, 50, 78)), np.clip(t / 0.7, 0, 1)[..., None])
    col = base * (0.55 + 0.75 * lum)[..., None]
    col = lerp(col, A((150, 112, 196)), (np.clip((lum - 0.78) / 0.2, 0, 1) * 0.6)[..., None])
    bague = (np.mod(t * 11, 1) < 0.16) & (t < 0.68)
    col = np.where(bague[..., None], col * 0.58, col)
    col = lerp(col, A((116, 224, 50)), smv(t, 0.84, 0.99)[..., None])
    col = lerp(col, A((196, 255, 110)), (smv(t, 0.93, 1.0) * lum)[..., None])
    # filet lumineux dans la rainure de la base (démon élégant)
    fil = (np.mod(t * 11, 1) > 0.05) & (np.mod(t * 11, 1) < 0.1) & (t < 0.45) & (t > 0.08)
    col = np.where(fil[..., None], lerp(col, C_VEIN, 0.55), col)
    e = np.where((t > 0.9)[..., None], E_VERT, 0).astype(np.float32)
    return col, e


def oeil_color(c, P, n):
    Pl = P - C0
    side = -1.0 if Pl[..., 0].mean() < 0 else 1.0
    u = (Pl[..., 0] - side * 1.3) * side       # vers l'extérieur
    v = Pl[..., 1] - 0.42
    ca, sa = math.cos(math.radians(18)), math.sin(math.radians(18))
    a = u * ca + v * sa
    b = -u * sa + v * ca
    q = np.sqrt((a / 0.66) ** 2 + (b / 0.36) ** 2)
    ins = (q < 1) & (b < 0.27)
    fente = (np.abs(a) < 0.06 * (1 - np.clip((b / 0.34) ** 2, 0, 1)) + 0.012) & (np.abs(b) < 0.31)
    col = np.empty(P.shape, np.float32)
    col[...] = C_CREUX
    corps = lerp(A((60, 170, 44)), A((120, 236, 60)), np.clip(1 - q, 0, 1)[..., None] * 1.4)
    corps = lerp(corps, A((226, 255, 176)), np.clip((0.42 - q) / 0.22, 0, 1)[..., None])
    corps = lerp(corps, A((40, 120, 34)), np.clip((b - 0.12) / 0.15, 0, 1)[..., None] * 0.7)   # ombre de l'arcade
    col = np.where(ins[..., None], corps, col)
    col = np.where((ins & fente)[..., None], A((12, 34, 12)), col)
    # halo sombre-vert autour de l'amande
    col = np.where((~ins & (q < 1.4))[..., None], lerp(C_CREUX, A((22, 60, 24)), np.clip((1.4 - q) / 0.4, 0, 1)[..., None]), col)
    e = np.where((ins & ~fente)[..., None], lerp(E_VERT, A((225, 225, 170)), np.clip((0.45 - q) / 0.25, 0, 1)[..., None]), 0).astype(np.float32)
    return col, e


def gorge_color(c, P, n):
    Pl = P - C0
    r = np.sqrt((Pl[..., 0] / 1.0) ** 2 + ((Pl[..., 1] + 1.8) / 0.5) ** 2)
    deep = np.clip((Pl[..., 2] + 2.6) / 2.0, 0, 1)
    col = lerp(A((20, 10, 26)), A((70, 190, 50)), (np.clip(1 - r, 0, 1) * (0.4 + 0.6 * deep))[..., None])
    col = lerp(col, A((190, 255, 130)), (np.clip(0.4 - r, 0, 1) * deep)[..., None] * 1.5)
    e = np.where((r < 0.7)[..., None], E_VERT * np.clip(1 - r, 0, 1)[..., None] * 1.2, 0).astype(np.float32)
    return col, e


def flamme_shape(uu, vv, k, scale=1.0):
    """Forme de flamme : bas rond, langue qui ondule vers le haut. uu dans [-1, 1], vv dans [0, 1] (bas -> haut)."""
    cx = 0.1 * np.sin(vv * math.pi * 1.6 + k)
    w = 0.92 * np.sin(np.clip(vv * 0.9 + 0.08, 0, 1) * math.pi) ** 0.65 * (1 - 0.35 * vv) * scale
    w = np.where(vv < 0.3, np.sqrt(np.clip(1 - ((0.3 - vv) / 0.3) ** 2, 0, 1)) * 0.92 * scale * 0.98 + 0.02, w)
    d = np.abs(uu - cx) / np.maximum(w, 1e-3)
    # deux langues au sommet de la première bouffée
    return d


def flamme_tile(W, H, k):
    s = (np.arange(W * SS) + 0.5) / (W * SS)
    t = (np.arange(H * SS) + 0.5) / (H * SS)
    S_, T_ = np.meshgrid(s, t)
    uu, vv = S_ * 2 - 1, 1 - T_
    d = flamme_shape(uu, vv, k)
    nz = vnoise(np.dstack([S_ * 3, T_ * 4, np.full_like(S_, k)]), 1.0, 5.0 + k)
    d = d * (0.92 + 0.16 * nz)
    ins = (d < 1) & (vv > 0.02) & (vv < 0.97)
    a = 225 * np.clip(1 - d ** 2, 0, 1) ** 0.55 * np.clip(vv / 0.12, 0, 1) * (1 - 0.35 * vv)
    col = lerp(A((70, 200, 56)), A((132, 246, 74)), np.clip(1 - d, 0, 1)[..., None] * 1.3)
    col = lerp(col, A((228, 255, 190)), (np.clip((0.45 - d) / 0.3, 0, 1) * np.clip(1 - vv * 1.3, 0, 1))[..., None])
    col_s = col.reshape(H, SS, W, SS, 3).mean((1, 3))
    a_s = (a * ins).reshape(H, SS, W, SS).mean((1, 3))
    out = np.zeros((H, W, 4), np.uint8)
    on = a_s > 18
    out[..., :3] = (np.clip(col_s, 0, 255).astype(np.uint8) & 0xFC) * on[..., None]
    out[..., 3] = np.where(on, np.clip(a_s, 18, 238), 0).astype(np.uint8)
    return out


def coeur_tile(W, H, k):
    s = (np.arange(W * SS) + 0.5) / (W * SS)
    t = (np.arange(H * SS) + 0.5) / (H * SS)
    S_, T_ = np.meshgrid(s, t)
    uu, vv = S_ * 2 - 1, 1 - T_
    d = flamme_shape(uu, vv, k + 1.3)
    val = np.clip(1 - d, 0, 1) ** 0.9 * np.clip(vv / 0.15, 0, 1)
    col = lerp(A((20, 60, 16)), A((80, 112, 58)), val[..., None]) * val[..., None]
    col_s = col.reshape(H, SS, W, SS, 3).mean((1, 3))
    out = np.zeros((H, W, 4), np.uint8)
    on = col_s.max(-1) > 12
    out[..., :3] = (np.clip(col_s, 0, 110).astype(np.uint8) & 0xFC) * on[..., None]
    out[..., 3] = on * 255
    return out


def halo_tile(W):
    s = (np.arange(W) + 0.5) / W
    u, v = np.meshgrid(s, s)
    r = np.hypot(u * 2 - 1, v * 2 - 1)
    val = np.exp(-(r / 0.5) ** 2) * (r < 0.98)
    col = A((34, 92, 26)) * val[..., None]
    out = np.zeros((W, W, 4), np.uint8)
    on = col.max(-1) > 12
    out[..., :3] = (col.astype(np.uint8) & 0xFC) * on[..., None]
    out[..., 3] = on * 255
    return out


def braise_tile(W):
    s = (np.arange(W) + 0.5) / W
    u, v = np.meshgrid(s, s)
    x, y = np.abs(u * 2 - 1), np.abs(v * 2 - 1)
    et = (x ** 0.8 + y ** 0.8) < 0.9
    k = np.clip(1 - np.hypot(x, y) * 1.2, 0, 1)
    col = lerp(A((80, 200, 50)), A((230, 255, 180)), k[..., None])
    out = np.zeros((W, W, 4), np.uint8)
    out[..., :3] = (col.astype(np.uint8) & 0xFC) * et[..., None]
    out[..., 3] = et * 255
    e = np.zeros((W, W, 4), np.uint8)
    e[..., :3] = (lerp(E_VERT, A((225, 225, 170)), k[..., None]) * et[..., None]).astype(np.uint8)
    e[..., 3] = et * 255
    return out, e


# ================================================================== faces à peindre et atlas
for c in CUBES:
    c["paint"] = {}
for c in CUBES:
    if c["mirror_of"]:
        continue
    typ = c["mat"]["type"]
    for f in c["faces"]:
        if c["sym"] and f == "east" and "west" in c["faces"]:
            continue
        P4, w, h, n = face_info(c, f)
        vis = 1.0
        if typ in OPAQUE:
            s_, t_ = np.meshgrid(np.linspace(0.02, 0.98, 13), np.linspace(0.02, 0.98, 13))
            P = P4[0] + (P4[1] - P4[0]) * s_[..., None] + (P4[3] - P4[0]) * t_[..., None]
            bu = buried(c, P, n)
            if bu.all():
                continue
            vis = 1 - bu.mean()
        k = {"oeil": 1.15, "flamme": 0.42, "coeur": 0.42, "dent": 1.0, "croc": 1.0}.get(typ, 1.0)
        if vis < 0.45:
            k *= 0.8                     # face presque enfouie (marche entre deux paliers) : un peu moins dense
        c["paint"][f] = (w, h, k)


def pack(dens):
    items = []
    for c in CUBES:
        for f, (w, h, k) in c["paint"].items():
            items.append(((c["name"], f), max(2, int(round(w * dens * k))), max(2, int(round(h * dens * k)))))
    items.append((("_clair", "x"), 2, 2))
    items.append((("_braise", "x"), 14, 14))
    items.sort(key=lambda it: (-it[2], -it[1]))
    uv, x, y, shelf = {}, 0, 0, 0
    for key, w, h in items:
        if x + w > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        if y + h > TEX or w > TEX:
            return None
        uv[key] = (x, y, x + w, y + h)
        x += w + 1
        shelf = max(shelf, h)
    return uv


DENS = 40.0
while (UVR := pack(DENS)) is None:
    DENS -= 0.25
CLEAR = list(UVR[("_clair", "x")])
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
TRANS_RECTS, ADD_RECTS = [], []


def paint_face(c, f, rect):
    P4, w, h, n = face_info(c, f)
    u0, v0, u1, v1 = rect
    W, H = u1 - u0, v1 - v0
    typ = c["mat"]["type"]
    if typ == "flamme":
        tex[v0:v1, u0:u1] = flamme_tile(W, H, c["mat"]["k"])
        TRANS_RECTS.append(rect)
        return
    if typ == "coeur":
        tex[v0:v1, u0:u1] = coeur_tile(W, H, c["mat"]["k"])
        ADD_RECTS.append(rect)
        return
    if typ == "halo":
        tex[v0:v1, u0:u1] = halo_tile(W)
        ADD_RECTS.append(rect)
        return
    s = (np.arange(W * SS) + 0.5) / (W * SS)
    t = (np.arange(H * SS) + 0.5) / (H * SS)
    S_, T_ = np.meshgrid(s, t)
    P = P4[0] + (P4[1] - P4[0]) * S_[..., None] + (P4[3] - P4[0]) * T_[..., None]
    alpha = np.ones(S_.shape, bool)
    e = None
    if typ == "os":
        col, e = os_color(c, P, n)
    elif typ == "dent":
        col, alpha = dent_color(c, P, n)
    elif typ == "croc":
        col, e = croc_color(c, P, n)
    elif typ == "corne":
        col, e = corne_color(c, P, n)
    elif typ == "oeil":
        col, e = oeil_color(c, P, n)
    elif typ == "gorge":
        col, e = gorge_color(c, P, n)
    else:
        raise ValueError(typ)
    alpha &= ~buried(c, P, n)
    col_s = col.reshape(H, SS, W, SS, 3).mean((1, 3))
    al_s = alpha.reshape(H, SS, W, SS).mean((1, 3)) >= 0.5
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = (np.clip(col_s, 0, 255).astype(np.uint8) & 0xFC) * al_s[..., None]
    out[..., 3] = al_s * 255
    tex[v0:v1, u0:u1] = out
    if e is not None:
        e_s = e.reshape(H, SS, W, SS, 3).mean((1, 3))
        on = al_s & (e_s.max(-1) > 20)
        oe = np.zeros((H, W, 4), np.uint8)
        oe[..., :3] = np.where(on[..., None], np.clip(e_s, 0, 225), 0).astype(np.uint8)
        oe[..., 3] = on * 255
        tex_e[v0:v1, u0:u1] = oe


for c in CUBES:
    for f in c["paint"]:
        paint_face(c, f, UVR[(c["name"], f)])
u0, v0, u1, v1 = UVR[("_braise", "x")]
tex[v0:v1, u0:u1], tex_e[v0:v1, u0:u1] = braise_tile(u1 - u0)
BRAISE_UV = [u0, v0, u1, v1]
assert tex[CLEAR[1], CLEAR[0], 3] == 0

semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
allowed = np.zeros(semi.shape, bool)
for (a0, b0, a1, b1) in TRANS_RECTS:
    allowed[b0:b1, a0:a1] = True
assert not (semi & ~allowed).any(), "semi-transparence hors trans_"
for (a0, b0, a1, b1) in ADD_RECTS + TRANS_RECTS:
    tex_e[b0:b1, a0:a1] = 0                     # pas de _e sur l'additif ni sur la flamme


def png_b64(arr, fn):
    im = Image.fromarray(arr, "RGBA")
    im.save(fn, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


tex_b64 = png_b64(tex, f"{NOM}.png")
tex_e_b64 = png_b64(tex_e, f"{NOM}_e.png")


def uv_of(c, f):
    if c["mirror_of"]:
        tw = BYNAME[c["mirror_of"]]
        r = uv_of(tw, SWAP.get(f, f))
        return CLEAR if r == CLEAR else [r[2], r[1], r[0], r[3]]
    if c["sym"] and f == "east" and "west" in c["paint"]:
        r = UVR[(c["name"], "west")]
        return [r[2], r[1], r[0], r[3]]
    if f in c["paint"]:
        return list(UVR[(c["name"], f)])
    return CLEAR


def r3(v):
    return [round(float(x), 4) for x in v]


elements = []
for c in CUBES:
    e = {"name": c["name"], "type": "cube", "uuid": c["uuid"], "from": r3(c["frm"] - C0), "to": r3(c["to"] - C0), "origin": r3(c["cu"] - C0), "box_uv": False,
         "faces": {f: {"uv": uv_of(c, f), "texture": 0} for f in FACES6}}
    rot = euler(c["Rl"])
    if any(abs(a) > 1e-4 for a in rot):
        e["rotation"] = [round(a, 3) for a in rot]
    elements.append(e)

# particule : une plaque, face up seule, à 0,3 px au-dessus du pivot (recette validée)
PART_UUID = str(_uuid.uuid4())
elements.append({"name": "braise", "type": "cube", "uuid": PART_UUID, "from": [-0.35, 0.3, -0.35], "to": [0.35, 0.6, 0.35], "origin": [0, 0.45, 0], "box_uv": False,
                 "faces": {"up": {"uv": BRAISE_UV, "texture": 0}}})


def node(k):
    g = G[k]
    return {"name": g["name"], "origin": r3(g["o"] - C0), "uuid": g["uuid"], "rotation": [round(float(a), 3) for a in g["rest"]],
            "children": list(g["ids"]) + [node(ch) for ch in g["children"]]}


# familier vivant (guide 6.6) : aucun groupe du corps ; racine « esprit », centre du crâne à l'origine
outliner = [node("esprit"),
            {"name": "particle_braise", "origin": [0, 0, 0], "uuid": str(_uuid.uuid4()), "rotation": [0, 0, 0], "children": [PART_UUID]}]


# ================================================================== animations
def fmt(v):
    if isinstance(v, (int, float, np.floating)):
        return str(round(float(v) + 0.0, 3))
    return v


def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": fmt(v[0]), "y": fmt(v[1]), "z": fmt(v[2])}], "time": round(t, 4), "interpolation": "linear"}


TROP = []


def anim(name, length, sampler=None, n=1, loop="loop", molang=None, include_end=True):
    times = [i * length / n for i in range(n + (1 if include_end else 0))]
    tracks = {}
    if sampler:
        for t in times:
            for g, chans in sampler(t).items():
                for ch, v in chans.items():
                    tracks.setdefault(g, {}).setdefault(ch, []).append((t, v))
    A_ = {}
    for g, chans in tracks.items():
        A_[G[g]["uuid"]] = {"name": G[g]["name"], "type": "bone", "keyframes": [kf(ch, t, v) for ch, lst in chans.items() for t, v in lst]}
    for g, chans in (molang or {}).items():
        ent = A_.setdefault(G[g]["uuid"], {"name": G[g]["name"], "type": "bone", "keyframes": []})
        for ch, tup in chans.items():
            ent["keyframes"] = [k for k in ent["keyframes"] if k["channel"] != ch]
            for ax, e in enumerate(tup):
                if isinstance(e, str) and (len(e) > 512 or e.count(";") > 15):
                    TROP.append(f"{len(e)} car. {e.count(';') + 1} instr. : {name} {G[g]['name']} {ch} {'xyz'[ax]}")
            ent["keyframes"].append(kf(ch, 0.0, tup))
    return {"uuid": str(_uuid.uuid4()), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "pet_idle", "animators": A_}


def put(p, g, ch, v):
    if ch in p.setdefault(g, {}):
        a = p[g][ch]
        p[g][ch] = tuple(a[i] * v[i] for i in range(3)) if ch == "scale" else tuple(a[i] + v[i] for i in range(3))
    else:
        p[g][ch] = tuple(v)


def flamme_tilt(p, a1, a2=None, a3=None):
    a2 = a1 * 0.4 if a2 is None else a2
    a3 = a1 * 0.3 if a3 is None else a3
    put(p, "flamme1", "rotation", (a1, 0, 0))
    put(p, "flamme2", "rotation", (a2, 0, 0))
    put(p, "flamme3", "rotation", (a3, 0, 0))


# ---------------------------------------------------------------- états du familier vivant (guide 6.6, mode vol)
# Le mod le fait voler à `hauteur` au-dessus des pieds du joueur et gère sa place : les états ne règlent que l'allure
# (inclinaison, flamme couchée par le vent, mâchoire, yeux), plus aucune contre-rotation du torse ni place sur le joueur.
TW, TR, TSI, TFA, TSL, TSW = 1.6, 1.0, 3.0, 2.0, 4.0, 3.2


def s_walk(t):
    """pet_walk : il suit en glissant, nez un peu baissé, flamme couchée vers l'arrière."""
    w = TAU * t / TW
    p = {}
    put(p, "fam_etat", "position", (0.3 * math.sin(w), 0.3 * math.sin(2 * w + 0.8), 0))
    put(p, "crane", "rotation", (-8 + 2 * math.sin(2 * w), 2 * math.sin(w), 3 * math.sin(w + 0.6)))
    put(p, "machoire", "rotation", (-3 - 2 * math.sin(w), 0, 0))
    flamme_tilt(p, 26 + 5 * math.sin(2 * w), 10 + 4 * math.sin(2 * w - 0.7), 8 + 4 * math.sin(2 * w - 1.4))
    return p


def s_run(t):
    """pet_run : il fonce pour rattraper son maître, plus penché, yeux plissés, flamme à l'horizontale."""
    w = TAU * t / TR
    p = {}
    put(p, "fam_etat", "position", (0.35 * math.sin(w), 0.45 * math.sin(2 * w), 0))
    put(p, "crane", "rotation", (-16 + 2.5 * math.sin(2 * w), 0, 4 * math.sin(w)))
    put(p, "machoire", "rotation", (-9 - 3 * math.sin(2 * w), 0, 0))
    put(p, "oeil_l", "scale", (1, 0.8, 1))
    put(p, "oeil_r", "scale", (1, 0.8, 1))
    flamme_tilt(p, 46 + 5 * math.sin(2 * w), 18 + 5 * math.sin(2 * w - 0.8), 14 + 5 * math.sin(2 * w - 1.6))
    return p


def s_sit(t):
    """pet_sit (maître accroupi à côté, ou 20 s sans bouger) : il descend et se fait petit, yeux plissés, flamme basse
    (l'ancien sneak, sans contre-rotation)."""
    w = TAU * t / TSI
    p = {}
    put(p, "fam_etat", "position", (0.25 * math.sin(w), -2.2 + 0.3 * math.sin(w + 1), 0))
    put(p, "crane", "rotation", (-10 + 2 * math.sin(w), 8 * math.sin(w * 0.5) ** 2 - 4, 4 * math.sin(w)))
    put(p, "crane", "scale", (0.88, 0.88, 0.88))
    put(p, "oeil_l", "scale", (1, 0.55, 1))
    put(p, "oeil_r", "scale", (1, 0.55, 1))
    put(p, "flamme1", "scale", (0.75, 0.7 + 0.05 * math.sin(2 * w), 1))
    flamme_tilt(p, 10, 4, 4)
    return p


def s_swim(t):
    """pet_swim : sous l'eau, la flamme se tasse ; il nage nez en avant en ondulant."""
    w = TAU * t / TSW
    p = {}
    put(p, "fam_etat", "position", (0.3 * math.sin(w), 0.3 * math.sin(2 * w), 0))
    put(p, "crane", "rotation", (-6 + 3 * math.sin(w), 10 * math.sin(w * 0.5), 5 * math.sin(w)))
    put(p, "flamme1", "scale", (0.7, 0.62 + 0.06 * math.sin(2 * w), 1))
    flamme_tilt(p, 30 + 6 * math.sin(w))
    return p


def s_fall(t):
    """pet_fall : inertie, mâchoire ouverte, yeux écarquillés, flamme qui monte."""
    w = TAU * t / TFA
    p = {}
    put(p, "fam_etat", "position", (0.2 * math.sin(w), 0.3 * math.sin(2 * w), 0))
    put(p, "crane", "rotation", (8 + 3 * math.sin(2 * w), 0, 6 * math.sin(w)))
    put(p, "machoire", "rotation", (-15 - 4 * math.sin(2 * w), 0, 0))
    put(p, "oeil_l", "scale", (1.2, 1.25, 1))
    put(p, "oeil_r", "scale", (1.2, 1.25, 1))
    put(p, "flamme1", "scale", (0.95, 1.3 + 0.08 * math.sin(3 * w), 1))
    flamme_tilt(p, -6 + 4 * math.sin(2 * w), -4, -3)
    return p


def s_sleep(t):
    """pet_sleep (maître endormi, ou 60 s sans bouger) : il somnole bas, penché sur le côté, yeux presque clos,
    flamme qui respire lentement (l'ancien sleep, sans la place sur la poitrine)."""
    w = TAU * t / TSL
    p = {}
    put(p, "fam_etat", "position", (0, -3.0 - 0.25 * math.sin(w), 0))
    put(p, "crane", "rotation", (-12 + 2 * math.sin(w), 0, 10))
    put(p, "machoire", "rotation", (-1.5 - 1.5 * math.sin(w), 0, 0))
    put(p, "oeil_l", "scale", (1, 0.22 + 0.05 * math.sin(w), 1))
    put(p, "oeil_r", "scale", (1, 0.22 + 0.05 * math.sin(w), 1))
    put(p, "flamme1", "scale", (0.75 + 0.04 * math.sin(w), 0.62 + 0.1 * math.sin(w), 1))
    flamme_tilt(p, -8 + 3 * math.sin(w), -4, -3)
    return p



# ---------------------------------------------------------------- idle : base lente + comportements tirés au hasard (Molang)
TI = 24.0
TRANCHE = 6
NB_IDX = 24
# tirage pondéré : 0–7 et 22–23 calmes (10/24), 16 regarde autour x3, 11 regarde le joueur x2, 12 curieux x2, les autres x1
REMAP = "v.i=v.i>17?(v.i<20?16:(v.i<22?v.i-9:0)):v.i"
PRE = (f"v.s=q.life_time/{TRANCHE}+q.instance_seed*13;"
       f"v.i=math.floor(math.mod(math.sin(math.floor(v.s)*109+43)*517+517,1)*{NB_IDX});"
       f"{REMAP};v.u=math.mod(v.s,1)*{TRANCHE};v.e=math.clamp(math.min(v.u-0.9,5.3-v.u)/0.7,0,1)")
NUIT_DORT = "v.i=v.i+(v.i<4)*(q.time_of_day>0.3)*(q.time_of_day<0.7)*(13-v.i)"


def E(a, d):
    return f"math.sin(math.clamp((v.u-{a})/{d},0,1)*180)"


def EP(a, b, r=0.5):
    return f"math.clamp(math.min(v.u-{a},{b}-v.u)/{r},0,1)"


def SM(a, b):
    return f"(0.5-0.5*math.cos(math.clamp((v.u-{a})/{b - a},0,1)*180))"


COMPORTEMENTS = {
    8: "claque des dents (deux salves rapides)",
    9: "rire silencieux (tête en arrière, mâchoire qui tressaute)",
    10: "tourne sur lui-même",
    11: "regarde le joueur, tête penchée, petit sourire",
    12: "s'approche curieux, orbites écarquillées",
    13: "s'assoupit (descend, yeux mi-clos, flamme basse) puis se réveille en sursaut ; plus fréquent la nuit",
    14: "crache une flammèche (recule, gueule ouverte, jet de braises)",
    15: "fait peur (bond en avant, gueule et flamme grandes ouvertes) puis rit",
    16: "regarde autour de lui",
    17: "fait une petite ronde en volant (rayon 4 px)",
}
TERMS = {}


def T(g, ch, ax, n, expr):
    TERMS.setdefault((g, ch, ax), []).append((n, expr))


CLAQ = f"({E(1.2, 0.55)}+{E(3.2, 0.55)})"
T("machoire", "rotation", 0, 8, f"-20*{CLAQ}*math.abs(math.sin(v.u*1260))")
T("crane", "rotation", 2, 8, f"5*{CLAQ}*math.sin(v.u*1260)")
T("crane", "rotation", 0, 9, "13*v.e")
T("machoire", "rotation", 0, 9, "-v.e*(14+8*math.sin(v.u*1080))")
T("fam_comp", "position", 1, 9, "0.3*v.e*math.abs(math.sin(v.u*540))")
T("fam_comp", "rotation", 1, 10, f"360*{SM(1.2, 3.0)}")
T("fam_comp", "position", 1, 10, f"0.6*{E(1.2, 1.8)}")
T("fam_comp", "rotation", 1, 11, f"78*{EP(1.0, 4.8)}")
T("crane", "rotation", 2, 11, f"12*{EP(1.4, 4.6, 0.4)}")
T("machoire", "rotation", 0, 11, f"-8*{E(2.6, 1.2)}")
T("fam_comp", "position", 0, 12, f"-1.0*{EP(1.0, 4.8, 0.7)}")
T("fam_comp", "position", 1, 12, f"0.7*{EP(1.0, 4.8, 0.7)}")
T("fam_comp", "position", 2, 12, f"-2.6*{EP(1.0, 4.8, 0.7)}")
T("fam_comp", "rotation", 1, 12, f"30*{EP(1.0, 4.8, 0.7)}")
T("crane", "rotation", 2, 12, f"-16*{EP(1.4, 4.4)}")
T("oeil_l", "scale", 0, 12, f"0.18*{EP(1.2, 4.6)}")
T("oeil_l", "scale", 1, 12, f"0.18*{EP(1.2, 4.6)}")
T("oeil_r", "scale", 0, 12, f"0.18*{EP(1.2, 4.6)}")
T("oeil_r", "scale", 1, 12, f"0.18*{EP(1.2, 4.6)}")
DORT = EP(0.9, 4.6, 1.0)
T("fam_comp", "position", 1, 13, f"-0.9*{DORT}+0.5*{E(4.6, 0.4)}")
T("crane", "rotation", 0, 13, f"-14*{DORT}+10*{E(4.6, 0.35)}")
T("oeil_l", "scale", 1, 13, f"-0.75*{EP(0.9, 4.6, 0.8)}+0.25*{E(4.6, 0.4)}")
T("oeil_r", "scale", 1, 13, f"-0.75*{EP(0.9, 4.6, 0.8)}+0.25*{E(4.6, 0.4)}")
T("flamme2", "scale", 1, 13, f"-0.35*{DORT}")
T("machoire", "rotation", 0, 13, f"-4*{DORT}")
T("crane", "rotation", 0, 14, f"14*{E(0.9, 1.2)}-10*{E(2.1, 0.6)}")
T("machoire", "rotation", 0, 14, f"-30*{E(1.9, 0.8)}")
T("fam_comp", "position", 2, 14, f"0.7*{E(2.0, 0.7)}")
T("ctrl_emit#c", "position", 0, 14, f"8*{E(2.0, 0.6)}")
T("flamme2", "scale", 1, 14, f"0.4*{E(1.0, 1.2)}")
PEUR = E(0.9, 0.9)
RIRE = EP(2.0, 4.9, 0.4)
T("fam_comp", "position", 0, 15, f"-0.5*{PEUR}")
T("fam_comp", "position", 1, 15, f"0.7*{PEUR}+0.3*{RIRE}*math.abs(math.sin(v.u*540))")
T("fam_comp", "position", 2, 15, f"-2.2*{PEUR}")
T("machoire", "rotation", 0, 15, f"-34*{PEUR}-(12+8*math.sin(v.u*1080))*{RIRE}")
T("crane", "rotation", 0, 15, f"-8*{PEUR}+12*{RIRE}")
for k in ("oeil_l", "oeil_r"):
    T(k, "scale", 0, 15, f"0.4*{PEUR}")
    T(k, "scale", 1, 15, f"0.4*{PEUR}")
T("flamme2", "scale", 1, 15, f"0.7*{PEUR}")
T("flamme2", "scale", 0, 15, f"0.3*{PEUR}")
T("fam_comp", "rotation", 1, 16, "45*v.e*math.sin((v.u-0.9)*90)")
T("crane", "rotation", 0, 16, "8*v.e")
T("fam_orbite", "rotation", 1, 17, f"360*{SM(1.0, 4.6)}")
T("fam_comp", "rotation", 2, 17, f"-14*{E(1.0, 3.6)}")
T("machoire", "rotation", 0, 17, f"-10*{E(1.0, 3.6)}")

# base lente (q.anim_time, périodes qui divisent 24 s)
BASE_IDLE = {
    ("fam_orbite", "rotation"): (0, 0, 0),
    ("fam_comp", "position"): ("0.35*math.sin(q.anim_time*15)", 0, "0.4*math.sin(q.anim_time*30)"),
    ("fam_comp", "rotation"): (0, "6*math.sin(q.anim_time*15+60)", 0),
    ("crane", "rotation"): ("2*math.sin(q.anim_time*45+30)", 0, "3*math.sin(q.anim_time*30)"),
    ("machoire", "rotation"): ("-3-1.5*math.sin(q.anim_time*45)", 0, 0),
    ("oeil_l", "scale"): (1, 1, 1),
    ("oeil_r", "scale"): (1, 1, 1),
    ("flamme2", "scale"): (1, 1, 1),
    ("ctrl_emit#c", "position"): (0, 0, 0),
}


def ind(n):
    return f"(v.i=={n})"


def molang_key(base, terms, ch):
    extra = [NUIT_DORT] if any(n == 13 for n, _ in terms) else []
    pre = PRE + "".join(";" + x for x in extra)
    return pre + ";" + fmt(base) + "".join(f"+{ind(n)}*({e})" for n, e in terms)


RELAIS = {"fam_comp": ["fam_comp_b", "fam_comp_c"], "crane": ["crane_b"], "machoire": ["machoire_b", "machoire_c"], "oeil_l": ["oeil_l_b"], "oeil_r": ["oeil_r_b"]}
idle_molang = {}
for (g, ch), base in BASE_IDLE.items():
    chaine = [g] + RELAIS.get(g, [])
    par_g = {x: [] for x in chaine}
    for ax in range(3):
        terms = TERMS.get((g, ch, ax), [])
        b0 = base[ax]
        for j, gx in enumerate(chaine):
            if not terms:
                par_g[gx].append(b0 if j == 0 else (1 if ch == "scale" else 0))
                continue
            k1 = len(terms)
            while len(molang_key(b0, terms[:k1], ch)) > 508:
                k1 -= 1
            par_g[gx].append(molang_key(b0, terms[:k1], ch))
            terms = terms[k1:]
            b0 = 1 if ch == "scale" else 0
        assert not terms, f"relais insuffisants : {g} {ch}"
    for j, gx in enumerate(chaine):
        if j == 0 or any(isinstance(v, str) for v in par_g[gx]):
            idle_molang.setdefault(gx, {})[ch] = tuple(par_g[gx])
orph = [k for k in TERMS if (k[0], k[1]) not in BASE_IDLE]
assert not orph, f"comportements sur un canal sans base : {orph}"


def tranches(seed=0.0, n=4):
    out = []
    for k in range(n):
        v = k + seed * 13
        x = math.fmod(math.sin(math.radians(math.floor(v) * 109 + 43)) * 517 + 517, 1)
        i = int(math.floor(x * NB_IDX))
        out.append((16 if i < 20 else (i - 9 if i < 22 else 0)) if i > 17 else i)
    return out


# ---------------------------------------------------------------- couche permanente : regard, réactions au joueur et au monde
DT = "math.min(1,q.delta_time*{})"
# familier vivant (guide 6.6) : les requêtes 6.3 parlent du familier ; le maître par q.owner_*
NUIT = "math.clamp((0.27-math.abs(q.time_of_day-0.5))*6,0,1)"
VIE = "math.clamp((q.owner_max_health*0.5-q.owner_health)*0.4,0,1)"      # vie basse du maître : il s'inquiète
PRES = "math.clamp((1.7-q.owner_distance)*1.5,0,1)"                       # le maître vient tout près (il s'arrête à 2 blocs)
EVEIL = "(1-q.is_sleeping)"
SAC = ("v.g=q.life_time/1.6+q.instance_seed*9+10;"
       "v.ga=math.mod(math.abs(math.sin(math.mod(math.floor(v.g),10)*61))*331,1);v.gb=math.mod(math.abs(math.sin(math.mod(math.floor(v.g)-1,10)*61))*331,1)")
SACV = "math.lerp(v.gb,v.ga,math.clamp(math.mod(v.g,1)*7,0,1))"
SAC2 = ("v.h=q.life_time/2.4+q.instance_seed*7+3;"
        "v.ha=math.mod(math.abs(math.sin(math.mod(math.floor(v.h),10)*47))*263,1);v.hb=math.mod(math.abs(math.sin(math.mod(math.floor(v.h)-1,10)*47))*263,1)")
SACV2 = "math.lerp(v.hb,v.ha,math.clamp(math.mod(v.h,1)*5,0,1))"
BLINK = ("v.b=q.life_time/3.2+q.instance_seed*5;"
         "v.c=math.sin(math.clamp((math.mod(v.b,1)-math.mod(math.floor(v.b)*0.618,0.75))*16,0,1)*180)")
eye_s = f"1+0.07*math.sin(q.life_time*90)-0.3*{VIE}*math.abs(math.sin(q.life_time*1102.5))"
overlay_molang = {
    # porté (menu Apparence, ou deuxième familier : guide 6.6) : à droite du joueur à hauteur de tête, comme avant
    "esprit": {"position": ("(1-q.is_pet)*12", "(1-q.is_pet)*28.5", "(1-q.is_pet)*1")},
    "fam_flot": {
        # vie basse du maître : il se tasse ; flottement irrégulier
        "position": ("0.25*math.sin(q.life_time*45+q.instance_seed*360)",
                     f"v.w=math.lerp(v.w,{VIE},{DT.format(1.5)});-0.8*v.w+0.45*math.sin(q.life_time*90+q.instance_seed*360)+0.2*math.sin(q.life_time*67.5)",
                     "0.3*math.sin(q.life_time*22.5+40)"),
        # regard : saccades de la tête (il regarde autour), il lève le nez quand son maître vient tout près
        "rotation": (f"v.hx=math.lerp(v.hx,{PRES}*-10*{EVEIL},{DT.format(2.5)});{SAC2};v.hx+2*math.sin(q.life_time*67.5)+({SACV2}*10-5)*{EVEIL}",
                     f"{SAC};({SACV}*36-18)*{EVEIL}",
                     f"v.yr=math.lerp(v.yr,math.clamp(-q.yaw_speed*0.05,-12,12),{DT.format(2)});v.r=math.lerp(v.r,q.is_in_rain,{DT.format(1)});"
                     "v.q=math.mod(q.life_time/8+q.instance_seed*5,1)*8;"
                     "v.yr+3*math.sin(q.life_time*112.5)+v.r*9*math.sin(v.q*1800)*math.sin(math.clamp(v.q/0.8,0,1)*180)"),
    },
    "fam_orbite": {"rotation": (0, f"v.lag=math.lerp(v.lag,math.clamp(q.yaw_speed*0.06,-14,14),{DT.format(3)});v.lag", 0)},
    "flamme1": {"scale": ("1+0.06*math.sin(q.life_time*405)",
                          f"(1+0.1*math.sin(q.life_time*540)+0.05*math.sin(q.life_time*1260))*(1-0.25*q.is_in_rain-0.35*q.is_in_water+0.3*q.is_in_lava+{NUIT}*(0.15+0.1*(q.moon_phase==0)))", 1)},
    "flamme2": {"rotation": (0, 0, "6*math.sin(q.life_time*292.5+40)"), "scale": (1, "1+0.12*math.sin(q.life_time*607.5+20)", 1)},
    "flamme3": {"rotation": (0, 0, "9*math.sin(q.life_time*382.5+90)")},
    # maître tout près : tête penchée, gueule entrouverte en sourire (plus de sens de q.head_y_rotation à deviner)
    "crane_b": {"rotation": ("-5*v.m", f"v.m=math.lerp(v.m,{PRES}*{EVEIL},{DT.format(3)});0", "12*v.m")},
    "machoire_b": {"rotation": ("-7*v.m", 0, 0)},
    "ctrl_emit#c": {"position": (-1, 0, 0)},
    "ctrl_lumiere#c": {"position": (f"0.5*{NUIT}", 0, 0)},
}
for k in ("oeil_l", "oeil_r"):
    overlay_molang[k] = {"position": (f"{SAC};({SACV}*0.3-0.15)", f"{SAC};(math.mod({SACV}*7.3,1)*0.2-0.1)", 0),
                         "scale": (eye_s, f"{BLINK};({eye_s})*(1-0.85*v.c)", 1)}
# menu Apparence : plus de cachette par q.is_in_menu (le mod oriente cam_/camy_ dans le menu depuis le guide du 2026-11-06 soir)


# ---------------------------------------------------------------- événements, attaque, blessure (s'ajoutent à l'état)
def os_flamme_scale(p, so, sf):
    put(p, "os", "scale", (so, so, so))
    put(p, "flamme1", "scale", (sf, sf, sf))


FL_PIV = (0.0, 2.9, 2.6)        # pivot de flamme1 : sommet arrière du crâne ; le centre du crâne est à l'origine


def _flamme(p, s, k, sy=1.0):
    """Flamme d'âme à l'échelle s ; k = 0 : posée au centre du crâne (son cœur), k = 1 : à sa place sur l'occiput."""
    put(p, "flamme1", "scale", (s, s * sy, s))
    put(p, "flamme1", "position", tuple(-(1 - k) * v for v in FL_PIV))


def _yeux(p, e):
    for k in ("oeil_l", "oeil_r"):
        put(p, k, "scale", (max(0.02, e), max(0.02, e), 1))
    for s_ in "lr":                                        # halos des orbites : allumés avec les yeux
        put(p, f"ctrl_alpha#h{s_}", "position", (-1 + sm(e, 0.5, 0.9), 0, 0))


def _cornes(p, c):
    for i in range(5):
        k = max(0.02, sm(c, 0.12 * i, 0.12 * i + 0.5))
        for s_ in "lr":
            put(p, f"corne{i + 1}_{s_}", "scale", (k, k, k))


def _regard(p, t, a, b, c, d):
    """Retombée : il lève le nez vers son maître, tête penchée, sourire entrouvert."""
    r = bump(t, a, b, c, d)
    put(p, "crane", "rotation", (10 * r, 0, 10 * r))
    put(p, "machoire", "rotation", (-6 * r, 0, 0))


def ev_equip(t):
    """event_equip (2,0 s) : une flammèche s'allume, seule, là où sera le cœur du crâne, vacille, puis s'embrase d'un coup
    (son d'âme qui s'échappe) ; les os se forment autour d'elle en tournant pendant qu'elle remonte à sa place sur
    l'occiput ; les cornes poussent de la base à la pointe ; les orbites s'allument en dernier ; il claque des dents
    deux fois, puis lève le nez vers son maître, tête penchée."""
    p = {}
    vac = 1 + 0.25 * math.sin(TAU * 9 * t) * (1 - sm(t, 0.3, 0.45))
    s = 0.08 + 0.35 * sm(t, 0.0, 0.3) + 0.57 * sm(t, 0.38, 0.55) + 0.35 * bump(t, 0.4, 0.55, 0.62, 0.95)
    _flamme(p, s, sm(t, 0.5, 0.95), sy=vac * (1 + 0.5 * bump(t, 0.38, 0.5, 0.6, 0.9)))
    so = max(0.02, sm(t, 0.45, 0.9) * (1 + 0.1 * bump(t, 0.8, 0.9, 0.94, 1.1)))
    put(p, "os", "scale", (so, so, so))
    put(p, "fam_ev", "rotation", (0, 160 * (1 - sm(t, 0.45, 1.0)), 0))
    put(p, "fam_ev", "position", (0, -1.2 * (1 - sm(t, 0.45, 1.0)), 0))
    _cornes(p, sm(t, 0.7, 1.15))
    _yeux(p, sm(t, 1.05, 1.18) * (1 + 0.35 * bump(t, 1.12, 1.18, 1.2, 1.38)))
    put(p, "machoire", "rotation", (-20 * bump(t, 1.25, 1.31, 1.33, 1.39) - 16 * bump(t, 1.42, 1.48, 1.5, 1.56), 0, 0))
    _regard(p, t, 1.5, 1.68, 1.8, 2.0)
    return p


def ev_teleport(t):
    """event_teleport (1,2 s, coincé 3 s ou à plus de 20 blocs) : même logique en bref : la flammèche jaillit, le crâne
    se reforme autour d'elle, les yeux se rallument, un claquement de dents, puis il regarde son maître."""
    p = {}
    s = 0.2 + 0.8 * sm(t, 0.0, 0.18) + 0.3 * bump(t, 0.08, 0.18, 0.22, 0.45)
    _flamme(p, s, sm(t, 0.15, 0.45), sy=1 + 0.4 * bump(t, 0.05, 0.15, 0.2, 0.4))
    so = max(0.02, sm(t, 0.12, 0.42) * (1 + 0.08 * bump(t, 0.36, 0.42, 0.45, 0.58)))
    put(p, "os", "scale", (so, so, so))
    put(p, "fam_ev", "rotation", (0, 90 * (1 - sm(t, 0.12, 0.5)), 0))
    _cornes(p, sm(t, 0.25, 0.5))
    _yeux(p, sm(t, 0.48, 0.58) * (1 + 0.3 * bump(t, 0.54, 0.58, 0.6, 0.72)))
    put(p, "machoire", "rotation", (-18 * bump(t, 0.66, 0.71, 0.73, 0.79), 0, 0))
    _regard(p, t, 0.78, 0.92, 1.0, 1.2)
    return p


def ev_jump(t):
    p = {}
    put(p, "fam_ev", "position", (0, -0.8 * bump(t, 0.0, 0.08, 0.1, 0.25) + 0.6 * bump(t, 0.2, 0.35, 0.4, 0.6), 0))
    put(p, "flamme1", "scale", (1, 1 + 0.25 * bump(t, 0.0, 0.12, 0.2, 0.45), 1))
    put(p, "crane", "rotation", (6 * bump(t, 0.05, 0.18, 0.25, 0.5), 0, 0))
    return p


AMP = "math.clamp(q.land_speed*0.1,0.4,1.4)"


def ev_land(t):
    b = bump(t, 0.0, 0.07, 0.12, 0.35) - 0.3 * bump(t, 0.32, 0.4, 0.42, 0.55)
    return {"fam_ev": {"position": (0, f"{round(-1.2 * b, 4)}*{AMP}", 0)},
            "machoire": {"rotation": (f"{round(-16 * bump(t, 0.05, 0.12, 0.16, 0.26), 4)}*{AMP}", 0, 0)},
            "flamme1": {"scale": (1, f"1-{round(0.2 * bump(t, 0.0, 0.07, 0.12, 0.4), 4)}*{AMP}", 1)}}


def ev_owner_hurt(t):
    """event_owner_hurt (son maître prend un coup) : il sursaute, orbites écarquillées et flamme qui flambe, puis montre
    les dents, furieux, la tête secouée de colère."""
    p = {}
    b = bump(t, 0.0, 0.07, 0.18, 0.5)
    f = bump(t, 0.35, 0.5, 0.85, 1.1)
    put(p, "fam_ev", "position", (0, 1.4 * b, 1.6 * b - 1.0 * f))
    put(p, "crane", "rotation", (18 * b - 8 * f, 0, 10 * bump(t, 0.0, 0.05, 0.25, 0.6) * math.sin(TAU * t * 7)
                                 + 6 * f * math.sin(TAU * t * 9)))
    put(p, "machoire", "rotation", (-20 * bump(t, 0.02, 0.1, 0.2, 0.5) - 26 * f, 0, 0))
    e_ = 1 + 0.4 * bump(t, 0.0, 0.05, 0.15, 0.45) - 0.3 * f
    for k in ("oeil_l", "oeil_r"):
        put(p, k, "scale", (1 + 0.4 * bump(t, 0.0, 0.05, 0.15, 0.45), e_, 1))
    put(p, "flamme1", "scale", (1 + 0.2 * b + 0.15 * f, 1 + 0.5 * b + 0.35 * f, 1))
    return p


def ev_reveil(t):
    """event_exit_sleep : il se réveille en sursaut, remonte, les yeux se rallument, la flamme jaillit."""
    p = {}
    b = bump(t, 0.0, 0.12, 0.25, 0.7)
    put(p, "fam_ev", "position", (0, 0.8 * b, 0))
    put(p, "crane", "rotation", (10 * b, 0, 0))
    put(p, "machoire", "rotation", (-14 * bump(t, 0.05, 0.15, 0.3, 0.6), 0, 0))
    for k in ("oeil_l", "oeil_r"):
        put(p, k, "scale", (1 + 0.25 * b, 1 + 0.3 * b, 1))
    put(p, "flamme1", "scale", (1, 1 + 0.4 * b, 1))
    return p


# pet_idle et pet_fly : base lente + comportements tirés au hasard ; en vol, il penche le nez et couche sa flamme selon
# sa vitesse (q.ground_speed du familier), au cas où le mode vol joue pet_fly aussi à l'arrêt (supposé, guide muet)
VIT = "math.clamp(q.ground_speed/4.3,0,1.4)"
fly_molang = dict(idle_molang)
fly_molang["fam_etat"] = {"rotation": (f"-8*{VIT}", 0, 0), "position": (0, f"0.3*math.sin(q.anim_time*45)*{VIT}", 0)}
fly_molang["flamme1"] = {"rotation": (f"26*{VIT}", 0, 0)}
fly_molang["flamme2"] = {"rotation": (f"10*{VIT}", 0, 0), "scale": idle_molang["flamme2"]["scale"]} if "flamme2" in idle_molang else {"rotation": (f"10*{VIT}", 0, 0)}
fly_molang["flamme3"] = {"rotation": (f"8*{VIT}", 0, 0)}

# familier vivant (guide 6.6) : vol près de l'épaule, à 2 blocs, hauteur de tête (centre du crâne à 1,8 bloc)
FAMILIER = {"mode": "vol", "distance": 2, "vitesse": 1, "hauteur": 1.8}
ANIMS = [
    anim("pet_idle", TI, molang=idle_molang),
    anim("pet_fly", TI, molang=fly_molang),
    anim("pet_walk", TW, s_walk, 16),
    anim("pet_run", TR, s_run, 12),
    anim("pet_sit", TSI, s_sit, 18),
    anim("pet_sleep", TSL, s_sleep, 20),
    anim("pet_swim", TSW, s_swim, 20),
    anim("pet_fall", TFA, s_fall, 16),
    anim("overlay_crane", 16.0, molang=overlay_molang),
]
ev = anim("event_equip", 2.0, ev_equip, 60, loop="once")
ev["animators"]["effects"] = {"name": "Effects", "type": "effect",
                              "keyframes": [{"channel": "sound", "data_points": [{"effect": "particle.soul_escape", "file": ""}], "time": 0.38}]}
ANIMS += [ev, anim("event_teleport", 1.2, ev_teleport, 36, loop="once"), anim("event_owner_hurt", 1.2, ev_owner_hurt, 36, loop="once"),
          anim("event_exit_sleep", 0.8, ev_reveil, 24, loop="once"),
          anim("event_jump", 0.6, ev_jump, 18, loop="once"), anim("event_land", 0.6, ev_land, 18, loop="once")]
assert len(ANIMS) <= 32, len(ANIMS)
assert not TROP, "\n".join(TROP)

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS,
         "unhandled_root_fields": {"phynaria": {"version": 1, "familier": FAMILIER}}}
limiter_sons(model)
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


mol = [e for a in ANIMS for b in a["animators"].values() for k in b["keyframes"] for e in k.get("data_points", [{}])[0].values() if isinstance(e, str) and "q." in e]
print(len(elements), "cubes ;", len(G) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      f"densité {DENS:.2f} texels/px ; remplissage {sum((r[2] - r[0]) * (r[3] - r[1]) for r in UVR.values()) / TEX ** 2:.0%}")
print("Molang : plus longue clé", max(len(e) for e in mol), "car.,", max(e.count(";") + 1 for e in mol), "instructions")
print("tranches de l'aperçu (graine 0) :", tranches(0.0, 4), "; graine 0,37 :", tranches(0.37, 8))

if os.environ.get("AIRE"):
    agg = {}
    for c in CUBES:
        for f, (w, h, k) in c["paint"].items():
            agg[c["name"]] = agg.get(c["name"], 0) + w * h * k * k
    tot = sum(agg.values())
    print("aire totale", round(tot, 1), "px²")
    for n_, a_ in sorted(agg.items(), key=lambda x: -x[1])[:30]:
        print(f"  {n_:14s} {a_:6.1f}  faces {list(BYNAME[n_]['paint'])}")
