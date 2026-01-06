import streamlit as st
import pandas as pd
import openpyxl
from openpyxl.styles import colors
import datetime

# --- INÍCIO DA CORREÇÃO (Monkey Patch para erro de Cores) ---
original_color_init = colors.Color.__init__

def patched_color_init(self, rgb=None, indexed=None, auto=None, theme=None, tint=0.0, index=None):
    try:
        original_color_init(self, rgb=rgb, indexed=indexed, auto=auto, theme=theme, tint=tint, index=index)
    except ValueError:
        pass

colors.Color.__init__ = patched_color_init
# --- FIM DA CORREÇÃO ---

st.markdown("# Contas a Pagar 🎫")
st.sidebar.markdown("# Contas a Pagar 🎫")

st.write("Aqui você pode gerenciar suas contas a pagar.")

try:
    arquivo = pd.read_excel('contas_a_pagar.xlsx')

    # Lista de colunas que sabemos que são datas
    colunas_datas_conhecidas = ['Competência', 'Pago em', 'Vencimento', 'Data']

    # 1. CONVERSÃO PARA DATETIME (Essencial para o filtro funcionar)
    if not arquivo.empty:
        for col in arquivo.columns:
            # Verifica se o nome da coluna é conhecido ou se o pandas detecta como data
            if col in colunas_datas_conhecidas or pd.api.types.is_datetime64_any_dtype(arquivo[col]):
                arquivo[col] = pd.to_datetime(arquivo[col], errors='coerce')

    # 2. FILTRO NO SIDEBAR
    st.sidebar.markdown("## Filtros 📅")
    
    # Identifica quais colunas no arquivo são de fato datas
    cols_datas_disponiveis = [c for c in arquivo.columns if pd.api.types.is_datetime64_any_dtype(arquivo[c])]
    
    if cols_datas_disponiveis:
        # Se houver mais de uma coluna de data, permite o usuário escolher
        coluna_filtro = st.sidebar.selectbox("Filtrar por data:", cols_datas_disponiveis)
        
        # Define o intervalo padrão (da menor até a maior data encontrada no arquivo)
        if not arquivo[coluna_filtro].dropna().empty:
            min_data = arquivo[coluna_filtro].min().date()
            max_data = arquivo[coluna_filtro].max().date()
        else:
            min_data = datetime.date.today()
            max_data = datetime.date.today()

        # Widget de seleção de período
        periodo = st.sidebar.date_input(
            "Selecione o Período",
            value=(min_data, max_data),
            format="DD/MM/YYYY"
        )
        
        # Lógica de validação e aplicação do filtro
        if isinstance(periodo, tuple):
            if len(periodo) == 2:
                inicio, fim = periodo
                if fim < inicio:
                    st.sidebar.error("Erro: A data final não pode ser menor que a inicial.")
                else:
                    # Filtra o DataFrame mantendo as linhas dentro do intervalo
                    mask = (arquivo[coluna_filtro].dt.date >= inicio) & (arquivo[coluna_filtro].dt.date <= fim)
                    arquivo = arquivo[mask]
            elif len(periodo) == 1:
                st.sidebar.info("Selecione a data final.")
    
    # 3. FORMATAÇÃO VISUAL (dd/mm/aaaa)
    # Criamos uma cópia para exibição, transformando as datas em texto formatado
    df_exibicao = arquivo.copy()
    if cols_datas_disponiveis:
        for col in cols_datas_disponiveis:
            df_exibicao[col] = df_exibicao[col].dt.strftime('%d/%m/%Y').fillna('')

    st.dataframe(df_exibicao)
    
except FileNotFoundError:
    st.error("O arquivo 'contas_a_pagar.xlsx' não foi encontrado.")
except Exception as e:
    st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")