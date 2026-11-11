"""Casque d'orage (ensemble Orage, tête) : remplace la couronne d'orage (archives/chapeaux/couronne_orage, « fixette sur des
couronnes », 2026-11-08). Design original : casque de guerrier de l'orage à la manière des casques à lamelles d'Extrême-Orient
(grammaire générique, aucune pièce réelle copiée) :
- bombe (calotte) de métal d'orage ouverte sur le visage : parois à la face intérieure à 4,66 px, dessus à y 32,66, arêtes
  biseautées en vrai volume (barres à 45° qui ne touchent que l'extérieur du coin de la tête), côtes en relief sur le dessus,
  bandeau inférieur gravé d'un zigzag lumineux, petit œil d'orage serti au front (cristal dans un chaton d'or, à plat) ;
- couvre-nuque de trois lames laquées bleu nuit, bordées d'or, lacées de cordons bleu clair, évasées vers l'arrière (octogone :
  coins à |x|+|z| ≥ 9,24) ;
- deux ailerons-paratonnerres aux tempes (ailettes rabattues vers l'arrière, en forme de plume découpée en marches d'éclair,
  bord d'or, filet lumineux, pointe de cristal d'orage) ;
- cimier : un éclair de métal en zigzag en vrai volume qui monte du sommet (tambour aux trois virgules d'or) et finit en
  cristal, avec une fourche. La foudre saute du cimier aux pointes des ailerons : elle a une cause et un trajet.
Rien en porte-à-faux devant le visage : le front s'arrête à y 30,7 (au-dessus des yeux), l'œil d'orage dépasse de 0,28 px à plat.

Recherche (sources dans .claude/styles/orage.md) : anatomie du casque à lamelles (bombe de plaques rivetées, sommet à rosace,
couvre-nuque de 3 à 7 lames lacées, ailettes rabattues aux tempes, cimier fixé sur une douille) ; oiseau-tonnerre et dieu du
tonnerre (ailes, tambour, virgules) pour les motifs ; foudre : flash bref, zigzag à angles vifs, cœur blanc, bord violet.

Fonctions avancées (guide 4 bis, 5 ter, 6.3, 6.4) :
- arcs (3, deux formes chacun) : add_ en deux plaques croisées alignées sur le trajet (cimier → pointe d'aileron, pointe du
  cimier → fourche), visibles sous tous les angles sans cam_ ; flash de 0,13 s tiré au hasard (hachage sinus, q.life_time,
  q.instance_seed), une décharge toutes les 1,5 à 3 s au repos, plus en course, aucune en sommeil ;
- calque _e : cristaux (150–205), œil du front, filet des ailerons et zigzag du bandeau ; ctrl_lumiere qui s'avive aux décharges ;
- particle_etincelle / emit_etincelle (pointe du cimier et des ailerons, ctrl_emit −1 sauf pendant un arc) : étincelles qui montent ;
- event_equip (1,6 s) : un éclair (camy_) frappe le cimier, la bombe se forme, les lames descendent en cascade, les ailerons se
  déplient, le cimier jaillit, premier arc ; un son (block.copper_bulb.turn_on) ; event_unequip (1,2 s) : l'inverse, fin à l'échelle 0.
États utiles : idle, walk, run, sneak, sleep (les autres retombent sur idle). Pas d'attack ni de hurt (pièce portée).
À juger en jeu : additif des arcs (jour, shader), hasard des arcs, ctrl_*, particules, _e de nuit, casque de fer porté (Armure).
Contrôle : FLASH=1 (ou A, B) force les arcs visibles (.build/casque_orage_flash.bbmodel, jamais livré).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

NOM = "casque_orage"
TEX = 512
SS = 4
FLASH = os.environ.get("FLASH", "")
TAU = 2 * math.pi
RNG = np.random.default_rng(7)


def lerp(a, b, k):
    return a + (b - a) * k


METAL = np.array([(22, 24, 36), (46, 52, 72), (70, 78, 104), (112, 122, 154), (170, 182, 214)], np.float32)
OR = np.array([(130, 90, 30), (176, 128, 44), (220, 170, 60), (255, 230, 140)], np.float32)
CRIS = np.array([(40, 40, 120), (70, 90, 200), (130, 160, 255), (190, 208, 255), (232, 240, 255)], np.float32)
LAQUE = np.array([(18, 20, 38), (34, 40, 70), (52, 62, 104)], np.float32)
CORDON = np.array((118, 160, 232), np.float32)


def grille01(W, H):
    yy, xx = np.mgrid[0:H * SS, 0:W * SS]
    return (xx + 0.5) / (W * SS), (yy + 0.5) / (H * SS)


def bas(a, W, H):
    return np.array(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS))


def reduire(col, W, H, mask=None):
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = bas(col, W, H)
    out[..., 3] = 255 if mask is None else (bas(mask.astype(np.float32) * 255, W, H) > 110) * 255
    return out


def emis(line, W, H, rgb):
    e = np.zeros((H, W, 4), np.uint8)
    m = bas(line.astype(np.float32) * 255, W, H) > 110
    e[m, :3] = rgb
    e[m, 3] = 255
    return e


def brosse(shape, amp=0.05):
    """Brossé horizontal discret (±5 %, règle « métal propre »)."""
    H, W = shape
    n = RNG.normal(0, 1, (H // SS + 1, 1)) * amp
    n = np.repeat(n, SS, axis=0)[:H]
    return 1 + np.broadcast_to(n, (H, W))


def paroi(W, H, bande=0.36):
    """Paroi de la bombe : plaques verticales rivetées (haut), bandeau bas plus sombre bordé d'or et gravé d'un zigzag clair."""
    x, y = grille01(W, H)
    col = lerp(METAL[3], METAL[2], np.clip(y / (1 - bande), 0, 1)[..., None])
    col = col * brosse(x.shape)[..., None]
    ph = (x * 6) % 1
    seam = (ph < 0.025) | (ph > 0.985)
    hi = (ph > 0.025) & (ph < 0.045)
    haut = y < 1 - bande
    col = np.where((seam & haut)[..., None], METAL[0], col)
    col = np.where((hi & haut)[..., None], METAL[4], col)
    rv = np.hypot((ph - 0.5) * W / 6, (y - 0.16) * H) < 0.055 * H
    col = np.where((rv & haut & (y < 0.5))[..., None], lerp(METAL[4], OR[3], 0.3), col)
    yb = (y - (1 - bande)) / bande
    inb = y >= 1 - bande
    col = np.where(inb[..., None], lerp(METAL[2], METAL[1], np.clip(yb, 0, 1)[..., None]) * brosse(x.shape)[..., None], col)
    gold = inb & ((yb < 0.13) | (yb > 0.84))
    col = np.where(gold[..., None], lerp(OR[1], OR[3], np.clip(1 - np.abs(yb - 0.5), 0, 1)[..., None]), col)
    groove = inb & (((yb > 0.13) & (yb < 0.2)) | ((yb > 0.77) & (yb < 0.84)))
    col = np.where(groove[..., None], METAL[0], col)
    zz = 0.48 + 0.2 * (2 * np.abs(2 * (x * 9 - np.floor(x * 9 + 0.5))) - 1)
    zig = inb & (np.abs(yb - zz) < 0.075)
    col = np.where(zig[..., None], np.array((200, 216, 255), np.float32), col)
    return reduire(col, W, H), emis(zig, W, H, (130, 160, 240))


def dessus(N, cy=0.4):
    """Dessus de la bombe : plaques qui convergent vers la rosace (centre en cy), bord sombre."""
    x, y = grille01(N, N)
    dx, dy = x - 0.5, y - cy
    r = np.hypot(dx, dy)
    a = (np.degrees(np.arctan2(dy, dx)) + 360) % 30
    col = lerp(METAL[3], METAL[2], np.clip(r * 1.6, 0, 1)[..., None]) * brosse(x.shape, 0.04)[..., None]
    seam = ((a < 0.9) | (a > 29.4)) & (r > 0.12)
    col = np.where(seam[..., None], METAL[0], col)
    col = np.where(((a > 0.9) & (a < 1.8) & (r > 0.12))[..., None], METAL[4], col)
    edge = (np.minimum(np.minimum(x, 1 - x), np.minimum(y, 1 - y)) < 0.02)
    col = np.where(edge[..., None], METAL[1], col)
    return reduire(col, N, N)


def biseau(W, H):
    """Arête biseautée : bande claire qui accroche la lumière, filets sombres aux bords (u en travers)."""
    x, y = grille01(W, H)
    q = np.abs(x - 0.5) * 2
    col = lerp(METAL[4], METAL[3], q[..., None] ** 1.5)
    col = np.where((q > 0.82)[..., None], METAL[1], col)
    return reduire(col, W, H)


def metal_long(W=32, H=96):
    """Tronçon du cimier : u en travers (arête claire au milieu), v le long, bague d'or au pied."""
    x, y = grille01(W, H)
    q = np.abs(x - 0.5) * 2
    v = 3.3 * (1 - q ** 1.3) + 0.8 * (q < 0.14)
    col = METAL[np.clip(v.astype(int), 0, 4)]
    col = np.where((y > 0.9)[..., None], lerp(OR[1], OR[2], 1 - q[..., None]), col)
    return reduire(col, W, H)


