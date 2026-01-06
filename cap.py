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

# Variáveis para controlar a exibição do texto do período
data_exibicao_inicio = None
data_exibicao_fim = None

try:
    arquivo = pd.read_excel('contas_a_pagar.xlsx')

    # Lista de colunas conhecidas para conversão de data
    colunas_datas_conhecidas = ['Competência', 'Pago em', 'Vencimento', 'Data']

    # 1. CONVERSÃO PARA DATETIME
    if not arquivo.empty:
        for col in arquivo.columns:
            if col in colunas_datas_conhecidas or pd.api.types.is_datetime64_any_dtype(arquivo[col]):
                arquivo[col] = pd.to_datetime(arquivo[col], errors='coerce')

    # --- ÁREA DE FILTROS NO SIDEBAR ---
    st.sidebar.markdown("## Filtros 🕵️")

    # 2. FILTRO DE DATA
    colunas_preferenciais = ['Vencimento', 'Pago em', 'Competência']
    cols_datas_disponiveis = [c for c in colunas_preferenciais if c in arquivo.columns]

    if not cols_datas_disponiveis:
         cols_datas_disponiveis = [c for c in arquivo.columns if pd.api.types.is_datetime64_any_dtype(arquivo[c])]

    if cols_datas_disponiveis:
        coluna_filtro = st.sidebar.selectbox("Filtrar por data:", cols_datas_disponiveis, index=0)
        
        if not arquivo[coluna_filtro].dropna().empty:
            min_data = arquivo[coluna_filtro].min().date()
            max_data = arquivo[coluna_filtro].max().date()
        else:
            min_data = datetime.date.today()
            max_data = datetime.date.today()

        data_exibicao_inicio = min_data
        data_exibicao_fim = max_data

        periodo = st.sidebar.date_input(
            "Selecione o intervalo:",
            value=(min_data, max_data),
            format="DD/MM/YYYY"
        )
        
        if isinstance(periodo, tuple):
            if len(periodo) == 2:
                inicio, fim = periodo
                if fim < inicio:
                    st.sidebar.error("Data final deve ser maior que a inicial.")
                else:
                    data_exibicao_inicio = inicio
                    data_exibicao_fim = fim
                    mask_data = (arquivo[coluna_filtro].dt.date >= inicio) & (arquivo[coluna_filtro].dt.date <= fim)
                    arquivo = arquivo[mask_data]
            elif len(periodo) == 1:
                st.sidebar.info("Selecione a data final.")

    # 3. FILTRO DA COLUNA "PAGO"
    filtro_pago = []
    if 'Pago' in arquivo.columns:
        opcoes_pago = arquivo['Pago'].unique()
        
        filtro_pago = st.sidebar.multiselect(
            "Selecione o status:",
            options=opcoes_pago,
            default=opcoes_pago
        )
        
        if filtro_pago:
            arquivo = arquivo[arquivo['Pago'].isin(filtro_pago)]
        else:
            arquivo = arquivo[arquivo['Pago'].isin(filtro_pago)]

    # 4. PREPARAÇÃO DA EXIBIÇÃO
    df_exibicao = arquivo.copy()
    esconder_index = False 

    # Lógica para esconder colunas quando apenas "Não" estiver selecionado
    if len(filtro_pago) == 1 and 'Não' in filtro_pago:
        colunas_para_remover = ['Competência', 'Item', 'Pago', 'Conta Contábil', 'Pago em', 'Index', 'Centro de Custo', 'Conta Bancária']
        cols_existentes = [c for c in colunas_para_remover if c in df_exibicao.columns]
        df_exibicao = df_exibicao.drop(columns=cols_existentes)
        esconder_index = True

    # 5. FORMATAÇÃO VISUAL (dd/mm/aaaa)
    if cols_datas_disponiveis:
        for col in cols_datas_disponiveis:
            if col in df_exibicao.columns:
                df_exibicao[col] = df_exibicao[col].dt.strftime('%d/%m/%Y').fillna('')

    # Exibe título do período
    if data_exibicao_inicio and data_exibicao_fim:
        st.write(f"Período: {data_exibicao_inicio.strftime('%d/%m/%Y')} até {data_exibicao_fim.strftime('%d/%m/%Y')}")

    # 6. ESTILIZAÇÃO AVANÇADA
    styler = df_exibicao.style

    # A) Colunas que DEVEM quebrar linha (Textos longos)
    colunas_wrap = ['Descrição', 'Fornecedor', 'Centro de Custo', 'Histórico']
    cols_wrap_presentes = [c for c in colunas_wrap if c in df_exibicao.columns]
    
    if cols_wrap_presentes:
        styler = styler.set_properties(
            subset=cols_wrap_presentes,
            # min-width garante que a coluna não fique fina demais antes de quebrar
            **{'white-space': 'normal', 'word-wrap': 'break-word', 'min-width': '180px'}
        )

    # B) Colunas que NÃO DEVEM quebrar linha (Datas e Números curtos)
    # Pegamos as datas + colunas que geralmente são curtas e feias se quebrarem
    colunas_nowrap = cols_datas_disponiveis + ['Valor', 'Documento', 'Status']
    cols_nowrap_presentes = [c for c in colunas_nowrap if c in df_exibicao.columns]

    if cols_nowrap_presentes:
        styler = styler.set_properties(
            subset=cols_nowrap_presentes,
            # nowrap proíbe a quebra de linha, forçando a largura necessária
            **{'white-space': 'nowrap', 'min-width': '90px'} 
        )
    
    # Aplica a ocultação do índice se necessário
    if esconder_index:
        styler = styler.hide(axis='index')

    st.write("Visualização Detalhada:")
    st.table(styler)
    
except FileNotFoundError:
    st.error("O arquivo 'contas_a_pagar.xlsx' não foi encontrado.")
except Exception as e:
    st.error(f"Ocorreu um erro ao carregar o arquivo: {e}")