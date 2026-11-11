"""La couronne de sang s'ouvre et révèle le joueur (effet_admin) : son original synthétisé. Inspiration grave qui enfle
(souffle balayé vers le haut, nappe de quinte basse), puis éclat mouillé à l'ouverture (bruit filtré bref + choc sourd) et
longue retombée. Écrit sang_revele.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 2.0
rng = S.seed(58)
t = S.temps(D)
T0 = 0.55
monte = S.souffle_balaye(D, 150, 900, rng, largeur=0.9)
monte *= np.clip(t / T0, 0, 1) ** 2 * (t < T0 + 0.02)
x = 0.5 * monte / np.max(np.abs(monte))
nappe = sum(np.sin(2 * np.pi * f * t + k) for k, f in enumerate((55.0, 82.4, 110.0)))
x += 0.45 * nappe * np.clip(t / T0, 0, 1) * np.exp(-np.maximum(t - T0, 0) / 0.7)
tt = S.temps(0.5)
eclat = S.passe_bande(S.bruit(0.5, rng), 300, 2200) * np.exp(-tt / 0.06)
choc = np.sin(2 * np.pi * np.cumsum(90 * (40 / 90) ** (tt / 0.5)) / S.SR) * np.exp(-tt / 0.18)
S.place(x, 0.8 * eclat / np.max(np.abs(eclat)) + choc, T0)
x = S.reverb(x, 1.0, 0.35, rng)[:len(t)]
S.ecrire("sang_revele.ogg", x, crete_db=-7.5)
