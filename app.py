import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da Página para Estilo Dark Profissional
st.set_page_config(page_title="Planejamento Financeiro", layout="wide", initial_sidebar_state="collapsed")

# CSS Customizado para imitar o visual do print
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e1e1e; padding: 20px; border-radius: 10px; border-left: 5px solid #4caf50; }
    .card-renda { border-left: 5px solid #00c853 ! profound; }
    .card-despesa { border-left: 5px solid #ff5252 ! profound; }
    .card-saldo { border-left: 5px solid #2979ff ! profound; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Menu Superior (Simulado com Tabs)
menu = st.tabs(["📊 Dashboard", "📝 Lançamentos", "📅 Despesas Fixas", "🔔 Alertas", "🎯 Metas", "📈 Simulador", "🏷️ Categorias"])

with menu[0]: # Aba Dashboard
    st.title("Dashboard Financeiro")
    st.caption("Visão geral das suas finanças pessoais")

    # Filtros de Período
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
    with col_f1:
        st.write("") # Espaçador
    with col_f2: st.button("Período Total", use_container_width=True)
    with col_f3: st.button("Por Mês", use_container_width=True)
    with col_f4: st.button("Por Período", use_container_width=True)

    st.markdown("---")

    # Cards Principais (Valores do seu print)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Renda Real", "R$ 84.216,15", "Salário + Comissão + Rendimentos")
    with c2:
        st.metric("Total de Despesas", "R$ 166.360,21", delta_color="inverse")
    with c3:
        st.metric("Saldo Real", "R$ 16.212,58")

    st.markdown("### Detalhamento de Receitas")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Renda Fixa", "R$ 83.399,03", "Salário, Comissão, 13º")
    r2.metric("Rendimentos", "R$ 817,12", "Investimentos")
    r3.metric("Vendas/Extras", "R$ 24.885,18", "Vendas, bicos")
    r4.metric("Dinheiro Pai", "R$ 1.000,00", "⚠️ Não é seu", delta_color="off")

    # Gráfico de Evolução (Dados Fev/Mar)
    st.markdown("---")
    st.subheader("Evolução Mensal")
    df_evolucao = pd.DataFrame({
        'Mês': ['Fevereiro', 'Março'],
        'Entradas': [9342.49, 5840.81],
        'Saídas': [10447.34, 5279.79]
    })
    fig = px.bar(df_evolucao, x='Mês', y=['Entradas', 'Saídas'], barmode='group', 
                 color_discrete_map={'Entradas': '#00c853', 'Saídas': '#ff5252'},
                 template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with menu[1]: # Aba Lançamentos
    st.subheader("📝 Registro de Lançamentos")
    st.info("Aqui você poderá adicionar novas despesas e receitas futuramente.")
    # Exemplo de tabela
    st.table(pd.DataFrame({
        'Data': ['10/03', '08/03'],
        'Descrição': ['Parcela MRV', 'Conta Água'],
        'Categoria': ['Moradia', 'Contas Fixas'],
        'Valor': [-1272.24, -50.00]
    }))

with menu[5]: # Aba Simulador
    st.subheader("📈 Simulador de Investimentos / Amortização")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        v_ini = st.number_input("Valor Inicial", value=1000.0)
        taxa = st.number_input("Taxa Mensal (%)", value=1.0)
    with col_s2:
        tempo = st.number_input("Tempo (Meses)", value=12)
        st.write(f"Resultado Estimado: R$ {v_ini * (1 + taxa/100)**tempo:,.2f}")

with menu[6]: # Aba Categorias
    st.subheader("🏷️ Gestão de Categorias")
    st.write("Categorias Atuais: Moradia, Lazer, Carro, Mercado, Investimentos, Extras.")
