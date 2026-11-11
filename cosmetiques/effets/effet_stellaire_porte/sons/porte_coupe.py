"""Coupure de la surface et retour de la porte dans le sol (effet_stellaire_porte, depart et arrivee), v3 : son original
synthétisé, aucun échantillon extérieur. Recette (.claude/references/effets/porte-etoiles.md, Sons) :
1. aspiration nette et brève, comme un « shloop » à l'envers (0–0,26 s) : bruit qui monte en hauteur (200 → 3 000 Hz)
   et en force de plus en plus vite, plus un fond grave aspiré, qui **s'arrête d'un coup** ;
2. « thup » sec à la coupure (sinus 110 → 45 Hz, 60 ms) et l'eau qui se referme (petit clapot) ;
3. la pierre redescend (0,4–1,25 s) : grondement grave qui roule, frottement, cliquetis qui ralentit, choc sourd à
   l'arrêt (1,25 s).
Clé 0,28 s avant la coupure, pour que le « thup » tombe sur l'image (2,38 s dans depart, 2,72 s dans arrivee). Écrit porte_coupe.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.65
rng = S.seed(193)
x = np.zeros(int(D * S.SR))
# 1. aspiration inversée
da = 0.26
a = S.souffle_balaye(da, 200, 3000, rng, largeur=1.0, morceaux=24)
ta = S.temps(da)
monte = (ta / da) ** 3
S.place(x, a * monte, 0.0, gain=0.8)
S.place(x, S.passe_bande(S.bruit(da, rng), 40, 200) * monte, 0.0, gain=0.5)
# 2. coupure
tc = S.temps(0.3)
S.place(x, np.sin(2 * np.pi * np.cumsum(45 + 65 * np.exp(-tc / 0.02)) / S.SR) * S.enveloppe(tc, 0.001, 0.06), da, gain=0.9)
S.place(x, S.passe_bande(S.bruit(0.15, rng), 400, 2000) * S.enveloppe(S.temps(0.15), 0.002, 0.03), da + 0.01, gain=0.25)
# 3. la pierre redescend
d = 0.85
t = S.temps(d)
env = np.interp(t, [0, 0.1, 0.75, 0.84], [0, 1, 0.9, 0])
S.place(x, S.passe_bande(S.bruit(d, rng), 45, 260) * env * (1 + 0.3 * np.sin(2 * np.pi * 15 * t)), 0.4, gain=0.85)
S.place(x, np.sin(2 * np.pi * 58 * t) * env, 0.4, gain=0.35)
S.place(x, S.passe_bande(S.bruit(d, rng), 400, 2500) * env * (0.6 + 0.4 * np.sin(2 * np.pi * 13 * t) ** 2), 0.4, gain=0.15)
ph = np.cumsum(30 * (1 - 0.6 * t / d)) / S.SR
ticks = np.zeros_like(t)
for n in range(1, int(ph[-1]) + 1):
    i = int(np.searchsorted(ph, n))
    if i < len(t) - 200:
        ticks[i:i + 200] += np.exp(-np.arange(200) / 25)
S.place(x, S.passe_bande(ticks * env, 200, 1200), 0.4, gain=0.25)
tp = S.temps(0.35)
S.place(x, np.sin(2 * np.pi * np.cumsum(50 + 45 * np.exp(-tp / 0.03)) / S.SR) * S.enveloppe(tp, 0.002, 0.1), 1.25, gain=0.75)
S.place(x, S.passe_bande(S.bruit(0.2, rng), 60, 400) * S.enveloppe(S.temps(0.2), 0.001, 0.04), 1.25, gain=0.4)
x = S.reverb(x, 0.6, 0.18, rng)[:len(x)]
S.ecrire("porte_coupe.ogg", x, sr=S.SR)
