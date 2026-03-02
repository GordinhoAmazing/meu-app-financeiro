import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Financeiro Léo", layout="wide")

st.title("📊 Dashboard Financeiro Alinhado - Léo")

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

def identificar_tipo(desc):
    desc = str(desc).upper()
    transfer_keywords = ['TRANSF', 'TRANSFERENCIA', 'TRANSFERÊNCIA', 'TED', 'DOC', 'PIX']
    fatura_keywords = ['FATURA', 'CARTAO', 'CARTÃO', 'CREDITO', 'NUBANK', 'ITAU', 'SANTANDER']
    resumo_keywords = ['VALOR FINAL', 'TOTAL', 'SALDO', 'PAGO', 'PAGAR', 'ATRASADO']

    if any(k in desc for k in resumo_keywords):
        return 'Resumo/Total'
    elif any(k in desc for k in transfer_keywords):
        return 'Transferência Interna'
    elif any(k in desc for k in fatura_keywords):
        return 'Fatura Cartão'
    else:
        return 'Normal'

uploaded_file = st.file_uploader("Arraste seu arquivo Excel aqui", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        abas_validas = [s for s in xls.sheet_names if '-' in s]

        dados_lista = []
        saldos_iniciais = {}
        for aba in abas_validas:
            # Lê a aba inteira para pegar saldo inicial e lançamentos
            df_raw = pd.read_excel(uploaded_file, sheet_name=aba, header=None)

            # Saldo inicial está na linha 1, coluna 2 (C)
            saldo_inicial = None
            try:
                saldo_inicial = float(str(df_raw.iloc[1, 2]).replace('R$', '').replace('.', '').replace(',', '.').strip())
            except:
                saldo_inicial = 0
            saldos_iniciais[aba] = saldo_inicial

            # Lê lançamentos a partir da linha 9 (onde está o cabeçalho)
            df = pd.read_excel(uploaded_file, sheet_name=aba, skiprows=8)
            df.columns = [str(c).strip().upper() for c in df.columns]
            df = df.loc[:, ~df.columns.duplicated()]

            if 'DATA' in df.columns and 'VALOR' in df.columns:
                col_loc = next((c for c in df.columns if 'LOCAL' in c), None)
                col_desc = next((c for c in df.columns if 'DESC' in c), None)

                df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
                df = df.dropna(subset=['VALOR'])
                df = df[df['VALOR'] != 0]

                if col_loc and col_desc:
                    df['DESC_COMPLETA'] = df[col_loc].astype(str) + " - " + df[col_desc].astype(str)
                elif col_desc:
                    df['DESC_COMPLETA'] = df[col_desc].astype(str)
                else:
                    df['DESC_COMPLETA'] = "Sem descrição"

                # Remove linhas de resumo/total
                df = df[~df['DESC_COMPLETA'].str.upper().str.contains('|'.join(['VALOR FINAL', 'TOTAL', 'SALDO', 'PAGO', 'PAGAR', 'ATRASADO']))]

                try:
                    partes_aba = aba.split('-')
                    num_mes = meses_map.get(partes_aba[0].strip()[:3].upper(), 1)
                    ano = int("20" + partes_aba[1].strip()[:2])
                    df['DATA_REAL'] = df['DATA'].apply(lambda d: datetime(ano, num_mes, int(float(d))) if str(d).replace('.', '').isdigit() else None)
                except:
                    df['DATA_REAL'] = pd.to_datetime(df['DATA'], errors='coerce')

                df['CATEGORIA'] = df['DESC_COMPLETA'].apply(categorizar)
                df['TIPO'] = df['DESC_COMPLETA'].apply(identificar_tipo)
                df['MES_REF'] = aba
                dados_lista.append(df[['DATA_REAL', 'DESC_COMPLETA', 'CATEGORIA', 'VALOR', 'TIPO', 'MES_REF']])

        if dados_lista:
            df_final = pd.concat(dados_lista, ignore_index=True)
            mes_sel = st.selectbox("Selecione o Mês para Conferência", options=df_final['MES_REF'].unique(), index=len(df_final['MES_REF'].unique())-1)
            df_mes = df_final[df_final['MES_REF'] == mes_sel].copy()

            saldo_inicial = saldos_iniciais.get(mes_sel, 0)

            df_validos = df_mes[df_mes['DATA_REAL'].notnull()]

            receitas = df_validos[(df_validos['VALOR'] > 0) & (df_validos['TIPO'] == 'Normal')]['VALOR'].sum()
            despesas = df_validos[(df_validos['VALOR'] < 0) & (df_validos['TIPO'] == 'Normal')]['VALOR'].sum()

            saldo_final = saldo_inicial + receitas + despesas

            st.subheader(f"Resumo de {mes_sel}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
            m2.metric("Entradas (Receitas)", f"R$ {receitas:,.2f}")
            m3.metric("Saídas (Despesas)", f"R$ {abs(despesas):,.2f}")
            m4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

            st.markdown("---")
            st.subheader("🔍 Conferência Detalhada")
            st.write("Compare os valores abaixo com seu Excel:")
            df_tab = df_mes.copy()
            df_tab['DATA'] = df_tab['DATA_REAL'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_tab[['DATA', 'DESC_COMPLETA', 'CATEGORIA', 'VALOR', 'TIPO']].sort_values('DATA'), use_container_width=True)

            csv = df_tab.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Dados deste Mês (CSV)", csv, f"conferencia_{mes_sel}.csv", "text/csv")

        else:
            st.error("Ainda não consegui alinhar os dados. Verifique se a palavra 'DATA' está na coluna A da sua tabela.")
    except Exception as e:
        st.error(f"Erro técnico: {e}")
else:
    st.info("Aguardando seu arquivo Excel para bater os números... 🚀")
