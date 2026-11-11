"""Impact et claquement (effet_admin_neant : le joueur touche le sol, ou la faille claque en se refermant) : son original
synthétisé. Coup sourd (sinus qui chute de 95 à 34 Hz), choc de bruit grave, queue de gravats qui crépitent.
Écrit neant_impact.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.2
rng = S.seed(314)
t = S.temps(D)
f = 34 + 61 * np.exp(-t / 0.07)
coup = np.sin(2 * np.pi * np.cumsum(f) / S.SR) * S.enveloppe(t, 0.003, 0.28)
choc = S.passe_bande(S.bruit(D, rng), 50, 700) * S.enveloppe(t, 0.002, 0.06)
grav = S.passe_bande(S.impulsions(D, 160, rng, duree_imp=0.002), 900, 5000) * np.clip((t - 0.05) / 0.05, 0, 1) * np.exp(-np.maximum(t - 0.1, 0) / 0.25)
x = coup + 0.6 * choc / np.max(np.abs(choc)) + 0.22 * grav / (np.max(np.abs(grav)) + 1e-9)
x = S.reverb(x, 0.7, 0.25, rng)[:len(t)]
S.ecrire("neant_impact.ogg", x, crete_db=-7.0)
