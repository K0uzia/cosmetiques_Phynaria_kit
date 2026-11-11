"""Pistolet mécanique : tromblon à vapeur victorien tenu dans la main droite, ensemble Steampunk (thème Mécanique). Design original.
Écrit pistolet_steampunk.png, pistolet_steampunk_e.png, pistolet_steampunk_r.png et .build/pistolet_steampunk_brut.bbmodel à côté de ce script.

Crosse de bois sombre veiné sous le poing (comme la poignée des lames), garde et talon de laiton. Devant le poing : carcasse de laiton,
petite chaudière de cuivre (vrai volume octogonal, bandes de laiton rivetées), manomètre sur le flanc extérieur (cadran ambre au calque _e
doux, aiguille dans son groupe), soupape sur le dessus. Tuyau de cuivre avec vanne de la chaudière au manchon du canon.
Canon de laiton coulissant dans le manchon (recul), ressort à boudin entre le manchon et une bague du canon, pavillon évasé en 16 douelles
découpées par alpha (deux étages : gorge puis évasement).

Repère : le canon vise -Z (devant le joueur), s = distance vers l'avant depuis la prise P0, h = hauteur. Le groupe `prise` porte une
légère ouverture vers l'extérieur ; `pistolet` porte la pose d'état ; `recul` porte le coup d'attaque et de blessure (aucun conflit entre
l'état et l'animation jouée par-dessus).

Mouvement mécanique : niveau de pression en crans, chaque cran est un échelon court avec dépassement et rappel (servo), tremblement au
maximum, puis décharge de la soupape (bouffée) et l'aiguille retombe. Toutes les boucles ont un nombre entier de cycles et aucune
transition ne déborde de la fin : début = fin.

Jet et bouffée « cachés » au repos : leur géométrie est construite K fois plus petite, enfouie dans la gorge du canon et dans le chapeau de
soupape ; l'animation les agrandit (scale K). Depuis le 2026-11-08, la géométrie est construite K / F_GEO fois plus petite et
les clés d'échelle sont divisées par F_GEO (repos 1/F_GEO pour la bouffée) : même taille à l'écran, clés ≤ 16 (guide 3 et 7). Les états ne touchent jamais au jet : il reste caché quelle que soit la façon dont le mod
combine `attack` avec l'état.

Remise aux règles du 2026-11-05 (.claude/references/procedures/remise-aux-regles.md ; ancien générateur : .build/gen_avant.py) :
- faces proches : faces étroites des plaques octogonales (toujours dans le volume) transparentes, bouts des longues plaques
  en retrait de 0,11, bagues courtes en anneau ouvert, bandes de la chaudière à 0,12 de la tôle, puis decoller() à pas
  court (0,13 px) : 520 paires de faces à moins de 0,1 px avant, environ 60 après, presque toutes dans le nœud
  tuyau–vanne–bride (gelé : le décollement le déformait) et sur les plaques de vapeur cachées à l'échelle 1/K ;
- métal propre : vert-de-gris et coulures retirés de la chaudière, brossé à ±5 % ;
- particules : emit_mc_poof et emit_mc_white_smoke de nouveau (correctif du mod du 2026-11-04), chacun avec un ctrl_emit
  (-1 dans les états, +5 au tir) ; la vapeur modélisée qui les remplaçait est retirée ;
- event_equip (1,4 s) : l'arme sort de la main, le canon coulisse en place, la pression monte, bouffée de la soupape ;
  sons : celui du tir et un à l'équipement (tools/sons.py, arme).

Fonctions spéciales (docs/guide-cosmetiques.md, sections 4 bis, 5 ter, 6.4) :
- `trans_jet`, `trans_bouffee` : plaques de vapeur en dégradé d'opacité (alpha 1–254), lisibles aussi en cutout (seuil 50 %) ;
- `emit_mc_poof`, `emit_mc_white_smoke` + `ctrl_emit` : particules de Minecraft à la bouche du pavillon, +Y du groupe le long
  du canon, seulement au tir (ctrl_emit non simulé par le renderer) ;
- `ctrl_alpha` (dans trans_jet) : opacité du jet, valeur lue = 1 + position x (0 normal, −1 invisible), comme le guide ;
- sons : `tir_vapeur` embarqué au tir (déclic et jet de vapeur, sons/tir_vapeur.py), `block.piston.contract` à l'équipement ; reflets _r retirés tant que REFLETS = False.
Les animations jouées par-dessus (attack, hurt) sont écrites en écarts : positions et rotations s'ajoutent à l'état, échelles se
multiplient (guide, 6.4) ; elles restent justes si le mod remplace au lieu d'ajouter (aiguille : écart de −3 crans depuis le cran 3).
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # calque _e embarqué (correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu)
NOM = "pistolet_steampunk"
TEX = 512
TAU = 2 * math.pi
K = 16.0            # facteur de réduction du jet et de la bouffée au repos
F_GEO = 2.0         # géométrie du jet et de la bouffée F_GEO fois plus grande, clés scale divisées d'autant (≤ 16, guide 3 et 7)

P0 = np.array((6.0, 11.3, -0.6))     # prise : sous le poing (bras x 4..8, bas du bras y = 12)
YAW_OUT = 4.0                        # ouverture du canon vers l'extérieur (degrés)
H_AXE = 0.4                          # hauteur de l'axe du canon au-dessus de la prise


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


def mech(x, h=1.9):
    """Sinus durci : tient aux extrêmes, passe vite entre les deux."""
    return math.tanh(h * x) / math.tanh(h)


# ------------------------------------------------------------------ matières (fiche de style steampunk)
BRASS = dict(base=(190, 142, 64), hi=(236, 196, 112), low=(112, 76, 32))
COPPER = dict(base=(176, 92, 52), hi=(232, 150, 96), low=(98, 46, 26))
STEEL = dict(base=(78, 82, 92), hi=(136, 140, 150), low=(38, 40, 48))
WOOD = dict(base=(84, 50, 30), hi=(122, 78, 46), low=(40, 22, 14))
AMBRE = np.array((255, 210, 120), np.float32)
AMBRE_B = np.array((220, 150, 50), np.float32)
VAPEUR = np.array((250, 250, 248), np.float32)
VAPEUR_B = np.array((220, 224, 228), np.float32)


def A(c):
    return np.array(c, np.float32)


def cell_noise(h, w, cells_y, cells_x, seed):
    r = np.random.default_rng(seed)
    a = (r.random((cells_y + 2, cells_x + 2)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((w, h), Image.BICUBIC), np.float32) / 255


def finish(col, mask):
    out = np.zeros(mask.shape + (4,), np.uint8)
    c = np.clip(col, 0, 255)
    if mask.any():
        c[~mask] = c[mask].mean(axis=0)
    out[..., :3] = c.astype(np.uint8)
    out[..., 3] = mask * 255
    return out


def rivet(col, x, y, r, metal):
    """Rivet peint : anneau sombre, tête, éclat (≥ 3 texels)."""
    h, w = col.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dd = np.hypot(xx + 0.5 - x, yy + 0.5 - y)
    col[dd <= r + 1.0] = A(metal["low"]) * 0.6
    col[dd <= r] = A(metal["base"])
    col[np.hypot(xx + 0.5 - x + r * 0.35, yy + 0.5 - y + r * 0.35) <= r * 0.5] = A(metal["hi"])


TILES = {}
TRANS = set()        # tuiles autorisées en alpha 1–254 (groupes trans_)


def bar_tile(metal, seed, grooves=3, W=96, H=16):
    a = np.zeros((H, W, 3), np.float32)
    r = np.random.default_rng(seed)
    for yy in range(H):
        q = abs((yy + 0.5) / H - 0.5) * 2
        c = lerp(A(metal["hi"]) * 0.85, A(metal["low"]), q ** 1.1)
        a[yy, :] = lerp(c, A(metal["base"]), 0.45)
    a *= (0.95 + 0.10 * r.random((1, W, 1), np.float32))      # brossé ±5 % (métal propre)
    for x in np.linspace(0, W, grooves + 1)[:-1].astype(int):
        a[:, x:x + 2] = A(metal["base"]) * 0.62
    return finish(a, np.ones((H, W), bool))


def cap_tile(metal, n=16):
    c = A(metal["base"]) * np.ones((n, n, 3), np.float32)
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2)
    c[r > n * 0.39] = A(metal["low"])
    c[r < n * 0.19] = A(metal["hi"])
    return finish(c, np.ones((n, n), bool))


def rib_tile(metal, rm, W=96, H=14, step=24):
    c = np.zeros((H, W, 3), np.float32)
    for yy in range(H):
        c[yy, :] = lerp(lerp(A(metal["base"]), A(metal["hi"]), 0.3), A(metal["low"]), abs((yy + 0.5) / H - 0.5) * 2)
    for x in np.arange(step / 2, W, step):
        rivet(c, x, H / 2, 2.2, rm)
    return finish(c, np.ones((H, W), bool))


def wood_tile(W=96, H=20, seed=31):
    """Bois sombre veiné : fil le long de la pièce, veines claires ondulées, nœud sombre."""
    v = (np.arange(H) + 0.5)[:, None] / H * 2 - 1
    u = (np.arange(W) + 0.5)[None, :] / W
    n1 = cell_noise(H, W, 3, 10, seed)
    n2 = cell_noise(H, W, 8, 40, seed + 1)
    q = np.abs(v) * np.ones((1, W))
    c = lerp(A(WOOD["base"]), A(WOOD["low"]), (q ** 1.4)[..., None])
    c = lerp(c, A(WOOD["hi"]), (np.clip(1 - q * 1.6, 0, 1) * 0.35)[..., None])
    vein = np.sin(v * 9.0 + n1 * 7.0 + u * 2.0) > 0.86
    c[vein] = lerp(c[vein], A(WOOD["hi"]) * 1.05, 0.7)
    dark = np.sin(v * 5.0 + n1 * 5.0 - 1.3) > 0.93
    c[dark] = A(WOOD["low"]) * 0.9
    c *= (0.9 + 0.2 * n2)[..., None]
    knot = np.hypot((u - 0.62) * W / 4.0, v * H / 3.2) < 1
    c[knot] = A(WOOD["low"]) * 0.8
    return finish(c, np.ones((H, W), bool))


def boiler_tile(W=96, H=64, seed=41):
    """Tôle de cuivre : galbe, brossé léger, joint circulaire riveté au milieu, joints sombres (métal propre, sans patine)."""
    r = np.random.default_rng(seed)
    v = (np.arange(H) + 0.5)[:, None] / H * 2 - 1
    streak = np.array(Image.fromarray((r.random((H, W // 10)) * 255).astype(np.uint8), "L").resize((W, H), Image.BILINEAR), np.float32) / 255 - 0.5
    c = A(COPPER["base"]) * np.ones((H, W, 3), np.float32)
    c *= (1 + 0.10 * streak)[..., None]
    c = lerp(c, A(COPPER["hi"]), (np.clip(0.55 - np.abs(v + 0.2), 0, 1) * 0.55 * np.ones((1, W)))[..., None])
    c = lerp(c, A(COPPER["low"]), (np.clip(np.abs(v) - 0.6, 0, 1) * 1.6 * np.ones((1, W)))[..., None])
    xm = W // 2
    c[:, xm - 4:xm + 4] = lerp(c[:, xm - 4:xm + 4], A(COPPER["hi"]), 0.25)     # couvre-joint
    c[:, xm - 5:xm - 4] = A(COPPER["low"]) * 0.7
    c[:, xm + 4:xm + 5] = A(COPPER["low"]) * 0.7
    for y in np.arange(8, H, 16):
        rivet(c, xm, y, 2.4, COPPER)
    c[:2] = A(COPPER["low"]) * 0.8
    c[-2:] = A(COPPER["low"]) * 0.8
    return finish(c, np.ones((H, W), bool))


def frame_tile(W=48, H=32, seed=51):
    """Plaque de carcasse : laiton brossé, biseau clair, filet gravé, 4 rivets de cuivre."""
    r = np.random.default_rng(seed)
    c = A(BRASS["base"]) * np.ones((H, W, 3), np.float32)
    c *= (0.95 + 0.10 * r.random((1, W, 1), np.float32))
    c[:2], c[-2:], c[:, :2], c[:, -2:] = A(BRASS["hi"]), A(BRASS["low"]), A(BRASS["hi"]), A(BRASS["low"])
    c[6:7, 6:-6] = c[-7:-6, 6:-6] = A(BRASS["low"])
    c[6:-6, 6:7] = c[6:-6, -7:-6] = A(BRASS["low"])
    for x, y in ((4.5, 4.5), (W - 4.5, 4.5), (4.5, H - 4.5), (W - 4.5, H - 4.5)):
        rivet(c, x, y, 2.0, COPPER)
    return finish(c, np.ones((H, W), bool))


def bore_tile(n=16):
    c = A(BRASS["hi"]) * np.ones((n, n, 3), np.float32)
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2)
    c[r < n * 0.42] = A(BRASS["low"]) * 0.7
    c[r < n * 0.32] = (18, 14, 12)
    return finish(c, np.ones((n, n), bool))


def dial_tiles(n=64):
    """Cadran : lunette de laiton, verre ambre, 7 crans (−120° à +120°), zone rouge en haut de l'échelle. Image : avant (−Z) à droite."""
    ss = 4
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    X, Y = (xx + 0.5 - N / 2) / (N / 2), -(yy + 0.5 - N / 2) / (N / 2)
    R = np.hypot(X, Y)
    ang = np.degrees(np.arctan2(X, Y))          # 0 en haut, + vers l'avant (droite de l'image)
    m = R < 0.985
    c = np.zeros((N, N, 3), np.float32)
    e = np.zeros((N, N, 3), np.float32)
    glass = R < 0.80
    c[...] = lerp(A(BRASS["hi"]), A(BRASS["low"]), np.clip((Y + 1) / 2 * -1 + 1, 0, 1)[..., None] * 0.8)
    c[(R > 0.80) & (R < 0.86)] = A(BRASS["low"]) * 0.7
    g = lerp(AMBRE, AMBRE_B, np.clip(R / 0.8, 0, 1)[..., None] ** 1.5)
    c[glass] = g[glass]
    e[glass] = (88, 56, 16)
    red = glass & (R > 0.58) & (R < 0.72) & (ang > 82) & (ang < 122)
    c[red] = (176, 44, 30)
    e[red] = (60, 12, 6)
    for k in range(13):
        a = -120 + 20 * k
        r0 = 0.56 if k % 2 == 0 else 0.64
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        along = X * sa + Y * ca
        across = np.abs(X * ca - Y * sa)
        tick = glass & (along > r0) & (along < 0.76) & (across < (0.045 if k % 2 == 0 else 0.03))
        c[tick] = (58, 32, 18)
        e[tick] = 0
    hl = glass & (np.abs(R - 0.66) < 0.035) & (ang < -40) & (ang > -95)        # reflet sur le verre
    c[hl] = lerp(AMBRE, VAPEUR, 0.7)
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.LANCZOS))
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((n, n), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    out[~al, :3] = 0
    erg = np.array(Image.fromarray(np.clip(e, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.NEAREST))
    eo = np.dstack([erg, (al & (erg.sum(axis=2) > 0)) * 255]).astype(np.uint8)
    eo[eo[..., 3] == 0] = 0
    return out, eo


def needle_tile():
    c = np.zeros((16, 4, 3), np.float32)
    c[...] = (34, 28, 26)
    c[:5] = (178, 40, 28)                      # pointe rouge (le haut de l'image = bout de l'aiguille)
    c[:, :1] *= 1.5
    return finish(c, np.ones((16, 4), bool))


def stave_tiles(W, H, w0, w1, lip, seed):
    """Douelle du pavillon : trapèze (gorge étroite à gauche, bouche large à droite), faces extérieure et intérieure."""
    ss = 4
    yy, xx = np.mgrid[0:H * ss, 0:W * ss]
    u = (xx + 0.5) / (W * ss)
    v = (yy + 0.5) / (H * ss) * 2 - 1
    hw = lerp(w0, w1, u)
    m = np.abs(v) < hw
    r = np.random.default_rng(seed)
    streak = np.array(Image.fromarray((r.random((4, W * ss)) * 255).astype(np.uint8), "L").resize((W * ss, H * ss), Image.BILINEAR), np.float32) / 255 - 0.5
    c = A(BRASS["base"]) * np.ones(u.shape + (3,), np.float32)
    c *= (1 + 0.10 * streak)[..., None]
    c = lerp(c, A(BRASS["hi"]), (np.clip(1 - np.abs(v) / np.maximum(hw, 1e-3), 0, 1) * 0.45)[..., None])
    c = lerp(c, A(BRASS["low"]), (np.clip(np.abs(v) / np.maximum(hw, 1e-3) - 0.75, 0, 1) * 2.4)[..., None])
    ci = lerp(A(BRASS["low"]) * 0.35, A(BRASS["low"]) * 1.05, np.clip(u * 1.3, 0, 1)[..., None]) * np.ones(u.shape + (1,), np.float32)
    if lip:
        c[u > 0.86] = A(BRASS["hi"])
        c[(u > 0.80) & (u <= 0.86)] = A(BRASS["low"]) * 0.8
        ci[u > 0.88] = A(BRASS["base"])
    else:
        c[u < 0.08] = A(BRASS["low"]) * 0.85
    shp = lambda a: np.array(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110
    o = np.dstack([shp(c), al * 255]).astype(np.uint8)
    i = np.dstack([shp(ci), al * 255]).astype(np.uint8)
    o[~al, :3] = 0
    i[~al, :3] = 0
    return o, i


def steam_tile(W, H, seed, plume=True):
    """Vapeur en dégradé d'opacité (alpha 1–254), blanc légèrement bleuté. Le cœur (alpha > 127) garde une forme lisible en cutout.
    plume : jet qui s'évase de la gorge (gauche) vers le bout (droite). Sinon : bouffée ronde, base en bas de l'image."""
    ss = 3
    yy, xx = np.mgrid[0:H * ss, 0:W * ss]
    u = (xx + 0.5) / (W * ss)
    v = (yy + 0.5) / (H * ss) * 2 - 1
    n1 = cell_noise(H * ss, W * ss, 4, 9, seed)
    n2 = cell_noise(H * ss, W * ss, 9, 22, seed + 1)
    lump = 0.78 + 0.32 * n1 + 0.12 * n2
    if plume:
        hw = lerp(0.24, 0.96, u ** 0.55) * (0.82 + 0.25 * n1)
        prof = np.clip(1 - (np.abs(v) / np.maximum(hw, 1e-3)) ** 2, 0, 1) ** 0.6
        along = np.clip(u / 0.05, 0, 1) * np.clip(1 - u ** 1.7, 0, 1)
        a = 250 * prof * along * lump
    else:
        cy = -0.15
        d = np.hypot((u - 0.5) * 2, (v - cy) * 1.05)
        puffs = np.zeros_like(d)
        for px, py, pr in ((0.5, 0.05, 0.42), (0.33, -0.18, 0.30), (0.66, -0.2, 0.30), (0.5, -0.45, 0.30), (0.42, 0.42, 0.26), (0.6, 0.4, 0.24)):
            puffs = np.maximum(puffs, np.clip(1 - np.hypot(u - px, (v - py) / 2) / pr * 0.5, 0, 1))
        a = 300 * np.clip(puffs - 0.3, 0, 1) / 0.7 * lump * np.clip((1 - v) / 0.25, 0, 1)
    a = np.clip(a, 0, 254)
    light = np.clip(1 - np.abs(v) * 0.8 - (0 if plume else (v + 1) * 0.15), 0, 1)
    c = lerp(VAPEUR_B, VAPEUR, light[..., None])
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(a.astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(np.int32)
    al[al < 10] = 0
    al = np.clip(al, 0, 254)
    out = np.dstack([rgb, al]).astype(np.uint8)
    out[al == 0, :3] = VAPEUR_B.astype(np.uint8)
    return out


TILES.update(bar_brass=bar_tile(BRASS, 701), bar_copper=bar_tile(COPPER, 702, 4), bar_steel=bar_tile(STEEL, 703, 6), bar_wood=wood_tile())
TILES.update(cap_brass=cap_tile(BRASS), cap_copper=cap_tile(COPPER), cap_steel=cap_tile(STEEL), cap_wood=cap_tile(WOOD), bore=bore_tile())
TILES.update(rib_brass=rib_tile(BRASS, COPPER), rib_copper=rib_tile(COPPER, BRASS, step=20), chaudiere=boiler_tile(), carcasse=frame_tile())
TILES["aiguille"] = needle_tile()
DIAL, DIAL_E = dial_tiles()
TILES["cadran"] = DIAL
# Douelles : gorge (rayon 0,47 → 0,85) et évasement (0,83 → 1,45) ; largeur relative du bout étroit
TILES["douelle1"], TILES["douelle1_in"] = stave_tiles(40, 28, 0.47 / 0.85, 1.0, False, 61)
TILES["douelle2"], TILES["douelle2_in"] = stave_tiles(40, 48, 0.83 / 1.45, 1.0, True, 62)
TILES["jet"] = steam_tile(128, 56, 71, plume=True)
TILES["bouffee"] = steam_tile(48, 56, 72, plume=False)
TRANS.update({"jet", "bouffee"})


def pack():
    items = sorted(((n, t.shape[1], t.shape[0]) for n, t in TILES.items()), key=lambda it: -it[2])
    uv, x, y, shelf = {}, 0, 0, 0
    for n, w, h in items:
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, f"atlas plein : {n}"
        uv[n] = (x, y, x + w, y + h)
        x += w + 1
        shelf = max(shelf, h)
    return uv


UV = pack()
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
for n, im in TILES.items():
    u0, v0, u1, v1 = UV[n]
    tex[v0:v1, u0:u1] = im
u0, v0, u1, v1 = UV["cadran"]
tex_e[v0:v1, u0:u1] = DIAL_E
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC                                       # postérisation invisible : PNG plus léger
tex[tex[..., 3] == 0] = 0
semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
zone = np.zeros(semi.shape, bool)
for n in TRANS:
    u0, v0, u1, v1 = UV[n]
    zone[v0:v1, u0:u1] = True
assert not (semi & ~zone).any(), "semi-transparence hors des tuiles trans_"
assert set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence _e"


def b64(arr, fn):
    im = Image.fromarray(arr, "RGBA")
    im.save(fn, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


tex_b64 = b64(tex, f"{NOM}.png")
tex_e_b64 = b64(tex_e, f"{NOM}_e.png")

# Masque de reflets (lu par face, moyenne) : niveau de gris par tuile
REFLET = {"bar_brass": 210, "cap_brass": 190, "rib_brass": 220, "carcasse": 200, "douelle1": 230, "douelle2": 235, "bore": 40,
          "bar_copper": 180, "cap_copper": 170, "rib_copper": 185, "chaudiere": 160, "bar_steel": 120, "cap_steel": 110,
          "cadran": 150, "aiguille": 60, "bar_wood": 22, "cap_wood": 22, "douelle1_in": 45, "douelle2_in": 55, "jet": 0, "bouffee": 0}
tex_r = np.zeros((TEX, TEX, 4), np.uint8)
for n, g_ in REFLET.items():
    u0, v0, u1, v1 = UV[n]
    if g_:
        m_ = TILES[n][..., 3] > 0
        tex_r[v0:v1, u0:u1][m_] = (g_, g_, g_, 255)
assert set(REFLET) == set(TILES), set(TILES) ^ set(REFLET)
tex_r_b64 = b64(tex_r, f"{NOM}_r.png")

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx (ordre du mod et du renderer). Blocage de cardan (axe local X sur ±Z) traité :
    rz = 0 et rx porte toute la rotation autour de l'axe. Vérifié par reconstruction."""
    if abs(R[2, 0]) < 0.99999:
        ry = math.asin(-R[2, 0])
        e = (math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0])))
    elif R[2, 0] < 0:
        e = (math.degrees(math.atan2(R[0, 1], R[0, 2])), 90.0, 0.0)
    else:
        e = (math.degrees(math.atan2(-R[0, 1], -R[0, 2])), -90.0, 0.0)
    assert np.allclose(rotm(*e), R, atol=1e-6), "euler"
    return e


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups, name
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(float(v), 3) for v in rotation]}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


