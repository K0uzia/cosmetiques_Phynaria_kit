"""Ouverture du portail (effet_portail : départ et arrivée, quand l'air se déchire) : son original synthétisé, aucun échantillon
extérieur. Une fente qui se déchire (crépitement sec qui s'accélère sur 0,25 s, comme une toile tendue qui cède), puis un souffle
scintillant qui monte vers l'aigu quand l'ovale s'écarte, et un « whoum » grave et doux qui retombe (l'air qui s'engouffre).
Écrit portail_ouvre.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.4
rng = S.seed(71)
t = S.temps(D)
x = np.zeros_like(t)
# déchirure : impulsions de plus en plus serrées, bande 1,5–8 kHz
dech = np.zeros_like(t)
for k in range(6):
    S.place(dech, S.impulsions(0.05, 250 + 380 * k, rng, duree_imp=0.0010), 0.05 * k, gain=0.4 + 0.12 * k)
dech = S.passe_bande(dech, 1500, 8000)
S.place(x, dech / np.max(np.abs(dech)), 0.0, gain=0.55)
# souffle scintillant qui monte (ouverture de l'ovale)
so = S.souffle_balaye(0.8, 900, 6500, rng, largeur=1.0)
so *= np.hanning(len(so)) ** 0.7
S.place(x, so / np.max(np.abs(so)), 0.22, gain=0.55)
# scintillement : petits tons cristallins espacés qui montent
for k, f in enumerate((1320, 1760, 2093, 2637)):
    S.place(x, S.cloche(f, 0.5, decroissance=0.18), 0.3 + 0.07 * k, gain=0.10)
# « whoum » : sinus grave qui glisse de 140 à 70 Hz, attaque douce
tw = S.temps(0.75)
fq = 140 * (0.5 ** (tw / 0.75))
w = np.sin(2 * np.pi * np.cumsum(fq) / S.SR) * np.clip(tw / 0.06, 0, 1) * np.exp(-tw / 0.25)
w += 0.4 * S.passe_bande(rng.standard_normal(len(tw)), 80, 400) * np.exp(-tw / 0.15)
S.place(x, w / np.max(np.abs(w)), 0.26, gain=0.75)
x = S.reverb(x, 0.6, 0.22, rng)[:len(t)]
S.ecrire("portail_ouvre.ogg", x, sr=S.SR, crete_db=-8.0)
