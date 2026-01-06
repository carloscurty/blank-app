import streamlit as st
import pandas as pd

st.markdown("### 💰 Caixa")
st.sidebar.markdown("### 💰 Filtros:")

# Aceitar também .xls e .xlsx
arquivo = st.file_uploader("Upload de arquivo", type=["csv", "xls", "xlsx"])
df = None

if arquivo:
    name = arquivo.name.lower() if hasattr(arquivo, "name") else ""
    try:
        if name.endswith(".csv"):
            arquivo.seek(0)
            df = pd.read_csv(arquivo)
            st.success("Arquivo CSV carregado com sucesso!")
        elif name.endswith((".xls", ".xlsx")):
            arquivo.seek(0)
            engine = "openpyxl" if name.endswith(".xlsx") else None
            df = pd.read_excel(arquivo, engine=engine) if engine else pd.read_excel(arquivo)
            st.success("Arquivo Excel carregado com sucesso!")
        else:
            st.error("Formato não suportado. Envie .csv, .xls ou .xlsx")
            
        # --- FORMATAÇÃO DE DATA (dd/mm/aaaa) ---
        if df is not None and not df.empty:
            # Tenta converter colunas que parecem datas mas estão como texto ou objetos
            # O parâmetro 'errors=ignore' mantém o original se não conseguir converter
            for col in df.columns:
                 if df[col].dtype == 'object':
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except (ValueError, TypeError):
                        pass

            # Aplica a formatação visual dd/mm/aaaa nas colunas que são de fato datas
            for col in df.select_dtypes(include=['datetime64', 'datetime']).columns:
                df[col] = df[col].dt.strftime('%d/%m/%Y')

            st.dataframe(df)
            
            st.write("Estatísticas:")
            st.write(df.describe(include='all'))

    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")