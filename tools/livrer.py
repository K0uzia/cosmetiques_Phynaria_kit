#!/usr/bin/env python3
"""Livre un cosmétique déjà généré et optimisé : vérifie, crée les aperçus (planche, GIF, vignette), puis met à jour le fichier unique.
Usage : python tools/livrer.py cosmetiques/<categorie>/<nom>
Le livrable n'est écrasé que si le vérificateur passe, avec et sans fusée. Regarder .build/apercu/planche.png ensuite."""
import json, os, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageSequence

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDU = os.path.join(ROOT, "tools", "render_bbmodel.py")
VERIF = os.path.join(ROOT, "tools", "verify_bbmodel.py")
# Caméra du GIF, cible du GIF, facteur de la planche, par catégorie.
CADRAGES = {"ailes": ("125,100,175", "0,22,0", "3.0"), "chapeaux": ("-40,55,-65", "0,34,0", "2.0"), "queues": ("80,60,110", "0,16,14", "2.0"),
            "armes": ("-60,50,-85", "0,14,-4", "2.0"), "auras": ("-55,55,-80", "0,18,0", "2.0"), "epaules": ("-45,55,-70", "0,24,0", "2.0"),
            "familiers": ("-70,70,-100", "0,22,0", "2.0")}
DEFAUT = ("-70,70,-100", "0,20,0", "2.0")
COLONNES, FPS, DUREE, FPS_RENDU = 4, 12, 8.0, 24


def verifier(modele, env):
    env_fusee = dict(env, MOLANG_QUERY="ground_speed=33,vertical_speed=0")
    for e, titre in ((env, "sans fusée"), (env_fusee, "avec fusée")):
        r = subprocess.run([sys.executable, VERIF, modele], env=e, capture_output=True, text=True, encoding="utf-8")
        print(f"--- vérification {titre}")
        print("\n".join(l for l in r.stdout.splitlines() if not l.startswith("[OK")))
        if r.returncode:
            sys.exit("ÉCHEC : le livrable n'a pas été modifié.")


def apercus(modele, sortie, categorie, env):
    cam, cible, zoom = CADRAGES.get(categorie, DEFAUT)
    with open(modele, encoding="utf-8") as f:
        m = json.load(f)
    longueurs = {a["name"]: float(a["length"]) for a in m["animations"] if not a["name"].startswith("particle_")}
    noms = list(longueurs)
    if not noms:
        sys.exit("ÉCHEC : aucune animation d'état à montrer.")
    tmp = tempfile.mkdtemp()

    def rendre(n):
        # GIF de l'état, cadré automatiquement sur la pièce (direction de la catégorie) ; planche 4 vues cadrée aussi.
        # Plus de WebP par état : la vue 3D du Vestiaire (tools/visionneuse.js) joue les animations en direct.
        subprocess.run([sys.executable, RENDU, modele, f"{tmp}/{n}.gif", n, "auto:" + cam], env=env, check=True, capture_output=True)
        subprocess.run([sys.executable, RENDU, modele, f"{tmp}/{n}.png", zoom], env=dict(env, ANIM=n, T=str(round(longueurs[n] * 0.3, 2)), CADRAGE="auto"), check=True, capture_output=True)

    def vignette():
        # Carte du Vestiaire : une vue cadrée serrée sur la pièce, en repos (ou premier état).
        n = "idle" if "idle" in noms else noms[0]
        subprocess.run([sys.executable, RENDU, modele, f"{tmp}/vignette.png", "--seule", cam, cible],
                       env=dict(env, ANIM=n, T=str(round(longueurs[n] * 0.3, 2))), check=True, capture_output=True)

    with ThreadPoolExecutor(6) as ex:
        taches = [ex.submit(rendre, n) for n in noms] + [ex.submit(vignette)]
        for t in taches:
            t.result()
    rangees = (len(noms) + COLONNES - 1) // COLONNES
    os.makedirs(sortie, exist_ok=True)
    # Planche : 4 vues par état.
    L = 720
    vues = []
    for n in noms:
        im = Image.open(f"{tmp}/{n}.png").convert("RGB")
        im = im.resize((L, im.height * L // im.width), Image.LANCZOS)
        ImageDraw.Draw(im).text((L - 8 - 7 * len(n), 6), n.upper(), fill=(255, 220, 120))   # coin haut droit, hors des titres de vue
        vues.append(im)
    H = vues[0].height
    planche = Image.new("RGB", (L * COLONNES, H * rangees), (18, 16, 22))
    for i, im in enumerate(vues):
        planche.paste(im, ((i % COLONNES) * L, (i // COLONNES) * H))
    planche.save(f"{sortie}/planche.png", optimize=True)
    shutil.copy2(f"{tmp}/vignette.png", f"{sortie}/vignette.png")
    # GIF : une case par état, toutes les animations sur 8 s.
    C = 300
    clips = {}
    for n in noms:
        images = []
        for f in ImageSequence.Iterator(Image.open(f"{tmp}/{n}.gif")):
            c = f.convert("RGB").resize((C, C), Image.LANCZOS)
            ImageDraw.Draw(c).text((8, 6), n.upper(), fill=(255, 220, 120))
            images.append(c)
        clips[n] = images
    images = []
    for i in range(int(DUREE * FPS)):
        g = Image.new("RGB", (C * COLONNES, C * rangees), (18, 16, 22))
        j = int(i / FPS * FPS_RENDU)
        for k, n in enumerate(noms):
            g.paste(clips[n][j % len(clips[n])], ((k % COLONNES) * C, (k // COLONNES) * C))
        images.append(g.quantize(colors=128, dither=0))
    images[0].save(f"{sortie}/animations.gif", save_all=True, append_images=images[1:], duration=int(1000 / FPS), loop=0)
    with open(f"{sortie}/etats.json", "w", encoding="utf-8") as f:
        json.dump(noms, f)   # ordre des cases, lu par le Vestiaire
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    dossier = os.path.abspath(sys.argv[1])
    nom, categorie = os.path.basename(dossier), os.path.basename(os.path.dirname(dossier))
    opt = os.path.join(dossier, ".build", nom + "_opt.bbmodel")
    if not os.path.isfile(opt):
        sys.exit(f"ÉCHEC : {opt} introuvable. Lancer le générateur puis tools/optimize_bbmodel.py.")
    env = dict(os.environ, MODCONV="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    verifier(opt, env)
    tampon = os.path.join(dossier, ".build", "apercu")
    apercus(opt, tampon, categorie, env)
    cible = os.path.join(dossier, "apercu")
    os.makedirs(cible, exist_ok=True)
    for f in ("planche.png", "animations.gif", "etats.json", "vignette.png"):
        shutil.copy2(os.path.join(tampon, f), os.path.join(cible, f))
    shutil.rmtree(os.path.join(cible, "etats"), ignore_errors=True)   # anciens WebP par état, remplacés par la vue 3D
    shutil.copy2(opt, os.path.join(dossier, nom + ".bbmodel"))
    sys.path.insert(0, os.path.dirname(RENDU))
    import gen_index
    gen_index.ecrire_index()
    print(f"Livré : {nom}. Regarder {os.path.join(cible, 'planche.png')}")


if __name__ == "__main__":
    main()
