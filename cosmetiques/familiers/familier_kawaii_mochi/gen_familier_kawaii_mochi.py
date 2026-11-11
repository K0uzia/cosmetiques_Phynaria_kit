"""Familier nuage-mochi v3 (2026-11-08) : FAMILIER VIVANT en mode vol (guide 6.6). Géométrie, texture, proportions et palette
de la v2 inchangées (générateur gardé dans .build/gen_avant.py, livrable dans .build/avant_livrable.bbmodel) : seuls la racine,
le placement et les animations changent (leçon du renard : la v10 qui reprend la v4 telle quelle, pas une refonte).
  - mode « vol » : c'est un nuage, il n'a pas de pattes et flotte par nature (types-familiers.md : slime, nuage, mascotte
    magique ; familiers.md cite le mochi en exemple) ; bloc {"mode": "vol", "distance": 2, "vitesse": 1, "hauteur": 1.6} :
    près de l'épaule (le dessous du nuage à 1,6 bloc, comme la v2 portée), à 2 blocs (petite mascotte qui reste proche) ;
  - racine « mochi » à l'origine, dessous du nuage à y = 0, visage vers −Z ; aucun groupe du corps ; porté (menu Apparence,
    second familier : q.is_pet = 0) l'overlay le remet à droite du joueur à hauteur d'épaule, exactement comme la v2 ;
  - pet_idle (24 s, les 10 comportements de la v2 au hasard) ; pet_fly = les mêmes comportements + vol (penché, bras qui
    battent, traîne) × q.ground_speed du nuage : immobile en vol, il vit comme au repos ; pet_walk, pet_run, pet_fall (v2),
    pet_sit (posé comme un coussin, yeux mi-clos), pet_sleep (nuage plat qui respire), pet_swim (s'élève hors de l'eau) ;
  - overlay_mochi : humeurs météo de la v2 (gris et crachin sous la pluie ou quand la vie du MAÎTRE est basse :
    q.owner_health ; éclaircie arc-en-ciel quand la pluie cesse), virages, saccades du regard ; quand le maître vient tout
    près (q.owner_distance < 1,6), il lève le visage, sautille et fait coucou du bras ;
  - event_owner_hurt : l'ancien hurt (sursaut, puis petit orage boudeur : gris sombre, yeux plissés, mini-éclairs, crachin) ;
    event_teleport : « plop » de guimauve ; event_equip (un son), event_jump, event_land. Plus d'attack, hurt, glide,
    event_unequip (pas dans la table du familier).
  - particules goutte et cœur : modélisées et gardées (portées, elles marchent), mais pas encore lancées par le mod sur un
    familier vivant (guide 6.6) : le vérificateur le signale.

Familier nuage-mochi v2 : petit nuage dodu à visage kawaii, mascotte magique qui flotte à droite du joueur, à hauteur d'épaule.
Ensemble Kawaii (fiche .claude/styles/kawaii.md ; crème, rose guimauve, lavande). Design original.
Écrit familier_kawaii_mochi.png, familier_kawaii_mochi_e.png et .build/familier_kawaii_mochi_brut.bbmodel à côté de ce script.

Refonte du 2026-11-05 (règles .claude/styles/familiers.md, .claude/references/familiers/, slimes-mascottes.md) :
  - placement : type « slime, blob, nuage » / « mascotte magique » (types-familiers.md) : il FLOTTE, la cause se voit (c'est un
    nuage) ; à droite du joueur, un peu en arrière, hauteur d'épaule ; jamais de pattes qui marchent dans le vide ;
  - volume : chaque bosse est un polyèdre convexe circonscrit à un ellipsoïde (38 plans tangents répartis en spirale de
    Fibonacci : on lit une boule, pas une boîte chanfreinée) ; une facette = une peau de 0,3 px découpée par alpha à son
    polygone, autour d'une âme pleine ; les texels d'une bosse qui entrent dans une autre bosse fixe sont transparents
    (on ne voit que la surface de l'union : pas de facettes qui se croisent) ; ventre au visage aplati comme un daifuku ;
  - peinture en espace monde : normale lissée de l'ellipsoïde, dégradé vers le blanc en haut, ombres lavande froides, ombre
    de contact entre bosses ; joues roses, bouche fine, yeux bleu nuit à deux reflets ;
  - visage expressif : paupières (échelle y, plaque couleur de peau à cils), yeux de joie « ∩ ∩ », bouche ouverte, bouche
    triste, clignements irréguliers, regard qui saccade ; plaques d'expression rentrées dans le ventre au repos (position).

Vivant (familiers.md) : idle de 24 s, base (flottement, respiration, dérive) + 10 comportements tirés au hasard par tranches
de 6 s (q.life_time, q.instance_seed), environ un tiers de tranches calmes ; la nuit, les tranches calmes deviennent des siestes.
  6 petits bonds de joie (squash & stretch)        11 pirouette
  7 se gonfle de joie (cœurs)                      12 sieste en nuage plat (souvent la nuit)
  8 s'aplatit en crêpe puis rebondit               13 éternue (et fait tomber quelques gouttes)
  9 arc-en-ciel bref (content)                     14 curieux : penche la tête, s'avance
 10 regarde le joueur, clignement lent, s'approche 15 câlin : vient se frotter contre la tête du joueur
overlay_mochi : regarde là où le joueur regarde (avec retard), se penche dans les virages, saccades du regard ; vie basse
(< 35 %) : il s'assombrit, s'affaisse, se rapproche, bouche triste et petite pluie (particule goutte qui se dissipe, jamais
posée) ; sous la pluie il boit l'eau et gonfle un peu ; cœurs quand le joueur frappe. event_jump / event_land (q.land_speed) :
squash & stretch ; event_equip (2026-11-08) : il se condense d'une nappe de brume, « plop » de guimauve, coucou, bond de joie ;
event_teleport : la condensation en bref ; event_unequip : inspire puis rétrécit.
Arbitrage des 16 animations : pas de « mount » (le staff met « idle » pour la case Monture, comportements compris).

Humeurs météo (retour du 2026-11-05 : « l'arc-en-ciel est blanc, pas en couleur » ; idée d'états météo) :
  - content : arc-en-ciel en couleurs franches (ARC_COLS saturés, alpha 228, _e à 30 %), au comportement 9 et en éclaircie
    quand la pluie cesse (trans_arc2, overlay, variable mémorisée v.ra : quelques secondes) ;
  - triste (vie < 35 %) ou sous la pluie : nuage gris bleuté (ctrl_teinte), crachin de gouttes (ctrl_emit), paupières tombantes ;
  - vexé (hurt, 3 s) : après le sursaut, il boude en se gonflant, devient petit nuage d'orage (ctrl_teinte sombre), yeux
    plissés inclinés, bouche boudeuse, crachin et 3 mini-éclairs (camy_eclair, opaques + _e, codes de l'Orage : zigzag, cœur
    blanc, halo bleu, bord violet ; flash de 0,1 s, deux formes alternées). Arc d'éclaircie et éclair : ctrl_alpha −1 dans
    chaque état, +1 dans hurt (ou +v.ar dans l'overlay).
Fonctions avancées : camy_ (éclair), trans_ (arc-en-ciel, gouttes), ctrl_alpha (fondu de l'arc), ctrl_emit (gouttes, cœurs), ctrl_teinte (gris
de tristesse, pluie), overlay_, event_*, particules modélisées (goutte, coeur), calque _e (reflets des yeux, cœurs).
À juger en jeu : variables mémorisées (lissages), ctrl_teinte, ctrl_emit, signe de q.head_y_rotation.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

AVEC_E = True
NOM = "familier_kawaii_mochi"
TEX = 512
TAU = 2 * math.pi
SS = 3

# ------------------------------------------------------------------ palette (kawaii.md)
CREME = (255, 249, 247)
BLANC = (255, 255, 255)
LAV = (214, 202, 232)            # ombre froide
LAV_D = (176, 158, 214)
ROSE = (255, 190, 212)
ROSE_L = (255, 222, 234)
ROSE_D = (234, 140, 178)
NUIT_H = (30, 28, 70)            # bleu nuit des yeux (jamais de noir pur)
NUIT_B = (86, 92, 170)
TRAIT = (78, 56, 110)            # bouche, cils
LANGUE = (255, 150, 180)


def lerp(a, b, k):
    return a + (b - a) * k


def col(c):
    return np.array(c, np.float32)


def mix(base, c, k):
    return lerp(base, col(c), np.clip(k, 0, 1)[..., None])


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def V(*a):
    return np.array(a, float)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


# ------------------------------------------------------------------ bosses : polyèdres circonscrits à des ellipsoïdes
def fib(n):
    ga = math.pi * (3 - math.sqrt(5))
    out = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - y * y)
        out.append(V(r * math.cos(ga * i), y, r * math.sin(ga * i)))
    return out


# nom, groupe, centre, rayons, plans en plus (normale, distance au centre), nombre de plans
FZ_K = 0.84
BOSSES = [
    ("ventre", "corps", V(0.0, -0.35, 0.0), V(3.0, 2.05, 2.45), [(V(0, 0, -1), FZ_K * 2.45), (V(0, -1, 0), 0.84 * 2.05)], 72),
    ("haut", "corps", V(0.1, 1.3, 0.35), V(2.15, 1.75, 1.95), [], 72),
    ("haut_g", "corps", V(-2.05, 0.45, 0.45), V(1.25, 1.1, 1.45), [], 48),
    ("haut_d", "corps", V(2.15, 0.4, 0.5), V(1.2, 1.05, 1.4), [], 48),
    ("bras_l", "bras_l", V(-3.05, -0.95, -0.2), V(1.05, 0.9, 1.1), [], 40),
    ("bras_r", "bras_r", V(3.05, -0.95, -0.2), V(1.05, 0.9, 1.1), [], 40),
]
FZ = -FZ_K * 2.45                  # plan du visage (repère du familier)
YB0 = -0.35 - 0.84 * 2.05            # dessous du nuage
YB1 = 3.05
EYE_Y, EYE_DX = -0.1, 0.9
EYE_W, EYE_H = 1.0, 1.2
MOUTH_Y = -0.66
CHEEK_X, CHEEK_Y = 1.45, -0.72


def planes_of(b):
    _, _, c, R, extra, n = b
    pl = [(u, float(np.linalg.norm(R * u))) for u in fib(n)]
    return pl + [(unit(u), d) for u, d in extra]


def clip(poly, n, d):
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        da, db = a @ n - d, b @ n - d
        if da <= 0:
            out.append(a)
        if da * db < 0:
            out.append(a + (b - a) * (da / (da - db)))
    return out


def facettes(b):
    pl = planes_of(b)
    out = []
    for i, (n, d) in enumerate(pl):
        a = unit(np.cross(n, V(0, 1, 0) if abs(n[1]) < 0.9 else V(1, 0, 0)))
        bb = np.cross(n, a)
        o = n * d
        poly = [o + 20 * (sa * a + sb * bb) for sa, sb in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        for j, (m, e) in enumerate(pl):
            if j != i and poly:
                poly = clip(poly, m, e)
        if len(poly) < 3:
            continue
        q = [poly[0]]
        for p in poly[1:]:
            if np.linalg.norm(p - q[-1]) > 1e-4:
                q.append(p)
        if np.linalg.norm(q[0] - q[-1]) < 1e-4:
            q.pop()
        if len(q) < 3:
            continue
        area = 0.5 * np.linalg.norm(sum(np.cross(q[k], q[(k + 1) % len(q)]) for k in range(len(q))))
        if area < 0.015:
            continue
        out.append((n, q))
    return out


PLANES = {b[0]: (b[2], planes_of(b)) for b in BOSSES}


def dedans(P, nom, marge):
    """P (..., 3) repère du familier : dans le polyèdre `nom`, à plus de `marge` des faces ?"""
    c, pl = PLANES[nom]
    q = P - c
    m = np.max(np.stack([q @ n - d for n, d in pl]), axis=0)
    return m < -marge


FIXES = [b[0] for b in BOSSES if b[1] == "corps"]


# ------------------------------------------------------------------ peinture
def normale_lisse(P, b):
    """Normale de l'ellipsoïde de la bouffée au point P (et non celle de la facette) : la peinture efface les facettes."""
    _, _, c, R, _, _ = b
    q = (P - c) / (R * R)
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


