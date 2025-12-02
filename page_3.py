import streamlit as st
import pandas as pd

st.markdown("# Caixa 💰")
st.sidebar.markdown("# Caixa 💰")

arquivo=st.file_uploader("Upload de arquivo", type=["csv", "xlsx"])
if arquivo:
    try:
        df=pd.read_csv(arquivo)
        st.success("Arquivo CSV carregado com sucesso!")
    except Exception as e:
        try:
            df=pd.read_excel(arquivo)
            st.success("Arquivo Excel carregado com sucesso!")
        except Exception as e:
            st.error("Erro ao carregar o arquivo. Por favor, envie um arquivo CSV ou Excel válido.")

    #st.dataframe(df)

#print(df.describe())