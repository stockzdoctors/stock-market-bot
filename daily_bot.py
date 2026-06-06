import sys
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, date
import requests
import os

# NSE trading holidays for 2026 — update this list each year
NSE_HOLIDAYS = {
    date(2026,  1, 26),  # Republic Day
    date(2026,  2, 26),  # Mahashivratri
    date(2026,  4,  3),  # Good Friday
    date(2026,  4, 14),  # Dr. Ambedkar Jayanti
    date(2026,  4, 22),  # Ram Navami
    date(2026,  5,  1),  # Maharashtra Day / Labour Day
    date(2026,  8, 27),  # Ganesh Chaturthi
    date(2026, 10,  2),  # Gandhi Jayanti
    date(2026, 10, 20),  # Dussehra
    date(2026, 11,  9),  # Diwali Balipratipada
    date(2026, 11, 25),  # Guru Nanak Jayanti
    date(2026, 12, 25),  # Christmas
}


class SmartFinanceDashboard:
    def __init__(self):
        self.nifty_50_symbols = [
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS',
            'ICICIBANK.NS', 'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'ASIANPAINT.NS',
            'AXISBANK.NS', 'KOTAKBANK.NS', 'MARUTI.NS', 'LT.NS', 'DMART.NS',
            'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'BAJFINANCE.NS', 'WIPRO.NS',
            'NESTLEIND.NS', 'ADANIPORTS.NS', 'POWERGRID.NS', 'NTPC.NS', 'HCLTECH.NS',
            'BAJAJFINSV.NS', 'TATAMOTORS.NS', 'JSWSTEEL.NS', 'BRITANNIA.NS', 'ONGC.NS',
            'CIPLA.NS', 'TATASTEEL.NS', 'UPL.NS', 'COALINDIA.NS', 'BPCL.NS',
            'DRREDDY.NS', 'EICHERMOT.NS', 'DIVISLAB.NS', 'INDUSINDBK.NS', 'M&M.NS'
        ]

    # ------------------------------------------------------------------ helpers

    def get_rsi_interpretation(self, rsi_value, trend):
        if rsi_value < 30:
            signal = "OVERSOLD"
            action = "Good buying opportunity" if trend == "BULLISH" else "Wait for confirmation"
        elif rsi_value > 70:
            signal = "OVERBOUGHT"
            action = "Book partial profits" if trend == "BULLISH" else "Avoid — high risk"
        else:
            signal = "NEUTRAL"
            action = "Monitor for breakout"
        return {
            'signal':     signal,
            'action':     action,
            'risk_level': 'LOW' if signal == 'NEUTRAL' else 'MEDIUM' if rsi_value < 30 else 'HIGH'
        }

    # -------------------------------------------------------- technical analysis

    def get_advanced_technical_analysis(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            hist  = stock.history(period="3mo")   # 3 months for breakout check

            if len(hist) < 20:
                return self._empty_technicals()

            hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
            hist['EMA_9']  = hist['Close'].ewm(span=9, adjust=False).mean()
            delta = hist['Close'].diff()
            gain  = delta.clip(lower=0).rolling(14).mean()
            loss  = (-delta.clip(upper=0)).rolling(14).mean()
            hist['RSI'] = 100 - (100 / (1 + gain / loss))

            current_price = hist['Close'].iloc[-1]
            prev_price    = hist['Close'].iloc[-2]
            sma_20        = hist['SMA_20'].iloc[-1]
            prev_sma      = hist['SMA_20'].iloc[-2]
            ema_9         = hist['EMA_9'].iloc[-1]
            rsi           = hist['RSI'].iloc[-1]
            high_3m       = hist['Close'].max()

            trend = ("BULLISH" if current_price > sma_20
                     else "BEARISH" if current_price < sma_20
                     else "NEUTRAL")

            # Price crossed above SMA20 today (pullback entry signal)
            sma_crossover = (prev_price <= prev_sma) and (current_price > sma_20)

            # Within 2% of 3-month high with RSI not yet overbought (breakout watch)
            near_high_breakout = (current_price >= high_3m * 0.98) and (rsi < 68)

            rsi_analysis = self.get_rsi_interpretation(rsi, trend)

            return {
                'trend':              trend,
                'rsi':                round(rsi, 1),
                'rsi_signal':         rsi_analysis['signal'],
                'rsi_action':         rsi_analysis['action'],
                'risk_level':         rsi_analysis['risk_level'],
                'sma_20':             round(sma_20, 2),
                'ema_9':              round(ema_9, 2),
                'sma_crossover':      sma_crossover,
                'near_high_breakout': near_high_breakout,
                'high_3m':            round(high_3m, 2),
                'strength':           (50 + (rsi - 50) / 2 if trend == "BULLISH"
                                       else 50 + (50 - rsi) / 2)
            }
        except Exception:
            return self._empty_technicals()

    def _empty_technicals(self):
        return {
            'trend': 'NEUTRAL', 'rsi': 50, 'rsi_signal': 'NEUTRAL',
            'rsi_action': 'Data unavailable', 'risk_level': 'UNKNOWN',
            'sma_20': 0, 'ema_9': 0, 'sma_crossover': False,
            'near_high_breakout': False, 'high_3m': 0, 'strength': 50
        }

    # --------------------------------------------------------------- nifty data

    def get_accurate_nifty_data(self):
        try:
            hist = yf.Ticker("^NSEI").history(period="5d")
            if len(hist) < 2:
                return self._nifty_fallback()

            current_price = hist['Close'].iloc[-1]
            prev_close    = hist['Close'].iloc[-2]
            change        = current_price - prev_close

            result = {
                'current_price':  round(current_price, 2),
                'change':         round(change, 2),
                'change_percent': round((change / prev_close) * 100, 2),
                'prev_close':     round(prev_close, 2),
                'high_52w':       round(hist['Close'].max(), 2),
                'low_52w':        round(hist['Close'].min(), 2),
                'volume':         hist['Volume'].iloc[-1] if 'Volume' in hist else 0,
                'vix':            None
            }
            try:
                vix_hist    = yf.Ticker("^INDIAVIX").history(period="2d")
                result['vix'] = round(vix_hist['Close'].iloc[-1], 2) if len(vix_hist) > 0 else None
            except Exception:
                pass
            return result
        except Exception:
            return self._nifty_fallback()

    def _nifty_fallback(self):
        return {
            'current_price': 25215.00, 'change': 150.50,
            'change_percent': 0.60,    'prev_close': 25064.50,
            'high_52w': 25500.00,      'low_52w': 23500.00, 'volume': 1500000
        }

    # ------------------------------------------------------------- stock batch

    def get_stock_data_batch(self):
        stocks_data = []
        for symbol in self.nifty_50_symbols:
            try:
                hist = yf.Ticker(symbol).history(period="2d")
                if len(hist) < 2:
                    continue
                current_price = hist['Close'].iloc[-1]
                prev_close    = hist['Close'].iloc[-2]
                stocks_data.append({
                    'symbol':         symbol.replace('.NS', ''),
                    'current_price':  round(current_price, 2),
                    'change_percent': round(((current_price - prev_close) / prev_close) * 100, 2),
                    'technicals':     self.get_advanced_technical_analysis(symbol)
                })
                time.sleep(0.05)
            except Exception:
                continue
        return sorted(stocks_data, key=lambda x: x['change_percent'], reverse=True)

    # -------------------------------------------------------- market prediction

    def get_intelligent_prediction(self, nifty_data, stocks_data):
        if not stocks_data:
            return {
                'direction': 'SIDEWAYS', 'reason': 'Insufficient data',
                'confidence': 'LOW', 'trend_strength': 50,
                'gainers_count': 0, 'losers_count': 0,
                'market_breadth': 0, 'total_stocks': 0
            }

        gainers        = [s for s in stocks_data if s['change_percent'] > 0]
        losers         = [s for s in stocks_data if s['change_percent'] < 0]
        market_breadth = len(gainers) - len(losers)
        pct            = nifty_data['change_percent']

        if len(gainers) > len(losers) + 10 and pct > 0.5:
            direction, confidence = 'UPWARD',   'HIGH'
            reason = 'Strong buying momentum across majority of stocks'
        elif len(losers) > len(gainers) + 10 and pct < -0.5:
            direction, confidence = 'DOWNWARD',  'HIGH'
            reason = 'Significant selling pressure in the market'
        elif len(gainers) > len(losers):
            direction, confidence = 'UPWARD',   'MEDIUM'
            reason = 'Moderate bullish bias with positive breadth'
        elif len(losers) > len(gainers):
            direction, confidence = 'DOWNWARD',  'MEDIUM'
            reason = 'Moderate bearish pressure detected'
        else:
            direction, confidence = 'SIDEWAYS',  'MEDIUM'
            reason = 'Balanced market forces — mixed signals'

        return {
            'direction': direction, 'reason': reason, 'confidence': confidence,
            'trend_strength': 65,   'market_breadth': market_breadth,
            'total_stocks': len(stocks_data),
            'gainers_count': len(gainers), 'losers_count': len(losers)
        }

    # ---------------------------------------------------------- swing engine ✨

    def get_swing_setups(self, stocks_data):
        """
        Four setup types:
          1. Oversold Bounce    RSI < 32 + BULLISH trend          → strong buy
          2. Pullback Entry     RSI 33-46 + SMA20 crossover today → good entry
          3. Momentum Breakout  near 3-month high + RSI 45-67     → continuation
          4. Overbought Exit    RSI > 70                           → avoid / book profits
        """
        swing_buys = []
        momentum   = []
        avoid_list = []

        for s in stocks_data:
            t         = s.get('technicals', {})
            rsi       = t.get('rsi', 50)
            trend     = t.get('trend', 'NEUTRAL')
            crossover = t.get('sma_crossover', False)
            near_high = t.get('near_high_breakout', False)
            price     = s['current_price']

            # 1. Oversold Bounce
            if rsi < 32 and trend == 'BULLISH':
                swing_buys.append({
                    'symbol':   s['symbol'], 'price': price, 'rsi': rsi,
                    'setup':    'Oversold Bounce',
                    'reason':   f'RSI {rsi} — deeply oversold in uptrend',
                    'stop':     round(price * 0.975, 1),  # 2.5% stop
                    'target':   round(price * 1.060, 1),  # 6% target
                    'stop_pct': 2.5, 'tgt_pct': 6.0,
                    'label':    '🔥 STRONG BUY'
                })

            # 2. Pullback Entry
            elif 33 <= rsi <= 46 and crossover and trend == 'BULLISH':
                swing_buys.append({
                    'symbol':   s['symbol'], 'price': price, 'rsi': rsi,
                    'setup':    'Pullback Entry',
                    'reason':   f'Price reclaimed SMA20 — RSI {rsi}',
                    'stop':     round(price * 0.980, 1),  # 2% stop
                    'target':   round(price * 1.050, 1),  # 5% target
                    'stop_pct': 2.0, 'tgt_pct': 5.0,
                    'label':    '✅ GOOD ENTRY'
                })

            # 3. Momentum Breakout
            if near_high and 45 <= rsi <= 67 and trend == 'BULLISH':
                momentum.append({
                    'symbol':   s['symbol'], 'price': price, 'rsi': rsi,
                    'setup':    'Momentum Breakout',
                    'reason':   f'Near 3-month high — RSI {rsi}, trend intact',
                    'stop':     round(price * 0.985, 1),  # 1.5% stop
                    'target':   round(price * 1.040, 1),  # 4% target
                    'stop_pct': 1.5, 'tgt_pct': 4.0,
                    'label':    '⚡ BREAKOUT'
                })

            # 4. Overbought — avoid or exit
            if rsi > 70:
                avoid_list.append({
                    'symbol': s['symbol'], 'price': price, 'rsi': rsi, 'trend': trend,
                    'note':   ('Book partial profits ⚠️' if trend == 'BULLISH'
                               else 'Avoid fresh entry ❌')
                })

        swing_buys.sort(key=lambda x: x['rsi'])
        momentum.sort(key=lambda x: x['rsi'])
        avoid_list.sort(key=lambda x: x['rsi'], reverse=True)

        return {
            'swing_buys': swing_buys[:4],
            'momentum':   momentum[:3],
            'avoid':      avoid_list[:5]
        }

    # -------------------------------------------------- 3 message builders 📨

    def build_part1_market_pulse(self, nifty_data, prediction):
        """~600 chars — Nifty snapshot, breadth, one-line outlook."""
        date_str   = datetime.now().strftime('%d %b %Y, %I:%M %p')
        nifty_icon = "🟢" if nifty_data['change_percent'] > 0 else "🔴"
        out_icon   = ("📈" if prediction['direction'] == 'UPWARD'
                      else "📉" if prediction['direction'] == 'DOWNWARD' else "⚖️")
        conf_icon  = ("🔥" if prediction['confidence'] == 'HIGH'
                      else "✅" if prediction['confidence'] == 'MEDIUM' else "⚠️")
        breadth    = prediction['market_breadth']
        b_str      = f"+{breadth}" if breadth > 0 else str(breadth)

        m  = f"📊 *BILLIONAIRES GROUP — Market Pulse*\n"
        m += f"🗓 {date_str}\n\n"
        m += f"━━━━━━━━━━━━━━━━━━━\n"
        m += f"*NIFTY 50* {nifty_icon} ₹{nifty_data['current_price']:,.0f}\n"
        m += f"Change: {nifty_data['change']:+.2f} ({nifty_data['change_percent']:+.2f}%)\n"
        m += f"Prev Close: ₹{nifty_data['prev_close']:,.0f}\n\n"
        m += f"📊 *Market Breadth*\n"
        m += f"Gainers: {prediction['gainers_count']}  |  Losers: {prediction['losers_count']}  |  Net: {b_str}\n"
        vix = nifty_data.get('vix')
        if vix:
            vix_icon = "😱 HIGH FEAR" if vix > 20 else ("⚠️ CAUTION" if vix > 15 else "😊 CALM")
            m += f"India VIX: *{vix}*  {vix_icon}\n"
        m += f"\n{out_icon} *Outlook: {prediction['direction']}* {conf_icon} {prediction['confidence']}\n"
        m += f"💬 {prediction['reason']}\n"
        m += f"━━━━━━━━━━━━━━━━━━━\n"
        m += f"_Part 1 of 3 — Top Movers next_"
        return m

    def build_part2_movers(self, stocks_data):
        """~1200 chars — compact 1-line per stock, top 8 gainers + losers."""
        gainers = [s for s in stocks_data if s['change_percent'] > 0][:8]
        losers  = [s for s in stocks_data if s['change_percent'] < 0][:8]

        m  = f"📊 *BILLIONAIRES GROUP — Top Movers*\n\n"
        m += f"🏆 *TOP GAINERS*\n"
        for s in gainers:
            t   = s.get('technicals', {})
            rsi = t.get('rsi', 0)
            te  = "🟢" if t.get('trend') == 'BULLISH' else "🔴" if t.get('trend') == 'BEARISH' else "🟡"
            flag = " ⚠️OB" if rsi > 70 else (" 👀OS" if rsi < 30 else "")
            m += f"{te} *{s['symbol']}*  ₹{s['current_price']:.0f}  {s['change_percent']:+.2f}%  RSI {rsi}{flag}\n"

        m += f"\n📉 *TOP LOSERS*\n"
        for s in losers:
            t   = s.get('technicals', {})
            rsi = t.get('rsi', 0)
            te  = "🟢" if t.get('trend') == 'BULLISH' else "🔴" if t.get('trend') == 'BEARISH' else "🟡"
            flag = " ⚠️OB" if rsi > 70 else (" 👀OS" if rsi < 30 else "")
            m += f"{te} *{s['symbol']}*  ₹{s['current_price']:.0f}  {s['change_percent']:+.2f}%  RSI {rsi}{flag}\n"

        m += f"\n_🟢 Bullish  🔴 Bearish  🟡 Neutral_\n"
        m += f"_RSI <30 = oversold 👀  |  RSI >70 = overbought ⚠️_\n"
        m += f"_Part 2 of 3 — Swing setups next_"
        return m

    def build_part3_swing(self, swing_setups):
        """~1400 chars — swing buy setups with entry, stop, target + avoid list."""
        m  = f"📊 *BILLIONAIRES GROUP — Swing Setups*\n\n"

        buys = swing_setups['swing_buys']
        if buys:
            m += f"✅ *SWING BUY CANDIDATES*\n"
            for s in buys:
                m += f"\n{s['label']} *{s['symbol']}*\n"
                m += f"  Setup: {s['setup']}\n"
                m += f"  Entry: ₹{s['price']:.0f}  |  {s['reason']}\n"
                m += f"  🎯 Target: ₹{s['target']:.0f} (+{s['tgt_pct']}%)\n"
                m += f"  🛑 Stop Loss: ₹{s['stop']:.0f} (−{s['stop_pct']}%)\n"
        else:
            m += f"✅ *SWING BUY CANDIDATES*\n"
            m += f"No high-conviction setups today — wait for better entries.\n"

        mom = swing_setups['momentum']
        if mom:
            m += f"\n⚡ *MOMENTUM / BREAKOUT WATCH*\n"
            for s in mom:
                m += f"\n{s['label']} *{s['symbol']}*\n"
                m += f"  Entry: ₹{s['price']:.0f}  |  {s['reason']}\n"
                m += f"  🎯 Target: ₹{s['target']:.0f} (+{s['tgt_pct']}%)\n"
                m += f"  🛑 Stop Loss: ₹{s['stop']:.0f} (−{s['stop_pct']}%)\n"

        avoid = swing_setups['avoid']
        if avoid:
            m += f"\n❌ *AVOID / BOOK PROFITS*\n"
            for s in avoid:
                m += f"• *{s['symbol']}*  ₹{s['price']:.0f}  RSI {s['rsi']}  — {s['note']}\n"

        m += f"\n━━━━━━━━━━━━━━━━━━━\n"
        m += f"🛡️ *Risk Rules*\n"
        m += f"• Max 5% capital per trade\n"
        m += f"• Set stop-loss before entering\n"
        m += f"• Not SEBI registered advice\n"
        m += f"━━━━━━━━━━━━━━━━━━━\n"
        m += f"_Data: Billionaires Group_"
        return m

    # --------------------------------------------------- news + chart 📰🖼️

    def fetch_market_news(self):
        """Fetch top 5 Indian market headlines, trying multiple RSS sources."""
        import xml.etree.ElementTree as ET

        sources = [
            "https://news.google.com/rss/search?q=NSE+NIFTY+Indian+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=Sensex+NIFTY+market+today&hl=en-IN&gl=IN&ceid=IN:en",
            "https://economictimes.indiatimes.com/markets/rss.cms",
        ]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for url in sources:
            try:
                r = requests.get(url, timeout=12, headers=headers)
                if r.status_code != 200:
                    continue
                root = ET.fromstring(r.content)
                news = []
                for item in root.findall('.//item')[:5]:
                    title = item.find('title')
                    if title is not None and title.text:
                        # strip Google News source suffix like " - Economic Times"
                        headline = title.text.strip().split(' - ')[0].strip()
                        if headline:
                            news.append(headline)
                if news:
                    print(f"   News fetched from: {url.split('/')[2]}")
                    return news
            except Exception as e:
                print(f"   Source failed ({url.split('/')[2]}): {e}")
                continue

        print("   All news sources failed — skipping news section")
        return []

    def generate_nifty_chart(self):
        """Generate a 1-month NIFTY price chart; returns PNG path or None."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates

            hist = yf.Ticker("^NSEI").history(period="1mo")
            if len(hist) < 5:
                return None

            closes = hist['Close']
            dates  = hist.index
            color  = '#00d26a' if closes.iloc[-1] >= closes.iloc[0] else '#ff4d4d'

            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor('#0d1117')
            ax.set_facecolor('#0d1117')

            ax.plot(dates, closes, color=color, linewidth=2)
            ax.fill_between(dates, closes, closes.min(), alpha=0.15, color=color)

            last   = closes.iloc[-1]
            pct    = (last - closes.iloc[0]) / closes.iloc[0] * 100
            sign   = '+' if pct >= 0 else ''
            ax.annotate(
                f"₹{last:,.0f}  ({sign}{pct:.2f}%)",
                xy=(dates[-1], last), xytext=(-80, 15),
                textcoords='offset points', color=color,
                fontsize=11, fontweight='bold'
            )

            ax.set_title("NIFTY 50  —  Last 1 Month", color='white', fontsize=13, pad=10)
            ax.tick_params(colors='#aaaaaa')
            for spine in ax.spines.values():
                spine.set_color('#333333')
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'₹{x:,.0f}'))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            plt.xticks(rotation=30, color='#aaaaaa')
            plt.yticks(color='#aaaaaa')
            ax.grid(True, color='#1e1e1e', linewidth=0.6)

            plt.tight_layout()
            path = '/tmp/nifty_chart.png'
            plt.savefig(path, dpi=120, bbox_inches='tight', facecolor='#0d1117')
            plt.close()
            return path
        except Exception as e:
            print(f"   Chart generation failed: {e}")
            return None

    def _build_news_caption(self, nifty_data, news_items):
        today = datetime.now().strftime('%d %b %Y')
        sign  = '+' if nifty_data['change_percent'] >= 0 else ''
        cap   = (f"📊 NIFTY 50 — {today}\n"
                 f"₹{nifty_data['current_price']:,}  "
                 f"({sign}{nifty_data['change_percent']:.2f}%)\n\n")
        if news_items:
            cap += "📰 Today's Market News\n"
            cap += "━━━━━━━━━━━━━━━━━━━\n"
            for i, headline in enumerate(news_items, 1):
                cap += f"{i}. {headline}\n\n"
        cap += "Source: ET Markets"
        return cap

    def _send_photo(self, bot_token, chat_id, photo_path, caption):
        try:
            with open(photo_path, 'rb') as f:
                r = requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendPhoto",
                    data={'chat_id': chat_id, 'caption': caption},
                    files={'photo': f},
                    timeout=30
                )
            if r.status_code == 200:
                return True
            print(f"   ❌ Photo HTTP {r.status_code}: {r.text[:120]}")
            return False
        except Exception as e:
            print(f"   ❌ Photo Exception: {e}")
            return False

    def send_chart_and_news(self, nifty_data, news_items):
        """Send NIFTY chart image + news headlines to all groups."""
        bot_token = self._get_token()
        chat_ids  = self._get_chat_ids()
        caption   = self._build_news_caption(nifty_data, news_items)
        chart     = self.generate_nifty_chart()

        print(f"\n📤 Sending chart+news to {len(chat_ids)} groups...")
        for cid in chat_ids:
            if chart:
                ok = self._send_photo(bot_token, cid, chart, caption)
            else:
                # fallback to text if chart failed
                ok = self._post(bot_token, cid, caption)
            print(f"  → Group {cid}: {'✅' if ok else '❌'}")
            time.sleep(1)

    # ----------------------------------------------- Telegram sender 📤

    def _post(self, bot_token, chat_id, text):
        """Send one message; returns True on success."""
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                data={'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'},
                timeout=15
            )
            if r.status_code == 200:
                return True
            print(f"   ❌ HTTP {r.status_code}: {r.text[:120]}")
            return False
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False

    def _get_token(self):
        token = os.environ.get('TELEGRAM_TOKEN')
        if not token:
            token = "8982141225:AAG7RzT_sVheN8eVF2T6xeJIzrOvQ-I70ws"
            print("⚠️  Using hardcoded token.")
        return token

    def _get_chat_ids(self):
        if os.environ.get('TEST_MODE', 'false').lower() == 'true':
            print("🧪 TEST MODE — sending to test group only")
            return ["-1002955746386"]
        return ["-1001669216683", "-1003702373696", "-1001645367784", "-1002955746386"]

    def send_to_telegram(self, messages):
        """Send a list of message strings to all groups in order."""
        bot_token = self._get_token()
        chat_ids  = self._get_chat_ids()

        if isinstance(messages, str):
            messages = [messages]

        print(f"\n📤 Sending {len(messages)} part(s) to {len(chat_ids)} groups...")

        for cid in chat_ids:
            print(f"  → Group {cid}:")
            for i, msg in enumerate(messages, 1):
                ok = self._post(bot_token, cid, msg)
                print(f"    {'✅' if ok else '❌'} Part {i}/{len(messages)}")
                if i < len(messages):
                    time.sleep(1)   # keep messages in order, avoid rate limit

        print("\n✅ Telegram sending completed!")

    # ---------------------------------------- Sector / Gap / Volume 📡

    def get_sector_performance(self):
        sectors = [
            ('BANK',   '^NSEBANK'),
            ('IT',     '^CNXIT'),
            ('PHARMA', '^CNXPHARMA'),
            ('AUTO',   '^CNXAUTO'),
            ('FMCG',   '^CNXFMCG'),
            ('METAL',  '^CNXMETAL'),
            ('REALTY', '^CNXREALTY'),
            ('ENERGY', '^CNXENERGY'),
        ]
        results = []
        for name, symbol in sectors:
            try:
                h = yf.Ticker(symbol).history(period='2d')
                if len(h) < 2:
                    continue
                chg = (h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2] * 100
                results.append({'name': name, 'change': round(chg, 2)})
            except Exception:
                continue
        return sorted(results, key=lambda x: x['change'], reverse=True)

    def get_gap_scanner(self):
        up, down = [], []
        for symbol in self.nifty_50_symbols:
            try:
                h = yf.Ticker(symbol).history(period='5d', interval='1d')
                if len(h) < 2:
                    continue
                prev_close = h['Close'].iloc[-2]
                today_open = h['Open'].iloc[-1]
                gap_pct    = (today_open - prev_close) / prev_close * 100
                sym        = symbol.replace('.NS', '')
                if gap_pct >= 0.8:
                    up.append({'symbol': sym, 'gap_pct': round(gap_pct, 2), 'open': round(today_open, 2)})
                elif gap_pct <= -0.8:
                    down.append({'symbol': sym, 'gap_pct': round(gap_pct, 2), 'open': round(today_open, 2)})
            except Exception:
                continue
        return {
            'up':   sorted(up,   key=lambda x: x['gap_pct'], reverse=True)[:5],
            'down': sorted(down, key=lambda x: x['gap_pct'])[:5],
        }

    def get_volume_spikes(self):
        spikes = []
        for symbol in self.nifty_50_symbols:
            try:
                h = yf.Ticker(symbol).history(period='25d', interval='1d')
                if len(h) < 21 or 'Volume' not in h.columns:
                    continue
                avg_vol   = h['Volume'].iloc[-21:-1].mean()
                today_vol = h['Volume'].iloc[-1]
                if avg_vol == 0:
                    continue
                ratio = today_vol / avg_vol
                if ratio >= 2.0:
                    chg = (h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2] * 100
                    spikes.append({
                        'symbol':     symbol.replace('.NS', ''),
                        'ratio':      round(ratio, 1),
                        'change_pct': round(chg, 2),
                        'price':      round(h['Close'].iloc[-1], 2),
                    })
            except Exception:
                continue
        return sorted(spikes, key=lambda x: x['ratio'], reverse=True)[:6]

    def build_part4_sector_performance(self, sectors):
        m = f"🏭 *SECTOR PERFORMANCE*\n\n"
        for s in sectors:
            icon    = "🟢" if s['change'] > 0 else ("🔴" if s['change'] < 0 else "⚪")
            bar_len = min(abs(int(s['change'] * 2)), 6)
            bar     = ("█" * bar_len) if bar_len > 0 else "─"
            m += f"{icon} *{s['name']:<8}*  {s['change']:+.2f}%  {bar}\n"
        if len(sectors) >= 2:
            m += f"\n🏆 Leading : *{sectors[0]['name']}*  ({sectors[0]['change']:+.2f}%)\n"
            m += f"⬇️  Lagging : *{sectors[-1]['name']}*  ({sectors[-1]['change']:+.2f}%)\n"
        m += f"━━━━━━━━━━━━━━━━━━━\n"
        m += f"_Part 4 of 5_"
        return m

    def build_part5_gap_volume(self, gaps, volume_spikes):
        m = f"📡 *GAP SCANNER + VOLUME SPIKES*\n\n"
        if gaps['up']:
            m += f"⬆️ *GAP UP*\n"
            for s in gaps['up']:
                m += f"  📈 *{s['symbol']}*  Open ₹{s['open']}  (+{s['gap_pct']}%)\n"
            m += "\n"
        if gaps['down']:
            m += f"⬇️ *GAP DOWN*\n"
            for s in gaps['down']:
                m += f"  📉 *{s['symbol']}*  Open ₹{s['open']}  ({s['gap_pct']}%)\n"
            m += "\n"
        if not gaps['up'] and not gaps['down']:
            m += f"_No significant gaps today_\n\n"
        if volume_spikes:
            m += f"🔊 *VOLUME SPIKES  (2x+ avg)*\n"
            for s in volume_spikes:
                arrow = "📈" if s['change_pct'] > 0 else "📉"
                m += f"  {arrow} *{s['symbol']}*  {s['ratio']}x vol  {s['change_pct']:+.2f}%  ₹{s['price']}\n"
        else:
            m += f"_No volume spikes detected today_"
        m += f"\n━━━━━━━━━━━━━━━━━━━\n"
        m += f"_Part 5 of 5_"
        return m

    # ---------------------------------------- ORB breakout scanner 📊

    def get_first_candle_breakouts(self):
        """Scan top 20 intraday gainers for first 15-min candle breakouts."""
        print("   Step 1: Fetching daily data to rank gainers...")
        ranked = []
        for symbol in self.nifty_50_symbols:
            try:
                hist = yf.Ticker(symbol).history(period='5d', interval='1d')
                if len(hist) < 2:
                    continue
                prev  = hist['Close'].iloc[-2]
                curr  = hist['Close'].iloc[-1]
                chg   = (curr - prev) / prev * 100
                ranked.append({'symbol': symbol, 'change_pct': round(chg, 2), 'current': round(curr, 2)})
            except Exception:
                continue

        top20 = sorted(ranked, key=lambda x: x['change_pct'], reverse=True)[:20]
        print(f"   Top 20 gainers identified. Scanning 15-min candles...")

        buys, sells = [], []
        for stock in top20:
            try:
                intra = yf.Ticker(stock['symbol']).history(period='1d', interval='15m')
                if len(intra) < 2:
                    continue

                first_high  = round(intra['High'].iloc[0], 2)
                first_low   = round(intra['Low'].iloc[0], 2)
                curr_price  = round(intra['Close'].iloc[-1], 2)
                risk        = round(first_high - first_low, 2)
                sym         = stock['symbol'].replace('.NS', '')
                avg_vol     = intra['Volume'].mean() if 'Volume' in intra.columns and intra['Volume'].mean() > 0 else 1
                vol_ratio   = round(intra['Volume'].iloc[0] / avg_vol, 1) if avg_vol > 0 else 1.0

                if risk <= 0:
                    continue

                if curr_price > first_high:
                    buys.append({
                        'symbol':     sym,
                        'entry':      first_high,
                        'sl':         first_low,
                        'target':     round(first_high + 2 * risk, 2),
                        'risk':       risk,
                        'change_pct': stock['change_pct'],
                        'current':    curr_price,
                    })
                elif curr_price < first_low:
                    sells.append({
                        'symbol':     sym,
                        'entry':      first_low,
                        'sl':         first_high,
                        'target':     round(first_low - 2 * risk, 2),
                        'risk':       risk,
                        'change_pct': stock['change_pct'],
                        'current':    curr_price,
                    })
            except Exception:
                continue

        return {'buy': buys, 'sell': sells, 'top20': top20}

    def build_breakout_message(self, breakouts):
        now   = datetime.now().strftime('%d %b %Y  %I:%M %p')
        buys  = breakouts['buy']
        sells = breakouts['sell']

        m  = f"⚡ *FIRST 15-MIN CANDLE BREAKOUT*\n"
        m += f"🕘 {now} IST\n"
        m += f"_(Scanned: Top 20 Gainers — NIFTY 50)_\n"
        m += f"━━━━━━━━━━━━━━━━━━━\n\n"

        if buys:
            m += f"🟢 *BUY SIGNALS  ({len(buys)})*\n\n"
            for s in buys:
                m += f"📈 *{s['symbol']}*  (+{s['change_pct']}%)\n"
                m += f"  Entry  : ₹{s['entry']}\n"
                m += f"  Stop   : ₹{s['sl']}  (Risk ₹{s['risk']:.1f})\n"
                m += f"  Target : ₹{s['target']}  (RR 1:2)\n\n"

        if sells:
            m += f"🔴 *SELL SIGNALS  ({len(sells)})*\n\n"
            for s in sells:
                m += f"📉 *{s['symbol']}*  ({s['change_pct']}%)\n"
                m += f"  Entry  : ₹{s['entry']}\n"
                m += f"  Stop   : ₹{s['sl']}  (Risk ₹{s['risk']:.1f})\n"
                m += f"  Target : ₹{s['target']}  (RR 1:2)\n\n"

        if not buys and not sells:
            m += f"😴 *No breakouts yet*\n"
            m += f"_All top 20 gainers still within_\n"
            m += f"_their first 15-min candle range_\n\n"

        m += f"━━━━━━━━━━━━━━━━━━━\n"
        m += f"• First candle: 9:15 – 9:30 AM\n"
        m += f"• Max 2% capital per trade\n"
        m += f"⚠️ _Not SEBI registered advice_"
        return m

    def send_breakout_alert(self, breakouts=None):
        if breakouts is None:
            breakouts = self.get_first_candle_breakouts()
        bot_token = self._get_token()
        chat_ids  = self._get_chat_ids()
        msg       = self.build_breakout_message(breakouts)

        print(f"\n📤 Sending breakout alert to {len(chat_ids)} groups...")
        for cid in chat_ids:
            ok = self._post(bot_token, cid, msg)
            print(f"  → {cid}: {'✅' if ok else '❌'}")
            time.sleep(1)
        return breakouts

    # ------------------------------------------ legacy compatibility

    def generate_intelligent_news(self, nifty_data, prediction, stocks_data):
        return []

    def format_telegram_message(self, nifty_data, stocks_data, prediction, market_news):
        """Legacy method — returns Part 1 only for backward compatibility."""
        return self.build_part1_market_pulse(nifty_data, prediction)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    today = date.today()
    if today.weekday() >= 5:
        print(f"Weekend ({today.strftime('%A %d-%b-%Y')}). NSE closed. Skipping.")
        sys.exit(0)
    if today in NSE_HOLIDAYS:
        print(f"NSE Holiday ({today.strftime('%d-%b-%Y')}). Market closed. Skipping.")
        sys.exit(0)

    print("🚀 Starting Billionaires Group Market Analysis Bot...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    bot = SmartFinanceDashboard()

    print("📊 Fetching Nifty data...")
    nifty = bot.get_accurate_nifty_data()
    print(f"   Nifty: ₹{nifty['current_price']:,} ({nifty['change_percent']:+.2f}%)")

    print("📈 Fetching stock data...")
    stocks = bot.get_stock_data_batch()
    print(f"   {len(stocks)} stocks fetched")

    print("🧠 Generating prediction...")
    pred = bot.get_intelligent_prediction(nifty, stocks)
    print(f"   Outlook: {pred['direction']} ({pred['confidence']})")

    print("🔍 Finding swing setups...")
    swings = bot.get_swing_setups(stocks)
    print(f"   Buys: {len(swings['swing_buys'])}  Momentum: {len(swings['momentum'])}  Avoid: {len(swings['avoid'])}")

    print("📝 Building messages...")
    part1 = bot.build_part1_market_pulse(nifty, pred)
    part2 = bot.build_part2_movers(stocks)
    part3 = bot.build_part3_swing(swings)

    for i, p in enumerate([part1, part2, part3], 1):
        flag = "✅" if len(p) <= 4096 else "⚠️ OVER LIMIT"
        print(f"   Part {i}: {len(p)} chars {flag}")

    print("📰 Fetching market news...")
    news = bot.fetch_market_news()
    print(f"   {len(news)} headlines fetched")

    print("-" * 50)
    bot.send_to_telegram([part1, part2, part3])
    bot.send_chart_and_news(nifty, news)
    print("-" * 50)
    print("✅ Done!")
