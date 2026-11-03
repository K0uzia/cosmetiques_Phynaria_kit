/* Visionneuse 3D du Vestiaire : lit un .bbmodel et l'affiche avec le mannequin posé selon l'état.
   Mêmes calculs que tools/render_bbmodel.py en convention du mod (MODCONV=1) : chaînes de groupes, keyframes
   linéaires, Molang, pose du joueur, éclairage plat par face, découpe par alpha. Sans bibliothèque, WebGL 2.
   Le cœur (Noyau) n'utilise pas le DOM : tools/test_visionneuse.mjs le compare au renderer Python. */
(function (racine) {
  "use strict";

  // ------------------------------------------------------------------ maths (affines 3x4, ligne par ligne)
  const ID = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0];
  function mul(A, B) {
    const r = new Array(12);
    for (let i = 0; i < 3; i++) {
      for (let j = 0; j < 3; j++) r[i * 4 + j] = A[i * 4] * B[j] + A[i * 4 + 1] * B[4 + j] + A[i * 4 + 2] * B[8 + j];
      r[i * 4 + 3] = A[i * 4] * B[3] + A[i * 4 + 1] * B[7] + A[i * 4 + 2] * B[11] + A[i * 4 + 3];
    }
    return r;
  }
  function appliquer(M, x, y, z) {
    return [M[0] * x + M[1] * y + M[2] * z + M[3], M[4] * x + M[5] * y + M[6] * z + M[7], M[8] * x + M[9] * y + M[10] * z + M[11]];
  }
  const T = (x, y, z) => [1, 0, 0, x, 0, 1, 0, y, 0, 0, 1, z];
  const S = (x, y, z) => [x, 0, 0, 0, 0, y, 0, 0, 0, 0, z, 0];
  /** Rotation Euler Blockbench (degrés) : X puis Y puis Z, soit Rz·Ry·Rx, comme rot_matrix() du renderer. */
  function R(rx, ry, rz) {
    const a = rx * Math.PI / 180, b = ry * Math.PI / 180, c = rz * Math.PI / 180;
    const cx = Math.cos(a), sx = Math.sin(a), cy = Math.cos(b), sy = Math.sin(b), cz = Math.cos(c), sz = Math.sin(c);
    const Rx = [1, 0, 0, 0, 0, cx, -sx, 0, 0, sx, cx, 0], Ry = [cy, 0, sy, 0, 0, 1, 0, 0, -sy, 0, cy, 0], Rz = [cz, -sz, 0, 0, sz, cz, 0, 0, 0, 0, 1, 0];
    return mul(Rz, mul(Ry, Rx));
  }

  // ------------------------------------------------------------------ Molang (sin et cos en degrés, inconnue = 0)
  const MATH = { sin: d => Math.sin(d * Math.PI / 180), cos: d => Math.cos(d * Math.PI / 180), clamp: (v, a, b) => Math.max(a, Math.min(b, v)),
    abs: Math.abs, max: Math.max, min: Math.min, sqrt: Math.sqrt, floor: Math.floor, ceil: Math.ceil, round: Math.round, pi: Math.PI };
  const cache = new Map();
  function molang(expr, q) {
    if (typeof expr === "number") return expr;
    const s = String(expr).trim();
    if (s === "") return 0;
    const n = Number(s); if (!Number.isNaN(n)) return n;
    let f = cache.get(s);
    if (!f) {
      const e = s.replace(/\bquery\./g, "q.").replace(/\bMath\./g, "math.").replace(/\bvariable\./g, "v.");
      try { f = new Function("q", "math", "v", "return (" + e + ");"); } catch (err) { f = () => 0; }
      cache.set(s, f);
    }
    try { const v = Number(f(q, MATH, q)); return Number.isFinite(v) ? v : 0; } catch (err) { return 0; }
  }
  function requetes(t, extra) {
    const base = Object.assign({ anim_time: t, life_time: t }, extra || {});
    return new Proxy(base, { get: (o, k) => (k in o ? o[k] : 0) });
  }

  // ------------------------------------------------------------------ keyframes (linéaires, bornées, comme sample())
  function echantillon(kfs, canal, t, defaut, q) {
    const l = kfs.filter(k => k.channel === canal).sort((a, b) => a.time - b.time);
    if (!l.length) return defaut;
    const val = k => ["x", "y", "z"].map(a => molang(k.data_points[0][a], q));
    if (t <= l[0].time) return val(l[0]);
    if (t >= l[l.length - 1].time) return val(l[l.length - 1]);
    for (let i = 0; i < l.length - 1; i++) {
      const a = l[i], b = l[i + 1];
      if (a.time <= t && t <= b.time) {
        const f = (t - a.time) / Math.max(1e-9, b.time - a.time), va = val(a), vb = val(b);
        return [0, 1, 2].map(j => va[j] * (1 - f) + vb[j] * f);
      }
    }
    return val(l[l.length - 1]);
  }

  // ------------------------------------------------------------------ pose du joueur (pose_joueur() du renderer)
  const PARTIES = { head: "head", hat: "head", helmet: "head", body: "body", torso: "body", chest: "body", rightarm: "right_arm", armright: "right_arm",
    leftarm: "left_arm", armleft: "left_arm", rightleg: "right_leg", legright: "right_leg", leftleg: "left_leg", legleft: "left_leg" };
  const PIVOTS = { head: [0, 24, 0], body: [0, 24, 0], right_arm: [5, 22, 0], left_arm: [-5, 22, 0], right_leg: [2, 12, 0], left_leg: [-2, 12, 0] };
  const CENTRE = [0, 16, 0];
  const partieDe = nom => PARTIES[String(nom).toLowerCase().replace(/[^a-z0-9]/g, "")] || "body";
  function etatDe(nom) {
    if (!nom) return "idle";
    const mot = String(nom).split(".").pop().toLowerCase();
    const table = [["glide", ["glide", "elytra", "plane"]], ["swim", ["swim", "nage"]], ["sleep", ["sleep", "dort", "dodo"]], ["mount", ["ride", "mount", "monture"]],
      ["sneak", ["sneak", "crouch", "accroupi"]], ["run", ["sprint", "run", "cours", "course"]], ["walk", ["walk", "marche"]]];
    for (const [e, mots] of table) if (mots.some(m => mot.includes(m))) return e;
    return "idle";
  }
  function poseJoueur(etat, t, duree) {
    const rot = {}, dep = {};
    for (const k in PIVOTS) { rot[k] = [0, 0, 0]; dep[k] = [0, 0, 0]; }
    let G = ID;
    if (etat === "walk" || etat === "run") {
      const a = (etat === "walk" ? 28 : 55) * Math.sin(2 * Math.PI * t / Math.max(duree, 1e-6));
      rot.right_leg[0] = a; rot.left_leg[0] = -a; rot.right_arm[0] = -a * 0.8; rot.left_arm[0] = a * 0.8;
    } else if (etat === "sneak") {
      rot.body[0] = -28.6; dep.body[1] = -3.2; dep.head[1] = -4.2;
      for (const c of ["right_arm", "left_arm"]) { rot[c][0] = 23; dep[c][1] = -3.2; }
      for (const c of ["right_leg", "left_leg"]) { dep[c][2] = 4.0; dep[c][1] = -0.2; }
    } else if (etat === "mount") {
      rot.right_leg[0] = 81; rot.right_leg[1] = -18; rot.left_leg[0] = 81; rot.left_leg[1] = 18;
      rot.right_arm[0] = 36; rot.left_arm[0] = 36;
    } else if (etat === "swim" || etat === "glide") G = R(-90, 0, 0);
    else if (etat === "sleep") G = R(90, 0, 0);
    const out = {};
    for (const k in PIVOTS) {
      const p = PIVOTS[k], d = dep[k];
      // G·(R·(x − pivot) + pivot + d − C) + C
      out[k] = mul(T(...CENTRE), mul(G, mul(T(p[0] + d[0] - CENTRE[0], p[1] + d[1] - CENTRE[1], p[2] + d[2] - CENTRE[2]), mul(R(...rot[k]), T(-p[0], -p[1], -p[2])))));
    }
    return out;
  }

  // ------------------------------------------------------------------ géométrie
  const COINS = { // (TL, TR, BR, BL) selon (a, b), comme FACE_CORNERS
    north: (a, b) => [[b[0], b[1], a[2]], [a[0], b[1], a[2]], [a[0], a[1], a[2]], [b[0], a[1], a[2]]],
    south: (a, b) => [[a[0], b[1], b[2]], [b[0], b[1], b[2]], [b[0], a[1], b[2]], [a[0], a[1], b[2]]],
    east: (a, b) => [[b[0], b[1], b[2]], [b[0], b[1], a[2]], [b[0], a[1], a[2]], [b[0], a[1], b[2]]],
    west: (a, b) => [[a[0], b[1], a[2]], [a[0], b[1], b[2]], [a[0], a[1], b[2]], [a[0], a[1], a[2]]],
    up: (a, b) => [[a[0], b[1], a[2]], [b[0], b[1], a[2]], [b[0], b[1], b[2]], [a[0], b[1], b[2]]],
    down: (a, b) => [[a[0], a[1], b[2]], [b[0], a[1], b[2]], [b[0], a[1], a[2]], [a[0], a[1], a[2]]],
  };
  const GRIS = [[120, 120, 128], [100, 100, 108], [88, 88, 96], [135, 135, 143], [30, 30, 40]];

  /** Prépare un modèle : faces du cosmétique (rattachées à leur élément) et du mannequin. */
  function preparer(m) {
    const tw = m.resolution.width, th = m.resolution.height;
    const parId = new Map(m.elements.map(e => [e.uuid, e]));
    const faces = [];          // {el, coins locaux, uv | couleur}
    const elements = [];       // {M élément, chaîne de groupes, partie}
    function parcourir(n, chaine, partie) {
      if (typeof n === "string") {
        const e = parId.get(n); if (!e) return;
        const o = e.origin || [0, 0, 0], r = e.rotation || [0, 0, 0];
        const idx = elements.push({ M: mul(T(...o), mul(R(...r), T(-o[0], -o[1], -o[2]))), chaine, partie }) - 1;
        const inf = e.inflate || 0, a = e.from.map(v => v - inf), b = e.to.map(v => v + inf);
        for (const [nom, fd] of Object.entries(e.faces || {})) {
          if (fd.texture === null || fd.texture === undefined) continue;
          const [u1, v1, u2, v2] = fd.uv;
          if (u1 === u2 || v1 === v2) continue;
          faces.push({ el: idx, coins: COINS[nom](a, b), uv: [u1 / tw, v1 / th, u2 / tw, v1 / th, u2 / tw, v2 / th, u1 / tw, v2 / th] });
        }
      } else {
        const suite = chaine.concat([n]);
        for (const c of n.children || []) parcourir(c, suite, partie);
      }
    }
    // Particules (guide, section 5 ter) : forme dans un groupe particle_<nom> à la racine, non portée.
    const particules = new Map();   // nom -> {racine, faces: [{el, coins, uv}], elements}
    const emetteurs = [];           // {nom, noeud, chaine, partie}
    for (const n of m.outliner) {
      if (typeof n === "object" && String(n.name || "").startsWith("particle_")) {
        const nom = n.name.slice(9), avant = faces.length;
        parcourir(n, [], "body");
        particules.set(nom, { racine: n, faces: faces.splice(avant) });
        continue;
      }
      parcourir(n, [], typeof n === "object" ? partieDe(n.name || "") : "body");
    }
    // Points de départ : groupes emit_<nom>, emit_<nom>2, emit_<nom>_3…, portés et animés avec le cosmétique.
    (function chercher(n, chaine, partie) {
      if (typeof n !== "object") return;
      const mt = /^emit_(.+?)_?\d*$/.exec(n.name || "");
      if (mt) emetteurs.push({ nom: mt[1], noeud: n, chaine, partie });
      for (const c of n.children || []) chercher(c, chaine.concat([n]), partie);
    })({ children: m.outliner.filter(n => typeof n === "object" && !String(n.name || "").startsWith("particle_")) }, [], "body");
    for (const e of emetteurs) {
      // partie du corps : celle du groupe de premier niveau
      const top = e.chaine[1] || e.noeud; e.partie = partieDe(top.name || ""); e.chaine = e.chaine.slice(1);
    }
    // Mannequin (face avant = −z, droite du joueur = +x)
    const boites = [[[-4, 24, -4], [4, 32, 4], 0, "head", 3], [[-4, 12, -2], [4, 24, 2], 1, "body"], [[4, 12, -2], [8, 24, 2], 2, "right_arm"],
      [[-8, 12, -2], [-4, 24, 2], 2, "left_arm"], [[0, 0, -2], [4, 12, 2], 1, "right_leg"], [[-4, 0, -2], [0, 12, 2], 2, "left_leg"]];
    const mannequin = [];
    for (const [a, b, c, partie, avant] of boites)
      for (const nom in COINS) mannequin.push({ partie, coins: COINS[nom](a, b), couleur: GRIS[nom === "north" && avant !== undefined ? avant : c] });
    for (const x of [-2.5, 1.0]) mannequin.push({ partie: "head", coins: [[x, 29, -4.01], [x + 1.5, 29, -4.01], [x + 1.5, 27.5, -4.01], [x, 27.5, -4.01]], couleur: GRIS[4] });
    const anims = new Map((m.animations || []).map(a => [a.name, a]));
    // Calque lumineux : seconde texture dont le nom finit par _e (guide, section 5 bis).
    const calque = (m.textures || []).slice(1).find(t => /_e(\.png)?$/i.test(t.name || "") && t.source);
    return { m, faces, elements, mannequin, anims, particules, emetteurs, calque: calque ? calque.source : null };
  }

  /** Matrices des groupes à l'instant t (convention du mod : rotation de base + rotation animée). */
  function matricesGroupes(P, anim, t, extra) {
    const anims = anim ? anim.animators || {} : {};
    const q = requetes(t, extra);
    const cacheM = new Map();
    return function (g) {
      if (cacheM.has(g)) return cacheM.get(g);
      const o = g.origin || [0, 0, 0];
      let rot = g.rotation || [0, 0, 0], sc = [1, 1, 1], pos = [0, 0, 0];
      const a = anims[g.uuid];
      if (a) {
        const ar = echantillon(a.keyframes, "rotation", t, [0, 0, 0], q);
        rot = [rot[0] + ar[0], rot[1] + ar[1], rot[2] + ar[2]];
        sc = echantillon(a.keyframes, "scale", t, [1, 1, 1], q);
        pos = echantillon(a.keyframes, "position", t, [0, 0, 0], q);
      }
      const M = mul(T(o[0] + pos[0], o[1] + pos[1], o[2] + pos[2]), mul(R(...rot), mul(S(...sc), T(-o[0], -o[1], -o[2]))));
      cacheM.set(g, M); return M;
    };
  }

  /** Temps local de l'animation : en boucle pour loop, borné sinon (comme load_model). */
  function tempsLocal(anim, t) {
    if (!anim) return 0;
    const L = Number(anim.length) || 0;
    return anim.loop === "loop" && L > 0 ? t % L : t;
  }

  /** Positions monde des faces du cosmétique (et du mannequin si demandé) : tableau de quads [[x,y,z]×4]. */
  function image(P, nomAnim, t, options) {
    const opt = Object.assign({ poser: true, mannequin: true, extra: null }, options || {});
    const anim = P.anims.get(nomAnim) || null;
    const tl = tempsLocal(anim, t);
    const duree = anim ? Number(anim.length) || 1 : 1;
    const pose = opt.poser ? poseJoueur(etatDe(nomAnim), tl, duree) : null;
    const groupe = matricesGroupes(P, anim, tl, opt.extra);
    const Mel = P.elements.map(el => {
      let M = el.M;
      for (let i = el.chaine.length - 1; i >= 0; i--) M = mul(groupe(el.chaine[i]), M);
      return pose ? mul(pose[el.partie], M) : M;
    });
    const cosm = P.faces.map(f => f.coins.map(c => appliquer(Mel[f.el], c[0], c[1], c[2])));
    const mann = opt.mannequin ? P.mannequin.map(f => f.coins.map(c => pose ? appliquer(pose[f.partie], c[0], c[1], c[2]) : c)) : [];
    const emit = (P.emetteurs || []).map(e => {
      let M = groupe(e.noeud);
      for (let i = e.chaine.length - 1; i >= 0; i--) M = mul(groupe(e.chaine[i]), M);
      if (pose) M = mul(pose[e.partie], M);
      const o = e.noeud.origin || [0, 0, 0];
      return { nom: e.nom, pos: appliquer(M, o[0], o[1], o[2]) };
    });
    return { cosm, mann, emit };
  }

  /** Quads monde d'une particule : pivot de son groupe placé en pos, animée par particle_<nom>_fall ou _rest. */
  function quadsParticule(P, nom, pos, age, pose, echelle, balance) {
    const part = P.particules.get(nom); if (!part) return [];
    const anim = P.anims.get(`particle_${nom}_${pose}`) || null;
    const groupe = matricesGroupes(P, anim, tempsLocal(anim, age), null);
    const o = part.racine.origin || [0, 0, 0];
    // Sans animation de chute, la particule se balance toute seule.
    const sway = !anim && pose === "fall" ? R(0, balance * 40, 22 * Math.sin(age * 2.6 + balance * 6)) : ID;
    const base = mul(T(pos[0], pos[1], pos[2]), mul(sway, mul(S(echelle, echelle, echelle), T(-o[0], -o[1], -o[2]))));
    return part.faces.map(f => {
      const el = P.elements[f.el];
      let M = el.M;
      for (let i = el.chaine.length - 1; i >= 0; i--) M = mul(groupe(el.chaine[i]), M);
      M = mul(base, M);
      return { coins: f.coins.map(c => appliquer(M, c[0], c[1], c[2])), uv: f.uv };
    });
  }

  const Noyau = { preparer, image, quadsParticule, poseJoueur, etatDe, partieDe, molang, R, mul, appliquer };

  // ------------------------------------------------------------------ rendu WebGL 2
  const VS = `#version 300 es
  in vec3 aPos; in vec2 aUv; in vec3 aCol; in float aOmbre;
  uniform mat4 uVP; out vec2 vUv; out vec3 vCol; out float vOmbre;
  void main(){ gl_Position = uVP * vec4(aPos, 1.0); vUv = aUv; vCol = aCol; vOmbre = aOmbre; }`;
  const FS = `#version 300 es
  precision mediump float; in vec2 vUv; in vec3 vCol; in float vOmbre;
  uniform sampler2D uTex; uniform sampler2D uLum; uniform float uJour; uniform float uAvecLum; out vec4 sortie;
  void main(){
    if (vCol.r < 0.0) {
      vec4 c = texture(uTex, vUv); if (c.a < 0.5) discard;
      vec4 e = texture(uLum, vUv);
      // Calque _e : s'ajoute à la couleur, visible dans le noir ; noir ou transparent = rien.
      vec3 lum = uAvecLum * e.rgb * step(0.5, e.a);
      sortie = vec4(min(c.rgb * vOmbre * uJour + lum, 1.0), 1.0);
    }
    else sortie = vec4(vCol * vOmbre * uJour, 1.0);
  }`;
  const LUMIERE = (() => { const l = [-0.4, 1.0, 0.6], n = Math.hypot(...l); return l.map(v => v / n); })();

  function creer(canvas) {
    const gl = canvas.getContext("webgl2", { antialias: true, alpha: false });
    if (!gl) return null;
    const prog = programme(gl, VS, FS);
    const loc = { pos: gl.getAttribLocation(prog, "aPos"), uv: gl.getAttribLocation(prog, "aUv"), col: gl.getAttribLocation(prog, "aCol"), ombre: gl.getAttribLocation(prog, "aOmbre"),
      vp: gl.getUniformLocation(prog, "uVP"), tex: gl.getUniformLocation(prog, "uTex"), lum: gl.getUniformLocation(prog, "uLum"),
      jour: gl.getUniformLocation(prog, "uJour"), avecLum: gl.getUniformLocation(prog, "uAvecLum") };
    const tampons = { pos: gl.createBuffer(), uv: gl.createBuffer(), col: gl.createBuffer(), ombre: gl.createBuffer(), idx: gl.createBuffer() };
    const tex = gl.createTexture(), texLum = gl.createTexture();
    const MAX_PART = 64;
    const MOUVEMENTS = { legere: [-8, 3], normale: [-16, 2.5], lourde: [-40, 1.5], flotte: [0, 0.8], monte: [6, 2] };   // vitesse verticale, dérive (px/s)
    const etat = { P: null, anim: null, t: 0, lecture: true, extra: null, theta: -35, phi: 18, dist: 70, cible: [0, 16, 0], n: 0, dernier: 0, distBase: 70, cibleBase: [0, 16, 0],
      surTemps: null, fond: [0.055, 0.051, 0.075], nuit: false, calqueVisible: true,
      particules: true, mouvement: "legere", parts: [], cumul: {}, capacite: 0 };
    let posArr, ombreArr;

    function charger(modele) {
      const P = preparer(modele);
      etat.P = P;
      const maxFacesPart = Math.max(0, ...[...P.particules.values()].map(p => p.faces.length));
      const fixe = P.faces.length + P.mannequin.length, nq = fixe + MAX_PART * maxFacesPart;
      etat.n = nq; etat.fixe = fixe; etat.parts = []; etat.cumul = {};
      const uv = new Float32Array(nq * 8), col = new Float32Array(nq * 12), idx = new Uint32Array(nq * 6);
      P.faces.forEach((f, i) => { uv.set(f.uv, i * 8); for (let k = 0; k < 4; k++) col.set([-1, 0, 0], i * 12 + k * 3); });
      P.mannequin.forEach((f, j) => { const i = P.faces.length + j; for (let k = 0; k < 4; k++) col.set(f.couleur.map(v => v / 255), i * 12 + k * 3); });
      for (let i = fixe; i < nq; i++) for (let k = 0; k < 4; k++) col.set([-1, 0, 0], i * 12 + k * 3);
      etat.uvArr = uv;
      for (let i = 0; i < nq; i++) idx.set([i * 4, i * 4 + 1, i * 4 + 2, i * 4, i * 4 + 2, i * 4 + 3], i * 6);
      posArr = new Float32Array(nq * 12); ombreArr = new Float32Array(nq * 4);
      gl.bindBuffer(gl.ARRAY_BUFFER, tampons.uv); gl.bufferData(gl.ARRAY_BUFFER, uv, gl.DYNAMIC_DRAW);
      remplir(gl, tampons.col, col);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, tampons.idx); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idx, gl.STATIC_DRAW);
      gl.bindBuffer(gl.ARRAY_BUFFER, tampons.pos); gl.bufferData(gl.ARRAY_BUFFER, posArr.byteLength, gl.DYNAMIC_DRAW);
      gl.bindBuffer(gl.ARRAY_BUFFER, tampons.ombre); gl.bufferData(gl.ARRAY_BUFFER, ombreArr.byteLength, gl.DYNAMIC_DRAW);
      // Textures embarquées : pixels nets, comme le jeu. Calque _e absent : texture noire (n'ajoute rien).
      const src = modele.textures && modele.textures[0] && modele.textures[0].source;
      etat.aCalque = !!P.calque;
      return Promise.all([texture(gl, tex, src), texture(gl, texLum, P.calque)]);
    }

    /** Cadre la caméra sur le cosmétique et le corps, sur quelques instants de l'animation. */
    function cadrer() {
      if (!etat.P) return;
      const a = etat.P.anims.get(etat.anim), L = a ? Number(a.length) || 1 : 1;
      let lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
      for (let k = 0; k < 6; k++) {
        const { cosm, mann } = image(etat.P, etat.anim, k * L / 6, { extra: etat.extra });
        for (const q of cosm.concat(mann)) for (const p of q) for (let i = 0; i < 3; i++) { lo[i] = Math.min(lo[i], p[i]); hi[i] = Math.max(hi[i], p[i]); }
      }
      etat.cible = etat.cibleBase = lo.map((v, i) => (v + hi[i]) / 2);
      const r = Math.max(10, Math.hypot(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]) / 2);
      etat.dist = etat.distBase = r / Math.sin(15 * Math.PI / 180) * 1.02;
    }

    function dessiner(maintenant) {
      if (!etat.P) return;
      const w = canvas.clientWidth * devicePixelRatio | 0, h = canvas.clientHeight * devicePixelRatio | 0;
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
      if (etat.lecture && etat.dernier) {
        etat.t += (maintenant - etat.dernier) / 1000;
        const a = etat.P.anims.get(etat.anim);
        if (a && a.loop !== "loop" && etat.t > Number(a.length) + 0.6) etat.t = 0;   // attaque, blessé : rejoués en boucle pour l'aperçu
        if (etat.surTemps) etat.surTemps(etat.t);
      }
      etat.dernier = maintenant;
      const { cosm, mann, emit } = image(etat.P, etat.anim, etat.t, { extra: etat.extra });
      const dt = etat.lecture && etat.dernierPart ? Math.min(0.1, (maintenant - etat.dernierPart) / 1000) : 0;
      etat.dernierPart = maintenant;
      simulerParticules(emit, dt);
      const quads = cosm.concat(mann);
      const quadsPart = [];
      for (const p of etat.parts) {
        const echelle = p.age > p.vie - 0.5 ? Math.max(0, (p.vie - p.age) / 0.5) : 1;   // rétrécit puis disparaît
        for (const q of quadsParticule(etat.P, p.nom, p.pos, p.pose === "rest" ? p.age - p.posee : p.age, p.pose, echelle, p.balance)) {
          if (quads.length + quadsPart.length >= etat.n) break;
          quadsPart.push(q);
        }
      }
      quadsPart.forEach((q, j) => etat.uvArr.set(q.uv, (etat.fixe + j) * 8));
      if (quadsPart.length) { gl.bindBuffer(gl.ARRAY_BUFFER, tampons.uv); gl.bufferSubData(gl.ARRAY_BUFFER, etat.fixe * 32, etat.uvArr.subarray(etat.fixe * 8, (etat.fixe + quadsPart.length) * 8)); }
      for (const q of quadsPart) quads.push(q.coins);
      for (let i = 0; i < quads.length; i++) {
        const q = quads[i];
        for (let k = 0; k < 4; k++) posArr.set(q[k], i * 12 + k * 3);
        // éclairage plat : 0,55 + 0,45·|n·l|, comme le renderer
        const ux = q[1][0] - q[0][0], uy = q[1][1] - q[0][1], uz = q[1][2] - q[0][2], vx = q[3][0] - q[0][0], vy = q[3][1] - q[0][1], vz = q[3][2] - q[0][2];
        let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx; const ln = Math.hypot(nx, ny, nz) || 1;
        const o = 0.55 + 0.45 * Math.abs((nx * LUMIERE[0] + ny * LUMIERE[1] + nz * LUMIERE[2]) / ln);
        ombreArr.fill(o, i * 4, i * 4 + 4);
      }
      gl.bindBuffer(gl.ARRAY_BUFFER, tampons.pos); gl.bufferSubData(gl.ARRAY_BUFFER, 0, posArr);
      gl.bindBuffer(gl.ARRAY_BUFFER, tampons.ombre); gl.bufferSubData(gl.ARRAY_BUFFER, 0, ombreArr);
      gl.viewport(0, 0, w, h);
      gl.clearColor(...(etat.nuit ? [0.012, 0.012, 0.024] : etat.fond), 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.enable(gl.DEPTH_TEST); gl.disable(gl.CULL_FACE);
      gl.useProgram(prog);
      gl.uniformMatrix4fv(loc.vp, false, vueProjection(etat, w / h));
      attribut(gl, tampons.pos, loc.pos, 3); attribut(gl, tampons.uv, loc.uv, 2); attribut(gl, tampons.col, loc.col, 3); attribut(gl, tampons.ombre, loc.ombre, 1);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex); gl.uniform1i(loc.tex, 0);
      gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, texLum); gl.uniform1i(loc.lum, 1);
      gl.uniform1f(loc.jour, etat.nuit ? 0.16 : 1.0); gl.uniform1f(loc.avecLum, etat.aCalque && etat.calqueVisible ? 1 : 0);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, tampons.idx);
      gl.drawElements(gl.TRIANGLES, quads.length * 6, gl.UNSIGNED_INT, 0);
    }

    /** Particules : réglages par défaut du guide (2 par seconde et par sorte, 6 s, Légère, se posent au sol y = 0). */
    function simulerParticules(emit, dt) {
      if (!etat.P || !dt) return;
      const [vy, derive] = MOUVEMENTS[etat.mouvement] || MOUVEMENTS.legere;
      if (etat.particules) {
        const parSorte = {};
        for (const e of emit) if (etat.P.particules.has(e.nom)) (parSorte[e.nom] = parSorte[e.nom] || []).push(e.pos);
        for (const nom in parSorte) {
          etat.cumul[nom] = (etat.cumul[nom] || 0) + dt * 2;
          while (etat.cumul[nom] >= 1 && etat.parts.length < MAX_PART) {
            etat.cumul[nom] -= 1;
            const pts = parSorte[nom], d = pts[Math.floor(Math.random() * pts.length)];
            const a = Math.random() * Math.PI * 2;
            etat.parts.push({ nom, pos: d.slice(), v: [Math.cos(a) * derive, vy, Math.sin(a) * derive], age: 0, vie: 6, pose: "fall", posee: 0, balance: Math.random() });
          }
          if (etat.cumul[nom] > 1) etat.cumul[nom] = 1;
        }
      }
      for (const p of etat.parts) {
        p.age += dt;
        if (p.pose === "fall") {
          for (let i = 0; i < 3; i++) p.pos[i] += p.v[i] * dt;
          if (etat.mouvement !== "flotte" && etat.mouvement !== "monte" && p.pos[1] <= 0.3) { p.pos[1] = 0.3; p.pose = "rest"; p.posee = p.age; }
        }
      }
      etat.parts = etat.parts.filter(p => p.age < p.vie);
    }

    let boucle = 0, actif = true;
    const tic = m => { if (!actif) return; dessiner(m); boucle = requestAnimationFrame(tic); };
    boucle = requestAnimationFrame(tic);

    // Orbite : glisser pour tourner, molette ou pincement pour zoomer, double-clic pour recadrer.
    const pointeurs = new Map(); let ecart0 = 0, dist0 = 0;
    canvas.addEventListener("pointerdown", e => { canvas.setPointerCapture(e.pointerId); pointeurs.set(e.pointerId, [e.clientX, e.clientY]);
      if (pointeurs.size === 2) { const [a, b] = [...pointeurs.values()]; ecart0 = Math.hypot(a[0] - b[0], a[1] - b[1]); dist0 = etat.dist; } });
    canvas.addEventListener("pointermove", e => {
      if (!pointeurs.has(e.pointerId)) return;
      const [x0, y0] = pointeurs.get(e.pointerId); pointeurs.set(e.pointerId, [e.clientX, e.clientY]);
      if (pointeurs.size === 2) { const [a, b] = [...pointeurs.values()]; const ec = Math.hypot(a[0] - b[0], a[1] - b[1]); if (ecart0) etat.dist = borne(dist0 * ecart0 / ec, etat.distBase * 0.25, etat.distBase * 3); return; }
      etat.theta -= (e.clientX - x0) * 0.5; etat.phi = borne(etat.phi + (e.clientY - y0) * 0.4, -85, 85);
    });
    const fin = e => { pointeurs.delete(e.pointerId); };
    canvas.addEventListener("pointerup", fin); canvas.addEventListener("pointercancel", fin);
    canvas.addEventListener("wheel", e => { e.preventDefault(); etat.dist = borne(etat.dist * Math.exp(e.deltaY * 0.0012), etat.distBase * 0.25, etat.distBase * 3); }, { passive: false });
    canvas.addEventListener("dblclick", () => recadrer());
    canvas.addEventListener("keydown", e => {
      const pas = { ArrowLeft: [8, 0], ArrowRight: [-8, 0], ArrowUp: [0, -6], ArrowDown: [0, 6] }[e.key];
      if (pas) { e.preventDefault(); e.stopPropagation(); etat.theta += pas[0]; etat.phi = borne(etat.phi + pas[1], -85, 85); }
      else if (e.key === "+" || e.key === "=") etat.dist = borne(etat.dist * 0.85, etat.distBase * 0.25, etat.distBase * 3);
      else if (e.key === "-") etat.dist = borne(etat.dist / 0.85, etat.distBase * 0.25, etat.distBase * 3);
      else if (e.key === "0") recadrer();
    });
    function recadrer() { etat.theta = -35; etat.phi = 18; etat.dist = etat.distBase; etat.cible = etat.cibleBase.slice(); }

    return {
      charger: async (modele, nomAnim) => { await charger(modele); etat.anim = nomAnim; etat.t = 0; cadrer(); recadrer(); },
      animation: nomAnim => { etat.anim = nomAnim; etat.t = 0; etat.parts = []; cadrer(); },
      lecture: v => { etat.lecture = v; etat.dernier = 0; },
      temps: t => { etat.t = t; },
      duree: () => { const a = etat.P && etat.P.anims.get(etat.anim); return a ? Number(a.length) || 0 : 0; },
      requetes: extra => { etat.extra = extra; },
      surTemps: f => { etat.surTemps = f; },
      recadrer,
      nuit: v => { etat.nuit = v; },
      calque: v => { etat.calqueVisible = v; },
      aCalque: () => !!(etat.P && etat.P.calque),
      aParticules: () => !!(etat.P && etat.P.particules.size && etat.P.emetteurs.length),
      particules: v => { etat.particules = v; if (!v) etat.parts = []; },
      mouvement: v => { etat.mouvement = v; },
      stats: () => ({ particules: etat.parts.length, t: etat.t, quads: etat.n }),
      /** Pour les tests : avance l'animation et les particules de s secondes, par pas de 50 ms. */
      avancer: s => { for (let k = 0; k < s / 0.05; k++) { etat.t += 0.05; simulerParticules(image(etat.P, etat.anim, etat.t, { extra: etat.extra }).emit, 0.05); } },
      detruire: () => { actif = false; cancelAnimationFrame(boucle); const ext = gl.getExtension("WEBGL_lose_context"); if (ext) ext.loseContext(); },
    };
  }

  function vueProjection(e, ratio) {
    const th = e.theta * Math.PI / 180, ph = e.phi * Math.PI / 180;
    // theta = 0 : caméra devant le joueur (côté −z).
    const oeil = [e.cible[0] + e.dist * Math.cos(ph) * Math.sin(th), e.cible[1] + e.dist * Math.sin(ph), e.cible[2] - e.dist * Math.cos(ph) * Math.cos(th)];
    const f = norm(sub(e.cible, oeil)), d = norm(croix(f, [0, 1, 0])), h = croix(d, f);
    const V = [d[0], h[0], -f[0], 0, d[1], h[1], -f[1], 0, d[2], h[2], -f[2], 0, -dot(d, oeil), -dot(h, oeil), dot(f, oeil), 1];
    const fov = 30 * Math.PI / 180, t = 1 / Math.tan(fov / 2), pres = 1, loin = 2000;
    const Pm = [t / ratio, 0, 0, 0, 0, t, 0, 0, 0, 0, (loin + pres) / (pres - loin), -1, 0, 0, 2 * loin * pres / (pres - loin), 0];
    return mul4(Pm, V);
  }
  function mul4(a, b) { const r = new Float32Array(16); for (let c = 0; c < 4; c++) for (let l = 0; l < 4; l++) { let s = 0; for (let k = 0; k < 4; k++) s += a[k * 4 + l] * b[c * 4 + k]; r[c * 4 + l] = s; } return r; }
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]], dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const croix = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const norm = a => { const n = Math.hypot(...a) || 1; return a.map(v => v / n); };
  const borne = (v, a, b) => Math.max(a, Math.min(b, v));
  function texture(gl, t, src) {
    return new Promise(ok => {
      gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 0]));
      for (const [p, v] of [[gl.TEXTURE_MIN_FILTER, gl.NEAREST], [gl.TEXTURE_MAG_FILTER, gl.NEAREST], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]])
        gl.texParameteri(gl.TEXTURE_2D, p, v);
      if (!src) return ok();
      const img = new Image();
      img.onload = () => { gl.bindTexture(gl.TEXTURE_2D, t); gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img); ok(); };
      img.onerror = () => ok();
      img.src = src;
    });
  }
  function remplir(gl, b, data) { gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW); }
  function attribut(gl, b, loc, n) { if (loc < 0) return; gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, n, gl.FLOAT, false, 0, 0); }
  function programme(gl, vs, fs) {
    const p = gl.createProgram();
    for (const [type, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      gl.attachShader(p, s);
    }
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    return p;
  }

  const api = { Noyau, creer };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else racine.Visionneuse = api;
})(typeof window !== "undefined" ? window : globalThis);