S_ = V(0, 0, -1)     # vers l'avant (le long du canon)
H_ = V(0, 1, 0)
X_ = V(1, 0, 0)      # vers l'extérieur (droite du joueur)


def W(s, h=0.0, x=0.0):
    return P0 + S_ * s + H_ * h + X_ * x


def full(tile):
    u0, v0, u1, v1 = UV[tile]
    return [u0, v0, u1, v1]


def strip(tile, cap, u0=0.0, u1=1.0):
    bu0, bv0, bu1, bv1 = UV[tile]
    ua = lerp(bu0, bu1, u0)
    ub = max(lerp(bu0, bu1, u1), ua + 2)
    lg = [ua, bv0, ub, bv1]
    end = full(cap)
    return {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}


def bar(g, name, p, q, r, tile="bar_brass", cap="cap_brass", octo=True, ov=0.05, u0=0.0, u1=1.0, r2=None):
    """Tronçon de p à q : section octogonale (deux cubes, le second tourné de 45° sur l'axe) ou losange seul."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X = unit(q - p)
    ref = V(0, 1, 0) if abs(X[1]) < 0.9 else V(0, 0, -1)
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R0 = np.column_stack([X, Y, Z_])
    R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
    faces = strip(tile, cap, u0, u1)
    ry = r if r2 is None else r2
    if octo == 8:
        # Octogone régulier : 4 plaques (demi-côtés r et r·tan 22,5°) à 0, 45, 90 et 135° ; leur union est l'octogone exact,
        # sans les pointes d'étoile de deux carrés. Bouts décalés de 0,03 px par plaque (pas de faces coplanaires).
        a_ = r * math.tan(math.pi / 8) * 1.02
        cu0, cv0, cu1, cv1 = UV[cap]
        cm, ch_ = (cu0 + cu1) / 2, (cu1 - cu0) / 2 * a_ / r
        fk = dict(faces, east=[cm - ch_, cv0, cm + ch_, cv1], west=[cm - ch_, cv0, cm + ch_, cv1])
        # remise aux règles : les faces étroites (±a_) sont toutes dans l'octogone, jamais vues : transparentes ;
        # tronçon court (≤ 0,8) : bouts des plaques 1 à 3 transparents (anneau ouvert), long : bouts en retrait de 0,11
        fk.update(north=CLEAR, south=CLEAR)
        court = L + 2 * ov <= 0.8
        for k in range(4):
            g_ = math.pi / 4 * k
            Yk = math.cos(g_) * Y + math.sin(g_) * Z_
            Rk = np.column_stack([X, Yk, np.cross(X, Yk)])
            d = 0.0 if court else 0.11 * k
            fkk = dict(fk, east=CLEAR, west=CLEAR) if court and k else fk
            cube(g, name + ("", "b", "c", "d")[k], p + (-ov + d, -r, -a_), p + (L + ov - d, r, a_), p, euler(Rk), fkk)
    elif octo:
        cube(g, name, p + (-ov, -ry, -r), p + (L + ov, ry, r), p, euler(R0), faces)
        rec = 0.11 if L + 2 * ov > 0.5 else 0.03
        fo = faces if rec > 0.05 else dict(faces, east=CLEAR, west=CLEAR)
        cube(g, name + "o", p + (-ov + rec, -ry * 0.97, -r * 0.97), p + (L + ov - rec, ry * 0.97, r * 0.97), p, euler(R45), fo)
    else:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R45), faces)


def oriented(g, name, c, X, Y, size, faces):
    """Cube centré en c, axes locaux X, Y (Z = X × Y), demi-tailles size."""
    X = unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    Z_ = np.cross(X, Y)
    c = np.asarray(c, float)
    cube(g, name, c - size, c + size, c, euler(np.column_stack([X, Y, Z_])), faces)


def plate_faces(tile, back=None):
    u0, v0, u1, v1 = UV[tile]
    b = UV[back] if back else (u0, v0, u1, v1)
    return {"south": [u0, v0, u1, v1], "north": [b[2], b[1], b[0], b[3]], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}


bras = group("right_arm", [5, 22, 0])
prise = group("prise", P0, parent=bras, rotation=(0, -YAW_OUT, 0))     # -Y : la bouche part vers l'extérieur (+X)
pis = group("pistolet", P0, parent=prise)
rec = group("recul", P0, parent=pis)

# Crosse : bois sous le poing, talon qui descend vers l'arrière, bagues et talon de laiton
bar(rec, "poignee", W(-0.7, 0.0), W(1.45, 0.12), 0.55, "bar_wood", "cap_wood", u0=0.0, u1=0.5, octo=8)
bar(rec, "crosse", W(-0.7, 0.0), W(-1.9, -0.72), 0.63, "bar_wood", "cap_wood", u0=0.5, u1=0.8, octo=8)
bar(rec, "talon_bois", W(-1.85, -0.68), W(-2.45, -1.2), 0.74, "bar_wood", "cap_wood", u0=0.8, u1=1.0, octo=8)
bar(rec, "talon", W(-2.4, -1.16), W(-2.7, -1.42), 0.82, ov=0.0, octo=8)
bar(rec, "bague_crosse", W(-0.85, 0.0), W(-0.55, 0.0), 0.66, "rib_brass", ov=0.0, octo=8)
bar(rec, "bague_avant", W(1.2, 0.12), W(1.5, 0.12), 0.64, "rib_brass", ov=0.0, octo=8)
# Garde de laiton et détente d'acier
bar(rec, "garde_av", W(1.3, -0.42), W(1.12, -1.15), 0.13, octo=False, ov=0.08)
bar(rec, "garde_bas", W(1.12, -1.15), W(0.05, -1.15), 0.13, octo=False, ov=0.08)
bar(rec, "garde_ar", W(0.05, -1.15), W(-0.3, -0.42), 0.13, octo=False, ov=0.08)
bar(rec, "detente", W(0.72, -0.4), W(0.52, -0.92), 0.12, "bar_steel", "cap_steel", octo=False, ov=0.03)

# Carcasse de laiton devant le poing
a, b = W(1.3, -0.45, -0.62), W(3.2, 1.05, 0.62)
cube(rec, "carcasse", np.minimum(a, b), np.maximum(a, b), W(2.2, 0.3), (0, 0, 0), {f: full("carcasse") for f in ("north", "south", "east", "west", "up", "down")})

# Chaudière de cuivre : octogone, bandes de laiton rivetées, dômes
HC = 2.0
bar(rec, "chaudiere", W(1.75, HC), W(4.85, HC), 1.0, "chaudiere", "cap_copper", ov=0.0, octo=8)
bar(rec, "bande_ar", W(2.3, HC), W(2.65, HC), 1.12, "rib_brass", ov=0.0, octo=8)      # 0,12 au-dessus de la tôle
bar(rec, "bande_av", W(3.95, HC), W(4.3, HC), 1.12, "rib_brass", ov=0.0, octo=8)
bar(rec, "dome_ar", W(1.5, HC), W(1.7, HC), 0.74, ov=0.0, octo=8)                       # bout intérieur à 0,05 de la tôle : hors des plans
bar(rec, "dome_av", W(4.9, HC), W(5.1, HC), 0.74, ov=0.0, octo=8)

# Manomètre sur le flanc extérieur : boîtier, cadran, moyeu ; aiguille dans son groupe
SM = 3.15
bar(rec, "mano_boitier", W(SM, HC, 1.05), W(SM, HC, 1.5), 0.62, "bar_brass", "cap_brass", ov=0.0, octo=8)
XD = 1.62
cd = W(SM, HC, XD - 0.15)
cube(rec, "mano_cadran", cd - (0.15, 0.6, 0.6), cd + (0.15, 0.6, 0.6), cd, (0, 0, 0), {"east": full("cadran"), "west": CLEAR, "north": CLEAR, "south": CLEAR, "up": CLEAR, "down": CLEAR})
ch = W(SM, HC, XD + 0.15)
cube(rec, "mano_moyeu", ch - (0.15, 0.11, 0.11), ch + (0.15, 0.11, 0.11), ch, (0, 0, 0), {f: full("cap_brass") for f in ("north", "south", "east", "west", "up", "down")})
aig = group("aiguille", W(SM, HC, XD), parent=rec)
ca = W(SM, HC + 0.27, XD + 0.13)
cube(aig, "aiguille", ca - (0.09, 0.33, 0.07), ca + (0.09, 0.33, 0.07), ca, (0, 0, 0), {f: full("aiguille") for f in ("north", "south", "east", "west", "up", "down")})

# Soupape sur le dessus : tige fixe, chapeau mobile (groupe), bouffée cachée dans le chapeau
SS = 3.95
bar(rec, "soupape_tige", W(SS, HC + 0.95), W(SS, HC + 1.55), 0.17, "bar_steel", "cap_steel", ov=0.0)
soup = group("soupape", W(SS, HC + 1.5), parent=rec)
bar(soup, "soupape_chapeau", W(SS, HC + 1.5), W(SS, HC + 1.8), 0.34, "rib_brass", "cap_brass", ov=0.0, octo=8)
bar(soup, "soupape_bouton", W(SS, HC + 1.8), W(SS, HC + 1.95), 0.13, ov=0.0, octo=False)
bouf_o = W(SS, HC + 1.62)
bouf = group("trans_bouffee", bouf_o, parent=soup)
for k in range(3):
    ang = math.radians(60 * k)
    Xp = X_ * math.cos(ang) + S_ * math.sin(ang)
    oriented(bouf, f"bouffee{k}", bouf_o + H_ * (1.05 * F_GEO / K), Xp, H_, np.array((0.9, 1.05, 0.15)) * F_GEO / K, plate_faces("bouffee"))

# Manchon du canon (fixe), tuyau de cuivre avec vanne
bar(rec, "manchon", W(3.1, H_AXE), W(6.0, H_AXE), 0.7, "bar_brass", "cap_brass", ov=0.0, u0=0.0, u1=0.6, octo=8)
bar(rec, "manchon_bague", W(5.85, H_AXE), W(6.15, H_AXE), 0.92, "rib_copper", "cap_copper", ov=0.0, octo=8)
SP = 5.78
bar(rec, "tuyau_h", W(5.0, HC), W(SP, HC), 0.22, "bar_copper", "cap_copper", ov=0.12)
bar(rec, "tuyau_v", W(SP, HC + 0.1), W(SP, 1.05), 0.22, "bar_copper", "cap_copper", ov=0.0)
bar(rec, "raccord", W(SP, HC + 0.24), W(SP, HC - 0.16), 0.3, ov=0.0)
bar(rec, "bride", W(SP, 1.3), W(SP, 1.0), 0.32, ov=0.0)
bar(rec, "vanne", W(SP, 1.62, -0.36), W(SP, 1.62, 0.36), 0.25, ov=0.0)
bar(rec, "vanne_tige", W(SP, 1.62, 0.36), W(SP, 1.62, 0.72), 0.08, "bar_steel", "cap_steel", octo=False, ov=0.0)
bar(rec, "vanne_poignee", W(SP - 0.32, 1.62, 0.74), W(SP + 0.32, 1.62, 0.74), 0.09, "bar_steel", "cap_steel", octo=False, ov=0.0)

# Ressort à boudin : du manchon à la bague du canon, compressé au recul (scale z autour de son arrière)
RS0, RS1, RR, NC = 6.15, 7.55, 0.86, 4
ress = group("ressort", W(RS0, H_AXE), parent=rec)
pts = []
for i in range(NC * 4 + 1):
    th = i * math.pi / 2 + math.pi / 4
    s = RS0 + (RS1 - RS0) * i / (NC * 4)
    pts.append(W(s, H_AXE + RR * math.sin(th), RR * math.cos(th)))
for i in range(NC * 4):
    bar(ress, f"spire{i}", pts[i], pts[i + 1], 0.1, "bar_steel", "cap_steel", octo=False, ov=0.07)

# Canon coulissant : tube, bagues, pavillon en douelles
can = group("canon", W(6.0, H_AXE), parent=rec)
bar(can, "tube", W(3.4, H_AXE), W(9.15, H_AXE), 0.5, "bar_brass", "bore", ov=0.0, octo=8)
bar(can, "bague_ressort", W(7.55, H_AXE), W(7.85, H_AXE), 0.92, "rib_brass", ov=0.0, octo=8)
bar(can, "bague_bouche", W(8.7, H_AXE), W(9.0, H_AXE), 0.64, "rib_copper", "cap_copper", ov=0.0, octo=8)
C_AX = lambda s: W(s, H_AXE)
for tier, (s0, s1, r0, r1, tile, th) in enumerate(((9.0, 10.2, 0.47, 0.85, "douelle1", 0.2), (10.12, 11.0, 0.83, 1.45, "douelle2", 0.2))):
    wide = 2 * r1 * math.tan(math.pi / 8) * 1.12
    for k in range(8):
        phi = math.radians(45 * k + 22.5)
        er = X_ * math.cos(phi) + H_ * math.sin(phi)
        p0, p1 = C_AX(s0) + er * r0, C_AX(s1) + er * r1
        Xl = unit(p1 - p0)
        Zl = unit(er - (er @ Xl) * Xl)
        Yl = np.cross(Zl, Xl)
        L = np.linalg.norm(p1 - p0)
        oriented(can, f"douelle{tier}_{k}", (p0 + p1) / 2 - Zl * (0.012 * (k % 2)), Xl, Yl, (L / 2, wide / 2, th / 2), plate_faces(tile, tile + "_in"))

# Jet de vapeur : 3 plaques croisées contenant l'axe, cachées dans la gorge (taille / K)
JS0, JL, JW = 9.0, 8.0, 4.0
jet = group("trans_jet", C_AX(JS0), parent=can)
for k in range(3):
    ang = math.radians(60 * k + 30)
    Yp = H_ * math.cos(ang) + X_ * math.sin(ang)
    oriented(jet, f"jet{k}", C_AX(JS0) + S_ * (JL / 2 * F_GEO / K), S_, Yp, np.array((JL / 2, JW / 2, 0.15)) * F_GEO / K, plate_faces("jet"))
group("ctrl_alpha", C_AX(JS0), parent=jet)
# Particules vanilla : +Y du groupe le long du canon (rotation X -90 : +Y vers -Z)
EMITS = []
for k, (nm, s) in enumerate((("emit_mc_poof", 10.85), ("emit_mc_white_smoke", 10.6))):
    EMITS.append(group(nm, C_AX(s), parent=can, rotation=(-90, 0, 0)))
    group(f"ctrl_emit@{k + 1}", C_AX(s), parent=nm)     # cadence : -1 coupée hors tir, +5 au tir (guide 5 ter)
CTRL_E = ["ctrl_emit@1", "ctrl_emit@2"]


def bone_node(name):
    g = groups[name]
    return {"name": name.split("@")[0], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node(bras)]


# ------------------------------------------------------------------ animations
# Guide, section 3 : +X bascule le haut vers l'arrière, donc relève la bouche (devant) ; +Y avance le côté droit, donc la bouche part vers
# l'intérieur (-X). Une seule main : pas de miroir. pose(rise, inward, roll) : roll penche le dessus vers l'extérieur.
def pose(rise, inward, roll):
    return rise, inward, -roll


def kf(t, x, y, z, ch="rotation"):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 3)), "y": str(round(y + 0.0, 3)), "z": str(round(z + 0.0, 3))}],
            "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, tracks, fps=24, loop="loop"):
    """tracks : {(groupe, canal): f(t) -> (x, y, z)}."""
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A_ = {}
    for (g, ch), f in tracks.items():
        A_.setdefault(groups[g]["uuid"], {"name": g.split("@")[0], "type": "bone", "keyframes": []})["keyframes"] += [kf(t, *f(t), ch=ch) for t in times]
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A_}


def step(tau, rise=0.05, over=0.28):
    """Échelon de servo : montée courte, dépassement puis rappel amorti (un rebond)."""
    if tau <= 0:
        return 0.0
    v = sm(tau, 0.0, rise)
    if tau > rise * 0.6:
        x = tau - rise * 0.6
        v += over * math.sin(TAU * x / 0.15) * math.exp(-x / 0.045)
    return v


def needle_deg(level):
    """Crans 0..6 → angle horaire depuis le haut, vu de l'extérieur (−120° à +120°)."""
    return -120 + 40 * level


