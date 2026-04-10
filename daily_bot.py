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
            signal, action = "OVERSOLD", "⚠️ Caution - wait for trend confirmation"
            explanation = "Stock is oversold but in bullish trend" if trend == "BULLISH" else "Oversold, wait for confirmation"
            risk_level = "HIGH"
        elif rsi_value > 70:
            signal, action = "OVERBOUGHT", "⚠️ Consider taking profits"
            explanation = "Overbought but strong trend" if trend == "BULLISH" else "High risk of correction"
            risk_level = "HIGH"
        else:
            signal, action, explanation = "NEUTRAL", "📊 Monitor for breakout signals", "Normal trading range"
            risk_level = "LOW"
        return {'signal': signal, 'action': action, 'explanation': explanation, 'risk_level': risk_level}

    def get_advanced_technical_analysis(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1mo")
            if len(hist) < 20: 
                return {'trend': 'NEUTRAL', 'rsi': 50, 'rsi_signal': 'N/A', 'rsi_action': 'N/A'}
            
            hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
            hist['RSI'] = ta.momentum.RSIIndicator(hist['Close']).rsi()
            
            curr, sma, rsi = hist['Close'][-1], hist['SMA_20'][-1], hist['RSI'][-1]
            trend = "BULLISH" if curr > sma else "BEARISH"
            analysis = self.get_rsi_interpretation(rsi, trend)
            
            return {
                'trend': trend, 
                'rsi': round(rsi, 2), 
                'rsi_signal': analysis['signal'], 
                'rsi_action': analysis['action']
            }
        except: 
            return {'trend': 'NEUTRAL', 'rsi': 50, 'rsi_signal': 'N/A', 'rsi_action': 'N/A'}

    def get_accurate_nifty_data(self):
        try:
            nifty = yf.Ticker("^NSEI")
            hist = nifty.history(period="1mo")
            if len(hist) < 2:
                return {'current_price': 0, 'change': 0, 'change_percent': 0, 'high_52w': 0, 'low_52w': 0}
            
            curr = hist['Close'][-1]
            prev = hist['Close'][-2]
            high_52w = hist['Close'].max()
            low_52w = hist['Close'].min()
            
            return {
                'current_price': round(curr, 2), 
                'change': round(curr - prev, 2), 
                'change_percent': round(((curr - prev) / prev) * 100, 2), 
                'high_52w': round(high_52w, 2), 
                'low_52w': round(low_52w, 2)
            }
        except: 
            return {'current_price': 0, 'change': 0, 'change_percent': 0, 'high_52w': 0, 'low_52w': 0}

    def get_stock_data_batch(self):
        stocks_data = []
        for symbol in self.nifty_50_symbols:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period="5d")
                if len(hist) < 2: 
                    continue
                
                curr, prev = hist['Close'][-1], hist['Close'][-2]
                tech = self.get_advanced_technical_analysis(symbol)
                
                stocks_data.append({
                    'symbol': symbol.replace('.NS', ''), 
                    'current_price': round(curr, 2), 
                    'change_percent': round(((curr - prev) / prev) * 100, 2),
                    'change': round(curr - prev, 2),
                    'technicals': tech
                })
                time.sleep(0.05)
            except: 
                continue
        
        return sorted(stocks_data, key=lambda x: x['change_percent'], reverse=True)

    def get_intelligent_prediction(self, nifty_data, stocks_data):
        gainers = [s for s in stocks_data if s['change_percent'] > 0]
        losers = [s for s in stocks_data if s['change_percent'] < 0]
        
        # Calculate confidence based on breadth
        breadth = len(gainers) - len(losers)
        if abs(breadth) > 15:
            confidence = "HIGH"
        elif abs(breadth) > 5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        direction = 'UPWARD' if len(gainers) > len(losers) else 'DOWNWARD'
        
        # Generate analysis reason
        if len(gainers) > len(losers) * 1.5:
            reason = "Strong buying momentum across majority of stocks"
        elif len(gainers) > len(losers):
            reason = "Moderate positive breadth with selective buying"
        else:
            reason = "Selling pressure dominates the market"
        
        return {
            'direction': direction, 
            'confidence': confidence, 
            'reason': reason,
            'gainers_count': len(gainers), 
            'losers_count': len(losers), 
            'market_breadth': breadth
        }

    def get_bullish_stocks_to_watch(self, stocks_data):
        # Filter stocks that are bullish and have positive momentum
        bullish = [s for s in stocks_data if s['technicals']['trend'] == 'BULLISH' and s['change_percent'] > 0]
        return [s['symbol'] for s in bullish[:5]]

    def get_stocks_to_avoid(self, stocks_data):
        # Filter stocks that are bearish or overbought
        avoid = [s for s in stocks_data if s['technicals']['trend'] == 'BEARISH' or s['technicals']['rsi'] > 70]
        return [s['symbol'] for s in avoid[:5]]

    def get_trading_recommendations(self, stocks_data):
        strong_buy = []
        avoid_sell = []
        
        for s in stocks_data:
            if s['technicals']['rsi'] < 30 and s['technicals']['trend'] == 'BULLISH':
                strong_buy.append(s['symbol'])
            elif s['technicals']['rsi'] > 70 and s['technicals']['trend'] == 'BEARISH':
                avoid_sell.append(s['symbol'])
        
        return strong_buy[:5], avoid_sell[:5]

    def format_telegram_message(self, nifty_data, stocks_data, prediction, current_time):
        # Get top 10 gainers and losers
        gainers = stocks_data[:10]
        losers = stocks_data[-10:][::-1]  # Reverse to show biggest losers first
        
        # Get recommendations
        strong_buy, avoid_sell = self.get_trading_recommendations(stocks_data)
        bullish_watch = self.get_bullish_stocks_to_watch(stocks_data)
        stocks_avoid = self.get_stocks_to_avoid(stocks_data)
        
        # Emoji for NIFTY change
        nifty_emoji = "🟢" if nifty_data['change_percent'] >= 0 else "🔴"
        
        # Build message
        msg = f"📊 *Billionaires Group ADVANCED MARKET ANALYSIS* 📊\n"
        msg += f"Time: {current_time}\n\n"
        
        msg += f"🎯 *NIFTY 50:* ₹{nifty_data['current_price']:,} {nifty_emoji}\n"
        msg += f"📈 Change: ₹{nifty_data['change']:+.2f} ({nifty_data['change_percent']:+.2f}%)\n"
        msg += f"📊 52W Range: ₹{nifty_data['low_52w']:,} - ₹{nifty_data['high_52w']:,}\n\n"
        
        msg += f"📖 *RSI GUIDE:*\n"
        msg += f"• <30: OVERSOLD (Potential BUY) 📈\n"
        msg += f"• 30-70: NEUTRAL (HOLD/Monitor) 📊\n"
        msg += f"• >70: OVERBOUGHT (Potential SELL) 📉\n\n"
        
        msg += f"📈 *MARKET OUTLOOK:* {prediction['direction']}\n"
        msg += f"🎯 Confidence: {prediction['confidence']}\n"
        msg += f"💡 Analysis: {prediction['reason']}\n\n"
        
        msg += f"📈 Advancing Stocks: {prediction['gainers_count']}\n"
        msg += f"📉 Declining Stocks: {prediction['losers_count']}\n"
        msg += f"📊 Market Breadth: {prediction['market_breadth']:+.0f}\n\n"
        
        msg += f"🏆 *TOP 10 GAINERS* 🏆\n"
        for i, s in enumerate(gainers, 1):
            trend_emoji = "🟢" if s['technicals']['trend'] == 'BULLISH' else "🔴"
            msg += f"{i}. {s['symbol']}: ₹{s['current_price']:,} ({s['change_percent']:+.2f}%) {trend_emoji}\n"
            msg += f"   📊 RSI: {s['technicals']['rsi']} | Trend: {s['technicals']['trend']}\n"
            msg += f"   ⚠️ Signal: {s['technicals']['rsi_signal']}\n"
            msg += f"   💡 Action: {s['technicals']['rsi_action']}\n"
            msg += f"   ───────────────────\n"
        
        msg += f"\n📉 *TOP 10 LOSERS* 📉\n"
        for i, s in enumerate(losers, 1):
            trend_emoji = "🟢" if s['technicals']['trend'] == 'BULLISH' else "🔴"
            msg += f"{i}. {s['symbol']}: ₹{s['current_price']:,} ({s['change_percent']:+.2f}%) {trend_emoji}\n"
            msg += f"   📊 RSI: {s['technicals']['rsi']} | Trend: {s['technicals']['trend']}\n"
            msg += f"   ⚠️ Signal: {s['technicals']['rsi_signal']}\n"
            msg += f"   💡 Action: {s['technicals']['rsi_action']}\n"
            msg += f"   ───────────────────\n"
        
        msg += f"\n💡 *TRADING RECOMMENDATIONS* 💡\n"
        msg += f"✅ Bullish Stocks to Watch: {', '.join(bullish_watch)}\n"
        msg += f"❌ Stocks to Avoid: {', '.join(stocks_avoid)}\n\n"
        
        msg += f"🎯 *TRADING STRATEGY GUIDE* 🎯\n"
        msg += f"• OVERBOUGHT + BEARISH = ❌ AVOID/SELL\n"
        msg += f"• OVERBOUGHT + BULLISH = ⚠️ PARTIAL PROFIT\n"
        msg += f"• OVERSOLD + BULLISH = ✅ STRONG BUY\n"
        msg += f"• OVERSOLD + BEARISH = ⏳ WAIT FOR CONFIRMATION\n"
        msg += f"• NEUTRAL = 📊 MONITOR BREAKOUT\n\n"
        
        msg += f"🛡️ *RISK MANAGEMENT TIPS:*\n"
        msg += f"• Never invest more than 5% in one stock\n"
        msg += f"• Use stop-loss for every trade\n"
        msg += f"• OVERBOUGHT stocks need tight stop-loss\n"
        msg += f"• OVERSOLD stocks can use wider stops\n\n"
        
        msg += f"📰 *MARKET INSIGHTS* 📰\n"
        msg += f"{'🟢 📈 Bullish Momentum Building' if prediction['direction'] == 'UPWARD' else '🔴 📉 Bearish Pressure Increasing'}\n\n"
        
        msg += f"Data Source: Yahoo Finance | Analysis Time: {current_time.split()[1]}"
        
        return msg

    def send_to_telegram(self, message):
        bot_token = os.environ.get('TELEGRAM_TOKEN')
        if not bot_token:
            print("Warning: TELEGRAM_TOKEN not found in environment variables")
            print("Message preview:")
            print(message[:500])
            return
        
        chat_ids = ["-1001669216683", "-1003702373696", "-1001645367784"]
        
        for cid in chat_ids:
            try:
                response = requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                    data={'chat_id': cid, 'text': message, 'parse_mode': 'Markdown'},
                    timeout=10
                )
                if response.status_code != 200:
                    print(f"Failed to send to {cid}: {response.text}")
            except Exception as e:
                print(f"Error sending to {cid}: {e}")

if __name__ == "__main__":
    bot = SmartFinanceDashboard()
    
    print("Fetching NIFTY data...")
    nifty = bot.get_accurate_nifty_data()
    
    print("Fetching stock data for NIFTY 50...")
    stocks = bot.get_stock_data_batch()
    
    print("Generating predictions...")
    pred = bot.get_intelligent_prediction(nifty, stocks)
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print("Formatting message...")
    msg = bot.format_telegram_message(nifty, stocks, pred, current_time)
    
    print("\n" + "="*50)
    print("MESSAGE PREVIEW:")
    print("="*50)
    print(msg)
    print("="*50)
    
    print("\nSending to Telegram...")
    bot.send_to_telegram(msg)
    print("Done!")
