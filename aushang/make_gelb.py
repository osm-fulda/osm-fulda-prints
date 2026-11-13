#!/usr/bin/env python3
"""Aushang für politisch Interessierte: „OpenStreetMap gehört DIR.“ (A5, gezeichnet auf A4).

  aushang-gelb.png, aushang-gelb-a4.pdf (Bogen, 2x A5)

Motiv der Zielgruppe: Mitbestimmung, Macht über Daten, Unabhängigkeit von Konzernen.
Nur Typografie auf Gelb; funktioniert auch als Schwarzweiß-Kopie.
"""
from common import INK, M, TW, druck, text, cap, fit, bottom, page, build

YELLOW = "#ffd43b"
# Feste Zeilenumbrüche nach Sinn. DHL: Sendungsverfolgung und Filialsuche auf dhl.de seit April 2024
# (laut Presseberichten, nicht offiziell angekündigt).
BODY = ["Wer die Daten macht, bestimmt, was man findet.",
        "OpenStreetMap steckt in Komoot, Wikipedia und bei DHL.",
        "Über zwei Millionen Freiwillige machen die Daten –",
        "und kein Konzern kann sie für sich allein behalten."]


def poster():
    out = []
    small = ["Google Maps gehört Google.", "Apple Maps gehört Apple."]
    ss = fit(small + ["OpenStreetMap gehört"], 600, 17)
    y = M + 6 + cap(600, ss)
    for l in small:
        out.append(text(M, y, l, ss, 500, "#6b5a12"))
        y += ss * 1.25
    y += 4
    out.append(text(M, y, "OpenStreetMap gehört", ss, 700, INK))
    big = 112
    y += 8 + cap(700, big)
    out.append(text(M - 3, y, "DIR.", big, 700, INK))
    y += 16
    # Motiv der Zielgruppe: Mitbestimmung, Macht über Daten, Unabhängigkeit von Konzernen.
    # Feste Zeilenumbrüche nach Sinn.
    for i, line in enumerate(BODY):
        y += (druck.cap_height(600 if i == 0 else 500, 7.4) if i == 0 else 7.4 * 1.32)
        out.append(text(M, y, line, 7.4, 600 if i == 0 else 500, INK))
        assert druck.text_width(line, 600, 7.4) <= TW, line
    bottom(out, INK, "#6b5a12", INK,
           "Bestimm mit, was über deine Stadt drinsteht. Scan und leg los.",
           "Die App StreetComplete stellt dir kurze Fragen. Jede Antwort ist sofort für alle sichtbar.",
           url=druck.go("a/gelb"), qs=44, s1=8.6, s2=5.2, w1=700)
    return page(YELLOW, out)


if __name__ == "__main__":
    druck.use_project_fonts()
    build("aushang-gelb", poster())