L0 = 3          # niveau de départ et de fin de toutes les boucles


class Programme:
    """Cycle de pression : ticks (+1 cran), décharges (soupape, bouffée, l'aiguille retombe de n crans)."""

    def __init__(self, L, ticks, puffs, tw=0.5, pd=1.0, base_smoke=0.25, jolt=1.0, vib=0.0, vib_f=0.0):
        self.L, self.ticks, self.puffs, self.tw, self.pd = L, ticks, puffs, tw, pd
        self.base_smoke, self.jolt, self.vib, self.vib_f = base_smoke, jolt, vib, vib_f
        tot = len(ticks) - sum(n for _, n in puffs)
        assert tot == 0, f"boucle de pression non fermée : {tot}"
        for tp, _ in puffs:
            assert tp - tw > 0.05 and tp + 0.72 * pd < L - 0.02, f"décharge {tp} trop près du bord"
        assert max(ticks) + 0.3 < L

    def tremble(self, t):
        return sum(bump(t, tp - self.tw, tp - self.tw * 0.75, tp - 0.03, tp) for tp, _ in self.puffs)

    def level(self, t):
        v = L0 + sum(step(t - ti) for ti in self.ticks)
        v -= sum(n * step(t - tp - 0.03, rise=0.07, over=0.22 / n) for tp, n in self.puffs)
        v += 0.13 * self.tremble(t) * math.sin(TAU * 19 * t)
        if self.vib:
            v += self.vib * math.sin(TAU * self.vib_f * t)
        return v

    def needle(self, t):
        return (-needle_deg(self.level(t)), 0, 0)

    def valve(self, t):
        y = 0.035 * self.tremble(t) * math.sin(TAU * 23 * t + 0.7)
        for tp, n in self.puffs:
            d = 0.18 * self.pd * (1.2 if n > 1 else 1.0)
            y += 0.24 * (step(t - tp, rise=0.035, over=0.2) - step(t - tp - d, rise=0.04, over=0.35))
        return (0, y, 0)

    def _puff(self, t):
        """(taille relative, montée) de la bouffée en cours."""
        for tp, n in self.puffs:
            p = self.pd
            if tp <= t <= tp + 0.72 * p:
                big = 1.3 if n > 1 else 1.0
                sz = big * sm(t, tp + 0.02, tp + 0.1 * p) * (1 + 0.3 * sm(t, tp + 0.1 * p, tp + 0.45 * p)) * (1 - sm(t, tp + 0.3 * p, tp + 0.62 * p))
                up = 0.9 * big * sm(t, tp + 0.05, tp + 0.62 * p) * (1 - sm(t, tp + 0.64 * p, tp + 0.7 * p))
                return sz, up
        return 0.0, 0.0

    def puff_scale(self, t):
        sz, _ = self._puff(t)
        k = (1 + (K - 1) * sz) / F_GEO
        return (k, k * 1.08, k)

    def puff_pos(self, t):
        return (0, self._puff(t)[1], 0)

    def kick(self, t):
        """Petit sursaut de l'arme à chaque décharge (la machine qui crache)."""
        j = 0.0
        for tp, n in self.puffs:
            x = t - tp - 0.02
            if x > 0:
                j += self.jolt * (1.3 if n > 1 else 1.0) * math.exp(-x / 0.07) * math.sin(TAU * x / 0.12)
        return j


