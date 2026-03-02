import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Financeiro Léo - Dashboard", layout="wide")

st.title("Financeiro Léo - Dashboard Consolidado")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Faça upload do seu arquivo Excel", type=["xlsx"])

if uploaded_file:
    # Carregar todas as abas
    xls = pd.ExcelFile(uploaded_file)
    st.write(f"Abas encontradas: {xls.sheet_names}")

    # Lista para armazenar dados consolidados
    df_list = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)

        # Tentar identificar colunas importantes (Data, Descrição, Valor)
        # Ajuste conforme seu arquivo real
        cols = df.columns.str.lower()
        if 'data' in cols and 'valor' in cols:
            # Padronizar nomes
            df = df.rename(columns=lambda x: x.strip().lower())
            df = df[['data', 'descrição', 'valor']] if 'descrição' in df.columns else df[['data', 'valor']]
            df_list.append(df)
        else:
            st.warning(f"Aba '{sheet}' ignorada por não conter colunas Data e Valor")

    if df_list:
        df_all = pd.concat(df_list, ignore_index=True)
        df_all['data'] = pd.to_datetime(df_all['data'], errors='coerce')
        df_all = df_all.dropna(subset=['data', 'valor'])

        st.subheader("Dados Consolidados")
        st.dataframe(df_all)

        # Filtro por mês
        meses = df_all['data'].dt.to_period('M').unique()
        mes_selecionado = st.selectbox("Selecione o mês para análise", options=sorted(meses.astype(str)))

        df_mes = df_all[df_all['data'].dt.to_period('M').astype(str) == mes_selecionado]

        st.subheader(f"Resumo do mês {mes_selecionado}")
        receita = df_mes[df_mes['valor'] > 0]['valor'].sum()
        despesa = df_mes[df_mes['valor'] < 0]['valor'].sum()
        saldo = receita + despesa

        col1, col2, col3 = st.columns(3)
        col1.metric("Receita", f"R$ {receita:,.2f}")
        col2.metric("Despesa", f"R$ {abs(despesa):,.2f}")
        col3.metric("Saldo", f"R$ {saldo:,.2f}")

        # Gráfico receita x despesa
        df_graf = df_mes.groupby(df_mes['data'].dt.day)['valor'].sum().reset_index()
        fig = px.bar(df_graf, x='data', y='valor', title="Fluxo Diário", labels={'data': 'Dia', 'valor': 'Valor (R$)'})
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Nenhum dado válido encontrado nas abas do arquivo.")

else:
    st.info("Por favor, faça upload do arquivo Excel para começar.")
    
