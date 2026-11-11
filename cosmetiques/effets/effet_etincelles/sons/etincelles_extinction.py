"""Extinction (effet_etincelles, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
L'anneau se resserre : le grésillement s'accélère et monte un peu (0–0,4 s), un dernier claquement d'étincelles quand il se
referme (0,45 s), puis quelques braises qui pétillent de plus en plus rarement et un souffle qui s'éteint.
Clé à 2,95 s dans depart (fermeture à 3,4 s), à 2,45 s dans arrivee (fermeture à 2,9 s). Écrit etincelles_extinction.ogg."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.6
TF = 0.45
rng = S.seed(53)
x = np.zeros(int(D * S.SR))
t = S.temps(D)
# grésillement qui s'accélère jusqu'à la fermeture puis s'éteint
env = (0.4 + 0.6 * np.clip(t / TF, 0, 1)) * np.where(t < TF, 1.0, np.exp(-(t - TF) / 0.12))
x += S.passe_bande(S.impulsions(D, 1100, rng, 0.0011), 3000, 10000) * env * 0.5
# claquement de fermeture
S.place(x, S.passe_bande(S.impulsions(0.12, 600, rng, 0.003), 800, 6000) * S.enveloppe(S.temps(0.12), 0.002, 0.04), TF, gain=0.9)
tt = S.temps(0.25)
S.place(x, np.sin(2 * np.pi * (95 + 60 * np.exp(-tt / 0.04)) * tt) * S.enveloppe(tt, 0.003, 0.06), TF, gain=0.45)
# braises : pétillements de plus en plus rares
for k in range(9):
    tk = TF + 0.1 + 0.9 * (k / 9) ** 1.6 + rng.uniform(-0.03, 0.03)
    p = S.passe_bande(S.impulsions(0.03, 300, rng, 0.0015), 2000, 8000) * S.enveloppe(S.temps(0.03), 0.001, 0.01)
    S.place(x, p, tk, gain=0.6 * (1 - k / 11))
# souffle qui s'éteint
sf = S.souffle_balaye(D, 1600, 300, rng, largeur=1.5) * np.exp(-t / 0.45)
x += sf * 0.3
x = S.reverb(x, 0.6, 0.22, rng)[:len(x)]
S.ecrire("etincelles_extinction.ogg", x, sr=S.SR)
