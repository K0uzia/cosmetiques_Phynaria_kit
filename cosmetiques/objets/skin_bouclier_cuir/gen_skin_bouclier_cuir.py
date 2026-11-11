"""Rondache de latex : skin d'objet (guide 14) pour tous les boucliers du joueur, ensemble Cuir (thème Fétiche).
Design original, rien d'explicite. Écrit skin_bouclier_cuir.png et .build/skin_bouclier_cuir_brut.bbmodel à côté de ce script.

D'après de vraies rondaches (.claude/references/objets/boucliers.md) : bouclier rond, umbo bombé au centre (la main est
derrière lui), bordure qui tient la peau, enarmes (poignée + sangle d'avant-bras) au dos, guige (sangle de port). Ici la peau
est du latex noir verni **tendu** sur une armature chromée à 8 rayons : chaque pan est plan, tendu d'un rayon à l'autre, comme
une ombrelle ; le cône très plat (10°) fait le bombé. Bordure chromée rivetée, umbo chromé en gradins, deux sangles de latex
sur la face (anneau en O et boucle à rouleau, comme le harnais du set) qui passent sous la bordure ; au dos, poignée tressée
sur deux pattes chromées et deux sangles en H, anneaux en O, boucles.

Repère (vérifié sur le bouclier vanilla, .build/vanille.py) : le bouclier de Minecraft est un modèle d'entité dessiné autour
du **coin 0** du bloc (pas de son centre), face peinte vers +Z, poignée derrière (-Z) en x -1..1, y -3..3, z -5..1. On garde
ce repère et les réglages Display de item/shield.json (jar 26.1.2) : en main, en 1re personne et dans la case, il est tenu
exactement comme le vanilla. Diamètre 17,8 px (vanilla 12 × 22 : même surface à 10 % près).

Étape `bloque` (bouclier levé) : le mod n'a qu'un jeu de réglages Display, alors que Minecraft passe à item/shield_blocking
pendant le blocage. Le passage est recréé dans le modèle : le groupe `b_levee` de l'étape porte en dur la part commune aux
deux mains en 1re personne (monté de 2,4 px, avancé de 0,8), et `item_use` ajoute, par Molang (`q.is_first_person`,
`q.hand`), la rotation et le décalage exacts de chaque cas (3e personne : basculé de 45° et tourné de 65° vers l'avant ;
1re personne : roulis de 10° et décalé de 2,8 px vers le centre). Rotations : les angles d'Euler s'ajoutent (base + clé).
Animations coupées : bouclier monté, sans la bascule de la 3e personne.

Animations (objets vivants, guide 14) :
- item_use (boucle) : la pose de blocage ci-dessus (valeurs constantes) ; même pose dans item_idle (correctif F6).
- event_enter_bloque (0,32 s) : les sangles de la face se tendent d'un coup (anneaux tirés à plat, petit rebond amorti).
- event_enter_repos (0,5 s) : elles se relâchent (anneaux qui se soulèvent un peu).
- event_hit (0,6 s) : un reflet blanc fait le tour de la bordure chromée, éclat sur l'umbo ; le seul son (`block.chain.hit`).
- event_select (0,6 s) : le même reflet, sans son.
Fonctions avancées : objet vivant (item_use, event_enter_<étape>, event_hit, event_select), étapes repos / bloque, Molang
(q.is_first_person, q.hand), add_ (reflet et éclat, cachés au repos dans la bordure et l'umbo, sortis par `position`).
Pas de `_e` (latex et chrome : aucune source de lumière logique), pas de particules.
À juger en jeu : la pose de blocage (si le mod passait déjà aux réglages de blocage, le bouclier serait tourné deux fois),
event_hit et son son (pas encore vérifiés par le développeur), les deux mains.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "tools"))
import numpy as np
from PIL import Image
import objet  # noqa: E402

NOM = "skin_bouclier_cuir"
TEX = 512
D2R = math.pi / 180


def lerp(a, b, k):
    return a + (b - a) * k


def sm(x, a=0.0, b=1.0):
    u = min(max((x - a) / (b - a), 0.0), 1.0)
    return u * u * (3 - 2 * u)


def A(c):
    return np.array(c, np.float32)


# ------------------------------------------------------------------ palette (.claude/styles/cuir.md : latex noir, chrome)
CUIR = dict(hi=A((200, 204, 214)), base=A((12, 12, 16)), low=A((4, 4, 6)))
MAT = dict(hi=A((52, 50, 58)), base=A((24, 22, 27)), low=A((10, 9, 12)))          # cuir du dos, mat
ARGENT = dict(hi=A((240, 242, 248)), base=A((168, 172, 184)), low=A((70, 72, 84)))
BRIN = A((38, 38, 46))
LUMIERE = np.array((-0.55, 0.62, 0.56)) / np.linalg.norm((-0.55, 0.62, 0.56))      # haut gauche, devant

# ------------------------------------------------------------------ géométrie : constantes
RS = 7.9                     # rayon des rayons de l'armature (fin des pans)
ZB, H = 1.15, 1.30           # cône des pans : hauteur à RS, flèche jusqu'au sommet
ZA = ZB + H
AP = RS * math.cos(22.5 * D2R)
BETA = math.degrees(math.atan(H / AP))   # pente d'un pan au milieu
GAMMA = math.degrees(math.atan(H / RS))  # pente le long d'un rayon (arête)
R_IN, R_OUT = 2.9, 7.6       # pans : trou sous la collerette de l'umbo, bord sous la bordure
R_BORD_IN, R_BORD = 7.25, 8.9
Z_BORD = (1.30, 1.60)
SANGLES = (112.5, 292.5)     # milieux de pans portant une sangle (haut gauche, bas droit)


def fini(col, mask=None):
    h, w = col.shape[:2]
    mask = np.ones((h, w), bool) if mask is None else mask
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = mask * 255
    out[~mask, :3] = 0
    return out


def sur(fn, W, H, ss=3):
    """Peint en sur-échantillonnage (fn(xs, ys) -> col, masque ; xs, ys en px du modèle) puis réduit (LANCZOS + seuil)."""
    col, m = fn(W * ss, H * ss)
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110
    return fini(rgb.astype(np.float32), al)


def bande(x, a, b, flou):
    """1 dans [a, b], descend à 0 sur `flou` de chaque côté (reflet net : flou petit)."""
    return np.clip(np.minimum(x - a + flou, b - x + flou) / max(flou, 1e-6), 0, 1)


# ------------------------------------------------------------------ textures
HW_P = R_OUT * math.sin(22.5 * D2R) + 0.08
S0, S1 = R_IN / math.cos(BETA * D2R), R_OUT / math.cos(BETA * D2R)
TPX = 12   # texels par px pour les pans


def pan_tile(k):
    """Pan k (milieu à 22,5 + 45k degrés) : latex noir, ton selon l'orientation du pan, reflet en arc blanc net en haut à
    gauche (le même dessin sur tout le bouclier, calculé en coordonnées du bouclier), contre-jour gris en bas à droite."""
    phi = 22.5 + 45 * k
    al = (phi - 90) * D2R
    W, Hh = round(2 * HW_P * TPX), round((S1 - S0) * TPX)

    def fn(w, h):
        x = (np.arange(w) + 0.5)[None, :] / w * 2 * HW_P - HW_P
        y = S1 - (np.arange(h) + 0.5)[:, None] / h * (S1 - S0)
        yc = y * math.cos(BETA * D2R)
        px, py = x * math.cos(al) - yc * math.sin(al), x * math.sin(al) + yc * math.cos(al)
        r = np.hypot(px, py)
        ang = (np.degrees(np.arctan2(py, px)) + 360) % 360
        rel = np.degrees(np.arctan2(x, yc))
        m = (np.abs(rel) <= 22.6) & (r >= R_IN) & (r <= R_OUT)
        n = np.array((0, math.sin(BETA * D2R), math.cos(BETA * D2R)))
        n = np.array((n[0] * math.cos(al) - n[1] * math.sin(al), n[0] * math.sin(al) + n[1] * math.cos(al), n[2]))
        ton = float(np.dot(n, LUMIERE))
        col = np.ones((h, w, 1), np.float32) * lerp(CUIR["base"], A((30, 30, 38)), np.clip((ton - 0.5) * 3.2, 0, 1))
        col = col * np.ones((1, w, 1))
        # ombre le long des rayons (le pan plonge sous l'arête)
        bord = np.clip((np.abs(rel) - 17) / 5.5, 0, 1)[..., None]
        col = lerp(col, CUIR["low"], bord * 0.8)

        def arc(r0, r1, a0, a1, flou_r, coul, effil=True):
            fa = np.clip(np.minimum(ang - a0, a1 - ang) / ((a1 - a0) * 0.35), 0, 1) if effil else ((ang >= a0) & (ang <= a1)).astype(float)
            mid, demi = (r0 + r1) / 2, (r1 - r0) / 2
            demi_eff = demi * np.sqrt(fa)
            v = bande(r, mid - demi_eff, mid + demi_eff, flou_r) * (fa > 0)
            return v[..., None], coul

        for v, c in (arc(4.25, 5.45, 88, 178, 0.06, CUIR["hi"]), arc(6.15, 6.42, 108, 150, 0.05, lerp(CUIR["hi"], CUIR["base"], 0.25)),
                     arc(3.35, 3.55, 120, 150, 0.04, lerp(CUIR["hi"], CUIR["base"], 0.45)),
                     arc(4.9, 5.45, 280, 340, 0.08, A((96, 98, 112)))):
            col = lerp(col, c, v)
        return col, m

    return sur(fn, W, Hh)


def chrome_anneau(r_in, r_out, n, rivets=0, ang_rivets=0.0):
    """Anneau chromé vu de face (plaque découpée), profil de jonc : creux sombre aux bords, filet clair, éclat franc en haut à
    gauche qui s'éteint en bas à droite ; rivets bombés peints."""
    def fn(w, h):
        xs = ((np.arange(w) + 0.5) / w * 2 - 1)[None, :] * r_out
        ys = (1 - (np.arange(h) + 0.5) / h * 2)[:, None] * r_out
        r = np.hypot(xs, ys) * np.ones((h, w))
        ang = (np.degrees(np.arctan2(ys, xs)) + 360) % 360 * np.ones((h, w))
        t = (r - r_in) / (r_out - r_in)
        m = (t >= 0) & (t <= 1)
        lit = np.cos((ang - 135) * D2R)
        prof = np.clip(1 - np.abs(t - 0.45) / 0.55, 0, 1)
        col = lerp(ARGENT["low"], ARGENT["base"], prof[..., None])
        hi = bande(t, 0.22, 0.42, 0.04) * np.clip((lit + 0.15) / 0.6, 0, 1)
        col = lerp(col, ARGENT["hi"], hi[..., None])
        col = lerp(col, ARGENT["low"], (np.clip(-lit - 0.2, 0, 1) * 0.55 * (t > 0.5))[..., None])
        col = lerp(col, ARGENT["low"] * 0.7, (bande(t, -1, 0.05, 0.02) + bande(t, 0.95, 2, 0.02))[..., None].clip(0, 1))
        for j in range(rivets):
            a = (ang_rivets + j * 360 / rivets) * D2R
            cx, cy = (r_in + 0.62 * (r_out - r_in)) * math.cos(a), (r_in + 0.62 * (r_out - r_in)) * math.sin(a)
            d = np.hypot(xs - cx, ys - cy)
            rv = 0.26
            dans = d < rv
            col[dans] = ARGENT["base"]
            col[dans & (d > rv * 0.7)] = ARGENT["low"]
            col[(np.hypot(xs - cx + 0.08, ys - cy - 0.08) < rv * 0.35) & dans] = ARGENT["hi"]
        return col, m
    return sur(fn, n, n)


