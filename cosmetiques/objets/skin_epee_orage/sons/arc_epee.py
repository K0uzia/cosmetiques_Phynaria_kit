"""Arc de l'épée (skin_epee_orage, event_hit) : son original synthétisé, aucun échantillon extérieur.
Le coup touche : claquement sec (4 ms) et petit choc grave (la décharge de la pointe), puis un crépitement plus aigu que celui
de la hache qui court 0,3 s (l'arc qui revient sur les deux fils vers la garde) avec trois petites reprises (arcs en retour à
0,24, 0,34 et 0,44 s de l'animation), et qui s'éteint. Pas de tonnerre (trop fort, fiche orage.md). Clé à 0 s dans event_hit.
Écrit arc_epee.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.6
rng = S.seed(71)
t = S.temps(D)
crep = S.passe_bande(S.impulsions(D, 900, rng), 2400, 11000)
env = 0.65 * np.exp(-t / 0.13)
for tr, g in ((0.24, 0.5), (0.34, 0.36), (0.44, 0.24)):
    env = env + g * np.exp(-np.abs(t - tr) / 0.016)
crep = crep * env
# chant d'arc bref (dent de scie 190 Hz filtrée, qui glisse vers le grave : l'arc descend la lame)
ph = np.cumsum(190 - 60 * t) / S.SR
arc = S.passe_bande((ph % 1.0 - 0.5), 300, 3200) * np.exp(-t / 0.11)
clac = np.zeros_like(t)
n = int(0.004 * S.SR)
S.place(clac, rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 4)), 0.003)
tc = S.temps(0.16)
S.place(clac, 0.45 * np.sin(2 * np.pi * (130 - 170 * tc) * tc) * np.exp(-tc / 0.035), 0.003)
x = 0.5 * crep / np.max(np.abs(crep)) + 0.22 * arc / np.max(np.abs(arc)) + 0.85 * clac / np.max(np.abs(clac))
x = S.reverb(x, 0.3, 0.1, rng)[:len(t)]
S.ecrire("arc_epee.ogg", x, sr=S.SR)
