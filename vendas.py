import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
import urllib.parse
from datetime import date, timedelta

st.set_page_config(page_title="Takeat BI", layout="wide", page_icon="🥗")

# ==========================================================
# 🛠️ FUNÇÃO DE FORMATAÇÃO
# ==========================================================
def formatar_real(valor):
    if pd.isna(valor): return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# ==========================================================
# 🔗 CONFIGURAÇÃO DE CONEXÃO
# ==========================================================
DB_HOST = "aws-1-us-east-2.pooler.supabase.com"
DB_PORT = "6543"
DB_NAME = "postgres"
DB_USER = "postgres.wnjmldfbjwfvkybessqg"
DB_PASS = "projetovendas2024"

try:
    senha_safe = urllib.parse.quote_plus(DB_PASS)
    DB_URI = f"postgresql+pg8000://{DB_USER}:{senha_safe}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
except Exception as e:
    st.error(f"Erro de config: {e}")
    DB_URI = None

@st.cache_resource
def get_engine():
    return create_engine(DB_URI, pool_pre_ping=True)

@st.cache_data(ttl=0) 
def carregar_dados(query, params=None):
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params)

# ==========================================================
# 🧭 NAVEGAÇÃO
# ==========================================================
st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Ir para:", ["📊 Dashboard", "⚙️ Atualizar Dados"])
st.sidebar.divider()

if DB_URI is None: st.stop()

# ==========================================================
# PÁGINA 1: DASHBOARD
# ==========================================================
if pagina == "📊 Dashboard":
    st.markdown("### 🥗 Dashboard de Vendas")
    try:
        df_datas = carregar_dados("SELECT MIN(data_hora) as data_min, MAX(data_hora) as data_max FROM vendas")
        if df_datas.empty or pd.isna(df_datas['data_min'][0]):
            st.info("Banco vazio.")
            st.stop()
        
        min_db = pd.to_datetime(df_datas['data_min'][0]).date()
        max_db = pd.to_datetime(df_datas['data_max'][0]).date()
        
        padrao_inicio = max_db - timedelta(days=30) if max_db - min_db > timedelta(days=30) else min_db
        st.sidebar.header("Filtros")
        intervalo = st.sidebar.date_input("Período", (padrao_inicio, max_db), min_value=min_db, max_value=max_db, format="DD/MM/YYYY")

        if len(intervalo) == 2:
            data_ini, data_fim = intervalo
            query = """
                SELECT id_pedido, data_hora, canal_venda, valor_bruto, valor_liquido 
                FROM vendas 
                WHERE data_hora::date BETWEEN :d_ini AND :d_fim
            """
            df = carregar_dados(query, params={'d_ini': data_ini, 'd_fim': data_fim})
            
            if not df.empty:
                df['data_hora'] = pd.to_datetime(df['data_hora'])
                
                k1, k2, k3, k4 = st.columns(4)
                fat = df['valor_bruto'].sum()
                ped = df['id_pedido'].nunique()
                k1.metric("Venda Bruta", formatar_real(fat))
                k2.metric("Ticket Médio", formatar_real(fat/ped if ped else 0))
                k3.metric("Venda Líquida", formatar_real(df['valor_liquido'].sum()))
                k4.metric("Pedidos", ped)
                st.divider()

                canal_stats = df.groupby('canal_venda').agg({'valor_bruto': 'sum', 'id_pedido': 'nunique'}).reset_index()
                canal_stats['Perc_Fat'] = canal_stats['valor_bruto'] / canal_stats['valor_bruto'].sum()
                
                g1, g2 = st.columns(2)
                fig1 = px.bar(canal_stats, x='valor_bruto', y='canal_venda', orientation='h', text='Perc_Fat', title="Faturamento por Canal")
                fig1.update_traces(texttemplate='%{text:.1%}')
                g1.plotly_chart(fig1, use_container_width=True)

                diario = df.groupby(df['data_hora'].dt.date)['valor_bruto'].sum().reset_index()
                fig_d = px.bar(diario, x='data_hora', y='valor_bruto', title="Evolução Diária")
                g2.plotly_chart(fig_d, use_container_width=True)
            else:
                st.warning("Sem dados.")
    except Exception as e:
        st.error(f"Erro Dashboard: {e}")
        st.cache_resource.clear()

