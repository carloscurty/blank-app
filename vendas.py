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

if LINK_DO_SUPABASE == "postgresql://postgres.wnjmldfbjwfvkybessqg:[projetovendas2024]@aws-1-us-east-2.pooler.supabase.com:5432/postgres":
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
        k1, k2, k3, k4 = st.columns(4)
        ticket_medio = df['valor_liquido'].sum() / df['id_pedido'].nunique() if df['id_pedido'].nunique() > 0 else 0
        k1.metric("Venda Bruta", f"R$ {df['valor_bruto'].sum():,.2f}")
        k2.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
        k3.metric("Venda Líquida", f"R$ {df['valor_liquido'].sum():,.2f}")
        k4.metric("Pedidos", df['id_pedido'].nunique())
        
        st.divider()       

        # Gráficos por canal de venda
        canal_stats = df.groupby('canal_venda').agg({
            'valor_liquido': 'sum',
            'id_pedido': 'nunique'
        }).reset_index()

        canal_stats.columns = ['Canal', 'Faturamento', 'Pedidos']

        # --- CÁLCULO DAS PORCENTAGENS ---
        canal_stats['Perc_Fat'] = canal_stats['Faturamento'] / canal_stats['Faturamento'].sum()
        canal_stats['Perc_Ped'] = canal_stats['Pedidos'] / canal_stats['Pedidos'].sum()

        g1, g2 = st.columns(2)

        # --- Gráfico de Faturamento (%) ---
        fig_faturamento = px.bar(canal_stats, 
                                x='Faturamento', 
                                y='Canal', 
                                orientation='h',
                                text='Perc_Fat', 
                                title="Faturamento por Canal",
                                hover_data={'Perc_Fat':':.1%', 'Faturamento':':,.2f'}) 

        # LÓGICA CONDICIONAL: < 10% fora, >= 10% dentro
        posicoes_fat = ['outside' if val < 0.04 else 'inside' for val in canal_stats['Perc_Fat']]

        fig_faturamento.update_traces(
            texttemplate='%{text:.1%}', 
            textposition=posicoes_fat, # Aplica a lista de posições calculada acima
            insidetextanchor='middle'  # Centraliza o texto quando estiver dentro
        )

        fig_faturamento.update_layout(
            xaxis_visible=False,
            yaxis_title=None,
            yaxis={'categoryorder':'total ascending'},
            uniformtext_minsize=8, # Garante que o texto não fique microscópico
            uniformtext_mode='hide'
        )

        g1.plotly_chart(fig_faturamento, use_container_width=True)

        # --- Gráfico de Pedidos (%) ---
        fig_pedidos = px.bar(canal_stats, 
                            x='Pedidos', 
                            y='Canal', 
                            orientation='h',
                            text='Perc_Ped', 
                            title="Pedidos por Canal",
                            hover_data={'Perc_Ped':':.1%', 'Pedidos':':d'})

        # LÓGICA CONDICIONAL: < 10% fora, >= 10% dentro
        posicoes_ped = ['outside' if val < 0.04 else 'inside' for val in canal_stats['Perc_Ped']]

        fig_pedidos.update_traces(
            texttemplate='%{text:.1%}', 
            textposition=posicoes_ped, # Aplica a lista de posições calculada
            insidetextanchor='middle'
        )

        fig_pedidos.update_layout(
            xaxis_visible=False,
            yaxis_title=None,
            yaxis={'categoryorder':'total ascending'},
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )

        g2.plotly_chart(fig_pedidos, use_container_width=True)

        st.divider()
        
# Gráficos
        c1, c2 = st.columns(2)
        
        # 1. Agrupa os dados por dia
        diario = df.groupby(df['data_hora'].dt.date)['valor_liquido'].sum().reset_index()
        
        # 2. FILTRO: Remove os dias onde o valor é estritamente zero
        diario = diario[diario['valor_liquido'] != 0]
        
        # 3. Cria o gráfico apenas com os dias ativos
        fig = px.bar(diario, x='data_hora', y='valor_liquido', title="Evolução Diária")
        c1.plotly_chart(fig, use_container_width=True)
        
        if 'canal_venda' in df.columns:
            fig2 = px.pie(df, names='canal_venda', values='valor_liquido', title="Mix de Canais", hole=0.4)
            c2.plotly_chart(fig2, use_container_width=True)
            
    else:
        st.info("Selecione um mês ao lado.")

    st.divider()    

except Exception as e:
    st.error(f"Erro inesperado: {e}")