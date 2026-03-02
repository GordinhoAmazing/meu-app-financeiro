import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Financeiro Léo", layout="wide")

st.title("📊 Dashboard Financeiro Inteligente - Léo")

# Função para categorizar automaticamente
def categorizar(desc):
    desc = str(desc).upper()
    if any(x in desc for x in ['MRV', 'AGUA', 'ENERGIA', 'CONDOMINIO', 'ALUGUEL', 'REFORMA']): return '🏠 Casa/Moradia'
    if any(x in desc for x in ['POSTO', 'GASOLINA', 'COMBUSTIVEL', 'UBER', 'MECANICO', 'ESTACIONAMENTO']): return '🚗 Transporte/Carro'
    if any(x in desc for x in ['MERCADO', 'MAX', 'SUPERMERCADO', 'PADARIA', 'AÇOUGUE']): return '🛒 Alimentação/Mercado'
    if any(x in desc for x in ['IFOOD', 'RESTAURANTE', 'PIZZA', 'LANCHE', 'CERVEJA', 'BAR']): return '🍔 Lazer/Comida Fora'
    if any(x in desc for x in ['NUBANK', 'CARTAO', 'FATURA', 'ITAU', 'SANTANDER']): return '💳 Cartão/Bancos'
    if any(x in desc for x in ['SALARIO', 'PIX RECEBIDO', 'TRANSFERENCIA RECEBIDA', 'COMISSAO']): return '💰 Receitas'
    if any(x in desc for x in ['CURSO', 'FACULDADE', 'LIVRO', 'TREINAMENTO']): return '📚 Educação'
    if any(x in desc for x in ['FARMACIA', 'MEDICO', 'EXAME', 'HOSPITAL']): return '🏥 Saúde'
    return '❓ Outros'

uploaded_file = st.file_uploader("Arraste seu arquivo Excel aqui", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        abas_validas = [s for s in xls.sheet_names if '-' in s]
        
        dados_lista = []
        for aba in abas_validas:
            df = pd.read_excel(uploaded_file, sheet_name=aba, skiprows=9)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            if 'DATA' in df.columns and 'VALOR' in df.columns:
                col_desc = next((c for c in df.columns if 'DESC' in c), None)
                df = df[['DATA', 'VALOR', (col_desc if col_desc else 'DATA')]].copy()
                if col_desc: df = df.rename(columns={col_desc: 'DESCRIÇÃO'})
                else: df['DESCRIÇÃO'] = "Sem descrição"
                
                df = df.dropna(subset=['VALOR'])
                df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
                df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
                df['CATEGORIA'] = df['DESCRIÇÃO'].apply(categorizar)
                df['MES_REF'] = aba
                dados_lista.append(df)

        if dados_lista:
            df_final = pd.concat(dados_lista, ignore_index=True).dropna(subset=['DATA', 'VALOR'])
            
            # Filtros Superiores
            c_filt1, c_filt2 = st.columns(2)
            mes_sel = c_filt1.selectbox("Selecione o Mês", options=df_final['MES_REF'].unique(), index=len(df_final['MES_REF'].unique())-1)
            
            df_mes = df_final[df_final['MES_REF'] == mes_sel].copy()
            
            # Métricas Principais
            receitas = df_mes[df_mes['VALOR'] > 0]['VALOR'].sum()
            despesas = df_mes[df_mes['VALOR'] < 0]['VALOR'].sum()
            
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("Entradas", f"R$ {receitas:,.2f}")
            m2.metric("Saídas", f"R$ {abs(despesas):,.2f}", delta_color="inverse")
            m3.metric("Saldo Líquido", f"R$ {(receitas + despesas):,.2f}")

            # Gráficos
            st.markdown("---")
            g1, g2 = st.columns(2)
            
            with g1:
                st.subheader("Gastos por Categoria")
                df_gastos = df_mes[df_mes['VALOR'] < 0].groupby('CATEGORIA')['VALOR'].sum().abs().reset_index()
                fig_pie = px.pie(df_gastos, values='VALOR', names='CATEGORIA', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with g2:
                st.subheader("Evolução Diária")
                df_mes['DIA'] = df_mes['DATA'].dt.day
                df_graf = df_mes.groupby('DIA')['VALOR'].sum().reset_index()
                fig_bar = px.bar(df_graf, x='DIA', y='VALOR', color='VALOR', color_continuous_scale=['#ff5252', '#00c853'])
                st.plotly_chart(fig_bar, use_container_width=True)

            # Tabela Detalhada
            st.markdown("---")
            st.subheader("📝 Lista de Lançamentos")
            st.dataframe(df_mes[['DATA', 'DESCRIÇÃO', 'CATEGORIA', 'VALOR']].sort_values('DATA'), use_container_width=True)
            
        else:
            st.error("Não encontrei dados válidos. Verifique o arquivo.")
    except Exception as e:
        st.error(f"Erro: {e}")
else:
    st.info("Aguardando o upload do seu Excel... 🚀")
