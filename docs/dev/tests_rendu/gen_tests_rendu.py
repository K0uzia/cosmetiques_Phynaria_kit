"""Modèles de test minimaux pour les 4 bugs de rendu (docs/dev/bugs_rendu_detail.md).
Écrit test1_shader.bbmodel, test2_reflet_decoupe.bbmodel, test3_menu_additif.bbmodel et test4_particules_mc.bbmodel
à côté de ce script. Chaque modèle ne teste qu'une chose, avec une pièce témoin quand c'est utile.
"""
import base64, io, json, math, os, uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

N = 64                      # texture 64 × 64, une case de 16 × 16 par motif


def png(a):
    b = io.BytesIO()
    Image.fromarray(a.astype(np.uint8), "RGBA").save(b, "PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def case(i, j):
    """UV d'une case (colonne i, ligne j)."""
    return [16 * i, 16 * j, 16 * i + 16, 16 * j + 16]


yy, xx = np.mgrid[0:16, 0:16]
r = np.hypot(xx + 0.5 - 8, yy + 0.5 - 8) / 8

tex = np.zeros((N, N, 4), np.uint8)
tex_e = np.zeros((N, N, 4), np.uint8)
tex_r = np.zeros((N, N, 4), np.uint8)
# case (0,0) : gris opaque, pièce témoin
tex[0:16, 0:16] = (150, 150, 160, 255)
# case (1,0) : dégradé additif, noir au bord -> rouge orangé au centre (noir = invisible en additif)
k = np.clip(1 - r, 0, 1)
tex[0:16, 16:32, 0] = 255 * k
tex[0:16, 16:32, 1] = 90 * k
tex[0:16, 16:32, 2] = 20 * k
tex[0:16, 16:32, 3] = 255
# case (2,0) : bleu à 50 % d'opacité (groupe trans_)
tex[0:16, 32:48] = (60, 120, 255, 128)
# case (3,0) : gris foncé opaque, avec un carré jaune vif dans le calque _e
tex[0:16, 48:64] = (70, 70, 76, 255)
tex_e[4:12, 52:60] = (255, 230, 60, 255)
# case (0,1) : disque doré opaque sur fond TRANSPARENT (découpe par alpha), masque _r blanc sur toute la case
disque = r <= 0.9
tex[16:32, 0:16][disque] = (200, 160, 60, 255)
tex_r[16:32, 0:16] = (255, 255, 255, 255)
# case (1,1) : même disque, SANS reflet (témoin)
tex[16:32, 16:32][disque] = (200, 160, 60, 255)
# texel transparent pour les faces cachées
CLEAR = [62, 62, 63, 63]
assert tex[62, 62, 3] == 0


def nuid():
    return str(uuid.uuid4())


def cube(name, frm, to, uv, faces=("south", "north"), rot=None):
    f = {n: {"uv": uv if n in faces else CLEAR, "texture": 0} for n in ("north", "south", "east", "west", "up", "down")}
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": frm, "to": to,
         "origin": [(a + b) / 2 for a, b in zip(frm, to)], "box_uv": False, "faces": f}
    if rot:
        e["rotation"] = rot
    return e


def groupe(name, origin, children):
    return {"name": name, "origin": origin, "uuid": nuid(), "children": children}


def modele(nom, elements, outliner, textures, animations=()):
    m = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": nom,
         "resolution": {"width": N, "height": N}, "elements": elements, "outliner": outliner,
         "textures": textures, "animations": list(animations)}
    with open(f"{nom}.bbmodel", "w") as fh:
        json.dump(m, fh, indent=1)
    print("écrit", f"{nom}.bbmodel")


def textures(nom, e=False, r=False, trans=False):
    t0 = tex.copy()
    if not trans:
        t0[0:16, 32:48] = 0          # le bleu à 50 % n'est permis que dans un groupe trans_ (test 1)
    t = [{"name": f"{nom}.png", "uv_width": N, "uv_height": N, "source": png(t0)}]
    if e:
        t.append({"name": f"{nom}_e.png", "uv_width": N, "uv_height": N, "source": png(tex_e)})
    if r:
        t.append({"name": f"{nom}_r.png", "uv_width": N, "uv_height": N, "source": png(tex_r)})
    return t


