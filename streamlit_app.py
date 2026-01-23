import streamlit as st
import runpy
import conciliacao  # Importa o módulo novo que criamos

# CONFIGURAÇÃO DEVE SER A PRIMEIRA LINHA
st.set_page_config(page_title="Gestão Takeat", layout="wide", page_icon="📊")

# ------ Sidebar
st.sidebar.title("MENU")

# Lista de Opções do Menu
menu_options = [
    "🛒 Vendas", 
    "🎫 Contas a Pagar", 
    "💰 Caixas", 
    "⚖️ Conciliação"  # Novo item adicionado
]

selection = st.sidebar.radio("Ir para:", menu_options)

# ------ Lógica de Roteamento (Router)
if selection == "⚖️ Conciliação":
    # Executa o módulo novo chamando a função app()
    conciliacao.app()

else:
    # Mapeamento para os arquivos antigos (Legacy)
    path_map = {
        "🛒 Vendas": "vendas.py",
        "🎫 Contas a Pagar": "cap.py",
        "💰 Caixas": "caixa.py"
    }
    
    # Executa via runpy (mantendo o funcionamento atual dos outros arquivos)
    if selection in path_map:
        runpy.run_path(path_map[selection], run_name="__main__")