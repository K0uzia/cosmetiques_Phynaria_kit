"""Charge (effet_stellaire_porte), v3 : son original synthétisé, aucun échantillon extérieur. Recette d'après les mesures
de la référence (.claude/references/effets/porte-etoiles.md, Sons) :
- la pierre sort du sol (0–0,5 s) : frottement grave et grains de pierre, choc sourd à l'arrêt ;
- l'anneau d'or tourne par à-coups (8 poussées calées sur la charge) : grondement de pierre lourde qui roule (énergie
  surtout à 60–130 Hz, ≈ 12 dB au-dessus des aigus), cliquetis mécanique régulier qui suit la vitesse, et sifflement
  électrique en série harmonique sur 660 Hz dont le 3e harmonique (≈ 1 980 Hz) domine, doublé à +11 Hz (battement),
  avec 1 320, 3 300 et 4 750 Hz plus faibles ; la hauteur suit un peu la vitesse ;
- chaque poussée **s'arrête net** 30 ms avant le verrou (le clac est à part : porte_cran*).
Plus bas que les clacs (crête -12 dBFS). Clé à 0 s. Écrit porte_gronde.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

# mêmes instants que gen_effet_stellaire_porte.py (C_LOCKS) : 8 verrouillages de 0,78 à 2,8 s
LOCKS = [0.78 + i * (2.8 - 0.78) / 7 for i in range(8)]
COUPS = [(tl - 0.25, tl - 0.03) for tl in LOCKS]
D = 3.1
rng = S.seed(196)
x = np.zeros(int(D * S.SR))
# pierre qui sort du sol
tr = S.temps(0.6)
v = np.clip(tr / 0.05, 0, 1) * np.clip((0.52 - tr) / 0.12, 0, 1)
S.place(x, S.passe_bande(S.bruit(0.6, rng), 60, 500) * v, 0.0, gain=0.9)
S.place(x, S.passe_bande(S.impulsions(0.6, 260, rng), 200, 2500) * v, 0.0, gain=0.4)
S.place(x, np.sin(2 * np.pi * 42 * tr) * v, 0.0, gain=0.5)
tc = S.temps(0.4)
S.place(x, np.sin(2 * np.pi * (50 + 40 * np.exp(-tc / 0.03)) * tc) * S.enveloppe(tc, 0.003, 0.12), 0.5, gain=0.9)
# fond grave continu pendant la composition (la machine tourne)
tf = S.temps(2.55)
fond = S.passe_bande(S.bruit(2.55, rng), 40, 160) * np.clip(tf / 0.3, 0, 1) * np.clip((2.55 - tf) / 0.3, 0, 1)
S.place(x, fond, 0.45, gain=0.3)
# poussées de rotation
for k, (t0, t1) in enumerate(COUPS):
    d = t1 - t0
    tt = S.temps(d)
    u = tt / d
    vit = np.clip(u / 0.25, 0, 1) ** 0.7 * np.clip((1 - u) / 0.04, 0, 1)    # démarre vite, file, s'arrête net
    # grondement de pierre qui roule
    roule = S.passe_bande(S.bruit(d, rng), 55, 180) * (1 + 0.4 * np.sin(2 * np.pi * 17 * tt))
    S.place(x, roule * vit, t0, gain=0.9)
    S.place(x, np.sin(2 * np.pi * np.cumsum(62 + 14 * vit) / S.SR) * vit, t0, gain=0.55)
    S.place(x, np.sin(2 * np.pi * np.cumsum(118 + 20 * vit) / S.SR) * vit, t0, gain=0.3)
    S.place(x, S.passe_bande(S.bruit(d, rng), 220, 900) * vit, t0, gain=0.6)       # frottement
    S.place(x, S.passe_bande(S.bruit(d, rng), 1500, 6000) * vit, t0, gain=0.12)      # grincement large bande
    # cliquetis mécanique régulier (dents), cadence proportionnelle à la vitesse
    ph = np.cumsum(38 * vit) / S.SR
    ticks = np.zeros_like(tt)
    for n in range(1, int(ph[-1]) + 1):
        i = int(np.searchsorted(ph, n))
        if i < len(tt) - 200:
            ticks[i:i + 200] += np.exp(-np.arange(200) / 25) * rng.uniform(0.6, 1.0)
    S.place(x, S.passe_bande(ticks * rng.standard_normal(len(tt)), 1500, 6000), t0, gain=0.22)
    S.place(x, S.passe_bande(ticks, 200, 900), t0, gain=0.25)
    # sifflement électrique : série sur 660 Hz, 3e harmonique dominant, battement à 11 Hz
    f0 = 660 * (0.97 + 0.03 * vit) * (1 + 0.01 * (k % 3 - 1))
    ph0 = 2 * np.pi * np.cumsum(f0) / S.SR
    sif = (0.25 * np.sin(ph0) + 0.5 * np.sin(2 * ph0) + 1.0 * np.sin(3 * ph0)
           + 0.6 * np.sin(3 * ph0 + 2 * np.pi * 11 * tt) + 0.18 * np.sin(5 * ph0) + 0.15 * np.sin(7.2 * ph0))
    S.place(x, sif * vit ** 1.5, t0, gain=0.3)
x = S.reverb(x, 0.6, 0.18, rng)[:len(x)]
S.ecrire("porte_gronde.ogg", x, sr=S.SR, crete_db=-12)
