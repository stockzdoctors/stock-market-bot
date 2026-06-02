import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import warnings
import requests
import json
import logging
import hashlib
from io import StringIO

try:
    from alice_blue import AliceBlue
    ALICE_AVAILABLE = True
except ImportError:
    ALICE_AVAILABLE = False

from tvDatafeed import TvDatafeed, Interval

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="Billionaires Group — Algo Trading",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
:root {
    --bg-void:#060910; --bg-deep:#0b0f1a; --bg-card:#0f1520; --bg-card2:#131926;
    --bg-elevated:#1a2235; --border:rgba(255,255,255,0.06); --border-accent:rgba(250,196,0,0.3);
    --gold:#FAC400; --gold-dim:#c49a00; --gold-glow:rgba(250,196,0,0.15);
    --teal:#00D9C4; --teal-dim:rgba(0,217,196,0.12); --red:#FF4D6A; --green:#00E096;
    --text-primary:#F0F4FF; --text-secondary:#8A96B0; --text-muted:#4A5568;
    --radius-sm:8px; --radius-md:14px; --radius-lg:20px;
}
html,body,.stApp { background-color:var(--bg-void) !important; font-family:'DM Sans',sans-serif; color:var(--text-primary); }
#MainMenu,header,footer,.stDeployButton,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="stMainMenuPopover"],
section[data-testid="stSidebar"] footer,a[href*="streamlit.io"],
.viewerBadge_container__1QSob,._container_51w34_1,._viewerBadge_nim44_23,.stApp > header { display:none !important; }
section[data-testid="stSidebar"] { display:none !important; }
.main .block-container { padding:0 !important; max-width:100% !important; }
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:var(--bg-deep); }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:4px; }
@keyframes pulse-green { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.4; transform:scale(0.7); } }
.page-wrap { padding:2rem 2.5rem 4rem; max-width:1400px; margin:0 auto; }
.page-hero { margin-bottom:2rem; padding-bottom:1.5rem; border-bottom:1px solid var(--border); }
.page-hero-title { font-family:'Syne',sans-serif; font-size:1.6rem; font-weight:800; color:var(--text-primary); margin-bottom:4px; }
.page-hero-sub { font-size:0.82rem; color:var(--text-muted); }
.metric-row { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:24px; }
.metric-card { background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius-md); padding:1.2rem 1.4rem; position:relative; overflow:hidden; }
.metric-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,var(--gold),transparent); }
.metric-icon { width:38px; height:38px; border-radius:var(--radius-sm); background:var(--gold-glow); border:1px solid var(--border-accent); display:flex; align-items:center; justify-content:center; font-size:1rem; margin-bottom:1rem; }
.metric-value { font-family:'Space Mono',monospace; font-size:1.6rem; font-weight:700; color:var(--text-primary); line-height:1; margin-bottom:4px; }
.metric-label { font-size:0.72rem; color:var(--text-muted); letter-spacing:0.05em; text-transform:uppercase; }
.metric-card.green::before { background:linear-gradient(90deg,var(--green),transparent); }
.metric-card.green .metric-icon { background:rgba(0,224,150,0.1); border-color:rgba(0,224,150,0.25); }
.metric-card.red::before { background:linear-gradient(90deg,var(--red),transparent); }
.metric-card.red .metric-icon { background:rgba(255,77,106,0.1); border-color:rgba(255,77,106,0.25); }
.metric-card.teal::before { background:linear-gradient(90deg,var(--teal),transparent); }
.metric-card.teal .metric-icon { background:var(--teal-dim); border-color:rgba(0,217,196,0.25); }
.section-header { display:flex; align-items:center; gap:12px; margin:2rem 0 1rem; }
.section-header-line { flex:1; height:1px; background:var(--border); }
.section-title { font-family:'Syne',sans-serif; font-size:0.78rem; font-weight:700; color:var(--text-muted); letter-spacing:0.15em; text-transform:uppercase; white-space:nowrap; }
.setup-card { background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius-lg); padding:0; margin-bottom:1rem; overflow:hidden; }
.setup-card-header { display:flex; align-items:center; gap:14px; padding:1.2rem 1.6rem; border-bottom:1px solid var(--border); background:var(--bg-card2); }
.setup-card-icon { width:42px; height:42px; border-radius:var(--radius-sm); background:var(--gold-glow); border:1px solid var(--border-accent); display:flex; align-items:center; justify-content:center; font-size:1.1rem; flex-shrink:0; }
.setup-card-num { font-family:'Space Mono',monospace; font-size:0.65rem; color:var(--gold); font-weight:700; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:2px; }
.setup-card-title { font-family:'Syne',sans-serif; font-size:0.95rem; font-weight:700; color:var(--text-primary); }
.setup-card-done { margin-left:auto; display:inline-flex; align-items:center; gap:6px; background:rgba(0,224,150,0.08); border:1px solid rgba(0,224,150,0.2); color:var(--green); font-size:0.7rem; font-weight:700; padding:4px 12px; border-radius:20px; }
.setup-card-pending { margin-left:auto; display:inline-flex; align-items:center; gap:6px; background:rgba(250,196,0,0.07); border:1px solid rgba(250,196,0,0.2); color:var(--gold); font-size:0.7rem; font-weight:700; padding:4px 12px; border-radius:20px; }
.strategy-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-top:1rem; }
.strategy-cell { background:var(--bg-elevated); border:1px solid var(--border); border-radius:var(--radius-sm); padding:0.8rem 1rem; }
.strategy-cell .sc-label { font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.08em; margin-bottom:4px; }
.strategy-cell .sc-value { font-family:'Space Mono',monospace; font-size:0.9rem; color:var(--text-primary); }
.strategy-cell.gold-accent { border-color:var(--border-accent); }
.strategy-cell.gold-accent .sc-value { color:var(--gold); }
.stTextInput input,.stNumberInput input { background:var(--bg-elevated) !important; border:1px solid var(--border) !important; color:var(--text-primary) !important; border-radius:var(--radius-sm) !important; font-family:'DM Sans',sans-serif !important; font-size:0.88rem !important; }
.stTextInput input:focus,.stNumberInput input:focus { border-color:var(--gold-dim) !important; box-shadow:0 0 0 3px var(--gold-glow) !important; }
.stTextInput label,.stNumberInput label,.stSelectbox label,.stSlider label { color:var(--text-secondary) !important; font-size:0.78rem !important; font-weight:500 !important; font-family:'DM Sans',sans-serif !important; }
div[data-baseweb="select"] > div { background:var(--bg-elevated) !important; border-color:var(--border) !important; }
.stButton > button { border-radius:var(--radius-md) !important; font-family:'Syne',sans-serif !important; font-weight:700 !important; letter-spacing:0.04em !important; font-size:0.85rem !important; transition:all 0.2s !important; border:none !important; }
.stButton > button[kind="primary"] { background:linear-gradient(135deg,var(--gold) 0%,#e6b000 100%) !important; color:#000 !important; box-shadow:0 4px 20px rgba(250,196,0,0.3) !important; }
.stButton > button[kind="secondary"] { background:var(--bg-elevated) !important; color:var(--text-primary) !important; border:1px solid var(--border) !important; }
.stDataFrame { border-radius:var(--radius-md) !important; overflow:hidden; }
.stDataFrame table { background:var(--bg-card) !important; border:none !important; }
.stDataFrame thead tr th { background:var(--bg-elevated) !important; color:var(--text-muted) !important; font-size:0.7rem !important; font-weight:700 !important; letter-spacing:0.1em !important; text-transform:uppercase !important; border:none !important; padding:10px 14px !important; }
.stDataFrame tbody tr td { background:var(--bg-card) !important; color:var(--text-primary) !important; font-size:0.82rem !important; border:none !important; border-bottom:1px solid var(--border) !important; padding:8px 14px !important; font-family:'Space Mono',monospace !important; }
.stDataFrame tbody tr:hover td { background:var(--bg-elevated) !important; }
[data-testid="metric-container"] { background:var(--bg-card) !important; border:1px solid var(--border) !important; border-radius:var(--radius-md) !important; padding:1rem 1.2rem !important; }
[data-testid="metric-container"] label { font-size:0.68rem !important; font-weight:700 !important; letter-spacing:0.12em !important; text-transform:uppercase !important; color:var(--text-muted) !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { font-family:'Space Mono',monospace !important; font-size:1.4rem !important; color:var(--text-primary) !important; }
.trail-box { background:rgba(0,224,150,0.07); border-left:3px solid var(--green); border-radius:0 var(--radius-sm) var(--radius-sm) 0; padding:0.5rem 1rem; margin:0.3rem 0; font-size:0.8rem; color:var(--green); font-family:'Space Mono',monospace; }
.scan-banner { background:rgba(0,224,150,0.06); border:1px solid rgba(0,224,150,0.15); border-radius:var(--radius-md); padding:0.9rem 1.4rem; margin:1rem 0; font-size:0.82rem; color:var(--green); display:flex; align-items:center; gap:10px; }
.stProgress > div > div { border-radius:4px !important; }
.stProgress > div > div > div { background:linear-gradient(90deg,var(--gold),var(--teal)) !important; }
.stCaption,small { color:var(--text-muted) !important; font-size:0.75rem !important; }
hr { border-color:var(--border) !important; margin:1.2rem 0 !important; }
.app-footer { margin-top:4rem; padding:1.5rem 0 1rem; border-top:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; font-size:0.72rem; color:var(--text-muted); }
.footer-brand { font-family:'Syne',sans-serif; font-weight:700; color:var(--text-secondary); letter-spacing:0.06em; }
.nav-radio div[data-baseweb="radio-group"] { flex-direction:row !important; gap:2px !important; align-items:center !important; }
.nav-radio div[data-baseweb="radio-group"] > label { padding:7px 20px !important; border-radius:8px !important; font-family:'Syne',sans-serif !important; font-size:0.8rem !important; font-weight:700 !important; letter-spacing:0.03em !important; color:var(--text-muted) !important; border:1px solid transparent !important; transition:all 0.15s !important; cursor:pointer !important; margin:0 !important; user-select:none !important; }
.nav-radio div[data-baseweb="radio-group"] > label:hover { color:var(--text-secondary) !important; background:rgba(255,255,255,0.04) !important; }
.nav-radio div[data-baseweb="radio-group"] > label > div:first-child { display:none !important; }
.nav-radio div[data-baseweb="radio-group"] > label[aria-checked="true"] { background:var(--bg-elevated) !important; color:var(--gold) !important; border-color:rgba(250,196,0,0.3) !important; }
.nav-radio div[data-baseweb="radio-group"] { background:rgba(255,255,255,0.025) !important; border:1px solid rgba(255,255,255,0.06) !important; border-radius:12px !important; padding:4px !important; }
.nav-signout button { background:rgba(255,77,106,0.08) !important; border:1px solid rgba(255,77,106,0.2) !important; color:#FF4D6A !important; font-size:0.75rem !important; padding:6px 14px !important; border-radius:var(--radius-md) !important; }
.qty-info { background:rgba(0,217,196,0.07); border-left:3px solid #00D9C4; border-radius:0 8px 8px 0; padding:0.5rem 1rem; margin:0.3rem 0; font-size:0.78rem; color:#00D9C4; font-family:'Space Mono',monospace; }
/* Locked config banner */
.locked-config-banner {
    background: linear-gradient(135deg, rgba(0,224,150,0.08), rgba(0,217,196,0.05));
    border: 1px solid rgba(0,224,150,0.25);
    border-radius: 14px;
    padding: 1.1rem 1.6rem;
    margin: 1rem 0 1.5rem;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}
.locked-config-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0,224,150,0.1);
    border: 1px solid rgba(0,224,150,0.2);
    border-radius: 20px;
    padding: 3px 12px;
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: #00E096;
    font-weight: 700;
}
.locked-config-pill span.lc-label {
    color: #4A5568;
    font-weight: 400;
    font-size: 0.68rem;
    margin-right: 2px;
}
.config-dirty-banner {
    background: rgba(250,196,0,0.07);
    border: 1px solid rgba(250,196,0,0.25);
    border-radius: 10px;
    padding: 0.75rem 1.2rem;
    margin: 0.5rem 0 1rem;
    font-size: 0.8rem;
    color: #FAC400;
    display: flex;
    align-items: center;
    gap: 10px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# ACCESS CONTROL
# ============================================================
APPROVED_USERS = {
    "billionaires": "BG@2026",
    "admin":        "Admin@2026",
    "member1":      "Member@001",
    "member2":      "Member@002",
}
USER_ALICEBLUE_CREDS = {
    "billionaires": {"app_code": "l8V6fBNFH4", "user_id": "AB103628", "api_secret": "Le7p6fYo5viCpF7dAhwcZI0zs1PVsg1ICQHezdns5ewXYCmnAVrfU4WquDnecgSeuLsvAnzoSEYMvYv5LggvUbguLVhN3rfqilQi"},
    "admin":        {"app_code": "", "user_id": "", "api_secret": ""},
    "member1":      {"app_code": "", "user_id": "", "api_secret": ""},
    "member2":      {"app_code": "", "user_id": "", "api_secret": ""},
}

for k, v in [('app_authenticated', False), ('app_username', ''), ('login_attempts', 0)]:
    if k not in st.session_state:
        st.session_state[k] = v

def show_login_page():
    st.markdown("""
    <div style="text-align:center;padding:3.5rem 0 2rem;">
        <div style="width:68px;height:68px;border-radius:20px;background:linear-gradient(135deg,#FAC400,#c49a00);
            margin:0 auto 1.2rem;display:flex;align-items:center;justify-content:center;font-size:2rem;
            box-shadow:0 10px 40px rgba(250,196,0,0.4);">💼</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;color:#F0F4FF;margin-bottom:6px;">BILLIONAIRES GROUP</div>
        <div style="font-size:0.78rem;color:#4A5568;letter-spacing:0.08em;">Be with us &nbsp;·&nbsp; Grow with us</div>
    </div>""", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.3, 1])
    with col:
        st.markdown('<div style="background:#0f1520;border:1px solid rgba(255,255,255,0.06);border-radius:20px;padding:2rem 2rem 1.5rem;box-shadow:0 24px 64px rgba(0,0,0,0.5);">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.65rem;color:#4A5568;text-align:center;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:1.4rem;">🔐 &nbsp; Member Access Portal</div>', unsafe_allow_html=True)
        username = st.text_input("Username", key="login_user", placeholder="Enter username")
        password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡  SIGN IN", use_container_width=True, type="primary"):
            if st.session_state.login_attempts >= 5:
                st.error("❌ Too many attempts. Refresh the page.")
            elif username in APPROVED_USERS and APPROVED_USERS[username] == password:
                st.session_state.app_authenticated = True
                st.session_state.app_username      = username
                st.session_state.login_attempts    = 0
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.error(f"❌ Invalid credentials — {5 - st.session_state.login_attempts} attempts remaining")
        st.markdown('<div style="margin-top:1.2rem;text-align:center;font-size:0.72rem;color:#4A5568;">🔒 &nbsp; Access restricted to approved members only</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.app_authenticated:
    show_login_page()
    st.stop()

# ============================================================
# SESSION STATE
# ============================================================

# ── DEFAULT ACTIVE CONFIG (the locked config Bot always uses) ──
_DEFAULT_ACTIVE_CONFIG = {
    'risk_amt':    10000,
    't1_mult':     1.0,
    't2_mult':     2.0,
    'final_mult':  3.0,
    'timeframe':   '15min',
    'scan_interval': 10,
    'instrument_type': 'Equity',
}

_defaults = {
    'active_trades': [], 'completed_trades': [], 'signals': [],
    'signal_count_per_stock': {},
    'auto_refresh': False, 'refresh_counter': 0,
    'filtered_stocks': [], 'filtered_df': pd.DataFrame(),
    'aliceblue_connected': False, 'session_id': None,
    'instrument_type': "Equity", 'bot_start_datetime': None, 'data_fetched': False,
    'active_page': 'home', 'nav_radio_widget': "🏠  Home",
    't1_mult': 1.0, 't2_mult': 2.0, 'final_mult': 3.0,
    'risk_amt': 10000,
    'timeframe': '15min',
    'min_change': 2.0, 'max_change': 5.0, 'min_ltp': 500, 'max_ltp': 3000,
    'scan_interval': 10,
    'traded_symbols_today': set(),
    'active_config': _DEFAULT_ACTIVE_CONFIG.copy(),
    'config_applied': False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

_today_str = datetime.now().strftime('%Y-%m-%d')
if st.session_state.get('_last_reset_date') != _today_str:
    st.session_state.signal_count_per_stock = {}
    st.session_state.traded_symbols_today   = set()
    st.session_state._last_reset_date       = _today_str

# ============================================================
# CONSTANTS
# ============================================================
BASE_URL = "https://ant.aliceblueonline.com/open-api/od/v1"
def _hdr(sid): return {"Content-Type": "application/json", "Authorization": f"Bearer {sid}"}
def r2(v):     return round(float(v), 2)

# ============================================================
# QTY CALCULATION
# ============================================================
def calculate_qty(risk_amount, entry, sl):
    risk_per_share = abs(r2(entry) - r2(sl))
    if risk_per_share <= 0:
        return 1, 0.0
    qty = max(1, int(risk_amount / risk_per_share))
    return qty, r2(risk_per_share)

# ============================================================
# HEADER & NAV
# ============================================================
def render_header():
    uname   = st.session_state.app_username.upper()
    bot_run = st.session_state.auto_refresh
    cur     = st.session_state.active_page
    PAGE_LABELS = ["🏠  Home", "⚙️  Setup", "🤖  Bot", "📋  History"]
    PAGE_KEYS   = ["home", "setup", "bot", "history"]
    current_idx = PAGE_KEYS.index(cur) if cur in PAGE_KEYS else 0
    dot_color = "#00E096" if bot_run else "#4A5568"
    dot_anim  = "animation:pulse-green 2s infinite;" if bot_run else ""
    badge_bg  = "rgba(0,224,150,0.08)" if bot_run else "rgba(74,85,104,0.15)"
    badge_bc  = "rgba(0,224,150,0.25)" if bot_run else "rgba(74,85,104,0.3)"
    badge_col = "#00E096" if bot_run else "#4A5568"
    badge_txt = "BOT RUNNING" if bot_run else "BOT STANDBY"
    st.markdown(f"""
    <div style="background:#0b0f1a;border-bottom:1px solid rgba(255,255,255,0.06);
        display:flex;align-items:center;justify-content:space-between;
        padding:0 2.5rem;height:64px;position:sticky;top:0;z-index:1000;">
        <div style="display:flex;align-items:center;gap:12px;flex-shrink:0;">
            <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#FAC400,#c49a00);
                display:flex;align-items:center;justify-content:center;font-size:1rem;
                box-shadow:0 4px 16px rgba(250,196,0,0.3);">⚡</div>
            <div>
                <div style="font-family:'Syne',sans-serif;font-size:0.95rem;font-weight:800;color:#F0F4FF;letter-spacing:0.03em;line-height:1.1;">BILLIONAIRES GROUP</div>
                <div style="font-size:0.6rem;color:#4A5568;letter-spacing:0.1em;text-transform:uppercase;">Algorithmic Trading</div>
            </div>
        </div>
        <div style="display:inline-flex;align-items:center;gap:7px;padding:5px 14px;border-radius:20px;font-size:0.7rem;font-weight:700;letter-spacing:0.06em;background:{badge_bg};border:1px solid {badge_bc};color:{badge_col};">
            <span style="width:7px;height:7px;border-radius:50%;background:{dot_color};display:inline-block;{dot_anim}"></span>
            {badge_txt} &nbsp;|&nbsp; {uname}
        </div>
    </div>""", unsafe_allow_html=True)
    nav_col, logout_col = st.columns([8, 1])
    with nav_col:
        st.markdown('<div class="nav-radio">', unsafe_allow_html=True)
        selected = st.radio("Navigation", PAGE_LABELS, index=current_idx,
                            horizontal=True, label_visibility="collapsed", key="nav_radio_widget")
        st.markdown('</div>', unsafe_allow_html=True)
    with logout_col:
        st.markdown('<div class="nav-signout">', unsafe_allow_html=True)
        if st.button("⎋ Sign Out", key="top_logout_btn"):
            st.session_state.app_authenticated = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    new_page = PAGE_KEYS[PAGE_LABELS.index(selected)]
    if new_page != st.session_state.active_page:
        st.session_state.active_page = new_page
        st.rerun()

render_header()

# ============================================================
# ALICEBLUE API
# ============================================================
def get_session_from_authcode(username, auth_code, api_secret):
    try:
        chk  = hashlib.sha256(f"{username}{auth_code}{api_secret}".encode()).hexdigest()
        resp = requests.post(f"{BASE_URL}/vendor/getUserDetails",
                             headers={"Content-Type": "application/json"},
                             json={"checkSum": chk}, timeout=15)
        data = resp.json()
        sid  = data.get("userSession", "")
        if not sid:
            st.error(f"❌ Auth failed: {data.get('emsg', data)}")
            return None, None
        st.success("✅ AliceBlue session obtained!")
        alice = None
        if ALICE_AVAILABLE:
            try:
                alice = AliceBlue(username=username, session_id=sid,
                                  master_contracts_to_download=['NSE', 'NFO'])
            except Exception as e:
                st.warning(f"⚠️ SDK init failed (REST still works): {e}")
        return alice, sid
    except Exception as e:
        st.error(f"❌ Connection error: {e}")
        return None, None

@st.cache_data(ttl=3600)
def load_nse_contracts():
    try:
        r = requests.get("https://v2api.aliceblueonline.com/restpy/static/contract_master/NSE.csv", timeout=15)
        if r.status_code != 200: return {}
        df, out = pd.read_csv(StringIO(r.text)), {}
        for _, row in df.iterrows():
            sym = str(row.get('Symbol','')).strip().upper()
            tok = str(row.get('Token','')).strip()
            grp = str(row.get('Group Name','')).strip().upper()
            if grp == 'EQ' and sym and tok: out[sym] = tok
        return out
    except: return {}

@st.cache_data(ttl=3600)
def load_nfo_contracts():
    try:
        r = requests.get("https://v2api.aliceblueonline.com/restpy/static/contract_master/NFO.csv", timeout=15)
        if r.status_code != 200: return {}
        df, out = pd.read_csv(StringIO(r.text)), {}
        for _, row in df.iterrows():
            sym = str(row.get('Trading Symbol','')).strip().upper()
            tok = str(row.get('Token','')).strip()
            if sym and tok: out[sym] = tok
        return out
    except: return {}

def get_token(exchange, symbol):
    sym = symbol.upper().strip()
    if exchange == "NSE":
        c = load_nse_contracts()
        return c.get(sym) or c.get(sym.replace("-EQ","")) or None
    elif exchange == "NFO":
        return load_nfo_contracts().get(sym)
    return None

# ============================================================
# ORDER PLACEMENT
# ============================================================
def place_entry_order(signal, sid):
    if not sid:
        st.error("❌ No session.")
        return False

    direction = "BUY" if signal['SIGNAL'] == 'BUY' else "SELL"

    if st.session_state.active_config['instrument_type'] == "Options":
        try:
            opt = json.loads(signal['SYMBOL'])
            symbol   = f"{opt['base']}{opt['expiry']}{int(opt['strike'])}{opt['type']}"
            exchange = "NFO"
        except Exception as e:
            st.error(f"❌ Option parse error: {e}")
            return False
    else:
        symbol   = signal['SYMBOL']
        exchange = "NSE"

    token = get_token(exchange, symbol)
    if not token:
        st.error(f"❌ Token not found for {exchange}:{symbol}")
        return False

    qty = int(signal['QUANTITY'])

    logging.info(
        f"[ORDER] {symbol} {direction} | "
        f"Entry={signal['ENTRY']} SL={signal['STOPLOSS']} "
        f"Risk/Share={signal['RISK_PER_SHARE']} RiskAmt={signal['RISK_AMOUNT']} "
        f"Qty={qty}"
    )

    payload = [{
        "exchange": exchange,
        "instrumentId": token,
        "transactionType": direction,
        "quantity": str(qty),
        "product": "INTRADAY",
        "orderComplexity": "REGULAR",
        "orderType": "LIMIT",
        "validity": "DAY",
        "price": str(r2(signal['ENTRY'])),
        "slTriggerPrice": "",
        "slLegPrice": "",
        "targetLegPrice": "",
        "trailingSlAmount": "",
        "disclosedQuantity": "",
        "marketProtectionPercent": "",
        "apiOrderSource": "",
        "orderTag": "BG_AlgoBot"
    }]

    try:
        raw  = requests.post(f"{BASE_URL}/orders/placeorder", headers=_hdr(sid), json=payload, timeout=15)
        resp = raw.json()
        logging.info(f"[ORDER RESP] {symbol} {direction}: {resp}")

        if resp.get("status") == "Ok":
            result = resp.get("result", [{}])
            if not result:
                st.warning(f"⚠️ Empty result for {symbol}")
                return False
            r0     = result[0]
            oid    = r0.get("brokerOrderId", "")
            reason = r0.get("rejectionReason", "")
            if r0.get("orderStatus") == "REJECTED" or reason:
                st.error(f"❌ REJECTED {symbol}: {reason or 'No reason'}")
                return False
            signal['broker_order_id'] = oid
            signal['sl_order_id']     = None
            st.success(
                f"📈 Entry | {symbol} {direction} × {qty} @ ₹{signal['ENTRY']:.2f} "
                f"| Risk/Share: ₹{signal['RISK_PER_SHARE']:.2f} "
                f"| ID:{oid or 'Pending'}"
            )
            return True
        else:
            st.error(f"❌ Order failed {symbol}: {resp.get('message', resp)}")
            return False
    except Exception as e:
        st.error(f"❌ Network error: {e}")
        return False

def modify_sl_order(signal, new_sl_price, sid, label="SL"):
    if not sid: return False
    new_sl = r2(new_sl_price)
    qty    = int(signal['QUANTITY'])

    if signal.get('sl_order_id'):
        payload = {
            "brokerOrderId": signal['sl_order_id'],
            "quantity": str(qty),
            "orderType": "SL",
            "slTriggerPrice": str(new_sl),
            "price": str(new_sl),
            "validity": "DAY",
            "disclosedQuantity": "0"
        }
        try:
            resp = requests.put(f"{BASE_URL}/orders/modifyorder", headers=_hdr(sid), json=payload, timeout=15).json()
            if resp.get("status") == "Ok":
                signal['current_sl'] = new_sl
                st.markdown(f'<div class="trail-box">🔄 SL → ₹{new_sl:.2f} ({label}) — {signal["SYMBOL"]}</div>', unsafe_allow_html=True)
                return True
            return False
        except:
            return False
    else:
        direction = "SELL" if signal['SIGNAL'] == 'BUY' else "BUY"
        if st.session_state.active_config['instrument_type'] == "Options":
            try:
                opt      = json.loads(signal['SYMBOL'])
                sym_key  = f"{opt['base']}{opt['expiry']}{int(opt['strike'])}{opt['type']}"
                exch     = "NFO"
            except:
                return False
        else:
            sym_key = signal['SYMBOL']
            exch    = "NSE"

        token = get_token(exch, sym_key)
        if not token: return False

        payload = [{
            "exchange": exch,
            "instrumentId": token,
            "transactionType": direction,
            "quantity": str(qty),
            "product": "INTRADAY",
            "orderComplexity": "REGULAR",
            "orderType": "SL",
            "validity": "DAY",
            "slTriggerPrice": str(new_sl),
            "price": str(new_sl),
            "slLegPrice": "",
            "targetLegPrice": "",
            "trailingSlAmount": "",
            "disclosedQuantity": "",
            "marketProtectionPercent": "",
            "apiOrderSource": "",
            "orderTag": "BG_SL"
        }]
        try:
            resp = requests.post(f"{BASE_URL}/orders/placeorder", headers=_hdr(sid), json=payload, timeout=15).json()
            logging.info(f"[SL ORDER] {signal['SYMBOL']} response: {resp}")
            if resp.get("status") == "Ok":
                result = resp.get("result", [{}])
                r0     = result[0] if result else {}
                reason = r0.get("rejectionReason", "")
                if reason:
                    st.warning(f"⚠️ SL rejected {signal['SYMBOL']}: {reason}")
                    return False
                signal['sl_order_id'] = r0.get("brokerOrderId", "")
                signal['current_sl']  = new_sl
                st.markdown(f'<div class="trail-box">🛡️ SL @ ₹{new_sl:.2f} ({label}) | Qty:{qty} — {signal["SYMBOL"]}</div>', unsafe_allow_html=True)
                return True
            return False
        except:
            return False

def close_position_market(signal, sid, reason="Final Target"):
    if not sid: return False
    direction = "SELL" if signal['SIGNAL'] == 'BUY' else "BUY"
    qty       = int(signal['QUANTITY'])

    if st.session_state.active_config['instrument_type'] == "Options":
        try:
            opt      = json.loads(signal['SYMBOL'])
            sym_key  = f"{opt['base']}{opt['expiry']}{int(opt['strike'])}{opt['type']}"
            exch     = "NFO"
        except:
            return False
    else:
        sym_key = signal['SYMBOL']
        exch    = "NSE"

    token = get_token(exch, sym_key)
    if not token: return False

    payload = [{
        "exchange": exch,
        "instrumentId": token,
        "transactionType": direction,
        "quantity": str(qty),
        "product": "INTRADAY",
        "orderComplexity": "REGULAR",
        "orderType": "MARKET",
        "validity": "DAY",
        "price": "0",
        "slTriggerPrice": "",
        "slLegPrice": "",
        "targetLegPrice": "",
        "trailingSlAmount": "",
        "disclosedQuantity": "",
        "marketProtectionPercent": "",
        "apiOrderSource": "",
        "orderTag": "BG_Close"
    }]
    try:
        resp = requests.post(f"{BASE_URL}/orders/placeorder", headers=_hdr(sid), json=payload, timeout=15).json()
        if resp.get("status") == "Ok":
            st.success(f"🏁 CLOSED {signal['SYMBOL']} at Market | {reason} | Qty:{qty}")
            if signal.get('sl_order_id'):
                try:
                    requests.delete(f"{BASE_URL}/orders/{signal['sl_order_id']}", headers=_hdr(sid), timeout=10)
                except:
                    pass
            return True
        return False
    except:
        return False

def get_funds(sid):
    try:
        r = requests.get(f"{BASE_URL}/funds", headers=_hdr(sid), timeout=15)
        d = r.json()
        return d.get("result", {}) if d.get("status") == "Ok" else {}
    except:
        return {}

# ============================================================
# TV DATA
# ============================================================
@st.cache_data(ttl=300)
def fetch_stocks_data_from_tv(symbols_list):
    data_out = []
    tv = TvDatafeed()
    with st.spinner(f"Fetching {len(symbols_list)} stocks..."):
        for sym in symbols_list:
            try:
                d = tv.get_hist(symbol=sym, exchange="NSE", interval=Interval.in_daily, n_bars=2)
                if d is not None and len(d) >= 2:
                    cp   = r2(d['close'].iloc[-1])
                    prev = r2(d['close'].iloc[-2])
                    pct  = r2(((cp - prev) / prev) * 100)
                    data_out.append({
                        'Symbol': sym, 'LTP': cp, 'Change %': pct,
                        'Volume': int(d['volume'].iloc[-1]) if 'volume' in d else 0,
                        'High': r2(d['high'].iloc[-1]), 'Low': r2(d['low'].iloc[-1])
                    })
                time.sleep(0.3)
            except:
                continue
    return pd.DataFrame(data_out)

def fetch_data(symbol, interval, n_bars=100):
    try:
        tv  = TvDatafeed()
        inv = {
            '1min':  Interval.in_1_minute,
            '5min':  Interval.in_5_minute,
            '15min': Interval.in_15_minute,
            'daily': Interval.in_daily
        }
        return tv.get_hist(symbol=symbol, exchange="NSE",
                           interval=inv.get(interval, Interval.in_15_minute), n_bars=n_bars)
    except:
        return None

# ============================================================
# STRATEGY  *** BUG FIX: bot_start_dt filtering ***
# ============================================================
class CandleBreakoutStrategy:
    def __init__(self, timeframe='15min', risk_amount=10000,
                 t1_mult=1.0, t2_mult=2.0, final_mult=3.0):
        self.timeframe   = timeframe
        self.risk_amount = risk_amount
        self.t1_mult     = t1_mult
        self.t2_mult     = t2_mult
        self.final_mult  = final_mult

    def analyze(self, df, symbol, date_tracker=None, bot_start_dt=None):
        if df is None or len(df) < 2: return None
        df.index = pd.to_datetime(df.index)
        today    = datetime.now().date()
        today_df = df[df.index.date == today]
        if len(today_df) < 1: return None

        # ── Normalise bot_start_dt to naive datetime ──────────
        if bot_start_dt and hasattr(bot_start_dt, 'tzinfo') and bot_start_dt.tzinfo:
            bot_start_dt = bot_start_dt.replace(tzinfo=None)
        if bot_start_dt is None:
            bot_start_dt = datetime.now()

        # ── Normalise today_df index to naive ─────────────────
        if today_df.index.tzinfo is not None:
            today_df = today_df.copy()
            today_df.index = today_df.index.tz_localize(None)

        # ══════════════════════════════════════════════════════
        # THE FIX:
        #
        # Split today's candles into two groups:
        #
        #   pre_bot  → candles BEFORE bot_start_dt
        #              used ONLY to pick the reference candle
        #
        #   post_bot → candles AT or AFTER bot_start_dt
        #              ONLY these can trigger a breakout signal
        #
        # Reference candle = the LAST candle in pre_bot
        # (i.e. the most-recently-closed candle when the bot started)
        #
        # Example:
        #   Bot starts at 10:00 AM
        #   pre_bot  → 9:15, 9:30, 9:45  ← last one (9:45) is the ref
        #   post_bot → 10:00, 10:15, ...  ← breakouts checked here only
        #
        # OLD (broken) logic always used iloc[0] (9:15 candle) as ref
        # and iterated from index 1 — so a 9:45 breakout still fired
        # even when the bot started at 10:00.
        # ══════════════════════════════════════════════════════
        # Option B: 9:15 candle (first candle of the day) is ALWAYS the reference.
        # Only candles at or after bot_start_dt can trigger a breakout signal.
        if len(today_df) < 1:
            return None
        ref      = today_df.iloc[0]                          # always 9:15 candle
        post_bot = today_df[today_df.index >= bot_start_dt]  # only post-bot candles fire

        if post_bot.empty:
            return None

        high_ref = r2(ref['high'])
        low_ref  = r2(ref['low'])
        rng      = r2(high_ref - low_ref)

        date_str = today.strftime('%Y-%m-%d')
        key      = f"{symbol}_{date_str}"

        if symbol in st.session_state.traded_symbols_today: return None
        if date_tracker and date_tracker.get(key, False):   return None
        if rng <= 0: return None

        signals = []
        for i in range(len(post_bot)):
            cur      = post_bot.iloc[i]
            bt       = post_bot.index[i]   # already naive

            cur_high = r2(cur['high'])
            cur_low  = r2(cur['low'])

            if cur_high > high_ref:
                direction = 'BUY'
                entry     = high_ref
                sl        = low_ref
                qty, risk_per_share = calculate_qty(self.risk_amount, entry, sl)
                t1    = r2(entry + rng * self.t1_mult)
                t2    = r2(entry + rng * self.t2_mult)
                final = r2(entry + rng * self.final_mult)

            elif cur_low < low_ref:
                direction = 'SELL'
                entry     = low_ref
                sl        = high_ref
                qty, risk_per_share = calculate_qty(self.risk_amount, entry, sl)
                t1    = r2(entry - rng * self.t1_mult)
                t2    = r2(entry - rng * self.t2_mult)
                final = r2(entry - rng * self.final_mult)

            else:
                continue

            max_loss = r2(risk_per_share * qty)

            sig = {
                'DATE':           date_str,
                'ENTRY_TIME':     bt.strftime('%H:%M:%S'),
                'SYMBOL':         symbol,
                'SIGNAL':         direction,
                'ENTRY':          entry,
                'STOPLOSS':       sl,
                'INITIAL_SL':     sl,
                'current_sl':     sl,
                'QUANTITY':       qty,
                'CANDLE_RANGE':   rng,
                'RISK_PER_SHARE': risk_per_share,
                'RISK_AMOUNT':    self.risk_amount,
                'MAX_LOSS':       max_loss,
                'T1': t1, 'T2': t2, 'FINAL_TARGET': final,
                'T1_HIT': False, 'T2_HIT': False, 'FINAL_HIT': False, 'STOPLOSS_HIT': False,
                'SL_TRAIL_LOG':   [f"Initial SL: ₹{sl:.2f}"],
                'broker_order_id': None, 'sl_order_id': None,
                'VOLUME': int(cur['volume']) if 'volume' in cur else 0,
            }
            if date_tracker:
                date_tracker[key] = True
            signals.append(sig)
            break   # one signal per symbol per day

        return signals if signals else None

# ============================================================
# TRADE MONITOR
# ============================================================
def monitor_active_trades(cfg):
    t1_mult    = cfg['t1_mult']
    t2_mult    = cfg['t2_mult']
    final_mult = cfg['final_mult']
    to_close = []
    sid      = st.session_state.get('session_id')

    for trade in st.session_state.active_trades:
        sym = trade['SYMBOL']
        try:
            data = fetch_data(sym, '1min', n_bars=1)
            if data is None or data.empty:
                data = fetch_data(sym, '5min', n_bars=1)
            if data is None or data.empty:
                continue

            price  = r2(data['close'].iloc[-1])
            is_buy = trade['SIGNAL'] == 'BUY'

            final_hit = (price >= trade['FINAL_TARGET']) if is_buy else (price <= trade['FINAL_TARGET'])
            if final_hit and not trade['FINAL_HIT']:
                trade['FINAL_HIT'] = True
                trade['PNL'] = r2(
                    (trade['FINAL_TARGET'] - trade['ENTRY']) * trade['QUANTITY'] if is_buy
                    else (trade['ENTRY'] - trade['FINAL_TARGET']) * trade['QUANTITY']
                )
                trade['CLOSE_REASON'] = "Final Target"
                if sid:
                    close_position_market(trade, sid, reason="Final Target 🏁")
                to_close.append(trade)
                continue

            t2_hit = (price >= trade['T2']) if is_buy else (price <= trade['T2'])
            if t2_hit and not trade['T2_HIT']:
                trade['T2_HIT'] = True
                new_sl = trade['T1']
                if r2(new_sl) != r2(trade.get('current_sl', trade['STOPLOSS'])):
                    trade['STOPLOSS']    = new_sl
                    trade['current_sl']  = new_sl
                    trade['SL_TRAIL_LOG'].append(f"T2 hit @ ₹{price:.2f} → SL to T1 ₹{new_sl:.2f}")
                    if sid:
                        modify_sl_order(trade, new_sl, sid, label="Trailed to T1")

            t1_hit = (price >= trade['T1']) if is_buy else (price <= trade['T1'])
            if t1_hit and not trade['T1_HIT']:
                trade['T1_HIT'] = True
                new_sl = trade['ENTRY']
                if r2(new_sl) != r2(trade.get('current_sl', trade['STOPLOSS'])):
                    trade['STOPLOSS']    = new_sl
                    trade['current_sl']  = new_sl
                    trade['SL_TRAIL_LOG'].append(f"T1 hit @ ₹{price:.2f} → SL to Breakeven ₹{new_sl:.2f}")
                    if sid:
                        modify_sl_order(trade, new_sl, sid, label="Breakeven")

            sl_hit = (price <= trade['current_sl']) if is_buy else (price >= trade['current_sl'])
            if sl_hit and not trade['STOPLOSS_HIT']:
                trade['STOPLOSS_HIT'] = True
                trade['PNL'] = r2(
                    (trade['current_sl'] - trade['ENTRY']) * trade['QUANTITY'] if is_buy
                    else (trade['ENTRY'] - trade['current_sl']) * trade['QUANTITY']
                )
                trade['CLOSE_REASON'] = f"SL Hit @ ₹{trade['current_sl']:.2f}"
                trade['SL_TRAIL_LOG'].append(f"❌ SL triggered @ ₹{price:.2f}")
                to_close.append(trade)

        except Exception as e:
            logging.warning(f"Monitor error {sym}: {e}")

    for t in to_close:
        if t in st.session_state.active_trades:
            st.session_state.active_trades.remove(t)
            st.session_state.completed_trades.append(t)

# ============================================================
# SIGNAL SCANNER
# ============================================================
def check_for_new_signals(symbols, cfg):
    risk_amount = cfg['risk_amt']
    timeframe   = cfg['timeframe']
    t1_mult     = cfg['t1_mult']
    t2_mult     = cfg['t2_mult']
    final_mult  = cfg['final_mult']

    strategy  = CandleBreakoutStrategy(timeframe, risk_amount, t1_mult, t2_mult, final_mult)
    bot_start = st.session_state.get('bot_start_datetime') or datetime.now()
    sid       = st.session_state.get('session_id')
    all_new   = []

    for sym in symbols:
        if sym in st.session_state.traded_symbols_today:
            continue
        data = fetch_data(sym, timeframe)
        if data is not None:
            sigs = strategy.analyze(
                data, sym,
                st.session_state.signal_count_per_stock,
                bot_start_dt=bot_start
            )
            if sigs:
                for sig in sigs:
                    st.session_state.traded_symbols_today.add(sym)
                    st.session_state.active_trades.append(sig)
                    if sid:
                        placed = place_entry_order(sig, sid)
                        if placed:
                            modify_sl_order(sig, sig['INITIAL_SL'], sid, label="Initial SL")
                all_new.extend(sigs)
        time.sleep(0.3)
    return all_new

# ============================================================
# DISPLAY HELPERS
# ============================================================
def display_active_trades(trades):
    if not trades:
        st.markdown(
            '<div style="text-align:center;padding:3rem;background:#0f1520;border:1px solid rgba(255,255,255,0.06);'
            'border-radius:14px;color:#4A5568;font-size:0.85rem;">⚡ No active trades running at the moment</div>',
            unsafe_allow_html=True
        )
        return
    rows = []
    for t in trades:
        status = []
        if t.get('T1_HIT'):  status.append("✅ T1")
        if t.get('T2_HIT'):  status.append("✅ T2")
        if not status:        status.append("🟡 Active")
        rows.append({
            'Symbol':      t['SYMBOL'],
            'Dir':         t['SIGNAL'],
            'Entry':       f"₹{t['ENTRY']:.2f}",
            'SL(Initial)': f"₹{t['INITIAL_SL']:.2f}",
            'SL(Current)': f"₹{t.get('current_sl', t['STOPLOSS']):.2f}",
            'T1':          f"₹{t['T1']:.2f}",
            'T2':          f"₹{t['T2']:.2f}",
            'Final':       f"₹{t['FINAL_TARGET']:.2f}",
            'Qty':         t['QUANTITY'],
            'Risk/Share':  f"₹{t.get('RISK_PER_SHARE', t['CANDLE_RANGE']):.2f}",
            'Risk Used':   f"₹{t.get('RISK_AMOUNT', '?'):,}",
            'Max Loss':    f"₹{t.get('MAX_LOSS', 0):,.0f}",
            'Status':      " | ".join(status),
        })
    df = pd.DataFrame(rows)
    def cs(val):
        if val == 'BUY':  return 'background-color:#00301a;color:#00E096;font-weight:700'
        if val == 'SELL': return 'background-color:#300010;color:#FF4D6A;font-weight:700'
        return ''
    st.dataframe(df.style.map(cs, subset=['Dir']), use_container_width=True)

def display_signals_table(signals):
    if not signals: return
    rows = []
    for t in signals:
        rps = t.get('RISK_PER_SHARE', t['CANDLE_RANGE'])
        ra  = t.get('RISK_AMOUNT', 0)
        qty = t['QUANTITY']
        rows.append({
            'Time':        t.get('ENTRY_TIME', ''),
            'Symbol':      t['SYMBOL'],
            'Dir':         t['SIGNAL'],
            'Entry':       f"₹{t['ENTRY']:.2f}",
            'SL':          f"₹{t['INITIAL_SL']:.2f}",
            'Range':       f"₹{t['CANDLE_RANGE']:.2f}",
            'Risk/Share':  f"₹{rps:.2f}",
            'Risk ₹':      f"₹{ra:,}",
            'Qty':         qty,
            'Qty Verify':  f"✅ {int(ra/rps)}" if rps > 0 else "?",
            'Max Loss':    f"₹{r2(rps * qty):,}",
            'T1':          f"₹{t['T1']:.2f}",
            'T2':          f"₹{t['T2']:.2f}",
            'Final':       f"₹{t['FINAL_TARGET']:.2f}",
        })
    df = pd.DataFrame(rows)
    def cs(val):
        if val == 'BUY':  return 'background-color:#00301a;color:#00E096;font-weight:700'
        if val == 'SELL': return 'background-color:#300010;color:#FF4D6A;font-weight:700'
        return ''
    st.dataframe(df.style.map(cs, subset=['Dir']), use_container_width=True)

def display_completed(trades):
    if not trades: return
    rows = []
    for t in trades:
        pnl_val = t.get('PNL', 0)
        rows.append({
            'Symbol':     t['SYMBOL'],
            'Dir':        t['SIGNAL'],
            'Entry':      f"₹{t['ENTRY']:.2f}",
            'Final SL':   f"₹{t.get('current_sl', t['STOPLOSS']):.2f}",
            'Qty':        t['QUANTITY'],
            'Risk Used':  f"₹{t.get('RISK_AMOUNT', 0):,}",
            'Reason':     t.get('CLOSE_REASON', '—'),
            'P&L':        f"{'+'if pnl_val >= 0 else ''}₹{pnl_val:.2f}",
            'T1': "✅" if t.get('T1_HIT') else "❌",
            'T2': "✅" if t.get('T2_HIT') else "❌",
        })
    df  = pd.DataFrame(rows)
    pnl = sum(t.get('PNL', 0) for t in trades)
    col = "#00E096" if pnl >= 0 else "#FF4D6A"
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:16px;margin-bottom:1rem;">'
        f'<div style="font-family:\'Space Mono\',monospace;font-size:1.5rem;font-weight:700;color:{col};">'
        f'{"+"if pnl>=0 else ""}₹{pnl:,.2f}</div>'
        f'<div style="font-size:0.72rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em;">Total Session P&L</div>'
        f'</div>',
        unsafe_allow_html=True
    )
    def cs(val):
        if val == 'BUY':  return 'background-color:#00301a;color:#00E096;font-weight:700'
        if val == 'SELL': return 'background-color:#300010;color:#FF4D6A;font-weight:700'
        return ''
    st.dataframe(df.style.map(cs, subset=['Dir']), use_container_width=True)

def run_bot_cycle(symbols, cfg, pb, status):
    st.session_state.refresh_counter += 1
    monitor_active_trades(cfg)
    new = check_for_new_signals(symbols, cfg)
    interval_sec = cfg['scan_interval']
    for i in range(interval_sec, 0, -1):
        pb.progress((interval_sec - i) / interval_sec)
        status.text(
            f"⏳ Next scan in {i}s  ·  Cycle #{st.session_state.refresh_counter}  "
            f"·  Active: {len(st.session_state.active_trades)}  "
            f"·  Risk: ₹{cfg['risk_amt']:,}"
        )
        time.sleep(1)
    return new

# ============================================================
# DEFAULT SYMBOLS
# ============================================================
default_symbols = [
    "RELIANCE","TCS","HDFCBANK","INFY","HINDUNILVR","ICICIBANK","SBIN",
    "BHARTIARTL","KOTAKBANK","BAJFINANCE","ITC","AXISBANK","LT","TITAN",
    "HCLTECH","WIPRO","SUNPHARMA","ONGC","MARUTI","NTPC",
    "PAYTM","VEDL","ADANIPOWER","SHRIRAMFIN","M&MFIN","HINDZINC",
    "ADANIGREEN","SUZLON","VBL","OFSS","BSE","TATAPOWER","SAIL",
    "INDUSINDBK","ADANIENSOL","DIXON","ADANIPORTS","GROWW","ETERNAL",
    "BEL","BHEL","TATASTEEL","LTF","JIOFIN","M&M","JSWENERGY","TRENT",
    "MCX","HINDALCO","ADANIENT","POWERINDIA","COCHINSHIP","INDIGO",
    "HDFCLIFE","IDEA","MAZDOCK","NMDC","POWERGRID","HAVELLS",
    "CHOLAFIN","PERSISTENT","SBILIFE","IDFCFIRSTB","JSWSTEEL",
    "WAAREEENER","CUMMINSIND","UNIONBANK","PFC","COALINDIA","ATGL",
    "TECHM","TATAELXSI","TMPV","NATIONALUM","LODHA","DRREDDY",
    "PREMIERENE","SWIGGY","TVSMOTOR","ULTRACEMCO","NESTLEIND","VOLTAS",
    "CIPLA","BAJAJFINSV","EICHERMOT","HAL","DIVISLAB","JINDALSTEL",
    "DMART","ABB","COFORGE","RADICO","ASHOKLEY","BLUESTARCO","CANBK",
    "LGEINDIA","AUBANK","BRITANNIA","RVNL","HUDCO","JUBLFOOD","BPCL",
    "SOLARINDS","RECLTD","IREDA","IRFC","POLYCAB","KEI","CGPOWER",
    "GRASIM","NAUKRI","BDL","HEROMOTOCO","LUPIN","BHARATFORG","CONCOR",
    "LAURUSLABS","POLICYBZR","KALYANKJIL","APOLLOHOSP","GODREJPROP",
    "KPITTECH","ALKEM","AMBUJACEM","BAJAJ-AUTO","TORNTPHARM","AUROPHARMA",
    "HINDPETRO","GAIL","LTM","DLF","HDFCAMC","IOC","FORTIS","MOTHERSON",
    "BANKBARODA","INDIANB","BOSCHLTD","YESBANK","HYUNDAI","OIL","SIEMENS",
    "GLENMARK","NHPC","ASIANPAINT","PNB","INDUSTOWER","NYKAA","FEDERALBNK",
    "MPHASIS","SRF","MAXHEALTH","EXIDEIND","ZYDUSLIFE","MUTHOOTFIN",
    "BIOCON","INDHOTEL","ABCAPITAL","APLAPOLLO","TATACAP","TATACONSUM",
    "SUPREMEIND","MRF","MANKIND","OBEROIRLTY","PAGEIND","GMRAIRPORT",
    "MARICO","TIINDIA","IRCTC","BANKINDIA","360ONE","ICICIGI","UPL",
    "SHREECEM","COLPAL","LICHSGFIN","ICICIAMC","PIIND","GODREJCP",
    "SBICARD","ASTRAL","MFSL","MOTILALOFS","PHOENIXLTD","PRESTIGE",
    "TATACOMM","PIDILITIND","PATANJALI","DABUR","COROMANDEL","BAJAJHLDNG",
]

# ============================================================
# PAGES
# ============================================================
page = st.session_state.active_page
st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 🏠 HOME
# ══════════════════════════════════════════════════════════════
if page == 'home':
    BRAND_NAME  = "BILLIONAIRES GROUP"
    BRAND_ICON  = "💼"
    TAGLINE     = "Be with us · Grow with us"
    ABOUT_PARA  = (
        "Billionaires Group is a community of passionate traders and investors "
        "united by one goal — consistent, disciplined wealth creation through the "
        "Indian stock markets. We combine cutting-edge algorithmic strategies with "
        "real-time market intelligence to give our members an unfair edge."
    )
    OFFERINGS = [
        ("📡","Live Algo Signals","Real-time Buy/Sell signals generated by our Candle Breakout engine across 150+ NSE stocks."),
        ("🤖","Automated Bot","Fully automated order placement, SL management, and trailing stop-loss via AliceBlue API."),
        ("📊","Risk Management","Position sizing: Qty = Risk ÷ |Entry − SL|. Every trade risks exactly what you set."),
        ("🎓","Education & Mentoring","Learn the strategy, understand the logic, and grow as a trader — not just a signal follower."),
    ]
    YOUTUBE_URL   = "https://www.youtube.com/@YOUR_CHANNEL"
    INSTAGRAM_URL = "https://www.instagram.com/YOUR_HANDLE"
    TWITTER_URL   = "https://x.com/YOUR_HANDLE"
    TELEGRAM_URL  = "https://t.me/YOUR_GROUP_OR_CHANNEL"
    WHATSAPP_URL  = "https://wa.me/91XXXXXXXXXX"
    WEBSITE_URL   = "https://www.yourwebsite.com"
    CONTACT_EMAIL = "your@email.com"
    CONTACT_PHONE = "+91 XXXXX XXXXX"

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0b0f1a 0%,#0f1520 60%,#131926 100%);
        border:1px solid rgba(250,196,0,0.12);border-radius:24px;padding:3rem 3rem 2.5rem;
        margin-bottom:2rem;position:relative;overflow:hidden;">
        <div style="position:absolute;top:-60px;right:-60px;width:300px;height:300px;border-radius:50%;
            background:radial-gradient(circle,rgba(250,196,0,0.07) 0%,transparent 70%);pointer-events:none;"></div>
        <div style="position:relative;z-index:1;">
            <div style="display:flex;align-items:center;gap:18px;margin-bottom:1.4rem;">
                <div style="width:64px;height:64px;border-radius:18px;background:linear-gradient(135deg,#FAC400,#c49a00);
                    display:flex;align-items:center;justify-content:center;font-size:1.9rem;
                    box-shadow:0 8px 32px rgba(250,196,0,0.4);flex-shrink:0;">{BRAND_ICON}</div>
                <div>
                    <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;color:#F0F4FF;line-height:1.1;">{BRAND_NAME}</div>
                    <div style="font-size:0.82rem;color:#FAC400;letter-spacing:0.1em;text-transform:uppercase;font-weight:600;margin-top:5px;">{TAGLINE}</div>
                </div>
            </div>
            <div style="max-width:700px;font-size:0.96rem;color:#8A96B0;line-height:1.8;border-left:3px solid rgba(250,196,0,0.4);padding-left:1.2rem;">{ABOUT_PARA}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header"><div class="section-title">What We Offer</div><div class="section-header-line"></div></div>', unsafe_allow_html=True)
    offer_cols = st.columns(len(OFFERINGS))
    for col, (icon, title, desc) in zip(offer_cols, OFFERINGS):
        with col:
            st.markdown(f"""
            <div style="background:#0f1520;border:1px solid rgba(255,255,255,0.06);border-radius:16px;
                padding:1.4rem 1.3rem 1.6rem;height:100%;position:relative;overflow:hidden;">
                <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#FAC400,transparent);"></div>
                <div style="font-size:1.8rem;margin-bottom:0.9rem;">{icon}</div>
                <div style="font-family:'Syne',sans-serif;font-size:0.92rem;font-weight:700;color:#F0F4FF;margin-bottom:0.5rem;">{title}</div>
                <div style="font-size:0.78rem;color:#4A5568;line-height:1.65;">{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header" style="margin-top:2.5rem;"><div class="section-title">Connect With Us</div><div class="section-header-line"></div></div>', unsafe_allow_html=True)
    social_defs = [
        ("▶  YouTube",   YOUTUBE_URL,   "#FF0000","rgba(255,0,0,0.08)","rgba(255,0,0,0.22)",      "Subscribe for trading tutorials, live market analysis and strategy breakdowns."),
        ("📸  Instagram", INSTAGRAM_URL, "#E1306C","rgba(225,48,108,0.08)","rgba(225,48,108,0.22)","Follow for daily charts, market updates and quick trading tips."),
        ("𝕏  Twitter/X", TWITTER_URL,   "#F0F4FF","rgba(240,244,255,0.04)","rgba(240,244,255,0.12)","Follow for real-time market commentary and quick trade ideas."),
        ("✈  Telegram",  TELEGRAM_URL,  "#29B6F6","rgba(41,182,246,0.08)","rgba(41,182,246,0.22)", "Join for live signals, alerts and community discussions."),
        ("💬  WhatsApp", WHATSAPP_URL,  "#25D366","rgba(37,211,102,0.08)","rgba(37,211,102,0.22)", "Connect for direct support and important trading alerts."),
        ("🌐  Website",  WEBSITE_URL,   "#FAC400","rgba(250,196,0,0.08)","rgba(250,196,0,0.25)",   "Visit our official website for more information, courses and resources."),
    ]
    socials = [(l,u,c,b,br,d) for l,u,c,b,br,d in social_defs if u.strip()]
    for i in range(0, len(socials), 2):
        row_items = socials[i:i+2]; cols = st.columns(2)
        for idx, (label,url,accent,bg,border,desc_text) in enumerate(row_items):
            with cols[idx]:
                st.markdown(f"""
                <a href="{url}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:block;">
                    <div style="background:{bg};border:1px solid {border};border-radius:16px;
                        padding:1.3rem 1.5rem;margin-bottom:14px;display:flex;align-items:flex-start;gap:16px;cursor:pointer;">
                        <div style="font-family:'Syne',sans-serif;font-size:0.95rem;font-weight:800;color:{accent};min-width:148px;padding-top:2px;flex-shrink:0;">{label}</div>
                        <div style="font-size:0.79rem;color:#4A5568;line-height:1.6;flex:1;">{desc_text}</div>
                        <div style="font-size:1.1rem;color:{accent};opacity:0.65;padding-top:2px;flex-shrink:0;">↗</div>
                    </div>
                </a>""", unsafe_allow_html=True)

    contact_parts = []
    if CONTACT_EMAIL.strip():
        contact_parts.append(f'<a href="mailto:{CONTACT_EMAIL}" style="text-decoration:none;color:#FAC400;font-weight:600;">📧 &nbsp;{CONTACT_EMAIL}</a>')
    if CONTACT_PHONE.strip():
        contact_parts.append(f'<span style="color:#8A96B0;">📞 &nbsp;{CONTACT_PHONE}</span>')
    if contact_parts:
        st.markdown('<div class="section-header" style="margin-top:1.5rem;"><div class="section-title">Contact</div><div class="section-header-line"></div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="background:#0f1520;border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:1.2rem 1.6rem;display:flex;align-items:center;gap:2.5rem;flex-wrap:wrap;font-size:0.9rem;">{"".join(contact_parts)}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# ⚙️ SETUP
# ══════════════════════════════════════════════════════════════
elif page == 'setup':
    st.markdown('<div class="page-hero"><div><div class="page-hero-title">Setup & Configuration</div><div class="page-hero-sub">Configure your settings and click <b style="color:#FAC400;">Apply & Lock Settings</b> before launching the bot</div></div></div>', unsafe_allow_html=True)

    cfg = st.session_state.active_config
    lock_time = st.session_state.get('config_locked_at', '')
    lock_label = f"Locked at {lock_time}" if lock_time else ("Default values — not yet applied" if not st.session_state.config_applied else "")

    st.markdown(f"""
    <div class="locked-config-banner">
        <div style="font-size:1.2rem;">{'🔒' if st.session_state.config_applied else '⚠️'}</div>
        <div style="flex:1;">
            <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:0.82rem;
                color:{'#00E096' if st.session_state.config_applied else '#FAC400'};margin-bottom:8px;">
                {'✅ Active Config — Bot will use these values' if st.session_state.config_applied else '⚠️ Not Applied Yet — Click Apply & Lock Settings below'}
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
                <div class="locked-config-pill"><span class="lc-label">RISK</span> ₹{cfg['risk_amt']:,}</div>
                <div class="locked-config-pill"><span class="lc-label">T1</span> {cfg['t1_mult']}×</div>
                <div class="locked-config-pill"><span class="lc-label">T2</span> {cfg['t2_mult']}×</div>
                <div class="locked-config-pill"><span class="lc-label">FINAL</span> {cfg['final_mult']}×</div>
                <div class="locked-config-pill"><span class="lc-label">TF</span> {cfg['timeframe']}</div>
                <div class="locked-config-pill"><span class="lc-label">SCAN</span> {cfg['scan_interval']}s</div>
                <div class="locked-config-pill"><span class="lc-label">INSTR</span> {cfg['instrument_type']}</div>
                {'<div style="margin-left:auto;font-size:0.68rem;color:#4A5568;">' + lock_label + '</div>' if lock_label else ''}
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(
        '<div class="setup-card"><div class="setup-card-header">'
        '<div class="setup-card-icon">💰</div>'
        '<div><div class="setup-card-num">Step 01</div>'
        '<div class="setup-card-title">Risk Management & Targets</div></div>'
        '<div class="setup-card-done">✓ Configure</div>'
        '</div></div>',
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input(
            "Risk per Trade (₹)",
            min_value=1,
            max_value=10_000_000,
            value=st.session_state.risk_amt,
            step=100,
            key="risk_amt",
            help=(
                "Qty = Risk ÷ |Entry − SL|\n"
                "BUY:  Entry=1st candle High, SL=1st candle Low\n"
                "SELL: Entry=1st candle Low,  SL=1st candle High\n\n"
                "Example: Entry=2000, SL=1995, Risk=₹1000\n"
                "|2000−1995|=5  →  Qty=1000÷5=200"
            ),
        )
    with c2:
        st.selectbox(
            "Target 1 (T1)",
            [0.5, 1.0, 1.5, 2.0],
            index=[0.5, 1.0, 1.5, 2.0].index(st.session_state.t1_mult),
            format_func=lambda x: f"{x}× Range",
            key="t1_mult"
        )
    with c3:
        st.selectbox(
            "Target 2 (T2)",
            [1.0, 1.5, 2.0, 2.5, 3.0],
            index=[1.0, 1.5, 2.0, 2.5, 3.0].index(st.session_state.t2_mult),
            format_func=lambda x: f"{x}× Range",
            key="t2_mult"
        )
    with c4:
        st.selectbox(
            "Final Target",
            [2.0, 2.5, 3.0, 3.5, 4.0, 5.0],
            index=[2.0, 2.5, 3.0, 3.5, 4.0, 5.0].index(st.session_state.final_mult),
            format_func=lambda x: f"{x}× Range",
            key="final_mult"
        )

    _r = st.session_state.risk_amt
    st.markdown(f"""
    <div style="background:#131926;border:1px solid rgba(0,217,196,0.2);border-radius:10px;
        padding:1rem 1.4rem;margin:0.6rem 0 1rem;font-size:0.83rem;color:#8A96B0;line-height:2;">
        <b style="color:#00D9C4;font-size:0.9rem;">📐 Qty Formula (same for BUY & SELL)</b><br>
        <span style="color:#FAC400;font-family:'Space Mono',monospace;">Qty = Risk Amount ÷ | Entry − SL |</span><br>
        BUY &nbsp;→ Entry = 1st candle <b style="color:#00E096;">High</b>, &nbsp;SL = 1st candle <b style="color:#FF4D6A;">Low</b><br>
        SELL → Entry = 1st candle <b style="color:#FF4D6A;">Low</b>, &nbsp; SL = 1st candle <b style="color:#00E096;">High</b><br>
        <hr style="border-color:rgba(255,255,255,0.06);margin:0.5rem 0;">
        <b style="color:#FAC400;">Live Preview with current input ₹{_r:,} — NOT active until you click Apply below</b><br>
        &nbsp;&nbsp;Range = ₹&nbsp;&nbsp;5 → Qty = <b style="color:#F0F4FF;">{max(1,int(_r/5))}</b> &nbsp;| Max Loss = <b style="color:#FF4D6A;">₹{r2(5*max(1,int(_r/5))):,.0f}</b><br>
        &nbsp;&nbsp;Range = ₹10 → Qty = <b style="color:#F0F4FF;">{max(1,int(_r/10))}</b> &nbsp;| Max Loss = <b style="color:#FF4D6A;">₹{r2(10*max(1,int(_r/10))):,.0f}</b><br>
        &nbsp;&nbsp;Range = ₹20 → Qty = <b style="color:#F0F4FF;">{max(1,int(_r/20))}</b> &nbsp;| Max Loss = <b style="color:#FF4D6A;">₹{r2(20*max(1,int(_r/20))):,.0f}</b><br>
        &nbsp;&nbsp;Range = ₹50 → Qty = <b style="color:#F0F4FF;">{max(1,int(_r/50))}</b> &nbsp;| Max Loss = <b style="color:#FF4D6A;">₹{r2(50*max(1,int(_r/50))):,.0f}</b>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    scanned_status = "setup-card-done" if st.session_state.data_fetched else "setup-card-pending"
    scanned_label  = "✓ Scanned" if st.session_state.data_fetched else "⚠ Pending"
    st.markdown(
        f'<div class="setup-card"><div class="setup-card-header">'
        f'<div class="setup-card-icon" style="background:var(--teal-dim);border-color:rgba(0,217,196,0.25);">📊</div>'
        f'<div><div class="setup-card-num">Step 02</div>'
        f'<div class="setup-card-title">Stock Universe & Filter</div></div>'
        f'<div class="{scanned_status}">{scanned_label}</div>'
        f'</div></div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.selectbox("Timeframe", ['15min', '5min'],
                     index=['15min', '5min'].index(st.session_state.get('timeframe', '15min')), key="timeframe")
        st.selectbox("Strategy", ["Candle Breakout Strategy"], key="strat")
    with c2:
        st.number_input("Min Change %", 0.0, 100.0, st.session_state.get('min_change', 2.0), 0.5, key="min_change")
        st.number_input("Max Change %", 0.0, 100.0, st.session_state.get('max_change', 5.0), 0.5, key="max_change")
    with c3:
        st.number_input("Min LTP (₹)", 0, 10000, st.session_state.get('min_ltp', 500), 100, key="min_ltp")
        st.number_input("Max LTP (₹)", 0, 50000, st.session_state.get('max_ltp', 3000), 100, key="max_ltp")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍  SCAN STOCK UNIVERSE", use_container_width=True, key="get_data", type="primary"):
        df = fetch_stocks_data_from_tv(tuple(default_symbols))
        if not df.empty:
            filt = df[
                (df['Change %'] >= st.session_state.min_change) &
                (df['Change %'] <= st.session_state.max_change) &
                (df['LTP'] > st.session_state.min_ltp) &
                (df['LTP'] < st.session_state.max_ltp)
            ]
            st.session_state.filtered_stocks = filt['Symbol'].tolist()
            st.session_state.filtered_df     = filt
            st.session_state.data_fetched    = True
            st.success(f"✅ {len(filt)} stocks matched")
            st.rerun()
        else:
            st.error("❌ No data from TradingView")

    if not st.session_state.filtered_df.empty:
        fdf = st.session_state.filtered_df
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Matched", len(fdf))
        with c2: st.metric("Avg Change %", f"{fdf['Change %'].mean():.2f}%")
        with c3: st.metric("Max Change %", f"{fdf['Change %'].max():.2f}%")
        with c4: st.metric("Avg LTP", f"₹{fdf['LTP'].mean():,.2f}")
        disp = fdf.copy()
        disp['LTP']      = disp['LTP'].apply(lambda x: f"₹{x:,.2f}")
        disp['Change %'] = disp['Change %'].apply(lambda x: f"{x:+.2f}%")
        st.dataframe(disp[['Symbol', 'LTP', 'Change %', 'Volume']], use_container_width=True, height=220)

    st.markdown("<br>", unsafe_allow_html=True)

    conn_status = "setup-card-done" if st.session_state.aliceblue_connected else "setup-card-pending"
    conn_label  = "✓ Connected" if st.session_state.aliceblue_connected else "⚠ Not Connected"
    st.markdown(
        f'<div class="setup-card"><div class="setup-card-header">'
        f'<div class="setup-card-icon" style="background:rgba(255,77,106,0.08);border-color:rgba(255,77,106,0.2);">🔑</div>'
        f'<div><div class="setup-card-num">Step 03</div>'
        f'<div class="setup-card-title">AliceBlue Broker Connection</div></div>'
        f'<div class="{conn_status}">{conn_label}</div>'
        f'</div></div>',
        unsafe_allow_html=True
    )

    creds      = USER_ALICEBLUE_CREDS.get(st.session_state.app_username, {})
    app_code   = creds.get("app_code", "")
    user_id    = creds.get("user_id", "")
    api_secret = creds.get("api_secret", "")

    ca, cb = st.columns([1, 2])
    with ca:
        inst_options = ["Equity", "Options"]
        inst_idx = inst_options.index(st.session_state.get('instrument_type', 'Equity'))
        st.selectbox("Instrument Type", inst_options, index=inst_idx, key="instrument_type")

    with cb:
        if app_code:
            st.markdown(f"""
            <div style="background:#131926;border:1px solid rgba(250,196,0,0.2);border-radius:10px;
                padding:0.75rem 1.1rem;margin-bottom:0.6rem;display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
                <div>
                    <div style="font-size:0.65rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Step A — Open AliceBlue Login</div>
                    <a href="https://ant.aliceblueonline.com/?appcode={app_code}" target="_blank" rel="noopener noreferrer"
                        style="display:inline-flex;align-items:center;gap:7px;background:rgba(250,196,0,0.08);border:1px solid rgba(250,196,0,0.28);color:#FAC400;font-size:0.82rem;font-weight:600;padding:6px 14px;border-radius:20px;text-decoration:none;">
                        🔗 Click here to Login &amp; get Auth Code
                    </a>
                    <div style="margin-top:5px;font-size:0.72rem;color:#4A5568;">Copy the <code style="color:#FAC400;background:rgba(250,196,0,0.08);padding:1px 5px;border-radius:4px;">authCode=</code> value from the redirect URL</div>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="background:rgba(255,77,106,0.07);border:1px solid rgba(255,77,106,0.2);border-radius:8px;padding:0.6rem 1rem;font-size:0.8rem;color:#FF4D6A;margin-bottom:0.6rem;">⚠️ Credentials not configured. Contact admin.</div>', unsafe_allow_html=True)

        col_auth, col_btn, col_funds = st.columns([2, 1.4, 1])
        with col_auth:
            auth_code = st.text_input("Step B — Auth Code", type="password", key="auth_code",
                                      placeholder="Paste authCode from redirect URL…")
        with col_btn:
            st.markdown("<div style='margin-top:1.78rem;'></div>", unsafe_allow_html=True)
            if st.button("🔌  Connect AliceBlue", key="connect_btn", type="primary", use_container_width=True):
                if not app_code or not user_id or not api_secret:
                    st.error("❌ Credentials not configured.")
                elif not auth_code:
                    st.error("❌ Paste your Auth Code first.")
                else:
                    _, sid = get_session_from_authcode(user_id, auth_code, api_secret)
                    if sid:
                        st.session_state.session_id          = sid
                        st.session_state.aliceblue_connected = True
                    else:
                        st.session_state.aliceblue_connected = False
        with col_funds:
            st.markdown("<div style='margin-top:1.78rem;'></div>", unsafe_allow_html=True)
            if st.session_state.aliceblue_connected:
                if st.button("💰 Funds", key="check_funds", use_container_width=True):
                    f = get_funds(st.session_state.session_id)
                    if f: st.json(f)
                    else: st.warning("Could not fetch funds")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="setup-card"><div class="setup-card-header">'
        '<div class="setup-card-icon" style="background:rgba(0,217,196,0.1);border-color:rgba(0,217,196,0.25);">⏱️</div>'
        '<div><div class="setup-card-num">Step 04</div>'
        '<div class="setup-card-title">Bot Scan Interval</div></div>'
        '<div class="setup-card-done">✓ Configure</div>'
        '</div></div>',
        unsafe_allow_html=True
    )
    st.slider(
        "Scan Interval (seconds)", 5, 60,
        st.session_state.get('scan_interval', 10), key="scan_interval"
    )
    st.caption(
        f"Bot will scan {len(st.session_state.filtered_stocks)} stocks every "
        f"{st.session_state.scan_interval}s  ·  "
        f"Staged Risk: ₹{st.session_state.risk_amt:,}  ·  "
        f"Active Risk: ₹{st.session_state.active_config['risk_amt']:,}"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(250,196,0,0.08),rgba(250,196,0,0.04));
        border:1px solid rgba(250,196,0,0.3);border-radius:16px;padding:1.4rem 1.6rem;margin-bottom:1rem;">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1rem;color:#FAC400;margin-bottom:6px;">
            🔒 Apply & Lock Settings
        </div>
        <div style="font-size:0.8rem;color:#8A96B0;margin-bottom:1rem;line-height:1.6;">
            Click this button to lock your current configuration. The Bot page will <b style="color:#F0F4FF;">only</b>
            use the values locked here — not whatever is typed in the fields above.
            You can change settings anytime and re-apply without stopping the bot.
        </div>
    </div>""", unsafe_allow_html=True)

    apply_col, _ = st.columns([1, 2])
    with apply_col:
        if st.button("🔒  APPLY & LOCK SETTINGS", type="primary", use_container_width=True, key="apply_settings"):
            st.session_state.active_config = {
                'risk_amt':        st.session_state.risk_amt,
                't1_mult':         st.session_state.t1_mult,
                't2_mult':         st.session_state.t2_mult,
                'final_mult':      st.session_state.final_mult,
                'timeframe':       st.session_state.timeframe,
                'scan_interval':   st.session_state.scan_interval,
                'instrument_type': st.session_state.instrument_type,
            }
            st.session_state.config_applied   = True
            st.session_state.config_locked_at = datetime.now().strftime('%H:%M:%S')
            st.success(
                f"✅ Settings locked!  Risk=₹{st.session_state.risk_amt:,}  "
                f"T1={st.session_state.t1_mult}×  T2={st.session_state.t2_mult}×  "
                f"Final={st.session_state.final_mult}×  TF={st.session_state.timeframe}  "
                f"Scan={st.session_state.scan_interval}s  "
                f"Instr={st.session_state.instrument_type}"
            )
            st.rerun()

    all_ok = st.session_state.data_fetched and st.session_state.aliceblue_connected and st.session_state.config_applied
    if all_ok:
        st.markdown(
            '<div style="background:rgba(0,224,150,0.07);border:1px solid rgba(0,224,150,0.2);'
            'border-radius:14px;padding:1.2rem 1.6rem;display:flex;align-items:center;gap:14px;margin-top:1rem;">'
            '<div style="font-size:1.5rem;">✅</div>'
            '<div><div style="font-family:\'Syne\',sans-serif;font-weight:700;color:#00E096;margin-bottom:3px;">Setup Complete!</div>'
            '<div style="font-size:0.8rem;color:#4A5568;">All steps configured — head to '
            '<b style="color:#FAC400;">Bot</b> tab to launch.</div></div></div>',
            unsafe_allow_html=True
        )
    else:
        missing = []
        if not st.session_state.data_fetched:        missing.append("Scan stock universe (Step 2)")
        if not st.session_state.aliceblue_connected: missing.append("Connect AliceBlue (Step 3)")
        if not st.session_state.config_applied:      missing.append("Apply & Lock Settings (button above)")
        st.markdown(
            f'<div style="background:rgba(250,196,0,0.06);border:1px solid rgba(250,196,0,0.2);'
            f'border-radius:14px;padding:1.2rem 1.6rem;margin-top:1rem;">'
            f'<div style="font-family:\'Syne\',sans-serif;font-weight:700;color:#FAC400;margin-bottom:8px;">⚠️ Setup Incomplete</div>'
            f'<div style="font-size:0.8rem;color:#8A96B0;">{"<br>".join(f"• {m}" for m in missing)}</div></div>',
            unsafe_allow_html=True
        )

# ══════════════════════════════════════════════════════════════
# 🤖 BOT
# ══════════════════════════════════════════════════════════════
elif page == 'bot':
    cfg = st.session_state.active_config

    st.markdown(
        '<div class="page-hero"><div>'
        '<div class="page-hero-title">Bot Control</div>'
        '<div class="page-hero-sub">Launch, monitor, and stop the live trading bot</div>'
        '</div></div>',
        unsafe_allow_html=True
    )

    if not st.session_state.config_applied:
        st.markdown(
            '<div class="config-dirty-banner">'
            '⚠️ &nbsp; You have not applied your settings yet. '
            'The bot will use <b>default values</b>. '
            'Go to <b>Setup → Apply & Lock Settings</b> first.'
            '</div>',
            unsafe_allow_html=True
        )

    lock_time = st.session_state.get('config_locked_at', '')
    st.markdown(f"""
    <div style="background:#131926;border:1px solid {'rgba(0,224,150,0.25)' if st.session_state.config_applied else 'rgba(250,196,0,0.2)'};
        border-radius:12px;padding:0.9rem 1.4rem;margin-bottom:1.2rem;display:flex;align-items:center;gap:12px;flex-wrap:wrap;font-size:0.84rem;">
        <span style="font-size:1rem;">{'🔒' if st.session_state.config_applied else '⚠️'}</span>
        <span style="color:#4A5568;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;font-weight:700;">
            {'Locked Config' if st.session_state.config_applied else 'Default Config (not applied)'}
            {(' — ' + lock_time) if lock_time else ''}:
        </span>
        <span>Risk: <b style="color:#FAC400;">₹{cfg['risk_amt']:,}</b></span>
        <span style="color:#4A5568;">·</span>
        <span>Qty: <b style="color:#00D9C4;">Risk ÷ |Entry−SL|</b></span>
        <span style="color:#4A5568;">·</span>
        <span>TF: <b style="color:#F0F4FF;">{cfg['timeframe']}</b></span>
        <span style="color:#4A5568;">·</span>
        <span>Stocks: <b style="color:#F0F4FF;">{len(st.session_state.filtered_stocks)}</b></span>
        <span style="color:#4A5568;">·</span>
        <span>T1:{cfg['t1_mult']}× &nbsp;T2:{cfg['t2_mult']}× &nbsp;Final:{cfg['final_mult']}×</span>
        <span style="color:#4A5568;">·</span>
        <span>Scan: <b style="color:#F0F4FF;">{cfg['scan_interval']}s</b></span>
    </div>""", unsafe_allow_html=True)

    col_start, col_stop, col_space = st.columns([1, 1, 4])
    with col_start:
        if not st.session_state.auto_refresh:
            if st.button("⚡  LAUNCH BOT", type="primary", use_container_width=True, key="start_bot"):
                if not st.session_state.data_fetched:
                    st.error("❌ Complete Setup Step 2 first (Scan stock universe)")
                elif not st.session_state.aliceblue_connected:
                    st.error("❌ Complete Setup Step 3 first (Connect AliceBlue)")
                elif not st.session_state.config_applied:
                    st.error("❌ Apply & Lock Settings in Setup first")
                else:
                    st.session_state.bot_start_datetime     = datetime.now()
                    st.session_state.auto_refresh           = True
                    st.session_state.signals                = []
                    st.session_state.refresh_counter        = 0
                    st.session_state.signal_count_per_stock = {}
                    st.session_state.traded_symbols_today   = set()
                    st.rerun()
    with col_stop:
        if st.session_state.auto_refresh:
            if st.button("⏹  STOP BOT", type="secondary", use_container_width=True, key="stop_bot"):
                st.session_state.auto_refresh = False
                st.rerun()

    if not st.session_state.auto_refresh:
        if not st.session_state.data_fetched or not st.session_state.aliceblue_connected or not st.session_state.config_applied:
            missing_items = []
            if not st.session_state.data_fetched:        missing_items.append("Scan stock universe (Setup Step 2)")
            if not st.session_state.aliceblue_connected: missing_items.append("Connect AliceBlue (Setup Step 3)")
            if not st.session_state.config_applied:      missing_items.append("Apply & Lock Settings (Setup page)")
            st.markdown(
                '<div style="margin-top:1.5rem;background:rgba(250,196,0,0.06);border:1px solid rgba(250,196,0,0.2);'
                'border-radius:14px;padding:1.4rem 1.8rem;">'
                '<div style="font-family:\'Syne\',sans-serif;font-weight:700;color:#FAC400;margin-bottom:6px;">⚠️ Pre-launch checklist</div>'
                '<div style="font-size:0.82rem;color:#8A96B0;line-height:1.8;">'
                + "<br>".join(f"• {m}" for m in missing_items) +
                '</div></div>',
                unsafe_allow_html=True
            )
    else:
        if not st.session_state.aliceblue_connected:
            st.error("⚠️ AliceBlue session lost — bot stopped.")
            st.session_state.auto_refresh = False
            st.rerun()

        start_str = st.session_state.bot_start_datetime.strftime('%H:%M:%S')
        syms      = st.session_state.filtered_stocks

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Bot Status", "🟢 RUNNING")
        with c2: st.metric("Cycle", f"#{st.session_state.refresh_counter}")
        with c3: st.metric("Active Trades", len(st.session_state.active_trades))
        with c4: st.metric("Risk per Trade", f"₹{cfg['risk_amt']:,}")

        st.markdown(
            f'<div class="scan-banner">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:#00E096;display:inline-block;animation:pulse-green 2s infinite;"></span>'
            f'Scanning <b style="margin:0 4px;">{len(syms)}</b> stocks &nbsp;·&nbsp; '
            f'Started <b style="margin:0 4px;">{start_str}</b> &nbsp;·&nbsp; '
            f'Interval <b style="margin:0 4px;">{cfg["scan_interval"]}s</b> &nbsp;·&nbsp; '
            f'Risk <b style="margin:0 4px;">₹{cfg["risk_amt"]:,}</b> &nbsp;·&nbsp; '
            f'Qty=Risk÷|Entry−SL|'
            f'</div>',
            unsafe_allow_html=True
        )

        pb     = st.progress(0)
        status = st.empty()
        new    = run_bot_cycle(syms, cfg, pb, status)
        if new:
            st.session_state.signals.extend(new)
            st.balloons()
            st.success(f"🎯 {len(new)} NEW SIGNAL{'S' if len(new)>1 else ''}! Qty computed as Risk ÷ |Entry−SL|")

        st.markdown('<div class="section-header"><div class="section-title">Active Trades</div><div class="section-header-line"></div></div>', unsafe_allow_html=True)
        display_active_trades(st.session_state.active_trades)

        if st.session_state.signals:
            st.markdown('<div class="section-header"><div class="section-title">Signals Today</div><div class="section-header-line"></div></div>', unsafe_allow_html=True)
            display_signals_table(st.session_state.signals)

        st.rerun()

# ══════════════════════════════════════════════════════════════
# 📋 HISTORY
# ══════════════════════════════════════════════════════════════
elif page == 'history':
    st.markdown(
        '<div class="page-hero"><div>'
        '<div class="page-hero-title">Trade History</div>'
        '<div class="page-hero-sub">All signals and completed trades from this session</div>'
        '</div></div>',
        unsafe_allow_html=True
    )

    active_count    = len(st.session_state.active_trades)
    signal_count    = len(st.session_state.signals)
    completed_count = len(st.session_state.completed_trades)
    total_pnl       = sum(t.get('PNL', 0) for t in st.session_state.completed_trades)
    pnl_cls  = "green" if total_pnl >= 0 else "red"
    pnl_sign = "+" if total_pnl >= 0 else ""

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card teal"><div class="metric-icon">📡</div><div class="metric-value">{signal_count}</div><div class="metric-label">Signals Today</div></div>
        <div class="metric-card"><div class="metric-icon">⚡</div><div class="metric-value">{active_count}</div><div class="metric-label">Still Active</div></div>
        <div class="metric-card"><div class="metric-icon">✅</div><div class="metric-value">{completed_count}</div><div class="metric-label">Completed</div></div>
        <div class="metric-card {pnl_cls}"><div class="metric-icon">₹</div><div class="metric-value">{pnl_sign}₹{total_pnl:,.0f}</div><div class="metric-label">Session P&amp;L</div></div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.signals:
        st.markdown('<div class="section-header"><div class="section-title">All Signals (with Qty Verification)</div><div class="section-header-line"></div></div>', unsafe_allow_html=True)
        display_signals_table(st.session_state.signals)

    if st.session_state.completed_trades:
        st.markdown('<div class="section-header"><div class="section-title">Completed Trades</div><div class="section-header-line"></div></div>', unsafe_allow_html=True)
        display_completed(st.session_state.completed_trades)

    if not st.session_state.signals and not st.session_state.completed_trades:
        st.markdown(
            '<div style="text-align:center;padding:4rem;background:#0f1520;border:1px solid rgba(255,255,255,0.06);'
            'border-radius:14px;color:#4A5568;font-size:0.85rem;margin-top:1rem;">📋 No trade history yet</div>',
            unsafe_allow_html=True
        )

    cfg    = st.session_state.active_config
    _t1    = cfg['t1_mult']
    _t2    = cfg['t2_mult']
    _final = cfg['final_mult']
    _r     = cfg['risk_amt']

    st.markdown('<div class="section-header" style="margin-top:2.5rem;"><div class="section-title">Strategy Reference (Active Config)</div><div class="section-header-line"></div></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="strategy-grid">
        <div class="strategy-cell"><div class="sc-label">BUY Signal</div><div class="sc-value">Price breaks 1st candle High</div></div>
        <div class="strategy-cell"><div class="sc-label">SELL Signal</div><div class="sc-value">Price breaks 1st candle Low</div></div>
        <div class="strategy-cell gold-accent"><div class="sc-label">Qty Formula</div><div class="sc-value">Risk ÷ |Entry − SL|</div></div>
        <div class="strategy-cell"><div class="sc-label">BUY: Entry / SL</div><div class="sc-value">1st candle High / Low</div></div>
        <div class="strategy-cell"><div class="sc-label">SELL: Entry / SL</div><div class="sc-value">1st candle Low / High</div></div>
        <div class="strategy-cell gold-accent"><div class="sc-label">Locked Risk Setting</div><div class="sc-value">₹{_r:,}</div></div>
        <div class="strategy-cell"><div class="sc-label">Example (Range=₹5)</div><div class="sc-value">₹{_r:,} ÷ ₹5 = {max(1,int(_r/5))} shares</div></div>
        <div class="strategy-cell"><div class="sc-label">Example (Range=₹10)</div><div class="sc-value">₹{_r:,} ÷ ₹10 = {max(1,int(_r/10))} shares</div></div>
        <div class="strategy-cell gold-accent"><div class="sc-label">Example (Range=₹50)</div><div class="sc-value">₹{_r:,} ÷ ₹50 = {max(1,int(_r/50))} shares</div></div>
        <div class="strategy-cell"><div class="sc-label">T1 ({_t1}× Range)</div><div class="sc-value">SL trails → Entry (Breakeven)</div></div>
        <div class="strategy-cell"><div class="sc-label">T2 ({_t2}× Range)</div><div class="sc-value">SL trails → T1 Price</div></div>
        <div class="strategy-cell gold-accent"><div class="sc-label">Final ({_final}× Range)</div><div class="sc-value">Close position at Market</div></div>
    </div>""", unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────
st.markdown("""
<div class="app-footer">
    <div class="footer-brand">⚡ BILLIONAIRES GROUP</div>
    <div>Be with us · Grow with us</div>
    <div>© 2026 · Algorithmic Trading System · NSE / NFO</div>
</div>""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
