"""Déchirure du ciel (effet_admin_neant : les mains écartent la faille) : son original synthétisé. Trois tractions
(arrachements graves de tissu : bruit 90-900 Hz à crépitement dense), la dernière qui cède, grondement sous-grave et souffle
d'air aspiré qui descend. Écrit neant_dechire.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.6
rng = S.seed(312)
t = S.temps(D)
x = np.zeros_like(t)
for k, (t0, d, g) in enumerate(((0.0, 0.22, 0.45), (0.28, 0.24, 0.65), (0.55, 0.45, 1.0))):
    seg = S.impulsions(d, 900 + 600 * k, rng, duree_imp=0.003) + 0.35 * S.bruit(d, rng)
    seg = S.passe_bande(seg, 90, 900)
    tt = np.arange(len(seg)) / S.SR
    seg *= np.clip(tt / 0.03, 0, 1) * np.exp(-np.maximum(tt - d * 0.6, 0) / 0.06)
    S.place(x, seg / (np.max(np.abs(seg)) + 1e-9), t0, gain=g)
gr = np.sin(2 * np.pi * np.cumsum(48 - 14 * np.clip(t / D, 0, 1)) / S.SR) * np.clip((t - 0.5) / 0.15, 0, 1) * np.exp(-np.maximum(t - 0.75, 0) / 0.35)
sou = S.souffle_balaye(D, 1800, 260, rng, largeur=0.9) * np.clip((t - 0.55) / 0.1, 0, 1) * np.exp(-np.maximum(t - 0.8, 0) / 0.3)
x = x + 0.7 * gr + 0.3 * sou / (np.max(np.abs(sou)) + 1e-9)
x = S.reverb(x, 0.8, 0.3, rng)[:len(t)]
S.ecrire("neant_dechire.ogg", x, crete_db=-8.0)
