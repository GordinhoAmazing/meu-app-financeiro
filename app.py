import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata

st.set_page_config(page_title="Financeiro Léo - Dashboard", layout="wide")

st.title("📊 Financeiro Léo - Dashboard Consolidado")

def normalize(text):
    if text is None:
        return ""
    t = str(text)
    t = unicodedata.normalize("NFKD", t).encode("ASCII", "ignore").decode()  # remove acentos
    return t.strip().lower()

uploaded_file = st.file_uploader("Envie seu arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file is None:
    st.info("Aguardando upload do arquivo Excel (.xlsx)...")
else:
    try:
        xls = pd.ExcelFile(uploaded_file)
    except Exception as e:
        st.error("Erro ao abrir o arquivo. Confirme que é um .xlsx válido.")
        st.exception(e)
        st.stop()

    st.write(f"Abas encontradas: {xls.sheet_names}")

    dados = []
    for sheet in xls.sheet_names:
        try:
            raw = pd.read_excel(uploaded_file, sheet_name=sheet, header=None)
        except Exception:
            # se não conseguir ler com header=None, pula
            st.warning(f"Não consegui ler a aba: {sheet}")
            continue

        # procura a linha que contém "DATA" (até a linha 20)
        header_row = None
        max_search = min(20, len(raw))
        for i in range(max_search):
            row_vals = raw.iloc[i].astype(str).fillna("").apply(lambda v: normalize(v))
            if any(v == "data" for v in row_vals):
                header_row = i
                break

        # Se não encontrar, tenta um fallback pulando 9 linhas (padrão observado)
        if header_row is None:
            header_row = 9

        # Lê a aba novamente, usando a linha encontrada como cabeçalho
        try:
            df = pd.read_excel(uploaded_file, sheet_name=sheet, skiprows=header_row, header=0)
        except Exception:
            st.warning(f"Erro ao reler a aba {sheet} com skiprows={header_row}. Pulando.")
            continue

        # Normaliza nomes de colunas e cria mapeamento normalizado -> original
        orig_cols = list(df.columns)
        norm_map = {normalize(c): c for c in orig_cols}

        # verifica se temos colunas de data e valor (usando normalização)
        if "data" not in norm_map or "valor" not in norm_map:
            st.info(f"Aba '{sheet}' ignorada — não localizei colunas DATA e VALOR.")
            continue

        col_data = norm_map["data"]
        col_valor = norm_map["valor"]
        col_descricao = norm_map.get("descricao") or norm_map.get("descrição") or None

        # seleciona apenas as colunas relevantes (se existirem)
        keep = [col_data, col_valor] + ([col_descricao] if col_descricao else [])
        df = df[[c for c in keep if c in df.columns]].copy()

        # padroniza nomes para 'data','descricao','valor'
        rename_map = {col_data: "data", col_valor: "valor"}
        if col_descricao:
            rename_map[col_descricao] = "descricao"
        df = df.rename(columns=rename_map)

        # converte tipos
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df["aba_origem"] = sheet

        # remove linhas sem data ou sem valor
        df = df.dropna(subset=["data", "valor"])

        if not df.empty:
            dados.append(df)
        else:
            st.info(f"Aba '{sheet}' não trouxe linhas válidas após limpeza.")

    if not dados:
        st.error("Não consegui extrair dados válidos de nenhuma aba. Verifique o arquivo e a posição das colunas.")
    else:
        df_all = pd.concat(dados, ignore_index=True)
        df_all["mes_ano"] = df_all["data"].dt.strftime("%Y-%m")
        meses = sorted(df_all["mes_ano"].unique())
        mes_sel = st.selectbox("Selecione mês para analisar", options=meses, index=len(meses)-1)

        df_mes = df_all[df_all["mes_ano"] == mes_sel].copy()
        receita = df_mes[df_mes["valor"] > 0]["valor"].sum()
        despesa = df_mes[df_mes["valor"] < 0]["valor"].sum()
        saldo = receita + despesa

        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {receita:,.2f}")
        c2.metric("Despesas", f"R$ {abs(despesa):,.2f}", delta_color="inverse")
        c3.metric("Saldo do Mês", f"R$ {saldo:,.2f}")

        st.markdown("---")
        st.subheader(f"Fluxo Diário — {mes_sel}")
        df_graf = df_mes.groupby(df_mes["data"].dt.day)["valor"].sum().reset_index().rename(columns={"data": "dia"})
        fig = px.bar(df_graf, x="data", y="valor", title="Movimentação diária", labels={"data": "Dia do mês", "valor": "Valor (R$)"})
        st.plotly_chart(fig, width="stretch")

        st.markdown("---")
        st.subheader("Detalhes dos lançamentos")
        # garante colunas para exibir
        show_cols = ["data", "descricao", "valor"]
        show_cols = [c for c in show_cols if c in df_mes.columns]
        st.dataframe(df_mes.sort_values("data")[show_cols], width="stretch")
