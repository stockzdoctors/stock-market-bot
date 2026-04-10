import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import ta
import requests
import os

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

    def get_rsi_interpretation(self, rsi_value, trend):
        if rsi_value < 30:
            signal, action = "OVERSOLD", "✅ BUY OPPORTUNITY"
            explanation = "Bullish bounce expected" if trend == "BULLISH" else "Wait for trend change"
        elif rsi_value > 70:
            signal, action = "OVERBOUGHT", "⚠️ PROFIT BOOKING"
            explanation = "High risk of correction"
        else:
            signal, action, explanation = "NEUTRAL", "📊 MONITOR", "Stable range"
        return {'signal': signal, 'action': action, 'explanation': explanation}

    def get_advanced_technical_analysis(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1mo")
            if len(hist) < 20: return {'trend': 'NEUTRAL', 'rsi': 50, 'rsi_signal': 'N/A', 'rsi_action': 'N/A'}
            hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
            hist['RSI'] = ta.momentum.RSIIndicator(hist['Close']).rsi()
            curr, sma, rsi = hist['Close'][-1], hist['SMA_20'][-1], hist['RSI'][-1]
            trend = "BULLISH" if curr > sma else "BEARISH"
            analysis = self.get_rsi_interpretation(rsi, trend)
            return {'trend': trend, 'rsi': round(rsi, 2), 'rsi_signal': analysis['signal'], 'rsi_action': analysis['action']}
        except: return {'trend': 'NEUTRAL', 'rsi': 50, 'rsi_signal': 'N/A', 'rsi_action': 'N/A'}

    def get_accurate_nifty_data(self):
        try:
            nifty = yf.Ticker("^NSEI")
            hist = nifty.history(period="5d")
            curr, prev = hist['Close'][-1], hist['Close'][-2]
            return {'current_price': round(curr, 2), 'change_percent': round(((curr - prev) / prev) * 100, 2)}
        except: return {'current_price': 0, 'change_percent': 0}

    def get_stock_data_batch(self):
        stocks_data = []
        for symbol in self.nifty_50_symbols:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period="2d")
                if len(hist) < 2: continue
                curr, prev, vol = hist['Close'][-1], hist['Close'][-2], hist['Volume'][-1]
                tech = self.get_advanced_technical_analysis(symbol)
                stocks_data.append({'symbol': symbol.replace('.NS', ''), 'current_price': round(curr, 2), 
                                    'change_percent': round(((curr - prev) / prev) * 100, 2), 
                                    'volume': vol, 'technicals': tech})
                time.sleep(0.05)
            except: continue
        return sorted(stocks_data, key=lambda x: x['change_percent'], reverse=True)

    def format_telegram_message(self, nifty_data, stocks_data):
        # Calculate Market Breadth
        bullish_count = len([s for s in stocks_data if s['technicals']['trend'] == 'BULLISH'])
        breadth_pct = (bullish_count / len(stocks_data)) * 100
        
        msg = f"🚀 *BILLIONAIRES GROUP: MARKET SCAN*\n📅 {datetime.now().strftime('%d %b | %H:%M')}\n\n"
        msg += f"🎯 *NIFTY 50:* ₹{nifty_data['current_price']:,} ({nifty_data['change_percent']:+.2f}%)\n"
        msg += f"📈 *Market Breadth:* {breadth_pct:.0f}% Bullish Setup\n\n"
        
        msg += f"🏆 *TOP 3 MOMENTUM GAINERS*\n"
        for s in stocks_data[:3]:
            msg += f"• {s['symbol']}: {s['change_percent']:+.2f}% | RSI:{s['technicals']['rsi']}\n"
        
        msg += f"\n⚠️ *ACTIONABLE SIGNALS*\n"
        signals = [s for s in stocks_data if s['technicals']['rsi_signal'] in ["OVERSOLD", "OVERBOUGHT"]][:3]
        for s in signals:
            msg += f"• {s['symbol']}: {s['technicals']['rsi_signal']} -> {s['technicals']['rsi_action']}\n"
        
        msg += f"\n💡 *Stockz Doctors Note:* Monitor volumes on breakout stocks.\n"
        msg += f"_Data accurate as of {datetime.now().strftime('%H:%M')}_"
        return msg

    def send_to_telegram(self, message):
        bot_token = os.environ.get('TELEGRAM_TOKEN')
        chat_ids = ["-1001669216683", "-1003702373696", "-1001645367784"]
        for cid in chat_ids:
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data={'chat_id': cid, 'text': message, 'parse_mode': 'Markdown'})

if __name__ == "__main__":
    bot = SmartFinanceDashboard()
    nifty = bot.get_accurate_nifty_data()
    stocks = bot.get_stock_data_batch()
    msg = bot.format_telegram_message(nifty, stocks)
    bot.send_to_telegram(msg)
