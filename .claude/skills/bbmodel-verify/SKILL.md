---
name: bbmodel-verify
description: Vérifier un .bbmodel avant livraison — limites du mod, boucles, superpositions, extension, poids — puis rendre les poses clés dans la convention du mod.
---

# Vérifier un .bbmodel

Toujours exécuter sur la version **optimisée** (celle qu'on livre).

```bash
python tools/optimize_bbmodel.py in.bbmodel out.bbmodel
python tools/verify_bbmodel.py out.bbmodel
```

Le script sort une ligne par contrôle. **Aucun FAIL toléré.** Les WARN sont à mentionner dans la livraison.

Ensuite, rendus de contrôle :
```bash
for a in idle:1.0 fly:0.6 glide:0.9 run:0.3 sneak:0.5; do IFS=: read n t <<< "$a"
  MODCONV=1 ANIM=$n T=$t python tools/render_bbmodel.py out.bbmodel pose_$n.png 1.5; done
python - <<'PY'
from PIL import Image
names=['idle','fly','glide','run','sneak']
tiles=[Image.open(f'pose_{n}.png').resize((525,540)) for n in names]
s=Image.new('RGB',(525*len(tiles),540))
for i,t in enumerate(tiles): s.paste(t,(525*i,0))
s.save('planche.png')
PY
```
Regarde `planche.png`. Check-list visuelle :
- [ ] pas de masse uniforme : rangées et couches lisibles
- [ ] aucun élément qui traverse le corps (sneak, run)
- [ ] course : ailes vers l'arrière (V fermé vu de dessus), pas écartées
- [ ] vol : plan basculé d'environ 40° ; élytres : presque dans le plan du dos
- [ ] sneak : repliées dans le dos, pointes vers le haut
- [ ] pas de « sac à dos » central, pas de cubes flottants
- [ ] rien de dégénéré (plume isolée loin du corps, traits parasites)

Si un point échoue → retour au générateur. Ne jamais retoucher le JSON à la main.

## Interpréter les écarts avec le jeu

| Symptôme in-game | Cause probable | Action |
|---|---|---|
| vol « à l'envers » | signe de X | changer le signe dans `mirror()` |
| course écartée au lieu de vers l'arrière | signe de Y | idem sur Y |
| clignotement noir | épaisseur nulle / coplanaire | épaisseur ≥ 0,3 + décalage profondeur |
| éléments qui suivent le joueur | effet porté par le modèle | → groupes `particle_` et `emit_` (guide, section 5 ter) |
| anim figée | mod lit une autre case / anim statique | vérifier le mapping des états et l'amplitude |
| ça clignote, ailes noires | bug du calque `_e` côté mod | `AVEC_E = False`, voir `docs/dev/bug_emissif_pour_dev.md` |