def disque_tile(rayon, n, kind):
    """Disque découpé : 'dos' (cuir mat du dos, surpiqûres noires à peine plus claires), 'chrome' (concentrique)."""
    def fn(w, h):
        xs = ((np.arange(w) + 0.5) / w * 2 - 1)[None, :] * rayon
        ys = (1 - (np.arange(h) + 0.5) / h * 2)[:, None] * rayon
        r = np.hypot(xs, ys) * np.ones((h, w))
        ang = (np.degrees(np.arctan2(ys, xs)) + 360) % 360 * np.ones((h, w))
        m = r <= rayon
        if kind == "dos":
            rng = np.random.default_rng(3)
            grain = rng.normal(0, 1, (h, w))
            col = MAT["base"] + grain[..., None] * 1.6
            col = lerp(col, MAT["low"], np.clip((r / rayon - 0.85) / 0.15, 0, 1)[..., None])
            for rc in (rayon - 0.75, 3.3):
                pts = bande(r, rc - 0.07, rc + 0.07, 0.03) * (np.sin(ang * D2R * rc / 0.16) > 0)
                col = lerp(col, MAT["hi"], pts[..., None])
        else:
            t = r / rayon
            col = lerp(ARGENT["base"], ARGENT["low"], np.clip((t - 0.7) / 0.3, 0, 1)[..., None])
            col = lerp(col, ARGENT["hi"], bande(t, 0.5, 0.68, 0.05)[..., None])
            col = lerp(col, ARGENT["low"], (bande(t, 0.0, 0.2, 0.08) * 0.4)[..., None])
        return col, m
    return sur(fn, n, n)


