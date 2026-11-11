"""Décharge du marteau (skin_masse_orage, event_hit) : son original synthétisé, aucun échantillon extérieur.
Le coup touche : claquement sec de 5 ms (l'arc qui part de la face), coup sourd et grave qui descend (la tête frappe, l'air
chauffé se dilate), puis crépitement qui s'éteint en 0,4 s avec les arcs en retour (trois petits regains à 60 ms d'écart).
Pas de grondement de tonnerre (trop fort, fiche orage.md). Clé à 0 s dans event_hit. Écrit decharge_masse.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.65
rng = S.seed(47)
t = S.temps(D)
T0 = 0.012
# claquement : bruit blanc très bref, puis un second plus faible 60 ms après (arc en retour)
clac = np.zeros_like(t)
for k, (dt, g) in enumerate(((0.0, 1.0), (0.062, 0.45), (0.124, 0.3))):
    n = int(0.005 * S.SR)
    S.place(clac, g * rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 4)), T0 + dt)
# coup sourd : sinus qui descend de 110 à 55 Hz, court
tc = S.temps(0.3)
coup = np.zeros_like(t)
S.place(coup, np.sin(2 * np.pi * (110 - 90 * tc) * tc) * np.exp(-tc / 0.07), T0)
# crépitement : impulsions denses 1,5–7 kHz, regains aux arcs en retour, décroissance
crep = S.passe_bande(S.impulsions(D, 700, rng), 1500, 7000)
env = np.exp(-np.maximum(t - T0, 0) / 0.16) * (t > T0)
for dt in (0.0, 0.062, 0.124):
    env = env + 0.5 * np.exp(-np.abs(t - T0 - dt - 0.02) / 0.02)
crep = crep * env
x = 0.9 * clac / np.max(np.abs(clac)) + 0.75 * coup / np.max(np.abs(coup)) + 0.45 * crep / np.max(np.abs(crep))
x = S.reverb(x, 0.3, 0.14, rng)[:len(t)]
S.ecrire("decharge_masse.ogg", x, sr=S.SR)
