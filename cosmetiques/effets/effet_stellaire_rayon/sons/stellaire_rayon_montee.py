"""Montée v2 (effet_stellaire_rayon, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Caractère d'un « faisceau de transport » (mesures : .claude/references/effets/rayon-teleportation.md, Sons) : la nappe de
souffle et le scintillement grésillant enflent (0–1,0 s, papillotement de plus en plus rapide), puis au sommet (1,0 s dans
le son : le corps part au départ, apparaît à l'arrivée) un « zip » qui tombe de 16 kHz vers ~2,5 kHz en ~0,45 s en
ralentissant, avec un petit coup grave, et une traîne scintillante centrée sur 2–7 kHz qui s'éteint en ~1 s.
Clé à T_HIDE − 1,0 (départ) et T_APP − 1,0 (arrivée). Ancienne version : v1/."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import synthe as S
import _faisceau as F

D, TP = 2.5, 1.0
rng = S.seed(172)
t = S.temps(D)
x = np.zeros(len(t))
u = np.clip(t / TP, 0, 1)
v = np.maximum(t - TP, 0)
# enflure puis traîne
env = np.where(t < TP, u ** 1.8, np.exp(-v / 0.09) * 0.55 + 0.45 * np.exp(-v / 0.5))
sc_lent, sc_vif = F.scintillement(D, rng, vitesse=14), F.scintillement(D, rng, vitesse=45)
sc = sc_lent * (1 - u) + sc_vif * u
x += sc * env * 1.5
nap = F.nappe(D, rng)
# après le sommet la nappe perd son grave : traîne 2–7 kHz
nap_aigu = S.passe_bande(nap, 2000, 7000)
x += np.where(t < TP, nap, nap_aigu * 1.3) * env * 0.45
# le « zip » au sommet (commence 30 ms avant)
z = F.zip_descendant(0.8, 16000, 1500, 0.17, rng=rng)
tz = S.temps(0.8)
S.place(x, z * S.enveloppe(tz, 0.03, 0.35), TP - 0.03, gain=0.5)
# petit coup grave au sommet
S.place(x, F.coup(0.7, 140, 58, 0.04, 0.22), TP, gain=0.45)
x = S.reverb(x, 0.8, 0.22, rng)[:len(x)]
S.ecrire("stellaire_rayon_montee.ogg", x, sr=S.SR)
