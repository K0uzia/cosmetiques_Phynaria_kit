"""Décharge de l'arc (skin_arc_orage, event_release) : son original synthétisé, aucun échantillon extérieur.
La flèche part : claquement sec de la corde (5 ms) et petit choc grave, puis un trait de crépitement qui file et s'éloigne
(la décharge suit la flèche : passe-bande qui descend, niveau qui tombe en 0,35 s), deux petites reprises aux pointes
(arcs à 0,12 et 0,2 s). Pas de tonnerre (trop fort, fiche orage.md). Clé à 0 s dans event_release.
Écrit decharge_arbalete.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.6
rng = S.seed(83)
t = S.temps(D)
crep_h = S.passe_bande(S.impulsions(D, 1100, rng), 3500, 12000)
crep_b = S.passe_bande(S.impulsions(D, 700, rng), 1500, 5000)
fuite = np.exp(-t / 0.12)
crep = crep_h * fuite * (1 - np.clip(t / 0.4, 0, 1)) + 0.7 * crep_b * fuite * np.clip(t / 0.15, 0, 1)
for tr, g in ((0.12, 0.35), (0.2, 0.22)):
    crep = crep + g * crep_h * np.exp(-np.abs(t - tr) / 0.012)
# sifflement bref de l'air (la flèche file) : souffle filtré qui descend
souffle = S.souffle_balaye(D, 5200, 1400, rng) * np.exp(-t / 0.1)
clac = np.zeros_like(t)
n = int(0.005 * S.SR)
S.place(clac, rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 4)), 0.002)
tc = S.temps(0.14)
S.place(clac, 0.4 * np.sin(2 * np.pi * (150 - 200 * tc) * tc) * np.exp(-tc / 0.03), 0.002)
x = 0.55 * crep / np.max(np.abs(crep)) + 0.18 * souffle / np.max(np.abs(souffle)) + 0.8 * clac / np.max(np.abs(clac))
x = S.reverb(x, 0.3, 0.1, rng)[:len(t)]
S.ecrire("decharge_arbalete.ogg", x, sr=S.SR)
