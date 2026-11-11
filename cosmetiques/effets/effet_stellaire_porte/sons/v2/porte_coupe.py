"""Coupure de la surface et retour de la porte dans le sol (effet_stellaire_porte, depart et arrivee) : son original
synthétisé, aucun échantillon extérieur. Coupure nette (souffle aspiré très bref qui finit d'un coup + petit choc), puis
la pierre qui redescend : grondement grave et frottement de pierre, qui finit par un choc sourd. Clé à la coupure
(3,93 s dans depart, 2,98 s dans arrivee) ; descente de 0,1 à 0,9–1,1 s après. Écrit porte_coupe.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.5
rng = S.seed(93)
x = np.zeros(int(D * S.SR))
a = S.souffle_balaye(0.16, 600, 5000, rng, largeur=1.0)
a *= np.linspace(0, 1, len(a)) ** 2
S.place(x, a, 0.0, gain=0.6)
tc = S.temps(0.3)
S.place(x, np.sin(2 * np.pi * (70 + 120 * np.exp(-tc / 0.015)) * tc) * S.enveloppe(tc, 0.001, 0.05), 0.16, gain=0.7)
d = 0.95
t = S.temps(d)
env = np.interp(t, [0, 0.1, 0.8, 0.95], [0, 1, 0.9, 0])
gr = S.passe_bande(S.bruit(d, rng), 40, 260) * env
fr = S.passe_bande(S.bruit(d, rng), 400, 2500) * env * (0.6 + 0.4 * np.sin(2 * np.pi * 13 * t) ** 2)
S.place(x, gr, 0.22, gain=0.8)
S.place(x, fr, 0.22, gain=0.18)
S.place(x, np.sin(2 * np.pi * (55 + 40 * np.exp(-tc / 0.03)) * tc) * S.enveloppe(tc, 0.002, 0.09), 1.1, gain=0.6)
x = S.reverb(x, 0.6, 0.18, rng)[:len(x)]
S.ecrire("porte_coupe.ogg", x, sr=S.SR)