def state(name, prog, rise, inward, roll, amp, cycles):
    L = prog.L

    def gun(t):
        ph = TAU * cycles * t / L
        return pose(rise + amp * mech(math.sin(ph)) + prog.kick(t), inward + 0.4 * amp * math.sin(ph + 1.1), roll + 0.3 * amp * mech(math.sin(ph + 0.5)))
    tracks = {(pis, "rotation"): gun, (aig, "rotation"): prog.needle, (soup, "position"): prog.valve,
              (bouf, "scale"): prog.puff_scale, (bouf, "position"): prog.puff_pos,
              (CTRL_E[0], "position"): lambda t: (-1.0, 0.0, 0.0), (CTRL_E[1], "position"): lambda t: (-1.0, 0.0, 0.0)}
    return anim(name, L, tracks, fps=30)


# idle 8 s : deux cycles de 4 s (3 → 4 → 5, tremble, décharge courte → 4, → 5, tremble, grande décharge → 3)
P_IDLE = Programme(8.0, [0.5, 1.2, 2.5, 4.5, 5.2, 6.5], [(1.8, 1), (3.1, 2), (5.8, 1), (7.1, 2)])
P_WALK = Programme(3.2, [0.3, 0.75, 1.75], [(1.3, 1), (2.3, 2)], tw=0.4, pd=0.9, base_smoke=0.35)
P_RUN = Programme(2.0, [0.1, 0.26, 1.1, 1.26], [(0.5, 2), (1.5, 2)], tw=0.2, pd=0.6, base_smoke=0.6, jolt=0.8, vib=0.05, vib_f=12)
P_SNEAK = Programme(4.0, [0.8, 1.8], [(2.9, 2)], tw=0.6, pd=1.0, base_smoke=0.1, jolt=0.5)
P_FALL = Programme(2.4, [0.3], [(1.2, 1)], tw=0.7, pd=0.9, base_smoke=0.3, vib=0.06, vib_f=10)

