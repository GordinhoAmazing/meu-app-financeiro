import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Financeiro Léo", layout="wide")

st.title("📊 Dashboard Financeiro Léo")

# Upload do arquivo
uploaded_file = st.file_uploader("Arraste seu arquivo Excel aqui", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        # Filtra abas que parecem meses (ex: JAN-25, FEV-25)
        abas_validas = [s for s in xls.sheet_names if '-' in s]
        
        dados_lista = []
        for aba in abas_validas:
            # Lê a aba pulando as 9 linhas de cabeçalho do seu padrão
            df = pd.read_excel(uploaded_file, sheet_name=aba, skiprows=9)
            
            # Limpa nomes de colunas para evitar erros de texto/espaço
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            if 'DATA' in df.columns and 'VALOR' in df.columns:
                # Mantém só o que importa e remove linhas vazias
                df = df[['DATA', 'VALOR', 'DESCRIÇÃO']].copy()
                df = df.dropna(subset=['VALOR'])
                df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
                df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
                df['MES_REF'] = aba
                dados_lista.append(df)

        if dados_lista:
            df_final = pd.concat(dados_lista, ignore_index=True).dropna(subset=['DATA', 'VALOR'])
            
            # Seletor de Mês
            meses = df_final['MES_REF'].unique()
            mes_sel = st.selectbox("Selecione o Mês", options=meses, index=len(meses)-1)
            
            df_mes = df_final[df_final['MES_REF'] == mes_sel].copy()
            
            # Cálculos
            receitas = df_mes[df_mes['VALOR'] > 0]['VALOR'].sum()
            despesas = df_mes[df_mes['VALOR'] < 0]['VALOR'].sum()
            
            # Cards de Resumo
            c1, c2, c3 = st.columns(3)
            c1.metric("Receitas", f"R$ {receitas:,.2f}")
            c2.metric("Despesas", f"R$ {abs(despesas):,.2f}", delta_color="inverse")
            c3.metric("Saldo", f"R$ {(receitas + despesas):,.2f}")

            # Gráfico de Barras Diário (CORRIGIDO)
            st.markdown("---")
            # Criamos a coluna 'DIA' para o gráfico
            df_mes['DIA'] = df_mes['DATA'].dt.day
            df_graf = df_mes.groupby('DIA')['VALOR'].sum().reset_index()
            
            fig = px.bar(df_graf, x='DIA', y='VALOR', 
                         title=f"Movimentação Diária - {mes_sel}",
                         labels={'DIA': 'Dia do Mês', 'VALOR': 'Valor Líquido (R$)'},
                         color='VALOR', color_continuous_scale=['#ff5252', '#00c853'])
            st.plotly_chart(fig, use_container_width=True)

            # Tabela de Dados
            st.subheader("📝 Detalhes dos Lançamentos")
            st.dataframe(df_mes[['DATA', 'DESCRIÇÃO', 'VALOR']].sort_values('DATA'), use_container_width=True)
        else:
            st.error("Não encontrei dados nas colunas DATA e VALOR. Verifique o arquivo.")
            
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
else:
    st.info("Aguardando o upload do seu Excel... 🚀")
    
