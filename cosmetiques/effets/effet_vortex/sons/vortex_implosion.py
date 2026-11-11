"""Implosion en un point (effet_vortex, fin du départ) : son original synthétisé. Clic sec, coup sourd dont la hauteur
tombe (170 -> 38 Hz en 0,18 s), petit souffle grave, puis onde qui ondule et s'éteint (battement lent). 1,2 s.
Écrit vortex_implosion.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.2
rng = S.seed(73)
t = S.temps(D)
x = np.zeros_like(t)
n = int(0.012 * S.SR)
clic = S.passe_bande(rng.standard_normal(n), 1500, 7000) * np.exp(-np.arange(n) / (n / 5))
S.place(x, clic / np.max(np.abs(clic)), 0.0, gain=0.55)
tc = S.temps(0.7)
f = 38 + 132 * np.exp(-tc / 0.06)
coup = np.sin(2 * np.pi * np.cumsum(f) / S.SR) * np.exp(-tc / 0.2)
S.place(x, coup, 0.004, gain=1.0)
bf = S.passe_bande(S.bruit(0.4, rng), 60, 500) * np.exp(-S.temps(0.4) / 0.08)
S.place(x, bf / np.max(np.abs(bf)), 0.004, gain=0.4)
to = S.temps(0.9)
onde = np.sin(2 * np.pi * 70 * to) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * to)) * np.exp(-to / 0.25)
S.place(x, onde, 0.15, gain=0.3)
x = S.reverb(x, 0.6, 0.22, rng)[:len(t)]
S.ecrire("vortex_implosion.ogg", x, crete_db=-7.0)
