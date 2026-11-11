"""Carillon céleste (diademe_berenice, event_equip) : son original synthétisé, aucun échantillon extérieur.
Trois notes de verre qui montent (mi 6, sol dièse 6, si 6 : accord de mi majeur, tonalité de l'ensemble Bérénice),
attaque douce, partiels presque harmoniques (célesta, verre), petite réverbération. Clé à 0,9 s : la pierre s'allume.
Écrit carillon_celeste.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.7
rng = S.seed(11)
x = np.zeros(int(D * S.SR))
for i, (f, g) in enumerate(((1318.5, 1.0), (1661.2, 0.8), (1975.5, 0.7))):
    S.place(x, S.cloche(f, 1.3, decroissance=0.55, desaccord=0.8), 0.12 * i, gain=g)
# halo : la tonique une octave plus bas, très douce, qui tient la fin
S.place(x, S.cloche(659.3, 1.4, decroissance=0.8, partiels=((1, 1.0), (2.0, 0.2))), 0.0, gain=0.25)
x = S.reverb(x, 0.8, 0.3, rng)[:len(x)]
S.ecrire("carillon_celeste.ogg", x, sr=S.SR)