L_MC = (unit(V(0.2, 1.0, -0.7)), unit(V(-0.2, 1.0, 0.7)))      # éclairage des entités de Minecraft : 2 lumières, ambiant 0,4
W_MC = float(os.environ.get("W_MC", "0"))     # part du modèle d’éclairage vanilla (2 lumières) dans la compensation ; 0 = renderer et Vestiaire
L_RB = unit(V(-0.4, 1.0, 0.6))                                   # renderer du dépôt


def eclairage(n):
    mc = np.clip(0.4 + 0.6 * (np.clip(n @ L_MC[0], 0, None) + np.clip(n @ L_MC[1], 0, None)), 0, 1)
    rb = 0.55 + 0.45 * np.abs(n @ L_RB)
    return W_MC * mc + (1 - W_MC) * rb


def lum_boule(P, b):
    n = normale_lisse(P, b)
    L = unit(V(-0.35, 1.0, -0.55))
    return np.clip(0.5 + 0.5 * (n @ L), 0, 1)


def ombre_contact(P, b):
    o = np.zeros(P.shape[:-1])
    for bb in BOSSES:
        if bb is b or bb[1] != "corps":
            continue
        _, _, c, R, _, _ = bb
        q = np.linalg.norm((P - c) / R, axis=-1)
        o = np.maximum(o, np.clip((1.25 - q) / 0.29, 0, 1) ** 1.5 * (q > 0.96))
    return o


NUAGE = (232, 232, 240)            # laisse de la marge à la compensation (jusqu’à ×1,1 sans saturer)
NUAGE_O = (206, 200, 228)          # ombre lavande douce


def peau(P, b, nf=None):
    """Nuage : blanc lumineux, ombres lavande douces vers le bas, bord plus clair ; teinte d'après la normale lisse de la
    bouffée. nf : normale de la facette ; la couleur est divisée par l'éclairage par face du jeu (approché) et multipliée par
    celui de la normale lisse : les facettes disparaissent au rendu."""
    n = normale_lisse(P, b)
    lum = lum_boule(P, b)
    hgt = np.clip((P[..., 1] - YB0) / (YB1 - YB0), 0, 1)
    k = np.clip(0.55 * lum + 0.45 * hgt, 0, 1)
    c = lerp(col(NUAGE_O), col(NUAGE), (k ** 0.8)[..., None])
    rim = np.clip(1 - np.abs(n[..., 2]) * 1.15, 0, 1) ** 2 * (n[..., 1] > -0.4)
    c = mix(c, (246, 246, 252), rim * 0.7)
    c = mix(c, NUAGE_O, ombre_contact(P, b) * 0.45)
    if nf is not None:
        comp = np.clip(eclairage(n) / eclairage(np.broadcast_to(nf, n.shape)), 0.7, 1.45)
        c = np.clip(c * comp[..., None], 0, 255)
    return c


VENTRE = BOSSES[0]


def visage(X, Y, c):
    """Joues, bouche neutre ; X, Y : repère du familier (vue de face)."""
    for s in (-1, 1):
        cx, cy = s * CHEEK_X, CHEEK_Y
        q = np.hypot((X - cx) / 0.42, (Y - cy) / 0.27)
        c = mix(c, ROSE, np.clip((1.0 - q) / 0.18, 0, 1))
        c = mix(c, ROSE_L, (np.hypot((X - cx + 0.12 * s) / 0.13, (Y - cy - 0.08) / 0.07) < 1) * 0.9)
        for kk in (-1, 1):
            x0 = cx + kk * 0.13
            seg = (np.abs((X - x0) + (Y - cy) * 0.45 * s) < 0.045) & (np.abs(Y - cy) < 0.11)
            c = mix(c, ROSE_D, seg * 1.0)
    u = X / 0.24
    arc = (np.abs(u) < 1) & (np.abs((Y - MOUTH_Y) - (-0.1 * (1 - u * u))) < 0.05)
    c = mix(c, TRAIT, arc * 1.0)
    return c


def finir(c, inside, em, W, H_, semi=None):
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H_), Image.LANCZOS))
    if semi is None:
        al = (np.array(Image.fromarray((inside * 255).astype(np.uint8), "L").resize((W, H_), Image.LANCZOS)) > 110) * 255
    else:
        al = np.array(Image.fromarray(np.clip(semi, 0, 254).astype(np.uint8), "L").resize((W, H_), Image.LANCZOS)).astype(int)
        al = np.where(al < 12, 0, al)
    out = np.dstack([rgb, al]).astype(np.uint8)
    if (al > 0).any():
        out[al == 0, :3] = rgb[al > 0].mean(axis=0).astype(np.uint8)
    oe = np.zeros((H_, W, 4), np.uint8)
    if em is not None:
        er = np.array(Image.fromarray(np.clip(em, 0, 255).astype(np.uint8), "RGB").resize((W, H_), Image.LANCZOS))
        on = (al > 0) & (er.max(axis=2) > 20)
        oe[on, :3] = er[on]
        oe[on, 3] = 255
    return out, oe


def grille(W, H_, w, h):
    yy, xx = np.mgrid[0:H_ * SS, 0:W * SS]
    return (xx + 0.5) / (W * SS) * w - w / 2, h / 2 - (yy + 0.5) / (H_ * SS) * h


def sd_poly(pts2):
    edges = []
    for i in range(len(pts2)):
        a, b = pts2[i], pts2[(i + 1) % len(pts2)]
        t = unit(b - a)
        edges.append((a, np.array([t[1], -t[0]])))

    def f(X, Y):
        return np.max([(X - a[0]) * nn[0] + (Y - a[1]) * nn[1] for a, nn in edges], axis=0)
    return f


TUILES = {}         # nom -> dict(w, h, painter(W, H), fixe (W, H) ou None)
PLATES = []         # (groupe, nom, centre de la plaque, X, Y, n)
DEBORD = 0.015


def peintre_facette(sp):
    def f(W, H_):
        X, Y = grille(W, H_, sp["w"], sp["h"])
        inside = sp["sd"](X, Y) < DEBORD
        P = sp["o"] + X[..., None] * sp["X"] + Y[..., None] * sp["Y"]
        for other in sp["coupe"]:
            inside &= ~dedans(P, other, 0.02)
        c = peau(P, sp["b"], sp["n"])
        if sp["b"] is VENTRE:
            c = np.where((P[..., 2] < -1.2)[..., None], visage(P[..., 0], P[..., 1], c), c)
        return finir(c, inside, None, W, H_)
    return f


for b in BOSSES:
    nom, g, c, R, _, _ = b
    coupe = [o for o in FIXES if o != nom] if g == "corps" else []
    for k, (n, poly) in enumerate(facettes(b)):
        P = [p + c for p in poly]
        if coupe and any(all(dedans(p[None], o, 0.05)[0] for p in P) for o in coupe):
            continue                    # facette entièrement dans une autre bosse : omise
        ctr = np.mean(P, axis=0)
        Xa = unit(P[1] - P[0])
        Ya = np.cross(n, Xa)
        p2 = [np.array([(p - ctr) @ Xa, (p - ctr) @ Ya]) for p in P]
        lo, hi = np.min(p2, axis=0) - DEBORD - 0.02, np.max(p2, axis=0) + DEBORD + 0.02
        mid = (lo + hi) / 2
        o = ctr + Xa * mid[0] + Ya * mid[1]
        f = sd_poly([q - mid for q in p2])
        tn = f"{nom}_{k}"
        sp = dict(w=hi[0] - lo[0], h=hi[1] - lo[1], sd=f, o=o, X=Xa, Y=Ya, b=b, coupe=coupe, n=n)
        TUILES[tn] = dict(w=sp["w"], h=sp["h"], painter=peintre_facette(sp), fixe=None)
        PLATES.append((g, tn, o - n * 0.15, Xa, Ya, n))


