# QzOS design

Temaförslag för QzOS skrivbord: **Glöd** (mörkt) och den ljusa systervarianten **Gryning**.

## Innehåll

`tema/` innehåller källfilerna från Design-ytan:

| Fil | Innehåll |
| --- | --- |
| `Main.dc.html` | Glöd – palett och tokens |
| `Desktop.dc.html` | Glöd – skrivbord |
| `Components.dc.html` | Glöd – komponenter |
| `GryningMain.dc.html` | Gryning – palett och tokens |
| `GryningDesktop.dc.html` | Gryning – skrivbord |
| `GryningComponents.dc.html` | Gryning – komponenter |
| `canvas.json` | Ytans layout: artboardens placering och storlek |

Filerna är i Design-formatet `.dc.html` och laddar ytans runtime (`./support.js`), så de visas som de är tänkta i Claude Design, inte direkt i en webbläsare.

## Färger

### Glöd (mörkt)

| Roll | Färg |
| --- | --- |
| Bakgrund | `#241B32` |
| Ytor | `#42314C` |
| Accent | `#EE7665` |
| Värme | `#FFA85D` |
| Text | `#F3F0F5` |
| Djup | `#1B1426` |
| Yta upphöjd | `#523E5D` |
| Kant | `#5A4766` |
| Dämpad text | `#C2B8CC` |
| Accent hover / tryck | `#F28A7B` / `#D9604F` |
| Lyckat | `#8FD5B0` |
| Fel | `#FF7E9D` |

### Gryning (ljust)

| Roll | Färg |
| --- | --- |
| Bakgrund | `#F6F1F4` |
| Ytor | `#FFFFFF` |
| Accent (fyllnad) | `#EE7665` |
| Accent text | `#B03F30` |
| Värme (fyllnad) | `#FFA85D` |
| Värme djup (fokus, länkar) | `#A8520F` |
| Text | `#241B32` |
| Yta sänkt | `#EFE7EE` |
| Kant | `#DDD0DC` |
| Dämpad text | `#6B5A78` |
| Lyckat | `#237A52` |
| Fel | `#C2335A` |

## Regler

- Korall betyder *aktivt eller valt*. Bärnsten betyder *titta här*: fokus, länkar, varningar.
- Text på korall och bärnsten är alltid mörk (`#241B32`). Ljus text på korall klarar inte kontrastkraven.
- Fel visas alltid med ikon och text, inte bara med färg.
- Typsnitt: Manrope (gränssnitt), JetBrains Mono (terminal och kod). Hörnradier 8 / 14 / 22 px, rutnät 4 px.
