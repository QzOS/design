#!/usr/bin/env python3
"""
webblasare.py - webbläsarens ikoner (QzOS/browser), i 90-talets anda

    python3 verktyg/webblasare.py        (bygg.py kör den också)

Skriver svg/webblasare/:
  bakat, framat, hem, ladda-om, bilder, oppna, skriv-ut, sok, stopp
      verktygsknapparna, 24 x 24 u, en per QBI_* i src/icons.h
  <namn>-inaktiv
      samma knapp avstängd: konturen i grått med en vit skugga, som förr
  nyckel-hel, nyckel-bruten
      statusradens nyckel, 16 x 16 u
Throbbern uppe till höger rör sig och ritas i kod (qb_icon_throbber), inte här.

Stilen: svart kontur, platta färger, en ljus fasett uppe till vänster och en
mörk nere till höger, som ikonerna i verktygsfälten i mitten av 90-talet.
Inget är ritat efter Netscape. Konturerna ligger på halva enheter och
fasetterna på hela, så att varje rak kant är en hel bildpunkt i 100 och
200 %. Allt är inom QzOS SVG Icon Profile (generic_gdi docs/svg.md):
svg, g, rect, circle, polygon och path, inga transformer, ingen text.
"""
import math
import pathlib

ROT = pathlib.Path(__file__).resolve().parent.parent
UT = ROT / "svg" / "webblasare"

SVART = "#000000"
P = {  # palett: (ljus, bas, mörk)
    "gron": ("#8FE3B6", "#2EA06C", "#12603E"),
    "gul": ("#FFF1A6", "#FFCF3F", "#C2900E"),
    "rod": ("#FF8A7A", "#D9342B", "#8C1712"),
    "bla": ("#9CBBF7", "#2F62CC", "#173A86"),
    "gra": ("#FFFFFF", "#C0C0C0", "#808080"),
    "morkgra": ("#8A8A98", "#4B4B57", "#26262E"),
    "himmel": ("#DDF0FF", "#9FD3FF", "#5A9BD6"),
    "tegel": ("#E0745E", "#B0412E", "#6E2216"),
    "papper": ("#FFFFFF", "#F4F4F4", "#B8B8B8"),
}


def f(v):
    v = round(v, 3)
    return str(int(v)) if v == int(v) else ("%.3f" % v).rstrip("0").rstrip(".")


def pts(p):
    return " ".join(f"{f(x)},{f(y)}" for x, y in p)


# ---------------------------------------------------------------- former
# Varje form är (typ, geometri, fyllning, kontur). Kontur är svart 1 u
# eller ingen. Inaktiva knappar ritas ur samma lista.

def poly(p, fyll, kontur=True):
    return ("poly", p, fyll, kontur)


def rekt(x, y, w, h, fyll, kontur=False):
    """med kontur: (x, y, w, h) är konturens mitt, alltså på halva enheter"""
    return ("rect", (x, y, w, h), fyll, kontur)


def cirkel(cx, cy, r, fyll, kontur=True):
    return ("circle", (cx, cy, r), fyll, kontur)


def bana(d, fyll, kontur=True):
    return ("path", d, fyll, kontur)


def svg_form(s, fyll=None, kontur=None):
    typ, g, fy, ko = s
    fy = fyll if fyll is not None else fy
    k = (f' stroke="{kontur or SVART}" stroke-width="1" stroke-linejoin="miter"' if ko else "")
    if typ == "poly":
        return f'<polygon points="{pts(g)}" fill="{fy}"{k}/>'
    if typ == "rect":
        x, y, w, h = g
        return f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fy}"{k}/>'
    if typ == "circle":
        cx, cy, r = g
        return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fy}"{k}/>'
    return f'<path d="{g}" fill="{fy}"{k}/>'


