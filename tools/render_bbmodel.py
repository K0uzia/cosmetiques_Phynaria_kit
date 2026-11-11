"""Rendu logiciel (numpy) d'un .bbmodel cubes-only + mannequin joueur, pour aperçu."""
import sys, json, base64, io, math, os, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def rot_matrix(rx, ry, rz):
    """Rotation Euler Blockbench (ordre ZYX appliqué : X puis Y puis Z)."""
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

FACE_CORNERS = {
    # (TL, TR, BR, BL) en fonction de (x0,y0,z0,x1,y1,z1)
    "north": lambda a, b: [(b[0], b[1], a[2]), (a[0], b[1], a[2]), (a[0], a[1], a[2]), (b[0], a[1], a[2])],
    "south": lambda a, b: [(a[0], b[1], b[2]), (b[0], b[1], b[2]), (b[0], a[1], b[2]), (a[0], a[1], b[2])],
    "east":  lambda a, b: [(b[0], b[1], b[2]), (b[0], b[1], a[2]), (b[0], a[1], a[2]), (b[0], a[1], b[2])],
    "west":  lambda a, b: [(a[0], b[1], a[2]), (a[0], b[1], b[2]), (a[0], a[1], b[2]), (a[0], a[1], a[2])],
    "up":    lambda a, b: [(a[0], b[1], a[2]), (b[0], b[1], a[2]), (b[0], b[1], b[2]), (a[0], b[1], b[2])],
    "down":  lambda a, b: [(a[0], a[1], b[2]), (b[0], a[1], b[2]), (b[0], a[1], a[2]), (a[0], a[1], a[2])],
}

# ---------------------------------------------------------------- Molang du guide (section 6.3)
# Analyseur écrit à la main, le même que molang() de tools/visionneuse.js (mêmes règles, même ordre de calcul).
# Priorités, de la plus faible à la plus forte :
#   ?: (à droite ; « a ? b » sans « : » vaut 0 si faux)  ||  &&  == !=  < <= > >=  + -  * /  - ! + (unaires)
# Vrai = 1, faux = 0 ; « 1--0.5 » = 1 − (−0,5). Instructions « ; », « v.x = … » (mémorisée), « t.x = … » (temporaire),
# « return ». Noms insensibles à la casse ; query./variable./temp./context. = q./v./t./c. ; requête inconnue = 0.
# Expression invalide (syntaxe, fonction inconnue, nombre d'arguments) ou résultat non fini : valeur neutre du canal
# (0, ou 1 pour l'échelle), comme le mod (guide 6.3).

def _m_sur(f):
    """Fonction mathématique sans exception : NaN ou ±inf comme en JavaScript."""
    def g(*a):
        try:
            return float(f(*a))
        except OverflowError:
            return math.inf
        except (ValueError, ZeroDivisionError):
            return math.nan
    return g


def _m_entier(f):
    return lambda v: float(f(v)) if math.isfinite(v) else v


def _m_nan(*a):
    return any(x != x for x in a)


# nom -> (nombre d'arguments, fonction). Mêmes définitions que FONCTIONS dans visionneuse.js.
# math.random et math.random_integer : l'aperçu prend le milieu, pour une image stable (en jeu : nouveau tirage à chaque image).
_MOLANG_FONCTIONS = {
    "sin": (1, _m_sur(lambda d: math.sin(d * math.pi / 180))),
    "cos": (1, _m_sur(lambda d: math.cos(d * math.pi / 180))),
    "abs": (1, abs),
    "sqrt": (1, _m_sur(math.sqrt)),
    "floor": (1, _m_entier(math.floor)),
    "ceil": (1, _m_entier(math.ceil)),
    "round": (1, lambda v: _m_entier(math.floor)(v + 0.5)),
    "trunc": (1, _m_entier(math.trunc)),
    "exp": (1, _m_sur(math.exp)),
    "atan": (1, lambda v: math.atan(v) * 180 / math.pi),
    "min": (2, lambda a, b: math.nan if _m_nan(a, b) else min(a, b)),
    "max": (2, lambda a, b: math.nan if _m_nan(a, b) else max(a, b)),
    "mod": (2, _m_sur(math.fmod)),
    "pow": (2, _m_sur(math.pow)),
    "atan2": (2, lambda y, x: math.atan2(y, x) * 180 / math.pi),
    "random": (2, lambda a, b: (a + b) / 2),
    "random_integer": (2, lambda a, b: _m_entier(math.floor)((a + b) / 2)),
    "clamp": (3, lambda v, a, b: math.nan if _m_nan(v, a, b) else max(a, min(b, v))),
    "lerp": (3, lambda a, b, k: a + (b - a) * k),
}
_MOLANG_ESPACES = {"q": "q", "query": "q", "v": "v", "variable": "v", "t": "t", "temp": "t", "c": "c", "context": "c"}
_MOLANG_JETON = re.compile(r"\s*(?:(\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?)|([A-Za-z_][A-Za-z0-9_.]*)|(&&|\|\||==|!=|<=|>=|[-+*/!?:<>(),;=]))")
_MOLANG_NIVEAUX = (("||",), ("&&",), ("==", "!="), ("<", "<=", ">", ">="), ("+", "-"), ("*", "/"))


class MolangErreur(Exception):
    pass


def molang_analyser(src):
    """Texte -> programme : liste d'instructions ["set", espace, nom, expr] | ["ret", expr] | ["expr", expr].
    Nœuds : ["n", x] ["q"|"v"|"t", nom] ["f", nom, [args]] ["-"|"!", a] ["op", o, a, b] ["?", c, a, b|None]."""
    jetons, i, s = [], 0, str(src)
    while True:
        m = _MOLANG_JETON.match(s, i)
        if not m:
            if s[i:].strip():
                raise MolangErreur(f"caractère inattendu : {s[i:i + 8]!r}")
            break
        if m.group(1) is not None:
            jetons.append(("n", float(m.group(1))))
        elif m.group(2) is not None:
            jetons.append(("id", m.group(2).lower()))
        else:
            jetons.append(("op", m.group(3)))
        i = m.end()
    jetons.append(("fin", None))
    pos = 0

    def est(o):
        return jetons[pos] == ("op", o)

    def prendre(o):
        nonlocal pos
        if not est(o):
            raise MolangErreur(f"« {o} » attendu")
        pos += 1

    def ternaire():
        nonlocal pos
        c = binaire(0)
        if not est("?"):
            return c
        pos += 1
        a, b = ternaire(), None
        if est(":"):
            pos += 1
            b = ternaire()
        return ["?", c, a, b]

    def binaire(niv):
        nonlocal pos
        if niv == len(_MOLANG_NIVEAUX):
            return unaire()
        a = binaire(niv + 1)
        while jetons[pos][0] == "op" and jetons[pos][1] in _MOLANG_NIVEAUX[niv]:
            o = jetons[pos][1]
            pos += 1
            a = ["op", o, a, binaire(niv + 1)]
        return a

    def unaire():
        nonlocal pos
        if est("-") or est("!") or est("+"):
            o = jetons[pos][1]
            pos += 1
            a = unaire()
            return a if o == "+" else [o, a]
        return primaire()

    def primaire():
        nonlocal pos
        genre, x = jetons[pos]
        if genre == "n":
            pos += 1
            return ["n", x]
        if est("("):
            pos += 1
            a = ternaire()
            prendre(")")
            return a
        if genre != "id":
            raise MolangErreur("valeur attendue")
        pos += 1
        if x in ("true", "false"):
            return ["n", 1.0 if x == "true" else 0.0]
        esp, _, nom = x.partition(".")
        if esp == "math":
            if nom == "pi":
                return ["n", math.pi]
            if nom not in _MOLANG_FONCTIONS:
                raise MolangErreur(f"fonction inconnue : {x}")
            prendre("(")
            args = []
            if not est(")"):
                args.append(ternaire())
                while est(","):
                    pos += 1
                    args.append(ternaire())
            prendre(")")
            if len(args) != _MOLANG_FONCTIONS[nom][0]:
                raise MolangErreur(f"{x} : {len(args)} argument(s)")
            return ["f", nom, args]
        if esp in _MOLANG_ESPACES and nom and "." not in nom:
            e = _MOLANG_ESPACES[esp]
            return ["n", 0.0] if e == "c" else [e, nom]
        raise MolangErreur(f"nom inconnu : {x}")

    prog = []
    while jetons[pos][0] != "fin":
        if est(";"):
            pos += 1
            continue
        genre, x = jetons[pos]
        if (genre, x) == ("id", "return"):
            pos += 1
            prog.append(["ret", ternaire()])
        elif genre == "id" and jetons[pos + 1] == ("op", "="):
            esp, _, nom = x.partition(".")
            e = _MOLANG_ESPACES.get(esp)
            if e not in ("v", "t") or not nom or "." in nom:
                raise MolangErreur(f"affectation impossible : {x}")
            pos += 2
            prog.append(["set", e, nom, ternaire()])
        else:
            prog.append(["expr", ternaire()])
        if jetons[pos][0] != "fin":
            prendre(";")
    if not prog:
        raise MolangErreur("expression vide")
    return prog


