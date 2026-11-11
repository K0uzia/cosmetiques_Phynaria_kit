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

  // ------------------------------------------------------------------ Molang du guide (section 6.3)
  // Analyseur écrit à la main, le même que molang() de tools/render_bbmodel.py (mêmes règles, même ordre de calcul).
  // Priorités, de la plus faible à la plus forte :
  //   ?: (à droite ; « a ? b » sans « : » vaut 0 si faux)  ||  &&  == !=  < <= > >=  + -  * /  - ! + (unaires)
  // Vrai = 1, faux = 0 ; « 1--0.5 » = 1 − (−0,5). Instructions « ; », « v.x = … » (mémorisée), « t.x = … » (temporaire),
  // « return ». Noms insensibles à la casse ; query./variable./temp./context. = q./v./t./c. ; requête inconnue = 0.
  // Expression invalide (syntaxe, fonction inconnue, nombre d'arguments) ou résultat non fini : valeur neutre du canal
  // (0, ou 1 pour l'échelle), comme le mod (guide 6.3).
  // nom -> [nombre d'arguments, fonction]. math.random et math.random_integer : le milieu, pour une image stable.
  const FONCTIONS = {
    sin: [1, d => Math.sin(d * Math.PI / 180)], cos: [1, d => Math.cos(d * Math.PI / 180)], abs: [1, Math.abs], sqrt: [1, Math.sqrt],
    floor: [1, Math.floor], ceil: [1, Math.ceil], round: [1, v => Math.floor(v + 0.5)], trunc: [1, Math.trunc], exp: [1, Math.exp],
    atan: [1, v => Math.atan(v) * 180 / Math.PI], min: [2, (a, b) => Math.min(a, b)], max: [2, (a, b) => Math.max(a, b)],
    mod: [2, (v, d) => v % d], pow: [2, Math.pow], atan2: [2, (y, x) => Math.atan2(y, x) * 180 / Math.PI],
    random: [2, (a, b) => (a + b) / 2], random_integer: [2, (a, b) => Math.floor((a + b) / 2)],
    clamp: [3, (v, a, b) => Math.max(a, Math.min(b, v))], lerp: [3, (a, b, k) => a + (b - a) * k] };
  const ESPACES = { q: "q", query: "q", v: "v", variable: "v", t: "t", temp: "t", c: "c", context: "c" };
  const NIVEAUX = [["||"], ["&&"], ["==", "!="], ["<", "<=", ">", ">="], ["+", "-"], ["*", "/"]];
  const JETON = /\s*(?:(\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?)|([A-Za-z_][A-Za-z0-9_.]*)|(&&|\|\||==|!=|<=|>=|[-+*/!?:<>(),;=]))/y;
  const NOMBRE = /^\s*[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?\s*$/;

  /** Texte -> programme (même forme que molang_analyser() du renderer) ; lève une erreur si invalide. */
  function analyser(src) {
    const s = String(src), jetons = [];
    let i = 0;
    for (;;) {
      JETON.lastIndex = i;
      const m = JETON.exec(s);
      if (!m) { if (s.slice(i).trim()) throw new Error("caractère inattendu : " + s.slice(i, i + 8)); break; }
      if (m[1] !== undefined) jetons.push(["n", parseFloat(m[1])]);
      else if (m[2] !== undefined) jetons.push(["id", m[2].toLowerCase()]);
      else jetons.push(["op", m[3]]);
      i = JETON.lastIndex;
    }
    jetons.push(["fin", null]);
    let pos = 0;
    const est = o => jetons[pos][0] === "op" && jetons[pos][1] === o;
    const prendre = o => { if (!est(o)) throw new Error("« " + o + " » attendu"); pos++; };
    function ternaire() {
      const c = binaire(0);
      if (!est("?")) return c;
      pos++;
      const a = ternaire(); let b = null;
      if (est(":")) { pos++; b = ternaire(); }
      return ["?", c, a, b];
    }
    function binaire(niv) {
      if (niv === NIVEAUX.length) return unaire();
      let a = binaire(niv + 1);
      while (jetons[pos][0] === "op" && NIVEAUX[niv].includes(jetons[pos][1])) { const o = jetons[pos][1]; pos++; a = ["op", o, a, binaire(niv + 1)]; }
      return a;
    }
    function unaire() {
      if (est("-") || est("!") || est("+")) { const o = jetons[pos][1]; pos++; const a = unaire(); return o === "+" ? a : [o, a]; }
      return primaire();
    }
    function primaire() {
      const [genre, x] = jetons[pos];
      if (genre === "n") { pos++; return ["n", x]; }
      if (est("(")) { pos++; const a = ternaire(); prendre(")"); return a; }
      if (genre !== "id") throw new Error("valeur attendue");
      pos++;
      if (x === "true" || x === "false") return ["n", x === "true" ? 1 : 0];
      const k = x.indexOf("."), esp = k < 0 ? x : x.slice(0, k), nom = k < 0 ? "" : x.slice(k + 1);
      if (esp === "math") {
        if (nom === "pi") return ["n", Math.PI];
        if (!Object.prototype.hasOwnProperty.call(FONCTIONS, nom)) throw new Error("fonction inconnue : " + x);
        prendre("(");
        const args = [];
        if (!est(")")) { args.push(ternaire()); while (est(",")) { pos++; args.push(ternaire()); } }
        prendre(")");
        if (args.length !== FONCTIONS[nom][0]) throw new Error(x + " : " + args.length + " argument(s)");
        return ["f", nom, args];
      }
      if (Object.prototype.hasOwnProperty.call(ESPACES, esp) && nom && !nom.includes(".")) { const e = ESPACES[esp]; return e === "c" ? ["n", 0] : [e, nom]; }
      throw new Error("nom inconnu : " + x);
    }
    const prog = [];
    while (jetons[pos][0] !== "fin") {
      if (est(";")) { pos++; continue; }
      const [genre, x] = jetons[pos], suiv = jetons[pos + 1];
      if (genre === "id" && x === "return") { pos++; prog.push(["ret", ternaire()]); }
      else if (genre === "id" && suiv[0] === "op" && suiv[1] === "=") {
        const k = x.indexOf("."), e = k < 0 ? undefined : ESPACES[x.slice(0, k)], nom = k < 0 ? "" : x.slice(k + 1);
        if ((e !== "v" && e !== "t") || !nom || nom.includes(".")) throw new Error("affectation impossible : " + x);
        pos += 2; prog.push(["set", e, nom, ternaire()]);
      } else prog.push(["expr", ternaire()]);
      if (jetons[pos][0] !== "fin") prendre(";");
    }
    if (!prog.length) throw new Error("expression vide");
    return prog;
  }
  const lire = (o, k) => (Object.prototype.hasOwnProperty.call(o, k) ? o[k] : 0);
  function evaluer(n, q, v, tmp) {
    switch (n[0]) {
      case "n": return n[1];
      case "q": { const x = q[n[1]]; return typeof x === "number" ? x : typeof x === "boolean" ? Number(x) : 0; }
      case "v": return lire(v, n[1]);
      case "t": return lire(tmp, n[1]);
      case "f": return FONCTIONS[n[1]][1](...n[2].map(a => evaluer(a, q, v, tmp)));
      case "-": return -evaluer(n[1], q, v, tmp);
      case "!": return evaluer(n[1], q, v, tmp) === 0 ? 1 : 0;
      case "?": return evaluer(n[1], q, v, tmp) !== 0 ? evaluer(n[2], q, v, tmp) : n[3] !== null ? evaluer(n[3], q, v, tmp) : 0;
    }
    const o = n[1], a = evaluer(n[2], q, v, tmp);
    if (o === "&&") return a !== 0 && evaluer(n[3], q, v, tmp) !== 0 ? 1 : 0;
    if (o === "||") return a !== 0 || evaluer(n[3], q, v, tmp) !== 0 ? 1 : 0;
    const b = evaluer(n[3], q, v, tmp);
    switch (o) {
      case "+": return a + b; case "-": return a - b; case "*": return a * b; case "/": return a / b;
      case "<": return a < b ? 1 : 0; case "<=": return a <= b ? 1 : 0; case ">": return a > b ? 1 : 0; case ">=": return a >= b ? 1 : 0;
      case "==": return a === b ? 1 : 0; default: return a !== b ? 1 : 0;
    }
  }
  const litV = n => Array.isArray(n) && (n[0] === "v" || n.some(x => Array.isArray(x) && litV(x)));
  /** Une image : valeur de la dernière instruction, ou du premier « return ». */
  function uneImage(prog, q, v) {
    const tmp = {}; let val = 0;
    for (const ins of prog) {
      if (ins[0] === "set") { val = evaluer(ins[3], q, v, tmp); (ins[1] === "v" ? v : tmp)[ins[2]] = val; }
      else { val = evaluer(ins[1], q, v, tmp); if (ins[0] === "ret") break; }
    }
    return val;
  }
  const cache = new Map();
  /** Valeur d'une clé. Variables mémorisées v.… : état stable sur 80 images de 0,05 s au même instant, comme render_bbmodel.py. */
  function molang(expr, q, neutre = 0) {
    if (typeof expr === "number") return expr;
    const s = String(expr);
    if (NOMBRE.test(s)) return parseFloat(s);
    if (!cache.has(s)) {
      let p = null;
      try { const prog = analyser(s); p = { prog, memo: prog.length > 1 || prog.some(i => (i[0] === "set" && i[1] === "v") || litV(i[i.length - 1])) }; } catch (err) { p = null; }
      cache.set(s, p);
    }
    const p = cache.get(s);
    if (!p) return neutre;
    const v = Object.create(null);
    let val = 0;
    try { for (let i = 0; i < (p.memo ? 80 : 1); i++) val = uneImage(p.prog, q, v); } catch (err) { return neutre; }
    return Number.isFinite(val) ? val : neutre;
  }
  function requetes(t, extra) {
    const base = Object.assign({ anim_time: t, life_time: t, delta_time: 0.05 }, extra || {});
    return new Proxy(base, { get: (o, k) => (k in o ? o[k] : 0) });
  }

  // ------------------------------------------------------------------ keyframes (linéaires, bornées, comme sample())
  function echantillon(kfs, canal, t, defaut, q) {
    const l = kfs.filter(k => k.channel === canal).sort((a, b) => a.time - b.time);
    if (!l.length) return defaut;
    const neutre = canal === "scale" ? 1 : 0;
    const val = k => ["x", "y", "z"].map(a => { const x = k.data_points[0][a]; return x === undefined || x === null ? neutre : molang(x, q, neutre); });
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
    if (/^(overlay_|event_|pet_)/.test(mot)) return "idle";   // couches, événements (guide 6.4) et états du familier vivant (6.6) : jamais un état du joueur, comme render_bbmodel.py
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

  // ------------------------------------------------------------------ familier vivant (guide 6.6), comme render_bbmodel.py
  // « vivant » : posé au sol à côté du joueur immobile, q.is_pet = 1 et requêtes de son état ; « menu » : porté,
  // q.is_pet = 0 et q.is_in_menu = 1 (le menu Apparence le montre porté) ; sinon porté à l'origine (vérificateur).
  const FAMILIER_MODES = ["sol", "vol", "nage", "perche"];
  const ETATS_PET = [["idle", ["idle", "repos", "immobile"]], ["walk", ["walk", "marche"]], ["run", ["run", "sprint", "cours", "course"]],
    ["sit", ["sit", "assis", "perch"]], ["sleep", ["sleep", "dort", "dodo"]], ["swim", ["swim", "nage"]], ["fly", ["fly", "vol", "flap"]],
    ["fall", ["fall", "chute"]], ["jump", ["jump", "saut"]], ["land", ["land", "atterri"]]];
  const PLACE_MAX = 1.5;   // blocs : distance d'aperçu (en jeu, il s'arrête à `distance` blocs)
  function familierDe(m) {
    const b = ((m.unhandled_root_fields || {}).phynaria || {}).familier;
    return b && typeof b === "object" && FAMILIER_MODES.includes(b.mode) ? b : null;
  }
  function etatPet(nom) {
    let mot = String(nom || "").split(".").pop().toLowerCase();
    if (mot.startsWith("pet_")) mot = mot.slice(4);
    const e = ETATS_PET.find(([, mots]) => mots.includes(mot));
    return e ? e[0] : "idle";
  }
  const nombre = (v, d) => { const x = parseFloat(v); return Number.isFinite(x) ? x : d; };
  function placeFamilier(b, etat) {
    const h = nombre(b.hauteur, 1.8) * 16;
    if (b.mode === "perche" && ["idle", "sit", "sleep"].includes(etat)) return [-6, 1.42 * 16, 0];
    if ((b.mode === "vol" || b.mode === "perche") && etat !== "swim") return [-16, h, 2];
    return [-Math.min(nombre(b.distance, 3), PLACE_MAX) * 16, 0, -4];
  }
  function requetesFamilier(b, etat) {
    const v = nombre(b.vitesse, 1), d = nombre(b.distance, 3);
    const q = { is_pet: 1, is_on_ground: 1, owner_distance: d, owner_health: 20, owner_max_health: 20,
      is_perched: b.mode === "perche" && ["idle", "sit", "sleep"].includes(etat) ? 1 : 0 };
    return Object.assign(q, ({ walk: { ground_speed: 4.3 * v, owner_distance: d + 1 }, run: { ground_speed: 6.5 * v, owner_distance: d + 5 },
      sit: { is_sitting: 1 }, sleep: { is_sleeping: 1 }, swim: { ground_speed: 2.5 * v, is_swimming: 1, is_in_water: 1, is_on_ground: 0 },
      fly: { ground_speed: 4.3 * v, is_flying: 1, is_on_ground: 0 }, fall: { vertical_speed: -10, is_on_ground: 0 },
      jump: { ground_speed: 2, vertical_speed: 6, is_on_ground: 0 }, land: { land_speed: 6 } })[etat] || {});
  }
  // Skin d'objet (guide 14) : groupes d'étape à la racine ; seule l'étape montrée (ou celle d'avant) est dessinée,
  // comme tools/apercu_objet.py (repli, modele_etape).
  const ETAPES = { epee: ["repos"], pioche: ["repos"], hache: ["repos"], pelle: ["repos"], houe: ["repos"], lance: ["repos", "leve", "lance"],
    arc: ["repos", "bande_1", "bande_2", "bande_3"], arbalete: ["repos", "bande_1", "bande_2", "bande_3", "chargee", "chargee_fusee"],
    trident: ["repos", "leve", "lance"], bouclier: ["repos", "bloque"], masse: ["repos"], canne: ["repos", "lancee"] };
  const ETAPES_CONNUES = new Set(Object.values(ETAPES).flat());
  /** Nom de groupe comme le lit le mod (objet.normal) : majuscules, accents, espaces et tirets ignorés. */
  const normal = n => String(n || "").normalize("NFKD").replace(/[^\x00-\x7f]/g, "").toLowerCase().replace(/[\s-]+/g, "_").replace(/^_+|_+$/g, "");
  function repliEtape(P, etape) {
    const liste = ETAPES[P.objetType] || [];
    for (let k = liste.indexOf(etape); k >= 0; k--) if (P.etapes.includes(liste[k])) return liste[k];
    return null;
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

  // ------------------------------------------------------------------ effet de téléportation (guide 15), comme render_bbmodel.py
  // Posé au sol, pas porté. charge (loop), depart et arrivee (once), noms sans accent ni majuscule ; le groupe vide « joueur »
  // donne la position et l'échelle du joueur (rotation ignorée) pendant charge, depart et arrivee (charge : guide du 2026-11-06 soir), sinon le joueur est debout à l'origine.
  const motAnim = nom => String(nom || "").split(".").pop().toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  function cheminJoueur(m) {
    function chercher(n, chemin) {
      if (typeof n !== "object" || !n) return null;
      const c2 = chemin.concat([n]);
      if (motAnim(n.name).replace(/ /g, "") === "joueur") return c2;
      for (const c of n.children || []) { const r = chercher(c, c2); if (r) return r; }
      return null;
    }
    for (const n of m.outliner || []) { const r = chercher(n, []); if (r) return r; }
    return null;
  }
  function effetDe(m) {
    return (m.animations || []).some(a => ["depart", "arrivee"].includes(motAnim(a.name))) || cheminJoueur(m) !== null;
  }

  /** Prépare un modèle : faces du cosmétique (rattachées à leur élément) et du mannequin. */
  function preparer(m) {
    const tw = m.resolution.width, th = m.resolution.height;
    const parId = new Map(m.elements.map(e => [e.uuid, e]));
    const faces = [];          // {el, coins locaux, uv | couleur}
    const elements = [];       // {M élément, chaîne de groupes, partie}
    function parcourir(n, chaine, partie, mode = 0, bill = null) {
      if (typeof n === "string") {
        const e = parId.get(n); if (!e) return;
        const o = e.origin || [0, 0, 0], r = e.rotation || [0, 0, 0];
        const racineEtape = chaine.length ? normal(chaine[0].name) : "";
        const idx = elements.push({ M: mul(T(...o), mul(R(...r), T(-o[0], -o[1], -o[2]))), chaine, partie, etape: ETAPES_CONNUES.has(racineEtape) ? racineEtape : null }) - 1;
        const inf = e.inflate || 0, a = e.from.map(v => v - inf), b = e.to.map(v => v + inf);
        for (const [nom, fd] of Object.entries(e.faces || {})) {
          if (fd.texture === null || fd.texture === undefined) continue;
          const [u1, v1, u2, v2] = fd.uv;
          if (u1 === u2 || v1 === v2) continue;
          faces.push({ el: idx, coins: COINS[nom](a, b), uv: [u1 / tw, v1 / th, u2 / tw, v1 / th, u2 / tw, v2 / th, u1 / tw, v2 / th], mode, bill });
        }
      } else {
        const suite = chaine.concat([n]);
        // fonctions anticipées (.claude/rules/conventions-anticipees.md) : trans_ = translucide (1), add_ = additif (2), comme le renderer
        const nomG = String(n.name || ""), m2 = nomG.startsWith("add_") ? 2 : nomG.startsWith("trans_") ? 1 : mode;
        // face caméra (guide 4 bis) : le groupe le plus proche, ses ancêtres, et le genre (sphérique ou debout)
        const b2 = /^camy?_/.test(nomG) ? { noeud: n, chaine, debout: nomG.startsWith("camy_") } : bill;
        for (const c of n.children || []) parcourir(c, suite, partie, m2, b2);
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
    const overlays = [...anims.keys()].filter(n => n.split(".").pop().startsWith("overlay_"));
    const objetType = ((((m.unhandled_root_fields || {}).phynaria || {}).objet) || {}).type;
    const etapes = ETAPES[objetType] ? m.outliner.filter(n => typeof n === "object").map(n => normal(n.name)).filter(n => ETAPES[objetType].includes(n)) : [];
    return { m, faces, elements, mannequin, anims, particules, emetteurs, overlays, calque: calque ? calque.source : null, main: matriceMain(m),
      familier: familierDe(m), objetType: ETAPES[objetType] ? objetType : null, etapes, effet: effetDe(m), joueur: cheminJoueur(m) };
  }

  // ------------------------------------------------------------------ skin d'objet (guide 14), comme tools/objet.py
  const CTX_DEFAUT = { thirdperson_righthand: { rotation: [0, -90, 55], translation: [0, 4, 0.5], scale: [0.85, 0.85, 0.85] }, gui: {} };
  const TYPES_OBJET = ["epee", "pioche", "hache", "pelle", "houe", "lance", "arc", "arbalete", "trident", "bouclier", "masse", "canne"];
  const Rax = (axe, deg) => {
    const a = deg * Math.PI / 180, c = Math.cos(a), s = Math.sin(a);
    return axe === "x" ? [1, 0, 0, 0, 0, c, -s, 0, 0, s, c, 0] : axe === "y" ? [c, 0, s, 0, 0, 1, 0, 0, -s, 0, c, 0] : [c, -s, 0, 0, s, c, 0, 0, 0, 0, 1, 0];
  };
  /** Objet (px du bloc) -> repère du joueur, tenu en main droite à la 3e personne, bras au repos (matrice_main() de objet.py) ;
      null si le modèle n'est pas un skin d'objet. Display : phynaria.objet.affichage, sinon display racine, sinon item/handheld. */
  function matriceMain(m) {
    const o = ((m.unhandled_root_fields || {}).phynaria || {}).objet;
    if (!o || typeof o !== "object" || !TYPES_OBJET.includes(o.type)) return null;
    const lu = (o.affichage && typeof o.affichage === "object") ? o.affichage : (m.display || {});
    const d = lu.thirdperson_righthand || CTX_DEFAUT.thirdperson_righthand;
    const borne = (v, l) => Math.max(-l, Math.min(l, Number(v)));
    const r = (d.rotation || [0, 0, 0]).map(Number), t = (d.translation || [0, 0, 0]).map(v => borne(v, 80)), s = (d.scale || [1, 1, 1]).map(v => borne(v, 4));
    const disp = [T(t[0] / 16, t[1] / 16, t[2] / 16), Rax("x", r[0]), Rax("y", r[1]), Rax("z", r[2]), S(s[0], s[1], s[2]), T(-0.5, -0.5, -0.5), S(1 / 16, 1 / 16, 1 / 16)];
    const chaine = [T(0, 24, 0), S(-1, -1, 1), T(-5, 2, 0), S(16, 16, 16), Rax("x", -90), Rax("y", 180), T(1 / 16, 0.125, -0.625)].concat(disp);
    return chaine.reduce((A, B) => mul(A, B));
  }

  /** Matrices des groupes à l'instant t (convention du mod : rotation de base + rotation animée). */
  function matricesGroupes(P, anim, t, extra, couches) {
    const anims = anim ? anim.animators || {} : {};
    const q = requetes(t, extra);
    // couches jouées par-dessus (overlay_, event_) : [{ anim, t }], chacune avec son propre temps
    const sup = (couches || []).filter(c => c.anim).map(c => ({ a: c.anim.animators || {}, t: c.t, q: requetes(c.t, extra) }));
    const cacheM = new Map(), echelles = new Map();
    const fn = function (g) {
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
      for (const c of sup) {
        const b = c.a[g.uuid]; if (!b) continue;
        const r2 = echantillon(b.keyframes, "rotation", c.t, [0, 0, 0], c.q), s2 = echantillon(b.keyframes, "scale", c.t, [1, 1, 1], c.q), p2 = echantillon(b.keyframes, "position", c.t, [0, 0, 0], c.q);
        rot = [rot[0] + r2[0], rot[1] + r2[1], rot[2] + r2[2]]; sc = [sc[0] * s2[0], sc[1] * s2[1], sc[2] * s2[2]]; pos = [pos[0] + p2[0], pos[1] + p2[1], pos[2] + p2[2]];
      }
      const M = mul(T(o[0] + pos[0], o[1] + pos[1], o[2] + pos[2]), mul(R(...rot), mul(S(...sc), T(-o[0], -o[1], -o[2]))));
      cacheM.set(g, M); echelles.set(g, sc); return M;
    };
    fn.echelle = g => { fn(g); return echelles.get(g); };   // échelle animée du groupe (groupe joueur d'un effet)
    return fn;
  }

  /** Temps local de l'animation : en boucle pour loop, borné sinon (comme load_model). */
  function tempsLocal(anim, t) {
    if (!anim) return 0;
    const L = Number(anim.length) || 0;
    return anim.loop === "loop" && L > 0 ? t % L : t;
  }

  /** Positions monde des faces du cosmétique (et du mannequin si demandé) : tableau de quads [[x,y,z]×4]. */
  function image(P, nomAnim, t, options) {
    const opt = Object.assign({ poser: true, mannequin: true, extra: null, familier: null, etape: null }, options || {});
    const anim = P.anims.get(nomAnim) || null;
    const tl = tempsLocal(anim, t);
    const duree = anim ? Number(anim.length) || 1 : 1;
    // effet de téléportation (guide 15) : posé au sol, le mannequin suit le groupe joueur (poseEffet plus bas)
    const poseJ = opt.poser && !P.effet ? poseJoueur(etatDe(nomAnim), tl, duree) : null;
    // skin d'objet : avec le joueur, toutes ses parties suivent le bras droit à travers la matrice de la main (load_model)
    let pose = poseJ && P.main ? Object.fromEntries(Object.keys(poseJ).map(k => [k, mul(poseJ.right_arm, P.main)])) : poseJ;
    // familier vivant (guide 6.6, load_model avec FAMILIER) : posé à côté du joueur, requêtes de son état (celles de la page passent après)
    const vivant = !!(P.familier && opt.familier === "vivant");
    if (vivant) {
      const e = etatPet(nomAnim);
      opt.extra = Object.assign(requetesFamilier(P.familier, e), opt.extra || {});
      if (pose) { const Tp = T(...placeFamilier(P.familier, e)); pose = Object.fromEntries(Object.keys(pose).map(k => [k, Tp])); }
    } else if (P.familier && opt.familier === "menu") opt.extra = Object.assign({ is_pet: 0, is_in_menu: 1 }, opt.extra || {});
    const couches = (opt.couches || []).map(c => ({ anim: P.anims.get(c.nom) || null, t: tempsLocal(P.anims.get(c.nom), c.t) }));
    const groupe = matricesGroupes(P, anim, tl, opt.extra, couches);
    const Mel = P.elements.map(el => {
      let M = el.M;
      for (let i = el.chaine.length - 1; i >= 0; i--) M = mul(groupe(el.chaine[i]), M);
      return pose ? mul(pose[el.partie], M) : M;
    });
    // ctrl_alpha (« 1 + position x ») sous 10 % : le groupe et ses enfants disparaissent (guide 4 bis), comme render_bbmodel.py
    const anims_ = anim ? anim.animators || {} : {}, qa = requetes(tl, opt.extra), cacheA = new Map();
    const cacheGroupe = g => {
      if (cacheA.has(g)) return cacheA.get(g);
      const c = (g.children || []).find(x => typeof x === "object" && x.name === "ctrl_alpha" && (anims_[x.uuid] || couches.some(k => k.anim && (k.anim.animators || {})[x.uuid])));
      let x = c && anims_[c.uuid] ? echantillon(anims_[c.uuid].keyframes, "position", tl, [0, 0, 0], qa)[0] : 0;
      for (const k of couches) { const b = c && k.anim && (k.anim.animators || {})[c.uuid]; if (b) x += echantillon(b.keyframes, "position", k.t, [0, 0, 0], requetes(k.t, opt.extra))[0]; }
      const v = c ? 1 + x < 0.1 : false;
      cacheA.set(g, v); valeurA.set(g, c ? Math.max(0, Math.min(1, 1 + x)) : 1); return v;
    };
    // « Comme en jeu » : opacité de ctrl_alpha, produit des groupes de la chaîne (CosmeticLayer.cube, mod 1.4.0) ;
    // add_ et _e : couleur × alpha ; trans_ : alpha × alpha ; opaque : caché sous 0,1
    const valeurA = new Map();
    const alphaEl = el => el.chaine.reduce((a, g) => { cacheGroupe(g); return a * valeurA.get(g); }, 1);
    // skin d'objet : groupes d'étape autres que celle montrée (repli sur l'étape d'avant, guide 14) non dessinés
    const etapeVue = opt.etape && P.etapes.length ? repliEtape(P, opt.etape) : undefined;
    const masque = P.elements.map(el => (etapeVue !== undefined && el.etape !== null && el.etape !== etapeVue) || el.chaine.some(cacheGroupe));
    const cosm = P.faces.map(f => masque[f.el] ? f.coins.map(() => [0, 0, 0]) : f.coins.map(c => appliquer(Mel[f.el], c[0], c[1], c[2])));
    // Faces caméra : pivot et orientation monde du groupe sans sa rotation animée ; dessiner() les tourne vers l'œil.
    const memo = new Map();
    const bill = P.faces.map(f => {
      if (!f.bill) return null;
      if (memo.has(f.bill)) return memo.get(f.bill);
      const n = f.bill.noeud, o = n.origin || [0, 0, 0], r = n.rotation || [0, 0, 0];
      let M = ID;
      for (let i = f.bill.chaine.length - 1; i >= 0; i--) M = mul(groupe(f.bill.chaine[i]), M);
      const partie = P.elements[f.el].partie;
      const Mp = pose ? mul(pose[partie], M) : M;
      const Pw = appliquer(mul(Mp, groupe(n)), o[0], o[1], o[2]);
      const Mb = mul(Mp, mul(T(o[0], o[1], o[2]), mul(R(...r), T(-o[0], -o[1], -o[2]))));
      const P0 = appliquer(Mb, o[0], o[1], o[2]);
      const col = [[1, 0, 0], [0, 1, 0], [0, 0, 1]].map(e => { const q = appliquer(Mb, o[0] + e[0], o[1] + e[1], o[2] + e[2]); const v = [q[0] - P0[0], q[1] - P0[1], q[2] - P0[2]]; const l = Math.hypot(...v) || 1; return v.map(x => x / l); });
      const b = { debout: f.bill.debout, Pw, col };
      memo.set(f.bill, b); return b;
    });
    let poseM = poseJ ? f => poseJ[f.partie] : null;
    if (P.effet && P.joueur && ["charge", "depart", "arrivee"].includes(motAnim(nomAnim))) {
      // groupe joueur : pieds à l'origine du groupe passée par sa chaîne animée, échelle = produit des échelles (rotation ignorée)
      let M = ID, sc = [1, 1, 1];
      for (let i = P.joueur.length - 1; i >= 0; i--) M = mul(groupe(P.joueur[i]), M);
      for (const g of P.joueur) { const s = groupe.echelle(g); sc = [sc[0] * s[0], sc[1] * s[1], sc[2] * s[2]]; }
      // mod 1.4.0 (bytecode, 2026-11-07) : échelle lue = |x| ; sous 0,05 rien n'est dessiné ; guide du 2026-11-08 : la copie du départ suit aussi l'échelle
      if (Math.abs(sc[0]) < 0.05) sc = [0, 0, 0];
      const o =P.joueur[P.joueur.length - 1].origin || [0, 0, 0], Pw = appliquer(M, o[0], o[1], o[2]);
      const Me = [sc[0], 0, 0, Pw[0], 0, sc[1], 0, Pw[1], 0, 0, sc[2], Pw[2]];
      poseM = () => Me;
    }
    const mann = opt.mannequin ? P.mannequin.map(f => f.coins.map(c => poseM ? appliquer(poseM(f), c[0], c[1], c[2]) : c)) : [];
    const emit = (vivant ? [] : P.emetteurs || []).map(e => {   // familier vivant : particules emit_ pas encore lancées (guide 6.6)
      let M = groupe(e.noeud);
      for (let i = e.chaine.length - 1; i >= 0; i--) M = mul(groupe(e.chaine[i]), M);
      if (pose) M = mul(pose[e.partie], M);
      const o = e.noeud.origin || [0, 0, 0];
      return { nom: e.nom, pos: appliquer(M, o[0], o[1], o[2]) };
    });
    const alphaEls = opt.alpha ? P.elements.map(alphaEl) : null;
    const alpha = alphaEls ? P.faces.map(f => alphaEls[f.el]) : null;
    return { cosm, mann, emit, bill, alpha };
  }

  /** Tourne les faces cam_ / camy_ vers l'œil (même calcul que render_bbmodel.py). */
  function faceCamera(cosm, bill, oeil) {
    return cosm.map((q, i) => {
      const b = bill[i]; if (!b) return q;
      const d = [oeil[0] - b.Pw[0], oeil[1] - b.Pw[1], oeil[2] - b.Pw[2]];
      const yaw = Math.atan2(d[0], d[2]) * 180 / Math.PI;
      const pitch = b.debout ? 0 : Math.atan2(d[1], Math.hypot(d[0], d[2])) * 180 / Math.PI;
      const Rt = mul(R(0, yaw, 0), R(-pitch, 0, 0));
      return q.map(p => {
        const v = [p[0] - b.Pw[0], p[1] - b.Pw[1], p[2] - b.Pw[2]];
        const l = [b.col[0][0] * v[0] + b.col[0][1] * v[1] + b.col[0][2] * v[2], b.col[1][0] * v[0] + b.col[1][1] * v[1] + b.col[1][2] * v[2], b.col[2][0] * v[0] + b.col[2][1] * v[1] + b.col[2][2] * v[2]];
        const w = appliquer(Rt, l[0], l[1], l[2]);
        return [b.Pw[0] + w[0], b.Pw[1] + w[1], b.Pw[2] + w[2]];
      });
    });
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
      return { coins: f.coins.map(c => appliquer(M, c[0], c[1], c[2])), uv: f.uv, mode: f.mode || 0 };
    });
  }

  const Noyau = { preparer, image, quadsParticule, poseJoueur, etatDe, etatPet, partieDe, molang, R, mul, appliquer, effetDe, motAnim };

  // ------------------------------------------------------------------ rendu WebGL 2
  const VS = `#version 300 es
  in vec3 aPos; in vec2 aUv; in vec3 aCol; in float aOmbre;
  uniform mat4 uVP; out vec2 vUv; out vec3 vCol; out float vOmbre;
  void main(){ gl_Position = uVP * vec4(aPos, 1.0); vUv = aUv; vCol = aCol; vOmbre = aOmbre; }`;
  const FS = `#version 300 es
  precision mediump float; in vec2 vUv; in vec3 vCol; in float vOmbre;
  uniform sampler2D uTex; uniform sampler2D uLum; uniform float uJour; uniform float uAvecLum; uniform float uPasse;
  uniform float uJeu; uniform vec3 uMonde; out vec4 sortie;
  void main(){
    // passes : 0 opaque (cutout), 1 translucide (trans_), 2 additif (add_), 3 calque _e (« comme en jeu » seulement) ;
    // vCol.g porte le mode d'une face texturée, vCol.b son opacité ctrl_alpha (« comme en jeu »)
    if (vCol.r < 0.0) {
      if (uPasse > 2.5) { if (vCol.g > 1.5) discard; }
      else if (abs(vCol.g - uPasse) > 0.5) discard;
      vec4 c = texture(uTex, vUv);
      vec4 e = texture(uLum, vUv);
      if (uJeu > 0.5) {
        // mod 1.4.0 : texels d'alpha < 0,1 jetés (opaque, trans_) ; vOmbre = lumière de face de Minecraft, uMonde = lumière du
        // monde ; add_ et _e sans lumière, ajoutés, couleur × alpha du texel (guide du 2026-11-08 ; alpha 0 seul jeté) ;
        // _e dans une passe à part, sur tout ce qui n'est pas add_ ; mipmaps (texture en NEAREST_MIPMAP_LINEAR, 4 niveaux)
        float al = vCol.b;
        if (uPasse > 2.5) { if (uAvecLum < 0.5 || e.a < 0.004) discard; sortie = vec4(e.rgb * e.a * al, 1.0); return; }
        if (uPasse > 1.5) { if (c.a < 0.004) discard; sortie = vec4(c.rgb * c.a * al, 1.0); return; }
        if (c.a < 0.1) discard;
        if (uPasse < 0.5) { if (al < 0.1) discard; sortie = vec4(c.rgb * vOmbre * uMonde, 1.0); }
        else sortie = vec4(c.rgb * vOmbre * uMonde, c.a * al);
        return;
      }
      // Calque _e : s'ajoute à la couleur, visible dans le noir ; noir ou transparent = rien.
      vec3 lum = uAvecLum * e.rgb * step(0.5, e.a);
      if (uPasse < 0.5) { if (c.a < 0.5) discard; sortie = vec4(min(c.rgb * vOmbre * uJour + lum, 1.0), 1.0); }
      else if (uPasse < 1.5) { if (c.a < 0.1) discard; sortie = vec4(min(c.rgb * vOmbre * uJour + lum, 1.0), c.a); }
      else { if (c.a < 0.004) discard; sortie = vec4(c.rgb * c.a, 1.0); }
    }
    else {
      if (uPasse > 0.5) discard;
      // « comme en jeu » : vOmbre < 0 = particule de Minecraft lumineuse (sans lumière)
      if (uJeu > 0.5) sortie = vec4(vOmbre < 0.0 ? vCol : vCol * vOmbre * uMonde, 1.0);
      else sortie = vec4(vCol * vOmbre * uJour, 1.0);
    }
  }`;
  // Ciel et sol du mode « comme en jeu » : triangle plein écran ; le sol (y = 0, damier de blocs) écrit sa profondeur.
  const VS_FOND = `#version 300 es
  out vec2 vNdc; void main(){ vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2)) * 2.0 - 1.0; vNdc = p; gl_Position = vec4(p, 0.0, 1.0); }`;
  const FS_FOND = `#version 300 es
  precision highp float; in vec2 vNdc; out vec4 sortie;
  uniform vec3 uAvant, uDroite, uHaut, uOeil, uZen, uHor, uSol; uniform vec2 uTan; uniform mat4 uVP;
  void main(){
    vec3 d = uAvant + vNdc.x * uTan.x * uDroite + vNdc.y * uTan.y * uHaut;
    float el = d.y / length(d);
    if (d.y < -1e-5 && uOeil.y > 0.0) {
      float t = -uOeil.y / d.y; vec3 h = uOeil + t * d;
      if (length(h.xz) < 480.0) {
        float dam = mod(floor(h.x / 16.0) + floor(h.z / 16.0), 2.0) < 0.5 ? 1.0 : 0.9;
        vec4 cl = uVP * vec4(h, 1.0);
        gl_FragDepth = clamp(cl.z / cl.w * 0.5 + 0.5, 0.0, 1.0);
        sortie = vec4(uSol * dam, 1.0); return;
      }
    }
    gl_FragDepth = 1.0;
    sortie = vec4(mix(uHor, uZen, clamp(el / 0.6, 0.0, 1.0)), 1.0);
  }`;
  const FS_COPIE = `#version 300 es
  precision mediump float; in vec2 vNdc; uniform sampler2D uImg; out vec4 sortie;
  void main(){ sortie = texture(uImg, vNdc * 0.5 + 0.5); }`;
  // Mesures du mod (render_bbmodel.py, CIELS_JEU) : ciel zénith, horizon, lumière du monde (luminosité « Lumineux »)
  const CIELS = {
    jour: [[120, 167, 255], [192, 216, 255], [1, 1, 1]],
    gris: [[168, 172, 180], [196, 200, 207], [1, 1, 1]],
    nuit: [[3, 4, 10], [12, 14, 26], [0.60, 0.62, 0.72]],
    shader: [[12, 12, 20], [40, 38, 46], [0.24, 0.23, 0.28]],
  };
  const SOL = [104, 102, 100], ECRAN_JEU = 1369;
  const L0 = (() => { const l = [0.2, 1, -0.7], n = Math.hypot(...l); return l.map(v => v / n); })();
  const L1 = (() => { const l = [-0.2, 1, 0.7], n = Math.hypot(...l); return l.map(v => v / n); })();
  /** Lumière d'une face de Minecraft (light.glsl) pour une normale unitaire. */
  const ombreMc = (x, y, z) => Math.min(1, (Math.max(0, x * L0[0] + y * L0[1] + z * L0[2]) + Math.max(0, x * L1[0] + y * L1[1] + z * L1[2])) * 0.6 + 0.4);
  // Particules de Minecraft (emit_mc_, approchées) : couleur, durée (s), vitesse verticale (px/s), taille (px), lumineuse
  const PARTS_MC = {
    flame: [[1, 0.62, 0.2], 1.2, 1.5, 1.6, true], soul_fire_flame: [[0.35, 0.9, 1], 1.2, 1.5, 1.6, true],
    small_flame: [[1, 0.62, 0.2], 0.8, 1, 0.9, true], end_rod: [[1, 1, 0.92], 3.2, 0.6, 1.4, true],
    electric_spark: [[0.85, 0.93, 1], 0.35, 0, 1.0, true], glow: [[0.55, 1, 0.85], 1.6, 0.4, 1.6, true],
    enchant: [[0.75, 0.75, 1], 1.5, -1, 1.2, true], portal: [[0.72, 0.32, 0.95], 2.0, -0.6, 1.4, true],
    wax_on: [[1, 0.75, 0.2], 1.5, 0, 1.4, true], wax_off: [[1, 1, 1], 1.5, 0, 1.4, true], scrape: [[0.5, 0.95, 0.85], 1.5, 0, 1.4, true],
    white_smoke: [[0.86, 0.86, 0.88], 1.6, 2.5, 2.8, false], smoke: [[0.3, 0.3, 0.32], 1.6, 2, 2.4, false],
    large_smoke: [[0.32, 0.32, 0.34], 2.2, 2.5, 4, false], campfire_cosy_smoke: [[0.6, 0.6, 0.62], 6, 1.6, 5, false],
    snowflake: [[0.97, 0.98, 1], 3, -3, 1.4, false], cherry_leaves: [[1, 0.74, 0.85], 5, -2, 1.6, false],
    cloud: [[1, 1, 1], 1.2, 0.5, 3, false], happy_villager: [[0.4, 0.95, 0.35], 1.5, 0, 1.4, false],
    heart: [[1, 0.25, 0.3], 1.6, 1.5, 2, false], note: [[0.4, 0.9, 0.4], 1, 1, 1.8, false],
  };
  function partMc(nom) {
    const id = nom.replace(/^mc_/, "");
    const d = /^dust_([0-9a-f]{6})_(\d+)$/i.exec(id);
    if (d) { const h = parseInt(d[1], 16); return [[(h >> 16 & 255) / 255, (h >> 8 & 255) / 255, (h & 255) / 255], 1.0, 0.3, 1.6 * Math.min(4, Number(d[2]) / 10), false]; }
    return PARTS_MC[id] || [[0.9, 0.9, 0.9], 1.0, 0.5, 1.4, false];
  }
  // Mouvement des particules modélisées (mod 1.4.0, CosmeticParticles$Fall) : gravité, vitesse limite (blocs/s), balancement
  const CHUTES = { legere: [1.2, 0.9, 0.6], normale: [6, 4, 0.2], lourde: [16, 20, 0], flotte: [0, 0, 0.15], monte: [-0.8, 0.8, 0.3] };
  /** « Quand » d'une sorte de particule (guide 5 ter) : lancée dans cet état ? Un effet de téléportation ignore Quand (sauf Jamais). */
  function quandOk(quand, nomAnim, effet) {
    const q = String(quand || "vol").toLowerCase();
    if (q === "jamais") return false;
    if (effet || q === "toujours") return true;
    const mot = String(nomAnim || "").split(".").pop().toLowerCase(), etat = etatDe(nomAnim);
    const vol = /fly|vol|glide|elytra|plane/.test(mot);
    if (q === "vol") return vol;
    if (q === "air") return vol || /jump|saut|fall|chute/.test(mot);
    if (q === "mouvement") return vol || ["walk", "run", "swim", "glide"].includes(etat);
    if (q === "arret") return !vol && ["idle", "sneak", "sleep", "mount"].includes(etat);
    return false;   // pluie, utilisation : pas simulés
  }
  const LUMIERE = (() => { const l = [-0.4, 1.0, 0.6], n = Math.hypot(...l); return l.map(v => v / n); })();

  // ------------------------------------------------------------------ sons
  // Clés « sound » de la piste Effects (guide 6.5) : les sons embarqués (phynaria_sounds, OGG en data:) sont joués ;
  // les sons de Minecraft ou d'un pack ne sont pas disponibles ici (ignorés). Un seul contexte audio pour la page,
  // préférence partagée par toutes les vues (Visionneuse.son).
  let audio = null, sonActif = true;
  try { sonActif = localStorage.getItem("vestiaire.son") !== "0"; } catch (e) {}
  function contexteAudio() {
    const C = racine.AudioContext || racine.webkitAudioContext;
    if (!C) return null;
    if (!audio) audio = new C();
    if (audio.state === "suspended") audio.resume().catch(() => {});
    return audio;
  }
  /** Sons embarqués d'un modèle : { nom: Promise<AudioBuffer | null> }, décodés à la demande. */
  function tableSons(m) {
    const src = m.phynaria_sounds || {}, cache = {};
    return nom => {
      if (!(nom in src)) return null;
      if (!cache[nom]) {
        const ctx = contexteAudio();
        if (!ctx) return null;
        cache[nom] = fetch(src[nom]).then(r => r.arrayBuffer()).then(b => ctx.decodeAudioData(b)).catch(() => null);
      }
      return cache[nom];
    };
  }
  /** Clés de son d'une animation, triées : [{ t, noms }]. */
  function clesSon(anim) {
    const e = anim && anim.animators && anim.animators.effects;
    return ((e && e.keyframes) || []).filter(k => k.channel === "sound")
      .map(k => ({ t: Number(k.time) || 0, noms: (k.data_points || []).map(d => d.effect).filter(Boolean) })).sort((a, b) => a.t - b.t);
  }

  function creer(canvas) {
    const gl = canvas.getContext("webgl2", { antialias: true, alpha: false });
    if (!gl) return null;
    const prog = programme(gl, VS, FS);
    const loc = { pos: gl.getAttribLocation(prog, "aPos"), uv: gl.getAttribLocation(prog, "aUv"), col: gl.getAttribLocation(prog, "aCol"), ombre: gl.getAttribLocation(prog, "aOmbre"),
      vp: gl.getUniformLocation(prog, "uVP"), tex: gl.getUniformLocation(prog, "uTex"), lum: gl.getUniformLocation(prog, "uLum"),
      jour: gl.getUniformLocation(prog, "uJour"), avecLum: gl.getUniformLocation(prog, "uAvecLum"), passe: gl.getUniformLocation(prog, "uPasse"),
      jeu: gl.getUniformLocation(prog, "uJeu"), monde: gl.getUniformLocation(prog, "uMonde") };
    const progFond = programme(gl, VS_FOND, FS_FOND), progCopie = programme(gl, VS_FOND, FS_COPIE);
    const locF = Object.fromEntries(["uAvant", "uDroite", "uHaut", "uOeil", "uZen", "uHor", "uSol", "uTan", "uVP"].map(n => [n, gl.getUniformLocation(progFond, n)]));
    const tampons = { pos: gl.createBuffer(), uv: gl.createBuffer(), col: gl.createBuffer(), ombre: gl.createBuffer(), idx: gl.createBuffer(), idxT: gl.createBuffer() };
    const tex = gl.createTexture(), texLum = gl.createTexture();
    const MAX_PART = 256, CAP_STUDIO = 64, MAX_MC = 256;
    const MOUVEMENTS = { legere: [-8, 3], normale: [-16, 2.5], lourde: [-40, 1.5], flotte: [0, 0.8], monte: [6, 2] };   // vitesse verticale, dérive (px/s)
    const etat = { P: null, anim: null, t: 0, lecture: true, extra: null, theta: -35, phi: 18, dist: 70, cible: [0, 16, 0], n: 0, dernier: 0, distBase: 70, cibleBase: [0, 16, 0],
      surTemps: null, familier: null, etape: null, fond: [0.055, 0.051, 0.075], nuit: false, calqueVisible: true,
      particules: true, mouvement: "legere", parts: [], cumul: {}, capacite: 0, jeu: null, phiJeu: 0, tSon: -1e-4, sons: null };
    /** Joue les sons de l'animation nom dont la clé tombe dans ]a, b] (temps local). */
    const enCours = new Set();
    const couperSons = () => { for (const s of enCours) try { s.stop(); } catch (e) {} enCours.clear(); };
    function jouerSons(nom, a, b) {
      if (!sonActif || !etat.P || !etat.sons || b <= a) return;
      const ctx = contexteAudio();
      if (!ctx || ctx.state !== "running") return;   // audio pas encore débloqué par un clic sur la page : rien (pas de rafale plus tard)
      for (const k of clesSon(etat.P.anims.get(nom))) {
        if (k.t <= a || k.t > b) continue;
        for (const n of k.noms) {
          const p = etat.sons(n); if (!p) continue;
          p.then(buf => { if (!buf || !actif || ctx.state !== "running") return;
            const g = ctx.createGain(); g.gain.value = 0.8; g.connect(ctx.destination);
            const s = ctx.createBufferSource(); s.buffer = buf; s.connect(g); s.start();
            enCours.add(s); s.onended = () => enCours.delete(s); });
        }
      }
    }
    let posArr, ombreArr;
    // « Comme en jeu » : image rendue à la densité de l'écran du joueur (1 369 lignes), sans anticrénelage, puis réduite
    let cadreJeu = null;
    function tamponJeu(w, h) {
      if (cadreJeu && cadreJeu.w === w && cadreJeu.h === h) return cadreJeu;
      if (cadreJeu) { gl.deleteFramebuffer(cadreJeu.fb); gl.deleteTexture(cadreJeu.tex); gl.deleteRenderbuffer(cadreJeu.prof); }
      const fb = gl.createFramebuffer(), t = gl.createTexture(), prof = gl.createRenderbuffer();
      gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texStorage2D(gl.TEXTURE_2D, Math.floor(Math.log2(Math.max(w, h))) + 1, gl.RGBA8, w, h);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.bindRenderbuffer(gl.RENDERBUFFER, prof); gl.renderbufferStorage(gl.RENDERBUFFER, gl.DEPTH_COMPONENT24, w, h);
      gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
      gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.RENDERBUFFER, prof);
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      cadreJeu = { fb, tex: t, prof, w, h };
      return cadreJeu;
    }
    /** Réglages d'une sorte de particule : ceux écrits dans le fichier (guide 5 ter, §6), puis ceux de la page (reglages.json). */
    function reglage(nom) {
      const f = ((((etat.P && etat.P.m.unhandled_root_fields) || {}).phynaria || {}).particules || {})[nom] || {};
      const d = { nombre: f.nombre, vie: f.duree, mouvement: f.mouvement, auSol: f.au_sol, rendu: f.rendu, quand: f.quand, limite: f.limite };
      const p = (etat.reglages && etat.reglages[nom]) || {};
      for (const k in p) if (p[k] !== undefined) d[k] = p[k];
      return d;
    }

    function charger(modele) {
      const P = preparer(modele);
      etat.P = P; etat.sons = tableSons(modele);
      if (audio && audio.state === "running") Object.keys(modele.phynaria_sounds || {}).forEach(n => etat.sons(n));   // décodés d'avance : pas de retard au premier son
      const maxFacesPart = Math.max(0, ...[...P.particules.values()].map(p => p.faces.length));
      const fixe = P.faces.length + P.mannequin.length, nq = fixe + MAX_PART * maxFacesPart + MAX_MC;
      etat.n = nq; etat.fixe = fixe; etat.parts = []; etat.cumul = {};
      const uv = new Float32Array(nq * 8), col = new Float32Array(nq * 12), idx = new Uint32Array(nq * 6);
      P.faces.forEach((f, i) => { uv.set(f.uv, i * 8); for (let k = 0; k < 4; k++) col.set([-1, f.mode || 0, 1], i * 12 + k * 3); });
      etat.colArr = col;
      etat.speciales = P.faces.some(f => f.mode);
      P.mannequin.forEach((f, j) => { const i = P.faces.length + j; for (let k = 0; k < 4; k++) col.set(f.couleur.map(v => v / 255), i * 12 + k * 3); });
      for (let i = fixe; i < nq; i++) for (let k = 0; k < 4; k++) col.set([-1, 0, 0], i * 12 + k * 3);
      etat.uvArr = uv;
      for (let i = 0; i < nq; i++) idx.set([i * 4, i * 4 + 1, i * 4 + 2, i * 4, i * 4 + 2, i * 4 + 3], i * 6);
      posArr = new Float32Array(nq * 12); ombreArr = new Float32Array(nq * 4);
      gl.bindBuffer(gl.ARRAY_BUFFER, tampons.uv); gl.bufferData(gl.ARRAY_BUFFER, uv, gl.DYNAMIC_DRAW);
      gl.bindBuffer(gl.ARRAY_BUFFER, tampons.col); gl.bufferData(gl.ARRAY_BUFFER, col, gl.DYNAMIC_DRAW);
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
        const { cosm, mann } = image(etat.P, etat.anim, k * L / 6, { extra: etat.extra, familier: etat.familier, etape: etat.etape });
        for (const q of cosm.concat(mann)) for (const p of q) for (let i = 0; i < 3; i++) { lo[i] = Math.min(lo[i], p[i]); hi[i] = Math.max(hi[i], p[i]); }
      }
      etat.cible = etat.cibleBase = lo.map((v, i) => (v + hi[i]) / 2);
      const r = Math.max(10, Math.hypot(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]) / 2);
      etat.dist = etat.distBase = r / Math.sin(15 * Math.PI / 180) * 1.02;
    }

    function dessiner(maintenant) {
      if (!etat.P) return;
      // Coût : rien n'est recalculé quand la vue est hors de l'écran, ni quand l'image serait la même
      // (pause, caméra immobile, pas de particule ni d'événement en cours). Résolution plafonnée à 2 pixels par point.
      if (!visible) { etat.dernier = 0; etat.dernierPart = 0; return; }
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      const w = canvas.clientWidth * dpr | 0, h = canvas.clientHeight * dpr | 0;
      if (!w || !h) return;
      const fige = !etat.lecture && !etat.evt && !etat.parts.length;
      if (fige && !sale && canvas.width === w && canvas.height === h) { etat.dernier = maintenant; return; }
      sale = false;
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
      if (etat.lecture && etat.dernier) {
        const dt = (maintenant - etat.dernier) / 1000;
        etat.t += dt;
        const a = etat.P.anims.get(etat.anim);
        // attaque, blessé : rejoués en boucle pour l'aperçu ; effet de téléportation (guide 15) : départ et arrivée aussi,
        // après 1 s sur leur dernière image (comme la demande au mod pour le menu Apparence, demandes_mod_6 §2)
        if (a && a.loop !== "loop" && etat.t > Number(a.length) + (etat.P.effet ? 1.0 : 0.6)) { etat.t = 0; etat.tSon = -1e-4; }
        // sons : clés franchies depuis l'image précédente (boucle : aussi celles d'avant le retour au début)
        const L = a ? Number(a.length) || 0 : 0, tl = tempsLocal(a, etat.t);
        if (dt < 0.25) {          // vue reprise après une pause (onglet caché, hors champ) : pas de rafale de sons
          if (tl < etat.tSon) { jouerSons(etat.anim, etat.tSon, L); etat.tSon = -1e-4; }
          jouerSons(etat.anim, etat.tSon, tl);
        }
        etat.tSon = tl;
        if (etat.surTemps) etat.surTemps(etat.t);
      }
      etat.dernier = maintenant;
      const couches = etat.P.overlays.map(nom => ({ nom, t: etat.t }));
      if (etat.evt) {
        const a = etat.P.anims.get(etat.evt.nom), te = etat.t - etat.evt.t0;
        if (a && te >= 0 && te <= Number(a.length)) {
          couches.push({ nom: etat.evt.nom, t: te });
          if (etat.lecture) { jouerSons(etat.evt.nom, etat.evt.tSon, te); etat.evt.tSon = te; }
        } else if (etat.evt.fin) { etat.evt.fin(); etat.evt = null; }
      }
      const jeu = etat.jeu;
      const im = image(etat.P, etat.anim, etat.t, { extra: etat.extra, couches, familier: etat.familier, etape: etat.etape, alpha: !!jeu });
      const { mann, emit } = im;
      const vue = vueDe(etat);
      const cosm = faceCamera(im.cosm, im.bill, vue.oeil);
      const dt = etat.lecture && etat.dernierPart ? Math.min(0.1, (maintenant - etat.dernierPart) / 1000) : 0;
      etat.dernierPart = maintenant;
      simulerParticules(emit, dt);
      const quads = cosm.concat(mann);
      const quadsPart = [], sprites = [];
      const modeRendu = { lumineux: 2, translucide: 1 };
      for (const p of etat.parts) {
        const echelle = p.age > p.vie - 0.5 ? Math.max(0, (p.vie - p.age) / 0.5) : 1;   // rétrécit puis disparaît
        if (p.mc) { sprites.push(p); continue; }
        const mr = jeu ? modeRendu[String(reglage(p.nom).rendu || "").toLowerCase()] : undefined;
        for (const q of quadsParticule(etat.P, p.nom, p.pos, p.pose === "rest" ? p.age - p.posee : p.age, p.pose, echelle, p.balance)) {
          if (quads.length + quadsPart.length >= etat.n - MAX_MC) break;
          if (mr !== undefined) q.mode = mr;
          quadsPart.push(q);
        }
      }
      quadsPart.forEach((q, j) => etat.uvArr.set(q.uv, (etat.fixe + j) * 8));
      if (quadsPart.length) { gl.bindBuffer(gl.ARRAY_BUFFER, tampons.uv); gl.bufferSubData(gl.ARRAY_BUFFER, etat.fixe * 32, etat.uvArr.subarray(etat.fixe * 8, (etat.fixe + quadsPart.length) * 8)); }
      for (const q of quadsPart) quads.push(q.coins);
      // couleurs : mode et opacité ctrl_alpha des faces texturées, mode des particules, couleur des particules de Minecraft
      const col = etat.colArr, nf = etat.P.faces.length;
      for (let i = 0; i < nf; i++) { const a = jeu ? im.alpha[i] : 1; for (let k = 0; k < 4; k++) col[i * 12 + k * 3 + 2] = a; }
      quadsPart.forEach((q, j) => { const i = etat.fixe + j; for (let k = 0; k < 4; k++) col.set([-1, q.mode, 1], i * 12 + k * 3); });
      // particules de Minecraft (emit_mc_, « comme en jeu ») : carrés face à la caméra, couleur et taille approchées
      const fv = norm(sub(vue.cible, vue.oeil)), dv = norm(croix(fv, [0, 1, 0])), hv = croix(dv, fv);
      const lumSprite = [];
      for (const p of sprites.slice(0, MAX_MC)) {
        if (quads.length >= etat.n) break;
        const s = p.taille * (1 - 0.5 * p.age / p.vie) / 2, i = quads.length;
        quads.push([[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([a, b]) => [0, 1, 2].map(k => p.pos[k] + (a * dv[k] + b * hv[k]) * s)));
        for (let k = 0; k < 4; k++) col.set(p.col, i * 12 + k * 3);
        lumSprite[i] = p.lumi;
      }
      gl.bindBuffer(gl.ARRAY_BUFFER, tampons.col); gl.bufferSubData(gl.ARRAY_BUFFER, 0, col.subarray(0, quads.length * 12));
      const oeil = vue.oeil, transl = [];
      for (let i = 0; i < quads.length; i++) {
        const q = quads[i];
        for (let k = 0; k < 4; k++) posArr.set(q[k], i * 12 + k * 3);
        const ux = q[1][0] - q[0][0], uy = q[1][1] - q[0][1], uz = q[1][2] - q[0][2], vx = q[3][0] - q[0][0], vy = q[3][1] - q[0][1], vz = q[3][2] - q[0][2];
        const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx; const ln = Math.hypot(nx, ny, nz) || 1;
        let o;
        if (lumSprite[i] !== undefined) o = lumSprite[i] ? -1 : 1;
        else if (jeu) {
          // lumière de Minecraft sur la face tournée vers l'œil (recto ou verso : le mod ne retire aucune face)
          const cx = (q[0][0] + q[2][0]) / 2, cy = (q[0][1] + q[2][1]) / 2, cz = (q[0][2] + q[2][2]) / 2;
          const sgn = (nx * (oeil[0] - cx) + ny * (oeil[1] - cy) + nz * (oeil[2] - cz)) < 0 ? -1 : 1;
          o = ombreMc(sgn * nx / ln, sgn * ny / ln, sgn * nz / ln);
        }
        else o = 0.55 + 0.45 * Math.abs((nx * LUMIERE[0] + ny * LUMIERE[1] + nz * LUMIERE[2]) / ln);   // éclairage plat, comme le renderer
        ombreArr.fill(o, i * 4, i * 4 + 4);
        if (col[i * 12] < 0 && Math.abs(col[i * 12 + 1] - 1) < 0.5) {
          const cx = (q[0][0] + q[2][0]) / 2 - oeil[0], cy = (q[0][1] + q[2][1]) / 2 - oeil[1], cz = (q[0][2] + q[2][2]) / 2 - oeil[2];
          transl.push([i, cx * cx + cy * cy + cz * cz]);
        }
      }
      gl.bindBuffer(gl.ARRAY_BUFFER, tampons.pos); gl.bufferSubData(gl.ARRAY_BUFFER, 0, posArr);
      gl.bindBuffer(gl.ARRAY_BUFFER, tampons.ombre); gl.bufferSubData(gl.ARRAY_BUFFER, 0, ombreArr);
      // translucides triés du plus loin au plus proche (le jeu les trie aussi : entityTranslucent)
      transl.sort((a, b) => b[1] - a[1]);
      const idxT = new Uint32Array(transl.length * 6);
      transl.forEach(([i], j) => idxT.set([i * 4, i * 4 + 1, i * 4 + 2, i * 4, i * 4 + 2, i * 4 + 3], j * 6));
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, tampons.idxT); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idxT, gl.DYNAMIC_DRAW);
      const ratio = w / h, VP = vueProjection(vue, ratio);
      let cj = null;
      if (jeu) {
        // image à la densité de l'écran du jeu (1 369 lignes pour 70°), sans anticrénelage ; mipmaps sur les textures du modèle
        // (guide du 2026-11-08 : 4 niveaux, comme les blocs)
        const hj = ECRAN_JEU, wj = Math.max(1, Math.round(hj * ratio));
        cj = tamponJeu(wj, hj);
        gl.bindFramebuffer(gl.FRAMEBUFFER, cj.fb); gl.viewport(0, 0, wj, hj);
        const [zen, hor, monde] = CIELS[jeu.ciel] || CIELS.gris;
        gl.disable(gl.BLEND); gl.enable(gl.DEPTH_TEST); gl.depthFunc(gl.ALWAYS); gl.depthMask(true);
        gl.useProgram(progFond);
        const th = Math.tan(vue.fov * Math.PI / 360);
        gl.uniform3fv(locF.uAvant, fv); gl.uniform3fv(locF.uDroite, dv); gl.uniform3fv(locF.uHaut, hv); gl.uniform3fv(locF.uOeil, oeil);
        gl.uniform3fv(locF.uZen, zen.map(v => v / 255)); gl.uniform3fv(locF.uHor, hor.map(v => v / 255)); gl.uniform3fv(locF.uSol, SOL.map((v, k) => v / 255 * monde[k]));
        gl.uniform2f(locF.uTan, th * ratio, th); gl.uniformMatrix4fv(locF.uVP, false, VP);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
        gl.depthFunc(gl.LEQUAL);
      } else {
        gl.viewport(0, 0, w, h);
        gl.clearColor(...(etat.nuit ? [0.012, 0.012, 0.024] : etat.fond), 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        gl.enable(gl.DEPTH_TEST); gl.depthFunc(gl.LESS);
      }
      gl.disable(gl.CULL_FACE);
      gl.useProgram(prog);
      gl.uniformMatrix4fv(loc.vp, false, VP);
      attribut(gl, tampons.pos, loc.pos, 3); attribut(gl, tampons.uv, loc.uv, 2); attribut(gl, tampons.col, loc.col, 3); attribut(gl, tampons.ombre, loc.ombre, 1);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex); gl.uniform1i(loc.tex, 0);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, jeu ? gl.NEAREST_MIPMAP_LINEAR : gl.NEAREST);
      gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, texLum); gl.uniform1i(loc.lum, 1);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, jeu ? gl.NEAREST_MIPMAP_LINEAR : gl.NEAREST);
      gl.uniform1f(loc.jour, etat.nuit ? 0.16 : 1.0); gl.uniform1f(loc.avecLum, etat.aCalque && etat.calqueVisible ? 1 : 0);
      gl.uniform1f(loc.jeu, jeu ? 1 : 0); gl.uniform3fv(loc.monde, jeu ? (CIELS[jeu.ciel] || CIELS.gris)[2] : [1, 1, 1]);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, tampons.idx);
      gl.uniform1f(loc.passe, 0); gl.drawElements(gl.TRIANGLES, quads.length * 6, gl.UNSIGNED_INT, 0);
      // mod 1.4.0 : opaque, puis trans_ (trié, écrit la profondeur dès alpha 0,1 : un add_ derrière est caché), puis add_ (sans
      // écrire la profondeur), puis le calque _e en additif (« comme en jeu » ; en studio il est ajouté dans chaque passe)
      gl.enable(gl.BLEND);
      if (transl.length) {
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.uniform1f(loc.passe, 1);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, tampons.idxT); gl.drawElements(gl.TRIANGLES, transl.length * 6, gl.UNSIGNED_INT, 0);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, tampons.idx);
      }
      gl.depthMask(false); gl.blendFunc(gl.ONE, gl.ONE);
      if (etat.speciales || quadsPart.length) { gl.uniform1f(loc.passe, 2); gl.drawElements(gl.TRIANGLES, quads.length * 6, gl.UNSIGNED_INT, 0); }
      if (jeu && etat.aCalque) { gl.uniform1f(loc.passe, 3); gl.drawElements(gl.TRIANGLES, quads.length * 6, gl.UNSIGNED_INT, 0); }
      gl.disable(gl.BLEND); gl.depthMask(true); gl.depthFunc(gl.LESS);
      if (cj) {
        // réduction à la taille de la vue, comme une capture d'écran du jeu affichée plus petite
        gl.bindTexture(gl.TEXTURE_2D, cj.tex); gl.generateMipmap(gl.TEXTURE_2D);
        gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, w, h);
        gl.disable(gl.DEPTH_TEST); gl.useProgram(progCopie);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, cj.tex); gl.uniform1i(gl.getUniformLocation(progCopie, "uImg"), 0);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
        gl.enable(gl.DEPTH_TEST);
      }
    }

    /** Particules : réglages du fichier ou de la page, sinon ceux du guide (2 par seconde et par sorte, 6 s, Légère, se posent
        au sol y = 0). « Comme en jeu » : « Quand » respecté (par défaut En vol), limite par joueur, mouvement du mod 1.4.0
        (gravité, vitesse limite, balancement), particules de Minecraft emit_mc_ approchées. */
    function simulerParticules(emit, dt) {
      if (!etat.P || !dt) return;
      const jeu = etat.jeu;
      const mvt = nom => reglage(nom).mouvement || etat.mouvement;
      if (etat.particules) {
        const parSorte = {};
        for (const e of emit) {
          const mc = e.nom.startsWith("mc_");
          if (mc ? !jeu : !etat.P.particules.has(e.nom)) continue;
          if (jeu && !quandOk(reglage(e.nom).quand, etat.anim, etat.P.effet)) continue;
          (parSorte[e.nom] = parSorte[e.nom] || []).push(e.pos);
        }
        const limites = Object.keys(parSorte).map(n => Number(reglage(n).limite) || 64);
        const cap = jeu ? Math.min(MAX_PART, Math.max(64, ...limites)) : CAP_STUDIO;
        for (const nom in parSorte) {
          etat.cumul[nom] = (etat.cumul[nom] || 0) + dt * (Number(reglage(nom).nombre) || 2);
          while (etat.cumul[nom] >= 1 && etat.parts.length < cap) {
            etat.cumul[nom] -= 1;
            const pts = parSorte[nom], d = pts[Math.floor(Math.random() * pts.length)];
            const a = Math.random() * Math.PI * 2;
            if (nom.startsWith("mc_")) {
              const [c, vie, vy, taille, lumi] = partMc(nom);
              etat.parts.push({ nom, mc: true, col: c, lumi, taille, pos: d.slice(), v: [Math.cos(a) * 1.2, vy, Math.sin(a) * 1.2], age: 0, vie: vie * (0.7 + 0.6 * Math.random()) });
              continue;
            }
            const m = mvt(nom);
            if (jeu) {
              // mod 1.4.0 : petite poussée au hasard, puis gravité jusqu'à la vitesse limite, balancement de côté
              const [g, lim, bal] = CHUTES[m] || CHUTES.legere;
              etat.parts.push({ nom, mvt: m, g, lim, bal, pos: d.slice(), v: [Math.cos(a) * 4, 0, Math.sin(a) * 4], age: 0, vie: Number(reglage(nom).vie) || 6, pose: "fall", posee: 0, balance: Math.random() });
              continue;
            }
            const [vy, derive] = MOUVEMENTS[m] || MOUVEMENTS.legere;
            etat.parts.push({ nom, mvt: m, pos: d.slice(), v: [Math.cos(a) * derive, vy, Math.sin(a) * derive], age: 0, vie: reglage(nom).vie || 6, pose: "fall", posee: 0, balance: Math.random() });
          }
          if (etat.cumul[nom] > 1) etat.cumul[nom] = 1;
        }
      }
      for (const p of etat.parts) {
        p.age += dt;
        if (p.mc) { for (let i = 0; i < 3; i++) p.pos[i] += p.v[i] * dt; p.v[0] *= Math.exp(-2 * dt); p.v[2] *= Math.exp(-2 * dt); continue; }
        if (p.pose !== "fall") continue;
        if (p.g !== undefined) {
          const g = p.g * 16, lim = p.lim * 16;
          p.v[1] = g > 0 ? Math.max(p.v[1] - g * dt, -lim) : g < 0 ? Math.min(p.v[1] - g * dt, lim) : p.v[1] * Math.exp(-3 * dt);
          p.v[0] *= Math.exp(-1.5 * dt); p.v[2] *= Math.exp(-1.5 * dt);
          const s = Math.sin(p.age * 2.3 + p.balance * 6) * p.bal * 16;
          p.pos[0] += (p.v[0] + s) * dt; p.pos[1] += p.v[1] * dt; p.pos[2] += p.v[2] * dt;
          if (p.g > 0 && p.pos[1] <= 0.3) {
            if (String(reglage(p.nom).auSol || "").startsWith("dispar")) p.age = p.vie;
            else { p.pos[1] = 0.3; p.pose = "rest"; p.posee = p.age; }
          }
          continue;
        }
        for (let i = 0; i < 3; i++) p.pos[i] += p.v[i] * dt;
        if (p.mvt !== "flotte" && p.mvt !== "monte" && p.pos[1] <= 0.3) { p.pos[1] = 0.3; p.pose = "rest"; p.posee = p.age; }
      }
      etat.parts = etat.parts.filter(p => p.age < p.vie);
    }

    let boucle = 0, actif = true, sale = true, visible = true, perdu = false, surPerte = null;
    const tic = m => { if (!actif) return; if (!perdu && !gl.isContextLost()) dessiner(m); boucle = requestAnimationFrame(tic); };
    // Contexte perdu (GPU réinitialisé, trop de contextes ouverts) : on arrête de dessiner et on prévient la page,
    // qui propose de recréer la vue sur un canvas neuf plutôt qu'un échec définitif.
    canvas.addEventListener("webglcontextlost", e => { e.preventDefault(); perdu = true; if (actif && surPerte) surPerte(); });
    boucle = requestAnimationFrame(tic);
    // Vue sortie de l'écran (fiche défilée sur mobile, carte hors champ) : plus de calcul jusqu'à son retour.
    const observateur = typeof IntersectionObserver === "function" ? new IntersectionObserver(es => { visible = es[es.length - 1].isIntersecting; sale = true; }) : null;
    if (observateur) observateur.observe(canvas);
    const marquer = () => { sale = true; };
    ["pointerdown", "pointermove", "wheel", "keydown", "dblclick"].forEach(t => canvas.addEventListener(t, marquer, { passive: true }));

    // Orbite : glisser pour tourner, molette ou pincement pour zoomer, double-clic pour recadrer.
    const pointeurs = new Map(); let ecart0 = 0, dist0 = 0;
    canvas.addEventListener("pointerdown", e => { canvas.setPointerCapture(e.pointerId); pointeurs.set(e.pointerId, [e.clientX, e.clientY]);
      if (pointeurs.size === 2) { const [a, b] = [...pointeurs.values()]; ecart0 = Math.hypot(a[0] - b[0], a[1] - b[1]); dist0 = etat.jeu ? etat.jeu.dist : etat.dist; } });
    /** Zoom : distance de la caméra (studio) ou du joueur en blocs (« comme en jeu », 1,5 à 32 blocs). */
    function zoomer(v, absolu) {
      if (etat.jeu) etat.jeu.dist = borne(absolu ? v : etat.jeu.dist * v, 1.5, 32);
      else etat.dist = borne(absolu ? v : etat.dist * v, etat.distBase * 0.25, etat.distBase * 3);
    }
    canvas.addEventListener("pointermove", e => {
      if (!pointeurs.has(e.pointerId)) return;
      const [x0, y0] = pointeurs.get(e.pointerId); pointeurs.set(e.pointerId, [e.clientX, e.clientY]);
      if (pointeurs.size === 2) { const [a, b] = [...pointeurs.values()]; const ec = Math.hypot(a[0] - b[0], a[1] - b[1]); if (ecart0) zoomer(dist0 * ecart0 / ec, true); return; }
      etat.theta -= (e.clientX - x0) * 0.5;
      // « comme en jeu » : glisser en hauteur monte ou baisse les yeux du joueur (de −20° à 60° vus depuis la pièce)
      if (etat.jeu) etat.phiJeu = borne(etat.phiJeu + (e.clientY - y0) * 0.3, -20, 60);
      else etat.phi = borne(etat.phi + (e.clientY - y0) * 0.4, -85, 85);
    });
    const fin = e => { pointeurs.delete(e.pointerId); };
    canvas.addEventListener("pointerup", fin); canvas.addEventListener("pointercancel", fin);
    canvas.addEventListener("wheel", e => { e.preventDefault(); zoomer(Math.exp(e.deltaY * 0.0012)); }, { passive: false });
    canvas.addEventListener("dblclick", () => recadrer());
    canvas.addEventListener("keydown", e => {
      const pas = { ArrowLeft: [8, 0], ArrowRight: [-8, 0], ArrowUp: [0, -6], ArrowDown: [0, 6] }[e.key];
      if (pas) { e.preventDefault(); e.stopPropagation(); etat.theta += pas[0]; if (etat.jeu) etat.phiJeu = borne(etat.phiJeu + pas[1], -20, 60); else etat.phi = borne(etat.phi + pas[1], -85, 85); }
      else if (e.key === "+" || e.key === "=") zoomer(0.85);
      else if (e.key === "-") zoomer(1 / 0.85);
      else if (e.key === "0") recadrer();
    });
    function recadrer() { etat.theta = -35; etat.phi = 18; etat.phiJeu = 0; etat.dist = etat.distBase; etat.cible = etat.cibleBase.slice(); }

    const api = {
      charger: async (modele, nomAnim) => {
        await charger(modele); etat.anim = nomAnim; etat.t = 0; etat.tSon = -1e-4;
        etat.familier = etat.P.familier ? "vivant" : null;   // un familier vivant se montre vivant par défaut
        etat.etape = etat.P.etapes.length ? "repos" : null;    // un skin à étapes se montre au repos
        cadrer(); recadrer();
      },
      animation: nomAnim => { couperSons(); etat.anim = nomAnim; etat.t = 0; etat.tSon = -1e-4; etat.parts = []; cadrer(); },
      lecture: v => { etat.lecture = v; etat.dernier = 0; if (!v) couperSons(); },
      temps: t => { etat.t = t; etat.tSon = tempsLocal(etat.P && etat.P.anims.get(etat.anim), t); },   // déplacer le curseur ne joue rien
      duree: () => { const a = etat.P && etat.P.anims.get(etat.anim); return a ? Number(a.length) || 0 : 0; },
      requetes: extra => { etat.extra = extra; },
      surTemps: f => { etat.surTemps = f; },
      recadrer,
      nuit: v => { etat.nuit = v; },
      /** « Comme en jeu » : null (rendu studio) ou { ciel: "jour" | "gris" | "nuit" | "shader", distance: blocs } ; le joueur
          debout (yeux à 1,62 bloc) regarde la pièce à cette distance, champ de 70°, écran de 1 369 lignes. */
      jeu: v => { etat.jeu = v ? { ciel: CIELS[v.ciel] ? v.ciel : "gris", dist: borne(Number(v.distance) || 3, 1.5, 32) } : null; etat.parts = []; etat.cumul = {}; },
      distanceJeu: () => (etat.jeu ? etat.jeu.dist : null),
      calque: v => { etat.calqueVisible = v; },
      aCalque: () => !!(etat.P && etat.P.calque),
      aParticules: () => !!(etat.P && etat.P.particules.size && etat.P.emetteurs.length),
      particules: v => { etat.particules = v; if (!v) etat.parts = []; },
      mouvement: v => { etat.mouvement = v; },
      reglages: r => { etat.reglages = r; },                                    // { sorte: { mouvement, vie, nombre } }
      evenement: (nom, fin) => { etat.evt = nom ? { nom, t0: etat.t, fin, tSon: -1e-4 } : null; },
      evenements: () => [...(etat.P ? etat.P.anims.keys() : [])].filter(n => n.split(".").pop().startsWith("event_")),
      stats: () => ({ particules: etat.parts.length, t: etat.t, quads: etat.n }),
      /** Pour les tests : avance l'animation et les particules de s secondes, par pas de 50 ms. */
      avancer: s => { for (let k = 0; k < s / 0.05; k++) { etat.t += 0.05; simulerParticules(image(etat.P, etat.anim, etat.t, { extra: etat.extra, familier: etat.familier, etape: etat.etape }).emit, 0.05); } },
      /** Pour les tests : particules en cours, par sorte ({ nom: nombre }). */
      sortes: () => etat.parts.reduce((o, p) => { o[p.nom] = (o[p.nom] || 0) + 1; return o; }, {}),
      /** Familier vivant (guide 6.6) : "vivant" (au sol à côté du joueur, par défaut) ou "menu" (porté, comme le menu Apparence). */
      familier: mode => { etat.familier = mode; etat.parts = []; cadrer(); },
      blocFamilier: () => (etat.P && etat.P.familier) || null,
      /** Effet de téléportation (guide 15) : posé au sol, joueur sur le groupe « joueur ». */
      effet: () => !!(etat.P && etat.P.effet),
      /** Skin d'objet (guide 14) : étape montrée (repos, bande_1…), null = tout le modèle. */
      etape: e => { etat.etape = e; cadrer(); },
      etapes: () => (etat.P ? etat.P.etapes.slice() : []),
      surPerte: f => { surPerte = f; if (perdu && f) f(); },
      perdu: () => perdu || gl.isContextLost(),
      /** Clés de son dans le modèle (embarqués ou non) : { embarques, autres }. */
      sons: () => { const r = { embarques: 0, autres: 0 }; if (!etat.P) return r;
        for (const a of etat.P.anims.values()) for (const k of clesSon(a)) for (const n of k.noms) r[n in (etat.P.m.phynaria_sounds || {}) ? "embarques" : "autres"]++;
        return r; },
      detruire: () => {
        if (!actif) return;
        actif = false; surPerte = null; couperSons(); cancelAnimationFrame(boucle); if (observateur) observateur.disconnect();
        // Libère tout de suite la mémoire du GPU et le contexte (Chrome n'en garde qu'une quinzaine par page), puis le canvas.
        if (!gl.isContextLost()) {
          for (const b of Object.values(tampons)) gl.deleteBuffer(b);
          gl.deleteTexture(tex); gl.deleteTexture(texLum); gl.deleteProgram(prog); gl.deleteProgram(progFond); gl.deleteProgram(progCopie);
          if (cadreJeu) { gl.deleteFramebuffer(cadreJeu.fb); gl.deleteTexture(cadreJeu.tex); gl.deleteRenderbuffer(cadreJeu.prof); cadreJeu = null; }
          const ext = gl.getExtension("WEBGL_lose_context"); if (ext) ext.loseContext();
        }
        etat.P = null; etat.parts = []; posArr = ombreArr = etat.uvArr = null;
        canvas.width = canvas.height = 1;
      },
    };
    // Tout appel de l'interface (état, temps, nuit, calque…) peut changer l'image : la redessiner.
    for (const k of Object.keys(api)) { const f = api[k]; api[k] = (...a) => { sale = true; return f(...a); }; }
    return api;
  }

  function oeilDe(e) {
    const th = e.theta * Math.PI / 180, ph = e.phi * Math.PI / 180;
    // theta = 0 : caméra devant le joueur (côté −z).
    return [e.cible[0] + e.dist * Math.cos(ph) * Math.sin(th), e.cible[1] + e.dist * Math.sin(ph), e.cible[2] - e.dist * Math.cos(ph) * Math.cos(th)];
  }
  /** Caméra : studio (orbite, champ de 30°) ou « comme en jeu » (joueur debout à la distance choisie, yeux à 1,62 bloc,
      champ de 70°, regard vers la pièce sans lever la tête de plus de 30°, comme render_bbmodel.camera_jeu). */
  function vueDe(e) {
    if (!e.jeu) return { oeil: oeilDe(e), cible: e.cible, fov: 30 };
    const th = e.theta * Math.PI / 180, d = e.jeu.dist * 16, c = e.cibleBase;
    const oeil = [c[0] + d * Math.sin(th), Math.max(2, 26 + d * Math.tan(e.phiJeu * Math.PI / 180)), c[2] - d * Math.cos(th)];
    // regard vers la pièce, à hauteur de poitrine au plus (0,5 à 1,75 bloc) : un grand effet dépasse de l'écran, comme en jeu
    return { oeil, cible: [c[0], borne(c[1], 8, 28), c[2]], fov: 70 };
  }
  function vueProjection(v, ratio) {
    const oeil = v.oeil;
    const f = norm(sub(v.cible, oeil)), d = norm(croix(f, [0, 1, 0])), h = croix(d, f);
    const V = [d[0], h[0], -f[0], 0, d[1], h[1], -f[1], 0, d[2], h[2], -f[2], 0, -dot(d, oeil), -dot(h, oeil), dot(f, oeil), 1];
    const fov = v.fov * Math.PI / 180, t = 1 / Math.tan(fov / 2), pres = v.fov > 50 ? 0.5 : 1, loin = 2000;
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
      img.onload = () => { gl.bindTexture(gl.TEXTURE_2D, t); gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
        // copies réduites pour le mode « comme en jeu » (guide du 2026-11-08 : mipmaps, 4 niveaux) ; le studio reste en NEAREST
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAX_LEVEL, 4); gl.generateMipmap(gl.TEXTURE_2D); ok(); };
      img.onerror = () => ok();
      img.src = src;
    });
  }
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

  /** Son des vues 3D (toutes) : Visionneuse.son() lit la préférence, Visionneuse.son(true | false) la change et la retient.
      L'appeler depuis un clic débloque l'audio du navigateur. */
  function son(on) {
    if (on === undefined) return sonActif;
    sonActif = !!on;
    try { localStorage.setItem("vestiaire.son", sonActif ? "1" : "0"); } catch (e) {}
    if (sonActif) contexteAudio();
    return sonActif;
  }

  const api = { Noyau, creer, son };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else racine.Visionneuse = api;
})(typeof window !== "undefined" ? window : globalThis);