idle = state("idle", P_IDLE, 0.0, 0.0, 0.0, 1.0, 2)
walk = state("walk", P_WALK, 3.0, 1.0, 0.0, 2.5, 2)
run = state("run", P_RUN, 12.0, 3.0, 2.0, 3.0, 2)
sneak = state("sneak", P_SNEAK, -16.0, 4.0, -2.0, 0.8, 1)
fall = state("fall", P_FALL, 8.0, 0.0, 0.0, 2.0, 2)

# attack (once, 0,8 s) : recul sec du canon, coup de la crosse vers le haut, jet au pavillon, aiguille à zéro puis remontée par crans
REC = 0.75
LS = RS1 - RS0


def recoil(t):
    return 0.0, 0.0, REC * sm(t, 0.02, 0.045) * (1 - sm(t, 0.09, 0.3)) - 0.12 * bump(t, 0.25, 0.31, 0.33, 0.45)


def spring_scale(t):
    return 1.0, 1.0, (LS - recoil(t)[2]) / LS


def kick_attack(t):
    k = 13 * sm(t, 0.02, 0.06) * (1 - sm(t, 0.1, 0.42)) - 2.5 * bump(t, 0.36, 0.44, 0.46, 0.6)
    return pose(k, -1.5 * bump(t, 0.02, 0.07, 0.15, 0.4), 3 * bump(t, 0.02, 0.07, 0.12, 0.45))


