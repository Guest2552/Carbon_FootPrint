
import streamlit as st
from utils.db import init_db, login_user, register_user, validate_password

init_db()

st.set_page_config(
    page_title="CarbonLens AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#0f1117;}
[data-testid="stSidebar"]{background:#161b2e;}
.main .block-container{padding-top:1.5rem;padding-bottom:2rem;max-width:1280px;}
.stMetric{background:#1a2035;border-radius:16px;padding:16px;border:1px solid rgba(255,255,255,0.07);}
h1,h2,h3{color:#e2e8f0;}
.stSelectbox label,.stSlider label,.stNumberInput label,.stRadio label{color:#94a3b8 !important;}
div[data-testid="stMetricValue"]{font-size:1.8rem;font-weight:800;color:#38bdf8;}
div[data-testid="stMetricDelta"]{font-size:0.85rem;}
.badge-chip{display:inline-block;background:#1e3a5f;border:1px solid #38bdf8;border-radius:20px;padding:4px 12px;margin:4px;font-size:0.85rem;color:#7dd3fc;}
.lb-gold{background:linear-gradient(90deg,#713f12,#92400e);border-radius:12px;padding:10px 16px;margin:4px 0;color:#fef3c7;}
.lb-silver{background:linear-gradient(90deg,#1e3a2f,#14532d);border-radius:12px;padding:10px 16px;margin:4px 0;color:#d1fae5;}
.lb-bronze{background:linear-gradient(90deg,#1e2a4a,#1e3a5f);border-radius:12px;padding:10px 16px;margin:4px 0;color:#bae6fd;}
.lb-row{background:#1a2035;border-radius:12px;padding:10px 16px;margin:4px 0;color:#cbd5e1;border:1px solid rgba(255,255,255,0.05);}
.action-easy{background:#1a2035;border-left:4px solid #10b981;border-radius:12px;padding:14px 18px;margin:8px 0;}
.action-medium{background:#1a2035;border-left:4px solid #f59e0b;border-radius:12px;padding:14px 18px;margin:8px 0;}
.card-dark{background:#1a2035;border-radius:16px;padding:20px;border:1px solid rgba(255,255,255,0.07);margin-bottom:12px;}
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

def auth_screen():
    st.markdown("<h1 style='text-align:center;font-size:2.5rem;'>🌍 CarbonLens <span style='color:#38bdf8'>AI</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#94a3b8;font-size:1.1rem;'>Personal carbon intelligence — track, understand, and reduce your footprint.</p>", unsafe_allow_html=True)
    st.markdown("---")

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

    with tab1:
        with st.form("login_form"):
            st.markdown("#### Sign in to your account")
            uname = st.text_input("Username", placeholder="Enter your username")
            pwd   = st.text_input("Password", type="password", placeholder="Enter your password")
            if st.form_submit_button("Login", use_container_width=True):
                if not uname or not pwd:
                    st.error("Please enter both username and password.")
                else:
                    user = login_user(uname, pwd)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

    with tab2:
        with st.form("register_form"):
            st.markdown("#### Create a new account")
            new_uname = st.text_input("Choose a username", placeholder="At least 3 characters")
            new_pwd   = st.text_input("Choose a password", type="password",
                                       placeholder="Min 8 chars, include a letter and number",
                                       help="Must be at least 8 characters, contain a letter and a number.")
            persona   = st.selectbox("Persona", ["Student","Working Professional","Remote Worker","Freelancer"])
            city_tier = st.selectbox("City tier", ["Tier 1","Tier 2","Tier 3/Rural"])
            hh_size   = st.slider("Household size", 1, 8, 3)
            if st.form_submit_button("Create account", use_container_width=True):
                if len(new_uname.strip()) < 3:
                    st.error("Username must be at least 3 characters.")
                else:
                    ok_pw, pw_msg = validate_password(new_pwd)
                    if not ok_pw:
                        st.error(pw_msg)
                    else:
                        ok, uid = register_user(new_uname, new_pwd, persona, city_tier, hh_size)
                        if ok:
                            st.success("Account created! Please login.")
                        else:
                            st.error("Username already taken. Choose another.")

if not st.session_state.user:
    auth_screen()
    st.stop()

# ── Sidebar ──────────────────────────────────────────────────────────
st.sidebar.markdown(f"### 👤 {st.session_state.user['username']}")
st.sidebar.caption(f"{st.session_state.user['persona']} · {st.session_state.user['city_tier']}")
st.sidebar.markdown("---")

st.sidebar.markdown("#### 🤖 Groq AI Coach")
st.sidebar.caption("Get your free API key at [console.groq.com](https://console.groq.com).")
api_key_input = st.sidebar.text_input(
    "Groq API key",
    type="password",
    key="groq_api_key_input",
    placeholder="gsk_...",
    help="Stored only in session memory — never saved to the database.",
)
if api_key_input:
    st.session_state["groq_api_key"] = api_key_input

st.sidebar.markdown("---")
nav = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "📅 History", "🏆 Leaderboard", "🏅 Badges", "⚙️ Scenario Lab"],
)
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.user = None
    st.rerun()

# ── Page routing ─────────────────────────────────────────────────────
if nav == "📊 Dashboard":
    import pages.dashboard as pg
elif nav == "📅 History":
    import pages.history as pg
elif nav == "🏆 Leaderboard":
    import pages.leaderboard as pg
elif nav == "🏅 Badges":
    import pages.badges as pg
else:
    import pages.scenario_lab as pg

pg.render(st.session_state.user)
