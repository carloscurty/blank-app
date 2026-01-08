import streamlit as st
import runpy

# CONFIGURAÇÃO DEVE SER A PRIMEIRA LINHA
st.set_page_config(page_title="Gestão Takeat", layout="wide", page_icon="📊")

# ------ Sidebar
st.sidebar.title("MENU")

# Navegação
pages = [
    ("🛒 Vendas", "vendas.py"),
    ("🎫 Contas a Pagar", "cap.py"),
    ("💰 Caixa", "caixa.py"),
]

selection = st.sidebar.radio("Ir para:", [p[0] for p in pages])
selected_path = next(p[1] for p in pages if p[0] == selection)

# Executa a página selecionada
# Nota: runpy roda no mesmo processo, compartilhando st.session_state
runpy.run_path(selected_path, run_name="__main__")