def lame(W, H):
    """Lame du couvre-nuque : laque bleu nuit, ombre de recouvrement en haut, bord d'or en bas, cordons lacés bleu clair."""
    x, y = grille01(W, H)
    col = lerp(LAQUE[1], LAQUE[2], y[..., None])
    col = np.where((y < 0.18)[..., None], lerp(LAQUE[0], LAQUE[1], (y / 0.18)[..., None]), col)
    gold = y > 0.84
    col = np.where(gold[..., None], lerp(OR[3], OR[1], ((y - 0.84) / 0.16)[..., None]), col)
    n = W / 22.0
    ph = (x * n) % 1
    cord = ((np.abs(ph - 0.36) < 0.07) | (np.abs(ph - 0.64) < 0.07)) & (y > 0.24) & (y < 0.8)
    cord_o = ((np.abs(ph - 0.36) < 0.1) | (np.abs(ph - 0.64) < 0.1)) & (y > 0.21) & (y < 0.83)
    col = np.where(cord_o[..., None], LAQUE[0], col)
    col = np.where(cord[..., None], CORDON * (0.85 + 0.25 * (1 - y))[..., None], col)
    return reduire(col, W, H)


AILE_POLY = [(0.0, 0.62), (0.25, 0.78), (0.55, 0.9), (0.8, 0.97), (1.0, 1.0), (0.92, 0.62), (0.80, 0.70), (0.70, 0.34),
             (0.56, 0.44), (0.46, 0.10), (0.30, 0.20), (0.20, 0.0), (0.0, 0.05)]
AILE_AME = [((0.05, 0.35), (0.50, 0.62), 0.24), ((0.50, 0.66), (0.90, 0.90), 0.14)]


def aile(W, H):
    """Aileron : plume rabattue en marches d'éclair (u vers l'arrière, v vers le haut ; image : v = 1 en haut), bord d'or,
    gravures le long du balayage, filet lumineux sur l'axe."""
    mk = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(mk).polygon([(u * W * SS, (1 - v) * H * SS) for u, v in AILE_POLY], fill=255)
    m = np.array(mk) > 127
    inner = np.array(mk.filter(ImageFilter.MinFilter(4 * SS + 1))) > 127
    x, y = grille01(W, H)
    v = 1 - y
    col = lerp(METAL[3], METAL[4], np.clip(0.1 + 0.6 * x - 0.4 * np.abs(v - (0.3 + 0.6 * x)), 0, 1)[..., None])
    col = col * brosse(x.shape, 0.04)[..., None]
    axe = 0.38 + 0.55 * x ** 1.2
    for off in (-0.13, 0.13):
        col = np.where((np.abs(v - axe - off * (1 - 0.6 * x)) < 0.012)[..., None], METAL[0], col)
    filet = (np.abs(v - axe) < 0.022) & (x < 0.92)
    col = np.where(filet[..., None], np.array((190, 210, 255), np.float32), col)
    col = np.where((m & ~inner)[..., None], lerp(OR[1], OR[3], np.clip(v, 0, 1)[..., None]), col)
    out = reduire(col, W, H, m)
    e = emis(filet & inner, W, H, (140, 172, 255))
    e[out[..., 3] == 0] = 0
    return out, e


