#!/usr/bin/env python3
"""Vérifie un .bbmodel contre les limites du mod de cosmétiques + les règles du projet.
Usage : python3 tools/verify_bbmodel.py modele.bbmodel [--max-ext 64] [--strict]
Code retour 0 si tout passe, 1 sinon."""
import sys, os, json, base64, io, zlib, math, collections, argparse
import numpy as np
try:
    sys.stdout.reconfigure(encoding="utf-8")   # console Windows (cp1252) : caractères ≤, →, accents
except (AttributeError, ValueError):
    pass
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("MODCONV", "1")
import render_bbmodel as rb

LIMITS = dict(cubes=8192, groups=2048, depth=64, anims=32, keyframes=32768, tex=512, compressed_kb=1000, ext=128.0,
              import_mb=16, stored_mb=8, rotation=360.0, inflate=8.0, name=64, uv_res=4096, anim_length=600.0, molang=512, sons=32,
              cle_position=320.0, cle_scale=16.0)
# zone autorisée (guide 3 et 7, 2026-11-06 soir) : cubes et pivots, sur chaque axe, mesurés sur le modèle AU REPOS.
# Les animations ne comptent plus : une clé position déplace un groupe de 320 px au plus, une clé scale l'agrandit 16 fois au plus.
EXT_EFFET, EXT_OBJET, EXT_PORTE = 320.0, 64.0, 128.0


def limite_extension(effet, objet):
    return EXT_EFFET if effet else (EXT_OBJET if objet else EXT_PORTE)


def extension_repos(m, P):
    """(distance max à l'origine sur un axe, où) : coins des cubes au repos P (renderer, sans animation) et pivots des groupes
    et des cubes (origin)."""
    best, ou = 0.0, "aucun cube"
    if len(P):
        best, ou = float(np.abs(P).max()), "cubes"
    piv = [n.get("origin") for n in m.get("elements", [])] + [g.get("origin") for r in m.get("outliner", []) for g in _groupes(r)]
    piv = [p for p in piv if isinstance(p, (list, tuple)) and len(p) == 3]
    if piv:
        d = float(np.abs(np.array(piv, float)).max())
        if d > best:
            best, ou = d, "pivots"
    return best, ou


# requêtes Molang du guide (6.3, 6.6, 14 ; 2026-11-06 soir) : une requête inconnue vaut 0 en jeu.
# hit_by_entity (6.3) : 1 pendant un coup reçu d'un joueur, d'un monstre ou d'un projectile ; pas encore vérifiée en jeu.
REQUETES = set("""anim_time life_time ground_speed vertical_speed health max_health is_on_ground is_sneaking is_flying is_sprinting
is_swimming is_gliding is_riding is_sleeping is_boosting yaw_speed head_x_rotation head_y_rotation time_of_day moon_phase is_in_rain
is_in_water is_in_lava is_first_person is_in_menu has_shader_pack is_slim_arms has_helmet has_chestplate has_leggings has_boots
body_x_rotation right_arm_x_rotation right_arm_z_rotation left_arm_x_rotation left_arm_z_rotation limb_swing limb_swing_amount
hurt_time attack_time hit_by_entity instance_seed distance_to_camera land_speed delta_time
is_pet is_perched is_sitting owner_distance owner_is_sneaking owner_is_sprinting owner_is_sleeping owner_health owner_max_health
owner_ground_speed use_progress item_durability is_enchanted in_first_person hand""".split())
REQUETES_OBJET = {"use_progress", "item_durability", "is_enchanted", "in_first_person", "hand"}

# skins d'objets vivants (guide 14, 2026-11-06 soir) : noms d'animation joués sur un objet
ANIMS_OBJET = {"item_idle", "item_use", "item_swing", "item_ground", "item_gui"}
EVENTS_OBJET = {"swing", "hit", "break", "use_start", "use_stop", "select", "release", "charged"}

def _nom_groupe(n):
    return n.get("name", "") if isinstance(n, dict) else ""


def _groupes(n):
    if not isinstance(n, dict):
        return []
    return [n] + [g for c in n.get("children", []) for g in _groupes(c)]


def categorie(path):
    """cosmetiques/<categorie>/<nom>/... (livrable ou .build/) → <categorie> ; None hors du dépôt de pièces."""
    parts = os.path.normpath(os.path.abspath(path)).split(os.sep)
    i = max((k for k, p in enumerate(parts) if p == "cosmetiques"), default=None)
    return parts[i + 1] if i is not None and i + 2 < len(parts) else None


# noms d'animation reconnus (guide 6.2, 6.4, 6.6) : dernière partie du nom, après le dernier « . »
ETATS_PORTE = {"idle", "repos", "immobile", "walk", "marche", "sprint", "run", "cours", "course", "sneak", "crouch", "accroupi",
               "fly", "vol", "flap", "glide", "elytra", "plane", "swim", "nage", "fall", "jump", "chute", "saut", "ride", "mount",
               "monture", "sleep", "dort", "dodo", "attack", "swing", "hit", "coup", "hurt", "damage", "degat", "dégât"}
EVENTS_PORTE = {"jump", "land", "equip", "unequip"} | {f"{s}_{e}" for s in ("enter", "exit")
                                                       for e in ("idle", "walk", "sprint", "sneak", "fly", "glide", "swim", "fall", "ride", "sleep")}
ETATS_PET = {"pet_idle", "idle", "repos", "immobile", "pet_walk", "walk", "marche", "pet_run", "run", "sprint", "cours", "course",
             "pet_sit", "sit", "assis", "perch", "pet_sleep", "sleep", "dort", "dodo", "pet_swim", "swim", "nage", "pet_fly", "fly", "vol",
             "flap", "pet_fall", "fall", "chute", "pet_jump", "jump", "saut", "pet_land", "land", "atterri"}
EVENTS_PET = {"equip", "jump", "land", "teleport", "perch", "owner_hurt"} | {f"{s}_{e}" for s in ("enter", "exit")
                                                                             for e in ("idle", "walk", "run", "sit", "sleep", "swim", "fly", "fall", "jump", "land")}
# effet de téléportation (guide 15) : animations trouvées par la fin de leur nom, accents et majuscules ignorés
ANIMS_EFFET = {"charge": "loop", "depart": "once", "arrivee": "once"}
EFFET_MAX_S = 5.0     # durée max de depart et arrivee
GROUPES_CORPS = {"head", "hat", "helmet", "body", "torso", "chest", "rightarm", "armright", "leftarm", "armleft", "rightleg", "legright",
                 "leftleg", "legleft"}     # guide 4 : majuscules, espaces, tirets et « _ » ignorés


