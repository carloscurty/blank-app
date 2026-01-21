import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
import urllib.parse
from datetime import date, timedelta

st.set_page_config(page_title="Takeat BI", layout="wide", page_icon="🥗")

# ==========================================================
# 🛠️ FUNÇÕES DE FORMATAÇÃO E AJUDA
# ==========================================================
def formatar_real(valor):
    if pd.isna(valor): return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def traduzir_dia(data):
    dias = {
        'Monday': 'Seg', 'Tuesday': 'Ter', 'Wednesday': 'Qua', 
        'Thursday': 'Qui', 'Friday': 'Sex', 'Saturday': 'Sáb', 'Sunday': 'Dom'
    }
    return dias.get(data.strftime('%A'), '')

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
# PÁGINA 1: DASHBOARD COMPLETO E FORMATADO
# ==========================================================
if pagina == "📊 Dashboard":
    st.markdown("### 🥗 Dashboard de Vendas")
    try:
        # Pega limites de data
        df_datas = carregar_dados("SELECT MIN(data_hora) as data_min, MAX(data_hora) as data_max FROM vendas")
        if df_datas.empty or pd.isna(df_datas['data_min'][0]):
            st.info("Banco de dados vazio. Vá em 'Atualizar Dados' para começar.")
            st.stop()
        
        min_db = pd.to_datetime(df_datas['data_min'][0]).date()
        max_db = pd.to_datetime(df_datas['data_max'][0]).date()
        
        # Filtros
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
                
                # --- 1. CARDS SUPERIORES ---
                k1, k2, k3, k4 = st.columns(4)
                fat = df['valor_bruto'].sum()
                ped = df['id_pedido'].nunique()
                liq = df['valor_liquido'].sum()
                
                k1.metric("Venda Bruta", formatar_real(fat))
                k2.metric("Ticket Médio", formatar_real(fat/ped if ped else 0))
                k3.metric("Venda Líquida", formatar_real(liq))
                k4.metric("Qtd. Pedidos", ped)
                st.divider()

                # --- 2. GRÁFICOS DE CANAL ---
                canal_stats = df.groupby('canal_venda').agg(
                    Faturamento=('valor_bruto', 'sum'),
                    Pedidos=('id_pedido', 'nunique')
                ).reset_index().sort_values('Faturamento', ascending=True)

                canal_stats['Faturamento_Label'] = canal_stats['Faturamento'].apply(formatar_real)

                g1, g2 = st.columns(2)
                
                # Pizza
                with g1:
                    fig_pizza = px.pie(
                        canal_stats, 
                        values='Faturamento', 
                        names='canal_venda', 
                        title='Participação por Canal (%)',
                        hole=0.4
                    )
                    fig_pizza.update_traces(
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>Faturamento: %{value:,.2f}<extra></extra>'
                    )
                    st.plotly_chart(fig_pizza, use_container_width=True)

                # Barras Canal
                with g2:
                    fig_bar = px.bar(
                        canal_stats, 
                        x='Faturamento', 
                        y='canal_venda', 
                        orientation='h', 
                        text='Faturamento_Label', 
                        title='Faturamento Total por Canal'
                    )
                    fig_bar.update_traces(
                        texttemplate='%{text}', 
                        textposition='outside',
                        hovertemplate='<b>%{y}</b><br>Total: %{text}<extra></extra>'
                    )
                    fig_bar.update_layout(xaxis_title="", yaxis_title="")
                    st.plotly_chart(fig_bar, use_container_width=True)

                # --- 3. EVOLUÇÃO DIÁRIA (CORRIGIDA ORDEM) ---
                st.subheader("Evolução Diária")
                
                diario = df.groupby(df['data_hora'].dt.date)['valor_bruto'].sum().reset_index()
                diario.columns = ['Data', 'Venda']
                diario['Data'] = pd.to_datetime(diario['Data'])
                
                # 1. Ordenação rigorosa pela data
                diario = diario.sort_values('Data')

                # 2. Cálculos e Labels
                media_periodo = diario['Venda'].mean()
                
                diario['Performance'] = diario['Venda'].apply(
                    lambda x: 'Acima da Média' if x >= media_periodo else 'Abaixo da Média'
                )
                
                diario['Data_Formatada'] = diario['Data'].apply(lambda x: f"{x.day:02d}/{x.month:02d}")
                diario['Venda_Label'] = diario['Venda'].apply(formatar_real)

                # 3. Extrai a lista de ordem correta para forçar no gráfico
                ordem_cronologica = diario['Data_Formatada'].tolist()

                fig_d = px.bar(
                    diario, 
                    x='Data_Formatada', 
                    y='Venda',
                    color='Performance',
                    color_discrete_map={
                        'Acima da Média': '#2ecc71',
                        'Abaixo da Média': '#e74c3c'
                    },
                    title="Vendas por Dia",
                    text='Venda_Label'
                )
                
                # 4. APLICAÇÃO DA ORDEM FORÇADA (categoryorder)
                fig_d.update_layout(
                    xaxis=dict(
                        title="",
                        type='category',
                        categoryorder='array',
                        categoryarray=ordem_cronologica # Força a ordem da lista extraída acima
                    ),
                    yaxis_title=None,
                    yaxis_showticklabels=False,
                    separators=",.",
                    legend_title_text="",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                fig_d.update_traces(
                    textposition='none', 
                    hovertemplate='<b>%{x}</b><br>Venda: %{text}<extra></extra>'
                )
                
                st.plotly_chart(fig_d, use_container_width=True)

                # --- 4. CARDS INFERIORES ---
                st.markdown("##### Estatísticas do Período")
                s1, s2, s3 = st.columns(3)
                
                melhor_dia = diario['Venda'].max()
                pior_dia = diario['Venda'].min()
                
                dia_melhor_obj = diario.loc[diario['Venda'] == melhor_dia, 'Data'].values[0] if not diario.empty else None
                dia_pior_obj = diario.loc[diario['Venda'] == pior_dia, 'Data'].values[0] if not diario.empty else None
                
                label_melhor = f"{pd.to_datetime(dia_melhor_obj).strftime('%d/%m')} ({traduzir_dia(pd.to_datetime(dia_melhor_obj))})" if dia_melhor_obj else "-"
                label_pior = f"{pd.to_datetime(dia_pior_obj).strftime('%d/%m')} ({traduzir_dia(pd.to_datetime(dia_pior_obj))})" if dia_pior_obj else "-"

                s1.metric("Média Diária", formatar_real(media_periodo))
                s2.metric(f"Melhor Dia: {label_melhor}", formatar_real(melhor_dia))
                s3.metric(f"Pior Dia: {label_pior}", formatar_real(pior_dia))

            else:
                st.warning("Sem dados para o período selecionado.")
    except Exception as e:
        st.error(f"Erro no Dashboard: {e}")
        st.cache_resource.clear()

# ==========================================================
# PÁGINA 2: CARGA COM SUBSTITUIÇÃO
# ==========================================================
elif pagina == "⚙️ Atualizar Dados":
    st.markdown("### ⚙️ Atualização e Correção")
    st.info("Utilize esta aba para carregar novos arquivos ou corrigir meses com dados errados.")
    
    arquivo = st.file_uploader("Arraste seu arquivo aqui (Excel ou CSV)", type=["xlsx", "csv", "xls"])
    substituir = st.checkbox("⚠️ Modo de Correção: Substituir dados existentes (Marque se precisar re-upar um mês com erro)")

    if arquivo and st.button("Processar e Salvar"):
        try:
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
                st.error("❌ Coluna 'Pedido' não encontrada no arquivo.")
                st.stop()

            arquivo.seek(0)
            if arquivo.name.endswith('.csv'):
                df_novo = pd.read_csv(arquivo, header=idx_cabecalho)
            else:
                df_novo = pd.read_excel(arquivo, header=idx_cabecalho)

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
                st.error("Erro Crítico: Coluna de ID do Pedido não identificada.")
                st.stop()
                
            df_limpo = df_novo[colunas_validas].copy()
            
            if 'data_hora' in df_limpo.columns:
                df_limpo['data_hora'] = pd.to_datetime(df_limpo['data_hora'], format='%d/%m/%Y - %H:%M', errors='coerce')
                df_limpo = df_limpo.dropna(subset=['data_hora'])

            df_limpo['id_pedido'] = pd.to_numeric(df_limpo['id_pedido'], errors='coerce')
            df_limpo = df_limpo.dropna(subset=['id_pedido'])
            df_limpo['id_pedido'] = df_limpo['id_pedido'].astype('int64')

            if 'canal_venda' in df_limpo.columns:
                df_limpo['canal_venda'] = df_limpo['canal_venda'].fillna('Indefinido').astype(str)
            if 'valor_bruto' in df_limpo.columns:
                df_limpo['valor_bruto'] = df_limpo['valor_bruto'].fillna(0.0)
            if 'valor_liquido' in df_limpo.columns:
                df_limpo['valor_liquido'] = df_limpo['valor_liquido'].fillna(0.0)

            df_agrupado = df_limpo.groupby('id_pedido', as_index=False).agg({
                'data_hora': 'first',      
                'canal_venda': 'first',    
                'valor_bruto': 'sum',      
                'valor_liquido': 'sum'     
            })
            
            engine = get_engine()
            df_para_subir = pd.DataFrame()
            ids_no_arquivo = df_agrupado['id_pedido'].tolist()
            
            if substituir:
                st.info("🔄 Modo de Correção Ativado. Substituindo registros...")
                with engine.begin() as conn:
                    if ids_no_arquivo:
                        ids_str = [str(x) for x in ids_no_arquivo]
                        chunk_size = 1000
                        for i in range(0, len(ids_str), chunk_size):
                            batch = tuple(ids_str[i:i + chunk_size])
                            if batch:
                                conn.execute(text(f"DELETE FROM vendas WHERE id_pedido::text IN {batch}"))
                df_para_subir = df_agrupado
            else:
                with engine.connect() as conn:
                    ids_banco = pd.read_sql(text("SELECT id_pedido FROM vendas"), conn)
                lista_existentes = set(ids_banco['id_pedido'].astype('int64').tolist())
                df_para_subir = df_agrupado[~df_agrupado['id_pedido'].isin(lista_existentes)]

            qtd = len(df_para_subir)
            
            if qtd > 0:
                progresso = st.progress(0)
                st.write(f"Gravando {qtd} registros...")
                
                with engine.begin() as conn:
                    df_para_subir.to_sql('vendas', conn, if_exists='append', index=False, chunksize=1000)
                
                progresso.progress(100)
                st.success("✅ Processo concluído com sucesso!")
                st.balloons()
                st.cache_data.clear()
            else:
                st.warning("⚠️ Arquivo processado. Nenhuma venda nova encontrada.")

        except Exception as e:
            st.error(f"Erro detalhado: {e}")
            st.cache_resource.clear()