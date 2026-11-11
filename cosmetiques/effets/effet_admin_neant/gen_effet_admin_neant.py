"""Déchirure du Néant v3 (agrandie, limite de 320 px des effets : guide 3 et 15) : effet de téléportation de l'ensemble Admin (guide 15). Design original (fiche
.claude/references/effets/neant-dechirure.md ; failles-portails.md, principes-fx-anime.md). Aucune œuvre reprise.
Écrit effet_admin_neant.png, effet_admin_neant_e.png et .build/effet_admin_neant_brut.bbmodel.

Retour sur la v1 (lèvres en lentille, masque blanc) : « la faille doit être plus craquelure ; pas de visage, juste des
yeux rouges qui apparaissent avec une pulsation vive, et le bras qui sort pour attraper ».

v3 (2026-11-06) : ciel haut et grand (trou centré à y = 170, 40 px devant le joueur, 110 × 78 px ; fissures sur ±250 px,
de y = 45 à 300 au repos), yeux plus grands à pulsation plus forte puis battement lent ; le grand bras (épaule, coude,
avant-bras, poignet, main, os plus clairs) est SORTI du groupe face caméra : orienté dans le monde, il descend en biais
(coude vers la droite du joueur) et atteint le joueur sous tous les angles. Le ciel est en cam_ (sphérique), pivot au
centre du trou : il fait face aussi au joueur dessous (camy_ le montrait par la tranche), et sa plaque noire, toujours
entre l'œil et le pivot, cache l'épaule : le bras sort du noir de partout. Le bras surgit du fond (échelle 0,16 → 1).
Le joueur est soulevé par à-coups pendant la charge (≤ 4 px). Mains du bord plus grandes, doigts peu écartés, ongles courts.

v4 (2026-11-06, « améliorer la qualité et les détails » ; captures en jeu de la v3 : de jour une « araignée géante »,
de nuit trou et fissures invisibles) : fissures de verre (largeur qui retombe vite après le bord du trou, segments
presque droits, nombreuses fêlures qui relient les fissures en cellules, micro-fêlures, fêlures isolées loin du trou,
arête claire d'un côté, éclats manquants, éclats de ciel décalés le long des fissures), fissures dans le trou à part
(cachées dès qu'il s'ouvre), effacées avec le trou ; lueur add_ violette floue autour des fissures et du bord du trou
(visible de nuit) ; trou : une image à trois échelles, une plaque à la fois, profondeur peinte (marche, couches de noir,
braises, liseré violet), tourbillon add_ qui tourne au fond, éclats de ciel épais recourbés vers le noir sur le bord,
esquilles aspirées en spirale ; yeux : iris strié, cœur brûlant, halo opaque rouge noirci, fente noire qui se resserre
aux battements et descend vers le joueur, lueur qui bave ; bras : vraie anatomie (tête et tubercule de l'humérus,
épicondyles, olécrâne, radius et cubitus séparés et croisés, carpes, métacarpes, phalanges à têtes en double bosse,
griffes pâles recourbées), os peints (ombre de cylindre, bouts sombres, fêlures), plus épais ; filaments d'encre qui
s'échappent du bras ; mains du bord au même niveau de détail.

v5 (2026-11-06, retour en jeu de la v4 : « souci sur la position du joueur dans la main, la main se retourne à 180°
quand il attrape ; yeux : juste une aura rouge ») : prise refaite (main d'en haut, paume sur la tête, doigts refermés
le long de l'épaule gauche et du dos, orientation tirée de l'avant-bras, rotation de poignet constante puis orientation
monde fixe pendant la prise et le transport : voir « prise » plus bas), joueur à l'échelle du bras, clés denses
(42 / s) pendant le geste ; yeux remplacés par une aura rouge diffuse. Fissures, trou, bras, sons, tailles inchangés.

v6 (2026-11-07, retour en jeu de la v5 : « les yeux c'est juste un ovale et plus deux yeux distincts ; les fissures sont
encore très pixel et non lisses ») : yeux = deux amandes de lumière rouge vive séparées, inclinées (coin intérieur plus
bas), sans détail interne, halo flou ; pulsation par un halo flou seul. Fissures en géométrie : un cube fin par segment
simplifié (bords nets à toute distance), image de profil en travers, lueur add_ par segment (profil flou en travers).
Cause du pixel (mesurée) : lignes de 1–2 texels de 0,63 px sur tuiles cutout, lueur à 5 px par texel. Trou, bras, prise,
sons, tailles inchangés.

v7 (2026-11-07, retour en jeu de la v6 : « les fissures ne sont que des traits droits, pas une fissure lisse et continue ;
les animations sont par à-coups ; même le bras a une micro-pause quand il remonte ») : fissures = chemins lisses (courbure
en sinus lents et coudes doux, largeur continue avec renflements et pointe effilée), segments courts (≤ 1,15 px avant
l'échelle, ≤ ~6° entre voisins), longues radiales + ramifications courtes ; propagation continue (pièces qui poussent par
l'échelle le long de leur corde, front qui accélère puis ralentit, recule à la fermeture) ; trou en une plaque à échelle
continue ; une seule secousse (au bris) ; bras : une courbe lisse par phase, arrêts seulement à la sortie, à la prise
(ou la pose) et à la rentrée (cause mesurée de la micro-pause : smoothsteps bout à bout, vitesse nulle à 3,42 s) ;
30 clés/s. Yeux, prise, couleurs, lueur, tailles, sons inchangés.

Pièces (posées au sol, pieds à l'origine ; tout le ciel dans un groupe cam_ : le ciel fêlé fait face à celui qui
regarde)
- Fissures (v6) : réseau noir ramifié (troncs qui s'affinent, angles cassés, fêlures entre troncs, cœur violet très
  sombre au calque _e) en cubes fins tournés dans le plan, un par segment simplifié ; 4 étapes selon la distance
  le long de la fissure, révélées par à-coups (propagation), effacées de l'extérieur vers le centre à la fermeture.
- Trou : 3 plaques noires opaques de plus en plus grandes, contour en éclats aigus et esquilles noires détachées
  autour ; éclats de ciel (plaques cutout bleu ciel) qui se détachent du bord et tombent en tournant à chaque palier.
- Yeux (v6) : deux amandes rouges sans détail, une plaque add_ par œil (amande nette) + un halo flou par œil
  (pulsation, cumul ≤ 252) ; trois coups vifs à l'apparition puis battement lent.
- Bras : long bras squelettique (humérus, coude, radius et cubitus, poignet, main à 4 doigts de 3 phalanges et pouce,
  jointures renflées, ongles pointus ivoire), chaîne cinématique inverse à deux os (épaule cachée dans le noir) :
  départ = il sort, descend saisir la copie du joueur, remonte et l'emporte dans le trou ; arrivée = il descend en
  tenant le joueur, le dépose, s'ouvre et remonte. Deux mains plus petites agrippent le bord du trou.
- Sol : ombre et onde (trans_, motifs symétriques : faces horizontales en miroir X dans le mod).
- Particules : éclat de ciel, poussière noire (modélisées) ; reverse_portal, ash, smoke, squid_ink (Minecraft).
Animations : charge (loop 2,4 s : premières fissures qui avancent et reculent, ombre), depart (4,8 s), arrivee (4,8 s),
particle_*_fall. Sons embarqués originaux (sons/*.py, tools/synthe.py) : neant_fele (fêlure par à-coups),
neant_pulse (battements graves des yeux) ; block.glass.break du jeu quand le trou s'ouvre ; rien pendant la charge.
Taille : ECHELLE_ZONE (2,5 : tout le ciel), C_CIEL = (0, 170, −40). Son de prise (neant_impact) à la saisie / à la pose.

Ce qui se juge seulement en jeu (« Essayer » de l'onglet Effets) : cam_ du ciel vu d'en dessous (lacet stable grâce aux
40 px de décalage, supposé), bras hors cam_, particules et cadences, additif des yeux, lecture des fissures fines à distance, sons.
"""
import base64, io, json, math, os, sys, uuid as _uuid

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

NOM = "effet_admin_neant"
TEX = 512
SS = 4
ECHELLE_ZONE = 2.5        # tout le ciel (cam_ciel) est dessiné à cette échelle autour de C_CIEL

YC = 170.0         # centre du trou (hauteur, monde)
ZC = -40.0         # centre du trou : 40 px devant le joueur (lacet stable pour le joueur dessous, voir docstring)
ZH = 3.6           # plan du ciel (local cam_, +Z vers celui qui regarde) : devant le pivot, qui cache l'épaule du bras
RX, RY = 22.0, 15.5        # demi-axes du trou ouvert (× ECHELLE_ZONE : 55 × 39 px)
TROUS = [0.42, 0.72, 1.0]  # paliers d'ouverture
XMAX, YBAS, YHAUT = 100.0, YC - 50.0, YC + 52.0      # étendue des fissures (avant échelle : ±250 px, y 45 à 300)
TP = 4                     # texels par px des fissures (avant échelle)
TUILE = 10.0               # px


# ------------------------------------------------------------------ peinture
def grille(W, H, ss=SS):
    n_w, n_h = W * ss, H * ss
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w, (np.arange(n_h) + 0.5) / n_h)


def lanczos(a, W, H):
    return np.array(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)).astype(np.float32)


def assembler(rgb, al, W, H, opaque=False, seuil=110):
    c = np.stack([lanczos(rgb[..., k], W, H) for k in range(3)], axis=-1)
    a = lanczos(al, W, H)
    arr = np.zeros((H, W, 4), np.uint8)
    a = np.where(a > seuil, 255, 0) if opaque else np.where(a > 8, np.clip(a, 1, 254), 0)
    arr[..., :3] = c
    arr[..., 3] = a
    arr[a == 0, :3] = 0
    return arr


def additif(rgb, W, H, gain):
    c = np.stack([lanczos(rgb[..., k] * gain, W, H) for k in range(3)], axis=-1)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = c
    a = c.max(axis=2) > 12
    arr[..., 3] = a * 255
    arr[~a, :3] = 0
    return arr


def mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.asarray(a, np.float32) * (1 - t) + np.asarray(b, np.float32) * t


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def bruit2d(W, H, rng, k=8):
    small = rng.random((k, k))
    return np.array(Image.fromarray((small * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255


def uni(rgb, N=8):
    a = np.zeros((N, N, 4), np.uint8)
    a[..., :3] = rgb
    a[..., 3] = 255
    return a


def os_tex(N=16, clair=1.0):
    u, v = grille(N, N)
    r = np.maximum(np.abs(u - 0.5), np.abs(v - 0.5)) * 2
    g = (1 - r ** 2) ** 2
    rgb = mix((22, 20, 26), (104, 98, 108), g * clair)
    return assembler(rgb, np.full(u.shape, 255.0), N, N, opaque=True)


def os_clair_tex(N=16):
    """Os du grand bras et des mains du bord : plus clairs (lisibles de loin sur le noir et sur le ciel)."""
    u, v = grille(N, N)
    r = np.maximum(np.abs(u - 0.5), np.abs(v - 0.5)) * 2
    g = (1 - r ** 2) ** 2
    rgb = mix((74, 68, 78), (196, 188, 190), g)
    return assembler(rgb, np.full(u.shape, 255.0), N, N, opaque=True)


def os_long_tex(W=16, H=48, pal=((70, 63, 60), (222, 212, 194)), seed=0, fentes=2, bouts=0.55):
    """Os vu de côté, longueur le long de v : ombre de cylindre en travers, bouts plus sombres (jointures), marbrure
    légère, fines fêlures sombres le long de l'os."""
    rng = np.random.default_rng(seed)
    u, v = grille(W, H)
    c = np.clip(1 - (2 * u - 1) ** 2, 0, 1) ** 0.7
    rgb = mix(pal[0], pal[1], c)
    fin = smooth((np.abs(v - 0.5) - 0.34) / 0.16)
    rgb = mix(rgb, rgb * 0.62, fin * bouts)
    n = bruit2d(u.shape[1], u.shape[0], rng, 6)
    rgb = rgb * (0.93 + 0.12 * n)[..., None]
    img = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(img)
    for _ in range(fentes):
        x, y = rng.uniform(0.3, 0.7) * W * SS, rng.uniform(0.1, 0.5) * H * SS
        pts = [(x, y)]
        for _ in range(int(rng.integers(4, 8))):
            x += rng.normal(0, 0.06) * W * SS
            y += rng.uniform(0.04, 0.09) * H * SS
            pts.append((x, y))
        d.line(pts, fill=255, width=max(1, int(0.8 * SS)))
    f = np.asarray(img, np.float32) / 255
    rgb = mix(rgb, rgb * 0.42, f)
    return assembler(rgb, np.full(u.shape, 255.0), W, H, opaque=True)


def os_bout_tex(N=16, pal=((96, 88, 82), (222, 212, 194))):
    """Bout d'os et tête articulaire : dôme clair, bord ombré."""
    u, v = grille(N, N)
    r = np.hypot(u - 0.45, v - 0.42) * 2
    rgb = mix(pal[0], pal[1], smooth(1 - r / 1.1) ** 0.8)
    return assembler(rgb, np.full(u.shape, 255.0), N, N, opaque=True)


def ivoire_tex(N=16):
    u, v = grille(N, N)
    r = np.hypot(u - 0.5, v - 0.42) * 2
    rgb = mix((246, 242, 230), (196, 188, 170), smooth(r))
    return assembler(rgb, np.full(u.shape, 255.0), N, N, opaque=True)


def ombre_tex(N):
    u, v = grille(N, N)
    r = np.hypot(u - 0.5, v - 0.5) * 2
    rgb = mix((8, 4, 12), (34, 12, 50), smooth(r))
    return assembler(rgb, 170 * smooth(1 - r) ** 1.2, N, N)


def onde_tex(N):
    u, v = grille(N, N)
    r = np.hypot(u - 0.5, v - 0.5) * 2
    anneau = smooth(1 - np.abs(r - 0.82) / 0.13)
    fil = smooth(1 - np.abs(r - 0.9) / 0.04)
    rgb = mix((20, 8, 30), (120, 60, 160), fil)
    return assembler(rgb, np.clip(210 * anneau + 30 * fil, 0, 230), N, N)


# --- réseau de fissures (coordonnées locales au centre du trou, px ; y vers le haut)
# v7 (retour en jeu de la v6 : « les fissures ce ne sont que des traits droits, pas une fissure lisse et continue ») :
# chaque fissure est un chemin lisse intégré pas à pas (DS) : sa courbure est une somme de sinus de grandes longueurs
# d'onde, plus quelques coudes doux (bosse gaussienne de courbure, jamais un angle) ; la largeur varie en continu
# (retombée après le bord du trou, renflements lents, pointe effilée au bout). Longues fissures radiales comme du verre
# brisé, petites ramifications courtes, quelques fêlures en arc près du trou (peu de cellules) et fêlures isolées.
RNG = np.random.default_rng(2027)
RNG2 = np.random.default_rng(4041)                 # détails (éclats de ciel décalés) : ne change pas le réseau
BX0, BX1 = -XMAX, XMAX
BY0, BY1 = YBAS - YC, YHAUT - YC
DS = 0.2           # pas d'intégration (px)
W_FIN = 0.40       # largeur courante loin du trou (1 px en jeu à l'échelle 2,5)
W_POINTE = 0.09    # largeur à la pointe
CHEMINS = []       # dict(P = (n, 2), W = (n,), L = (n,) longueur parcourue depuis l'impact, A = angle, rang)
TRONCS = []        # par tronc : (angle, [(point, longueur parcourue)])
EPAVES = []        # éclats de ciel décalés le long des fissures : (x, y, angle de la fissure, longueur parcourue, taille)


def dans(p, m=0.6):
    return BX0 + m < p[0] < BX1 - m and BY0 + m < p[1] < BY1 - m


def portee(p, a):
    """Distance au bord de la zone le long de la direction a."""
    d = np.array((math.cos(a), math.sin(a)))
    ts = []
    for k, (lo, hi) in enumerate(((BX0, BX1), (BY0, BY1))):
        if abs(d[k]) > 1e-6:
            ts += [(lo - p[k]) / d[k], (hi - p[k]) / d[k]]
    return min(t for t in ts if t > 0)


def onde_lisse(s, rng, longueurs, amp):
    """Somme de sinus de longueurs d'onde données (px), amplitude totale ≈ amp : bruit lisse le long de s."""
    out = np.zeros_like(s)
    for lw in longueurs:
        out += rng.uniform(0.5, 1.0) * np.sin(2 * math.pi * s / (lw * rng.uniform(0.8, 1.25)) + rng.uniform(0, 2 * math.pi))
    return amp * out / max(1e-9, len(longueurs) * 0.75)


def chemin_lisse(p0, a0, longueur, w0, L0, rang, plein=0.0, lam=8.0, ondul=0.022, coudes=0, rappel=0.06, w_debut=None,
                 deux_pointes=False, crochet=0.0):
    """Intègre une fissure lisse : courbure = sinus lents + coudes gaussiens doux + rappel vers la direction de départ.
    Largeur : w0 jusqu'à `plein`, retombée exponentielle (lam) vers W_FIN, renflements lents (±18 %), pointe effilée."""
    n = max(3, int(longueur / DS) + 1)
    s = np.arange(n) * DS
    kap = onde_lisse(s, RNG, (55.0, 26.0, 13.0), ondul) + crochet * np.clip(s / max(longueur, 1e-6), 0, 1) ** 2
    for _ in range(coudes):                                  # coude doux : rotation de 10 à 24° étalée sur ~5 px
        sc, sg = RNG.uniform(0.15, 0.85) * longueur, RNG.uniform(1.6, 2.4)
        kap += RNG.choice((-1, 1)) * math.radians(RNG.uniform(10, 24)) * np.exp(-0.5 * ((s - sc) / sg) ** 2) / (sg * math.sqrt(2 * math.pi))
    P, a = [np.array(p0, float)], a0
    A = [a]
    for i in range(1, n):
        a += kap[i] * DS - rappel * (a - a0) * DS
        q = P[-1] + DS * np.array((math.cos(a), math.sin(a)))
        if not dans(q):
            break
        P.append(q)
        A.append(a)
    P = np.array(P)
    s = s[:len(P)]
    tot = s[-1]
    wb = W_FIN + (w0 - W_FIN) * np.exp(-np.maximum(0.0, s - plein) / lam)
    wb = wb * (1.0 + onde_lisse(s, RNG, (17.0, 9.0), 0.18))  # renflements lents
    if w_debut is not None:                                   # branche : naît à la largeur de sa base
        wb = np.minimum(wb, w_debut + (wb - w_debut) * np.clip(s / 1.5, 0, 1))
    effile = np.clip((tot - s) / max(2.0, 0.35 * tot), 0, 1) ** 0.85
    if deux_pointes:
        effile = np.minimum(effile, np.clip(s / max(2.0, 0.35 * tot), 0, 1) ** 0.85)
    W = W_POINTE + (wb - W_POINTE) * effile
    c = {"P": P, "W": W, "L": L0 + s, "A": np.array(A), "rang": rang}
    CHEMINS.append(c)
    return c


def ramifier(c, taux_epine, taux_branche, rang_max=2):
    """Petites ramifications le long d'un chemin : épines courtes (1,2 à 4 px) et quelques vraies branches."""
    P, W, L, A = c["P"], c["W"], c["L"], c["A"]
    tot = len(P) * DS
    s = 3.0
    while True:
        s += RNG.exponential(1.0 / taux_epine)
        i = int(s / DS)
        if i >= len(P) - 8:
            break
        cote = RNG.choice((-1, 1))
        if c["rang"] < rang_max and RNG.random() < taux_branche / taux_epine:
            lg = RNG.uniform(8, 26) * (1.0 if c["rang"] == 0 else 0.6)
            b = chemin_lisse(P[i], A[i] + cote * math.radians(RNG.uniform(22, 48)), lg, W[i] * 0.7, L[i], c["rang"] + 1,
                             lam=4.0, ondul=0.03, coudes=int(RNG.random() < 0.4), rappel=0.03, w_debut=W[i] * 0.75)
            ramifier(b, taux_epine * 0.8, taux_branche * 0.5, rang_max)
        elif W[i] > 0.3:
            chemin_lisse(P[i], A[i] + cote * math.radians(RNG.uniform(30, 72)), RNG.uniform(1.2, 4.2), W[i] * 0.55, L[i], 3,
                         lam=1.0, ondul=0.0, rappel=0.0, w_debut=W[i] * 0.6, crochet=cote * RNG.uniform(0.0, 0.25))


ANG_T = [0.08, 0.62, 1.2, 1.62, 2.3, 2.95, 3.4, 4.1, 4.75, 5.35]
LONG_T = [0.95, 0.55, 0.9, 0.75, 0.97, 0.5, 0.85, 0.65, 0.95, 0.6]    # longueurs inégales : pas une étoile régulière
for k, a in enumerate(ANG_T):
    a += RNG.normal(0, 0.1)
    p0 = np.array((1.6 * math.cos(a), 1.6 * math.sin(a)))
    w0 = 1.2 + 0.25 * abs(math.cos(a)) + RNG.uniform(-0.1, 0.12)
    c = chemin_lisse(p0, a, portee(p0, a) * LONG_T[k] * RNG.uniform(0.9, 1.0), w0, 0.0, 0,
                     plein=0.8 * math.hypot(RX * math.cos(a), RY * math.sin(a)), lam=9.0, coudes=2)
    TRONCS.append((a, [(p.copy(), L) for p, L in zip(c["P"][::5], c["L"][::5])]))
    for p, L, a_ in zip(c["P"][::10], c["L"][::10], c["A"][::10]):
        if 3 < L < 34 and RNG2.random() < 0.18:                # éclat de ciel décalé le long de la fissure
            EPAVES.append((p[0], p[1], a_, L, RNG2.uniform(1.6, 3.0)))
for c in list(CHEMINS):
    ramifier(c, 0.3, 0.06)


# quelques fêlures en arc près du trou entre troncs voisins (peu de cellules : la référence est surtout radiale)
def arc(p1, p2, L, w):
    m = (p1 + p2) / 2
    n_ = m / max(1e-6, np.linalg.norm(m))
    ctl = m + n_ * 0.16 * np.linalg.norm(p2 - p1)
    u = np.linspace(0, 1, max(4, int(np.linalg.norm(p2 - p1) * 1.25 / DS)))[:, None]
    P = (1 - u) ** 2 * p1 + 2 * u * (1 - u) * ctl + u ** 2 * p2
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    W = w * (1 - 0.35 * np.sin(math.pi * s / s[-1])) * (1.0 + onde_lisse(s, RNG, (9.0,), 0.1))
    A = np.arctan2(np.gradient(P[:, 1]), np.gradient(P[:, 0]))
    CHEMINS.append({"P": P, "W": W, "L": L + s, "A": A, "rang": 2})


for Lr, wr in ((24.0, 0.56), (34.0, 0.5), (46.0, 0.46)):
    for k in range(len(TRONCS)):
        a1, c1 = TRONCS[k]
        a2, c2 = TRONCS[(k + 1) % len(TRONCS)]
        if (a2 - a1) % (2 * math.pi) > 0.85 or RNG.random() > 0.3:
            continue
        p1 = next((p for p, L in c1 if L >= Lr * RNG.uniform(0.9, 1.1)), None)
        p2 = next((p for p, L in c2 if L >= Lr * RNG.uniform(0.9, 1.1)), None)
        if p1 is not None and p2 is not None:
            arc(p1, p2, Lr, wr)
# fêlures isolées loin du trou (elles ne partent pas toutes du centre) : deux moitiés depuis leur milieu
for _ in range(7):
    th, rr = RNG.uniform(0, 2 * math.pi), RNG.uniform(0.4, 0.82)
    p0 = np.array((rr * XMAX * math.cos(th), rr * (BY1 - BY0) / 2 * math.sin(th)))
    if dans(p0, 4):
        L0 = float(np.linalg.norm(p0))
        a = th + RNG.uniform(-1.0, 1.0)
        for a_, lg in ((a, RNG.uniform(5, 13)), (a + math.pi, RNG.uniform(4, 10))):
            c = chemin_lisse(p0, a_, lg, 0.55, L0, 2, lam=3.0, ondul=0.03, w_debut=0.3)
            ramifier(c, 0.12, 0.0)
print("fissures :", len(CHEMINS), "chemins lisses, longueur totale", round(sum(len(c["P"]) for c in CHEMINS) * DS), "px")


# v6 (retour en jeu de la v5 : « fissures très pixel et non lisses ») : plus de fissures peintes. Les fissures de la v5
# étaient des lignes de 1 à 2 texels (0,63 px chacun) sur des tuiles cutout, en escalier, et leur lueur add_ floue
# n'avait qu'un texel pour 5 px (gros carrés violets) : le jeu échantillonne les textures au plus proche, un flou en
# basse résolution s'y voit en blocs. Chaque fissure est maintenant une suite de cubes fins tournés dans le plan (bords
# géométriques nets à toute distance, voir « fissures en géométrie » plus bas).
FW, FH = int((BX1 - BX0) * TP), int((BY1 - BY0) * TP)


# --- trou : contour en éclats aigus + esquilles détachées
def contour_trou(f, seed):
    rng = np.random.default_rng(seed)
    n = 34
    pts = []
    for i in range(n):
        th = 2 * math.pi * (i + rng.uniform(-0.3, 0.3)) / n
        r = 1.0 + rng.uniform(-0.13, 0.08)
        if i % 2:
            r *= rng.uniform(0.84, 0.93)                  # creux entre deux éclats (v4 : moins hérissé)
        elif rng.random() < 0.15:
            r *= rng.uniform(1.05, 1.13)                  # longue pointe
        pts.append((f * RX * r * math.cos(th), min(YHAUT - YC - 0.6, f * RY * r * math.sin(th) + (0.6 * f if math.sin(th) < 0 else 0))))
    esq = []
    for i in range(int(3 + 3 * f)):
        th = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(1.12, 1.32)
        c = np.array((f * RX * r * math.cos(th), min(YHAUT - YC - 2.0, f * RY * r * math.sin(th))))
        s_ = rng.uniform(0.5, 1.2) * (0.6 + 0.4 * f)
        a0 = rng.uniform(0, 2 * math.pi)
        esq.append([tuple(c + s_ * np.array((math.cos(a0 + j * 2.1 + rng.uniform(-0.3, 0.3)), math.sin(a0 + j * 2.1)))) for j in range(3)])
    return pts, esq


def trou_tex(f, seed, tpx=4):
    """v4 : une seule image pour les 3 paliers (plaques à l'échelle f). Profondeur peinte (le cam_ n'a pas de
    parallaxe) : marche plus claire près du bord, deux couches de noir en retrait, liseré violet sombre sur le bord
    intérieur (_e), braises violettes éparses au fond."""
    pts, esq = contour_trou(f, seed)
    ext = 1.45 * f
    hw, hh = RX * ext, RY * ext
    W, H = int(2 * hw * tpx), int(2 * hh * tpx)
    k = tpx * SS
    conv = lambda p: ((p[0] + hw) * k, (hh - p[1]) * k)

    def masque(ech, avec_esq=False, flou=0.0):
        im_ = Image.new("L", (W * SS, H * SS), 0)
        d_ = ImageDraw.Draw(im_)
        d_.polygon([conv((p[0] * ech, p[1] * ech)) for p in pts], fill=255)
        if avec_esq:
            for tri in esq:
                d_.polygon([conv(p) for p in tri], fill=255)
        if flou:
            im_ = im_.filter(ImageFilter.GaussianBlur(flou * k))
        return np.asarray(im_, np.float32) / 255

    al = masque(1.0, True) * 255
    bord = np.clip((1 - masque(1.0, flou=0.55)) * 2.4, 0, 1) * (al > 0)        # bande intérieure près du contour
    m2, m3 = masque(0.74, flou=1.6), masque(0.46, flou=2.2)
    rng = np.random.default_rng(seed + 1)
    u, v = grille(W, H)
    n = bruit2d(u.shape[1], u.shape[0], rng, 7)
    rgb = mix((11, 4, 17), (6, 2, 10), m2)                         # marche du bord
    rgb = mix(rgb, (2, 1, 4), m3)                                  # fond
    rgb = mix(rgb, (24, 9, 38), n * 0.5 * (m2 - m3).clip(0, 1))    # brume entre les deux couches
    rgb = mix(rgb, (58, 18, 90), bord ** 1.6 * 0.7)               # lueur du bord intérieur
    emb = Image.new("L", (W * SS, H * SS), 0)
    de = ImageDraw.Draw(emb)
    for _ in range(46):                                            # braises éparses dans le noir
        th, rr = rng.uniform(0, 2 * math.pi), math.sqrt(rng.uniform(0.04, 0.6))
        c = conv((RX * f * rr * math.cos(th), RY * f * rr * math.sin(th)))
        ra = rng.uniform(0.16, 0.34) * k
        de.ellipse([c[0] - ra, c[1] - ra, c[0] + ra, c[1] + ra], fill=int(rng.uniform(150, 255)))
    emb = np.asarray(emb, np.float32) / 255
    rgb = mix(rgb, (110, 46, 160), emb * 0.65)
    im = assembler(rgb, al, W, H, opaque=True)
    e = np.zeros_like(im)
    e_rgb = np.stack([lanczos(np.asarray(c_) * 255, W, H) / 255 for c_ in (bord ** 1.6, emb)], -1)
    e[..., 0] = np.clip(70 * e_rgb[..., 0] + 130 * e_rgb[..., 1], 0, 255)
    e[..., 1] = np.clip(20 * e_rgb[..., 0] + 50 * e_rgb[..., 1], 0, 255)
    e[..., 2] = np.clip(112 * e_rgb[..., 0] + 190 * e_rgb[..., 1], 0, 255)
    e[..., 3] = 255
    e[im[..., 3] == 0, :3] = 0
    ys, xs = np.nonzero(im[..., 3])                          # recadré sur le contenu (la boîte compte dans l'extension)
    a0, a1, b0, b1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    boite = (a0 / tpx - hw, hh - b1 / tpx, a1 / tpx - hw, hh - b0 / tpx)      # x0, y0, x1, y1 en px
    return im[b0:b1, a0:a1].copy(), e[b0:b1, a0:a1].copy(), boite


def eclat_tex(seed, N=24):
    """Éclat de ciel : triangle irrégulier, face bleu ciel claire, arête blanche, bord intérieur sombre."""
    rng = np.random.default_rng(seed)
    img = Image.new("L", (N * SS, N * SS), 0)
    d = ImageDraw.Draw(img)
    pts = [(rng.uniform(0.05, 0.4) * N * SS, rng.uniform(0.05, 0.3) * N * SS), (rng.uniform(0.6, 0.95) * N * SS, rng.uniform(0.1, 0.45) * N * SS),
           (rng.uniform(0.3, 0.7) * N * SS, rng.uniform(0.75, 0.97) * N * SS)]
    d.polygon(pts, fill=255)
    u, v = grille(N, N)
    rgb = mix((150, 205, 240), (92, 150, 205), v + 0.25 * u)
    rgb = mix(rgb, (235, 248, 255), smooth(1 - v / 0.25) * 0.7)
    dos = mix((40, 52, 70), (20, 24, 34), v)
    al = np.asarray(img, np.float32)
    return assembler(rgb, al, N, N, opaque=True), assembler(dos, al, N, N, opaque=True)


EYE_X, EYE_Y = 6.6, 2.6
LW_, LH_ = 15.0, 10.0          # v6 : une plaque par œil (centrée sur l'œil)
LUEUR_MAX = 150                # amande (plaque de fond) ; + halo de pulsation (HALO_MAX) : 230, + 22 du tourbillon au plus (le halo du bord ne les touche pas)
HALO_MAX = 80                  # plaque de pulsation : halo flou seul (pas de seconde amande nette, qui se lirait comme une pupille)
OA, OH, OB = 4.3, 0.7, 1.5     # demi-longueur, paupière haute (presque droite), paupière basse (arrondie), px
OEIL_INC = 13.0                # degrés : coin intérieur plus bas que l'extérieur (regard menaçant)


def lueur_oeil_tex(tpx=6, halo=False):
    """v6 (« plus deux yeux distincts » après l'ovale de la v5 ; avant, en v4, « pas de vrais yeux ») : une amande de
    lumière rouge vive (œil droit ; le gauche en miroir d'UV), sans iris, pupille, fente ni cœur blanc, bord anticrénelé
    (sur-échantillonnage × 4), qui bave en halo flou autour ; le noir du trou reste visible entre les deux."""
    W, H = int(LW_ * tpx), int(LH_ * tpx)
    u, v = grille(W, H)
    x, y = (u - 0.5) * LW_, (0.5 - v) * LH_
    a = math.radians(OEIL_INC)
    xr, yr = x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)
    s_ = np.clip(1 - (xr / OA) ** 2, 0, None)
    s_ = s_ * np.where(xr > 0, 1.0, np.clip(1 - 0.25 * (xr / OA) ** 2, 0, 1))            # coin intérieur plus effilé
    dedans = ((yr < OH * s_ ** 0.45) & (yr > -OB * s_ ** 0.7)).astype(np.float32)
    m = dedans.reshape(H, SS, W, SS).mean(axis=(1, 3))                                     # bord anticrénelé
    mi = Image.fromarray((m * 255).astype(np.uint8))
    h1 = np.asarray(mi.filter(ImageFilter.GaussianBlur(0.9 * tpx)), np.float32) / 255
    h2 = np.asarray(mi.filter(ImageFilter.GaussianBlur(2.0 * tpx)), np.float32) / 255
    xs, ys = (np.arange(W) + 0.5) / W - 0.5, 0.5 - (np.arange(H) + 0.5) / H
    X, Y = np.meshgrid(xs * LW_, ys * LH_)
    bord = smooth(np.clip(1 - (X / (LW_ / 2)) ** 2 - (Y / (LH_ / 2)) ** 2, 0, 1) / 0.35)
    if halo:
        g = np.clip(0.75 * h1 / max(h1.max(), 1e-6) + 0.35 * h2 / max(h2.max(), 1e-6), 0, 1) * bord
        mx = HALO_MAX
    else:
        g = np.clip(m + 0.5 * h1 * (1 - m) + 0.2 * h2 * (1 - m), 0, 1) * bord
        mx = LUEUR_MAX
    rgb = np.stack([mx * g, 0.13 * mx * g ** 2, 0.05 * mx * g ** 2.5], -1)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = np.clip(rgb, 0, 255)
    a_ = arr[..., 0] > 4
    arr[..., 3] = a_ * 255
    arr[~a_, :3] = 0
    return arr


def bord_eclat_tex(seed, W=24, H=40):
    """Éclat épais du bord du trou : pointe en haut (vers le centre, recourbée dans le noir), base large en bas ;
    face bleu ciel, arête blanche d'un côté (tranche de verre), fêlure sombre ; dos sombre."""
    rng = np.random.default_rng(seed)
    img = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(img)
    xt = rng.uniform(0.3, 0.7)
    pts = [(rng.uniform(0.0, 0.12), 1.0), (rng.uniform(0.35, 0.6), rng.uniform(0.9, 1.0)), (rng.uniform(0.88, 1.0), 1.0),
           (rng.uniform(0.72, 0.9), rng.uniform(0.45, 0.6)), (xt, 0.02), (rng.uniform(0.08, 0.26), rng.uniform(0.4, 0.62))]
    d.polygon([(px * W * SS, py * H * SS) for px, py in pts], fill=255)
    u, v = grille(W, H)
    rgb = mix((168, 214, 244), (96, 150, 202), v * 0.5 + 0.5 * (1 - v) * 0.6)
    arete = np.abs(u - (xt + (0.06 - xt) * v)) < 0.11           # long bord gauche : tranche claire
    rgb = mix(rgb, (240, 250, 255), arete * 0.9)
    rgb = mix(rgb, (30, 50, 80), smooth(1 - v / 0.22) * 0.7)       # pointe plongée dans l'ombre du trou
    al = np.asarray(img, np.float32)
    dos = mix((44, 58, 80), (16, 18, 28), 1 - v)
    return assembler(rgb, al, W, H, opaque=True), assembler(dos, al, W, H, opaque=True)


def tourbillon_tex(N=72):
    """Poussière et braises violettes en spirale au fond du vide (add_, tourne lentement) ; rien au centre (yeux)."""
    u, v = grille(N, N)
    x, y = (u - 0.5) * 2, (v - 0.5) * 2
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    bras_ = 0.5 + 0.5 * np.cos(2 * (th - 2.6 * np.log(r + 0.05)))
    rng = np.random.default_rng(31)
    n = bruit2d(u.shape[1], u.shape[0], rng, 10)
    g = bras_ ** 3 * (0.4 + 0.6 * n) * smooth((r - 0.42) / 0.2) * smooth((1 - r) / 0.18)
    rgb = np.stack([22 * g, 7 * g, 58 * g], -1)
    return additif(rgb, N, N, 1.0)


def halo_trou_tex(tpx=1.0):
    """Lueur add_ violette sombre qui borde le trou (dedans et un peu dehors) : de nuit, le trou a un contour."""
    pts, esq = contour_trou(1.0, 300)
    hw, hh = RX * 1.5, RY * 1.5
    W, H = int(2 * hw * tpx * 2), int(2 * hh * tpx * 2)
    k = W / (2 * hw)
    im_ = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im_).polygon([((p[0] + hw) * k, (hh - p[1]) * k) for p in pts], fill=255)
    a = np.asarray(im_.filter(ImageFilter.GaussianBlur(1.6 * k)), np.float32) / 255
    b = np.asarray(im_.filter(ImageFilter.GaussianBlur(4.0 * k)), np.float32) / 255
    g = np.clip(1 - np.abs(a - 0.5) * 2, 0, 1) ** 1.2 * 0.9 + np.clip(b * (1 - a) * 1.4, 0, 1) * 0.1
    rgb = np.stack([40 * g, 12 * g, 72 * g], -1)
    out = additif(rgb, W, H, 1.0)
    return np.array(Image.fromarray(out).resize((W // 2, H // 2), Image.BILINEAR))


def part_tex(rgb0, rgb1, seed, N=8):
    rng = np.random.default_rng(seed)
    u, v = grille(N, N)
    r = np.hypot(u - 0.5, (v - 0.5) * 1.3) * 2 + 0.35 * bruit2d(u.shape[1], u.shape[0], rng, 4)
    return assembler(mix(rgb1, rgb0, smooth(1 - r)), np.where(r < 0.95, 255.0, 0), N, N, opaque=True)


# ------------------------------------------------------------------ atlas
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_A = []


def a_poser(nom, im, e=None):
    _A.append((nom, im, e))


def ranger(pas=2):
    n = TEX // pas
    occ = np.zeros((n, n), bool)
    for nom, im, e in sorted(_A, key=lambda p: -p[1].shape[0] * p[1].shape[1]):
        h, w = im.shape[:2]
        gh, gw = -(-h // pas), -(-w // pas)
        place = None
        libre = ~occ
        for gy in range(n - gh + 1):
            ligne = libre[gy:gy + gh].all(axis=0)
            if not ligne.any():
                continue
            run = 0
            for gx in range(n):
                run = run + 1 if ligne[gx] else 0
                if run >= gw:
                    place = (gy, gx - gw + 1)
                    break
            if place:
                break
        assert place is not None, f"atlas plein : {nom}"
        gy, gx = place
        occ[max(0, gy - 1):gy + gh + 1, max(0, gx - 1):gx + gw + 1] = True
        y, x = gy * pas, gx * pas
        tex[y:y + h, x:x + w] = im
        if e is not None:
            tex_e[y:y + h, x:x + w] = e
        UV[nom] = (x, y, x + w, y + h)
    print(f"atlas : {occ.mean() * 100:.0f} % occupé")


# --- fissures en géométrie (v6, tracé lisse v7) : chaque chemin lisse est coupé au bord du trou (dedans : fissures à
# part, sans arête claire, cachées par le trou qui s'ouvre), rééchantillonné en segments courts (corde ≤ SEG_MAX px,
# écart à la courbe ≤ SEG_ECART px : angle entre segments voisins ≤ ~6°), un cube fin par segment ; segments groupés
# en « pièces » (≤ PIECE_MAX px, presque droites) qui poussent par l'échelle le long de leur corde (propagation fluide).
_pts_c, _ = contour_trou(1.0, 300)
_mc = Image.new("L", (FW, FH), 0)
ImageDraw.Draw(_mc).polygon([((x * 0.98 - BX0) * TP, (BY1 - y * 0.98) * TP) for x, y in _pts_c], fill=255)
DANS_TROU = np.asarray(_mc) > 0
_ac = np.array([math.atan2(y, x) for x, y in _pts_c])
_rc = np.array([math.hypot(x, y) for x, y in _pts_c])
_o = np.argsort(_ac)
_ac, _rc = _ac[_o], _rc[_o]


def dans_trou(x, y):
    i, j = int((BY1 - y) * TP), int((x - BX0) * TP)
    return 0 <= i < FH and 0 <= j < FW and bool(DANS_TROU[i, j])


def r_trou(x, y):
    """Échelle du trou (f) à partir de laquelle le point (x, y) est dedans."""
    rc = np.interp(math.atan2(y, x), _ac, _rc, period=2 * math.pi)
    return math.hypot(x, y) / (0.98 * rc)


SEG_MAX, SEG_ECART, PIECE_MAX, PIECE_ECART = 1.15, 0.012, 7.0, 0.3


def reechantillonner(P, W):
    """Indices gardés : corde ≤ SEG_MAX, écart des points intermédiaires ≤ SEG_ECART, largeur presque linéaire."""
    idx, i, n = [0], 0, len(P)
    while i < n - 1:
        j = i + 1
        while j + 1 < n:
            c = P[j + 1] - P[i]
            lc = float(np.linalg.norm(c))
            if lc > SEG_MAX:
                break
            d = c / lc
            rel = P[i + 1:j + 1] - P[i]
            if np.abs(rel[:, 0] * d[1] - rel[:, 1] * d[0]).max() > SEG_ECART:
                break
            u = (rel @ d) / lc
            if np.abs(W[i + 1:j + 1] - (W[i] * (1 - u) + W[j + 1] * u)).max() > 0.03:
                break
            j += 1
        idx.append(j)
        i = j
    return idx


CHAINES = []        # (centre ?, P (n, 2), W (n,), L (n,), n° de chemin)
for nc, c in enumerate(CHEMINS):
    P, W, L = c["P"], c["W"], c["L"]
    cls = np.array([dans_trou(x, y) for x, y in P])
    debut = 0
    for i in range(1, len(P) + 1):
        if i == len(P) or cls[i] != cls[debut]:
            if i - debut >= 2:
                sl = slice(debut, i + 1 if i < len(P) else i)      # recouvre le point de coupe (pas de trou au bord)
                CHAINES.append((bool(cls[debut]), P[sl], W[sl], L[sl], nc))
            debut = i

PIECES = []         # dict(centre, pivot, theta (deg), segs [(x0, y0, x1, y1, w0, w1)], L0, L1, chaine, rmax)
NSEG = 0
for nch, (cls, P, W, L, nc) in enumerate(CHAINES):
    k = reechantillonner(P, W)
    V, VW, VL = P[k], W[k], L[k]
    NSEG += len(V) - 1
    # pièces : suites de segments presque droites
    i = 0
    while i < len(V) - 1:
        j = i + 1
        while j + 1 < len(V):
            c = V[j + 1] - V[i]
            lc = float(np.linalg.norm(c))
            if lc > PIECE_MAX:
                break
            d = c / lc
            rel = V[i + 1:j + 1] - V[i]
            if np.abs(rel[:, 0] * d[1] - rel[:, 1] * d[0]).max() > PIECE_ECART:
                break
            j += 1
        d = V[j] - V[i]
        PIECES.append({"centre": cls, "pivot": V[i].copy(), "theta": math.degrees(math.atan2(d[1], d[0])),
                       "segs": [(*V[m], *V[m + 1], VW[m], VW[m + 1]) for m in range(i, j)],
                       "L0": float(VL[i]), "L1": float(VL[j]), "chaine": nch, "chemin": nc,
                       "rmax": max(r_trou(x, y) for x, y in V[i:j + 1])})
        i = j
print("fissures :", len(CHAINES), "chaînes ;", NSEG, "segments ;", len(PIECES), "pièces")



def profil_tex():
    """Profil en travers d'une fissure (v le long de la largeur) : 24 rangs d'arête claire (verre qui accroche la
    lumière), puis 24 rangs de cœur noir à fil violet très sombre ; + profil des fissures dans le trou ; + lueur add_."""
    H = 48
    t = np.abs(np.arange(24) + 0.5 - 12) / 12                     # 0 au milieu du cœur, 1 au bord
    coeur = smooth(1 - t / 0.42)
    im = np.zeros((H, 4, 4), np.uint8)
    e = np.zeros((H, 4, 4), np.uint8)
    hl = mix((178, 200, 222), (238, 246, 252), smooth(np.arange(24) / 23.0))
    im[:24, :, :3] = hl[:, None, :]
    im[24:, :, :3] = mix((5, 3, 8), (34, 12, 52), 0.85 * coeur)[:, None, :]
    im[..., 3] = 255
    e[24:, :, 0], e[24:, :, 1], e[24:, :, 2] = (40 * coeur)[:, None], (12 * coeur)[:, None], (64 * coeur)[:, None]
    e[..., 3] = 255
    ic = np.zeros((24, 4, 4), np.uint8)
    ic[..., :3] = mix((6, 3, 9), (16, 6, 24), 0.8 * coeur)[:, None, :]
    ic[..., 3] = 255
    ec = e[24:].copy()
    g = np.exp(-(((np.arange(32) + 0.5 - 16) / 16) / 0.45) ** 2 / 2)
    g = np.clip((g - 0.03) / 0.97, 0, 1)
    lu = np.zeros((32, 4, 4), np.uint8)
    lu[..., 0], lu[..., 1], lu[..., 2] = (36 * g)[:, None], (11 * g)[:, None], (64 * g)[:, None]
    lu[..., 3] = np.where(lu[..., :3].max(axis=2) > 2, 255, 0)
    lu[lu[..., 3] == 0, :3] = 0
    return im, e, ic, ec, lu


_fim, _fe, _fic, _fec, _flu = profil_tex()
a_poser("fissure", _fim, _fe)
a_poser("fissure_trou", _fic, _fec)
a_poser("lueur_fissure", _flu)
im, e, TROU_BOITE = trou_tex(1.0, 300)            # v4 : une image pour les 3 paliers (plaques à l'échelle f)
a_poser("trou", im, e)
TROU_DIM = [tuple(f * c for c in TROU_BOITE) for f in TROUS]
for i in range(3):
    fa, do = eclat_tex(60 + i)
    a_poser(f"eclat{i}", fa)
    a_poser(f"eclat{i}d", do)
for i in range(4):
    fa, do = bord_eclat_tex(500 + i)
    a_poser(f"bord{i}", fa)
    a_poser(f"bord{i}d", do)
a_poser("tourbillon", tourbillon_tex())
a_poser("halo_trou", halo_trou_tex())
a_poser("lueur_oeil", lueur_oeil_tex())
a_poser("lueur_oeil_halo", lueur_oeil_tex(halo=True))
# os : longueur le long de v (faces up/down), copie transposée (faces east/west, longueur le long de u), bouts
OS_E = uni((12, 8, 16), 4)
for nom_, pal_, bouts_, sd in (("osl", ((50, 42, 40), (228, 216, 194)), 0.68, 1),
                               ("gri", ((150, 142, 128), (250, 246, 236)), 0.0, 3)):
    lo = os_long_tex(16, 48, pal_, sd, 2 if nom_ != "gri" else 0, bouts_)
    a_poser(nom_, lo, np.broadcast_to(OS_E[:1, :1], lo.shape).copy())
    a_poser(nom_ + "_t", lo.transpose(1, 0, 2).copy(), np.broadcast_to(OS_E[:1, :1], (lo.shape[1], lo.shape[0], 4)).copy())
    bo = os_bout_tex(16, (tuple(int(c * 1.25) for c in pal_[0]), pal_[1]))
    a_poser(nom_ + "_b", bo, np.broadcast_to(OS_E[:1, :1], bo.shape).copy())
a_poser("ombre", ombre_tex(64))
a_poser("onde", onde_tex(96))
a_poser("p_eclat", part_tex((200, 232, 250), (96, 150, 205), 5))
a_poser("p_poussiere", part_tex((40, 34, 46), (6, 4, 8), 6))
ranger()


_b64 = []
for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(fn, optimize=True)
    _buf = io.BytesIO()
    im_.save(_buf, "PNG", optimize=True)
    _b64.append("data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode())
tex_b64, tex_e_b64 = _b64


def coin(nom, k=3):
    x0, y0, _, _ = UV[nom]
    return (x0 + 1, y0 + 1, x0 + 1 + k, y0 + 1 + k)


# ------------------------------------------------------------------ géométrie
def nuid():
    return str(_uuid.uuid4())


class G:
    tous = []

    def __init__(self, nom, origin, parent=None, rotation=None):
        assert len(nom) <= 64
        self.nom, self.origin, self.uuid, self.enfants = nom, [float(v) for v in origin], nuid(), []
        self.rotation = [(float(v) + 180) % 360 - 180 for v in rotation] if rotation is not None else None
        self.ciel = bool(parent and (parent.ciel or parent.nom.startswith("cam_ciel")))
        if parent is not None:
            parent.enfants.append(self)
        G.tous.append(self)

    def json(self):
        d = {"name": self.nom, "origin": [round(v, 3) for v in self.origin], "uuid": self.uuid,
             "children": [c.json() if isinstance(c, G) else c for c in self.enfants]}
        if self.rotation and any(abs(r) > 1e-6 for r in self.rotation):
            d["rotation"] = [round(r, 3) for r in self.rotation]
        return d


elements = []
DU_CIEL = set()


def r3(v):
    return [float(a) for a in v]


def inv(uv):
    return [uv[2], uv[1], uv[0], uv[3]]


def ajouter(g, e):
    elements.append(e)
    g.enfants.append(e["uuid"])
    if g.ciel or g.nom.startswith("cam_ciel"):
        DU_CIEL.add(e["uuid"])
    return e


def cube(g, nom, a, b, faces, rot_=None, origine=None):
    a, b = np.asarray(a, float), np.asarray(b, float)
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": r3(np.minimum(a, b)), "to": r3(np.maximum(a, b)),
         "origin": r3((a + b) / 2 if origine is None else origine), "box_uv": False, "faces": faces}
    if rot_ is not None and any(rot_):
        e["rotation"] = r3(rot_)
    return ajouter(g, e)


def plaque(g, nom, c, w, h, faces, ep=0.3, horiz=False, rot_=None, origine=None):
    c = np.asarray(c, float)
    d = np.array((w / 2, ep / 2, h / 2)) if horiz else np.array((w / 2, h / 2, ep / 2))
    return cube(g, nom, c - d, c + d, faces, rot_, c if origine is None else origine)


def F(uv):
    return {"uv": [round(float(x), 3) for x in uv], "texture": 0}


def six(uv):
    return {k: F(uv) for k in ("north", "south", "east", "west", "up", "down")}


LONGS = {n: (n, n + "_t", n + "_b") for n in ("osl", "gri")}


def habiller(uv):
    """Faces d'un os le long de +Z : image longue sur up/down (v le long de l'os), transposée sur east/west, bout sur
    north/south ; un nom en _b : la même image partout (têtes articulaires) ; sinon un coin uni."""
    if uv in LONGS:
        lo, tr, bo = LONGS[uv]
        return {"north": F(UV[bo]), "south": F(UV[bo]), "east": F(UV[tr]), "west": F(UV[tr]), "up": F(UV[lo]), "down": F(UV[lo])}
    if uv.endswith("_b"):
        return six(UV[uv])
    return six(coin(uv))


def os_le_long(g, nom, x, y, z0, z1, w, uv="osl", octo=True, wy=None):
    """Os le long de +Z du groupe, de z0 à z1, section w × wy (+ copie roulée de 45° : section octogonale)."""
    wy = w if wy is None else wy
    cube(g, nom, (x - w / 2, y - wy / 2, z0), (x + w / 2, y + wy / 2, z1), habiller(uv))
    if octo and z1 - z0 > 0.5:
        w2 = min(w, wy) * 0.9
        cube(g, nom + "_o", (x - w2 / 2, y - w2 / 2, z0 + 0.1), (x + w2 / 2, y + w2 / 2, z1 - 0.1), habiller(uv),
             rot_=(0, 0, 45), origine=(x, y, (z0 + z1) / 2))


def noeud(g, nom, p, k, uv="osl_b"):
    x, y, z = p
    cube(g, nom, (x - k / 2, y - k / 2, z - k / 2), (x + k / 2, y + k / 2, z + k / 2), habiller(uv))
    k2 = k * 0.88
    cube(g, nom + "_o", (x - k2 / 2, y - k2 / 2, z - k2 / 2 + 0.1), (x + k2 / 2, y + k2 / 2, z + k2 / 2 - 0.1), habiller(uv),
         rot_=(0, 0, 45), origine=p)


def rot(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def euler_de(R):
    """Angles (rx, ry, rz) tels que rot(rx, ry, rz) = R (R = Rz·Ry·Rx), contrôle de reconstruction."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    rx = math.atan2(R[2, 1], R[2, 2])
    rz = math.atan2(R[1, 0], R[0, 0])
    ang = tuple(math.degrees(a) for a in (rx, ry, rz))
    assert np.allclose(rot(*ang), R, atol=1e-5), "euler_de : reconstruction fausse"
    return ang


O = (0, 0, 0)
C0 = (0.0, YC, 0.0)                 # centre de construction du ciel (avant échelle et décalage)
C_CIEL = (0.0, YC, ZC)              # centre du trou dans le monde : pivot du cam_ et épaule du bras
EFFET = G("effet", O)
JOUEUR = G("joueur", O)
CIEL = G("ciel", C_CIEL, EFFET)
CAMY = G("cam_ciel", C_CIEL, CIEL)
SECOUSSE = G("secousse", C0, CAMY)       # à-coups des fissures

# --- fissures (v6, lisses v7) : un cube fin par segment court, tourné dans le plan (lacet autour de Z), prolongé de sa
# demi-largeur aux deux bouts (jointures recouvertes) ; arête claire d'un même côté le long de toute une chaîne (celui
# qui regarde le plus la lumière LUM : pas de saut d'un bord à l'autre dans une courbe), largeur de l'arête continue.
# Pièces (v7) : un groupe par pièce, pivot au début de la pièce, tourné selon sa corde ; ses cubes sont posés dans le
# repère non tourné de la pièce, si bien que l'échelle x du groupe la fait pousser le long de sa corde depuis son début
# (largeur inchangée). Lueur add_ violette : un sous-groupe add_ par pièce, un cube large par paire de segments, longueur
# exacte (pas de recouvrement additif aux jointures), profil flou en travers.
LUM = np.array((-0.6, 0.8))
GL = 1.1            # débord de la lueur de chaque côté (px)
_cote = {}
for p_ in PIECES:
    for x0, y0, x1, y1, w0, w1 in p_["segs"]:
        _cote[p_["chaine"]] = _cote.get(p_["chaine"], 0.0) + (-(y1 - y0) * LUM[0] + (x1 - x0) * LUM[1])


def _loc(o, th, q):
    """Point q exprimé dans le repère non tourné d'une pièce de pivot o et d'angle th (degrés)."""
    a = math.radians(-th)
    d = np.asarray(q, float) - o
    return o + np.array((math.cos(a) * d[0] - math.sin(a) * d[1], math.sin(a) * d[0] + math.cos(a) * d[1]))


def poser_piece(g, gl, nom, p_, z, zl):
    o, th, centre = p_["pivot"], p_["theta"], p_["centre"]
    retourne = _cote.get(p_["chaine"], 0.0) < 0
    x_, y_, wu, hu = UV["fissure_trou"] if centre else UV["fissure"]
    segs = p_["segs"]
    for m, (x0, y0, x1, y1, w0, w1) in enumerate(segs):
        a0, a1 = _loc(o, th, (x0, y0)), _loc(o, th, (x1, y1))
        d = a1 - a0
        lg = float(np.linalg.norm(d))
        if lg < 1e-4:
            continue
        phi = math.atan2(d[1], d[0]) + (math.pi if retourne else 0.0)
        nloc = np.array((-math.sin(phi), math.cos(phi)))
        w = (w0 + w1) / 2
        if centre:
            hl, v0 = 0.0, y_
        else:
            hl = max(0.3 * w, 0.42 * min(1.0, max(0.0, (w - 0.3) / 0.3)))
            v0 = y_ + 24 - 24 * hl / w if hl > 1e-3 else y_ + 24
        c = (a0 + a1) / 2 + nloc * hl / 2
        L_ = lg + w
        zz = z + 0.012 * (m % 2)
        cube(g, f"{nom}_{m}", (c[0] - L_ / 2, YC + c[1] - (w + hl) / 2, zz - 0.02), (c[0] + L_ / 2, YC + c[1] + (w + hl) / 2, zz + 0.02),
             {"south": F((x_ + 1, v0, x_ + 3, hu))}, rot_=(0, 0, (math.degrees(phi) + 180) % 360 - 180), origine=(c[0], YC + c[1], zz))
    if gl is None:
        return
    lx, ly, lu_, lv = UV["lueur_fissure"]
    for m in range(0, len(segs), 2):
        s0, s1 = segs[m], segs[min(m + 1, len(segs) - 1)]
        a0, a1 = _loc(o, th, s0[:2]), _loc(o, th, s1[2:4])
        d = a1 - a0
        lg = float(np.linalg.norm(d))
        if lg < 1e-4:
            continue
        mm = (a0 + a1) / 2
        W_ = (s0[4] + s1[5]) / 2 + 2 * GL
        cube(gl, f"{nom}_l{m // 2}", (mm[0] - lg / 2, YC + mm[1] - W_ / 2, zl - 0.02), (mm[0] + lg / 2, YC + mm[1] + W_ / 2, zl + 0.02),
             {"south": F((lx + 1, ly, lx + 3, lv))}, rot_=(0, 0, math.degrees(math.atan2(d[1], d[0]))), origine=(mm[0], YC + mm[1], zl))


FISS = G("fissures", C0, SECOUSSE)
FISS_C = G("fissures_centre", C0, SECOUSSE)
GPIECES = []        # (groupe, pièce)
for i, p_ in enumerate(PIECES):
    o = p_["pivot"]
    if p_["centre"]:
        g = G(f"fc{i}", (o[0], YC + o[1], ZH + 0.23), FISS_C, rotation=(0, 0, p_["theta"]))
        poser_piece(g, None, f"fc{i}", p_, ZH + 0.23, 0)
    else:
        g = G(f"f{i}", (o[0], YC + o[1], ZH + 0.12), FISS, rotation=(0, 0, p_["theta"]))
        gl = G(f"add_f{i}", (o[0], YC + o[1], ZH - 0.96), g)
        poser_piece(g, gl, f"f{i}", p_, ZH + 0.12 + 0.03 * (p_["chaine"] % 6), ZH - 0.96)
    GPIECES.append((g, p_))
rng_p = np.random.default_rng(77)
GEPAVES = []        # (groupe, longueur parcourue)
for i, (x, y, a, L, t_) in enumerate(EPAVES):
    n_ = np.array((-math.sin(a), math.cos(a))) * rng_p.choice((-1, 1))
    c = np.array((x, y)) + n_ * rng_p.uniform(0.4, 0.9)
    g = G(f"epave_{i + 1}", (c[0], YC + c[1], ZH + 0.5), FISS,
          rotation=(rng_p.uniform(10, 20) * rng_p.choice((-1, 1)), rng_p.uniform(-12, 12), math.degrees(a) + rng_p.uniform(-25, 25)))
    v = i % 3
    plaque(g, f"epave_{i + 1}", (c[0], YC + c[1], ZH + 0.5), t_, t_ * 0.8, {"south": F(UV[f"eclat{v}"]), "north": F(inv(UV[f"eclat{v}d"]))}, ep=0.3)
    GEPAVES.append((g, L))


# --- trou (v7) : une seule plaque (l'image à l'échelle 1) que l'échelle du groupe ouvre en continu (plus de paliers
# qui sautent), tourbillon add_ au fond, lueur add_ du bord, éclats épais du bord à la même échelle
x0, y0, x1, y1 = TROU_DIM[2]
TROU = [G("trou", (0, YC, ZH - 0.74), SECOUSSE)]
plaque(TROU[0], "trou", ((x0 + x1) / 2, YC + (y0 + y1) / 2, ZH - 0.74), x1 - x0, y1 - y0, {"south": F(UV["trou"])}, ep=0.1)
TOURB = G("add_tourbillon", (0, YC, ZH - 0.09), SECOUSSE)
plaque(TOURB, "tourbillon", (0, YC, ZH - 0.09), 1.7 * RY, 1.7 * RY, {"south": F(UV["tourbillon"])}, ep=0.06)
HALO = G("add_halo_trou", (0, YC, ZH + 0.91), SECOUSSE)
plaque(HALO, "halo_trou", (0, YC, ZH + 0.91), 3 * RX, 3 * RY, {"south": F(UV["halo_trou"])}, ep=0.06)
PTS_TROU, _ = contour_trou(1.0, 300)
BORDS = []
rng_b = np.random.default_rng(99)
for i, (f, n) in enumerate(zip(TROUS, (9, 13, 17))):
    gb = G("bord", (0, YC, ZH), SECOUSSE) if i == 2 else None        # v7 : seulement les éclats du trou entier, mis à l'échelle
    if gb is not None:
        BORDS.append(gb)
    pairs = [j for j in range(0, len(PTS_TROU), 2)]
    for m, j in enumerate(pairs[int(q)] for q in np.linspace(0, len(pairs) - 1e-6, n)):
        p = np.array(PTS_TROU[j]) * f
        r_ = p / np.linalg.norm(p)
        Ls, Wb = rng_b.uniform(5.0, 8.5) * f ** 0.6, rng_b.uniform(3.2, 5.0) * f ** 0.6
        tilt = math.radians(rng_b.uniform(24, 42))
        t3 = np.array((-r_[1], r_[0], 0.0))
        d3 = math.cos(tilt) * np.array((-r_[0], -r_[1], 0.0)) + math.sin(tilt) * np.array((0, 0, -1.0))
        Rb = np.column_stack([t3, d3, np.cross(t3, d3)]) @ rot(0, 0, rng_b.uniform(-10, 10))
        o = np.array((p[0] + r_[0] * 1.1, YC + p[1] + r_[1] * 1.1, ZH + 0.32 + 0.09 * (m % 3)))
        if gb is None:
            continue
        g = G(f"eclat_bord{i + 1}_{m + 1}", tuple(o), gb, rotation=euler_de(Rb))
        v = m % 4
        plaque(g, f"eclat_bord{i + 1}_{m + 1}", o + (0, Ls / 2 - 0.4, 0), Wb, Ls, {"south": F(UV[f"bord{v}"]), "north": F(inv(UV[f"bord{v}d"]))}, ep=0.5)

# --- éclats de ciel qui se détachent du bord à chaque palier et tombent
ECLATS = []        # (groupe, palier, angle, rng-params)
rng_e = np.random.default_rng(88)
for i in range(13):
    pal = i % 3
    th = 2 * math.pi * (i / 13) + rng_e.uniform(-0.2, 0.2)
    f = TROUS[pal]
    c = np.array((f * RX * 0.92 * math.cos(th), YC + f * RY * 0.92 * math.sin(th), ZH + 0.25 + 0.05 * (i % 4)))
    s_ = rng_e.uniform(3.4, 5.4) * (0.7 + 0.3 * f)
    g = G(f"eclat_{i + 1}", tuple(c), SECOUSSE, rotation=(0, 0, rng_e.uniform(-180, 180)))
    v = i % 3
    plaque(g, f"eclat_{i + 1}", c, s_, s_, {"south": F(UV[f"eclat{v}"]), "north": F(inv(UV[f"eclat{v}d"]))}, ep=0.3)
    ECLATS.append((g, pal, th, rng_e.uniform(-1, 1, 3), rng_e.uniform(0.85, 1.25)))

# --- esquilles de ciel qui flottent autour du bord et sont aspirées en spirale vers le noir
DEBRIS = []
rng_d = np.random.default_rng(55)
for i in range(10):
    th = 2 * math.pi * i / 10 + rng_d.uniform(-0.25, 0.25)
    r0 = rng_d.uniform(1.12, 1.45)
    c = np.array((RX * r0 * math.cos(th), YC + RY * r0 * math.sin(th), ZH + 1.1 + 0.1 * (i % 3)))
    g = G(f"esquille_{i + 1}", tuple(c), SECOUSSE, rotation=tuple(rng_d.uniform(-60, 60, 3)))
    s_ = rng_d.uniform(1.4, 2.6)
    v = i % 3
    plaque(g, f"esquille_{i + 1}", c, s_, s_ * 0.8, {"south": F(UV[f"eclat{v}"]), "north": F(inv(UV[f"eclat{v}d"]))}, ep=0.3)
    DEBRIS.append((g, th, r0, rng_d.uniform(0.3, 0.6), rng_d.uniform(-1, 1, 3)))

# --- yeux (v6) : deux amandes de lumière rouge, une plaque add_ par œil (pivot au centre de l'œil : la pulsation
# grossit chaque œil sur place, sans les rapprocher), fond + pulsation par œil (amande nette + halo flou qui gonfle aux coups : cumul ≤ LUEUR_MAX + HALO_MAX)
LUEUR, LUEUR2 = [], []
for s_, cote in ((1, "d"), (-1, "g")):
    for liste, nom_, dz, im_ in ((LUEUR, "add_yeux", 1.04, "lueur_oeil"), (LUEUR2, "add_yeux_pulse", 1.26, "lueur_oeil_halo")):
        uv_ = UV[im_] if s_ > 0 else inv(UV[im_])
        c_ = (s_ * EYE_X, YC + EYE_Y, ZH + dz)
        g = G(f"{nom_}_{cote}", c_, CAMY)
        plaque(g, f"lueur_oeil{'_pulse' if dz > 1.1 else ''}_{cote}", c_, LW_, LH_, {"south": F(uv_)}, ep=0.1)
        liste.append(g)


# --- os orientés et main squelettique (anatomie : carpes, métacarpes, phalanges à têtes en double bosse, griffes)
def os_dir(parent, nom, a, b, ws, uv="osl"):
    """Os de a vers b (coordonnées du parent), un groupe orienté ; sections de largeurs ws bout à bout (recouvrement
    0,34 px : faces de bout à ≥ 0,14 px ; largeurs voisines à ≥ 0,24 px d'écart)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    z3 = d / L
    ref = np.array((0, 1.0, 0)) if abs(z3[1]) < 0.9 else np.array((1.0, 0, 0))
    x3 = np.cross(ref, z3)
    x3 /= np.linalg.norm(x3)
    R = np.column_stack([x3, np.cross(z3, x3), z3])
    g = G(nom, tuple(a), parent, rotation=euler_de(R))
    n = len(ws)
    for i, w in enumerate(ws):
        os_le_long(g, f"{nom}_{i + 1}", a[0], a[1], a[2] + i * L / n - (0.34 if i else 0), a[2] + (i + 1) * L / n, w, uv)
    return g


def phalange(g, nom, x, y, z, l, w, uv="osl"):
    """Base renflée, corps plus fin, tête en double bosse (deux condyles)."""
    os_le_long(g, nom + "_b", x, y, z + 0.12, z + 0.12 + 0.32 * l, w * 1.22, uv)
    os_le_long(g, nom + "_m", x, y, z + 0.32 * l - 0.22, z + 0.78 * l + 0.22, w * 0.84, uv)
    for sx in (-1, 1):
        cube(g, f"{nom}_c{'g' if sx < 0 else 'd'}", (x + sx * 0.34 * w - 0.27 * w, y - 0.55 * w, z + 0.72 * l),
             (x + sx * 0.34 * w + 0.27 * w, y + 0.3 * w, z + l - 0.05), habiller(uv + "_b"))


def distale(g, nom, x, y, z, l, w, c, pointe=1.0, uv="osl"):
    """Phalange distale effilée et griffe recourbée vers la paume (+Y), pâle, en trois pièces."""
    os_le_long(g, nom + "_b", x, y, z + 0.12, z + 0.12 + 0.32 * l, w * 1.22, uv)
    os_le_long(g, nom + "_m", x, y, z + 0.32 * l - 0.22, z + l, w * 0.72, uv)
    p = np.array((x, y - 0.12 * w, z + l - 0.05))
    for q, (wx, wy, lq, ang) in enumerate(((0.7, 0.75, 1.2, -6.0), (0.45, 0.55, 1.2, -18.0), (0.22, 0.32, 0.8 + 1.4 * pointe, -32.0))):
        wx, wy, lq = wx * c, wy * c, lq * c
        cube(g, f"{nom}_griffe{q + 1}", (p[0] - wx / 2, p[1] - wy / 2, p[2]), (p[0] + wx / 2, p[1] + wy / 2, p[2] + lq), habiller("gri"),
             rot_=(ang, 0, 0), origine=tuple(p))
        p = p + (lq - 0.15 * c) * np.array((0, -math.sin(math.radians(ang)), math.cos(math.radians(ang))))


DOIGTS_X = [-1.0, -0.36, 0.3, 0.92]       # × demi-largeur de la paume
DOIGTS_S = [0.92, 1.0, 0.95, 0.78]
DOIGTS_FAN = [-15.0, -5.0, 5.0, 15.0]
DOIGTS_FLEX = [0.9, 1.0, 1.08, 1.2]
CARPES = [(-1.6, 0.35, 1.25), (-0.55, 0.3, 1.15), (0.5, 0.4, 1.2), (1.5, 0.3, 1.05),
          (-1.75, 1.35, 1.1), (-0.6, 1.3, 1.3), (0.55, 1.4, 1.2), (1.6, 1.3, 1.15)]


def main(parent, nom, pivot, k=1.0, pouce=1, pointe=1.0, eventail=1.0, uvo="osl"):
    """Poignet au pivot, doigts vers +Z local, flexion (rotation X négative) vers +Y local ; pouce côté x = pouce.
    Renvoie (doigts [[g1, g2, g3]], pouce [g1, g2, g3])."""
    px, py, pz = pivot
    LP = [4.6 * k, 3.3 * k, 2.4 * k]
    WP = [1.7 * k, 1.5 * k, 1.3 * k]
    LM = 6.2 * k
    hw = 3.6 * k
    rng_c = np.random.default_rng(len(nom) * 7 + int(k * 100))
    for j, (cx, cz, sz) in enumerate(CARPES):                      # carpes : deux rangées de petits os noueux
        sz *= k
        yc = py - 0.35 * k + 0.13 * k * j if j < 4 else py + 0.86 * k + 0.13 * k * (j - 4)   # dessus/dessous à ≥ 0,12 k
        cube(parent, f"{nom}_carpe{j + 1}", (px + cx * k - sz / 2, yc - 0.35 * k, pz + cz * k - sz / 2),
             (px + cx * k + sz / 2, yc + 0.35 * k, pz + cz * k + sz / 2), habiller(uvo + "_b"),
             rot_=(0, -25.0 + 7.0 * j + 1.3 * (len(nom) % 3), 0), origine=(px + cx * k, yc, pz + cz * k))
    doigts = []
    for j, (xk, sc, fan) in enumerate(zip(DOIGTS_X, DOIGTS_S, DOIGTS_FAN)):
        xk *= hw * pouce
        fan *= pouce * eventail
        w = 1.09 * k
        os_dir(parent, f"{nom}_mc{j + 1}", (px + 0.45 * xk, py + (j - 1.5) * 0.25 * k, pz + 2.25 * k), (px + xk, py, pz + LM - 0.15), [1.15 * w, 0.8 * w, 1.1 * w], uvo)
        chaine, par, z = [], parent, pz + LM
        for q in range(3):
            g = G(f"{nom}_d{j + 1}_{q + 1}", (px + xk, py, z), par, rotation=(0, fan, 0) if q == 0 else None)
            l = LP[q] * sc
            if q < 2:
                phalange(g, f"{nom}_d{j + 1}_{q + 1}", px + xk, py, z, l, WP[q] * (0.9 + 0.1 * sc), uvo)
            else:
                distale(g, f"{nom}_d{j + 1}_{q + 1}", px + xk, py, z, l, WP[q] * (0.9 + 0.1 * sc), k, pointe, uvo)
            chaine.append(g)
            par, z = g, z + l
        doigts.append(chaine)
    tp = (px + 2.65 * k * pouce, py - 0.75 * k, pz + 1.2 * k)
    pc, par, z = [], parent, tp[2]
    for q, (l, w) in enumerate(((3.6, 1.55), (2.6, 1.4), (1.9, 1.25))):
        g = G(f"{nom}_p{q + 1}", (tp[0], tp[1], z), par, rotation=(0, 40 * pouce, 0) if q == 0 else None)
        if q < 2:
            phalange(g, f"{nom}_p{q + 1}", tp[0], tp[1], z, l * k, w * k, uvo)
        else:
            distale(g, f"{nom}_p{q + 1}", tp[0], tp[1], z, l * k, w * k, k, pointe * 0.8, uvo)
        pc.append(g)
        par, z = g, z + l * k
    return doigts, pc


# --- le grand bras : hors du cam_ (orienté dans le monde, il atteint le joueur sous tous les angles) ; épaule au pivot du
# ciel, que la plaque noire du trou (3,6 × 2,5 = 9 px devant le pivot, face à l'œil) cache depuis tous les points de vue.
# v4 : vraie anatomie (tête et tubercule de l'humérus, épicondyles et condyles du coude, olécrâne, radius et cubitus
# séparés et croisés, carpes, métacarpes, phalanges à têtes renflées, griffes), plus épais et plus contrasté.
S_EP = np.array(C_CIEL)
L1, L2 = 96.0, 88.0
KB = 3.4
BRAS = G("bras", tuple(S_EP), CIEL)                 # échelle : surgit du fond du noir (0,2 → 1) et y rentre
EPAULE = G("bras_epaule", tuple(S_EP), BRAS)
noeud(EPAULE, "bras_tete_humerus", tuple(S_EP), 3.0 * KB)
cube(EPAULE, "bras_tubercule", S_EP + (0.45 * KB, 0.2 * KB, 0.6 * KB), S_EP + (1.85 * KB, 1.3 * KB, 2.3 * KB), habiller("osl_b"), rot_=(0, 18, 0),
     origine=S_EP + (1.15 * KB, 0.85 * KB, 1.45 * KB))
os_dir(EPAULE, "bras_humerus", S_EP + (0, 0, 1.2 * KB), S_EP + (0, 0.1, L1 - 1.0 * KB), [2.15 * KB, 1.8 * KB, 1.5 * KB, 1.72 * KB, 2.05 * KB])
E0 = S_EP + (0, 0, L1)
cube(EPAULE, "bras_epicondyles", E0 + (-1.8 * KB, -0.65 * KB, -2.0 * KB), E0 + (1.8 * KB, 0.65 * KB, -0.4 * KB), habiller("osl_b"))
noeud(EPAULE, "bras_condyle_a", tuple(E0 + (1.2 * KB, 0, -0.5 * KB)), 1.5 * KB)
noeud(EPAULE, "bras_condyle_b", tuple(E0 + (-1.25 * KB, 0.16 * KB, -0.55 * KB)), 1.24 * KB)
COUDE = G("bras_coude", tuple(E0), EPAULE)
noeud(COUDE, "bras_olecrane", tuple(E0 + (0.95 * KB, -0.25 * KB, 0.9 * KB)), 1.65 * KB)
W0 = E0 + (0, 0, L2)
# radius : du côté −x au coude, il croise par-dessus (+y) le cubitus et finit côté +x, large au poignet
noeud(COUDE, "bras_tete_radius", tuple(E0 + (-1.1 * KB, 0.25 * KB, 1.3 * KB)), 1.3 * KB)
RM = E0 + (0.0, 0.85 * KB, 0.5 * L2)
os_dir(COUDE, "bras_radius_a", E0 + (-1.1 * KB, 0.25 * KB, 2.0 * KB), RM, [1.0 * KB, 0.82 * KB, 0.95 * KB])
os_dir(COUDE, "bras_radius_b", RM + (0, 0, -0.5), W0 + (0.9 * KB, 0.3 * KB, -1.6 * KB), [0.78 * KB, 1.12 * KB, 1.45 * KB])
# cubitus : du côté +x (olécrâne) vers −x, sous le radius (−y), fin au poignet
UM = E0 + (0.0, -0.75 * KB, 0.5 * L2)
os_dir(COUDE, "bras_cubitus_a", E0 + (1.05 * KB, -0.25 * KB, 1.6 * KB), UM, [1.45 * KB, 1.15 * KB, 0.9 * KB])
os_dir(COUDE, "bras_cubitus_b", UM + (0, 0, -0.5), W0 + (-0.85 * KB, -0.35 * KB, -1.9 * KB), [0.7 * KB, 0.6 * KB, 0.86 * KB])
POIGNET = G("bras_poignet", tuple(W0), COUDE)
KM = 1.7                                         # main : enserre le torse du joueur
DGB, PCB = main(POIGNET, "bras_main", tuple(W0), k=KM, pouce=1, pointe=0.9)

# --- deux mains qui agrippent le bord du trou (plus petites, doigts posés à plat, peu écartés : pas hérissées)
BORD = []          # (groupe d'avance, direction radiale (x, y), doigts, pouce)
for i, (th, k) in enumerate(((math.radians(148), 0.9), (math.radians(-28), 0.85))):
    r = np.array((math.cos(th), math.sin(th), 0.0))
    W = np.array((0.55 * RX * r[0], YC + 0.55 * RY * r[1], ZH - 1.6))
    zl = r * math.cos(math.radians(22)) + np.array((0, 0, math.sin(math.radians(22))))   # doigts vers l'extérieur, vers l'avant
    yl = np.array((0, 0, -1.0))
    yl = yl - zl * (yl @ zl)
    yl /= np.linalg.norm(yl)
    xl = np.cross(yl, zl)
    Rm = np.column_stack([xl, yl, zl])
    g0 = G(f"main_bord{i + 1}", tuple(W), CAMY, rotation=euler_de(Rm))
    av = G(f"main_bord{i + 1}_avance", tuple(W), g0)
    dg, pc = main(av, f"bord{i + 1}", tuple(W), k=k, pouce=1 if i == 0 else -1, pointe=0.6, eventail=0.35)
    BORD.append((g0, av, dg, pc))


# --- sol
SOL = G("sol", O, EFFET)
TR_OM = G("trans_ombre", O, SOL)
plaque(TR_OM, "ombre", (0, 0.06, 0), 64, 64, {"up": F(UV["ombre"])}, ep=0.1, horiz=True)
A_OMBRE = G("ctrl_alpha", O, TR_OM)
ONDE = G("onde", O, SOL)
TR_O = G("trans_onde", O, ONDE)
plaque(TR_O, "onde", (0, 0.3, 0), 20, 20, {"up": F(UV["onde"])}, ep=0.1, horiz=True)
A_ONDE = G("ctrl_alpha", O, TR_O)

# --- points de départ des particules (+Y du groupe = direction), chacun avec son ctrl_emit
EMG = G("emetteurs", C0, CAMY)
EMS = G("emetteurs_sol", O, EFFET)
EMITS, CTRL = [], {}


def emit(nom, pos, sorte, parent=EMG, rot_=None):
    ge = G(nom, pos, parent, rotation=rot_)
    CTRL.setdefault(sorte, []).append(G("ctrl_emit", pos, ge))
    EMITS.append((ge, sorte))


for k, th in enumerate((0.3, 1.6, 2.9, 4.4)):
    emit("emit_eclat" + (str(k + 1) if k else ""), (RX * math.cos(th), YC + RY * math.sin(th), ZH + 0.8), "eclat", rot_=(-30, 0, 0))
for k, (a, ch) in enumerate(TRONCS[::1][:8]):
    p = next((p for p, L in ch if L >= (24 if k % 2 else 48)), ch[-1][0])
    emit("emit_poussiere" + (str(k + 1) if k else ""), (p[0], YC + p[1], ZH + 1.0), "poussiere")
for x in (-4, 4):
    emit("emit_mc_reverse_portal", (x, YC - 1, ZH + 0.5), "portal")
for th in (0.8, 2.6, 4.0, 5.6):
    emit("emit_mc_ash", (RX * 1.05 * math.cos(th), YC + RY * 1.05 * math.sin(th), ZH + 0.5), "ash")
for x in (-5, 3):
    emit("emit_mc_squid_ink", (x, YC - RY * 0.85, ZH + 0.6), "encre", rot_=(180, 0, 0))
for k in range(6):
    th = math.radians(k * 60 + 30)
    emit("emit_mc_smoke", (7.0 * math.cos(th), 0.4, 7.0 * math.sin(th)), "fumee", parent=EMS, rot_=(40, 90 - k * 60 - 30, 0))
# filaments noirs qui s'échappent du bras (encre de seiche) : deux points sur l'humérus, deux sur l'avant-bras
for par_, pos_ in ((EPAULE, S_EP + (0, 1.2 * KB, 0.32 * L1)), (EPAULE, S_EP + (0, -1.1 * KB, 0.72 * L1)),
                   (COUDE, E0 + (0, 1.3 * KB, 0.3 * L2)), (COUDE, E0 + (0, -1.2 * KB, 0.7 * L2))):
    emit("emit_mc_squid_ink", tuple(pos_), "encre_bras", parent=par_)

# --- particules modélisées (à la racine)
PART_E = G("particle_eclat", O)
plaque(PART_E, "eclat", (0, 0.5, 0), 2.2, 2.2, {"up": F(UV["p_eclat"])}, horiz=True)
PART_P = G("particle_poussiere", (3, 0, 0))
plaque(PART_P, "poussiere", (3, 0.6, 0), 1.4, 1.4, {"up": F(UV["p_poussiere"])}, horiz=True)

outliner = [EFFET.json(), JOUEUR.json(), PART_E.json(), PART_P.json()]
assert len(EMITS) <= 32, len(EMITS)


# ------------------------------------------------------------------ animations
def s(v):
    return v if isinstance(v, str) else str(round(v + 0.0, 4))


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": s(x), "y": s(y), "z": s(z)}], "time": round(t, 4), "interpolation": "linear"}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def ressort(t, t0, amp, f=5.0, k=8.0):
    if t <= t0:
        return 0.0
    u = t - t0
    return amp * math.exp(-k * u) * math.sin(2 * math.pi * f * u)


def u3(v):
    return (v, v, v)


class Anim:
    def __init__(self, nom, L, loop, fps=12, extra=()):
        self.nom, self.L, self.loop, self.A = nom, L, loop, {}
        ts = set(round(i / fps, 4) for i in range(int(L * fps) + 1)) | {round(e, 4) for e in extra if 0 <= e <= L}
        if loop != "loop":
            ts |= {round(L, 4)}
        self.T = sorted(t for t in ts if t <= L)

    def piste(self, g, ch, fn, deroule=False):
        e = ECHELLE_ZONE if (ch == "position" and g.ciel and not g.nom.startswith("ctrl_")) else 1.0
        if not callable(fn):
            keys = [kf(ch, 0, *(v * e for v in fn))]
        else:
            vals = [tuple(v * e for v in fn(t)) for t in self.T]
            if deroule:                                   # angles continus (pas de saut de 360° entre deux clés)
                out = [vals[0]]
                for v in vals[1:]:
                    out.append(tuple(a + 360 * round((p - a) / 360) for a, p in zip(v, out[-1])))
                vals = out
            keys = []
            for k_, (t, v) in enumerate(zip(self.T, vals)):
                if ch == "scale" and k_ and (not any(vals[k_ - 1])) != (not any(v)):
                    keys.append(kf(ch, t - 0.002, *vals[k_ - 1]))
                keys.append(kf(ch, t, *v))
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += keys

    def piste_fine(self, g, ch, fn, dt=1 / 120):
        """v7 : piste échantillonnée finement (dt), seulement aux instants où la valeur change (l'optimiseur simplifie
        ensuite) : propagation des fissures et ouverture du trou sans paliers."""
        e = ECHELLE_ZONE if (ch == "position" and g.ciel and not g.nom.startswith("ctrl_")) else 1.0
        T = [round(t, 5) for t in np.arange(0, self.L + 1e-9, dt)]
        if T[-1] < self.L - 1e-6:
            T.append(self.L)
        V = [tuple(round(v * e, 5) for v in fn(t)) for t in T]
        keys = [kf(ch, t, *v) for i, (t, v) in enumerate(zip(T, V))
                if i in (0, len(T) - 1) or v != V[i - 1] or v != V[i + 1]]
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += keys

    def vis(self, g, f):
        self.piste(g, "scale", lambda t: (1, 1, 1) if f(t) else (0, 0, 0))

    def cacher(self, *gs):
        for g in gs:
            self.piste(g, "scale", (0, 0, 0))

    def emettre(self, sorte, fn):
        for i, c in enumerate(CTRL[sorte]):
            if callable(fn):
                self.piste(c, "position", lambda t, i=i: (max(-1.0, min(7.0, fn(t, i))), 0, 0))
            else:
                self.piste(c, "position", (fn, 0, 0))

    def son(self, t, nom):
        self.A.setdefault("effects", {"name": "Effects", "type": "effect", "keyframes": []})["keyframes"].append(
            {"channel": "sound", "data_points": [{"effect": nom, "file": ""}], "time": round(t, 4)})

    def json(self):
        return {"uuid": nuid(), "name": self.nom, "loop": self.loop, "override": False, "length": self.L, "snapping": 24,
                "selected": self.nom == "arrivee", "animators": self.A}


# --- fissures, trou, éclats
LMAX = max(p_["L1"] for p_ in PIECES)


def croissance(p_, Lf):
    """Part poussée d'une pièce quand le front de propagation est à Lf (longueur parcourue depuis l'impact)."""
    return min(1.0, max(0.0, (Lf - p_["L0"]) / max(1e-6, p_["L1"] - p_["L0"])))


def fissures(an, f_L, f_k, secousses=()):
    """v7 : f_L(t) = front de propagation (px parcourus depuis l'impact), continu : chaque pièce pousse le long de sa corde
    quand le front la traverse (échelle x), recule quand il revient (fermeture) ; f_k(t) = échelle du trou : les fissures
    du centre disparaissent quand le trou les couvre. Secousses : une par bris (ressort à 7 Hz, clés à 120 / s)."""
    for g, p_ in GPIECES:
        if p_["centre"]:
            fn = lambda t, p_=p_: croissance(p_, f_L(t)) if f_k(t) < min(0.97, p_["rmax"]) else 0.0
        else:
            fn = lambda t, p_=p_: croissance(p_, f_L(t))
        an.piste_fine(g, "scale", lambda t, fn=fn: (fn(t), 1, 1) if fn(t) > 0 else (0, 0, 0))
    for g, L in GEPAVES:                                   # éclat décalé : grandit juste derrière le front
        an.piste_fine(g, "scale", lambda t, L=L: u3(sm(f_L(t), L, L + 6.0)) if f_L(t) > L else (0, 0, 0))
    an.piste_fine(SECOUSSE, "position", lambda t: (sum(ressort(t, tc, 0.4, 7.0, 9.0) for tc in secousses),
                                                   sum(ressort(t, tc + 0.012, -0.3, 8.0, 9.0) for tc in secousses), 0), dt=1 / 60)


def trou(an, f_k):
    """v7 : une plaque, échelle continue f_k(t) (0 → 1 à l'ouverture, 1 → 0 à la fermeture)."""
    for g in TROU:
        an.piste_fine(g, "scale", lambda t: (f_k(t), f_k(t), 1) if f_k(t) > 1e-3 else (0, 0, 0), dt=1 / 60)
    for g in BORDS:                                   # éclats épais du bord (pivot dans le plan du ciel)
        an.piste_fine(g, "scale", lambda t: u3(f_k(t)) if f_k(t) > 1e-3 else (0, 0, 0), dt=1 / 60)
    for g in (TOURB, HALO):
        an.piste_fine(g, "scale", lambda t: (f_k(t), f_k(t), 1) if f_k(t) > 1e-3 else (0, 0, 0), dt=1 / 60)
    an.piste(TOURB, "rotation", lambda t: (0, 0, -34.0 * t))     # poussière qui tourne lentement au fond


def debris(an, t0, t1):
    """Esquilles de ciel qui flottent autour du bord puis sont aspirées en spirale vers le noir (t0 → t1)."""
    for i, (g, th, r0, vit, rr) in enumerate(DEBRIS):
        a0, a1 = t0 + 0.05 * i, t1 - 0.04 * (9 - i)

        def pos(t, th=th, r0=r0, vit=vit, a0=a0, a1=a1):
            u = sm(t, a0, a1)
            a = th + vit * 2.2 * u + 0.15 * math.sin(3 * t + th)
            r = r0 - (r0 - 0.62) * u ** 1.6
            return (RX * (r * math.cos(a) - r0 * math.cos(th)), RY * (r * math.sin(a) - r0 * math.sin(th)) + 0.4 * math.sin(2.1 * t + th), -1.2 * u)

        an.piste(g, "position", pos)
        an.piste(g, "rotation", lambda t, rr=rr, a0=a0: tuple(r * 140 * max(0.0, t - a0) for r in rr))
        an.piste(g, "scale", lambda t, a0=a0, a1=a1: u3(sm(t, a0, a0 + 0.25) * (1 - sm(t, a1 - 0.25, a1))) if a0 <= t <= a1 else (0, 0, 0))


def eclats(an, t_pal):
    """t_pal[k] : instant où le palier k s'ouvre (l'éclat du bord tombe)."""
    for g, pal, th, rr, vit in ECLATS:
        t0 = t_pal[pal] + 0.03 * (abs(rr[0]) * 3)

        def pos(t, t0=t0, th=th, rr=rr, vit=vit):
            if t < t0:
                return (0, 0, 0)
            u = (min(t, t0 + 1.1) - t0) * vit if t < t0 + 1.1 else 0.0       # caché ensuite : revient au bord
            return (math.cos(th) * 4.0 * u + rr[1] * 2 * u, 6.0 * u - 26.0 * u * u, 7.0 * u)

        an.piste(g, "position", pos)
        an.piste(g, "rotation", lambda t, t0=t0, rr=rr: tuple(0.0 if t < t0 else r * 420 * (t - t0) for r in rr))
        an.piste(g, "scale", lambda t, t0=t0: u3(1.0 - 0.6 * sm(t, t0 + 0.5, t0 + 1.05)) if t0 - 0.04 <= t < t0 + 1.1 else (0, 0, 0))


def yeux(an, t_on, t_off):
    """v5 : aura rouge. Fond : s'allume d'un coup puis bat lentement ; pulsation : trois coups vifs à l'apparition (la
    nappe s'élargit et double d'intensité), puis suit le battement lent à mi-force."""
    pulses = [t_on, t_on + 0.4, t_on + 0.8]
    on = lambda t: sm(t, t_on, t_on + 0.05) * (1 - sm(t, t_off, t_off + 0.15))
    bat = lambda t: 0.5 + 0.5 * math.cos(2 * math.pi * max(0.0, t - pulses[-1] - 0.3) / 1.1) if t > pulses[-1] + 0.3 else 1.0

    def fond(t):
        if not (t_on <= t <= t_off + 0.15):
            return (0, 0, 0)
        k = on(t) * (0.85 + 0.15 * bat(t))
        return (k, k, 1)

    def pulse(t):
        if not (t_on <= t <= t_off + 0.15):
            return (0, 0, 0)
        fl = max(sm(t, pk, pk + 0.05) * math.exp(-max(0.0, t - pk - 0.05) / 0.2) for pk in pulses)     # v7 : attaque en 0,05 s
        k = on(t) * max(fl * 1.45, 0.25 + 0.6 * bat(t) * sm(t, pulses[-1] + 0.3, pulses[-1] + 0.6))
        return (k, k * 0.92, 1) if k > 0.04 else (0, 0, 0)

    for g in LUEUR:
        an.piste(g, "scale", fond)
    for g in LUEUR2:
        an.piste(g, "scale", pulse)


# --- bras : cinématique inverse


def quat(R):
    w = math.sqrt(max(0.0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    x = math.copysign(math.sqrt(max(0.0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2, R[2, 1] - R[1, 2])
    y = math.copysign(math.sqrt(max(0.0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2, R[0, 2] - R[2, 0])
    z = math.copysign(math.sqrt(max(0.0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2, R[1, 0] - R[0, 1])
    return np.array((w, x, y, z))


def mat(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def slerp(R0, R1, u):
    q0, q1 = quat(R0), quat(R1)
    if q0 @ q1 < 0:
        q1 = -q1
    d = min(1.0, q0 @ q1)
    if d > 0.9995:
        return mat(q0 + u * (q1 - q0))
    th = math.acos(d)
    return mat((math.sin((1 - u) * th) * q0 + math.sin(u * th) * q1) / math.sin(th))


POLE = np.array((1.0, 0.05, -0.35))           # coude vers la droite du joueur (+X), un peu vers l'avant : de face, le
POLE /= np.linalg.norm(POLE)                   # bras dessine un « < » de côté et l'avant-bras se voit en entier


def ik(P, poids_saisie, s_=1.0):
    """(rotations épaule, coude, poignet, E, P, S) : poignet en P (monde) avec le bras à l'échelle s_ autour de l'épaule.
    v5 : la main suit l'avant-bras avec une rotation de poignet constante W_REL (celle de la prise : jamais de demi-tour
    du poignet), puis, avec le poids de prise (fonction du temps), garde l'orientation monde G_PRISE pendant la prise et
    le transport (le joueur, qui ne tourne pas, reste dans la main)."""
    S_ = S_EP
    Pl = S_ + (np.asarray(P, float) - S_) / max(s_, 1e-3)
    d = Pl - S_
    dist = float(np.clip(np.linalg.norm(d), abs(L1 - L2) + 0.5, L1 + L2 - 0.25))
    u = d / np.linalg.norm(d)
    v = POLE - u * (POLE @ u)
    v /= np.linalg.norm(v)
    ca = (L1 ** 2 + dist ** 2 - L2 ** 2) / (2 * L1 * dist)
    a = math.acos(max(-1.0, min(1.0, ca)))
    E = S_ + L1 * (math.cos(a) * u + math.sin(a) * v)
    Pw = S_ + u * dist
    h = (E - S_) / L1
    f = (Pw - E) / np.linalg.norm(Pw - E)
    nb = np.cross(v, u)
    nb /= np.linalg.norm(nb)
    Rs = np.column_stack([nb, np.cross(h, nb), h])
    Re = np.column_stack([nb, np.cross(f, nb), f])
    if W_REL is None:
        return Re, f
    Rh = slerp(Re @ W_REL, G_PRISE, poids_saisie)
    return euler_de(Rs), euler_de(Rs.T @ Re), euler_de(Re.T @ Rh), S_ + s_ * (E - S_), S_ + s_ * (Pw - S_), S_


# --- prise (v5, retour en jeu de la v4 : « la main se retourne à 180° quand il attrape », joueur à côté de la main).
# Cause mesurée : la main passait de l'orientation de l'avant-bras à une orientation de prise fixe (doigts vers −Z) à
# ~130° de là, par un poids lié à la distance au joueur : demi-tour en 0,07 s à la saisie, puis retour pendant le
# transport (le joueur, suivi par le poignet, sortait de la main). v5 : prise par le haut du corps, la main d'en haut :
# paume à plat sur la tête (poignet relevé de ~45° : griffe), doigts refermés le long de l'épaule gauche et du dos,
# pouce devant ; orientation de prise G_PRISE tirée de l'avant-bras à la saisie (dorsiflexion pure + 9° d'inclinaison),
# rotation de poignet constante W_REL avant la prise, orientation monde fixe pendant la prise et le transport.
W_REL = None
POSE_SAISIE = [-25.0, -65.0, -30.0]     # griffe refermée sur l'épaule (doigts qui descendent le long du flanc)
C_PRISE = np.array((-2.0, 4.2, -1.0))    # sommet de la tête (0 ; 32,6 ; 0) dans le repère de la main (paume = +Y)
PSI_PRISE = -12.0                       # lacet de la main autour de la verticale (déviation du poignet ≈ 9°)
SOMMET = np.array((0.0, 32.6, 0.0))


def _prise():
    W = np.array((6.0, 36.0, -4.0))
    for _ in range(40):
        Re, f = ik(W, 0.0)
        hz = np.array((f[0], 0.0, f[2]))
        hz /= np.linalg.norm(hz)
        a = math.radians(PSI_PRISE)
        hz = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]]) @ hz
        y_ = np.array((0.0, -1.0, 0.0))
        G_ = np.column_stack([np.cross(y_, hz), y_, hz])
        W = SOMMET - G_ @ C_PRISE
    Re, f = ik(W, 0.0)
    return W, G_, Re.T @ G_


GR, G_PRISE, W_REL = _prise()             # GR : poignet à la prise (repère du joueur, pieds à l'origine)
assert abs(np.linalg.det(G_PRISE) - 1) < 1e-9
print("prise : poignet", np.round(GR, 2), "; rotation du poignet", round(math.degrees(math.acos((np.trace(W_REL) - 1) / 2)), 1), "deg")


POSE_OUVERT = [-6.0, -10.0, -8.0]       # main ouverte, doigts à peine fléchis
POSE_CROCHET = [-12.0, -62.0, -50.0]    # crochets sur le bord du trou
POSE_TENDU = [6.0, 2.0, 0.0]
POUCE_S = [-8.0, -28.0, -20.0]


def flex(an, dg, pc, f_pose, f_jit=None):
    """f_pose(t) -> (liste de 3 angles) ; f_jit(t, j) -> degrés ajoutés."""
    for j, chaine in enumerate(dg):
        for q, g in enumerate(chaine):
            def fn(t, j=j, q=q):
                v = f_pose(t)[q] * DOIGTS_FLEX[j]
                if f_jit:
                    v += f_jit(t, j) * (1.0, 0.7, 0.5)[q]
                return (v, 0, 0)
            an.piste(g, "rotation", fn)
    for q, g in enumerate(pc):
        an.piste(g, "rotation", lambda t, q=q: (f_pose(t)[q] * 0.6 + POUCE_S[q] * (f_pose(t)[1] / POSE_SAISIE[1]) * 0.6, 0, 0))


def melange(a, b, u):
    return [x * (1 - u) + y * u for x, y in zip(a, b)]


def courbe(pts, n=160):
    """v7 : courbe de Catmull-Rom centripète par les points pts (pas de boucle ni de pointe), paramétrée par la longueur
    parcourue : renvoie f(u), u ∈ [0, 1]. Vitesse continue à chaque point de passage (la v6 s'arrêtait à chacun)."""
    P = [np.asarray(q, float) for q in pts]
    P = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    D = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1:i + 3]
        t0 = 0.0
        t1 = t0 + max(1e-6, np.linalg.norm(p1 - p0)) ** 0.5
        t2 = t1 + max(1e-6, np.linalg.norm(p2 - p1)) ** 0.5
        t3 = t2 + max(1e-6, np.linalg.norm(p3 - p2)) ** 0.5
        for tt in np.linspace(t1, t2, n, endpoint=False):
            a1 = (t1 - tt) / (t1 - t0) * p0 + (tt - t0) / (t1 - t0) * p1
            a2 = (t2 - tt) / (t2 - t1) * p1 + (tt - t1) / (t2 - t1) * p2
            a3 = (t3 - tt) / (t3 - t2) * p2 + (tt - t2) / (t3 - t2) * p3
            b1 = (t2 - tt) / (t2 - t0) * a1 + (tt - t0) / (t2 - t0) * a2
            b2 = (t3 - tt) / (t3 - t1) * a2 + (tt - t1) / (t3 - t1) * a3
            D.append((t2 - tt) / (t2 - t1) * b1 + (tt - t1) / (t2 - t1) * b2)
    D.append(P[-2])
    D = np.array(D)
    S = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(D, axis=0), axis=1))])
    S /= S[-1]
    return lambda u: np.array([np.interp(min(1.0, max(0.0, u)), S, D[:, k]) for k in range(3)])


def trajet(t, phases):
    """phases : [(t_a, t_b, courbe, profil)] ; entre deux phases (et avant, après), la main est immobile au bout de la
    phase précédente : ce sont les seuls arrêts (sortie, prise, pose, rentrée). profil(τ) : avancement sur la courbe,
    dérivée nulle seulement en 0 et 1."""
    if t <= phases[0][0]:
        return phases[0][2](0.0)
    for ta, tb, f, pr in phases:
        if t <= tb:
            return f(pr((t - ta) / (tb - ta))) if t >= ta else f(0.0)
    return phases[-1][2](1.0)


def doux(u):
    return sm(u, 0.0, 1.0)


def doux_lent(u):
    """Départ lent (la main s'ouvre presque sur place), puis accélère vers le noir et s'y arrête en douceur."""
    return sm(u, 0.0, 1.0) ** 2


def bras(an, f_P, f_vis, f_pose, f_s, f_w, f_jit=None):
    """f_P(t) : poignet (monde) ; f_s(t) : échelle du bras (il vient du fond du noir) ; f_w(t) : poids de la prise."""
    cache = {}

    def sol(t):
        if t not in cache:
            P = f_P(t)
            cache[t] = ik(P, f_w(t), f_s(t))
        return cache[t]
    an.piste(BRAS, "scale", lambda t: u3(f_s(t)) if f_vis(t) else (0, 0, 0))
    an.piste(EPAULE, "rotation", lambda t: sol(t)[0], deroule=True)
    an.piste(COUDE, "rotation", lambda t: sol(t)[1], deroule=True)
    an.piste(POIGNET, "rotation", lambda t: sol(t)[2], deroule=True)
    flex(an, DGB, PCB, f_pose, f_jit)
    return sol


def mains_bord(an, t_in, t_out):
    for i, (g0, av, dg, pc) in enumerate(BORD):
        ti, to = t_in + 0.12 * i, t_out + 0.08 * i
        an.vis(g0, lambda t, ti=ti, to=to: ti <= t <= to + 0.3)
        an.piste(av, "position", lambda t, ti=ti, to=to: (0, 0, -5.5 + 5.5 * sm(t, ti, ti + 0.35) - 6.0 * sm(t, to, to + 0.3)))
        flex(an, dg, pc, lambda t, ti=ti, to=to: melange(POSE_TENDU, POSE_CROCHET, sm(t, ti + 0.2, ti + 0.45) * (1 - sm(t, to - 0.1, to + 0.1))),
             lambda t, j, i=i: 1.8 * math.sin(t * 17 + j * 1.7 + i * 2))


def sol_ombre(an, f_s, f_a):
    an.piste(SOL, "scale", lambda t: (f_s(t), 1, f_s(t)) if f_s(t) > 0.02 else (0, 0, 0))
    an.piste(A_OMBRE, "position", lambda t: (f_a(t), 0, 0))


def onde(an, t0, dur=0.6, k=1.9):
    an.piste(ONDE, "scale", lambda t: (0.25 + k * sm(t, t0, t0 + dur), 1, 0.25 + k * sm(t, t0, t0 + dur)) if t0 <= t <= t0 + dur + 0.1 else (0, 0, 0))
    an.piste(A_ONDE, "position", lambda t: (-0.95 * sm(t, t0 + 0.2, t0 + dur), 0, 0))


# ---- charge (loop 2,4 s) : premières fissures qui avancent et reculent, ombre au sol
LC = 2.4
W1 = 2 * math.pi / LC
an = Anim("charge", LC, "loop", fps=30)
# v7 : le front avance et recule en continu (boucle fermée : 0 à t = 0 et t = LC), plus d'à-coups ni de secousses
fissures(an, lambda t: 46.0 * (0.5 - 0.5 * math.cos(W1 * t)) ** 1.3, lambda t: 0.0)
an.cacher(*TROU, *BORDS, TOURB, HALO, *[d[0] for d in DEBRIS], *[e[0] for e in ECLATS], *LUEUR, *LUEUR2, BRAS, *[b[0] for b in BORD], ONDE)
sol_ombre(an, lambda t: 0.55 + 0.05 * math.sin(W1 * t), lambda t: -0.45 + 0.12 * math.sin(W1 * t))
an.emettre("ash", lambda t, i: -0.5 if i < 2 else -1)
an.emettre("poussiere", lambda t, i: -1 + 1.5 * bump(t, 0.3, 0.35, 0.9, 1.2) if i < 2 else -1)
for so in ("eclat", "portal", "encre", "fumee", "encre_bras"):
    an.emettre(so, -1)
# le joueur est aspiré par à-coups (guide 15 : joueur lu pendant la charge) : il décolle de 4 px au plus et retombe
an.piste(JOUEUR, "position", lambda t: (0, 4.0 * (0.5 - 0.5 * math.cos(W1 * t)) + 0.4 * math.sin(3 * W1 * t) * math.sin(W1 * t / 2) ** 2, 0))
charge = an.json()


# ---- trame commune : fissures par à-coups, trou en 3 paliers, yeux, fermeture
def ouverture_fermeture(an, T_F, T_T, T_Y, T_YOFF, T_BORD, T_BORD_OUT, T_TF, T_FF, T_PRISE):
    """T_F : début et fin de la propagation (T_F[0] → T_F[-1] + 0,15) ; T_T : le trou passe par 0,42, 0,72 et ~0,95 de sa
    taille (ouverture continue) ; T_TF : fermeture ; T_FF : les fissures reculent vers le centre (T_FF[0] → T_FF[-1]).
    v7 (retour en jeu de la v6 : « animations par à-coups ») : plus de paliers ; front et trou suivent des courbes
    continues, accélération puis ralentissement, seuls arrêts au début et à la fin."""
    t0p, t1p = T_F[0] - 0.04, T_F[-1] + 0.15
    f_L = lambda t: LMAX * (sm(t, t0p, t1p) ** 1.25) * (1 - sm(t, T_FF[0] - 0.05, T_FF[-1] + 0.1))
    to0, to1 = T_T[0] - 0.08, T_T[2] + 0.12
    f_k = lambda t: (1 - (1 - min(1.0, max(0.0, (t - to0) / (to1 - to0)))) ** 2.2 if t > to0 else 0.0) * (1 - sm(t, T_TF[0] - 0.05, T_TF[2] + 0.08))
    fissures(an, f_L, f_k, (T_T[0],))
    trou(an, f_k)
    eclats(an, T_T)
    yeux(an, T_Y, T_YOFF)
    debris(an, T_T[2] + 0.1, T_TF[0])
    mains_bord(an, T_BORD, T_BORD_OUT)
    an.emettre("eclat", lambda t, i: -1 + 6 * bump(t, T_T[0], T_T[0] + 0.05, T_T[2] + 0.5, T_T[2] + 0.7))
    an.emettre("poussiere", lambda t, i: -1 + 3 * bump(t, T_F[0], T_F[0] + 0.1, T_T[2] + 0.3, T_T[2] + 0.6)
               + 3 * bump(t, T_FF[0], T_FF[0] + 0.05, T_FF[-1], T_FF[-1] + 0.1))
    an.emettre("portal", lambda t, i: -1 + 3 * bump(t, T_T[1], T_T[1] + 0.2, T_TF[0], T_TF[0] + 0.1))
    an.emettre("ash", lambda t, i: -1 + 3 * bump(t, T_T[0], T_T[0] + 0.1, T_TF[2], T_TF[2] + 0.3))
    an.emettre("encre", lambda t, i: -1 + 2 * bump(t, T_T[2] + 0.3, T_T[2] + 0.5, T_TF[0], T_TF[0] + 0.1))
    an.son(T_F[0] - 0.05, "neant_fele")
    an.son(T_T[0], "block.glass.break")
    an.son(T_Y, "neant_pulse")
    an.son(T_PRISE, "neant_impact")


def joueur_tenu(P, s_):
    """Position du groupe joueur (échelle s_) pour que le poignet reste en P : le point GR du joueur suit la main."""
    return tuple(np.asarray(P, float) - s_ * GR)


R0 = S_EP + (4.0, -10.0, 2.0)                  # poignet au fond du noir (bras à petite échelle)
S_MIN = 0.16


# ---- depart (once 4,8 s) : fissures, trou, yeux, le bras surgit du noir, descend de côté, saisit, emporte ; fermeture
LD = 4.8
T_F = (0.1, 0.35, 0.6, 0.85)
T_T = (1.0, 1.12, 1.25)
T_Y = 1.4
D_SORT, D_HAUT, D_APP, D_SAISIT, D_SERRE, D_LEVE, D_RENTRE = 1.85, 2.35, 2.6, 2.78, 2.98, 3.08, 3.85
T_YOFF = 3.95
T_TF = (4.05, 4.15, 4.25)
T_FF = (4.0, 4.1, 4.2, 4.3)            # v4 : les fissures s'effacent avec le trou (plus d'« araignée » seule)
EX = list(T_F) + list(T_T) + list(T_TF) + list(T_FF) + [D_SORT, D_SAISIT, D_SERRE] + list(np.arange(D_SORT, D_RENTRE + 0.06, 1 / 42))
an = Anim("depart", LD, "once", fps=30, extra=EX)
ouverture_fermeture(an, T_F, T_T, T_Y, T_YOFF, 1.45, 3.8, T_TF, T_FF, D_SERRE)
# v7 (« même le bras a une micro-pause quand il remonte ») : cause mesurée : chemin() enchaînait des smoothsteps, vitesse
# nulle à chaque point de passage, dont GR + (10, 70, −18) à D_LEVE + 0,35 = 3,43 s, entre la levée et la rentrée (le
# joueur tenu s'arrêtait à 3,42 s) ; aussi à D_HAUT et D_APP. Maintenant une courbe lisse par phase, parcourue d'un seul
# élan : arrêts seulement à la sortie, à la prise (D_SAISIT → D_SERRE) et à la rentrée.
PH_DEP = [(D_SORT, D_SAISIT, courbe([R0, (56.0, 90.0, -24.0), GR + (14.0, 12.0, -6.0), GR]), doux),
          (D_SERRE, D_RENTRE, courbe([GR, GR + (10.0, 70.0, -18.0), S_EP + (2.0, -6.0, 1.0)]), doux)]
P_dep = lambda t: trajet(t, PH_DEP)
s_dep = lambda t: S_MIN + (1 - S_MIN) * sm(t, D_SORT, D_HAUT - 0.05) * (1 - sm(t, D_LEVE + 0.4, D_RENTRE))
sol_dep = bras(an, P_dep, lambda t: D_SORT - 0.02 <= t <= D_RENTRE + 0.05,
               lambda t: melange(melange(POSE_TENDU, POSE_OUVERT, sm(t, D_SORT, D_HAUT)), POSE_SAISIE, sm(t, D_SAISIT, D_SERRE)), s_dep,
               lambda t: sm(t, D_APP - 0.2, D_SAISIT),
               lambda t, j: -8 * bump(t, D_HAUT, D_HAUT + 0.1, D_SAISIT - 0.1, D_SAISIT) * math.sin(t * 30 + j))


def joueur_dep(t):
    if t < D_SERRE:
        return (0, 0, 0), 1.0 + ressort(t, D_SAISIT + 0.1, -0.05, 6.0, 10.0)
    s_ = s_dep(t) if t <= D_RENTRE else 0.0          # v5 : même échelle que le bras (le joueur reste dans la main)
    p = joueur_tenu(P_dep(t), s_)
    if t < D_LEVE + 0.1:
        p = (p[0], max(0.0, p[1]), p[2])
    return p, (s_ if s_ > 0.04 else 0.0)


an.piste(JOUEUR, "position", lambda t: joueur_dep(t)[0])
an.piste(JOUEUR, "scale", lambda t: u3(joueur_dep(t)[1]) if joueur_dep(t)[1] > 0 else (0, 0, 0))
sol_ombre(an, lambda t: (0.6 + 0.4 * sm(t, 0.3, 1.5)) * (1 - sm(t, T_FF[0], LD - 0.05)),
          lambda t: -0.7 + 0.45 * sm(t, 0.3, 1.5) - 0.3 * sm(t, T_FF[0], LD - 0.1))
onde(an, D_SERRE + 0.08, 0.55, 1.6)
an.emettre("fumee", lambda t, i: -1 + 4 * bump(t, D_SERRE, D_SERRE + 0.05, D_SERRE + 0.2, D_SERRE + 0.4))
an.emettre("encre_bras", lambda t, i: -1 + 3 * bump(t, D_SORT, D_SORT + 0.2, D_RENTRE - 0.3, D_RENTRE))
depart = an.json()

# ---- arrivee (once 4,8 s) : fissures, trou, yeux, le bras surgit en tenant le joueur, le dépose et remonte
LA = 4.8
T_F = (0.1, 0.32, 0.54, 0.76)
T_T = (0.92, 1.04, 1.16)
T_Y = 1.3
A_SORT, A_HAUT, A_APP, A_POSE, A_LACHE, A_RENTRE = 1.7, 2.2, 2.5, 2.7, 2.95, 3.6
T_YOFF = 3.75
T_TF = (3.95, 4.05, 4.15)
T_FF = (3.9, 4.0, 4.1, 4.2)
EX = list(T_F) + list(T_T) + list(T_TF) + list(T_FF) + [A_SORT, A_POSE] + list(np.arange(A_SORT, A_RENTRE + 0.06, 1 / 42))
an = Anim("arrivee", LA, "once", fps=30, extra=EX)
ouverture_fermeture(an, T_F, T_T, T_Y, T_YOFF, 1.35, 3.65, T_TF, T_FF, A_POSE)
PH_ARR = [(A_SORT, A_POSE, courbe([R0, (56.0, 92.0, -24.0), GR + (10.0, 16.0, -4.0), GR]), doux),
          (A_POSE, A_RENTRE, courbe([GR, GR + (3.0, 3.0, 1.0), S_EP + (2.0, -6.0, 1.0)]), doux_lent)]
P_arr = lambda t: trajet(t, PH_ARR)
s_arr = lambda t: S_MIN + (1 - S_MIN) * sm(t, A_SORT, A_HAUT - 0.05) * (1 - sm(t, A_LACHE + 0.2, A_RENTRE))
sol_arr = bras(an, P_arr, lambda t: A_SORT - 0.02 <= t <= A_RENTRE + 0.05,
               lambda t: melange(POSE_SAISIE, POSE_OUVERT, sm(t, A_POSE + 0.05, A_LACHE)), s_arr,
               lambda t: 1.0 - sm(t, A_LACHE, A_LACHE + 0.35))


def joueur_arr(t):
    if t < A_SORT:
        return (0, 0, 0), 0.0
    if t >= A_POSE:
        return (0, 0, 0), 1.0 + ressort(t, A_POSE, 0.06, 5.0, 9.0)
    s_ = s_arr(t)                                     # v5 : même échelle que le bras
    p = joueur_tenu(P_arr(t), s_)
    return (p[0], max(0.0, p[1]), p[2]), s_


an.piste(JOUEUR, "position", lambda t: joueur_arr(t)[0])
an.piste(JOUEUR, "scale", lambda t: u3(joueur_arr(t)[1]) if joueur_arr(t)[1] > 0 else (0, 0, 0))
sol_ombre(an, lambda t: (0.6 + 0.4 * sm(t, 0.3, 1.5)) * (1 - sm(t, T_FF[0], LA - 0.05)),
          lambda t: -0.7 + 0.45 * sm(t, 0.3, 1.5) + 0.2 * bump(t, A_POSE, A_POSE + 0.05, A_POSE + 0.2, A_POSE + 0.8) - 0.3 * sm(t, T_FF[0], LA - 0.1))
onde(an, A_POSE)
an.emettre("fumee", lambda t, i: -1 + 6 * bump(t, A_POSE - 0.01, A_POSE, A_POSE + 0.15, A_POSE + 0.3))
an.emettre("encre_bras", lambda t, i: -1 + 3 * bump(t, A_SORT, A_SORT + 0.2, A_RENTRE - 0.3, A_RENTRE))
arrivee = an.json()


# ---- animations des particules (guide 5 ter §3)
def anim_particule(nom, L, g, rot_=None):
    a_ = Anim(nom, L, "loop", fps=16)
    a_.piste(g, "rotation", lambda t: tuple(r * 360 * t / L for r in rot_))
    return a_.json()


ANIMS = [charge, depart, arrivee, anim_particule("particle_eclat_fall", 1.2, PART_E, (1, 1, 0)),
         anim_particule("particle_poussiere_fall", 2.0, PART_P, (1, 0, 1))]

# contrôle (cam_) : la plaque du trou est toujours entre l'œil et l'épaule ; le bras sort donc du noir sous tous les
# angles. On mesure, pour le joueur sous le trou et des spectateurs à 10 et 30 blocs, la part du bras cachée par le trou
# (derrière la plaque et dans son contour) : le reste se voit, qu'il soit devant ou derrière le plan du ciel.
PLAQUE = (ZH - 0.3) * ECHELLE_ZONE
VUES = [("joueur", np.array((0.0, 26.0, 0.0)))] + [(f"{d // 16} blocs, {az} deg", np.array((d * math.sin(math.radians(az)), 26.0, d * math.cos(math.radians(az)))))
                                                for d in (160, 480) for az in range(0, 360, 45)]
for nom_a, f_P, f_s, t0, t1 in (("depart", P_dep, s_dep, D_HAUT, D_LEVE), ("arrivee", P_arr, s_arr, A_HAUT, A_LACHE)):
    pire = (1.0, "")
    for t in np.linspace(t0, t1, 12):
        _, _, _, E, Pw, S_ = ik(f_P(t), 0, f_s(t))
        pts = [S_ + (E - S_) * u for u in np.linspace(0.3, 1, 8)] + [E + (Pw - E) * u for u in np.linspace(0, 1, 8)]
        for nv, cam in VUES:
            n_ = (cam - S_) / np.linalg.norm(cam - S_)
            vu = np.mean([(p - S_) @ n_ > PLAQUE or np.linalg.norm((p - S_) - ((p - S_) @ n_) * n_) > RY * ECHELLE_ZONE for p in pts])
            if vu < pire[0]:
                pire = (vu, f"{nv}, t = {t:.2f}")
    print(f"bras ({nom_a}) : part visible la plus faible {pire[0] * 100:.0f} % ({pire[1]})")
    assert pire[0] >= 0.5 or os.environ.get("SANS_CONTROLE"), "bras caché par le trou"


# ------------------------------------------------------------------ ECHELLE_ZONE : tout le ciel autour de C_CIEL
C, C_ = np.array(C0), np.array(C_CIEL)
for e in elements:
    if e["uuid"] in DU_CIEL:
        for k in ("from", "to", "origin"):
            e[k] = r3(C_ + ECHELLE_ZONE * (np.array(e[k]) - C))
for g in G.tous:
    if g.ciel:
        g.origin = list(C_ + ECHELLE_ZONE * (np.array(g.origin) - C))
outliner = [EFFET.json(), JOUEUR.json(), PART_E.json(), PART_P.json()]

for e in elements:
    for k in ("from", "to", "origin"):
        e[k] = [round(v, 3) for v in e[k]]
    if "rotation" in e:
        e["rotation"] = [round(v, 3) for v in e["rotation"]]

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures,
         "animations": ANIMS}
sys.path.insert(0, os.path.join("..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
embarquer_sons(model, {n: f"sons/{n}.ogg" for n in ("neant_fele", "neant_pulse", "neant_impact")})
limiter_sons(model, max_effet=4)
for a_ in ANIMS:
    eff = a_["animators"].get("effects")
    assert not eff or len(eff["keyframes"]) <= 4, a_["name"]

os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


def ngroupes(n):
    return 1 + sum(ngroupes(c) for c in n.get("children", []) if isinstance(c, dict))


print(len(elements), "cubes ;", sum(ngroupes(n) for n in model["outliner"]), "groupes ; profondeur", max(depth(n) for n in model["outliner"]), ";",
      len(model["animations"]), "anims ;", sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()), "keyframes ;",
      os.path.getsize(OUT) // 1024, "Ko ;", len(EMITS), "emit_ ;", NSEG, "segments de fissures ;", len(PIECES), "pièces")
