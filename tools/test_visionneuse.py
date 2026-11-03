#!/usr/bin/env python3
"""Compare la visionneuse 3D du Vestiaire (tools/visionneuse.js, exécutée par node) au renderer Python (MODCONV=1, mannequin posé).
Usage : python tools/test_visionneuse.py [modele.bbmodel ...]   (sans argument : quelques pièces livrées).
Pour chaque modèle, plusieurs états et instants : positions des faces du cosmétique et du mannequin, écart max en px."""
import glob, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["MODCONV"] = "1"
import render_bbmodel as rb

ICI = os.path.dirname(os.path.abspath(__file__))
NODE = r"""
const V = require(process.argv[1]); const fs = require("fs");
const [chemin, cas] = [process.argv[2], JSON.parse(process.argv[3])];
const P = V.Noyau.preparer(JSON.parse(fs.readFileSync(chemin, "utf8")));
console.log(JSON.stringify(cas.map(([a, t]) => { const r = V.Noyau.image(P, a, t); return { cosm: r.cosm, mann: r.mann }; })));
"""


def cas_de(m):
    out = []
    for a in m["animations"]:
        if a["name"].startswith("particle_"):
            continue
        L = float(a["length"])
        out += [(a["name"], round(L * f, 4)) for f in (0.13, 0.61)]
    return out


def tester(chemin):
    m = json.load(open(chemin))
    cas = cas_de(m)
    r = subprocess.run(["node", "-e", NODE, os.path.join(ICI, "visionneuse.js"), chemin, json.dumps(cas)], capture_output=True, text=True, check=True)
    js = json.loads(r.stdout)
    pire = 0.0
    for (a, t), j in zip(cas, js):
        an = next(x for x in m["animations"] if x["name"] == a)
        tl = t % float(an["length"]) if an.get("loop") == "loop" else t
        pz = rb.pose_joueur(rb.etat_de(a), tl, float(an["length"]))
        q, _ = rb.load_model(chemin, anim_time=t, anim_name=a, pose=pz)
        mq = rb.mannequin(pz)
        if len(q) != len(j["cosm"]) or len(mq) != len(j["mann"]):
            print(f"  ÉCHEC {a} t={t} : {len(q)}/{len(j['cosm'])} faces, mannequin {len(mq)}/{len(j['mann'])}")
            return False
        for (pts, _, _), jq in zip(q + mq, j["cosm"] + j["mann"]):
            for p, jp in zip(pts, jq):
                pire = max(pire, max(abs(float(p[i]) - jp[i]) for i in range(3)))
    ok = pire < 1e-3
    print(f"  {'OK' if ok else 'ÉCHEC'} {os.path.basename(chemin)} : {len(cas)} cas, écart max {pire:.2e} px")
    return ok


if __name__ == "__main__":
    racine = os.path.dirname(ICI)
    chemins = sys.argv[1:] or sorted(glob.glob(os.path.join(racine, "cosmetiques", "*", "*", "*.bbmodel")))
    sys.exit(0 if all([tester(c) for c in chemins]) else 1)
