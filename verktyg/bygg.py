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
    # skalet och programmen
    "terminal": ["M3.5 5l3 3-3 3", "M8.5 11h4"],
    "webb": ["C8 8 6", "M2 8h12", "M8 2c-1.9 1.7-2.6 3.9-2.6 6s.7 4.3 2.6 6c1.9-1.7 2.6-3.9 2.6-6S9.9 3.7 8 2z"],
    "reglage": ["M2.5 4.5h6.5", "C10.5 4.5 1.5", "M12 4.5h1.5", "M2.5 11.5h1.5", "C5.5 11.5 1.5", "M7 11.5h6.5"],
    "text": ["M4 2.5h5l3 3v8H4z", "M9 2.5v3h3", "M6 8.5h4", "M6 11h3"],
    "kalkylator": ["R3.5 2.5 9 11 1.5", "M5.75 5h4.5", "P6 8 .8", "P8 8 .8", "P10 8 .8", "P6 10.75 .8", "P8 10.75 .8", "P10 10.75 .8"],
    "bild": ["R2.5 3.5 11 9 1.5", "P6 6.5 1", "M13.5 10.5l-3-3-6 5"],
    "pensel": ["M10 3l3 3-6.5 6.5H3.5V9.5z", "M8.5 4.5l3 3"],
    "palett": ["M8 2.5a5.5 5.5 0 1 0 0 11c1 0 1.5-.6 1.5-1.3 0-.9-.8-1.2-.8-2s.6-1.2 1.5-1.2h1.3c1.2 0 2-.9 2-2 0-2.5-2.5-4.5-5.5-4.5z",
               "P5 7.25 .8", "P7.25 5 .8", "P10.25 5.5 .8"],
    "lista": ["M6 4.5h7", "M6 8h7", "M6 11.5h7", "P3.25 4.5 .8", "P3.25 8 .8", "P3.25 11.5 .8"],
    "kalender": ["R2.5 3.5 11 10 1.5", "M2.5 6.75h11", "M5.5 2v3", "M10.5 2v3"],
    "musik": ["M6 12V4.25l7-1.5v8", "C4.5 12 1.5", "C11.5 10.75 1.5"],
    "strom": ["M8 2.5v5.25", "M4.6 4.6a5 5 0 1 0 6.8 0"],
    "anvandare": ["C8 5.5 2.5", "M3 13.5c.8-2.6 2.7-4 5-4s4.2 1.4 5 4"],
    "wifi": ["M2 6.5a9 9 0 0 1 12 0", "M4.25 9a5.8 5.8 0 0 1 7.5 0", "P8 12 1.1"],
    "volym": ["M2.5 6.25h2.5l3.5-3v9.5l-3.5-3H2.5z", "M11 6a3 3 0 0 1 0 4", "M12.75 4.25a5.5 5.5 0 0 1 0 7.5"],
    "batteri": ["R1.5 4.75 11.5 6.5 1.75", "M14.5 7v2", "F3.25 6.5 6 3 .5"],
    "bluetooth": ["M4.5 5l6.5 6-3 2.5v-11l3 2.5-6.5 6"],
    "mane": ["M13 9.5A5.5 5.5 0 1 1 6.5 3a4.5 4.5 0 0 0 6.5 6.5z"],
    "fokus": ["C8 8 5.5", "C8 8 2"],
    "flygplan": ["M8 2c.7 0 1.1.6 1.1 1.4v3l4.4 2.6v1.5L9.1 9.2v2.3l1.4 1.1v1.2L8 13.1l-2.5.7v-1.2l1.4-1.1V9.2l-4.4 1.3V9l4.4-2.6v-3C6.9 2.6 7.3 2 8 2z"],
    "sol": ["C8 8 2.75", "M8 1.75v1.5", "M8 12.75v1.5", "M1.75 8h1.5", "M12.75 8h1.5",
            "M3.6 3.6l1 1", "M11.4 11.4l1 1", "M3.6 12.4l1-1", "M11.4 4.6l1-1"],
    "klocka": ["C8 8 5.5", "M8 5v3l2 1.5"],
    "las": ["R3.5 7 9 6.5 1.5", "M5.5 7V5a2.5 2.5 0 0 1 5 0v2"],
    "logga-ut": ["M6.5 13.5H4A1.5 1.5 0 0 1 2.5 12V4A1.5 1.5 0 0 1 4 2.5h2.5", "M10 5l3 3-3 3", "M13 8H6.5"],
    "starta-om": ["M13 8a5 5 0 1 1-1.5-3.55", "M11.75 2v2.75H9"],
    "avisering": ["M4 11.25V7a4 4 0 0 1 8 0v4.25l1 1.25H3z", "M6.5 14.25h3"],
    "rutnat": ["R2.5 2.5 4.5 4.5 1.25", "R9 2.5 4.5 4.5 1.25", "R2.5 9 4.5 4.5 1.25", "R9 9 4.5 4.5 1.25"],
    "skrivbord": ["R2 3 12 8 1.5", "M5.5 13.5h5", "M8 11v2.5"],
    "papperskorg": ["M3 4.5h10", "M6.5 4.5V3h3v1.5", "M4.5 4.5l.7 8.6a1 1 0 0 0 1 .9h3.6a1 1 0 0 0 1-.9l.7-8.6"],
    "kor": ["R2.5 2.5 11 11 2", "M6.5 5.5 9 8l-2.5 2.5"],
    "nal": ["M9.5 2.5l4 4", "M11.5 4.5 8 8", "M10 2.5 6.5 6 4 6.5l5.5 5.5.5-2.5 3.5-3.5", "M6.75 9.25 3 13"],
    # verktygsfältet: comctl32:s standardbilder (STD_*) och File Managers
    "klipp-ut": ["C5 11.5 2", "C11 11.5 2", "M6.25 9.9 11.5 2.5", "M9.75 9.9 4.5 2.5"],
    "kopiera": ["R5.5 5.5 8 8 1.5", "M2.5 10.5V4A1.5 1.5 0 0 1 4 2.5h6.5"],
    "klistra-in": ["M6 3H4.5A1 1 0 0 0 3.5 4v9a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1H10", "R6 2 4 2.5 .75"],
    "angra": ["M3.5 6.5h6a3.5 3.5 0 0 1 0 7H7", "M6 4 3.5 6.5 6 9"],
    "gor-om": ["M12.5 6.5h-6a3.5 3.5 0 0 0 0 7H9", "M10 4l2.5 2.5L10 9"],
    "ny-fil": ["M9 2.5H4v11h8V5.5z", "M9 2.5v3h3", "M8 7.5v4", "M6 9.5h4"],
    "oppna": ["M2.5 12.5v-8a1 1 0 0 1 1-1h3L8 5h4a1 1 0 0 1 1 1v1.5", "M2.5 12.5 4.5 7.5h9.5l-2 5z"],
    "spara": ["M2.5 3.5a1 1 0 0 1 1-1h7l3 3v7a1 1 0 0 1-1 1h-9a1 1 0 0 1-1-1z", "M5.5 2.5v3h4v-3", "M5 13.5V10h6v3.5"],
    "skriv-ut": ["M4.5 6V2.5h7V6", "M4.5 11.5h-1a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v3.5a1 1 0 0 1-1 1h-1", "M4.5 9.5h7v4h-7z"],
    "forhandsgranska": ["M7 13.5H4v-11h5l3 3v1.5", "M9 2.5v3h3", "C9.75 10.25 2", "M11.25 11.75 13.5 14"],
    "ersatt": ["M3 5.5h8", "M9 3l2.5 2.5L9 8", "M13 10.5H5", "M7 8l-2.5 2.5L7 13"],
    "detaljer": ["R2.5 3 11 10 1.5", "M2.5 6.5h11", "M2.5 9.75h11", "M6.5 3v10"],
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
        elif k == "F":
            x, y, w, h, r = rest.split()
            ut.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{farg}" stroke="none"/>')
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
        if len(o) > 3 and o[3]:
            s += glyf(o[3], x + p + 8, cy + 7, 16,
                      fg if typ in ("hover", "fara", "inaktiv") else t["text-dampad"])
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

    # skjutreglage med bockar under knappens band, i kant-kontroll
    w, tr, sp = 200, M["reglage-tumme"], M["reglage-spar"]
    bl, ba = M["reglage-bock"], M["reglage-bock-avstand"]
    x0, cy = 4 + tr / 2, 4 + tr / 2
    tx = x0 + (w - tr) * 0.4
    s = rekt(x0, cy - sp / 2, w - tr, sp, sp / 2, t["spar"])
    s += rekt(x0, cy - sp / 2, tx - x0, sp, sp / 2, t["accent"])
    for i in range(11):
        s += rekt(round(x0 + (w - tr) * i / 10 - .5), cy + tr / 2 + ba, M["kant"], bl, 0, t["kant-kontroll"])
    s += (f'<circle cx="{fmt(tx)}" cy="{fmt(cy)}" r="{fmt(tr / 2 - .5)}" fill="{t["reglage-tumme"]}" '
          f'stroke="{t["kant-kontroll"]}"/>')
    fil("reglage/bockar", "Skjutreglage med bockar", w + 8, tr + ba + bl + 8, s)

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
            # fyllningen ensam har för lite kontrast mot ytan; ramen visar läget utan färg (princip 4)
            s += rekt(4, 4, vk, vk, R["kontroll"], t["markering"], t["kant-kontroll"])
            g = t["markering-text"]
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


