# OSM Fulda – Drucksachen

Visitenkarten und Aushang für [OpenStreetMap Fulda](https://wiki.openstreetmap.org/wiki/Fulda),
im Stil des OSM-Fulda-Titelbilds (Schrift *Barlow Condensed*, Textfarbe `#2d3335`).

| Ordner | Was | Druckdatei |
|---|---|---|
| `mitmachkarte/` | Visitenkarte 85×55, doppelseitig: vorne Titelbild, hinten 6 QR-Codes (Info, Wiki, Matrix, StreetComplete, OSMapp, Panoramax). Für Leute, die schon Interesse haben. | `mitmachkarte-a4.pdf` |
| `infokarte/` | Visitenkarte 85×55, einseitig, zum Liegenlassen (Wartezimmer …): Logo, Aufhänger, 2 QR-Codes. | `infokarte-a4.pdf` |
| `aushang/` | A5 für Schaufenster/Scheiben, beidseitig gleich bedruckt. Variante mit Mitmach-Rückseite als Vorlage für einen späteren Profidruck. | `aushang-a4.pdf`, `aushang-mit-rueckseite-a4.pdf` |
| `gemeinsam/` | `druck.py` (Schrift, QR, Logo, URLs), `make_a4.py` (Druckbogen), Schriften, Logo, Titelbild | – |

## Bauen

```sh
python3 mitmachkarte/make_mitmachkarte.py
python3 infokarte/make_infokarte.py
python3 aushang/make_aushang.py
```

Braucht: Python 3 mit `qrcode`, `fonttools`, `Pillow`; `rsvg-convert` (librsvg); optional `gs`
(Ghostscript – komprimiert die Bögen von ~18 MB auf ~2 MB). Zum Prüfen der Codes: `zbarimg`.
Die Schriften werden aus `gemeinsam/fonts/` geladen, installieren ist nicht nötig.

Texte, Labels und URLs stehen jeweils oben im Skript, gemeinsame URLs in `gemeinsam/druck.py`.

**Achtung:** Die Skripte überschreiben die SVGs. Wer eine SVG in Inkscape nachbearbeitet, baut den
Bogen danach nur noch mit `gemeinsam/make_a4.py` (siehe Kopf der Datei). Für Inkscape vorher
`gemeinsam/fonts/*.ttf` nach `~/.local/share/fonts/` kopieren.

## Drucken

- Immer **100 % / tatsächliche Größe**, nie „an Seite anpassen“.
- **Visitenkarten** (A4 hoch): Duplex **an langer Kante spiegeln**. 10 Karten pro Bogen.
- **Aushang** (A4 quer, 2× A5): Duplex **an kurzer Kante**; vorher einen Bogen testen.
- Dicker Karton (> ~105 g/m²) wird vom Drucker oft nicht automatisch gewendet → manuell:
  erst Seite 1, Stapel wenden, dann Seite 2.
- Fürs Fenster mind. 160–200 g/m², sonst scheint die Rückseite durch.

## Schneiden

Die Karten liegen ohne Abstand aneinander – ein Schnitt pro Kante. Die **Vorderseite** hat
durchgehende hellgraue Haarlinien über den ganzen Bogen, sie bleiben nach jedem Schnitt sichtbar.
**Mit der Vorderseite nach oben schneiden**, Klinge genau auf die Linie. Die Rückseite hat
absichtlich keine Linien (Duplex-Versatz von 1–2 mm würde sie auf die Karte schieben); die
schwarzen Randmarken dort zeigen gegen das Licht, wie weit die Rückseite versetzt ist.

## Lizenzen

- Schrift Barlow Condensed: SIL Open Font License, siehe `gemeinsam/fonts/OFL.txt`.
- Kartendaten im Titelbild: © OpenStreetMap-Mitwirkende, ODbL.