def metal_v(n=16, Hh=32):
    """Chrome le long de v (pièce allongée en v) : creux sombres aux bords, filet clair décalé."""
    u = ((np.arange(n) + 0.5) / n * 2 - 1)[None, :] * np.ones((Hh, 1))
    c = lerp(ARGENT["base"], ARGENT["low"], (np.clip(np.abs(u) - 0.45, 0, 1) / 0.55)[..., None])
    c[(u > -0.62) & (u < -0.22)] = ARGENT["hi"]
    c[(u > 0.15) & (u < 0.3)] = lerp(ARGENT["base"], ARGENT["hi"], 0.35)
    return fini(c)


def cap_tile(m, n=32):
    """Dessus d'un gradin d'umbo : concentrique (indépendant de la rotation du cube), anneau clair, bord sombre."""
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n / 2)
    c = lerp(m["base"], m["low"], np.clip((r - 0.8) / 0.4, 0, 1)[..., None])
    c = lerp(c, m["hi"], bande(r, 0.35, 0.6, 0.08)[..., None])
    return fini(c)


def sangle_tile(W=20, Hh=64, reflet=True):
    """Sangle de latex le long de v : noir, liseré sombre aux bords, **une** ligne de reflet blanche nette (style du set)."""
    u = ((np.arange(W) + 0.5) / W * 2 - 1)[None, :] * np.ones((Hh, 1))
    c = lerp(CUIR["base"], CUIR["low"], np.clip((np.abs(u) - 0.7) / 0.3, 0, 1)[..., None])
    if reflet:
        c[(u > -0.5) & (u < 0.04)] = CUIR["hi"]
        c[((u > -0.64) & (u <= -0.5)) | ((u >= 0.04) & (u < 0.16))] = lerp(CUIR["hi"], CUIR["base"], 0.5)
    c[np.abs(u) > 0.86] = lerp(CUIR["base"], A((44, 44, 52)), 0.5)
    return fini(c)


def oring_tile(n=48, r_in=0.5):
    ss = 4
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    dx, dy = (xx + 0.5) / N * 2 - 1, -((yy + 0.5) / N * 2 - 1)
    r = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx)
    m = (r < 0.98) & (r > r_in)
    mid = (r - r_in) / (0.98 - r_in)
    col = lerp(ARGENT["low"], ARGENT["base"], np.clip(1 - np.abs(mid - 0.5) * 2, 0, 1)[..., None] * 1.2)
    lit = np.cos(ang - 135 * D2R)
    col = np.where((lit > 0.5)[..., None] & (np.abs(mid - 0.42) < 0.22)[..., None], ARGENT["hi"], col)
    col = np.where((lit < -0.6)[..., None], lerp(col, ARGENT["low"], 0.6), col)
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.LANCZOS))
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((n, n), Image.LANCZOS)) > 110
    return fini(rgb.astype(np.float32), al)


def boucle_tile(W=48, Hh=32):
    """Boucle rectangulaire à rouleau vue de face : cadre chromé arrondi aux coins, barrette centrale (ardillon) ; le vide
    du cadre est découpé (on y voit la sangle)."""
    ss = 4
    w, h = W * ss, Hh * ss
    yy, xx = np.mgrid[0:h, 0:w]
    u, v = (xx + 0.5) / w * 2 - 1, (yy + 0.5) / h * 2 - 1
    ex, ey = 0.80, 0.62
    dehors = (np.maximum(np.abs(u) - ex, 0) ** 2 + np.maximum(np.abs(v) - ey, 0) ** 2) > 0.18 ** 2
    dedans = (np.abs(u) < ex - 0.04) & (np.abs(v) < ey - 0.04)
    barre = (np.abs(u) < 0.09) & (v > -0.6) & (v < 0.75)
    m = (~dehors & ~dedans) | barre
    col = lerp(ARGENT["base"], ARGENT["low"], np.clip(v * 0.5 + 0.5, 0, 1)[..., None] * 0.8)
    col[(v < -0.62) & ~dehors] = ARGENT["hi"]
    col[barre & (u < 0)] = ARGENT["hi"]
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, Hh), Image.LANCZOS))
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((W, Hh), Image.LANCZOS)) > 110
    return fini(rgb.astype(np.float32), al)


def tresse_v(W=24, Hh=96, period=9.0, reflet=False):
    """Poignée tressée (cuir noir), brins en chevrons le long de v."""
    v = (np.arange(Hh) + 0.5)[:, None]
    u = ((np.arange(W) + 0.5) / W * 2 - 1)[None, :]
    c_ = v / period + np.abs(u) * 1.6
    f = c_ - np.floor(c_)
    brin = np.sin(np.pi * f) ** 0.6
    col = lerp(CUIR["low"], BRIN, brin[..., None]) * np.ones((Hh, W, 1), np.float32)
    creux = (f < 0.12) | (f > 0.9)
    if reflet:
        coeur = np.broadcast_to((u > -0.42) & (u < 0.2), (Hh, W))
        col[coeur] = CUIR["hi"]
        col[coeur & creux] = lerp(CUIR["hi"], CUIR["low"], 0.6)
    else:
        col[creux] = CUIR["low"]
    return fini(col)


