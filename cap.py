import streamlit as st
import pandas as pd
import datetime

# --- FUNÇÃO DE CARREGAMENTO COM CACHE ---
@st.cache_data
def carregar_excel_cap():
    try:
        return pd.read_excel('contas_a_pagar.xlsx')
    except Exception as e:
        return None

st.markdown("# Contas a Pagar 🎫")

# Carrega dados (usando cache)
arquivo_raw = carregar_excel_cap()

if arquivo_raw is None:
    st.error("Erro ao carregar 'contas_a_pagar.xlsx'. Verifique se o arquivo existe.")
    st.stop()

# Trabalhamos com uma cópia para não alterar o cache
arquivo = arquivo_raw.copy()

# Variáveis de exibição
data_exibicao_inicio = None
data_exibicao_fim = None

# Lista de colunas conhecidas
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
    
    # Tratamento para min/max seguro
    datas_validas = arquivo[coluna_filtro].dropna()
    if not datas_validas.empty:
        min_data = datas_validas.min().date()
        max_data = datas_validas.max().date()
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
    opcoes_pago = sorted(arquivo['Pago'].dropna().unique())
    if opcoes_pago:
        filtro_pago = st.sidebar.multiselect(
            "Selecione o status:",
            options=opcoes_pago,
            default=list(opcoes_pago)
        )
        if filtro_pago:
            arquivo = arquivo[arquivo['Pago'].isin(filtro_pago)]

# 4. PREPARAÇÃO DA EXIBIÇÃO
df_exibicao = arquivo.copy()
esconder_index = False 

# Lógica para esconder colunas
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

# 6. ESTILIZAÇÃO
styler = df_exibicao.style

# A) Colunas com quebra de linha
colunas_wrap = ['Descrição', 'Fornecedor', 'Centro de Custo', 'Histórico']
cols_wrap_presentes = [c for c in colunas_wrap if c in df_exibicao.columns]

if cols_wrap_presentes:
    styler = styler.set_properties(
        subset=cols_wrap_presentes,
        **{'white-space': 'normal', 'word-wrap': 'break-word', 'min-width': '180px'}
    )

# B) Colunas sem quebra (nowrap)
colunas_nowrap = cols_datas_disponiveis + ['Valor', 'Documento', 'Status']
cols_nowrap_presentes = [c for c in colunas_nowrap if c in df_exibicao.columns]

if cols_nowrap_presentes:
    styler = styler.set_properties(
        subset=cols_nowrap_presentes,
        **{'white-space': 'nowrap', 'min-width': '100px'} 
    )

# C) Formatação de Moeda
def _format_brl(x):
    try:
        if pd.isna(x) or x == '': return ''
        num = float(x)
        return f"R$ {num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return x

valor_cols = [c for c in df_exibicao.columns if c.lower().strip() == 'valor']
if valor_cols:
    styler = styler.format({c: _format_brl for c in valor_cols})

if esconder_index:
    styler = styler.hide(axis='index')

st.write("Visualização Detalhada:")
# Aviso de performance se houver muitos dados
if len(df_exibicao) > 500:
    st.warning(f"Exibindo {len(df_exibicao)} linhas. A tabela pode ficar lenta. Use os filtros para reduzir.")

if len(df_exibicao) > 0:
    st.dataframe(df_exibicao, use_container_width=True, hide_index=esconder_index)
else:
    st.info("Nenhum dado disponível com os filtros selecionados.")