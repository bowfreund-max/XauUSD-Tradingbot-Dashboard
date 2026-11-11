//+------------------------------------------------------------------+
//| Vantage MT5 Live Feed Connector                                  |
//| Sends the current chart symbol's Bid/Ask to the local dashboard. |
//+------------------------------------------------------------------+
#property strict
#property version   "1.00"
#property description "Local Vantage MT5 to XAUUSD Dashboard feed"

input string InpBridgeURL = "http://127.0.0.1:8765/api/tick";
input int    InpTimerSeconds = 1;

string JsonEscape(string value)
{
   StringReplace(value, "\\", "\\\\");
   StringReplace(value, "\"", "\\\"");
   return value;
}

void SendQuote()
{
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
      return;

   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   long spread_points = (point > 0.0) ? (long)MathRound((tick.ask-tick.bid)/point) : 0;
   string stamp = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
   StringReplace(stamp, ".", "-");

   string payload = StringFormat(
      "{\"symbol\":\"%s\",\"bid\":%s,\"ask\":%s,\"last\":%s,\"time\":\"%s\",\"digits\":%d,\"spread_points\":%I64d}",
      JsonEscape(_Symbol),
      DoubleToString(tick.bid, digits),
      DoubleToString(tick.ask, digits),
      DoubleToString(tick.last, digits),
      stamp,
      digits,
      spread_points
   );

   char post[];
   StringToCharArray(payload, post, 0, WHOLE_ARRAY, CP_UTF8);
   ArrayResize(post, ArraySize(post)-1);
   char result[];
   string response_headers;
   string headers = "Content-Type: application/json\r\n";
   ResetLastError();
   int status = WebRequest("POST", InpBridgeURL, headers, 1500, post, result, response_headers);
   if(status == -1)
      Print("Dashboard bridge error: ", GetLastError(),
            ". Add http://127.0.0.1:8765 to MT5 Tools > Options > Expert Advisors > WebRequest URLs.");
}

int OnInit()
{
   if(InpTimerSeconds < 1)
      return INIT_PARAMETERS_INCORRECT;
   EventSetTimer(InpTimerSeconds);
   Print("Vantage Dashboard connector active for ", _Symbol,
         ". Allow WebRequest URL: http://127.0.0.1:8765");
   SendQuote();
   return INIT_SUCCEEDED;
}

void OnTimer()
{
   SendQuote();
}

void OnDeinit(const int reason)
{
   EventKillTimer();
}
