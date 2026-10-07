// Ecom Merch Weekly: deck renderer v2 (the PSD template lives here).
// Usage: node build_deck.js data/deck_<week>.json out.pptx [--template]
// Exec-readable layout: one point per slide, serif headline, at most one chart/table card,
// a short facts card and an empty Jamie card. Charts are native shapes so they survive
// Google Slides import and stay editable. Fonts: IBM Plex Serif / Sans / Mono (Google Fonts).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const [, , specPath, outPath, flag] = process.argv;
const TEMPLATE = flag === "--template";
const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
// Logos: <skill>/assets when installed as a skill (scripts/ sits beside assets/), else ./assets next to this file.
const ASSETS = [process.env.MERCH_ASSETS, path.join(__dirname, "..", "assets"), path.join(__dirname, "assets")]
  .find((d) => d && fs.existsSync(path.join(d, "psd_logo_black.png")));
if (!ASSETS) { console.error("BUILD FAILED: psd_logo_black.png not found (set MERCH_ASSETS)"); process.exit(1); }

// ---------------------------------------------------------------- tokens
const C = {
  bg: "F4F3EF", card: "FFFFFF", cardLine: "E2E0D8", ink: "1A1A1A", ink2: "4A4A46", mute: "7A7A74",
  rule: "D9D7CF", dark: "161616", dark2: "2A2A28", lime: "D4FF3F", cobalt: "2B3FE0", cobaltLt: "CDD2F7",
  good: "1B7A4B", bad: "B3261E", badTint: "FBE9E7", jamie: "FBFCF4", jamieLine: "A9B97A",
};
const SERIF = "IBM Plex Serif", SANS = "IBM Plex Sans", MONO = "IBM Plex Mono";
const W = 13.333, H = 7.5, MX = 0.6, CW = W - 2 * MX;
const Y = { kicker: 0.42, head: 0.98, body: 2.02, bodyEnd: 5.12, bottom: 5.27, bottomEnd: 6.66, rule: 6.82, foot: 6.9 };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "PSD Ecom";
pres.company = "PSD Underwear";
pres.title = `Ecom Merch Weekly · ${spec.meta.week}`;
pres.theme = { headFontFace: SERIF, bodyFontFace: SANS };

const LOGO_B = path.join(ASSETS, "psd_logo_black.png"), LOGO_W = path.join(ASSETS, "psd_logo_white.png");
const T = (s, text, o) => s.addText(text, Object.assign({ fontFace: SANS, margin: 0, isTextBox: true, valign: "top", color: C.ink }, o));
const R = (s, o) => s.addShape(pres.shapes.RECTANGLE, Object.assign({ line: { type: "none" } }, o));
const RR = (s, o) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, Object.assign({ rectRadius: 0.06, line: { color: C.cardLine, width: 0.75 } }, o));
const dirColor = (d, inv) => { if (!d) return C.mute; const v = inv ? -d.dir : d.dir; return v > 0 ? C.good : v < 0 ? C.bad : C.mute; };
const cellColor = (c) => ({ bad: C.bad, good: C.good, accent: C.cobalt, muted: C.mute }[c] || C.ink);
const estLines = (text, wIn, pt) => String(text).split("\n").reduce((n, l) => n + Math.max(1, Math.ceil(l.length / Math.max(1, wIn * (125 / pt)))), 0);
const kfmt = (v) => (v >= 1000 ? `${(v / 1000).toFixed(1)}K` : `${v}`);

