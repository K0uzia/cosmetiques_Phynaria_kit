"""Passage (effet_etincelles, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Le souffle du passage : une bouffée d'air chaud aspirée (bande qui monte puis retombe), un coup sourd doux au moment où
le joueur traverse le plan de l'anneau (0,4 s dans le son), et une gerbe d'étincelles qui crépite.
Clé à 1,9 s dans depart (le joueur franchit l'anneau à 2,3 s), à 0,7 s dans arrivee (il en sort à 1,1 s).
Écrit etincelles_passage.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.3
TP = 0.4
rng = S.seed(52)
x = np.zeros(int(D * S.SR))
# aspiration : bande qui monte jusqu'au passage
a = S.souffle_balaye(TP + 0.05, 250, 1400, rng, largeur=1.4)
S.place(x, a * np.linspace(0, 1, len(a)) ** 2, 0.0, gain=0.8)
# relâche : bande qui retombe
b = S.souffle_balaye(0.8, 1400, 220, rng, largeur=1.4)
S.place(x, b * S.enveloppe(S.temps(0.8), 0.005, 0.25), TP, gain=0.7)
# coup sourd doux (corps grave) au passage
tt = S.temps(0.35)
S.place(x, np.sin(2 * np.pi * (70 + 40 * np.exp(-tt / 0.05)) * tt) * S.enveloppe(tt, 0.004, 0.09), TP, gain=0.6)
# gerbe : crépitement aigu bref
g = S.passe_bande(S.impulsions(0.6, 500, rng, 0.0012), 3000, 10000) * S.enveloppe(S.temps(0.6), 0.005, 0.18)
S.place(x, g, TP, gain=0.45)
x = S.reverb(x, 0.7, 0.22, rng)[:len(x)]
S.ecrire("etincelles_passage.ogg", x, sr=S.SR)
