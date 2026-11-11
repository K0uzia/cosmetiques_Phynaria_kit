"""L'espace se tord (effet_vortex, début du départ) : son original synthétisé, aucun échantillon extérieur. Grondement grave
qui monte (55 -> 104 Hz) en vrillant (vibrato de plus en plus rapide), bande de souffle qui tourne (modulation d'amplitude
qui accélère, effet de phase) et monte de 300 à 1 600 Hz. 1,6 s. Écrit vortex_torsion.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.6
rng = S.seed(71)
t = S.temps(D)
u = t / D
f = 55 * (104 / 55) ** (u ** 1.4)
vib = 3 + 7 * u ** 1.5                                   # vrille de plus en plus rapide
ph = 2 * np.pi * np.cumsum(f * (1 + 0.035 * np.sin(2 * np.pi * np.cumsum(vib) / S.SR))) / S.SR
drone = np.sin(ph) + 0.45 * np.sin(2 * ph + 0.3) + 0.18 * np.sin(3.01 * ph)
souffle = S.souffle_balaye(D, 300, 1600, rng, largeur=1.0)
tour = 0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(2 + 9 * u ** 1.3) / S.SR)
env = np.clip(t / 0.35, 0, 1) * (1 - np.clip((t - (D - 0.25)) / 0.25, 0, 1)) ** 1.5
x = (0.75 * drone / np.max(np.abs(drone)) + 0.5 * souffle / np.max(np.abs(souffle)) * (0.3 + 0.7 * tour) * (0.4 + 0.6 * u)) * env
x = S.reverb(x, 0.5, 0.2, rng)[:len(t)]
S.ecrire("vortex_torsion.ogg", x, crete_db=-8.0)
