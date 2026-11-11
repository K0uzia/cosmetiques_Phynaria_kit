"""Arc de la hache (skin_hache_orage, event_hit) : son original synthétisé, aucun échantillon extérieur.
Le coup touche : claquement sec (5 ms) et petit choc grave, puis un crépitement qui court 0,35 s (l'arc qui parcourt le fil)
avec trois petites reprises (les arcs en retour à 0,24, 0,34 et 0,44 s de l'animation), et qui s'éteint. Pas de tonnerre
(trop fort, fiche orage.md). Clé à 0 s dans event_hit. Écrit arc_hache.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.62
rng = S.seed(53)
t = S.temps(D)
crep = S.passe_bande(S.impulsions(D, 700, rng), 1800, 9000)
env = 0.7 * np.exp(-t / 0.16)
for tr, g in ((0.24, 0.55), (0.34, 0.4), (0.44, 0.28)):
    env = env + g * np.exp(-np.abs(t - tr) / 0.018)
crep = crep * env
# bourdonnement d'arc bref (dent de scie 140 Hz filtrée)
arc = S.passe_bande(((t * 140) % 1.0 - 0.5), 250, 2600) * np.exp(-t / 0.09)
clac = np.zeros_like(t)
n = int(0.005 * S.SR)
S.place(clac, rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 4)), 0.004)
tc = S.temps(0.2)
S.place(clac, 0.5 * np.sin(2 * np.pi * (110 - 150 * tc) * tc) * np.exp(-tc / 0.04), 0.004)
x = 0.5 * crep / np.max(np.abs(crep)) + 0.2 * arc / np.max(np.abs(arc)) + 0.9 * clac / np.max(np.abs(clac))
x = S.reverb(x, 0.3, 0.12, rng)[:len(t)]
S.ecrire("arc_hache.ogg", x, sr=S.SR)
