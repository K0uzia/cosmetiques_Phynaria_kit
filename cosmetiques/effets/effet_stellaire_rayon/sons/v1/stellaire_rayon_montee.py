"""Montée de charge (effet_stellaire_rayon, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
La silhouette de lumière se charge : accord de sinus qui monte en glissant (300 → 1 200 Hz) avec un trémolo électronique
qui s'accélère (8 → 40 Hz), souffle clair qui monte, puis un « tinn » net au sommet (1,0 s dans le son) quand le corps
part (départ) ou apparaît (arrivée), et une traîne scintillante. Écrit rayon_montee.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D, TP = 1.7, 1.0
rng = S.seed(72)
t = S.temps(D)
x = np.zeros(len(t))
u = np.clip(t / TP, 0, 1)
env = u ** 1.6 * np.where(t < TP, 1.0, np.exp(-(t - TP) / 0.08))
f = 300 * 4 ** (u ** 1.3)                                  # 300 → 1 200 Hz
ph = 2 * np.pi * np.cumsum(f) / S.SR
trem_f = 8 + 32 * u ** 2
trem = 0.65 + 0.35 * np.sin(2 * np.pi * np.cumsum(trem_f) / S.SR)
for r, g in ((1.0, 0.5), (1.5, 0.3), (2.0, 0.2), (3.0, 0.08)):
    x += g * np.sin(ph * r) * env * trem
x += S.souffle_balaye(D, 900, 6000, rng, largeur=1.2) * env * 0.35
# sommet : « tinn » net et traîne scintillante
for fr, g in ((2637, 0.35), (3951, 0.22)):
    S.place(x, S.cloche(fr, 0.7, decroissance=0.35, desaccord=3.0), TP, gain=g)
sc = S.passe_bande(S.impulsions(D, 220, rng, 0.0008), 5000, 12000) * np.where(t > TP, np.exp(-(t - TP) / 0.3), 0)
x += sc * 0.3
x = S.reverb(x, 0.7, 0.22, rng)[:len(x)]
S.ecrire("stellaire_rayon_montee.ogg", x, sr=S.SR)
