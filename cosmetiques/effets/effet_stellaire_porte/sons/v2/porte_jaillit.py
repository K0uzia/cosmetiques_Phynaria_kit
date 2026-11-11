"""Jaillissement de l'eau (effet_stellaire_porte, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Coup sourd à l'ouverture (souffle large bande très bref), puis rugissement d'eau grave qui gonfle avec la gerbe et se
retire (bruit riche en graves modulé en bouillonnement), puis la surface qui ondule : nappe douce et clapotis.
Clé à 1,5 s dans depart, 0 s dans arrivee. Écrit porte_jaillit.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 2.0
rng = S.seed(92)
x = np.zeros(int(D * S.SR))
tt = S.temps(0.5)
S.place(x, np.sin(2 * np.pi * (48 + 80 * np.exp(-tt / 0.05)) * tt) * S.enveloppe(tt, 0.004, 0.18), 0.04, gain=0.9)
S.place(x, S.passe_bande(S.bruit(0.4, rng), 300, 9000) * S.enveloppe(S.temps(0.4), 0.002, 0.06), 0.04, gain=0.5)
# rugissement : gonfle (0,45 s), tient, se retire (fin à 1,1 s)
d = 1.15
t = S.temps(d)
env = np.interp(t, [0, 0.12, 0.5, 0.65, 1.15], [0, 1, 0.9, 0.7, 0])
bouillon = 1 + 0.35 * np.sin(2 * np.pi * 9 * t + 3 * np.sin(2 * np.pi * 2.3 * t))
grave = S.passe_bande(S.bruit(d, rng), 60, 700) * env * bouillon
moyen = S.passe_bande(S.bruit(d, rng), 700, 4000) * env ** 1.5
S.place(x, grave, 0.06, gain=0.9)
S.place(x, moyen, 0.06, gain=0.35)
# surface : nappe douce et clapotis (gouttes)
t2 = S.temps(0.9)
S.place(x, S.passe_bande(S.bruit(0.9, rng), 200, 1500) * np.interp(t2, [0, 0.2, 0.9], [0, 0.4, 0]), 1.05, gain=0.4)
for i in range(14):
    tg = 0.25 + rng.uniform(0, 1.5)
    f = rng.uniform(900, 2400)
    tc = S.temps(0.08)
    S.place(x, np.sin(2 * np.pi * f * (1 + 2.5 * tc) * tc) * S.enveloppe(tc, 0.001, 0.015), tg, gain=0.08)
x = S.reverb(x, 0.8, 0.2, rng)[:len(x)]
S.ecrire("porte_jaillit.ogg", x, sr=S.SR)
