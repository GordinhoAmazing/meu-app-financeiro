import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Financeiro Léo - Dashboard", layout="wide")

st.title("📊 Financeiro Léo - Dashboard Consolidado")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Faça upload do seu arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    # Carregar todas as abas
    xls = pd.ExcelFile(uploaded_file)
    st.write(f"Abas encontradas: {xls.sheet_names}")

    # Lista para armazenar dados consolidados
    df_list = []

    for sheet in xls.sheet_names:
        # Lemos a aba pulando as 9 primeiras linhas (onde ficam seus saldos iniciais)
        df = pd.read_excel(uploaded_file, sheet_name=sheet, skiprows=9)

        # CORREÇÃO DO ERRO: Forçamos os nomes das colunas a serem texto (string)
        df.columns = [str(c).strip().lower() for c in df.columns]
        cols = df.columns

        # Procuramos pelas colunas DATA e VALOR
        if 'data' in cols and 'valor' in cols:
            # Pegamos apenas as colunas que existem (data, valor e descrição se houver)
            colunas_uteis = [c for c in ['data', 'descrição', 'valor'] if c in cols]
            df = df[colunas_uteis].copy()
            df['aba_origem'] = sheet
            df_list.append(df)
        else:
            st.warning(f"Aba '{sheet}' ignorada (não encontrei as colunas DATA e VALOR na linha 10)")

    if df_list:
        # Junta tudo em uma tabela só
        df_all = pd.concat(df_list, ignore_index=True)
        
        # Limpeza final dos dados
        df_all['data'] = pd.to_datetime(df_all['data'], errors='coerce')
        df_all = df_all.dropna(subset=['data', 'valor'])
        df_all['valor'] = pd.to_numeric(df_all['valor'], errors='coerce')

        st.subheader("✅ Dados Consolidados com Sucesso")
        
        # Filtro por mês
        df_all['mes_ano'] = df_all['data'].dt.strftime('%Y-%m')
        meses = sorted(df_all['mes_ano'].unique())
        mes_selecionado = st.selectbox("Selecione o mês para análise", options=meses, index=len(meses)-1)

        df_mes = df_all[df_all['mes_ano'] == mes_selecionado]

        # Resumo Financeiro
        receita = df_mes[df_mes['valor'] > 0]['valor'].sum()
        despesa = df_mes[df_mes['valor'] < 0]['valor'].sum()
        saldo = receita + despesa

        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {receita:,.2f}")
        c2.metric("Despesas", f"R$ {abs(despesa):,.2f}", delta_color="inverse")
        c3.metric("Saldo do Mês", f"R$ {saldo:,.2f}")

        # Gráfico de Barras Diário
        st.markdown("---")
        st.subheader(f"Fluxo de Caixa - {mes_selecionado}")
        df_graf = df_mes.groupby(df_mes['data'].dt.day)['valor'].sum().reset_index()
        fig = px.bar(df_graf, x='data', y='valor', 
                     title="Saldo Diário (Entradas - Saídas)",
                     labels={'data': 'Dia do Mês', 'valor': 'Valor Líquido (R$)'},
                     color='valor', color_continuous_scale=['#ff5252', '#00c853'])
        st.plotly_chart(fig, use_container_width=True)

        # Tabela de Detalhes
        st.subheader("📝 Detalhes dos Lançamentos")
        st.dataframe(df_mes[['data', 'descrição', 'valor']].sort_values(by='data'), use_container_width=True)

    else:
        st.error("Não consegui extrair dados de nenhuma aba. Verifique se os lançamentos começam na linha 10.")

else:
    st.info("Aguardando o upload do arquivo Excel para começar... 🚀")
    
