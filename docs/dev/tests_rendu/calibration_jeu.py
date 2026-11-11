"""Planche de calibration du mode « comme en jeu » (2026-11-07) : pour chaque cas, capture en jeu (recadrée) / rendu studio
(ancien aperçu : fond sombre, cadrage serré) / rendu « comme en jeu » (render_bbmodel.py, JEU=1 : ciel, sol, lumière de
Minecraft, écran de 1 369 lignes en 70°, sans lissage). Points de vue approchés à l'œil d'après les captures.
Usage : python docs/dev/tests_rendu/calibration_jeu.py   ->   docs/dev/tests_rendu/calibration_jeu.png"""
import os, sys
from PIL import Image, ImageDraw
ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.normpath(os.path.join(ICI, "..", "..", ".."))
sys.path.insert(0, os.path.join(RACINE, "tools"))
os.environ["MODCONV"] = "1"
import render_bbmodel as rb

CAPTURES = os.path.expanduser(r"~/AppData/Roaming/.phynaria/profiles/ftb-evolution-2/screenshots")
E = os.path.join(RACINE, "cosmetiques", "effets")
# (titre, capture, recadrage, modèle, animation, instant, ciel, œil, cible)
CAS = [
    ("Rayon stellaire v1, jour gris, ~10 blocs", "2026-11-07_18.23.36", (700, 0, 1700, 1000), "effet_stellaire_rayon/.build/v1_livrable.bbmodel",
     "arrivee", 1.2, "gris", (-90, 40, -150), (0, 70, 0)),
    ("Rayon stellaire v1, nuit + shader, ~12 blocs", "2026-11-07_18.24.31", (760, 0, 1760, 1000), "effet_stellaire_rayon/.build/v1_livrable.bbmodel",
     "arrivee", 1.2, "shader", (-110, 40, -170), (0, 70, 0)),
    ("Cercle d'étincelles v1, nuit, ~5 blocs", "2026-11-07_16.44.14", (780, 300, 1580, 1100), "effet_etincelles/.build/v1_livrable.bbmodel",
     "arrivee", 1.0, "nuit", (-40, 46, -70), (0, 18, 0)),
    ("Portail de passage v1, nuit, ~5 blocs", "2026-11-07_16.44.00", (780, 200, 1580, 1000), "effet_portail/.build/v1_livrable.bbmodel",
     "arrivee", 1.0, "nuit", (-30, 34, -72), (0, 20, 0)),
    ("Déchirure du Néant v5, jour gris, ~6 blocs", "2026-11-07_15.45.18", (300, 0, 1600, 1300), "effet_admin_neant/.build/v5_livrable.bbmodel",
     "depart", 1.6, "gris", (-20, 40, -120), (0, 140, 0)),
]
C = 420


def tuile(im, titre):
    im = im.convert("RGB").resize((C, C), Image.LANCZOS)
    ImageDraw.Draw(im).rectangle((0, 0, C, 16), fill=(0, 0, 0))
    ImageDraw.Draw(im).text((4, 2), titre, fill=(255, 225, 150))
    return im


lignes = []
for titre, cap, boite, modele, anim, t, ciel, oeil, cible in CAS:
    chemin = os.path.join(E, modele)
    import json
    m = json.load(open(chemin))
    pz, pm = rb.poses_scene(m, anim, t)
    os.environ.pop("JEU", None)
    q, tex = rb.load_model(chemin, anim_time=t, anim_name=anim, pose=pz)
    scene = q + rb.mannequin(pm)
    a = Image.open(os.path.join(CAPTURES, cap + ".png")).crop(boite)
    cam, tgt = rb.cadrer(rb.points_de(q), (-44, 34, -56), marge=1.1, rayon_min=16.0)
    b = rb.render(scene, tex, cam, tgt, size=600)
    os.environ["JEU"] = "1"; os.environ["CIEL"] = ciel
    c = rb.render(scene, tex, oeil, cible, size=rb.ECRAN_JEU, fov=rb.FOV_JEU)
    # même part de l'écran que le recadrage de la capture (hauteur de la boîte / 1 369 lignes), centrée
    h = boite[3] - boite[1]; x0 = (rb.ECRAN_JEU - h) // 2
    c = c.crop((x0, x0, x0 + h, x0 + h))
    lignes.append((titre, [tuile(a, "En jeu : " + cap), tuile(b, "Ancien rendu (studio)"), tuile(c, "Comme en jeu (" + rb.NOMS_CIELS[ciel] + ")")]))
    print("ok", titre, flush=True)

can = Image.new("RGB", (3 * C + 40, len(lignes) * (C + 30) + 10), (18, 14, 20))
d = ImageDraw.Draw(can)
for i, (titre, ims) in enumerate(lignes):
    y = 10 + i * (C + 30)
    d.text((10, y), titre, fill=(235, 235, 235))
    for j, im in enumerate(ims):
        can.paste(im, (10 + j * (C + 10), y + 18))
can.save(os.path.join(ICI, "calibration_jeu.png"), optimize=True)
print("ok", os.path.join(ICI, "calibration_jeu.png"))
