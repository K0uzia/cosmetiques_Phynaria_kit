"""Envol céleste (effet_berenice, depart) : son original synthétisé, aucun échantillon extérieur.
Un souffle clair qui monte (les ailes de lumière se referment en cocon), un arpège de verre en mi majeur qui accélère
vers l'aigu pendant l'ascension, puis l'éclat : accord de cloches et crépitement d'étincelles très doux, longue traîne.
Clé à 0,4 s dans depart : l'éclat (1,7 s dans le son) tombe à 2,1 s, quand le cocon éclate en plumes.
Écrit envol_celeste.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 2.9
TB = 1.7                                   # l'éclat
rng = S.seed(23)
x = np.zeros(int(D * S.SR))
# souffle qui monte, de plus en plus fort jusqu'à l'éclat
sf = S.souffle_balaye(TB + 0.1, 500, 4200, rng, largeur=1.0)
t = S.temps(TB + 0.1)
S.place(x, sf * (t / (TB + 0.1)) ** 1.6 * 0.35, 0.0)
# arpège montant (mi majeur : mi, sol dièse, si), de plus en plus serré
notes = [659.3, 830.6, 987.8, 1318.5, 1661.2, 1975.5, 2637.0, 3322.4]
tk = 0.05
for i, f in enumerate(notes):
    S.place(x, S.cloche(f, 0.9, decroissance=0.3, desaccord=0.7), tk, gain=0.35 + 0.06 * i)
    tk += 0.26 * 0.8 ** i
# éclat : accord large et clair
for f, g in ((659.3, 0.5), (1318.5, 1.0), (1661.2, 0.75), (1975.5, 0.7), (2637.0, 0.45)):
    S.place(x, S.cloche(f, 1.2, decroissance=0.45, desaccord=1.0), TB, gain=g)
# étincelles : crépitement aigu très court qui s'éteint
cr = S.passe_bande(S.impulsions(0.9, 70, rng, 0.0015), 5000, 11000)
S.place(x, cr * S.enveloppe(S.temps(0.9), 0.01, 0.25) * 0.5, TB)
x = S.reverb(x, 1.0, 0.32, rng)[:len(x)]
S.ecrire("envol_celeste.ogg", x, sr=S.SR)
