# Skalet: färdriktning

Skalet i generic_gdi (`examples/shell/`) följer i dag Shell95-skissen:
aktivitetsfält längs en kant, Start-meny med banderoll och skrivbord med
ikoner ur `~/Desktop`. Mekaniken finns: en knapp per fönster genom
skalprotokollet, programstart, senaste dokument, Kör, Avsluta, ikoner som
markeras, öppnas, flyttas och döps om, och klockan.

Det här dokumentet är riktningen för hur skalet ska se ut och kännas,
inte hur det ser ut i dag. Det är brainstorming: komponenterna finns för
att prova, och lekplatsen för att se dem tillsammans. Formen går mot ett
modernt skrivbord med ett flytande fält och en Start-panel. Den ska vara
QzOS egen, inte en kopia av något annat system.

![Skalet i Glöd](oversikt/skal-glod.png)

## Lekplatsen

`lekplats/index.html` är skalet att använda i en webbläsare: fönster som
öppnas, aktiveras, minimeras, maximeras och dras, Start med sök och alla
program, snabbinställningar, aviseringar, förhandsvisning av fönster,
strömmenyn med låsskärm, och skrivbordsikoner. Reglagen byter tema,
skala (75–200 %), fältets form och placering, Start-panelens variant
och bakgrund. Terminalen förstår `hjälp`, `ls`, `tema`, `skala` och
`öppna`.

Sidan byggs av `verktyg/bygg.py` ur `lekplats/mall.html`. Färgerna och
måtten kommer ur `tokens/tokens.json`, och glyferna, programikonerna och
bakgrunden ur samma kod som SVG-filerna. Ändras en token ändras
lekplatsen med den.

## Komponenterna

Filerna ligger under `svg/<tema>/skal/`.

| Komponent | Filer | Lägen | Finns i skalet i dag |
|---|---|---|---|
| Aktivitetsfältet | `falt/` | flytande, dockat | `taskbar.c`, dockat längs en kant |
| Programknapp | `programknapp/` | vila, hover, tryck, öppen, aktiv, uppmärksamhet, fokus | en knapp per fönster, med text i stället för ikon |
| Start-knapp | `startknapp/` | vila, hover, öppen | Start-knappen, nedtryckt när menyn är uppe |
| Bricka och klocka | `bricka/` | vila, hover, öppen | bara klockan |
| Start-panelen | `startpanel/` | kompakt, med översikt, sök | Start-menyn som ägarritad popup |
| Strömmenyn | `strommeny/` | | Avsluta |
| Snabbpanelen | `snabbpanel/` | | nej |
| Avisering | `avisering/` | | nej |
| Förhandsvisning | `forhandsvisning/` | | nej |
| Skrivbordsikon | `skrivbordsikon/` | vila, hover, vald, vald med fokus, byter namn, markeringsruta | `desktop.c`, utom markeringsrutan |

Dessutom, gemensamt för båda temana:

- `svg/appikoner/`: tolv programikoner för programmen i
  `generic_gdi/examples` och några som skalet behöver plats för, samt
  stora mapp- och filikoner för skrivbordet.
- `svg/logo.svg`: QzOS-märket, en sol vid horisonten.
- `svg/bakgrund/`: bakgrundsbilden Dyner i båda temana.
- 30 nya glyfer i `svg/glyfer/` för skalet: ström, wifi, volym, batteri,
  lås, avisering och andra.

## Mått

| Mått | u |
|---|---|
| Fältets höjd | 56 |
| Fältets avstånd från kanten, flytande | 8 |
| Knappcell i fältet | 44, ikonen 32 |
| Markören under en knapp | 6 × 3 öppen, 16 × 3 aktiv |
| Start-panelen | 640 bred, 880 med översikt |
| Snabbpanelen och aviseringarna | 360 breda |
| Skrivbordsikon | cell 88 × 100, ikon 48, etikett högst två rader |
| Programikon | 48, hörnradie 27 % |

Arbetsytan (`ui_setworkarea`) är skärmen utom fältet och dess avstånd:
72 u nedtill för det flytande fältet, 56 u för det dockade.

## Vad mekaniken behöver

Det mesta av beteendet finns. Det här saknas för att skalet ska se ut så
här. Inget av det byggs nu.

1. **Fönsterikoner i skalprotokollet.** Programknapparna visar ikoner,
   och protokollet bär inga i dag. Knappar för fästa program behöver
   också en lista i skalets inställningar, bredvid genvägarna under
   `shell/programs`.
2. **Uppmärksamhet.** Ett program ska kunna be om uppmärksamhet,
   motsvarande `FlashWindow`. Knappen får då en bärnstensfärgad markör.
3. **Miniatyrer.** Förhandsvisningen behöver fönstrets bild från
   servern, som redan håller den (`gfx_image_share_desc`).
4. **Start som panel.** Start-panelen är ett eget popupfönster med sök,
   rutnät och listor, inte en ägarritad meny. Tangentbordet behöver
   regeln för att skalet får ta fokus (F3 i `docs/shell.md`).
5. **Sök.** En källa som söker i program, senaste dokument och
   inställningar, gärna genom libshells namnrymd.
6. **Meddelandefältet.** Snabbpanelen och aviseringarna kräver det lilla
   protokoll som är uppskjutet tills en klient behöver det, och tjänster
   för nätverk, ljud och ström som rutorna kan styra.
7. **Alfa och oskärpa.** Fältet och panelerna är halvgenomskinliga med
   oskärpa bakom. Det kräver alfa i kompositören, område 3 i #393.
   Utan det ritas de täckande, vilket också ser rätt ut.
8. **Skalning och animering.** Allt är i u och följer `mal.md`.
   Panelerna glider in på `rorelse.medel` (200 ms), vilket kräver
   animering i takt med `WS_FRAME`.

## Öppna frågor

1. Ska fältet vara flytande eller dockat som standard?
2. Centrerat eller vänsterställt?
3. Ska Start-panelen ha översikten, och vad hör hemma i den?
4. Ska fästa program och öppna fönster dela knapp, som här, eller
   ligga i var sin grupp?
5. Behövs virtuella ikoner på skrivbordet, som Papperskorgen?
