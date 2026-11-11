"""Synthèse de sons originaux pour les cosmétiques (numpy), écrits en OGG Vorbis mono (soundfile / libsndfile).

Aucun son récupéré sur le web ni extrait d'un jeu : tout est calculé ici, graine fixe, donc reproductible.
Usage dans cosmetiques/<categorie>/<nom>/sons/<nom_son>.py :
    import synthe as S
    x = S.cloche(880, 1.2) + ...
    S.ecrire("carillon_celeste.ogg", x)      # crête -6 dBFS, fondus, contrôle du mod (tools/sons.py)
Dépendance : pip install soundfile (libsndfile 1.2 écrit l'OGG Vorbis)."""
import os
import numpy as np

SR = 44100
CRETE_DB = -6.8          # -6 dBFS au plus après décodage (le Vorbis dépasse un peu la crête du signal)


def temps(d, sr=SR):
    return np.arange(int(round(d * sr))) / sr


def seed(n):
    return np.random.default_rng(n)


def enveloppe(t, attaque=0.005, decroissance=0.5):
    """Montée linéaire courte puis décroissance exponentielle (constante de temps en s)."""
    a = np.clip(t / max(attaque, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attaque, 0) / decroissance)


def cloche(f, d, decroissance=0.6, partiels=((1, 1.0), (2.0, 0.35), (3.01, 0.12), (4.2, 0.05)), desaccord=0.6, sr=SR):
    """Carillon doux : partiels presque harmoniques (verre, célesta), les aigus s'éteignent plus vite ; léger battement."""
    t = temps(d, sr)
    x = np.zeros_like(t)
    for k, (r, a) in enumerate(partiels):
        dk = decroissance / (1 + 0.9 * k)
        for s in (-1, 1):
            x += 0.5 * a * np.sin(2 * np.pi * (f * r + s * desaccord * 0.5) * t + k) * enveloppe(t, 0.004, dk)
    return x


def bruit(d, rng, sr=SR):
    return rng.standard_normal(int(round(d * sr)))


def passe_bande(x, bas, haut, sr=SR, pente=1.0):
    """Filtre passe-bande doux dans le domaine fréquentiel (gaussien en log-fréquence hors de la bande)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / sr)
    f = np.maximum(f, 1.0)
    g = np.ones_like(f)
    g[f < bas] = np.exp(-(np.log2(bas / f[f < bas]) / (0.5 * pente)) ** 2)
    g[f > haut] = np.exp(-(np.log2(f[f > haut] / haut) / (0.5 * pente)) ** 2)
    return np.fft.irfft(X * g, len(x))


def souffle_balaye(d, f0, f1, rng, largeur=1.2, sr=SR, morceaux=48):
    """Bruit dont la bande centrale glisse de f0 à f1 (souffle, froissement) : fenêtres recouvrantes filtrées."""
    n = int(round(d * sr))
    out = np.zeros(n)
    w = n // morceaux * 2
    fen = np.hanning(w)
    for i in range(morceaux):
        a = i * w // 2
        if a >= n:
            break
        seg = rng.standard_normal(w)
        fc = f0 * (f1 / f0) ** (i / max(morceaux - 1, 1))
        seg = passe_bande(seg, fc / 2 ** (largeur / 2), fc * 2 ** (largeur / 2), sr) * fen
        b = min(n, a + w)
        out[a:b] += seg[:b - a]
    return out


def impulsions(d, densite, rng, duree_imp=0.0025, sr=SR):
    """Crépitement : impulsions brèves au hasard (densité par seconde, amplitude aléatoire)."""
    n = int(round(d * sr))
    out = np.zeros(n)
    m = int(densite * d)
    li = max(4, int(duree_imp * sr))
    forme = np.exp(-np.arange(li) / (li / 5)) * np.sign(rng.standard_normal(li))
    for p in rng.integers(0, max(1, n - li), m):
        out[p:p + li] += rng.uniform(0.3, 1.0) * forme
    return out


def reverb(x, d=0.6, mix=0.25, rng=None, sr=SR):
    """Petite réverbération : convolution par un bruit à décroissance exponentielle, adoucie."""
    rng = rng or seed(1)
    t = temps(d, sr)
    ir = rng.standard_normal(len(t)) * np.exp(-t / (d / 5))
    ir = passe_bande(ir, 200, 6000, sr)
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
    y = np.fft.irfft(np.fft.rfft(x, len(x) + len(ir)) * np.fft.rfft(ir, len(x) + len(ir)), len(x) + len(ir))[:len(x) + len(ir)]
    out = np.zeros(len(y))
    out[:len(x)] += x * (1 - mix)
    out += y * mix
    return out


def place(dst, src, t, sr=SR, gain=1.0):
    """Ajoute src dans dst à l'instant t (s)."""
    a = int(round(t * sr))
    b = min(len(dst), a + len(src))
    dst[a:b] += gain * src[:b - a]
    return dst


def finir(x, crete_db=CRETE_DB, fondu=0.02, sr=SR):
    """Retire le continu, fondus d'entrée (2 ms) et de sortie, normalise la crête à crete_db dBFS."""
    x = x - np.mean(x)
    n_in, n_out = int(0.002 * sr), int(fondu * sr)
    x[:n_in] *= np.linspace(0, 1, n_in)
    x[-n_out:] *= np.linspace(1, 0, n_out) ** 2
    return x / (np.max(np.abs(x)) + 1e-12) * 10 ** (crete_db / 20)


def ecrire(chemin, x, sr=SR, cible_ko=40, crete_db=CRETE_DB):
    """Écrit un OGG Vorbis mono, qualité réduite pas à pas jusqu'à passer sous cible_ko ; contrôle comme le mod."""
    import soundfile as sf
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sons import lire_ogg
    x = finir(np.asarray(x, dtype=np.float64), crete_db, sr=sr)
    for niveau in (0.45, 0.55, 0.65, 0.75, 0.85, 0.95):        # compression_level : 0 = meilleure qualité
        sf.write(chemin, x.astype(np.float32), sr, format="OGG", subtype="VORBIS", compression_level=niveau)
        if os.path.getsize(chemin) <= cible_ko * 1024:
            break
    info = lire_ogg(open(chemin, "rb").read())
    print(f"{os.path.basename(chemin)} : {info['duree']:.2f} s, {sr} Hz mono, {info['octets'] / 1024:.1f} Ko, crête {crete_db:g} dBFS")
    return info
