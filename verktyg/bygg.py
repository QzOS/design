#!/usr/bin/env python3
"""
bygg.py - bygger komponenterna ur tokens/tokens.json

    python3 verktyg/bygg.py

Skriver:
  svg/glyfer/*.svg          symbolerna, 16 u, ritade i currentColor
  svg/<tema>/<komponent>/   varje komponent i varje läge, för glod och gryning
  tokens/<tema>.css         rollerna och måtten som CSS-variabler
  docs/dpi.md               måtten i bildpunkter vid varje skala

Allt mäts i u (1 u = 1 bildpunkt vid 96 dpi). En SVG:s viewBox är i u, så
samma fil ritas skarp i alla skalor: bredd och höjd gånger skalan.

Bara standardbiblioteket behövs.
"""
import json
import math
import pathlib
import re
import shutil

ROT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROT / "tokens" / "tokens.json").read_text(encoding="utf-8"))
M = T["matt"]
R = T["radie"]
TYP = T["typ"]["stilar"]
FONT = "Manrope, Inter, 'DejaVu Sans', sans-serif"
TEMAN = ("glod", "gryning")

# ---------------------------------------------------------------- färg


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """a blandat med t av b"""
    ra, ga, ba = hexrgb(a)
    rb, gb, bb = hexrgb(b)
    return "#%02X%02X%02X" % (round(ra + (rb - ra) * t),
                              round(ga + (gb - ga) * t),
                              round(ba + (bb - ba) * t))


class Tema:
    def __init__(self, namn):
        self.namn = namn
        self.f = dict(T["farg"][namn])
        f = self.f
        # härledda lägen som inte har en egen roll
        f["kant-kontroll-hover"] = mix(f["kant-kontroll"], f["text"], 0.4)
        f["fel-hover"] = mix(f["fel"], f["text"], 0.15)
        f["fel-tryck"] = mix(f["fel-hover"], "#000000", 0.18)
        self.h = T["hojd"][namn]

    def __getitem__(self, k):
        return self.f[k]


# ---------------------------------------------------------------- glyfer
# 16 x 16 u, levande yta 12 u (2 u marginal), streck 1,5 u, runda ändar.
# Ett element utan fyllning stryks; "P" är en punkt som fylls.

GLYFER = {
    "stang": ["M4.5 4.5 11.5 11.5", "M11.5 4.5 4.5 11.5"],
    "minimera": ["M4 8h8"],
    "maximera": ["R4 4 8 8 1.5"],
    "aterstall": ["R3.5 6 6.5 6.5 1.5", "M6 3.5h4.5A1.5 1.5 0 0 1 12 5v4.5"],
    "hjalp": ["M6 6.2a2 2 0 1 1 2.9 1.8c-.6.3-.9.7-.9 1.3v.5", "P8 11.8 .95"],
    "bock": ["M3.5 8.5 6.5 11.5 12.5 5"],
    "obestamd": ["M4.5 8h7"],
    "punkt": ["P8 8 3"],
    "chevron-upp": ["M4.5 9.75 8 6.25 11.5 9.75"],
    "chevron-ned": ["M4.5 6.25 8 9.75 11.5 6.25"],
    "chevron-vanster": ["M9.75 4.5 6.25 8 9.75 11.5"],
    "chevron-hoger": ["M6.25 4.5 9.75 8 6.25 11.5"],
    "pil-upp": ["M8 13V3", "M4 7l4-4 4 4"],
    "pil-ned": ["M8 3v10", "M4 9l4 4 4-4"],
    "pil-vanster": ["M13 8H3", "M7 4 3 8l4 4"],
    "pil-hoger": ["M3 8h10", "M9 4l4 4-4 4"],
    "plus": ["M8 3.5v9", "M3.5 8h9"],
    "minus": ["M3.5 8h9"],
    "sok": ["C7 7 4", "M10 10l3 3"],
    "meny": ["M3 4.5h10", "M3 8h10", "M3 11.5h10"],
    "mer": ["P3.5 8 1.1", "P8 8 1.1", "P12.5 8 1.1"],
    "storleksgrepp": ["M13 7 7 13", "M13 10.5 10.5 13"],
    "mapp": ["M2.5 4.5a1 1 0 0 1 1-1h3l1.5 1.5h4.5a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1h-9a1 1 0 0 1-1-1z"],
    "fil": ["M4 2.5h5l3 3v8H4z", "M9 2.5v3h3"],
    "info": ["C8 8 6", "M8 7.25v3.5", "P8 5.1 .95"],
    "varning": ["M8 2.75 14 13.25H2z", "M8 6.75v3", "P8 11.3 .95"],
    "fel": ["C8 8 6", "M6 6l4 4", "M10 6l-4 4"],
    "fraga": ["C8 8 6", "M6.4 6.6a1.7 1.7 0 1 1 2.4 1.6c-.5.2-.8.6-.8 1.1v.2", "P8 11.25 .9"],
}

# märket utan ring, för de fyllda signalikonerna i dialogerna
MARKEN = {
    "info": ["M8 7.25v4", "P8 4.9 1"],
    "varning": ["M8 4.5v4.25", "P8 11.4 1"],
    "fel": ["M5.75 5.75l4.5 4.5", "M10.25 5.75l-4.5 4.5"],
    "fraga": ["M6.2 6.2a1.9 1.9 0 1 1 2.7 1.8c-.6.3-.9.7-.9 1.3v.3", "P8 11.6 1"],
    "lyckat": ["M4.75 8.25 7 10.5 11.25 5.75"],
}


