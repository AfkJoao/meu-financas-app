import streamlit as st
from datetime import datetime

# 1. Configuração da Data no formato BR (DD/MM/YYYY)
data_atual = datetime.now().strftime('%d/%m/%Y')

st.title("📊 Simulador de Investimento - Tesouraria Pessoal")
st.write(f"Data de referência: **{data_atual}**")

st.divider()

# 2. Entradas de Dados (Campos Digitáveis)
col1, col2 = st.columns(2)

with col1:
    # Substituído o slider por number_input para maior precisão
    taxa_selic = st.number_input(
        "Taxa CDI/Selic (% a.a.)", 
        value=12.15, 
        step=0.01,
        format="%.2f"
    )

with col2:
    # Campo para digitar a porcentagem que o banco paga
    percentual_cdi = st.number_input(
        "% do CDI que o banco paga", 
        value=100.0, 
        step=1.0,
        format="%.1f"
    )

# 3. Cálculo Atrelado (Lógica de Engenharia de Software)
rendimento_efetivo = taxa_selic * (percentual_cdi / 100)

st.divider()

# 4. Exibição do Resultado
st.subheader("Resultado da Análise")
st.metric(
    label="Rendimento Real Efetivo", 
    value=f"{rendimento_efetivo:.2f}% ao ano"
)

st.info(f"Com o CDI a {taxa_selic}% e o banco pagando {percentual_cdi}%, seu dinheiro rende {rendimento_efetivo:.2f}% a.a.")