def cristal(W=32, H=64):
    x, y = grille01(W, H)
    q = np.abs(x - 0.5) * 2
    v = 1.0 + 2.6 * (1 - y) + 0.6 * (x < 0.5) - 0.8 * q
    col = CRIS[np.clip(v.astype(int), 0, 4)]
    tri_ = q < y * 1.02 + 0.03
    edge = (q > y * 1.02 - 0.14) | (q < 0.07)
    col = np.where(edge[..., None], CRIS[4], col)
    a = np.where(tri_, np.clip(170 + 40 * (1 - y) + 30 * edge, 170, 215), 0)
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = bas(col, W, H)
    out[..., 3] = np.array(Image.fromarray(a.astype(np.uint8), "L").resize((W, H), Image.BOX))
    e = np.zeros_like(out)
    ev = lerp(np.array((90, 110, 200)), np.array((165, 195, 255)), (1 - (np.arange(H) + 0.5) / H)[:, None, None])
    e[..., :3] = np.broadcast_to(ev, (H, W, 3)).astype(np.uint8)
    e[..., 3] = 255
    e[out[..., 3] == 0] = 0
    out[out[..., 3] == 0, :3] = 0
    return out, e


def medaillon(N=96):
    """Tambour du sommet : disque de métal, bord d'or clouté, trois virgules d'or en spirale."""
    x, y = grille01(N, N)
    x, y = x * 2 - 1, 1 - y * 2
    r = np.hypot(x, y)
    disc, rim = r < 0.97, (r > 0.80) & (r < 0.97)
    tom = np.zeros(x.shape, bool)
    for k in range(3):
        a0 = math.radians(90 + 120 * k)
        tom |= np.hypot(x - 0.30 * math.cos(a0), y - 0.30 * math.sin(a0)) < 0.19
        for j in range(1, 16):
            aj, rj = a0 + math.radians(9 * j), 0.30 + 0.018 * j
            tom |= np.hypot(x - rj * math.cos(aj), y - rj * math.sin(aj)) < 0.19 * (1 - j / 16.5)
    dot = np.zeros(x.shape, bool)
    for k in range(12):
        ak = math.radians(15 + 30 * k)
        dot |= np.hypot(x - 0.885 * math.cos(ak), y - 0.885 * math.sin(ak)) < 0.035
    shade = np.clip(0.5 + 0.35 * y - 0.25 * r, 0, 1)[..., None]
    col = lerp(METAL[1], METAL[3], shade)
    col = np.where(((r < 0.80) & (r > 0.74))[..., None], METAL[0], col)
    col = np.where(rim[..., None], lerp(OR[1], OR[3], shade), col)
    col = np.where(dot[..., None], METAL[0], col)
    col = np.where(tom[..., None], lerp(OR[0], OR[3], np.clip(shade + 0.1, 0, 1)), col)
    return reduire(col, N, N, disc)


def oeil(N=48):
    """Œil d'orage du front : chaton d'or, cristal bleu à reflet blanc ; le cristal est la source du calque _e."""
    x, y = grille01(N, N)
    x, y = x * 2 - 1, 1 - y * 2
    r = np.hypot(x, y)
    disc = r < 0.97
    gem = r < 0.6
    shade = np.clip(0.55 + 0.4 * y, 0, 1)[..., None]
    col = lerp(OR[0], OR[3], shade)
    col = np.where(((r > 0.6) & (r < 0.68))[..., None], METAL[0], col)
    col = np.where(gem[..., None], lerp(CRIS[1], CRIS[3], np.clip(0.5 + 0.5 * y - 0.6 * r, 0, 1)[..., None]), col)
    hl = np.hypot(x + 0.2, y - 0.25) < 0.16
    col = np.where(hl[..., None], CRIS[4], col)
    out = reduire(col, N, N, disc)
    e = emis(gem, N, N, (150, 180, 255))
    e[emis(hl, N, N, (1, 1, 1))[..., 3] > 0, :3] = (210, 225, 255)
    return out, e


WHITE, BLUE, VIOLET = np.array((250, 250, 240), np.float32), np.array((150, 210, 255), np.float32), np.array((120, 80, 255), np.float32)


