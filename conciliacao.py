import streamlit as st
import pandas as pd
import re

# ==============================================================================
# 1. FUNÇÕES DE LIMPEZA (EXTREMAMENTE ROBUSTAS)
# ==============================================================================

def extrair_data_regex(valor):
    """
    Busca apenas o padrão DD/MM/AAAA dentro de qualquer texto.
    Ignora horas, hífens, espaços ou erros.
    """
    if pd.isna(valor): return None
    valor = str(valor)
    
    # Regex para encontrar dia/mes/ano (ex: 22/01/2026)
    match = re.search(r'(\d{2}/\d{2}/\d{4})', valor)
    
    if match:
        return match.group(1) # Retorna apenas a data limpa
    return None

def limpar_dinheiro(valor):
    """
    Converte qualquer formato de dinheiro para float.
    Lida com: 'R$ 1.200,50', '1200.50', '1,200.50' e floats nativos.
    """
    if pd.isna(valor): return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    
    valor = str(valor).strip()
    
    # Se for apenas traço ou vazio
    if valor in ['-', '', 'nan', 'None']: return 0.0
    
    # Remove R$ e espaços
    valor = valor.replace('R$', '').strip()
    
    # Lógica para detectar se é 1.000,00 (Brasil) ou 1000.00 (EUA/Excel)
    if ',' in valor and '.' in valor:
        # Assumimos padrão Brasil (ponto separa milhar, vírgula decimal)
        valor = valor.replace('.', '').replace(',', '.')
    elif ',' in valor:
        # Apenas vírgula? Assume decimal (10,50 -> 10.50)
        valor = valor.replace(',', '.')
    
    # Se tiver apenas ponto, já está certo (10.50), a não ser que seja milhar (1.000)
    # Mas no contexto bancário, 1.000 geralmente não aparece sem decimal.
    # Vamos confiar no float() direto.
    
    try:
        return float(valor)
    except:
        return 0.0

# ==============================================================================
# 2. CARREGAMENTO INTELIGENTE
# ==============================================================================
def carregar_arquivo(uploaded_file, file_type="stone"):
    try:
        # Lê o arquivo inteiro como STRING primeiro para não perder dados
        if uploaded_file.name.endswith('.csv'):
            # Detecta separador: Stone usa ; e Sistema usa ,
            sep = ';' if file_type == 'stone' else ','
            df = pd.read_csv(uploaded_file, sep=sep, dtype=str, encoding='latin1', on_bad_lines='skip')
        else:
            df = pd.read_excel(uploaded_file, dtype=str)

        # PROCURA O CABEÇALHO REAL
        # Percorre as primeiras 20 linhas procurando palavras chave
        idx_header = None
        keywords = ['DATA', 'Data', 'PEDIDO', 'Pedido', 'VALOR', 'Valor']
        
        for i, row in df.head(20).iterrows():
            row_str = row.astype(str).str.cat(sep=' ').upper()
            # Se achar DATA e VALOR na mesma linha, e NÃO for a linha de Total
            if any(k in row_str for k in keywords) and 'TOTAL' not in row_str:
                idx_header = i
                break
        
        if idx_header is not None:
            # Recarrega ou ajusta o dataframe para começar dali
            df.columns = df.iloc[idx_header]
            df = df.iloc[idx_header+1:].reset_index(drop=True)
        
        # Limpa nomes das colunas
        df.columns = [str(c).strip().upper().replace('Ã', 'A').replace('Ç', 'C').replace('Í', 'I') for c in df.columns]
        
        return df

    except Exception as e:
        st.error(f"Erro ao ler arquivo ({file_type}): {e}")
        return pd.DataFrame()

