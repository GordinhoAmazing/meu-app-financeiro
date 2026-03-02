import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Financeiro Léo", layout="wide")

st.title("📊 Dashboard Financeiro de Precisão - Léo")

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
    if any(x in desc for x in ['SALARIO', 'PIX RECEBIDO', 'COMISSAO', 'PAGOU', 'RENDIMENTOS']): return '💰 Receitas'
    return '❓ Outros'

uploaded_file = st.file_uploader("Arraste seu arquivo Excel aqui", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        abas_validas = [s for s in xls.sheet_names if '-' in s]
        
        dados_lista = []
        for aba in abas_validas:
            df_raw = pd.read_excel(uploaded_file, sheet_name=aba, header=None)
            
            linha_inicio = None
            for i, row in df_raw.iterrows():
                if "DATA" in [str(v).strip().upper() for v in row.values]:
                    linha_inicio = i
                    break
            
            if linha_inicio is not None:
                df = pd.read_excel(uploaded_file, sheet_name=aba, skiprows=linha_inicio + 1, header=None)
                colunas = [str(c).strip().upper() for c in df_raw.iloc[linha_inicio].values]
                df.columns = colunas
                df = df.loc[:, ~df.columns.duplicated()]
                
                if 'DATA' in df.columns and 'VALOR' in df.columns:
                    # Pega Local e Descrição para não perder nada
                    col_loc = next((c for c in df.columns if 'LOCAL' in c), None)
                    col_desc = next((c for c in df.columns if 'DESC' in c), None)
                    
                    df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
                    df = df.dropna(subset=['VALOR'])
                    df = df[df['VALOR'] != 0] # Ignora zeros que não afetam saldo
                    
                    # Cria uma descrição completa
                    df['DESC_COMPLETA'] = df[col_loc].astype(str) + " - " + df[col_desc].astype(str) if col_loc and col_desc else df[col_desc if col_desc else 'DATA'].astype(str)
                    
                    # Monta Data
                    try:
                        partes_aba = aba.split('-')
                        num_mes = meses_map.get(partes_aba[0].strip()[:3].upper(), 1)
                        ano = int("20" + partes_aba[1].strip()[:2])
                        df['DATA_REAL'] = df['DATA'].apply(lambda d: datetime(ano, num_mes, int(float(d))) if str(d).replace('.','').isdigit() else None)
                    except:
                        df['DATA_REAL'] = pd.to_datetime(df['DATA'], errors='coerce')

                    df['CATEGORIA'] = df['DESC_COMPLETA'].apply(categorizar)
                    df['MES_REF'] = aba
                    dados_lista.append(df[['DATA_REAL', 'DESC_COMPLETA', 'CATEGORIA', 'VALOR', 'MES_REF']])

        if dados_lista:
            df_final = pd.concat(dados_lista, ignore_index=True).dropna(subset=['DATA_REAL'])
            mes_sel = st.selectbox("Selecione o Mês para Conferência", options=df_final['MES_REF'].unique(), index=len(df_final['MES_REF'].unique())-1)
            df_mes = df_final[df_final['MES_REF'] == mes_sel].copy()
            
            receitas = df_mes[df_mes['VALOR'] > 0]['VALOR'].sum()
            despesas = df_mes[df_mes['VALOR'] < 0]['VALOR'].sum()
            
            st.subheader(f"Resumo de {mes_sel}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Entradas (Receitas)", f"R$ {receitas:,.2f}")
            m2.metric("Saídas (Despesas)", f"R$ {abs(despesas):,.2f}")
            m3.metric("Saldo do Mês", f"R$ {(receitas + despesas):,.2f}")

            st.markdown("---")
            st.subheader("🔍 Conferência Detalhada")
            st.write("Compare os valores abaixo com seu Excel:")
            df_tab = df_mes.copy()
            df_tab['DATA'] = df_tab['DATA_REAL'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_tab[['DATA', 'DESC_COMPLETA', 'CATEGORIA', 'VALOR']].sort_values('DATA'), use_container_width=True)
            
            # Botão para baixar e conferir no Excel se precisar
            csv = df_tab.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Dados deste Mês (CSV)", csv, f"conferencia_{mes_sel}.csv", "text/csv")

        else:
            st.error("Ainda não consegui alinhar os dados. Verifique se a palavra 'DATA' está na coluna A da sua tabela.")
    except Exception as e:
        st.error(f"Erro técnico: {e}")
else:
    st.info("Aguardando seu arquivo Excel para bater os números... 🚀")
    
