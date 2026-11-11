"""Nuage de paillettes (skin_arc_kawaii, event_release) : son original synthétisé, aucun échantillon extérieur.
Petit « pof » mou de guimauve (bruit grave très court), puis deux notes de célesta qui montent (sol 6, do 7) et une pluie
de tintements aigus qui s'éteint avec le nuage modélisé (0,7 s). Doux, court : il s'ajoute au son de l'arc du jeu.
Clé à 0,02 s dans event_release. Écrit paillettes.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.9
rng = S.seed(77)
t = S.temps(D)
x = np.zeros_like(t)
# pof de guimauve : souffle grave filtré, 40 ms
pof = S.passe_bande(S.bruit(0.06, rng), 180, 700) * S.enveloppe(S.temps(0.06), 0.004, 0.018)
S.place(x, pof / np.max(np.abs(pof)), 0.0, gain=0.55)
# deux notes de célesta qui montent
for t0, f, g in ((0.03, 1568.0, 0.8), (0.11, 2093.0, 0.65)):
    S.place(x, S.cloche(f, 0.7, decroissance=0.32), t0, gain=g)
# pluie de tintements aigus (paillettes), de plus en plus faibles
for k in range(9):
    t0 = 0.16 + 0.055 * k + rng.uniform(-0.015, 0.015)
    f = rng.choice([3136.0, 3520.0, 3951.0, 4186.0])
    S.place(x, S.cloche(f, 0.25, decroissance=0.07, partiels=((1, 1.0), (2.0, 0.2))), t0, gain=0.28 * (1 - k / 11))
x = S.reverb(x, 0.4, 0.18, rng)[:len(t)]
S.ecrire("paillettes.ogg", x, sr=S.SR)
