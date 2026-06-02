"""
styles.py — Global Streamlit CSS
==================================
All custom CSS lives here as the ``APP_STYLES`` constant so it is never
scattered across page modules.  Inject it once at the top of every page:

    st.markdown(APP_STYLES, unsafe_allow_html=True)

Colour palette (dark-mode GitHub-inspired)
------------------------------------------
Background        #0d1117
Surface           #161b22
Border            #21262d  /  #30363d
Text (primary)    #e2e8f0
Text (muted)      #64748b  /  #475569
Accent (indigo)   #818cf8  /  #4338ca
Accent (sky)      #38bdf8
"""

APP_STYLES: str = """
<style>
  /* ── Base ─────────────────────────────────────────────────────────────── */
  .stApp { background: #0d1117; }
  .block-container { max-width: 800px; padding-top: 2rem; padding-bottom: 1.5rem; }
  #MainMenu, footer, header { visibility: hidden; }

  /* ── Header ───────────────────────────────────────────────────────────── */
  .app-title {
    font-size: 2.1rem; font-weight: 800; text-align: center;
    background: linear-gradient(90deg, #818cf8 30%, #38bdf8 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: .2rem;
  }
  .app-subtitle {
    text-align: center; color: #475569; font-size: .88rem;
    margin-bottom: 2rem; letter-spacing: .01em;
  }

  /* ── Field labels ─────────────────────────────────────────────────────── */
  .field-label {
    color: #64748b; font-size: .78rem; font-weight: 700;
    letter-spacing: .08em; text-transform: uppercase;
    margin: 0 0 .35rem .05rem;
  }

  /* ── Chat window ──────────────────────────────────────────────────────── */
  .chat-window {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 14px;
    padding: 1.2rem 1.2rem .8rem;
    height: 430px;
    overflow-y: auto;
    margin-bottom: 1.4rem;
    scroll-behavior: smooth;
  }
  .chat-window::-webkit-scrollbar { width: 5px; }
  .chat-window::-webkit-scrollbar-track { background: transparent; }
  .chat-window::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }

  /* ── Empty state ──────────────────────────────────────────────────────── */
  .empty-state {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; height: 380px; gap: .8rem;
    color: #30363d; font-size: .93rem; user-select: none;
  }
  .empty-icon { font-size: 2.8rem; }

  /* ── Message rows ─────────────────────────────────────────────────────── */
  .msg-row { display: flex; flex-direction: column; margin-bottom: 1.1rem; gap: .25rem; }
  .msg-row.user { align-items: flex-end; }
  .msg-row.bot  { align-items: flex-start; }

  .msg-meta { font-size: .71rem; font-weight: 700; letter-spacing: .04em; }
  .msg-row.user .msg-meta { color: #818cf8; margin-right: .25rem; }
  .msg-row.bot  .msg-meta { color: #38bdf8; margin-left: .25rem; }

  /* ── Bubbles ──────────────────────────────────────────────────────────── */
  .bubble {
    max-width: 84%; padding: .72rem 1rem;
    font-size: .92rem; line-height: 1.65; word-wrap: break-word;
    white-space: pre-wrap;
  }
  .msg-row.user .bubble {
    background: linear-gradient(135deg, #4338ca, #6d28d9);
    color: #fff; border-radius: 18px 18px 4px 18px;
    box-shadow: 0 3px 14px rgba(99,102,241,.28);
  }
  .msg-row.bot .bubble {
    background: #1e2530; color: #cbd5e1;
    border: 1px solid #21262d;
    border-radius: 4px 18px 18px 18px;
  }

  /* ── Audience badge ───────────────────────────────────────────────────── */
  .badge {
    display: inline-block;
    background: rgba(56,189,248,.1);
    border: 1px solid rgba(56,189,248,.22);
    color: #7dd3fc; border-radius: 20px;
    padding: .08rem .48rem; font-size: .67rem;
    margin-left: .4rem; vertical-align: middle;
    font-weight: 600; letter-spacing: .03em;
  }

  /* ── Source tooltip ───────────────────────────────────────────────────── */
  .source-tooltip {
    display: inline-block;
    background: rgba(129,140,248,.15);
    border: 1px solid rgba(129,140,248,.3);
    color: #a5b4fc;
    border-radius: 12px;
    padding: .08rem .5rem;
    font-size: .65rem;
    margin-left: .4rem;
    vertical-align: middle;
    font-weight: 600;
    cursor: help;
    position: relative;
  }

  .source-tooltip:hover::after {
    content: attr(data-tooltip);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    background: #1e2530;
    border: 1px solid #30363d;
    color: #cbd5e1;
    padding: .5rem .75rem;
    border-radius: 8px;
    font-size: .7rem;
    white-space: pre-line;
    z-index: 1000;
    min-width: 200px;
    max-width: 350px;
    box-shadow: 0 4px 12px rgba(0,0,0,.4);
    margin-bottom: .5rem;
  }

  /* ── Exchange divider ─────────────────────────────────────────────────── */
  .exchange-divider {
    border: none; border-top: 1px solid #21262d;
    margin: .6rem 0 1rem;
  }

  /* ── Text input ───────────────────────────────────────────────────────── */
  .stTextInput input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    padding: .65rem 1rem !important;
    font-size: .93rem !important;
    transition: border-color .15s, box-shadow .15s;
  }
  .stTextInput input:focus {
    border-color: #818cf8 !important;
    box-shadow: 0 0 0 2px rgba(129,140,248,.18) !important;
    outline: none !important;
  }
  .stTextInput input::placeholder { color: #3d4a5c !important; }

  /* ── Selectbox ────────────────────────────────────────────────────────── */
  .stSelectbox > div > div {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
  }
  .stSelectbox [data-baseweb="select"] { background: #161b22 !important; }
  .stSelectbox svg { fill: #64748b !important; }

  /* ── Buttons (shared) ─────────────────────────────────────────────────── */
  .stButton > button {
    width: 100% !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: .9rem !important;
    padding: .62rem 1rem !important;
    letter-spacing: .02em;
    transition: opacity .15s, transform .1s !important;
    cursor: pointer;
  }
  .stButton > button:active { transform: scale(.98) !important; }

  /* Send (first column) */
  div[data-testid="column"]:nth-child(1) .stButton > button {
    background: linear-gradient(135deg, #4338ca, #7c3aed) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 2px 12px rgba(99,102,241,.35) !important;
  }
  div[data-testid="column"]:nth-child(1) .stButton > button:hover { opacity: .88 !important; }

  /* Clear (second column) */
  div[data-testid="column"]:nth-child(2) .stButton > button {
    background: #161b22 !important;
    color: #64748b !important;
    border: 1px solid #30363d !important;
  }
  div[data-testid="column"]:nth-child(2) .stButton > button:hover {
    border-color: #64748b !important;
    color: #94a3b8 !important;
  }

  /* ── Spinner ──────────────────────────────────────────────────────────── */
  div[data-testid="stSpinner"] p { color: #64748b !important; font-size: .88rem; }
</style>
"""
