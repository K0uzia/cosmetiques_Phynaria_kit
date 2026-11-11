"""Fermeture du portail (effet_portail : l'ovale implose) : son original synthétisé. Aspiration : souffle qui gonfle et descend
du médium vers le grave (0,45 s, montée en crescendo comme un son à l'envers), puis un « whoum » sourd et court au moment où
tout se referme en un point, et une poussière de petits tintements qui s'éteint. Écrit portail_ferme.ogg."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.3
rng = S.seed(97)
t = S.temps(D)
x = np.zeros_like(t)
TP = 0.45                                   # instant où le portail se referme en un point
asp = S.souffle_balaye(TP, 3500, 500, rng, largeur=1.0)
asp *= np.linspace(0, 1, len(asp)) ** 2.2
S.place(x, asp / np.max(np.abs(asp)), 0.0, gain=0.6)
tw = S.temps(0.6)
fq = 110 * (0.55 ** (tw / 0.6))
w = np.sin(2 * np.pi * np.cumsum(fq) / S.SR) * np.clip(tw / 0.01, 0, 1) * np.exp(-tw / 0.16)
w += 0.5 * S.passe_bande(rng.standard_normal(len(tw)), 60, 300) * np.exp(-tw / 0.08)
S.place(x, w / np.max(np.abs(w)), TP, gain=0.9)
for k, f in enumerate((2349, 1976, 2637, 1760, 2093)):
    S.place(x, S.cloche(f, 0.45, decroissance=0.12), TP + 0.04 + 0.06 * k, gain=0.07)
x = S.reverb(x, 0.6, 0.25, rng)[:len(t)]
S.ecrire("portail_ferme.ogg", x, sr=S.SR, crete_db=-8.0)