def _molang_eval(n, q, v, tmp):
    k = n[0]
    if k == "n":
        return n[1]
    if k == "q":
        x = q.get(n[1], 0.0)
        return float(x) if isinstance(x, (int, float)) else 0.0
    if k == "v":
        return v.get(n[1], 0.0)
    if k == "t":
        return tmp.get(n[1], 0.0)
    if k == "f":
        return _MOLANG_FONCTIONS[n[1]][1](*[_molang_eval(a, q, v, tmp) for a in n[2]])
    if k == "-":
        return -_molang_eval(n[1], q, v, tmp)
    if k == "!":
        return 1.0 if _molang_eval(n[1], q, v, tmp) == 0 else 0.0
    if k == "?":
        if _molang_eval(n[1], q, v, tmp) != 0:
            return _molang_eval(n[2], q, v, tmp)
        return _molang_eval(n[3], q, v, tmp) if n[3] is not None else 0.0
    o = n[1]
    a = _molang_eval(n[2], q, v, tmp)
    if o == "&&":
        return 1.0 if a != 0 and _molang_eval(n[3], q, v, tmp) != 0 else 0.0
    if o == "||":
        return 1.0 if a != 0 or _molang_eval(n[3], q, v, tmp) != 0 else 0.0
    b = _molang_eval(n[3], q, v, tmp)
    if o == "+": return a + b
    if o == "-": return a - b
    if o == "*": return a * b
    if o == "/":
        if b == 0:   # comme en JavaScript : ±inf, ou NaN pour 0/0
            return math.nan if a == 0 or a != a else math.copysign(math.inf, a) * math.copysign(1.0, b)
        return a / b
    if o == "<": return 1.0 if a < b else 0.0
    if o == "<=": return 1.0 if a <= b else 0.0
    if o == ">": return 1.0 if a > b else 0.0
    if o == ">=": return 1.0 if a >= b else 0.0
    if o == "==": return 1.0 if a == b else 0.0
    return 1.0 if a != b else 0.0      # !=


def _molang_lit_v(n):
    """Le nœud lit-il une variable mémorisée ?"""
    return isinstance(n, list) and (n[0] == "v" or any(isinstance(x, list) and _molang_lit_v(x) for x in n))


def _molang_image(prog, q, v):
    """Une image : valeur de la dernière instruction, ou du premier « return »."""
    tmp, val = {}, 0.0
    for ins in prog:
        if ins[0] == "set":
            val = _molang_eval(ins[3], q, v, tmp)
            (v if ins[1] == "v" else tmp)[ins[2]] = val
        else:
            val = _molang_eval(ins[1], q, v, tmp)
            if ins[0] == "ret":
                break
    return val


_MOLANG_CACHE = {}


def molang_programme(expr):
    """(programme, avec mémoire ?) mis en cache, ou None si l'expression est invalide."""
    if expr not in _MOLANG_CACHE:
        try:
            prog = molang_analyser(expr)
            memo = len(prog) > 1 or any(i[0] == "set" and i[1] == "v" or _molang_lit_v(i[-1]) for i in prog)
            _MOLANG_CACHE[expr] = (prog, memo)
        except (MolangErreur, RecursionError):
            _MOLANG_CACHE[expr] = None
    return _MOLANG_CACHE[expr]


_NOMBRE = re.compile(r"\s*[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?\s*")


def molang_requetes(t):
    """Requêtes de l'aperçu. Simuler un état : MOLANG_QUERY="ground_speed=33,vertical_speed=0,is_gliding=1".
    Inconnue = 0, comme le mod ; q.delta_time = 0,05 s (une image à 20 images/s) sauf si MOLANG_QUERY le donne."""
    q = {"anim_time": float(t), "life_time": float(t), "delta_time": 0.05}
    q.update(_REQ_FAMILIER)   # familier vivant (FAMILIER=vivant / menu) : requêtes de son état, posées par load_model()
    for kv in filter(None, os.environ.get("MOLANG_QUERY", "").split(",")):
        k, v = kv.split("=")
        q[k.strip().lower()] = float(v)
    return q


def molang(expr, t, neutre=0.0):
    """Valeur d'une clé (guide 6.3) à l'instant t. Variables mémorisées v.… : l'aperçu n'a pas d'image précédente,
    on calcule l'état stable (80 images de 0,05 s au même instant), comme après quelques secondes en jeu
    (même règle que visionneuse.js). Expression invalide ou résultat non fini : neutre (0, ou 1 pour l'échelle)."""
    if isinstance(expr, (int, float)):
        return float(expr)
    s = str(expr)
    if _NOMBRE.fullmatch(s):
        return float(s)
    p = molang_programme(s)
    if p is None:
        return neutre
    prog, memo = p
    q, v, val = molang_requetes(t), {}, 0.0
    for _ in range(80 if memo else 1):
        val = _molang_image(prog, q, v)
    return val if math.isfinite(val) else neutre

def sample(keyframes, channel, t, default):
    kfs = sorted([k for k in keyframes if k["channel"] == channel], key=lambda k: k["time"])
    if not kfs:
        return np.array(default, float)
    neutre = 1.0 if channel == "scale" else 0.0
    def val(k): return np.array([molang(k["data_points"][0].get(a, neutre), t, neutre) for a in "xyz"])
    if t <= kfs[0]["time"]: return val(kfs[0])
    if t >= kfs[-1]["time"]: return val(kfs[-1])
    for a, b in zip(kfs, kfs[1:]):
        if a["time"] <= t <= b["time"]:
            f = (t - a["time"]) / max(1e-9, b["time"] - a["time"])
            return val(a) * (1 - f) + val(b) * f
    return val(kfs[-1])

# ---------------------------------------------------------------- pose du joueur selon l'état
# Groupes de premier niveau qui suivent une partie du corps (guide, section 4) ; tout le reste suit le torse.
PARTIES = {"head": "head", "hat": "head", "helmet": "head", "body": "body", "torso": "body", "chest": "body",
           "rightarm": "right_arm", "armright": "right_arm", "leftarm": "left_arm", "armleft": "left_arm",
           "rightleg": "right_leg", "legright": "right_leg", "leftleg": "left_leg", "legleft": "left_leg"}
# Articulations du joueur (guide, section 4).
PIVOTS = {"head": (0, 24, 0), "body": (0, 24, 0), "right_arm": (5, 22, 0), "left_arm": (-5, 22, 0),
          "right_leg": (2, 12, 0), "left_leg": (-2, 12, 0)}
