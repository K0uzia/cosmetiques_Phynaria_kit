"""Aspiration (effet_vortex, départ, de 1,1 s à l'implosion) : son original synthétisé. Souffle qui enfle comme un air
avalé à l'envers (crescendo exponentiel, bande qui monte de 500 à 4 500 Hz), grondement sous-jacent qui monte, coupé net
juste avant l'implosion. 1,37 s. Écrit vortex_aspiration.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.37
rng = S.seed(72)
t = S.temps(D)
u = t / D
souffle = S.souffle_balaye(D, 500, 4500, rng, largeur=1.4, morceaux=64)
souffle /= np.max(np.abs(souffle))
f = 48 + 40 * u ** 2
gr = np.sin(2 * np.pi * np.cumsum(f) / S.SR)
gr = gr + 0.3 * np.sin(2 * 2 * np.pi * np.cumsum(f) / S.SR)
cresc = (np.exp(3.2 * u) - 1) / (np.exp(3.2) - 1)
coupe = 1 - np.clip((t - (D - 0.03)) / 0.03, 0, 1)
x = (0.85 * souffle + 0.45 * gr / np.max(np.abs(gr))) * (0.08 + 0.92 * cresc) * coupe
S.ecrire("vortex_aspiration.ogg", x, crete_db=-8.0)