// ---------------------------------------------------------------- chrome
function pill(s, text, x, y, color) {
  const w = Math.max(0.9, text.length * 0.083 + 0.3);
  R(s, { x: x - w, y, w, h: 0.32, fill: { color: color || C.ink } });
  T(s, text, { x: x - w, y, w, h: 0.32, fontFace: MONO, fontSize: 10, color: "FFFFFF", align: "center", valign: "middle", charSpacing: 1 });
  return w;
}
function chrome(s, sl, n, dark) {
  // section title: numbered chip + bold title, so the reader always knows what the slide is about
  const sec = sl.sec || (sl.type === "appendix" ? "A" : "");
  let kx = MX;
  if (sec) {
    R(s, { x: MX, y: Y.kicker, w: 0.46, h: 0.38, fill: { color: C.ink } });
    T(s, sec, { x: MX, y: Y.kicker, w: 0.46, h: 0.38, fontFace: MONO, fontSize: 12, bold: true, color: C.lime, align: "center", valign: "middle" });
    kx += 0.6;
  }
  T(s, sl.kicker || "", { x: kx, y: Y.kicker, w: 8.4, h: 0.38, fontFace: SANS, fontSize: 17, bold: true, color: dark ? "FFFFFF" : C.ink, valign: "middle", fit: "shrink" });
  let px = W - MX;
  if (sl.missing && sl.missing.length) px -= pill(s, "INPUT MISSING", px, Y.kicker + 0.03, C.bad) + 0.12;
  if (sl.pill) pill(s, sl.pill, px, Y.kicker + 0.03, C.mute);
  s.addShape(pres.shapes.LINE, { x: MX, y: Y.rule, w: CW, h: 0, line: { color: dark ? C.dark2 : C.rule, width: 0.75 } });
  if (sl.footer) T(s, sl.footer, { x: MX, y: Y.foot, w: CW - 1.9, h: 0.3, fontSize: 9, color: C.mute, valign: "middle", fit: "shrink" });
  s.addImage({ path: dark ? LOGO_W : LOGO_B, x: W - MX - 1.3, y: Y.foot + 0.06, w: 0.66, h: 0.18 });
  T(s, String(n).padStart(2, "0"), { x: W - MX - 0.45, y: Y.foot, w: 0.45, h: 0.3, fontSize: 9, color: C.mute, align: "right", valign: "middle" });
}
function headline(s, text, y, maxH) {
  const lines = estLines(text, CW, 24);
  T(s, text, { x: MX, y, w: CW - 0.3, h: maxH || 0.95, fontFace: SERIF, fontSize: lines > 2 ? 20 : 24, color: C.ink2, valign: "top", fit: "shrink" });
}
function missingLine(s, items, y) {
  T(s, [{ text: "Missing input: ", options: { bold: true, color: C.bad } }, { text: items.join(" · "), options: { color: C.bad } }],
    { x: MX, y, w: CW, h: 0.26, fontSize: 10, valign: "middle", fit: "shrink" });
}
function card(s, x, y, w, h, title) {
  RR(s, { x, y, w, h, fill: { color: C.card } });
  if (title) T(s, title, { x: x + 0.22, y: y + 0.16, w: w - 0.44, h: 0.24, fontFace: MONO, fontSize: 9, color: C.cobalt, charSpacing: 1, fit: "shrink" });
  return { x: x + 0.22, y: y + (title ? 0.46 : 0.18), w: w - 0.44, h: h - (title ? 0.62 : 0.36) };
}

