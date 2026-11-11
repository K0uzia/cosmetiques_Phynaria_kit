"""Extinction v2 (effet_stellaire_rayon, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Caractère d'un « faisceau de transport » (mesures : .claude/references/effets/rayon-teleportation.md, Sons) : le faisceau
se resserre et se coupe (0–0,15 s) : « zip » bref qui tombe de 11 kHz vers 2,5 kHz, nappe de souffle coupée net, coup
mat (120 → 55 Hz), puis la traîne scintillante 2–7 kHz qui s'efface en ~0,8 s. Clé à T_OFF − 0,03. Ancienne version : v1/."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import synthe as S
import _faisceau as F

D, TF = 1.6, 0.12
rng = S.seed(173)
t = S.temps(D)
x = np.zeros(len(t))
# nappe présente au début, coupée net à TF
cut = np.clip(t / 0.01, 0, 1) * np.where(t < TF, 1.0, np.exp(-(t - TF) / 0.04))
x += F.nappe(D, rng) * cut * 0.4
# zip bref
z = F.zip_descendant(0.5, 11000, 2000, 0.06, largeur=1000, rng=rng)
S.place(x, z * S.enveloppe(S.temps(0.5), 0.01, 0.12), 0.0, gain=0.6)
# coup mat
S.place(x, F.coup(0.5, 120, 55, 0.03, 0.12), TF, gain=0.7)
# traîne scintillante aiguë
v = np.maximum(t - TF, 0)
tr = S.passe_bande(F.scintillement(D, rng, vitesse=35), 1800, 9000) + 0.4 * S.passe_bande(S.bruit(D, rng), 2000, 7000)
x += tr * np.where(t < TF, (t / TF) ** 2, 1.0) * np.exp(-v / 0.32) * 0.9
x = S.reverb(x, 0.7, 0.22, rng)[:len(x)]
S.ecrire("stellaire_rayon_extinction.ogg", x, sr=S.SR)
