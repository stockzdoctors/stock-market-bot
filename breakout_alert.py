import sys
import json
import os
import subprocess
from datetime import datetime, date

from daily_bot import SmartFinanceDashboard, NSE_HOLIDAYS

TODAY        = date.today().isoformat()
SIGNALS_FILE = f"signals/{TODAY}.json"


def save_signals(breakouts):
    os.makedirs('signals', exist_ok=True)
    signals = []
    for s in breakouts['buy']:
        signals.append({
            'symbol': s['symbol'], 'type': 'BUY',
            'entry': s['entry'], 'sl': s['sl'], 'target': s['target'],
            'risk': s['risk'], 'change_pct': s['change_pct'],
            'current': s['current'], 'status': 'OPEN',
            'hit_price': None, 'hit_time': None,
        })
    for s in breakouts['sell']:
        signals.append({
            'symbol': s['symbol'], 'type': 'SELL',
            'entry': s['entry'], 'sl': s['sl'], 'target': s['target'],
            'risk': s['risk'], 'change_pct': s['change_pct'],
            'current': s['current'], 'status': 'OPEN',
            'hit_price': None, 'hit_time': None,
        })
    with open(SIGNALS_FILE, 'w') as f:
        json.dump({'date': TODAY, 'signals': signals}, f, indent=2)
    print(f"   Saved {len(signals)} signal(s) → {SIGNALS_FILE}")


def push_to_git():
    subprocess.run(['git', 'config', 'user.name',  'Stock Market Bot'], check=False)
    subprocess.run(['git', 'config', 'user.email', 'bot@stockmarket.com'], check=False)
    subprocess.run(['git', 'pull', '--rebase'], check=False)
    subprocess.run(['git', 'add', SIGNALS_FILE], check=False)
    staged = subprocess.run(['git', 'diff', '--staged', '--quiet'])
    if staged.returncode != 0:
        subprocess.run(['git', 'commit', '-m', f'Add breakout signals {TODAY}'], check=False)
        subprocess.run(['git', 'push'], check=False)
        print("   Pushed signals to repo ✅")


if __name__ == "__main__":
    test_mode = os.getenv("TEST_MODE", "").lower() in ("1", "true", "yes")
    today = date.today()
    if not test_mode:
        if today.weekday() >= 5:
            print(f"Weekend ({today.strftime('%A')}). NSE closed. Skipping.")
            sys.exit(0)
        if today in NSE_HOLIDAYS:
            print(f"NSE Holiday ({today}). Market closed. Skipping.")
            sys.exit(0)

    print("⚡ First 15-Min Candle Breakout Scanner")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    bot       = SmartFinanceDashboard()
    breakouts = bot.get_first_candle_breakouts()
    bot.send_breakout_alert(breakouts)
    save_signals(breakouts)
    push_to_git()

    print("-" * 50)
    print("✅ Done!")
