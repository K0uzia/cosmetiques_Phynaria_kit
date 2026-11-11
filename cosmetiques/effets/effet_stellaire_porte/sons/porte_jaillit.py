"""Jaillissement de l'eau et surface ouverte (effet_stellaire_porte, depart et arrivee), v3 : son original synthétisé,
aucun échantillon extérieur. Recette d'après les mesures de la référence (.claude/references/effets/porte-etoiles.md,
Sons), même ordre des couches :
1. aspiration très brève (0–0,06 s, bruit 300–1500 Hz qui monte) ;
2. éclat clair (0,06 s : 30 ms de bruit 1,5–5 kHz) puis, 20 ms après, **coup sourd énorme** (sinus 160 → 50 Hz,
   énergie surtout sous 120 Hz) : le « boum » d'ouverture ;
3. gerbe d'écume (0,1–0,45 s : bruit 5–10 kHz qui retombe) et rugissement d'eau qui gonfle (bruit 110–800 Hz,
   centre ≈ 500 Hz) avec des bouffées graves irrégulières (bouillonnement, 2–4 par seconde) ;
4. retour de la gerbe (0,6–1,1 s) : « whoosh » qui glisse de 2,5 kHz à 250 Hz et s'avale, petit creux à 1,15 s ;
5. surface ouverte (1,15–2,5 s) : ronronnement liquide grave (bruit 35–200 Hz sur un fond à 46 Hz, pente forte vers l'aigu) qui
   pulse irrégulièrement (± 5 dB), éteint avant la coupure (2,64 s au départ, 2,98 s à l'arrivée).
Clé à 0,21 s dans depart (éclat à 0,27), 0 s dans arrivee. Écrit porte_jaillit.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 2.55
rng = S.seed(192)
x = np.zeros(int(D * S.SR))
# 1. aspiration
ta = S.temps(0.07)
S.place(x, S.passe_bande(S.bruit(0.07, rng), 300, 1500) * (ta / 0.07) ** 2, 0.0, gain=0.35)
# 2. éclat + coup sourd
te = S.temps(0.08)
S.place(x, S.passe_bande(S.bruit(0.08, rng), 1500, 5000) * S.enveloppe(te, 0.002, 0.025), 0.06, gain=0.9)
tb = S.temps(0.8)
boum = np.sin(2 * np.pi * np.cumsum(50 + 110 * np.exp(-tb / 0.06)) / S.SR) * S.enveloppe(tb, 0.004, 0.22)
S.place(x, boum, 0.08, gain=1.0)
S.place(x, S.passe_bande(S.bruit(0.5, rng), 40, 200) * S.enveloppe(S.temps(0.5), 0.003, 0.12), 0.08, gain=0.8)
# 3. écume et rugissement
tg = S.temps(1.0)
S.place(x, S.passe_bande(S.bruit(1.0, rng), 5000, 10000) * S.enveloppe(tg, 0.01, 0.18), 0.1, gain=0.7)
d = 1.15
t = S.temps(d)
env = np.interp(t, [0, 0.08, 0.5, 0.75, 1.0, 1.15], [0, 1, 1, 0.85, 0.4, 0])
bouffees = 1 + 0.5 * np.maximum(np.sin(2 * np.pi * np.cumsum(2.5 + 1.5 * np.sin(2 * np.pi * 0.9 * t)) / S.SR), 0) ** 3
rug = S.passe_bande(S.bruit(d, rng), 110, 800) * env
grave = S.passe_bande(S.bruit(d, rng), 35, 130) * env * bouffees
S.place(x, rug, 0.1, gain=1.4)
S.place(x, grave, 0.1, gain=0.7)
# bouillonnement : bulles graves éparses
for i in range(40):
    tq = 0.15 + rng.uniform(0, 0.95)
    f = rng.uniform(150, 600)
    tc = S.temps(0.05)
    S.place(x, np.sin(2 * np.pi * f * (1 + 4 * tc) * tc) * S.enveloppe(tc, 0.002, 0.012), tq, gain=0.12)
# 4. retour de la gerbe : whoosh descendant
w = S.souffle_balaye(0.5, 2500, 250, rng, largeur=1.4)
tw = S.temps(0.5)
S.place(x, w * np.interp(tw, [0, 0.3, 0.45, 0.5], [0.2, 1, 0.6, 0]), 0.62, gain=0.5)
# 5. surface ouverte : ronronnement liquide qui pulse
ds = 1.4
ts = S.temps(ds)
lent = np.cumsum(rng.standard_normal(len(ts)))
lent = S.passe_bande(lent - lent.mean(), 1.5, 5)          # fluctuations 2–5 Hz
lent = 10 ** (5 * lent / (np.max(np.abs(lent)) + 1e-9) / 20)
envs = np.interp(ts, [0, 0.15, 1.0, 1.4], [0, 1, 0.8, 0])
brun = S.passe_bande(S.bruit(ds, rng), 35, 200)
hum = (0.35 * np.sin(2 * np.pi * 46 * ts) + 0.12 * np.sin(2 * np.pi * 92 * ts + 1)
       + 2.5 * brun / (np.std(brun) + 1e-9) * 0.4)
S.place(x, hum * lent * envs, 1.1, gain=0.25)
S.place(x, S.passe_bande(S.bruit(ds, rng), 150, 900) * lent * envs, 1.1, gain=0.12)
x = S.reverb(x, 0.8, 0.2, rng)[:len(x)]
S.ecrire("porte_jaillit.ogg", x, sr=S.SR)
