"""Effet de téléportation de l'ensemble Admin, v7 « Ciel d'alvéoles » (guide 15). Design original par analogie (fiches
.claude/styles/admin.md, .claude/references/effets/apparition-ciel-alveoles.md, mesures de la scène de référence). Écrit
effet_admin.png, effet_admin_e.png, .build/effet_admin_brut.bbmodel et .build/effet_admin_commejeu.bbmodel (identiques depuis
que le mod lit les faces horizontales comme Blockbench, guide du 2026-11-06 soir). v1 refusée : .build/gen_avant.py ; v2 : .build/gen_v2_cape.py ;
v3 (glyphes, goutte et filets en méduse) : .build/gen_v3.py.

Retour sur la v3 : « l'hexagone est pas le même, le sang on dirait des tentacules rouges et non du sang liquide qui coule pour
former une masse, les hexagones n'ont pas la même palette ni la même forme, le texte c'est pas ALERTE SYSTÈME ».

Retour en jeu sur la v5 (2026-11-06 22.42) : dôme de panneaux validé (inchangé) ; sang refusé : « le sang va falloir le rendre
bien plus lisse et comme un fluide » (vu d'en dessous : éventail de plaques, melon à côtes, chapelets de perles noires).
v6 (sang seul refait, v5 dans .build/gen_v5.py) : poche = surface de révolution de 32 × 40 facettes (une plaque par facette,
face extérieure sur le quadrilatère entre deux anneaux) peinte d'une peau continue (dégradé, reflet en bande verticale,
croissant clair dessous), fond fermé par une calotte ronde ; brins = tubes ronds à 8 facettes sur les méridiens, noyés quand
la poche gonfle ; gouttes renflées (10 × 7 facettes) aux sommets qui s'étirent et se détachent ; bourrelets en demi-tubes le
long des jointures ; déchirure = la poche se vide et remonte, six filets tombent jusqu'au sol, flaque lisse. Reflets _r/_m
sur le sang seulement (essai, REFLETS_SANG).

Retour en jeu sur la v6 (2026-11-06 23.22–23.23, de nuit) : « ça fait ballon de baudruche, effet plastique je trouve, le sang ».
Causes relevées sur les captures : poche en œuf parfait de révolution, valeur claire et uniforme (saumon de nuit), grand reflet
doux et mat (matcap _m rose sur toute la poche), filets en tiges droites. v7 (v6 dans .build/gen_v6.py) : reflets _r/_m coupés
(REFLETS_SANG = False) ; masse presque noire (rouge sombre au milieu) et brins plus rouges (minces = translucides), reflets en
petits traits nets blancs rosés cassés le long des coulures ; poche en oignon irrégulier (bosses, deux lobes, axe qui penche)
recouverte de 14 brins en relief (anneaux perpendiculaires au brin), trois gouttes pendantes sous le fond qui s'étirent ; la
masse se balance mollement avec ses brins ; filets épais en haut, effilés, ondulés, renflés de gouttes, qui se cassent en une
goutte détachée qui tombe au sol ; _e du sang en rouge sombre (nuit), jamais rose.

Design v4 (plafond inchangé ; le sang décrit ici est remplacé par la v6)
- Plafond : hexagones allongés (pointes à gauche et à droite, rapport 2,6 : 1 mesuré sur la scène), pavés en colonnes décalées
  d'une demi-hauteur, sur un dôme bas. Palette mesurée : fond pêche clair au centre, bande de bord rose-rouge, liseré rose
  lavande, jointure prune ; petit motif d'alvéoles clair dans le fond ; texte « ALERTE / SYSTÈME » rouge (traits ≥ 8 texels).
  Texte asymétrique sur des faces horizontales : écrit dans le sens de Blockbench, que le mod suit depuis le 2026-11-06 (soir) ;
  retourner_pour_jeu (tools/uv_horizontal.py) ne retourne plus rien (MIROIR_X_JEU = False).
- Sang liquide : perles qui naissent aux sommets des jointures et gonflent ; le sang file le long des jointures ; les perles
  s'étirent en gouttes qui tombent (particules) ; des filets fins coulent du plafond en cascade et convergent sous le centre
  où une masse ronde se forme ; la masse gonfle et pend, les filets s'élargissent en nappes brillantes qui se soudent en une
  poche lisse ; elle tremble (échelle non uniforme), se tend, se déchire : les nappes s'ouvrent vers l'extérieur, le noyau
  éclate, le joueur géant apparaît ; les nappes s'amincissent, se vident et remontent, le sang retombé fait une flaque.
- Lumière rouge : disque `add_` au sol, voile `camy_` + `add_` derrière la scène.

Animations
- charge (loop 4 s) : trois alvéoles qui clignotent au-dessus, lueur rouge au sol qui respire.
- arrivee (once 4,9 s) : alvéoles (alveoles_alarme) → perles et jointures (sang_suinte) → filets, masse, poche → déchirure,
  joueur géant (sang_revele) → descente du joueur, sang qui se vide, alvéoles qui s'éteignent en vague.
- depart (once 4,8 s) : alvéoles, perles, filets autour du joueur ; il monte en grandissant, la poche se ferme sur lui puis
  remonte dans le plafond ; les alvéoles s'éteignent.
- overlay_alveoles : pulsation des lueurs en vague.

Fonctions : add_, trans_, camy_, ctrl_alpha, ctrl_emit, particle_/emit_, emit_mc_dust, overlay_, groupe joueur, sons embarqués,
calque _e, Molang (q.anim_time, math.mod) sur les échelles et rotations. À juger en jeu : sens du texte (faces horizontales lues comme Blockbench),
lisibilité du plafond vu d'en dessous, poche de sang vue de près, joueur géant, cadence des particules.
"""
import base64, io, json, math, os, sys, copy, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

NOM = "effet_admin"
TEX = 512
SS = 4
# v5 : ciel « en hauteur max et taille max » (consigne de l'utilisateur), dans la limite de 320 px au repos par axe
# (guide 3 et 15, 2026-11-06 soir) avec une marge d'environ 10 px ; v4 : tout ×1 (bridé à 64 px).
R_CIEL = 280.0                # rayon du plafond (centres des alvéoles) : 17,5 blocs
EZ = ECHELLE_ZONE = R_CIEL / 53.0   # facteur sur les distances de la v4 (germe, zones de sang, vagues)
Y_BORD, Y_HAUT = 222.0, 300.0  # dôme de 13,9 à 18,75 blocs de haut
PW, PH = 72.0, 27.5           # panneau : largeur pointe à pointe, hauteur (rapport 2,62 ; scène ≈ 2,7) : 4,5 × 1,7 blocs
KS = 4.0                      # épaisseur du sang aux jointures (perles, veines) : lisible à 19 blocs
K_SAC = 5.03                  # taille de la poche de sang : de y 299 à y ≈ 60 (le joueur qui arrive, œil à y 26, la voit d'en dessous)
TIP = 0.12                    # longueur de chaque pointe / largeur (scène ≈ 0,10–0,12)
SEED_XZ = (-13.0 * EZ, -15.0 * EZ)      # première alvéole : devant à gauche, au-dessus du joueur
ECHELLE_GEANT = 6.2           # joueur révélé dans le sang : 13 blocs de haut (tête à y 278, épaules dans le ventre de la poche)
Y_GEANT = 80.0                # hauteur des pieds du joueur géant (dans la poche : bas de la poche à y ≈ 60)
POLICE = "C:/Windows/Fonts/impact.ttf"
TEXTE = ("ALERTE", "SYSTÈME")


def y_dome(r):
    return Y_BORD + (Y_HAUT - Y_BORD) * (1 - (r / (R_CIEL + 4)) ** 2)


# ------------------------------------------------------------------ outils de peinture
def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def grille(W, H):
    n_w, n_h = W * SS, H * SS
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w * 2 - 1, 1 - (np.arange(n_h) + 0.5) / n_h * 2)


