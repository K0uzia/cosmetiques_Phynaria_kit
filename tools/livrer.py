#!/usr/bin/env python3
"""Livre un cosmétique déjà généré et optimisé : vérifie, crée les aperçus (planche, GIF, vignette), puis met à jour le fichier unique.
Usage : python tools/livrer.py cosmetiques/<categorie>/<nom>
Skins d'objets (cosmetiques/objets/) : aperçus par étape de tools/apercu_objet.py, sans GIF.
Effets de téléportation (cosmetiques/effets/, guide 15) : planche à 4 instants par animation (charge, depart, arrivee),
cadrée sur l'effet et le joueur (qui peut tomber du ciel) ; dans le GIF, depart et arrivee gardent leur dernière image 1 s.
Le livrable n'est écrasé que si le vérificateur passe, avec et sans fusée. Regarder .build/apercu/planche.png ensuite."""
import json, os, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageSequence
try:
    sys.stdout.reconfigure(encoding="utf-8")   # console Windows (cp1252) : caractères →, ≤, accents
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDU = os.path.join(ROOT, "tools", "render_bbmodel.py")
VERIF = os.path.join(ROOT, "tools", "verify_bbmodel.py")
# Caméra du GIF, cible du GIF, facteur de la planche, par catégorie.
CADRAGES = {"ailes": ("125,100,175", "0,22,0", "3.0"), "chapeaux": ("-40,55,-65", "0,34,0", "2.0"), "queues": ("80,60,110", "0,16,14", "2.0"),
            "armes": ("-60,50,-85", "0,14,-4", "2.0"), "auras": ("-55,55,-80", "0,18,0", "2.0"), "epaules": ("-45,55,-70", "0,24,0", "2.0"),
            "familiers": ("-70,70,-100", "0,22,0", "2.0"), "effets": ("-70,60,-100", "0,16,0", "2.0")}
DEFAUT = ("-70,70,-100", "0,20,0", "2.0")
COLONNES, FPS, DUREE, FPS_RENDU = 4, 12, 8.0, 24
# Étiquettes des cases (police par défaut de PIL : sans accent). Familier vivant (guide 6.6) : ses états pet_*.
ETIQUETTES = {"idle": "REPOS", "walk": "MARCHE", "run": "COURSE", "sneak": "ACCROUPI", "fly": "VOL", "glide": "ELYTRES", "fall": "EN L'AIR",
              "swim": "NAGE", "mount": "MONTURE", "sleep": "SOMMEIL", "attack": "ATTAQUE", "hurt": "BLESSE"}
ETIQUETTES_EFFET = {"charge": "CHARGE", "depart": "DEPART", "arrivee": "ARRIVEE"}   # guide 15
INSTANTS_EFFET = {"loop": "0,0.25,0.5,0.75", "once": "0.1,0.4,0.7,1.0"}           # fractions de la durée, planche d'un effet
TENUE_EFFET = 1.0   # s : dernière image de depart et arrivee gardée dans le GIF
ETIQUETTES_PET = {"idle": "REPOS", "walk": "MARCHE", "run": "COURSE", "sit": "ASSIS", "sleep": "DORT", "swim": "NAGE", "fly": "VOL",
                  "fall": "CHUTE", "jump": "SAUT", "land": "ATTERRIT"}


