import time
from datetime import datetime, timezone
from telegram_bot import send_telegram_message
from strategy import generate_signal
from assets import get_best_asset
from market_data import get_forex_candles

if __name__ == "__main__":
    send_telegram_message("🤖 *Signal bot started — real market data enabled*")

    while True:
        asset = get_best_asset()
        candles = get_forex_candles(asset)

        if candles is None or len(candles) < 30:
            time.sleep(60)
            continue

        signal = generate_signal(candles)

        if signal:
            entry_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

            reason = (
                "EMA 9 crossed EMA 21 with RSI confirmation"
            )

            msg = f"""
📊 *NEW SIGNAL*
💱 Asset: `{asset}`
⏱ Timeframe: 1M
🕒 Entry Time: `{entry_time}`
📈 Action: *{signal}*
🧠 Reason: {reason}
⚠️ Demo / Signal only
"""
            send_telegram_message(msg)

        time.sleep(60)
