"""Passage dans le portail (effet_portail : le joueur traverse l'ovale au départ, en sort à l'arrivée) : son original
synthétisé. Un « chime soufflé » : deux tons doux vers 880 et 1 320 Hz, légèrement désaccordés, qui glissent d'un demi-ton vers
le bas en s'éteignant (0,6 s), sur un souffle qui passe de l'aigu au médium (on traverse une membrane). Écrit portail_passe.ogg."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.0
rng = S.seed(83)
t = S.temps(D)
x = np.zeros_like(t)
glis = 2 ** (-(1 / 12) * np.clip(t / 0.6, 0, 1))
for f, a, d in ((880, 1.0, 0.28), (1320, 0.5, 0.2), (1765, 0.18, 0.12)):
    for s in (-1, 1):
        ph = 2 * np.pi * np.cumsum((f + s * 1.8) * glis) / S.SR
        x += 0.5 * a * np.sin(ph) * S.enveloppe(t, 0.03, d)
so = S.souffle_balaye(0.7, 5200, 1400, rng, largeur=1.1)
so *= np.hanning(len(so))
S.place(x, 0.45 * so / np.max(np.abs(so)), 0.0)
x = S.reverb(x, 0.5, 0.25, rng)[:len(t)]
S.ecrire("portail_passe.ogg", x, sr=S.SR, crete_db=-9.0)
