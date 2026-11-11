"""Expulsion (effet_vortex, arrivée) : son original synthétisé. Souffle qui sort du vortex et enfle (bande qui descend de
3 500 à 600 Hz), puis coup sourd au moment où le joueur se pose (0,95 s : 95 -> 36 Hz) et onde au sol qui s'étale.
1,6 s. Écrit vortex_expulsion.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D, TC = 1.6, 0.95
rng = S.seed(75)
t = S.temps(D)
souffle = S.souffle_balaye(D, 3500, 600, rng, largeur=1.3, morceaux=64)
souffle /= np.max(np.abs(souffle))
env = np.clip(t / TC, 0, 1) ** 1.8 * np.exp(-np.clip(t - TC, 0, None) / 0.18)
x = 0.7 * souffle * env
tc = S.temps(0.6)
f = 36 + 59 * np.exp(-tc / 0.07)
coup = np.sin(2 * np.pi * np.cumsum(f) / S.SR) * np.exp(-tc / 0.17)
S.place(x, coup, TC, gain=1.0)
bf = S.passe_bande(S.bruit(0.5, rng), 80, 900) * np.exp(-S.temps(0.5) / 0.12)
S.place(x, bf / np.max(np.abs(bf)), TC, gain=0.45)
x = S.reverb(x, 0.6, 0.22, rng)[:len(t)]
S.ecrire("vortex_expulsion.ogg", x, crete_db=-7.0)
