"""Alvéoles qui s'allument dans le ciel (effet_admin) : son original synthétisé. Bips graves à deux tons (carré adouci,
filtré), d'abord isolés puis de plus en plus serrés quand les alvéoles pavent le ciel, sur une nappe sourde qui monte.
Écrit alveoles_alarme.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.9
rng = S.seed(31)
t = S.temps(D)
x = np.zeros_like(t)


def bip(f, d):
    tt = S.temps(d)
    sq = np.tanh(3.0 * np.sin(2 * np.pi * f * tt)) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)
    env = np.clip(tt / 0.008, 0, 1) * np.clip((d - tt) / 0.03, 0, 1)
    return S.passe_bande(sq * env, 120, 900, pente=0.8)


instants = [0.0, 0.42, 0.62, 0.78, 0.9, 1.0, 1.08, 1.15, 1.21, 1.27, 1.32]
for i, ti in enumerate(instants):
    f = 196.0 if i % 2 == 0 else 147.0
    S.place(x, bip(f, 0.16 if i < 3 else 0.09), ti, gain=1.0 if i < 3 else 0.7)
nappe = 0.0
for f0 in (73.4, 110.0):
    nappe = nappe + np.sin(2 * np.pi * f0 * t + 0.2 * np.sin(2 * np.pi * 0.7 * t))
nappe *= np.clip((t - 0.3) / 1.1, 0, 1) ** 1.5 * np.clip((D - t) / 0.4, 0, 1)
x += 0.35 * nappe
x = S.reverb(x, 0.9, 0.3, rng)[:len(t)]
S.ecrire("alveoles_alarme.ogg", x, crete_db=-8.0)