// ---------------------------------------------------------------- blocks
function stats(s, items, x, y, w, h) {
  const n = items.length, rh = h / n;
  items.forEach((st, i) => {
    const cy = y + i * rh;
    T(s, st.value, { x, y: cy, w, h: rh * 0.48, fontSize: 30, bold: true, color: st.accent ? C.cobalt : C.ink, valign: "bottom", fit: "shrink" });
    T(s, st.label, { x, y: cy + rh * 0.5, w, h: 0.26, fontSize: 12, bold: true });
    T(s, st.sub, { x, y: cy + rh * 0.5 + 0.26, w, h: 0.24, fontSize: 10, color: C.mute, fit: "shrink" });
    if (i < n - 1) s.addShape(pres.shapes.LINE, { x, y: cy + rh - 0.05, w, h: 0, line: { color: C.rule, width: 0.5 } });
  });
}
function table(s, b, r) {
  const cols = b.columns, sum = cols.reduce((a, c) => a + c.w, 0), cw = cols.map((c) => (c.w / sum) * r.w);
  const txt = (c) => (c !== null && typeof c === "object" ? c.t : c);
  let fs_ = b.big ? 12 : b.dense ? 9.5 : 10.5;
  const avail = r.h - (b.note ? 0.32 : 0);
  const hgt = (f) => { const lh = (f / 72) * 1.7 + 0.12; return lh * (1 + b.rows.reduce((a, row) => a + Math.max(...row.map((c, i) => estLines(txt(c) ?? "", cw[i] - 0.18, f))), 0)); };
  while (hgt(fs_) > avail && fs_ > 7.5) fs_ -= 0.5;
  const bl = { type: "solid", pt: 0.5, color: C.rule }, none = { type: "none" };
  const head = cols.map((c) => ({ text: c.h.toUpperCase(), options: { fontFace: MONO, fontSize: Math.min(9, fs_), color: C.mute, align: c.a === "r" ? "right" : "left", border: [none, none, bl, none] } }));
  const rows = b.rows.map((row) => row.map((c, i) => {
    const o = c !== null && typeof c === "object" ? c : { t: c };
    return { text: String(o.t ?? ""), options: { bold: !!o.b, color: cellColor(o.c), align: cols[i].a === "r" ? "right" : "left", border: [none, none, bl, none] } };
  }));
  const rowH = Math.min(b.big ? 0.42 : 0.34, avail / (b.rows.length + 1));
  s.addTable([head, ...rows], { x: r.x, y: r.y, w: r.w, colW: cw, rowH, fontFace: SANS, fontSize: fs_, color: C.ink, valign: "middle", margin: [2, 5, 2, 5], autoPage: false });
  if (b.note) T(s, b.note, { x: r.x, y: r.y + r.h - 0.28, w: r.w, h: 0.28, fontSize: 8.5, italic: true, color: C.mute, valign: "bottom", fit: "shrink" });
}
function hbars(s, b, r) {
  const hasCmp = b.items.some((i) => i.cmp != null);
  const n = b.items.length, rh = Math.min(0.34, (r.h - (hasCmp ? 0.28 : 0) - (b.note ? 0.4 : 0)) / n);
  const lw = r.w * 0.36, vw = 1.45, bw = r.w - lw - vw - 0.1;
  const max = Math.max(...b.items.map((i) => Math.max(i.value || 0, i.cmp || 0)), 1e-9);
  const f = rh < 0.24 ? 9 : 10;
  b.items.forEach((it, i) => {
    const y = r.y + i * rh;
    T(s, it.label, { x: r.x, y, w: lw - 0.1, h: rh, fontSize: f, valign: "middle", bold: !!it.hl, color: it.muted ? C.mute : C.ink, fit: "shrink" });
    const bh = hasCmp ? rh * 0.36 : rh * 0.55, by = y + (rh - (hasCmp ? bh * 2 + 0.03 : bh)) / 2;
    R(s, { x: r.x + lw, y: by, w: Math.max(0.03, (it.value / max) * bw), h: bh, fill: { color: it.muted ? C.rule : it.hl ? C.ink : C.cobalt } });
    if (hasCmp) R(s, { x: r.x + lw, y: by + bh + 0.03, w: Math.max(0.03, ((it.cmp || 0) / max) * bw), h: bh, fill: { color: C.cobaltLt } });
    T(s, it.display, { x: r.x + lw + bw + 0.1, y, w: vw, h: rh, fontSize: f, valign: "middle", color: it.muted ? C.mute : C.ink2, fit: "shrink" });
  });
  if (hasCmp) legend(s, r.x + lw, r.y + n * rh + 0.06, ["This week", "Last week"]);
  if (b.note) T(s, b.note, { x: r.x, y: r.y + r.h - 0.38, w: r.w, h: 0.38, fontSize: 8.5, italic: true, color: C.mute, valign: "bottom", fit: "shrink" });
}
function legend(s, x, y, labels) {
  [C.cobalt, C.cobaltLt].forEach((c, i) => {
    R(s, { x: x + i * 1.35, y: y + 0.07, w: 0.2, h: 0.11, fill: { color: c } });
    T(s, labels[i], { x: x + i * 1.35 + 0.26, y, w: 1.05, h: 0.24, fontSize: 9, color: C.mute, valign: "middle" });
  });
}
function vbars(s, b, r) {
  const n = b.items.length, slot = r.w / n, plot = r.h - 0.95, base = r.y + 0.25 + plot;
  const max = Math.max(...b.items.map((i) => Math.max(i.value, i.cmp || 0)));
  b.items.forEach((it, i) => {
    const x = r.x + i * slot, bw = slot * 0.3, h1 = (it.value / max) * plot, h0 = ((it.cmp || 0) / max) * plot;
    R(s, { x: x + slot * 0.18, y: base - h1, w: bw, h: h1, fill: { color: C.cobalt } });
    R(s, { x: x + slot * 0.18 + bw + 0.04, y: base - h0, w: bw, h: h0, fill: { color: C.cobaltLt } });
    T(s, kfmt(it.value), { x: x, y: base - h1 - 0.24, w: slot * 0.66, h: 0.22, fontSize: 9, bold: true, align: "center" });
    T(s, it.label, { x, y: base + 0.06, w: slot, h: 0.22, fontSize: 9.5, align: "center" });
    T(s, it.sub, { x, y: base + 0.28, w: slot, h: 0.2, fontSize: 8.5, align: "center", color: C.mute });
  });
  s.addShape(pres.shapes.LINE, { x: r.x, y: base, w: r.w, h: 0, line: { color: C.rule, width: 0.75 } });
  legend(s, r.x, base + 0.5, ["This week", "Same day last week"]);
}
function funnel(s, b, r) {
  const n = b.steps.length, gap = 0.08, sh = Math.min(0.5, (r.h - gap * (n - 1)) / n);
  const lw = 1.75, rw = b.rw || 1.55, fw = r.w - lw - rw - 0.15;
  const max = Math.max(...b.steps.map((x) => x.value || 0));
  b.steps.forEach((st, i) => {
    const y = r.y + i * (sh + gap);
    T(s, [{ text: st.label, options: { breakLine: true, color: C.ink2 } }, { text: st.display, options: { bold: true, fontSize: 13, color: st.value == null ? C.bad : C.ink } }],
      { x: r.x, y, w: lw, h: sh, fontSize: 9.5, valign: "middle", fit: "shrink" });
    const bw = st.value == null ? fw * 0.4 : Math.max(0.08, Math.sqrt(st.value / max) * fw);
    if (st.value == null) R(s, { x: r.x + lw, y: y + 0.06, w: bw, h: sh - 0.12, fill: { color: C.card }, line: { color: C.bad, width: 1, dashType: "dash" } });
    else R(s, { x: r.x + lw, y: y + 0.06, w: bw, h: sh - 0.12, fill: { color: i === 0 ? C.ink : C.cobalt } });
    if (st.rate) T(s, st.rate, { x: r.x + lw + fw + 0.15, y, w: rw, h: sh, fontSize: 9.5, color: C.ink2, valign: "middle", fit: "shrink" });
  });
}
function calendar2(s, b, r) {
  const cols = 7, rows = Math.ceil(b.calendar.length / cols), g = 0.1;
  const cw = (r.w - g * (cols - 1)) / cols, ch = (r.h - g * (rows - 1)) / rows;
  const tag = { Site: [C.lime, C.ink], Email: [C.cobalt, "FFFFFF"], SMS: [C.ink, "FFFFFF"], Push: [C.cobaltLt, C.ink] };
  b.calendar.forEach((d, i) => {
    const x = r.x + (i % cols) * (cw + g), y = r.y + Math.floor(i / cols) * (ch + g);
    RR(s, { x, y, w: cw, h: ch, fill: { color: d.items.length ? C.card : "F8F7F3" } });
    T(s, d.day, { x: x + 0.1, y: y + 0.08, w: cw - 0.2, h: 0.22, fontFace: MONO, fontSize: 9, color: C.mute });
    const ih = Math.min(0.5, (ch - 0.36) / Math.max(1, d.items.length));
    d.items.forEach((it, j) => {
      const iy = y + 0.34 + j * ih;
      (it.tags || [it.tag]).forEach((tg, k) => {
        const [bg, fg] = tag[tg] || [C.rule, C.ink];
        R(s, { x: x + 0.1 + k * 0.47, y: iy, w: 0.43, h: 0.16, fill: { color: bg } });
        T(s, tg.toUpperCase(), { x: x + 0.1 + k * 0.47, y: iy, w: 0.43, h: 0.16, fontFace: MONO, fontSize: 6.5, color: fg, align: "center", valign: "middle" });
      });
      T(s, it.text, { x: x + 0.1, y: iy + 0.17, w: cw - 0.2, h: ih - 0.19, fontSize: 8.5, bold: true, fit: "shrink" });
    });
  });
}
function imageSlot(s, label, x, y, h) {
  const w = h * 0.8; // 4:5 portrait, mobile first
  R(s, { x, y, w, h, fill: { color: "ECEBE5" }, line: { color: "B9B7AE", width: 1, dashType: "dash" } });
  T(s, [{ text: "IMAGE · 4:5", options: { fontFace: MONO, fontSize: 9, color: C.mute, breakLine: true, charSpacing: 1 } }, { text: label, options: { fontSize: 10, color: C.ink2 } }],
    { x: x + 0.15, y, w: w - 0.3, h, align: "center", valign: "middle" });
  return w;
}
// product thumbnail (4:5); a neutral tile when the image couldn't be fetched
function thumb(s, img, x, y, h) {
  const w = h * 0.8;
  if (img && fs.existsSync(img)) s.addImage({ path: img, x, y, w, h, sizing: { type: "cover", w, h } });
  else { R(s, { x, y, w, h, fill: { color: "ECEBE5" }, line: { color: "D9D7CF", width: 0.5 } });
    T(s, "IMG", { x, y, w, h, fontFace: MONO, fontSize: 6.5, color: C.mute, align: "center", valign: "middle" }); }
  return w;
}
const SIG = { "HIGH VIEWS · LOW CVR": [C.bad, "FFFFFF"], "HIGH VIEWS · LOW ATC": ["E8A33D", C.ink], RISER: [C.good, "FFFFFF"], FALLER: [C.ink, "FFFFFF"] };
function sigChip(s, tag, x, y) {
  const [bg, fg] = SIG[tag] || [C.rule, C.ink], w = tag.length * 0.058 + 0.16;
  R(s, { x, y, w, h: 0.17, fill: { color: bg } });
  T(s, tag, { x, y, w, h: 0.17, fontFace: MONO, fontSize: 6.5, bold: true, color: fg, align: "center", valign: "middle" });
  return w;
}
function product_grid(s, b, r) {
  const cols = b.cols || 2, g = 0.35, cw = (r.w - g * (cols - 1)) / cols, per = Math.ceil(b.items.length / cols);
  const headH = 0.2, noteH = b.note ? 0.3 : 0, rh = (r.h - headH - noteH) / per, ih = Math.min(rh - 0.04, 0.5);
  const mw = [0.5, 0.58, 0.55, 0.62, 0.45, 0.5], mtot = mw.reduce((a, c) => a + c, 0);
  for (let c = 0; c < cols; c++) {
    const x0 = r.x + c * (cw + g), nx = x0 + 0.22 + ih * 0.8 + 0.1, nw = cw - (nx - x0) - mtot;
    b.heads.forEach((h, i) => T(s, h.toUpperCase(), { x: nx + nw + mw.slice(0, i).reduce((a, v) => a + v, 0), y: r.y, w: mw[i], h: headH, fontFace: MONO, fontSize: 7, color: C.mute, align: "right", valign: "bottom" }));
    b.items.slice(c * per, (c + 1) * per).forEach((it, j) => {
      const y = r.y + headH + j * rh, cy = y + (rh - ih) / 2;
      s.addShape(pres.shapes.LINE, { x: x0, y, w: cw, h: 0, line: { color: C.rule, width: 0.5 } });
      T(s, String(it.rank), { x: x0, y, w: 0.22, h: rh, fontFace: MONO, fontSize: 8, color: C.mute, valign: "middle" });
      thumb(s, it.img, x0 + 0.22, cy, ih);
      const hasSig = it.signals && it.signals.length;
      T(s, [{ text: it.title, options: { bold: true, breakLine: true } }, { text: it.type + (it.coll ? "  ·  " + it.coll : ""), options: { color: C.mute, fontSize: 7.5 } }],
        { x: nx, y: hasSig ? y + 0.02 : y, w: nw - 0.05, h: hasSig ? rh - 0.18 : rh, fontSize: 9, valign: "middle", fit: "shrink" });
      if (hasSig) { let sx = nx; it.signals.forEach((t) => { sx += sigChip(s, t, sx, y + rh - 0.2) + 0.05; }); }
      it.cells.forEach((cl, i) => T(s, cl.t, { x: nx + nw + mw.slice(0, i).reduce((a, v) => a + v, 0), y, w: mw[i], h: rh, fontSize: 9, bold: !!cl.b,
        color: cellColor(cl.c), align: "right", valign: "middle", fit: "shrink" }));
    });
  }
  if (b.note) T(s, b.note, { x: r.x, y: r.y + r.h - 0.28, w: r.w, h: 0.28, fontSize: 8, italic: true, color: C.mute, valign: "bottom", fit: "shrink" });
}
function signal_cards(s, b, r) {
  const cols = b.cols || 4, rows = Math.ceil(b.cards.length / cols), g = 0.18;
  const cw = (r.w - g * (cols - 1)) / cols, ch = (r.h - g * (rows - 1)) / rows;
  b.cards.forEach((cd, i) => {
    const x = r.x + (i % cols) * (cw + g), y = r.y + Math.floor(i / cols) * (ch + g);
    RR(s, { x, y, w: cw, h: ch, fill: { color: "FAFAF7" } });
    const ih = ch - 0.2, iw = thumb(s, cd.img, x + 0.1, y + 0.1, ih), tx = x + iw + 0.2, tw = cw - iw - 0.3;
    sigChip(s, cd.tag, tx, y + 0.07);
    T(s, cd.title, { x: tx, y: y + 0.26, w: tw, h: 0.2, fontSize: cd.title.length > 28 ? 7.5 : 9, bold: true, valign: "middle", fit: "shrink" });
    T(s, cd.type, { x: tx, y: y + 0.45, w: tw, h: 0.14, fontSize: 7, color: C.mute, valign: "middle" });
    T(s, cd.lines.map((l, k) => ({ text: l, options: { breakLine: k < cd.lines.length - 1, bold: /^Entry|^Source/.test(l) ? false : false } })),
      { x: tx, y: y + 0.6, w: tw, h: ch - 0.64, fontSize: 7, color: C.ink2, valign: "top", lineSpacingMultiple: 0.95 });
  });
}
function block(s, b, r) {
  ({ table, hbars, vbars, funnel, calendar2, product_grid, signal_cards }[b.kind] || (() => { throw new Error("unknown block " + b.kind); }))(s, b, r);
}

