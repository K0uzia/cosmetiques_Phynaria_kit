"""Pulsation du regard (effet_admin_neant : deux yeux rouges s'allument dans le noir en trois battements) : son original
synthétisé. Trois battements graves, comme un cœur énorme derrière le ciel : coup sourd (sinus 58 -> 34 Hz qui retombe,
attaque feutrée) suivi d'un second coup plus faible, à 0, 0,4 et 0,8 s (pulsations des yeux) ; sous-grondement qui s'éteint.
Écrit neant_pulse.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.7
rng = S.seed(911)
t = S.temps(D)
x = np.zeros_like(t)


def coup(gain, f0=58.0, f1=34.0, d=0.32):
    tc = S.temps(d)
    f = f1 + (f0 - f1) * np.exp(-tc / 0.05)
    ph = 2 * np.pi * np.cumsum(f) / S.SR
    c = np.sin(ph) * S.enveloppe(tc, 0.006, 0.09)
    c += 0.35 * np.sin(2 * ph + 0.5) * S.enveloppe(tc, 0.004, 0.05)
    feutre = S.passe_bande(S.bruit(d, rng), 60, 260) * S.enveloppe(tc, 0.002, 0.02)
    c += 0.4 * feutre / np.max(np.abs(feutre))
    return gain * c


for tk, g in ((0.0, 1.0), (0.4, 0.92), (0.8, 0.85)):
    S.place(x, coup(g), tk)
    S.place(x, coup(g * 0.45, 50, 32, 0.25), tk + 0.15)
gr = sum(a * np.sin(2 * np.pi * f * t + rng.random() * 6) for f, a in ((31, 1.0), (31.7, 0.8), (46.5, 0.3)))
gr *= np.clip(t / 0.2, 0, 1) * np.exp(-np.maximum(t - 1.0, 0) / 0.25)
x += 0.25 * gr / np.max(np.abs(gr))
x = S.reverb(x, 0.8, 0.22, rng)[:len(t)]
S.ecrire("neant_pulse.ogg", x, crete_db=-7.0)