def glyfdelar(delar, farg):
    ut = []
    for d in delar:
        k, rest = d[0], d[1:]
        if k == "P":
            cx, cy, r = rest.split()
            ut.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{farg}" stroke="none"/>')
        elif k == "C":
            cx, cy, r = rest.split()
            ut.append(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>')
        elif k == "R":
            x, y, w, h, r = rest.split()
            ut.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/>')
        else:
            ut.append(f'<path d="{d}"/>')
    return "".join(ut)


def glyf(namn, x, y, storlek, farg, streck=1.5, delar=None):
    """glyfen namn med övre vänstra hörnet i x, y och storleken storlek u"""
    s = storlek / 16
    d = delar if delar is not None else GLYFER[namn]
    return (f'<g transform="translate({fmt(x)} {fmt(y)}) scale({fmt(s)})" fill="none" '
            f'stroke="{farg}" stroke-width="{fmt(streck)}" stroke-linecap="round" '
            f'stroke-linejoin="round">{glyfdelar(d, farg)}</g>')


# ---------------------------------------------------------------- SVG


def fmt(v):
    if isinstance(v, float):
        v = round(v, 3)
        if v == int(v):
            return str(int(v))
        return ("%.3f" % v).rstrip("0").rstrip(".")
    return str(v)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def dokument(w, h, titel, kropp, defs=""):
    d = f"<defs>{defs}</defs>" if defs else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{fmt(w)}" height="{fmt(h)}" '
            f'viewBox="0 0 {fmt(w)} {fmt(h)}" role="img" aria-label="{esc(titel)}">'
            f"<title>{esc(titel)}</title>{d}{kropp}</svg>\n")


def rekt(x, y, w, h, r, fyll="none", kant=None, kb=1, extra=""):
    """en rektangel; kanten ligger innanför (x, y, w, h) som i libgdi"""
    if kant:
        o = kb / 2
        return (f'<rect x="{fmt(x + o)}" y="{fmt(y + o)}" width="{fmt(w - kb)}" '
                f'height="{fmt(h - kb)}" rx="{fmt(max(0, r - o))}" fill="{fyll}" '
                f'stroke="{kant}" stroke-width="{fmt(kb)}"{extra}/>')
    return (f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" '
            f'rx="{fmt(r)}" fill="{fyll}"{extra}/>')


def ring(t, x, y, w, h, r):
    """fokusringen: 2 u bred, 2 u utanför kanten"""
    a, b = M["fokusavstand"], M["fokusring"]
    o = a + b / 2
    return (f'<rect x="{fmt(x - o)}" y="{fmt(y - o)}" width="{fmt(w + 2 * o)}" '
            f'height="{fmt(h + 2 * o)}" rx="{fmt(r + o)}" fill="none" '
            f'stroke="{t["fokus"]}" stroke-width="{fmt(b)}"/>')


def inre_ring(t, x, y, w, h, r):
    """fokusringen innanför, för rader i listor där grannarna ligger kant i kant"""
    b = M["fokusring"]
    return rekt(x, y, w, h, r, "none", t["fokus"], b)


def text(x, y, s, stil, farg, anchor="start", vikt=None, storlek=None):
    st = TYP[stil]
    return (f'<text x="{fmt(x)}" y="{fmt(y)}" font-family="{FONT}" '
            f'font-size="{storlek or st["storlek"]}" font-weight="{vikt or st["vikt"]}" '
            f'fill="{farg}" text-anchor="{anchor}" dominant-baseline="central">{esc(s)}</text>')


def textbredd(s, stil, storlek=None):
    """en uppskattning; i libui mäter gdi_textextent"""
    st = TYP[stil]
    return len(s) * (storlek or st["storlek"]) * 0.58


def skugga(t, niva, fid):
    h = t.h[str(niva)]
    return (f'<filter id="{fid}" x="-30%" y="-30%" width="160%" height="190%">'
            f'<feDropShadow dx="0" dy="{h["y"]}" stdDeviation="{fmt(h["oskarpa"] / 2)}" '
            f'flood-color="{t["skugga"]}" flood-opacity="{h["alfa"]}"/></filter>')


# ---------------------------------------------------------------- delar
# Varje funktion ritar en komponent med övre vänstra hörnet i (x, y) och
# returnerar SVG-kroppen. Filerna läggs med 4 u marginal för fokusringen.

LAGEN = ("vila", "hover", "tryck", "fokus", "inaktiv")


def knapp(t, x, y, typ, lage, etikett, w=None):
    h = M["kontroll-h"]
    w = w or max(M["knapp-min-b"], round(textbredd(etikett, "knapp")) + 2 * M["knapp-utfyllnad-x"])
    r = R["kontroll"]
    kant = None
    if lage == "inaktiv":
        bg, fg = t["yta-inaktiv"], t["text-inaktiv"]
        if typ == "kontur":
            bg, kant = "none", t["kant"]
    elif typ == "primar":
        bg = {"hover": t["accent-hover"], "tryck": t["accent-tryck"]}.get(lage, t["accent"])
        fg = t["pa-accent"]
    elif typ == "sekundar":
        bg = {"hover": t["knapp-hover"], "tryck": t["knapp-tryck"]}.get(lage, t["knapp"])
        fg = t["text"]
    elif typ == "kontur":
        bg = {"hover": t["yta-hover"], "tryck": t["yta-tryck"]}.get(lage, "none")
        kant = {"hover": t["kant-kontroll-hover"]}.get(lage, t["kant-kontroll"])
        fg = t["text"]
    elif typ == "fara":
        bg = {"hover": t["fel-hover"], "tryck": t["fel-tryck"]}.get(lage, t["fel"])
        fg = t["pa-fel"]
    s = rekt(x, y, w, h, r, bg, kant)
    vikt = 700 if typ in ("primar", "fara") else 600
    s += text(x + w / 2, y + h / 2, etikett, "knapp", fg, "middle", vikt)
    if lage == "fokus":
        s += ring(t, x, y, w, h, r)
    return s, w


