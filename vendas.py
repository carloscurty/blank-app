import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
import urllib.parse
from datetime import date, timedelta

st.set_page_config(page_title="Takeat BI", layout="wide", page_icon="🥗")

# ==========================================================
# 🛠️ FUNÇÃO DE FORMATAÇÃO BRASILEIRA
# ==========================================================
def formatar_real(valor):
    if pd.isna(valor):
        return "R$ 0,00"
    texto = f"{valor:,.2f}"
    return f"R$ {texto.replace(',', 'X').replace('.', ',').replace('X', '.')}"

# ==========================================================
# 🔗 CONFIGURAÇÃO INFALÍVEL
# ==========================================================

# PASSO 1: Link do Supabase
LINK_DO_SUPABASE = "postgresql://postgres.wnjmldfbjwfvkybessqg:[SENHA_REAL]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

# PASSO 2: Senha real
SENHA_REAL = "projetovendas2024"

# --- Lógica de conexão ---
try:
    uri_limpa = LINK_DO_SUPABASE.strip()
    if "postgresql://" in uri_limpa and "pg8000" not in uri_limpa:
        uri_final = uri_limpa.replace("postgresql://", "postgresql+pg8000://")
    else:
        uri_final = uri_limpa

    prefixo, resto = uri_final.split("://")
    credenciais, endereco = resto.split("@")
    usuario = credenciais.split(":")[0]
    senha_safe = urllib.parse.quote_plus(SENHA_REAL)
    DB_URI = f"{prefixo}://{usuario}:{senha_safe}@{endereco}"

except Exception as e:
    DB_URI = None

# ==========================================================
# 📥 CARGA DE DADOS
# ==========================================================

st.markdown("### 🥗 Dashboard de Vendas (Valor Bruto)")

if DB_URI is None:
    st.warning("⚠️ Verifique o Link e a Senha no código.")
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
        st.code(str(e))
        st.stop()

# ==========================================================
# 📊 APLICAÇÃO VISUAL
# ==========================================================

