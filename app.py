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
st.set_page_config(page_title="FinFuture Enterprise", page_icon="🏢", layout="wide")

# --- CSS PRO (DESIGN SYSTEM) ---
st.markdown("""
<style>
    /* Fundo Gradiente Dark */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #FFFFFF;
    }
    
    /* Login Box Vidro */
    .auth-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 40px;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* Inputs Escuros */
    .stTextInput input, .stSelectbox, .stDateInput {
        color: #fff !important;
    }
    
    /* Métricas Estilizadas */
    div[data-testid="metric-container"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 15px;
        transition: 0.3s;
    }
    div[data-testid="metric-container"]:hover {
        border-color: #00d4ff;
        transform: translateY(-5px);
    }
</style>
""", unsafe_allow_html=True)

# --- GLOBAL STATE (IDIOMA & CONFIG) ---
if 'language' not in st.session_state:
    st.session_state['language'] = 'PT'

TRANS = {
    'PT': {
        'date_fmt': 'DD/MM/YYYY',
        'welcome': 'Bem-vindo ao FinFuture',
        'menu': ["Dashboard", "Novo Lançamento", "Importar Dados", "Carteira", "Configurações"],
        'imp_title': '📥 Importação Inteligente (ETL)',
        'imp_desc': 'Arraste seu extrato (Excel ou CSV) para processar centenas de linhas automaticamente.',
        'col_map': 'Mapeamento de Colunas',
        'btn_proc': 'Processar Arquivo',
        'success_imp': 'Linhas importadas com sucesso!',
        'login_fail': 'Usuário ou senha incorretos.',
        'logout': 'Sair do Sistema'
    },
    'EN': {
        'date_fmt': 'MM/DD/YYYY',
        'welcome': 'Welcome to FinFuture',
        'menu': ["Dashboard", "New Entry", "Import Data", "Wallet", "Settings"],
        'imp_title': '📥 Smart Import (ETL)',
        'imp_desc': 'Drag your bank statement (Excel or CSV) to process hundreds of rows automatically.',
        'col_map': 'Column Mapping',
        'btn_proc': 'Process File',
        'success_imp': 'Rows imported successfully!',
        'login_fail': 'Invalid username or password.',
        'logout': 'Logout'
    }
}
T = TRANS[st.session_state['language']]

# --- BANCO DE DADOS (SQLITE) ---
DB_NAME = "finfuture_enterprise.sqlite"

def init_db():
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
    # Tabela de Transações
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

