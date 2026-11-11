"""Ouverture (effet_etincelles, depart et arrivee) : son original synthétisé, aucun échantillon extérieur.
Un « pfft » d'allumage (le nœud d'étincelles prend), puis un grésillement de métal chauffé qui s'épaissit pendant que l'anneau
se dessine en spirale (crépitement aigu dense, souffle qui monte), et se stabilise en ronronnement crépitant.
Clé à 0,25 s dans depart (le nœud prend à la main), à 0,05 s dans arrivee. Écrit etincelles_ouverture.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.9
rng = S.seed(51)
x = np.zeros(int(D * S.SR))
t = S.temps(D)
# allumage : souffle bref et sourd
S.place(x, S.souffle_balaye(0.22, 900, 2600, rng, largeur=1.2) * S.enveloppe(S.temps(0.22), 0.01, 0.08), 0.0, gain=0.7)
# grésillement : crépitement qui s'épaissit (densité croissante), puis se tient
env = np.clip(t / 0.9, 0, 1) ** 0.8 * np.exp(-np.maximum(t - 1.3, 0) / 0.25)
cr = S.passe_bande(S.impulsions(D, 900, rng, 0.0012), 2500, 9000) * env
x += cr * 0.55
# grains plus gros (étincelles qui claquent), plus rares
gr = S.passe_bande(S.impulsions(D, 45, rng, 0.004), 900, 4000) * env
x += gr * 0.5
# souffle qui monte avec l'anneau
sf = S.souffle_balaye(D, 400, 1800, rng, largeur=1.6) * env
x += sf * 0.3
x = S.reverb(x, 0.6, 0.2, rng)[:len(x)]
S.ecrire("etincelles_ouverture.ogg", x, sr=S.SR)