def _segd(X, Y, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = max(vx * vx + vy * vy, 1e-9)
    t = np.clip(((X - a[0]) * vx + (Y - a[1]) * vy) / L2, 0, 1)
    return np.hypot(X - a[0] - t * vx, Y - a[1] - t * vy)


def bolt(seed, W, H, n=5, w0=4.2, w1=2.8, ss=4):
    """Éclair de l'ensemble (cœur blanc, halo bleu, bord violet) : (tuile add_, tuile trans_), racine en haut au centre."""
    r = np.random.default_rng(seed)
    pts = [(0.5, 0.0)]
    side = 1 if r.random() < 0.5 else -1
    for i in range(1, n):
        pts.append((float(np.clip(0.5 + side * r.uniform(0.12, 0.26), 0.18, 0.82)), i / n + float(r.uniform(-0.04, 0.04))))
        side = -side
    pts.append((0.5 + float(r.uniform(-0.06, 0.06)), 1.0))
    chans = [(pts, w0, w1)]
    for i in r.choice(np.arange(1, n - 1), size=2, replace=False):
        bx, by = pts[int(i)]
        d = 1 if bx >= 0.5 else -1
        br = [(bx, by), (float(np.clip(bx + d * r.uniform(0.10, 0.16), 0.06, 0.94)), by + float(r.uniform(0.08, 0.12)))]
        br.append((float(np.clip(br[-1][0] - d * r.uniform(0.02, 0.06), 0.06, 0.94)), br[-1][1] + float(r.uniform(0.06, 0.10))))
        chans.append((br, w0 * 0.36, w0 * 0.2))
    yy, xx = np.mgrid[0:H * ss, 0:W * ss]
    X, Y = (xx + 0.5) / ss, (yy + 0.5) / ss
    best = np.full(X.shape, 1e9)
    for P, wa, wb in chans:
        for j in range(len(P) - 1):
            ww = lerp(wa, wb, j / max(1, len(P) - 2))
            best = np.minimum(best, _segd(X, Y, (P[j][0] * W, P[j][1] * H), (P[j + 1][0] * W, P[j + 1][1] * H)) / ww)
    core = np.clip((0.34 - best) / 0.12, 0, 1)
    g1, g2 = np.exp(-(best / 1.45) ** 2), np.exp(-(best / 2.8) ** 2)
    rgb = np.maximum.reduce([VIOLET * 0.62 * g2[..., None], BLUE * 0.92 * g1[..., None], WHITE * core[..., None]])
    im = bas(rgb, W, H)
    add = np.zeros((H, W, 4), np.uint8)
    lum = im.max(axis=2)
    add[..., :3] = np.where((lum > 16)[..., None], im, 0)
    add[..., 3] = (lum > 16) * 255
    fa = np.array(Image.fromarray(np.where(best < 0.45, 180, np.where(best < 1.25, 120, 0)).astype(np.uint8), "L").resize((W, H), Image.BOX)).astype(np.float32)
    cc = np.array(Image.fromarray(((best < 0.45) * 255).astype(np.uint8), "L").resize((W, H), Image.BOX)).astype(np.float32) / 255
    tr = np.zeros((H, W, 4), np.uint8)
    tr[..., :3] = lerp(np.array((150, 185, 255), np.float32), np.array((236, 242, 255), np.float32), cc[..., None]).astype(np.uint8)
    al = np.where(fa >= 30, np.clip(fa, 120, 180), 0)
    tr[..., 3] = al.astype(np.uint8)
    tr[al == 0, :3] = 0
    return add, tr


def etincelle(N=16):
    x, y = grille01(N, N)
    x, y = x * 2 - 1, y * 2 - 1
    d = np.abs(x) ** 0.5 + np.abs(y) ** 0.5
    m = bas((d < 0.95) * 255.0, N, N) > 110
    c = bas((d < 0.55) * 255.0, N, N) > 110
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = (150, 200, 255)
    out[c, :3] = (245, 248, 255)
    out[..., 3] = m * 255
    return out


# ------------------------------------------------------------------ texture (rangement en étagères)
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_shelf = {"x": 0, "y": 0, "h": 0}


_file = []


def poser(nom, im, em=None):
    _file.append((nom, im, em))


def ranger():
    """Rangement en étagères, des plus hautes tuiles aux plus basses."""
    x = y = hs = 0
    for nom, im, em in sorted(_file, key=lambda t: -t[1].shape[0]):
        h, w = im.shape[:2]
        if x + w > TEX:
            x, y, hs = 0, y + hs + 1, 0
        assert y + h <= TEX - 4, nom
        tex[y:y + h, x:x + w] = im
        if em is not None:
            tex_e[y:y + h, x:x + w] = em
        UV[nom] = (x, y, x + w, y + h)
        x, hs = x + w + 1, max(hs, h)


PX = 24                                             # texels par pixel de modèle (bombe, lames, ailerons)
RI, T = 4.66, 0.55
RO = RI + T
YT, YTO, YW, YB, YF = 32.66, 33.21, 32.4, 28.8, 30.7
p_, e_ = paroi(int(2 * RI * PX), int((YW - YB) * PX), bande=0.34)
poser("paroi", p_, e_)
p_, e_ = paroi(int(2 * RI * PX), int((YW - YF) * PX), bande=0.5)
poser("front", p_, e_)
poser("dessus", dessus(int(2 * RI * 16), cy=(RI - 0.9) / (2 * RI)))
AL, AHT = 7.6, 5.6
AW, AH = int(AL * PX), int(AHT * PX)
a_, ae_ = aile(AW, AH)
poser("aile", a_, ae_)
poser("lame", lame(int(9.6 * PX), int(1.3 * PX)))
poser("biseau", biseau(24, 224))
poser("metal", metal_long())
c_, ce_ = cristal()
poser("cristal", c_, ce_)
poser("medal", medaillon())
o_, oe_ = oeil()
poser("oeil", o_, oe_)
poser("spark", etincelle())
for i, sd in enumerate((131, 147, 183)):
    a_, _t = bolt(sd, 48, 112)
    poser(f"boltH{i}", np.ascontiguousarray(np.transpose(a_, (1, 0, 2))))
for i, sd in enumerate((31, 47)):
    a_, t_ = bolt(sd, 64, 112)
    poser(f"boltV{i}", a_)
    poser(f"boltVT{i}", t_)
ranger()
for n in UV:
    if not (n.startswith("boltVT") or n == "cristal"):
        u0, v0, u1, v1 = UV[n]
        assert set(np.unique(tex[v0:v1, u0:u1, 3])) <= {0, 255}, n
_b64 = []
for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(fn, optimize=True)
    _buf = io.BytesIO()
    im_.save(_buf, "PNG", optimize=True)
    _b64.append("data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode())


# ------------------------------------------------------------------ géométrie
def nuid():
    return str(_uuid.uuid4())


class G:
    def __init__(self, nom, origin, parent=None, rot=None):
        assert len(nom) <= 64
        self.nom, self.origin, self.uuid, self.enfants = nom, [round(float(v), 3) for v in origin], nuid(), []
        self.rot = rot
        self.parent = parent
        if parent is not None:
            parent.enfants.append(self)

    def json(self):
        d = {"name": self.nom, "origin": self.origin, "uuid": self.uuid, "children": [c.json() if isinstance(c, G) else c for c in self.enfants]}
        if self.rot is not None and any(self.rot):
            d["rotation"] = [round(float(v), 3) for v in self.rot]
        return d


def Rm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
            @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))


def monde(p, g):
    """Position au repos d'un point défini dans le repère non tourné, sous le groupe g (rotations des groupes parents)."""
    p = np.array(p, float)
    while g is not None:
        if g.rot is not None and any(g.rot):
            o = np.array(g.origin)
            p = Rm(*g.rot) @ (p - o) + o
        g = g.parent
    return p


elements = []


def cube(g, nom, a, b, origin, faces, rot=None):
    a, b = [min(u, v) for u, v in zip(a, b)], [max(u, v) for u, v in zip(a, b)]
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in a], "to": [round(float(v), 3) for v in b],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False, "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if rot is not None and any(rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    g.enfants.append(e["uuid"])
    return e


def uvr(n, fu=False, fv=False, part=None):
    u0, v0, u1, v1 = UV[n]
    if part:
        a, b, c, d = part
        u0, u1, v0, v1 = u0 + (u1 - u0) * a, u0 + (u1 - u0) * b, v0 + (v1 - v0) * c, v0 + (v1 - v0) * d
    return [u1 if fu else u0, v1 if fv else v0, u0 if fu else u1, v0 if fv else v1]


SOMBRE = uvr("metal", part=(0.0, 0.1, 0.0, 0.5))         # faces cachées ou dessous : métal sombre (bord de la tuile)
HEAD = G("head", (0, 24, 0))
CASQ = G("casque", (0, 31, 0), HEAD)
G("ctrl_lumiere", (0, 31, 0), CASQ)