# ==========================================================
# PÁGINA 2: CARGA DE DADOS (COM SOMA DE VALORES)
# ==========================================================
elif pagina == "⚙️ Atualizar Dados":
    st.markdown("### ⚙️ Atualização Incremental")
    arquivo = st.file_uploader("Arraste seu arquivo aqui", type=["xlsx", "csv", "xls"])

    if arquivo and st.button("Processar e Salvar"):
        try:
            # 1. Encontra Cabeçalho
            if arquivo.name.endswith('.csv'):
                df_temp = pd.read_csv(arquivo, header=None, nrows=10)
            else:
                df_temp = pd.read_excel(arquivo, header=None, nrows=10)

            idx_cabecalho = -1
            for i, row in df_temp.iterrows():
                if row.astype(str).str.contains("Pedido", case=False).any():
                    idx_cabecalho = i
                    break
            
            if idx_cabecalho == -1:
                st.error("❌ Coluna 'Pedido' não encontrada.")
                st.stop()

            arquivo.seek(0)
            if arquivo.name.endswith('.csv'):
                df_novo = pd.read_csv(arquivo, header=idx_cabecalho)
            else:
                df_novo = pd.read_excel(arquivo, header=idx_cabecalho)

            # 2. Mapeamento
            mapa_colunas = {
                'Pedido': 'id_pedido',
                'Data - Hora': 'data_hora',
                'Canal': 'canal_venda',
                'Valor Bruto': 'valor_bruto',
                'Valor Líquido': 'valor_liquido'
            }
            
            df_novo = df_novo.rename(columns=mapa_colunas)
            colunas_validas = [c for c in mapa_colunas.values() if c in df_novo.columns]
            
            if 'id_pedido' not in colunas_validas:
                st.error("Erro Crítico: ID do Pedido não encontrado.")
                st.stop()
                
            df_limpo = df_novo[colunas_validas].copy()
            
            # Tratamento de Data e ID
            if 'data_hora' in df_limpo.columns:
                df_limpo['data_hora'] = pd.to_datetime(df_limpo['data_hora'], dayfirst=True, errors='coerce')

            df_limpo['id_pedido'] = pd.to_numeric(df_limpo['id_pedido'], errors='coerce')
            df_limpo = df_limpo.dropna(subset=['id_pedido']) 
            df_limpo['id_pedido'] = df_limpo['id_pedido'].astype('int64')

            # ---------------------------------------------------------
            # 🚨 LÓGICA DE CONSOLIDAÇÃO (SOMA)
            # ---------------------------------------------------------
            # Se houver pedidos duplicados (ex: pagamentos parciais),
            # SOMAMOS os valores e mantemos a data/canal do primeiro registro.
            
            df_agrupado = df_limpo.groupby('id_pedido', as_index=False).agg({
                'data_hora': 'first',      # Mantém a data do primeiro registro
                'canal_venda': 'first',    # Mantém o canal
                'valor_bruto': 'sum',      # SOMA o valor bruto das parcelas
                'valor_liquido': 'sum'     # SOMA o valor líquido das parcelas
            })
            # ---------------------------------------------------------

            # 3. Lógica Incremental
            engine = get_engine()
            with engine.connect() as conn:
                ids_banco = pd.read_sql(text("SELECT id_pedido FROM vendas"), conn)
            
            lista_existentes = set(ids_banco['id_pedido'].astype('int64').tolist())
            
            # Filtra usando o dataframe AGRUPADO
            df_para_subir = df_agrupado[~df_agrupado['id_pedido'].isin(lista_existentes)]
            
            qtd_novos = len(df_para_subir)
            
            if qtd_novos > 0:
                progresso = st.progress(0)
                st.write(f"Encontrei {qtd_novos} vendas novas consolidadas. Enviando...")
                
                with engine.begin() as conn:
                    df_para_subir.to_sql('vendas', conn, if_exists='append', index=False, chunksize=1000)
                
                progresso.progress(100)
                st.success(f"✅ Sucesso! {qtd_novos} vendas gravadas.")
                st.balloons()
                st.cache_data.clear()
            else:
                st.warning("⚠️ Arquivo processado. Todas as vendas já estão no banco.")

        except Exception as e:
            st.error(f"Erro detalhado: {e}")
            st.cache_resource.clear()