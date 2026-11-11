"""Éclair des anneaux v2 (effet_stellaire_anneaux, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Caractère mesuré sur la référence (fiche .claude/references/effets/anneaux-transport.md, « Sons ») :
- juste avant l'éclair, le grave retombe (≈ −10 dB) et un sifflement électrique monte, raies vers 3,7 et 4,9 kHz ;
- à l'éclair, une houle grave ≈ 50 Hz et un souffle brillant ; puis ≈ 1,4 s de scintillement 4–8 kHz (centre de gravité
  du spectre qui passe de ≈ 1 à ≈ 3,5 kHz) sur un ton moyen ≈ 600 Hz qui s'éteint.
Plus fort à 0,37 s (le joueur disparaît ou apparaît). Clé à 1,85 s dans depart et 1,8 s dans arrivee.
Ancienne version : sons/v1/. Écrit anneaux_eclair.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.75
TP = 0.37
rng = S.seed(172)
x = np.zeros(int(D * S.SR))


def osc(f):
    return np.sin(2 * np.pi * np.cumsum(f) / S.SR)


def flutter(d, vitesse, rng):
    """Enveloppe qui frémit (bruit lissé, toujours positif) : scintillement."""
    n = S.passe_bande(rng.standard_normal(int(round(d * S.SR))), 1, vitesse)
    n = n / (np.std(n) + 1e-9)
    return np.clip(0.55 + 0.45 * n, 0, None)


# 1. sifflement électrique qui monte jusqu'à l'éclair (deux raies dans le rapport mesuré 4,9 / 3,7)
d = TP + 0.12
tt = S.temps(d)
u = np.clip(tt / TP, 0, 1)
f = 1500 * (3720 / 1500) ** (u ** 1.4)
env = u ** 2.5 * np.exp(-np.maximum(tt - TP, 0) / 0.05)
vib = 1 + 0.006 * np.sin(2 * np.pi * 23 * tt)
S.place(x, (osc(f * vib) + 0.6 * osc(f * 1.317 * vib)) * env, 0.0, gain=0.07)
# fond de machine retombé (≈ −10 dB par rapport à la descente) avant l'éclair
fd = np.clip(S.temps(TP + 0.1) / 0.08, 0, 1) * np.clip((TP + 0.1 - S.temps(TP + 0.1)) / 0.12, 0, 1)
S.place(x, (S.passe_bande(S.bruit(TP + 0.1, rng), 40, 160) + 0.6 * S.passe_bande(S.bruit(TP + 0.1, rng), 160, 2000, pente=1.6)) * fd, 0.0, gain=0.07)
# montée de souffle sous le sifflement
s = S.souffle_balaye(TP, 700, 6000, rng, largeur=1.1, morceaux=16)
S.place(x, s * np.linspace(0, 1, len(s)) ** 3, 0.0, gain=0.28)

# 2. l'éclair : houle grave, souffle brillant
dh = D - TP + 0.01
tt = S.temps(dh)
houle = (osc(50 + 40 * np.exp(-tt / 0.06)) + 0.35 * osc(100 + 60 * np.exp(-tt / 0.06))) * S.enveloppe(tt, 0.03, 0.3)
S.place(x, houle, TP - 0.01, gain=0.45)
gr = S.passe_bande(S.bruit(dh, rng), 35, 160) * S.enveloppe(tt, 0.04, 0.45)
S.place(x, gr, TP - 0.01, gain=0.6)
mi = S.passe_bande(S.bruit(dh, rng), 250, 3500, pente=1.5) * S.enveloppe(tt, 0.02, 0.4)
S.place(x, mi, TP - 0.01, gain=0.22)
w = S.passe_bande(S.bruit(0.7, rng), 1500, 12000) * S.enveloppe(S.temps(0.7), 0.006, 0.12)
S.place(x, w, TP, gain=0.5)

# 3. scintillement 4–8 kHz qui frémit et s'éteint, ton moyen ≈ 600 Hz
ds = D - TP - 0.02
tt = S.temps(ds)
sc = S.passe_bande(S.bruit(ds, rng), 4000, 8000) * flutter(ds, 35, rng) * S.enveloppe(tt, 0.08, 0.45)
S.place(x, sc, TP + 0.02, gain=0.38)
cr = S.passe_bande(S.impulsions(ds, 260, rng, 0.0007), 3000, 11000) * S.enveloppe(tt, 0.05, 0.35)
S.place(x, cr, TP + 0.02, gain=0.25)
ton = (osc(608 * (1 + 0.01 * np.sin(2 * np.pi * 5.5 * tt))) + 0.4 * osc(912 * (1 + 0.01 * np.sin(2 * np.pi * 5.5 * tt)))) * S.enveloppe(tt, 0.05, 0.35)
S.place(x, ton, TP + 0.02, gain=0.045)

x = S.reverb(x, 0.9, 0.28, rng)[:len(x)]
S.ecrire("anneaux_eclair.ogg", x, sr=S.SR)
