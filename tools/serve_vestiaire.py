#!/usr/bin/env python3
"""Serveur local du Vestiaire : la page se met à jour seule dès qu'un cosmétique est ajouté ou modifié.
Usage : python tools/serve_vestiaire.py [port]   (ou double-clic sur ouvrir_vestiaire.bat). Accessible depuis cette machine uniquement."""
import json, os, sys, threading, webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_index

verrou = threading.Lock()
derniere = [None]


class Vestiaire(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=gen_index.ROOT, **k)

    def log_message(self, *a):
        pass

    def end_headers(self):
        if urlparse(self.path).path.endswith(".bbmodel"):
            self.send_header("Content-Disposition", "attachment")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        p = urlparse(self.path)
        chemin = unquote(p.path)
        if chemin == "/api/cosmetiques":
            return self.api(parse_qs(p.query).get("s", [""])[0])
        if chemin in ("/", "/index.html"):
            with verrou:
                gen_index.ecrire_index()
            self.path = "/index.html"
            return super().do_GET()
        # Seuls les cosmétiques sont servis, jamais les dossiers cachés ni le reste du dépôt.
        morceaux = chemin.strip("/").split("/")
        if morceaux[0] != "cosmetiques" or any(m.startswith(".") or m == ".." for m in morceaux):
            return self.send_error(404)
        return super().do_GET()

    def api(self, signature):
        with verrou:
            d = gen_index.donnees()
            if d["signature"] != derniere[0]:
                gen_index.ecrire_index(d)   # index.html reste juste aussi hors serveur
                derniere[0] = d["signature"]
        if d["signature"] == signature:
            self.send_response(304)
            self.end_headers()
            return
        corps = json.dumps(d, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
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
