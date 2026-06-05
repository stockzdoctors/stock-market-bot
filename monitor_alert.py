"""
Runs every 15 minutes during market hours (9:32 AM – 3:30 PM IST).
Reads today's breakout signals, checks current prices, and fires
a Telegram alert the moment a SL or Target is hit (once per signal).
"""
import sys
import json
import os
import subprocess
import time
from datetime import datetime, date

import requests
import yfinance as yf

from daily_bot import SmartFinanceDashboard, NSE_HOLIDAYS

TODAY        = date.today().isoformat()
SIGNALS_FILE = f"signals/{TODAY}.json"


def load_signals():
    if not os.path.exists(SIGNALS_FILE):
        return None
    with open(SIGNALS_FILE) as f:
        return json.load(f)


def save_and_push(data):
    with open(SIGNALS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    subprocess.run(['git', 'config', 'user.name',  'Stock Market Bot'], check=False)
    subprocess.run(['git', 'config', 'user.email', 'bot@stockmarket.com'], check=False)
    subprocess.run(['git', 'pull', '--rebase'], check=False)
    subprocess.run(['git', 'add', SIGNALS_FILE], check=False)
    staged = subprocess.run(['git', 'diff', '--staged', '--quiet'])
    if staged.returncode != 0:
        subprocess.run(['git', 'commit', '-m', f'Update signal status {TODAY} {datetime.now().strftime("%H:%M")}'], check=False)
        subprocess.run(['git', 'push'], check=False)


def build_hit_message(alerts):
    now = datetime.now().strftime('%I:%M %p')
    m   = f"🚨 *SIGNAL UPDATE — {now} IST*\n"
    m  += f"━━━━━━━━━━━━━━━━━━━\n\n"
    for hit_type, sig in alerts:
        direction = "📈" if sig['type'] == 'BUY' else "📉"
        pnl       = round(abs(sig['hit_price'] - sig['entry']), 2)
        pnl_pct   = round(pnl / sig['entry'] * 100, 2)
        if hit_type == 'TARGET':
            m += f"✅ {direction} *{sig['symbol']}* — TARGET HIT 💰\n"
        else:
            m += f"❌ {direction} *{sig['symbol']}* — STOP LOSS HIT\n"
        m += f"  Entry  : ₹{sig['entry']}\n"
        m += f"  Hit at : ₹{sig['hit_price']}  ({now})\n"
        m += f"  Move   : ₹{pnl} ({pnl_pct}%)\n\n"
    m += "⚠️ _Not SEBI registered advice_"
    return m


def main():
    today = date.today()
    if today.weekday() >= 5 or today in NSE_HOLIDAYS:
        print("Market closed. Skipping.")
        sys.exit(0)

    now = datetime.now()
    market_open  = now.replace(hour=9,  minute=32, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    if now < market_open or now > market_close:
        print(f"Outside market hours ({now.strftime('%H:%M')} IST). Skipping.")
        sys.exit(0)

    data = load_signals()
    if not data:
        print("No signals file for today. Breakout alert may not have run yet.")
        sys.exit(0)

    open_signals = [s for s in data['signals'] if s['status'] == 'OPEN']
    if not open_signals:
        print("All signals already closed. Nothing to monitor.")
        sys.exit(0)

    print(f"Monitoring {len(open_signals)} open signal(s)...")
    bot     = SmartFinanceDashboard()
    alerts  = []
    changed = False

    for sig in data['signals']:
        if sig['status'] != 'OPEN':
            continue
        try:
            intra = yf.Ticker(f"{sig['symbol']}.NS").history(period='1d', interval='1m')
            if len(intra) == 0:
                continue
            current            = round(intra['Close'].iloc[-1], 2)
            sig['current']     = current

            hit_type = None
            if sig['type'] == 'BUY':
                if current >= sig['target']:
                    hit_type = 'TARGET'
                elif current <= sig['sl']:
                    hit_type = 'SL'
            else:  # SELL
                if current <= sig['target']:
                    hit_type = 'TARGET'
                elif current >= sig['sl']:
                    hit_type = 'SL'

            if hit_type:
                sig['status']    = 'TARGET_HIT' if hit_type == 'TARGET' else 'SL_HIT'
                sig['hit_price'] = current
                sig['hit_time']  = datetime.now().strftime('%H:%M')
                alerts.append((hit_type, sig))
                changed = True
                print(f"  🔔 {sig['symbol']} {sig['status']} at ₹{current}")
        except Exception as e:
            print(f"  Error checking {sig['symbol']}: {e}")

    if alerts:
        token    = bot._get_token()
        chat_ids = bot._get_chat_ids()
        msg      = build_hit_message(alerts)
        for cid in chat_ids:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={'chat_id': cid, 'text': msg, 'parse_mode': 'Markdown'},
                timeout=15
            )
            time.sleep(1)
        print(f"Sent alert for {len(alerts)} hit(s) ✅")

    if changed:
        save_and_push(data)
    else:
        print("No new hits. All signals still open.")


if __name__ == "__main__":
    main()