def peint_oeil(W, H_):
    X, Y = grille(W, H_, EYE_W, EYE_H)
    q = np.hypot(X / (EYE_W / 2), Y / (EYE_H / 2))
    t = np.clip((EYE_H / 2 - Y) / EYE_H, 0, 1)
    c = lerp(col(NUIT_H), col(NUIT_B), (t ** 1.7)[..., None])
    c = mix(c, (130, 150, 220), np.clip((q - 0.55) / 0.3, 0, 1) * (Y < -0.1) * 0.5)      # iris plus clair en bas
    c = mix(c, (20, 18, 50), np.clip((q - 0.86) / 0.14, 0, 1))                             # cerne
    r1 = np.hypot((X - 0.15) / 0.21, (Y - 0.24) / 0.23) < 1
    r2 = np.hypot((X + 0.19) / 0.095, (Y + 0.27) / 0.095) < 1
    c = mix(c, BLANC, (r1 | r2) * 1.0)
    em = np.zeros(c.shape, np.float32)
    em[r1] = (210, 210, 235)
    em[r2] = (150, 150, 190)
    return finir(c, q < 1, em, W, H_)


def couleur_face(X, Y):
    P = np.stack([X, Y, np.full(X.shape, FZ)], axis=-1)
    return visage(X, Y, peau(P, VENTRE, V(0, 0, -1)))


def peint_paupiere(cx):
    def f(W, H_):
        X, Y = grille(W, H_, EYE_W, EYE_H)
        q = np.hypot(X / (EYE_W / 2), Y / (EYE_H / 2))
        c = couleur_face(X + cx, Y + EYE_Y)
        cils = (q > 0.8) & (Y < 0.2 * EYE_H)
        c = mix(c, TRAIT, cils * 1.0)
        return finir(c, q < 1, None, W, H_)
    return f


JW, JH = 1.0, 0.7


def peint_joie(W, H_):
    X, Y = grille(W, H_, JW, JH)
    u = X / 0.4
    yc = -0.22 + 0.42 * np.sqrt(np.clip(1 - u * u, 0, 1))
    arc = (np.abs(u) < 1.02) & (np.abs(Y - yc) < 0.07)
    c = np.zeros(X.shape + (3,), np.float32)
    c[...] = NUIT_H
    return finir(c, arc, None, W, H_)


MW, MH = 0.95, 0.62


def peint_bouche(kind):
    def f(W, H_):
        X, Y = grille(W, H_, MW, MH)
        fond = np.hypot(X / (MW / 2), Y / (MH / 2)) < 1
        c = couleur_face(X, Y + MOUTH_Y)
        if kind == "o":
            # bouche ouverte en D : bord haut plat, langue rose
            m = (np.hypot(X / 0.28, (Y - 0.06) / 0.26) < 1) & (Y < 0.07)
            c = mix(c, TRAIT, m * 1.0)
            c = mix(c, LANGUE, (m & (np.hypot(X / 0.17, (Y + 0.12) / 0.09) < 1)) * 1.0)
        else:
            u = X / 0.22
            arc = (np.abs(u) < 1) & (np.abs((Y + 0.02) - 0.09 * (1 - u * u)) < 0.045)
            c = mix(c, TRAIT, arc * 1.0)
        return finir(c, fond, None, W, H_)
    return f


AW, AH, AR0, AR1 = 9.6, 4.9, 3.0, 4.6
# Retour en jeu du 2026-11-05 : « l'arc-en-ciel est blanc, pas en couleur ». Les pastels (186–255) en trans_, plus un _e à 55 %
# de la couleur et un liseré blanc par bande, se lisaient blancs. Couleurs franches et saturées, alpha plus fort, _e faible.
ARC_COLS = [(232, 58, 92), (255, 140, 40), (255, 212, 40), (70, 196, 96), (50, 140, 236), (140, 84, 220)]


def peint_arc(W, H_):
    X, Y = grille(W, H_, AW, AH)
    Y = Y + AH / 2
    r = np.hypot(X, Y)
    k = np.clip((r - AR0) / (AR1 - AR0), 0, 0.9999)
    band = (k * len(ARC_COLS)).astype(int)
    c = col(ARC_COLS)[band]
    c = c * (1 - 0.12 * ((k * 6) % 1)[..., None])           # léger dégradé dans chaque bande (pas de liseré blanc)
    inside = (r > AR0) & (r < AR1) & (Y > 0)
    edge = np.clip(np.minimum(r - AR0, AR1 - r) / 0.25, 0, 1)
    a = 228 * edge * np.clip(Y / 0.9, 0, 1) * inside
    em = c * 0.3
    return finir(c, inside, em, W, H_, semi=a)


def peint_goutte(W, H_):
    X, Y = grille(W, H_, 1.0, 1.4)
    q = np.hypot(X / 0.42, (Y + 0.22) / 0.42)
    tip = (Y > -0.22) & (np.abs(X) < 0.42 * (1 - (Y + 0.22) / 0.9))
    inside = (q < 1) | tip
    c = lerp(col((196, 220, 255)), col((150, 170, 236)), np.clip((0.4 - Y) / 1.0, 0, 1)[..., None])
    c = mix(c, BLANC, (np.hypot((X + 0.14) / 0.1, (Y + 0.12) / 0.16) < 1) * 1.0)
    return finir(c, inside, None, W, H_, semi=inside * 205)


def peint_coeur(W, H_):
    X, Y = grille(W, H_, 1.0, 0.9)
    x, y = X / 0.48, (Y + 0.02) / 0.44
    inside = (x * x + y * y - 1) ** 3 - x * x * y ** 3 < 0
    c = lerp(col(ROSE_L), col(ROSE_D), np.clip((0.4 - Y) / 0.9, 0, 1)[..., None])
    hl = np.hypot((X + 0.18) / 0.1, (Y - 0.14) / 0.07) < 1
    c = mix(c, BLANC, hl * 1.0)
    em = np.zeros(c.shape, np.float32)
    em[inside] = (160, 70, 110)
    return finir(c, inside, em, W, H_)


EW, EH = 1.3, 2.5
ECLAIRS = {
    "eclair_a": [(-0.12, 1.25), (0.5, 1.25), (0.12, 0.3), (0.52, 0.3), (-0.22, -1.25), (-0.02, -0.12), (-0.46, -0.12)],
    "eclair_b": [(0.12, 1.25), (-0.5, 1.25), (-0.16, 0.42), (-0.54, 0.42), (0.24, -1.25), (0.06, -0.02), (0.44, -0.02)],
}


def peint_eclair(pts):
    def f(W, H_):
        from PIL import ImageDraw, ImageFilter
        Wp, Hp = W * SS, H_ * SS
        m = Image.new("L", (Wp, Hp), 0)
        ImageDraw.Draw(m).polygon([((x / EW + 0.5) * Wp, (0.5 - y / EH) * Hp) for x, y in pts], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(Wp * 0.035))        # coins adoucis (kawaii : pas d'angle vif)
        inside = np.array(m) > 128
        core = np.array(m.filter(ImageFilter.MinFilter(2 * int(Wp * 0.07) + 1))) > 150
        mid = np.array(m.filter(ImageFilter.MinFilter(2 * int(Wp * 0.035) + 1))) > 140
        c = np.zeros((Hp, Wp, 3), np.float32)
        c[...] = (120, 80, 255)                    # bord violet
        c[mid] = (150, 210, 255)                   # halo bleu
        c[core] = (255, 255, 245)                  # cœur blanc
        em = np.zeros_like(c)
        em[inside] = (90, 60, 200)
        em[mid] = (110, 160, 220)
        em[core] = (225, 225, 215)
        return finir(c, inside, em, W, H_)
    return f


def peint_ame(W, H_):
    c = np.zeros((H_ * SS, W * SS, 3), np.float32)
    c[...] = LAV
    return finir(c, np.ones(c.shape[:2], bool), None, W, H_)


TUILES["oeil"] = dict(w=EYE_W, h=EYE_H, painter=peint_oeil, fixe=None)
for s, tag in ((-1, "l"), (1, "r")):
    TUILES[f"paup_{tag}"] = dict(w=EYE_W, h=EYE_H, painter=peint_paupiere(s * EYE_DX), fixe=None)
TUILES["joie"] = dict(w=JW, h=JH, painter=peint_joie, fixe=None)
TUILES["bouche_o"] = dict(w=MW, h=MH, painter=peint_bouche("o"), fixe=None)
TUILES["bouche_t"] = dict(w=MW, h=MH, painter=peint_bouche("t"), fixe=None)
TUILES["arc"] = dict(w=AW, h=AH, painter=peint_arc, fixe=(196, 100))
TUILES["goutte"] = dict(w=1, h=1, painter=peint_goutte, fixe=(14, 20))
TUILES["coeur"] = dict(w=1, h=1, painter=peint_coeur, fixe=(20, 18))
TUILES["ame"] = dict(w=1, h=1, painter=peint_ame, fixe=(8, 8))
for n, pts in ECLAIRS.items():
    TUILES[n] = dict(w=EW, h=EH, painter=peint_eclair(pts), fixe=(36, 70))

UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
SEMI = ("arc", "goutte")


