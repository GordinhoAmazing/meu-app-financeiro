import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Planejamento Financeiro Léo", layout="wide", initial_sidebar_state="collapsed")

# CSS para deixar a interface "Vibe DeepAgent"
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #ffffff; }
    div[data-testid="stMetricLabel"] { font-size: 16px; color: #a3a8b4; }
    .stDataFrame { border: 1px solid #262730; border-radius: 10px; }
    .stSelectbox label { color: #a3a8b4; }
    h1, h2, h3 { color: #ffffff; font-family: 'Inter', sans-serif; }
    .card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f6feb;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Planejamento Financeiro - Léo")
st.markdown("---")

meses_map = {'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6, 'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12}

def categorizar(desc):
    desc = str(desc).upper()
    if any(x in desc for x in ['MRV', 'AGUA', 'ENERGIA', 'CONDOMINIO', 'ALUGUEL', 'REFORMA', 'CASA']): return '🏠 Casa'
    if any(x in desc for x in ['POSTO', 'GASOLINA', 'COMBUSTIVEL', 'UBER', 'MECANICO', 'ESTACIONAMENTO', 'PLAZA', 'IGUATEMI']): return '🚗 Transporte'
    if any(x in desc for x in ['MERCADO', 'MAX', 'PADARIA', 'AÇOUGUE', 'COCA', 'NUTELLA']): return '🛒 Mercado'
    if any(x in desc for x in ['IFOOD', 'RESTAURANTE', 'PIZZA', 'LANCHE', 'CERVEJA', 'BAR', 'ALMOÇO', 'JANTA', 'BK']): return '🍔 Lazer/Comida'
    if any(x in desc for x in ['NUBANK', 'CARTAO', 'FATURA', 'ITAU', 'SANTANDER', 'PICPAY']): return '💳 Bancos/Cartão'
    if any(x in desc for x in ['SALARIO', 'PIX RECEBIDO', 'COMISSAO', 'PAGOU', 'RENDIMENTOS']): return '💰 Receitas'
    return '❓ Outros'

uploaded_file = st.file_uploader("📁 Arraste seu arquivo Excel aqui", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        abas_validas = [s for s in xls.sheet_names if '-' in s]
        dados_lista = []
        saldos_iniciais = {}

        for aba in abas_validas:
            df_raw = pd.read_excel(uploaded_file, sheet_name=aba, header=None)
            # Saldo Inicial (Linha 1, Coluna C)
            try: saldo_inicial = float(str(df_raw.iloc[0, 2]).replace('R$', '').replace('.', '').replace(',', '.').strip())
            except: saldo_inicial = 0
            saldos_iniciais[aba] = saldo_inicial

            # Lançamentos (A partir da linha 9)
            df = pd.read_excel(uploaded_file, sheet_name=aba, skiprows=8)
            df.columns = [str(c).strip().upper() for c in df.columns]
            df = df.loc[:, ~df.columns.duplicated()]

            if 'DATA' in df.columns and 'VALOR' in df.columns:
                col_loc = next((c for c in df.columns if 'LOCAL' in c), None)
                col_desc = next((c for c in df.columns if 'DESC' in c), None)
                df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
                df = df.dropna(subset=['VALOR'])
                df = df[df['VALOR'] != 0]
                df['DESC_COMPLETA'] = (df[col_loc].astype(str) + " - " + df[col_desc].astype(str)) if col_loc and col_desc else df[col_desc].astype(str)
                
                # Filtro de segurança: se não tem data, não é lançamento
                try:
                    partes = aba.split('-')
                    num_mes = meses_map.get(partes[0].strip()[:3].upper(), 1)
                    ano = int("20" + partes[1].strip()[:2])
                    df['DATA_REAL'] = df['DATA'].apply(lambda d: datetime(ano, num_mes, int(float(d))) if str(d).replace('.','').isdigit() else None)
                except: df['DATA_REAL'] = pd.to_datetime(df['DATA'], errors='coerce')
                
                df = df.dropna(subset=['DATA_REAL'])
                df['CATEGORIA'] = df['DESC_COMPLETA'].apply(categorizar)
                df['MES_REF'] = aba
                dados_lista.append(df[['DATA_REAL', 'DESC_COMPLETA', 'CATEGORIA', 'VALOR', 'MES_REF']])

        if dados_lista:
            df_final = pd.concat(dados_lista, ignore_index=True)
            
            # Seletor de Período (Estilo DeepAgent)
            c_sel1, c_sel2 = st.columns([1, 3])
            mes_sel = c_sel1.selectbox("Período", options=df_final['MES_REF'].unique(), index=len(df_final['MES_REF'].unique())-1)
            
            df_mes = df_final[df_final['MES_REF'] == mes_sel].copy()
            s_ini = saldos_iniciais.get(mes_sel, 0)
            receitas = df_mes[df_mes['VALOR'] > 0]['VALOR'].sum()
            despesas = df_mes[df_mes['VALOR'] < 0]['VALOR'].sum()
            saldo_real = s_ini + receitas + despesas

            # Cards de Resumo (Estilo DeepAgent)
            st.markdown("### Dashboard")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f'<div class="card" style="border-left-color: #238636;">'
                            f'<p style="color:#a3a8b4;margin:0;">Renda Real</p>'
                            f'<h2 style="color:#2ea043;margin:0;">R$ {receitas:,.2f}</h2>'
                            f'</div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="card" style="border-left-color: #da3633;">'
                            f'<p style="color:#a3a8b4;margin:0;">Total de Despesas</p>'
                            f'<h2 style="color:#f85149;margin:0;">R$ {abs(despesas):,.2f}</h2>'
                            f'</div>', unsafe_allow_html=True)
            with m3:
                cor_saldo = "#1f6feb" if saldo_real >= 0 else "#da3633"
                st.markdown(f'<div class="card" style="border-left-color: {cor_saldo};">'
                            f'<p style="color:#a3a8b4;margin:0;">Saldo Real (Final)</p>'
                            f'<h2 style="color:{cor_saldo};margin:0;">R$ {saldo_real:,.2f}</h2>'
                            f'</div>', unsafe_allow_html=True)

            # Gráficos
            st.markdown("---")
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("Distribuição de Gastos")
                df_pie = df_mes[df_mes['VALOR'] < 0].groupby('CATEGORIA')['VALOR'].sum().abs().reset_index()
                fig_pie = px.pie(df_pie, values='VALOR', names='CATEGORIA', hole=0.5, color_discrete_sequence=px.colors.qualitative.G10)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                st.plotly_chart(fig_pie, use_container_width=True)
            with g2:
                st.subheader("Evolução Diária")
                df_bar = df_mes.groupby(df_mes['DATA_REAL'].dt.day)['VALOR'].sum().reset_index()
                fig_bar = px.bar(df_bar, x='DATA_REAL', y='VALOR', color='VALOR', color_continuous_scale='RdYlGn')
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                st.plotly_chart(fig_bar, use_container_width=True)

            # Tabela de Lançamentos
            st.markdown("### 📝 Lançamentos")
            df_tab = df_mes.copy()
            df_tab['DATA'] = df_tab['DATA_REAL'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_tab[['DATA', 'DESC_COMPLETA', 'CATEGORIA', 'VALOR']].sort_values('DATA', ascending=False), use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
else:
    st.info("Aguardando seu arquivo Excel para gerar o Dashboard... 🚀")
