"""Pop de bulle de gomme (bulle_kawaii, idle et event_unequip) : son original synthétisé, aucun échantillon extérieur.
Un « plop » rond : sinus dont la hauteur tombe de 950 à 230 Hz en 45 ms (la paroi qui se rétracte), petit claquement
aigu de 6 ms au moment de la rupture, et un « smack » mouillé grave et très court. Écrit pop_gomme.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 0.32
rng = S.seed(7)
t = S.temps(D)
f = 230 + 720 * np.exp(-t / 0.018)
phase = 2 * np.pi * np.cumsum(f) / S.SR
plop = np.sin(phase) * S.enveloppe(t, 0.0015, 0.055)
clic = S.passe_bande(S.bruit(D, rng), 2500, 7000) * S.enveloppe(t, 0.0005, 0.004)
smack = S.passe_bande(S.bruit(D, rng), 120, 700) * S.enveloppe(t, 0.001, 0.02)
x = 1.0 * plop + 0.35 * clic / np.max(np.abs(clic)) + 0.25 * smack / np.max(np.abs(smack))
x = S.reverb(x, 0.25, 0.12, rng)[:len(t)]
S.ecrire("pop_gomme.ogg", x)
