# QzOS design

Presentationen för QzOS skrivbord: temana **Glöd** (mörkt) och
**Gryning** (ljust), komponenterna som SVG i logiska enheter och målet
för hur de ska ersätta NT 4.0 Classic. Börja med [`mal.md`](mal.md), och
[`skal.md`](skal.md) för skalet. `lekplats/index.html` är skalet att prova
i en webbläsare.

![Glöd](oversikt/glod.png)

## Innehåll

| | |
|---|---|
| `mal.md` | målet: principer, skalning, lägen, komponenterna, krav på mekaniken, öppna frågor |
| `skal.md` | skalets färdriktning: komponenterna, måtten, vad mekaniken behöver |
| `lekplats/` | skalet att använda i en webbläsare; `index.html` byggs ur `mall.html` |
| `tokens/tokens.json` | källan: färgroller för båda temana, mått, radier, typ, skuggor, rörelse och kopplingen till `COL_*` |
| `tokens/glod.css`, `tokens/gryning.css` | rollerna och måtten som CSS-variabler (genererade) |
| `svg/glyfer/` | 59 symboler, 16 u, i `currentColor` |
| `svg/appikoner/`, `svg/logo.svg`, `svg/bakgrund/` | programikoner, QzOS-märket och bakgrundsbilden Dyner |
| `svg/glod/`, `svg/gryning/` | varje komponent i varje läge, en fil per läge; skalets under `skal/` |
| `oversikt/` | kontrollerna och skalet per tema, och ett urval vid 100–200 % (genererade) |
| `docs/dpi.md` | alla mått i bildpunkter vid varje skala (genererad) |
| `verktyg/` | `bygg.py` bygger SVG, CSS, DPI-tabellen och lekplatsen; `oversikt.py` ritar översikterna |
| `tema/` | de första skisserna från Design-ytan, i formatet `.dc.html` |

## Bygga

```sh
python3 verktyg/bygg.py
python3 verktyg/oversikt.py <katalog med manrope-latin-*-normal.woff2>
```

`bygg.py` behöver bara Python. `oversikt.py` behöver Python-paketet
playwright med Chromium. Manrope finns till exempel i npm-paketet
`@fontsource/manrope`.

## Kort om temana

- 1 u = 1 bildpunkt vid 96 dpi. Storlekar avrundas, kanter blir hela
  bildpunkter, se `mal.md`.
- Korall betyder *aktivt eller valt*, bärnsten *titta här*: fokus,
  länkar och varningar. Text på korall och bärnsten är alltid mörk.
- Fel visas alltid med ikon och text, inte bara med färg.
- Typsnitt: Manrope för gränssnittet, JetBrains Mono för terminal och
  kod.
- Radier: 5 u (kryssruta, tips), 8 u (kontroller), 12 u (fönster,
  menyer, dialoger), 22 u (paneler).
