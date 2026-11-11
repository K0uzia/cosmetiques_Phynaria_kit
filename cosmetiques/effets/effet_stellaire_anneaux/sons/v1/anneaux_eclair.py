"""Éclair des anneaux (effet_stellaire_anneaux, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Bourdon qui monte pendant que la bande de lumière remonte la colonne, onde brillante au plus fort (0,37 s : le joueur
disparaît ou apparaît), puis traîne qui scintille et s'éteint.
Clé à 1,85 s dans depart et 1,8 s dans arrivee. Écrit anneaux_eclair.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.6
TP = 0.37
rng = S.seed(72)
x = np.zeros(int(D * S.SR))
# montée : bourdon dont la hauteur grimpe (glissando) jusqu'au plus fort
tt = S.temps(TP)
f = 140 * 2 ** (2.2 * (tt / TP) ** 1.5)
m = np.sin(2 * np.pi * np.cumsum(f) / S.SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(2 * f) / S.SR) + 0.25 * np.sin(2 * np.pi * np.cumsum(3 * f) / S.SR)
S.place(x, m * (tt / TP) ** 2, 0.0, gain=0.35)
s = S.souffle_balaye(TP, 600, 5000, rng, largeur=1.0)
S.place(x, s * (tt[:len(s)] / TP) ** 2.5, 0.0, gain=0.3)
# onde : coup grave doux + éclat aigu bref
tt = S.temps(0.6)
S.place(x, np.sin(2 * np.pi * (60 + 90 * np.exp(-tt / 0.04)) * tt) * S.enveloppe(tt, 0.003, 0.15), TP, gain=0.8)
e = S.passe_bande(S.bruit(0.5, rng), 2500, 12000) * S.enveloppe(S.temps(0.5), 0.002, 0.07)
S.place(x, e, TP, gain=0.35)
# traîne : accord clair qui scintille et s'éteint
for fr, g in ((880, 0.18), (1318, 0.12), (1760, 0.08)):
    S.place(x, S.cloche(fr, 1.1, decroissance=0.45, desaccord=3.0), TP + 0.01, gain=g)
r = S.passe_bande(S.impulsions(1.0, 220, rng, 0.0008), 4000, 12000) * S.enveloppe(S.temps(1.0), 0.01, 0.3)
S.place(x, r, TP + 0.03, gain=0.25)
x = S.reverb(x, 0.9, 0.3, rng)[:len(x)]
S.ecrire("anneaux_eclair.ogg", x, sr=S.SR)
