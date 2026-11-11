#!/usr/bin/env python3
"""Serveur local du Vestiaire : la page se met à jour seule dès qu'un cosmétique est ajouté ou modifié.
Usage : python tools/serve_vestiaire.py [port]   (ou double-clic sur ouvrir_vestiaire.bat). Accessible depuis cette machine uniquement.
Allègements : page, données et .bbmodel compressés (gzip) ; fichiers versionnés (?v=) gardés en cache par le navigateur ;
vignettes servies en WebP si Pillow est installé (repli : le PNG d'origine).
Mode édition (tools/edition.py) : /api/edition/… lit et enregistre fiches, statuts et ensembles ; requêtes acceptées
seulement depuis la page servie ici (hôte 127.0.0.1 ou localhost, même origine, JSON)."""
import gzip, importlib, io, json, os, sys, threading, webbrowser
from collections import OrderedDict
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_index
import edition

try:
    from PIL import Image
except ImportError:          # Pillow absent : vignettes en PNG, rien d'autre ne change
    Image = None

verrou = threading.Lock()
derniere = [None]
SUIVIS = ("prix", "objet", "particules", "fiche", "exporter", "gen_index", "edition")   # outils rechargés s'ils changent


def _dates():
    ici = os.path.dirname(os.path.abspath(__file__))
    return tuple(os.path.getmtime(os.path.join(ici, n + ".py")) for n in SUIVIS)


_mtime = [_dates()]
_memoire = OrderedDict()     # (genre, chemin, mtime, taille) -> octets ; petit cache LRU des fichiers compressés ou convertis
_memoire_verrou = threading.Lock()
MEMOIRE_MAX = 96 * 1024 * 1024
COMPRESSIBLES = (".bbmodel", ".json", ".js", ".css", ".html", ".txt")


def a_jour():
    """Recharge les outils (gen_index.py, edition.py, fiche.py…) s'ils ont changé depuis le lancement."""
    m = _dates()
    if m != _mtime[0]:
        for n in SUIVIS:              # dépendances d'abord : gen_index et edition en dernier
            if n in sys.modules:
                importlib.reload(sys.modules[n])
        _mtime[0] = m


def en_memoire(genre, chemin, fabriquer):
    st = os.stat(chemin)
    cle = (genre, chemin, st.st_mtime_ns, st.st_size)
    with _memoire_verrou:
        if cle in _memoire:
            _memoire.move_to_end(cle)
            return _memoire[cle]
    octets = fabriquer(chemin)
    with _memoire_verrou:
        _memoire[cle] = octets
        while sum(len(v) for v in _memoire.values()) > MEMOIRE_MAX and len(_memoire) > 1:
            _memoire.popitem(last=False)
    return octets


def gz(chemin):
    with open(chemin, "rb") as f:
        return gzip.compress(f.read(), 6)


def webp(chemin):
    with Image.open(chemin) as im:
        b = io.BytesIO()
        im.save(b, "WEBP", quality=82, method=4)
        return b.getvalue()


