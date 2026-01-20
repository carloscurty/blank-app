import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
import urllib.parse

st.set_page_config(page_title="Takeat BI", layout="wide", page_icon="🥗")

# ==========================================================
# 🔗 CONFIGURAÇÃO INFALÍVEL (MÉTODO DO LINK COMPLETO)
# ==========================================================

# PASSO 1: Cole aqui o link INTEIRO que você pegou no Supabase (Connection String)
# Aquele que tem: postgresql://postgres.wnjm... etc
LINK_DO_SUPABASE = "postgresql://postgres.wnjmldfbjwfvkybessqg:[SENHA_REAL]@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

# PASSO 2: Coloque sua senha real aqui
SENHA_REAL = "projetovendas2024"

# --- Lógica que arruma o link automaticamente ---
try:
    # Remove espaços vazios que podem vir ao copiar
    uri_limpa = LINK_DO_SUPABASE.strip()
    
    # 1. Troca o driver para pg8000 (necessário para python puro)
    if "postgresql://" in uri_limpa and "pg8000" not in uri_limpa:
        uri_final = uri_limpa.replace("postgresql://", "postgresql+pg8000://")
    else:
        uri_final = uri_limpa

    # 2. Injeta a senha correta no lugar certo
    # O link do Supabase vem com '[YOUR-PASSWORD]' ou com a senha antiga.
    # Vamos achar onde fica a senha (entre : e @) e substituir.
    
    prefixo, resto = uri_final.split("://")
    credenciais, endereco = resto.split("@")
    usuario = credenciais.split(":")[0]
    
    # Codifica a senha para evitar erro com caracteres especiais
    senha_safe = urllib.parse.quote_plus(SENHA_REAL)
    
    # Remonta o link blindado
    DB_URI = f"{prefixo}://{usuario}:{senha_safe}@{endereco}"

except Exception as e:
    # Se o usuário ainda não colou o link, define como None para não quebrar na hora
    DB_URI = None

# ==========================================================
# 📥 CARGA DE DADOS
# ==========================================================

st.markdown("### 🥗 Dashboard de Vendas")

if LINK_DO_SUPABASE == "COLE_O_LINK_INTEIRO_AQUI":
    st.warning("⚠️ Você precisa editar o arquivo `vendas.py` e colar o Link do Supabase na linha 15.")
    st.stop()

@st.cache_resource
def get_engine():
    return create_engine(DB_URI)

@st.cache_data(ttl=600)
def carregar_dados(query, params=None):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error("Erro de Conexão")
        st.info("Verifique se você colou o link do 'Connection Pooling' (Porta 6543) e a senha correta.")
        st.code(str(e))
        st.stop()

# ==========================================================
# 📊 APLICAÇÃO VISUAL
# ==========================================================

try:
    # Carrega Mêses
    df_meses = carregar_dados("SELECT DISTINCT TO_CHAR(data_hora, 'YYYY-MM') as mes_ano FROM vendas ORDER BY mes_ano DESC")
    
    if df_meses.empty:
        st.info("Conectado! Mas a tabela 'vendas' está vazia.")
        st.stop()
        
    opcoes = df_meses['mes_ano'].tolist()
    
    st.sidebar.header("Filtros")
    sel_meses = st.sidebar.multiselect("Selecione o Mês", options=opcoes, default=opcoes[:1])

    if sel_meses:
        # Busca dados filtrados
        placeholders = ', '.join([f':m{i}' for i in range(len(sel_meses))])
        params = {f'm{i}': mes for i, mes in enumerate(sel_meses)}
        query = f"SELECT * FROM vendas WHERE TO_CHAR(data_hora, 'YYYY-MM') IN ({placeholders})"
        
        df = carregar_dados(query, params=params)
        df['data_hora'] = pd.to_datetime(df['data_hora'])
        
        # Métricas
        k1, k2, k3 = st.columns(3)
        k1.metric("Venda Líquida", f"R$ {df['valor_liquido'].sum():,.2f}")
        k2.metric("Pedidos", df['id_pedido'].nunique())
        
        if 'ticket_medio' in df.columns:
            k3.metric("Ticket Médio", f"R$ {df['ticket_medio'].mean():,.2f}")
        
        st.divider()
        
        # Gráficos
        c1, c2 = st.columns(2)
        diario = df.groupby(df['data_hora'].dt.date)['valor_liquido'].sum().reset_index()
        fig = px.line(diario, x='data_hora', y='valor_liquido', title="Evolução Diária", markers=True)
        c1.plotly_chart(fig, use_container_width=True)
        
        if 'canal_venda' in df.columns:
            fig2 = px.pie(df, names='canal_venda', values='valor_liquido', title="Mix de Canais", hole=0.4)
            c2.plotly_chart(fig2, use_container_width=True)
            
    else:
        st.info("Selecione um mês ao lado.")

except Exception as e:
    st.error(f"Erro inesperado: {e}")