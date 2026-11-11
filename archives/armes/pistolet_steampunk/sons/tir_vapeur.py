"""Tir à vapeur (pistolet_steampunk, attack) : son original synthétisé, aucun échantillon extérieur.
Déclic métallique double (gâchette puis soupape, 0 et 0,025 s), puis jet de vapeur : souffle qui jaillit (0,03–0,11 s),
s'étire en sifflement plus aigu et s'efface avec le jet modélisé (0,62 s). Clé à 0,03 s dans attack, comme l'ancien son.
Écrit tir_vapeur.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.8
rng = S.seed(41)
t = S.temps(D)
# déclics : résonances métalliques très courtes (laiton), deux coups
clic = np.zeros_like(t)
for t0, f, g in ((0.0, 3400, 1.0), (0.025, 2600, 0.7)):
    tc = S.temps(0.04)
    son = sum(a * np.sin(2 * np.pi * f * r * tc) for r, a in ((1, 1.0), (1.52, 0.6), (2.31, 0.3))) * np.exp(-tc / 0.006)
    S.place(clic, son, t0, gain=g)
# vapeur : bruit qui jaillit, bande qui monte de 1,8 à 5 kHz (le jet s'étire), extinction avec le fondu du jet
env = np.clip((t - 0.03) / 0.06, 0, 1) * np.where(t > 0.15, np.exp(-(t - 0.15) / 0.2), 1.0)
vap = S.souffle_balaye(D, 1800, 5000, rng, largeur=1.4) * env
# petit sifflement de soupape (sinus à 2,9 kHz, faible) dans le jet
sif = np.sin(2 * np.pi * 2900 * t) * env ** 2
x = 0.6 * clic / np.max(np.abs(clic)) + 1.0 * vap / np.max(np.abs(vap)) + 0.08 * sif
x = S.reverb(x, 0.3, 0.12, rng)[:len(t)]
S.ecrire("tir_vapeur.ogg", x, sr=S.SR)
