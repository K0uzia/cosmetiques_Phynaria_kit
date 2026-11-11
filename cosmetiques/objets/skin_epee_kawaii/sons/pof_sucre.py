"""Pof de sucre (skin_epee_kawaii, event_hit) : son original synthétisé, aucun échantillon extérieur.
Petit « pof » mou de guimauve (souffle grave très court), une seule note de célesta (mi 6) et deux tintements aigus qui
s'éteignent avec la bouffée de cœurs (0,45 s). Court et doux : il joue à chaque coup qui touche, par-dessus le son du jeu.
Clé à 0,04 s dans event_hit. Écrit pof_sucre.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.5
rng = S.seed(31)
t = S.temps(D)
x = np.zeros_like(t)
pof = S.passe_bande(S.bruit(0.05, rng), 160, 620) * S.enveloppe(S.temps(0.05), 0.003, 0.016)
S.place(x, pof / np.max(np.abs(pof)), 0.0, gain=0.6)
S.place(x, S.cloche(1318.5, 0.45, decroissance=0.2), 0.012, gain=0.7)
for t0, f, g in ((0.07, 3520.0, 0.22), (0.13, 4186.0, 0.16)):
    S.place(x, S.cloche(f, 0.2, decroissance=0.06, partiels=((1, 1.0), (2.0, 0.2))), t0, gain=g)
x = S.reverb(x, 0.3, 0.14, rng)[:len(t)]
S.ecrire("pof_sucre.ogg", x, sr=S.SR)