def corps(nom):
    return nom.lower().replace(" ", "").replace("-", "").replace("_", "") in GROUPES_CORPS


# pièces portées : pas de réaction aux coups (animation.md, « Attaque et blessé », 2026-11-05) ; armes : attack seul
REACTIONS_INTERDITES = {c: {"attack", "hurt"} for c in ("chapeaux", "epaules", "queues", "sacs", "auras")}
REACTIONS_INTERDITES["armes"] = {"hurt"}

# ailes qui se traversent (.claude/rules/categories/ailes.md, ailes_orage v4) : poses de repos, éléments qui passent la colonne x = 0.
# Mesure sur le centre de chaque élément (moyenne de ses coins) : les coins d'une plaque découpée sont souvent transparents
# (membrane des ailes abyssales : coin à +1,3 px en course, rien de visible). Calibré le 2026-11-05 sur les 9 paires d'ailes :
# validées en jeu (abyssales, Bérénice, givre, steampunk) au plus 1,58 px hors racine (givre, secondaires en idle) et
# 2,53 px à la racine (Bérénice, scapulaires en sneak) ; repos en X refusé (ailes_orage v4) : 6,1 px.
POSES_REPOS = ("idle", "walk", "run", "sneak", "sleep", "mount")
COTE_MIN = 0.5      # |x| du centre d'un élément en pose de base pour lui donner un côté
RACINE = 6.0        # |x| de base sous lequel un élément couvre la racine (scapulaires, attache) : seulement une alerte
CROISE_TOL = 2.0    # dépassement permis du centre d'un élément d'aile de l'autre côté de x = 0 (px) : au-delà, FAIL
RACINE_TOL = 3.0    # idem pour la racine : au-delà, WARN (plumes qui s'entremêlent à la pointe du V)


def ailes_croisees(path, anims):
    """{"aile": pire, "racine": pire} avec pire = (dépassement px, anim, t, élément) sur les poses de repos ; None sans pose de repos.
    Côté de chaque élément = signe du centre x en pose de base (|x| > COTE_MIN). Ignorés : cam_/camy_ (tournés vers la caméra
    au rendu, leur géométrie ici n'est pas celle vue), emit_ (vides), particle_ (non portés, déjà exclus par le renderer),
    éléments cachés par ctrl_alpha ou à échelle quasi nulle (< 0,05 px)."""
    repos = [an for an in anims if an["name"].split(".")[-1] in POSES_REPOS]
    if not repos:
        return None
    def par_element(**kw):
        noms = []
        q, _ = rb.load_model(path, noms=noms, **kw)
        acc = {}
        for (pts, _, _), (uid, chemin) in zip(q, noms):
            if any(n.startswith(("cam_", "camy_", "emit_")) for n in chemin):
                continue
            acc.setdefault(uid, []).extend(pts)
        return {u: np.array(p) for u, p in acc.items()}
    base = {u: P[:, 0].mean() for u, P in par_element().items()}
    cote = {u: np.sign(cx) for u, cx in base.items() if abs(cx) > COTE_MIN}
    m = json.load(open(path, encoding="utf-8"))
    nom_el = {e["uuid"]: e.get("name", "?") for e in m["elements"]}
    pire = {"aile": (-99.0, "", 0.0, ""), "racine": (-99.0, "", 0.0, "")}
    for an in repos:
        L = float(an["length"])
        for t in (0.0, L / 4, L / 2, 3 * L / 4):
            for u, P in par_element(anim_time=float(t), anim_name=an["name"]).items():
                s = cote.get(u)
                if s is None or np.ptp(P, axis=0).max() < 0.05 or np.abs(P).max() < 1e-9:
                    continue
                d = float(-s * P[:, 0].mean())          # centre passé de l'autre côté de la colonne
                z = "racine" if abs(base[u]) < RACINE else "aile"
                if d > pire[z][0]:
                    pire[z] = (d, an["name"], float(t), nom_el.get(u, u))
    return pire


# échelles superposées (guide 6.4 et 14) : un événement joue par-dessus l'état et les overlay_, et plusieurs événements
# peuvent jouer ensemble ; leurs échelles se MULTIPLIENT. Un groupe déplié ×10 par event_swing ET par event_hit l'est ×100
# au coup qui touche (skin_epee_orage, 2026-11-08). Ensembles qui se recouvrent vraiment (un « créneau » = au plus une
# animation à la fois ; l'état en cours en est un, obligatoire) :
#   objet : coup (swing + hit le même tick, select si l'on frappe juste après l'avoir pris en main), minage (swing à chaque
#   coup + break), utilisation (use_start, item_use, charged, une étape), relâche (use_stop + release + une étape le même
#   tick ; use_start encore en cours sur un clic bref). item_ground et item_gui ne jouent aucun événement.
#   porté / familier : changement d'état (un exit_ + un enter_ le même tick, avec jump, land, teleport ou perch qui le
#   provoquent, et attack, hurt, owner_hurt qui peuvent tomber dessus). event_equip / event_unequip ne jouent qu'avec l'état
#   (pas de recouvrement documenté avec les autres : non compté).
def _creneaux_superposes(short, objet):
    ev = lambda *e: [[f"event_{x}"] for x in e]
    if objet:
        etapes = [sorted(n for n in short if n.startswith("event_enter_"))]
        return [("coup", [["item_idle", "item_swing"]] + ev("select", "swing", "hit")),
                ("minage", [["item_idle", "item_swing"]] + ev("select", "swing", "break")),
                ("utilisation", [["item_use"]] + ev("select", "use_start", "charged") + etapes),
                ("relâche", [["item_idle", "item_use"]] + ev("use_start", "use_stop", "release", "charged") + etapes)]
    etats = sorted(n for n in short if not n.startswith(("event_", "overlay_", "particle_")) and n not in ("attack", "hurt"))
    cause = [f"event_{x}" for x in ("jump", "land", "teleport", "perch")]
    return [("changement d'état", [etats or [None], cause] + [[n] for n in ("attack", "hurt", "event_owner_hurt")]
             + [sorted(n for n in short if n.startswith("event_enter_")), sorted(n for n in short if n.startswith("event_exit_"))])]


