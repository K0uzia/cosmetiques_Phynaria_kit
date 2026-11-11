"""Charge (effet_stellaire_porte) : son original synthétisé, aucun échantillon extérieur. La pierre sort du sol (frottement
grave et grondement, 0–0,5 s, choc sourd à l'arrêt), puis l'anneau d'or tourne par à-coups : 8 poussées de grondement
de rotation (roulement grave à 55–70 Hz + frottement 250–2500 Hz + léger sifflement métallique qui suit la vitesse),
calées sur les rotations de la charge (chaque cran se verrouille 0,03 s après la fin d'une poussée ; son du cran à part :
porte_cran). Plus bas que les clacs (crête -12 dBFS). Clé à 0 s. Écrit porte_gronde.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

# mêmes instants que gen_effet_stellaire_porte.py (C_LOCKS) : 8 verrouillages de 0,78 à 2,8 s
LOCKS = [0.78 + i * (2.8 - 0.78) / 7 for i in range(8)]
COUPS = [(tl - 0.25, tl - 0.03) for tl in LOCKS]
D = 3.1
rng = S.seed(96)
x = np.zeros(int(D * S.SR))
# pierre qui sort du sol
tr = S.temps(0.6)
v = np.clip(tr / 0.05, 0, 1) * np.clip((0.52 - tr) / 0.12, 0, 1)
S.place(x, S.passe_bande(S.bruit(0.6, rng), 60, 500) * v, 0.0, gain=0.9)
S.place(x, S.passe_bande(S.impulsions(0.6, 220, rng), 200, 2500) * v, 0.0, gain=0.35)
S.place(x, np.sin(2 * np.pi * 42 * tr) * v, 0.0, gain=0.5)
tc = S.temps(0.4)
S.place(x, np.sin(2 * np.pi * (50 + 40 * np.exp(-tc / 0.03)) * tc) * S.enveloppe(tc, 0.003, 0.12), 0.5, gain=0.9)
# fond grave continu pendant la composition
tf = S.temps(2.55)
fond = S.passe_bande(S.bruit(2.55, rng), 35, 140) * np.clip(tf / 0.3, 0, 1) * np.clip((2.55 - tf) / 0.3, 0, 1)
S.place(x, fond, 0.45, gain=0.35)
# poussées de rotation
for t0, t1 in COUPS:
    d = t1 - t0
    tt = S.temps(d)
    u = tt / d
    vit = np.sin(np.pi * u) ** 1.2
    S.place(x, S.passe_bande(S.bruit(d, rng), 250, 2500) * vit, t0, gain=0.35)
    S.place(x, np.sin(2 * np.pi * np.cumsum(55 + 15 * vit) / S.SR) * vit, t0, gain=0.6)
    f = 1700 * (0.8 + 0.2 * vit)
    S.place(x, np.sin(2 * np.pi * np.cumsum(f) / S.SR) * vit, t0, gain=0.04)
x = S.reverb(x, 0.6, 0.2, rng)[:len(x)]
S.ecrire("porte_gronde.ogg", x, sr=S.SR, crete_db=-12)
