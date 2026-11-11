"""Fêlure du ciel (effet_admin_neant : le ciel se fend comme une vitre, par à-coups) : son original synthétisé.
Quatre claquements secs de verre qui se fend (bruit aigu très bref + petit tintement résonant), de plus en plus forts,
séparés par un crépitement de micro-fissures qui accélère, sur un gémissement grave de matière sous tension.
Les claquements tombent à 0, 0,25, 0,5 et 0,75 s (à-coups des fissures dans l'animation, clé à t - 0,05).
Écrit neant_fele.ogg à côté de ce script."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S

D = 1.3
rng = S.seed(4207)
t = S.temps(D)
x = np.zeros_like(t)


def claquement(gain, fr):
    tc = S.temps(0.16)
    sec = S.passe_bande(S.bruit(0.16, rng), 2500, 9000) * np.exp(-tc / 0.006)
    corps = S.passe_bande(S.bruit(0.16, rng), 500, 2200) * np.exp(-tc / 0.018) * 0.6
    ting = sum(a * np.sin(2 * np.pi * f * tc + rng.random() * 6) * np.exp(-tc / d)
               for f, a, d in ((fr, 0.5, 0.05), (fr * 1.53, 0.3, 0.03), (fr * 2.31, 0.18, 0.02)))
    c = sec / np.max(np.abs(sec)) + corps / np.max(np.abs(corps)) * 0.6 + ting * 0.5
    return gain * c


for k, (tk, g, fr) in enumerate(((0.0, 0.45, 3100), (0.25, 0.6, 2700), (0.5, 0.8, 3500), (0.75, 1.0, 2400))):
    S.place(x, claquement(g, fr), tk + 0.004)
# crépitement de micro-fissures qui accélère entre les claquements
cr = S.passe_bande(S.impulsions(D, 90, rng, 0.0012), 1800, 8000)
cr *= np.clip(t / 0.9, 0, 1) ** 1.6 * np.exp(-np.maximum(t - 0.95, 0) / 0.08)
x += 0.35 * cr / (np.max(np.abs(cr)) + 1e-9)
# gémissement grave de la matière sous tension
gm = S.passe_bande(S.bruit(D, rng), 120, 480)
gm *= np.clip(t / 0.5, 0, 1) * np.exp(-np.maximum(t - 0.85, 0) / 0.2) * (0.7 + 0.3 * np.sin(2 * np.pi * 3.1 * t))
x += 0.3 * gm / np.max(np.abs(gm))
x = S.reverb(x, 0.5, 0.18, rng)[:len(t)]
S.ecrire("neant_fele.ogg", x, crete_db=-7.0)