class Vestiaire(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=gen_index.ROOT, **k)

    def log_message(self, *a):
        pass

    def accepte(self, quoi):
        return quoi in self.headers.get("Accept-Encoding" if quoi == "gzip" else "Accept", "")

    def end_headers(self):
        p = urlparse(self.path)
        if p.path.endswith(".bbmodel"):
            self.send_header("Content-Disposition", "attachment")
        # Un fichier demandé avec ?v=<version> ne change jamais sous cette adresse : le navigateur le garde.
        if "v=" in p.query and p.path.startswith("/cosmetiques/"):
            self.send_header("Cache-Control", "max-age=31536000, immutable")
        else:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def envoyer(self, corps, type_, compresser=False, vary=None):
        if compresser and self.accepte("gzip"):
            corps = gzip.compress(corps, 6)
            self.send_response(200)
            self.send_header("Content-Encoding", "gzip")
        else:
            self.send_response(200)
        self.send_header("Content-Type", type_)
        self.send_header("Content-Length", str(len(corps)))
        if compresser or vary:
            self.send_header("Vary", vary or "Accept-Encoding")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(corps)

    def do_HEAD(self):
        return self.do_GET()

    def do_GET(self):
        p = urlparse(self.path)
        chemin = unquote(p.path)
        if chemin == "/api/cosmetiques":
            return self.api(parse_qs(p.query).get("s", [""])[0])
        if chemin.startswith("/api/edition/"):
            return self.edition("GET", chemin, parse_qs(p.query))
        if chemin in ("/", "/index.html"):
            with verrou:
                a_jour()
                if hasattr(gen_index, "page_index"):
                    d = gen_index.donnees()
                    page = gen_index.page_index(d)
                    gen_index.ecrire_atomique(gen_index.INDEX, page)   # index.html reste juste aussi hors serveur
                    derniere[0] = d["signature"]
                else:
                    gen_index.ecrire_index()
                    page = None
            if page is not None:
                return self.envoyer(page.encode("utf-8"), "text/html; charset=utf-8", compresser=True)
            self.path = "/index.html"
            return super().do_GET()
        # Seuls les cosmétiques (et leurs copies sous nom propre, livrables/) sont servis, jamais les dossiers cachés ni le reste du dépôt.
        morceaux = chemin.strip("/").split("/")
        if morceaux[0] not in ("cosmetiques", "livrables") or any(m.startswith(".") or m == ".." for m in morceaux):
            return self.send_error(404)
        fichier = os.path.join(gen_index.ROOT, *morceaux)
        if os.path.isfile(fichier):
            try:
                if Image is not None and morceaux[-1] == "vignette.png" and self.accepte("image/webp"):
                    return self.envoyer(en_memoire("webp", fichier, webp), "image/webp", vary="Accept")
                if fichier.endswith(COMPRESSIBLES) and self.accepte("gzip"):
                    corps = en_memoire("gz", fichier, gz)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json" if fichier.endswith((".bbmodel", ".json")) else self.guess_type(fichier))
                    self.send_header("Content-Encoding", "gzip")
                    self.send_header("Content-Length", str(len(corps)))
                    self.send_header("Vary", "Accept-Encoding")
                    self.end_headers()
                    if self.command != "HEAD":
                        self.wfile.write(corps)
                    return
            except (OSError, ValueError):
                pass     # fichier en cours d'écriture : repli sur l'envoi normal
        return super().do_GET()

    def local(self):
        """Hôte et origine locaux seulement : une page d'un autre site ne peut pas écrire dans le dépôt."""
        hote = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        if hote not in ("127.0.0.1", "localhost"):
            return False
        origine = self.headers.get("Origin")
        port = self.server.server_address[1]
        return origine is None or origine in (f"http://127.0.0.1:{port}", f"http://localhost:{port}")

    def repondre_json(self, code, d):
        corps = json.dumps(d, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def do_POST(self):
        chemin = unquote(urlparse(self.path).path)
        if not chemin.startswith("/api/edition/"):
            return self.send_error(404)
        return self.edition("POST", chemin, {})

    def edition(self, methode, chemin, q):
        if not self.local():
            return self.repondre_json(403, {"erreur": "Mode édition réservé à la page du Vestiaire ouverte sur cette machine."})
        try:
            corps = None
            if methode == "POST":
                if "application/json" not in (self.headers.get("Content-Type") or ""):
                    return self.repondre_json(415, {"erreur": "JSON attendu"})
                n = int(self.headers.get("Content-Length") or 0)
                if not 0 < n <= 256 * 1024:
                    return self.repondre_json(413, {"erreur": "requête vide ou trop grosse"})
                corps = json.loads(self.rfile.read(n).decode("utf-8"))
            with verrou:
                a_jour()
                if methode == "GET" and chemin == "/api/edition/piece":
                    return self.repondre_json(200, edition.lire_piece(q.get("nom", [""])[0]))
                if methode == "GET" and chemin == "/api/edition/ensembles":
                    return self.repondre_json(200, edition.lire_ensembles())
                if methode == "POST" and chemin == "/api/edition/piece":
                    notes = edition.enregistrer_piece(corps)
                elif methode == "POST" and chemin == "/api/edition/ensemble":
                    notes = edition.enregistrer_ensemble(corps)
                else:
                    return self.repondre_json(404, {"erreur": "adresse inconnue"})
                derniere[0] = None   # la prochaine demande de la page renverra les données à jour
            return self.repondre_json(200, {"ok": True, "notes": notes})
        except edition.Refus as e:
            return self.repondre_json(400, {"erreur": str(e)})
        except (ValueError, OSError) as e:
            return self.repondre_json(500, {"erreur": f"{type(e).__name__} : {e}"})

    def api(self, signature):
        with verrou:
            a_jour()
            d = gen_index.donnees()
            if d["signature"] != derniere[0]:
                gen_index.ecrire_index(d)   # index.html reste juste aussi hors serveur
                derniere[0] = d["signature"]
        if d["signature"] == signature:
            self.send_response(304)
            self.end_headers()
            return
        self.envoyer(json.dumps(d, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", compresser=True)


def main():
    nombres = [a for a in sys.argv[1:] if a.isdigit()]
    port = int(nombres[0]) if nombres else 8765
    try:
        serveur = ThreadingHTTPServer(("127.0.0.1", port), Vestiaire)
    except OSError:
        # Déjà lancé : on rouvre simplement la page.
        webbrowser.open(f"http://127.0.0.1:{port}/")
        return
    url = f"http://127.0.0.1:{port}/"
    print(f"Vestiaire : {url}  (Ctrl+C pour arrêter)")
    if "--sans-navigateur" not in sys.argv:
        webbrowser.open(url)
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
