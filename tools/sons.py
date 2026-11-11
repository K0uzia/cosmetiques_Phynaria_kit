"""Sons des cosmétiques : fréquence (limiter_sons) et sons embarqués (embarquer_sons, controler_sons).

Garde les sons rares (retour de l'utilisateur : « infernal » quand chaque mouvement siffle, plusieurs fois de suite).
Usage dans un générateur, juste avant d'écrire le modèle :
    limiter_sons(model)
Règle (.claude/rules/essentiel.md, Sons rares ; format : .claude/rules/fonctions-avancees.md) :
- états en mouvement (walk, run, fly, glide, fall, swim, sneak, mount…) : aucun son ;
- repos (idle, sleep) : au plus un son par boucle, et seulement si la boucle dure au moins PERIODE_MIN secondes ;
- attack : au plus un son, seulement pour une arme (attaque=True) ; event_equip et event_unequip (rares), depart et arrivee
  d'un effet de téléportation : au plus un ; charge : aucun (max_charge pour une exception demandée) ; hurt et autres événements : aucun ;
- couches permanentes (overlay_…) : aucun son (elles tournent en même temps que l'état).
Le modèle est modifié sur place.

Sons embarqués (guide 6.5 du 2026-11-05, conforme au format relevé dans le mod 1.4.0) :
    embarquer_sons(model, {"carillon_celeste": "sons/carillon_celeste.ogg"})
écrit l'objet racine `phynaria_sounds` {nom: "data:audio/ogg;base64,…"} ; une clé `sound` de la piste Effects dont l'effet
est ce nom joue le son embarqué. Contrôles identiques à ceux du mod (BbModel.embeddedSounds, OggSound.check) : nom
[a-z0-9_]{1,32}, 8 sons au plus, OGG Vorbis mono, 102 400 octets et 5 s au plus. `controler_sons(model)` sert au vérificateur."""
import os, re, base64, runpy

PERIODE_MIN = 20.0       # « encore un peu trop fréquent » à 8 s (2e retour)
REPOS = ("idle", "sleep")
PONCTUELS = ("attack", "hurt")


def limiter_sons(model, attaque=False, max_effet=1, max_charge=0):
    """max_effet : sons gardés dans depart et arrivee d'un effet de téléportation (1 par défaut ; 2 pour un même événement en
    deux temps, ex. fissure puis bris de vitre d'effet_givre, demande de l'utilisateur du 2026-11-06).
    max_charge : sons gardés dans la charge d'un effet (0 par défaut ; exception demandée pour effet_stellaire_porte,
    2026-11-07 : un clac par cran + le grondement de l'anneau)."""
    for an in model["animations"]:
        effets = an.get("animators", {}).get("effects")
        if not effets:
            continue
        nom = an["name"].split(".")[-1]
        sons = sorted((k for k in effets["keyframes"] if k["channel"] == "sound"), key=lambda k: k["time"])
        if nom in REPOS:
            garde = sons[:1] if float(an["length"]) >= PERIODE_MIN else []
        elif nom in ("depart", "arrivee"):                       # effet (guide 15) : un son, deux sur demande (max_effet)
            garde = sons[:max_effet]
        elif nom == "charge":                                    # effet : aucun, sauf exception demandée (max_charge)
            garde = sons[:max_charge]
        elif (nom == "attack" and attaque) or nom in ("event_equip", "event_unequip"):
            garde = sons[:1]
        else:
            garde = []
        effets["keyframes"] = [k for k in effets["keyframes"] if k["channel"] != "sound"] + garde
        if not effets["keyframes"]:
            del an["animators"]["effects"]


# --- Sons embarqués -----------------------------------------------------------------------------------------------------
# Constantes du mod (fr.phynaria.utilities.core.skin.BbModel / OggSound / BbAnimation, version 1.4.0).
NOM_SON = re.compile(r"[a-z0-9_]{1,32}")                                  # BbModel.SOUND_NAME
ID_SON = re.compile(r"(?:[a-z0-9_.-]{1,32}:)?[a-z0-9_./-]{1,96}")          # BbAnimation.SOUND_ID (clés de la piste Effects)
MAX_SONS = 8                                                              # BbModel.MAX_SOUND_FILES
MAX_OCTETS = 102400                                                       # OggSound.MAX_BYTES
MAX_SECONDES = 5.0                                                        # OggSound.MAX_SECONDS
CIBLE_OCTETS = 40 * 1024                                                  # notre cible (budget du fichier compressé)
_MC = None


