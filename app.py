# 1. Instala as bibliotecas necessárias (silenciosamente)
!pip install streamlit pandas plotly openpyxl -q

# 2. Cria o arquivo app.py com o código do seu Dashboard
# (Usando aspas triplas para escrever o arquivo inteiro de uma vez)
codigo = '''
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Minhas Finanças Pro", layout="wide")

# Nomes dos arquivos onde os dados serão salvos
ARQUIVO_DESPESAS = "despesas.csv"
ARQUIVO_APORTES = "aportes.csv"

# --- FUNÇÕES PARA LIDAR COM DADOS ---
def carregar_dados(arquivo, colunas):
    """Carrega os dados do CSV. Se não existir, cria um vazio."""
    if not os.path.exists(arquivo):
        return pd.DataFrame(columns=colunas)
    return pd.read_csv(arquivo)

def salvar_dados(df, arquivo):
    """Salva o dataframe atualizado no arquivo CSV."""
    df.to_csv(arquivo, index=False)

# Carregando os dados existentes
df_despesas = carregar_dados(ARQUIVO_DESPESAS, ["Data", "Categoria", "Descrição", "Valor"])
df_aportes = carregar_dados(ARQUIVO_APORTES, ["Data", "Tipo", "Destino", "Valor"])

# --- BARRA LATERAL (ENTRADA DE DADOS) ---
st.sidebar.title("💸 Novo Registro")
tipo_registro = st.sidebar.radio("O que vamos registrar?", ["Despesa", "Aporte/Investimento"])

if tipo_registro == "Despesa":
    st.sidebar.subheader("Nova Despesa")
    data_despesa = st.sidebar.date_input("Data", date.today())
    cat_despesa = st.sidebar.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Outros"])
    desc_despesa = st.sidebar.text_input("Descrição (Ex: Pizza, Uber)")
    valor_despesa = st.sidebar.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    
    if st.sidebar.button("Salvar Despesa"):
        nova_linha = pd.DataFrame({"Data": [data_despesa], "Categoria": [cat_despesa], "Descrição": [desc_despesa], "Valor": [valor_despesa]})
        df_despesas = pd.concat([df_despesas, nova_linha], ignore_index=True)
        salvar_dados(df_despesas, ARQUIVO_DESPESAS)
        st.sidebar.success("Despesa salva com sucesso!")
        st.rerun()

else: # Se for Aporte
    st.sidebar.subheader("Novo Aporte")
    data_aporte = st.sidebar.date_input("Data do Aporte", date.today())
    tipo_aporte = st.sidebar.selectbox("Tipo", ["Reserva de Emergência", "Investimentos (Ações/FIIs)", "Outros"])
    destino_aporte = st.sidebar.text_input("Destino (Ex: CDB Banco X, FII MXRF11)")
    valor_aporte = st.sidebar.number_input("Valor Aportado (R$)", min_value=0.0, format="%.2f")
    
    if st.sidebar.button("Salvar Aporte"):
        nova_linha = pd.DataFrame({"Data": [data_aporte], "Tipo": [tipo_aporte], "Destino": [destino_aporte], "Valor": [valor_aporte]})
        df_aportes = pd.concat([df_aportes, nova_linha], ignore_index=True)
        salvar_dados(df_aportes, ARQUIVO_APORTES)
        st.sidebar.success("Aporte registrado!")
        st.rerun()

# --- ÁREA PRINCIPAL (DASHBOARD) ---
st.title("💰 Painel de Controle Financeiro")

aba1, aba2, aba3 = st.tabs(["📊 Visão Geral de Gastos", "📈 Investimentos & Reserva", "📝 Histórico Detalhado"])

# === ABA 1: GASTOS ===
with aba1:
    if not df_despesas.empty:
        df_despesas["Data"] = pd.to_datetime(df_despesas["Data"])
        df_despesas["Mes"] = df_despesas["Data"].dt.strftime("%Y-%m")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Evolução Mensal")
            gastos_por_mes = df_despesas.groupby("Mes")["Valor"].sum().reset_index()
            fig_bar = px.bar(gastos_por_mes, x="Mes", y="Valor", title="Total Gasto por Mês", text_auto=True)
            st.plotly_chart(fig_bar, use_container_width=True)
        with col2:
            st.subheader("Divisão por Categoria")
            fig_pie = px.pie(df_despesas, values="Valor", names="Categoria", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        # Métricas Rápidas
        st.divider()
        total = df_despesas["Valor"].sum()
        st.metric("Total Gasto (Histórico)", f"R$ {total:,.2f}")

    else:
        st.info("Nenhuma despesa registrada ainda.")

# === ABA 2: INVESTIMENTOS ===
with aba2:
    st.header("Gestão de Patrimônio")
    col_inv1, col_inv2 = st.columns(2)
    
    with col_inv1:
        st.markdown("### 🧮 Calculadora CDB")
        valor_cdb = st.number_input("Valor Investido (R$)", value=1000.00)
        taxa_cdi = st.number_input("CDI/Selic (% a.a.)", value=12.15)
        percentual = st.slider("% do CDI", 80, 150, 100)
        
        rend_anual = valor_cdb * (taxa_cdi/100) * (percentual/100)
        rend_mensal_liq = (rend_anual / 12) * 0.825 # Aprox IR 17.5%
        st.success(f"Rendimento Líquido Estimado: R$ {rend_mensal_liq:.2f} / mês")

    with col_inv2:
        st.markdown("### 🚀 Aportes")
        if not df_aportes.empty:
            df_aportes["Data"] = pd.to_datetime(df_aportes["Data"])
            df_aportes["Mes"] = df_aportes["Data"].dt.strftime("%Y-%m")
            fig_aportes = px.bar(df_aportes, x="Mes", y="Valor", color="Tipo")
            st.plotly_chart(fig_aportes, use_container_width=True)
        else:
            st.info("Nenhum aporte registrado.")

# === ABA 3: HISTÓRICO ===
with aba3:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.markdown("**Despesas**")
        st.dataframe(df_despesas, use_container_width=True)
    with col_f2:
        st.markdown("**Aportes**")
        st.dataframe(df_aportes, use_container_width=True)
'''

with open("app.py", "w") as f:
    f.write(codigo)

# 3. Descobre o IP do túnel
print("⏳ Instalando e iniciando...")
print("⚠️ COPIE O NÚMERO ABAIXO (IP):")
!wget -q -O - ipv4.icanhazip.com

# 4. Roda o Streamlit com o fix (-y) para não travar
print("🚀 Clique no link 'your url is: https://...' abaixo!")
!streamlit run app.py & npx -y localtunnel --port 8501
