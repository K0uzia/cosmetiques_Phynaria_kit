"""Descente des anneaux (effet_stellaire_anneaux, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Cinq glissements métalliques qui descendent (bande de souffle qui glisse vers le grave + bourdon du métal qui baisse),
chacun finit par un choc sourd et une petite résonance d'anneau quand l'anneau se pose (0,65 s puis toutes les 0,22 s).
Clé à 0,1 s dans depart et 0,15 s dans arrivee (anneaux posés à 0,75 s + 0,22 k, resp. 0,8 s + 0,22 k).
Écrit anneaux_descente.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 2.2
rng = S.seed(71)
x = np.zeros(int(D * S.SR))
for k in range(5):
    tp = 0.65 + 0.22 * k                       # pose de l'anneau k
    t0 = tp - 0.6                              # début de sa chute
    # glissement : souffle filtré qui descend, qui enfle vers la pose
    a = S.souffle_balaye(0.6, 2600, 700, rng, largeur=0.9)
    a *= np.linspace(0, 1, len(a)) ** 1.6
    S.place(x, a, t0, gain=0.35)
    # bourdon métallique qui baisse (deux partiels inharmoniques)
    tt = S.temps(0.6)
    f = 330 * (1 - 0.25 * tt / 0.6) * (1 + 0.04 * k)
    b = (np.sin(2 * np.pi * np.cumsum(f) / S.SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(f * 2.76) / S.SR))
    S.place(x, b * (tt / 0.6) ** 2, t0, gain=0.12)
    # choc sourd à la pose
    tt = S.temps(0.3)
    S.place(x, np.sin(2 * np.pi * (85 + 50 * np.exp(-tt / 0.03)) * tt) * S.enveloppe(tt, 0.002, 0.06), tp, gain=0.7)
    # résonance de l'anneau (métal lourd, partiels inharmoniques, s'éteint vite)
    S.place(x, S.cloche(240 * (1 + 0.05 * k), 0.9, decroissance=0.35,
                        partiels=((1, 1.0), (2.32, 0.5), (4.25, 0.25), (6.8, 0.1)), desaccord=1.5), tp + 0.004, gain=0.28)
x = S.reverb(x, 0.8, 0.25, rng)[:len(x)]
S.ecrire("anneaux_descente.ogg", x, sr=S.SR)
