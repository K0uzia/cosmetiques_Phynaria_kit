"""Modèle de calibration : 3 barres colorées (X rouge, Y vert, Z bleu) + 5 animations d'1 s.
Permet de lire : sens de chaque axe de rotation, support de scale et de position."""
import json, base64, io, uuid
from PIL import Image

tex = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
for i, c in enumerate([(230, 40, 40, 255), (40, 200, 60, 255), (50, 90, 240, 255), (240, 240, 240, 255)]):
    for y in range(4):
        for x in range(4): tex.putpixel((x + 4 * i, y), c)
buf = io.BytesIO(); tex.save(buf, "PNG")
src = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def u(): return str(uuid.uuid4())
def cube(name, f, t, uvx):
    fc = {k: {"uv": [uvx, 0, uvx + 4, 4], "texture": 0} for k in ("north", "south", "east", "west", "up", "down")}
    return {"name": name, "type": "cube", "uuid": u(), "from": f, "to": t, "origin": [0, 24, 0], "box_uv": False, "faces": fc}

els = [cube("bar_x", [0, 23, -1], [12, 25, 1], 0), cube("bar_y", [-1, 24, -1], [1, 36, 1], 4),
       cube("bar_z", [-1, 23, 0], [1, 25, 12], 8), cube("center", [-1.5, 22.5, -1.5], [1.5, 25.5, 1.5], 12)]
root = {"name": "calib", "origin": [0, 24, 0], "uuid": u(), "rotation": [0, 0, 0], "children": [e["uuid"] for e in els]}
outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": u(), "children": [{"name": "item", "origin": [0, 0, 0], "uuid": u(), "children": [root]}]}]

def kf(ch, t, x, y, z): return {"channel": ch, "data_points": [{"x": str(x), "y": str(y), "z": str(z)}], "time": t, "interpolation": "linear"}
def anim(name, kfs):
    return {"uuid": u(), "name": name, "loop": "loop", "override": False, "length": 1.0, "snapping": 24, "selected": False,
            "animators": {root["uuid"]: {"name": "calib", "type": "bone", "keyframes": kfs}}}
anims = [
    anim("rot_x", [kf("rotation", 0, 0, 0, 0), kf("rotation", 1, 45, 0, 0)]),       # la barre VERTE doit basculer : vers +Z (bleu) ou -Z ?
    anim("rot_y", [kf("rotation", 0, 0, 0, 0), kf("rotation", 1, 0, 45, 0)]),       # la barre ROUGE tourne à plat : vers -Z ou +Z ?
    anim("rot_z", [kf("rotation", 0, 0, 0, 0), kf("rotation", 1, 0, 0, 45)]),       # la barre ROUGE monte ou descend ?
    anim("scale_test", [kf("scale", 0, 1, 1, 1), kf("scale", 1, 0, 0, 0)]),         # tout rétrécit jusqu'à disparaître ?
    anim("pos_test", [kf("position", 0, 0, 0, 0), kf("position", 1, 0, 8, 0)]),     # tout monte de 8 px ?
]
m = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": "calibration_axes",
     "resolution": {"width": 16, "height": 16}, "elements": els, "outliner": outliner,
     "textures": [{"name": "calib.png", "uv_width": 16, "uv_height": 16, "source": src}], "animations": anims}
json.dump(m, open("calibration_axes.bbmodel", "w")); print("ok")
