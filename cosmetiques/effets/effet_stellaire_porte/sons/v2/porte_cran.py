"""Verrouillage d'un cran (effet_stellaire_porte, charge et depart) : son original synthétisé, aucun échantillon extérieur.
« Clac » mécanique lourd : claquement sec large bande (métal contre métal), choc grave du pêne qui tombe 40 ms après,
courte résonance de métal épais qui s'éteint vite. Court (0,55 s) pour être rejoué à chaque cran (8 fois dans la charge,
toutes les 0,29 s, une fois dans le départ). Écrit porte_cran.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.55
rng = S.seed(95)
x = np.zeros(int(D * S.SR))
tc = S.temps(0.2)
clac = S.passe_bande(S.bruit(0.2, rng), 1200, 8000) * S.enveloppe(tc, 0.0008, 0.012)
S.place(x, clac, 0.0, gain=0.8)
S.place(x, S.passe_bande(S.bruit(0.2, rng), 300, 1500) * S.enveloppe(tc, 0.001, 0.03), 0.0, gain=0.5)
tp = S.temps(0.35)
choc = np.sin(2 * np.pi * (78 + 70 * np.exp(-tp / 0.015)) * tp) * S.enveloppe(tp, 0.002, 0.06)
S.place(x, choc, 0.04, gain=1.0)
S.place(x, S.passe_bande(S.bruit(0.15, rng), 80, 400) * S.enveloppe(S.temps(0.15), 0.001, 0.03), 0.04, gain=0.6)
S.place(x, S.cloche(260, 0.45, decroissance=0.12, partiels=((1, 1.0), (2.37, 0.5), (3.85, 0.25), (5.4, 0.1)), desaccord=1.4),
        0.002, gain=0.18)
x = S.reverb(x, 0.4, 0.18, rng)[:len(x)]
S.ecrire("porte_cran.ogg", x, sr=S.SR)
