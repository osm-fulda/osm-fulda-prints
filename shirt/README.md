# Shirt-Motive

Motive für den DTF-Druck (Direct to Film). Die PNGs in diesem Ordner lädt man beim Druckdienst hoch;
Quellen und Skripte liegen in `quelle/`.

<img src="vorschau.png" width="700" alt="Shirt-Motive">

| Datei | Motiv |
|---|---|
| `grosslogo-linie-hell.png` | großes Logo als flache Linienzeichnung, 27,8 cm breit |
| `pocketlogo-flaeche-dunkel.png` | Brustlogo mit gefüllter Karte für dunkle Shirts, mit heller Kontur |
| `stadtplan-lupe-detail-hell.png` | Stadtplan Fulda, 27 cm breit, Lupe über Dom und Schloss mit 2× Zoom: Gärten, Wege, Bäume, Brunnen |
| `stadtplan-lupe-detail-dunkel.png` | derselbe Stadtplan für dunkle Shirts (schwarz, dunkelgrau, marineblau, olivgrün): helle Straßen und Schrift, helle Kontur um Lupe und Griff |
| `tags-mapper-hell.png` | der Mensch im Shirt als Mapper-„Objekt“ im Stil des iD-Editors, mit `name=FIXME` |
| `tags-mapper-dunkel.png` | dasselbe für dunkle Shirts: helle Schrift und Rahmen |

## Bauen

```sh
quelle/build.sh            # Schriften kommen aus ../gemeinsam/fonts
```

Braucht zusätzlich zu den Werkzeugen der Haupt-README ImageMagick (`magick`).

`build.sh` erzeugt auch `pocketlogo-linie-hell` und `tags-fulda-hell`. Die sind nicht in Gebrauch:
PNGs danach löschen und `python3 quelle/vorschau.py ../gemeinsam/fonts` neu laufen lassen.

## Druckgrenzen prüfen

```sh
quelle/check.sh MOTIV.svg BREITE_MM ausgabe.png
```

Rot im Ergebnis: Farbe dünner als 1 mm (der Film kann sich in der Wäsche lösen).
Blau: Lücken schmaler als 0,5 mm (können im Druck zulaufen).

## Daten

Der Stadtplan kommt aus OpenStreetMap: Overpass-Abfragen `quelle/stadtplan.overpassql`,
`lupe.overpassql` und `detail.overpassql`, Ergebnisse in `quelle/*-osm.json`. Das aussortierte Motiv
`tags-fulda-hell` nutzt den echten Ortsknoten Fulda (`fulda-node.overpassql`). Neu holen, je Abfrage:

```sh
curl --data-urlencode data@stadtplan.overpassql https://overpass-api.de/api/interpreter -o stadtplan-osm.json
```

Kartendaten © OpenStreetMap-Mitwirkende, ODbL; der Stadtplan zeigt die Namensnennung.

## Mapper-Namen

`tags.py` erzeugt für jede Zeile in `quelle/mapper-namen.txt` eigene Motive `tags-mapper-NAME-hell`
und `tags-mapper-NAME-dunkel`.
Die Datei und diese Motive enthalten echte Namen und sind per `.gitignore` vom Repo ausgeschlossen.
