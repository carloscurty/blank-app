import streamlit as st
import pandas as pd
import openpyxl
from openpyxl.styles import colors

# --- INÍCIO DA CORREÇÃO (Monkey Patch para erro de Cores) ---
original_color_init = colors.Color.__init__

def patched_color_init(self, rgb=None, indexed=None, auto=None, theme=None, tint=0.0, index=None):
    try:
        original_color_init(self, rgb=rgb, indexed=indexed, auto=auto, theme=theme, tint=tint, index=index)
    except ValueError:
        pass

colors.Color.__init__ = patched_color_init
# --- FIM DA CORREÇÃO ---

st.markdown("### 🎫 Contas a Pagar")
st.sidebar.markdown("# 🎫 Contas a Pagar")

st.write("Aqui você pode gerenciar suas contas a pagar.")

try:
    arquivo = pd.read_excel('contas_a_pagar.xlsx')

    # --- FORMATAÇÃO DE DATA ESPECÍFICA ---
    if not arquivo.empty:
        # Lista das colunas que sabemos que são datas
        colunas_datas = ['Vencimento', 'Competência', 'Pago em']
        
        for col in colunas_datas:
            # Verifica se a coluna existe no arquivo
            if col in arquivo.columns:
                # 1. Força a conversão para datetime (tratando erros como NaT)
                arquivo[col] = pd.to_datetime(arquivo[col], errors='coerce')
                # 2. Formata para dd/mm/aaaa
                arquivo[col] = arquivo[col].dt.strftime('%d/%m/%Y')
                # 3. Limpa valores vazios (NaT viram string vazia para ficar bonito na tabela)
                arquivo[col] = arquivo[col].fillna('')

    st.dataframe(arquivo)
    
except FileNotFoundError:
    st.error("O arquivo 'contas_a_pagar.xlsx' não foi encontrado.")
except Exception as e:
    st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")