"""Test du menu Apparence (mod 1.4.0) : aura_brasier en deux variantes, d'après cosmetiques/auras/aura_brasier/.build/.
- test_menu_aura_a.bbmodel : la correction livrée (méthode « camera » de tools/menu_aura.py) : dans le menu, chaque groupe
  cam_/camy_ est tourné face à la caméra par défaut du menu (lacet 30°, vue de 5° au-dessus) par son enveloppe vm_.
- test_menu_aura_b.bbmodel : l'ancienne correction (méthode « retourne », 2026-11-05 20.36.18) : cam_/camy_ retournés de 180°,
  face à une caméra placée droit devant ; la lueur reste plaquée derrière le dos dans la vue de 3/4 du menu.
Usage : python docs/dev/tests_rendu/gen_test_menu_aura.py (après python cosmetiques/auras/aura_brasier/gen_aura_brasier.py
et l'optimisation)."""
import json, os
ICI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ICI, "..", "..", "..", "cosmetiques", "auras", "aura_brasier", ".build", "aura_brasier_opt.bbmodel")
m = json.load(open(SRC, encoding="utf-8"))
for nom, camera in (("test_menu_aura_a", True), ("test_menu_aura_b", False)):
    v = json.loads(json.dumps(m))
    v["name"] = nom
    n = 0
    if not camera:
        for an in v["animations"]:
            for a in an["animators"].values():
                if not a.get("name", "").startswith("vm_"):
                    continue
                for kf in a["keyframes"]:
                    if kf["channel"] == "rotation":
                        for dp in kf["data_points"]:
                            dp["x"], dp["y"], dp["z"] = "0", "q.is_in_menu*180", "0"
                            n += 1
    with open(os.path.join(ICI, nom + ".bbmodel"), "w", encoding="utf-8") as fh:
        json.dump(v, fh, separators=(",", ":"))
    print(nom, "écrit", f"({n} rotations remplacées)" if n else "")