# ==============================================================================
# 3. INTERFACE
# ==============================================================================
def app():
    st.markdown("## ⚖️ Conciliação: Stone vs Sistema")
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        f_stone = st.file_uploader("📂 Arquivo Stone", type=['csv','xlsx'], key='f1')
    with c2:
        f_sys = st.file_uploader("📂 Arquivo Sistema", type=['csv','xlsx'], key='f2')

    if f_stone and f_sys:
        st.divider()
        df_stone = carregar_arquivo(f_stone, "stone")
        df_sys = carregar_arquivo(f_sys, "sistema")

        if not df_stone.empty and not df_sys.empty:
            
            # --- SELEÇÃO DE COLUNAS ---
            cols1, cols2 = st.columns(2)
            
            # Helpers para achar índice
            def get_idx(cols, keys):
                for i, c in enumerate(cols):
                    if any(k in c for k in keys): return i
                return 0

            with cols1:
                st.caption("Configuração Stone")
                opt_s = df_stone.columns
                col_d_s = st.selectbox("Coluna DATA", opt_s, index=get_idx(opt_s, ['DATA', 'VENDA']))
                col_v_s = st.selectbox("Coluna VALOR", opt_s, index=get_idx(opt_s, ['LIQUIDO', 'VALOR LIQUIDO']))

            with cols2:
                st.caption("Configuração Sistema")
                opt_sys = df_sys.columns
                col_d_sys = st.selectbox("Coluna DATA", opt_sys, index=get_idx(opt_sys, ['DATA', 'HORA']))
                col_v_sys = st.selectbox("Coluna VALOR", opt_sys, index=get_idx(opt_sys, ['LIQUIDO', 'VALOR LIQUIDO']))

            if st.button("🔄 Processar Agora"):
                try:
                    # --- 1. PROCESSAR STONE ---
                    # Extrai data via Regex (pega 22/01/2026 mesmo que tenha hora junto)
                    df_stone['data_limpa'] = df_stone[col_d_s].apply(extrair_data_regex)
                    df_stone['data_ref'] = pd.to_datetime(df_stone['data_limpa'], dayfirst=True, errors='coerce')
                    
                    # Converte Valor
                    df_stone['valor_ref'] = df_stone[col_v_s].apply(limpar_dinheiro)
                    
                    # Remove datas inválidas (linhas vazias ou cabeçalhos repetidos)
                    df_stone = df_stone.dropna(subset=['data_ref'])

                    # --- 2. PROCESSAR SISTEMA ---
                    df_sys['data_limpa'] = df_sys[col_d_sys].apply(extrair_data_regex)
                    df_sys['data_ref'] = pd.to_datetime(df_sys['data_limpa'], dayfirst=True, errors='coerce')
                    
                    df_sys['valor_ref'] = df_sys[col_v_sys].apply(limpar_dinheiro)
                    
                    df_sys = df_sys.dropna(subset=['data_ref'])

                    # --- 3. AGRUPAMENTO ---
                    # Agrupa por dia para somar tudo
                    agg_stone = df_stone.groupby('data_ref')['valor_ref'].sum().reset_index().rename(columns={'valor_ref': 'Stone'})
                    agg_sys = df_sys.groupby('data_ref')['valor_ref'].sum().reset_index().rename(columns={'valor_ref': 'Sistema'})

                    # --- 4. CRUZAMENTO (MERGE) ---
                    df_final = pd.merge(agg_sys, agg_stone, on='data_ref', how='outer').fillna(0)
                    df_final['Diferenca'] = df_final['Stone'] - df_final['Sistema']
                    df_final = df_final.sort_values('data_ref')

                    # Formatação visual da data
                    df_final['Data'] = df_final['data_ref'].dt.strftime('%d/%m/%Y')
                    cols_show = ['Data', 'Sistema', 'Stone', 'Diferenca']

                    # --- 5. EXIBIÇÃO ---
                    st.success("Cálculo realizado!")
                    
                    # Totais
                    tot_sys = df_final['Sistema'].sum()
                    tot_stone = df_final['Stone'].sum()
                    tot_dif = tot_stone - tot_sys

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Sistema", f"R$ {tot_sys:,.2f}")
                    m2.metric("Total Stone", f"R$ {tot_stone:,.2f}")
                    m3.metric("Diferença", f"R$ {tot_dif:,.2f}", delta_color="normal")

                    # Tabela
                    def colorir(val):
                        color = '#ffcccc' if abs(val) > 1.00 else '#ccffcc'
                        return f'background-color: {color}; color: black'

                    st.dataframe(
                        df_final[cols_show].style
                        .format({'Sistema': 'R$ {:,.2f}', 'Stone': 'R$ {:,.2f}', 'Diferenca': 'R$ {:,.2f}'})
                        .applymap(colorir, subset=['Diferenca']),
                        use_container_width=True,
                        hide_index=True
                    )

                except Exception as e:
                    st.error(f"Erro Crítico: {e}")
                    with st.expander("Ver detalhes do erro"):
                        st.write(e)