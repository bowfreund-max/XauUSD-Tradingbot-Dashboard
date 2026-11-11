# Vantage MT5 Live Feed

## What this adds
- The dashboard reads live Bid/Ask quotes from the symbol open in your Vantage MT5 terminal.
- A local Python bridge receives the MT5 Expert Advisor updates and serves the dashboard.
- The dashboard checks for a fresh MT5 quote every second. If no tick has arrived for 10 seconds, it marks the feed disconnected.
- The simulated/paper-trading engine remains simulated. No live orders are sent to Vantage.
- The chart candles still come from Twelve Data; the live quote and spread are from your MT5 terminal.

## Requirements
- Vantage Markets MT5 installed and logged in to your Standard STP account.
- Python 3 installed on the same Windows computer.
- XAUUSD selected in MT5 Market Watch and opened as a chart.
- The dashboard repository downloaded to that computer.

## Setup on Windows
1. Download or clone this repository.
2. Open MT5 and log in to your Vantage account.
3. In MT5, open File > Open Data Folder.
4. Open MQL5 > Experts and copy VantageDashboardFeed.mq5 there.
5. In MT5 MetaEditor, open the file and press F7 to compile it.
6. In MT5, open Tools > Options > Expert Advisors. Enable Allow WebRequest for listed URL and add exactly: http://127.0.0.1:8765
7. Open an XAUUSD chart. Drag VantageDashboardFeed onto it and enable Algo Trading / automated trading if MT5 requests it. The EA only sends quotes; it does not place orders.
8. In the repository folder, double-click start_dashboard.bat.
9. Open http://127.0.0.1:8765 in your browser.

Keep MT5, the EA, the Python bridge, and the browser open while using the live dashboard. The local bridge is intentionally bound to 127.0.0.1 and is not exposed to the public internet.

## Important
- The MT5 symbol may have a broker suffix. Attach the EA to the exact Vantage gold chart symbol shown in your terminal; the EA sends that chart symbol automatically.
- Bid/Ask and spread are broker-terminal values. Actual account fees, swaps, contract size, and execution conditions must be checked in the instrument specification inside MT5.
- Standard STP is generally spread-based for eligible instruments; do not assume every fee is zero. Overnight swaps may apply.
- This does not verify profitability or guarantee execution prices.

## Public Telegram signal feed

The local bridge also reads the public web previews (no Telegram login) for:
- https://t.me/s/ssfgold
- https://t.me/s/xauempirefx
- https://t.me/s/Free_signals

It polls these pages approximately once per minute and exposes the parsed results at `/api/telegram-signals`. The dashboard displays signals only when the post contains XAUUSD/Gold, BUY or SELL, an entry, an SL, and a TP with a directionally consistent price structure. Posts that cannot be parsed confidently are skipped.

This is a best-effort reader of Telegram's public HTML preview, not the Telegram Bot API. Telegram can change the page structure, limit requests, or remove public access. The parser has not been validated against every post format; check each detected signal against the original post before relying on it. The displayed consensus is a count of detected posts, not a verified performance score. Telegram signals are not used to send live orders.