def kryssruta(t, x, y, varde, lage, etikett="Alternativ"):
    n, r = M["kryssruta"], R["liten"]
    inaktiv = lage == "inaktiv"
    if varde == "av":
        fyll = t["yta-inaktiv"] if inaktiv else t["falt"]
        kant = t["kant"] if inaktiv else (t["kant-kontroll-hover"] if lage == "hover" else t["kant-kontroll"])
        s = rekt(x, y, n, n, r, fyll, kant)
    else:
        if inaktiv:
            s = rekt(x, y, n, n, r, t["yta-inaktiv"], t["kant"])
            fg = t["text-inaktiv"]
        else:
            s = rekt(x, y, n, n, r, t["accent-hover"] if lage == "hover" else t["accent"])
            fg = t["pa-accent"]
        s += glyf("bock" if varde == "pa" else "obestamd", x + 1, y + 1, 16, fg, 2)
    if lage == "fokus":
        s += ring(t, x, y, n, n, r)
    s += text(x + n + M["etikett-avstand"], y + n / 2, etikett, "brod",
              t["text-inaktiv"] if inaktiv else t["text"])
    return s


def radioknapp(t, x, y, varde, lage, etikett="Alternativ"):
    n = M["radioknapp"]
    c = n / 2
    inaktiv = lage == "inaktiv"
    if varde == "av":
        fyll = t["yta-inaktiv"] if inaktiv else t["falt"]
        kant = t["kant"] if inaktiv else (t["kant-kontroll-hover"] if lage == "hover" else t["kant-kontroll"])
        s = f'<circle cx="{fmt(x + c)}" cy="{fmt(y + c)}" r="{fmt(c - .5)}" fill="{fyll}" stroke="{kant}"/>'
    else:
        if inaktiv:
            s = f'<circle cx="{fmt(x + c)}" cy="{fmt(y + c)}" r="{fmt(c - .5)}" fill="{t["yta-inaktiv"]}" stroke="{t["kant"]}"/>'
            p = t["text-inaktiv"]
        else:
            f = t["accent-hover"] if lage == "hover" else t["accent"]
            s = f'<circle cx="{fmt(x + c)}" cy="{fmt(y + c)}" r="{fmt(c)}" fill="{f}"/>'
            p = t["pa-accent"]
        s += f'<circle cx="{fmt(x + c)}" cy="{fmt(y + c)}" r="3.5" fill="{p}"/>'
    if lage == "fokus":
        s += ring(t, x, y, n, n, c)
    s += text(x + n + M["etikett-avstand"], y + c, etikett, "brod",
              t["text-inaktiv"] if inaktiv else t["text"])
    return s


def vaxel(t, x, y, varde, lage, etikett="Alternativ"):
    w, h, k = M["vaxel-b"], M["vaxel-h"], M["vaxel-knopp"]
    r = h / 2
    inaktiv = lage == "inaktiv"
    if inaktiv:
        s = rekt(x, y, w, h, r, t["yta-inaktiv"], t["kant"])
        kf = t["text-inaktiv"]
    elif varde == "pa":
        s = rekt(x, y, w, h, r, t["accent-hover"] if lage == "hover" else t["accent"])
        kf = t["pa-accent"]
    else:
        s = rekt(x, y, w, h, r, t["falt"],
                 t["kant-kontroll-hover"] if lage == "hover" else t["kant-kontroll"])
        kf = t["text"] if lage == "hover" else t["text-dampad"]
    cx = x + w - r if varde == "pa" else x + r
    s += f'<circle cx="{fmt(cx)}" cy="{fmt(y + r)}" r="{fmt(k / 2)}" fill="{kf}"/>'
    if lage == "fokus":
        s += ring(t, x, y, w, h, r)
    s += text(x + w + M["etikett-avstand"] + 2, y + r, etikett, "brod",
              t["text-inaktiv"] if inaktiv else t["text"])
    return s


def falt(t, x, y, lage, w=200, varde=None, platshallare="Platshållare", slut=None):
    h, r, px = M["kontroll-h"], R["kontroll"], M["falt-utfyllnad-x"]
    inaktiv = lage == "inaktiv"
    fyll = t["yta-inaktiv"] if inaktiv else t["falt"]
    kant = {"hover": t["kant-kontroll-hover"], "fokus": t["fokus"], "fel": t["fel"],
            "inaktiv": t["kant"], "oppen": t["fokus"]}.get(lage, t["kant-kontroll"])
    s = rekt(x, y, w, h, r, fyll, kant)
    if varde:
        s += text(x + px, y + h / 2, varde, "brod", t["text-inaktiv"] if inaktiv else t["text"])
        if lage == "fokus" and not slut:
            cx = x + px + textbredd(varde, "brod") + 2
            s += rekt(cx, y + 8, 1.5, h - 16, 0, t["text"])
    else:
        s += text(x + px, y + h / 2, platshallare, "brod",
                  t["text-inaktiv"] if inaktiv else t["text-dampad"])
    if lage == "fel":
        s += glyf("fel", x + w - px - 16, y + 8, 16, t["fel"])
    if slut:
        s += glyf(slut, x + w - px - 16, y + 8, 16,
                  t["text-inaktiv"] if inaktiv else t["text-dampad"])
    if lage in ("fokus", "oppen"):
        s += ring(t, x, y, w, h, r)
    return s


