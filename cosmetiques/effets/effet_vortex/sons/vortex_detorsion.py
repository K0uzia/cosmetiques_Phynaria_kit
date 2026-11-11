"""Ouverture du vortex à l'arrivée (effet_vortex) : son original synthétisé. Petit déchirement sec (un point qui s'ouvre),
puis le grondement de la torsion à rebours : la hauteur descend (104 -> 58 Hz) et la vrille ralentit, souffle qui tourne en
descendant de 1 600 à 350 Hz. 1,4 s. Écrit vortex_detorsion.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.4
rng = S.seed(74)
t = S.temps(D)
u = t / D
x = np.zeros_like(t)
n = int(0.05 * S.SR)
dech = S.passe_bande(rng.standard_normal(n), 900, 6000) * np.exp(-np.arange(n) / (n / 4))
S.place(x, dech / np.max(np.abs(dech)), 0.0, gain=0.5)
f = 104 * (58 / 104) ** (u ** 0.7)
vib = 9 - 6 * u
ph = 2 * np.pi * np.cumsum(f * (1 + 0.035 * np.sin(2 * np.pi * np.cumsum(vib) / S.SR))) / S.SR
drone = np.sin(ph) + 0.45 * np.sin(2 * ph + 0.3) + 0.18 * np.sin(3.01 * ph)
souffle = S.souffle_balaye(D, 1600, 350, rng, largeur=1.0)
tour = 0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(9 - 7 * u) / S.SR)
env = np.clip(t / 0.08, 0, 1) * (1 - u) ** 1.2
x += (0.7 * drone / np.max(np.abs(drone)) + 0.5 * souffle / np.max(np.abs(souffle)) * (0.3 + 0.7 * tour)) * env
x = S.reverb(x, 0.5, 0.2, rng)[:len(t)]
S.ecrire("vortex_detorsion.ogg", x, crete_db=-8.0)
