"""Formation de la glace (effet_givre : départ quand le gros cristal pousse, arrivée au jaillissement) : son original
synthétisé, aucun échantillon extérieur, pas de note « musicale ». La glace se cristallise en montant : crépitements secs qui
accélèrent, trois craquements de gel aux à-coups de la pousse (0, 0,25, 0,5 s), léger chuintement de givre qui monte, puis
quelques derniers grésillements. Écrit givre_forme.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.0
rng = S.seed(47)
t = S.temps(D)
# crépitement de cristallisation : densité croissante jusqu'à 0,6 s puis extinction
crep = np.zeros_like(t)
for k in range(8):
    a = 0.075 * k
    S.place(crep, S.impulsions(0.075, 150 + 220 * k, rng, duree_imp=0.0012), a, gain=0.35 + 0.09 * k)
S.place(crep, S.impulsions(0.4, 300, rng, duree_imp=0.0012) * np.exp(-S.temps(0.4) / 0.12), 0.6, gain=0.6)
crep = S.passe_bande(crep, 2200, 11000)
# craquements de gel : clic sec + petite résonance sourde du bloc, aux à-coups
cra = np.zeros_like(t)
for k, tk in enumerate((0.0, 0.25, 0.5)):
    n = int(0.03 * S.SR)
    burst = S.passe_bande(rng.standard_normal(n), 500, 4000) * np.exp(-np.arange(n) / (n / 6))
    S.place(cra, burst, tk + 0.01, gain=0.7 + 0.15 * k)
    tc = S.temps(0.12)
    S.place(cra, np.sin(2 * np.pi * (180 + 40 * k) * tc) * np.exp(-tc / 0.025), tk + 0.01, gain=0.35)
# chuintement de givre qui monte
ch = S.souffle_balaye(0.7, 1800, 7000, rng)
ch = ch * np.hanning(len(ch))
x = 0.55 * crep / np.max(np.abs(crep)) + 0.8 * cra / np.max(np.abs(cra))
S.place(x, 0.18 * ch / np.max(np.abs(ch)), 0.02)
x = S.reverb(x, 0.35, 0.15, rng)[:len(t)]
S.ecrire("givre_forme.ogg", x, sr=S.SR, crete_db=-9.0)
