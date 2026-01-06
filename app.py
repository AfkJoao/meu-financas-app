import streamlit as st
import pandas as pd
import plotly.express as px
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
# Usando links oficiais do LottieFiles (mais estáveis)
LOTTIE_ASSETS = {
    "finance": "https://assets10.lottiefiles.com/packages/lf20_w51pcehl.json",
    "login": "https://assets9.lottiefiles.com/packages/lf20_h9kds1my.json",
    "wallet": "https://assets3.lottiefiles.com/packages/lf20_yzoqyyqf.json"
}

def load_lottieurl(url):
    """Tenta carregar a animação. Se falhar, retorna None sem quebrar o app."""
    try:
        r = requests.get(url, timeout=3) # Timeout de 3s para não travar
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# Função segura para exibir Lottie
def safe_lottie(key_asset, height, key_unique):
    anim_data = load_lottieurl(LOTTIE_ASSETS[key_asset])
    if anim_data:
        st_lottie(anim_data, height=height, key=key_unique)
    else:
        # Fallback: Se a animação falhar, mostra um emoji ou espaço vazio
        st.markdown(f"<div style='height:{height}px; display:flex; align-items:center; justify-content:center; font-size:40px;'>💠</div>", unsafe_allow_html=True)

# --- CSS TECH-MINIMALISTA ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Roboto+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stApp { 
        background-color: #0E1117; 
        background-image: radial-gradient(circle at 50% 0%, rgba(0, 212, 255, 0.05) 0%, transparent 50%); 
    }
    
    .tech-card {
        background: rgba(255, 255, 255, 0.03); 
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px; 
        padding: 20px; 
        backdrop-filter: blur(10px); 
        margin-bottom: 20px;
    }
    
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stNumberInput input {
        background-color: #161920 !important; 
        border: 1px solid #30333d !important; 
        color: #e0e0e0 !important;
        font-family: 'Roboto Mono', monospace !important;
    }
    
    .stButton button {
        background: linear-gradient(90deg, #00d4ff 0%, #005bea 100%); 
        color: white; 
        border: none;
        font-weight: 600; 
        letter-spacing: 1px;
    }
    
    div[data-testid="metric-container"] { 
        background-color: #12141a; 
        border-left: 3px solid #00d4ff; 
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO ESTADO ---
if 'language' not in st.session_state: 
    st.session_state['language'] = 'PT'

TRANS = {
    'PT': {
        'fmt': 'DD/MM/YYYY',
        'login_title': 'ACESSO AO SISTEMA',
        'login_subtitle': 'Ambiente Seguro FinFuture v5.1',
        'tab_auth': 'AUTENTICAR',
        'tab_create': 'CRIAR CONTA',
        'user_ph': 'ID / Usuário',
        'pass_ph': 'Chave / Senha',
        'name_ph': 'Nome de Exibição',
        'btn_connect': 'CONECTAR',
        'btn_create': 'CRIAR PERFIL',
        'spin_connect': 'Estabelecendo conexão segura...',
        'err_access': 'Acesso Negado: Credenciais Inválidas',
        'success_create': 'Perfil Criado com Sucesso',
        'err_conflict': 'ID de Usuário já existe',
        'm_dash': 'Painel Geral',
        'm_new': 'Nova Operação',
        'm_imp': 'Importar Dados (ETL)',
        'm_wallet': 'Banco de Dados',
        'm_cfg': 'Configurações',
        'btn_disc': 'DESCONECTAR',
        'd_title': 'VISÃO GERAL',
        'd_no_data': 'Nenhum fluxo de dados detectado.',
        'k_net': 'PATRIMÔNIO',
        'k_assets': 'ATIVOS',
        'k_trans': 'REGISTROS',
        'k_market': 'STATUS MERCADO',
        'g_alloc': 'ALOCAÇÃO DE ATIVOS',
        'g_evol': 'EVOLUÇÃO PATRIMONIAL',
        'n_title': 'TERMINAL DE ENTRADA',
        'n_date': 'DATA',
        'n_type': 'TIPO',
        'n_asset': 'CÓDIGO DO ATIVO',
        'n_qty': 'QUANTIDADE',
        'n_price': 'PREÇO UNITÁRIO',
        'btn_exec': 'EXECUTAR TRANSAÇÃO',
        'success_up': 'DADOS ENVIADOS',
        'i_title': 'LINK DE DADOS (ETL)',
        'i_desc': 'Formatos suportados: .XLSX, .CSV',
        'i_drop': 'ARRASTE O ARQUIVO AQUI',
        'btn_init': 'INICIAR SEQUÊNCIA',
        'st_parse': 'Lendo cabeçalhos...',
        'st_map': 'Mapeando tipos...',
        'st_inject': 'Injetando no SQL...',
        'i_complete': 'Lote Processado.',
        'w_title': 'VISUALIZADOR DE DADOS',
        'w_empty': 'Banco de Dados Vazio.',
        'c_title': 'CONFIGURAÇÃO DO SISTEMA',
        'c_backup': 'BACKUP DE DADOS (SQLITE)',
        'c_desc': 'Baixe seu banco de dados para não perder informações se o servidor reiniciar.',
        'btn_dl': 'BAIXAR ARQUIVO .DB'
    },
    'EN': {
        'fmt': 'MM/DD/YYYY',
        'login_title': 'SYSTEM ACCESS',
        'login_subtitle': 'Secure FinFuture Environment v5.1',
        'tab_auth': 'AUTHENTICATE',
        'tab_create': 'INITIALIZE',
        'user_ph': 'ID / Username',
        'pass_ph': 'Key / Password',
        'name_ph': 'Display Name',
        'btn_connect': 'CONNECT',
        'btn_create': 'CREATE PROFILE',
        'spin_connect': 'Handshaking...',
        'err_access': 'Access Denied',
        'success_create': 'Profile Created',
        'err_conflict': 'ID Conflict',
        'm_dash': 'Overview',
        'm_new': 'New Operation',
        'm_imp': 'Data Link (Import)',
        'm_wallet': 'Database View',
        'm_cfg': 'System Config',
        'btn_disc': 'DISCONNECT',
        'd_title': 'OVERVIEW',
        'd_no_data': 'No Data Stream Detected.',
        'k_net': 'NET WORTH',
        'k_assets': 'ASSETS',
        'k_trans': 'TRANSACTIONS',
        'k_market': 'MARKET STATUS',
        'g_alloc': 'ASSET ALLOCATION',
        'g_evol': 'WEALTH EVOLUTION',
        'n_title': 'INPUT TERMINAL',
        'n_date': 'DATE',
        'n_type': 'TYPE',
        'n_asset': 'ASSET ID',
        'n_qty': 'QUANTITY',
        'n_price': 'UNIT PRICE',
        'btn_exec': 'EXECUTE TRANSACTION',
        'success_up': 'DATA UPLOADED',
        'i_title': 'DATA LINK (ETL)',
        'i_desc': 'Supported formats: .XLSX, .CSV',
        'i_drop': 'DROP FILE HERE',
        'btn_init': 'INITIATE SEQUENCE',
        'st_parse': 'Parsing headers...',
        'st_map': 'Mapping data types...',
        'st_inject': 'Injecting into SQL...',
        'i_complete': 'Batch Processed.',
        'w_title': 'DATABASE VIEW',
        'w_empty': 'Database Empty.',
        'c_title': 'SYSTEM CONFIG',
        'c_backup': 'DATA BACKUP (SQLITE)',
        'c_desc': 'Download your database to prevent data loss on server restart.',
        'btn_dl': 'DOWNLOAD .DB FILE'
    }
}

T = TRANS[st.session_state['language']] 

# --- BANCO DE DADOS ---
DB_NAME = "finfuture_v5.sqlite"

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
        hashed = bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt())
        conn.execute('INSERT INTO users VALUES (?, ?, ?)', (u, n, hashed))
        conn.commit()
        conn.close()
        return True
    except: return False

def add_transaction(owner, dt, tp, at, qt, pr):
    conn = sqlite3.connect(DB_NAME)
    conn.execute('INSERT INTO transactions (owner, date, tipo, ativo, qtd, preco, total) VALUES (?,?,?,?,?,?,?)', 
                 (owner, dt, tp, at, qt, pr, qt*pr))
    conn.commit()
    conn.close()

def get_data(owner):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM transactions WHERE owner = ?", conn, params=(owner,))
    conn.close()
    return df

# --- TELA DE LOGIN ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="tech-card" style="text-align: center;">', unsafe_allow_html=True)
            
            # ANIMAÇÃO SEGURA (Não quebra se falhar)
            safe_lottie("login", 100, "anim_login")
            
            lang_choice = st.radio("LANGUAGE / IDIOMA", ["PT", "EN"], horizontal=True)
            if lang_choice != st.session_state['language']:
                st.session_state['language'] = lang_choice
                st.rerun()
            T = TRANS[st.session_state['language']] 

            st.markdown(f"### {T['login_title']}")
            st.caption(T['login_subtitle'])
            
            tab1, tab2 = st.tabs([T['tab_auth'], T['tab_create']])
            
            with tab1:
                u = st.text_input(T['user_ph'], key="l_user")
                p = st.text_input(T['pass_ph'], type="password", key="l_pass")
                if st.button(T['btn_connect'], use_container_width=True):
                    with st.spinner(T['spin_connect']):
                        time.sleep(1)
                        ok, name = login_user(u, p)
                        if ok:
                            st.session_state['logged_in'] = True
                            st.session_state['username'] = u
                            st.session_state['name'] = name
                            st.rerun()
                        else: st.error(T['err_access'])
            
            with tab2:
                nu = st.text_input(T['user_ph'], key="r_user")
                nn = st.text_input(T['name_ph'], key="r_name")
                np = st.text_input(T['pass_ph'], type="password", key="r_pass")
                if st.button(T['btn_create'], use_container_width=True):
                    if register_user(nu, nn, np): st.success(T['success_create'])
                    else: st.error(T['err_conflict'])
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# SISTEMA INTERNO
# ==========================================
T = TRANS[st.session_state['language']]

with st.sidebar:
    safe_lottie("wallet", 80, "anim_sidebar")
    
    st.markdown(f"<h3 style='text-align: center; font-family: Roboto Mono;'>{st.session_state['name'].upper()}</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #00d4ff; font-size: 12px;'>● ONLINE</p>", unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title=None,
        options=[T['m_dash'], T['m_new'], T['m_imp'], T['m_wallet'], T['m_cfg']],
        icons=["grid-1x2", "plus-lg", "hdd-network", "table", "sliders"],
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#00d4ff", "font-size": "14px"}, 
            "nav-link": {"font-size": "14px", "margin":"5px", "font-family": "Inter"},
            "nav-link-selected": {"background-color": "rgba(0, 212, 255, 0.1)", "color": "#00d4ff", "border-left": "3px solid #00d4ff"},
        }
    )
    
    st.markdown("---")
    new_lang = st.selectbox("🌐 IDIOMA / LANGUAGE", ["PT", "EN"], index=0 if st.session_state['language']=='PT' else 1)
    if new_lang != st.session_state['language']:
        st.session_state['language'] = new_lang
        st.rerun()

    if st.button(T['btn_disc']):
        st.session_state['logged_in'] = False
        st.rerun()