CENTRE = np.array([0.0, 16.0, 0.0])   # pivot du corps entier quand il est couché


def partie_de(nom):
    n = "".join(c for c in nom.lower() if c.isalnum())
    return PARTIES.get(n, "body")


def etat_de(anim_name):
    """Dernière partie du nom d'animation, ramenée à un état du guide (section 6.2)."""
    if not anim_name:
        return "idle"
    mot = anim_name.split(".")[-1].lower()
    if mot.startswith(("overlay_", "event_", "pet_")):
        # couches et événements (guide 6.4) : jamais un état ; « engrenages » contient « nage ». pet_ : états du familier
        # vivant (guide 6.6), pas du joueur : mannequin debout, familier montré à l'origine sans la pose du joueur
        return "idle"
    for etat, mots in (("glide", ("glide", "elytra", "plane")), ("swim", ("swim", "nage")), ("sleep", ("sleep", "dort", "dodo")),
                       ("mount", ("ride", "mount", "monture")), ("sneak", ("sneak", "crouch", "accroupi")),
                       ("run", ("sprint", "run", "cours", "course")), ("walk", ("walk", "marche"))):
        if any(m in mot for m in mots):
            return etat
    return "idle"


# ---------------------------------------------------------------- familier vivant (guide 6.6)
# Aperçu d'un familier vivant (FAMILIER=vivant) : posé au sol à côté du joueur immobile, q.is_pet = 1 et les requêtes
# de son état (vitesse, assis, dans l'eau…). FAMILIER=menu : porté, q.is_pet = 0, q.is_in_menu = 1 (le menu Apparence
# le montre porté). Sans FAMILIER : porté à l'origine, comme avant (vérificateur). Mêmes calculs dans visionneuse.js.
FAMILIER_MODES = ("sol", "vol", "nage", "perche")
ETATS_PET = (("idle", ("idle", "repos", "immobile")), ("walk", ("walk", "marche")), ("run", ("run", "sprint", "cours", "course")),
             ("sit", ("sit", "assis", "perch")), ("sleep", ("sleep", "dort", "dodo")), ("swim", ("swim", "nage")),
             ("fly", ("fly", "vol", "flap")), ("fall", ("fall", "chute")), ("jump", ("jump", "saut")), ("land", ("land", "atterri")))
PLACE_MAX = 1.5   # blocs : distance d'aperçu (en jeu, il s'arrête à `distance` blocs)
_REQ_FAMILIER = {}


def familier_de(m):
    """Bloc phynaria.familier d'un familier vivant (mode sol, vol, nage, perche), sinon None."""
    b = ((m.get("unhandled_root_fields") or {}).get("phynaria") or {}).get("familier")
    return b if isinstance(b, dict) and b.get("mode") in FAMILIER_MODES else None


def etat_pet(anim_name):
    """État du familier (guide 6.6, table 3) d'après la dernière partie du nom, préfixe pet_ facultatif ; sinon idle."""
    mot = (anim_name or "").split(".")[-1].lower()
    mot = mot[4:] if mot.startswith("pet_") else mot
    return next((e for e, mots in ETATS_PET if mot in mots), "idle")


def _nombre(v, defaut):
    try:
        return float(v)
    except (TypeError, ValueError):
        return defaut


def place_familier(bloc, etat):
    """Origine du familier dans le repère du joueur (px) : à sa gauche (−X), un peu devant ; perché sur l'épaule gauche
    (1,42 bloc) au repos, assis ou endormi ; en vol à `hauteur` blocs au-dessus des pieds, près de l'épaule."""
    mode, h = bloc["mode"], _nombre(bloc.get("hauteur"), 1.8) * 16
    if mode == "perche" and etat in ("idle", "sit", "sleep"):
        return (-6.0, 1.42 * 16, 0.0)
    if mode in ("vol", "perche") and etat not in ("swim",):
        return (-16.0, h, 2.0)
    d = min(_nombre(bloc.get("distance"), 3), PLACE_MAX) * 16
    return (-d, 0.0, -4.0)


def requetes_familier(bloc, etat):
    """Requêtes Molang d'un familier vivant dans un état (guide 6.6, 4) : sa vitesse (marche du joueur 4,3 blocs/s,
    × `vitesse`), au sol ou non, assis, dans l'eau ; maître à `distance` blocs, en pleine vie, immobile."""
    v, d = _nombre(bloc.get("vitesse"), 1), _nombre(bloc.get("distance"), 3)
    q = {"is_pet": 1, "is_on_ground": 1, "owner_distance": d, "owner_health": 20, "owner_max_health": 20,
         "is_perched": 1 if bloc["mode"] == "perche" and etat in ("idle", "sit", "sleep") else 0}
    q.update({"walk": {"ground_speed": 4.3 * v, "owner_distance": d + 1},
              "run": {"ground_speed": 6.5 * v, "owner_distance": d + 5},
              "sit": {"is_sitting": 1}, "sleep": {"is_sleeping": 1},
              "swim": {"ground_speed": 2.5 * v, "is_swimming": 1, "is_in_water": 1, "is_on_ground": 0},
              "fly": {"ground_speed": 4.3 * v, "is_flying": 1, "is_on_ground": 0},
              "fall": {"vertical_speed": -10, "is_on_ground": 0},
              "jump": {"ground_speed": 2, "vertical_speed": 6, "is_on_ground": 0},
              "land": {"land_speed": 6}}.get(etat, {}))
    return q


def pose_joueur(etat, t=0.0, duree=1.0):
    """Transformations du mannequin, à la manière du jeu vanilla (approchées) : partie -> fonction point -> point.
    Couché en élytres et en nage (face vers le sol), sur le dos en sommeil, assis en monture, penché accroupi,
    bras et jambes qui balancent en marche et en course. Les autres états : debout."""
    rot = {k: np.zeros(3) for k in PIVOTS}
    dep = {k: np.zeros(3) for k in PIVOTS}
    G = np.eye(3)
    if etat in ("walk", "run"):
        a = (28 if etat == "walk" else 55) * math.sin(2 * math.pi * t / max(duree, 1e-6))
        rot["right_leg"][0], rot["left_leg"][0] = a, -a          # +X : la jambe part vers l'avant
        rot["right_arm"][0], rot["left_arm"][0] = -a * 0.8, a * 0.8
    elif etat == "sneak":
        rot["body"][0] = -28.6                                    # le haut du torse vers l'avant
        dep["body"][1] = -3.2
        dep["head"][1] = -4.2
        for c in ("right_arm", "left_arm"):
            rot[c][0], dep[c][1] = 23, -3.2
        for c in ("right_leg", "left_leg"):
            dep[c][2], dep[c][1] = 4.0, -0.2
    elif etat == "mount":
        for c, y in (("right_leg", -18), ("left_leg", 18)):
            rot[c][0], rot[c][1] = 81, y
        for c in ("right_arm", "left_arm"):
            rot[c][0] = 36
    elif etat in ("swim", "glide"):
        G = rot_matrix(-90, 0, 0)                                 # couché, face vers le sol, dos vers le ciel
    elif etat == "sleep":
        G = rot_matrix(90, 0, 0)                                  # sur le dos
    fonctions = {}
    for k, piv in PIVOTS.items():
        R, piv, d = rot_matrix(*rot[k]), np.array(piv, float), dep[k]
        fonctions[k] = (lambda p, R=R, piv=piv, d=d: G @ (R @ (p - piv) + piv + d - CENTRE) + CENTRE)
    return fonctions


