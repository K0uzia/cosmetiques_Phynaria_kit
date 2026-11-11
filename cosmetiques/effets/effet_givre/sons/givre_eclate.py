"""Éclatement du cristal (effet_givre, depart) : son original synthétisé, aucun échantillon extérieur.
Clé à 0 s = 0,62 s avant le bris. 0-0,62 s : la glace se fend (crépitement qui s'accélère, gémissement grave de la glace
sous tension), validé en jeu. La brisure synthétisée a été refusée (« sois logique, des sons de glace/vitre qui se brise ») :
le son s'arrête au bris, où le générateur joue block.glass.break du jeu. Écrit givre_eclate.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D, TB = 0.72, 0.62
rng = S.seed(57)
t = S.temps(D)
# crépitement de fissure : densité croissante jusqu'au bris
crep = np.zeros_like(t)
for k in range(6):
    a, b = TB * k / 6, TB * (k + 1) / 6
    seg = S.impulsions(b - a, 120 + 260 * k, rng, duree_imp=0.0018)
    S.place(crep, seg, a, gain=0.35 + 0.13 * k)
crep = S.passe_bande(crep, 1800, 9000)
crep *= np.where(t < TB, 1.0, np.exp(-(t - TB) / 0.05))
# gémissement de la glace sous tension (grave, montant)
f = 70 + 50 * np.clip(t / TB, 0, 1)
gem = np.sin(2 * np.pi * np.cumsum(f) / S.SR) * np.clip(t / TB, 0, 1) ** 2 * np.where(t < TB, 1, np.exp(-(t - TB) / 0.04))
gem = S.passe_bande(gem + 0.3 * np.sign(gem) * np.abs(gem) ** 3, 60, 900)
x = 0.7 * crep / np.max(np.abs(crep)) + 0.45 * gem / np.max(np.abs(gem))
x = S.reverb(x, 0.4, 0.2, rng)[:len(t)]
S.ecrire("givre_eclate.ogg", x, sr=S.SR, crete_db=-12.0)   # niveau de la fissure validée (elle était sous la brisure)