def reflet_arc_tile(n=128):
    """Reflet de la bordure (add_ : noir = invisible) : arc de 70° centré à 135°, cœur blanc, extrémités effilées."""
    def fn(w, h):
        xs = ((np.arange(w) + 0.5) / w * 2 - 1)[None, :] * R_BORD
        ys = (1 - (np.arange(h) + 0.5) / h * 2)[:, None] * R_BORD
        r = np.hypot(xs, ys)
        ang = (np.degrees(np.arctan2(ys, xs)) + 360) % 360
        da = np.abs(ang - 135)
        fa = np.clip(1 - da / 36, 0, 1)
        t = (r - R_BORD_IN) / (R_BORD - R_BORD_IN)
        I = bande(t, 0.18, 0.5, 0.12) * fa ** 0.7
        col = np.stack([I * 245, I * 248, I * 255], -1)
        return col, I > 0.02
    return sur(fn, n, n)


def eclat_tile(n=32):
    yy, xx = np.mgrid[0:n, 0:n]
    dx, dy = (xx + 0.5) / n * 2 - 1, (yy + 0.5) / n * 2 - 1
    r = np.hypot(dx, dy) + 1e-6
    ang = np.arctan2(dy, dx)
    long_ = np.exp(-(np.abs(np.sin(2 * ang)) * r * 9) ** 2) * np.clip(1 - r, 0, 1) ** 1.2
    I = np.clip(long_ + 0.9 * np.exp(-(r / 0.16) ** 2), 0, 1)
    return fini(np.stack([I * 235, I * 240, I * 255], -1))


GRADINS = ((2.65, 2.2, 2.8), (2.2, 2.8, 3.35), (1.65, 3.35, 3.8), (0.95, 3.8, 4.05))


def dome_tile(j, n):
    """Dessus du gradin j de l'umbo, vu de face : chrome, croissant d'éclat en haut à gauche, bord sombre en bas à droite ;
    pris dans la même courbe d'un gradin à l'autre (le croissant se resserre vers le sommet : dôme)."""
    a = GRADINS[j][0]

    def fn(w, h):
        xs = ((np.arange(w) + 0.5) / w * 2 - 1)[None, :] * a
        ys = (1 - (np.arange(h) + 0.5) / h * 2)[:, None] * a
        r = np.hypot(xs, ys) * np.ones((h, w))
        ang = (np.degrees(np.arctan2(ys, xs)) + 360) % 360 * np.ones((h, w))
        t = r / a
        lit = np.cos((ang - 135) * D2R)
        col = lerp(ARGENT["base"], ARGENT["low"], np.clip((t - 0.55) / 0.45, 0, 1)[..., None] * np.clip(0.6 - lit * 0.6, 0, 1)[..., None])
        hi = bande(t, 0.5, 0.82, 0.05) * np.clip((lit - 0.35) / 0.3, 0, 1)
        col = lerp(col, ARGENT["hi"], hi[..., None])
        col = lerp(col, ARGENT["low"] * 0.8, bande(t, 0.9, 1.1, 0.04)[..., None])
        if j == 3:
            col = lerp(col, ARGENT["hi"], np.exp(-((xs + 0.25) ** 2 + (ys - 0.25) ** 2) / 0.04)[..., None])
        return col, t <= 1
    return sur(fn, n, n)


TILES = {f"pan{k}": pan_tile(k) for k in range(8)}
TILES.update({f"dome{j}": dome_tile(j, (48, 40, 32, 24)[j]) for j in range(4)})
TILES.update({
    "bordure": chrome_anneau(R_BORD_IN, R_BORD, 256, rivets=16, ang_rivets=11.25),
    "bordure_dos": chrome_anneau(7.2, R_BORD, 128),
    "dos": disque_tile(8.45, 160, "dos"), "collerette": chrome_anneau(2.75, 3.45, 80, rivets=0),
    "umbo_dos": disque_tile(2.8, 64, "chrome"),
    "metal": metal_v(), "metal_h": np.ascontiguousarray(np.transpose(metal_v(), (1, 0, 2))), "cap": cap_tile(ARGENT), "sangle": sangle_tile(), "sangle_cote": sangle_tile(8, 32, reflet=False),
    "sangle_h": np.ascontiguousarray(np.transpose(sangle_tile(), (1, 0, 2))),
    "sangle_cote_h": np.ascontiguousarray(np.transpose(sangle_tile(8, 32, reflet=False), (1, 0, 2))),
    "oring": oring_tile(), "boucle": boucle_tile(), "tresse": tresse_v(), "tresse_reflet": tresse_v(reflet=True),
    "reflet": reflet_arc_tile(), "eclat": eclat_tile(),
})


def pack():
    """Rangement en étagères ; chaque pièce va dans la première étagère où elle tient (en hauteur et en largeur restante)."""
    items = sorted(((n, t.shape[1], t.shape[0]) for n, t in TILES.items()), key=lambda it: -it[2])
    uv, etageres = {}, []          # [y, hauteur, x libre]
    for n, w, h in items:
        for e in etageres:
            if h <= e[1] and e[2] + w <= TEX:
                uv[n] = (e[2], e[0], e[2] + w, e[0] + h)
                e[2] += w + 1
                break
        else:
            y = etageres[-1][0] + etageres[-1][1] + 1 if etageres else 0
            assert y + h <= TEX - 6, f"atlas plein : {n}"
            etageres.append([y, h, w + 1])
            uv[n] = (0, y, w, y + h)
    return uv


UV = pack()
tex = np.zeros((TEX, TEX, 4), np.uint8)
for n, im in TILES.items():
    u0, v0, u1, v1 = UV[n]
    tex[v0:v1, u0:u1] = im
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[tex[..., 3] == 0] = 0
assert set(np.unique(tex[..., 3])) <= {0, 255}
im = Image.fromarray(tex, "RGBA")
im.save(f"{NOM}.png", optimize=True)
_b = io.BytesIO()
im.save(_b, "PNG", optimize=True)
tex_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()


def full(t):
    return list(UV[t])


def miroir_u(uv):
    return [uv[2], uv[1], uv[0], uv[3]]


# ------------------------------------------------------------------ arbre (groupes, cubes)
def nuid():
    return str(_uuid.uuid4())


elements = []
GROUPES = {}


class G:
    def __init__(self, nom, origin, rot=(0, 0, 0), parent=None):
        assert nom not in GROUPES, nom
        self.nom, self.origin, self.rot, self.uuid, self.enfants = nom, [round(float(v), 4) for v in origin], [round(float(v), 4) for v in rot], nuid(), []
        GROUPES[nom] = self
        if parent is not None:
            parent.enfants.append(self)

    def noeud(self):
        return {"name": self.nom, "origin": self.origin, "rotation": self.rot, "uuid": self.uuid,
                "children": [c.noeud() if isinstance(c, G) else c for c in self.enfants]}