def load_model(path, anim_time=None, anim_name=None, pose=None, noms=None):
    """pose : None (cosmétique seul, dans le repère du joueur debout) ou résultat de pose_joueur().
    noms : liste facultative, remplie d'un (uuid de l'élément, noms des groupes parents) par face (vérificateur)."""
    m = json.load(open(path))
    # familier vivant (guide 6.6) : FAMILIER=vivant le pose au sol à côté du joueur, avec les requêtes de son état ;
    # FAMILIER=menu : porté, comme le menu Apparence. Le mannequin garde sa propre pose (pet_ = joueur immobile).
    _REQ_FAMILIER.clear()
    bloc, vue_fam = familier_de(m), os.environ.get("FAMILIER", "")
    if bloc and vue_fam == "vivant":
        etat = etat_pet(anim_name)
        _REQ_FAMILIER.update(requetes_familier(bloc, etat))
        if pose is not None:
            d = np.array(place_familier(bloc, etat), float)
            pose = {k: (lambda p, d=d: np.asarray(p, float) + d) for k in pose}
    elif bloc and vue_fam == "menu":
        _REQ_FAMILIER.update({"is_pet": 0, "is_in_menu": 1})
    if pose is not None:
        # skin d'objet (guide 14, tools/objet.py) : avec le joueur, tenu en main droite à la 3e personne (Display du modèle) ;
        # sans pose (vérificateur), dans son bloc 0..16. Même calcul dans visionneuse.js (matriceMain).
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import objet
        main = objet.main_de_modele(m)
        if main is not None:
            bras = pose["right_arm"]
            pose = {k: (lambda p, M=main: bras(objet.appliquer(M, p))) for k in pose}
    animators = {}
    if anim_time is not None and m.get("animations"):
        an = next((a for a in m["animations"] if a["name"] == anim_name), m["animations"][0])
        t = anim_time % float(an["length"]) if an.get("loop") == "loop" else anim_time
        animators = {k: (v["keyframes"], t) for k, v in an["animators"].items()}
    tex = None
    if m.get("textures"):
        src = m["textures"][0]["source"].split(",", 1)[1]
        tex = Image.open(io.BytesIO(base64.b64decode(src))).convert("RGBA")
        # calque lumineux _e (guide 5 bis) : ajouté à la couleur dans render(), comme en jeu et dans le Vestiaire
        te = next((t for t in m["textures"][1:] if t.get("name", "").rsplit(".", 1)[0].endswith("_e") and t.get("source")), None)
        if te is not None:
            tex.calque = Image.open(io.BytesIO(base64.b64decode(te["source"].split(",", 1)[1]))).convert("RGBA")
    tw = m["resolution"]["width"]; th = m["resolution"]["height"]
    by_id = {e["uuid"]: e for e in m["elements"]}

    quads = []  # (4 points world, 4 uv (0..1), couleur, ou None / "add" / "trans" pour une face texturée)

    def transform_chain(chain):
        def f(p):
            p = np.array(p, dtype=float)
            for origin, R, S, pos in chain:   # élément d'abord, puis groupes parents
                p = R @ (S * (p - origin)) + origin + pos
            return p
        return f

    def cache_alpha(node):
        """Opacité pilotée par un enfant ctrl_alpha (« 1 + position x ») < 10 % : le groupe disparaît (guide 4 bis)."""
        for c in node.get("children", []):
            if isinstance(c, dict) and c.get("name") == "ctrl_alpha" and c.get("uuid") in animators:
                kfs, t = animators[c["uuid"]]
                if 1 + sample(kfs, "position", t, [0, 0, 0])[0] < 0.1:
                    return True
        return False

    def walk2(node, parents, partie="body", mode=None, bill=None, cache=False, chemin=()):
        if isinstance(node, str):
            e = by_id[node]
            R = rot_matrix(*e.get("rotation", [0, 0, 0]))
            ch = [(np.array(e["origin"], float), R, np.ones(3), np.zeros(3))] + list(reversed(parents))
            T = transform_chain(ch)
            inf = e.get("inflate", 0)
            a, b = [v - inf for v in e["from"]], [v + inf for v in e["to"]]
            for fname, fdata in e["faces"].items():
                if fdata.get("texture") is None:
                    continue
                u1, v1, u2, v2 = fdata["uv"]
                if u1 == u2 or v1 == v2:
                    continue
                pts = [T(p) for p in FACE_CORNERS[fname](a, b)]
                if pose is not None:
                    pts = [pose[partie](p) for p in pts]
                if cache:
                    pts = [np.zeros(3) for _ in pts]
                uvs = [(u1 / tw, v1 / th), (u2 / tw, v1 / th), (u2 / tw, v2 / th), (u1 / tw, v2 / th)]
                quads.append((pts, uvs, {"mode": mode, "bill": bill} if bill else mode))
                if noms is not None:
                    noms.append((node, chemin))
        else:
            rot = np.array(node.get("rotation", [0, 0, 0]), float)
            S, pos = np.ones(3), np.zeros(3)
            if node.get("uuid") in animators:
                kfs, t = animators[node["uuid"]]
                ar = sample(kfs, "rotation", t, [0, 0, 0])
                import os
                if os.environ.get("MODCONV") == "1":
                    rot = rot + ar                               # convention du mod : rotations appliquées telles quelles
                else:
                    rot = rot + np.array([-ar[0], -ar[1], ar[2]])   # convention Blockbench (x,y inversés)
                S = sample(kfs, "scale", t, [1, 1, 1])
                pos = sample(kfs, "position", t, [0, 0, 0])
            R = rot_matrix(*rot)
            # fonctions anticipées (.claude/rules/conventions-anticipees.md) : add_ = additif, trans_ = translucide
            nom = node.get("name", "")
            m2 = "add" if nom.startswith("add_") else "trans" if nom.startswith("trans_") else mode
            suite = parents + [(np.array(node.get("origin", [0, 0, 0]), float), R, S, pos)]
            b2 = bill
            if nom.startswith(("cam_", "camy_")):
                # face caméra (guide 4 bis) : pivot et orientation monde du groupe sans son animation de rotation ;
                # render() tourne ces faces vers chaque caméra, l'animation s'applique ensuite
                o = np.array(node.get("origin", [0, 0, 0]), float)
                base = parents + [(o, rot_matrix(*node.get("rotation", [0, 0, 0])), S, pos)]
                Tb = transform_chain(list(reversed(base)))
                P0 = Tb(o)
                f = (lambda q: pose[partie](q)) if pose is not None else (lambda q: q)
                Pw = f(P0)
                cols = [f(Tb(o + e)) - Pw for e in np.eye(3)]
                Rw = np.column_stack([c / max(np.linalg.norm(c), 1e-9) for c in cols])
                b2 = ("camy" if nom.startswith("camy_") else "cam", Pw, Rw)
            c2 = cache or cache_alpha(node)
            for c in node.get("children", []):
                walk2(c, suite, partie, m2, b2, c2, chemin + (nom,))

    for n in m["outliner"]:
        if isinstance(n, dict) and n.get("name", "").startswith("particle_"):
            continue   # modèle de particule : pas porté par le joueur
        walk2(n, [], partie_de(n.get("name", "")) if isinstance(n, dict) else "body")
    return quads, tex

def mannequin(pose=None):
    """Joueur gris (Steve). Face avant = -z (nord), dos = +z. pose : résultat de pose_joueur(), debout si None."""
    quads = []
    def box(a, b, col, partie, front_col=None):
        f = pose[partie] if pose else (lambda p: p)
        for fname, fn in FACE_CORNERS.items():
            c = front_col if (fname == "north" and front_col) else col
            quads.append(([f(np.array(p, float)) for p in fn(a, b)], None, c))
    g1, g2, g3 = (120, 120, 128), (100, 100, 108), (88, 88, 96)
    box((-4, 24, -4), (4, 32, 4), g1, "head", (135, 135, 143))   # tête
    box((-4, 12, -2), (4, 24, 2), g2, "body")                    # torse
    box((4, 12, -2), (8, 24, 2), g3, "right_arm"); box((-8, 12, -2), (-4, 24, 2), g3, "left_arm")   # bras (droite du joueur = +x)
    box((0, 0, -2), (4, 12, 2), g2, "right_leg"); box((-4, 0, -2), (0, 12, 2), g3, "left_leg")      # jambes
    # yeux
    f = pose["head"] if pose else (lambda p: p)
    for x in (-2.5, 1.0):
        quads.append(([f(np.array(p, float)) for p in [(x, 29, -4.01), (x + 1.5, 29, -4.01), (x + 1.5, 27.5, -4.01), (x, 27.5, -4.01)]], None, (30, 30, 40)))
    return quads


