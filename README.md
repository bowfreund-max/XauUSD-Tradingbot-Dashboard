# XAUUSD Tradingbot Dashboard

Standalone browser dashboard for **XAU/USD paper trading**.

## Included
- GoldAPI.io quote display (price, bid/ask, spread, daily range and change)
- Twelve Data candles: M1, M5, M15 and H1
- EMA trend signal and simple range-breakout zone signal
- Paper trading with virtual starting balance of USD 1,000
- Fixed 0.5% account risk per trade and maximum 2 open trades
- Stop-loss and take-profit monitoring; BUY exits use Bid and SELL exits use Ask
- Local browser storage for API keys, balance and trade history
- Automatic refresh every 60 seconds while the page is open

## Run
Open [index.html](./index.html) in a modern browser. Enter your own GoldAPI and Twelve Data API keys in the settings panel, then save them.

If direct API requests are blocked by provider CORS settings, the browser cannot retrieve data directly. In that case the app needs a small server-side proxy. Do not publish API keys in source code or commit them to this repository.

## GitHub Pages
The included workflow deploys the static page to GitHub Pages after it is enabled in the repository settings:
1. Open **Settings → Pages**.
2. Under **Build and deployment**, select **GitHub Actions**.
3. Pushes to the default branch will trigger the deployment workflow.

## Important limitations
- This is a **simulation only**. It does not connect to a broker or place real orders.
- Bot signals are simple EMA and recent-range rules. They have not been backtested or validated and do not imply profitability.
- The dashboard runs only while the browser page is open. It is not a 24/7 background service.
- This first version uses fixed stop-loss and take-profit levels; it does not implement a trailing stop.
- Paper-trade results do not include commissions, swaps, slippage or guaranteed execution.

Use at your own risk for testing and education only. Nothing here is financial advice.
