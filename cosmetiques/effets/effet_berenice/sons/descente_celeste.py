"""Descente céleste (effet_berenice, arrivee) : son original synthétisé, aucun échantillon extérieur.
Un scintillement qui descend (le joueur traverse le ciel ouvert), deux battements d'ailes feutrés, puis le contact :
une cloche grave et douce en mi avec sa quinte, et un souffle qui s'étale comme l'onde au sol.
Clé à 1,8 s dans arrivee : le contact (1,2 s dans le son) tombe à 3,0 s, quand le joueur se pose.
Écrit descente_celeste.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 2.6
TC = 1.2                                   # le contact
rng = S.seed(31)
x = np.zeros(int(D * S.SR))
# scintillement qui descend
for i, f in enumerate((3322.4, 2637.0, 1975.5, 1661.2, 1318.5)):
    S.place(x, S.cloche(f, 0.7, decroissance=0.25, desaccord=0.9), 0.04 + 0.17 * i, gain=0.3)
# deux battements d'ailes : souffles graves courts
for tb in (0.35, 0.8):
    w = S.souffle_balaye(0.38, 350, 900, rng, largeur=1.4)
    S.place(x, w * np.sin(np.pi * S.temps(0.38) / 0.38) ** 2 * 0.55, tb)
# contact : cloche grave et quinte, souffle qui s'étale
for f, g in ((329.6, 1.0), (493.9, 0.55), (659.3, 0.45), (1318.5, 0.2)):
    S.place(x, S.cloche(f, 1.4, decroissance=0.6, partiels=((1, 1.0), (2.0, 0.3), (3.01, 0.08))), TC, gain=g)
on = S.souffle_balaye(1.0, 1200, 300, rng, largeur=1.2)
S.place(x, on * S.enveloppe(S.temps(1.0), 0.03, 0.3) * 0.4, TC)
x = S.reverb(x, 1.0, 0.3, rng)[:len(x)]
S.ecrire("descente_celeste.ogg", x, sr=S.SR)