def sons_minecraft():
    """Noms des sons de Minecraft (tools/sons_minecraft.txt, relevé dans le sounds.json du jeu)."""
    global _MC
    if _MC is None:
        f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sons_minecraft.txt")
        _MC = {l.strip() for l in open(f, encoding="utf-8") if l.strip() and not l.startswith("#")}
    return _MC


def lire_ogg(data):
    """Reproduit OggSound.check du mod : pages OggS contiguës jusqu'au bout du fichier, premier paquet = en-tête
    d'identification Vorbis, 1 canal, durée = dernière position de granule / fréquence. ValueError si refusé."""
    if data is None or len(data) < 58:
        raise ValueError("pas un OGG Vorbis")
    if len(data) > MAX_OCTETS:
        raise ValueError(f"plus de 100 Ko ({len(data)} octets > {MAX_OCTETS})")
    canaux, freq, granule, pos = -1, -1, -1, 0
    while pos + 27 <= len(data):
        if data[pos:pos + 4] != b"OggS":
            raise ValueError("pas un OGG Vorbis (page OggS attendue)")
        g = int.from_bytes(data[pos + 6:pos + 14], "little")
        nseg = data[pos + 26]
        corps = pos + 27 + nseg
        if corps > len(data):
            raise ValueError("pas un OGG Vorbis (page tronquée)")
        taille = sum(data[pos + 27:corps])
        if corps + taille > len(data):
            raise ValueError("pas un OGG Vorbis (page tronquée)")
        if canaux < 0:
            if taille < 16 or data[corps] != 1 or data[corps + 1:corps + 7] != b"vorbis":
                raise ValueError("pas un OGG Vorbis (en-tête Vorbis attendu)")
            canaux, freq = data[corps + 11], int.from_bytes(data[corps + 12:corps + 16], "little")
        if g != 0xFFFFFFFFFFFFFFFF:
            granule = g
        pos = corps + taille
    if canaux < 1 or freq <= 0:
        raise ValueError("pas un OGG Vorbis")
    if canaux != 1:
        raise ValueError(f"il doit être mono ({canaux} canaux)")
    duree = 0.0 if granule < 0 else granule / freq
    if duree > MAX_SECONDES:
        raise ValueError(f"plus de 5 secondes ({duree:.2f} s)")
    return {"canaux": canaux, "frequence": freq, "duree": duree, "octets": len(data)}


def _decoder(uri):
    """data:…;base64,… -> octets (le mod exige « data: » et « ;base64 » avant la virgule)."""
    i = uri.find(",")
    if not uri.startswith("data:") or i < 0 or not uri[:i].endswith(";base64"):
        raise ValueError("pas une URI data:…;base64")
    if (len(uri) - i) // 4 * 3 > MAX_OCTETS + 3:
        raise ValueError("plus de 100 Ko")
    return base64.b64decode(uri[i + 1:])


def embarquer_sons(model, sons, refabriquer=True):
    """sons = {nom: chemin .ogg}. Si le .ogg manque ou est plus ancien que le script voisin de même nom en .py
    (source synthétisée, tools/synthe.py), le script est relancé. Lève ValueError si le mod ignorerait un son."""
    table = model.setdefault("phynaria_sounds", {})
    for nom, chemin in sons.items():
        if not NOM_SON.fullmatch(nom):
            raise ValueError(f"nom de son invalide : {nom!r} (attendu [a-z0-9_]{{1,32}})")
        chemin = os.path.abspath(chemin)
        src = os.path.splitext(chemin)[0] + ".py"
        if refabriquer and os.path.exists(src) and (not os.path.exists(chemin) or os.path.getmtime(src) > os.path.getmtime(chemin)):
            ici = os.getcwd()
            try:
                runpy.run_path(src, run_name="__main__")      # le script se place dans son dossier
            finally:
                os.chdir(ici)
        data = open(chemin, "rb").read()
        try:
            info = lire_ogg(data)
        except ValueError as e:
            raise ValueError(f"son {nom} ({chemin}) refusé par le mod : {e}")
        table[nom] = "data:audio/ogg;base64," + base64.b64encode(data).decode()
        print(f"son embarqué : {nom} ({info['duree']:.2f} s, {info['frequence']} Hz, {info['octets'] / 1024:.1f} Ko)")
    if len(table) > MAX_SONS:
        raise ValueError(f"{len(table)} sons embarqués (au plus {MAX_SONS})")
    return model


