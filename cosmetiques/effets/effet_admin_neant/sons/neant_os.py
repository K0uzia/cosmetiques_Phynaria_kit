"""Os qui raclent (effet_admin_neant : les doigts squelettiques grattent puis percent la fente) : son original synthétisé.
Raclement granuleux (bruit filtré modulé à 28 Hz) et craquements secs d'articulations (claquements résonants 600-1600 Hz).
Écrit neant_os.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.9
rng = S.seed(311)
t = S.temps(D)
rac = S.passe_bande(S.bruit(D, rng), 700, 3800)
gr = (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 28 * t + 3 * np.sin(2 * np.pi * 3 * t)))) * (0.6 + 0.4 * rng.random(len(t)))
rac *= gr * np.clip(t / 0.08, 0, 1) * np.exp(-np.maximum(t - 0.45, 0) / 0.15)
x = 0.5 * rac / np.max(np.abs(rac))
for tk, f in ((0.06, 1250), (0.21, 900), (0.33, 1550), (0.52, 700), (0.61, 1100)):
    n = int(0.06 * S.SR)
    tt = np.arange(n) / S.SR
    clic = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.009) + 0.4 * S.passe_bande(S.bruit(0.06, rng), 1500, 6000) * np.exp(-tt / 0.004)
    S.place(x, clic, tk, gain=0.9)
x = S.reverb(x, 0.35, 0.18, rng)[:len(t)]
S.ecrire("neant_os.ogg", x, crete_db=-10.0)