# --- bombe
BOMBE = G("bombe", (0, 31, 0), CASQ)
paroi_ = uvr("paroi")
cube(BOMBE, "paroi_av", (-RI, YF, -RO), (RI, YW, -RI), (0, 31, 0), {"north": uvr("front"), "south": SOMBRE, "down": SOMBRE})
cube(BOMBE, "paroi_ar", (-RI, YB, RI), (RI, YW, RO), (0, 31, 0), {"south": paroi_, "north": SOMBRE, "down": SOMBRE})
cube(BOMBE, "paroi_d", (RI, YB, -RI), (RO, YW, RI), (0, 31, 0), {"east": paroi_, "west": SOMBRE, "down": SOMBRE, "north": uvr("biseau", part=(0.1, 0.9, 0, 0.3))})
cube(BOMBE, "paroi_g", (-RO, YB, -RI), (-RI, YW, RI), (0, 31, 0), {"west": paroi_, "east": SOMBRE, "down": SOMBRE, "north": uvr("biseau", part=(0.1, 0.9, 0, 0.3))})
cube(BOMBE, "dessus", (-RI, YT, -RI), (RI, YTO, RI), (0, 31, 0), {"up": uvr("dessus")})
# arêtes biseautées : barres à 45°, face intérieure sur x + y = 37,45 (le coin de la seconde couche est à 37,0)
BC, BW, BT = 4.95, 1.0, 0.5
YC = 32.85
bz = uvr("biseau")                                            # u en travers, v le long
bx = [bz[1], bz[0], bz[3], bz[2]]                             # même tuile couchée (approx. : seule la bande claire compte)
for sx in (1, -1):
    c = (sx * BC, YC, 0)
    cube(BOMBE, f"biseau_{'dg'[sx < 0]}", (c[0] - BT / 2, YC - BW / 2, -RI), (c[0] + BT / 2, YC + BW / 2, RI), c,
         {"up": bz, "east" if sx > 0 else "west": bz, "down": SOMBRE}, rot=(0, 0, 45 * sx))
for sz in (1, -1):
    c = (0, YC, sz * BC)
    cube(BOMBE, f"biseau_{'ar' if sz > 0 else 'av'}", (-RI, YC - BW / 2, c[2] - BT / 2), (RI, YC + BW / 2, c[2] + BT / 2), c,
         {"up": uvr("biseau", part=(0, 1, 0, 1)), "south" if sz > 0 else "north": uvr("biseau"), "down": SOMBRE}, rot=(-45 * sz, 0, 0))
# montants des coins (verticaux, à 45°) et rivets d'or aux coins du dessus
for sx in (1, -1):
    for sz in (1, -1):
        c = (sx * BC, 0, sz * BC)
        y0 = YB if sz > 0 else YF - 0.1                  # devant : rien au niveau du visage
        pv = uvr("biseau", part=(0, 1, 0, 0.3))
        cube(BOMBE, f"montant_{'dg'[sx < 0]}{'ar' if sz > 0 else 'av'}", (c[0] - BT / 2, y0, c[2] - BW / 2), (c[0] + BT / 2, YW + 0.1, c[2] + BW / 2),
             (c[0], 31, c[2]), {"east": pv, "west": pv, "down": SOMBRE}, rot=(0, -45 * sx * sz, 0))
        r = 0.42
        cr = (sx * 5.0, YC + 0.05, sz * 5.0)
        orr = uvr("oeil", part=(0.03, 0.15, 0.45, 0.55))
        cube(BOMBE, f"rivet_{'dg'[sx < 0]}{'ar' if sz > 0 else 'av'}", (cr[0] - r, cr[1] - r, cr[2] - r), (cr[0] + r, cr[1] + r, cr[2] + r), cr,
             {f: orr for f in ("north", "south", "east", "west", "up", "down")}, rot=(0, 45, 0))
# gradin du dessus (profil de bombe) : plaque plus étroite posée sur le dessus, chants biseautés clairs
TY0, TY1 = 33.05, 33.7
chant = uvr("biseau", part=(0.25, 0.75, 0, 1))
cube(BOMBE, "gradin", (-3.5, TY0, -3.6), (3.5, TY1, 3.4), (0, 33, 0),
     {"up": uvr("dessus", part=(0.12, 0.88, 0.1, 0.86)), "north": chant, "south": chant, "east": chant, "west": chant})
# tambour du sommet (rosace) : disque découpé (face up), âme octogonale
DZ = -0.9
TAMB = G("tambour", (0, 33.75, DZ), BOMBE)
cube(TAMB, "tambour", (-1.5, 33.56, DZ - 1.5), (1.5, 33.96, DZ + 1.5), (0, 33.75, DZ), {"up": uvr("medal")})
for j, ry in enumerate((0, 45)):
    rr = 1.02 * (1 if j == 0 else 0.985)
    m_ = uvr("metal", part=(0, 1, 0.3, 0.6))
    cube(TAMB, f"tambour_k{j}", (-rr, 33.6, DZ - rr), (rr, 33.91 - 0.02 * j, DZ + rr), (0, 33.75, DZ), {"north": m_, "south": m_, "east": m_, "west": m_}, rot=(0, ry, 0))
# œil d'orage au front : chaton découpé (face nord) + âme, à plat sur la paroi (rien en porte-à-faux)
OY = (YF + YW) / 2
OEIL = G("oeil", (0, OY, -RO), BOMBE)
cube(OEIL, "oeil", (-0.8, OY - 0.8, -RO - 0.28), (0.8, OY + 0.8, -RO + 0.1), (0, OY, -RO), {"north": uvr("oeil")})
cube(OEIL, "oeil_k", (-0.55, OY - 0.55, -RO - 0.24), (0.55, OY + 0.55, -RO + 0.06), (0, OY, -RO),
     {f: uvr("oeil", part=(0.03, 0.15, 0.45, 0.55)) for f in ("east", "west", "up", "down")}, rot=(0, 0, 45))

# --- couvre-nuque : 3 lames évasées, octogone (côtés, coins à 45°, dos)
LAMES = []
for k in range(3):
    ac, ad, th = 4.95 + 0.32 * k, 6.62 + 0.32 * k, 0.36
    yt, h, fl = YB + 0.15 - 1.0 * k, 1.3, 12 + 8 * k
    tc = ad * math.sqrt(2) - ac
    hd = (ac - tc) / math.sqrt(2) + 0.12
    LG = G(f"lame{k + 1}", (0, yt, 0), CASQ)
    LAMES.append(LG)
    segs = [("ar", 0, ac, -tc - 0.12, tc + 0.12), ("cd", 45, ad, -hd, hd), ("cg", -45, ad, -hd - 0.02, hd),
            ("d", 90, ac, -tc - 0.12, 0.6), ("g", -90, ac, -0.6, tc + 0.12)]
    W9 = 9.6
    for nom, yaw, a, t0, t1 in segs:
        gy = G(f"lame{k + 1}_{nom}", (0, yt, 0), LG, rot=(0, yaw, 0))
        gf = G(f"lame{k + 1}_{nom}_f", (0, yt, a), gy, rot=(-fl, 0, 0))
        pu = ((t0 + W9 / 2) / W9, (t1 + W9 / 2) / W9)
        f_ = uvr("lame", part=(max(0, pu[0]), min(1, pu[1]), 0, 1))
        cube(gf, f"lame{k + 1}_{nom}", (t0, yt - h, a), (t1, yt, a + th), (0, yt, a),
             {"south": f_, "north": uvr("lame", part=(0.1, 0.2, 0.1, 0.2)), "down": uvr("lame", part=(0, 1, 0.9, 1.0))})

