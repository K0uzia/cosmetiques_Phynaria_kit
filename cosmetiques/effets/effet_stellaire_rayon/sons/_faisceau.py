"""Briques communes aux sons v2 du rayon (effet_stellaire_rayon) : synthèse originale, aucun échantillon extérieur.
Caractère d'un « faisceau de transport » de science-fiction, d'après des mesures notées dans
.claude/references/effets/rayon-teleportation.md (Sons) : coup grave + nappe de souffle large bande, scintillement de
partiels fixes inharmoniques, « zip » qui descend de l'extrême aigu vers 3 kHz en 0,35 s, traîne 2–7 kHz."""
import numpy as np
import synthe as S

# partiels du scintillement : fréquences fixes inharmoniques réparties sur 200 Hz–8,5 kHz (rapports libres, pas une gamme)
PARTIELS = ((205, 0.5), (575, 0.8), (1590, 0.7), (2330, 1.0), (3410, 0.5), (4370, 0.6), (6980, 0.45), (7930, 0.5), (8420, 0.3))


def scintillement(d, rng, vitesse=30.0, profondeur=0.85, sr=S.SR):
    """Partiels fixes dont l'amplitude papillote au hasard (bruit lissé à ~vitesse Hz) : la nappe « électrique » qui grésille."""
    t = S.temps(d, sr)
    x = np.zeros_like(t)
    for f, a in PARTIELS:
        m = S.passe_bande(rng.standard_normal(len(t)), 1.0, vitesse, sr, pente=1.5)
        m = m / (np.max(np.abs(m)) + 1e-9)
        amp = (1 - profondeur) + profondeur * np.clip(0.5 + m, 0, 1)
        x += a * amp * np.sin(2 * np.pi * f * (1 + rng.uniform(-0.002, 0.002)) * t + rng.uniform(0, 6.28))
    return x / len(PARTIELS)


def nappe(d, rng, sr=S.SR):
    """Souffle large bande (150 Hz–15 kHz), un peu plus riche dans le grave et autour de 3–5 kHz."""
    b = S.bruit(d, rng, sr)
    return 0.6 * S.passe_bande(b, 150, 15000, sr, pente=1.2) + 0.5 * S.passe_bande(S.bruit(d, rng, sr), 2500, 6000, sr)


def coup(d=0.9, f0=170, f1=62, tau_f=0.05, tau=0.35, sr=S.SR):
    """Coup grave : sinus qui glisse de f0 vers f1 (« whoomp » de l'arrivée du faisceau)."""
    t = S.temps(d, sr)
    f = f1 + (f0 - f1) * np.exp(-t / tau_f)
    ph = 2 * np.pi * np.cumsum(f) / sr
    return (np.sin(ph) + 0.25 * np.sin(2 * ph)) * S.enveloppe(t, 0.012, tau)


def zip_descendant(d, f_haut=16000, f_bas=1500, tau=0.17, largeur=1500, rng=None, sr=S.SR):
    """Bande de bruit (~largeur Hz) + sinus qui tombent de f_haut vers f_bas en ralentissant (constante tau) : le « zip ».
    Deux traces parallèles (la seconde à 0,8 fois la fréquence, plus faible), le sinus s'efface vite (pas de sifflement tenu)."""
    rng = rng or S.seed(5)
    t = S.temps(d, sr)
    x = np.zeros_like(t)
    for k, (r, g) in enumerate(((1.0, 1.0), (0.8, 0.45))):
        fc = r * (f_bas + (f_haut - f_bas) * np.exp(-t / tau))
        ph = 2 * np.pi * np.cumsum(fc) / sr
        bb = S.passe_bande(rng.standard_normal(len(t)), 1.0, largeur / 2, sr, pente=1.0)
        bb /= np.max(np.abs(bb)) + 1e-9
        x += g * (0.35 * np.sin(ph + k) * np.exp(-t / 0.25) + 1.4 * bb * np.sin(ph + 0.3 + k))
    return x