def popup(t, x, y, w, objekt, fid):
    """en meny eller en uppfälld lista; objekt är (typ, text, kortkommando)"""
    p, oh = M["meny-utfyllnad"], M["menyobjekt-h"]
    h = 2 * p
    for o in objekt:
        h += 9 if o[0] == "avskiljare" else oh
    s = rekt(x, y, w, h, R["yta"], t["yta-upphojd"], t["kant"], extra=f' filter="url(#{fid})"')
    cy = y + p
    for o in objekt:
        typ = o[0]
        if typ == "avskiljare":
            s += rekt(x + p + 6, cy + 4, w - 2 * p - 12, 1, 0, t["kant"])
            cy += 9
            continue
        etikett, kort = o[1], (o[2] if len(o) > 2 else "")
        fg, fk = t["text"], t["text-dampad"]
        if typ == "hover":
            s += rekt(x + p, cy, w - 2 * p, oh, 6, t["accent"])
            fg = fk = t["pa-accent"]
        elif typ == "vald":
            s += rekt(x + p, cy, w - 2 * p, oh, 6, t["markering"])
            fg = t["markering-text"]
        elif typ == "inaktiv":
            fg = fk = t["text-inaktiv"]
        elif typ == "fara":
            fg = fk = t["fel"]
        if typ in ("bock", "vald"):
            s += glyf("bock", x + p + 6, cy + 7, 16, fg)
        if typ == "radio":
            s += glyf("punkt", x + p + 8, cy + 9, 12, fg)
        s += text(x + p + 32, cy + oh / 2, etikett, "brod", fg)
        if typ == "undermeny":
            s += glyf("chevron-hoger", x + w - p - 22, cy + 7, 16, fk)
        elif kort:
            s += text(x + w - p - 10, cy + oh / 2, kort, "brod", fk, "end", 500, 13)
        cy += oh
    return s, h


def listrad(t, x, y, lage, etikett="Dokument", w=240, niva=0, oppen=None, ikon="mapp"):
    h = M["listrad-h"]
    s = ""
    fg, ik = t["text"], t["ikon"]
    if lage == "hover":
        s += rekt(x, y, w, h, 6, t["yta-hover"])
    elif lage in ("vald", "vald-fokus"):
        s += rekt(x, y, w, h, 6, t["markering"])
        fg = t["markering-text"]
    elif lage == "inaktiv":
        fg = ik = t["text-inaktiv"]
    if lage == "vald-fokus":
        s += inre_ring(t, x, y, w, h, 6)
    ix = x + 8 + niva * M["trad-indrag"]
    if oppen == "lov":
        ix += 20  # ett löv i ett träd: ingen pil, men ikonen i linje med syskonens
    elif oppen is not None:
        s += glyf("chevron-ned" if oppen else "chevron-hoger", ix, y + 6, 16, t["text-dampad"])
        ix += 20
    s += glyf(ikon, ix, y + 6, 16, ik)
    s += text(ix + 24, y + h / 2, etikett, "brod", fg)
    return s


# ---------------------------------------------------------------- filerna