def reduire(rgb, a, W, H, seuil=None, amax=255):
    """Sur-échantillonné → W×H. seuil : alpha 0/255 (découpe) ; sinon alpha continu plafonné à amax (trans_)."""
    im = np.array(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(float)
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = im
    if seuil is not None:
        m = al > seuil
        out[..., 3] = m * 255
        if m.any():
            out[~m, :3] = out[m, :3].mean(axis=0)
    else:
        al = np.where(al < 24, 0, np.clip(al, 1, amax))
        out[..., 3] = al.astype(np.uint8)
        out[al == 0, :3] = 0
    return out


def additif(rgbf, W, H):
    """rgbf : image flottante 0..255 (sur-échantillonnée) ; noir = invisible, alpha 255 ailleurs."""
    im = np.array(Image.fromarray(np.clip(rgbf, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = im
    lum = im.max(axis=2)
    out[..., 3] = (lum > 10) * 255
    out[lum <= 10, :3] = 0
    return out



# ------------------------------------------------------------------ palette (mesurée sur la scène de référence, fiche)
FOND_C = np.array((250, 132, 102), float)     # fond du panneau, centre (pêche clair)
FOND_B = np.array((236, 84, 84), float)      # fond, vers les bords
BANDE = np.array((228, 70, 92), float)       # bande de bord rose-rouge
BANDE_C = np.array((244, 104, 108), float)
LISERE = np.array((255, 150, 182), float)     # liseré rose lavande le long de la jointure
JOINT = np.array((184, 66, 98), float)        # jointure prune
TEXTE_C = np.array((186, 40, 32), float)      # texte rouge
# v7 : la v6 (176/52/42, 108/24/18, 52/13/9 + matcap rose large) se lisait « ballon de baudruche, plastique » en jeu.
# Sang épais = presque noir ; seules les parties minces (filets, bords) laissent passer un rouge profond saturé.
SANG = ((140, 22, 22), (76, 9, 11), (22, 3, 5))        # éclairé, base, ombre : jamais rose ni saumon
SANG_FIN = ((170, 26, 22), (112, 12, 12), (42, 4, 6))   # filets et brins minces : rouge profond translucide
SPEC = np.array((255, 222, 214), float)       # reflet mouillé : petit, net, blanc rosé
GLOW = np.array((255, 70, 64), float)

HX, HY = 320, 122     # texture d'un panneau (rapport PW / PH)


def hex_long(W, H, ss=SS):
    """Distance (texels, positive dedans) au bord d'un hexagone allongé (pointes à gauche et à droite) qui remplit W×H."""
    n_w, n_h = W * ss, H * ss
    X, Y = np.meshgrid((np.arange(n_w) + 0.5) / ss - W / 2, (np.arange(n_h) + 0.5) / ss - H / 2)
    hw, hh, tip = W / 2, H / 2, TIP * W
    nx, ny = hh, tip
    L = math.hypot(nx, ny)
    d = np.minimum(hh - np.abs(Y), ((hw - np.abs(X)) * nx - np.abs(Y) * ny) / L)
    return d, X, Y


def texte_masque(W, H):
    """Masque du texte (sur-échantillonné) : « ALERTE » en gros, « SYSTÈME » dessous (police grasse, traits ≥ 8 texels)."""
    img = Image.new("L", (W * SS, H * SS), 0)
    dr = ImageDraw.Draw(img)
    for txt, taille, yc in ((TEXTE[0], 50, 0.40), (TEXTE[1], 34, 0.75)):
        f = ImageFont.truetype(POLICE, taille * SS)
        b = dr.textbbox((0, 0), txt, font=f)
        dr.text((W * SS / 2 - (b[2] - b[0]) / 2 - b[0], yc * H * SS - (b[3] - b[1]) / 2 - b[1]), txt, font=f, fill=255)
    return np.array(img) / 255.0


def micro_alveoles(X, Y, s=9.0):
    """Petit motif d'alvéoles clair dans le fond (vu sur la scène de près)."""
    xc = (X * 2 / 3) / s
    zc = (-X / 3 + math.sqrt(3) / 3 * Y) / s
    yc = -xc - zc
    rx, ry, rz = np.round(xc), np.round(yc), np.round(zc)
    dx, dy, dz = np.abs(rx - xc), np.abs(ry - yc), np.abs(rz - zc)
    m1 = (dx > dy) & (dx > dz)
    rx = np.where(m1, -ry - rz, rx)
    m2 = (~m1) & (dy > dz)
    ry = np.where(m2, -rx - rz, ry)
    rz = np.where(~m1 & ~m2, -rx - ry, rz)
    return np.maximum.reduce([np.abs(xc - rx), np.abs(yc - ry), np.abs(zc - rz)]) > 0.43


TEXTE_MASQUE = texte_masque(HX, HY)


def panneau():
    d, X, Y = hex_long(HX, HY)
    J = 4.0
    v = np.clip(1 - np.maximum((np.abs(X) / (HX / 2)) ** 2.2, (np.abs(Y) / (HY / 2)) ** 2.0) * 0.9, 0, 1)
    col = FOND_B + (FOND_C - FOND_B) * smooth(v)[..., None]
    col = col + micro_alveoles(X, Y)[..., None] * np.array((10, 14, 10), float)
    band = (d > J) & (d < J + 7)
    col = np.where(band[..., None], BANDE + (BANDE_C - BANDE) * smooth((d - J) / 7)[..., None], col)
    rim = (d > J - 1.5) & (d <= J + 1.2)
    col = np.where(rim[..., None], LISERE, col)
    jt = d <= J - 1.5
    col = np.where(jt[..., None], JOINT, col)
    a = np.where(d > 0, 0.87, 0.0)
    a = np.where((jt | rim | band) & (d > 0), 0.95, a)
    T = TEXTE_MASQUE * (d > J + 7)
    col = col * (1 - T[..., None]) + TEXTE_C * T[..., None]
    a = np.maximum(a, T * 0.95)
    return reduire(col, a, HX, HY, amax=246)


def panneau_lueur():
    W, H = 96, 36
    d, X, Y = hex_long(W, H)
    dn = d / (H / 2)
    f = 0.9 * np.exp(-((dn - 0.1) / 0.1) ** 2) + 0.35 * np.clip(dn, 0, 1)
    f *= d > 0.3
    return additif(GLOW[None, None] * 0.24 * np.clip(f, 0, 1)[..., None], W, H)


def matiere(m, val):
    c, b, o = (np.array(v, float) for v in m)
    v = np.clip(val, 0, 1)[..., None]
    lo = o + (b - o) * smooth(v / 0.6)
    return np.where(v < 0.6, lo, b + (c - b) * smooth((v - 0.6) / 0.4))


# v7 : sang visqueux, pas plastique. Deux peaux peintes en continu (azimut θ en largeur, profil s en hauteur) :
# « peau » (minces : brins, filets, gouttes, bourrelets) en rouge profond, « poche » (masse épaisse) presque noire.
# Ce qui faisait plastique en v6 (mesuré sur les captures 23.22–23.23) : valeur uniforme et claire, reflet large et doux
# (matcap _m rose sur toute la poche), forme d'œuf parfaite. Ici : coulures verticales, sillons sombres le long des brins,
# reflets en petits traits nets et cassés qui suivent les coulures, bas plus sombre, haut plus mince et plus rouge.
N_P, NR_P = 32, 32            # poche : facettes autour, rangs le long du profil
CW, CH = 4, 4                 # texels par facette (peau des minces)
CWP, CHP = 8, 6               # texels par facette (poche) : reflets de 1–2 texels ≈ 2–3 px
TH_L = math.radians(225.0)    # azimut du reflet : vers le témoin (−X, −Z)
Y_S = Y_HAUT - 1.25
HS = 47.5 * K_SAC
RT, RMAX, S_VENTRE = 4.6 * K_SAC, 14.0 * K_SAC, 0.68      # v7 : col plus fin, ventre plus bas (oignon qui pend)
S_FIN = 0.9973                # bas de la poche fermé par une calotte ronde (rayon 0,12 × RMAX)
NB, TW = int(os.environ.get("NBRINS", 14)), 0.35             # brins (rubans) enroulés sur la poche : nombre, torsion moyenne (rad du haut au bas)
BRIN_TH = [2 * math.pi * (f + 0.3) / NB + 0.18 * math.sin(2.3 * f) for f in range(NB)]
BRIN_TW = [TW + 0.18 * math.sin(1.7 * f + 0.5) for f in range(NB)]


def R_sac(s):
    if s < S_VENTRE:
        return RT + (RMAX - RT) * math.sin(math.pi / 2 * s / S_VENTRE)
    return RMAX * math.sqrt(max(0.0, 1 - ((s - S_VENTRE) / (1 - S_VENTRE)) ** 2))


def bosse(th, s):
    """Irrégularité de la poche (facteur sur le rayon) : bosses lentes, deux lobes qui pendent en bas, asymétrie."""
    lob = (np.maximum(0, np.cos(th - 0.9)) ** 3 + 0.8 * np.maximum(0, np.cos(th - 3.6)) ** 4
           + 0.5 * np.maximum(0, np.cos(th - 2.3)) ** 6)
    b = (1 + 0.09 * np.sin(3 * th + 1.3 + 2.2 * s) + 0.07 * np.sin(5 * th - 0.7 + 4.1 * s) * s
         + 0.07 * np.sin(2 * th + 0.4 + 1.5 * s) + 0.3 * lob * smooth((s - 0.5) / 0.3) - 0.08 * smooth((s - 0.2) / 0.2) * np.maximum(0, np.cos(th - 5.2)) ** 2)
    return b


def centre_sac(s):
    """Axe de la poche : elle penche et s'affaisse d'un côté (gravité, pas un œuf de révolution)."""
    return np.array((0.11 * RMAX * s ** 2, 0.0, -0.07 * RMAX * s ** 2.5))


_ss = np.linspace(0, S_FIN, 4000)
_pr = np.array([(R_sac(v), -HS * v) for v in _ss])
_al = np.concatenate(([0], np.cumsum(np.hypot(*np.diff(_pr, axis=0).T))))
S_ROWS = list(np.interp(np.linspace(0, _al[-1], NR_P + 1), _al, _ss))      # rangs à pas constant le long du profil


def _wrapd(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def _traits(th, s, seed):
    """Reflets mouillés : petits traits nets, verticaux (le long des coulures), cassés en tronçons."""
    sp = np.zeros_like(th)
    for i, (dth, w, f, ph) in enumerate(((0.32, 0.05, 9.0, 0.3), (0.12, 0.035, 13.0, 1.7), (0.52, 0.03, 7.0, 4.1),
                                         (-2.6, 0.04, 11.0, 2.2), (0.22, 0.025, 17.0, 5.0))):
        dth = dth + 0.05 * np.sin(s * 6 + seed + i)
        cut = smooth((np.sin(s * f * 1.8 + ph + seed) * np.sin(s * f * 0.7 + 2 * ph) - 0.25) / 0.2)      # tronçons courts
        sp = np.maximum(sp, (0.95 if i < 3 else 0.55) * np.exp(-(_wrapd(th - TH_L - dth) / w) ** 2) * cut)
    return sp


def peau_val(th, s):
    """Minces (brins, filets) : valeur (0..1) et force du reflet en (azimut, profil)."""
    c = np.cos(th - TH_L)
    v = 0.44 + 0.12 * c - 0.08 * s + 0.05 * np.sin(7 * th + 3 * s)
    sp = _traits(th, s, 0.0) * smooth((s - 0.05) / 0.1) * smooth((0.95 - s) / 0.08)
    return v, sp


def peau_tex():
    W, H = N_P * CW, NR_P * CH
    x, y = grille(W, H)
    th = (x + 1) / 2 * 2 * np.pi
    fr = (1 - y) / 2 * NR_P
    j = np.clip(np.floor(fr).astype(int), 0, NR_P - 1)
    S = np.array(S_ROWS)
    s = S[j] + (fr - j) * (S[j + 1] - S[j])
    v, sp = peau_val(th, s)
    col = matiere(SANG_FIN, v)
    col = col + (SPEC - col) * np.clip(sp, 0, 1)[..., None]
    return reduire(col, np.ones_like(x), W, H, seuil=110)


def poche_tex():
    """Masse épaisse : presque noire, coulures verticales, sillons sombres de part et d'autre des brins, haut plus mince
    (rouge qui transparaît), bas plus sombre, reflets en traits nets."""
    W, H = N_P * CWP, NR_P * CHP
    x, y = grille(W, H)
    th = (x + 1) / 2 * 2 * np.pi
    fr = (1 - y) / 2 * NR_P
    j = np.clip(np.floor(fr).astype(int), 0, NR_P - 1)
    S = np.array(S_ROWS)
    s = S[j] + (fr - j) * (S[j + 1] - S[j])
    c = np.cos(th - TH_L)
    v = 0.30 + 0.12 * c - 0.10 * smooth((s - 0.55) / 0.4) + 0.2 * np.clip(1 - s / 0.14, 0, 1)      # masse plus sombre que ses brins
    cou = (0.07 * np.sin(13 * th + 0.5 * np.sin(5 * s + th)) + 0.05 * np.sin(23 * th + 2.0 + 0.8 * s)
           + 0.04 * np.sin(7 * th - 1.0 + 1.5 * s))      # coulures presque verticales (suivent les colonnes de facettes)
    v = v + cou * smooth(s / 0.1)
    # v7 : pas de sillons le long des brins : en diagonale, ils crénelaient aux recouvrements des facettes
    v = v - 0.12 * np.exp(-((s - 0.985) / 0.03) ** 2)
    sp = 0.55 * _traits(th, s, 1.3) * smooth((s - 0.08) / 0.1) * smooth((0.9 - s) / 0.1)      # les brins portent l'essentiel des reflets
    col = matiere(SANG, v)
    col = col + (SPEC - col) * np.clip(sp, 0, 1)[..., None]
    return reduire(col, np.ones_like(x), W, H, seuil=110)


def bourrelet():
    """Sang qui file sous une jointure (demi-tube) : α en largeur (0 = côté, π/2 = dessous), longueur en hauteur."""
    x, y = grille(32, 32)
    al = (x + 1) / 2 * np.pi
    u = (1 - y) / 2
    v = 0.36 + 0.14 * np.sin(al) + 0.05 * np.sin(u * 9 + al)
    sp = 0.9 * np.exp(-((al - 1.15) / 0.08) ** 2) * smooth((np.sin(u * 11 + 0.6) - 0.1) / 0.3)
    col = matiere(SANG_FIN, v)
    col = col + (SPEC - col) * np.clip(sp, 0, 1)[..., None]
    return reduire(col, np.ones_like(x), 32, 32, seuil=110)


def calotte(N):
    """Fond rond d'une goutte ou de la poche, vu d'en dessous."""
    x, y = grille(N, N)
    r = np.hypot(x, y)
    v = 0.22 + 0.06 * (1 - r)
    sp = 0.45 * np.exp(-(np.hypot((x + 0.3) / 0.22, (y + 0.3) / 0.06)) ** 2)      # un trait net, pas une tache
    col = matiere(SANG, v)
    col = col + (SPEC - col) * np.clip(sp, 0, 1)[..., None]
    return reduire(col, (r < 0.985).astype(float), N, N, seuil=110)


def flaque(N):
    """Flaque lisse : contour rond irrégulier, reflet large et doux, bord un peu plus clair (ménisque)."""
    x, y = grille(N, N)
    r = np.hypot(x, y)
    ph = np.arctan2(y, x)
    bord = 0.86 + 0.06 * np.sin(5 * ph + 0.7) + 0.035 * np.sin(9 * ph + 2.1)
    v = 0.26 - 0.06 * r / bord + 0.22 * np.exp(-((r / bord - 0.93) / 0.05) ** 2)
    sp = 0.8 * np.exp(-(np.hypot((x + 0.3) / 0.3, (y - 0.25) / 0.05)) ** 2)
    col = matiere(SANG, v)
    col = col + (SPEC - col) * np.clip(sp, 0, 1)[..., None]
    a = smooth((bord - r) / 0.04) * 0.92
    return reduire(col, a, N, N, amax=232)


def matcap(N=128):
    """Matcap du sang (calque _m) : noir partout (le reflet s'ajoute), lueur large et douce en haut à gauche, liseré."""
    x, y = np.meshgrid((np.arange(N) + 0.5) / N * 2 - 1, 1 - (np.arange(N) + 0.5) / N * 2)
    r = np.hypot(x, y)
    f = 0.55 * np.exp(-(np.hypot(x + 0.32, y - 0.38) / 0.42) ** 2) + 0.25 * np.exp(-((r - 0.9) / 0.08) ** 2)
    col = np.array((255, 150, 130), float)[None, None] * np.clip(f, 0, 1)[..., None]
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = 255
    return out


def disque_sol_glow(N):
    x, y = grille(N, N)
    r = np.hypot(x, y)
    f = 0.85 * np.exp(-(r / 0.55) ** 2) + 0.5 * np.exp(-((r - 0.8) / 0.07) ** 2)
    f *= smooth((0.99 - r) / 0.1)
    return additif(GLOW[None, None] * 0.42 * f[..., None], N, N)


def voile_f(W, H):
    x, y = grille(W, H)
    Y = (y + 1) / 2
    f = np.exp(-(x / 0.75) ** 2) * smooth(Y / 0.15) * (0.35 + 0.65 * Y) * smooth((1 - Y) / 0.12)
    return additif(GLOW[None, None] * 0.2 * f[..., None], W, H)


def goutte_p(N):
    x, y = grille(N, N)
    r = np.hypot(x / 0.55, (y + 0.25) / 0.6)
    pointe = (np.abs(x) < 0.55 * np.clip((0.95 - y) / 1.2, 0, 1)) & (y > -0.25)
    a = (r < 1) | pointe
    v = 0.45 + 0.5 * np.exp(-(np.hypot(x + 0.18, y + 0.1) / 0.18) ** 2)
    return reduire(matiere(SANG, v), a.astype(float), N, N, seuil=110)


def etincelle_p(N):
    x, y = grille(N, N)
    a = np.hypot(x, y) < 0.8
    col = np.array((255, 200, 196), float)[None, None] * np.ones(x.shape + (1,))
    return reduire(col, a.astype(float), N, N, seuil=110)


# ------------------------------------------------------------------ atlas
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
OCC = np.zeros((TEX, TEX), bool)
OCC[TEX - 4:, TEX - 4:] = True


def poser(nom, im):
    h, w = im.shape[:2]
    for y in range(0, TEX - h + 1, 8):
        for x in range(0, TEX - w + 1, 8):
            if not OCC[y:y + h, x:x + w].any():
                tex[y:y + h, x:x + w] = im
                OCC[y:y + h, x:x + w] = True
                UV[nom] = (x, y, x + w, y + h)
                return
    raise AssertionError("atlas plein : " + nom)


poser("panneau", panneau())
poser("panneau_lueur", panneau_lueur())
poser("peau", peau_tex())
poser("poche", poche_tex())
poser("bourrelet", bourrelet())
poser("calotte", calotte(48))      # v7 : reflet du fond en trait fin, pas un pavé de texels
poser("sol_glow", disque_sol_glow(96))
poser("flaque", flaque(96))
poser("voile", voile_f(48, 96))
poser("p_goutte", goutte_p(16))
poser("p_etincelle", etincelle_p(8))
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert not tex[TEX - 4:TEX - 2, TEX - 4:TEX - 2, 3].any()
TRANS_UV = ("panneau", "flaque")
_hors = tex[..., 3].copy()
for k in TRANS_UV:
    x0, y0, x1, y1 = UV[k]
    _hors[y0:y1, x0:x1] = 0
assert set(np.unique(_hors)) <= {0, 255}

# Calque _e : panneaux (fond et liseré lisibles de nuit, texte sombre), un peu de reflet sur le sang, rien sous les add_.
_e = np.zeros((TEX, TEX, 4), np.uint8)
for k, (x0, y0, x1, y1) in UV.items():
    if k in ("panneau_lueur", "sol_glow", "voile"):
        continue
    w = tex[y0:y1, x0:x1].astype(float)
    rgb = w[..., :3]
    if k == "panneau":
        lis = (rgb[..., 2] > 160) & (rgb[..., 0] > 240)
        txt = (rgb[..., 1] < 70) & (rgb[..., 0] > 180)
        jnt = rgb[..., 0] < 170
        f = np.where(lis, 0.7, np.where(txt, 0.12, np.where(jnt, 0.15, 0.42)))
    elif k == "p_etincelle":
        f = np.full(rgb.shape[:2], 0.6)
    elif k in ("peau", "poche", "bourrelet", "calotte"):
        # v7 : sang de nuit = rouge sombre (lumière rouge de l'alerte), reflets en petits traits ; jamais rose
        f = np.where(rgb[..., 1] > 120, 0.45, 0.5)
    else:
        f = np.where(rgb[..., 0] > 200, 0.3, 0.06)
    _e[y0:y1, x0:x1, :3] = np.clip(rgb * f[..., None], 0, 255).astype(np.uint8)
    _e[y0:y1, x0:x1, 3] = (w[..., 3] > 0) * 255
_e[_e[..., 3] == 0, :3] = 0


def b64(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


# v6 : reflets sur le sang seulement (guide 5 quater : masque _r lu par face, matcap _m ≤ 256²). Essai, à juger en jeu ;
# REFLETS_SANG = False les retire sans toucher au reste.
REFLETS_SANG = False     # v7 : coupés, le matcap rose large faisait « plastique » (voir docstring)
_r = np.zeros((TEX, TEX, 4), np.uint8)
for k in ("peau", "bourrelet", "calotte"):
    x0, y0, x1, y1 = UV[k]
    _r[y0:y1, x0:x1, :3] = 150
_r[..., 3] = 255
_m = matcap(128)
Image.fromarray(tex, "RGBA").save(f"{NOM}.png", optimize=True)
if REFLETS_SANG:
    Image.fromarray(_r, "RGBA").save(f"{NOM}_r.png", optimize=True)
    Image.fromarray(_m, "RGBA").save(f"{NOM}_m.png", optimize=True)
Image.fromarray(_e, "RGBA").save(f"{NOM}_e.png", optimize=True)
tex_b64, tex_e_b64 = b64(Image.fromarray(tex, "RGBA")), b64(Image.fromarray(_e, "RGBA"))


# ------------------------------------------------------------------ géométrie
def nuid():
    return str(_uuid.uuid4())


def rot_matrix(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def euler(R):
    """Angles (degrés) de R = Rz·Ry·Rx, avec contrôle de reconstruction."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(R[2, 0]) > 1 - 1e-9:          # cardan bloqué (v6 : facettes dont la largeur suit ±Z) : rx = 0
        rx, rz = 0.0, math.atan2(-R[0, 1], R[1, 1])
    else:
        rx = math.atan2(R[2, 1], R[2, 2])
        rz = math.atan2(R[1, 0], R[0, 0])
    e = tuple(math.degrees(v) for v in (rx, ry, rz))
    assert np.allclose(rot_matrix(*e), R, atol=1e-6)
    return e


class G:
    def __init__(self, nom, origin, parent=None, rotation=None):
        assert len(nom) <= 64
        self.nom, self.origin, self.uuid, self.enfants = nom, [round(float(v), 4) for v in origin], nuid(), []
        self.rotation, self.parent = rotation, parent
        if parent is not None:
            parent.enfants.append(self)

    def json(self):
        d = {"name": self.nom, "origin": self.origin, "uuid": self.uuid,
             "children": [c.json() if isinstance(c, G) else c for c in self.enfants]}
        if self.rotation:
            d["rotation"] = [round(float(v), 4) for v in self.rotation]
        return d


elements = []


def cube(g, nom, a, b, faces, origin=None, rot=None):
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in a], "to": [round(float(v), 4) for v in b],
         "origin": [round(float(v), 4) for v in (origin if origin is not None else (np.add(a, b) / 2))], "box_uv": False,
         "faces": {k: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for k, uv in faces.items()}}
    if rot:
        e["rotation"] = [round(float(v), 4) for v in rot]
    elements.append(e)
    g.enfants.append(e["uuid"])


def plaque(g, nom, c, w, h, uv, face="south", ep=0.15):
    c = np.asarray(c, float)
    if face in ("south", "north"):
        a, b = c - (w / 2, h / 2, ep / 2), c + (w / 2, h / 2, ep / 2)
    else:
        a, b = c - (w / 2, ep / 2, h / 2), c + (w / 2, ep / 2, h / 2)
    cube(g, nom, a, b, {face: uv}, origin=c)


def prisme(g, nom, c, rayon, y0, y1, uv_cote, uv_bout, decal=0.0, bouts=True):
    """Prisme à 8 pans (2 cubes à 45°, le second rentré de 0,1 px aux bouts), décalé de `decal` degrés en lacet."""
    c = np.asarray(c, float)
    for i, (ang, ins) in enumerate(((decal, 0.0), (decal + 45, 0.1))):
        a = (c[0] - rayon, y0 + ins, c[2] - rayon)
        b = (c[0] + rayon, y1 - ins, c[2] + rayon)
        f = {k: uv_cote for k in ("north", "south", "east", "west")}
        f["up"] = uv_bout if bouts else CLEAR
        f["down"] = uv_bout if bouts else CLEAR
        cube(g, f"{nom}_{i}", a, b, f, origin=(c[0], (y0 + y1) / 2, c[2]), rot=(0, ((ang + 180) % 360) - 180, 0) if ang else None)


EMIT = {}


def emit(sorte, pos, parent, nom=None):
    lst = EMIT.setdefault(sorte, [])
    n = nom or ("emit_" + sorte + (str(len(lst) + 1) if lst else ""))
    g = G(n, pos, parent)
    c = G("ctrl_emit", pos, g)
    lst.append((g, c))
    return g


EFFET = G("effet", (0, 0, 0))
JOUEUR = G("joueur", (0, 0, 0))

# --- plafond d'alvéoles allongées (colonnes décalées d'une demi-hauteur, comme sur la scène)
TXT_U_INV, TXT_V_INV = False, False      # sens du texte vu d'en dessous (réglé sur l'aperçu, avant le retournement pour le jeu)


def uv_panneau(k):
    x0, y0, x1, y1 = UV[k]
    if TXT_U_INV:
        x0, x1 = x1, x0
    if TXT_V_INV:
        y0, y1 = y1, y0
    return [x0, y0, x1, y1]


PLAF = G("plafond", (0, 0, 0), EFFET)
DXC = PW * (1 - TIP)                     # pas entre colonnes
TUILES = []
for ci in range(-7, 8):
    xc = ci * DXC
    for ri in range(-16, 17):
        zc = ri * PH + (PH / 2 if ci % 2 else 0.0)
        r = math.hypot(xc, zc)
        if r > R_CIEL:
            continue
        rax = ri - (ci - (ci & 1)) // 2          # coordonnées axiales : 3 couleurs, deux voisines jamais à la même hauteur
        TUILES.append([xc, zc, r, (ci - rax) % 3])
TUILES.sort(key=lambda p: math.hypot(p[0] - SEED_XZ[0], p[1] - SEED_XZ[1]))
D_MAX = max(math.hypot(p[0] - SEED_XZ[0], p[1] - SEED_XZ[1]) for p in TUILES)
V_LOC = [(PW / 2, 0.0), (PW / 2 - TIP * PW, PH / 2), (-(PW / 2 - TIP * PW), PH / 2), (-PW / 2, 0.0),
         (-(PW / 2 - TIP * PW), -PH / 2), (PW / 2 - TIP * PW, -PH / 2)]
ALV = []
CADRES = {}          # i -> (centre, matrice) des alvéoles proches du centre (support des perles et des veines)
for i, (xc, zc, r, coul) in enumerate(TUILES):
    yc = y_dome(r)
    pente = 2 * (Y_HAUT - Y_BORD) * r / (R_CIEL + 4) ** 2
    n = np.array((pente * xc / max(r, 1e-6), 1.0, pente * zc / max(r, 1e-6)))
    n /= np.linalg.norm(n)
    ax = np.array((n[2], 0.0, -n[0]))
    ang = math.acos(n[1])
    if np.linalg.norm(ax) < 1e-9:
        R = np.eye(3)
    else:
        ax /= np.linalg.norm(ax)
        K_ = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
        R = np.eye(3) + math.sin(ang) * K_ + (1 - math.cos(ang)) * K_ @ K_
    rot = euler(R)
    c = np.array((xc, yc, zc))
    k_ = 1 / math.sqrt(math.cos(ang))    # rattrape en partie le rétrécissement apparent dû à l'inclinaison
    w, h = PW * k_, PH * k_
    o = 0.22 * coul
    tg = G(f"alv{i}", c, PLAF, rotation=rot)
    tt = G(f"trans_alv{i}", c, tg)
    cube(tt, f"alv{i}", c + (-w / 2, o - 0.05, -h / 2), c + (w / 2, o + 0.05, h / 2),
         {"down": uv_panneau("panneau"), "up": uv_panneau("panneau"), "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR})
    ta = G(f"add_alv{i}", c, tg)
    cube(ta, f"alv{i}_lueur", c + (-w / 2, o - 0.75, -h / 2), c + (w / 2, o - 0.62, h / 2),
         {"down": UV["panneau_lueur"], "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR})
    ca = G("ctrl_alpha", c, ta)
    ALV.append((tg, ta, ca, c, math.hypot(xc - SEED_XZ[0], zc - SEED_XZ[1]), coul))
    if r < 30 * EZ:
        CADRES[i] = (c, R)
N_ALV = len(ALV)

# --- v6 : surfaces lisses. Chaque goutte, filet et la poche sont des surfaces de révolution (ou des tubes) faites de
# facettes : une plaque par facette, dont la face extérieure épouse le quadrilatère entre deux anneaux (rangs bout à
# bout, colonnes impaires décalées le long de leur normale : jamais deux faces voisines coplanaires), peinte avec la
# peau continue. Fond fermé par une calotte ronde découpée par alpha (pas de moulinet ni de trou vu d'en dessous).
def facette(g, nom, a, b, c, d, uv, axe, decal=0.0, ep=0.3):
    """a-b : bord côté racine, c-d : bord suivant ; a→b = sens des facettes ; axe : point de l'axe (normale vers l'extérieur)."""
    ex = (b - a) + (d - c)
    ey = (a + b) / 2 - (c + d) / 2
    h = float(np.linalg.norm(ey))
    ex = ex / np.linalg.norm(ex)
    ey = ey - (ey @ ex) * ex
    ey /= np.linalg.norm(ey)
    ez = np.cross(ex, ey)
    m = (a + b + c + d) / 4
    u0, v0, u1, v1 = uv
    if ez @ (m - axe) < 0:
        ex, ez = -ex, -ez
        u0, u1 = u1, u0
    w = max(np.linalg.norm(b - a), np.linalg.norm(d - c)) * 1.03 + 0.06
    m = m + ez * decal
    cube(g, nom, m + (-w / 2, -h / 2, -ep), m + (w / 2, h / 2, 0), {"south": [u0, v0, u1, v1]}, origin=m,
         rot=euler(np.column_stack((ex, ey, ez))))


def anneaux(C, rayons, N, ref=(0.0, 0.0, 1.0)):
    """Anneaux de N+1 points autour de la courbe C (racine → bout). A × B = −T : facettes orientées vers l'extérieur."""
    C = [np.asarray(c, float) for c in C]
    n = len(C)
    P = []
    for j in range(n):
        T = C[min(j + 1, n - 1)] - C[max(j - 1, 0)]
        T /= np.linalg.norm(T)
        A = np.asarray(ref, float) - (np.asarray(ref, float) @ T) * T
        A /= np.linalg.norm(A)
        B = np.cross(A, T)
        P.append([C[j] + rayons[j] * (math.cos(2 * math.pi * k / N) * A + math.sin(2 * math.pi * k / N) * B) for k in range(N + 1)])
    return C, P


def surface(g, nom, C, P, uvf, decal=0.15):
    for j in range(len(P) - 1):
        ax_ = (C[j] + C[j + 1]) / 2
        for k in range(len(P[j]) - 1):
            facette(g, f"{nom}.{j}.{k}", P[j][k], P[j][k + 1], P[j + 1][k], P[j + 1][k + 1], uvf(j, k), ax_, decal=decal * (k % 2))


def calotte_bas(g, nom, centre, r):
    c = np.asarray(centre, float)
    cube(g, nom, c - (r, 0.15, r), c + (r, 0.15, r), {"down": UV["calotte"]}, origin=c)


U_P, V_P = UV["peau"][0], UV["peau"][1]


def uv_col(k, n, j):
    """Case de la peau : facette k sur n autour, rang j."""
    return [U_P + N_P * CW * k / n, V_P + CH * j, U_P + N_P * CW * (k + 1) / n, V_P + CH * (j + 1)]


def rang_de(s):
    return int(np.clip(np.searchsorted(S_ROWS, s) - 1, 0, NR_P - 1))


# --- sang aux jointures : bourrelets lisses (demi-tubes) le long des arêtes, gouttes renflées aux sommets
SUINT = G("suintement", (0, 0, 0), EFFET)
VEINES, PERLES = [], []
vus_aretes, vus_sommets = set(), set()
UB = UV["bourrelet"]
for i, (c, R) in sorted(CADRES.items(), key=lambda kv: math.hypot(kv[1][0][0], kv[1][0][2])):
    vf = None
    for k in range(6):
        (ax_, az_), (bx_, bz_) = V_LOC[k], V_LOC[(k + 1) % 6]
        A = c + R @ np.array((ax_, 0, az_))
        B = c + R @ np.array((bx_, 0, bz_))
        m = (round((A[0] + B[0]) / 2, 1), round((A[2] + B[2]) / 2, 1))
        ra = math.hypot(*m)
        if ra < 14 * EZ and m not in vus_aretes:
            vus_aretes.add(m)
            vf = vf or G(f"vf{i}", c, SUINT, rotation=euler(R))
            L = math.hypot(bx_ - ax_, bz_ - az_)
            L *= 0.35 + 0.4 * ((len(VEINES) * 0.618) % 1)        # coulée partielle depuis le sommet
            psi = math.degrees(math.atan2(-(bz_ - az_), bx_ - ax_))
            dy = -0.13 * (k % 3)
            org = c + (ax_, -1.0 + dy, az_)
            g = G(f"veine{len(VEINES)}", org, vf, rotation=(0, psi, 0) if abs(psi) > 1e-6 else None)
            rb = 0.5 * KS
            xs = [-0.3 * rb, 0.2 * L, 0.5 * L, 0.8 * L, L]
            rs_ = [rb * f for f in (0.9, 1.0, 0.92, 0.72, 0.28)]

            def pt(x_, r_, a_, org=org):
                return org + (x_, -r_ * math.sin(a_), r_ * math.cos(a_))
            for ii in range(4):
                for kk in range(4):
                    a0, a1 = math.pi * kk / 4, math.pi * (kk + 1) / 4
                    facette(g, f"vn{len(VEINES)}.{ii}.{kk}", pt(xs[ii], rs_[ii], a0), pt(xs[ii], rs_[ii], a1),
                            pt(xs[ii + 1], rs_[ii + 1], a0), pt(xs[ii + 1], rs_[ii + 1], a1),
                            [UB[0] + 8 * kk, UB[1] + 8 * ii, UB[0] + 8 * kk + 8, UB[1] + 8 * ii + 8],
                            org + ((xs[ii] + xs[ii + 1]) / 2, 0, 0), decal=0.12 * (kk % 2))
            VEINES.append((g, ra))
        s_ = (round(A[0], 1), round(A[2], 1))
        rs = math.hypot(*s_)
        if 6.5 * EZ < rs < 30 * EZ and s_ not in vus_sommets:
            vus_sommets.add(s_)
            PERLES.append((c + R @ np.array((ax_, -1.05, az_)), rs))

# gouttes : une sur quatre sommets, réparties ; profil de goutte renflée (col, ventre, bout rond), 10 facettes × 7 rangs
PERLES = [p for j, p in enumerate(sorted(PERLES, key=lambda p: p[1])) if j % 4 == 0][:16]
PROFIL_P = [(u * KS * 1.5, r * KS * 1.35) for u, r in ((0.0, 0.42), (0.45, 0.5), (1.0, 0.7), (1.6, 1.0), (2.1, 1.08), (2.5, 0.9),
                                           (2.75, 0.55), (2.88, 0.3))]
LB = PROFIL_P[-1][0]
N_G = 10
PERLE_G = []
for n_, (W_, rs) in enumerate(PERLES):
    g = G(f"perle{n_}", W_, SUINT)
    C, P = anneaux([W_ - (0, u, 0) for u, r in PROFIL_P], [r for u, r in PROFIL_P], N_G)
    rows = [rang_de(0.3 + 0.68 * u / LB) for u, r in PROFIL_P]
    surface(g, f"pl{n_}", C, P, lambda j, k, rows=rows: uv_col(k, N_G, rows[j]), decal=0.1)
    calotte_bas(g, f"pl{n_}c", W_ - (0, LB + 0.1, 0), PROFIL_P[-1][1] * 1.04)
    if n_ % 2 == 0:
        emit("goutte", W_ - (0, LB + 0.4, 0), g)
    PERLE_G.append((g, rs))

# --- poche (v7) : masse irrégulière et asymétrique (bosses, deux lobes qui pendent, axe qui penche), 32 × 40 facettes
# peintes de la peau « poche » presque noire ; douze brins enroulés en relief sur sa surface (les filets qui se sont
# rejoints, encore visibles comme sur la scène) ; trois gouttes pendantes sous le fond qui s'étirent.
SAC = G("poche", (0, Y_S, 0), EFFET)
PEAU = G("peau", (0, Y_S, 0), SAC)
U_K, V_K = UV["poche"][0], UV["poche"][1]


def pt_sac(th, v, f=1.0):
    c = centre_sac(v)
    r = R_sac(v) * float(bosse(th, v)) * f
    return np.array((c[0] + r * math.sin(th), Y_S - HS * v, c[2] + r * math.cos(th)))


PS = [[pt_sac(2 * math.pi * k / N_P, v) for k in range(N_P + 1)] for v in S_ROWS]
CS = [np.array((centre_sac(v)[0], Y_S - HS * v, centre_sac(v)[2])) for v in S_ROWS]
surface(PEAU, "pc", CS, PS, lambda j, k: [U_K + CWP * k, V_K + CHP * j, U_K + CWP * (k + 1), V_K + CHP * (j + 1)])
C_FOND = CS[-1] - (0, 0.1, 0)
calotte_bas(PEAU, "pc_fond", C_FOND, R_sac(S_FIN) * 1.25)
for k in range(3):
    emit("goutte", C_FOND + (0.4 * R_sac(S_FIN) * math.cos(k * 2.1), -0.5, 0.4 * R_sac(S_FIN) * math.sin(k * 2.1)), PEAU)
Y_BAS_SAC = Y_S - HS * S_FIN

# gouttes pendantes sous le fond (s'étirent mollement, ne tombent pas sur la caméra : elles restent accrochées)
PROFIL_D = [(u * 7.0, r * 5.2) for u, r in ((0.0, 0.55), (0.5, 0.42), (1.1, 0.36), (1.7, 0.55), (2.2, 0.95), (2.6, 1.05),
                                           (2.95, 0.85), (3.15, 0.5), (3.25, 0.22))]
PEND = []
for n_, (th, sv) in enumerate(((0.9, 0.93), (3.6, 0.95), (2.2, 0.975))):
    W_ = pt_sac(th, sv, 0.55)
    g = G(f"pend{n_}", W_, PEAU)
    C, P = anneaux([W_ - (0, u, 0) for u, r in PROFIL_D], [r * (1 - 0.18 * n_) for u, r in PROFIL_D], 10)
    rows = [rang_de(0.3 + 0.65 * u / PROFIL_D[-1][0]) for u, r in PROFIL_D]
    surface(g, f"pd{n_}", C, P, lambda j, k, rows=rows: uv_col(k, 10, rows[j]), decal=0.1)
    calotte_bas(g, f"pd{n_}c", W_ - (0, PROFIL_D[-1][0] + 0.1, 0), PROFIL_D[-1][1] * (1 - 0.18 * n_) * 1.1)
    PEND.append(g)

N_B = 8                       # brins : facettes
BRINS = []


def ruban(g, nom, Cb, nrm, azi, w, h, rows, n=N_B, decal=0.12):
    """Tube aplati (ruban) : demi-largeur w le long de la surface, demi-épaisseur h vers l'extérieur."""
    P = [[Cb[j] + w[j] * math.cos(2 * math.pi * k / n) * azi[j] + h[j] * math.sin(2 * math.pi * k / n) * nrm[j] for k in range(n + 1)]
         for j in range(len(Cb))]
    surface(g, nom, Cb, P, lambda j, k: uv_col(k, n, rows[j]), decal=decal)


for f in range(NB):
    thf, tw = BRIN_TH[f], BRIN_TW[f]
    sv = list(np.linspace(0.004, 0.93, 16))      # s'arrêtent avant le fond (au-delà, ils se croisaient en hérisson)
    vb = 0.3 + 0.55 * ((f * 0.618) % 1)            # goutte renflée qui glisse le long du brin
    lar = (0.75 + 0.5 * ((f * 0.382) % 1))
    h_ = [(1.6 + 3.2 * math.sin(math.pi * min(1.0, v / 1.1))) * (1 - 0.7 * smooth((v - 0.84) / 0.08)) * lar * (1 + 0.4 * math.exp(-((v - vb) / 0.05) ** 2)) for v in sv]
    w_ = [1.3 * h for h in h_]                     # à peine aplati : un ruban plat crénelait ses bords (plaques en dents de scie)
    Cb, nrm, azi = [], [], []
    for v, h in zip(sv, h_):
        th = thf + tw * v
        c = np.array((centre_sac(v)[0], Y_S - HS * v, centre_sac(v)[2]))
        p = pt_sac(th, v)
        n = (p - c) / np.linalg.norm(p - c)
        a = np.array((math.cos(th), 0.0, -math.sin(th)))
        Cb.append(p + n * (0.8 * h + 0.25 * (f % 3)))      # posés sur la peau : un brin à moitié enfoui la coupait en dents de scie
        nrm.append(n)
        azi.append(a)
    # anneaux perpendiculaires au brin (des anneaux horizontaux sur un brin en biais donnaient des plaques en écailles)
    for j in range(len(Cb)):
        T = Cb[min(j + 1, len(Cb) - 1)] - Cb[max(j - 1, 0)]
        T = T / np.linalg.norm(T)
        n = nrm[j] - (nrm[j] @ T) * T
        nrm[j] = n / np.linalg.norm(n)
        a = np.cross(T, nrm[j])
        azi[j] = a if a @ azi[j] > 0 else -a
    g = G(f"brin{f}", Cb[0], SAC)
    ruban(g, f"br{f}", Cb, nrm, azi, w_, h_, [rang_de(v) for v in sv])
    calotte_bas(g, f"br{f}c", Cb[-1] - (0, 0.1, 0), w_[-1] * 0.95)      # bout rond (une goutte), pas une pointe
    BRINS.append((g, f / NB))

# --- filets (v7) : épais au plafond, s'effilent, ondulent, renflés de gouttes ; ils se cassent en bas (goutte détachée
# qui tombe au sol) au lieu de tiges droites jusqu'au sol
FILETS = G("filets", (0, Y_S, 0), EFFET)
N_F = 8
U_F = [0.0, 0.03, 0.07, 0.12, 0.18, 0.26, 0.34, 0.41, 0.44, 0.47, 0.55, 0.64, 0.68, 0.72, 0.75, 0.762, 0.77, 0.778, 0.786, 0.793, 0.8]


def r_filet(u):
    return (1.4 + 7.0 * math.exp(-u / 0.11) + 1.7 * math.exp(-((u - 0.44) / 0.03) ** 2) + 1.3 * math.exp(-((u - 0.68) / 0.03) ** 2)
            + 2.6 * math.sqrt(max(0.0, 1 - ((u - 0.777) / 0.019) ** 2))) * (1 - 0.7 * smooth((u - 0.79) / 0.01))


FIL, CHUTE = [], []
Y0_F, Y1_F = y_dome(60.0) - 1.5, 1.5      # du plafond (près du col de la poche) au sol
for k in range(6):
    a_ = 2 * math.pi * k / 6 + 0.4
    rr = (11.0 + 1.6 * ((k * 0.618) % 1)) * K_SAC          # 55–63 px : hors des bras du géant (±50), sous le ventre
    x0, z0 = rr * math.sin(a_), rr * math.cos(a_)
    Cf = [(x0 + (3 + 15 * u) * math.sin(u * 8.5 + k), Y0_F + (Y1_F - Y0_F) * u, z0 + (3 + 12 * u) * math.cos(u * 7.0 + 2 * k)) for u in U_F]
    g = G(f"filet{k}", Cf[0], FILETS)
    C, P = anneaux(Cf, [r_filet(u) * (0.85 + 0.3 * ((k * 0.382) % 1)) for u in U_F], N_F)
    rows = [rang_de(0.2 + 0.75 * u) for u in U_F]
    surface(g, f"fl{k}", C, P, lambda j, k_, rows=rows: uv_col(k_, N_F, rows[j]), decal=0.12)
    calotte_bas(g, f"fl{k}c", np.array(Cf[-1]) - (0, 0.1, 0), 0.9)
    if k % 3 != 2:
        emit("goutte", np.array(Cf[-1]) - (0, 0.5, 0), g)
    FIL.append(g)
    # goutte détachée : naît sous le bout du filet et tombe jusqu'au sol
    W_ = np.array(Cf[-1]) - (0, 3.0, 0)
    gc = G(f"chute{k}", W_, FILETS)
    prof = [(u * 1.6, r * 1.6) for u, r in ((0.0, 0.3), (0.8, 0.7), (1.6, 1.0), (2.2, 0.85), (2.6, 0.4))]
    C, P = anneaux([W_ - (0, u, 0) for u, r in prof], [r for u, r in prof], 8)
    surface(gc, f"ch{k}", C, P, lambda j, k_: uv_col(k_, 8, rang_de(0.5 + 0.1 * j)), decal=0.1)
    calotte_bas(gc, f"ch{k}c", W_ - (0, prof[-1][0] + 0.1, 0), prof[-1][1] * 1.1)
    CHUTE.append((gc, float(W_[1]) - 2.0))
L_FIL = Y0_F - Y1_F


# lumière rouge : disque au sol, voile derrière, flaque
SOL = G("sol", (0, 0, 0), EFFET)
ADD_SOL = G("add_sol", (0, 0, 0), SOL)
plaque(ADD_SOL, "sol_lueur", (0, 0.45, 0), 230.0, 230.0, UV["sol_glow"], face="up", ep=0.1)     # la lumière rouge sous le dôme
FLAQUE = G("flaque", (0, 0, 0), EFFET)
TR_FL = G("trans_flaque", (0, 0, 0), FLAQUE)
plaque(TR_FL, "flaque", (0, 0.22, 0), 150.0, 150.0, UV["flaque"], face="up", ep=0.1)     # v6 : la poche entière retombe
for k in range(6):
    a_ = 2 * math.pi * k / 6
    emit("etincelle", (60.0 * math.cos(a_), 0.8, 60.0 * math.sin(a_)), SOL)
for k in range(3):
    a_ = 2 * math.pi * (k + 0.5) / 3
    emit("mc_dust_8c0c1c_15", (16.0 * math.cos(a_), 0.6, 16.0 * math.sin(a_)), FLAQUE, nom="emit_mc_dust_8c0c1c_15")
for k in range(4):
    a_ = 2 * math.pi * (k + 0.25) / 4
    emit("mc_dust_ff8c8c_10", (110.0 * math.cos(a_), y_dome(110) - 3.0, 110.0 * math.sin(a_)), PLAF, nom="emit_mc_dust_ff8c8c_10")
VOILE = G("voile", (0, 0, 0), EFFET)
CAMV = G("camy_voile", (0, 150, 0), VOILE)
ADDV = G("add_voile", (0, 150, 0), CAMV)
plaque(ADDV, "voile", (0, 150, -280.0), 480.0, 280.0, UV["voile"])

# --- particules
PART = {}
PART["goutte"] = G("particle_goutte", (0, 0, 0))
plaque(PART["goutte"], "p_goutte", (0, 1.4, 0), 1.8, 1.8, UV["p_goutte"])     # v5 : vue de loin
PART["etincelle"] = G("particle_etincelle", (0, 0, 0))
plaque(PART["etincelle"], "p_etincelle", (0, 0.9, 0), 0.9, 0.9, UV["p_etincelle"])

outliner = [EFFET.json(), JOUEUR.json()] + [PART[k].json() for k in ("goutte", "etincelle")]
NEMIT = sum(len(v) for v in EMIT.values())
assert NEMIT <= 32, NEMIT


# ------------------------------------------------------------------ animations
def s(v):
    return v if isinstance(v, str) else str(round(float(v) + 0.0, 4))


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


def temps(L, fps=10):
    n = max(2, int(round(L * fps)))
    return [round(L * i / n, 4) for i in range(n + 1)]


def jaillit(t, a, d=0.3, over=0.15):
    """0 → 1 avec dépassement amorti."""
    if t <= a:
        return 0.0
    u = (t - a) / d
    if u >= 2.4:
        return 1.0
    if u <= 1:
        return sm(u, 0, 1) * (1 + over)
    return 1 + over * math.exp(-3.5 * (u - 1)) * math.cos(math.pi * (u - 1) * 1.2)


class Anim:
    def __init__(self, nom, L, loop, fps=12):
        self.nom, self.L, self.loop, self.A = nom, L, loop, {}
        self.T = temps(L, fps)

    def piste(self, g, ch, f, T=None):
        T = self.T if T is None else sorted(set(round(v, 4) for v in T))
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += [kf(ch, t, *f(t)) for t in T]

    def fixe(self, g, ch, v):
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"].append(kf(ch, 0, *v))

    def son(self, t, nom):
        e = self.A.setdefault("effects", {"name": "Effects", "type": "effect", "keyframes": []})
        e["keyframes"].append({"channel": "sound", "data_points": [{"effect": nom, "file": ""}], "time": t})

    def cadence(self, sorte, f, T=None):
        for i, (g, c) in enumerate(EMIT[sorte]):
            self.piste(c, "position", lambda t, i=i: (max(-1.0, min(7.0, f(t, i))), 0, 0), T=T)

    def json(self):
        return {"uuid": nuid(), "name": self.nom, "loop": self.loop, "override": False, "length": self.L, "snapping": 24,
                "selected": self.nom == "arrivee", "animators": self.A}


uni = lambda v: (v, v, v)
Z3 = (0, 0, 0)
TAU = 2 * math.pi


def mol_on_off(on, off, d_on=0.12, d_off=0.16):
    e = f"math.clamp((q.anim_time-{s(on)})/{s(d_on)},0,1)*math.clamp(({s(off)}-q.anim_time)/{s(d_off)},0,1)"
    return (e, e, e)


def alveoles(an, t_on, t_off):
    """t_on(i, d), t_off(i, d) : instants d'allumage et d'extinction de l'alvéole i (d = distance au germe)."""
    for i, (tg, ta, ca, c, d, var) in enumerate(ALV):
        an.fixe(tg, "scale", mol_on_off(t_on(i, d), t_off(i, d)))


def ordre_on(i, d, t0, t_grappe, t_vague, t_fin):
    if i == 0:
        return t0
    if i <= 6:
        return t_grappe + 0.05 * i + 0.02 * (i % 2)
    return t_vague + (t_fin - t_vague) * (max(0.0, d - 10 * EZ) / (D_MAX - 10 * EZ)) ** 0.85 + 0.03 * ((i * 37) % 5)


def pas(t, a, b, L):
    """Instants d'une fenêtre [a, b] (bords compris), avec 0 et L."""
    n = max(2, int(round((b - a) * 16)))
    return [0.0, L] + [a + (b - a) * i / n for i in range(n + 1)]




def cl(a, d):
    return f"math.clamp((q.anim_time-{s(a)})/{s(d)},0,1)"


def dn(b, d):
    return f"math.clamp(({s(b)}-q.anim_time)/{s(d)},0,1)"


def veines_perles(an, t0, t1, toff):
    """Le sang suinte des sommets et file le long des jointures (bourrelet qui s'allonge et s'épaissit) ; aux sommets, les
    gouttes gonflent, s'étirent lentement (scale y) et reviennent d'un coup quand la goutte se détache (particule)."""
    for n_, (g, ra) in enumerate(VEINES):
        a = t0 + (t1 - t0) * (ra / 24 / EZ) * 0.8 + 0.12 * ((n_ * 0.618) % 1)
        e = f"{cl(a, 0.45)}*{dn(toff + 0.3 * ra / 24 / EZ, 0.35)}"
        ep = f"{e}*(0.45+0.55*{cl(a + 0.15, 0.5)})"
        an.fixe(g, "scale", (e, ep, ep))
    for n_, (g, rs) in enumerate(PERLE_G):
        a = t0 + (t1 - t0) * (rs / 30 / EZ) * 0.7 + 0.15 * ((n_ * 0.618) % 1)
        per = 1.0 + 0.5 * ((n_ * 0.382) % 1)
        gg = f"{cl(a, 0.4)}*{dn(toff + 0.3 * rs / 30 / EZ, 0.35)}"
        st = f"math.pow(math.mod(math.max(0,q.anim_time-{s(a + 0.4)}),{s(per)})/{s(per)},2)"
        an.fixe(g, "scale", (f"{gg}*(1-0.22*{st})", f"{gg}*(1+0.9*{st})", f"{gg}*(1-0.22*{st})"))


def brins(an, coule, coule_f, fin=None):
    """Les filets descendent du plafond en cascade (étirement amorti), ondulent mollement, puis sont noyés dans la poche."""
    T = sorted(set(temps(an.L, 14)))
    for f, (g, ph) in enumerate(BRINS):
        a = coule + (coule_f - coule - 0.45) * ((f * 0.618) % 1)

        def sc(t, a=a):
            y = jaillit(t, a, 0.45, 0.1)
            if fin is not None:
                y *= 1 - sm(t, fin, fin + 0.2)
            return (1, y, 1)
        an.piste(g, "scale", sc, T=T)
        an.piste(g, "rotation", lambda t, ph=ph, a=a: (2.5 * math.sin(TAU * (t / 1.7 + ph)) * sm(t, a, a + 0.3),
                                                      0, 2.0 * math.sin(TAU * (t / 2.1 + 0.37 + ph)) * sm(t, a, a + 0.3)), T=T)


def peau(an, nait, gonfle, gonfle_f):
    """Colonne fine qui descend avec les brins, puis gonfle en poche ronde (dépassement amorti)."""
    T = sorted(set(temps(an.L, 16)))

    def f(t):
        h = jaillit(t, nait, 0.55, 0.06)
        w = 0.16 + 0.84 * jaillit(t, gonfle, gonfle_f - gonfle, 0.025)
        return (w * min(1.0, 4 * h), h, w * min(1.0, 4 * h))
    an.piste(PEAU, "scale", f, T=T)
    # v7 : la masse se balance mollement avec ses brins (pivot au plafond, déphasé en x et z) et ses gouttes pendantes s'étirent
    an.piste(SAC, "rotation", lambda t: (1.6 * math.sin(TAU * t / 2.3) * sm(t, gonfle, gonfle + 0.5), 0,
                                          1.2 * math.sin(TAU * (t / 1.7 + 0.31)) * sm(t, gonfle, gonfle + 0.5)), T=T)
    for n_, g in enumerate(PEND):
        def fp(t, n_=n_):
            on = sm(t, gonfle_f - 0.3, gonfle_f + 0.2)
            e = 0.5 + 0.5 * math.sin(TAU * (t / (1.1 + 0.27 * n_) + 0.37 * n_))
            return (on * (1 - 0.15 * e), on * (0.8 + 0.7 * e), on * (1 - 0.15 * e))
        an.piste(g, "scale", fp, T=T)


def tremble(t, debut, fin):
    """Liquide qui tremble : oscillation anisotrope amortie (x et z en opposition), tension juste avant la fin."""
    tr = sm(t, debut, debut + 0.15) * (1 - sm(t, fin, fin + 0.08))
    w = 0.045 * math.sin(TAU * (t - debut) / 0.46) * tr
    w2 = 0.03 * math.sin(TAU * (t - debut) / 0.33 + 1.1) * tr
    tend = bump(t, fin - 0.2, fin - 0.03, fin, fin + 0.06)
    return 1 + w + 0.03 * tend, 1 - 0.5 * w - w2 + 0.06 * tend, 1 - w + w2 + 0.03 * tend


def vide(t, dech):
    """Arrivée : la poche se vide par le bas (le sang retombe en filets) et remonte mollement dans le plafond ;
    le joueur géant est dévoilé des pieds à la tête, la caméra du joueur (au sol, au centre) n'est jamais traversée."""
    if t <= dech:
        return 1.0, 1.0
    u = sm(t, dech, dech + 0.75)
    reb = 0.05 * math.sin(TAU * (t - dech) / 0.3) * math.exp(-4 * (t - dech))
    fin = 1 - sm(t, dech + 0.55, dech + 0.8)            # aplatie, elle ne laisse pas de disque au plafond
    return (1 - 0.42 * u) * (1 + reb) * fin, max(0.0, (1 - u) * (1 - reb))


def poche_ar(an, tremble_d, dech):
    T = sorted(set(temps(an.L, 16) + pas(0, dech, dech + 0.8, an.L)))

    def sc(t):
        x, y, z = tremble(t, tremble_d, dech)
        sx, sy = vide(t, dech)
        return (x * sx, y * sy, z * sx)
    an.piste(SAC, "scale", sc, T=T)


def poche_de(an, tremble_d, avale):
    T = sorted(set(temps(an.L, 16)))

    def sc(t):
        x, y, z = tremble(t, tremble_d, avale)
        a = sm(t, avale, avale + 0.6)
        b = 1 - sm(t, avale + 0.5, avale + 0.75)
        return (x * (1 - 0.45 * a) * b, max(0.0, y * (1 - 0.97 * a)), z * (1 - 0.45 * a) * b)
    an.piste(SAC, "scale", sc, T=T)


def filets_ar(an, dech):
    """Les filets tombent du plafond, près de la poche qui se vide, jusqu'au sol (chute accélérée, léger rebond), puis s'amincissent et gouttent."""
    T = sorted(set(pas(0, dech, dech + 0.7, an.L) + pas(0, dech + 0.8, dech + 1.9, an.L)))
    for k, g in enumerate(FIL):
        d = 0.05 * ((k * 0.618) % 1) * 3

        def sc(t, d=d):
            if t <= dech + d:
                return (0, 0, 0)
            u = min(1.0, (t - dech - d) / 0.42)
            ly = u * u + 0.04 * math.sin(TAU * max(0.0, t - dech - d - 0.42) / 0.35) * math.exp(-5 * max(0.0, t - dech - d - 0.42)) * (u >= 1)
            w = 1 - sm(t, dech + 1.05 + d, dech + 1.8 + d)
            return (w, ly, w)
        an.piste(g, "scale", sc, T=T)
        an.piste(g, "rotation", lambda t, k=k: (1.0 * math.sin(TAU * (t / 0.9 + 0.17 * k)) * sm(t, dech, dech + 0.5),
                                               0, 0.8 * math.sin(TAU * (t / 1.1 + 0.29 * k)) * sm(t, dech, dech + 0.5)), T=T)
    # v7 : le bout de chaque filet se casse en une goutte qui tombe jusqu'au sol (chute accélérée), puis disparaît
    for k, (g, h) in enumerate(CHUTE):
        d = 0.05 * ((k * 0.618) % 1) * 3
        t0 = dech + d + 0.42
        tf = t0 + math.sqrt(h / 260.0)
        T2 = sorted(set([0.0, an.L, t0 - 0.05, t0, tf, tf + 0.05] + [t0 + (tf - t0) * i / 6 for i in range(7)]))
        an.piste(g, "scale", lambda t, t0=t0, tf=tf: uni(1.0 if t0 <= t <= tf else 0.0), T=T2)
        an.piste(g, "position", lambda t, t0=t0, h=h: (0, -min(h, 130.0 * max(0.0, t - t0) ** 2 * 2), 0), T=T2)


# ---- charge (loop 4 s)
LC = 4.0
ch = Anim("charge", LC, "loop")
ch.fixe(JOUEUR, "scale", (1, 1, 1))
ch.piste(JOUEUR, "position", lambda t: (0, 1.6 * (1 - math.cos(TAU * t / LC)), 0))      # lévite d'un souffle, attiré par le ciel
for i, (tg, ta, ca, c, d, coul) in enumerate(ALV):
    if i < 3:
        e = f"math.clamp(0.5+3*math.sin(q.anim_time*180-{s(70 * i)}),0,1)"
        ch.fixe(tg, "scale", (e, e, e))
    else:
        ch.fixe(tg, "scale", Z3)
for g in (SAC, SUINT, FLAQUE, FILETS):
    ch.fixe(g, "scale", Z3)
ch.piste(SOL, "scale", lambda t: uni(0.45 + 0.12 * math.sin(TAU * t / 2)))
ch.piste(VOILE, "scale", lambda t: (0.6, 0.35 + 0.1 * math.sin(TAU * t / 2), 1))
ch.cadence("etincelle", lambda t, i: 0)
ch.cadence("goutte", lambda t, i: -1)
ch.cadence("mc_dust_8c0c1c_15", lambda t, i: -1)
ch.cadence("mc_dust_ff8c8c_10", lambda t, i: 0 if i == 0 else -1)
SORTE_G = [g.parent.nom.rstrip("0123456789_") for g, c in EMIT["goutte"]]      # perle, peau, filet

# ---- arrivee (once 4,9 s)
LA = 4.9
A_COULE, A_COULE_F, A_NAIT = 1.2, 2.0, 1.45
A_GONFLE, A_GONFLE_F, A_TREMBLE, A_JOUEUR, A_DECH = 2.0, 2.5, 2.3, 2.82, 2.78
A_DESC, A_DESC_F = 3.1, 4.5
ar = Anim("arrivee", LA, "once")
alveoles(ar, lambda i, d: ordre_on(i, d, 0.05, 0.32, 0.72, 1.65), lambda i, d: 4.0 + 0.8 * d / D_MAX)
veines_perles(ar, 0.8, 1.5, 3.95)
brins(ar, A_COULE, A_COULE_F)
peau(ar, A_NAIT, A_GONFLE, A_GONFLE_F)
poche_ar(ar, A_TREMBLE, A_DECH)
filets_ar(ar, A_DECH)


ar.piste(JOUEUR, "scale", lambda t: uni(0.0 if t < A_JOUEUR else
                                        ECHELLE_GEANT if t < A_DESC else
                                        ECHELLE_GEANT + (1 - ECHELLE_GEANT) * sm(t, A_DESC, A_DESC_F)),
         T=[0, A_JOUEUR - 0.06, A_JOUEUR] + pas(0, A_DESC, A_DESC_F, LA))
ar.piste(JOUEUR, "position", lambda t: (0, Y_GEANT * (1 - sm(t, A_DESC, A_DESC_F) ** 1.4), 0), T=pas(0, A_DESC, A_DESC_F, LA) + [0.5])
ar.piste(SOL, "scale", lambda t: uni(sm(t, 0.6, 1.6) * (0.8 + 0.25 * bump(t, A_DECH, A_DECH + 0.15, 3.0, 3.4))
                                     * (1 - sm(t, 4.2, 4.85))))
ar.piste(VOILE, "scale", lambda t: (1, sm(t, 0.7, 1.7) * (1 - sm(t, 4.0, 4.7)) + 1e-3, 1))
ar.piste(FLAQUE, "scale", lambda t: uni(sm(t, A_DECH + 0.35, A_DECH + 1.0) * (1 - sm(t, 4.3, 4.85))))
ar.son(0.05, "alveoles_alarme")
ar.son(0.85, "sang_suinte")
ar.son(A_DECH - 0.5, "sang_revele")
ar.cadence("etincelle", lambda t, i: 1 if 0.8 < t < 4.3 else -1)
ar.cadence("goutte", lambda t, i: {"perle": 2 if 1.4 < t < 4.0 else -1, "filet": 4 if A_DECH + 0.4 < t < A_DECH + 1.6 else -1,
                                   "peau": 4 if A_GONFLE_F < t < A_DECH else -1}[SORTE_G[i]])
ar.cadence("mc_dust_8c0c1c_15", lambda t, i: 3 if 3.3 < t < 4.6 else -1)
ar.cadence("mc_dust_ff8c8c_10", lambda t, i: 2 if 0.9 < t < 4.0 else -1)

# ---- depart (once 4,8 s)
LD = 4.8
D_COULE, D_COULE_F, D_GONFLE, D_GONFLE_F, D_TREMBLE = 0.8, 1.4, 1.6, 2.3, 2.0
D_MONTE, D_MONTE_F, D_CACHE, D_AVALE = 1.8, 2.4, 2.5, 2.65
de = Anim("depart", LD, "once")
alveoles(de, lambda i, d: ordre_on(i, d, 0.02, 0.14, 0.38, 1.05), lambda i, d: 3.7 + 0.85 * d / D_MAX)
veines_perles(de, 0.4, 0.95, 3.45)
brins(de, D_COULE, D_COULE_F + 0.3)
peau(de, D_COULE + 0.2, D_GONFLE, D_GONFLE_F)
poche_de(de, D_TREMBLE, D_AVALE)
de.fixe(FILETS, "scale", Z3)
de.piste(JOUEUR, "scale", lambda t: uni((1 + (ECHELLE_GEANT - 1) * sm(t, D_MONTE, D_MONTE_F)) * (0.0 if t >= D_CACHE else 1.0)),
         T=pas(0, D_MONTE, D_MONTE_F, LD) + [D_CACHE - 0.06, D_CACHE])
de.piste(JOUEUR, "position", lambda t: (0, Y_GEANT * sm(t, D_MONTE, D_MONTE_F), 0), T=pas(0, D_MONTE, D_MONTE_F, LD))
de.piste(SOL, "scale", lambda t: uni(sm(t, 0.3, 1.1) * (1 + 0.2 * bump(t, D_MONTE, 2.1, 2.6, 3.0)) * (1 - sm(t, 3.9, 4.6))))
de.piste(VOILE, "scale", lambda t: (1, sm(t, 0.4, 1.2) * (1 - sm(t, 3.7, 4.4)) + 1e-3, 1))
de.fixe(FLAQUE, "scale", Z3)
de.son(0.03, "alveoles_alarme")
de.son(0.45, "sang_suinte")
de.son(D_CACHE - 0.5, "sang_revele")
de.cadence("etincelle", lambda t, i: 1 if 0.4 < t < 4.0 else -1)
de.cadence("goutte", lambda t, i: {"perle": 2 if 0.9 < t < 3.5 else -1, "peau": 3 if D_GONFLE_F < t < D_AVALE + 0.3 else -1,
                                   "filet": -1}[SORTE_G[i]])
de.cadence("mc_dust_8c0c1c_15", lambda t, i: -1)
de.cadence("mc_dust_ff8c8c_10", lambda t, i: 2 if 0.6 < t < 3.8 else -1)

# ---- overlay_alveoles (4 s) : la lueur des alvéoles pulse en vague depuis le germe
LO = 4.0
ov = Anim("overlay_alveoles", LO, "loop")
for i, (tg, ta, ca, c, d, coul) in enumerate(ALV):
    ov.fixe(ca, "position", (f"-0.4+0.4*math.sin(q.anim_time*180-{s(round(d / EZ * 7) % 360)})", 0, 0))


# ---- particules
def part_anim(sorte, L, ch_, f, n=12):
    a = Anim(f"particle_{sorte}_fall", L, "loop")
    a.piste(PART[sorte], ch_, f, T=[round(i * L / n, 4) for i in range(n + 1)])
    return a


pg = part_anim("goutte", 0.8, "scale", lambda t: (1 - 0.12 * math.sin(TAU * t / 0.8), 1 + 0.15 * math.sin(TAU * t / 0.8), 1), n=8)
pe = part_anim("etincelle", 0.5, "scale", lambda t: uni(1 + 0.35 * math.sin(TAU * t / 0.5)), n=8)

ANIMS = [ch.json(), de.json(), ar.json(), ov.json(), pg.json(), pe.json()]
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
if REFLETS_SANG:
    textures += [{"name": f"{NOM}_r.png", "uv_width": TEX, "uv_height": TEX, "source": b64(Image.fromarray(_r, "RGBA"))},
                 {"name": f"{NOM}_m.png", "uv_width": 128, "uv_height": 128, "source": b64(Image.fromarray(_m, "RGBA"))}]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures,
         "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
from uv_horizontal import retourner_pour_jeu
embarquer_sons(model, {"alveoles_alarme": "sons/alveoles_alarme.ogg", "sang_suinte": "sons/sang_suinte.ogg",
                       "sang_revele": "sons/sang_revele.ogg"})
limiter_sons(model, max_effet=3)

os.makedirs(".build", exist_ok=True)
with open(f".build/{NOM}_commejeu.bbmodel", "w") as fh:      # ce que le jeu affichera (faces horizontales non retournées)
    json.dump(model, fh, separators=(",", ":"))
n_ret = retourner_pour_jeu(model)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


def ngroupes(n):
    return 1 + sum(ngroupes(c) for c in n.get("children", []) if isinstance(c, dict))


print(N_ALV, "alvéoles ;", len(VEINES), "bourrelets ;", len(PERLE_G), "gouttes ;", n_ret, "faces horizontales retournées ; bas de la poche y %.1f" % Y_BAS_SAC)
print(len(elements), "cubes ;", sum(ngroupes(n) for n in model["outliner"]), "groupes ; profondeur", max(depth(n) for n in model["outliner"]),
      ";", len(model["animations"]), "anims ;", sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()),
      "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;", NEMIT, "emit_ :", {k: len(v) for k, v in EMIT.items()})