def etiquette(n, vivant):
    """Libellé d'une case : l'état en français ; familier vivant : « FAMILIER : MARCHE »."""
    import render_bbmodel as rb
    mot = n.split(".")[-1]
    if rb.mot_anim(n) in ETIQUETTES_EFFET:
        return ETIQUETTES_EFFET[rb.mot_anim(n)]
    if vivant:
        return "FAMILIER : " + ETIQUETTES_PET[rb.etat_pet(n)]
    return ETIQUETTES.get(mot, mot.upper())


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
    sys.path.insert(0, os.path.dirname(RENDU))
    import render_bbmodel as rb
    # familier vivant (guide 6.6) : aperçus au sol à côté du joueur immobile, avec les requêtes de chaque état (vitesse…)
    vivant = rb.familier_de(m) is not None
    if vivant:
        env = dict(env, FAMILIER="vivant")
    # effet de téléportation (guide 15) : posé au sol, le joueur suit le groupe « joueur »
    effet = categorie == "effets" or rb.effet_de(m)
    boucle = {a["name"]: a.get("loop") == "loop" for a in m["animations"]}
    # états seulement : ni particules, ni couches permanentes, ni événements (guide 6.4)
    longueurs = {a["name"]: float(a["length"]) for a in m["animations"] if not a["name"].split(".")[-1].startswith(("particle_", "overlay_", "event_"))}
    noms = list(longueurs)
    if not noms:
        # pièce statique (seulement overlay_ ou event_) : une seule case « idle », la pose de repos
        noms, longueurs = ["idle"], {"idle": 1.0}
    if effet:
        ordre = {"charge": 0, "depart": 1, "arrivee": 2}
        noms.sort(key=lambda n: ordre.get(rb.mot_anim(n), 3))
    # case de la vignette et de la vue de nuit : repos ; effet : l'arrivée aux trois quarts (joueur posé, effet visible)
    fixe = next((n for n in noms if rb.mot_anim(n) == "arrivee"), None) if effet else None
    fixe = fixe or ("idle" if "idle" in noms else noms[0])
    t_fixe = str(round(longueurs[fixe] * (0.75 if effet else 0.3), 2))
    tmp = tempfile.mkdtemp()

    def rendre(n):
        # GIF de l'état, cadré automatiquement sur la pièce (direction de la catégorie) ; planche 4 vues cadrée aussi.
        # Plus de WebP par état : la vue 3D du Vestiaire (tools/visionneuse.js) joue les animations en direct.
        subprocess.run([sys.executable, RENDU, modele, f"{tmp}/{n}.gif", n, "auto:" + cam], env=env, check=True, capture_output=True)
        if effet:
            # 4 instants de l'animation au lieu de 4 vues (render_bbmodel.py, INSTANTS)
            subprocess.run([sys.executable, RENDU, modele, f"{tmp}/{n}.png"], env=dict(env, ANIM=n, INSTANTS=INSTANTS_EFFET["loop" if boucle.get(n) else "once"]),
                           check=True, capture_output=True)
            return
        subprocess.run([sys.executable, RENDU, modele, f"{tmp}/{n}.png", zoom], env=dict(env, ANIM=n, T=str(round(longueurs[n] * 0.3, 2)), CADRAGE="auto"), check=True, capture_output=True)

    def vignette():
        # Carte du Vestiaire : une vue cadrée serrée sur la pièce, en repos (ou premier état).
        subprocess.run([sys.executable, RENDU, modele, f"{tmp}/vignette.png", "--seule", cam, cible],
                       env=dict(env, ANIM=fixe, T=t_fixe), check=True, capture_output=True)

    def nuit():
        # Vue de nuit (calque _e et lumière seule), repos : panneau « De nuit » du Vestiaire.
        subprocess.run([sys.executable, RENDU, modele, f"{tmp}/nuit.png", zoom], env=dict(env, ANIM=fixe, T=t_fixe, CADRAGE="auto", NUIT="1"),
                       check=True, capture_output=True)

    def jeu():
        # Planche « comme en jeu » (render_bbmodel.py, JEU=1) : la pièce vue par un joueur debout à 3 et 10 blocs, de jour,
        # jour gris, nuit et nuit avec shader (approché), à la densité de l'écran : c'est elle qui dit ce qu'on verra en jeu.
        subprocess.run([sys.executable, RENDU, modele, f"{tmp}/jeu.png"], env=dict(env, ANIM=fixe, T=t_fixe, JEU="1"),
                       check=True, capture_output=True)

    with ThreadPoolExecutor(6) as ex:
        taches = [ex.submit(rendre, n) for n in noms] + [ex.submit(vignette), ex.submit(nuit), ex.submit(jeu)]
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
        e = etiquette(n, vivant)
        ImageDraw.Draw(im).text((L - 8 - 7 * len(e), 6), e, fill=(255, 220, 120))   # coin haut droit, hors des titres de vue
        vues.append(im)
    H = vues[0].height
    planche = Image.new("RGB", (L * COLONNES, H * rangees), (18, 16, 22))
    for i, im in enumerate(vues):
        planche.paste(im, ((i % COLONNES) * L, (i // COLONNES) * H))
    planche.save(f"{sortie}/planche.png", optimize=True)
    shutil.copy2(f"{tmp}/vignette.png", f"{sortie}/vignette.png")
    shutil.copy2(f"{tmp}/nuit.png", f"{sortie}/nuit.png")
    shutil.copy2(f"{tmp}/jeu.png", f"{sortie}/jeu.png")
    # GIF : une case par état, toutes les animations sur 8 s.
    C = 300
    clips = {}
    for n in noms:
        images = []
        for f in ImageSequence.Iterator(Image.open(f"{tmp}/{n}.gif")):
            c = f.convert("RGB").resize((C, C), Image.LANCZOS)
            ImageDraw.Draw(c).text((8, 6), etiquette(n, vivant), fill=(255, 220, 120))
            images.append(c)
        clips[n] = images
    images = []
    for i in range(int(DUREE * FPS)):
        g = Image.new("RGB", (C * COLONNES, C * rangees), (18, 16, 22))
        j = int(i / FPS * FPS_RENDU)
        for k, n in enumerate(noms):
            c = clips[n]
            # effet : depart et arrivee (once) gardent leur dernière image avant de reprendre
            i_c = min(j % (len(c) + int(TENUE_EFFET * FPS_RENDU)), len(c) - 1) if effet and not boucle.get(n) else j % len(c)
            g.paste(c[i_c], ((k % COLONNES) * C, (k // COLONNES) * C))
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
    # fiche (fiche.json, guide 10 bis) et réglages des particules (reglages.json, guide 5 ter §6) embarqués dans
    # unhandled_root_fields.phynaria avant la vérification ; le bloc familier d'un générateur est gardé (tools/fiche.py)
    sys.path.insert(0, os.path.dirname(RENDU))
    import fiche
    for n in fiche.embarquer_fichier(opt, dossier):
        print(f"[phynaria] {n}")
    verifier(opt, env)
    tampon = os.path.join(dossier, ".build", "apercu")
    cible = os.path.join(dossier, "apercu")
    os.makedirs(cible, exist_ok=True)
    if categorie == "objets":
        # skin d'objet (guide 14) : une rangée par étape (inventaire, objet, main 3e et 1re personne), pas d'animation
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "apercu_objet.py"), opt, tampon], env=env, capture_output=True, text=True, encoding="utf-8")
        if r.returncode:
            sys.exit(f"ÉCHEC des aperçus : {r.stderr[-2000:]}")
        fichiers = ("planche.png", "etats.json", "vignette.png", "nuit.png")
        for vieux in ("animations.gif",):
            if os.path.exists(os.path.join(cible, vieux)):
                os.remove(os.path.join(cible, vieux))
    else:
        apercus(opt, tampon, categorie, env)
        fichiers = ("planche.png", "animations.gif", "etats.json", "vignette.png", "nuit.png", "jeu.png")
    for f in fichiers:
        shutil.copy2(os.path.join(tampon, f), os.path.join(cible, f))
    shutil.rmtree(os.path.join(cible, "etats"), ignore_errors=True)   # anciens WebP par état, remplacés par la vue 3D
    shutil.copy2(opt, os.path.join(dossier, nom + ".bbmodel"))
    sys.path.insert(0, os.path.dirname(RENDU))
    import gen_index
    # copie sous le nom propre (fiche.json) dans livrables/<Ensemble>/ : seul le champ « name » change.
    # Avant l'index : le bouton Télécharger du Vestiaire donne cette copie (le mod nomme le cosmétique d'après le fichier).
    import exporter
    if not os.path.isfile(os.path.join(dossier, "fiche.json")):
        print(f"ATTENTION : {nom}/fiche.json manque (nom propre, description, lore, prix : delivery.md, étape 7)")
    exporter.exporter_piece(dossier)
    gen_index.ecrire_index()
    print(f"Livré : {nom}. Regarder {os.path.join(cible, 'planche.png')} et {os.path.join(cible, 'jeu.png')} (comme en jeu)")


if __name__ == "__main__":
    main()
