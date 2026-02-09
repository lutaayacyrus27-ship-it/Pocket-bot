import os
import time
import requests
import pandas as pd
from datetime import datetime, timezone
import ta

# =========================
# LOAD SECRETS FROM VARIABLES
# =========================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

# Check that variables are set
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or not ALPHAVANTAGE_API_KEY:
    raise ValueError("Missing environment variables! Make sure TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, and ALPHAVANTAGE_API_KEY are set.")

# =========================
# TELEGRAM SENDER
# =========================
def send_telegram_message(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram send failed:", e)

# =========================
# ASSETS (AUTO SWITCH – BASIC)
# =========================
ASSETS = ["EURUSD", "GBPUSD", "USDJPY"]

def get_best_asset():
    return ASSETS[0]  # Simple placeholder, later we can add payout logic

# =========================
# MARKET DATA (1 MIN) - Alpha Vantage
# =========================
def get_forex_candles(symbol="EURUSD"):
    try:
        from_symbol = symbol[:3]
        to_symbol = symbol[3:]
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "FX_INTRADAY",
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "interval": "1min",
            "apikey": ALPHAVANTAGE_API_KEY,
            "outputsize": "compact"
        }
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        key = "Time Series FX (1min)"
        if key not in data:
            print("Alpha Vantage data not found, retrying next loop.")
            return None
        df = pd.DataFrame.from_dict(data[key], orient="index")
        df = df.rename(columns={"4. close": "close"})
        df["close"] = df["close"].astype(float)
        df = df.sort_index()
        return df.tail(50)
    except Exception as e:
        print("Error fetching market data:", e)
        return None

# =========================
# STRATEGY (EMA + RSI)
# =========================
def generate_signal(candles: pd.DataFrame):
    try:
        candles["ema_fast"] = ta.trend.ema_indicator(candles["close"], window=9)
        candles["ema_slow"] = ta.trend.ema_indicator(candles["close"], window=21)
        candles["rsi"] = ta.momentum.rsi(candles["close"], window=14)
        last = candles.iloc[-1]
        prev = candles.iloc[-2]
        if prev["ema_fast"] < prev["ema_slow"] and last["ema_fast"] > last["ema_slow"] and last["rsi"] > 50:
            return "BUY"
        if prev["ema_fast"] > prev["ema_slow"] and last["ema_fast"] < last["ema_slow"] and last["rsi"] < 50:
            return "SELL"
        return None
    except Exception as e:
        print("Strategy calculation failed:", e)
        return None

# =========================
# MAIN LOOP
# =========================
if __name__ == "__main__":
    send_telegram_message("🤖 *Signal bot started — EMA + RSI (1M) Railway-safe*")

    while True:
        asset = get_best_asset()
        candles = get_forex_candles(asset)
        if candles is None or len(candles) < 30:
            time.sleep(60)
            continue
        signal = generate_signal(candles)
        if signal:
            entry_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            msg = f"""
📊 *NEW SIGNAL*
💱 Asset: `{asset}`
⏱ Timeframe: 1M
🕒 Entry Time: `{entry_time}`
📈 Action: *{signal}*
🧠 Reason: EMA 9 crossed EMA 21 + RSI confirmation
⚠️ Demo / Signal only
"""
            send_telegram_message(msg)
        time.sleep(60)
