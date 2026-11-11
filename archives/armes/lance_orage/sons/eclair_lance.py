"""Éclair de la lance (lance_orage, attack) : son original synthétisé, aucun échantillon extérieur.
Crépitement électrique qui se charge pendant l'élan (0–0,19 s), claquement sec et court au coup (0,19 s : impact et arcs),
petit coup grave sous le claquement, puis crépitement qui s'éteint avec les arcs (0,44 s). Pas de tonnerre (trop fort,
fiche orage.md). Clé à 0 s dans attack. Écrit eclair_lance.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.75
rng = S.seed(31)
t = S.temps(D)
T_COUP = 0.19
# crépitement : impulsions denses, bande 1,5–8 kHz ; montée jusqu'au coup, décroissance ensuite
crep = S.passe_bande(S.impulsions(D, 900, rng), 1500, 8000)
env_c = np.where(t < T_COUP, (t / T_COUP) ** 1.5 * 0.55, np.exp(-(t - T_COUP) / 0.12))
crep = crep * env_c
# bourdonnement d'arc : dent de scie à 120 Hz filtrée, seulement autour du coup
arc = S.passe_bande(((t * 120) % 1.0 - 0.5), 200, 2500) * np.exp(-np.abs(t - T_COUP - 0.05) / 0.08)
# claquement : bruit blanc très bref (6 ms) + petit coup grave qui descend (air chauffé)
clac = np.zeros_like(t)
n = int(0.006 * S.SR)
S.place(clac, rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 4)), T_COUP)
tc = S.temps(0.25)
S.place(clac, 0.6 * np.sin(2 * np.pi * (90 - 120 * tc) * tc) * np.exp(-tc / 0.05), T_COUP)
x = 0.55 * crep / np.max(np.abs(crep)) + 0.25 * arc / np.max(np.abs(arc)) + 1.0 * clac / np.max(np.abs(clac))
x = S.reverb(x, 0.35, 0.15, rng)[:len(t)]
S.ecrire("eclair_lance.ogg", x, sr=S.SR)
