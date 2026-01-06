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
from datetime import date, datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="FinFuture Global", page_icon="🌍", layout="wide")

# --- CSS PRO ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1e2024 0%, #0f1012 100%);
        color: #FFFFFF;
    }
    .auth-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 30px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    /* Forçar cor escura nos inputs de data */
    input[type="text"] {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- GERENCIAMENTO DE ESTADO E IDIOMA ---
if 'language' not in st.session_state:
    st.session_state['language'] = 'PT'

# Dicionário de Traduções
TRANS = {
    'PT': {
        'date_fmt': 'DD/MM/YYYY', # Formato para o Streamlit
        'welcome': 'Bem-vindo ao FinFuture',
        'login_btn': 'Acessar Dashboard',
        'signup_btn': 'Registrar Agora',
        'user_lbl': 'Usuário',
        'pass_lbl': 'Senha',
        'dash': 'Dashboard',
        'new': 'Novo Aporte',
        'wallet': 'Minha Carteira',
        'config': 'Configurações',
        'logout': 'Sair',
        'total_patr': 'Patrimônio Total',
        'assets': 'Ativos',
        'save_cloud': 'Salvar na Nuvem',
        'success': 'Transação salva com sucesso!',
        'table_header': 'Seus Dados',
        'lang_lbl': 'Idioma / Language'
    },
    'EN': {
        'date_fmt': 'MM/DD/YYYY', # Formato Americano
        'welcome': 'Welcome to FinFuture',
        'login_btn': 'Access Dashboard',
        'signup_btn': 'Register Now',
        'user_lbl': 'Username',
        'pass_lbl': 'Password',
        'dash': 'Dashboard',
        'new': 'New Entry',
        'wallet': 'My Wallet',
        'config': 'Settings',
        'logout': 'Logout',
        'total_patr': 'Total Net Worth',
        'assets': 'Assets',
        'save_cloud': 'Save to Cloud',
        'success': 'Transaction saved successfully!',
        'table_header': 'Your Data',
        'lang_lbl': 'Language'
    }
}

T = TRANS[st.session_state['language']]

# --- BANCO DE DADOS (SQLITE) ---
DB_NAME = "finfuture_v2.sqlite"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password_hash BLOB NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            date TEXT,
            tipo TEXT,
            ativo TEXT,
            qtd REAL,
            preco REAL,
            total REAL,
            FOREIGN KEY(owner) REFERENCES users(username)
        )
    ''')
    conn.commit()
    conn.close()

# --- FUNÇÕES DE SEGURANÇA ---
def register_user(username, name, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT username FROM users WHERE username = ?', (username,))
    if c.fetchone():
        conn.close()
        return False, "User already exists/Usuário já existe"
    
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    
    c.execute('INSERT INTO users (username, name, password_hash) VALUES (?, ?, ?)', 
              (username, name, hashed))
    conn.commit()
    conn.close()
    return True, "OK"

def login_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT name, password_hash FROM users WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    if data:
        stored_name, stored_hash = data
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return True, stored_name
    return False, None

# --- FUNÇÕES DE DADOS ---
def get_user_data(username):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM transactions WHERE owner = ?", conn, params=(username,))
    conn.close()
    return df

def add_transaction(username, date_val, tipo, ativo, qtd, preco):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    total = qtd * preco
    # Salva sempre em formato ISO (YYYY-MM-DD) no banco para não bagunçar ordenação
    c.execute('''
        INSERT INTO transactions (owner, date, tipo, ativo, qtd, preco, total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, date_val, tipo, ativo, qtd, preco, total))
    conn.commit()
    conn.close()

# --- INICIALIZAÇÃO ---
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

# --- LOGIN SCREEN ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/12586/12586638.png", width=80)
        st.title("FinFuture Global")
        
        # Seletor de Idioma no Login
        lang_choice = st.radio("Language / Idioma", ["PT", "EN"], horizontal=True)
        st.session_state['language'] = lang_choice
        T = TRANS[lang_choice] # Atualiza tradução na hora
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            with st.form("login"):
                u = st.text_input(T['user_lbl'])
                p = st.text_input(T['pass_lbl'], type="password")
                if st.form_submit_button(T['login_btn'], type="primary"):
                    ok, name = login_user(u, p)
                    if ok:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = u
                        st.session_state['name'] = name
                        st.rerun()
                    else:
                        st.error("Error/Erro")
        
        with tab2:
            with st.form("signup"):
                nu = st.text_input(T['user_lbl'])
                nn = st.text_input("Name/Nome")
                np = st.text_input(T['pass_lbl'], type="password")
                if st.form_submit_button(T['signup_btn']):
                    ok, msg = register_user(nu, nn, np)
                    if ok:
                        st.success("Account created! Log in now.")
                    else:
                        st.error(msg)
    st.stop()

