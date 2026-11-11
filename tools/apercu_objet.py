#!/usr/bin/env python3
"""Aperçus d'un skin d'objet (guide 14) : une rangée par étape (repos, bande_1…), cinq vues chacune.
Usage : python tools/apercu_objet.py modele.bbmodel dossier_sortie        (appelé par tools/livrer.py pour cosmetiques/objets/)

Vues (calculs dans tools/objet.py, d'après le code de Minecraft ; à confirmer en jeu) :
  Inventaire  : réglage `gui`, vu de face (+Z), cadre = la case 16 × 16 ; en encart, la case à sa taille réelle (32 px, interface ×2)
  Objet 3/4, Profil : l'objet seul dans son bloc
  Main 3e pers. : `thirdperson_righthand`, bras droit levé de 18° comme un joueur qui tient un objet
  1re pers.   : `firstperson_righthand`, caméra du joueur (champ de vision 70°), sans balancement ; arbalète : geste de
                chargement (bande_*) et visée (chargee*) de Minecraft ; trait blanc = carré de 16 px d'un objet vanilla plat
Écrit planche.png, vignette.png (la case d'inventaire, pour le Vestiaire), nuit.png (3/4 de nuit) et etats.json (étapes).
Une étape absente du modèle est montrée par son repli (guide 14) : « bande_2 → bande_1 »."""
import copy, json, math, os, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
os.environ.setdefault("MODCONV", "1")
import render_bbmodel as rb  # noqa: E402
import objet  # noqa: E402

TUILE = 380
FOND = (18, 14, 20)


def repli(etape, presentes, type_):
    """Étape dessinée pour `etape` : elle-même si modelée, sinon les étapes d'avant (guide 14), sinon tout le modèle."""
    liste = list(objet.ETAPES[type_])
    for e in reversed(liste[:liste.index(etape) + 1]):
        if e in presentes:
            return e
    return None


def modele_etape(m, etape):
    """Copie du modèle avec seulement les groupes de l'étape (et tout ce qui n'est pas un groupe d'étape)."""
    connues = objet.etapes_connues()
    m2 = copy.deepcopy(m)
    m2["outliner"] = [n for n in m["outliner"] if not (isinstance(n, dict) and objet.normal(n.get("name", "")) in connues
                                                       and objet.normal(n["name"]) != etape)]
    return m2


def transformer(quads, M):
    return [([objet.appliquer(M, p) for p in pts], uvs, col) for pts, uvs, col in quads]


def pose_tenue():
    """Joueur debout, bras droit levé de 18° vers l'avant (HumanoidModel, bras qui tient un objet : xRot − π/10)."""
    pz = rb.pose_joueur("idle")
    R, piv = rb.rot_matrix(18, 0, 0), np.array(rb.PIVOTS["right_arm"], float)
    pz["right_arm"] = lambda p, R=R, piv=piv: R @ (np.asarray(p, float) - piv) + piv
    return pz


def titre(im, texte, coin=(10, 8)):
    ImageDraw.Draw(im).text(coin, texte, fill=(235, 200, 200))
    return im


def vue_gui(quads, tex, aff):
    q = transformer(quads, objet.matrice_gui(aff["gui"]))
    fov, demi = 6.0, 8 * 1.18
    D = demi / math.tan(math.radians(fov / 2))
    im = rb.render(q, tex, (0, 0, D), (0, 0, 0), size=TUILE, fov=fov, bg=FOND)
    c = 8 / demi * 0.5 * TUILE
    d = ImageDraw.Draw(im)
    d.rectangle([TUILE / 2 - c, TUILE / 2 - c, TUILE / 2 + c, TUILE / 2 + c], outline=(90, 80, 110))
    # case à sa taille réelle (interface ×2 : 32 px), agrandie ×3 sans lissage
    case = im.crop((int(TUILE / 2 - c), int(TUILE / 2 - c), int(TUILE / 2 + c), int(TUILE / 2 + c))).resize((32, 32), Image.LANCZOS)
    fond = Image.new("RGB", (32, 32), (139, 139, 139))     # gris d'une case de Minecraft
    fond.paste(case, (0, 0), Image.fromarray((np.abs(np.asarray(case).astype(int) - FOND).max(2) > 12).astype(np.uint8) * 255))
    im.paste(fond.resize((96, 96), Image.NEAREST), (TUILE - 104, TUILE - 104))
    return im


def vue_objet(quads, tex, direction):
    cam, cible = rb.cadrer(rb.points_de(quads), direction, marge=1.08, rayon_min=6.0)
    return rb.render(quads, tex, cam, cible, size=TUILE, bg=FOND)


def vue_main(chemin, tex):
    pz = pose_tenue()
    q, _ = rb.load_model(chemin, pose=pz)
    pts = rb.points_de(q) + [(4, 12, -2), (8, 24, 2)]
    cam, cible = rb.cadrer(pts, (0.75, 0.32, -0.9), marge=1.12, rayon_min=10.0)
    return rb.render(q + rb.mannequin(pz), tex, cam, cible, size=TUILE, bg=FOND)


