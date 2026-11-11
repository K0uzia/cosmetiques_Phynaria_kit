"""Présence du masque (effet_admin_neant : le masque blanc émerge du vide) : son original synthétisé. Souffle très grave
qui inspire puis expire (bruit 60-320 Hz modulé lentement), grondement sous-grave désaccordé, sans mélodie.
Écrit neant_presence.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 2.2
rng = S.seed(313)
t = S.temps(D)
souf = S.passe_bande(S.bruit(D, rng), 60, 320)
resp = np.clip(t / 0.9, 0, 1) ** 1.5 * np.exp(-np.maximum(t - 1.0, 0) / 0.5) + 0.5 * np.exp(-((t - 1.45) / 0.3) ** 2)
souf *= resp
gr = np.zeros_like(t)
for f, a in ((36, 1.0), (36.6, 0.8), (54.3, 0.35), (72.8, 0.18)):
    gr += a * np.sin(2 * np.pi * f * t + rng.random() * 6)
gr *= np.clip(t / 0.6, 0, 1) * np.exp(-np.maximum(t - 1.3, 0) / 0.45)
x = souf / np.max(np.abs(souf)) + 0.55 * gr / np.max(np.abs(gr))
x = S.reverb(x, 1.0, 0.3, rng)[:len(t)]
S.ecrire("neant_presence.ogg", x, crete_db=-8.0)