// ---------------------------------------------------------------- bottom row (facts + Jamie)
function bottom(s, sl) {
  // Three fill-in boxes: what changed, why, next steps.
  // speaker notes stay empty: they belong to the presenter
  if (!sl.jamie) return;
  const cols = ["WHAT CHANGED", "WHY", "NEXT STEPS"], g = 0.25;
  const y = Y.bottom, h = Y.bottomEnd - Y.bottom, bw = (CW - g * (cols.length - 1)) / cols.length;
  cols.forEach((c, i) => {
    const x = MX + i * (bw + g);
    RR(s, { x, y, w: bw, h, fill: { color: C.jamie }, line: { color: C.jamieLine, width: 1, dashType: "dash" } });
    T(s, c, { x: x + 0.22, y: y + 0.16, w: bw - 0.44, h: 0.22, fontFace: MONO, fontSize: 9, bold: true, color: "5E6E2C", charSpacing: 1 });
    for (let k = 0; k < 3; k++) s.addShape(pres.shapes.LINE, { x: x + 0.22, y: y + 0.66 + k * 0.3, w: bw - 0.44, h: 0, line: { color: "D5DDB8", width: 0.75 } });
  });
}

// ---------------------------------------------------------------- slide types
function body(s, sl, top) {
  const b = sl.body, end = sl.type === "appendix" || !sl.jamie ? Y.rule - 0.15 : Y.bodyEnd, h = end - top;
  switch (b.layout) {
    case "card_full": block(s, b.card, card(s, MX, top, CW, h, b.card.title)); break;
    case "stats_card": stats(s, b.stats, MX, top, 3.0, h); block(s, b.card, card(s, MX + 3.35, top, CW - 3.35, h, b.card.title)); break;
    case "two_cards": {
      const w = (CW - 0.25) * (b.split || 0.5), w2 = CW - 0.25 - w;
      block(s, b.left, card(s, MX, top, w, h, b.left.title));
      block(s, b.right, card(s, MX + w + 0.25, top, w2, h, b.right.title)); break;
    }
    case "card_side": {
      const lw = 6.6, rw = CW - lw - 0.25, rx = MX + lw + 0.25;
      block(s, b.left, card(s, MX, top, lw, h, b.left.title));
      const h1 = (h - 0.2) * 0.52, h2 = h - 0.2 - h1;
      block(s, b.right[0], card(s, rx, top, rw, h1, b.right[0].title));
      block(s, b.right[1], card(s, rx, top + h1 + 0.2, rw, h2, b.right[1].title)); break;
    }
    case "image_card": {
      const iw = imageSlot(s, b.image, MX, top, h);
      block(s, b.card, card(s, MX + iw + 0.3, top, CW - iw - 0.3, h, b.card.title)); break;
    }
    case "table_images": {
      let iw = 0; const n = b.images.length;
      for (let i = n - 1; i >= 0; i--) iw += imageSlot(s, b.images[i], W - MX - (iw + h * 0.8) - (n - 1 - i) * 0.2, top, h);
      const used = iw + 0.2 * (n - 1) + 0.3;
      block(s, b.card, card(s, MX, top, CW - used, h, b.card.title)); break;
    }
    case "calendar2": block(s, { kind: "calendar2", calendar: b.calendar }, { x: MX, y: top, w: CW, h }); break;
    default: throw new Error("unknown layout " + b.layout);
  }
}
function finding(sl, n) {
  const s = pres.addSlide(); s.background = { color: C.bg };
  chrome(s, sl, n);
  headline(s, sl.headline, Y.head);
  let top = Y.body;
  if (sl.missing && sl.missing.length) { missingLine(s, sl.missing, Y.body - 0.12); top += 0.22; }
  body(s, sl, top);
  bottom(s, sl);
}
function cover(sl, n) {
  const s = pres.addSlide(); s.background = { color: C.dark };
  s.addImage({ path: LOGO_W, x: MX, y: 0.5, w: 1.66, h: 0.45 });
  pill(s, sl.pill, W - MX, 0.56, C.dark2);
  T(s, sl.kicker, { x: MX, y: 1.9, w: 9, h: 0.3, fontFace: MONO, fontSize: 12, color: C.lime, charSpacing: 2 });
  T(s, sl.title, { x: MX, y: 2.3, w: 11.2, h: 1.0, fontFace: SERIF, fontSize: 48, color: "FFFFFF", fit: "shrink" });
  if (sl.headline) T(s, sl.headline, { x: MX, y: 3.45, w: 11.2, h: 0.45, fontSize: 18, color: "C9C9C4", fit: "shrink" });
  sl.stats.forEach((st, i) => {
    const x = MX + i * 3.2;
    T(s, st.value, { x, y: 4.95, w: 3, h: 0.6, fontSize: 32, bold: true, color: st.accent ? C.lime : "FFFFFF" });
    T(s, st.label, { x, y: 5.58, w: 3, h: 0.26, fontSize: 12, color: "E6E6E1" });
    T(s, st.sub, { x, y: 5.84, w: 3, h: 0.24, fontSize: 10, color: "9A9A94" });
  });
  s.addShape(pres.shapes.LINE, { x: MX, y: Y.rule, w: CW, h: 0, line: { color: C.dark2, width: 0.75 } });
  T(s, sl.foot_left, { x: MX, y: Y.foot, w: 6, h: 0.3, fontSize: 10, color: "9A9A94", valign: "middle" });
  T(s, sl.foot_right, { x: W - MX - 6, y: Y.foot, w: 6, h: 0.3, fontSize: 10, color: "9A9A94", valign: "middle", align: "right" });
}
function summary(sl, n) {
  const s = pres.addSlide(); s.background = { color: C.bg };
  chrome(s, sl, n);
  headline(s, sl.headline, Y.head);
  const top = Y.body, h = Y.rule - 0.2 - top;
  stats(s, sl.stats, MX, top, 3.3, h);
  const x = MX + 3.75, w = CW - 3.75;
  RR(s, { x, y: top, w, h, fill: { color: C.jamie }, line: { color: C.jamieLine, width: 1, dashType: "dash" } });
  T(s, sl.card_title, { x: x + 0.3, y: top + 0.22, w: w - 0.6, h: 0.26, fontFace: MONO, fontSize: 10, color: "5E6E2C", charSpacing: 1 });
  const rh = (h - 1.2) / sl.card_rows;
  for (let i = 0; i < sl.card_rows; i++) {
    const y = top + 0.65 + i * rh;
    T(s, String(i + 1), { x: x + 0.3, y, w: 0.3, h: rh, fontFace: MONO, fontSize: 14, color: "A9B97A", valign: "middle" });
    s.addShape(pres.shapes.LINE, { x: x + 0.75, y: y + rh - 0.12, w: w - 1.05, h: 0, line: { color: "D5DDB8", width: 0.75 } });
  }
  T(s, sl.card_note, { x: x + 0.3, y: top + h - 0.45, w: w - 0.6, h: 0.3, fontSize: 10, color: C.mute, valign: "middle" });
}
function divider(sl, n) {
  const s = pres.addSlide(); s.background = { color: C.dark };
  if (sl.kicker) T(s, sl.kicker, { x: MX, y: Y.kicker, w: 8, h: 0.3, fontFace: MONO, fontSize: 11, color: C.lime, charSpacing: 2, valign: "middle" });
  T(s, sl.num, { x: MX, y: 2.35, w: 3, h: 0.8, fontFace: MONO, fontSize: 44, color: C.lime });
  T(s, sl.title, { x: MX, y: 3.2, w: 11.5, h: 0.95, fontFace: SERIF, fontSize: 38, color: "FFFFFF", fit: "shrink" });
  if (sl.sub) T(s, sl.sub, { x: MX, y: 4.2, w: 9, h: 0.5, fontSize: 15, color: "C9C9C4" });
  s.addImage({ path: LOGO_W, x: W - MX - 1.3, y: Y.foot + 0.06, w: 0.66, h: 0.18 });
  T(s, String(n).padStart(2, "0"), { x: W - MX - 0.45, y: Y.foot, w: 0.45, h: 0.3, fontSize: 9, color: "9A9A94", align: "right", valign: "middle" });
}

