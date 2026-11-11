"""Arc de la pioche (skin_pioche_orage, event_hit) : son original synthétisé, aucun échantillon extérieur.
Le coup touche : petit tintement d'acier sur la pointe (le pic est un fer de frappe, plus mat que la lame de l'épée), claquement
sec de 4 ms (la décharge de la pointe), puis un crépitement court qui remonte le dos du fer (0,25 s) avec deux reprises (arcs en
retour à 0,22 et 0,32 s de l'animation), et qui s'éteint. Pas de tonnerre (trop fort, fiche orage.md). Clé à 0 s dans event_hit.
Écrit arc_pioche.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.55
rng = S.seed(83)
t = S.temps(D)
crep = S.passe_bande(S.impulsions(D, 760, rng), 2000, 9500)
env = 0.6 * np.exp(-t / 0.11)
for tr, g in ((0.22, 0.45), (0.32, 0.3)):
    env = env + g * np.exp(-np.abs(t - tr) / 0.015)
crep = crep * env
# tintement d'acier mat (partiels inharmoniques, très court)
tint = S.cloche(1480, D, decroissance=0.09, partiels=((1, 1.0), (2.76, 0.4), (5.4, 0.15)))
clac = np.zeros_like(t)
n = int(0.004 * S.SR)
S.place(clac, rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 4)), 0.002)
tc = S.temps(0.14)
S.place(clac, 0.4 * np.sin(2 * np.pi * (150 - 190 * tc) * tc) * np.exp(-tc / 0.03), 0.002)
x = 0.45 * crep / np.max(np.abs(crep)) + 0.2 * tint / np.max(np.abs(tint)) + 0.85 * clac / np.max(np.abs(clac))
x = S.reverb(x, 0.25, 0.1, rng)[:len(t)]
S.ecrire("arc_pioche.ogg", x, sr=S.SR)
