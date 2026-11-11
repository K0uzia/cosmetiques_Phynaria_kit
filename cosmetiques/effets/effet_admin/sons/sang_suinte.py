"""Le liquide rouge suinte des jointures et gonfle en goutte (effet_admin) : son original synthétisé. Bruit grave filtré
(écoulement épais) et « glops » visqueux : petites bulles dont la hauteur descend, de plus en plus lourdes ; étirement
grave à la fin (la goutte qui pend). Écrit sang_suinte.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.7
rng = S.seed(47)
t = S.temps(D)
coule = S.souffle_balaye(D, 260, 120, rng, largeur=1.0)
coule *= np.clip(t / 0.4, 0, 1) * np.clip((D - t) / 0.5, 0, 1)
x = 0.5 * coule / np.max(np.abs(coule))
for i, ti in enumerate(np.cumsum(rng.uniform(0.07, 0.16, 12))):
    if ti > D - 0.2:
        break
    d = 0.09 + 0.012 * i
    tt = S.temps(d)
    f0, f1 = rng.uniform(380, 520) - 18 * i, rng.uniform(90, 130)
    ph = 2 * np.pi * np.cumsum(f0 * (f1 / f0) ** (tt / d)) / S.SR
    S.place(x, np.sin(ph) * np.sin(np.pi * tt / d) ** 1.5, ti, gain=0.55 + 0.03 * i)
tt = S.temps(0.7)
etire = np.sin(2 * np.pi * np.cumsum(70 * (45 / 70) ** (tt / 0.7)) / S.SR) * np.sin(np.pi * tt / 0.7)
S.place(x, etire, D - 0.75, gain=0.7)
x = S.passe_bande(x, 50, 2500, pente=0.9)
x = S.reverb(x, 0.5, 0.2, rng)[:len(t)]
S.ecrire("sang_suinte.ogg", x, crete_db=-8.0)
