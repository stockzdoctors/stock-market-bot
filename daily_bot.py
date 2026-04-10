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

            signal, action = "OVERSOLD", "✅ Good buying opportunity"

            explanation = "Stock is oversold but in bullish trend" if trend == "BULLISH" else "Oversold, wait for confirmation"

        elif rsi_value > 70:

            signal, action = "OVERBOUGHT", "⚠️ Consider taking profits"

            explanation = "Overbought but strong trend" if trend == "BULLISH" else "High risk of correction"

        else:

            signal, action, explanation = "NEUTRAL", "📊 Monitor for breakout", "Normal trading range"

        return {'signal': signal, 'action': action, 'explanation': explanation, 'risk_level': 'LOW' if signal == 'NEUTRAL' else 'HIGH'}



    def get_advanced_technical_analysis(self, symbol):

        try:

            stock = yf.Ticker(symbol)

            hist = stock.history(period="1mo")

            if len(hist) < 20: return {'trend': 'NEUTRAL', 'rsi': 50}

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

            curr = hist['Close'][-1]

            prev = hist['Close'][-2]

            return {'current_price': round(curr, 2), 'change': round(curr - prev, 2), 'change_percent': round(((curr - prev) / prev) * 100, 2), 'high_52w': round(hist['Close'].max(), 2), 'low_52w': round(hist['Close'].min(), 2)}

        except: return {'current_price': 0, 'change': 0, 'change_percent': 0, 'high_52w': 0, 'low_52w': 0}



    def get_stock_data_batch(self):

        stocks_data = []

        for symbol in self.nifty_50_symbols:

            try:

                stock = yf.Ticker(symbol)

                hist = stock.history(period="2d")

                if len(hist) < 2: continue

                curr, prev = hist['Close'][-1], hist['Close'][-2]

                tech = self.get_advanced_technical_analysis(symbol)

                stocks_data.append({'symbol': symbol.replace('.NS', ''), 'current_price': round(curr, 2), 'change_percent': round(((curr - prev) / prev) * 100, 2), 'technicals': tech})

                time.sleep(0.05)

            except: continue

        return sorted(stocks_data, key=lambda x: x['change_percent'], reverse=True)



    def get_intelligent_prediction(self, nifty_data, stocks_data):

        gainers = [s for s in stocks_data if s['change_percent'] > 0]

        losers = [s for s in stocks_data if s['change_percent'] < 0]

        direction = 'UPWARD' if len(gainers) > len(losers) else 'DOWNWARD'

        return {'direction': direction, 'confidence': 'MEDIUM', 'reason': 'Market breadth analysis', 'gainers_count': len(gainers), 'losers_count': len(losers), 'market_breadth': len(gainers) - len(losers)}



    def generate_intelligent_news(self, nifty_data, prediction, stocks_data):

        return [{'title': 'Market Trend Update', 'summary': f"Analysis based on {len(stocks_data)} stocks", 'impact': 'NEUTRAL'}]



    def format_telegram_message(self, nifty_data, stocks_data, prediction, market_news):

        gainers, losers = stocks_data[:5], stocks_data[-5:]

        msg = f"📊 *Billionaires Group Market Analysis*\n\n🎯 *NIFTY 50:* ₹{nifty_data['current_price']} ({nifty_data['change_percent']}%)\n\n"

        msg += f"{'📈' if prediction['direction'] == 'UPWARD' else '📉'} *Outlook:* {prediction['direction']}\n\n🏆 *Top 5 Gainers:*\n"

        for s in gainers: msg += f"• {s['symbol']}: {s['change_percent']}%\n"

        msg += f"\n📉 *Top 5 Losers:*\n"

        for s in losers: msg += f"• {s['symbol']}: {s['change_percent']}%\n"

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

    pred = bot.get_intelligent_prediction(nifty, stocks)

    news = bot.generate_intelligent_news(nifty, pred, stocks)

    msg = bot.format_telegram_message(nifty, stocks, pred, news)

    bot.send_to_telegram(msg)