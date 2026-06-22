"""
Stock Market Bot — Streamlit Dashboard
Run: streamlit run dashboard.py
"""
import os
import sys
import subprocess
import threading
import queue
from datetime import datetime
import pytz
import streamlit as st

IST = pytz.timezone("Asia/Kolkata")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt")


def load_token():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip()
    return os.environ.get("TELEGRAM_TOKEN", "")


def save_token(token):
    with open(CONFIG_FILE, "w") as f:
        f.write(token.strip())


st.set_page_config(
    page_title="Stock Market Bot",
    page_icon="📈",
    layout="centered",
)

st.title("📈 Stock Market Bot Dashboard")

now_ist = datetime.now(IST)
st.caption(f"🕐 Current IST time: **{now_ist.strftime('%I:%M %p')}** — {now_ist.strftime('%A, %d %b %Y')}")

st.divider()

saved_token = load_token()
token = st.text_input(
    "Telegram Token (saved automatically)",
    value=saved_token,
    type="password",
    placeholder="Paste your bot token here — saved for next time",
)

if token and token != saved_token:
    save_token(token)
    st.success("Token saved!")

test_mode = st.toggle("Test mode (send to test group only)", value=False)

st.divider()


def run_script(script_name, token, test_mode, output_queue):
    env = os.environ.copy()
    env["TELEGRAM_TOKEN"] = token
    env["TEST_MODE"] = "true" if test_mode else "false"
    try:
        proc = subprocess.Popen(
            [sys.executable, script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        for line in proc.stdout:
            output_queue.put(line.rstrip())
        proc.wait()
        output_queue.put(f"__EXIT__{proc.returncode}")
    except Exception as e:
        output_queue.put(f"❌ Error: {e}")
        output_queue.put("__EXIT__1")


def show_output_area(script_name, button_label, description):
    st.subheader(button_label)
    st.caption(description)

    key = script_name.replace(".", "_")

    if st.button(f"▶ Send {button_label}", key=f"btn_{key}", use_container_width=True):
        if not token:
            st.error("Please enter your Telegram token above first.")
            return

        output_box = st.empty()
        lines = []
        q = queue.Queue()

        t = threading.Thread(
            target=run_script,
            args=(script_name, token, test_mode, q),
            daemon=True,
        )
        t.start()

        while True:
            try:
                line = q.get(timeout=60)
            except queue.Empty:
                lines.append("⚠️ Timeout waiting for output.")
                break

            if line.startswith("__EXIT__"):
                code = line.replace("__EXIT__", "")
                if code == "0":
                    lines.append("\n✅ Sent successfully!")
                else:
                    lines.append(f"\n❌ Something went wrong (exit code {code}).")
                break
            else:
                lines.append(line)

            output_box.code("\n".join(lines), language="")

        output_box.code("\n".join(lines), language="")
        t.join(timeout=5)


# ── 1. Morning Alert ─────────────────────────────────────────────────────────
show_output_area(
    script_name="daily_bot.py",
    button_label="Morning Market Pulse — 9:20 AM IST",
    description="Market overview · Top movers · Sector performance · Gap scanner · India VIX",
)

st.divider()

# ── 2. Breakout Alert ────────────────────────────────────────────────────────
show_output_area(
    script_name="breakout_alert.py",
    button_label="Breakout Signals — 9:32 AM IST",
    description="First 15-min candle breakout scanner · BUY / SELL signals with SL & targets",
)

st.divider()

# ── 3. EOD Report ────────────────────────────────────────────────────────────
show_output_area(
    script_name="eod_report.py",
    button_label="EOD Performance Report — 4:00 PM IST",
    description="End-of-day summary · Targets hit · SLs hit · Open positions",
)

st.divider()
st.caption("Test Mode OFF = sends to all live groups · Test Mode ON = test group only")
