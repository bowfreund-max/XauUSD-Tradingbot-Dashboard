# XAUUSD Tradingbot Dashboard

Browser-only XAUUSD dashboard designed for GitHub Pages.

## Funktionen
- XAU/USD-Kurs und Kursverlauf über Twelve Data
- Zeitrahmen M1, M5, M15 und H1
- EMA-Trend und Range-Breakout-Analyse
- Signal-Score von 0 bis 100 als einfache technische Bewertung
- Manuelle Übernahme von BUY-/SELL-Signalen aus öffentlichen Telegram-Kanälen
- Paper-Trading mit virtuellem Startguthaben von 1.000 USD
- 0,5 % simuliertes Kontorisiko pro Trade und maximal zwei offene Trades
- Speicherung von API-Key, Signalen und Paper-Trades lokal im Browser

## GitHub Pages verwenden
1. Öffne im Repository **Settings → Pages**.
2. Wähle unter **Build and deployment** die Quelle **GitHub Actions**.
3. Warte, bis der Workflow **Deploy static dashboard to GitHub Pages** erfolgreich abgeschlossen ist.
4. Öffne danach die veröffentlichte Pages-Adresse.

Nach der Veröffentlichung läuft das Dashboard direkt im Browser. Es ist keine Python-Installation, kein lokaler Connector und keine MT5-Verbindung erforderlich.

## Kursdaten einrichten
- Trage im Dashboard deinen eigenen Twelve-Data-API-Key ein und speichere ihn.
- Der Kurs wird etwa alle 60 Sekunden abgefragt. Die Kerzen werden ebenfalls etwa alle 60 Sekunden aktualisiert.
- Der Key wird nur im lokalen Browser-Speicher dieses Browsers abgelegt. Gib ihn nicht weiter und committe ihn nicht in das Repository.
- Der angezeigte Kurs ist ein Anbieter-Kurs und kein ausführbarer Vantage-Bid-/Ask-Kurs. Broker-Spread, Slippage, Kommission und Swap werden nicht simuliert.

## Telegram
GitHub Pages ist eine statische Website. Sie kann öffentliche Telegram-Kanäle nicht zuverlässig serverseitig auslesen. Deshalb enthält das Dashboard Links zu den öffentlichen Vorschauen. Signale können manuell aus dem Originalbeitrag mit Entry, SL und TP übernommen werden. Die Einträge bleiben lokal im Browser gespeichert.

## Wichtige Grenzen
- Das Dashboard ist eine Simulation und sendet keine echten Orders an Vantage oder MT5.
- Der Signal-Score ist eine selbst definierte, einfache technische Kennzahl. Er ist weder eine Trefferwahrscheinlichkeit noch ein validiertes Handelssystem.
- EMA- und Breakout-Regeln sind nicht ausreichend backgetestet und versprechen keine Gewinne.
- Paper-Trading nutzt den angezeigten Kurs ohne echten Broker-Spread und ohne realistische Ausführungskosten.
- Aktualisierungen erfolgen nur, solange die Browserseite geöffnet ist. Es gibt keinen 24/7-Hintergrunddienst.
- Verfügbarkeit, Aktualität und API-Limits hängen vom Twelve-Data-Tarif ab.

Nur zu Test- und Lernzwecken. Keine Anlageberatung.
