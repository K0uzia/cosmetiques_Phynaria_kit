"""Claquement de fouet (skin_canne_cuir : event_swing et event_enter_lancee) : son original synthétisé, aucun échantillon.
D'après les mesures publiées (.claude/references/objets/fouets.md) : le bang est une petite onde de choc, une onde en N de
1 à 2 ms dont l'énergie est entre 1 et 5 kHz, suivie d'échos courts (100–200 ms au plus). Avant, la lanière siffle en
fendant l'air (souffle qui monte vers l'aigu à mesure que la boucle accélère).
Déroulé : 0–0,13 s sifflement balayé 500 → 3 200 Hz, de plus en plus fort ; 0,13 s onde en N (1,4 ms) + éclat de bruit
2–7 kHz (4 ms) + petite résonance du cuir vers 1,1 kHz (12 ms) ; puis un écho faible à 55 ms et une queue de 0,2 s.
Écrit claquement_cuir.ogg à côté de ce script (le générateur pose la clé 0,13 s avant l'instant du claquement)."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.55
T0 = 0.13
rng = S.seed(1108)
t = S.temps(D)
x = np.zeros_like(t)

# sifflement de la lanière : bande qui monte, enveloppe croissante, coupée net au bang
env_s = np.clip(t / T0, 0, 1) ** 2.2 * (t < T0 + 0.004)
sw = S.souffle_balaye(D, 500, 3200, rng, largeur=1.1)
x += 0.3 * sw / np.max(np.abs(sw)) * env_s

# onde en N : montée brusque, descente linéaire jusqu'au négatif, remontée brusque (1,4 ms)
tn = S.temps(0.0014)
n_wave = 1 - 2 * tn / tn[-1]
bang = np.zeros_like(t)
S.place(bang, n_wave, T0)
# éclat de bruit aigu (4 ms) et résonance du cuir (12 ms)
tb = S.temps(0.03)
eclat = S.passe_bande(S.bruit(0.03, rng), 2000, 7000) * np.exp(-tb / 0.004)
S.place(bang, eclat / (np.max(np.abs(eclat)) + 1e-9), T0, gain=0.8)
reso = np.sin(2 * np.pi * 1100 * tb) * np.exp(-tb / 0.012)
S.place(bang, reso, T0, gain=0.35)
# écho faible (mur, sol) à 55 ms
S.place(bang, bang[int(T0 * S.SR):int((T0 + 0.03) * S.SR)].copy(), T0 + 0.055, gain=0.18)

x = x + bang
x = S.reverb(x, 0.22, 0.1, rng)[:len(t)]
S.ecrire("claquement_cuir.ogg", x, sr=S.SR)