# ---------------------------------------------------------------- skalet
# Programikonerna är desamma i båda temana: en rundad ruta i en lutning
# och glyfen ovanpå. Namnen är programmen i generic_gdi/examples.

APPAR = {
    "filer": ("Filer", "#FFC27A", "#FF9F4A", "mapp", "#3A2410"),
    "terminal": ("Terminal", "#3A2B44", "#1B1426", "terminal", "#FFA85D"),
    "text": ("Anteckningar", "#FFFFFF", "#E8DEE7", "text", "#523E5D"),
    "kalkylator": ("Kalkylator", "#7A6688", "#523E5D", "kalkylator", "#F3F0F5"),
    "bilder": ("Bilder", "#B9C6FF", "#8C9EF5", "bild", "#1F2A5C"),
    "rita": ("Rita", "#F7A08F", "#EE7665", "pensel", "#3A1610"),
    "farger": ("Färger", "#A8E2C2", "#6FC49A", "palett", "#103A26"),
    "loggar": ("Loggar", "#6A5676", "#42314C", "lista", "#E3D8E2"),
    "installningar": ("Inställningar", "#D4CBDC", "#A898B4", "reglage", "#241B32"),
    "webb": ("Webb", "#5B74D6", "#3B53B3", "webb", "#FFFFFF"),
    "kalender": ("Kalender", "#FFFFFF", "#EFE7EE", "kalender", "#DB6452"),
    "musik": ("Musik", "#FFA85D", "#EE7665", "musik", "#3A1610"),
}

_id = [0]


def nytt_id(prefix):
    _id[0] += 1
    return f"{prefix}{_id[0]}"


