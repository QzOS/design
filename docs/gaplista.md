# Gaplistan: målbilden mot det som finns

Vad som saknas mellan [`mal.md`](../mal.md) och [`skal.md`](../skal.md) och
det som finns i generic_gdi och gfx_v3d. Underlag för att anpassa designen till
mekanismerna, med de beslut som tagits. Läget gäller 4 november 2026.

Märkning av vad en uppgift bygger på:

- **mätt:** provat på Pi 400.
- **kod:** läst i koden. Inte provat.
- **bedömning:** min uppskattning.

## Sammanfattning

1. **Mekaniken för mått och typsnitt finns nu.** En profil är en textfil med egna
   mått, typsnitt och färger, med arv. Den går att byta med fönster öppna och
   sprids av skalet till alla program. Se
   [Profiler i generic_gdi](#profiler-i-generic_gdi).
2. **Rundade fönsterhörn går att göra i kompositören,** utan ny shader och utan
   att röra kontrollkoden. Kostnaden är rimlig (mätt). Beslutat, inte byggt.
3. **Skuggorna i `mal.md` håller 60 Hz** med fem stora överlappande fönster, men
   inte med tolv, om alla har högsta nivån (mätt). `mal.md` ger inte alla fönster
   högsta nivån, och det är inte mätt med rätt blandning än.
4. **Kontrollhöjd 32 u är nära för dialoger.** De räknas i dialogenheter, och
   knapparna är redan 29 bildpunkter (mätt). Det som är placerat i bildpunkter
   ändras inte av sig självt.
5. **Fyra krav i `mal.md` stämmer inte längre,** se
   [Skillnader mot `mal.md`](#skillnader-mot-malmd).

## Profiler i generic_gdi

Det som byggts sedan listan skrevs (generic_gdi#460):

- **Uppdelning:** DPI är samma design i annan storlek. En profil är en annan
  design. En profil ger nominella värden, och fönstrets DPI realiserar dem.
- **Filer:** `NAME.profile` med `[profile]`, `[metrics]`, `[fonts]` och `[colors]`,
  i katalogen `UI_PROFILEDIR`. En saknad nyckel ärvs, ett värde gäller även om det
  är 0, och `auto` går efter typsnittet. Classic och Flat är inbyggda.
- **Källan:** `tokens.json` i det här repot. `tools/gen-profiles.py` i generic_gdi
  skriver `profiles/glod.profile` och `gryning.profile`. Vid försök går det lika bra
  att lägga en egen fil med `parent=gryning` och några nycklar.
- **Byte:** en transaktion. Ett toppfönster behåller klientytans storlek, en dialog
  följer basenheterna, och skalet väljer för alla.
- **Mått som läses:** titelrad, knappcell och synlig knapp, ram, resize-zon utanför
  fönstret, menyrad, rader i lista och träd, menyobjekt, header, flik, statusrad,
  kombinationsruta, kryssruta och textfältets marginal.
- **Inte i filen än:** hörnradier och skuggor, som kommer härnäst, samt
  ritfunktioner. `draw=` väljer bara mellan Classic och den tillfälliga platta.

## Proven

Proven ligger på grenar som inte ska slås ihop: `spike/rounded-corners` i
gfx_v3d och `spike/control-height` i generic_gdi.

### Rundade hörn och skuggor

Verktyget är `tools/spike_round.c`. Fönster om 800 × 600 överlappar varandra på
en 1920 × 1080-utbild i skärmens format (RGBX8). Tiden är från `comp_frame` till
dess fence, medianen, utan klientens arbete. **Flytt** är ett fönster som flyttas
8 bildpunkter, **helbild** är hela utbilden. En bildruta har 16,7 ms.

Hörnen: masken skrivs till utbildens alfakanal, och fönstret blandas mot den.
Det kräver sex ytor per fönster men ingen ny shader. Skuggan följer de rundade
hörnen. Hörnradie 12, skugga 56 u och 24 u nedåt, alltså höjd 3 i `mal.md`.

| Variant | Fönster | Ytor | Helbild ms | Flytt ms |
|---|---:|---:|---:|---:|
| Raka hörn, ingen skugga | 1 | 1 | 2,26 | 2,06 |
| Dagens ring, radie 10 | 1 | 9 | 2,81 | 2,76 |
| Skugga enligt `mal.md` | 1 | 10 | 3,07 | 3,34 |
| Rundade hörn | 1 | 6 | 3,14 | 2,96 |
| Rundade hörn och skugga | 1 | 15 | 4,03 | 4,25 |
| Raka hörn, ingen skugga | 5 | 5 | 4,83 | 3,41 |
| Dagens ring, radie 10 | 5 | 45 | 8,00 | 6,54 |
| Skugga enligt `mal.md` | 5 | 50 | 9,37 | 8,86 |
| Rundade hörn | 5 | 30 | 9,51 | 6,98 |
| Rundade hörn och skugga | 5 | 75 | 14,09 | 12,71 |
| Raka hörn, ingen skugga | 12 | 12 | 9,37 | 3,70 |
| Dagens ring, radie 10 | 12 | 108 | 16,85 | 10,55 |
| Skugga enligt `mal.md` | 12 | 120 | 20,03 | 12,66 |
| Rundade hörn | 12 | 72 | 19,94 | 9,87 |
| Rundade hörn och skugga | 12 | 180 | 30,72 | 19,54 |

Slutsatser:

- **Fem stora fönster går bra:** rundade hörn och skugga klarar 60 Hz med
  marginal för klienten. Tolv klarar det inte.
- **Allt ritas i dag, också det som är helt skymt.** Kompositören hoppar inte över
  skymda fönster (kod). Det är troligen den billigaste förbättringen, men den är
  inte mätt.
- **Skugga bara på översta fönstren.** `mal.md` ger redan inaktiva fönster höjd 2,
  och en mindre skugga kostar mindre. Det är inte mätt.
- **Batchgränsen:** 15 ytor per fönster ger högst 17 fönster inom gränsen på 256
  batchar. Den gränsen är tillfällig (generic_gdi#459).

Inte provat: på riktig skärm genom winsrv, annan hörnradie än 12, och hur
kanten upplevs. Bilden är bedömd offline, och provets skuggfyllning har små hack
nere i hörnen, vilket är provets förenkling.

### Kontrollhöjd

Dialoger från mallar räknas i dialogenheter, som mäts ur gränssnittstypsnittet.
Ett större typsnitt gör alltså hela dialogen större utan kodändring. Knappen är
den vanliga mallens 14 enheter hög:

| Typsnitt | Basenheter | Knapphöjd | Knappbredd 50 enheter |
|---|---|---:|---:|
| Dagens "ui", 13 | 8 × 17 | 29 | 100 |
| IBM Plex Sans 13 | 7 × 18 | 31 | 87 |
| IBM Plex Sans 14 | 8 × 19 | 33 | 100 |
| IBM Plex Sans 15 | 9 × 21 | 36 | 112 |

Plex är en ställföreträdare, eftersom Manrope inte finns här. Manropes värden är
inte mätta. `sysprop` ser riktig ut vid Plex 14. `schemes`, placerad i
bildpunkter, behåller sina mått och blir trängre, men går inte sönder. Med mått från profilen får listan färre rader i sin fasta höjd.

Det gör att 32 u i praktiken blir en fråga om typsnitt för dialoger, medan det
som är placerat i bildpunkter måste ses över. I exemplen finns 71 `ui_create`,
och Paint, Program Manager och UI Designer har tillsammans 30 till (kod, räknat
med `grep`, inte alla är kontroller).

## Mekanismerna

| Krav i `mal.md` | Läge | Vad som saknas | Storlek |
|---|---|---|---|
| Skala per fönster | Klart i #439, fysiska bildpunkter (kod) | Byte av skala medan programmet kör | Medel |
| Mått per profil | Klart i #463–#469 (kod, mätt) | Fler mått när komponenterna ritas | Liten var |
| Ett gemensamt ritlager | Sömmen finns, `src/ui/theme.[ch]` (kod). Cirka 75 direkta anrop går inte genom den (`grep`) | Funktion per komponent och läge, med roller | Stor |
| Hover | `ui_trackleave` och `MSG_MOUSELEAVE` finns, men ingen kontroll använder dem (kod) | Kontrollerna måste spåra läget | Medel, per kontroll |
| Fokus från tangentbordet | Hittar inget (kod) | Ett läge per fönster, motsvarande `WM_UPDATEUISTATE` | Liten |
| TrueType i gränssnittet | Klart: Manrope och JetBrains Mono från `UI_FONTDIR` (mätt) | Hur de levereras i ett riktigt system | Liten |
| Alfa hela vägen | Skuggor, konstant alfa och `WNDX_LAYERED` klart i #450 (kod). Inte i `MSG_PAINT`, och beslutet gör det onödigt för hörnen | Inget för hörnen | Se beslut 1 |
| Animering i takt med skärmen | `ui_requestframe` och `MSG_FRAME` klart i #435 (kod) | Övergångar i kontrollerna | Medel |
| Ikoner och glyfer | libsvg med cache finns (kod) | Glyferna byggda till typsnitt eller ritade med libsvg. Titelradens symboler är för stora i dag | Liten |

## Komponenterna

Storleken är en bedömning, utan de gemensamma kraven ovan.

| Komponent | Det nya mot i dag | Storlek |
|---|---|---|
| Fönster | Titelrad och ram klara. Kvar: rundade hörn och skugga per höjd | Medel |
| Storleksgrepp | Klart: 6 u utanför kanten, 12 u i hörnen, genom servern (generic_gdi#466) | Klart |
| Titelradsknappar | Mått klara. Kvar: hover och nya glyfer | Liten |
| Knapp | Primär, sekundär, kontur, fara. I dag finns en sort | Medel, kräver stil i API:t |
| Kryssruta, radio | 18 u, fyllda | Liten |
| Växel | Ny kontroll | Liten |
| Textfält, kombinationsruta | Rundade, 32 u, fokusring | Medel. Kantutjämnade former över klientens yta finns genom `gdi_composite` |
| Rullningslist | Smal, breddas vid hover, **inga pilknappar**. Beteendeändring i en stor kontroll, och krockar med princip 6 | Medel |
| Listrad, trädrad, header | Radhöjd 28 u, hover | Medel |
| Flik | Understrykning i stället för kortflikar. Ritningen är en av de direkta | Medel |
| Meny | Rundad popup med skugga, 30 u rader. `menu.c` ritar direkt | Medel |
| Tips, statusrad, gruppram, förlopp, reglage, splitter, upp/ned, verktygsknapp | Färger, former och hover | Liten var |
| Dialog | Signalikoner i `ui_msgbox`, knappar i höjd 32 u | Liten |

## Skalet

| Komponent | Läge | Vad som saknas | Storlek |
|---|---|---|---|
| Fältet, flytande eller dockat | `taskbar.c`, dockat. Arbetsyta finns | Rundad form med skugga, ikoner i stället för text | Medel |
| Start-panel, sök | Ägarritad meny | Sökfunktion, ny panel | Stor |
| Förhandsvisning av fönster | Nej | Protokollet kan inte visa en annans fönster (kod). Kräver stöd i servern | Medel |
| Snabbpanel | Nej | Reglagen behöver data om nät, ljud och batteri, som saknas helt (kod). Inte en grafisk fråga | Stor |
| Aviseringar | Nej | Protokoll mellan program och skal | Medel |
| Bakgrundsbild | libsvg kan rita (kod) | Skrivbordsfönstret ritar den | Liten |

## Skillnader mot `mal.md`

Jag har inte ändrat `mal.md`. Det här är förslag.

1. **Krav 1, logiska koordinater.** `mal.md` säger att libui räknar i u. Beslutet i
   generic_gdi#439 blev tvärtom: libui och GDI behåller **fysiska bildpunkter**, och
   en profil anger u som realiseras. Regeln `max(1, floor(u × s))` för kanter gäller
   och är byggd för en profils linjer.
2. **Krav 3, hover,** beskrivs som saknat. Mekanismen finns (`ui_trackleave`). Det
   som saknas är att kontrollerna använder den.
3. **Krav 6 säger** att skuggor och rundade hörn kräver alfa från libgdi till
   kompositören. Skuggor finns utan det. Enligt beslut 1 görs hörnen också utan.
4. **Skalorna.** `mal.md` har fasta steg per skärm. #439 tar godtyckligt DPI från
   48 till 960 per fönster. Fasta steg går att välja i skalet.
5. **Rullningslisten och princip 6.** Att ta bort pilknapparna ändrar träffytorna,
   som princip 6 säger ska vara desamma. Öppen.

## Beslut

1. **Kompositören äger de yttre fönsterhörnen.** Äldre program får rundade hörn utan
   PARGB-ytor och utan att ändra sin ritning. Radie eller fönsterroll är metadata per
   fönster, inte en enda radie. Musen går på hela rektangeln tills vidare. Hörnen
   ska också fungera utan GPU, eftersom generic_gdi inte är knutet till gfx_v3d.
2. **Ordning:** typsnitt och kontrollmått, ram och titelrad, hörn och skuggor,
   visuell integration. De två första är klara.
3. **Skuggnivå per roll** enligt `mal.md`: 1 för tips och små popuper, 2 för inaktiva
   fönster och menyer, 3 för aktivt fönster och dialoger. Skuggor är av som
   systemstandard. Cachad geometri, damage-begränsning och att hoppa över skymda
   delar mäts före eventuell dynamisk kvalitet.
4. **Profiler är data,** enkla textfiler. Ett byte är en transaktion. Klientytan
   behålls, och dialogens barn skalas med basenheterna.

## Öppna frågor

1. **Ska kod placerad i bildpunkter, som `schemes`, följa med,** eller räcker det att
   nya och mallbaserade dialoger gör det?
2. **Skalets snabbpanel** behöver systemtjänster som inte finns. Är den med i första
   versionen?
3. **Rullningslisten** utan pilknappar, se ovan.
