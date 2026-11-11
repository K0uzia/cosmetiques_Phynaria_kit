"""Verrouillage d'un cran (effet_stellaire_porte, charge et depart), v3 : son original synthétisé, aucun échantillon
extérieur. Recette d'après les mesures de la référence (.claude/references/effets/porte-etoiles.md, Sons) :
« ka-chunk » en deux temps : (1) frappe métallique (bruit 400–5000 Hz de 15 ms + partiels inharmoniques
1150/1390/1770/2360/3050 Hz, le 1150 Hz sonne le plus longtemps, ≈ 0,3 s), (2) 30 ms après, choc grave du pêne
(sinus 150 → 85 Hz, corps à 290 Hz, bruit 100–500 Hz) ; puis souffle hydraulique 3–10 kHz qui s'éteint en ≈ 0,3 s.
Écrit quatre fichiers : porte_cran, porte_cran_b (un ton plus bas), porte_cran_c (plus haut) pour les 8 crans de la
charge, et porte_cran_fin (le dernier cran, en haut, au départ : plus grave, plus long, plus de souffle)."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "..", "tools"))
import numpy as np
import synthe as S


def cran(k=1.0, lourd=0.0, graine=95):
    """k : facteur de hauteur ; lourd : 0 (cran courant) à 1 (dernier cran)."""
    rng = S.seed(graine)
    D = 0.75 + 0.35 * lourd
    x = np.zeros(int(D * S.SR))
    # (1) frappe métallique : attaque large bande + partiels de métal épais
    tc = S.temps(0.12)
    S.place(x, S.passe_bande(S.bruit(0.12, rng), 400 * k, 5000) * S.enveloppe(tc, 0.0006, 0.015), 0.0, gain=0.9)
    S.place(x, S.passe_bande(S.bruit(0.12, rng), 7000, 10500) * S.enveloppe(tc, 0.0005, 0.008), 0.0, gain=0.25)
    tr = S.temps(0.6 + 0.3 * lourd)
    for f, a, dec in ((1150, 1.0, 0.30), (1390, 0.5, 0.16), (1770, 0.55, 0.12), (2360, 0.4, 0.08), (3050, 0.25, 0.05)):
        f *= k * (1 - 0.08 * lourd)
        bat = 1 + 0.25 * np.sin(2 * np.pi * 7 * tr)              # deux modes voisins qui battent
        S.place(x, np.sin(2 * np.pi * f * tr + rng.uniform(0, 6)) * bat * S.enveloppe(tr, 0.0008, dec * (1 + 0.6 * lourd)),
                0.0, gain=0.16 * a)
    # (2) choc grave du pêne, 30 ms après
    t2 = 0.03
    tp = S.temps(0.4 + 0.2 * lourd)
    f0 = (150 + 30 * lourd) * k
    choc = np.sin(2 * np.pi * np.cumsum(85 * k * (1 - 0.15 * lourd) + (f0 - 85 * k) * np.exp(-tp / 0.03)) / S.SR)
    S.place(x, choc * S.enveloppe(tp, 0.0015, 0.11 + 0.08 * lourd), t2, gain=0.8)
    S.place(x, np.sin(2 * np.pi * np.cumsum(290 * k * (1 + 0.3 * np.exp(-tp / 0.01))) / S.SR) * S.enveloppe(tp, 0.001, 0.035), t2, gain=0.6)
    S.place(x, S.passe_bande(S.bruit(0.4, rng), 100, 500) * S.enveloppe(tp[:len(tp)], 0.001, 0.05)[:int(0.4 * S.SR)],
            t2, gain=0.7 + 0.2 * lourd)
    # souffle hydraulique (« pssh ») qui suit le verrou
    dh = 0.45 + 0.3 * lourd
    th = S.temps(dh)
    hiss = S.passe_bande(S.bruit(dh, rng), 3000, 10000) * np.interp(th, [0, 0.02, 0.1, dh], [0, 1, 0.75, 0]) ** 1.6
    S.place(x, hiss, 0.03, gain=0.3 + 0.1 * lourd)
    return S.reverb(x, 0.45, 0.16, rng)[:len(x)]


if __name__ == "__main__":
    S.ecrire("porte_cran.ogg", cran(1.0, 0, 95))
    S.ecrire("porte_cran_b.ogg", cran(0.93, 0, 96))
    S.ecrire("porte_cran_c.ogg", cran(1.07, 0, 97))
    S.ecrire("porte_cran_fin.ogg", cran(0.86, 1.0, 98))