// ---------------------------------------------------------------- lint + run
const BANNED = /\b(should|recommend|consider|suggest|opportunity to|must|delve|leverage|utilize|robust|crucial(ly)?|pivotal|testament|underscor\w*|highlighting|showcas\w*|notably|importantly|significantly|game.?changer|seamless(ly)?)\b/i;
const problems = [];
spec.slides.forEach((sl, i) => {
  const n = i + 1;
  if (sl.type === "finding" || sl.type === "summary") {
    if (!TEMPLATE && !(sl.footer || "").includes(spec.meta.week)) problems.push(`slide ${n} (${sl.id}): footer missing the reporting week`);
    const texts = [sl.headline, ...(sl.observations || [])];
    texts.forEach((t) => {
      if (BANNED.test(t || "")) problems.push(`slide ${n} (${sl.id}): banned or recommendation wording: "${(t.match(BANNED) || [])[0]}"`);
      if (((t || "").match(/—/g) || []).length > 0) problems.push(`slide ${n} (${sl.id}): em dash in headline/observation`);
      if ((t || "").length > 230) problems.push(`slide ${n} (${sl.id}): observation over 230 characters`);
    });
  }
  if (sl.type === "cover" && (sl.headline || "").length > 100) problems.push(`slide ${n} (cover): cover line over 100 characters (one line at most)`);
  if (sl.type === "cover" && BANNED.test(sl.headline || "")) problems.push(`slide ${n} (cover): banned wording`);
  ({ cover, divider, summary }[sl.type] || finding)(sl, n);
});
if (problems.length) { console.error("BUILD FAILED (fail-closed):\n - " + problems.join("\n - ")); process.exit(1); }
pres.writeFile({ fileName: outPath }).then(() => console.log(`wrote ${outPath} (${spec.slides.length} slides)`));
