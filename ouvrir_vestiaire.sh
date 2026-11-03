#!/usr/bin/env bash
# Équivalent Linux de ouvrir_vestiaire.bat : lance le serveur local du Vestiaire et ouvre la page.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
        exec "$py" tools/serve_vestiaire.py "$@"
    fi
done
echo "Python est introuvable. Installez Python 3 (ex. : sudo apt install python3), puis relancez ce fichier."
read -rp "Appuyez sur Entrée pour fermer..." _
exit 1