# ==========================================
# ÁREA LOGADA
# ==========================================

# --- SIDEBAR COM CONFIGURAÇÃO ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['name']}")
    
    # Seletor de Idioma Persistente
    new_lang = st.selectbox(T['lang_lbl'], ["PT", "EN"], index=0 if st.session_state['language']=='PT' else 1)
    if new_lang != st.session_state['language']:
        st.session_state['language'] = new_lang
        st.rerun() # Recarrega a página para aplicar o idioma novo
        
    T = TRANS[st.session_state['language']] # Garante tradução atualizada

    menu_opts = [T['dash'], T['new'], T['wallet'], T['config']]
    selected = option_menu(
        menu_title=None,
        options=menu_opts,
        icons=["speedometer2", "plus-circle", "wallet2", "gear"],
        styles={"nav-link-selected": {"background-color": "#00d4ff", "color": "black"}}
    )
    
    st.markdown("---")
    if st.button(T['logout']):
        st.session_state['logged_in'] = False
        st.rerun()

df = get_user_data(st.session_state['username'])

# --- PÁGINAS ---

if selected == T['dash']:
    st.title(f"📊 {T['dash']}")
    if df.empty:
        st.info("No data yet / Sem dados ainda.")
    else:
        total = df['total'].sum()
        col1, col2 = st.columns(2)
        col1.metric(T['total_patr'], f"R$ {total:,.2f}")
        col2.metric(T['assets'], df['ativo'].nunique())
        
        fig = px.bar(df, x='ativo', y='total', color='tipo')
        st.plotly_chart(fig, use_container_width=True)

elif selected == T['new']:
    st.header(f"💸 {T['new']}")
    with st.form("new_entry", clear_on_submit=True):
        c1, c2 = st.columns(2)
        
        # --- A MÁGICA DA DATA AQUI ---
        # O formato muda dinamicamente baseado no T['date_fmt'] (DD/MM/YYYY ou MM/DD/YYYY)
        data_op = c1.date_input("Data / Date", date.today(), format=T['date_fmt'])
        
        tipo = c2.selectbox("Tipo / Type", ["Ação", "FII", "CDB", "Tesouro", "Crypto"])
        ativo = st.text_input("Ticker (Ex: AAPL, VALE3)").upper()
        
        c3, c4 = st.columns(2)
        qtd = c3.number_input("Qtd", min_value=0.01)
        preco = c4.number_input("Preço / Price", min_value=0.01)
        
        if st.form_submit_button(T['save_cloud'], type="primary"):
            add_transaction(st.session_state['username'], data_op, tipo, ativo, qtd, preco)
            st.success(T['success'])
            time.sleep(1)
            st.rerun()

elif selected == T['wallet']:
    st.header(f"🗂️ {T['table_header']}")
    
    if not df.empty:
        # Preparar dataframe para visualização (Formatar Data)
        df_view = df.copy()
        
        # Converte a data salva (YYYY-MM-DD) para o formato do país
        if st.session_state['language'] == 'PT':
            # Converte para DD/MM/YYYY
            df_view['date'] = pd.to_datetime(df_view['date']).dt.strftime('%d/%m/%Y')
        else:
            # Converte para MM/DD/YYYY
            df_view['date'] = pd.to_datetime(df_view['date']).dt.strftime('%m/%d/%Y')

        # Configurar AgGrid
        gb = GridOptionsBuilder.from_dataframe(df_view[['date', 'tipo', 'ativo', 'qtd', 'preco', 'total']])
        gb.configure_pagination()
        gb.configure_column("total", type=["numericColumn"], valueFormatter="'R$ ' + x.toLocaleString()")
        gb.configure_column("date", header_name="Data (Local)")
        gridOptions = gb.build()
        
        AgGrid(df_view, gridOptions=gridOptions, fit_columns_on_grid_load=True, theme='alpine', height=400)
    else:
        st.warning("Empty / Vazio")

elif selected == T['config']:
    st.header(f"⚙️ {T['config']}")
    st.write(f"User: {st.session_state['username']}")
    st.info(f"Current Region Mode: {st.session_state['language']}")