# --- ailerons-paratonnerres
AILES, TIPS_A = [], {}
for sx in (1, -1):
    sd = "dg"[sx < 0]
    piv = (sx * 5.4, 31.6, -3.9)
    gy = G(f"aileron_{sd}", piv, CASQ, rot=(0, 34 * sx, 0))
    gr = G(f"aileron_{sd}_r", piv, gy, rot=(-14, 0, -13 * sx))
    AILES.append((gy, gr, sx))
    x0, x1 = sorted((sx * 5.30, sx * 5.80))
    z0, L, y0, H = -4.3, AL, 29.6, AHT
    out_f, in_f = ("east", "west") if sx > 0 else ("west", "east")
    cube(gr, f"aileron_{sd}", (x0, y0, z0), (x1, y0 + H, z0 + L), piv, {out_f: uvr("aile", fu=sx > 0), in_f: uvr("aile", fu=sx < 0)})
    xa0, xa1 = sorted((sx * 5.42, sx * 5.68))
    for j, ((ua, va), (ub, vb), wv) in enumerate(AILE_AME):
        pa = np.array((z0 + L * ua, y0 + H * va))
        pb = np.array((z0 + L * ub, y0 + H * vb))
        mid, d = (pa + pb) / 2, pb - pa
        ln = float(np.hypot(*d))
        al = -math.degrees(math.atan2(d[1], d[0]))
        w = wv * H
        m_ = uvr("metal", part=(0.35, 0.65, 0.2, 0.8))
        cube(gr, f"aileron_{sd}_ame{j}", (xa0, mid[1] - w / 2, mid[0] - ln / 2), (xa1, mid[1] + w / 2, mid[0] + ln / 2), (0, mid[1], mid[0]),
             {"up": m_, "down": m_, "north": m_, "south": m_}, rot=(al, 0, 0))
    m_ = uvr("oeil", part=(0.03, 0.15, 0.45, 0.55))
    cube(gr, f"charniere_{sd}", (sx * 5.1, 30.5, -4.5), (sx * 5.62, 32.5, -3.5), piv, {f: m_ for f in ("north", "south", "east", "west", "up", "down")})
    # pointe de cristal : deux plaques croisées dans l'axe du balayage
    tip = np.array((z0 + L, y0 + H))
    dz_, dy_ = 1.0, 0.7
    nn = math.hypot(dz_, dy_)
    dz_, dy_ = dz_ / nn, dy_ / nn
    Lc = 1.7
    base = tip - 0.45 * np.array((dz_, dy_))
    cc = base + Lc / 2 * np.array((dz_, dy_))
    xm = sx * 5.55
    be = math.degrees(math.atan2(dz_, dy_))
    gc = G(f"cristal_{sd}", (xm, base[1], base[0]), gr)
    tg = G(f"trans_cristal_{sd}", (xm, base[1], base[0]), gc)
    cr = uvr("cristal")
    cube(tg, f"cristal_{sd}", (xm - 0.15, cc[1] - Lc / 2, cc[0] - 0.5), (xm + 0.15, cc[1] + Lc / 2, cc[0] + 0.5), (xm, cc[1], cc[0]), {"east": cr, "west": cr}, rot=(be, 0, 0))
    cube(tg, f"cristal_{sd}r", (xm - 0.42, cc[1] - Lc / 2, cc[0] - 0.15), (xm + 0.42, cc[1] + Lc / 2, cc[0] + 0.15), (xm, cc[1], cc[0]), {"north": cr, "south": cr}, rot=(be, 0, 0))
    end = base + (Lc - 0.1) * np.array((dz_, dy_))
    TIPS_A[sd] = (gc, (xm, end[1], end[0]))

# --- cimier : éclair de métal en zigzag, bout et fourche en cristal
CB = np.array((0.0, 33.9, DZ))
CIM = G("cimier", tuple(CB), CASQ)
cube(CIM, "douille", (-0.62, 33.7, DZ - 1.05), (0.62, 34.45, DZ + 0.9), tuple(CB), {f: uvr("oeil", part=(0.03, 0.15, 0.45, 0.55)) for f in ("north", "south", "east", "west", "up")})
ZC = [(0.0, 0.0), (-0.8, 3.1), (1.5, 4.0), (0.8, 7.0)]
SC = [(1.9, 1.0), (1.5, 0.85), (1.3, 0.7)]
for i in range(3):
    (u0, v0), (u1, v1) = ZC[i], ZC[i + 1]
    w, th = SC[i]
    L = math.hypot(u1 - u0, v1 - v0) + w * 0.5
    ang = math.degrees(math.atan2(u1 - u0, v1 - v0))
    c = (0.0, CB[1] + (v0 + v1) / 2, CB[2] + (u0 + u1) / 2)
    m_ = uvr("metal", part=(0, 1, 0, 0.6 + 0.4 * (i == 0)))
    cube(CIM, f"cimier{i}", (-th / 2, c[1] - L / 2, c[2] - w / 2), (th / 2, c[1] + L / 2, c[2] + w / 2), c,
         {**{f: m_ for f in ("north", "south", "east", "west")}, "up": uvr("metal", part=(0, 1, 0, 0.1))}, rot=(ang, 0, 0))


