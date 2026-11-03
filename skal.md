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
| Fler program | `overflode/` | vila, öppen, uppmärksamhet | två pilknappar som rullar raderna |
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
- 31 nya glyfer i `svg/glyfer/` för skalet: ström, wifi, volym, batteri,
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

## Beteende i gränsfallen

Det här är beteendekontrakt för skalet och libui, inte bara för
lekplatsen. Lekplatsen gör så här, och det går att pröva där.

### Smal skärm och hög skala

Allt räknas i u, så en hög skala gör skärmen smalare i u. Vid 200 % är
en skärm om 1920 bildpunkter 960 u bred.

- **Start-panelen** är 640 u bred, men aldrig bredare än skärmen minus
  8 u på var sida. Rutnätet med fästa program tar så många kolumner om
  minst 92 u som ryms, och listan Senaste så många om minst 240 u.
- **Översikten** i Start visas bara när panelen ryms med den, alltså när
  skärmen är minst 896 u bred. Annars visas den kompakta panelen, även
  om översikten är vald.
- **Fönster** öppnas och hålls inom arbetsytan: ett fönster blir aldrig
  större än arbetsytan minus 16 u, och minst 120 u av titelraden går
  alltid att nå. Fönstret minns sin egen storlek och får tillbaka den
  när det finns plats.
- **Ett maximerat fönster** följer arbetsytan när fältet byter form
  eller skalan ändras.

### Överflöd i fältet

- Programknappar som inte ryms samlas bakom en **Mer-knapp** sist i
  gruppen, med glyfen `mer`. Den öppnar en meny med programmen och om
  de är öppna eller minimerade.
- **Det aktiva programmets knapp syns alltid.** Ligger den bland de
  dolda byter den plats med den sista synliga.
- Mer-knappen har markören för öppen om något dolt program har fönster,
  och uppmärksamhetens markör om något av dem ber om uppmärksamhet.
- Hur många knappar som ryms räknas om när fönster öppnas och stängs,
  när skärmen ändrar storlek och när skalan eller fältets form byts.

### Fokusets livscykel

1. **Panel eller meny öppnas** (Start, snabbinställningarna,
   aviseringarna, strömmenyn, Mer): skalet minns var fokus var, och
   fokus flyttas in i panelen. Start får fokus i sökfältet, så att det
   går att skriva direkt. De andra får fokus på sin första knapp.
2. **Escape, eller samma knapp igen,** stänger och lämnar tillbaka fokus
   dit det var. En meny lämnar tillbaka fokus till knappen som öppnade
   den.
3. **Något väljs i panelen:** det som öppnas får fokus, inte det som
   hade fokus före.
4. **Ett klick utanför** stänger panelen, och fokus stannar där klicket
   hamnade.
5. **Ett fönster som aktiveras** får fokus där det var senast i
   fönstret, annars i första fältet, annars i fönstret självt.
6. **Ett aktivt fönster som minimeras eller stängs** lämnar fokus till
   nästa fönster i z-ordningen. Finns inget får skrivbordet fokus.
7. **Låsskärmen** minns fokus på samma sätt och lämnar tillbaka det när
   den låses upp.

Tangenter:

- **Ctrl+Esc** öppnar och stänger Start, som i NT. **Super** ensam gör
  samma sak.
- **Pil upp och ned, Home och End** flyttar mellan objekten i en meny.

I generic_gdi behöver punkt 1 och 2 regeln för att skalet får ta fokus
(F3 i `docs/shell.md`), och punkt 5 att libui minns fokus per fönster
när det inaktiveras.

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
