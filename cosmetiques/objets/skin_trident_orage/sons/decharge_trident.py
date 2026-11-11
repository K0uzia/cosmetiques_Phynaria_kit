"""Décharge du trident (skin_trident_orage, event_release) : son original synthétisé, aucun échantillon extérieur.
Le trident part : claquement sec (6 ms) et choc grave bref (le bras qui lance), puis trois reprises d'arc rapprochées (les
trois dents se déchargent l'une après l'autre, 0,05 / 0,1 / 0,16 s), crépitement qui file et s'éloigne avec l'arme (passe-bande
qui descend, niveau qui tombe en 0,4 s), souffle bref. Pas de tonnerre (trop fort, fiche orage.md). Clé à 0 s dans event_release.
Écrit decharge_trident.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.65
rng = S.seed(131)
t = S.temps(D)
crep_h = S.passe_bande(S.impulsions(D, 1300, rng), 3800, 12500)
crep_b = S.passe_bande(S.impulsions(D, 600, rng), 1200, 4200)
fuite = np.exp(-t / 0.14)
crep = crep_h * fuite * (1 - np.clip(t / 0.45, 0, 1)) + 0.6 * crep_b * fuite * np.clip(t / 0.12, 0, 1)
for tr, g in ((0.05, 0.45), (0.1, 0.38), (0.16, 0.3)):
    crep = crep + g * crep_h * np.exp(-np.abs(t - tr) / 0.01)
souffle = S.souffle_balaye(D, 4200, 900, rng) * np.exp(-t / 0.13)
clac = np.zeros_like(t)
n = int(0.006 * S.SR)
S.place(clac, rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 4)), 0.002)
tc = S.temps(0.16)
S.place(clac, 0.5 * np.sin(2 * np.pi * (120 - 160 * tc) * tc) * np.exp(-tc / 0.035), 0.002)
x = 0.55 * crep / np.max(np.abs(crep)) + 0.2 * souffle / np.max(np.abs(souffle)) + 0.8 * clac / np.max(np.abs(clac))
x = S.reverb(x, 0.3, 0.1, rng)[:len(t)]
S.ecrire("decharge_trident.ogg", x, sr=S.SR)
