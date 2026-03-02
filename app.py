import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Financeiro Léo", layout="wide")

st.title("📊 Dashboard Financeiro Inteligente - Léo")

meses_map = {
    'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
    'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
}

def categorizar(desc):
    desc = str(desc).upper()
    if any(x in desc for x in ['MRV', 'AGUA', 'ENERGIA', 'CONDOMINIO', 'ALUGUEL', 'REFORMA', 'CASA']): return '🏠 Casa'
    if any(x in desc for x in ['POSTO', 'GASOLINA', 'COMBUSTIVEL', 'UBER', 'MECANICO', 'ESTACIONAMENTO', 'PLAZA', 'IGUATEMI']): return '🚗 Transporte'
    if any(x in desc for x in ['MERCADO', 'MAX', 'PADARIA', 'AÇOUGUE', 'COCA', 'NUTELLA']): return '🛒 Mercado'
    if any(x in desc for x in ['IFOOD', 'RESTAURANTE', 'PIZZA', 'LANCHE', 'CERVEJA', 'BAR', 'ALMOÇO', 'JANTA', 'BK']): return '🍔 Lazer/Comida'
    if any(x in desc for x in ['NUBANK', 'CARTAO', 'FATURA', 'ITAU', 'SANTANDER', 'PICPAY']): return '💳 Bancos/Cartão'
    if any(x in desc for x in ['SALARIO', 'PIX RECEBIDO', 'COMISSAO', 'PAGOU']): return '💰 Receitas'
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
                
                # Renomeia a coluna de descrição apenas se não existir 'DESCRIÇÃO'
                if col_desc and 'DESCRIÇÃO' not in df.columns:
                    df = df.rename(columns={col_desc: 'DESCRIÇÃO'})
                elif 'DESCRIÇÃO' not in df.columns:
                    df['DESCRIÇÃO'] = "Sem descrição"
                
                df = df.dropna(subset=['VALOR'])
                
                try:
                    partes_aba = aba.split('-')
                    nome_mes = partes_aba[0].strip()[:3].upper()
                    ano = int("20" + partes_aba[1].strip()[:2])
                    num_mes = meses_map.get(nome_mes, 1)
                    
                    def montar_data(dia):
                        try:
                            d = int(float(dia))
                            return datetime(ano, num_mes, d)
                        except: return None
                    
                    df['DATA_REAL'] = df['DATA'].apply(montar_data)
                except:
                    df['DATA_REAL'] = pd.to_datetime(df['DATA'], errors='coerce')

                df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
                df['CATEGORIA'] = df['DESCRIÇÃO'].apply(categorizar)
                df['MES_REF'] = aba
                dados_lista.append(df)

        if dados_lista:
            df_final = pd.concat(dados_lista, ignore_index=True).dropna(subset=['VALOR'])
            mes_sel = st.selectbox("Selecione o Mês", options=df_final['MES_REF'].unique(), index=len(df_final['MES_REF'].unique())-1)
            df_mes = df_final[df_final['MES_REF'] == mes_sel].copy()
            
            receitas = df_mes[df_mes['VALOR'] > 0]['VALOR'].sum()
            despesas = df_mes[df_mes['VALOR'] < 0]['VALOR'].sum()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Receitas", f"R$ {receitas:,.2f}")
            m2.metric("Despesas", f"R$ {abs(despesas):,.2f}", delta_color="inverse")
            m3.metric("Saldo", f"R$ {(receitas + despesas):,.2f}")

            st.markdown("---")
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("Gastos por Categoria")
                df_gastos = df_mes[df_mes['VALOR'] < 0].groupby('CATEGORIA')['VALOR'].sum().abs().reset_index()
                fig_pie = px.pie(df_gastos, values='VALOR', names='CATEGORIA', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            with g2:
                st.subheader("Fluxo Diário")
                df_mes['DIA_GRAF'] = df_mes['DATA_REAL'].dt.day
                df_graf = df_mes.groupby('DIA_GRAF')['VALOR'].sum().reset_index()
                fig_bar = px.bar(df_graf, x='DIA_GRAF', y='VALOR', color='VALOR', color_continuous_scale=['#ff5252', '#00c853'])
                st.plotly_chart(fig_bar, use_container_width=True)

            st.subheader("📝 Detalhes dos Lançamentos")
            df_tab = df_mes.copy()
            df_tab['DATA'] = df_tab['DATA_REAL'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_tab[['DATA', 'DESCRIÇÃO', 'CATEGORIA', 'VALOR']].sort_values('DATA'), use_container_width=True)
        else:
            st.error("Não encontrei dados válidos.")
    except Exception as e:
        st.error(f"Erro: {e}")
else:
    st.info("Aguardando o upload do seu Excel... 🚀")