def echelles_superposees(m, objet, seuil=1.5):
    """[(groupe, ensemble, cumul, base, [(anim, pic)])] : groupes dont l'échelle (pic des clés numériques, ancêtres compris)
    est multipliée par ≥ seuil quand des animations qui se recouvrent jouent ensemble, par rapport à l'état + une seule
    (borne haute : les pics sont multipliés sans tenir compte du moment où ils tombent)."""
    anims = m.get("animations", [])
    short_of = {an["name"]: an["name"].split(".")[-1] for an in anims}
    short = set(short_of.values())
    if not any(n.startswith("event_") for n in short):
        return []
    parent, nom = {}, {}
    def tour(n, p=None):
        if isinstance(n, dict):
            parent[n.get("uuid")] = p; nom[n.get("uuid")] = n.get("name", "")
            for c in n.get("children", []): tour(c, n.get("uuid"))
    for n in m.get("outliner", []): tour(n)
    pic = collections.defaultdict(dict)   # pic[anim court][uuid] = (sx, sy, sz) maximum des clés scale numériques
    for an in anims:
        for u, b in an.get("animators", {}).items():
            vals = [[], [], []]
            for k in b.get("keyframes", []):
                if k.get("channel") != "scale": continue
                for dp in k.get("data_points", []):
                    for i, ax in enumerate("xyz"):
                        try: vals[i].append(abs(float(dp.get(ax, 1))))
                        except (TypeError, ValueError): pass
            if any(vals):
                p = tuple(max(v) if v else 1.0 for v in vals)
                old = pic[short_of[an["name"]]].get(u, (0, 0, 0))
                pic[short_of[an["name"]]][u] = tuple(max(a_, b_) for a_, b_ in zip(old, p))
    def chaine(a_, u):   # pic effectif d'un groupe dans une animation : produit sur lui et ses ancêtres
        s = np.ones(3)
        while u is not None:
            s *= pic.get(a_, {}).get(u, (1.0, 1.0, 1.0)); u = parent.get(u)
        return s
    over = [n for n in short if n.startswith("overlay_")]
    touches = {u for d in pic.values() for u in d}
    cibles = {u for u in parent if any(v in touches for v in _ancetres(u, parent))}
    out = {}
    for u in cibles:
        s_over = np.ones(3)
        for o in over: s_over = s_over * chaine(o, u)
        for nom_ens, creneaux in _creneaux_superposes(short, objet):
            etat = [a_ for a_ in creneaux[0] if a_ is None or a_ in short] or [None]
            couches = [[a_ for a_ in c if a_ in short] for c in creneaux[1:]]
            couches = [c for c in couches if c]
            for e in etat:
                se = chaine(e, u) * s_over if e else s_over
                meilleurs = [max(c, key=lambda a_: chaine(a_, u).max()) for c in couches]
                fac = [chaine(a_, u) for a_ in meilleurs]
                actifs = [(a_, f) for a_, f in zip(meilleurs, fac) if f.max() > 1.0 + 1e-6]
                if len(actifs) + (se.max() > 1.0 + 1e-6) < 2: continue
                cumul = se * np.prod([np.maximum(f, 1.0) for f in fac], axis=0) if fac else se
                base = max((se * f for f in fac), key=lambda v: v.max(), default=se)
                base = np.maximum(base, se)
                if cumul.max() >= seuil * base.max() and cumul.max() > 1.0:
                    k = (u, nom_ens)
                    if k not in out or cumul.max() > out[k][2]:
                        out[k] = (nom.get(u, u), nom_ens, float(cumul.max()), float(base.max()),
                                  ([(e, float(chaine(e, u).max()))] if e else []) + [(a_, float(f.max())) for a_, f in actifs])
    # ne garder que le plus haut groupe en cause (les enfants héritent du même cumul)
    garde = [v for (u, ens), v in out.items() if not any((p_, ens) in out and abs(out[(p_, ens)][2] - v[2]) < 1e-6
                                                         for p_ in _ancetres(u, parent)[1:])]
    return sorted(garde, key=lambda v: -v[2] / max(v[3], 1e-6))


