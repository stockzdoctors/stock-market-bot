import sys
from datetime import datetime, date

from daily_bot import SmartFinanceDashboard, NSE_HOLIDAYS

if __name__ == "__main__":
    today = date.today()
    if today.weekday() >= 5:
        print(f"Weekend ({today.strftime('%A %d-%b-%Y')}). NSE closed. Skipping.")
        sys.exit(0)
    if today in NSE_HOLIDAYS:
        print(f"NSE Holiday ({today.strftime('%d-%b-%Y')}). Market closed. Skipping.")
        sys.exit(0)

    print("⚡ First 15-Min Candle Breakout Scanner")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    bot = SmartFinanceDashboard()
    bot.send_breakout_alert()

    print("-" * 50)
    print("✅ Done!")
