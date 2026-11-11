"""Descente des anneaux v2 (effet_stellaire_anneaux, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Caractère mesuré sur la référence (fiche .claude/references/effets/anneaux-transport.md, « Sons ») :
- un ronronnement de machine pendant toute la descente : fondamentale ≈ 120 Hz, partiels ≈ 240, 533 et 1 070 Hz, souffle 1–2 kHz ;
- chaque anneau arrive dans un « chouif » d'air qui glisse vers le grave et se pose par un « chlonk » bref :
  coup sourd ≈ 58 Hz (≈ 0,1 s, +15 dB sur le fond), corps métallique ≈ 390 Hz, claquement aigu 2–10 kHz très court.
Poses à 0,65 s puis toutes les 0,22 s (clé à 0,1 s dans depart, 0,15 s dans arrivee : anneaux posés à 0,75 / 0,8 s + 0,22 k).
Ancienne version : sons/v1/. Écrit anneaux_descente.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 2.2
NA = 5
TP = [0.65 + 0.22 * k for k in range(NA)]
rng = S.seed(171)
x = np.zeros(int(D * S.SR))
t = S.temps(D)


def osc(f):
    """Oscillateur à fréquence variable (tableau de Hz)."""
    return np.sin(2 * np.pi * np.cumsum(f) / S.SR)


# 1. ronronnement de la machine : 120 Hz et partiels mesurés, léger flottement, monte puis s'éteint après la dernière pose
n = S.passe_bande(rng.standard_normal(len(t)), 1, 6)
flot = 1 + 0.01 * n / (np.std(n) + 1e-9)
f0 = 120 * (1 + 0.03 * np.clip(t / 0.4, 0, 1)) * np.clip(flot, 0.97, 1.03)
mach = osc(f0) + 0.55 * osc(2 * f0) + 0.6 * osc(4.44 * f0) + 0.22 * osc(8.9 * f0)
rugo = 1 + 0.25 * np.sin(2 * np.pi * 31 * t)                       # grain mécanique
env_m = np.clip(t / 0.35, 0, 1) ** 1.5 * (1 - np.clip((t - TP[-1] - 0.05) / 0.45, 0, 1)) ** 2
S.place(x, mach * rugo * env_m, 0.0, gain=0.055)
# lit de bruit de machine dense (la référence est large bande de 100 Hz à 8 kHz) et grondement grave
S.place(x, S.passe_bande(S.bruit(D, rng), 110, 2600, pente=1.6) * env_m, 0.0, gain=0.10)
S.place(x, S.passe_bande(S.bruit(D, rng), 40, 150) * env_m, 0.0, gain=0.12)
air = S.passe_bande(S.bruit(D, rng), 900, 2200)
S.place(x, air * env_m, 0.0, gain=0.05)

for k, tp in enumerate(TP):
    g = 1.0 - 0.04 * k
    # 2. « chouif » : souffle qui glisse de l'aigu vers le grave et enfle jusqu'à la pose
    d = 0.34
    a = S.souffle_balaye(d, 5200, 800, rng, largeur=0.8, morceaux=24)
    u = np.linspace(0, 1, len(a))
    S.place(x, a * u ** 2.2, tp - d, gain=0.42 * g)
    # 3. « chlonk » de la pose
    tt = S.temps(0.35)
    coup = np.sin(2 * np.pi * np.cumsum(58 + 70 * np.exp(-tt / 0.018)) / S.SR) * S.enveloppe(tt, 0.002, 0.075)
    S.place(x, coup, tp, gain=0.95 * g)
    corps = S.cloche(392 * (1 + 0.025 * (k % 3 - 1)), 0.5, decroissance=0.16,
                     partiels=((1, 1.0), (1.48, 0.55), (2.09, 0.35), (2.74, 0.18), (3.9, 0.08)), desaccord=2.0)
    S.place(x, corps, tp + 0.003, gain=0.14 * g)
    clic = S.passe_bande(S.bruit(0.06, rng), 2000, 10000) * S.enveloppe(S.temps(0.06), 0.0008, 0.011)
    S.place(x, clic, tp, gain=0.18 * g)

x = S.reverb(x, 0.6, 0.18, rng)[:len(x)]
S.ecrire("anneaux_descente.ogg", x, sr=S.SR)