def _ancetres(u, parent):
    r = []
    while u is not None:
        r.append(u); u = parent.get(u)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path"); ap.add_argument("--max-ext", type=float, default=None,
                    help="limite au repos (défaut : 320 effet, 64 skin d'objet, 128 sinon)"); ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    ok = True
    def check(cond, msg, warn=False):
        nonlocal ok
        tag = "OK " if cond else ("WARN" if warn else "FAIL")
        if not cond and not warn: ok = False
        print(f"[{tag}] {msg}")

    raw = open(a.path, "rb").read()
    try:
        m = json.loads(raw)
    except Exception as e:
        print("[FAIL] JSON invalide :", e); return 1
    import fiche as fiche_mod
    mode_pet, objet = fiche_mod.mode_familier(m), fiche_mod.type_objet(m)
    # effet de téléportation (guide 15) : dossier cosmetiques/effets/, ou animation depart/arrivee, ou groupe joueur
    effet = categorie(a.path) == "effets" or rb.effet_de(m)
    formats = ("free", "modded_entity", "java_block") if objet else ("free", "modded_entity")   # skin d'objet : Java Block/Item (guide 14)
    check(m.get("meta", {}).get("model_format") in formats, f"format = {m.get('meta', {}).get('model_format')} (attendu {' ou '.join(formats)})")
    # textures : une principale, en premier, plus au plus une _e (lumière), une _r (masque de reflets), une _m (matcap) (guide, sections 5 à 5 quater)
    all_texs = m.get("textures", [])
    suffixe = lambda t: next((x for x in ("_e", "_r", "_m") if os.path.splitext(t.get("name", ""))[0].endswith(x)), "")
    is_e = lambda t: suffixe(t) != ""
    texs = [t for t in all_texs if not is_e(t)]
    e_texs = [t for t in all_texs if suffixe(t) in ("_e", "_r")]
    m_texs = [t for t in all_texs if suffixe(t) == "_m"]
    nb = collections.Counter(suffixe(t) for t in all_texs if is_e(t))
    check(len(texs) == 1 and all(v <= 1 for v in nb.values()),
          f"{len(texs)} texture(s) principale(s) + calques {dict(nb) or 'aucun'} (attendu 1 + au plus une _e, une _r, une _m)")
    check(not all_texs or not is_e(all_texs[0]), "texture principale en premier")
    for t in m_texs:
        im_m = Image.open(io.BytesIO(base64.b64decode(t["source"].split(",", 1)[1])))
        check(max(im_m.size) <= 256, f"matcap _m {im_m.size[0]}x{im_m.size[1]} (≤ 256)")
    if texs:
        src = texs[0].get("source", "")
        if not src.startswith("data:image/png;base64,"):
            print("[FAIL] texture non embarquée en PNG base64"); return 1
        im = Image.open(io.BytesIO(base64.b64decode(src.split(",", 1)[1])))
        res = (m["resolution"]["width"], m["resolution"]["height"])
        check(im.format == "PNG", f"texture au format {im.format} (attendu PNG)")
        check(max(res) <= LIMITS["uv_res"], f"résolution UV {res} (≤ {LIMITS['uv_res']})")
        check(im.size[0] <= LIMITS["tex"] and im.size[1] <= LIMITS["tex"], f"texture {im.size[0]}x{im.size[1]} (≤ {LIMITS['tex']})")
        check(tuple(map(float, im.size)) == tuple(map(float, res)), f"résolution déclarée {res} = PNG {im.size}")
        alpha = np.array(im.convert("RGBA"))[:, :, 3]
        semi = int(((alpha > 0) & (alpha < 255)).sum())
        # guide 4 bis : trans_ respecte l'opacité ; depuis le 2026-11-08 (demandes 6), add_ ajoute couleur × alpha (lueur
        # qui s'estompe par l'alpha) ; ailleurs, un pixel est opaque ou invisible (cutout)
        a_trans = any(_nom_groupe(n).startswith(("trans_", "add_")) for n in m.get("outliner", []) for n in _groupes(n))
        if a_trans and semi:
            print(f"[INFO] pixels semi-transparents : {semi}, permis dans les groupes trans_ et add_ (guide 4 bis ; à garder sur "
                  "les seules faces trans_ et add_ ; add_ : couleur × alpha depuis le 2026-11-08)")
        else:
            check(semi == 0, f"pixels semi-transparents : {semi}")
        for t in e_texs:
            ie = Image.open(io.BytesIO(base64.b64decode(t["source"].split(",", 1)[1])))
            check(ie.size == im.size, f"calque {suffixe(t)} {ie.size} = texture {im.size}")
    # structure
    els = m["elements"]
    if len(all_texs) > 1:
        main_i = all_texs.index(texs[0]) if texs else 0
        bad_tex = sum(1 for e in els for fd in e["faces"].values() if fd.get("texture") not in (None, main_i))
        check(bad_tex == 0, f"faces assignées à un calque (_e, _r, _m) : {bad_tex}")
    def walk(n, d=1):
        if isinstance(n, str): return 0, d - 1
        g, dm = 1, d
        for c in n.get("children", []):
            gg, dd = walk(c, d + 1); g += gg; dm = max(dm, dd)
        return g, dm
    groups, depth = 0, 0
    for n in m["outliner"]:
        g, d = walk(n); groups += g; depth = max(depth, d)
    check(len(els) <= LIMITS["cubes"], f"{len(els)} cubes (≤ {LIMITS['cubes']})")
    check(all(e.get("type", "cube") == "cube" for e in els), "cubes uniquement (pas de mesh)")
    check(groups <= LIMITS["groups"], f"{groups} groupes (≤ {LIMITS['groups']})")
    check(depth <= LIMITS["depth"], f"profondeur {depth} (≤ {LIMITS['depth']})")
    def group_nodes(n):
        if isinstance(n, str): return []
        return [n] + [g for c in n.get("children", []) for g in group_nodes(c)]
    gnodes = [g for n in m["outliner"] for g in group_nodes(n)]
    gnames = [g.get("name", "") for g in gnodes]
    check(all(len(n) <= LIMITS["name"] for n in gnames), f"noms de groupes ≤ {LIMITS['name']} caractères")
    # emit_mc_<id> et ctrl_<…> peuvent se répéter (guide 5 ter et 4 bis) ; les autres noms restent uniques
    uniques = [n for n in gnames if not n.startswith(("emit_mc_", "ctrl_"))]
    check(len({n[:LIMITS["name"]] for n in uniques}) == len(uniques), "noms de groupes uniques (après coupure ; emit_mc_ et ctrl_ exceptés)")
    # particules (guide, section 5 ter)
    roots = [n.get("name", "") for n in m["outliner"] if isinstance(n, dict)]
    kinds = {n[len("particle_"):] for n in gnames if n.startswith("particle_")}
    bad_part = [n for n in gnames if n.startswith("particle_") and n not in roots]
    check(not bad_part, f"groupes particle_ à la racine : {len(bad_part)} hors racine")
    emits = [g for g in gnodes if g.get("name", "").startswith("emit_")]
    emit_kind = lambda name: name[len("emit_"):].rstrip("0123456789").rstrip("_")
    # emit_mc_<identifiant> : particule vanilla (fonction anticipée, .claude/rules/conventions-anticipees.md), sans particle_ associée
    orphans = sorted({g["name"] for g in emits if not g["name"].startswith("emit_mc_") and emit_kind(g["name"]) not in kinds})
    check(not orphans, f"points emit_ sans particule : {orphans or 'aucun'}")
    missing = sorted(kinds - {emit_kind(g["name"]) for g in emits})
    check(not missing, f"particules sans point emit_ : {missing or 'aucune'}")
    check(len(kinds) <= 4, f"{len(kinds)} sorte(s) de particules (≤ 4)")
    check(len(emits) <= 32, f"{len(emits)} points emit_ (≤ 32)")
    check(all(not g.get("children") or all(isinstance(c, dict) and c.get("name", "").startswith("ctrl_") for c in g["children"]) for g in emits),
          "points emit_ vides (hors groupes ctrl_)")
    ctrls = [g for g in gnodes if g.get("name", "").startswith("ctrl_")]
    check(all(not g.get("children") for g in ctrls), f"groupes ctrl_ vides : {len(ctrls)}")
    CTRL_OK = ("ctrl_alpha", "ctrl_teinte", "ctrl_lumiere", "ctrl_uv", "ctrl_reflet", "ctrl_emit")      # guide 4 bis, 2026-11-04
    bad_ctrl = sorted({g["name"] for g in ctrls if g["name"] not in CTRL_OK})
    check(not bad_ctrl, f"groupes ctrl_ connus du mod ({', '.join(CTRL_OK)}) : {bad_ctrl or 'tous'}")
    # ctrl_emit règle la cadence du point emit_ qui le contient (guide 5 ter) : ailleurs, il ne fait rien
    emit_ctrl = {c.get("uuid") for g in emits for c in g.get("children", []) if isinstance(c, dict) and c.get("name") == "ctrl_emit"}
    hors = [g for g in ctrls if g["name"] == "ctrl_emit" and g.get("uuid") not in emit_ctrl]
    check(not hors, f"ctrl_emit placés dans un point emit_ : {len(hors)} hors d'un point" if hors else "ctrl_emit placés dans un point emit_")
    mc = sorted({g["name"] for g in emits if g["name"].startswith("emit_mc_")})
    check(len(mc) <= 4, f"{len(mc)} sorte(s) de particules Minecraft (≤ 4)")
    check(not [n for n in mc if n[-1].isdigit() and not n.startswith("emit_mc_dust_")], f"emit_mc_ sans chiffre au bout (le chiffre fait partie du nom de la particule) : {mc or 'aucun'}")
    # bloc unhandled_root_fields.phynaria (guide 5 ter §6, 6.6, 10 bis, 14) : réglages des particules, fiche, familier, objet
    err_p, alerte_p, resume_p = fiche_mod.valider_phynaria(m)
    for t in alerte_p:
        check(False, t, warn=True)
    if fiche_mod.bloc(m, creer=False) is not None:
        check(not err_p, "bloc phynaria (" + (", ".join(resume_p) or "vide") + ") : " + ("; ".join(err_p) if err_p else "format du guide"))
    if not objet:
        pr = [p for p in (fiche_mod.bloc(m, creer=False) or {}).get("particules", []) or [] if isinstance(p, dict)]
        propres = [p.get("particule", "?") for p in pr if str(p.get("quand", "")).lower() == "utilisation"
                   or str(p.get("rafale", "")).lower() == "tir"]
        if propres:
            check(False, f"réglages « À l'utilisation » / « Au tir » sur {propres} : réservés aux skins d'objets (guide 5 ter, 14), jamais "
                  "joués sur un cosmétique porté", warn=True)
    # familier vivant (guide 6.6) : il quitte le corps du joueur
    if mode_pet:
        corps_racine = sorted(n for n in roots if corps(n))
        check(not corps_racine, f"familier vivant (mode {mode_pet}) sans groupe du corps à la racine : {corps_racine or 'aucun'} (guide 6.6)")
        if emits:
            check(False, f"familier vivant : ses particules (emit_) ne sont pas encore lancées par le mod (guide 6.6)", warn=True)
        if any(n.startswith("phys_") for n in gnames):
            check(False, "familier vivant : les groupes phys_ restent sur leur pose animée, sans ressort (guide 6.6)", warn=True)
    if effet:
        # guide 15 : pas porté ; groupe vide « joueur » = position et échelle du joueur pendant depart et arrivee
        corps_racine = sorted(n for n in roots if corps(n))
        if corps_racine:
            check(False, f"effet de téléportation : groupes du corps {corps_racine} à la racine — l'effet n'est pas porté, ils ne suivent "
                  "aucune partie du joueur (guide 15) : les renommer", warn=True)
        jg = [g for g in gnodes if rb.mot_anim(g.get("name", "")).replace(" ", "") == "joueur"]
        if not jg:
            print("[INFO] effet de téléportation sans groupe joueur : le joueur apparaît normalement (guide 15)")
        for g in jg:
            check(not g.get("children"), f"groupe joueur vide (guide 15) : {len(g.get('children', []))} enfant(s)")
            rot_j = sorted({an["name"] for an in m.get("animations", []) for u, b in an.get("animators", {}).items()
                            if u == g.get("uuid") and any(k.get("channel") == "rotation" for k in b.get("keyframes", []))})
            if rot_j:
                check(False, f"groupe joueur : rotation animée dans {rot_j}, ignorée par le mod (position et échelle seules, guide 15)", warn=True)
        if jg:
            hauts = []
            for an in m.get("animations", []):
                if rb.mot_anim(an["name"]) in ("charge", "depart", "arrivee"):
                    for t in np.linspace(0, float(an["length"]), 25):
                        pl = rb.place_joueur_effet(m, float(t), an["name"])
                        if pl is not None:
                            hauts.append((float(np.abs(pl[0]).max()), float(np.abs(pl[1]).max()), an["name"]))
            if hauts:
                d, _, n = max(hauts)
                print(f"[INFO] groupe joueur : jusqu'à {d:.0f} px de l'origine (dans '{n}'), échelle {min(h[1] for h in hauts):.2f} à "
                      f"{max(h[1] for h in hauts):.2f} ; groupe vide, hors extension (guide 15 : y = 160 pour une arrivée du ciel)")
        raf = [p.get("particule", "?") for p in (fiche_mod.bloc(m, creer=False) or {}).get("particules", []) or []
               if isinstance(p, dict) and str(p.get("rafale", "aucune")).lower() not in ("aucune", "")]
        if raf:
            check(False, f"effet de téléportation : rafales réglées pour {raf}, sans effet (guide 15 : particules lancées tant que l'effet joue)", warn=True)
    if categorie(a.path) == "objets":
        check(objet is not None, "skin d'objet : bloc phynaria.objet avec un type connu (tools/objet.py, guide 14)"
              + ("" if objet else " — absent : le staff devra choisir le type à l'import"))
    if objet:
        import objet as objet_mod
        etapes = set(fiche_mod.OBJETS[objet])
        connues = objet_mod.etapes_connues()
        hors = sorted(n for n in roots if objet_mod.normal(n) in connues and objet_mod.normal(n) not in etapes)
        check(not hors, f"skin d'objet ({objet}) : étapes à la racine valides : " + (f"{hors} ne sont pas des étapes de ce type" if hors else "oui"))
        mises = sorted({objet_mod.normal(n) for n in roots} & etapes)
        print(f"[INFO] skin d'objet ({objet}) : étapes modelées {mises or 'aucune (toujours dessiné en entier)'} ; étapes du type {list(fiche_mod.OBJETS[objet])}")
        if m.get("animations") or emits:
            print("[INFO] skin d'objet vivant : animations, ctrl_, particules et sons joués (guide 14, 2026-11-06 soir) ; sons et particules "
                  "en main seulement, au sol item_ground + overlay_, dans l'inventaire item_gui seul ; option joueur « Animations des "
                  "skins d'objets » ; à juger en jeu")
        if m.get("animations") and m.get("meta", {}).get("model_format") == "java_block":
            check(False, "skin d'objet animé en java_block : Blockbench n'a pas d'animations dans ce format, préférer free "
                  "+ phynaria.objet.affichage (guide 14)", warn=True)
        if any(n.startswith(("cam_", "camy_", "phys_")) for n in gnames):
            check(False, "skin d'objet : cam_, camy_ et phys_ ne sont pas annoncés pour les objets (guide 14 : canaux, Molang, ctrl_, "
                  "_e, add_, trans_)", warn=True)
        obj = (fiche_mod.bloc(m, creer=False) or {}).get("objet", {})
        aff = obj.get("affichage") if isinstance(obj.get("affichage"), dict) else m.get("display")
        if aff is None:
            check(False, "skin d'objet : pas de réglages Display (phynaria.objet.affichage ou display) : tenu comme item/handheld, "
                  "objet en diagonale pointe en haut à droite (guide 14)", warn=True)
        else:
            e_a, a_a = objet_mod.valider_affichage(aff)
            for t in a_a:
                check(False, t, warn=True)
            check(not e_a, "réglages Display : " + ("; ".join(e_a) if e_a else f"{len(aff)} contextes valides"))
        # java_block : depuis le guide du 2026-11-06 (soir, section 9), textures gardées à leur taille (512 au plus), _e et _r gardés
        P0, _ = rb.load_model(a.path)
        P0 = np.array([p for q in P0 for p in q[0]])
        if len(P0):
            lo, hi = P0.min(0), P0.max(0)
            print(f"[INFO] skin d'objet : boîte {np.round(lo, 1).tolist()} → {np.round(hi, 1).tolist()} (bloc 0..16 ; jusqu'à 64 px accepté)")
    # fonctions avancées (guide 4 bis, 5 quater, 6.4, 6.5) : le renderer simule add_ et trans_, pas le reste
    avance = sorted({p for n in gnames for p in ("add_", "trans_", "cam_", "camy_", "ctrl_", "phys_", "emit_mc_") if n.startswith(p)}
                    | {p for an in m.get("animations", []) for p in ("overlay_", "event_") if an.get("name", "").split(".")[-1].startswith(p)})
    if avance:
        print(f"[INFO] fonctions avancées : {', '.join(avance)} (aperçu : add_, trans_, cam_ et camy_ simulés ; le reste se juge avec /cosmetique apercu)")
    over_rot = [x.get("name", "?") for x in els + gnodes if any(abs(v) > LIMITS["rotation"] for v in x.get("rotation", [0, 0, 0]))]
    check(not over_rot, f"rotations de base ≤ ±{LIMITS['rotation']:.0f}° : {len(over_rot)} hors limite" + (f" ({', '.join(over_rot[:5])}…)" if over_rot else ""))
    bad_face = [e["name"] for e in els if any(fd.get("rotation", 0) % 90 for fd in e["faces"].values())]
    check(not bad_face, f"rotations de face multiples de 90° : {len(bad_face)} hors règle" + (f" ({', '.join(bad_face[:5])}…)" if bad_face else ""))
    over_inf = [e["name"] for e in els if abs(e.get("inflate", 0)) > LIMITS["inflate"]]
    check(not over_inf, f"inflate ≤ ±{LIMITS['inflate']:.0f} : {len(over_inf)} hors limite" + (f" ({', '.join(over_inf[:5])}…)" if over_inf else ""))
    thin = [e["name"] for e in els if any(abs(e["to"][i] - e["from"][i]) < 1e-6 for i in range(3))]
    check(not thin, f"épaisseur nulle : {len(thin)} élément(s)" + (f" ({', '.join(thin[:5])}…)" if thin else ""))
    # skin d'objet : deux étapes (groupes racine repos, bande_1…) ne sont jamais dessinées ensemble -> doublons comptés par étape
    etape_de = {}
    if objet is not None:
        import objet as objet_mod

        def _uuids(n):
            return [c for c in n.get("children", []) if isinstance(c, str)] + [u for c in n.get("children", []) if isinstance(c, dict) for u in _uuids(c)]
        for n in m.get("outliner", []):
            if isinstance(n, dict) and objet_mod.normal(n.get("name", "")) in objet_mod.etapes_connues():
                for u in _uuids(n):
                    etape_de[u] = objet_mod.normal(n["name"])
    dup = 0
    for et in sorted(set(etape_de.values())) or [None]:
        cnt = collections.Counter((tuple(e["from"]), tuple(e["to"]), tuple(e.get("rotation", [0, 0, 0]))) for e in els
                                  if etape_de.get(e.get("uuid")) in (None, et))
        dup = max(dup, sum(v - 1 for v in cnt.values() if v > 1))
    check(dup == 0, f"éléments strictement superposés : {dup}")
    for e in els:
        for f, fd in e["faces"].items():
            if fd.get("texture") is not None and len(fd["uv"]) == 4 and (fd["uv"][0] == fd["uv"][2] or fd["uv"][1] == fd["uv"][3]):
                check(False, f"UV dégénérée sur {e['name']}.{f}", warn=True); break
    # animations
    anims = m.get("animations", [])
    check(len(anims) <= LIMITS["anims"], f"{len(anims)} animations (≤ {LIMITS['anims']})")
    nk = sum(len(b["keyframes"]) for an in anims for b in an["animators"].values())
    check(nk <= LIMITS["keyframes"], f"{nk} keyframes (≤ {LIMITS['keyframes']})")
    bad_ch = collections.Counter(k["channel"] for an in anims for b in an["animators"].values() for k in b["keyframes"]
                                 if k["channel"] not in ("rotation", "position", "scale") and not (k["channel"] == "sound" and b.get("type") == "effect"))
    check(not bad_ch, f"canaux non supportés par le mod : {dict(bad_ch) or 'aucun'}")
    sons = [(an["name"], sum(1 for b in an["animators"].values() for k in b["keyframes"] if k["channel"] == "sound")) for an in anims]
    trop = [n for n, c in sons if c > LIMITS["sons"]]
    check(not trop, f"sons ≤ {LIMITS['sons']} par animation" + (f" : {trop}" if trop else ""))
    # sons embarqués (phynaria_sounds, relevé dans le mod 1.4.0 ; tools/sons.py) et noms des clés de son
    from sons import controler_sons
    s_err, s_alt, s_inf = controler_sons(m)
    for t in s_inf:
        print("[INFO]", t)
    for t in s_err:
        check(False, t)
    for t in s_alt:
        check(False, t, warn=True)
    if m.get("phynaria_sounds") and not s_err:
        check(True, f"{len(m['phynaria_sounds'])} son(s) embarqué(s) : OGG Vorbis mono, ≤ 100 Ko, ≤ 5 s, noms valides, ≤ 8")
    names = [an["name"] for an in anims]
    short = {n.split(".")[-1] for n in names}
    if objet:
        attendues = ()
        # guide 14 : noms joués sur un objet (dernière partie du nom)
        hors_o = sorted(n for n in short if not (n in ANIMS_OBJET or n.startswith(("overlay_", "particle_"))
                                                 or (n.startswith("event_") and (n[6:] in EVENTS_OBJET or n.startswith("event_enter_")))))
        if hors_o and short & (ANIMS_OBJET | {f"event_{e}" for e in EVENTS_OBJET}):
            check(False, f"skin d'objet : animations au nom non reconnu (guide 14 : item_idle, item_use, item_swing, item_ground, "
                  f"item_gui, event_swing/hit/break/use_start/use_stop/select/release/charged, event_enter_<étape>, overlay_) : {hors_o}", warn=True)
        elif hors_o:
            print(f"[INFO] skin d'objet sans animation item_ ni event_ d'objet : il joue son animation à lui en main et au sol (guide 14) : {hors_o}")
        import objet as objet_mod
        mauvais = [n for n in short if n.startswith("event_enter_")
                   and objet_mod.normal(n[len("event_enter_"):]) not in fiche_mod.OBJETS[objet]]
        if mauvais:
            check(False, f"skin d'objet ({objet}) : {mauvais} ne nomment pas une étape de ce type {list(fiche_mod.OBJETS[objet])}", warn=True)
    elif effet:
        attendues = ()
        mots_effet = {rb.mot_anim(n) for n in names}
        for need in ("depart", "arrivee"):
            check(need in mots_effet, f"effet : animation '{need}' présente (guide 15)", warn=True)
    elif mode_pet:
        attendues = ("pet_idle", "pet_walk", "pet_sit") + (("pet_fly",) if mode_pet in ("vol", "perche") else ()) + (("pet_swim",) if mode_pet == "nage" else ())
    else:
        attendues = ("idle", "fly", "glide", "run", "sneak")
    for need in attendues:
        check(need in short, f"animation '{need}' présente", warn=True)
    # noms joués : états (6.2, ou 6.6 pour un familier vivant), overlay_, event_ connus, particle_<sorte>_fall/_rest
    etats_ok, events_ok = (ETATS_PET, EVENTS_PET) if mode_pet else (ETATS_PORTE, EVENTS_PORTE)
    inconnus = sorted(n for n in short if not (n in etats_ok or n.startswith(("overlay_", "particle_"))
                                               or (n.startswith("event_") and n[len("event_"):] in events_ok)))
    if effet:
        # guide 15 : charge (loop), depart et arrivee (once, 5 s au plus), overlay_ ; les états et événements du joueur ne sont pas joués
        hors = sorted(n for n in short if rb.mot_anim(n) not in ANIMS_EFFET and not n.startswith(("overlay_", "particle_")))
        du_joueur = [n for n in hors if n in ETATS_PORTE or n.startswith("event_")]
        if hors:
            check(False, f"effet : animations non jouées (guide 15 : charge, depart, arrivee, overlay_) : {hors}"
                  + (f" — {du_joueur} sont des états ou événements d'un cosmétique porté" if du_joueur else ""), warn=True)
        for an in anims:
            mot = rb.mot_anim(an["name"])
            if mot in ANIMS_EFFET:
                if ANIMS_EFFET[mot] == "once":
                    check(float(an["length"]) <= EFFET_MAX_S, f"effet : '{an['name']}' dure {float(an['length']):g} s (≤ {EFFET_MAX_S:g} s, guide 15)")
                if an.get("loop", "once") != ANIMS_EFFET[mot]:
                    check(False, f"effet : '{an['name']}' en {an.get('loop', 'once')} (attendu {ANIMS_EFFET[mot]}, guide 15)", warn=True)
        inconnus = []
    if inconnus and not objet:
        check(False, f"animations au nom non reconnu ({'familier vivant, guide 6.6' if mode_pet else 'guide 6.2 et 6.4'}) : {inconnus} — "
              "non jouées d'office (un nom d'état libre seulement si le staff le choisit, un event_ inconnu jamais)", warn=True)
    if mode_pet and short & {"attack", "hurt"}:
        check(False, "familier vivant : attack et hurt ne sont pas des états du familier ; event_owner_hurt quand son maître prend un coup (guide 6.6)", warn=True)
    check(all(len(n) <= 64 for n in names), "noms d'animation ≤ 64 caractères")
    too_long = [an["name"] for an in anims if float(an["length"]) > LIMITS["anim_length"]]
    check(not too_long, f"durée des animations ≤ {LIMITS['anim_length']:.0f} s" + (f" : {', '.join(too_long)}" if too_long else ""))
    exprs = [v for an in anims for b in an["animators"].values() if b.get("type") != "effect" for k in b["keyframes"] for dp in k.get("data_points", []) for v in dp.values() if isinstance(v, str)]
    longest = max(map(len, exprs), default=0)
    check(longest <= LIMITS["molang"], f"expression Molang la plus longue : {longest} caractères (≤ {LIMITS['molang']})")
    import re as _re
    vues = {x for e in exprs for x in _re.findall(r"\b(?:q|query)\.([a-z_][a-z0-9_]*)", e.lower())}
    inconnues = sorted(vues - REQUETES)
    if inconnues:
        check(False, f"requêtes Molang inconnues du guide (valent 0 en jeu) : {inconnues}", warn=True)
    if not objet and vues & REQUETES_OBJET:
        check(False, f"requêtes de skin d'objet {sorted(vues & REQUETES_OBJET)} hors d'un skin d'objet (valent 0, guide 14)", warn=True)
    if "hit_by_entity" in vues:
        print("[INFO] q.hit_by_entity : nouvelle requête (guide 6.3, 2026-11-06 soir), pas encore vérifiée en jeu ; aperçu : 0, "
              "MOLANG_QUERY=hit_by_entity=1 pour la simuler")
    # clés position (≤ 320 px par axe) et scale (≤ 16 fois) : valeurs numériques ; une expression se juge en jeu
    cles_hors, cles_expr = [], 0
    for an in anims:
        for b in an["animators"].values():
            for k in b.get("keyframes", []):
                lim_k = {"position": LIMITS["cle_position"], "scale": LIMITS["cle_scale"]}.get(k.get("channel"))
                if lim_k is None:
                    continue
                for dp in k.get("data_points", []):
                    for ax in ("x", "y", "z"):
                        v = dp.get(ax)
                        if v is None or (isinstance(v, str) and not v.strip()):
                            continue
                        try:
                            f = float(v)
                        except (TypeError, ValueError):
                            cles_expr += 1
                            continue
                        if abs(f) > lim_k:
                            cles_hors.append(f"{an['name']}/{b.get('name', '?')}.{k['channel']}.{ax}={f:g}")
    check(not cles_hors, f"clés position ≤ {LIMITS['cle_position']:.0f} px et scale ≤ {LIMITS['cle_scale']:.0f} fois (guide 3 et 7)"
          + (f" : {len(cles_hors)} hors limite ({', '.join(cles_hors[:4])}…)" if cles_hors else "")
          + (f" ; {cles_expr} valeur(s) en Molang non mesurées" if cles_expr else ""))
    # échelles superposées : événements qui jouent ensemble (guide 6.4 et 14), échelles multipliées
    sup = echelles_superposees(m, objet)
    for g_nom, ens, cumul, base, part in sup[:6]:
        check(False, f"échelles superposées ({ens}) : '{g_nom}' ×{cumul:.3g} quand {' + '.join(f'{a_}(×{v:.3g})' for a_, v in part)} "
              f"jouent ensemble, contre ×{base:.3g} avec l'état et un seul événement — ne déplier (scale) un groupe que dans une "
              "animation à la fois (fonctions-avancees.md, Pièges ; borne haute : pics multipliés)", warn=True)
    if len(sup) > 6:
        print(f"[INFO] … et {len(sup) - 6} autre(s) groupe(s) aux échelles superposées")
    # boucles et extension animée (renderer en convention mod ; l'extension animée n'est plus limitée par le mod)
    ext = 0.0; ext_where = None
    for an in anims:
        L = float(an["length"])
        if an.get("loop") == "loop":
            qa, _ = rb.load_model(a.path, anim_time=0.0, anim_name=an["name"])
            qb, _ = rb.load_model(a.path, anim_time=L - 1e-6, anim_name=an["name"])
            pa = np.array([p for q in qa for p in q[0]]); pb = np.array([p for q in qb for p in q[0]])
            # faces cachées par ctrl_alpha (ramenées à l'origine) à l'un des deux instants : hors comparaison
            vis = ~((np.abs(pa).max(axis=1) < 1e-9) | (np.abs(pb).max(axis=1) < 1e-9)) if len(pa) else np.zeros(0, bool)
            gap = float(np.abs(pa[vis] - pb[vis]).max()) if vis.any() else 0.0
            check(gap < 0.05, f"boucle '{an['name']}' fermée (écart {gap:.3f} px)")
        for t in np.linspace(0, L, 9):
            q, _ = rb.load_model(a.path, anim_time=float(t), anim_name=an["name"])
            P = np.array([p for qq in q for p in qq[0]])
            if not len(P): continue
            e = max(abs(P[:, 0]).max(), abs(P[:, 2]).max(), P[:, 1].max(), -P[:, 1].min())
            if e > ext: ext, ext_where = e, (an["name"], round(float(t), 2))
    # zone autorisée (guide 3 et 7) : modèle au repos (aucune animation), cubes et pivots, limite selon la catégorie
    lim = a.max_ext if a.max_ext is not None else limite_extension(effet, objet)
    q, _ = rb.load_model(a.path)
    P = np.array([p for qq in q for p in qq[0]])
    rep_ext, rep_ou = extension_repos(m, P)
    genre = "effet de téléportation" if effet else ("skin d'objet" if objet else "cosmétique porté ou familier")
    check(rep_ext <= lim, f"au repos : {rep_ext:.1f} px de l'origine ({rep_ou}) (≤ {lim:g}, {genre} ; guide 3)")
    if lim - 4 <= rep_ext <= lim:
        check(False, f"au repos : {rep_ext:.1f} px, peu de marge sous {lim:g}", warn=True)
    if anims:
        print(f"[INFO] extension animée max {ext:.1f} px dans {ext_where} (plus limitée par le mod : un grand modèle reste dessiné "
              "tant qu'une partie peut être à l'écran)")
    # règles par catégorie, déduite du chemin cosmetiques/<categorie>/<nom>/...
    cat = categorie(a.path)
    if cat in REACTIONS_INTERDITES:
        interdites = sorted(REACTIONS_INTERDITES[cat] & short)
        check(not interdites, f"réactions {'/'.join(sorted(REACTIONS_INTERDITES[cat]))} absentes ({cat}) : "
              + (f"{interdites} présentes — un équipement ne réagit pas aux coups (.claude/rules/animation.md, « Attaque et blessé »)" if interdites else "aucune"))
    if cat == "ailes":
        pire = ailes_croisees(a.path, anims)
        if pire is None:
            print("[INFO] ailes de leur côté de la colonne : aucune pose de repos à tester")
        else:
            for z, tol, warn in (("aile", CROISE_TOL, False), ("racine", RACINE_TOL, True)):
                d, an_name, t, nom = pire[z]
                check(d <= tol, f"ailes de leur côté de la colonne au repos ({z}, centres à |x| {'≥' if z == 'aile' else '<'} {RACINE:g} px) : "
                      f"dépassement max {max(d, 0):.2f} px (≤ {tol:g})"
                      + (f" — '{nom}' traverse dans '{an_name}' à t={t:.2f} s ; les ailes ne se croisent jamais (.claude/rules/categories/ailes.md, ailes_orage v4)" if d > tol else ""),
                      warn=warn)
    # poids
    comp = len(zlib.compress(raw, 9)) // 1024
    print(f"[INFO] poids brut {len(raw) // 1024} Ko | compressé {comp} Ko | texture {len(texs[0]['source']) // 1024 if texs else 0} Ko")
    check(comp < LIMITS["compressed_kb"], f"compressé {comp} Ko (< {LIMITS['compressed_kb']})")
    check(len(raw) <= LIMITS["import_mb"] * 1024 * 1024, f"fichier importé ≤ {LIMITS['import_mb']} Mo")
    check(len(raw) <= LIMITS["stored_mb"] * 1024 * 1024, f"brut ≤ {LIMITS['stored_mb']} Mo (limite stockée ; taille nettoyée par le serveur non mesurable ici)", warn=True)
    if a.strict: check(len(raw) < 1_000_000, "brut < 1 Mo (strict)", warn=True)
    print("\nRÉSULTAT :", "OK — livrable" if ok else "ÉCHEC — ne pas livrer")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
