import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import requests
from streamlit_option_menu import option_menu
from datetime import datetime, date

# --- CONFIGURAÇÃO DA PÁGINA (WIDE & DARK) ---
st.set_page_config(page_title="FinFuture Black", page_icon="🦅", layout="wide")

# --- CSS PERSONALIZADO (A MÁGICA DO DESIGN) ---
st.markdown("""
<style>
    /* Fundo geral e cor de texto */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Cartões de KPI (Métricas) */
    div[data-testid="metric-container"] {
        background-color: #262730;
        border: 1px solid #41444C;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    
    /* Ajuste de Títulos */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 300;
    }
    
    /* Tabelas mais limpas */
    .dataframe {
        font-size: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS ---
ARQUIVO_DADOS = "carteira_black.csv"

def carregar_dados():
    try:
        return pd.read_csv(ARQUIVO_DADOS)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Qtd", "Preco_Medio", "Total_Investido"])

def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

def get_market_price(ticker, tipo):
    """Busca preço atual. Se for FII/Ação busca online. Se for Renda Fixa, simula CDI."""
    if tipo == "Renda Fixa":
        return None # Renda fixa calculamos via CDI
    try:
        stock = yf.Ticker(f"{ticker}.SA")
        hist = stock.history(period="1d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
    except:
        pass
    return 0.0

def get_selic():
    """Pega a Selic atual para cálculos de Renda Fixa"""
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        df = pd.read_json(url)
        return float(df['valor'].iloc[0])
    except:
        return 11.25 # Fallback

def get_weather_ip():
    """Pega clima e local baseados no IP (Simulado para performance)"""
    try:
        # Simulando para não travar o app gratuito
        return "São Paulo", "24°C"
    except:
        return "Brasil", "--°C"

# --- SIDEBAR (NAVEGAÇÃO MODERNA) ---
with st.sidebar:
    # Perfil Rápido
    st.image("https://cdn-icons-png.flaticon.com/512/4140/4140048.png", width=70)
    st.markdown("### Olá, Investidor")
    
    # Widget de Clima
    cidade, temp = get_weather_ip()
    st.caption(f"📍 {cidade} | ⛅ {temp}")
    
    st.markdown("---")
    
    # Menu Estiloso
    selected = option_menu(
        menu_title="Navegação",
        options=["Dashboard", "Novo Aporte", "Minha Carteira", "Configurações"],
        icons=["speedometer2", "plus-circle", "wallet2", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#00d4ff", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"5px", "--hover-color": "#333"},
            "nav-link-selected": {"background-color": "#00d4ff", "color": "white"},
        }
    )

# --- CARREGAR DADOS ---
df = carregar_dados()
selic_atual = get_selic()

# ==========================================
# PÁGINA 1: DASHBOARD (VISÃO MACRO)
# ==========================================
if selected == "Dashboard":
    st.title("📊 Visão Geral do Patrimônio")
    st.markdown(f"**Referência Selic:** {selic_atual}% a.a.")
    
    if df.empty:
        st.info("👋 Bem-vindo! Vá em 'Novo Aporte' para começar sua jornada.")
    else:
        # Lógica de Cálculo de Patrimônio
        df['Preco_Atual'] = 0.0
        df['Saldo_Atual'] = 0.0
        
        # Barra de progresso para atualização
        progress_text = "Atualizando cotações em tempo real..."
        my_bar = st.progress(0, text=progress_text)
        
        total_steps = len(df)
        
        for index, row in df.iterrows():
            if row['Tipo'] == "Ação/FII":
                preco = get_market_price(row['Ativo'], row['Tipo'])
                # Se não achar preço (ex: final de semana ou erro), usa o preço de compra
                atual = preco if preco > 0 else row['Preco_Medio']
                df.at[index, 'Preco_Atual'] = atual
                df.at[index, 'Saldo_Atual'] = atual * row['Qtd']
            else:
                # Renda Fixa (Cálculo Simplificado de Rentabilidade)
                # Assumindo 1% ao mês para simplificar visualização rápida
                dias = (pd.to_datetime(date.today()) - pd.to_datetime(row['Data'])).days
                rentabilidade = row['Total_Investido'] * (0.01 * (dias/30)) 
                df.at[index, 'Saldo_Atual'] = row['Total_Investido'] + rentabilidade
            
            my_bar.progress((index + 1) / total_steps)
            
        my_bar.empty()
        
        # KPIS (OS NÚMEROS GRANDES)
        total_investido = df['Total_Investido'].sum()
        saldo_bruto = df['Saldo_Atual'].sum()
        lucro = saldo_bruto - total_investido
        performance = (lucro / total_investido) * 100 if total_investido > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Patrimônio Total", f"R$ {saldo_bruto:,.2f}", delta=f"{performance:.2f}%")
        col2.metric("Total Investido", f"R$ {total_investido:,.2f}")
        col3.metric("Lucro/Prejuízo Estimado", f"R$ {lucro:,.2f}", delta_color="normal")
        col4.metric("Ativos na Carteira", df['Ativo'].nunique())
        
        st.markdown("---")
        
        # GRÁFICOS LADO A LADO
        g1, g2 = st.columns(2)
        
        with g1:
            st.subheader("Alocação por Classe")
            fig_pizza = px.pie(df, values='Saldo_Atual', names='Tipo', hole=0.7, 
                               color_discrete_sequence=['#00d4ff', '#ff0055', '#ffd700'])
            fig_pizza.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
            st.plotly_chart(fig_pizza, use_container_width=True)
            
        with g2:
            st.subheader("Maiores Posições")
            # Agrupar por ativo
            posicao = df.groupby('Ativo')['Saldo_Atual'].sum().reset_index().sort_values('Saldo_Atual', ascending=True)
            fig_bar = px.bar(posicao, x='Saldo_Atual', y='Ativo', orientation='h', text_auto=True,
                             color='Saldo_Atual', color_continuous_scale='Bluered')
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# PÁGINA 2: NOVO APORTE
# ==========================================
elif selected == "Novo Aporte":
    st.title("💸 Registrar Operação")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.info("Preencha os dados ao lado para atualizar sua carteira.")
        
    with c2:
        with st.form("form_aporte", clear_on_submit=True):
            data = st.date_input("Data da Operação", date.today())
            tipo = st.selectbox("Classe do Ativo", ["Ação/FII", "Renda Fixa"])
            ativo = st.text_input("Código do Ativo (Ex: VALE3, CDB Inter)").upper()
            
            col_f1, col_f2 = st.columns(2)
            qtd = col_f1.number_input("Quantidade / Cotas", min_value=0.01, step=1.0)
            preco = col_f2.number_input("Preço Unitário / Valor Aportado", min_value=0.01, format="%.2f")
            
            if st.form_submit_button("Confirmar Aporte", type="primary"):
                total = qtd * preco
                novo_dado = pd.DataFrame([{
                    "Data": data, "Ativo": ativo, "Tipo": tipo, 
                    "Qtd": qtd, "Preco_Medio": preco, "Total_Investido": total
                }])
                df = pd.concat([df, novo_dado], ignore_index=True)
                salvar_dados(df)
                st.success(f"Aporte de R$ {total:.2f} em {ativo} registrado!")
                st.rerun()

# ==========================================
# PÁGINA 3: CARTEIRA DETALHADA
# ==========================================
elif selected == "Minha Carteira":
    st.title("📜 Extrato Detalhado")
    
    if not df.empty:
        # Filtros
        filtro_tipo = st.multiselect("Filtrar por Tipo", df['Tipo'].unique(), default=df['Tipo'].unique())
        df_filtrado = df[df['Tipo'].isin(filtro_tipo)]
        
        # Tabela Estilizada
        st.dataframe(
            df_filtrado, 
            use_container_width=True,
            column_config={
                "Data": st.column_config.DateColumn("Data da Compra", format="DD/MM/YYYY"),
                "Total_Investido": st.column_config.NumberColumn("Valor Investido", format="R$ %.2f"),
                "Preco_Medio": st.column_config.NumberColumn("Preço Pago", format="R$ %.2f"),
            },
            hide_index=True
        )
        
        if st.button("🗑️ Limpar Carteira (Resetar Dados)"):
            pd.DataFrame(columns=["Data", "Ativo", "Tipo", "Qtd", "Preco_Medio", "Total_Investido"]).to_csv(ARQUIVO_DADOS, index=False)
            st.warning("Carteira resetada!")
            st.rerun()
    else:
        st.warning("Nenhum dado encontrado.")

# ==========================================
# PÁGINA 4: CONFIGURAÇÕES
# ==========================================
elif selected == "Configurações":
    st.title("⚙️ Ajustes")
    st.write("Configurações do Usuário")
    
    st.toggle("Modo Escuro (Ativo por Padrão)", value=True, disabled=True)
    st.selectbox("Moeda Principal", ["BRL (R$)", "USD ($)"])
    st.selectbox("Idioma", ["Português", "English"])
    
    st.info("Versão 3.0 Pro - Build 2026")
