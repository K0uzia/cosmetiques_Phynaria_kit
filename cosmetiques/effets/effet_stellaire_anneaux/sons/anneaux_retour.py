"""Retour des anneaux v2 (effet_stellaire_anneaux, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Caractère mesuré sur la référence (fiche .claude/references/effets/anneaux-transport.md, « Sons ») :
- le ronronnement de machine revient (≈ 120 Hz, souffle ≈ 1,1–1,5 kHz) pendant que les anneaux repartent ;
- chaque anneau se décroche (petit « tchk » : coup sourd ≈ 65 Hz plus faible qu'à la pose, claquement aigu) puis file
  vers le haut dans un « fouiii » d'air qui glisse vers l'aigu ; le dernier départ finit dans un souffle brillant ≈ 5 kHz.
Départs à 0,05 s puis toutes les 0,2 s (le dernier arrivé part le premier), de plus en plus faibles.
Clé à 2,8 s dans depart et 2,85 s dans arrivee. Ancienne version : sons/v1/. Écrit anneaux_retour.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.8
NA = 5
T0 = [0.05 + 0.2 * k for k in range(NA)]
rng = S.seed(173)
x = np.zeros(int(D * S.SR))
t = S.temps(D)


def osc(f):
    return np.sin(2 * np.pi * np.cumsum(f) / S.SR)


# 1. ronronnement de la machine, qui s'éteint après le dernier départ
f0 = 124 * (1 + 0.02 * np.sin(2 * np.pi * 0.7 * t))
mach = osc(f0) + 0.5 * osc(2 * f0) + 0.4 * osc(4.4 * f0) + 0.25 * osc(9.5 * f0)
env_m = np.clip(t / 0.12, 0, 1) * (1 - np.clip((t - T0[-1] - 0.1) / 0.5, 0, 1)) ** 2
S.place(x, mach * (1 + 0.25 * np.sin(2 * np.pi * 29 * t)) * env_m, 0.0, gain=0.055)
S.place(x, S.passe_bande(S.bruit(D, rng), 100, 2200, pente=1.6) * env_m, 0.0, gain=0.10)
S.place(x, S.passe_bande(S.bruit(D, rng), 40, 160) * env_m, 0.0, gain=0.12)
S.place(x, S.passe_bande(S.bruit(D, rng), 1000, 1600) * env_m, 0.0, gain=0.05)

for k, t0 in enumerate(T0):
    g = 1.0 - 0.13 * k
    # 2. décrochage
    tt = S.temps(0.25)
    S.place(x, osc(65 + 50 * np.exp(-tt / 0.015)) * S.enveloppe(tt, 0.002, 0.05), t0, gain=0.45 * g)
    clic = S.passe_bande(S.bruit(0.05, rng), 2500, 10000) * S.enveloppe(S.temps(0.05), 0.0008, 0.009)
    S.place(x, clic, t0, gain=0.15 * g)
    S.place(x, S.cloche(392 * (1 - 0.02 * k), 0.35, decroissance=0.1,
                        partiels=((1, 1.0), (1.48, 0.5), (2.09, 0.3), (2.74, 0.15)), desaccord=2.0), t0 + 0.003, gain=0.1 * g)
    # 3. « fouiii » qui file vers le haut et s'éloigne
    d = 0.5
    a = S.souffle_balaye(d, 800, 5000, rng, largeur=0.8, morceaux=20)
    u = np.linspace(0, 1, len(a))
    S.place(x, a * np.sin(np.pi * u ** 0.6) ** 1.5, t0 + 0.02, gain=0.42 * g)

# 4. souffle brillant au dernier départ
b = S.passe_bande(S.bruit(0.5, rng), 3500, 7500) * S.enveloppe(S.temps(0.5), 0.04, 0.12)
S.place(x, b, T0[-1] + 0.15, gain=0.18)

x = S.reverb(x, 0.8, 0.25, rng)[:len(x)]
S.ecrire("anneaux_retour.ogg", x, sr=S.SR)
