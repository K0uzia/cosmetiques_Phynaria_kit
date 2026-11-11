"""Souffle de plumes (ailes_berenice, event_equip) : son original synthétisé, aucun échantillon extérieur.
Un souffle d'air qui enfle puis retombe pendant que l'éventail s'ouvre, un froissement de plumes (bruit granuleux aigu),
et un tintement très léger de mi aigu qui relie l'ensemble Bérénice (même tonalité que le diadème et l'aura).
Clé posée à 0,75 s dans event_equip : le sommet du souffle (0,35 s dans le fichier) tombe sur l'ouverture des primaires (1,1 s).
Écrit souffle_plumes.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.3
rng = S.seed(7)
t = S.temps(D)
# souffle : bande qui monte de 350 à 1 400 Hz, enveloppe en cloche (montée gaussienne jusqu'à 0,35 s, puis décroissance)
env = np.where(t < 0.35, np.exp(-((t - 0.35) / 0.2) ** 2), np.exp(-(t - 0.35) / 0.28))
souffle = S.souffle_balaye(D, 350, 1400, rng, largeur=1.6) * env
# froissement : bruit aigu modulé par de petites rafales irrégulières (barbes de plumes qui se frottent)
gr = S.passe_bande(S.bruit(D, rng), 2500, 7000)
rafales = np.convolve(np.abs(rng.standard_normal(len(t))) ** 3, np.hanning(600) / 300, mode="same")
froiss = gr * rafales * np.exp(-((t - 0.42) / 0.3) ** 2)
# tintement : mi 6 doux, très bas dans le mélange
tint = np.zeros_like(t)
S.place(tint, S.cloche(1318.5, 0.9, decroissance=0.35), 0.33)
x = 1.0 * souffle / np.max(np.abs(souffle)) + 0.35 * froiss / np.max(np.abs(froiss)) + 0.22 * tint / np.max(np.abs(tint))
x = S.reverb(x, 0.5, 0.18, rng)[:len(t)]
S.ecrire("souffle_plumes.ogg", x, sr=S.SR)