def vue_premiere(quads, tex, aff, etape=None, type_=None):
    M = objet.matrice_premiere(aff["firstperson_righthand"], etape, type_)
    q = transformer(quads, M)
    hfov = 2 * math.degrees(math.atan(math.tan(math.radians(35)) * 16 / 9))
    grand = rb.render(q, tex, (0, 0, 0), (0, 0, -1), size=TUILE * 2, fov=hfov, bg=(70, 96, 130))
    # écran 16:9 ; on garde le bas de l'écran à droite du tiers (là où Minecraft dessine l'objet, visée de l'arbalète comprise),
    # cadre gris = bord de l'écran, croix = centre de l'écran (viseur)
    N, h = TUILE * 2, TUILE * 2 * 9 // 16
    haut = (N - h) // 2
    x0, y0 = int(N * 0.3), haut + int(h * 0.3)
    im = grand.crop((x0, y0, N, haut + h))
    k = (TUILE - 20) / im.width
    im = im.resize((TUILE - 20, round((haut + h - y0) * k)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    cx, cy = k * (N / 2 - x0), k * (N / 2 - y0)
    d.line([(cx - 6, cy), (cx + 6, cy)], fill=(255, 255, 255)); d.line([(cx, cy - 6), (cx, cy + 6)], fill=(255, 255, 255))
    # repère : le carré de 16 px d'un objet vanilla plat (z = 8) dans le même réglage, pour juger l'encombrement
    f = 1 / math.tan(math.radians(hfov) / 2)
    coins = [objet.appliquer(M, p) for p in ((0, 0, 8), (16, 0, 8), (16, 16, 8), (0, 16, 8))]
    if all(c[2] < -0.1 for c in coins):
        pts = [(k * ((c[0] / -c[2]) * f * 0.5 * N + N / 2 - x0), k * (-(c[1] / -c[2]) * f * 0.5 * N + N / 2 - y0)) for c in coins]
        d.line(pts + pts[:1], fill=(225, 225, 235), width=1)
        d.text((4, im.height - 14), "blanc : carre vanilla 16 px", fill=(225, 225, 235))
    out = Image.new("RGB", (TUILE, TUILE), FOND)
    oy = (TUILE - im.height) // 2
    out.paste(im, (10, oy))
    d = ImageDraw.Draw(out)
    d.rectangle([10, oy, 10 + im.width - 1, oy + im.height - 1], outline=(90, 80, 110))
    return out


def apercus(chemin, sortie):
    with open(chemin, encoding="utf-8") as f:
        m = json.load(f)
    type_ = objet.type_de(m)
    if type_ is None:
        sys.exit("ÉCHEC : pas de bloc phynaria.objet avec un type connu (tools/objet.py)")
    aff = objet.lire_affichage(m)
    presentes = {objet.normal(n.get("name", "")) for n in m["outliner"] if isinstance(n, dict)} & set(objet.ETAPES[type_])
    os.makedirs(sortie, exist_ok=True)
    tmp = tempfile.mkdtemp()
    rangees, noms = [], []
    for e in objet.ETAPES[type_]:
        r = repli(e, presentes, type_)
        if e != "repos" and r != e and not presentes - {"repos"}:
            continue          # objet sans étapes : une seule rangée
        noms.append(e)
        ch = os.path.join(tmp, f"{e}.bbmodel")
        with open(ch, "w", encoding="utf-8") as f:
            json.dump(modele_etape(m, r), f)
        quads, tex = rb.load_model(ch)
        tuiles = [titre(vue_gui(quads, tex, aff), "Inventaire (gui)"), titre(vue_objet(quads, tex, (-0.55, 0.45, 1.0)), "Objet 3/4"),
                  titre(vue_objet(quads, tex, (1.0, 0.2, 0.12)), "Profil"), titre(vue_main(ch, tex), "Main droite, 3e pers."),
                  titre(vue_premiere(quads, tex, aff, e, type_), "1re pers. (bas de l'ecran)")]
        rang = Image.new("RGB", (TUILE * len(tuiles), TUILE), FOND)
        for i, t in enumerate(tuiles):
            rang.paste(t, (i * TUILE, 0))
        etiquette = e.upper() + ("" if r == e or r is None else f"  (repli : {r})")
        ImageDraw.Draw(rang).text((TUILE * len(tuiles) - 9 * len(etiquette) - 10, 8), etiquette, fill=(255, 220, 120))
        rangees.append(rang)
        if e == "repos":
            tuiles[0].resize((480, 480), Image.LANCZOS).save(os.path.join(sortie, "vignette.png"), optimize=True)
            os.environ["NUIT"] = "1"
            try:
                titre(vue_objet(quads, tex, (-0.55, 0.45, 1.0)), "De nuit (calque _e)").save(os.path.join(sortie, "nuit.png"), optimize=True)
            finally:
                os.environ.pop("NUIT", None)
    planche = Image.new("RGB", (rangees[0].width, TUILE * len(rangees)), FOND)
    for i, r in enumerate(rangees):
        planche.paste(r, (0, i * TUILE))
    planche.save(os.path.join(sortie, "planche.png"), optimize=True)
    with open(os.path.join(sortie, "etats.json"), "w", encoding="utf-8") as f:
        json.dump(noms, f)
    return noms


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print("étapes :", apercus(sys.argv[1], sys.argv[2]))
