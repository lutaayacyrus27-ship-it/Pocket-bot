import time
import requests
import pandas as pd
from datetime import datetime, timezone
import ta

# =========================
# TELEGRAM CONFIG (HARDCODED)
# =========================
TELEGRAM_BOT_TOKEN = "8001603915:AAFRnbrYgjCsQf4EiiKLNeoI6jnNYeA7UVw"
TELEGRAM_CHAT_ID = "-1003715220808"

# =========================
# MARKET DATA CONFIG
# =========================
ALPHAVANTAGE_API_KEY = "PUT_YOUR_ALPHA_VANTAGE_KEY_HERE"

# =========================
# TELEGRAM SENDER
# =========================
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=10)

# =========================
# ASSETS (AUTO SWITCH – BASIC)
# =========================
ASSETS = ["EURUSD", "GBPUSD", "USDJPY"]

def get_best_asset():
    # Simple version – later we add real payout logic
    return ASSETS[0]

# =========================
# REAL MARKET DATA (1 MIN)
# =========================
def get_forex_candles(symbol="EURUSD"):
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
        return None

    df = pd.DataFrame.from_dict(data[key], orient="index")
    df = df.rename(columns={"4. close": "close"})
    df["close"] = df["close"].astype(float)
    df = df.sort_index()

    return df.tail(50)

# =========================
# STRATEGY (EMA + RSI)
# =========================
def generate_signal(candles: pd.DataFrame):
    candles["ema_fast"] = ta.trend.ema_indicator(candles["close"], window=9)
    candles["ema_slow"] = ta.trend.ema_indicator(candles["close"], window=21)
    candles["rsi"] = ta.momentum.rsi(candles["close"], window=14)

    last = candles.iloc[-1]
    prev = candles.iloc[-2]

    if (
        prev["ema_fast"] < prev["ema_slow"]
        and last["ema_fast"] > last["ema_slow"]
        and last["rsi"] > 50
    ):
        return "BUY"

    if (
        prev["ema_fast"] > prev["ema_slow"]
        and last["ema_fast"] < last["ema_slow"]
        and last["rsi"] < 50
    ):
        return "SELL"

    return None

# =========================
# MAIN LOOP
# =========================
if __name__ == "__main__":
    send_telegram_message("🤖 *Signal bot started — EMA + RSI (1M)*")

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