def cube(g, nom, frm, to, origin, faces, rot=(0, 0, 0)):
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm],
         "to": [round(float(v), 3) for v in to], "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in faces.get(f, CLEAR)], "texture": 0}
                   for f in ("north", "south", "east", "west", "up", "down")}}
    if any(abs(r) > 1e-4 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    g.enfants.append(e["uuid"])
    return e


def plaque_z(g, nom, c, demi, z0, z1, avant=None, arriere=None, rot=(0, 0, 0), origin=None):
    """Plaque fine dans le plan XY (découpée par alpha), tranches transparentes."""
    c = np.asarray(c, float)
    f = {}
    if avant:
        f["south"] = full(avant)
    if arriere:
        f["north"] = miroir_u(full(arriere))
    cube(g, nom, (c[0] - demi[0], c[1] - demi[1], z0), (c[0] + demi[0], c[1] + demi[1], z1),
         origin if origin is not None else (c[0], c[1], (z0 + z1) / 2), f, rot)


def octo_z(g, nom, a, z0, z1, cap, cote, off=22.5, cx=0.0, cy=0.0):
    """Gradin à 12 pans (axe Z) : trois carrés tournés de 30°, dessus à la même hauteur : le dessin du dessus est concentrique
    et centré sur l'axe, donc identique d'un carré à l'autre là où ils se recouvrent (pas d'étoile de coins décalés)."""
    for j, (aa, zt, rz) in enumerate(((a, z1, off), (a, z1, off + 30), (a, z1, off + 60))):
        f = {"south": full(cap), "east": full(cote), "west": full(cote), "up": full(cote), "down": full(cote)}
        cube(g, f"{nom}{'abc'[j]}", (cx - aa, cy - aa, z0), (cx + aa, cy + aa, zt), (cx, cy, z0), f, (0, 0, rz))


def octo_y(g, nom, cx, cz, r, y0, y1, tile, up_tile=None):
    """Barre octogonale le long de Y (poignée)."""
    for j, ry in enumerate((0, 45)):
        r2 = r * (0.97 if j else 1)
        f = {k: full(tile) for k in ("north", "south", "east", "west")}
        if up_tile:
            f["south"] = full(up_tile)
        f["up"] = f["down"] = full("metal")
        cube(g, f"{nom}{'o' if j else ''}", (cx - r2, y0 + 0.05 * j, cz - r2), (cx + r2, y1 - 0.05 * j, cz + r2), (cx, (y0 + y1) / 2, cz), f, (0, ry, 0))


# ------------------------------------------------------------------ construction d'un bouclier (une copie par étape)
def bouclier(P, racine, tension, g=(0.0, 0.0, 0.0)):
    """P : préfixe des noms ; tension 0 (sangles lâches, repos) ou 1 (tendues, bloque) ; g : décalage de toute la copie."""
    g = np.asarray(g, float)

    def V(*p):
        return np.asarray(p, float) + g

    corps = G(P + "corps", V(0, 0, 0), parent=racine)
    # pans de latex tendus (cône à 8 pans)
    pans = G(P + "pans", V(0, 0, ZA), parent=corps)
    for k in range(8):
        phi = 22.5 + 45 * k
        cube(pans, f"{P}pan{k}", V(-HW_P, S0, ZA - 0.3), V(HW_P, S1, ZA), V(0, 0, ZA), {"south": full(f"pan{k}")}, (-BETA, 0, phi - 90))
    # armature : 8 rayons chromés sur les arêtes
    s0r, s1r = 3.25 / math.cos(GAMMA * D2R), 7.55 / math.cos(GAMMA * D2R)
    for k in range(8):
        f = {"south": full("metal"), "east": full("metal"), "west": full("metal"), "up": full("cap"), "down": full("cap")}
        cube(pans, f"{P}rayon{k}", V(-0.2, s0r, ZA), V(0.2, s1r, ZA + 0.3), V(0, 0, ZA), f, (-GAMMA, 0, 45 * k - 90))
    # bordure chromée : plaque avant (anneau découpé, rivets peints), paroi en 32 segments, anneau du dos
    bord = G(P + "bordure", V(0, 0, 0), parent=corps)
    plaque_z(bord, P + "bord_avant", V(0, 0, 0)[:2], (R_BORD, R_BORD), Z_BORD[0] + g[2], Z_BORD[1] + g[2], avant="bordure", arriere="bordure_dos")
    plaque_z(bord, P + "bord_dos", V(0, 0, 0)[:2], (R_BORD, R_BORD), 0.20 + g[2], 0.35 + g[2], arriere="bordure_dos")
    L = 2 * R_BORD * math.tan(math.pi / 32)
    for j in range(32):
        a = j * 360 / 32
        f = {"up": full("metal_h")}
        cube(bord, f"{P}paroi{j:02d}", V(-L / 2, R_BORD - 0.55, 0.22), V(L / 2, R_BORD, Z_BORD[1] - 0.02), V(0, 0, 0), f, (0, 0, a - 90))
    # dos : peau de cuir mat, fond de l'umbo chromé
    plaque_z(corps, P + "dos", V(0, 0, 0)[:2], (8.45, 8.45), 0.55 + g[2], 0.85 + g[2], arriere="dos")
    plaque_z(corps, P + "umbo_dos", V(0, 0, 0)[:2], (2.8, 2.8), 0.40 + g[2], 0.55 + g[2], arriere="umbo_dos")
    # umbo : collerette rivetée + 4 gradins octogonaux
    umbo = G(P + "umbo", V(0, 0, 2.0), parent=corps)
    plaque_z(umbo, P + "collerette", V(0, 0, 0)[:2], (3.45, 3.45), 2.0 + g[2], 2.3 + g[2], avant="collerette", arriere="collerette")
    for k in range(8):
        a = (22.5 + 45 * k) * D2R
        c = V(3.12 * math.cos(a), 3.12 * math.sin(a), 0)
        f = {"south": full("cap"), "east": full("metal"), "west": full("metal"), "up": full("metal"), "down": full("metal")}
        cube(umbo, f"{P}rivet{k}", c + (-0.25, -0.25, 2.3), c + (0.25, 0.25, 2.52), c + (0, 0, 2.3), f, (0, 0, 22.5 + 45 * k))
    for j, (a, z0, z1) in enumerate(GRADINS):
        # gradin rond : paroi de 16 segments (face extérieure seule) + dessus en disque découpé
        L = 2 * a * math.tan(math.pi / 16)
        for k in range(16):
            cube(umbo, f"{P}gradin{j}_{k:02d}", V(-L / 2, a - 0.32, z0), V(L / 2, a, z1 - 0.03), V(0, 0, z0), {"up": full("metal_h")}, (0, 0, k * 22.5 + 11.25 - 90))
        plaque_z(umbo, f"{P}gradin{j}", V(0, 0, 0)[:2], (a, a), z1 - 0.15 + g[2], z1 + g[2], avant=f"dome{j}")
    # éclat de l'umbo (add_, caché dans le dernier gradin au repos)
    ecl = G("add_" + P + "eclat", V(0, 0, 3.83), parent=umbo)
    plaque_z(ecl, P + "eclat", V(0, 0, 0)[:2], (0.5, 0.5), 3.80 + g[2], 3.85 + g[2], avant="eclat")
    # le même éclat pour event_select : un groupe par événement (select et hit peuvent jouer ensemble ; leurs échelles se
    # multiplieraient : ×2,4 × 2,4 = ×5,8 sur un seul groupe)
    ecl_s = G("add_" + P + "eclat_sel", V(0, 0, 3.82), parent=umbo)
    plaque_z(ecl_s, P + "eclat_sel", V(0, 0, 0)[:2], (0.49, 0.49), 3.79 + g[2], 3.84 + g[2], avant="eclat")
    # reflet de la bordure (add_, caché dans la plaque avant au repos)
    refl = G("add_" + P + "reflet", V(0, 0, 1.45), parent=bord)
    plaque_z(refl, P + "reflet", V(0, 0, 0)[:2], (R_BORD, R_BORD), 1.42 + g[2], 1.47 + g[2], avant="reflet")

    # sangles de la face (dans le repère du pan : x en travers, y le long de la pente, z au-dessus de la surface)
    lache = 1 - tension
    meta = {}
    for i, phi in enumerate(SANGLES):
        cb = math.cos(BETA * D2R)
        sA, sR, sO = 3.3 / cb, (5.35, 5.6)[i] / cb, 7.45 / cb
        hw = (0.7, 0.66)[i]          # deux sangles un peu différentes (anneau plus bas sur celle du bas)
        lift, dy, tilt = 0.24 * lache, -0.3 * lache, -9.0 * lache
        Li, Lo = (sR + dy - 0.75) - sA, sO - (sR + dy + 0.75)
        thi, tho = math.degrees(math.atan(lift / Li)), math.degrees(math.atan(lift / Lo))
        sg = G(f"{P}sangle{i}", V(0, 0, ZA), (-BETA, 0, phi - 90), parent=corps)
        fs = {"south": full("sangle"), "east": full("sangle_cote"), "west": full("sangle_cote"), "up": full("sangle_cote"), "down": full("sangle_cote")}
        gi = G(f"{P}sangle{i}_in", V(0, sA, ZA), (thi, 0, 0), parent=sg)
        cube(gi, f"{P}s{i}_in", V(-hw, sA, ZA + 0.02), V(hw, sR + dy - 0.55, ZA + 0.27), V(0, sA, ZA), fs)
        gr = G(f"{P}sangle{i}_anneau", V(0, sR + dy, ZA + lift), (tilt, 0, 0), parent=sg)
        plaque_z(gr, f"{P}s{i}_anneau", V(0, sR + dy, 0)[:2], (0.85, 0.85), ZA + lift + 0.30 + g[2], ZA + lift + 0.45 + g[2], avant="oring", arriere="oring")
        go = G(f"{P}sangle{i}_out", V(0, sO, ZA), (-tho, 0, 0), parent=sg)
        cube(go, f"{P}s{i}_out", V(-hw, sR + dy + 0.55, ZA + 0.02), V(hw, sO + 0.12, ZA + 0.27), V(0, sO, ZA), fs)
        cb_ = V(0, sR + dy + 0.55 + 0.62 * (sO - sR - dy - 0.55), 0)
        plaque_z(go, f"{P}s{i}_boucle", cb_[:2], (0.98, 0.62), ZA + 0.30 + g[2], ZA + 0.45 + g[2], avant="boucle", arriere="boucle")
        # sur la bordure puis le long de la paroi (repère tourné seulement autour de Z)
        gb = G(f"{P}sangle{i}_bord", V(0, 0, 0), (0, 0, phi - 90), parent=corps)
        cube(gb, f"{P}s{i}_bord", V(-hw, 7.15, Z_BORD[1]), V(hw, R_BORD + 0.02, Z_BORD[1] + 0.22), V(0, 0, 0), fs)
        fp = dict(fs, up=full("sangle"), south=full("sangle_cote"))
        cube(gb, f"{P}s{i}_paroi", V(-hw, R_BORD + 0.02, 0.25), V(hw, R_BORD + 0.24, Z_BORD[1] + 0.22), V(0, 0, 0), fp)
        meta[i] = dict(thi=thi, tho=tho, dy=dy, lift=lift, tilt=tilt)

    # dos : poignée tressée sur deux pattes chromées, sangles en H, anneaux en O, boucles
    dos = G(P + "enarmes", V(0, 0, 0), parent=corps)
    fm = {k: full("metal") for k in ("north", "south", "east", "west", "up", "down")}
    fm["north"] = full("cap")
    for j, (y0, y1) in enumerate(((2.3, 3.2), (-3.2, -2.3))):
        cube(dos, f"{P}patte{j}", V(-0.55, y0, -4.4), V(0.55, y1, 0.42), V(0, (y0 + y1) / 2, 0), fm)
    octo_y(dos, P + "poignee", g[0], -3.7 + g[2], 0.62, -2.35 + g[1], 2.35 + g[1], "tresse", None)
    fsd = {"north": full("sangle"), "east": full("sangle_cote"), "west": full("sangle_cote"), "up": full("sangle_cote"), "down": full("sangle_cote")}
    th_dos = math.degrees(math.atan(0.35 / 4.9)) * lache
    fsh = {"north": full("sangle_h"), "up": full("sangle_cote_h"), "down": full("sangle_cote_h"), "east": full("sangle_cote"), "west": full("sangle_cote")}
    for j, ys in enumerate((4.9, -4.9)):
        # sangle en deux moitiés, pivot à l'anneau : lâche, le milieu bâille vers le bras (-Z) ; tendue, à plat
        for sgn, c in ((-1, "g"), (1, "d")):
            gh = G(f"{P}dos_sangle{j}{c}", V(sgn * 4.9, ys, 0.4), (0, -sgn * th_dos, 0), parent=dos)
            x0, x1 = sorted((sgn * 4.9, 0.0))
            cube(gh, f"{P}dos_sangle{j}{c}", V(x0, ys - 0.7, 0.30), V(x1, ys + 0.7, 0.50), V(sgn * 4.9, ys, 0.4), fsh)
            bx = 2.4 if j == 0 else -2.4
            if sgn * bx > 0:
                plaque_z(gh, f"{P}dos_boucle{j}", V(bx, ys, 0)[:2], (0.98, 0.62), 0.12 + g[2], 0.27 + g[2], arriere="boucle", rot=(0, 0, 90), origin=V(bx, ys, 0.2))
        for sx in (-5.62, 5.62):
            plaque_z(dos, f"{P}dos_anneau{j}{'d' if sx > 0 else 'g'}", V(sx, ys, 0)[:2], (0.72, 0.72), 0.05 + g[2], 0.17 + g[2], arriere="oring")
        yv0, yv1 = (3.2, 4.2) if ys > 0 else (-4.2, -3.2)
        gl = G(f"{P}dos_lien{j}", V(0, 0, 0.4), parent=dos)
        cube(gl, f"{P}dos_lien{j}", V(-0.6, yv0, 0.30 - 0.33 * lache), V(0.6, yv1, 0.50 - 0.33 * lache), V(0, 0, 0.4), fsd)
    meta["dos"] = dict(th=th_dos, lien=-0.33 * lache)
    return meta


# ------------------------------------------------------------------ pose de blocage (item/shield_blocking du jar 26.1.2)
def _d(r, t, s):
    return objet._d(r, t, s)


def _gauche(d):
    r, t = d["rotation"], d["translation"]
    return _d((r[0], -r[1], -r[2]), (-t[0], t[1], t[2]), d["scale"])


VAN = {"3R": (_d((0, 90, 0), (10, 6, -4), 1), _d((45, 155, 0), (-3.49, 11, -2), 1)),
       "3L": (_gauche(_d((0, 90, 0), (10, 6, 12), 1)), _gauche(_d((45, 155, 0), (11.51, 7, 2.5), 1))),
       "1R": (_d((0, 180, 5), (-10, 1.75, -10), 1.25), _d((0, 180, -5), (-15, 3.25, -11), 1.25)),
       "1L": (_gauche(_d((0, 180, 5), (10, 0, -10), 1.25)), _gauche(_d((0, 180, -5), (5, 5, -11), 1.25)))}


def euler(R):
    """Angles (x, y, z) tels que R = Rz·Ry·Rx (ordre de Blockbench et du renderer)."""
    b = -math.asin(max(-1, min(1, R[2, 0])))
    return np.degrees([math.atan2(R[2, 1], R[2, 2]), b, math.atan2(R[1, 0], R[0, 0])])


def rotm(e):
    rx, ry, rz = np.radians(e)
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


DELTA = {}
for k, (n, b) in VAN.items():
    M = np.linalg.inv(objet.matrice_display(n)) @ objet.matrice_display(b)
    DELTA[k] = (euler(M[:3, :3]), M[:3, 3])
# part commune aux deux mains en 1re personne, en dur dans la géométrie (monté, avancé) ; pivot du groupe b_levee : origine
G_BLOQUE = np.array((0.0, (DELTA["1R"][1][1] + DELTA["1L"][1][1]) / 2, DELTA["1R"][1][2]))
CLES = {}
for k, (e, t) in DELTA.items():
    q = t - rotm(e) @ G_BLOQUE            # x -> R(x + g) + q = R x + t
    CLES[k] = (e, q)

# ------------------------------------------------------------------ modèle
repos = G(objet.etape("repos", "bouclier"), (0, 0, 0))
bloque = G(objet.etape("bloque", "bouclier"), (0, 0, 0))
levee = G("b_levee", (0, 0, 0), parent=bloque)
META_R = bouclier("r_", repos, 0.0)
META_B = bouclier("b_", levee, 1.0, G_BLOQUE)


def kf(t, v, ch="rotation", interp="linear"):
    return {"channel": ch, "data_points": [{"x": v[0] if isinstance(v[0], str) else str(round(float(v[0]) + 0.0, 4)),
                                            "y": v[1] if isinstance(v[1], str) else str(round(float(v[1]) + 0.0, 4)),
                                            "z": v[2] if isinstance(v[2], str) else str(round(float(v[2]) + 0.0, 4))}],
            "time": round(float(t), 4), "interpolation": interp}


def anim(name, L, loop="once"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": round(L, 4), "snapping": 60,
            "selected": name == "item_use", "animators": {}}


def piste(an, nom, keys):
    g = GROUPES[nom]
    an["animators"].setdefault(g.uuid, {"name": nom, "type": "bone", "keyframes": []})["keyframes"] += keys


def molang(i, ch):
    """Valeur de l'axe i du canal ch selon le cas (1re/3e personne, main) ; 0 si nulle partout."""
    vals = {k: (CLES[k][0] if ch == "rotation" else CLES[k][1])[i] for k in CLES}
    vals = {k: (0.0 if abs(v) < 1e-3 else round(float(v), 3)) for k, v in vals.items()}
    if all(v == 0 for v in vals.values()):
        return "0"
    return f"q.is_first_person ? (q.hand ? {vals['1L']} : {vals['1R']}) : (q.hand ? {vals['3L']} : {vals['3R']})"


ANIMS = []
use = anim("item_use", 1.0, "loop")
piste(use, "b_levee", [kf(0, [molang(i, "rotation") for i in range(3)]), kf(0, [molang(i, "position") for i in range(3)], "position")])
ANIMS.append(use)
# Correctif F6 : la même pose de blocage dans item_idle (b_levee n'est dessiné qu'à l'étape bloque) ; si le mod voit « plus
# utilisé » une image, item_idle reprend sans fondu ni retombée (objets.md, « Retour en jeu 2026-11-08 soir », recette 2).
idle = anim("item_idle", 1.0, "loop")
piste(idle, "b_levee", [kf(0, [molang(i, "rotation") for i in range(3)]), kf(0, [molang(i, "position") for i in range(3)], "position")])
ANIMS.append(idle)


def tension_keys(an, P, meta_de, meta_vers, courbe, L, fps=40):
    """Écarts (pose de départ - pose de la copie) qui vont vers 0 selon courbe(t) (1 -> 0)."""
    n = int(L * fps)
    n_ = int(L * fps)
    a, b = meta_de["dos"], meta_vers["dos"]
    for j in range(2):
        for sgn, c_ in ((-1, "g"), (1, "d")):
            piste(an, f"{P}dos_sangle{j}{c_}", [kf(i / n_ * L, (0, -sgn * (courbe(i / n_ * L) if i < n_ else 0.0) * (a["th"] - b["th"]), 0)) for i in range(n_ + 1)])
        piste(an, f"{P}dos_lien{j}", [kf(i / n_ * L, (0, 0, (courbe(i / n_ * L) if i < n_ else 0.0) * (a["lien"] - b["lien"])), "position") for i in range(n_ + 1)])
    for i in (0, 1):
        a, b = meta_de[i], meta_vers[i]
        ki, ko, kr, kp = [], [], [], []
        for j in range(n + 1):
            t = j / n * L
            c = courbe(t) if j < n else 0.0
            ki.append(kf(t, (c * (a["thi"] - b["thi"]), 0, 0)))
            ko.append(kf(t, (-c * (a["tho"] - b["tho"]), 0, 0)))
            kr.append(kf(t, (c * (a["tilt"] - b["tilt"]), 0, 0)))
            kp.append(kf(t, (0, c * (a["dy"] - b["dy"]), c * (a["lift"] - b["lift"])), "position"))
        piste(an, f"{P}sangle{i}_in", ki)
        piste(an, f"{P}sangle{i}_out", ko)
        piste(an, f"{P}sangle{i}_anneau", kr + kp)


# se tendre : coup sec puis petit rebond amorti ; se relâcher : lent
LB, LR = 0.32, 0.5
ent_b = anim("event_enter_bloque", LB)
tension_keys(ent_b, "b_", META_R, META_B, lambda t: math.exp(-t / 0.045) * math.cos(2 * math.pi * t / 0.16) * (1 - sm(t, LB - 0.08, LB)), LB)
ANIMS.append(ent_b)
ent_r = anim("event_enter_repos", LR)
tension_keys(ent_r, "r_", META_B, META_R, lambda t: 1 - sm(t, 0.0, LR * 0.9), LR)
ANIMS.append(ent_r)


def reflet(an, eclat="eclat"):
    """Reflet qui fait le tour de la bordure (sorti de la plaque, tourne de 135° à -85°, rentre), éclat sur l'umbo
    (un groupe d'éclat par événement : jamais deux échelles sur le même groupe)."""
    for P in ("r_", "b_"):
        rr, ee = "add_" + P + "reflet", "add_" + P + eclat
        rot = [kf(t, (0, 0, -220 * sm(t, 0.03, 0.5))) for t in np.linspace(0, 0.5, 11)] + [kf(0.6, (0, 0, 0))]
        pos = [kf(0, (0, 0, 0), "position"), kf(0.03, (0, 0, 0.3), "position"), kf(0.5, (0, 0, 0.3), "position"),
               kf(0.54, (0, 0, 0), "position"), kf(0.6, (0, 0, 0), "position")]
        piste(an, rr, rot + pos)
        piste(an, ee, [kf(0, (0, 0, 0), "position"), kf(0.16, (0, 0, 0), "position"), kf(0.19, (0, 0, 0.4), "position"),
                       kf(0.36, (0, 0, 0.4), "position"), kf(0.39, (0, 0, 0), "position"), kf(0.6, (0, 0, 0), "position"),
                       kf(0, (1, 1, 1), "scale"), kf(0.19, (1, 1, 1), "scale"), kf(0.25, (2.4, 2.4, 1), "scale"),
                       kf(0.36, (1, 1, 1), "scale"), kf(0.6, (1, 1, 1), "scale")])


hit = anim("event_hit", 0.6)
reflet(hit)
ANIMS.append(hit)
sel = anim("event_select", 0.6)
reflet(sel, "eclat_sel")
ANIMS.append(sel)

outliner = [repos.noeud(), bloque.noeud()]
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
VANILLA = {   # item/shield.json du jar 26.1.2 (head : défaut du mod)
    "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [10, 6, -4], "scale": [1, 1, 1]},
    "thirdperson_lefthand": {"rotation": [0, 90, 0], "translation": [10, 6, 12], "scale": [1, 1, 1]},
    "firstperson_righthand": {"rotation": [0, 180, 5], "translation": [-10, 1.75, -10], "scale": [1.25, 1.25, 1.25]},
    "firstperson_lefthand": {"rotation": [0, 180, 5], "translation": [10, 0, -10], "scale": [1.25, 1.25, 1.25]},
    "gui": {"rotation": [15, -25, -5], "translation": [2, 3, 0], "scale": [0.65, 0.65, 0.65]},
    "fixed": {"rotation": [0, 180, 0], "translation": [-4.5, 4.5, -5], "scale": [0.55, 0.55, 0.55]},
    "on_shelf": {"rotation": [0, 0, 0], "translation": [11, 18.5, 8.7], "scale": [1.4, 1.4, 1.4]},
    "ground": {"rotation": [0, 0, 0], "translation": [2, 4, 2], "scale": [0.25, 0.25, 0.25]},
}
AFFICHAGE = objet.affichage("bouclier", **VANILLA)
model = objet.modele(NOM, "bouclier", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)

from sons import limiter_sons, cle_son  # noqa: E402
limiter_sons(model)                       # ne garde rien (aucun son posé avant) ; le seul son est ajouté ci-dessous
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.03, "block.chain.hit")]}

os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))
json.dump({k: {"euler": list(map(float, e)), "q": list(map(float, q))} for k, (e, q) in CLES.items()} | {"g": list(map(float, G_BLOQUE))},
          open(".build/blocage.json", "w"), indent=1)


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(GROUPES), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print("blocage : g =", np.round(G_BLOQUE, 3), {k: (np.round(e, 2).tolist(), np.round(q, 2).tolist()) for k, (e, q) in CLES.items()})
