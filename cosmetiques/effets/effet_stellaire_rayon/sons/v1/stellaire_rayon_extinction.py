"""Extinction (effet_stellaire_rayon, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Le faisceau se resserre et s'éteint d'un coup : glissando électronique rapide vers le grave (0–0,15 s), souffle qui se
referme, petit coup mat, puis quelques notes de verre de plus en plus rares. Écrit rayon_extinction.ogg."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D, TF = 1.4, 0.15
rng = S.seed(73)
t = S.temps(D)
x = np.zeros(len(t))
tz = S.temps(0.22)
fz = 1900 * (180 / 1900) ** np.clip(tz / TF, 0, 1)
z = np.sin(2 * np.pi * np.cumsum(fz) / S.SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(fz) / S.SR)
S.place(x, z * S.enveloppe(tz, 0.003, 0.08), 0.0, gain=0.45)
w = S.souffle_balaye(0.3, 5000, 600, rng, largeur=1.2)
S.place(x, w * np.hanning(len(w)), 0.0, gain=0.5)
tt = S.temps(0.3)
S.place(x, np.sin(2 * np.pi * (75 + 50 * np.exp(-tt / 0.02)) * tt) * S.enveloppe(tt, 0.002, 0.06), TF, gain=0.6)
for k in range(6):
    tk = TF + 0.08 + 0.85 * (k / 6) ** 1.5 + rng.uniform(-0.02, 0.02)
    S.place(x, S.cloche(rng.choice([1760, 2093, 2637, 3136]), 0.5, decroissance=0.22, desaccord=2.0), tk, gain=0.22 * (1 - k / 8))
x = S.reverb(x, 0.7, 0.25, rng)[:len(x)]
S.ecrire("stellaire_rayon_extinction.ogg", x, sr=S.SR)
