import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import requests
import yfinance as yf
from datetime import datetime, date
from streamlit_lottie import st_lottie

# --- CONFIGURAÇÃO DA PÁGINA (PROFESSIONAL MODE) ---
st.set_page_config(page_title="FinFuture OS", page_icon="💎", layout="wide")

# --- DICIONÁRIO DE IDIOMAS (I18N) ---
LANG = {
    "PT": {
        "welcome": "Painel de Controle Patrimonial",
        "location": "Acessando de",
        "weather": "Clima",
        "tab1": "📊 Dashboard Executivo",
        "tab2": "📈 Mercado & Aportes",
        "tab3": "🏛️ Renda Fixa (CDB/Selic)",
        "kpi_total": "Patrimônio Estimado",
        "kpi_income": "Provisão de Rendimentos",
        "kpi_assets": "Ativos Monitorados",
        "new_entry": "Nova Movimentação",
        "save": "Registrar Operação",
        "desc_selic": "Análise de CDB baseada na Curva de Juros e Data de Aporte",
    },
    "EN": {
        "welcome": "Asset Management Dashboard",
        "location": "Accessing from",
        "weather": "Weather",
        "tab1": "📊 Executive Dashboard",
        "tab2": "📈 Market & Investments",
        "tab3": "🏛️ Fixed Income (Yields)",
        "kpi_total": "Estimated Net Worth",
        "kpi_income": "Yield Provision",
        "kpi_assets": "Monitored Assets",
        "new_entry": "New Entry",
        "save": "Register Operation",
        "desc_selic": "CDB Analysis based on Interest Curve and Deposit Date",
    }
}

# --- FUNÇÕES DE UTILIDADE E APIs ---

def load_lottieurl(url):
    """Carrega animações Lottie da internet"""
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def get_location_data():
    """Pega cidade baseada no IP (Simulação segura para não travar)"""
    try:
        response = requests.get('http://ip-api.com/json/')
        data = response.json()
        return f"{data['city']}, {data['countryCode']}"
    except:
        return "Localização Desconhecida"

