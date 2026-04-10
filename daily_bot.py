import yfinance as yf
import pandas as pd
import random
from datetime import datetime
import ta
import requests
import os
import matplotlib.pyplot as plt
import mplfinance as mpf  # specialized library for financial charting

class SmartFinanceDashboard:
    def __init__(self):
        # Your target Chat IDs and Bot Token
        self.bot_token = os.environ.get('TELEGRAM_TOKEN', "YOUR_HARDCODED_TOKEN_FOR_TESTING")
        self.chat_ids = ["-1001669216683"] # Add your student group IDs here

        # Educational Content Database
        self.glossary = {
            "RSI": "Momentum indicator (0-100). >70 is Overbought (may drop), <30 is Oversold (may rise).",
            "SMA_20": "Simple Moving Average: The average close price of the last 20 days. Defines the short-term trend."
        }
        self.chart_filename = "temp_chart.png"

    # --- 1. Educational Engine ---
    def get_educational_moment(self):
        psychology = [
            "🧠 *Mindset:* Don't let yesterday's loss affect today's decision.",
            "📉 *Rule:* Cut your losses short and let your winners run.",
            "⚖️ *Lesson:* The trend is your friend until the end."
        ]
        term, definition = random.choice(list(self.glossary.items()))
        return f"{random.choice(psychology)}\n💡 *Concept:* *{term}* - {definition}"

    # --- 2. Data & Charting Engine ---
    def analyze_symbol(self, symbol="^NSEI"): # Defaults to Nifty 50
        """Fetches data, runs analysis, and generates a professional chart."""
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3mo") # Need enough data for SMA

        if len(hist) < 20:
            return None, "Insufficient data."

        # Analysis
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['RSI'] = ta.momentum.RSIIndicator(hist['Close']).rsi()

        curr_p = hist['Close'][-1]
        prev_p = hist['Close'][-2]
        change_pct = ((curr_p - prev_p) / prev_p) * 100
        rsi = round(hist['RSI'][-1], 2)
        trend = "BULLISH" if curr_p > hist['SMA_20'][-1] else "BEARISH"

        # Generate Chart (using mplfinance for professional looking candle charts)
        self.generate_pro_chart(hist, symbol)

        analysis_results = {
            'symbol': symbol,
            'price': round(curr_p, 2),
            'change_pct': round(change_pct, 2),
            'rsi': rsi,
            'trend': trend
        }
        return analysis_results, "Success"

    def generate_pro_chart(self, hist_data, symbol):
        """Creates a professional candlestick chart with SMA."""
        # Clean up data for mplfinance
        df = hist_data.copy()
        df.index.name = 'Date'

        # Technical Indicators to plot
        ap = [
            mpf.make_addplot(df['SMA_20'], color='blue', width=1.5, panel=0), # Add SMA
        ]

        # Define the plot style
        my_style = mpf.make_mpf_style(base_mpf_style='charles', gridstyle='')

        # Plot the chart and save to file
        print(f"📊 Generating professional chart for {symbol}...")
        mpf.plot(df, type='candle', style=my_style, addplot=ap,
                 title=f"\n{symbol} Analysis (Last 3 Months)",
                 ylabel='Price',
                 volume=False,
                 savefig=self.chart_filename) # Critical: Saves the image

    # --- 3. Telegram & Formatting Engine ---
    def format_analysis_caption(self, results):
        """Formats the analysis and educational content into a compact caption."""
        msg = f"📈 *DAILY MARKET INTEL: {results['symbol']}* 📉\n"
        msg += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        # Market Analysis
        p_emoji = "🟢" if results['change_pct'] > 0 else "🔴"
        t_emoji = "📈" if results['trend'] == "BULLISH" else "📉"
        msg += f"{p_emoji} *Price:* ₹{results['price']:,.2f} ({results['change_pct']:+.2f}%)\n"
        msg += f"📊 *RSI:* {results['rsi']}\n"
        msg += f"{t_emoji} *20-Day Trend:* {results['trend']}\n\n"

        # Educational Corner (Dynamic and different every time)
        msg += "🎓 *STUDENT LEARNING CORNER*\n"
        msg += self.get_educational_moment() + "\n\n"

        msg += "_🛡️ Disclaimer: For educational purposes only._"
        return msg

    def send_to_telegram(self, message, image_path):
        """Sends an image with a formatted Markdown caption to all chat IDs."""
        print(f"\n📤 Attempting to send chart to {len(self.chat_ids)} groups...")
        send_photo_url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"

        for cid in self.chat_ids:
            try:
                # Need to open the image file in binary mode
                with open(image_path, 'rb') as photo:
                    payload = {
                        'chat_id': cid,
                        'caption': message,
                        'parse_mode': 'Markdown' # Markdown formatting for the caption
                    }
                    files = {'photo': photo}

                    response = requests.post(send_photo_url, data=payload, files=files, timeout=30)

                    if response.status_code == 200:
                        print(f"✅ Chart sent successfully to {cid}")
                    else:
                        print(f"❌ Failed to send to {cid}: {response.text}")

            except FileNotFoundError:
                print(f"❌ Error: Chart file '{image_path}' not found.")
            except Exception as e:
                print(f"❌ Critical Error sending to {cid}: {str(e)}")

        # Clean up the temporary file after sending
        if os.path.exists(image_path):
            os.remove(image_path)
            print("🧹 Temporary chart file cleaned up.")

    def run_automated_cycle(self):
        # 1. Analyze (fetches data, calculates technicals, and generates chart image)
        analysis, status = self.analyze_symbol("^NSEI") # Default to Nifty

        if analysis:
            # 2. Format the textual part (Market Summary + Education Moment)
            caption_text = self.format_analysis_caption(analysis)

            # 3. Send the image and the formatted caption together
            self.send_to_telegram(caption_text, self.chart_filename)
        else:
            print(f"❌ Automated cycle failed: {status}")

# --- Automation / Execution Loop ---
if __name__ == "__main__":
    print("🚀 Starting Billionaires Group Educational Bot with Charting...")
    
    bot = SmartFinanceDashboard()
    
    # You can set this up with a while loop + time.sleep() for continuous running
    # or trigger it daily with a scheduler (like cron or AWS Lambda).
    bot.run_automated_cycle()
    
    print("🏁 Cycle completed.")
