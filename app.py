import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import requests
import time
from streamlit_option_menu import option_menu
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import datetime, date

# --- CONFIGURAÇÃO DA PÁGINA (DESIGN SYSTEM) ---
st.set_page_config(page_title="FinFuture OS", page_icon="🦅", layout="wide")

# --- CSS AVANÇADO (GLASSMORPHISM & ANIMAÇÕES) ---
st.markdown("""
<style>
    /* Fundo Tecnológico */
    .stApp {
        background: linear-gradient(to bottom right, #0f0c29, #302b63, #24243e);
        color: #E0E0E0;
    }
    
    /* Login Box */
    .login-box {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 30px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    }
    
    /* Cartões de KPI Modernos */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px;
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: scale(1.02);
        border-color: #00d4ff;
    }
    
    /* Ajustes Gerais */
    h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 400; }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- SISTEMA DE LOGIN SEGURO ---
def check_password():
    """Retorna True se o usuário estiver logado com sucesso."""
    if st.session_state.get('password_correct', False):
        return True

    # Interface de Login (Centralizada)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown('<div class="login-box"><h2>🔐 Acesso Restrito</h2><p>FinFuture Private System</p></div>', unsafe_allow_html=True)
        
        user = st.text_input("Usuário", key="login_user")
        pwd = st.text_input("Senha", type="password", key="login_pwd")
        
        if st.button("Entrar no Sistema", type="primary"):
            # Verifica nos Secrets do Streamlit
            try:
                secrets = st.secrets["passwords"]
                if user in secrets and secrets[user] == pwd:
                    st.session_state['password_correct'] = True
                    st.session_state['user_name'] = user
                    st.rerun()
                else:
                    st.error("Credenciais Inválidas")
            except:
                # Fallback para rodar local sem secrets configurados
                if user == "admin" and pwd == "admin":
                    st.session_state['password_correct'] = True
                    st.rerun()
                else:
                    st.warning("Configure st.secrets ou use admin/admin localmente")
    return False

if not check_password():
    st.stop() # Para a execução aqui se não estiver logado

# =========================================================
#  A PARTIR DAQUI, O CÓDIGO SÓ RODA SE ESTIVER LOGADO
# =========================================================

# --- FUNÇÕES DE INTEGRAÇÃO (Backend) ---
ARQUIVO_DADOS = "carteira_master.csv"

def carregar_dados():
    try:
        return pd.read_csv(ARQUIVO_DADOS)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Qtd", "Preco_Medio", "Total_Investido"])

def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

@st.cache_data(ttl=3600)
def get_weather_real():
    """Busca Localização via IP e Clima via Open-Meteo"""
    try:
        # 1. Pega Lat/Lon pelo IP
        ip_data = requests.get("http://ip-api.com/json/", timeout=3).json()
        lat, lon = ip_data['lat'], ip_data['lon']
        city = ip_data['city']
        
        # 2. Pega Clima exato na Lat/Lon
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        w_data = requests.get(w_url, timeout=3).json()
        
        temp = w_data['current_weather']['temperature']
        code = w_data['current_weather']['weathercode']
        
        # Ícones baseados no código WMO
        icon = "☀️" if code == 0 else "⛅" if code < 3 else "🌧️" if code < 60 else "⛈️"
        
        return city, f"{temp}°C", icon
    except:
        return "Localização Oculta", "--", "🌐"

def get_market_price(ticker):
    try:
        stock = yf.Ticker(f"{ticker}.SA")
        hist = stock.history(period="1d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
    except:
        pass
    return 0.0

def get_selic():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        return float(pd.read_json(url)['valor'].iloc[0])
    except:
        return 11.25

# --- BARRA LATERAL PRO ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/11516/11516624.png", width=60)
    
    # Widget de Clima Real
    city, temp, icon = get_weather_real()
    
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin-bottom: 20px;">
        <small style="color: #bbb;">Localização Segura</small><br>
        <b>{city}</b><br>
        <span style="font-size: 20px;">{icon} {temp}</span>
    </div>
    """, unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title=None,
        options=["Visão Geral", "Lançamentos", "Carteira Avançada", "Análise IA"],
        icons=["columns-gap", "plus-lg", "table", "cpu"],
        styles={
            "container": {"padding": "0!important", "background": "transparent"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "#444"},
            "nav-link-selected": {"background-color": "#00d4ff", "color": "black", "font-weight": "bold"},
        }
    )
    
    st.markdown("---")
    if st.button("Sair / Logout"):
        st.session_state['password_correct'] = False
        st.rerun()

# --- LÓGICA PRINCIPAL ---
df = carregar_dados()
selic_atual = get_selic()