# ---------------------------------------------------------------- test 1 : shaders
# Quatre plaques de 6 × 6 px en rang derrière le dos (z = 4), de gauche à droite vues de dos :
#   A témoin opaque | B add_ (dégradé additif) | C trans_ (bleu 50 %) | D opaque + calque _e (carré jaune)
def plaque(name, x0, uv):
    return cube(name, [x0, 18, 4], [x0 + 6, 24, 4.3], uv)


A = plaque("A_temoin", -13, case(0, 0))
B = plaque("B_additif", -6.5, case(1, 0))
C = plaque("C_translucide", 0.5, case(2, 0))
D = plaque("D_lumineux", 7, case(3, 0))
modele("test1_shader", [A, B, C, D],
       [groupe("body", [0, 24, 0], [A["uuid"], groupe("add_test", [0, 21, 4], [B["uuid"]]),
                                    groupe("trans_test", [0, 21, 4], [C["uuid"]]), D["uuid"]])],
       textures("test1_shader", e=True, trans=True))

# ---------------------------------------------------------------- test 2 : reflets sur une plaque découpée
# Deux disques dorés de 8 px derrière le dos : à gauche avec reflet (masque _r blanc), à droite sans (témoin).
R1 = cube("disque_reflet", [-10, 16, 4], [-2, 24, 4.3], case(0, 1))
R2 = cube("disque_temoin", [2, 16, 4], [10, 24, 4.3], case(1, 1))
modele("test2_reflet_decoupe", [R1, R2], [groupe("body", [0, 24, 0], [R1["uuid"], R2["uuid"]])], textures("test2_reflet_decoupe", r=True))

# ---------------------------------------------------------------- test 3 : menu Apparence
# Un disque de lueur additive de 20 px, face caméra, DERRIÈRE le torse (z = 5). En jeu : halo rouge autour du torse,
# caché par le corps au centre, aucun noir.
H = cube("halo", [-10, 8, 5], [10, 28, 5.3], case(1, 0))
modele("test3_menu_additif", [H], [groupe("body", [0, 24, 0], [groupe("add_halo", [0, 18, 5], [groupe("cam_halo", [0, 18, 5], [H["uuid"]])])])],
       textures("test3_menu_additif"))

# ---------------------------------------------------------------- test 4 : particules Minecraft
# - emit_mc_flame, groupe vide FIXE à 2 px au-dessus du milieu de la tête (0 ; 34 ; 0) dans « head » ;
# - emit_mc_end_rod, groupe vide porté par un groupe « orbite » qui tourne autour du joueur (rayon 10 px,
#   à hauteur de taille, un tour en 4 s) dans « body ».
# Une petite sphère grise (cube témoin) marque chaque point : la particule doit naître dessus.
T1 = cube("repere_tete", [-0.5, 33.5, -0.5], [0.5, 34.5, 0.5], case(0, 0), faces=("north", "south", "east", "west", "up", "down"))
T2 = cube("repere_orbite", [9.5, 15.5, -0.5], [10.5, 16.5, 0.5], case(0, 0), faces=("north", "south", "east", "west", "up", "down"))
emit_tete = groupe("emit_mc_flame", [0, 34, 0], [])
emit_orb = groupe("emit_mc_end_rod", [10, 16, 0], [])
orbite = groupe("orbite", [0, 16, 0], [T2["uuid"], emit_orb])
anim = {"uuid": nuid(), "name": "idle", "loop": "loop", "override": False, "length": 4.0, "snapping": 24, "selected": False,
        "animators": {orbite["uuid"]: {"name": "orbite", "type": "bone", "keyframes": [
            {"channel": "rotation", "data_points": [{"x": "0", "y": str(-90 * i), "z": "0"}], "time": float(i), "interpolation": "linear"}
            for i in range(5)]}}}
modele("test4_particules_mc", [T1, T2],
       [groupe("head", [0, 24, 0], [T1["uuid"], emit_tete]), groupe("body", [0, 24, 0], [orbite])],
       textures("test4_particules_mc"), [anim])