def jet_scale(t):
    w = sm(t, 0.03, 0.11) * (1 + 0.45 * sm(t, 0.11, 0.36)) * (1 - 0.85 * sm(t, 0.38, 0.62))
    l = sm(t, 0.03, 0.11) * (1 + 0.6 * sm(t, 0.11, 0.45)) * (1 - sm(t, 0.52, 0.66))
    w *= 1 - sm(t, 0.58, 0.66)
    return (1 + (K - 1) * w) / F_GEO, (1 + (K - 1) * w) / F_GEO, (1 + (K - 1) * l) / F_GEO


def jet_pos(t):
    return 0.0, 0.25 * sm(t, 0.15, 0.6) * (1 - sm(t, 0.64, 0.68)), -1.2 * sm(t, 0.2, 0.62) * (1 - sm(t, 0.64, 0.68))


def jet_alpha(t):
    return -sm(t, 0.3, 0.62) * (1 - sm(t, 0.7, 0.75)), 0.0, 0.0      # 1 + x : opaque, fondu jusqu'à invisible, retour à 0 une fois caché


def needle_attack(t):
    dl = -3 * step(t - 0.035, rise=0.04, over=0.1)                              # écart : la pression tombe d'un coup (cran 3 → 0)
    dl += sum(step(t - ti) for ti in (0.34, 0.47, 0.6))                         # puis remonte par crans
    return (-40 * dl, 0, 0)


