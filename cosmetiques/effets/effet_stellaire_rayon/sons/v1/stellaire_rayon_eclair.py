"""Éclair du faisceau (effet_stellaire_rayon, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
La colonne tombe du ciel : un souffle aigu qui descend (0–0,35 s), puis l'impact au sol (0,35 s dans le son) : coup sourd
doux, éclat cristallin bref (trois partiels froids) et chuintement lumineux qui s'éteint.
Clé à 0,0 s dans depart et arrivee (impact au sol à 0,35 s). Écrit rayon_eclair.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D, TI = 1.7, 0.35
rng = S.seed(71)
x = np.zeros(int(D * S.SR))
# chute : souffle qui descend de l'aigu vers le médium, de plus en plus fort
a = S.souffle_balaye(TI + 0.03, 7000, 1400, rng, largeur=1.0)
S.place(x, a * np.linspace(0.15, 1, len(a)) ** 1.5, 0.0, gain=0.7)
# impact : coup sourd (sinus qui glisse vers le grave)
tt = S.temps(0.5)
S.place(x, np.sin(2 * np.pi * (60 + 90 * np.exp(-tt / 0.03)) * tt) * S.enveloppe(tt, 0.002, 0.12), TI, gain=0.8)
# éclat cristallin froid
for f, g in ((1568, 0.35), (2349, 0.28), (3520, 0.2)):
    S.place(x, S.cloche(f, 1.1, decroissance=0.5, desaccord=2.0), TI, gain=g)
# chuintement lumineux : bruit aigu qui s'éteint, petits grains scintillants
t = S.temps(D)
ch = S.passe_bande(S.bruit(D, rng), 4000, 11000) * np.where(t > TI, np.exp(-(t - TI) / 0.35), 0)
x += ch * 0.25
sc = S.passe_bande(S.impulsions(D, 260, rng, 0.0009), 5000, 12000) * np.where(t > TI, np.exp(-(t - TI) / 0.5), 0)
x += sc * 0.35
x = S.reverb(x, 0.8, 0.25, rng)[:len(x)]
S.ecrire("stellaire_rayon_eclair.ogg", x, sr=S.SR)