def komponenter(t):
    """(sökväg, titel, w, h, kropp, defs) för alla filer i temat t"""
    ut = []
    m = 4

    def fil(sok, titel, w, h, kropp, defs=""):
        ut.append((sok, titel, w, h, kropp, defs))

    # knappar
    for typ, etikett in (("primar", "Spara"), ("sekundar", "Avbryt"),
                         ("kontur", "Exportera"), ("fara", "Radera")):
        for lage in LAGEN:
            k, w = knapp(t, m, m, typ, lage, etikett, 104)
            fil(f"knapp/{typ}-{lage}", f"Knapp, {typ}, {lage}", w + 2 * m, M["kontroll-h"] + 2 * m, k)

    # kryssruta, radioknapp, växel
    for varde in ("av", "pa", "obestamd"):
        for lage in ("vila", "hover", "fokus", "inaktiv"):
            fil(f"kryssruta/{varde}-{lage}", f"Kryssruta, {varde}, {lage}", 128, M["kryssruta"] + 2 * m,
                kryssruta(t, m, m, varde, lage))
    for varde in ("av", "pa"):
        for lage in ("vila", "hover", "fokus", "inaktiv"):
            fil(f"radioknapp/{varde}-{lage}", f"Radioknapp, {varde}, {lage}", 128, M["radioknapp"] + 2 * m,
                radioknapp(t, m, m, varde, lage))
            fil(f"vaxel/{varde}-{lage}", f"Växel, {varde}, {lage}", 150, M["vaxel-h"] + 2 * m,
                vaxel(t, m, m, varde, lage))

    # textfält
    for lage, varde in (("vila", None), ("hover", None), ("fokus", "Värde"),
                        ("fel", "kort"), ("inaktiv", None)):
        fil(f"textfalt/{lage}", f"Textfält, {lage}", 208, M["kontroll-h"] + 2 * m,
            falt(t, m, m, lage, varde=varde))
    fil("textfalt/sok", "Sökfält", 208, M["kontroll-h"] + 2 * m,
        falt(t, m, m, "vila", platshallare="Sök", slut="sok"))

    # kombinationsruta
    for lage in ("vila", "hover", "fokus", "inaktiv"):
        fil(f"kombinationsruta/{lage}", f"Kombinationsruta, {lage}", 208, M["kontroll-h"] + 2 * m,
            falt(t, m, m, lage, varde="Detaljer", slut="chevron-ned"))
    lista = [("normal", "Ikoner"), ("hover", "Lista"), ("vald", "Detaljer")]
    pk, ph = popup(t, m, m + M["kontroll-h"] + 4, 200, lista, "s2")
    fil("kombinationsruta/oppen", "Kombinationsruta, öppen", 208 + 2 * 12,
        m + M["kontroll-h"] + 4 + ph + 32,
        falt(t, m, m, "oppen", varde="Detaljer", slut="chevron-upp") + pk, skugga(t, 1, "s2"))

    # upp/ned
    for lage in ("vila", "fokus", "hover-upp"):
        s = falt(t, m, m, "fokus" if lage == "fokus" else "vila", w=104, varde="15")
        bx = m + 104 - 30
        if lage == "hover-upp":
            s += rekt(bx, m + 3, 26, 13, 4, t["yta-hover"])
        s += glyf("chevron-upp", bx + 7, m + 3.5, 12, t["text-dampad"])
        s += glyf("chevron-ned", bx + 7, m + 16.5, 12, t["text-dampad"])
        fil(f"uppned/{lage}", f"Upp/ned, {lage}", 112, M["kontroll-h"] + 2 * m, s)

    # rullningslist
    rb, lh = M["rullningslist-b"], 160
    for lage in ("vila", "hover", "drag"):
        if lage == "vila":
            tb = M["rullningslist-tumme-vila"]
            s = rekt(rb - tb - 2, 40, tb, 60, tb / 2, t["tumme"])
        else:
            tb = M["rullningslist-tumme-hover"]
            s = rekt(0, 0, rb, lh, rb / 2, t["yta-sankt"])
            s += rekt((rb - tb) / 2, 40, tb, 60, tb / 2,
                      t["tumme-hover"] if lage == "drag" else t["tumme"])
        fil(f"rullningslist/lodrat-{lage}", f"Rullningslist, lodrät, {lage}", rb, lh,
            rekt(0, 0, rb, lh, 0, t["yta"]) + s)
        # vågrät: samma mått vridna
        if lage == "vila":
            s2 = rekt(40, rb - tb - 2, 60, tb, tb / 2, t["tumme"])
        else:
            s2 = rekt(0, 0, lh, rb, rb / 2, t["yta-sankt"])
            s2 += rekt(40, (rb - tb) / 2, 60, tb, tb / 2,
                       t["tumme-hover"] if lage == "drag" else t["tumme"])
        fil(f"rullningslist/vagrat-{lage}", f"Rullningslist, vågrät, {lage}", lh, rb,
            rekt(0, 0, lh, rb, 0, t["yta"]) + s2)

    # meny
    objekt = [("normal", "Öppna", "Enter"), ("hover", "Byt namn", "F2"),
              ("normal", "Kopiera", "Ctrl+C"), ("inaktiv", "Klistra in", "Ctrl+V"),
              ("avskiljare",), ("bock", "Visa dolda filer", "Ctrl+H"),
              ("radio", "Rutnät", ""), ("undermeny", "Sortera efter", ""),
              ("avskiljare",), ("fara", "Flytta till papperskorgen", "Del")]
    pk, ph = popup(t, 16, 8, 280, objekt, "s2")
    fil("meny/popup", "Popupmeny", 312, ph + 40, pk, skugga(t, 2, "s2"))
    for typ, namn in (("normal", "vila"), ("hover", "hover"), ("bock", "bock"),
                      ("radio", "radio"), ("undermeny", "undermeny"), ("inaktiv", "inaktiv"),
                      ("fara", "fara")):
        o = [(typ, "Menyobjekt", "" if typ in ("undermeny", "radio") else "Ctrl+K")]
        pk, ph = popup(t, 0, 0, 240, o, "x")
        # ett objekt för sig: menyns yta utan menyns ram
        pk = re.sub(r"^<rect [^>]*/>", rekt(0, 0, 240, ph, 0, t["yta-upphojd"]), pk, count=1)
        fil(f"meny/objekt-{namn}", f"Menyobjekt, {namn}", 240, ph, pk)
    # menyrad
    mh = M["menyrad-h"]
    s = rekt(0, 0, 360, mh, 0, t["yta"])
    cx = 6
    for i, e in enumerate(("Arkiv", "Redigera", "Visa", "Hjälp")):
        bw = textbredd(e, "brod") + 20
        if i == 2:
            s += rekt(cx, 3, bw, mh - 6, 6, t["yta-hover"])
        s += text(cx + bw / 2, mh / 2, e, "brod", t["text"], "middle")
        cx += bw + 2
    s += rekt(0, mh - 1, 360, 1, 0, t["kant"])
    fil("meny/menyrad", "Menyrad", 360, mh, s)

    # flikar
    fh = M["flik-h"]
    for lage in ("vald", "vila", "hover", "fokus", "inaktiv"):
        w = 100
        s = rekt(0, 0, w + 8, fh + 8, 0, t["yta"])
        x0, y0 = 4, 4
        if lage == "hover":
            s += rekt(x0 + 2, y0 + 3, w - 4, fh - 6, 6, t["yta-hover"])
        fg = {"vila": t["text-dampad"], "inaktiv": t["text-inaktiv"]}.get(lage, t["text"])
        vikt = 700 if lage in ("vald", "fokus") else 500
        s += text(x0 + w / 2, y0 + fh / 2 - 1, "Allmänt", "brod", fg, "middle", vikt)
        s += rekt(x0, y0 + fh - 1, w, 1, 0, t["kant"])
        if lage in ("vald", "fokus"):
            ib = M["flik-indikator"]
            s += rekt(x0 + 14, y0 + fh - ib, w - 28, ib, ib / 2, t["accent"])
        if lage == "fokus":
            s += ring(t, x0 + 4, y0 + 4, w - 8, fh - 10, 6)
        fil(f"flik/{lage}", f"Flik, {lage}", w + 8, fh + 8, s)

    # listrader och trädrader
    for lage in ("vila", "hover", "vald", "vald-fokus", "inaktiv"):
        fil(f"listrad/{lage}", f"Listrad, {lage}", 248, M["listrad-h"] + 8,
            rekt(0, 0, 248, M["listrad-h"] + 8, 0, t["yta"]) + listrad(t, 4, 4, lage))
    for oppen in (False, True):
        namn = "expanderad" if oppen else "fallen"
        fil(f"tradrad/{namn}", f"Trädrad, {namn}", 248, M["listrad-h"] + 8,
            rekt(0, 0, 248, M["listrad-h"] + 8, 0, t["yta"]) +
            listrad(t, 4, 4, "vila", "Projekt", 240, 1, oppen))
    s = rekt(0, 0, 248, 6 * 28 + 8, 0, t["yta"])
    rader = [(0, True, "Hem", "vila", "mapp"), (1, True, "Projekt", "vald-fokus", "mapp"),
             (2, False, "qzos", "vila", "mapp"), (2, False, "design", "hover", "mapp"),
             (2, "lov", "anteckningar.md", "vila", "fil"), (1, False, "Bilder", "vila", "mapp")]
    for i, (niva, op, e, lage, ik) in enumerate(rader):
        s += listrad(t, 4, 4 + i * 28, lage, e, 240, niva, op, ik)
    fil("tradrad/exempel", "Trädvy, exempel", 248, 6 * 28 + 8, s)

    # header
    hh = M["header-h"]
    for lage in ("vila", "hover", "sorterad-upp", "sorterad-ned"):
        s = rekt(0, 0, 160, hh, 0, t["yta-hover"] if lage == "hover" else t["yta"])
        aktiv = lage != "vila"
        s += text(10, hh / 2, "Namn", "etikett", t["text"] if aktiv else t["text-dampad"])
        if lage.startswith("sorterad"):
            s += glyf("chevron-upp" if lage.endswith("upp") else "chevron-ned", 160 - 26, 8, 12, t["text"])
        s += rekt(159, 6, 1, hh - 12, 0, t["kant"])
        s += rekt(0, hh - 1, 160, 1, 0, t["kant"])
        fil(f"header/{lage}", f"Header, {lage}", 160, hh, s)

    # skjutreglage
    for lage in ("vila", "hover", "fokus", "inaktiv"):
        w, tr, sp = 200, M["reglage-tumme"], M["reglage-spar"]
        x0, cy = 4 + tr / 2, 4 + tr / 2
        tx = x0 + (w - tr) * 0.4
        inaktiv = lage == "inaktiv"
        s = rekt(x0, cy - sp / 2, w - tr, sp, sp / 2, t["spar"])
        s += rekt(x0, cy - sp / 2, tx - x0, sp, sp / 2, t["text-inaktiv"] if inaktiv else t["accent"])
        rr = tr / 2 + (1 if lage == "hover" else 0)
        if inaktiv:
            s += f'<circle cx="{fmt(tx)}" cy="{fmt(cy)}" r="{fmt(rr - .5)}" fill="{t["yta-inaktiv"]}" stroke="{t["kant"]}"/>'
        else:
            s += (f'<circle cx="{fmt(tx)}" cy="{fmt(cy)}" r="{fmt(rr - .5)}" fill="{t["reglage-tumme"]}" '
                  f'stroke="{t["kant-kontroll"]}"/>')
        if lage == "fokus":
            s += ring(t, tx - tr / 2, cy - tr / 2, tr, tr, tr / 2)
        fil(f"reglage/{lage}", f"Skjutreglage, {lage}", w + 8, tr + 8, s)

    # förlopp
    fh2 = M["forlopp-h"]
    for lage in ("bestamd", "obestamd", "fel"):
        s = rekt(4, 4, 200, fh2, fh2 / 2, t["spar"])
        if lage == "obestamd":
            s += rekt(4 + 60, 4, 70, fh2, fh2 / 2, t["accent"])
        else:
            s += rekt(4, 4, 128, fh2, fh2 / 2, t["fel"] if lage == "fel" else t["accent"])
        fil(f"forlopp/{lage}", f"Förlopp, {lage}", 208, fh2 + 8, s)

    # verktygsknapp
    vk = M["verktygsknapp"]
    for lage in ("vila", "hover", "tryck", "vald", "fokus", "inaktiv"):
        s = ""
        g = t["text"]
        if lage == "hover":
            s += rekt(4, 4, vk, vk, R["kontroll"], t["yta-hover"])
        elif lage == "tryck":
            s += rekt(4, 4, vk, vk, R["kontroll"], t["yta-tryck"])
        elif lage == "vald":
            s += rekt(4, 4, vk, vk, R["kontroll"], t["markering"])
            g = t["accent-text"]
        elif lage == "inaktiv":
            g = t["text-inaktiv"]
        s += glyf("sok", 4 + (vk - 16) / 2, 4 + (vk - 16) / 2, 16, g)
        if lage == "fokus":
            s += ring(t, 4, 4, vk, vk, R["kontroll"])
        fil(f"verktygsknapp/{lage}", f"Verktygsknapp, {lage}", vk + 8, vk + 8,
            rekt(0, 0, vk + 8, vk + 8, 0, t["yta"]) + s)

    # tips
    e = "Spara (Ctrl+S)"
    tw = textbredd(e, "etikett") + 20
    s = rekt(12, 8, tw, 26, R["liten"], t["tips-bakgrund"], extra=' filter="url(#s1)"')
    s += text(12 + tw / 2, 21, e, "etikett", t["tips-text"], "middle")
    fil("tips/tips", "Verktygstips", tw + 24, 48, s, skugga(t, 1, "s1"))

    # statusrad
    sh = M["statusrad-h"]
    s = rekt(0, 0, 480, sh, 0, t["yta"]) + rekt(0, 0, 480, 1, 0, t["kant"])
    s += text(12, sh / 2, "12 objekt · 1 markerat", "etikett", t["text-dampad"], vikt=500)
    s += text(480 - 32, sh / 2, "42,3 GB ledigt", "etikett", t["text-dampad"], "end", 500)
    s += glyf("storleksgrepp", 480 - 20, sh - 18, 16, t["text-inaktiv"])
    fil("statusrad/statusrad", "Statusrad", 480, sh, s)

    # gruppram
    s = rekt(0, 0, 296, 128, 0, t["bakgrund"])
    s += text(8, 14, "Utseende", "etikett", t["text-dampad"])
    s += rekt(4, 28, 288, 96, R["yta"], t["yta"], t["kant"])
    s += kryssruta(t, 20, 44, "pa", "vila", "Animationer")
    s += vaxel(t, 20, 82, "av", "vila", "Genomskinlighet")
    fil("gruppram/gruppram", "Gruppram", 296, 128, s)

    # splitter
    for lage in ("vila", "hover", "drag"):
        b = M["splitter-greppyta"]
        s = rekt(0, 0, b, 120, 0, t["yta"])
        if lage == "vila":
            s += rekt(b / 2 - .5, 0, 1, 120, 0, t["kant"])
        else:
            s += rekt(b / 2 - 1, 0, 2, 120, 1, t["accent"] if lage == "drag" else t["kant-kontroll"])
        fil(f"splitter/{lage}", f"Splitter, {lage}", b, 120, s)

    # titelradsknappar
    th, tk = M["titelrad-h"], M["titelradsknapp"]
    for namn in ("minimera", "maximera", "aterstall", "stang"):
        for lage in ("vila", "hover", "tryck", "inaktiv"):
            s = rekt(0, 0, th, th, 0, t["titel-inaktiv"] if lage == "inaktiv" else t["yta"])
            o = (th - tk) / 2
            g = t["text"]
            if lage == "hover":
                s += rekt(o, o, tk, tk, R["kontroll"], t["accent"] if namn == "stang" else t["yta-hover"])
                if namn == "stang":
                    g = t["pa-accent"]
            elif lage == "tryck":
                s += rekt(o, o, tk, tk, R["kontroll"], t["accent-tryck"] if namn == "stang" else t["yta-tryck"])
                if namn == "stang":
                    g = t["pa-accent"]
            elif lage == "inaktiv":
                g = t["text-dampad"]
            s += glyf(namn, (th - 16) / 2, (th - 16) / 2, 16, g)
            fil(f"titelrad/{namn}-{lage}", f"Titelradsknapp, {namn}, {lage}", th, th, s)

    # fönster
    for lage in ("aktivt", "inaktivt"):
        W, H, mg = 480, 300, 48
        aktiv = lage == "aktivt"
        x0, y0 = mg, mg - 16
        fid = "s3" if aktiv else "s2"
        cid = f"klipp-{lage}"
        defs = skugga(t, 3 if aktiv else 2, fid)
        defs += f'<clipPath id="{cid}"><rect x="{x0}" y="{y0}" width="{W}" height="{H}" rx="{R["yta"]}"/></clipPath>'
        s = rekt(x0, y0, W, H, R["yta"], t["yta"], extra=f' filter="url(#{fid})"')
        s += f'<g clip-path="url(#{cid})">'
        s += rekt(x0, y0, W, th, 0, t["yta"] if aktiv else t["titel-inaktiv"])
        s += rekt(x0, y0 + th - 1, W, 1, 0, t["kant"])
        s += "</g>"
        s += rekt(x0 + 12, y0 + 10, 16, 16, 4, t["accent"] if aktiv else t["text-inaktiv"])
        s += glyf("mapp", x0 + 14, y0 + 12, 12, t["pa-accent"] if aktiv else t["titel-inaktiv"], 2)
        s += text(x0 + 36, y0 + th / 2, "Filer", "titel", t["text"] if aktiv else t["text-dampad"])
        bx = x0 + W - M["titelradsknapp-avstand"]
        for namn in ("stang", "maximera", "minimera"):
            bx -= tk
            s += glyf(namn, bx + (tk - 16) / 2, y0 + (th - 16) / 2, 16,
                      t["text"] if aktiv else t["text-dampad"])
            bx -= M["titelradsknapp-avstand"]
        s += rekt(x0, y0, W, H, R["yta"], "none",
                  t["fonster-kant-aktiv"] if aktiv else t["fonster-kant-inaktiv"])
        fil(f"fonster/{lage}", f"Fönster, {lage}", W + 2 * mg, H + 2 * mg, s, defs)

    # dialoger
    dialoger = {
        "info": ("info", "Kopieringen är klar", "214 filer kopierades till Bilder.", [("primar", "OK")]),
        "varning": ("varning", "Filen finns redan", "Vill du ersätta anteckningar.md?",
                    [("sekundar", "Avbryt"), ("primar", "Ersätt")]),
        "fel": ("fel", "Kunde inte spara", "Disken är full. Frigör utrymme och försök igen.",
                [("primar", "OK")]),
        "fraga": ("info", "Spara ändringarna?", "Ändringarna i budget.ods går annars förlorade.",
                  [("sekundar", "Avbryt"), ("sekundar", "Spara inte"), ("primar", "Spara")]),
    }
    for namn, (signal, rubrik, brod, knappar) in dialoger.items():
        W, H, mg = 420, 168, 48
        x0, y0 = mg, mg - 16
        defs = skugga(t, 3, "s3")
        s = rekt(x0, y0, W, H, R["yta"], t["yta"], t["fonster-kant-aktiv"], extra=' filter="url(#s3)"')
        s += f'<circle cx="{x0 + 24 + 16}" cy="{y0 + 24 + 16}" r="16" fill="{t[signal]}"/>'
        s += glyf(namn, x0 + 24 + 4, y0 + 24 + 4, 24, t["pa-" + signal], 2.2, MARKEN[namn])
        s += text(x0 + 72, y0 + 34, rubrik, "rubrik", t["text"])
        s += text(x0 + 72, y0 + 62, brod, "brod", t["text-dampad"])
        bx = x0 + W - 24
        for typ, e in reversed(knappar):
            bw = max(M["knapp-min-b"], round(textbredd(e, "knapp")) + 2 * M["knapp-utfyllnad-x"])
            bx -= bw
            k, _ = knapp(t, bx, y0 + H - 24 - M["kontroll-h"], typ, "vila", e, bw)
            s += k
            bx -= 8
        fil(f"dialog/{namn}", f"Dialog, {namn}", W + 2 * mg, H + 2 * mg, s, defs)

    return ut