attack = anim("attack", 0.8, {(rec, "rotation"): kick_attack, (can, "position"): recoil, (ress, "scale"): spring_scale,
                              (jet, "scale"): jet_scale, (jet, "position"): jet_pos, ("ctrl_alpha", "position"): jet_alpha,
                              (aig, "rotation"): needle_attack,
                              (CTRL_E[0], "position"): lambda t: (5 * bump(t, 0.03, 0.05, 0.12, 0.18), 0.0, 0.0),     # s'ajoute à l'état
                              (CTRL_E[1], "position"): lambda t: (5 * bump(t, 0.05, 0.08, 0.4, 0.5), 0.0, 0.0)}, fps=60, loop="once")


def hurt_gun(t):
    env = sm(t, 0.0, 0.05) * (1 - sm(t, 0.4, 0.72))
    trem = math.sin(TAU * t / 0.11) * math.exp(-4.5 * t)
    return pose(env * (-7 + 4 * trem), env * 2.0, env * 5 * trem)


def hurt_needle(t):
    return (-40 * 1.1 * math.sin(TAU * t / 0.09) * math.exp(-5 * t) * sm(t, 0, 0.03), 0, 0)     # écart : l'aiguille s'affole puis se calme


hurt = anim("hurt", 0.8, {(rec, "rotation"): hurt_gun, (aig, "rotation"): hurt_needle}, fps=40, loop="once")

attack["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "tir_vapeur", "file": ""}], "time": 0.03}]}

# event_equip 1,4 s (par-dessus l'état) : l'arme sort de la main (échelle avec dépassement), le canon coulisse en place
# (ressort qui se détend), la pression monte par crans, la soupape lâche une bouffée. Tout revient à 0 ; un son.
def eq_scale(t):
    k = 0.3 + 0.7 * step(t, rise=0.12, over=0.12)
    return k, k, k


def eq_canon(t):
    return 0.0, 0.0, REC * (1 - step(t - 0.3, rise=0.1, over=0.2))


def eq_needle(t):
    return (-40 * (-3 * (1 - sum(step(t - ti) for ti in (0.55, 0.7, 0.85)) / 3)), 0, 0) if t < 1.3 else (0.0, 0.0, 0.0)


def eq_puff(t):
    sz = sm(t, 0.95, 1.03) * (1 - sm(t, 1.15, 1.35))
    k = (1 + (K - 1) * sz) / F_GEO
    return k, k * 1.08, k


equip = anim("event_equip", 1.4, {(pis, "scale"): eq_scale, (can, "position"): eq_canon,
                                  (ress, "scale"): lambda t: (1.0, 1.0, (LS - eq_canon(t)[2]) / LS),
                                  (soup, "position"): lambda t: (0.0, 0.24 * bump(t, 0.93, 0.97, 1.15, 1.25), 0.0),
                                  (bouf, "scale"): eq_puff, (bouf, "position"): lambda t: (0.0, 0.9 * sm(t, 0.97, 1.3) * (1 - sm(t, 1.32, 1.38)), 0.0)},
             fps=40, loop="once")
equip["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.piston.contract", "file": ""}], "time": 0.32}]}

ANIMS = [idle, walk, run, sneak, fall, attack, hurt, equip]

