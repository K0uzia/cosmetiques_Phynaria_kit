"""Lueur céleste (aura_berenice, event_equip) : son original synthétisé, aucun échantillon extérieur.
Une nappe douce qui enfle (mi 5 + si 5, attaque lente) pendant que la lumière monte des pieds vers la tête, parsemée de
petits scintillements aigus de la même gamme (mi majeur pentatonique), puis s'éteint. Clé à 0,8 s : le sommet (0,8 s dans
le fichier) tombe à l'ouverture de la gloire (1,6 s). Écrit lueur_celeste.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 2.0
rng = S.seed(23)
t = S.temps(D)
env = np.clip(t / 0.8, 0, 1) ** 2 * np.where(t > 0.8, np.exp(-(t - 0.8) / 0.45), 1.0)
nappe = sum(a * np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 4.5 * t + k))      # léger vibrato
            for k, (f, a) in enumerate(((659.3, 1.0), (987.8, 0.6), (1318.5, 0.25))))
nappe = nappe * env
gamme = (1318.5, 1480.0, 1661.2, 1975.5, 2217.5, 2637.0)
scint = np.zeros_like(t)
for _ in range(14):
    t0 = rng.uniform(0.25, 1.3)
    S.place(scint, S.cloche(rng.choice(gamme), 0.6, decroissance=0.18, partiels=((1, 1.0), (2.0, 0.15))), t0, gain=rng.uniform(0.3, 0.8))
souffle = S.passe_bande(S.bruit(D, rng), 3000, 9000) * env
x = 0.9 * nappe / np.max(np.abs(nappe)) + 0.4 * scint / np.max(np.abs(scint)) + 0.04 * souffle / np.max(np.abs(souffle))
x = S.reverb(x, 0.9, 0.3, rng)[:len(t)]
S.ecrire("lueur_celeste.ogg", x, sr=S.SR)