def get_market_data(ticker):
    """Busca dados da B3 em tempo real via Yahoo Finance"""
    try:
        stock = yf.Ticker(f"{ticker}.SA")
        hist = stock.history(period="1d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            # Tenta pegar dividendos (Yield anual estimado)
            info = stock.info
            div_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
            return price, div_yield
        return 0.0, 0.0
    except:
        return 0.0, 0.0

@st.cache_data(ttl=86400)
def get_selic_history():
    """Busca histórico da Selic no Banco Central"""
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/120?formato=json"
        df = pd.read_json(url)
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
        return df
    except:
        return pd.DataFrame()

# --- ARMAZENAMENTO DE DADOS ---
ARQUIVO_DADOS = "carteira_global.csv"

def carregar_dados():
    if not os.path.exists(ARQUIVO_DADOS):
        return pd.DataFrame(columns=["Data", "Tipo", "Ativo", "Qtd", "Preco_Compra", "Taxa_Contratada", "Valor_Total"])
    return pd.read_csv(ARQUIVO_DADOS)

def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

# --- INÍCIO DO APP ---

# 1. Sidebar de Configuração
st.sidebar.header("⚙️ System Config")
selected_lang = st.sidebar.selectbox("Language / Idioma", ["PT", "EN"])
text = LANG[selected_lang]

# 2. Header com Animação e KPIs de Ambiente
lottie_tech = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_w51pcehl.json")

col_head1, col_head2, col_head3 = st.columns([1, 4, 2])
with col_head1:
    if lottie_tech:
        st_lottie(lottie_tech, height=100)
with col_head2:
    st.title(text["welcome"])
    st.caption(f"🚀 FinFuture OS v2.0 | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
with col_head3:
    loc = get_location_data()
    st.metric(label=text["location"], value=loc, delta=text["weather"])

# --- CARREGAR DADOS ---
df = carregar_dados()

# --- ENTRADA DE DADOS (SIDEBAR) ---
st.sidebar.markdown("---")
st.sidebar.subheader(text["new_entry"])

with st.sidebar.form("entry_form"):
    tipo = st.selectbox("Tipo de Ativo", ["Ação/FII", "Renda Fixa (CDB/Tesouro)"])
    data_op = st.date_input("Data da Operação", date.today())
    ativo_nome = st.text_input("Código/Nome (Ex: MXRF11 ou CDB Nubank)")
    
    col_form1, col_form2 = st.columns(2)
    with col_form1:
        qtd = st.number_input("Qtd / Cotas", min_value=0.0, step=1.0)
    with col_form2:
        preco = st.number_input("Preço/Valor Unitário (R$)", min_value=0.0, format="%.2f")
    
    taxa = 0.0
    if tipo == "Renda Fixa (CDB/Tesouro)":
        taxa = st.number_input("Taxa Contratada (% do CDI ou Fixa)", value=100.0)
        
    submitted = st.form_submit_button(text["save"])
    
    if submitted:
        val_total = qtd * preco
        novo = pd.DataFrame([{
            "Data": data_op, "Tipo": tipo, "Ativo": ativo_nome.upper(), 
            "Qtd": qtd, "Preco_Compra": preco, "Taxa_Contratada": taxa, "Valor_Total": val_total
        }])
        df = pd.concat([df, novo], ignore_index=True)
        salvar_dados(df)
        st.success("Salvo com sucesso!")
        st.rerun()

# --- ABAS PRINCIPAIS ---
aba1, aba2, aba3 = st.tabs([text["tab1"], text["tab2"], text["tab3"]])

# === ABA 1: DASHBOARD EXECUTIVO ===
with aba1:
    if not df.empty:
        # Cálculos de KPI
        total_investido = df["Valor_Total"].sum()
        total_ativos = df["Ativo"].nunique()
        
        # Gráficos
        c1, c2, c3 = st.columns(3)
        c1.metric(text["kpi_total"], f"R$ {total_investido:,.2f}", delta="+Aportes")
        c2.metric(text["kpi_assets"], total_ativos)
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Distribuição de Carteira")
            fig_pizza = px.pie(df, values='Valor_Total', names='Tipo', hole=0.6, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pizza, use_container_width=True)
            
        with col_g2:
            st.subheader("Aportes por Ativo")
            fig_bar = px.bar(df, x='Ativo', y='Valor_Total', color='Tipo', template="plotly_dark")
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Aguardando dados... Use a sidebar.")

# === ABA 2: MERCADO EM TEMPO REAL (FIIs/AÇÕES) ===
with aba2:
    st.subheader("📡 Monitoramento da B3 (Live)")
    
    df_rv = df[df["Tipo"] == "Ação/FII"].copy()
    
    if not df_rv.empty:
        # Agrupar por ativo
        carteira = df_rv.groupby("Ativo").agg({"Qtd": "sum", "Preco_Compra": "mean"}).reset_index()
        
        lista_cotacao = []
        
        # Barra de progresso para o loading da API
        bar = st.progress(0, text="Conectando à B3...")
        
        for i, row in carteira.iterrows():
            ticker = row['Ativo']
            preco_atual, div_yield = get_market_data(ticker)
            
            valor_posicao = row['Qtd'] * preco_atual
            lucro = valor_posicao - (row['Qtd'] * row['Preco_Compra'])
            
            lista_cotacao.append({
                "Ativo": ticker,
                "Preço Médio": row['Preco_Compra'],
                "Preço Atual": preco_atual,
                "Variação (R$)": lucro,
                "Div. Yield Est. (%)": div_yield,
                "Total Atual": valor_posicao
            })
            bar.progress((i + 1) / len(carteira), text=f"Baixando dados de {ticker}...")
            
        bar.empty()
        
        df_view = pd.DataFrame(lista_cotacao)
        st.dataframe(
            df_view.style.format({
                "Preço Médio": "R$ {:.2f}", "Preço Atual": "R$ {:.2f}", 
                "Variação (R$)": "R$ {:.2f}", "Total Atual": "R$ {:.2f}", "Div. Yield Est. (%)": "{:.2f}%"
            }), 
            use_container_width=True
        )
        
        # Gráfico de Yield
        fig_yield = px.bar(df_view, x="Ativo", y="Div. Yield Est. (%)", title="Dividend Yield Estimado", color="Div. Yield Est. (%)")
        st.plotly_chart(fig_yield, use_container_width=True)

    else:
        st.warning("Nenhum FII ou Ação cadastrada.")

# === ABA 3: RENDA FIXA AVANÇADA (SELIC HISTÓRICA) ===
with aba3:
    st.markdown(f"### {text['desc_selic']}")
    
    selic_hist = get_selic_history()
    
    if not selic_hist.empty:
        selic_atual = selic_hist['valor'].iloc[-1]
        media_anual = selic_hist['valor'].mean() # Média do período carregado
        
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Selic Hoje", f"{selic_atual}% a.a.")
        col_s2.metric("Média Selic (Últimos Meses)", f"{media_anual:.2f}% a.a.")
        
        # Pegar os CDBs da carteira
        df_rf = df[df["Tipo"] == "Renda Fixa (CDB/Tesouro)"].copy()
        
        if not df_rf.empty:
            df_rf['Data'] = pd.to_datetime(df_rf['Data'])
            
            resultados = []
            
            for index, row in df_rf.iterrows():
                # Lógica: Filtra a Selic apenas DEPOIS da data do aporte
                dias_corridos = (pd.to_datetime(date.today()) - row['Data']).days
                
                # Cálculo Estimado (Simplificado para performance)
                # Valor * (1 + (TaxaCDI * %Banco / 100)) ^ (Anos)
                anos = dias_corridos / 365
                taxa_efetiva = (selic_atual * (row['Taxa_Contratada']/100)) / 100
                
                valor_presente = row['Valor_Total'] * ((1 + taxa_efetiva) ** anos)
                rendimento = valor_presente - row['Valor_Total']
                
                resultados.append({
                    "Ativo": row['Ativo'],
                    "Data Aporte": row['Data'].strftime('%d/%m/%Y'),
                    "Dias": dias_corridos,
                    "Aportado": row['Valor_Total'],
                    "Taxa Momento": f"{selic_atual}%",
                    "Saldo Estimado": valor_presente,
                    "Lucro Bruto": rendimento
                })
            
            df_rf_view = pd.DataFrame(resultados)
            st.dataframe(df_rf_view, use_container_width=True)
            
            # Gráfico Comparativo de Rentabilidade
            fig_line = px.line(selic_hist, x='data', y='valor', title="Histórico da Taxa Selic (B.C.)")
            st.plotly_chart(fig_line, use_container_width=True)
            
        else:
            st.info("Nenhum Renda Fixa cadastrado.")
    else:
        st.error("Erro ao conectar com Banco Central.")

# Rodapé Tecnológico
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>Developed with Python & Streamlit • Data provided by B3 & BCB</div>", unsafe_allow_html=True)
