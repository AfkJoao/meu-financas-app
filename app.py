import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Minhas Finanças Pro", layout="wide")

# Nomes dos arquivos de dados
ARQUIVO_DESPESAS = "despesas.csv"
ARQUIVO_APORTES = "aportes.csv"

# --- FUNÇÃO ESPECIAL: BUSCAR SELIC NO BANCO CENTRAL ---
@st.cache_data(ttl=86400) # O sistema guarda o valor por 24h para não travar
def buscar_selic_atual():
    """
    Conecta na API do Banco Central e pega a Meta Selic atual.
    Código da série 432 = Meta Selic definida pelo COPOM.
    """
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        # O Pandas lê o JSON direto da URL (Automação!)
        df_bc = pd.read_json(url)
        selic_atual = float(df_bc['valor'].iloc[0])
        return selic_atual
    except:
        # Se o site do Banco Central cair, usa 11.25 como segurança
        return 11.25

# --- FUNÇÕES DE ARQUIVO ---
def carregar_dados(arquivo, colunas):
    if not os.path.exists(arquivo):
        return pd.DataFrame(columns=colunas)
    return pd.read_csv(arquivo)

def salvar_dados(df, arquivo):
    df.to_csv(arquivo, index=False)

# Carregar dados
df_despesas = carregar_dados(ARQUIVO_DESPESAS, ["Data", "Categoria", "Descrição", "Valor"])
df_aportes = carregar_dados(ARQUIVO_APORTES, ["Data", "Tipo", "Destino", "Valor"])

# --- BARRA LATERAL (ENTRADA DE DADOS) ---
st.sidebar.header("💸 Novo Registro")
tipo_registro = st.sidebar.radio("Tipo", ["Despesa", "Aporte"], label_visibility="collapsed")

if tipo_registro == "Despesa":
    st.sidebar.subheader("Nova Despesa")
    data_despesa = st.sidebar.date_input("Data", date.today())
    cat_despesa = st.sidebar.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Outros"])
    desc_despesa = st.sidebar.text_input("Descrição (Ex: Pizza)")
    # step=0 remove as setinhas de + e -
    valor_despesa = st.sidebar.number_input("Valor (R$)", min_value=0.0, step=0.0, format="%.2f")
    
    if st.sidebar.button("Salvar Despesa", use_container_width=True):
        nova_linha = pd.DataFrame({"Data": [data_despesa], "Categoria": [cat_despesa], "Descrição": [desc_despesa], "Valor": [valor_despesa]})
        df_despesas = pd.concat([df_despesas, nova_linha], ignore_index=True)
        salvar_dados(df_despesas, ARQUIVO_DESPESAS)
        st.sidebar.success("Salvo!")
        st.rerun()

else: # Aporte
    st.sidebar.subheader("Novo Aporte")
    data_aporte = st.sidebar.date_input("Data", date.today())
    tipo_aporte = st.sidebar.selectbox("Tipo", ["Reserva (CDB)", "FIIs", "Ações", "Outros"])
    destino_aporte = st.sidebar.text_input("Ativo (Ex: CDB Banco X)")
    valor_aporte = st.sidebar.number_input("Valor (R$)", min_value=0.0, step=0.0, format="%.2f")
    
    if st.sidebar.button("Salvar Aporte", use_container_width=True):
        nova_linha = pd.DataFrame({"Data": [data_aporte], "Tipo": [tipo_aporte], "Destino": [destino_aporte], "Valor": [valor_aporte]})
        df_aportes = pd.concat([df_aportes, nova_linha], ignore_index=True)
        salvar_dados(df_aportes, ARQUIVO_APORTES)
        st.sidebar.success("Investimento Salvo!")
        st.rerun()

# --- DASHBOARD PRINCIPAL ---
st.title("💰 Painel Financeiro Inteligente")

aba1, aba2, aba3 = st.tabs(["📊 Gastos", "📈 Investimentos (Automático)", "📝 Histórico"])

# === ABA 1: GASTOS ===
with aba1:
    if not df_despesas.empty:
        df_despesas["Data"] = pd.to_datetime(df_despesas["Data"])
        df_despesas["Mes"] = df_despesas["Data"].dt.strftime("%Y-%m")
        
        c1, c2 = st.columns(2)
        with c1:
            grafico_mes = df_despesas.groupby("Mes")["Valor"].sum().reset_index()
            fig = px.bar(grafico_mes, x="Mes", y="Valor", title="Gasto Mensal", text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig_pizza = px.pie(df_despesas, values="Valor", names="Categoria", hole=0.5, title="Por Categoria")
            st.plotly_chart(fig_pizza, use_container_width=True)
            
        st.metric("Total Gasto", f"R$ {df_despesas['Valor'].sum():,.2f}")
    else:
        st.info("Cadastre sua primeira despesa na lateral.")

# === ABA 2: INVESTIMENTOS (COM INTEGRAÇÃO API) ===
with aba2:
    st.header("Simulador de Rentabilidade Real")
    
    # 1. Busca a Selic automática
    selic_real = buscar_selic_atual()
    
    col_calc, col_graf = st.columns(2)
    
    with col_calc:
        st.markdown("### 🧮 Calculadora de CDB")
        # Cartão mostrando a taxa capturada da internet
        st.info(f"📡 **Conexão Banco Central:** A Taxa Selic atual é **{selic_real}% a.a.**")
        
        st.markdown("Preencha os dados abaixo (Digite os valores):")
        
        # Caixas de texto simples (sem botões +/-)
        valor_investido = st.number_input("Quanto você tem investido? (R$)", value=1000.00, step=0.0)
        percentual_cdi = st.number_input("Quanto o banco paga do CDI? (%)", value=100.0, step=0.0)
        
        # CÁLCULO AUTOMÁTICO
        # Fórmula: Valor * (Selic/100) * (Pct_Banco/100)
        rendimento_anual_bruto = valor_investido * (selic_real / 100) * (percentual_cdi / 100)
        rendimento_mensal_bruto = rendimento_anual_bruto / 12
        
        # IR Regressivo (Média 17.5% para simulação)
        ir = 0.175
        rendimento_liquido = rendimento_mensal_bruto * (1 - ir)
        
        st.divider()
        st.success(f"💰 Seu dinheiro renderá limpo: **R$ {rendimento_liquido:.2f} / mês**")
        st.caption(f"*Cálculo baseado na Selic de hoje ({selic_real}%) e desconto médio de IR.")

    with col_graf:
        st.markdown("### 🚀 Meus Aportes")
        if not df_aportes.empty:
            df_aportes["Data"] = pd.to_datetime(df_aportes["Data"])
            df_aportes["Mes"] = df_aportes["Data"].dt.strftime("%Y-%m")
            fig = px.bar(df_aportes, x="Mes", y="Valor", color="Tipo", barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhum aporte registrado ainda.")

# === ABA 3: DADOS ===
with aba3:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Histórico de Despesas**")
        st.dataframe(df_despesas, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("**Histórico de Aportes**")
        st.dataframe(df_aportes, use_container_width=True, hide_index=True)