# ---------------------------------------------------------------- effet de téléportation (guide 15)
# Posé au sol, pas porté : le cosmétique ne suit aucune partie du corps. Animations charge (loop), depart et arrivee (once),
# trouvées par la dernière partie du nom, accents et majuscules ignorés. Le groupe vide `joueur` donne la position et
# l'échelle du joueur (rotation ignorée) pendant charge, depart et arrivee (charge : guide du 2026-11-06 soir) ; sans lui,
# le joueur est debout à l'origine. Mêmes calculs dans visionneuse.js (effetDe, poseEffet).
ANIMS_EFFET = ("charge", "depart", "arrivee")


def mot_anim(anim_name):
    """Dernière partie du nom d'animation, en minuscules et sans accent (« animation.portail.Arrivée » -> « arrivee »)."""
    import unicodedata
    mot = (anim_name or "").split(".")[-1].lower()
    return "".join(c for c in unicodedata.normalize("NFD", mot) if unicodedata.category(c) != "Mn")


def chemin_joueur(m):
    """Groupes de la racine jusqu'au groupe `joueur` (guide 15), ou None."""
    def chercher(n, chemin):
        if not isinstance(n, dict):
            return None
        chemin = chemin + [n]
        if mot_anim(n.get("name", "")).replace(" ", "") == "joueur":
            return chemin
        for c in n.get("children", []):
            r = chercher(c, chemin)
            if r:
                return r
        return None
    for n in m.get("outliner", []):
        r = chercher(n, [])
        if r:
            return r
    return None


def effet_de(m):
    """Vrai pour un effet de téléportation : une animation depart ou arrivee, ou un groupe `joueur` (guide 15)."""
    mots = {mot_anim(a.get("name", "")) for a in m.get("animations", [])}
    return bool(mots & {"depart", "arrivee"}) or chemin_joueur(m) is not None


def place_joueur_effet(m, anim_time, anim_name):
    """(position monde des pieds, échelle) du groupe `joueur` dans charge, depart ou arrivee ; None ailleurs ou sans groupe.
    Position = origine du groupe passée par sa chaîne animée ; échelle = produit des échelles animées de la chaîne."""
    if mot_anim(anim_name) not in ANIMS_EFFET:
        return None
    chemin = chemin_joueur(m)
    if not chemin:
        return None
    an = next((a for a in m.get("animations", []) if a["name"] == anim_name), None)
    anims = an.get("animators", {}) if an else {}
    t = float(anim_time or 0.0)
    if an and an.get("loop") == "loop":
        t %= float(an["length"])
    chaine, S_tot = [], np.ones(3)
    for g in chemin:
        rot, S, pos = np.array(g.get("rotation", [0, 0, 0]), float), np.ones(3), np.zeros(3)
        if g.get("uuid") in anims:
            kfs = anims[g["uuid"]]["keyframes"]
            rot = rot + sample(kfs, "rotation", t, [0, 0, 0])
            S = sample(kfs, "scale", t, [1, 1, 1])
            pos = sample(kfs, "position", t, [0, 0, 0])
        chaine.append((np.array(g.get("origin", [0, 0, 0]), float), rot_matrix(*rot), S, pos))
        S_tot = S_tot * S
    p = chaine[-1][0].copy()
    for o, R, S, pos in reversed(chaine):
        p = R @ (S * (p - o)) + o + pos
    return p, S_tot


def pose_effet(m, anim_time, anim_name):
    """Pose du mannequin pour un effet : toutes ses parties suivent le groupe `joueur` (à l'échelle 0, réduit à un point :
    rien de dessiné) ; None = debout à l'origine (sans groupe `joueur`, ou hors de charge, depart et arrivee)."""
    pl = place_joueur_effet(m, anim_time, anim_name)
    if pl is None:
        return None
    P, S = pl
    # Mod 1.4.0 (bytecode TeleportEffects.picture/submit, 2026-11-07) : échelle lue = |x| ; sous 0,05 le joueur n'est pas
    # dessiné. Guide du 2026-11-08 (demandes 6) : la copie du départ suit aussi l'échelle, comme charge et arrivee.
    s = abs(float(S[0]))
    if s < 0.05:
        S = np.zeros(3)
    f = lambda q, P=P, S=S: S * np.asarray(q, float) + P
    return {k: f for k in PIVOTS}


def poses_scene(m, anim_name, anim_time, poser=True):
    """(pose du cosmétique, pose du mannequin) pour load_model() et mannequin(). Effet de téléportation : cosmétique
    posé au sol (None), mannequin sur le groupe `joueur`. Sinon, avec poser : la pose de l'état du joueur pour les deux."""
    if effet_de(m):
        return None, pose_effet(m, anim_time, anim_name)
    if not poser:
        return None, None
    an = next((a for a in m.get("animations", []) if a["name"] == anim_name), None)
    L = float(an["length"]) if an else 1.0
    t = float(anim_time or 0.0)
    if an and an.get("loop") == "loop" and L > 0:
        t %= L
    pz = pose_joueur(etat_de(anim_name), t, L)
    return pz, pz


def cadrer(points, direction, fov=28, marge=1.0, rayon_min=7.0):
    """Caméra qui centre des points (le cosmétique) vus depuis une direction : (position, cible).
    Sphère englobante prise sur la boîte des points ; rayon minimal pour garder un peu du corps en repère."""
    d = np.array(direction, float); d /= np.linalg.norm(d)
    if len(points):
        P = np.asarray(points, float); lo, hi = P.min(0), P.max(0)
        c, r = (lo + hi) / 2, max(np.linalg.norm(hi - lo) / 2, rayon_min)
    else:
        c, r = np.array([0.0, 16.0, 0.0]), 16.0
    dist = r / math.sin(math.radians(fov / 2)) * marge
    return tuple(c + d * dist), tuple(c)


def points_de(quads):
    return [p for q in quads for p in q[0]]


# ------------------------------------------------------------------ « comme en jeu » (JEU=1)
# Mesuré dans le mod 1.4.0 et Minecraft 26.1.2 (.claude/references/mod/rendu-en-jeu.md) : textures au plus proche, pas
# d'anticrénelage ; faces éclairées par les deux lumières fixes de Minecraft (0,4 dessous à 1,0 dessus), recto et verso
# (pas d'élimination) ; × lumière du monde (lightmap) ; trans_ : coupé sous 26, écrit la profondeur. Écran de 1 369
# lignes, champ de 70°. Guide du 2026-11-08 (demandes 6) : add_ et _e ajoutés sans lumière, couleur × alpha du texel
# (alpha 0 seul jeté) ; mipmaps (4 niveaux, réglage vidéo du joueur) : niveau choisi par triangle d'après l'empreinte
# d'un pixel d'écran en texels (approché : moyenne 2 × 2 pondérée par l'alpha ; MIPMAPS=0 pour les couper).
ECRAN_JEU, FOV_JEU = 1369, 70.0
_L0 = np.array([0.2, 1.0, -0.7]) / np.linalg.norm([0.2, 1.0, -0.7])
_L1 = np.array([-0.2, 1.0, 0.7]) / np.linalg.norm([-0.2, 1.0, 0.7])
# ciel (zénith, horizon), lumière du monde (lightmap, luminosité « Lumineux » du joueur) ; nuit et shader : approchés
CIELS_JEU = {
    "jour": ((120, 167, 255), (192, 216, 255), (1.0, 1.0, 1.0)),
    "gris": ((168, 172, 180), (196, 200, 207), (1.0, 1.0, 1.0)),     # temps couvert des captures du 2026-11-07
    "nuit": ((3, 4, 10), (12, 14, 26), (0.60, 0.62, 0.72)),
    "shader": ((12, 12, 20), (40, 38, 46), (0.24, 0.23, 0.28)),
}
SOL_JEU = (104, 102, 100)
NOMS_CIELS = {"jour": "Jour", "gris": "Jour gris", "nuit": "Nuit", "shader": "Nuit + shader (approché)"}