def atlas():
    def pack(dens):
        items = []
        for n, t in TUILES.items():
            w, h = t["fixe"] if t["fixe"] else (int(math.ceil(t["w"] * dens)), int(math.ceil(t["h"] * dens)))
            items.append((n, w, h))
        items.sort(key=lambda it: -it[2])
        uv, x, y, shelf = {}, 0, 0, 0
        for n, w, h in items:
            if x + w + 1 > TEX:
                x, y, shelf = 0, y + shelf + 1, 0
            if y + h > TEX - 6 or w > TEX:
                return None
            uv[n] = (x, y, x + w, y + h)
            x += w + 1
            shelf = max(shelf, h)
        return uv

    dens = 48.0
    while (uv := pack(dens)) is None:
        dens -= 0.25
    UV.update(uv)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, t in TUILES.items():
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1], tex_e[v0:v1, u0:u1] = t["painter"](u1 - u0, v1 - v0)
    assert tex[TEX - 3, TEX - 3, 3] == 0
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    ok = np.zeros(semi.shape, bool)
    for n in SEMI:
        u0, v0, u1, v1 = UV[n]
        ok[v0:v1, u0:u1] = True
    assert not (semi & ~ok).any(), "semi-transparence hors trans_"
    b64 = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        bb = io.BytesIO()
        im.save(bb, "PNG", optimize=True)
        b64.append("data:image/png;base64," + base64.b64encode(bb.getvalue()).decode())
    return dens, b64


# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


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
    assert np.allclose(rot_matrix(*ang), R, atol=1e-4), "euler"
    return ang


def group(name, origin, parent=None, nm=None):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "name": nm or name}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    if g is not None:
        groups[g]["ids"].append(e["uuid"])
    return e


