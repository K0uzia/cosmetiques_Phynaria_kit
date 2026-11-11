"""Éclair du faisceau v2 (effet_stellaire_rayon, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Caractère d'un « faisceau de transport » (mesures : .claude/references/effets/rayon-teleportation.md, Sons) : la colonne
tombe (0–0,35 s, souffle qui descend et grossit), puis à l'impact (0,35 s) un « whoomp » grave (170 → 62 Hz) et une nappe
de souffle large bande (150 Hz–15 kHz) avec un scintillement de partiels fixes qui grésillent, qui baisse d'environ 9 dB
en 0,9 s. Clé à 0,0 s dans depart et arrivee. Ancienne version : v1/."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import synthe as S
import _faisceau as F

D, TI = 2.1, 0.35
rng = S.seed(171)
t = S.temps(D)
x = np.zeros(len(t))
# chute de la colonne : souffle qui descend de l'aigu et grossit jusqu'à l'impact
a = S.souffle_balaye(TI + 0.02, 9000, 2200, rng, largeur=1.3)
S.place(x, a * np.linspace(0.05, 1, len(a)) ** 2, 0.0, gain=0.35)
# impact : coup grave + nappe + scintillement, attaque 15 ms, retombée lente (-9 dB en 0,9 s) puis extinction
u = np.maximum(t - TI, 0)
env = np.where(t < TI, 0, np.clip(u / 0.015, 0, 1) * (0.35 + 0.65 * np.exp(-u / 0.12)) * np.exp(-u / 0.75))
x += F.nappe(D, rng) * env * 0.55
x += F.scintillement(D, rng, vitesse=28) * env * 1.6
S.place(x, F.coup(1.0, 170, 62, 0.05, 0.35), TI, gain=0.9)
x = S.reverb(x, 0.9, 0.22, rng)[:len(x)]
S.ecrire("stellaire_rayon_eclair.ogg", x, sr=S.SR)