def mipmaps(arr, niveaux):
    """Copies réduites d'une texture RGBA (uint8) : moyenne 2 × 2, couleur pondérée par l'alpha (approché) ; niveau 0 = arr.
    S'arrête quand une dimension devient impaire ou à `niveaux` (réglage vidéo « Niveaux de mipmap », 4 par défaut)."""
    out = [arr]
    a = arr.astype(np.float32)
    for _ in range(max(0, niveaux)):
        h, w = a.shape[:2]
        if h % 2 or w % 2 or h < 2 or w < 2:
            break
        q = a.reshape(h // 2, 2, w // 2, 2, 4)
        al = q[..., 3:4]
        som = al.sum(axis=(1, 3))
        rgb = np.where(som > 0, (q[..., :3] * al).sum(axis=(1, 3)) / np.maximum(som, 1e-6), q[..., :3].mean(axis=(1, 3)))
        a = np.concatenate([rgb, som / 4], axis=-1)
        out.append(np.clip(a + 0.5, 0, 255).astype(np.uint8))
    return out


def jeu_actif():
    return os.environ.get("JEU") == "1"


def ombre_mc(n):
    """Lumière d'une face de Minecraft (light.glsl) pour une normale tournée vers la caméra."""
    return min(1.0, (max(0.0, float(n @ _L0)) + max(0.0, float(n @ _L1))) * 0.6 + 0.4)


def camera_jeu(points, distance_blocs, direction=(-44, 0, -56), yeux=26.0):
    """Œil d'un joueur debout (1,62 bloc) à `distance_blocs` du centre de la pièce, dans la direction donnée, qui la regarde."""
    if len(points):
        P = np.asarray(points, float); c = (P.min(0) + P.max(0)) / 2
    else:
        c = np.array([0.0, 16.0, 0.0])
    d = np.array([direction[0], 0.0, direction[2]], float); d /= np.linalg.norm(d)
    eye = np.array([c[0], 0.0, c[2]]) + d * distance_blocs * 16
    eye[1] = yeux
    # regard vers la pièce, à hauteur de poitrine au plus (0,5 à 1,75 bloc) : un grand effet dépasse de l'écran, comme en jeu
    c = np.array(c, float)
    c[1] = min(max(c[1], 8.0), 28.0)
    return tuple(eye), tuple(c)


def render(quads, tex, cam_pos, target, size=900, fov=28, bg=(18, 14, 20)):
    jeu = jeu_actif()
    S = 1 if jeu else 2  # supersampling (aucun en jeu)
    W = H = size * S
    cam_pos = np.array(cam_pos, float); target = np.array(target, float)
    fwd = target - cam_pos; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    f = 1 / math.tan(math.radians(fov) / 2)
    light = np.array([-0.4, 1.0, 0.6]); light /= np.linalg.norm(light)

    import os
    jour = 0.16 if os.environ.get("NUIT") == "1" else 1.0     # comme la vue de nuit du Vestiaire
    if jour < 1:
        bg = (3, 3, 6)
    color = np.zeros((H, W, 3), np.float32); color[:] = np.array(bg) / 255
    zbuf = np.full((H, W), np.inf, np.float32)
    lumjeu = np.ones(3)
    if jeu:
        # ciel en dégradé (horizon -> zénith) et sol de pierre à y = 0 (damier de blocs), éclairé par la lumière du monde
        zen, hor, lj = CIELS_JEU.get(os.environ.get("CIEL", "jour"), CIELS_JEU["jour"])
        lumjeu = np.array(lj, float); jour = 1.0
        fo = 1 / math.tan(math.radians(fov) / 2)
        xs_, ys_ = np.meshgrid((np.arange(W) + 0.5 - W / 2) / (fo * 0.5 * W), -(np.arange(H) + 0.5 - H / 2) / (fo * 0.5 * H))
        dirs = fwd[None, None, :] + xs_[..., None] * right[None, None, :] + ys_[..., None] * up[None, None, :]
        elev = dirs[..., 1] / np.linalg.norm(dirs, axis=-1)
        k = np.clip(elev / 0.6, 0, 1)[..., None]
        color[:] = (np.array(hor) * (1 - k) + np.array(zen) * k) / 255
        if cam_pos[1] > 0:
            tt = np.where(dirs[..., 1] < -1e-6, -cam_pos[1] / np.minimum(dirs[..., 1], -1e-6), np.inf)
            tt = np.minimum(tt, 1e6)
            hx, hz = cam_pos[0] + tt * dirs[..., 0], cam_pos[2] + tt * dirs[..., 2]
            sol = np.isfinite(tt) & (np.hypot(hx, hz) < 480)
            damier = np.where((np.floor(hx / 16) + np.floor(hz / 16)) % 2 == 0, 1.0, 0.9)
            csol = np.array(SOL_JEU) / 255 * lumjeu
            color[sol] = (csol[None, :] * damier[sol][:, None])
            zbuf[sol] = tt[sol]
    seuil_e = 0 if jeu else 127
    texarr = np.array(tex) if tex is not None else None
    earr = np.array(tex.calque) if tex is not None and getattr(tex, "calque", None) is not None and tex.calque.size == tex.size else None
    niv_max = int(os.environ.get("MIPMAPS", "4")) if jeu else 0
    mips_t = mipmaps(texarr, niv_max) if texarr is not None else None
    mips_e = mipmaps(earr, niv_max) if earr is not None else None

    def project(p):
        d = p - cam_pos
        x, y, z = d @ right, d @ up, d @ fwd
        return np.array([(x / z) * f * 0.5 * W + W / 2, -(y / z) * f * 0.5 * H + H / 2, z])

    def face_cam(q):
        """Groupes cam_ / camy_ : faces tournées vers cette caméra autour du pivot du groupe."""
        pts, uvs, col = q
        if not isinstance(col, dict):
            return q
        kind, Pw, Rw = col["bill"]
        d = cam_pos - Pw
        yaw = math.degrees(math.atan2(d[0], d[2]))
        pitch = math.degrees(math.atan2(d[1], math.hypot(d[0], d[2]))) if kind == "cam" else 0.0
        Rt = rot_matrix(0, yaw, 0) @ rot_matrix(-pitch, 0, 0)
        C = Rt @ Rw.T
        return ([Pw + C @ (p - Pw) for p in pts], uvs, col["mode"])

    quads = [face_cam(q) for q in quads]

    def prof(q):
        return float(np.mean([(p - cam_pos) @ fwd for p in q[0]]))
    opaques = [q for q in quads if q[2] not in ("add", "trans")]
    trans = sorted((q for q in quads if q[2] == "trans"), key=prof, reverse=True)
    adds = [q for q in quads if q[2] == "add"]
    for pts, uvs, col in opaques + trans + adds:
        n = np.cross(pts[1] - pts[0], pts[3] - pts[0])
        ln = np.linalg.norm(n)
        if ln < 1e-9:
            continue
        n /= ln
        if jeu:
            # face (ou son verso) tournée vers la caméra : lumière de Minecraft, × lumière du monde
            if n @ (cam_pos - np.mean(pts, axis=0)) < 0:
                n = -n
            shade = ombre_mc(n) * lumjeu
        else:
            shade = 0.55 + 0.45 * abs(n @ light)
        P = np.array([project(p) for p in pts])
        if (P[:, 2] <= 0.1).any():
            continue
        for tri in ((0, 1, 2), (0, 2, 3)):
            A, B, C = P[list(tri)]
            xmin, xmax = int(max(0, np.floor(min(A[0], B[0], C[0])))), int(min(W - 1, np.ceil(max(A[0], B[0], C[0]))))
            ymin, ymax = int(max(0, np.floor(min(A[1], B[1], C[1])))), int(min(H - 1, np.ceil(max(A[1], B[1], C[1]))))
            if xmin > xmax or ymin > ymax:
                continue
            xs, ys = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
            det = (B[0] - A[0]) * (C[1] - A[1]) - (C[0] - A[0]) * (B[1] - A[1])
            if abs(det) < 1e-9:
                continue
            l1 = ((B[0] - xs) * (C[1] - ys) - (C[0] - xs) * (B[1] - ys)) / det
            l2 = ((C[0] - xs) * (A[1] - ys) - (A[0] - xs) * (C[1] - ys)) / det
            l3 = 1 - l1 - l2
            eps = -1e-4
            mask = (l1 >= eps) & (l2 >= eps) & (l3 >= eps)
            if not mask.any():
                continue
            # interpolation perspective-correcte
            iz = l1 / A[2] + l2 / B[2] + l3 / C[2]
            z = 1 / np.where(iz == 0, 1e-9, iz)
            sub_z = zbuf[ymin:ymax + 1, xmin:xmax + 1]
            mask &= z < sub_z
            special = col in ("add", "trans")
            if col is None or special:
                uvA, uvB, uvC = (np.array(uvs[i]) for i in tri)
                u = (l1 * uvA[0] / A[2] + l2 * uvB[0] / B[2] + l3 * uvC[0] / C[2]) * z
                v = (l1 * uvA[1] / A[2] + l2 * uvB[1] / B[2] + l3 * uvC[1] / C[2]) * z
                niv = 0
                if niv_max:
                    # empreinte d'un pixel d'écran en texels (dérivées du triangle, comme le GPU) -> niveau de mipmap
                    T = np.array([(uvB - uvA) * texarr.shape[1::-1], (uvC - uvA) * texarr.shape[1::-1]]).T
                    Sm = np.array([[B[0] - A[0], C[0] - A[0]], [B[1] - A[1], C[1] - A[1]]])
                    J = T @ np.linalg.inv(Sm)
                    rho = max(np.linalg.norm(J[:, 0]), np.linalg.norm(J[:, 1]))
                    niv = int(min(len(mips_t) - 1, max(0, round(math.log2(rho))))) if rho > 1 else 0
                ta = mips_t[niv]
                tu = np.clip((u * ta.shape[1]).astype(int), 0, ta.shape[1] - 1)
                tv = np.clip((v * ta.shape[0]).astype(int), 0, ta.shape[0] - 1)
                samp = ta[tv, tu]
                # jeu (mod 1.4.0) : trans_ = entityTranslucent, coupé sous alpha 0,1 (26) et écrit la profondeur ; il est
                # dessiné avant add_ (passes OPAQUE, TRANSLUCENT, ADDITIVE) : un add_ derrière une face trans_ est caché.
                # add_ (guide du 2026-11-08) : couleur × alpha, seul l'alpha 0 est jeté
                mask &= samp[..., 3] > (0 if col == "add" else 25 if col == "trans" or jeu else 0 if special else 127)
                rgb = samp[..., :3] / 255.0
                if col == "add":
                    rgb = rgb * (samp[..., 3:4] / 255.0)
                if earr is not None:
                    es = mips_e[min(niv, len(mips_e) - 1)]
                    ee = es[np.clip((v * es.shape[0]).astype(int), 0, es.shape[0] - 1), np.clip((u * es.shape[1]).astype(int), 0, es.shape[1] - 1)]
                    # _e : jeu = couleur × alpha (guide du 2026-11-08) ; studio : texels d'alpha > 127, couleur entière
                    lum = (ee[..., :3] / 255.0) * ((ee[..., 3:4] / 255.0) if jeu else (ee[..., 3:4] > seuil_e))
                else:
                    lum = 0.0
            else:
                rgb = np.broadcast_to(np.array(col) / 255.0, xs.shape + (3,))
                lum = 0.0
            if not mask.any():
                continue
            sub_c = color[ymin:ymax + 1, xmin:xmax + 1]
            lumf = np.broadcast_to(lum, rgb.shape) if not np.isscalar(lum) else lum
            if col == "add":
                sub_c[mask] = np.minimum(sub_c[mask] + rgb[mask], 1.0)
            elif col == "trans":
                al = (samp[..., 3:4] / 255.0)
                # jeu : le calque _e est une passe additive à part, ajoutée en entier (pas × alpha)
                sub_c[mask] = np.minimum(rgb * shade * jour * al + sub_c * (1 - al) + lumf * (1.0 if jeu else al), 1.0)[mask]
                sub_z[mask] = z[mask]
            else:
                sub_c[mask] = np.minimum(rgb * shade * jour + lumf, 1.0)[mask]
                sub_z[mask] = z[mask]

    img = Image.fromarray((np.clip(color, 0, 1) * 255).astype(np.uint8))
    return img if S == 1 else img.resize((size, size), Image.LANCZOS)


def planche_jeu(path, out, anim=None, t=0.0, cases=None, cote=640):
    """Planche « comme en jeu » : la pièce vue par un joueur debout, champ de 70°, à la densité de pixels de l'écran
    (1 369 lignes, rendu au plus proche sans anticrénelage), puis réduite pour la planche comme une capture.
    cases : [(ciel, distance en blocs)] ; par défaut jour et jour gris à 3 blocs (« Essayer »), nuit à 3 et 10 blocs."""
    os.environ["JEU"] = "1"
    m = json.load(open(path))
    cases = cases or [("jour", 3), ("gris", 10), ("nuit", 3), ("shader", 10)]
    poser = os.environ.get("MODCONV") == "1" and os.environ.get("POSE", "1") != "0"
    pz, pm = poses_scene(m, anim, t, poser) if anim else (None, None)
    q, tex = load_model(path, anim_time=t if anim else None, anim_name=anim, pose=pz)
    scene = q + mannequin(pm)
    pts = points_de(q) or points_de(scene)
    tuiles = []
    for ciel, d in cases:
        os.environ["CIEL"] = ciel
        # effet : vu de face-gauche (« Essayer ») ; pièce portée : de dos 3/4, comme la 3e personne (F5)
        cam, tgt = camera_jeu(pts, d, (-44, 0, -56) if effet_de(m) else (40, 0, 60))
        im = render(scene, tex, cam, tgt, size=ECRAN_JEU, fov=FOV_JEU)   # carré central de l'écran, 1 pixel = 1 pixel du jeu
        tuiles.append((f"{NOMS_CIELS[ciel]}, {d} blocs", im.resize((cote, cote), Image.LANCZOS)))
    can = Image.new("RGB", (cote * 2 + 30, cote * 2 + 70), (18, 14, 20))
    d_ = ImageDraw.Draw(can)
    for i, (titre, im) in enumerate(tuiles):
        x, y = (i % 2) * (cote + 10) + 10, (i // 2) * (cote + 20) + 40
        can.paste(im, (x, y))
        d_.text((x + 8, y - 22), titre + " (comme en jeu)", fill=(235, 200, 200))
    can.save(out)
    return out

if __name__ == "__main__":
    import os
    path, out = sys.argv[1], sys.argv[2]
    if out.endswith(".gif"):
        frames = []
        anim_name = sys.argv[3] if len(sys.argv) > 3 else None
        m = json.load(open(path)); an = next((a for a in m["animations"] if a["name"] == anim_name), m["animations"][0])
        dur = float(an["length"]); fps = 24; n = max(12, int(round(dur * fps)))
        poser = os.environ.get("MODCONV") == "1" and os.environ.get("POSE", "1") != "0"
        arg_cam = sys.argv[4] if len(sys.argv) > 4 else "-44,34,-56"
        if arg_cam.startswith("auto:"):
            # Cadrage automatique : la pièce sur 8 instants de l'animation, vue depuis la direction donnée.
            pts = []
            for k in range(8):
                tk = k * dur / 8
                pk, pm = poses_scene(m, an["name"], tk, poser)
                pts += points_de(load_model(path, anim_time=tk, anim_name=an["name"], pose=pk)[0])
                if effet_de(m):
                    pts += points_de(mannequin(pm))   # effet (guide 15) : le joueur peut tomber du ciel, il reste dans le cadre
            cam, tgt = cadrer(pts, [float(v) for v in arg_cam[5:].split(",")], marge=1.18, rayon_min=9.0)
        else:
            cam = tuple(float(v) for v in arg_cam.split(","))
            tgt = tuple(float(v) for v in sys.argv[5].split(",")) if len(sys.argv) > 5 else (0, 14, 0)
        for i in range(n):
            pz, pm = poses_scene(m, an["name"], i * dur / n, poser)
            q, tex = load_model(path, anim_time=i * dur / n, anim_name=an["name"], pose=pz)
            frames.append(render(q + mannequin(pm), tex, cam, tgt, size=480).quantize(colors=128, dither=0))
            print("frame", i + 1, "/", n, flush=True)
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0, optimize=False)
        if os.environ.get("WEBP"):
            # Animation de l'état seule, pour la fiche du Vestiaire : WebP animé, léger, 12 images/s.
            im = [f.convert("RGB").resize((400, 400), Image.LANCZOS) for f in frames[::2]]
            im[0].save(os.environ["WEBP"], save_all=True, append_images=im[1:], duration=int(2000 / fps), loop=0, quality=78, method=4)
        print("ok", out); sys.exit()
    pz = pm = None
    m = json.load(open(path))
    poser = os.environ.get("MODCONV") == "1" and os.environ.get("POSE", "1") != "0"
    if jeu_actif() and "--seule" not in sys.argv:
        # JEU=1 : planche « comme en jeu » (jour, jour gris, nuit, nuit + shader ; 3 et 10 blocs), ANIM et T facultatifs
        cases = [(c.split(":")[0], float(c.split(":")[1])) for c in os.environ["CASES"].split(",")] if os.environ.get("CASES") else None
        planche_jeu(path, out, os.environ.get("ANIM"), float(os.environ.get("T", "0")), cases)
        print("ok", out); sys.exit()
    if os.environ.get("INSTANTS") and os.environ.get("ANIM"):
        # Planche d'un effet de téléportation (guide 15) : 4 instants de l'animation (fractions de sa durée), vue de face 3/4,
        # cadrés ensemble sur l'effet et le joueur (qui peut tomber du ciel ou rétrécir).
        nom = os.environ["ANIM"]; an = next((a for a in m["animations"] if a["name"] == nom), None)
        L = float(an["length"]) if an else 1.0
        fr = [float(v) for v in os.environ["INSTANTS"].split(",")][:4]
        scenes = []
        for f_ in fr:
            pk, pm_ = poses_scene(m, nom, f_ * L, poser)
            q, tex = load_model(path, anim_time=f_ * L, anim_name=nom, pose=pk)
            scenes.append((f_ * L, q, q + mannequin(pm_)))
        pts = [p for _, q, sc in scenes for p in points_de(sc)]
        cam, tgt = cadrer(pts, (-44, 34, -56), marge=1.1, rayon_min=16.0)
        tiles = [(f"t = {t_:.2f} s", render(sc, tex, cam, tgt, size=700)) for t_, _, sc in scenes]
        canvas = Image.new("RGB", (700 * 2 + 30, 700 * 2 + 70), (18, 14, 20))
        d = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        except Exception:
            font = ImageFont.load_default()
        for i, (titre, t_im) in enumerate(tiles):
            x, y = (i % 2) * 710 + 10, (i // 2) * 720 + 40
            canvas.paste(t_im, (x, y))
            d.text((x + 12, y - 32), titre, fill=(235, 200, 200), font=font)
        canvas.save(out)
        print("ok", out); sys.exit()
    if os.environ.get("ANIM"):
        pz, pm = poses_scene(m, os.environ["ANIM"], float(os.environ.get("T", "0")), poser)
        quads, tex = load_model(path, anim_time=float(os.environ.get("T", "0")), anim_name=os.environ["ANIM"], pose=pz)
    else:
        quads, tex = load_model(path)
    scene = quads + mannequin(pm)
    if "--seule" in sys.argv:
        # Vignette : une seule vue (caméra, cible), recadrée serrée sur ce qui n'est pas le fond, en carré.
        i = sys.argv.index("--seule")
        cam = tuple(float(v) for v in sys.argv[i + 1].split(",")); tgt = tuple(float(v) for v in sys.argv[i + 2].split(","))
        fond = (18, 14, 20)
        img = render(scene, tex, cam, tgt, size=1000, bg=fond)
        # Cadre calculé sur le cosmétique seul (sans mannequin), au moins 42 % de la vue pour garder le corps en repère.
        a = np.asarray(render(quads, tex, cam, tgt, size=1000, bg=fond)).astype(int)
        ys, xs = np.nonzero(np.abs(a - np.array(fond)).max(axis=2) > 10)
        if len(xs):
            cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
            cote = max(max(xs.max() - xs.min(), ys.max() - ys.min()) * 1.22 + 24, 420)
            boite = [int(round(v)) for v in (cx - cote / 2, cy - cote / 2, cx + cote / 2, cy + cote / 2)]
            carre = Image.new("RGB", (boite[2] - boite[0], boite[3] - boite[1]), fond)
            carre.paste(img.crop((max(0, boite[0]), max(0, boite[1]), min(1000, boite[2]), min(1000, boite[3]))), (max(0, -boite[0]), max(0, -boite[1])))
            img = carre
        img.resize((480, 480), Image.LANCZOS).save(out, optimize=True)
        print("ok", out); sys.exit()
    zoom = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    target = (0, 14, 0)
    views = [
        ("Face 3/4", (-44, 34, -56)),
        ("Dos 3/4", (46, 36, 54)),
        ("Face", (0, 22, -74)),
        ("Dessus", (0.5, 85, -16)),
    ]
    if os.environ.get("CADRAGE") == "auto":
        pts = points_de(quads)
        tiles = [render(scene, tex, *cadrer(pts, c, marge=1.1, rayon_min=13.0), size=700) for _, c in views]   # rayon minimal : le corps reste en repère
    else:
        tiles = [render(scene, tex, tuple(v * zoom for v in c), target, size=700) for _, c in views]
    canvas = Image.new("RGB", (700 * 2 + 30, 700 * 2 + 70), (18, 14, 20))
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    except Exception:
        font = ImageFont.load_default()
    for i, (t, (name, _)) in enumerate(zip(tiles, views)):
        x, y = (i % 2) * 710 + 10, (i // 2) * 720 + 40
        canvas.paste(t, (x, y))
        d.text((x + 12, y - 32), name, fill=(235, 200, 200), font=font)
    canvas.save(out)
    print("ok", out)