def ljushet(hexf):
    if not hexf.startswith("#"):
        return 1.0
    r, g, b = (int(hexf[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def inaktiv(former, siluett=False):
    """
    Avstängd som i verktygsfälten förr: konturen och de mörka ytorna i
    grått, och samma sak i vitt en enhet ned och åt höger, bakom.
    De ljusa ytorna försvinner. Med siluett fylls varje form med kontur,
    för en knapp vars former är för smala för två konturer i 24 bildpunkter.
    """
    def lager(farg, dx):
        ut = []
        for typ, g, fy, ko in former:
            if siluett and not ko:
                continue
            fyll = farg if siluett or ljushet(fy) < 0.2 else "none"
            if fyll == "none" and not ko:
                continue
            g2 = flytta((typ, g), dx)
            ut.append(svg_form((typ, g2, fyll, ko), kontur=farg))
        return "".join(ut)
    return lager("#FFFFFF", 1) + lager("#808080", 0)


def flytta(s, d):
    typ, g = s
    if not d:
        return g
    if typ == "poly":
        return [(x + d, y + d) for x, y in g]
    if typ == "rect":
        x, y, w, h = g
        return (x + d, y + d, w, h)
    if typ == "circle":
        cx, cy, r = g
        return (cx + d, cy + d, r)
    # en bana: flytta alla absoluta koordinatpar (banorna här är bara M, L, A och Z, absoluta)
    ut, tal, i = [], [], 0
    for tok in g.replace(",", " ").split():
        if tok[0].isalpha():
            ut.append(tok)
            if tok in ("A", "a"):
                i = -5
            continue
        v = float(tok)
        if i < 0:  # A: rx ry rotation stor svep, oförändrade
            ut.append(tok)
            i += 1
            continue
        ut.append(f(v + d))
        i += 1
    return " ".join(ut)


def spegla(former, w=24):
    """samma bild åt andra hållet; fasetterna byter inte sida uppåt och nedåt"""
    ut = []
    for typ, g, fy, ko in former:
        if typ == "poly":
            g = [(w - x, y) for x, y in g]
        elif typ == "rect":
            x, y, ww, h = g
            g = (w - x - ww, y, ww, h)
        elif typ == "circle":
            cx, cy, r = g
            g = (w - cx, cy, r)
        ut.append((typ, g, fy, ko))
    return ut


# ---------------------------------------------------------------- knapparna

def bakat():
    l, b, m = P["gron"]
    return [
        poly([(2.5, 12), (11.5, 3.5), (11.5, 8.5), (21.5, 8.5), (21.5, 15.5), (11.5, 15.5), (11.5, 20.5)], b),
        poly([(4, 12), (11, 5.4), (11, 6.8), (5.5, 12)], l, False),
        rekt(12, 9, 9, 1, l),
        rekt(12, 14, 9, 1, m),
        rekt(20, 10, 1, 4, m),
        poly([(5.5, 12), (11, 17.2), (11, 18.6), (4, 12)], m, False),
    ]


def framat():
    return spegla(bakat())


def hem():
    gl, gb, gm = P["gul"]
    rl, rb, rm = P["rod"]
    tl, tb, tm = P["tegel"]
    bl, bb, bm = P["bla"]
    hl, hb, hm = P["himmel"]
    return [
        rekt(15.5, 3.5, 3, 6, tb, True),           # skorstenen, taket ritas över
        rekt(16, 4, 1, 5, tl),
        rekt(5.5, 11.5, 13, 10, gb, True),         # väggarna
        rekt(6, 12, 1, 9, gl),
        rekt(17, 12, 1, 9, gm),
        rekt(6, 20, 12, 1, gm),
        poly([(1.5, 12.5), (12, 2.5), (22.5, 12.5)], rb),  # taket
        poly([(3.9, 11.5), (12, 3.9), (12, 5.3), (5.4, 11.5)], rl, False),
        rekt(4, 11, 16, 1, rm),
        rekt(7.5, 14.5, 4, 4, hb, True),           # fönstret
        rekt(8, 15, 1, 3, hl),
        rekt(13.5, 14.5, 4, 7, bb, True),          # dörren
        rekt(14, 15, 1, 6, bl),
        rekt(16, 18, 1, 1, gl),                    # handtaget
    ]


def _bage(cx, cy, r1, r2, a0, a1, spets):
    """ett band mellan r1 och r2 från vinkel a0 till a1 (grader, medurs i bilden) med en pilspets vid a1"""
    def p(r, a):
        return (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    rm, bred = (r1 + r2) / 2, (r2 - r1)
    ut = [p(r2, a) for a in range(a0, a1 + 1, 5)]
    if a1 not in range(a0, a1 + 1, 5):
        ut.append(p(r2, a1))
    # pilspetsen: bredare än bandet, spetsen framåt längs cirkeln
    ut += [p(r2 + bred * 0.75, a1), p(rm, a1 + spets), p(r1 - bred * 0.75, a1)]
    ut += [p(r1, a) for a in range(a1, a0 - 1, -5)]
    return ut


def ladda_om():
    bl, bb, bm = P["bla"]
    gl, gb, gm = P["gron"]
    return [
        poly(_bage(12, 12, 5, 8.5, 195, 300, 34), bb),
        poly(_bage(12, 12, 5, 8.5, 15, 120, 34), gb),
        poly([(5.2, 9.0), (6.5, 6.6), (8.6, 4.7), (11, 3.9), (11.2, 5.2), (9.1, 5.9), (7.4, 7.4), (6.3, 9.4)], bl, False),
        poly([(18.8, 15.0), (17.5, 17.4), (15.4, 19.3), (13, 20.1), (12.8, 18.8), (14.9, 18.1), (16.6, 16.6), (17.7, 14.6)], gm, False),
    ]


def bilder():
    l, b, m = P["gra"]
    hl, hb, hm = P["himmel"]
    gl, gb, gm = P["gron"]
    yl, yb, ym = P["gul"]
    return [
        rekt(2.5, 4.5, 19, 15, b, True),           # ramen
        rekt(3, 5, 18, 1, l), rekt(3, 5, 1, 14, l),
        rekt(3, 18, 18, 1, m), rekt(20, 5, 1, 14, m),
        rekt(5.5, 7.5, 13, 9, hb, True),           # bilden
        rekt(6, 8, 12, 2, hl),
        cirkel(15.5, 10.5, 1.75, yb),              # solen
        poly([(5.5, 16.5), (9.5, 11.5), (12, 14.2), (14, 12.5), (18.5, 16.5)], gb),  # bergen
        poly([(9.5, 11.5), (10.9, 13.2), (8.1, 13.2)], "#FFFFFF", False),
        poly([(6.4, 16), (9.5, 12.2), (10, 12.8), (7.6, 16)], gl, False),
    ]


def oppna():
    gl, gb, gm = P["gul"]
    pl, pb, pm = P["papper"]
    return [
        poly([(2.5, 5.5), (8.5, 5.5), (10.5, 7.5), (19.5, 7.5), (19.5, 19.5), (2.5, 19.5)], gm),  # mappens baksida
        rekt(5.5, 3.5, 11, 10, pb, True),          # papperet
        rekt(7, 6, 8, 1, pm), rekt(7, 8, 8, 1, pm), rekt(7, 10, 6, 1, pm),
        poly([(2.5, 19.5), (6.5, 11.5), (22.5, 11.5), (18.5, 19.5)], gb),          # framsidan
        rekt(7, 12, 15, 1, gl),
        poly([(3.6, 19), (6.6, 13), (7.5, 13), (4.5, 19)], gl, False),
        rekt(4, 18, 14, 1, gm),
    ]


def skriv_ut():
    l, b, m = P["gra"]
    pl, pb, pm = P["papper"]
    gl, gb, gm = P["gron"]
    return [
        rekt(6.5, 2.5, 11, 8, pb, True),           # papperet in
        rekt(8, 4, 8, 1, pm), rekt(8, 6, 6, 1, pm),
        rekt(2.5, 8.5, 19, 9, b, True),            # skrivaren
        rekt(3, 9, 18, 1, l), rekt(3, 9, 1, 8, l),
        rekt(3, 16, 18, 1, m), rekt(20, 9, 1, 8, m),
        rekt(5, 12, 12, 2, SVART),                 # springan
        rekt(18, 11, 2, 2, gb),                    # lampan
        rekt(18, 11, 1, 1, gl),
        rekt(5.5, 15.5, 13, 6, pb, True),          # papperet ut
        rekt(7, 17, 9, 1, pm), rekt(7, 19, 7, 1, pm),
    ]


def sok():
    l, b, m = P["morkgra"]
    hl, hb, hm = P["himmel"]
    vansterhalva = [
        rekt(4.5, 3.5, 5, 5, b, True),             # okularet
        rekt(5, 4, 1, 4, l),
        rekt(2.5, 8.5, 8, 9, b, True),             # tuben
        rekt(3, 9, 1, 8, l),
        rekt(9, 9, 1, 8, m),
        cirkel(6.5, 17.5, 3.5, hb),                # linsen
        cirkel(5.5, 16.5, 1, "#FFFFFF", False),
    ]
    return [rekt(10.5, 10.5, 3, 4, b, True)] + vansterhalva + spegla(vansterhalva)


def stopp():
    rl, rb, rm = P["rod"]
    ytter = [(7.5, 1.5), (16.5, 1.5), (22.5, 7.5), (22.5, 16.5), (16.5, 22.5), (7.5, 22.5), (1.5, 16.5), (1.5, 7.5)]
    inre = [(8.3, 3.5), (15.7, 3.5), (20.5, 8.3), (20.5, 15.7), (15.7, 20.5), (8.3, 20.5), (3.5, 15.7), (3.5, 8.3)]
    return [
        poly(ytter, "#FFFFFF"),
        poly(inre, rb, False),
        poly([(8.3, 3.5), (15.7, 3.5), (16.5, 4.5), (8, 4.5), (4.5, 8), (4.5, 15.5), (3.5, 15.7), (3.5, 8.3)], rl, False),
        poly([(20.5, 8.3), (20.5, 15.7), (15.7, 20.5), (8.3, 20.5), (8.5, 19.5), (15.5, 19.5), (19.5, 15.5), (19.5, 8.5)], rm, False),
        rekt(6.5, 10.5, 11, 3, "#FFFFFF", True),   # balken
    ]


KNAPPAR = {
    "bakat": ("Bakåt", "QBI_BACK", bakat),
    "framat": ("Framåt", "QBI_FORWARD", framat),
    "hem": ("Hem", "QBI_HOME", hem),
    "ladda-om": ("Ladda om", "QBI_RELOAD", ladda_om, True),
    "bilder": ("Bilder", "QBI_IMAGES", bilder),
    "oppna": ("Öppna", "QBI_OPEN", oppna),
    "skriv-ut": ("Skriv ut", "QBI_PRINT", skriv_ut),
    "sok": ("Sök", "QBI_FIND", sok),
    "stopp": ("Stopp", "QBI_STOP", stopp),
}


# ---------------------------------------------------------------- nyckeln

def nyckel(hel):
    """
    Hel: guld, en säker anslutning. Bruten: grå, i två delar med ett tydligt
    avbrott och den yttre delen nedfallen, så att skillnaden syns i 16 bildpunkter.
    """
    l, b, m = P["gul"] if hel else ("#E4E4E4", "#9C9C9C", "#5E5E5E")
    hal = "#7A5A00" if hel else "#3C3C3C"
    ut = [
        cirkel(4.5, 8, 3.5, b),                    # handtaget
        bana("M2.6 6.6 A2.4 2.4 0 0 1 5.9 5.6 L5.4 6.5 A1.4 1.4 0 0 0 3.5 7.2 Z", l, False),
        cirkel(4.5, 8, 1.25, hal),                 # hålet
    ]
    if hel:
        ut += [
            poly([(7.5, 6.5), (15.5, 6.5), (15.5, 9.5), (14.5, 9.5), (14.5, 11.5), (12.5, 11.5),
                  (12.5, 9.5), (11.5, 9.5), (11.5, 11.5), (9.5, 11.5), (9.5, 9.5), (7.5, 9.5)], b),
            rekt(8, 7, 7, 1, l),
        ]
    else:
        ut += [
            # stumpen vid handtaget, med en sågtandad brottyta
            poly([(7.5, 6.5), (10.5, 6.5), (9.7, 7.5), (10.5, 8.5), (9.7, 9.5), (7.5, 9.5)], b),
            rekt(8, 7, 2, 1, l),
            # den yttre delen, en och en halv enhet bort och fallen ett steg
            poly([(12, 7.5), (15.5, 7.5), (15.5, 10.5), (14.5, 10.5), (14.5, 12.5), (12.5, 12.5),
                  (12.5, 10.5), (12, 10.5), (12.8, 9.5), (12, 8.5)], b),
            rekt(13, 8, 2, 1, l),
        ]
    return ut


# ---------------------------------------------------------------- filerna

def dokument(w, titel, kropp):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{w}" viewBox="0 0 {w} {w}" '
            f'role="img" aria-label="{titel}"><title>{titel}</title>{kropp}</svg>\n')


def bygg():
    UT.mkdir(parents=True, exist_ok=True)
    for gammal in UT.glob("*.svg"):
        gammal.unlink()
    n = 0
    for namn, (titel, _, fn, *flagga) in KNAPPAR.items():
        siluett = bool(flagga and flagga[0])
        former = fn()
        (UT / f"{namn}.svg").write_text(dokument(24, titel, "".join(svg_form(s) for s in former)), encoding="utf-8")
        (UT / f"{namn}-inaktiv.svg").write_text(dokument(24, f"{titel}, inaktiv", inaktiv(former, siluett)), encoding="utf-8")
        n += 2
    for hel, namn, titel in ((True, "nyckel-hel", "Säker anslutning"), (False, "nyckel-bruten", "Osäker anslutning")):
        (UT / f"{namn}.svg").write_text(dokument(16, titel, "".join(svg_form(s) for s in nyckel(hel))), encoding="utf-8")
        n += 1
    return n


if __name__ == "__main__":
    print(f"{bygg()} filer i svg/webblasare/")
