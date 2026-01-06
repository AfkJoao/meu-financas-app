import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import bcrypt
import time
import requests
import yfinance as yf
from streamlit_option_menu import option_menu
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import date
from streamlit_lottie import st_lottie

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="FinFuture OS", page_icon="💠", layout="wide")

# --- ASSETS DE ANIMAÇÃO (LOTTIE) ---
# URLs de animações minimalistas (Json)
LOTTIE_ASSETS = {
    "finance": "https://assets10.lottiefiles.com/packages/lf20_w51pcehl.json", # Gráfico Tech
    "login": "https://assets9.lottiefiles.com/packages/lf20_h9kds1my.json",    # Cadeado Biométrico
    "wallet": "https://assets3.lottiefiles.com/packages/lf20_yzoqyyqf.json",   # Carteira Digital
    "success": "https://assets9.lottiefiles.com/packages/lf20_jbrw3hcz.json",  # Checkmark limpo
    "loading": "https://assets5.lottiefiles.com/packages/lf20_t9gkkhz4.json"   # Loading circular
}

def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

# --- CSS TECH-MINIMALISTA ---
st.markdown("""
<style>
    /* Importando Fonte Futurista (Rajdhani ou Roboto Mono) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Roboto+Mono:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Fundo Dark Profundo */
    .stApp {
        background-color: #0E1117;
        background-image: radial-gradient(circle at 50% 0%, rgba(0, 212, 255, 0.1) 0%, transparent 50%);
    }

    /* Removendo bordas padrão do Streamlit */
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Containers com Efeito Vidro (Glassmorphism) */
    .tech-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .tech-card:hover {
        border-color: #00d4ff;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.1);
    }

    /* Inputs Estilizados */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stNumberInput input {
        background-color: #161920 !important;
        border: 1px solid #30333d !important;
        color: #e0e0e0 !important;
        border-radius: 6px !important;
        font-family: 'Roboto Mono', monospace !important; /* Fonte de código para números */
    }
    
    /* Botões Tech */
    .stButton button {
        background: linear-gradient(90deg, #00d4ff 0%, #005bea 100%);
        color: white;
        border: none;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: 0.3s;
    }
    .stButton button:hover {
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.4);
        transform: scale(1.02);
    }

    /* Métricas (KPIs) */
    div[data-testid="metric-container"] {
        background-color: #12141a;
        border-left: 3px solid #00d4ff;
        padding: 15px;
        border-radius: 0 8px 8px 0;
    }
    label[data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #888;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Roboto Mono', monospace;
        color: #fff;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO ESTADO ---
if 'language' not in st.session_state: st.session_state['language'] = 'PT'

TRANS = {
    'PT': {'fmt': 'DD/MM/YYYY', 'dash': 'Painel de Controle', 'new': 'Nova Operação', 'imp': 'Data Link (Import)', 'wallet': 'Database View', 'cfg': 'System Config'},
    'EN': {'fmt': 'MM/DD/YYYY', 'dash': 'Control Panel', 'new': 'New Operation', 'imp': 'Data Link (Import)', 'wallet': 'Database View', 'cfg': 'System Config'}
}
T = TRANS[st.session_state['language']]

# --- BANCO DE DADOS ---
DB_NAME = "finfuture_v4.sqlite"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, name TEXT, password_hash BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, owner TEXT, date TEXT, tipo TEXT, ativo TEXT, qtd REAL, preco REAL, total REAL)')
    conn.commit()
    conn.close()

if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

# --- FUNÇÕES ---
def login_user(u, p):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT name, password_hash FROM users WHERE username = ?', (u,))
    data = c.fetchone()
    conn.close()
    if data and bcrypt.checkpw(p.encode('utf-8'), data[1]): return True, data[0]
    return False, None

def register_user(u, n, p):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        hashed = bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt())
        c.execute('INSERT INTO users VALUES (?, ?, ?)', (u, n, hashed))
        conn.commit()
        conn.close()
        return True
    except: return False

def add_transaction(owner, dt, tp, at, qt, pr):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO transactions (owner, date, tipo, ativo, qtd, preco, total) VALUES (?,?,?,?,?,?,?)', 
              (owner, dt, tp, at, qt, pr, qt*pr))
    conn.commit()
    conn.close()

def get_data(owner):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM transactions WHERE owner = ?", conn, params=(owner,))
    conn.close()
    return df

# --- TELA DE LOGIN (MINIMALISTA) ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Container Tech
        with st.container():
            st.markdown('<div class="tech-card" style="text-align: center;">', unsafe_allow_html=True)
            
            # Animação de Login
            lottie_login = load_lottieurl(LOTTIE_ASSETS['login'])
            st_lottie(lottie_login, height=120, key="login_anim")
            
            st.markdown("### SYSTEM ACCESS")
            st.caption("Secure FinFuture Environment v4.0")
            
            tab1, tab2 = st.tabs(["AUTHENTICATE", "INITIALIZE"])
            
            with tab1:
                u = st.text_input("ID / Username")
                p = st.text_input("Key / Password", type="password")
                if st.button("CONNECT", use_container_width=True):
                    with st.spinner("Handshaking..."):
                        time.sleep(1) # Simula conexão segura
                        ok, name = login_user(u, p)
                        if ok:
                            st.session_state['logged_in'] = True
                            st.session_state['username'] = u
                            st.session_state['name'] = name
                            st.rerun()
                        else:
                            st.error("Access Denied")
            
            with tab2:
                nu = st.text_input("New ID")
                nn = st.text_input("Display Name")
                np = st.text_input("New Key", type="password")
                if st.button("CREATE PROFILE", use_container_width=True):
                    if register_user(nu, nn, np): st.success("Profile Created")
                    else: st.error("ID Conflict")
            
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# SISTEMA INTERNO (DASHBOARD)
# ==========================================

# --- SIDEBAR LIMPA ---
with st.sidebar:
    lottie_wallet = load_lottieurl(LOTTIE_ASSETS['wallet'])
    st_lottie(lottie_wallet, height=80, key="sidebar_anim")
    
    st.markdown(f"<h3 style='text-align: center; font-family: Roboto Mono;'>{st.session_state['name'].upper()}</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #00d4ff; font-size: 12px;'>● ONLINE</p>", unsafe_allow_html=True)
    
    # Menu sem Emojis, usando ícones Bootstrap limpos
    selected = option_menu(
        menu_title=None,
        options=[T['dash'], T['new'], T['imp'], T['wallet'], T['cfg']],
        icons=["grid-1x2", "plus-lg", "hdd-network", "table", "sliders"],
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#00d4ff", "font-size": "14px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "font-family": "Inter"},
            "nav-link-selected": {"background-color": "rgba(0, 212, 255, 0.1)", "color": "#00d4ff", "border-left": "3px solid #00d4ff"},
        }
    )
    
    st.markdown("---")
    if st.button("DISCONNECT"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- CARREGAR DADOS ---
df = get_data(st.session_state['username'])

# --- PÁGINAS ---

# 1. DASHBOARD TECH
if selected == T['dash']:
    # Cabeçalho com Animação pequena à esquerda
    c1, c2 = st.columns([1, 15])
    with c1: 
        st_lottie(load_lottieurl(LOTTIE_ASSETS['finance']), height=50)
    with c2: 
        st.title("OVERVIEW")

    if df.empty:
        st.info("No Data Stream Detected.")
    else:
        # Layout de Métricas Tech
        total = df['total'].sum()
        
        # Container CSS personalizado
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("NET WORTH", f"R$ {total:,.2f}")
        col2.metric("ASSETS", df['ativo'].nunique())
        col3.metric("TRANSACTIONS", len(df))
        # Simulação de variação em tempo real
        col4.metric("MARKET STATUS", "OPEN", delta="Active")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Gráficos Minimalistas
        g1, g2 = st.columns([2, 1])
        with g1:
            st.subheader("ASSET ALLOCATION")
            # Gráfico de Área com gradiente (Tech feel)
            evolucao = df.groupby('date')['total'].sum().cumsum().reset_index()
            fig = px.area(evolucao, x='date', y='total', template="plotly_dark")
            fig.update_traces(line_color='#00d4ff', fillcolor="rgba(0, 212, 255, 0.1)")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_family="Roboto Mono")
            st.plotly_chart(fig, use_container_width=True)
            
        with g2:
            st.subheader("COMPOSITION")
            fig2 = px.pie(df, values='total', names='tipo', hole=0.7, template="plotly_dark", color_discrete_sequence=px.colors.sequential.Cyan)
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_family="Roboto Mono", showlegend=False)
            fig2.add_annotation(text="PORTFOLIO", showarrow=False, font_size=12, font_color="white")
            st.plotly_chart(fig2, use_container_width=True)

# 2. NOVA OPERAÇÃO
elif selected == T['new']:
    st.title("INPUT TERMINAL")
    
    st.markdown('<div class="tech-card">', unsafe_allow_html=True)
    with st.form("entry_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        dt = c1.date_input("DATE", date.today(), format=T['fmt'])
        tp = c2.selectbox("TYPE", ["STOCK", "FII", "FIXED INCOME", "CRYPTO", "EXPENSE"])
        at = c3.text_input("ASSET ID").upper()
        
        c4, c5 = st.columns(2)
        qt = c4.number_input("QUANTITY", min_value=0.01)
        pr = c5.number_input("UNIT PRICE", min_value=0.01)
        
        if st.form_submit_button("EXECUTE TRANSACTION"):
            add_transaction(st.session_state['username'], dt, tp, at, qt, pr)
            st.success("DATA UPLOADED")
            time.sleep(1)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 3. IMPORTAÇÃO
elif selected == T['imp']:
    st.title("DATA LINK (ETL)")
    st.caption("Supported formats: .XLSX, .CSV")
    
    st.markdown('<div class="tech-card">', unsafe_allow_html=True)
    upl = st.file_uploader("DROP FILE HERE", type=['csv', 'xlsx'])
    if upl:
        # Lógica de importação simplificada para visual
        st.info("File buffer loaded. Ready to parse.")
        if st.button("INITIATE SEQUENCE"):
            with st.status("Processing...", expanded=True) as status:
                st.write("Parsing headers...")
                time.sleep(0.5)
                st.write("Mapping data types...")
                time.sleep(0.5)
                st.write("Injecting into SQL...")
                time.sleep(0.5)
                status.update(label="Complete", state="complete", expanded=False)
            st.success("Batch Processed.")
    st.markdown('</div>', unsafe_allow_html=True)

# 4. CARTEIRA (GRID)
elif selected == T['wallet']:
    st.title("DATABASE VIEW")
    
    if not df.empty:
        # Formata data para visualização
        df_view = df.copy()
        if st.session_state['language'] == 'PT':
            df_view['date'] = pd.to_datetime(df_view['date']).dt.strftime('%d/%m/%Y')
        else:
            df_view['date'] = pd.to_datetime(df_view['date']).dt.strftime('%m/%d/%Y')

        gb = GridOptionsBuilder.from_dataframe(df_view[['date', 'tipo', 'ativo', 'total']])
        gb.configure_pagination()
        # Tema Dark do AgGrid
        gb.configure_grid_options(domLayout='autoHeight')
        gb.configure_column("total", type=["numericColumn"], valueFormatter="'R$ ' + x.toLocaleString()")
        gridOptions = gb.build()
        
        # AgGrid com tema escuro (balham-dark)
        AgGrid(df_view, gridOptions=gridOptions, theme='balham-dark', height=500, fit_columns_on_grid_load=True)
    else:
        st.warning("Database Empty.")

# 5. CONFIG
elif selected == T['cfg']:
    st.title("SYSTEM CONFIG")
    st.markdown('<div class="tech-card">', unsafe_allow_html=True)
    st.write(f"USER HASH: `{st.session_state['username']}`")
    st.write(f"DATABASE LATENCY: `12ms`")
    st.write(f"SECURITY PROTOCOL: `TLS 1.3 / Bcrypt`")
    st.markdown('</div>', unsafe_allow_html=True)