def pointe_cristal(parent, nom, p0, p1, w):
    """Cristal d'orage entre p0 et p1 (dans le plan YZ, en (z, y) relatifs à CB) : deux plaques croisées trans_."""
    a = CB + np.array((0, p0[1], p0[0]))
    b = CB + np.array((0, p1[1], p1[0]))
    d = b - a
    L = float(np.linalg.norm(d)) + 0.3
    be = math.degrees(math.atan2(d[2], d[1]))
    c = (a + b) / 2 + 0.1 * d / np.linalg.norm(d)
    g = G(f"cristal_{nom}", tuple(a), parent)
    tg = G(f"trans_cristal_{nom}", tuple(a), g)
    cr = uvr("cristal")
    cube(tg, f"cristal_{nom}", (-0.15, c[1] - L / 2, c[2] - w / 2), (0.15, c[1] + L / 2, c[2] + w / 2), tuple(c), {"east": cr, "west": cr}, rot=(be, 0, 0))
    cube(tg, f"cristal_{nom}r", (-w * 0.42, c[1] - L / 2, c[2] - 0.15), (w * 0.42, c[1] + L / 2, c[2] + 0.15), tuple(c), {"north": cr, "south": cr}, rot=(be, 0, 0))
    return g, b


GCT, TIP_C = pointe_cristal(CIM, "cimier", (0.75, 6.7), (2.3, 9.4), 1.4)
GCF, TIP_F = pointe_cristal(CIM, "fourche", (1.5, 3.9), (3.1, 5.3), 0.9)
CRISTAUX = [GCT, GCF, TIPS_A["d"][0], TIPS_A["g"][0]]

# --- points d'émission (étincelles)
EMITS = []
for k, (g, p) in enumerate([(GCT, TIP_C), (TIPS_A["d"][0], TIPS_A["d"][1]), (TIPS_A["g"][0], TIPS_A["g"][1])]):
    e = G("emit_etincelle" + (str(k + 1) if k else ""), tuple(p), g)
    G("ctrl_emit", tuple(p), e)
    EMITS.append((e, 0.41 + 3.17 * k))

# --- arcs : du cimier aux pointes des ailerons, et de la pointe du cimier à la fourche
ARC_GRP = G("arcs", (0, 36, 0), CASQ)
J = CB + np.array((0, 4.0, 1.5))                                   # coude du cimier (point P2)
ARCS = []
trajets = [(J + np.array((0.35, 0.1, 0)), monde(TIPS_A["d"][1], TIPS_A["d"][0])),
           (J + np.array((-0.35, 0.1, 0)), monde(TIPS_A["g"][1], TIPS_A["g"][0])),
           (np.array(TIP_C) - np.array((0, 0.2, 0.2)), np.array(TIP_F) + np.array((0, 0.1, 0.1)))]
for i, (S, E) in enumerate(trajets):
    M, d = (S + E) / 2, E - S
    hz = math.hypot(d[0], d[2])
    ty = math.degrees(math.atan2(-d[2], d[0])) if hz > 1e-6 else 0.0
    ph = math.degrees(math.atan2(d[1], hz))
    L = float(np.linalg.norm(d)) * 1.04
    hh = 0.95 if L > 5 else 0.6
    gy = G(f"arc{i + 1}", tuple(M), ARC_GRP, rot=(0, ty, 0))
    gp = G(f"arc{i + 1}_p", tuple(M), gy, rot=(0, 0, ph))
    forms = []
    for j in range(2):
        fg = G(f"arc{i + 1}{'ab'[j]}", tuple(M), gp)
        G("ctrl_alpha", tuple(M), fg)
        ga = G(f"add_arc{i + 1}{'ab'[j]}", tuple(M), fg)
        ti = (i + j) % 3
        f_ = uvr(f"boltH{ti}", fv=j == 1)
        o = 0.08 * j
        cube(ga, f"arc{i + 1}{'ab'[j]}", (M[0] - L / 2, M[1] - hh, M[2] - 0.15 + o), (M[0] + L / 2, M[1] + hh, M[2] + 0.15 + o), tuple(M),
             {"north": f_, "south": f_})
        cube(ga, f"arc{i + 1}{'ab'[j]}x", (M[0] - L / 2, M[1] - 0.15 - o, M[2] - hh), (M[0] + L / 2, M[1] + 0.15 - o, M[2] + hh), tuple(M),
             {"up": f_, "down": f_})
        forms.append(fg)
    ARCS.append((forms[0], forms[1], 0.41 + 3.17 * i))

# --- éclair de l'apparition : camy_ du ciel jusqu'à la pointe du cimier ; caché dans les états
FC = (0, 53, 0.5)
FOUDRE = G("foudre", FC, HEAD)
CAMY = G("camy_foudre", FC, FOUDRE)
CA_F = G("ctrl_alpha", FC, CAMY)
FA, FT = G("add_foudre", FC, CAMY), G("trans_foudre", FC, CAMY)
for j in range(2):
    y1 = 63.5 - 10.0 * j                                          # bas de l'éclair à y = 43 : la pointe du cimier
    cube(FA, f"foudre{j}", (-2.6, y1 - 10, 0.35), (2.6, y1, 0.65), FC, {"south": uvr(f"boltV{j}", fu=j == 1)})
    cube(FT, f"foudre{j}t", (-2.65, y1 - 10.1, -0.55 - 0.3 * j), (2.65, y1 + 0.1, -0.25 - 0.3 * j), FC, {"south": uvr(f"boltVT{j}", fu=j == 1)})

PART = G("particle_etincelle", (0, 0, 0))
cube(PART, "etincelle", (-0.25, 0.3, -0.15), (0.25, 0.8, 0.15), (0, 0.55, 0), {"south": uvr("spark")})
outliner = [HEAD.json(), PART.json()]


# ------------------------------------------------------------------ animations
def s(v):
    return v if isinstance(v, str) else str(round(v + 0.0, 4))


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": s(x), "y": s(y), "z": s(z)}], "time": round(t, 4), "interpolation": "linear"}


def piste(A, g, keys):
    A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += keys


def vis(P, p, c, w0, w1):
    if FLASH:
        return "1" if FLASH == "1" or (FLASH == "A") == (w0 == 0) else "0"
    x = f"(q.life_time/{P:g}+q.instance_seed*17+{c:.3g})"
    k = f"math.mod(math.abs(math.sin(math.floor({x})*127.1))*437.585,1)"
    w = f"(math.mod({x},1)-0.05-{k}*{0.8 / p:.3g})"
    return f"({k}<{p:g})*({w}>{w0 / P:.3g})*({w}<{w1 / P:.3g})"


