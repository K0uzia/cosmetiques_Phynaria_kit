"""Retour des anneaux (effet_stellaire_anneaux, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Cinq souffles métalliques qui montent (le dernier anneau arrivé part le premier, un toutes les 0,2 s), chacun avec un
bourdon qui s'élève et s'éloigne, de plus en plus faible.
Clé à 2,8 s dans depart et 2,85 s dans arrivee. Écrit anneaux_retour.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.8
rng = S.seed(73)
x = np.zeros(int(D * S.SR))
for k in range(5):
    t0 = 0.05 + 0.2 * k
    g = 1.0 - 0.12 * k
    # petit décrochage métallique au départ
    S.place(x, S.cloche(260 * (1 - 0.04 * k), 0.4, decroissance=0.15,
                        partiels=((1, 1.0), (2.32, 0.5), (4.25, 0.2)), desaccord=1.5), t0, gain=0.18 * g)
    a = S.souffle_balaye(0.65, 600, 2800, rng, largeur=0.9)
    env = np.sin(np.pi * np.linspace(0, 1, len(a))) ** 1.5
    S.place(x, a * env, t0, gain=0.33 * g)
    tt = S.temps(0.65)
    f = 250 * (1 + 0.35 * tt / 0.65) * (1 + 0.03 * k)
    b = np.sin(2 * np.pi * np.cumsum(f) / S.SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(f * 2.76) / S.SR)
    S.place(x, b * env[:len(b)], t0, gain=0.1 * g)
x = S.reverb(x, 0.8, 0.28, rng)[:len(x)]
S.ecrire("anneaux_retour.ogg", x, sr=S.SR)
