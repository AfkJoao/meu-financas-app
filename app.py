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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="FinFuture Cloud", page_icon="☁️", layout="wide")

# --- CSS PRO (GLASSMORPHISM & LOGIN) ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1e2024 0%, #0f1012 100%);
        color: #FFFFFF;
    }
    .auth-container {
        max-width: 400px;
        margin: auto;
        padding: 30px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    h1, h2, h3 { font-family: 'Inter', sans-serif; }
    .stButton button { width: 100%; border-radius: 5px; font-weight: bold; transition: 0.3s; }
    .stButton button:hover { transform: scale(1.02); }
</style>
""", unsafe_allow_html=True)

# --- GERENCIAMENTO DE BANCO DE DADOS (SQLITE) ---
DB_NAME = "finfuture_db.sqlite"

def init_db():
    """Cria as tabelas se elas não existirem"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabela de Usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password_hash BLOB NOT NULL
        )
    ''')
    
    # Tabela de Transações (Com chave estrangeira para o dono)
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

# --- FUNÇÕES DE SEGURANÇA E AUTH ---
def register_user(username, name, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Verifica se usuário existe
    c.execute('SELECT username FROM users WHERE username = ?', (username,))
    if c.fetchone():
        conn.close()
        return False, "Usuário já existe!"
    
    # Criptografa a senha
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    
    c.execute('INSERT INTO users (username, name, password_hash) VALUES (?, ?, ?)', 
              (username, name, hashed))
    conn.commit()
    conn.close()
    return True, "Conta criada com sucesso!"

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

# --- FUNÇÕES DE DADOS (AGORA COM SQL) ---
def get_user_data(username):
    conn = sqlite3.connect(DB_NAME)
    # Puxa APENAS os dados do usuário logado
    df = pd.read_sql_query("SELECT * FROM transactions WHERE owner = ?", conn, params=(username,))
    conn.close()
    return df

def add_transaction(username, date_val, tipo, ativo, qtd, preco):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    total = qtd * preco
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

# --- TELA DE LOGIN / REGISTRO ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    col_center = st.columns([1, 1, 1])
    
    with col_center[1]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/12586/12586638.png", width=80)
        st.title("FinFuture Access")
        
        tab_login, tab_signup = st.tabs(["Entrar", "Criar Conta"])
        
        with tab_login:
            with st.form("login_form"):
                user = st.text_input("Usuário")
                pwd = st.text_input("Senha", type="password")
                btn_login = st.form_submit_button("Acessar Dashboard", type="primary")
                
                if btn_login:
                    success, name = login_user(user, pwd)
                    if success:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = user
                        st.session_state['name'] = name
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")

        with tab_signup:
            with st.form("signup_form"):
                new_user = st.text_input("Escolha um Usuário (Login)")
                new_name = st.text_input("Seu Nome Completo")
                new_pwd = st.text_input("Escolha uma Senha", type="password")
                new_pwd2 = st.text_input("Confirme a Senha", type="password")
                btn_reg = st.form_submit_button("Registrar Agora")
                
                if btn_reg:
                    if new_pwd != new_pwd2:
                        st.error("As senhas não coincidem!")
                    elif len(new_pwd) < 4:
                        st.error("Senha muito curta.")
                    else:
                        success, msg = register_user(new_user, new_name, new_pwd)
                        if success:
                            st.success(msg)
                            time.sleep(1)
                            st.info("Faça login na aba ao lado.")
                        else:
                            st.error(msg)
    
    st.stop() # Para o código aqui se não estiver logado

# =========================================================
#  ÁREA RESTRITA (DASHBOARD DO USUÁRIO LOGADO)
# =========================================================

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['name']}")
    st.caption(f"ID: @{st.session_state['username']}")
    
    # Clima (Simulado por IP para não travar)
    st.markdown("---")
    try:
        ip_data = requests.get("http://ip-api.com/json/", timeout=2).json()
        st.caption(f"📍 {ip_data.get('city', 'Local')} | ⛅ 24°C")
    except:
        st.caption("📍 Brasil | ⛅ --°C")
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Novo Aporte", "Minha Carteira", "Configurações"],
        icons=["columns-gap", "plus-circle", "wallet2", "gear"],
        styles={"nav-link-selected": {"background-color": "#00d4ff", "color": "black"}}
    )
    
    st.markdown("---")
    if st.button("Sair (Logout)"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- CARREGA DADOS DO USUÁRIO ---
df = get_user_data(st.session_state['username'])
selic_atual = 11.25 # Poderia vir da API como antes

# --- LÓGICA DAS PÁGINAS ---

# 1. DASHBOARD
if selected == "Dashboard":
    st.title(f"Visão Geral de {st.session_state['name'].split()[0]}")
    
    if df.empty:
        st.info("👋 Sua conta é nova! Vá em 'Novo Aporte' para começar.")
    else:
        investido = df['total'].sum()
        ativos_count = df['ativo'].nunique()
        
        # Simulação de Lucro (Exemplo visual)
        lucro_estimado = investido * 0.05 
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Patrimônio Total", f"R$ {investido:,.2f}")
        c2.metric("Lucro Estimado (+5%)", f"R$ {lucro_estimado:,.2f}", delta="Simulado")
        c3.metric("Ativos", ativos_count)
        
        g1, g2 = st.columns([2, 1])
        with g1:
            fig = px.bar(df, x='ativo', y='total', color='tipo', title="Distribuição por Ativo")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            fig2 = px.pie(df, values='total', names='tipo', hole=0.6, title="Alocação")
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

# 2. NOVO APORTE
elif selected == "Novo Aporte":
    st.header("💸 Registrar Movimentação")
    
    with st.form("transacao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        data_op = col1.date_input("Data", date.today())
        tipo = col2.selectbox("Tipo", ["Ação", "FII", "CDB", "Tesouro"])
        
        ativo = st.text_input("Código (Ex: PETR4, CDB XP)").upper()
        
        c1, c2 = st.columns(2)
        qtd = c1.number_input("Quantidade", min_value=0.01, step=1.0)
        preco = c2.number_input("Preço Unitário", min_value=0.01)
        
        if st.form_submit_button("Salvar na Nuvem", type="primary"):
            add_transaction(st.session_state['username'], data_op, tipo, ativo, qtd, preco)
            st.success("Transação salva com sucesso no seu banco de dados!")
            time.sleep(1)
            st.rerun()

# 3. CARTEIRA (GRID)
elif selected == "Minha Carteira":
    st.header("🗂️ Seus Dados")
    
    if not df.empty:
        gb = GridOptionsBuilder.from_dataframe(df[['date', 'tipo', 'ativo', 'qtd', 'preco', 'total']])
        gb.configure_pagination()
        gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum')
        gb.configure_column("total", type=["numericColumn", "numberColumnFilter", "customCurrencyFormat"], custom_currency_symbol="R$")
        gridOptions = gb.build()
        
        AgGrid(df, gridOptions=gridOptions, theme='alpine', height=400)
    else:
        st.warning("Nenhum dado encontrado.")

# 4. CONFIGURAÇÕES
elif selected == "Configurações":
    st.header("⚙️ Conta")
    st.write(f"**Usuário:** {st.session_state['username']}")
    st.write(f"**Nome:** {st.session_state['name']}")
    st.info("A senha é criptografada no banco de dados. Nem o administrador pode vê-la.")
