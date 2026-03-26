# Paleta de cores — tema marrom moderno
COLORS = {
    "bg_dark":       "#1a1208",
    "bg_mid":        "#251a0e",
    "bg_card":       "#2e2010",
    "bg_card2":      "#3a2814",
    "border":        "#4a3420",
    "border_bright": "#6b4c2a",
    "brown_main":    "#8b5e3c",
    "brown_light":   "#c4956a",
    "brown_bright":  "#e8b48a",
    "cream":         "#f5e6d3",
    "muted":         "#9a7d65",
    "accent":        "#d4894a",
    "green":         "#7ab87a",
    "red":           "#c0635a",
    "yellow":        "#d4a843",
    "sidebar_bg":    "#120d06",
}

PLOT_BG = COLORS["bg_card"]

def plot_layout(height=300):
    return dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PLOT_BG,
        font=dict(color=COLORS["muted"], family="Lora, serif"),
        margin=dict(l=0, r=0, t=36, b=0),
        height=height,
        xaxis=dict(gridcolor=COLORS["border"], showgrid=True, color=COLORS["muted"]),
        yaxis=dict(gridcolor=COLORS["border"], showgrid=True, color=COLORS["muted"]),
        legend=dict(bgcolor=PLOT_BG, bordercolor=COLORS["border"]),
        title_font=dict(color=COLORS["brown_bright"], size=14),
    )


GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;600;700&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=Inconsolata:wght@600;700&display=swap');

    :root {
        --bg-dark:       #1a1208;
        --bg-mid:        #251a0e;
        --bg-card:       #2e2010;
        --bg-card2:      #3a2814;
        --border:        #4a3420;
        --border-bright: #6b4c2a;
        --brown-main:    #8b5e3c;
        --brown-light:   #c4956a;
        --brown-bright:  #e8b48a;
        --cream:         #f5e6d3;
        --muted:         #9a7d65;
        --accent:        #d4894a;
        --green:         #7ab87a;
        --red:           #c0635a;
        --yellow:        #d4a843;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif !important;
        background-color: var(--bg-dark) !important;
        color: var(--cream) !important;
    }

    .stApp { background-color: var(--bg-dark) !important; }
    .main .block-container { padding-top: 1.8rem; max-width: 1300px; }

    /* ── Sidebar ─────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #120d06 !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * { color: var(--cream) !important; }
    [data-testid="stSidebarNav"] a {
        border-radius: 8px !important;
        transition: background .15s !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: var(--bg-card) !important;
    }

    /* ── Tabs ────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--bg-card) !important;
        border-radius: 10px;
        padding: 4px;
        gap: 3px;
        border: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: var(--muted) !important;
        border-radius: 7px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        font-size: 13px;
        padding: 8px 18px !important;
        transition: all .18s !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--bg-card2) !important;
        color: var(--brown-bright) !important;
        border-bottom: 2px solid var(--accent) !important;
    }
    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background-color: rgba(74,52,32,.4) !important;
        color: var(--brown-light) !important;
    }

    /* ── Inputs & selects ────────────────────────────────── */
    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input {
        background-color: var(--bg-mid) !important;
        color: var(--cream) !important;
        border: 1px solid var(--border-bright) !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        transition: border-color .18s, box-shadow .18s !important;
    }
    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stNumberInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(212,137,74,.2) !important;
        outline: none !important;
    }
    .stTextInput label,
    .stTextArea label,
    .stNumberInput label,
    .stSelectbox label,
    .stRadio label,
    .stDateInput label,
    .stSlider label {
        color: var(--brown-light) !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: .07em !important;
    }

    /* ── Selectbox ───────────────────────────────────────── */
    [data-baseweb="select"] > div {
        background-color: var(--bg-mid) !important;
        border-color: var(--border-bright) !important;
        color: var(--cream) !important;
        border-radius: 8px !important;
    }
    [data-baseweb="popover"] { background: var(--bg-card2) !important; }
    [data-baseweb="option"] { background: var(--bg-card2) !important; color: var(--cream) !important; }
    [data-baseweb="option"]:hover { background: var(--border) !important; }

    /* ── Buttons ─────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, var(--brown-main), var(--accent)) !important;
        color: var(--cream) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-family: 'DM Sans', sans-serif !important;
        letter-spacing: .02em !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--accent), var(--brown-light)) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(212,137,74,.35) !important;
    }
    .stButton > button:active { transform: translateY(0) !important; }

    /* ── Form submit ─────────────────────────────────────── */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, var(--brown-main), var(--accent)) !important;
        color: var(--cream) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-family: 'DM Sans', sans-serif !important;
        letter-spacing: .04em !important;
        padding: 10px 24px !important;
        transition: all 0.2s !important;
    }
    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, var(--accent), var(--brown-light)) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(212,137,74,.4) !important;
    }

    /* ── Toggle ──────────────────────────────────────────── */
    .stToggle [data-baseweb="checkbox"] span {
        background: var(--accent) !important;
    }

    /* ── Checkbox ────────────────────────────────────────── */
    .stCheckbox span[data-baseweb="checkbox"] {
        border-color: var(--border-bright) !important;
    }

    /* ── Radio ───────────────────────────────────────────── */
    .stRadio label { color: var(--cream) !important; }
    .stRadio [data-baseweb="radio"] span { border-color: var(--accent) !important; }
    .stRadio [aria-checked="true"] span { background: var(--accent) !important; }

    /* ── Date input ──────────────────────────────────────── */
    .stDateInput input {
        background: var(--bg-mid) !important;
        color: var(--cream) !important;
        border: 1px solid var(--border-bright) !important;
        border-radius: 8px !important;
    }

    /* ── Slider ──────────────────────────────────────────── */
    .stSlider [data-baseweb="slider"] [data-testid="stThumbValue"] {
        color: var(--accent) !important;
    }
    .stSlider div[data-baseweb="slider"] > div {
        background: var(--border) !important;
    }
    .stSlider div[role="slider"] {
        background: var(--accent) !important;
        border: 2px solid var(--brown-light) !important;
    }

    /* ── Dataframe ───────────────────────────────────────── */
    .stDataFrame {
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    .stDataFrame thead th {
        background: var(--bg-card2) !important;
        color: var(--brown-light) !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: .07em !important;
    }

    /* ── Alerts ──────────────────────────────────────────── */
    .stSuccess { background: rgba(122,184,122,.13) !important; border-color: var(--green) !important; color: #a8d8a8 !important; border-radius: 8px !important; }
    .stError   { background: rgba(192,99,90,.13) !important;  border-color: var(--red) !important;   color: #e8a09a !important; border-radius: 8px !important; }
    .stWarning { background: rgba(212,168,67,.13) !important; border-color: var(--yellow) !important; border-radius: 8px !important; }
    .stInfo    { background: rgba(139,94,60,.1) !important;   border-color: var(--border-bright) !important; border-radius: 8px !important; }

    /* ── Scrollbar ───────────────────────────────────────── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: var(--bg-dark); }
    ::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--brown-main); }

    /* ── Divider ─────────────────────────────────────────── */
    hr { border-color: var(--border) !important; opacity: 0.6; }

    /* ═══════════════════════════════════════════════════════
       COMPONENTES CUSTOMIZADOS GLOBAIS
    ═══════════════════════════════════════════════════════ */

    .page-header {
        font-family: 'Lora', serif;
        font-size: 28px; font-weight: 700;
        color: var(--brown-bright);
        margin-bottom: 4px;
        letter-spacing: -.01em;
    }
    .page-sub {
        font-size: 14px; color: var(--muted); margin-bottom: 22px;
    }

    .section-title {
        font-family: 'Lora', serif;
        font-size: 12px; color: var(--brown-light);
        text-transform: uppercase; letter-spacing: .12em;
        margin: 24px 0 12px; padding-bottom: 8px;
        border-bottom: 1px solid var(--border);
        display: flex; align-items: center; gap: 8px;
    }

    .metric-card {
        background: linear-gradient(145deg, var(--bg-card), var(--bg-card2));
        border: 1px solid var(--border);
        border-top: 2px solid var(--brown-main);
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 10px;
        transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        border-top-color: var(--accent);
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0,0,0,.3);
    }
    .metric-card .m-icon  { font-size: 20px; margin-bottom: 8px; }
    .metric-card .m-label { font-size: 10.5px; color: var(--muted); text-transform: uppercase; letter-spacing: .1em; margin-bottom: 4px; }
    .metric-card .m-value { font-family: 'Inconsolata', monospace; font-size: 24px; font-weight: 700; color: var(--brown-bright); }
    .metric-card .m-delta { font-size: 11px; color: var(--border-bright); margin-top: 4px; }

    .alert-card {
        background: rgba(192,99,90,.1);
        border: 1px solid rgba(192,99,90,.28);
        border-left: 3px solid var(--red);
        border-radius: 8px;
        padding: 10px 14px; margin-bottom: 6px;
        color: #e8a09a; font-size: 13.5px;
    }
    .alert-card strong { color: var(--red); }

    .id-badge {
        display: inline-block;
        background: var(--bg-card2);
        border: 1px solid var(--border-bright);
        border-radius: 4px;
        padding: 1px 8px;
        font-family: 'Inconsolata', monospace;
        font-size: 12px;
        color: var(--brown-light);
        margin-right: 6px;
    }

    .badge-ok {
        background: rgba(122,184,122,.12); color: var(--green);
        border: 1px solid rgba(122,184,122,.28);
        border-radius: 4px; font-size: 10px; font-weight: 700; padding: 2px 7px;
    }
    .badge-low {
        background: rgba(212,168,67,.12); color: var(--yellow);
        border: 1px solid rgba(212,168,67,.28);
        border-radius: 4px; font-size: 10px; font-weight: 700; padding: 2px 7px;
    }
    .badge-crit {
        background: rgba(192,99,90,.12); color: var(--red);
        border: 1px solid rgba(192,99,90,.28);
        border-radius: 4px; font-size: 10px; font-weight: 700; padding: 2px 7px;
    }

    .prod-row {
        background: linear-gradient(145deg,#2e2010,#3a2814);
        border: 1px solid #4a3420; border-radius: 10px;
        padding: 11px 14px;
        display: flex; align-items: center; gap: 12px;
        transition: border-color .18s, box-shadow .18s;
    }
    .prod-row:hover { border-color: var(--brown-main); box-shadow: 0 2px 12px rgba(139,94,60,.18); }
    .prod-row-icon {
        width: 36px; height: 36px; border-radius: 8px; flex-shrink: 0;
        background: linear-gradient(135deg,#4a3420,#6b4c2a);
        display: flex; align-items: center; justify-content: center; font-size: 16px;
    }
    .prod-row-name { font-weight: 600; font-size: 13.5px; color: var(--brown-bright); }
    .prod-row-meta { font-size: 11px; color: var(--muted); margin-top: 1px; }
    .prod-row-qty  { font-family: 'Inconsolata', monospace; font-size: 13px; color: var(--brown-light);
                     flex-shrink: 0; min-width: 80px; text-align: right; margin-left: auto; }

    .edit-panel {
        background: linear-gradient(135deg,#251a0e,#2e2010);
        border: 1px solid #6b4c2a; border-left: 3px solid var(--accent);
        border-radius: 10px; padding: 20px; margin: 4px 0 8px;
    }

    /* ── Download button ──────────────────────────────────── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--bg-card), var(--bg-card2)) !important;
        color: var(--brown-light) !important;
        border: 1px solid var(--border-bright) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    .stDownloadButton > button:hover {
        border-color: var(--accent) !important;
        color: var(--brown-bright) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Form container ──────────────────────────────────── */
    [data-testid="stForm"] {
        background: linear-gradient(145deg, #1f1508, #251a0e) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }
</style>
"""
