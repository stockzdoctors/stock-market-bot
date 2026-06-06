"""
Runs at 3:20 PM IST. Sends a full performance summary of all
breakout signals from the day — targets hit, SLs hit, still open.
"""
import sys
import json
import os
import time
from datetime import datetime, date

import requests

from daily_bot import SmartFinanceDashboard, NSE_HOLIDAYS

TODAY        = date.today().isoformat()
SIGNALS_FILE = f"signals/{TODAY}.json"


def build_eod_message():
    date_str = datetime.now().strftime('%d %b %Y')
    m  = f"📊 *END OF DAY REPORT*\n"
    m += f"📅 {date_str}\n"
    m += f"━━━━━━━━━━━━━━━━━━━\n\n"

    if not os.path.exists(SIGNALS_FILE):
        m += "_No breakout signals were generated today._"
        return m

    with open(SIGNALS_FILE) as f:
        data = json.load(f)

    signals = data.get('signals', [])
    if not signals:
        m += "_No breakout signals were generated today._"
        return m

    buys  = [s for s in signals if s['type'] == 'BUY']
    sells = [s for s in signals if s['type'] == 'SELL']

    def fmt(s):
        if s['status'] == 'TARGET_HIT':
            pnl = round(abs(s.get('hit_price', s['target']) - s['entry']), 1)
            return f"  ✅ *{s['symbol']}* — Target Hit  +₹{pnl}  ({s.get('hit_time','--')})\n"
        elif s['status'] == 'SL_HIT':
            pnl = round(abs(s.get('hit_price', s['sl']) - s['entry']), 1)
            return f"  ❌ *{s['symbol']}* — SL Hit  −₹{pnl}  ({s.get('hit_time','--')})\n"
        else:
            curr = s.get('current', '–')
            return f"  🔵 *{s['symbol']}* — Closed Open  ₹{curr}\n"

    if buys:
        m += f"🟢 *BUY SIGNALS* ({len(buys)})\n"
        for s in buys:
            m += fmt(s)
        m += "\n"

    if sells:
        m += f"🔴 *SELL SIGNALS* ({len(sells)})\n"
        for s in sells:
            m += fmt(s)
        m += "\n"

    total        = len(signals)
    target_hits  = sum(1 for s in signals if s['status'] == 'TARGET_HIT')
    sl_hits      = sum(1 for s in signals if s['status'] == 'SL_HIT')
    still_open   = sum(1 for s in signals if s['status'] == 'OPEN')
    closed       = target_hits + sl_hits
    win_rate     = int(target_hits / closed * 100) if closed > 0 else 0

    m += f"━━━━━━━━━━━━━━━━━━━\n"
    m += f"Total Signals : {total}\n"
    m += f"✅ Targets Hit : {target_hits}\n"
    m += f"❌ SL Hit      : {sl_hits}\n"
    m += f"🔵 Still Open  : {still_open}\n"
    if closed > 0:
        m += f"🎯 Win Rate    : {win_rate}%\n"
    m += f"\n⚠️ _Not SEBI registered advice_"
    return m


def main():
    test_mode = os.getenv("TEST_MODE", "").lower() in ("1", "true", "yes")
    today = date.today()
    if not test_mode and (today.weekday() >= 5 or today in NSE_HOLIDAYS):
        print("Market closed. Skipping EOD report.")
        sys.exit(0)

    print("📊 Generating End-of-Day Report...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    bot      = SmartFinanceDashboard()
    token    = bot._get_token()
    chat_ids = bot._get_chat_ids()
    msg      = build_eod_message()

    for cid in chat_ids:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={'chat_id': cid, 'text': msg, 'parse_mode': 'Markdown'},
            timeout=15
        )
        print(f"  → {cid}: {'✅' if r.status_code == 200 else '❌'}")
        time.sleep(1)

    print("-" * 50)
    print("✅ Done!")


if __name__ == "__main__":
    main()