try:
    # 1. Busca Data Mínima e Máxima para configurar o calendário
    df_datas = carregar_dados("SELECT MIN(data_hora) as data_min, MAX(data_hora) as data_max FROM vendas")
    
    if df_datas.empty or pd.isna(df_datas['data_min'][0]):
        st.info("Conectado! Mas a tabela 'vendas' está vazia.")
        st.stop()
    
    # Converte para objeto date do python
    min_db = pd.to_datetime(df_datas['data_min'][0]).date()
    max_db = pd.to_datetime(df_datas['data_max'][0]).date()
    
    st.sidebar.header("Filtros")
    
    # 2. Seletor de Data (Intervalo)
    padrao_inicio = max_db - timedelta(days=30) if max_db - min_db > timedelta(days=30) else min_db
    
    intervalo = st.sidebar.date_input(
        "Selecione o Período",
        value=(padrao_inicio, max_db),
        min_value=min_db,
        max_value=max_db,
        format="DD/MM/YYYY"
    )

    # Verifica se o usuário selecionou as duas datas
    if len(intervalo) == 2:
        data_ini, data_fim = intervalo
        
        # 3. Query Filtrando por DATA (BETWEEN)
        query = """
            SELECT * FROM vendas 
            WHERE data_hora::date BETWEEN :d_ini AND :d_fim
        """
        params = {'d_ini': data_ini, 'd_fim': data_fim}
        
        df = carregar_dados(query, params=params)
        df['data_hora'] = pd.to_datetime(df['data_hora'])
        
        if df.empty:
            st.warning("Nenhuma venda encontrada neste período.")
            st.stop()
        
        # --- KPIS PRINCIPAIS ---
        k1, k2, k3, k4 = st.columns(4)
        
        venda_bruta = df['valor_bruto'].sum()
        venda_liquida = df['valor_liquido'].sum()
        pedidos = df['id_pedido'].nunique()
        ticket_medio = venda_bruta / pedidos if pedidos > 0 else 0
        
        k1.metric("Venda Bruta", formatar_real(venda_bruta))
        k2.metric("Ticket Médio (Bruto)", formatar_real(ticket_medio))
        k3.metric("Venda Líquida", formatar_real(venda_liquida))
        k4.metric("Pedidos", pedidos)
        
        st.divider()      

        # --- PREPARAÇÃO DADOS CANAIS ---
        canal_stats = df.groupby('canal_venda').agg({
            'valor_bruto': 'sum',
            'id_pedido': 'nunique'
        }).reset_index()

        canal_stats.columns = ['Canal', 'Faturamento', 'Pedidos']

        canal_stats['Perc_Fat'] = canal_stats['Faturamento'] / canal_stats['Faturamento'].sum()
        canal_stats['Perc_Ped'] = canal_stats['Pedidos'] / canal_stats['Pedidos'].sum()

        g1, g2, g3 = st.columns(3)

        # --- GRÁFICO 1: Faturamento Bruto (%) ---
        fig_faturamento = px.bar(canal_stats, 
                                 x='Faturamento', y='Canal', orientation='h',
                                 text='Perc_Fat', title="Faturamento Bruto por Canal") 

        posicoes_fat = ['outside' if val < 0.04 else 'inside' for val in canal_stats['Perc_Fat']]

        fig_faturamento.update_traces(
            texttemplate='%{text:.1%}', 
            textposition=posicoes_fat,
            insidetextanchor='middle',
            hovertemplate='<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>' 
        )

        fig_faturamento.update_layout(
            xaxis_visible=False,
            yaxis_title=None, 
            xaxis_title=None,
            yaxis={'categoryorder':'total ascending'},
            separators=",.", 
            uniformtext_minsize=8, uniformtext_mode='hide'
        )

        g1.plotly_chart(fig_faturamento, use_container_width=True)

        # --- GRÁFICO 2: Pedidos (%) ---
        fig_pedidos = px.bar(canal_stats, 
                             x='Pedidos', y='Canal', orientation='h',
                             text='Perc_Ped', title="Pedidos por Canal",
                             hover_data={'Perc_Ped':':.1%', 'Pedidos':':d'})

        posicoes_ped = ['outside' if val < 0.04 else 'inside' for val in canal_stats['Perc_Ped']]

        fig_pedidos.update_traces(
            texttemplate='%{text:.1%}', 
            textposition=posicoes_ped,
            insidetextanchor='middle'
        )

        fig_pedidos.update_layout(
            xaxis_visible=False,
            yaxis_title=None, 
            xaxis_title=None, 
            yaxis={'categoryorder':'total ascending'},
            separators=",.",
            uniformtext_minsize=8, uniformtext_mode='hide'
        )

        g2.plotly_chart(fig_pedidos, use_container_width=True)

        # --- GRÁFICO 3: Mix (Pizza) ---
        if 'canal_venda' in df.columns:
            fig2 = px.pie(df, names='canal_venda', values='valor_bruto', title="Mix (Bruto)", hole=0.4)
            fig2.update_layout(separators=",.") 
            fig2.update_traces(
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>R$ %{value:,.2f}<extra></extra>'
            )
            g3.plotly_chart(fig2, use_container_width=True)

        st.divider()
        
        # --- GRÁFICO 4: Evolução Diária ---
        c1 = st.columns(1)[0]
        
        # 1. Agrupa
        diario = df.groupby(df['data_hora'].dt.date)['valor_bruto'].sum().reset_index()
        diario = diario[diario['valor_bruto'] > 0]
        diario['data_hora'] = pd.to_datetime(diario['data_hora'])

        # ----------------------------------------------------
        # NOVO: KPIS DO GRÁFICO DIÁRIO
        # ----------------------------------------------------
        if not diario.empty:
            media_diaria = diario['valor_bruto'].mean()
            
            # Pega linha com valor máx e min
            dia_max = diario.loc[diario['valor_bruto'].idxmax()]
            dia_min = diario.loc[diario['valor_bruto'].idxmin()]
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Média Diária", formatar_real(media_diaria))
            m2.metric(f"Melhor Dia ({dia_max['data_hora'].strftime('%d/%m')})", formatar_real(dia_max['valor_bruto']))
            m3.metric(f"Pior Dia ({dia_min['data_hora'].strftime('%d/%m')})", formatar_real(dia_min['valor_bruto']))
        
        # ----------------------------------------------------

        # 2. Configura Label e Dia da Semana
        dias_semana = {
            0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta',
            4: 'Sexta', 5: 'Sábado', 6: 'Domingo'
        }
        
        diario['label_eixo'] = diario['data_hora'].dt.strftime('%d/%m')
        diario['dia_sem'] = diario['data_hora'].dt.dayofweek.map(dias_semana)

        # 3. Gráfico
        fig = px.bar(diario, x='label_eixo', y='valor_bruto', title="Faturamento diário (Bruto)")
        
        fig.update_layout(
            separators=",.",
            xaxis_title=None,          
            yaxis_title=None,          
            yaxis_showticklabels=False, 
            hovermode="x unified"
        )
        
        # 4. Hover customizado
        fig.update_traces(
            customdata=diario[['dia_sem']],
            hovertemplate='<b>%{x} (%{customdata[0]})</b><br>Venda: R$ %{y:,.2f}<extra></extra>'
        )
        
        c1.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("Selecione a Data Inicial e Final no calendário.")

    st.divider()    

except Exception as e:
    st.error(f"Erro inesperado: {e}")