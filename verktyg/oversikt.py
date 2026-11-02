#!/usr/bin/env python3
"""
oversikt.py - ritar översiktsbilderna i oversikt/ ur svg/

    python3 verktyg/oversikt.py [typsnittskatalog]

Kräver Python-paketet playwright med Chromium. Typsnittskatalogen ska ha
Manrope som manrope-latin-<vikt>-normal.woff2 (till exempel ur npm-paketet
@fontsource/manrope); utan den ritas texten i ett reservtypsnitt.

Skriver oversikt/glod.png och oversikt/gryning.png (alla komponenter vid
100 %) och oversikt/dpi.png (ett urval vid 100, 125, 150, 175 och 200 %).
"""
import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

ROT = pathlib.Path(__file__).resolve().parent.parent
SVG = ROT / "svg"
UT = ROT / "oversikt"
_T = json.loads((ROT / "tokens" / "tokens.json").read_text(encoding="utf-8"))["farg"]
# sidans bakgrund, text, dämpad text och fönsterytan som kontrollerna står på
FARG = {t: (f["bakgrund"], f["text"], f["text-dampad"], f["yta"]) for t, f in _T.items()}


def typsnitt(katalog):
    if not katalog:
        return ""
    k = pathlib.Path(katalog).resolve()
    return "".join(
        f"@font-face{{font-family:Manrope;font-weight:{v};"
        f"src:url('file://{k}/manrope-latin-{v}-normal.woff2') format('woff2')}}"
        for v in (400, 500, 600, 700, 800))


def inline(p, prefix):
    """SVG:n inbäddad, med id:n unika i dokumentet"""
    s = p.read_text(encoding="utf-8")
    s = re.sub(r'id="([^"]+)"', lambda m: f'id="{prefix}-{m.group(1)}"', s)
    return re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{prefix}-{m.group(1)})", s)


def galleri(tema, fonter):
    bg, fg, dim, yta = FARG[tema]
    delar = []
    n = 0
    grupper = sorted(p for p in (SVG / tema).iterdir() if p.is_dir())
    for g in grupper:
        kort = []
        for f in sorted(g.glob("*.svg")):
            n += 1
            kort.append(f'<figure><div class=y>{inline(f, f"i{n}")}</div>'
                        f'<figcaption>{f.stem}</figcaption></figure>')
        delar.append(f"<section><h2>{g.name}</h2><div class=rad>{''.join(kort)}</div></section>")
    glyfer = "".join(
        f'<figure><span class=g>{inline(f, f"g{i}")}</span><figcaption>{f.stem}</figcaption></figure>'
        for i, f in enumerate(sorted((SVG / "glyfer").glob("*.svg"))))
    delar.insert(0, f"<section><h2>glyfer</h2><div class=rad>{glyfer}</div></section>")
    return f"""<!doctype html><meta charset=utf-8><style>{fonter}
body{{margin:0;padding:32px;background:{bg};color:{fg};font-family:Manrope,sans-serif;width:1600px}}
h1{{font-size:28px;margin:0 0 24px}}
h2{{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:{dim};margin:28px 0 10px}}
.rad{{display:flex;flex-wrap:wrap;gap:14px 18px;align-items:flex-start}}
figure{{margin:0;display:flex;flex-direction:column;gap:4px}}
figcaption{{font-size:11px;color:{dim};font-family:monospace}}
.g{{color:{fg};display:inline-flex;padding:6px;border:1px dashed {dim}55;border-radius:6px}}
.g svg{{width:32px;height:32px}}
.y{{background:{yta};padding:8px;border-radius:10px;line-height:0}}
</style><h1>{tema} · alla komponenter vid 100 %, på fönsterytan</h1>{''.join(delar)}"""


URVAL = ["knapp/primar-fokus", "knapp/sekundar-vila", "kryssruta/pa-vila", "radioknapp/pa-vila",
         "vaxel/pa-vila", "textfalt/fokus", "titelrad/stang-hover"]


def dpi(fonter):
    skalor = (1, 1.25, 1.5, 1.75, 2)
    rader = []
    n = 0
    for tema in ("glod", "gryning"):
        bg, fg, dim, yta = FARG[tema]
        celler = []
        for s in skalor:
            items = []
            for u in URVAL:
                p = SVG / tema / f"{u}.svg"
                txt = p.read_text(encoding="utf-8")
                w = float(re.search(r'width="([\d.]+)"', txt).group(1))
                h = float(re.search(r'height="([\d.]+)"', txt).group(1))
                n += 1
                el = inline(p, f"d{n}")
                el = re.sub(r'width="[\d.]+" height="[\d.]+"', f'width="{w * s:g}" height="{h * s:g}"', el, count=1)
                items.append(el)
            celler.append(f'<div class=kol><div class=sk>{int(s * 100)} %</div>{"".join(items)}</div>')
        rader.append(f'<div class=tema style="background:{yta};color:{fg}">{"".join(celler)}</div>')
    return f"""<!doctype html><meta charset=utf-8><style>{fonter}
body{{margin:0;font-family:Manrope,sans-serif;width:max-content}}
.tema{{display:flex;gap:40px;padding:28px 32px;align-items:flex-start}}
.kol{{display:flex;flex-direction:column;gap:10px}}
.sk{{font-size:14px;font-weight:700;opacity:.8}}
svg{{display:block}}
</style>{''.join(rader)}"""


def main():
    fonter = typsnitt(sys.argv[1] if len(sys.argv) > 1 else None)
    UT.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        sida = b.new_page(device_scale_factor=1)
        for tema in ("glod", "gryning"):
            sida.set_content(galleri(tema, fonter), wait_until="networkidle")
            sida.screenshot(path=str(UT / f"{tema}.png"), full_page=True)
        sida.set_content(dpi(fonter), wait_until="networkidle")
        sida.screenshot(path=str(UT / "dpi.png"), full_page=True)
        b.close()
    print("oversikt/glod.png, oversikt/gryning.png, oversikt/dpi.png")


if __name__ == "__main__":
    main()
