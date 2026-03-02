import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Financeiro Léo", layout="wide")

st.title("📊 Meu App Financeiro - Léo & Esposa")
st.sidebar.info("CONTATO - SE FOR CHORAR MANDA ÁUDIO AMOR <3")

# Dados que conferimos juntos
data = {
    'Mês': ['Fevereiro', 'Março'],
    'Entradas': [9342.49, 5840.81],
    'Saídas': [10447.34, 5279.79],
    'Saldo': [-1104.85, 561.02]
}
df = pd.DataFrame(data)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Resumo de Fevereiro")
    st.write(f"Entradas: R$ 9.342,49")
    st.write(f"Saídas: R$ 10.447,34")
    st.error(f"Saldo: R$ -1.104,85")

with col2:
    st.subheader("Resumo de Março")
    st.write(f"Entradas: R$ 5.840,81")
    st.write(f"Saídas: R$ 5.279,79")
    st.success(f"Saldo: R$ 561,02")

st.markdown("---")
st.subheader("Evolução Mensal")
fig = px.bar(df, x='Mês', y=['Entradas', 'Saídas'], barmode='group', color_discrete_map={'Entradas': '#4caf50', 'Saídas': '#f44336'})
st.plotly_chart(fig, use_container_width=True)