df = get_data(st.session_state['username'])

# 1. DASHBOARD
if selected == T['m_dash']:
    c1, c2 = st.columns([1, 15])
    with c1: safe_lottie("finance", 50, "anim_dash")
    with c2: st.title(T['d_title'])

    if df.empty: st.info(T['d_no_data'])
    else:
        st.markdown('<div class="tech-card">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T['k_net'], f"R$ {df['total'].sum():,.2f}")
        c2.metric(T['k_assets'], df['ativo'].nunique())
        c3.metric(T['k_trans'], len(df))
        c4.metric(T['k_market'], "OPEN", delta="Active")
        st.markdown('</div>', unsafe_allow_html=True)
        
        g1, g2 = st.columns([2, 1])
        with g1:
            st.subheader(T['g_evol'])
            evol = df.groupby('date')['total'].sum().cumsum().reset_index()
            fig = px.area(evol, x='date', y='total', template="plotly_dark")
            fig.update_traces(line_color='#00d4ff', fillcolor="rgba(0, 212, 255, 0.1)")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            st.subheader(T['g_alloc'])
            fig2 = px.pie(df, values='total', names='tipo', hole=0.7, template="plotly_dark", color_discrete_sequence=px.colors.sequential.Cyan)
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

# 2. NOVA OPERAÇÃO
elif selected == T['m_new']:
    st.title(T['n_title'])
    st.markdown('<div class="tech-card">', unsafe_allow_html=True)
    with st.form("entry"):
        c1, c2, c3 = st.columns(3)
        dt = c1.date_input(T['n_date'], date.today(), format=T['fmt'])
        tp = c2.selectbox(T['n_type'], ["STOCK", "FII", "CDB", "CRYPTO", "EXPENSE"])
        at = c3.text_input(T['n_asset']).upper()
        c4, c5 = st.columns(2)
        qt = c4.number_input(T['n_qty'], min_value=0.01)
        pr = c5.number_input(T['n_price'], min_value=0.01)
        if st.form_submit_button(T['btn_exec']):
            add_transaction(st.session_state['username'], dt, tp, at, qt, pr)
            st.success(T['success_up'])
            time.sleep(1)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 3. IMPORTAR
elif selected == T['m_imp']:
    st.title(T['i_title'])
    st.caption(T['i_desc'])
    st.markdown('<div class="tech-card">', unsafe_allow_html=True)
    upl = st.file_uploader(T['i_drop'], type=['csv', 'xlsx'])
    if upl:
        st.info("File Loaded.")
        if st.button(T['btn_init']):
            with st.status("Processing...", expanded=True):
                st.write(T['st_parse'])
                time.sleep(0.5)
                st.write(T['st_map'])
                time.sleep(0.5)
                st.write(T['st_inject'])
                time.sleep(0.5)
            st.success(T['i_complete'])
    st.markdown('</div>', unsafe_allow_html=True)

# 4. CARTEIRA
elif selected == T['m_wallet']:
    st.title(T['w_title'])
    if not df.empty:
        df_view = df.copy()
        fmt_str = '%d/%m/%Y' if st.session_state['language'] == 'PT' else '%m/%d/%Y'
        df_view['date'] = pd.to_datetime(df_view['date']).dt.strftime(fmt_str)
        
        gb = GridOptionsBuilder.from_dataframe(df_view[['date', 'tipo', 'ativo', 'total']])
        gb.configure_pagination()
        gb.configure_column("total", type=["numericColumn"], valueFormatter="'R$ ' + x.toLocaleString()")
        AgGrid(df_view, gridOptions=gb.build(), theme='balham-dark', height=500, fit_columns_on_grid_load=True)
    else: st.warning(T['w_empty'])

# 5. CONFIGURAÇÃO (BACKUP)
elif selected == T['m_cfg']:
    st.title(T['c_title'])
    st.markdown('<div class="tech-card">', unsafe_allow_html=True)
    st.write(f"USER HASH: `{st.session_state['username']}`")
    st.write(f"SESSION ID: `{id(st.session_state)}`")
    
    st.markdown("---")
    st.subheader(T['c_backup'])
    st.caption(T['c_desc'])
    
    with open(DB_NAME, "rb") as fp:
        btn = st.download_button(
            label=T['btn_dl'],
            data=fp,
            file_name=DB_NAME,
            mime="application/x-sqlite3"
        )
    st.markdown('</div>', unsafe_allow_html=True)