def cle_son(t, nom):
    """Clé de la piste Effects (format Blockbench) qui joue le son `nom` (embarqué ou Minecraft) à l'instant t."""
    return {"channel": "sound", "data_points": [{"effect": nom, "file": ""}], "time": t}


def resoudre_son(effet, table):
    """Comme le mod (BbAnimation.readSounds puis CosmeticAnimator.sounds) : nom nettoyé, en minuscules, préfixé de
    « minecraft: » s'il n'a pas d'espace de noms ; s'il commence par « minecraft: » et que la suite est dans la table
    embarquée, le son embarqué est joué (il passe avant un son du jeu de même nom) ; sinon un son du jeu ou d'un pack.
    Renvoie ("invalide" | "embarque" | "minecraft" | "inconnu", nom)."""
    e = (effet or "").strip().lower()
    if not ID_SON.fullmatch(e):
        return "invalide", e
    if ":" not in e:
        e = "minecraft:" + e
    if e.startswith("minecraft:") and e[10:] in table:
        return "embarque", e[10:]
    if e.startswith("minecraft:") and e[10:] in sons_minecraft():
        return "minecraft", e[10:]
    return "inconnu", e


def controler_sons(model):
    """Pour le vérificateur : (erreurs, alertes, infos), listes de textes."""
    erreurs, alertes, infos = [], [], []
    brut = model.get("phynaria_sounds")
    table = {}
    if brut is not None and not isinstance(brut, dict):
        erreurs.append("phynaria_sounds doit être un objet {nom: data:audio/ogg;base64,…}")
        brut = {}
    for nom, uri in (brut or {}).items():
        n = nom.strip().lower()
        if not NOM_SON.fullmatch(n) or n != nom:
            erreurs.append(f"son embarqué {nom!r} : nom invalide (attendu [a-z0-9_]{{1,32}})")
            continue
        if len(table) >= MAX_SONS:
            erreurs.append(f"son embarqué {nom} : plus de {MAX_SONS} sons, ignoré par le mod")
            continue
        try:
            info = lire_ogg(_decoder(uri if isinstance(uri, str) else ""))
        except ValueError as e:
            erreurs.append(f"son embarqué {nom} ignoré par le mod : {e}")
            continue
        table[n] = info
        infos.append(f"son embarqué {n} : {info['duree']:.2f} s, {info['frequence']} Hz, mono, {info['octets'] / 1024:.1f} Ko")
        if info["octets"] > CIBLE_OCTETS:
            alertes.append(f"son embarqué {n} : {info['octets'] / 1024:.0f} Ko (> {CIBLE_OCTETS // 1024} Ko visés)")
    joues = set()
    for an in model.get("animations", []):
        for b in an.get("animators", {}).values():
            for k in b.get("keyframes", []):
                if k.get("channel") != "sound":
                    continue
                for dp in k.get("data_points", []):
                    sorte, nom = resoudre_son(dp.get("effect", ""), table)
                    if sorte == "invalide":
                        erreurs.append(f"{an['name']} : son {dp.get('effect')!r} au nom invalide (ignoré par le mod)")
                    elif sorte == "inconnu" and not nom.startswith("minecraft:"):
                        infos.append(f"{an['name']} : son {nom} d'un pack de ressources du serveur (guide 6.5 ; muet sans le pack)")
                    elif sorte == "inconnu":
                        alertes.append(f"{an['name']} : son {dp.get('effect')!r} ni embarqué ni dans Minecraft (muet sauf pack de ressources)")
                    elif sorte == "embarque":
                        joues.add(nom)
    for n in sorted(set(table) - joues):
        alertes.append(f"son embarqué {n} jamais joué (poids inutile)")
    return erreurs, alertes, infos