def etat(nom, L, rate, pulse=0.04):
    A = {}
    P, p = rate
    for fa, fb, c in ARCS:
        for j, fg in enumerate((fa, fb)):
            w0, w1 = ((0.0, 0.06), (0.06, 0.13))[j]
            e = "-1" if p == 0 else f"{vis(P, p, c, w0, w1)}-1"
            assert len(e) <= 512
            piste(A, fg.enfants[0], [kf("position", 0, e, 0, 0)])
    for g, c in EMITS:
        piste(A, g.enfants[0], [kf("position", 0, "-1" if p == 0 else f"8*{vis(P, p, c, 0.0, 0.22)}-1", 0, 0)])
    piste(A, CA_F, [kf("position", 0, -1, 0, 0)])
    c0 = ARCS[0][2]
    piste(A, CASQ.enfants[0], [kf("position", 0, "-0.4" if p == 0 else f"1.2*{vis(P, p, c0, 0.0, 0.2)}-0.4", 0, 0)])
    for i, g in enumerate(CRISTAUX):                       # cristaux qui respirent ; le casque reste rigide
        sc = f"1+{s(pulse)}*math.sin(q.anim_time*{s(360 * 2 / L)}+{70 * i})"
        piste(A, g, [kf("scale", 0, sc, sc, sc)])
    return {"uuid": nuid(), "name": nom, "loop": "loop", "override": False, "length": L, "snapping": 24, "selected": nom == "idle", "animators": A}


STATES = [etat("idle", 8.0, (5.0, 0.4)), etat("walk", 1.6, (4.0, 0.45)), etat("run", 1.0, (2.5, 0.6)),
          etat("sneak", 4.0, (9.0, 0.25), 0.02), etat("sleep", 4.0, (1.0, 0.0), 0.01)]


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def creneaux(ch, fen, L, val=1.0):
    ts = {0.0, L}
    for a, b in fen:
        ts |= {max(0.0, a - 0.005), a, max(0.0, b - 0.005), b}
    out = []
    for t in sorted(ts):
        tt = t if t < L else L - 1e-6
        out.append(kf(ch, t, val if any(a <= tt < b for a, b in fen) else 0.0, 0, 0))
    return out


def apparition(A, fg, fen, L):
    """Flash forcé par-dessus l'état : ctrl_alpha +1 pendant l'animation (0 à la fin), échelle 0 hors des fenêtres."""
    piste(A, fg.enfants[0], [kf("position", 0, 1, 0, 0), kf("position", L - 0.005, 1, 0, 0), kf("position", L, 0, 0, 0)])
    ks = creneaux("position", fen, L)
    piste(A, fg, [kf("scale", k["time"], *([float(k["data_points"][0]["x"])] * 3)) for k in ks[:-1]] + [kf("scale", L, 1, 1, 1)])


def event(nom, L, f_bombe, f_lame, f_aile, f_cimier, foudre, arcs=None, son=None):
    T = [round(j * L / 40, 4) for j in range(41)]
    A = {}
    piste(A, CA_F, creneaux("position", foudre, L))
    piste(A, BOMBE, [kf("scale", t, *([f_bombe(t)] * 3)) for t in T])
    for k, g in enumerate(LAMES):
        piste(A, g, [kf("scale", t, *([f_lame(t, k)] * 3)) for t in T])
    for gy, gr, sx in AILES:
        piste(A, gy, [kf("rotation", t, 0, -34 * sx * f_aile(t)[0], 0) for t in T])
        piste(A, gr, [kf("scale", t, *([f_aile(t)[1]] * 3)) for t in T])
    piste(A, CIM, [kf("scale", t, *([f_cimier(t)] * 3)) for t in T])
    if arcs:
        for i, fen in arcs:
            apparition(A, ARCS[i][0], fen, L)
    a = {"uuid": nuid(), "name": nom, "loop": "once", "override": False, "length": L, "snapping": 24, "selected": False, "animators": A}
    if son:
        a["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
            {"channel": "sound", "data_points": [{"effect": son, "file": ""}], "time": 0.04}]}
    return a


EQ = 1.6
equip = event("event_equip", EQ,
              lambda t: 1.0 if t >= EQ else 0.02 + 0.98 * sm(t, 0.14, 0.45) + 0.04 * bump(t, 0.4, 0.45, 0.5, 0.62),
              lambda t, k: 1.0 if t >= EQ else 0.02 + 0.98 * sm(t, 0.38 + 0.11 * k, 0.62 + 0.11 * k),
              lambda t: (0.0, 1.0) if t >= EQ else (1 - sm(t, 0.82, 1.12) - 0.08 * bump(t, 1.05, 1.12, 1.16, 1.3), 0.02 + 0.98 * sm(t, 0.62, 0.86)),
              lambda t: 1.0 if t >= EQ else 0.02 + 0.98 * sm(t, 0.86, 1.14) + 0.10 * bump(t, 1.08, 1.14, 1.2, 1.36),
              [(0.04, 0.12), (0.15, 0.24)], arcs=[(0, [(1.22, 1.30)]), (1, [(1.26, 1.34)]), (2, [(1.18, 1.25)])],
              son="block.copper_bulb.turn_on")
UQ = 1.2
equip_u = lambda t: 0.0 if t >= UQ - 1e-6 else 1.0
unequip = event("event_unequip", UQ,
                lambda t: equip_u(t) * (1 - sm(t, 0.75, 1.15)),
                lambda t, k: equip_u(t) * (1 - sm(t, 0.45 + 0.1 * (2 - k), 0.75 + 0.1 * (2 - k))),
                lambda t: (sm(t, 0.15, 0.45), equip_u(t) * (1 - sm(t, 0.35, 0.6))),
                lambda t: equip_u(t) * (1 - sm(t, 0.0, 0.35)),
                [(0.0, 0.08)])

PF = 0.4
p_fall = {"uuid": nuid(), "name": "particle_etincelle_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24, "selected": False,
          "animators": {PART.uuid: {"name": PART.nom, "type": "bone", "keyframes":
                        [kf("scale", t, *([1 + 0.35 * math.cos(TAU * t / PF)] * 3)) for t in [i * PF / 8 for i in range(9)]]}}}

ANIMS = STATES + [equip, unequip, p_fall]
assert len(ANIMS) <= 32
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner,
         "textures": [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": _b64[0]},
                      {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": _b64[1]}],
         "animations": ANIMS}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel" if not FLASH else f".build/{NOM}_flash.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


def ngroupes(n):
    return 1 + sum(ngroupes(c) for c in n.get("children", []) if isinstance(c, dict))


# contrôle des distances à la tête (au repos) : coins des cubes opaques du casque hors des groupes d'effet
print(len(elements), "cubes ;", sum(ngroupes(n) for n in outliner), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;", len(EMITS), "emit_")