# ------------------------------------------------------------------ écriture
assert 80 <= len(elements) <= 140, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
textures.append({"name": f"{NOM}_r.png", "uv_width": TEX, "uv_height": TEX, "source": tex_r_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
# Pas de retirer_particules() : il retirerait aussi les points emit_mc_ (vapeur vanilla qui se dissipe, permise partout).
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
# Sons rares : aucun en mouvement, un au plus au repos (boucle ≥ 8 s), à l'attaque et à la blessure (retour de l'utilisateur).
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
# emit_mc_poof et emit_mc_white_smoke gardés : les particules de Minecraft partent bien du point depuis le correctif du
# 2026-11-04 (test en jeu, 16 h 26–16 h 33) ; plus de vapeur modélisée qui les remplaçait. Cadence pilotée par ctrl_emit (tir).
from sons import limiter_sons, embarquer_sons
embarquer_sons(model, {"tir_vapeur": "sons/tir_vapeur.ogg"})   # son original synthétisé (tools/synthe.py)
limiter_sons(model, attaque=True)   # arme : le coup de vapeur au tir reste
from reactions import retirer_reactions
retirer_reactions(model, garder=("attack",))
# Ambiance : métal mouillé sous la pluie, lumière plus forte la nuit et sous la pluie, éclats sur les arêtes polies.
from ambiance import ajouter_ambiance
ajouter_ambiance(model)


# ------------------------------------------------------------------ faces proches (.claude/references/procedures/remise-aux-regles.md)
def decoller(model, seuil=0.1, cible=0.115, pas_max=0.26, passes=16, ep_min=0.28, log=print, geler=()):
    """Écarte les faces parallèles visibles qui se chevauchent à moins de `seuil` px (faces opposées comprises), sur la
    pose de base : la face de la pièce la plus petite avance (de préférence) ou recule le long de sa normale jusqu'à
    `cible` px, de `pas_max` px au plus, sans qu'une pièce devienne plus mince que `ep_min`. Modifie model sur place."""
    import tempfile
    import numpy as np
    import render_bbmodel as rb
    from PIL import Image
    AX = {"east": (0, 1), "west": (0, -1), "up": (1, 1), "down": (1, -1), "south": (2, 1), "north": (2, -1)}
    by = {e["uuid"]: e for e in model["elements"]}
    tex = model["textures"][0]["source"].split(",", 1)[1]
    A = np.asarray(Image.open(io.BytesIO(base64.b64decode(tex))).convert("RGBA"))[..., 3] > 127
    H, W = A.shape

    def ordre():
        out = []

        def w(n):
            if isinstance(n, str):
                e = by[n]
                for f, fd in e["faces"].items():
                    if fd.get("texture") is None:
                        continue
                    u1, v1, u2, v2 = fd["uv"]
                    if u1 == u2 or v1 == v2:
                        continue
                    out.append((n, f))
            else:
                for c in n.get("children", []):
                    w(c)
        for n in model["outliner"]:
            if isinstance(n, dict) and n.get("name", "").startswith("particle_"):
                continue
            w(n)
        return out

    def opaque(uv4, s, t):
        top = uv4[0] + (uv4[1] - uv4[0]) * s[..., None]
        bot = uv4[3] + (uv4[2] - uv4[3]) * s[..., None]
        uv = top + (bot - top) * t[..., None]
        return A[np.clip((uv[..., 1] * H).astype(int), 0, H - 1), np.clip((uv[..., 0] * W).astype(int), 0, W - 1)]

    S_, T_ = np.meshgrid(np.linspace(0.02, 0.98, 20), np.linspace(0.02, 0.98, 20))
    S_, T_ = S_.ravel(), T_.ravel()
    restant = None
    cumul = {}                                  # déplacement total de chaque face : jamais de retour en arrière (pas d'oscillation)
    for passe in range(passes):
        fd, tmp = tempfile.mkstemp(suffix=".bbmodel")
        os.close(fd)
        with open(tmp, "w") as fh:
            json.dump({k: v for k, v in model.items() if k != "animations"}, fh)
        Q, _ = rb.load_model(tmp)
        os.remove(tmp)
        ids = ordre()
        assert len(ids) == len(Q)
        centre = {}
        for (eid, f), q in zip(ids, Q):
            centre.setdefault(eid, []).append(np.mean(np.array(q[0], float), 0))
        centre = {k: np.mean(v, 0) for k, v in centre.items()}
        F = []
        for (eid, f), q in zip(ids, Q):
            P, uv = np.array(q[0], float), np.array(q[1], float)
            n = np.cross(P[1] - P[0], P[3] - P[0])
            ar = np.linalg.norm(n)
            if ar < 1e-9:
                continue
            n = n / ar
            c = P.mean(0)
            out = n if (c - centre[eid]) @ n >= 0 else -n
            pts = P[0] + (P[1] - P[0]) * S_[:, None] + (P[3] - P[0]) * T_[:, None]
            op = opaque(uv, S_, T_)
            if not op.any():
                continue
            F.append(dict(eid=eid, f=f, P=P, n=out, ar=ar, pts=pts[op], lo=P.min(0) - seuil, hi=P.max(0) + seuil))
        paires = []
        for i in range(len(F)):
            a = F[i]
            for j in range(i + 1, len(F)):
                b = F[j]
                if a["eid"] == b["eid"] or abs(a["n"] @ b["n"]) < 0.9986:
                    continue
                if (a["lo"] > b["hi"]).any() or (b["lo"] > a["hi"]).any():
                    continue
                # échantillons opaques de b proches du plan de a et dans a (et réciproquement)
                best = None
                for x, y in ((a, b), (b, a)):
                    d = (y["pts"] - x["P"][0]) @ x["n"]
                    near = np.abs(d) < seuil
                    if not near.any():
                        continue
                    e1, e2 = x["P"][1] - x["P"][0], x["P"][3] - x["P"][0]
                    M = np.stack([e1, e2], 1)
                    st, *_ = np.linalg.lstsq(M, (y["pts"][near] - x["P"][0]).T, rcond=None)
                    ins = (st[0] > 0.005) & (st[0] < 0.995) & (st[1] > 0.005) & (st[1] < 0.995)
                    if not ins.any():
                        continue
                    dd = d[near][ins]
                    sd = float(dd[np.argmin(np.abs(dd))])
                    if best is None or abs(sd) < abs(best[1]):
                        best = (x is a, sd)
                if best is not None:
                    paires.append((i, j, best))
        if passe == 0:
            log(f"faces proches (< {seuil} px) avant décollement : {len(paires)}")
        if not paires:
            restant = 0
            break
        bouge = {}
        non = 0
        for i, j, (a_ref, sd) in paires:
            ref, oth = (F[i], F[j]) if a_ref else (F[j], F[i])
            # sd : distance signée de oth au plan de ref, le long de la normale sortante de ref
            opts = []
            for cible_s in (cible, -cible):
                for qui, k in ((oth, oth["n"] @ ref["n"]), (ref, -1.0)):
                    ds = cible_s - sd
                    delta = ds / k                      # avance de la face de qui le long de sa normale sortante
                    e = by[qui["eid"]]
                    if e["name"].startswith(tuple(geler)):
                        continue
                    ax, sg = AX[qui["f"]]
                    ep = e["to"][ax] - e["from"][ax]
                    if abs(delta) > pas_max or ep + delta < min(ep_min, ep):
                        continue
                    if (qui["eid"], qui["f"]) in bouge:
                        continue
                    c0 = cumul.get((qui["eid"], qui["f"]), 0.0)
                    if c0 * delta < 0 or abs(c0 + delta) > 1.4 * pas_max:
                        continue
                    score = abs(delta) + (0.04 if delta < 0 else 0) + 0.002 * qui["ar"]
                    opts.append((score, qui, delta))
            if not opts:
                non += 1
                continue
            _, qui, delta = min(opts, key=lambda o: o[0])
            bouge[(qui["eid"], qui["f"])] = delta
        for (eid, f), delta in bouge.items():
            cumul[(eid, f)] = cumul.get((eid, f), 0.0) + delta
            e = by[eid]
            ax, sg = AX[f]
            if sg > 0:
                e["to"][ax] = round(e["to"][ax] + delta, 3)
            else:
                e["from"][ax] = round(e["from"][ax] - delta, 3)
        restant = len(paires)
        log(f"  passe {passe + 1} : {len(paires)} paires, {len(bouge)} faces déplacées, {non} sans solution")
        if not bouge or passe == passes - 1:
            for i, j, (a_ref, sd) in paires:
                log(f"    reste {sd:+.3f} px : {by[F[i]['eid']]['name']}.{F[i]['f']} / {by[F[j]['eid']]['name']}.{F[j]['f']}")
            break
    return restant


RESTE_PROCHES = decoller(model, pas_max=0.13, geler=("vanne", "raccord", "bride", "tuyau", "manchon_bague", "mano_moyeu", "aiguille"))      # petites pièces : déplacements courts (au-delà, les bagues se déformaient)
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      len(EMITS), "emit_mc_")