# ---------------------------------------------------------------- CSS och DPI


def css(t):
    rader = [f"/* {t.namn}: genererad av verktyg/bygg.py ur tokens/tokens.json */",
             f':root[data-tema="{t.namn}"], .tema-{t.namn} {{']
    for k, v in T["farg"][t.namn].items():
        rader.append(f"  --{k}: {v};")
    for k, v in M.items():
        rader.append(f"  --matt-{k}: calc({v} * var(--u, 1px));")
    for k, v in R.items():
        rader.append(f"  --radie-{k}: calc({v} * var(--u, 1px));")
    for n, h in t.h.items():
        rader.append(f"  --hojd-{n}: 0 calc({h['y']} * var(--u, 1px)) calc({h['oskarpa']} * var(--u, 1px)) "
                     f"rgb({' '.join(str(c) for c in hexrgb(t['skugga']))} / {h['alfa']});")
    for k, v in T["rorelse"].items():
        if isinstance(v, (int, float)):
            rader.append(f"  --rorelse-{k}: {v}ms;")
    rader.append("}")
    return "\n".join(rader) + "\n"


def rund(v):
    return int(math.floor(v + 0.5))


def dpi_md():
    sk = T["enhet"]["skalor"]
    huvud = "| Mått | u | " + " | ".join(f"{int(s * 100)} %" for s in sk) + " |"
    linje = "|---|---:|" + "---:|" * len(sk)
    rader = ["# Måtten i bildpunkter", "",
             "Genererad av `verktyg/bygg.py` ur `tokens/tokens.json`. Regeln står i",
             "`mal.md`: storlekar `round(u × s)`, kanter `max(1, floor(u × s))`.", "",
             "## Storlekar", "", huvud, linje]
    kanter = ("kant", "fokusring")
    for k, v in list(M.items()) + [("radie-" + k, v) for k, v in R.items() if k != "pill"]:
        if k in kanter:
            continue
        rader.append(f"| {k} | {v} | " + " | ".join(str(rund(v * s)) for s in sk) + " |")
    rader += ["", "## Kanter", "", huvud, linje]
    for k in kanter:
        v = M[k]
        rader.append(f"| {k} | {v} | " + " | ".join(str(max(1, math.floor(v * s))) for s in sk) + " |")
    rader += ["", "## Glyfstreck", "", huvud, linje,
              "| glyfstreck | 1.5 | " + " | ".join(fmt(round(1.5 * s * 2) / 2) for s in sk) + " |"]
    rader += ["", "## Text", "", huvud, linje]
    for k, st in TYP.items():
        rader.append(f"| {k} | {st['storlek']} | " + " | ".join(str(rund(st['storlek'] * s)) for s in sk) + " |")
    return "\n".join(rader) + "\n"


# ---------------------------------------------------------------- main


def main():
    svg = ROT / "svg"
    if svg.exists():
        shutil.rmtree(svg)
    (svg / "glyfer").mkdir(parents=True)
    for namn, delar in GLYFER.items():
        kropp = (f'<g fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
                 f'stroke-linejoin="round">{glyfdelar(delar, "currentColor")}</g>')
        (svg / "glyfer" / f"{namn}.svg").write_text(dokument(16, 16, namn, kropp), encoding="utf-8")
    antal = len(GLYFER)
    for tn in TEMAN:
        t = Tema(tn)
        for sok, titel, w, h, kropp, defs in komponenter(t):
            p = svg / tn / f"{sok}.svg"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(dokument(w, h, titel, kropp, defs), encoding="utf-8")
            antal += 1
        (ROT / "tokens" / f"{tn}.css").write_text(css(t), encoding="utf-8")
    (ROT / "docs").mkdir(exist_ok=True)
    (ROT / "docs" / "dpi.md").write_text(dpi_md(), encoding="utf-8")
    print(f"{antal} SVG-filer, {len(TEMAN)} CSS-filer och docs/dpi.md")


if __name__ == "__main__":
    main()