def plate(g, name, c, X, Y, out, tile, th=0.3, both=False):
    X, Y = unit(X), unit(Y)
    w, h = TUILES[tile]["w"], TUILES[tile]["h"]
    u0, v0, u1, v1 = UV[tile]
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    south, north = [u0, v0, u1, v1], [u1, v0, u0, v1]
    if not both:
        if R_[:, 2] @ out > 0:
            north = CLEAR
        else:
            south = CLEAR
    c = np.asarray(c, float)
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": south, "north": north, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def ame_box(b):
    nom, g, c, R, _, _ = b
    lo, hi = 0.05, 0.6
    for _ in range(30):
        s = (lo + hi) / 2
        pts = np.array([c + np.array(sg) * s * R for sg in np.ndindex(2, 2, 2)]) if False else \
            np.array([c + np.array([sx, sy, sz]) * s * R for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
        if dedans(pts, nom, 0.36).all():
            lo = s
        else:
            hi = s
    h = lo * R
    if nom == "ventre":
        h = h.copy()
        h[2] = min(h[2], 0.95)           # place pour les plaques d'expression rentrées (z > −1,26)
    else:
        h = h * 0.88                     # âmes des bouffées en retrait : aucune face parallèle à celle du ventre
    return c, h


def bone_node(name):
    g = groups[name]
    return {"name": g["name"], "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


C0_V2 = V(12.5, 27.6, 3.0)               # v2 portée : à droite du joueur, à hauteur d'épaule
C0 = V(0.0, -YB0, 0.0)                   # familier vivant (guide 6.6) : dessous du nuage à l'origine, visage vers −Z
PORTE = C0_V2 - C0                       # décalage quand il est porté (q.is_pet = 0)


def L(*p):
    return C0 + V(*p)


EX, EY, EZ = V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)
SQP = L(0, YB0, 0)
HIDE = 0.75                       # recul des plaques d'expression au repos (rentrées dans le ventre)

group("mochi", V(0, 0, 0))               # racine du familier vivant (pas de groupe du corps)
group("fam_elan", SQP, "mochi")
group("fam_reac", C0, "fam_elan")
group("fam_pos", C0, "fam_reac")
group("fam_regard", C0, "fam_pos")
group("fam_comp", C0, "fam_regard")
group("fam_comp2", C0, "fam_comp")
group("fam_snap", SQP, "fam_comp2")
group("fam_squash", SQP, "fam_snap")
group("fam_joie", SQP, "fam_squash")
group("fam_joie2", SQP, "fam_joie")
group("ctrl_teinte#c", C0, "fam_joie2", nm="ctrl_teinte")
group("corps", C0, "fam_joie2")
ARMS = {}
for tag, s in (("l", -1), ("r", 1)):
    b = next(bb for bb in BOSSES if bb[0] == f"bras_{tag}")
    ARMS[tag] = group(f"bras_{tag}", C0 + b[2] - V(s * 0.6 * b[3][0], -0.1, 0), "fam_joie2")
EYES, LIDS = {}, {}
for s, tag in ((-1, "l"), (1, "r")):
    ec = L(s * EYE_DX, EYE_Y, FZ - 0.1 + 0.15)
    EYES[tag] = group(f"oeil_{tag}", ec, "fam_joie2")
    LIDS[tag] = group(f"paup_{tag}", L(s * EYE_DX, EYE_Y + EYE_H / 2, FZ - 0.2 + 0.15), EYES[tag])
group("yeux_joie", L(0, EYE_Y, FZ), "fam_joie2")
group("bouche_o", L(0, MOUTH_Y, FZ), "fam_joie2")
group("bouche_t", L(0, MOUTH_Y, FZ), "fam_joie2")
group("trans_arc", L(0, -0.2, 3.15), "fam_squash")
group("ctrl_alpha#arc", L(0, -0.2, 3.15), "trans_arc", nm="ctrl_alpha")
group("trans_arc2", L(0, -0.2, 3.6), "fam_squash")          # éclaircie après la pluie (overlay, variable mémorisée)
group("ctrl_alpha#arc2", L(0, -0.2, 3.6), "trans_arc2", nm="ctrl_alpha")
ECL_TOP = L(0.3, YB0 + 0.15, -0.5)                              # l'éclair naît du dessous du nuage
group("camy_eclair", ECL_TOP, "fam_squash")
group("eclair", ECL_TOP, "camy_eclair")
group("ctrl_alpha#ecl", ECL_TOP, "eclair", nm="ctrl_alpha")
group("eclair_a", ECL_TOP, "eclair")
group("eclair_b", ECL_TOP + V(0.15, 0, 0), "eclair")
for i, x in enumerate((-1.3, 0.2, 1.4)):
    gn = group(f"emit_goutte{i + 1 if i else ''}", L(x, YB0 - 0.15, 0.2 - 0.3 * i), "fam_joie2")
    group(f"ctrl_emit#g{i}", L(x, YB0 - 0.15, 0.2 - 0.3 * i), gn, nm="ctrl_emit")
group("emit_coeur", L(0.4, YB1 + 0.25, 0.2), "fam_joie2")
group("ctrl_emit#c", L(0.4, YB1 + 0.25, 0.2), "emit_coeur", nm="ctrl_emit")

DENS, (tex_b64, tex_e_b64) = atlas()
for b in BOSSES:
    c, h = ame_box(b)
    u0, v0, u1, v1 = UV["ame"]
    cube(b[1], f"ame_{b[0]}", C0 + c - h, C0 + c + h, C0 + c, (0, 0, 0), {k: ([u0, v0, u1, v1] if k not in ("up", "down") else CLEAR) for k in ("north", "south", "east", "west", "up", "down")})
for g, tn, o, Xa, Ya, n in PLATES:
    plate(g, tn, C0 + o, Xa, Ya, n, tn)
for s, tag in ((-1, "l"), (1, "r")):
    plate(EYES[tag], f"oeil_{tag}", L(s * EYE_DX, EYE_Y, FZ - 0.1 + 0.15), EX, EY, -EZ, "oeil")
    plate(LIDS[tag], f"paup_{tag}", L(s * EYE_DX, EYE_Y, FZ - 0.2 + 0.15), EX, EY, -EZ, f"paup_{tag}")
    plate("yeux_joie", f"joie_{tag}", L(s * EYE_DX, EYE_Y + 0.05, FZ - 0.3 + 0.15 + HIDE), EX, EY, -EZ, "joie")
plate("bouche_o", "bouche_o", L(0, MOUTH_Y, FZ - 0.1 + 0.15 + HIDE), EX, EY, -EZ, "bouche_o")
plate("bouche_t", "bouche_t", L(0, MOUTH_Y, FZ - 0.2 + 0.15 + HIDE + 0.3), EX, EY, -EZ, "bouche_t")
plate("trans_arc", "arc", L(0, -0.2 + AH / 2, 3.15), EX, EY, EZ, "arc", both=True)
plate("trans_arc2", "arc2", L(0, -0.2 + AH / 2, 3.6), EX, EY, EZ, "arc", both=True)
plate("eclair_a", "eclair_a", ECL_TOP + V(0, -EH / 2, 0), EX, EY, EZ, "eclair_a")
plate("eclair_b", "eclair_b", ECL_TOP + V(0.15, -EH / 2, 0.4), EX, EY, EZ, "eclair_b")

outliner = []


def particule(nom, w, d, tile, trans):
    u0, v0, u1, v1 = UV[tile]
    root = {"name": f"particle_{nom}", "origin": [0, 0, 0], "uuid": nuid(), "rotation": [0, 0, 0], "children": []}
    holder = root
    if trans:
        sub = {"name": f"trans_particule_{nom}", "origin": [0, 0, 0], "uuid": nuid(), "rotation": [0, 0, 0], "children": []}
        root["children"].append(sub)
        holder = sub
    e = cube(None, nom, (-w / 2, 0.3, -d / 2), (w / 2, 0.6, d / 2), (0, 0.45, 0), (0, 0, 0), {"up": [u0, v0, u1, v1]})
    holder["children"].append(e["uuid"])
    outliner.append(root)


particule("goutte", 0.5, 0.7, "goutte", True)
particule("coeur", 0.7, 0.63, "coeur", False)


# ------------------------------------------------------------------ animations
# Guide, section 3 : rotation +X = le haut part vers l'arrière ; +Y = le côté droit (+X) avance (le visage, vers −Z, se tourne
# vers le joueur, à −X) ; +Z = le côté droit monte. Position +Y monte, +X vers la droite du joueur.
def fmt(v):
    if isinstance(v, str):
        return v
    return str(round(float(v) + 0.0, 4))


def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": fmt(v[0]), "y": fmt(v[1]), "z": fmt(v[2])}], "time": round(t, 3), "interpolation": "linear"}


def anim(name, length, tracks=None, n_kf=None, loop="loop", molang=None):
    A = {}
    if tracks:
        n = n_kf or max(6, int(round(length * 10)))
        times = [i * length / n for i in range(n + 1)]
        for g, chans in tracks.items():
            A.setdefault(groups[g]["uuid"], {"name": groups[g]["name"], "type": "bone", "keyframes": []})["keyframes"] += \
                [kf(ch, t, f(t)) for ch, f in chans.items() for t in times]
    for g, chans in (molang or {}).items():
        A.setdefault(groups[g]["uuid"], {"name": groups[g]["name"], "type": "bone", "keyframes": []})["keyframes"] += \
            [kf(ch, 0.0, v) for ch, v in chans.items()]
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "pet_idle", "animators": A}


def mirror(f):
    return lambda t: (lambda v: (v[0], -v[1], -v[2]))(f(t))


def squash(k):
    """k > 0 : écrasé ; k < 0 : étiré ; volume à peu près constant."""
    return (1 + 0.5 * k, 1 - k, 1 + 0.5 * k)


def clin(t, *ts, dur=0.24):
    v = 1.0
    for a in ts:
        v -= 0.95 * bump(t, a, a + dur * 0.35, a + dur * 0.5, a + dur)
    return v


ZERO3 = (0, 0, 0)


def etat(name, T_, pos, regard, sq, oeil, paup, bras, n_kf=None, extra=None):
    tr = {"fam_pos": {"position": pos}, "fam_regard": {"rotation": regard}, "fam_squash": {"scale": lambda t: squash(sq(t))},
          "trans_arc": {"scale": lambda t: (0.001, 0.001, 0.001)},
          "ctrl_alpha#arc2": {"position": lambda t: (-1, 0, 0)}, "ctrl_alpha#ecl": {"position": lambda t: (-1, 0, 0)}}
    for tag in ("l", "r"):
        tr[EYES[tag]] = {"scale": (lambda t: (1, oeil(t), 1))}
        tr[LIDS[tag]] = {"scale": (lambda t: (1, paup(t), 1))}
    tr[ARMS["r"]] = {"rotation": bras}
    tr[ARMS["l"]] = {"rotation": mirror(bras)}
    tr.update(extra or {})
    return anim(name, T_, tr, n_kf=n_kf)


# walk (1,6 s) : sautille à chaque pas, un peu en retrait, bras qui se balancent
TW = 1.6


def walk_sq(t):
    k = math.cos(TAU * 2 * t / TW)
    return 0.09 * k ** 7 if k > 0 else -0.04 * (1 - k * k)


walk = etat("pet_walk", TW,
            lambda t: (0.1 * math.sin(TAU * t / TW), -0.2 + 0.75 * abs(math.sin(TAU * t / TW)), 0.8),
            lambda t: (-4 + 2 * math.sin(TAU * 2 * t / TW), 4, 4 * math.sin(TAU * t / TW)),
            walk_sq, lambda t: clin(t, 0.9), lambda t: 0.0,
            lambda t: (0, -10 * math.sin(TAU * t / TW), 14 + 10 * math.sin(TAU * t / TW)), n_kf=24)

# run (1 s) : traîne derrière, étiré par le vent, penché, bras rabattus vers l'arrière, yeux plissés
TR = 1.0
run = etat("pet_run", TR,
           lambda t: (0.3, -0.4 + 0.55 * abs(math.sin(TAU * t / TR)), 2.8),
           lambda t: (-12 + 2.5 * math.sin(TAU * 2 * t / TR), 6, 3 * math.sin(TAU * t / TR)),
           lambda t: -0.06 + 0.04 * math.cos(TAU * 2 * t / TR),
           lambda t: 1.0, lambda t: 0.3,
           lambda t: (0, -38, 22 + 9 * math.sin(TAU * 2 * t / TR)), n_kf=20)

# pet_sit (3 s) : le maître s'accroupit à côté, ou rien ne bouge depuis 20 s : il se pose comme un coussin (descend un peu,
# s'aplatit), yeux mi-clos, bras rentrés. Repris du sneak de la v2, sans le décalage vers le joueur (il n'est plus contre lui).
TS = 3.0
sit = etat("pet_sit", TS,
           lambda t: (0, -1.2 + 0.18 * math.sin(TAU * t / TS), 0),
           lambda t: (-3 + 1.5 * math.sin(TAU * t / TS), 0, 2 * math.sin(TAU * t / TS + 1)),
           lambda t: 0.16 + 0.025 * math.sin(TAU * t / TS),
           lambda t: clin(t, 1.9), lambda t: 0.4,
           lambda t: (0, 8, -28 + 3 * math.sin(TAU * t / TS)), n_kf=24)

# pet_swim (2,4 s) : dans l'eau, le nuage s'en extrait : il monte, s'étire, plisse les yeux, bras levés qui s'ébrouent
TN = 2.4
swim = etat("pet_swim", TN,
            lambda t: (0, 1.4 + 0.3 * math.sin(TAU * t / TN), 0),
            lambda t: (-4 + 2 * math.sin(TAU * t / TN), 0, 4 * math.sin(TAU * 2 * t / TN)),
            lambda t: -0.08 + 0.03 * math.sin(TAU * 2 * t / TN),
            lambda t: 1.0, lambda t: 0.45,
            lambda t: (0, 0, 40 + 14 * math.sin(TAU * 3 * t / TN)), n_kf=24)

# pet_fall (1,2 s) : il tombe (il flotte quand même), étiré, yeux grands ouverts, bras levés qui gigotent (v2)
TA = 1.2
fall = etat("pet_fall", TA,
            lambda t: (0, 1.4 + 0.15 * math.sin(TAU * t / TA), 0.4),
            lambda t: (4 + 2 * math.sin(TAU * t / TA), 0, 5 * math.sin(TAU * t / TA)),
            lambda t: -0.11 + 0.025 * math.sin(TAU * 2 * t / TA),
            lambda t: 1.08, lambda t: 0.0,
            lambda t: (0, 0, 58 + 12 * math.sin(TAU * 2 * t / TA)), n_kf=18,
            extra={"bouche_o": {"position": lambda t: (0, 0, -HIDE)}})

# pet_sleep (4 s) : le maître dort, ou rien ne bouge depuis 60 s : il s'endort en nuage plat (même aplatissement que la v2),
# paupières closes, respiration lente, léger roulis.
TZ = 4.0
SQ_SLEEP = 0.38
sleep = etat("pet_sleep", TZ,
             lambda t: (0, -0.6, 0),
             lambda t: (0, 0, 3 * math.sin(TAU * t / TZ)),
             lambda t: SQ_SLEEP + 0.04 * math.sin(TAU * t / TZ),
             lambda t: 1.0, lambda t: 1.0,
             lambda t: (0, 0, -30 + 3 * math.sin(TAU * t / TZ)), n_kf=24)


# event_owner_hurt (3 s, ancien hurt de la v2, joué par-dessus l état : rotations et positions s ajoutent, échelles se
# multiplient) : son maître prend un coup ; sursaut (0–1 s), puis il se vexe contre l agresseur : il boude en se gonflant (joues de « pukupuku »), se couvre en
# petit nuage d'orage (gris sombre, ctrl_teinte), yeux plissés et inclinés, bouche boudeuse, crachin, et deux ou trois mini-éclairs
# (codes de l'Orage : zigzag, cœur blanc, halo bleu, bord violet, flash de 0,1 s, deux formes alternées), puis se calme.
TH = 3.0
FLASH_A = ((0.92, 1.04), (2.02, 2.12))
FLASH_B = ((1.48, 1.58),)
VEX = lambda t: bump(t, 0.45, 0.85, 2.35, 2.95)


def fenetres(t, fen):
    return 1.0 if any(a <= t <= b for a, b in fen) else 0.001


def flash(t):
    return max(bump(t, a - 0.02, a, b, b + 0.12) for a, b in FLASH_A + FLASH_B)


owner_hurt = anim("event_owner_hurt", TH, {
    "trans_arc": {"scale": lambda t: (0.001,) * 3}, LIDS["l"]: {"scale": lambda t: (1, 0, 1)}, LIDS["r"]: {"scale": lambda t: (1, 0, 1)},
    "fam_elan": {"position": lambda t: (0.7 * bump(t, 0.0, 0.06, 0.2, 0.6) * math.sin(TAU * t * 7), 1.0 * bump(t, 0.0, 0.08, 0.16, 0.65), 3.0 * bump(t, 0.0, 0.08, 0.16, 0.65))},
    "fam_snap": {"rotation": lambda t: (16 * bump(t, 0.0, 0.08, 0.16, 0.6), 30 * bump(t, 0.5, 0.65, 0.8, 1.0), 8 * bump(t, 0.0, 0.05, 0.2, 0.62) * math.sin(TAU * t * 6)),
                 "scale": lambda t: squash(0.24 * bump(t, 0.0, 0.05, 0.08, 0.2) - 0.08 * bump(t, 0.18, 0.28, 0.3, 0.45) + 0.04 * bump(t, 0.42, 0.5, 0.52, 0.65))},
    EYES["l"]: {"scale": lambda t: (1 + 0.12 * bump(t, 0.0, 0.05, 0.4, 0.6), 1 + 0.12 * bump(t, 0.0, 0.05, 0.4, 0.6) - 0.45 * VEX(t), 1),
                "rotation": lambda t: (0, 0, -22 * VEX(t))},
    EYES["r"]: {"scale": lambda t: (1 + 0.12 * bump(t, 0.0, 0.05, 0.4, 0.6), 1 + 0.12 * bump(t, 0.0, 0.05, 0.4, 0.6) - 0.45 * VEX(t), 1),
                "rotation": lambda t: (0, 0, 22 * VEX(t))},
    "fam_squash": {"scale": lambda t: (1 + 0.1 * VEX(t), 1 + 0.05 * VEX(t), 1 + 0.1 * VEX(t))},
    "ctrl_teinte#c": {"position": lambda t: (-0.42 * VEX(t) + 0.5 * flash(t), -0.42 * VEX(t) + 0.5 * flash(t), -0.3 * VEX(t) + 0.5 * flash(t))},
    "ctrl_alpha#ecl": {"position": lambda t: (1.0 if 0.8 <= t <= 2.3 else 0.0, 0, 0)},
    "ctrl_alpha#arc2": {"position": lambda t: (-1, 0, 0)},       # pas d'éclaircie pendant la bouderie (et aperçu de hurt seul juste)
    "eclair_a": {"scale": lambda t: (fenetres(t, FLASH_A),) * 3},
    "eclair_b": {"scale": lambda t: (fenetres(t, FLASH_B),) * 3},
    "fam_comp": {"rotation": lambda t: (0, 0, 3 * flash(t) * math.sin(TAU * t * 9))},
    "ctrl_emit#g0": {"position": lambda t: (3 * VEX(t), 0, 0)},
    "ctrl_emit#g1": {"position": lambda t: (3 * VEX(t), 0, 0)},
    "ctrl_emit#g2": {"position": lambda t: (3 * VEX(t), 0, 0)},
}, n_kf=120, loop="once",
    # bouche boudeuse, sauf si l'overlay la montre déjà (vie basse) : sinon elle sortirait deux fois du visage
    molang={"bouche_t": {"position": (0, 0, f"-{HIDE + 0.3}*(q.anim_time>0.6)*(q.anim_time<2.8)*(q.owner_health>=q.owner_max_health*0.35)")}})

# ------------------------------------------------------------------ idle : base vivante + 10 comportements au hasard (Molang)
TI, SL, NB = 24.0, 6.0, 16
PRE = (f"v.s=q.life_time/{SL:g}+q.instance_seed*17;v.i=math.floor(math.mod(math.sin(math.floor(v.s)*109+43)*517+517,1)*{NB});"
       f"v.u=math.mod(v.s,1)*{SL:g};v.e=math.clamp(math.min(v.u-0.6,5.4-v.u)/0.7,0,1)")
NUIT_SIESTE = "v.i=v.i+(v.i<3)*(q.time_of_day>0.3)*(q.time_of_day<0.7)*(12-v.i)"
COTE = "(math.mod(math.floor(v.s),2)*2-1)"
SAD = "(q.owner_health<q.owner_max_health*0.35)"          # vie basse du maître (guide 6.6 : q.health parle du familier)
NUIT = "(q.time_of_day>0.3)*(q.time_of_day<0.7)"


def E(a, d):
    return f"math.sin(math.clamp((v.u-{a})/{d},0,1)*180)"


def EP(a, b, r=0.4):
    return f"math.clamp(math.min(v.u-{a},{b}-v.u)/{r},0,1)"


COMPORTEMENTS = {
    6: "petits bonds de joie", 7: "se gonfle de joie (cœurs)", 8: "s'aplatit en crêpe puis rebondit", 9: "arc-en-ciel bref",
    10: "regarde le joueur, clignement lent, s'approche", 11: "pirouette", 12: "sieste en nuage plat (nuit)",
    13: "éternue (quelques gouttes)", 14: "curieux : penche la tête, s'avance", 15: "câlin contre la tête du joueur",
}
TERMS = {}


def T(g, ch, ax, n, expr):
    TERMS.setdefault((g, ch, ax), []).append((n, expr))


H1, H2 = E(1.0, 0.7), E(2.0, 0.7)
# 6 petits bonds
T("fam_comp", "position", 1, 6, f"1.3*({H1}+{H2})")
for ax, k in ((0, 0.5), (1, -1), (2, 0.5)):
    T("fam_joie", "scale", ax, 6, f"{k}*(0.14*({E(0.75, 0.3)}+{E(1.75, 0.3)}+{E(2.65, 0.35)})-0.12*({E(1.05, 0.55)}+{E(2.05, 0.55)}))")
T(ARMS["r"], "rotation", 2, 6, f"45*({H1}+{H2})")
T(ARMS["l"], "rotation", 2, 6, f"-45*({H1}+{H2})")
# 7 se gonfle de joie
G7 = EP(0.9, 3.4)
for ax in range(3):
    T("fam_joie", "scale", ax, 7, f"{G7}*(0.17+0.04*math.sin(v.u*900))")
T(ARMS["r"], "rotation", 2, 7, f"35*{G7}")
T(ARMS["l"], "rotation", 2, 7, f"-35*{G7}")
# 8 crêpe
G8 = EP(1.1, 3.0)
for ax, k in ((0, 0.3), (1, -0.42), (2, 0.3)):
    T("fam_joie", "scale", ax, 8, f"{k}*{G8}")
T("fam_joie2", "scale", 1, 8, f"0.2*{E(3.0, 0.6)}-0.08*{E(3.6, 0.5)}")
T("fam_joie2", "scale", 0, 8, f"-0.1*{E(3.0, 0.6)}")
T("fam_joie2", "scale", 2, 8, f"-0.1*{E(3.0, 0.6)}")
T(ARMS["r"], "rotation", 2, 8, f"55*{G8}")
T(ARMS["l"], "rotation", 2, 8, f"-55*{G8}")
# 9 arc-en-ciel
G9 = EP(1.0, 4.8, 0.6)
T("fam_comp", "position", 1, 9, f"0.6*{E(0.7, 0.6)}")
T("fam_comp", "rotation", 0, 9, f"-6*{G9}")
T(ARMS["r"], "rotation", 2, 9, f"50*{G9}")
T(ARMS["l"], "rotation", 2, 9, f"-50*{G9}")
# 10 regarde le joueur
T("fam_comp", "rotation", 1, 10, "32*v.e")
T("fam_comp", "rotation", 2, 10, "7*v.e")
T("fam_comp", "position", 0, 10, "-0.9*v.e")
# 11 pirouette
T("fam_comp2", "rotation", 1, 11, "(v.u<3.2)*(180-180*math.cos(math.clamp((v.u-1.4)/1.7,0,1)*180))")
for ax, k in ((0, 0.4), (1, -1), (2, 0.4)):
    T("fam_joie2", "scale", ax, 11, f"{k}*-0.1*{E(1.4, 1.7)}")
T(ARMS["r"], "rotation", 2, 11, f"55*{E(1.3, 1.9)}")
T(ARMS["l"], "rotation", 2, 11, f"-55*{E(1.3, 1.9)}")
# 12 sieste
G12 = EP(0.7, 5.3, 0.7)
for ax, k in ((0, 0.22), (1, -0.34), (2, 0.22)):
    T("fam_joie", "scale", ax, 12, f"{k}*{G12}")
T("fam_joie2", "scale", 1, 12, f"0.04*math.sin(v.u*120)*{G12}")
T("fam_comp", "position", 1, 12, f"-0.6*{G12}")
T(ARMS["r"], "rotation", 2, 12, f"-25*{G12}")
T(ARMS["l"], "rotation", 2, 12, f"25*{G12}")
# 13 éternue : inspire (étiré, penché en arrière), atchoum (écrasé, en avant), gouttes
T("fam_comp", "rotation", 0, 13, f"10*{E(1.0, 1.2)}-16*{E(2.1, 0.4)}")
T("fam_comp", "position", 2, 13, f"-0.6*{E(2.1, 0.4)}")
for ax, k in ((0, -0.4), (1, 1), (2, -0.4)):
    T("fam_joie2", "scale", ax, 13, f"{k}*(0.12*{E(1.0, 1.2)}-0.16*{E(2.1, 0.4)})")
for i in range(3):
    T(f"ctrl_emit#g{i}", "position", 0, 13, f"5*{E(2.1, 0.5)}")
# 14 curieux
T("fam_comp", "rotation", 2, 14, f"18*v.e*{COTE}")
T("fam_comp", "position", 2, 14, "-0.8*v.e")
T("fam_comp", "position", 1, 14, "0.4*v.e")
T(ARMS["r"], "rotation", 2, 14, "25*v.e")
# 15 câlin : se rapproche de la tête du joueur, se frotte
G15 = EP(1.0, 4.6, 0.7)
T("fam_comp", "position", 0, 15, f"-2.4*{G15}")
T("fam_comp", "position", 1, 15, f"0.2*math.sin(v.u*500)*{G15}")
T("fam_comp", "rotation", 1, 15, f"24*{G15}")
T("fam_comp", "rotation", 2, 15, f"{G15}*(-8+6*math.sin(v.u*500))")
T("fam_joie2", "scale", 0, 15, f"0.07*math.sin(v.u*500)*{G15}")
T(ARMS["l"], "rotation", 2, 15, f"-40*{G15}")
# expressions
JOIE = f"(v.i==7)*{EP(1.0, 3.6)}+(v.i==9)*{G9}+(v.i==15)*{EP(1.4, 4.4)}+(v.i==6)*{EP(0.8, 2.9)}"
T("yeux_joie", "position", 2, 7, f"-{HIDE}*({EP(1.0, 3.6)}>0.5)")
T("yeux_joie", "position", 2, 9, f"-{HIDE}*({G9}>0.5)")
T("yeux_joie", "position", 2, 15, f"-{HIDE}*({EP(1.4, 4.4)}>0.5)")
T("yeux_joie", "position", 2, 6, f"-{HIDE}*({EP(0.8, 2.9)}>0.5)")
T("bouche_o", "position", 2, 7, f"-{HIDE}*({EP(1.0, 3.6)}>0.5)")
T("bouche_o", "position", 2, 6, f"-{HIDE}*({EP(0.8, 2.9)}>0.5)")
T("bouche_o", "position", 2, 13, f"-{HIDE}*({E(1.9, 0.7)}>0.3)")
T("bouche_o", "position", 2, 14, f"-{HIDE}*(v.e>0.5)")
T("trans_arc", "scale", 0, 9, f"{G9}")
T("trans_arc", "scale", 1, 9, f"{G9}")
T("trans_arc", "scale", 2, 9, f"{G9}")
T("ctrl_alpha#arc", "position", 0, 9, f"{G9}")
T("ctrl_emit#c", "position", 0, 7, f"4*{G7}")
T("ctrl_emit#c", "position", 0, 15, f"3*{G15}")
for tag in ("l", "r"):
    T(LIDS[tag], "scale", 1, 8, "0.5*v.e")
    T(LIDS[tag], "scale", 1, 10, f"0.6*{E(2.4, 1.6)}")
    T(LIDS[tag], "scale", 1, 12, "v.e")
    T(LIDS[tag], "scale", 1, 13, f"{E(1.7, 0.9)}")

BLINK = ("v.b=q.life_time/2.7+q.instance_seed*5;"
         "v.c=math.sin(math.clamp((math.mod(v.b,1)-math.mod(math.floor(v.b)*0.618,0.75))*19,0,1)*180)")

BASE = {
    ("fam_pos", "position"): ("0.22*math.sin(q.anim_time*15)", "0.4*math.sin(q.anim_time*90)", "0.2*math.sin(q.anim_time*15+60)"),
    ("fam_regard", "rotation"): ("2.5*math.sin(q.anim_time*90)", "6*math.sin(q.anim_time*30)", "4*math.sin(q.anim_time*45)"),
    ("fam_squash", "scale"): ("1-0.015*math.sin(q.anim_time*90+30)", "1+0.03*math.sin(q.anim_time*90+30)", "1-0.015*math.sin(q.anim_time*90+30)"),
    ("fam_comp", "position"): (0, 0, 0), ("fam_comp", "rotation"): (0, 0, 0), ("fam_comp2", "rotation"): (0, 0, 0),
    ("fam_joie", "scale"): (1, 1, 1), ("fam_joie2", "scale"): (1, 1, 1),
    (ARMS["r"], "rotation"): (0, 0, "10+7*math.sin(q.anim_time*90+45)"), (ARMS["l"], "rotation"): (0, 0, "-10-7*math.sin(q.anim_time*90+45)"),
    ("yeux_joie", "position"): (0, 0, 0), ("bouche_o", "position"): (0, 0, 0),
    ("trans_arc", "scale"): (0.001, 0.001, 0.001), ("ctrl_alpha#arc", "position"): (-1, 0, 0),
    ("ctrl_emit#c", "position"): (0, 0, 0),
    ("ctrl_alpha#arc2", "position"): (-1, 0, 0), ("ctrl_alpha#ecl", "position"): (-1, 0, 0),
    (LIDS["l"], "scale"): (1, f"0.3*{SAD}+0.35*{NUIT}", 1), (LIDS["r"], "scale"): (1, f"0.3*{SAD}+0.35*{NUIT}", 1),
}
for i in range(3):
    BASE[(f"ctrl_emit#g{i}", "position")] = (0, 0, 0)
MOLANG_TROP = []


def ninstr(s):
    return s.count(";") + 1


def relais(g):
    """Groupe relais de g : même pivot, reprend ses cubes et ses enfants (les termes d'un seul comportement sont actifs à la
    fois : la somme répartie sur deux groupes, ou le produit pour l'échelle, reste exacte)."""
    k = g + "_b"
    if k in groups:
        return k
    gg = groups[g]
    group(k, gg["origin"], g, nm=gg["name"] + "_b")
    groups[k]["ids"], gg["ids"] = gg["ids"], []
    for n, x in groups.items():
        if x["parent"] == g and n != k:
            x["parent"] = k
    return k


def cles(base, terms, neutre, pre_extra=""):
    """Répartit base + termes en clés de 512 caractères et 16 instructions au plus ; renvoie la liste des clés."""
    out, cur = [], []

    def build(ts, b):
        pre = PRE + pre_extra + (";" + NUIT_SIESTE if any(n == 12 for n, _ in ts) else "")
        bb = fmt(b)
        return pre + ";" + (bb if bb not in ("0", "0.0") else "") + "".join(f"+(v.i=={n})*({e})" for n, e in ts)
    b = base
    for t in terms:
        if cur and len(build(cur + [t], b)) > 505:
            out.append(build(cur, b))
            cur, b = [], neutre
        cur.append(t)
    out.append(build(cur, b))
    for k in out:
        if len(k) > 512 or ninstr(k) > 16:
            MOLANG_TROP.append(f"{len(k)} car.")
    return out


def construire_repos(nom, base):
    """pet_idle et pet_fly : base vivante + les 10 comportements au hasard (TERMS), répartis en clés de 512 caractères."""
    idle_molang = {}

    def poser(g, ch, ax, v):
        idle_molang.setdefault(g, {}).setdefault(ch, [None, None, None])[ax] = v

    for (g, ch), b in base.items():
        for ax in range(3):
            neutre = 1 if ch == "scale" else 0
            terms = TERMS.get((g, ch, ax), [])
            ks = cles(b[ax], terms, neutre) if terms else [b[ax]]
            if g in (LIDS["l"], LIDS["r"]) and ax == 1:
                assert len(ks) == 1, [len(k) for k in ks] + [len(PRE), len(NUIT_SIESTE)]
                a, _, bb = ks[0].rpartition(";")
                ks = [f"{a};math.min(1,{bb})"]
            gg = g
            for i, k in enumerate(ks):
                poser(gg, ch, ax, k)
                if i + 1 < len(ks):
                    gg = relais(gg)
    orph = [k for k in TERMS if (k[0], k[1]) not in base]
    assert not orph, f"comportements sans base : {orph}"
    for tag in ("l", "r"):
        poser(EYES[tag], "scale", 1, f"{PRE};{BLINK};1-0.96*v.c")
        r = relais(EYES[tag])
        k = f"{PRE};1-0.96*math.min(1,{JOIE})"
        if len(k) > 512 or ninstr(k) > 16:
            MOLANG_TROP.append(f"{len(k)} car. yeux")
        poser(r, "scale", 1, k)
    for g, chans in idle_molang.items():
        for ch, v in chans.items():
            neutre = 1 if ch == "scale" else 0
            chans[ch] = tuple(neutre if x is None else x for x in v)
    return anim(nom, TI, molang=idle_molang)


idle = construire_repos("pet_idle", BASE)
# pet_fly (mode vol : peut-être joué aussi à l'arrêt, non précisé par le guide) : les mêmes comportements, plus l'allure de vol
# de la v2 (penché, traîne, bras qui battent comme de petites ailes décoratives, étiré au battement) × la vitesse du nuage
# (q.ground_speed parle du familier, guide 6.6 §4) : immobile, il vit comme au repos ; en route, il vole.
KV = "math.clamp(q.ground_speed/3,0,1)"
BASE_VOL = dict(BASE)
BASE_VOL[("fam_pos", "position")] = ("0.22*math.sin(q.anim_time*15)", f"0.4*math.sin(q.anim_time*90)+{KV}*0.6*math.sin(q.anim_time*150)",
                                     f"0.2*math.sin(q.anim_time*15+60)+{KV}*1.6")
BASE_VOL[("fam_regard", "rotation")] = (f"2.5*math.sin(q.anim_time*90)-{KV}*6", "6*math.sin(q.anim_time*30)", "4*math.sin(q.anim_time*45)")
BASE_VOL[("fam_squash", "scale")] = tuple(f"({a})*(1+{KV}*{k}*math.sin(q.anim_time*450+35))" for a, k in
                                          zip(BASE[("fam_squash", "scale")], (-0.03, 0.06, -0.03)))
BASE_VOL[(ARMS["r"], "rotation")] = (0, 0, f"10+7*math.sin(q.anim_time*90+45)+{KV}*(18+30*math.sin(q.anim_time*450))")
BASE_VOL[(ARMS["l"], "rotation")] = (0, 0, f"-10-7*math.sin(q.anim_time*90+45)-{KV}*(18+30*math.sin(q.anim_time*450))")
fly = construire_repos("pet_fly", BASE_VOL)

# ------------------------------------------------------------------ overlay_mochi : regard, virages, humeur, monde
DT = "math.min(1,q.delta_time*{})"
PRES = "math.clamp((1.6-q.owner_distance)/0.6,0,1)"     # maître tout près (le nuage l attend à 2 blocs)
SACC = ("v.g=math.mod(q.life_time,32)/1.6;v.k=math.floor(v.g);"
        "v.ga=math.mod(math.abs(math.sin((math.mod(v.k,20)+q.instance_seed*20)*61))*331,1);"
        "v.gb=math.mod(math.abs(math.sin((math.mod(v.k+19,20)+q.instance_seed*20)*61))*331,1);"
        "v.gv=math.lerp(v.gb,v.ga,math.clamp(math.mod(v.g,1)*6,0,1))")
overlay_molang = {
    "fam_reac": {
        # le maître vient tout près (il s'arrête à 2 blocs) : il lève le visage vers lui (+X : le haut part vers l'arrière)
        "rotation": (f"v.ax=math.lerp(v.ax,{PRES}*9,{DT.format(2)});v.ax",
                     0,
                     f"v.az=math.lerp(v.az,math.clamp(-q.yaw_speed*0.05,-12,12),{DT.format(2)});v.az"),
        "position": (f"v.w1=math.lerp(v.w1,{SAD},{DT.format(1.5)});-0.8*v.w1",
                     f"v.w2=math.lerp(v.w2,{SAD},{DT.format(1.5)});v.pr=math.lerp(v.pr,{PRES},{DT.format(2)});"
                     "-0.7*v.w2+0.5*v.pr*math.abs(math.sin(q.life_time*315))",
                     0),
        "scale": (f"v.r1=math.lerp(v.r1,q.is_in_rain,{DT.format(0.8)});1+0.07*v.r1",
                  f"v.r2=math.lerp(v.r2,q.is_in_rain,{DT.format(0.8)});1+0.07*v.r2",
                  f"v.r3=math.lerp(v.r3,q.is_in_rain,{DT.format(0.8)});1+0.07*v.r3"),
    },
    "bouche_t": {"position": (0, 0, f"-{HIDE + 0.3}*{SAD}")},
    # humeur grise : triste (vie basse) ou sous la pluie ; nuage gris bleuté (ctrl_teinte, non simulé par l'aperçu)
    "ctrl_teinte#c": {"position": (f"-0.16*{SAD}-0.2*q.is_in_rain", f"-0.11*{SAD}-0.16*q.is_in_rain", f"0.02*{SAD}-0.05*q.is_in_rain")},
    # éclaircie : quand la pluie cesse, un arc-en-ciel se lève derrière lui quelques secondes (v.ra suit la pluie lentement)
    "trans_arc2": {"scale": ("v.ra=math.lerp(v.ra,q.is_in_rain,math.min(1,q.delta_time*0.22));"
                             "v.ar=math.clamp((v.ra-0.08)*3,0,1)*math.clamp((1-v.ra)*5,0,1)*(1-q.is_in_rain);0.001+1.15*v.ar",
                             "0.001+1.15*v.ar", "0.001+1.15*v.ar")},
    "ctrl_alpha#arc2": {"position": ("v.ar", 0, 0)},
    "ctrl_emit#c": {"position": (-1, 0, 0)},
    # porté (menu Apparence, ou second familier : guide 6.6) : à droite du joueur, à hauteur d'épaule, comme la v2
    "mochi": {"position": tuple(f"(1-q.is_pet)*{round(float(v), 3)}" for v in PORTE)},
    # coucou du bras droit quand le maître arrive tout près
    ARMS["r"]: {"rotation": (0, 0, f"v.cc=math.lerp(v.cc,{PRES},{DT.format(2)});v.cc*(30+22*math.sin(q.life_time*540))")},
}
for i in range(3):
    overlay_molang[f"ctrl_emit#g{i}"] = {"position": (f"-1+3*math.max({SAD}*(q.owner_max_health>0),q.is_in_rain)", 0, 0)}
for tag, s in (("l", -1), ("r", 1)):
    overlay_molang[EYES[tag]] = {"position": (f"{SACC};(v.gv*2-1)*0.09", f"{SACC};(math.mod(v.gv*7.3,1)*2-1)*0.05", 0)}
    overlay_molang[LIDS[tag]] = {"rotation": (0, 0, f"{-s * 16}*math.max({SAD},q.is_in_rain*0.5)")}
overlay = anim("overlay_mochi", 32.0, molang=overlay_molang)


# ------------------------------------------------------------------ événements
# Apparition (2026-11-08) : le nuage se CONDENSE. Une nappe de brume large et fine, plus pâle, se resserre en tourbillonnant
# et s'épaissit (largeur 1,8 → 1, hauteur 0,08 → 1) ; « plop » de guimauve (étiré puis écrasé, son) ; il ouvre les yeux
# (tenus plissés jusque-là : les paupières valent 0 dans l'état, une échelle d'événement ne peut pas les fermer, donc l'œil
# s'aplatit), fait coucou du bras droit, puis petit bond de joie, yeux ^^, et lève la frimousse vers son maître.
def _apparition(T0, T1, T2, T3, T4, vague=True):
    """T0 fin de condensation, T1 fin du plop, T2 yeux ouverts, T3 début de la joie, T4 fin."""
    def elan_s(t):
        c = sm(t, 0.0, T0)
        g = 0.3 + 0.7 * sm(t, 0.0, T0 * 0.4)
        w = g * (1.8 - 0.8 * c) * (1 + 0.04 * math.sin(TAU * 5 * t) * (1 - c))
        h = max(0.04, 0.08 + 0.92 * c * c)
        k = 0.2 * bump(t, T0 - 0.05, T0 + 0.05, T0 + 0.06, T0 + 0.14) - 0.22 * bump(t, T0 + 0.1, T0 + 0.17, T0 + 0.19, T1) \
            + 0.06 * bump(t, T1 - 0.05, T1, T1 + 0.02, T1 + 0.12)
        return (w * (1 - 0.5 * k), h * (1 + k), w * (1 - 0.5 * k))    # k > 0 : étiré (le plop part vers le haut)
    tint = lambda t: (0.22 * (1 - sm(t, T0 * 0.5, T0 + 0.1)),) * 2 + (0.28 * (1 - sm(t, T0 * 0.5, T0 + 0.1)),)
    oeil = lambda t: (1, max(0.08, 0.08 + 0.92 * sm(t, T1, T2)) * (1 + 0.15 * bump(t, T2 - 0.03, T2, T2 + 0.02, T2 + 0.12)), 1)
    joie = lambda t: (0, 0, -HIDE if T3 + 0.05 <= t <= T4 - 0.12 else 0)
    bond = lambda t: (0, 0.9 * bump(t, T3, T3 + 0.14, T3 + 0.16, T3 + 0.34), 0)
    regard = lambda t: (8 * bump(t, T3, T3 + 0.15, T4 - 0.2, T4), 0, 6 * bump(t, T3, T3 + 0.15, T4 - 0.2, T4))
    tours = lambda t: (0, -150 * (1 - sm(t, 0.0, T0 + 0.1)), 0)                  # la brume s'enroule en se resserrant
    pistes = {"fam_elan": {"scale": elan_s, "position": bond, "rotation": tours}, "ctrl_teinte#c": {"position": tint},
              EYES["l"]: {"scale": oeil}, EYES["r"]: {"scale": oeil}, "yeux_joie": {"position": joie},
              "fam_regard": {"rotation": regard}}
    if vague:
        v = lambda t: bump(t, T2, T2 + 0.12, T3 - 0.05, T3 + 0.1)
        pistes[ARMS["r"]] = {"rotation": lambda t: (0, 0, v(t) * (55 + 18 * math.sin(TAU * 3.2 * (t - T2))))}
    return pistes


equip = anim("event_equip", 2.0, _apparition(0.55, 0.8, 0.95, 1.45, 2.0), n_kf=60, loop="once")
equip["animators"]["effects"] = {"name": "Effects", "type": "effect",
                                 "keyframes": [{"channel": "sound", "data_points": [{"effect": "entity.chicken.egg", "file": ""}], "time": 0.58}]}


# event_teleport : il revient près du maître (20 blocs, ou coincé 3 s) : la même condensation en bref, sans coucou ni son
teleport = anim("event_teleport", 1.2, _apparition(0.32, 0.5, 0.6, 0.7, 1.2, vague=False), n_kf=36, loop="once")


def ev_jump(t):
    return squash(0.16 * bump(t, 0.0, 0.06, 0.06, 0.14) - 0.14 * bump(t, 0.1, 0.2, 0.3, 0.5))


jump = anim("event_jump", 0.55, {"fam_snap": {"scale": ev_jump}, "fam_elan": {"position": lambda t: (0, -0.5 * bump(t, 0.05, 0.2, 0.25, 0.5), 0)}},
            n_kf=22, loop="once")
AMP = "math.clamp(q.land_speed*0.12,0.4,1.4)"


def land_k(t):
    return 0.22 * bump(t, 0.0, 0.06, 0.1, 0.24) - 0.08 * bump(t, 0.2, 0.3, 0.32, 0.44) + 0.03 * bump(t, 0.42, 0.5, 0.5, 0.6)


land = anim("event_land", 0.6, n_kf=24, loop="once", molang=None)
land["animators"][groups["fam_snap"]["uuid"]] = {"name": "fam_snap", "type": "bone", "keyframes": [
    kf("scale", round(t, 3), (f"1+{round(0.5 * land_k(t), 4)}*{AMP}", f"1-{round(land_k(t), 4)}*{AMP}", f"1+{round(0.5 * land_k(t), 4)}*{AMP}"))
    for t in [i * 0.6 / 24 for i in range(25)]]}

outliner.insert(0, bone_node("mochi"))     # familier vivant : sa propre racine, aucun groupe du corps (guide 6.6)
# familier vivant en vol (guide 6.6) : un nuage n'a pas de pattes, il flotte ; près de l'épaule (dessous à 1,6 bloc), à 2 blocs
FAMILIER = {"mode": "vol", "distance": 2, "vitesse": 1, "hauteur": 1.6}
ANIMS = [idle, fly, walk, run, sit, sleep, swim, fall, overlay, equip, teleport, owner_hurt, jump, land]
assert len(ANIMS) <= 32
assert not MOLANG_TROP, "Molang trop long : " + " | ".join(MOLANG_TROP)

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


exprs = [v for a in ANIMS for b in a["animators"].values() for k in b["keyframes"] for dp in k.get("data_points", []) for v in dp.values()
         if isinstance(v, str) and not v.replace(".", "").replace("-", "").isdigit()]
print(len(elements), "cubes ;", len(groups) + 2, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      f"densité {DENS:.1f} texels/px ; Molang max {max(map(len, exprs))} car., {max(map(ninstr, exprs))} instructions")