# --- FUNÇÕES DE SEGURANÇA (AUTH) ---
def register_user(username, name, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        c.execute('INSERT INTO users VALUES (?, ?, ?)', (username, name, hashed))
        conn.commit()
        conn.close()
        return True, "Sucesso!"
    except sqlite3.IntegrityError:
        return False, "Usuário já existe!"

def login_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT name, password_hash FROM users WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    if data:
        if bcrypt.checkpw(password.encode('utf-8'), data[1]):
            return True, data[0]
    return False, None

# --- FUNÇÕES DE DADOS ---
def add_transaction(username, date_val, tipo, ativo, qtd, preco):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    total = qtd * preco
    # Salva sempre ISO (YYYY-MM-DD)
    c.execute('INSERT INTO transactions (owner, date, tipo, ativo, qtd, preco, total) VALUES (?,?,?,?,?,?,?)', 
              (username, date_val, tipo, ativo, qtd, preco, total))
    conn.commit()
    conn.close()

def get_data(username):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM transactions WHERE owner = ?", conn, params=(username,))
    conn.close()
    return df

# --- INICIALIZAÇÃO ---
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

# --- TELA DE LOGIN ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/2432/2432752.png", width=70)
        st.title("FinFuture ID")
        
        # Switch Idioma Login
        lang_login = st.radio("Language", ["PT", "EN"], horizontal=True)
        st.session_state['language'] = lang_login
        T = TRANS[lang_login]

        tab1, tab2 = st.tabs(["Login", "Registrar"])
        
        with tab1:
            with st.form("login_form"):
                u = st.text_input("User/Usuário")
                p = st.text_input("Pass/Senha", type="password")
                if st.form_submit_button("Entrar / Login", type="primary"):
                    ok, name = login_user(u, p)
                    if ok:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = u
                        st.session_state['name'] = name
                        st.rerun()
                    else:
                        st.error(T['login_fail'])
        
        with tab2:
            with st.form("reg_form"):
                nu = st.text_input("Novo Usuário")
                nn = st.text_input("Nome Completo")
                np = st.text_input("Senha", type="password")
                if st.form_submit_button("Criar Conta"):
                    ok, msg = register_user(nu, nn, np)
                    if ok:
                        st.success("Conta criada! Faça login.")
                    else:
                        st.error(msg)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# ÁREA LOGADA (SaaS)
# ==========================================

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9327/9327421.png", width=50)
    st.markdown(f"### Olá, {st.session_state['name'].split()[0]}")
    
    # Seletor Idioma Persistente
    l_idx = 0 if st.session_state['language'] == 'PT' else 1
    new_lang = st.selectbox("Idioma / Language", ["PT", "EN"], index=l_idx)
    if new_lang != st.session_state['language']:
        st.session_state['language'] = new_lang
        st.rerun()
    T = TRANS[st.session_state['language']]
    
    # Menu Principal
    selected = option_menu(
        menu_title=None,
        options=T['menu'],
        icons=["speedometer2", "plus-lg", "cloud-upload", "wallet2", "gear"],
        styles={"nav-link-selected": {"background-color": "#00d4ff", "color": "#000"}}
    )
    
    # Localização
    st.markdown("---")
    try:
        geo = requests.get("http://ip-api.com/json/", timeout=2).json()
        st.caption(f"📍 {geo.get('city', 'Unknown')} | 🟢 Online")
    except:
        st.caption("📍 GPS Offline")
        
    if st.button(T['logout']):
        st.session_state['logged_in'] = False
        st.rerun()

# --- CARREGAR DADOS ---
df = get_data(st.session_state['username'])

# --- PÁGINAS ---

# 1. DASHBOARD
if selected == T['menu'][0]: # Dashboard
    st.title("📊 Executive Overview")
    
    if df.empty:
        st.info("Sistema vazio. Comece importando dados ou lançando manualmente.")
    else:
        # KPIs
        total = df['total'].sum()
        ativos_unicos = df['ativo'].nunique()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Net Worth (Patrimônio)", f"R$ {total:,.2f}")
        c2.metric("Assets (Ativos)", ativos_unicos)
        c3.metric("Records (Registros)", len(df))
        
        # Gráficos
        g1, g2 = st.columns([2, 1])
        with g1:
            st.subheader("Evolução Patrimonial")
            # Agrupa por data (assumindo ISO format)
            evolucao = df.groupby('date')['total'].sum().cumsum().reset_index()
            fig = px.area(evolucao, x='date', y='total', template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
        with g2:
            st.subheader("Alocação")
            fig2 = px.pie(df, values='total', names='tipo', hole=0.6, template="plotly_dark")
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig2, use_container_width=True)

# 2. NOVO LANÇAMENTO (MANUAL)
elif selected == T['menu'][1]: # Novo Lançamento
    st.header(f"📝 {T['menu'][1]}")
    
    with st.form("manual_entry", clear_on_submit=True):
        c1, c2 = st.columns(2)
        # Formato de data dinâmico
        dt_input = c1.date_input("Data", date.today(), format=T['date_fmt'])
        tipo = c2.selectbox("Tipo", ["Ação", "FII", "Renda Fixa", "Crypto", "Despesa"])
        
        ativo = st.text_input("Código/Descrição (Ex: PETR4, Uber)").upper()
        
        c3, c4 = st.columns(2)
        qtd = c3.number_input("Qtd", min_value=0.01, value=1.0)
        preco = c4.number_input("Valor Unitário", min_value=0.01)
        
        if st.form_submit_button("Salvar Registro", type="primary"):
            add_transaction(st.session_state['username'], dt_input, tipo, ativo, qtd, preco)
            st.toast("Salvo com sucesso!", icon="✅")
            time.sleep(1)
            st.rerun()

# 3. IMPORTAÇÃO INTELIGENTE (NOVO!)
elif selected == T['menu'][2]: # Importar
    st.header(T['imp_title'])
    st.markdown(T['imp_desc'])
    
    uploaded_file = st.file_uploader("Upload .csv ou .xlsx", type=['csv', 'xlsx'])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_imp = pd.read_csv(uploaded_file)
            else:
                df_imp = pd.read_excel(uploaded_file)
            
            st.markdown(f"### 1. {T['col_map']}")
            st.dataframe(df_imp.head(3))
            
            with st.form("import_map"):
                c1, c2, c3 = st.columns(3)
                col_date = c1.selectbox("Coluna Data", df_imp.columns)
                col_desc = c2.selectbox("Coluna Descrição", df_imp.columns)
                col_val = c3.selectbox("Coluna Valor", df_imp.columns)
                
                def_type = st.selectbox("Tipo Padrão", ["Despesa", "Ação", "FII", "Renda Fixa"])
                
                if st.form_submit_button(T['btn_proc']):
                    count = 0
                    bar = st.progress(0)
                    for i, row in df_imp.iterrows():
                        try:
                            # Tenta converter data flexível
                            raw_date = row[col_date]
                            final_date = pd.to_datetime(raw_date, dayfirst=True).date()
                            
                            val = float(str(row[col_val]).replace('R$', '').replace(',', '.'))
                            
                            add_transaction(
                                st.session_state['username'],
                                final_date,
                                def_type,
                                str(row[col_desc]).upper(),
                                1.0, # Qtd padrão
                                val
                            )
                            count += 1
                        except:
                            pass # Ignora erros de linha
                        bar.progress((i+1)/len(df_imp))
                    
                    bar.empty()
                    st.success(f"✅ {count} {T['success_imp']}")
                    time.sleep(2)
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

# 4. CARTEIRA (AG-GRID)
elif selected == T['menu'][3]: # Carteira
    st.header("🗂️ Data Grid")
    
    if not df.empty:
        # Prepara visualização (Formata data dependendo do idioma)
        df_view = df.copy()
        if st.session_state['language'] == 'PT':
            df_view['date'] = pd.to_datetime(df_view['date']).dt.strftime('%d/%m/%Y')
        else:
            df_view['date'] = pd.to_datetime(df_view['date']).dt.strftime('%m/%d/%Y')
            
        gb = GridOptionsBuilder.from_dataframe(df_view[['date', 'tipo', 'ativo', 'total']])
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
        gb.configure_column("total", type=["numericColumn"], valueFormatter="'R$ ' + x.toLocaleString()")
        gb.configure_default_column(groupable=True, value=True, enableRowGroup=True)
        gb.configure_selection('multiple', use_checkbox=True)
        gridOptions = gb.build()
        
        AgGrid(df_view, gridOptions=gridOptions, theme='alpine', height=500, fit_columns_on_grid_load=True)
    else:
        st.warning("Empty / Vazio")

# 5. CONFIGURAÇÕES
elif selected == T['menu'][4]: # Config
    st.header("⚙️ System Config")
    st.info(f"User ID: {st.session_state['username']}")
    st.info(f"Database: SQLITE (Secure)")
    st.info(f"Version: 4.0.1 Enterprise")
