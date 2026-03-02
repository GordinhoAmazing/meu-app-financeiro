import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Financeiro Léo", layout="wide")

st.title("📊 Dashboard Financeiro Inteligente - Léo")

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
            
            # Remove colunas duplicadas mantendo a primeira ocorrência
            df = df.loc[:, ~df.columns.duplicated()]
            
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            if 'DATA' in df.columns and 'VALOR' in df.columns:
                col_desc = next((c for c in df.columns if 'DESC' in c), None)
                
                cols_to_keep = ['DATA', 'VALOR']
                if col_desc:
                    cols_to_keep.append(col_desc)
                
                df = df[cols_to_keep].copy()
                
                if col_desc:
                    df = df.rename(columns={col_desc: 'DESCRIÇÃO'})
                else:
                    if 'DESCRIÇÃO' not in df.columns:
                        df['DESCRIÇÃO'] = "Sem descrição"
                
                df = df.dropna(subset=['VALOR'])
                df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
                df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
                df['CATEGORIA'] = df['DESCRIÇÃO'].apply(categorizar)
                df['MES_REF'] = aba
                dados_lista.append(df)

        if dados_lista:
            df_final = pd.concat(dados_lista, ignore_index=True).dropna(subset=['DATA', 'VALOR'])
            
            meses = df_final['MES_REF'].unique()
            mes_sel = st.selectbox("Selecione o Mês", options=meses, index=len(meses)-1)
            
            df_mes = df_final[df_final['MES_REF'] == mes_sel].copy()
            
            receitas = df_mes[df_mes['VALOR'] > 0]['VALOR'].sum()
            despesas = df_mes[df_mes['VALOR'] < 0]['VALOR'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Receitas", f"R$ {receitas:,.2f}")
            c2.metric("Despesas", f"R$ {abs(despesas):,.2f}", delta_color="inverse")
            c3.metric("Saldo", f"R$ {(receitas + despesas):,.2f}")

            st.markdown("---")
            df_mes['DIA'] = df_mes['DATA'].dt.day
            df_graf = df_mes.groupby('DIA')['VALOR'].sum().reset_index()
            
            fig = px.bar(df_graf, x='DIA', y='VALOR', 
                         title=f"Movimentação Diária - {mes_sel}",
                         labels={'DIA': 'Dia do Mês', 'VALOR': 'Valor Líquido (R$)'},
                         color='VALOR', color_continuous_scale=['#ff5252', '#00c853'])
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📝 Detalhes dos Lançamentos")
            st.dataframe(df_mes[['DATA', 'DESCRIÇÃO', 'CATEGORIA', 'VALOR']].sort_values('DATA'), use_container_width=True)
        else:
            st.error("Não encontrei dados válidos. Verifique o arquivo.")
    except Exception as e:
        st.error(f"Erro: {e}")
else:
    st.info("Aguardando o upload do seu Excel... 🚀")
