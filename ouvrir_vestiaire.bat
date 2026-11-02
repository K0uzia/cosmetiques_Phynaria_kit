@echo off
cd /d "%~dp0"
where py >nul 2>nul && (py tools\serve_vestiaire.py & goto fin)
where python >nul 2>nul && (python tools\serve_vestiaire.py & goto fin)
where python3 >nul 2>nul && (python3 tools\serve_vestiaire.py & goto fin)
echo Python est introuvable. Installez Python 3, puis relancez ce fichier.
pause
:fin