def appikon(namn, x, y, s):
    """programikonen namn, s u stor; returnerar (kropp, defs)"""
    _, a, b, g, gf = APPAR[namn]
    gid = nytt_id("ag")
    defs = (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>')
    r = s * 0.27
    k = rekt(x, y, s, s, r, f"url(#{gid})")
    k += (f'<rect x="{fmt(x + .5)}" y="{fmt(y + .5)}" width="{fmt(s - 1)}" height="{fmt(s - 1)}" '
          f'rx="{fmt(r - .5)}" fill="none" stroke="#241B32" stroke-opacity=".14"/>')
    gs = s * 0.56
    k += glyf(g, x + (s - gs) / 2, y + (s - gs) / 2, gs, gf, 1.75)
    return k, defs


def logo(x, y, s, fyll=None):
    """QzOS-märket: en sol vid horisonten; returnerar (kropp, defs)"""
    gid, mid = nytt_id("lg"), nytt_id("lm")
    cx, cy, r = x + s / 2, y + s * 0.56, s * 0.40
    defs = (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="#FFA85D"/><stop offset="1" stop-color="#EE7665"/></linearGradient>'
            f'<mask id="{mid}"><rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(s)}" height="{fmt(s)}" fill="#fff"/>'
            f'<rect x="{fmt(x)}" y="{fmt(cy + s * .02)}" width="{fmt(s)}" height="{fmt(s * .07)}" fill="#000"/>'
            f'<rect x="{fmt(x)}" y="{fmt(cy + s * .16)}" width="{fmt(s)}" height="{fmt(s * .09)}" fill="#000"/>'
            f'<rect x="{fmt(x)}" y="{fmt(cy + s * .33)}" width="{fmt(s)}" height="{fmt(s)}" fill="#000"/></mask>')
    k = (f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" fill="{fyll or f"url(#{gid})"}" '
         f'mask="url(#{mid})"/>')
    return k, defs


def bakgrund(tema, w=1920, h=1080):
    """bakgrundsbilden Dyner"""
    if tema == "glod":
        himmel = ("#1F1730", "#3A2443", "#5A2F4C")
        sol = ("#FFA85D", "#EE7665", 0.9)
        dyner = [("#6B3456", "#4E2A49"), ("#B24C61", "#7C3A57"), ("#E9735F", "#C2515E"),
                 ("#F59A62", "#E36F5A"), ("#FFBE7A", "#F2925F")]
    else:
        himmel = ("#FBF4F2", "#F7E6E6", "#F3D6D8")
        sol = ("#FFC791", "#F7957F", 0.85)
        dyner = [("#EBC6CF", "#DDB2C0"), ("#F2B2A8", "#E39A98"), ("#F7A68C", "#EE8C7C"),
                 ("#FBC08E", "#F4A07D"), ("#FFDDB0", "#FCC38F")]
    d = (f'<linearGradient id="h" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{himmel[0]}"/><stop offset=".6" stop-color="{himmel[1]}"/>'
         f'<stop offset="1" stop-color="{himmel[2]}"/></linearGradient>'
         f'<linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{sol[0]}"/>'
         f'<stop offset="1" stop-color="{sol[1]}"/></linearGradient>')
    for i, (a, b) in enumerate(dyner):
        d += (f'<linearGradient id="d{i}" x1="0" y1="0" x2=".35" y2="1"><stop offset="0" stop-color="{a}"/>'
              f'<stop offset="1" stop-color="{b}"/></linearGradient>')
    former = [
        "M0 560C260 520 420 470 640 500S1040 600 1260 560 1700 470 1920 500V1080H0Z",
        "M0 700C180 640 360 520 560 500S900 610 1080 650 1420 520 1620 470 1840 520 1920 560V1080H0Z",
        "M0 820C220 760 420 690 640 700S980 800 1240 760 1640 620 1920 640V1080H0Z",
        "M0 900C300 860 520 780 820 800S1260 900 1520 860 1800 790 1920 800V1080H0Z",
        "M0 1000C360 960 700 900 1040 930S1640 1010 1920 960V1080H0Z",
    ]
    k = f'<rect width="{w}" height="{h}" fill="url(#h)"/>'
    k += f'<circle cx="1330" cy="470" r="150" fill="url(#s)" opacity="{sol[2]}"/>'
    for i, f in enumerate(former):
        k += f'<path d="{f}" fill="url(#d{i})" transform="scale({w / 1920} {h / 1080})"/>'
    return k, d


def _halo(t):
    return t["bakgrund"]


def radbryt(s, bredd, stil="etikett", rader=2):
    """s i högst rader rader om bredd u; bryter helst vid punkt, mellanslag eller bindestreck"""
    max_tecken = max(1, int(bredd / (TYP[stil]["storlek"] * 0.58)))
    ut = []
    while s and len(ut) < rader:
        if len(s) <= max_tecken:
            ut.append(s)
            s = ""
            break
        bit = s[:max_tecken + 1]  # en brytpunkt får ligga precis efter raden
        i = max(bit.rfind(" "), bit.rfind("."), bit.rfind("-"), bit.rfind("_"))
        if i <= 0:
            i = max_tecken
        ut.append(s[:i].rstrip())
        s = s[i:].lstrip(" ")
    if s:
        ut[-1] = ut[-1][:max_tecken - 1].rstrip() + "…"
    return ut


def ikonetikett(t, cx, y, s, farg=None, bredd=80):
    """en etikett på skrivbordet, högst två rader, med en ring i bakgrundens färg"""
    ut = ""
    for i, rad in enumerate(radbryt(s, bredd)):
        ut += (f'<text x="{fmt(cx)}" y="{fmt(y + i * 15)}" font-family="{FONT}" font-size="12" '
               f'font-weight="600" fill="{farg or t["text"]}" text-anchor="middle" '
               f'dominant-baseline="central" stroke="{_halo(t)}" stroke-opacity=".55" stroke-width="3" '
               f'paint-order="stroke" stroke-linejoin="round">{esc(rad)}</text>')
    return ut


def skrivbordsikon(t, x, y, lage, etikett="Projekt", ikon="mapp-stor"):
    """en ikon på skrivbordet i en cell om ikoncell-b x ikoncell-h u"""
    w, h = M["ikoncell-b"], M["ikoncell-h"]
    s, defs = "", ""
    if lage == "hover":
        s += rekt(x, y, w, h, R["yta"], t["text"], extra=' fill-opacity=".10"')
    elif lage in ("vald", "vald-fokus", "byter-namn"):
        s += rekt(x, y, w, h, R["yta"], t["accent"], extra=' fill-opacity=".28"')
        s += rekt(x, y, w, h, R["yta"], "none", t["accent"], extra=' stroke-opacity=".7"')
    if lage == "vald-fokus":
        s += inre_ring(t, x, y, w, h, R["yta"])
    ix, iy = x + 20, y + 8
    if ikon == "mapp-stor":
        s += stor_mapp(ix, iy, 48)
    elif ikon == "fil-stor":
        s += stor_fil(ix, iy, 48)
    else:
        k, d = appikon(ikon, ix, iy, 48)
        s += k
        defs += d
    if lage == "byter-namn":
        fw = 80
        s += rekt(x + 4, y + 62, fw, 22, R["liten"], t["falt"], t["fokus"])
        tw = textbredd(etikett, "etikett")
        s += rekt(x + 4 + (fw - tw) / 2 - 2, y + 66, tw + 4, 14, 2, t["accent"], extra=' fill-opacity=".45"')
        s += text(x + w / 2, y + 73, etikett, "etikett", t["text"], "middle")
    else:
        s += ikonetikett(t, x + w / 2, y + 74, etikett)
    return s, defs


def stor_mapp(x, y, s):
    k = s / 48
    return (f'<g transform="translate({fmt(x)} {fmt(y)}) scale({fmt(k)})">'
            '<path d="M4 10a4 4 0 0 1 4-4h11l4 4h17a4 4 0 0 1 4 4v24a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z" fill="#E5853F"/>'
            '<rect x="4" y="15" width="40" height="27" rx="4" fill="#FFB86B"/>'
            '<rect x="4" y="15" width="40" height="3" rx="1.5" fill="#FFD3A0" opacity=".7"/></g>')


def stor_fil(x, y, s):
    k = s / 48
    return (f'<g transform="translate({fmt(x)} {fmt(y)}) scale({fmt(k)})">'
            '<path d="M10 4h19l11 11v27a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" fill="#F7F3F6"/>'
            '<path d="M29 4v9a2 2 0 0 0 2 2h9z" fill="#D4CBDC"/>'
            '<rect x="14" y="22" width="20" height="2.5" rx="1.25" fill="#A898B4"/>'
            '<rect x="14" y="28" width="20" height="2.5" rx="1.25" fill="#A898B4"/>'
            '<rect x="14" y="34" width="13" height="2.5" rx="1.25" fill="#A898B4"/></g>')


FALT_H = 56
CELL = 44


def falt_yta(t, x, y, w, h=FALT_H, flytande=True, fid=None):
    if flytande:
        return rekt(x, y, w, h, R["panel"], t["yta"], t["kant"],
                    extra=(f' fill-opacity=".92"' + (f' filter="url(#{fid})"' if fid else "")))
    return rekt(x, y, w, h, 0, t["yta"], extra=' fill-opacity=".94"') + rekt(x, y, w, 1, 0, t["kant"])


def programknapp(t, x, y, lage, app="filer"):
    """en programknapp i fältet: 44 u, ikonen 32 u, markören längst ned"""
    s, defs = "", ""
    if lage in ("hover", "aktiv"):
        s += rekt(x, y, CELL, CELL, R["yta"], t["yta-hover"])
    elif lage == "tryck":
        s += rekt(x, y, CELL, CELL, R["yta"], t["yta-tryck"])
    elif lage == "uppmarksamhet":
        s += rekt(x, y, CELL, CELL, R["yta"], t["varme"], extra=' fill-opacity=".28"')
    k, d = appikon(app, x + 6, y + 4 if lage != "tryck" else y + 5, 32)
    s += k
    defs += d
    if lage in ("oppen", "hover", "fokus"):
        s += rekt(x + CELL / 2 - 3, y + CELL - 4, 6, 3, 1.5, t["text-dampad"])
    elif lage == "aktiv":
        s += rekt(x + CELL / 2 - 8, y + CELL - 4, 16, 3, 1.5, t["accent"])
    elif lage == "uppmarksamhet":
        s += rekt(x + CELL / 2 - 8, y + CELL - 4, 16, 3, 1.5, t["varme"])
    if lage == "fokus":
        s += ring(t, x, y, CELL, CELL, R["yta"])
    return s, defs


def startknapp(t, x, y, lage):
    s = ""
    if lage == "hover":
        s += rekt(x, y, CELL, CELL, R["yta"], t["yta-hover"])
    elif lage == "oppen":
        s += rekt(x, y, CELL, CELL, R["yta"], t["yta-tryck"])
    k, d = logo(x + 8, y + 8, 28)
    return s + k, d


def ikonknapp(t, x, y, glyfnamn, lage="vila", b=CELL, h=CELL):
    s = ""
    if lage == "hover":
        s += rekt(x, y, b, h, R["yta"], t["yta-hover"])
    elif lage == "oppen":
        s += rekt(x, y, b, h, R["yta"], t["yta-tryck"])
    s += glyf(glyfnamn, x + (b - 20) / 2, y + (h - 20) / 2, 20, t["text"])
    return s


ALLA_SYMBOLER = ("wifi", "volym", "batteri")


def bricka_knapp(symboler):
    """bredden på knappen till snabbpanelen: en cell utan symboler, annars 24 u per symbol"""
    return CELL if not symboler else 20 + 24 * len(symboler)


def bricka_bredd(symboler):
    return bricka_knapp(symboler) + 4 + 64


def bricka(t, x, y, lage="vila", symboler=(), tid="14:32", datum="mån 2 nov"):
    """
    Knappen till snabbpanelen och klockan; returnerar (kropp, bredd).
    En statussymbol ritas bara när en tjänst rapporterar den. Utan någon
    visar knappen glyfen reglage, så att snabbpanelen går att nå ändå.
    """
    s = ""
    bw = bricka_knapp(symboler)
    if lage in ("hover", "oppen"):
        s += rekt(x, y, bw, CELL, R["yta"], t["yta-hover"] if lage == "hover" else t["yta-tryck"])
    if symboler:
        for i, g in enumerate(symboler):
            s += glyf(g, x + 12 + i * 24, y + 14, 16, t["text"])
    else:
        s += glyf("reglage", x + (CELL - 20) / 2, y + (CELL - 20) / 2, 20, t["text"])
    cx = x + bw + 4
    s += text(cx + 32, y + 15, tid, "etikett", t["text"], "middle", 700, 13)
    s += text(cx + 32, y + 30, datum, "etikett", t["text-dampad"], "middle", 500, 11)
    return s, bw + 4 + 64


def aktivitetsfalt(t, x, y, w, appar, flytande=True, fid=None, symboler=()):
    """hela fältet; appar är (app, läge)"""
    s, defs = falt_yta(t, x, y, w, FALT_H, flytande, fid), ""
    bb = bricka_bredd(symboler)
    innehall = CELL + 4 + CELL + 12 + len(appar) * (CELL + 4) + 8 + bb + 4 + CELL
    cx = x + (w - innehall) / 2 if flytande else x + 12
    cy = y + (FALT_H - CELL) / 2
    k, d = startknapp(t, cx, cy, "vila")
    s, defs = s + k, defs + d
    cx += CELL + 4
    s += ikonknapp(t, cx, cy, "sok")
    cx += CELL + 6
    s += rekt(cx, cy + 10, 1, CELL - 20, 0, t["kant"])
    cx += 6
    for app, lage in appar:
        k, d = programknapp(t, cx, cy, lage, app)
        s, defs = s + k, defs + d
        cx += CELL + 4
    if not flytande:
        cx = x + w - 12 - bb - 4 - CELL
    else:
        cx += 4
    s += rekt(cx - 6, cy + 10, 1, CELL - 20, 0, t["kant"])
    k, bw = bricka(t, cx, cy, symboler=symboler)
    s += k
    cx += bw + 4
    s += ikonknapp(t, cx, cy, "avisering")
    s += f'<circle cx="{fmt(cx + 29)}" cy="{fmt(cy + 13)}" r="4" fill="{t["varme"]}" stroke="{t["yta"]}" stroke-width="2"/>'
    return s, defs


def falt_bredd(n, symboler=()):
    return CELL + 4 + CELL + 12 + n * (CELL + 4) + 8 + bricka_bredd(symboler) + 4 + CELL + 24


def startpanel(t, x, y, variant="kompakt", fid=None):
    """Start-panelen; returnerar (kropp, defs, bredd, höjd)"""
    p = 24
    w = 640 if variant != "oversikt" else 880
    h = 560
    # täckande: utan oskärpa skymtar texten i fönstren bakom igenom en genomskinlig panel
    s = rekt(x, y, w, h, R["panel"], t["yta"], t["kant"],
             extra=(f' filter="url(#{fid})"' if fid else ""))
    defs = ""
    cid = nytt_id("sp")
    defs += f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{R["panel"]}"/></clipPath>'
    # sök
    sw = 640 - 2 * p
    sokt = variant == "sok"
    s += rekt(x + p, y + p, sw, 40, 20, t["falt"], t["fokus"] if sokt else t["kant-kontroll"])
    s += glyf("sok", x + p + 14, y + p + 12, 16, t["text-dampad"])
    if sokt:
        s += text(x + p + 40, y + p + 20, "term", "brod", t["text"])
        s += rekt(x + p + 40 + textbredd("term", "brod") + 1, y + p + 10, 1.5, 20, 0, t["text"])
        s += ring(t, x + p, y + p, sw, 40, 20)
    else:
        s += text(x + p + 40, y + p + 20, "Sök program, dokument och inställningar", "brod", t["text-dampad"])
    cy = y + p + 40 + 24
    if sokt:
        s += text(x + p, cy + 8, "Bästa träff", "etikett", t["text-dampad"])
        cy += 24
        s += rekt(x + p, cy, sw, 72, R["yta"], t["markering"])
        k, d = appikon("terminal", x + p + 16, cy + 12, 48)
        s, defs = s + k, defs + d
        s += text(x + p + 80, cy + 26, "Terminal", "rubrik", t["markering-text"], storlek=16)
        s += text(x + p + 80, cy + 48, "Program · examples/term", "brod", t["text-dampad"], storlek=13)
        k, _ = knapp(t, x + p + sw - 96 - 16, cy + 20, "primar", "vila", "Öppna", 96)
        s += k
        cy += 72 + 20
        s += text(x + p, cy + 8, "Fler träffar", "etikett", t["text-dampad"])
        cy += 22
        rader = [("installningar", "Terminalens typsnitt", "Inställningar > Utseende"),
                 ("loggar", "terminal.log", "~/.local/state · i går"),
                 ("text", "terminal.md", "~/qzos/docs · 28 okt")]
        for i, (a, e, under) in enumerate(rader):
            ry = cy + i * 52
            if i == 1:
                s += rekt(x + p, ry, sw, 48, R["kontroll"], t["yta-hover"])
            k, d = appikon(a, x + p + 10, ry + 8, 32)
            s, defs = s + k, defs + d
            s += text(x + p + 54, ry + 17, e, "brod", t["text"], vikt=600)
            s += text(x + p + 54, ry + 34, under, "etikett", t["text-dampad"], vikt=500)
    else:
        s += text(x + p, cy + 8, "Fästa", "etikett", t["text"], vikt=700, storlek=13)
        s += rekt(x + p + sw - 108, cy - 4, 108, 24, 12, t["knapp"])
        s += text(x + p + sw - 60, cy + 8, "Alla program", "etikett", t["text"], "middle")
        s += glyf("chevron-hoger", x + p + sw - 22, cy + 2, 12, t["text"])
        cy += 26
        appar = ["filer", "terminal", "text", "webb", "kalender", "musik",
                 "bilder", "rita", "kalkylator", "farger", "loggar", "installningar"]
        cw = sw / 6
        for i, a in enumerate(appar):
            tx, ty = x + p + (i % 6) * cw, cy + (i // 6) * 84
            if i == 1:
                s += rekt(tx + 4, ty, cw - 8, 80, R["yta"], t["yta-hover"])
            k, d = appikon(a, tx + (cw - 40) / 2, ty + 10, 40)
            s, defs = s + k, defs + d
            s += text(tx + cw / 2, ty + 64, APPAR[a][0], "etikett", t["text"], "middle", 500)
        cy += 2 * 84 + 18
        s += text(x + p, cy + 8, "Senaste", "etikett", t["text"], vikt=700, storlek=13)
        cy += 24
        senaste = [("text", "anteckningar.md", "14:02"), ("bilder", "dyner.png", "i dag"),
                   ("loggar", "session.log", "i går"), ("text", "mal.md", "i går"),
                   ("kalkylator", "budget.ods", "28 okt"), ("rita", "logga.svg", "27 okt")]
        lw = sw / 2
        for i, (a, e, nar) in enumerate(senaste):
            lx, ly = x + p + (i % 2) * lw, cy + (i // 2) * 52
            k, d = appikon(a, lx + 8, ly + 8, 32)
            s, defs = s + k, defs + d
            s += text(lx + 52, ly + 17, e, "brod", t["text"], vikt=600, storlek=13)
            s += text(lx + 52, ly + 34, nar, "etikett", t["text-dampad"], vikt=500)
    # sidfoten
    fy = y + h - 64
    s += f'<g clip-path="url(#{cid})">' + rekt(x, fy, w, 64, 0, t["yta-sankt"], extra=' fill-opacity=".5"') + "</g>"
    s += rekt(x, fy, w, 1, 0, t["kant"])
    s += f'<circle cx="{fmt(x + p + 18)}" cy="{fmt(fy + 32)}" r="18" fill="{t["varme"]}"/>'
    s += text(x + p + 18, fy + 32, "A", "rubrik", t["pa-accent"], "middle", storlek=15)
    s += text(x + p + 46, fy + 32, "Användare", "brod", t["text"], vikt=700)
    for i, g in enumerate(("strom", "reglage", "fil")):
        s += ikonknapp(t, x + w - p - 40 - i * 44, fy + 12, g, b=40, h=40)
    if variant == "oversikt":
        ox, ow = x + 640, w - 640 - 2 * p
        s += rekt(ox, y + p, 1, h - 64 - 2 * p, 0, t["kant"])
        ox += p
        s += text(ox, y + p + 10, "I dag", "etikett", t["text"], vikt=700, storlek=13)
        s += rekt(ox, y + p + 28, ow, 132, R["yta"], t["yta-sankt"], extra=' fill-opacity=".5"')
        s += text(ox + 16, y + p + 52, "måndag", "etikett", t["accent-text"], vikt=700)
        s += text(ox + 16, y + p + 80, "2 november", "rubrik", t["text"])
        s += rekt(ox + 16, y + p + 104, 3, 36, 1.5, t["accent"])
        s += text(ox + 28, y + p + 113, "Temagenomgång", "brod", t["text"], vikt=600, storlek=13)
        s += text(ox + 28, y + p + 131, "15:00–15:30", "etikett", t["text-dampad"], vikt=500)
        s += text(ox, y + p + 186, "Spelas nu", "etikett", t["text"], vikt=700, storlek=13)
        my = y + p + 204
        s += rekt(ox, my, ow, 88, R["yta"], t["yta-sankt"], extra=' fill-opacity=".5"')
        k, d = appikon("musik", ox + 14, my + 14, 40)
        s, defs = s + k, defs + d
        s += text(ox + 66, my + 26, "[Låttitel]", "brod", t["text"], vikt=700, storlek=13)
        s += text(ox + 66, my + 44, "[Artist]", "etikett", t["text-dampad"], vikt=500)
        s += rekt(ox + 14, my + 68, ow - 28, 4, 2, t["spar"])
        s += rekt(ox + 14, my + 68, (ow - 28) * .35, 4, 2, t["accent"])
        s += text(ox, y + p + 320, "Systemet", "etikett", t["text"], vikt=700, storlek=13)
        sy = y + p + 338
        s += rekt(ox, sy, ow, 96, R["yta"], t["yta-sankt"], extra=' fill-opacity=".5"')
        for i, (e, v, f) in enumerate((("Disk", "62 %", .62), ("Minne", "41 %", .41))):
            ry = sy + 18 + i * 40
            s += text(ox + 14, ry + 6, e, "etikett", t["text-dampad"], vikt=600)
            s += text(ox + ow - 14, ry + 6, v, "etikett", t["text"], "end", 700)
            s += rekt(ox + 14, ry + 18, ow - 28, 4, 2, t["spar"])
            s += rekt(ox + 14, ry + 18, (ow - 28) * f, 4, 2, t["varme"])
    return s, defs, w, h


def snabbpanel(t, x, y, fid=None):
    w, p = 360, 18
    h = 324
    # täckande: utan oskärpa skymtar texten i fönstren bakom igenom en genomskinlig panel
    s = rekt(x, y, w, h, R["panel"], t["yta"], t["kant"],
             extra=(f' filter="url(#{fid})"' if fid else ""))
    rutor = [("wifi", "Wi-Fi", "Hemma-5G", True), ("bluetooth", "Bluetooth", "2 enheter", True),
             ("flygplan", "Flygläge", "Av", False), ("fokus", "Fokus", "Av", False),
             ("mane", "Nattljus", "Från 21:00", False), ("starta-om", "Glöd", "Mörkt tema", True)]
    rw = (w - 2 * p - 2 * 10) / 3
    for i, (g, e, under, pa) in enumerate(rutor):
        rx, ry = x + p + (i % 3) * (rw + 10), y + p + (i // 3) * 82
        fyll = t["accent"] if pa else t["knapp"]
        fg = t["pa-accent"] if pa else t["text"]
        s += rekt(rx, ry, rw, 72, R["yta"], fyll)
        s += glyf("mane" if e == "Glöd" else g, rx + 12, ry + 12, 20, fg)
        s += text(rx + 12, ry + 46, e, "etikett", fg, vikt=700, storlek=13)
        s += text(rx + 12, ry + 61, under, "etikett", fg if pa else t["text-dampad"], vikt=500, storlek=11)
    sy = y + p + 2 * 82 + 10
    for i, (g, v) in enumerate((("sol", .7), ("volym", .45))):
        ry = sy + i * 40
        s += glyf(g, x + p, ry, 20, t["text-dampad"])
        tx, tw = x + p + 34, w - 2 * p - 34
        s += rekt(tx, ry + 8, tw, 4, 2, t["spar"])
        s += rekt(tx, ry + 8, tw * v, 4, 2, t["accent"])
        s += (f'<circle cx="{fmt(tx + tw * v)}" cy="{fmt(ry + 10)}" r="8.5" fill="{t["reglage-tumme"]}" '
              f'stroke="{t["kant-kontroll"]}"/>')
    fy = y + h - 52
    s += rekt(x, fy, w, 1, 0, t["kant"])
    # batteriets rad visas bara när en tjänst rapporterar ett batteri; bänken har inget
    s += ikonknapp(t, x + w - p - 36, fy + 8, "reglage", b=36, h=36)
    s += ikonknapp(t, x + w - p - 76, fy + 8, "strom", b=36, h=36)
    return s, w, h


def avisering(t, x, y, fid=None):
    w, h = 360, 132
    s = rekt(x, y, w, h, R["yta"] + 4, t["yta"], t["kant"],
             extra=(f' filter="url(#{fid})"' if fid else ""))
    k, d = appikon("kalender", x + 16, y + 16, 20)
    s += k
    s += text(x + 44, y + 26, "Kalender", "etikett", t["text-dampad"], vikt=600)
    s += text(x + w - 16, y + 26, "nu", "etikett", t["text-dampad"], "end", 500)
    s += text(x + 16, y + 54, "Temagenomgång om 10 min", "brod", t["text"], vikt=700)
    s += text(x + 16, y + 74, "Videosamtal · 15:00–15:30", "etikett", t["text-dampad"], vikt=500, storlek=13)
    k1, _ = knapp(t, x + 16, y + h - 16 - 32, "primar", "vila", "Anslut", 96)
    k2, _ = knapp(t, x + 120, y + h - 16 - 32, "sekundar", "vila", "Påminn senare", 136)
    return s + k1 + k2, d, w, h


def forhandsvisning(t, x, y, fid=None):
    """fönstrets miniatyr när pekaren är över dess knapp i fältet"""
    w, h = 240, 172
    s = rekt(x, y, w, h, R["yta"], t["yta"], t["kant"],
             extra=(f' filter="url(#{fid})"' if fid else ""))
    k, d = appikon("filer", x + 12, y + 12, 16)
    s += k
    s += text(x + 36, y + 20, "Filer — Hem", "etikett", t["text"], vikt=600)
    s += rekt(x + w - 36, y + 6, 28, 28, R["kontroll"], t["yta-hover"])
    s += glyf("stang", x + w - 30, y + 12, 16, t["text"])
    mx, my, mw, mh = x + 12, y + 42, w - 24, h - 54
    s += rekt(mx, my, mw, mh, 6, t["yta"], t["kant"])
    s += rekt(mx + 1, my + 1, 52, mh - 2, 5, t["yta-sankt"], extra=' fill-opacity=".6"')
    for i in range(6):
        ix, iy = mx + 66 + (i % 3) * 52, my + 14 + (i // 3) * 46
        s += stor_mapp(ix, iy, 28)
    return s, d, w, h


# ---------------------------------------------------------------- skalet i dag
# Det skal generic_gdi har under en profil (examples/shell, gg #481), med
# samma tokens: ett dockat fält med en textknapp per fönster, en
# accentmarkör under det aktiva, klockan och Start som en meny.

IDAG_H = 40


def idag_falt(t, x, y, w):
    s = rekt(x, y, w, IDAG_H, 0, t["yta"]) + rekt(x, y, w, 1, 0, t["kant"])
    kh = M["kontroll-h"]
    ky = y + (IDAG_H - kh) / 2
    k, d = logo(x + 10, ky + 8, 16)
    sw = 16 + 6 + round(textbredd("Start", "knapp")) + 16
    s += k + text(x + 32, ky + kh / 2, "Start", "knapp", t["text"])
    cx = x + 8 + sw + 6
    for titel, aktiv in (("Namnlös – Anteckningar", True), ("Filer – Hem", False), ("Terminal", False)):
        bw = 160
        if aktiv:
            s += rekt(cx, ky, bw, kh, R["kontroll"], t["knapp"])
            s += rekt(cx + bw / 2 - 8, ky + kh - 3, 16, 3, 1.5, t["accent"])
        if textbredd(titel, "brod", 13) > bw - 20:  # som i fältet: titeln kortas med en ellips
            while textbredd(titel + "…", "brod", 13) > bw - 20:
                titel = titel[:-1]
            titel = titel.rstrip(" –") + "…"
        s += text(cx + 10, ky + kh / 2, titel, "brod", t["text"], vikt=700 if aktiv else 500, storlek=13)
        cx += bw + 4
    s += text(x + w - 12, ky + kh / 2, "14:32", "etikett", t["text"], "end", 600, 13)
    return s, d


def idag_startmeny(t, x, y, fid):
    """Start-menyn med accentbanderoll och solen: Program, Dokument, Inställningar, Hjälp, Kör, Avsluta"""
    objekt = [("hover", "Program", "", "rutnat"), ("normal", "Dokument", "", "fil"),
              ("normal", "Inställningar", "", "reglage"), ("normal", "Hjälp", "", "hjalp"),
              ("normal", "Kör …", "", "kor"), ("avskiljare",), ("normal", "Avsluta …", "", "strom")]
    b, mw = 28, 220
    pk, ph = popup(t, x + b, y, mw, objekt, fid)
    pk = re.sub(r"^<rect [^>]*/>", "", pk, count=1)  # menyns egen yta: hela menyn ritas nedan
    for i in range(3):  # undermenyerna har pilar
        pk += glyf("chevron-hoger", x + b + mw - M["meny-utfyllnad"] - 22,
                   y + M["meny-utfyllnad"] + i * M["menyobjekt-h"] + 7, 16,
                   t["pa-accent"] if i == 0 else t["text-dampad"])
    w = b + mw
    cid = nytt_id("ban")
    defs = f'<clipPath id="{cid}"><rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(ph)}" rx="{R["yta"]}"/></clipPath>'
    k, d = logo(x + 6, y + ph - 26, 16, "#FFFFFF")
    kropp = rekt(x, y, w, ph, R["yta"], t["yta-upphojd"], extra=f' filter="url(#{fid})"')
    kropp += f'<g clip-path="url(#{cid})">{rekt(x, y, b, ph, 0, t["accent"])}</g>' + k + pk
    kropp += rekt(x, y, w, ph, R["yta"], "none", t["kant"])
    return kropp, defs + d, w, ph


def skal_komponenter(t):
    ut = []

    def fil(sok, titel, w, h, kropp, defs=""):
        ut.append(("skal/" + sok, titel, w, h, kropp, defs))

    bg = t["yta"]
    for lage in ("vila", "hover", "tryck", "oppen", "aktiv", "uppmarksamhet", "fokus"):
        k, d = programknapp(t, 6, 6, lage, "filer")
        fil(f"programknapp/{lage}", f"Programknapp, {lage}", CELL + 12, CELL + 12,
            rekt(0, 0, CELL + 12, CELL + 12, 0, bg) + k, d)
    for lage in ("vila", "oppen", "uppmarksamhet"):
        # överflödet: program som inte ryms i fältet, bakom en Mer-knapp sist
        s = rekt(0, 0, CELL + 12, CELL + 12, 0, bg)
        if lage == "oppen":
            s += rekt(6, 6, CELL, CELL, R["yta"], t["yta-tryck"])
        elif lage == "uppmarksamhet":
            s += rekt(6, 6, CELL, CELL, R["yta"], t["varme"], extra=' fill-opacity=".28"')
        s += glyf("mer", 6 + (CELL - 20) / 2, 6 + (CELL - 20) / 2 - 2, 20, t["text"])
        if lage == "uppmarksamhet":
            s += rekt(6 + CELL / 2 - 8, 6 + CELL - 4, 16, 3, 1.5, t["varme"])
        else:
            s += rekt(6 + CELL / 2 - 3, 6 + CELL - 4, 6, 3, 1.5, t["text-dampad"])
        fil(f"overflode/{lage}", f"Fler program, {lage}", CELL + 12, CELL + 12, s)
    for lage in ("vila", "hover", "oppen"):
        k, d = startknapp(t, 6, 6, lage)
        fil(f"startknapp/{lage}", f"Start-knapp, {lage}", CELL + 12, CELL + 12,
            rekt(0, 0, CELL + 12, CELL + 12, 0, bg) + k, d)
    for lage in ("vila", "hover", "oppen"):
        k, bw = bricka(t, 6, 6, lage)
        fil(f"bricka/{lage}", f"Bricka och klocka, {lage}", bw + 12, CELL + 12,
            rekt(0, 0, bw + 12, CELL + 12, 0, bg) + k)
    k, bw = bricka(t, 6, 6, "vila", ALLA_SYMBOLER)
    fil("bricka/alla-symboler", "Bricka med wifi, volym och batteri", bw + 12, CELL + 12,
        rekt(0, 0, bw + 12, CELL + 12, 0, bg) + k)
    appar = [("filer", "aktiv"), ("terminal", "oppen"), ("webb", "vila"), ("text", "oppen"),
             ("kalender", "uppmarksamhet"), ("musik", "vila"), ("installningar", "vila")]
    w = falt_bredd(len(appar))
    k, d = aktivitetsfalt(t, 24, 16, w, appar, True, "s2")
    fil("falt/flytande", "Aktivitetsfältet, flytande", w + 48, FALT_H + 48, k, d + skugga(t, 2, "s2"))
    k, d = aktivitetsfalt(t, 0, 0, 1280, appar, False)
    fil("falt/dockat", "Aktivitetsfältet, dockat", 1280, FALT_H, k, d)
    k, d = idag_falt(t, 0, 0, 1280)
    fil("i-dag/falt", "Aktivitetsfältet i dag", 1280, IDAG_H, k, d)
    k, d, pw, ph = idag_startmeny(t, 16, 8, "s2")
    fil("i-dag/startmeny", "Start-menyn i dag", pw + 32, ph + 40, k, d + skugga(t, 2, "s2"))
    for variant in ("kompakt", "oversikt", "sok"):
        k, d, pw, ph = startpanel(t, 40, 24, variant, "s3")
        fil(f"startpanel/{variant}", f"Start-panelen, {variant}", pw + 80, ph + 96, k, d + skugga(t, 3, "s3"))
    objekt = [("normal", "Lås", "Super+L", "las"), ("normal", "Logga ut", "", "logga-ut"),
              ("avskiljare",), ("hover", "Starta om", "", "starta-om"), ("normal", "Stäng av", "", "strom")]
    pk, ph = popup(t, 16, 8, 220, objekt, "s2")
    fil("strommeny/strommeny", "Strömmenyn", 252, ph + 40, pk, skugga(t, 2, "s2"))
    k, pw, ph = snabbpanel(t, 24, 16, "s3")
    fil("snabbpanel/snabbpanel", "Snabbpanelen", pw + 48, ph + 72, k, skugga(t, 3, "s3"))
    k, d, pw, ph = avisering(t, 24, 16, "s2")
    fil("avisering/avisering", "Avisering", pw + 48, ph + 56, k, d + skugga(t, 2, "s2"))
    k, d, pw, ph = forhandsvisning(t, 24, 16, "s2")
    fil("forhandsvisning/forhandsvisning", "Förhandsvisning av fönster", pw + 48, ph + 56, k,
        d + skugga(t, 2, "s2"))
    for lage in ("vila", "hover", "vald", "vald-fokus", "byter-namn"):
        k, d = skrivbordsikon(t, 8, 8, lage)
        fil(f"skrivbordsikon/{lage}", f"Skrivbordsikon, {lage}", 104, 116,
            rekt(0, 0, 104, 116, 0, t["bakgrund"]) + k, d)
    s = rekt(0, 0, 320, 220, 0, t["bakgrund"])
    for i, (e, ik) in enumerate((("Projekt", "mapp-stor"), ("anteckningar.md", "fil-stor"),
                                 ("Terminal", "terminal"))):
        k, d = skrivbordsikon(t, 16 + i * 96, 16, "vald" if i < 2 else "vila", e, ik)
        s += k
        if d:
            s += f"<defs>{d}</defs>"
    s += rekt(8, 8, 200, 150, 4, t["accent"], extra=' fill-opacity=".14"')
    s += rekt(8, 8, 200, 150, 4, "none", t["accent"])
    fil("skrivbordsikon/markeringsruta", "Markeringsruta över två ikoner", 320, 220, s)
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


def centrerad(inre, yttre):
    """ett mått centrerat i ett annat, med samma paritet så att det inte hamnar en halv bildpunkt snett"""
    return inre + (inre - yttre) % 2


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
    rader += ["", "## Centrerat i ett annat mått", "",
              "Samma paritet som det yttre måttet: skiljer den sig läggs 1 bildpunkt till.", "",
              huvud, linje]
    for k, yttre in (("reglage-spar", "reglage-tumme"),):
        v = M[k]
        rader.append(f"| {k} i {yttre} | {v} | " + " | ".join(
            str(centrerad(rund(v * s), rund(M[yttre] * s))) for s in sk) + " |")
    rader += ["", "## Glyfstreck", "", huvud, linje,
              "| glyfstreck | 1.5 | " + " | ".join(fmt(rund(1.5 * s * 2) / 2) for s in sk) + " |"]
    rader += ["", "## Text", "", huvud, linje]
    for k, st in TYP.items():
        rader.append(f"| {k} | {st['storlek']} | " + " | ".join(str(rund(st['storlek'] * s)) for s in sk) + " |")
    return "\n".join(rader) + "\n"


# ---------------------------------------------------------------- lekplatsen


def lekplats():
    """lekplats/index.html ur lekplats/mall.html, med tokens, symboler och bakgrunder"""
    from urllib.parse import quote
    mall = (ROT / "lekplats" / "mall.html").read_text(encoding="utf-8")
    tokens = "".join(css(Tema(tn)) for tn in TEMAN)
    tapeter = "body {"
    for tn in TEMAN:
        k, d = bakgrund(tn)
        data = quote(dokument(1920, 1080, "Dyner", k, d).replace('role="img" ', "").strip(), safe=" =:/,'")
        tapeter += f' --tapet-{tn}: url("data:image/svg+xml,{data}");'
    tokens += tapeter + " }\n"
    defs, sym = "", ""
    for namn, delar in GLYFER.items():
        sym += (f'<symbol id="g-{namn}" viewBox="0 0 16 16"><g fill="none" stroke="currentColor" stroke-width="1.5" '
                f'stroke-linecap="round" stroke-linejoin="round">{glyfdelar(delar, "currentColor")}</g></symbol>')
    for namn in APPAR:
        k, d = appikon(namn, 0, 0, 48)
        defs += d
        sym += f'<symbol id="a-{namn}" viewBox="0 0 48 48">{k}</symbol>'
    sym += f'<symbol id="mapp-stor" viewBox="0 0 48 48">{stor_mapp(0, 0, 48)}</symbol>'
    sym += f'<symbol id="fil-stor" viewBox="0 0 48 48">{stor_fil(0, 0, 48)}</symbol>'
    k, d = logo(0, 0, 48)
    defs += d
    sym += f'<symbol id="logo" viewBox="0 0 48 48">{k}</symbol>'
    k, d = logo(0, 0, 48, "#FFFFFF")  # på Start-menyns accentbanderoll i läget I dag
    defs += d
    sym += f'<symbol id="logo-vit" viewBox="0 0 48 48">{k}</symbol>'
    appar = json.dumps({a: {"namn": v[0]} for a, v in APPAR.items()}, ensure_ascii=False)
    ut = (mall.replace("/*TOKENS*/", tokens)
          .replace("<!--SYMBOLER-->", f"<defs>{defs}</defs>{sym}")
          .replace("/*APPAR*/", appar))
    (ROT / "lekplats" / "index.html").write_text(ut, encoding="utf-8")


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
    (svg / "appikoner").mkdir()
    for namn in APPAR:
        k, d = appikon(namn, 0, 0, 48)
        (svg / "appikoner" / f"{namn}.svg").write_text(dokument(48, 48, APPAR[namn][0], k, d), encoding="utf-8")
        antal += 1
    for namn, f in (("mapp", stor_mapp), ("fil", stor_fil)):
        (svg / "appikoner" / f"{namn}-stor.svg").write_text(dokument(48, 48, namn, f(0, 0, 48)), encoding="utf-8")
        antal += 1
    k, d = logo(0, 0, 48)
    (svg / "logo.svg").write_text(dokument(48, 48, "QzOS", k, d), encoding="utf-8")
    (svg / "bakgrund").mkdir()
    for tn in TEMAN:
        k, d = bakgrund(tn)
        (svg / "bakgrund" / f"dyner-{tn}.svg").write_text(dokument(1920, 1080, "Dyner", k, d), encoding="utf-8")
        antal += 2
    for tn in TEMAN:
        t = Tema(tn)
        for sok, titel, w, h, kropp, defs in komponenter(t) + skal_komponenter(t):
            p = svg / tn / f"{sok}.svg"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(dokument(w, h, titel, kropp, defs), encoding="utf-8")
            antal += 1
        (ROT / "tokens" / f"{tn}.css").write_text(css(t), encoding="utf-8")
    (ROT / "docs").mkdir(exist_ok=True)
    (ROT / "docs" / "dpi.md").write_text(dpi_md(), encoding="utf-8")
    lekplats()
    import webblasare  # webbläsarens ikoner har sin egen stil och sin egen fil
    antal += webblasare.bygg()
    print(f"{antal} SVG-filer, {len(TEMAN)} CSS-filer, docs/dpi.md och lekplats/index.html")


if __name__ == "__main__":
    main()