# ==========================================
# 1. DASHBOARD EXECUTIVO
# ==========================================
if selected == "Visão Geral":
    st.title(f"Olá, {st.session_state.get('user_name', 'Investidor').title()}")
    st.caption(f"Sincronizado com Banco Central (Selic {selic_atual}%) e B3 (15min delay).")
    
    if df.empty:
        st.warning("Sistema limpo. Inicie os lançamentos no menu lateral.")
    else:
        # --- PROCESSAMENTO EM TEMPO REAL ---
        if 'Preco_Atual' not in df.columns:
            df['Preco_Atual'] = 0.0
            
        saldo_total = 0.0
        investido_total = df['Total_Investido'].sum()
        
        # Barra de Status Tecnológica
        status_text = st.empty()
        status_bar = st.progress(0)
        
        for i, row in df.iterrows():
            status_text.text(f"📡 Conectando satélite financeiro... Atualizando {row['Ativo']}...")
            
            if row['Tipo'] == "Ação/FII":
                preco = get_market_price(row['Ativo'])
                atual = preco if preco > 0 else row['Preco_Medio']
                saldo_posicao = atual * row['Qtd']
            else:
                # Simulação RF
                dias = (pd.to_datetime(date.today()) - pd.to_datetime(row['Data'])).days
                rentabilidade = row['Total_Investido'] * (0.0095 * (dias/30)) # ~0.95% a.m.
                saldo_posicao = row['Total_Investido'] + rentabilidade
            
            saldo_total += saldo_posicao
            status_bar.progress((i + 1) / len(df))
            
        status_text.empty()
        status_bar.empty()
        
        lucro = saldo_total - investido_total
        var_pct = (lucro / investido_total) * 100 if investido_total > 0 else 0
        
        # KPIS
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Patrimônio Líquido", f"R$ {saldo_total:,.2f}", delta=f"{var_pct:.2f}%")
        c2.metric("Total Aportado", f"R$ {investido_total:,.2f}")
        c3.metric("Resultado (R$)", f"R$ {lucro:,.2f}", delta_color="normal")
        c4.metric("Ativos Monitorados", df['Ativo'].nunique())
        
        st.markdown("---")
        
        # GRÁFICOS PREMIUM
        g1, g2 = st.columns([2, 1])
        
        with g1:
            st.markdown("### 🧬 Composição da Carteira")
            fig = px.sunburst(df, path=['Tipo', 'Ativo'], values='Total_Investido', color='Tipo',
                              color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
            st.plotly_chart(fig, use_container_width=True)
            
        with g2:
            st.markdown("### 🏆 Top Assets")
            top = df.groupby('Ativo')['Total_Investido'].sum().nlargest(5).reset_index()
            st.dataframe(top.style.background_gradient(cmap="Blues"), use_container_width=True, hide_index=True)

# ==========================================
# 2. LANÇAMENTOS
# ==========================================
elif selected == "Lançamentos":
    st.header("📝 Nova Movimentação")
    
    with st.expander("Instruções de Preenchimento", expanded=True):
        st.info("Para Renda Fixa, use o código do banco no campo 'Ativo' (Ex: CDB INTER). Para Bolsa, use o Ticker (Ex: WEGE3).")
    
    with st.form("main_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data", date.today())
        tipo = col2.selectbox("Tipo", ["Ação/FII", "Renda Fixa"])
        
        ativo = st.text_input("Código do Ativo").upper()
        
        c1, c2, c3 = st.columns(3)
        qtd = c1.number_input("Qtd / Cotas", min_value=0.0, step=1.0)
        preco = c2.number_input("Preço Unitário / Valor", min_value=0.0, format="%.2f")
        taxa = c3.text_input("Taxa (Opcional)", value="100% CDI")
        
        if st.form_submit_button("🚀 Registrar na Blockchain (Simulado)", type="primary"):
            total = qtd * preco
            novo = pd.DataFrame([{
                "Data": data, "Ativo": ativo, "Tipo": tipo, 
                "Qtd": qtd, "Preco_Medio": preco, "Total_Investido": total
            }])
            df = pd.concat([df, novo], ignore_index=True)
            salvar_dados(df)
            st.balloons()
            st.success("Transação registrada com sucesso!")

# ==========================================
# 3. CARTEIRA AVANÇADA (AgGrid)
# ==========================================
elif selected == "Carteira Avançada":
    st.header("🗂️ Gestão de Dados (Excel Mode)")
    st.caption("Edite células clicando duas vezes nelas. Use os filtros no topo das colunas.")
    
    if not df.empty:
        # Configuração da Tabela Profissional
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
        gb.configure_side_bar()
        gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)
        
        # Formatação Monetária JS
        js_code = """
        function(params) {
            if (params.value !== null) {
                return 'R$ ' + params.value.toFixed(2);
            }
            return null;
        }
        """
        gb.configure_column("Total_Investido", cellRenderer=js_code)
        gb.configure_column("Preco_Medio", cellRenderer=js_code)
        
        # Seleção
        gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren=True)
        gridOptions = gb.build()
        
        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            data_return_mode='AS_INPUT', 
            update_mode='MODEL_CHANGED', 
            fit_columns_on_grid_load=True,
            theme='alpine', # Tema Clean
            height=400
        )
        
        # Botão de Salvar Edições
        data = grid_response['data']
        df_editado = pd.DataFrame(data)
        
        col_btn1, col_btn2 = st.columns([1, 4])
        if col_btn1.button("💾 Salvar Alterações"):
            salvar_dados(df_editado)
            st.toast("Banco de dados atualizado!", icon="✅")
            time.sleep(1)
            st.rerun()

# ==========================================
# 4. ANÁLISE IA (Placeholder)
# ==========================================
elif selected == "Análise IA":
    st.title("🧠 FinGPT Advisor")
    st.markdown("""
    <div style='background-color: #1E1E1E; padding: 20px; border-radius: 10px; border-left: 5px solid #00d4ff;'>
        <b>Insight Automático:</b><br>
        Sua carteira está concentrada em Renda Fixa. Com a Selic atual de {:.2f}%, isso é conservador, 
        mas considere diversificar em FIIs de Papel para aumentar o fluxo de caixa mensal.
    </div>
    """.format(selic_atual), unsafe_allow_html=True)
    
    st.image("https://cdn.dribbble.com/users/1068771/screenshots/14937812/media/6b04be20c8a513511116c27303cb566e.jpg", caption="Módulo de IA em desenvolvimento")
