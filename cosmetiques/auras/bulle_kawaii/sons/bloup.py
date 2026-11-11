"""Bloup d'apparition (bulle_kawaii, event_equip) : son original synthétisé, aucun échantillon extérieur.
Trois petites bouffées qui montent (bulles qui gonflent l'une après l'autre) : sinus doux dont la hauteur glisse vers le haut,
plus aigus à chaque bouffée, avec un souffle léger. Écrit bloup.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.9
rng = S.seed(5)
x = np.zeros(int(D * S.SR))
for k, (t0, f0) in enumerate(((0.0, 260), (0.22, 340), (0.44, 450))):
    d = 0.18
    t = S.temps(d)
    f = f0 * (1 + 1.1 * (t / d) ** 0.7)
    ph = 2 * np.pi * np.cumsum(f) / S.SR
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
    S.place(x, np.sin(ph) * env, t0, gain=0.8 + 0.1 * k)
tt = S.temps(D)
souffle = S.passe_bande(S.bruit(D, rng), 800, 3000) * np.exp(-((tt - 0.3) / 0.25) ** 2)
x = x + 0.06 * souffle / np.max(np.abs(souffle))
x = S.reverb(x, 0.3, 0.15, rng)[:len(x)]
S.ecrire("bloup.ogg", x)
