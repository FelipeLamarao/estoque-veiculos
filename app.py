import streamlit as st
import pandas as pd
import os
import numpy as np
import glob

# Page Configuration
st.set_page_config(
    page_title="Pedragon - Gestão de Estoque",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Style for Premium Aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Inter:wght@400;500;600;700&display=swap');
    
    /* Apply base fonts */
    .main, [class*="css"], [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Title Styling */
    .main-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
        font-size: 2.5rem;
    }
    
    .subtitle {
        font-family: 'Inter', sans-serif;
        color: #64748B;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }
    
    /* Metric Card Customizations */
    [data-testid="stMetric"], [data-testid="metric-container"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 20px 24px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    [data-testid="stMetric"]:hover, [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        border-color: #CBD5E1;
    }
    
    [data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif;
        font-size: 34px !important;
        font-weight: 800 !important;
        color: #1E3A8A !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Inter', sans-serif;
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.75px;
    }
</style>
""", unsafe_allow_html=True)

# Helper to format currency
def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Load data with caching as strictly required
@st.cache_data(ttl=60)
def load_data(filepath):
    if not os.path.exists(filepath):
        # Return empty dataframe with correct columns if file not found yet
        return pd.DataFrame(columns=["modelo", "opc", "ano", "cor", "Dias estoque", "Situação", "Placa", "Chassi", "Marca", "Preço", "familia"])
    
    # Robust load supporting Excel or delimited CSV
    if filepath.endswith('.xlsx') or filepath.endswith('.xls'):
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath, sep=';', encoding='latin-1')
        # If read_csv fallback fails due to single column (e.g. if it is comma-separated instead of semicolon-separated), reload with ','
        if df.shape[1] <= 1:
            df = pd.read_csv(filepath, sep=',', encoding='utf-8')

    # Strip double quotes from all string/object columns to avoid unbalanced quote artifacts
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.replace('"', '', regex=False).str.strip()

    # Map column names if they are different
    rename_mapping = {
        'Modelo': 'modelo',
        'OPC': 'opc',
        'Ano': 'ano',
        'Cor': 'cor',
        'Dias Estoque': 'Dias estoque',
        'Situação': 'Situação',
        'Preço Público/Venda': 'Preço'
    }
    df = df.rename(columns=rename_mapping)

    # 1. Fill missing Brand (Marca) since all vehicles are Chevrolet in Pedragon GM data
    if 'Marca' not in df.columns:
        df['Marca'] = 'Chevrolet'
    else:
        df['Marca'] = df['Marca'].fillna('Chevrolet').astype(str).str.strip()

    # 2. Clean and parse Plates and Chassis
    if 'Placa' in df.columns:
        df['Placa'] = df['Placa'].fillna('SEM PLACA').astype(str).str.strip()
        df['Placa'] = df['Placa'].replace('', 'SEM PLACA')
    else:
        df['Placa'] = 'SEM PLACA'

    if 'Chassi' in df.columns:
        df['Chassi'] = df['Chassi'].fillna('').astype(str).str.strip()
    else:
        df['Chassi'] = ''

    # 3. Clean and parse Price
    if 'Preço' in df.columns:
        df['Preço'] = df['Preço'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['Preço'] = pd.to_numeric(df['Preço'], errors='coerce').fillna(0.0)
    else:
        df['Preço'] = 0.0

    # 4. Clean and parse Year (keep original text format like 2025/2026)
    if 'ano' in df.columns:
        df['ano'] = df['ano'].fillna('').astype(str).str.strip()
    else:
        df['ano'] = 'N/A'

    # 5. Clean and parse Status (Situação)
    if 'Situação' in df.columns:
        df['Situação'] = df['Situação'].fillna('Disponível').astype(str).str.strip()
        df['Situação'] = df['Situação'].replace('', 'Disponível')
    else:
        df['Situação'] = 'Disponível'

    # 6. Calculate stock days if missing
    if 'Dias estoque' not in df.columns:
        if 'Data de Entrada' in df.columns:
            try:
                date_ent = pd.to_datetime(df['Data de Entrada'], errors='coerce')
                df['Dias estoque'] = (pd.to_datetime('now') - date_ent).dt.days.fillna(0).astype(int)
            except Exception:
                df['Dias estoque'] = 0
        elif 'Data Chegada' in df.columns:
            try:
                date_arr = pd.to_datetime(df['Data Chegada'], format='%d/%m/%Y', errors='coerce')
                df['Dias estoque'] = (pd.to_datetime('now') - date_arr).dt.days.fillna(0).astype(int)
            except Exception:
                df['Dias estoque'] = 0
        else:
            df['Dias estoque'] = 0
    else:
        df['Dias estoque'] = pd.to_numeric(df['Dias estoque'], errors='coerce').fillna(0).astype(int)

    # 7. Normalize remaining required fields
    for col in ["modelo", "opc", "cor"]:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
        else:
            df[col] = ''

    # Check case-insensitively for a column named 'familia'
    familia_col = next((col for col in df.columns if col.lower() == 'familia'), None)
    if familia_col:
        df = df.rename(columns={familia_col: 'familia'})
        df['familia'] = df['familia'].fillna('').astype(str).str.strip().str.upper()
    else:
        df['familia'] = df['modelo'].astype(str).apply(
            lambda x: (x.split()[1] if len(x.split()) > 1 else (x.split()[0] if x.split() else '')).upper()
        )

    return df

# Main Title
st.markdown("<h1 class='main-title'>🚗 Pedragon - Controle de Estoque</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Painel interativo para consulta e monitoramento do estoque de veículos em tempo real.</p>", unsafe_allow_html=True)

# Load the inventory (Estoque Físico)
csv_path = "estoque.csv"
df_estoque = load_data(csv_path)
df_estoque['Fase'] = 'Estoque Físico'
df_estoque['Origem'] = 'Próprio'

# Load progress data (Em Progresso)
arquivos_progresso = [f for f in os.listdir('.') if f.startswith('Rel_MalaDireta') and (f.endswith('.xls') or f.endswith('.xlsx'))]

if arquivos_progresso:
    arquivos_progresso.sort(key=os.path.getmtime, reverse=True)
    arquivo_atual = arquivos_progresso[0]
    df_progresso = load_data(arquivo_atual)
else:
    st.error('Arquivo de mala direta não encontrado na pasta!')
    df_progresso = pd.DataFrame()

# Forçar Renomeação da Coluna Chassi (tratando 'Pedido', 'Pedido (Chassi)', etc)
df_progresso = df_progresso.rename(columns={
    'Pedido': 'Chassi',
    'Pedido (Chassi)': 'Chassi',
    'Chassi/Pedido': 'Chassi'
})

# Aplicar Regra M65 (Próprio/Extra)
df_progresso['Origem'] = np.where(df_progresso['Chassi'].astype(str).str.lower().str.endswith('m65'), 'Próprio', 'Extra')

# Alinhamento de Colunas Básicas para ficarem idênticas às de estoque
df_progresso = df_progresso.rename(columns={
    'Modelo': 'modelo',
    'Cor': 'cor',
    'Ano': 'ano'
})

# Add Fase column if missing
df_progresso['Fase'] = 'Em Progresso'

# União (pd.concat)
df_master = pd.concat([df_estoque, df_progresso], ignore_index=True)

# Converta explicitamente todas as colunas do tipo 'object' (texto) para strings puras e substitua os NaNs por textos vazios:
cols_texto = df_master.select_dtypes(include=['object']).columns
df_master[cols_texto] = df_master[cols_texto].fillna('').astype(str)

# Force a coluna 'Dias estoque' a ser numérica lidando com os valores vazios do progresso:
df_master['Dias estoque'] = pd.to_numeric(df_master['Dias estoque'], errors='coerce').fillna(0).astype(int)

df = df_master

if df.empty:
    st.warning("Os arquivos de dados de estoque ou progresso ainda não foram gerados ou estão vazios. Por favor, gere os dados mockados.")
else:
    # Raio-X dos Dados (Debug)
    with st.expander('🛠️ Raio-X dos Dados (Modo Debug)'):
        st.write(f'Total no Estoque Físico: {len(df_estoque)} linhas')
        st.write(f'Total no Progresso: {len(df_progresso)} linhas')
        st.write('Amostra dos dados de Progresso lidos:')
        st.dataframe(df_progresso.head())

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filtros do Estoque")
    
    # 0. Fase do Veículo Filter (logo no topo)
    selected_fases = st.sidebar.multiselect(
        "Fase do Veículo",
        options=["Estoque Físico", "Em Progresso"],
        default=["Estoque Físico", "Em Progresso"],
        placeholder="Todas as fases"
    )
    
    # 0.1 Família do Veículo Filter
    all_families = sorted(df["familia"].unique())
    selected_families = st.sidebar.multiselect(
        "Família do Veículo",
        options=all_families,
        placeholder="Todas as famílias"
    )
    
    # 1. Brand Filter
    all_brands = sorted(df["Marca"].unique())
    selected_brands = st.sidebar.multiselect(
        "Filtrar por Marca",
        options=all_brands,
        placeholder="Todas as marcas"
    )
    
    # 2. Year multiselect filter
    all_years = sorted(df["ano"].unique())
    selected_years = st.sidebar.multiselect(
        "Filtrar por Ano",
        options=all_years,
        placeholder="Todos os anos"
    )
    
    # 3. Dias de Pátio slider
    min_dias = 0
    max_dias = int(df["Dias estoque"].max())
    selected_dias = st.sidebar.slider(
        "Dias de Pátio (Estoque)",
        min_value=min_dias,
        max_value=max_dias,
        value=(min_dias, max_dias)
    )
    
    # 4. Color Filter
    all_colors = sorted(df["cor"].unique())
    selected_colors = st.sidebar.multiselect(
        "Filtrar por Cor",
        options=all_colors,
        placeholder="Todas as cores"
    )
    
    # 5. Situação / Pedidos Filter
    situacao_options = ["Todos", "Livre (Disponível)", "Com Pedido/Reservado", "Vendido"]
    selected_situacao = st.sidebar.selectbox(
        "Situação do Veículo",
        options=situacao_options,
        index=0
    )
    
    isolate_pedidos = st.sidebar.checkbox("Isolar Veículos com Pedido")
    
    # --- MAIN PAGE: FREE TEXT SEARCH ---
    search_query = st.text_input(
        "Busca Rápida",
        placeholder="Digite o Modelo, Chassi ou Pacote Opcional (ex: R7R) para filtrar...",
        help="A pesquisa não diferencia maiúsculas/minúsculas e busca correspondências parciais em Modelo, Chassi e Pacotes Opcionais."
    )
    
    # --- FILTERING LOGIC ---
    filtered_df = df.copy()
    
    # Apply Fase filter
    if selected_fases:
        filtered_df = filtered_df[filtered_df["Fase"].isin(selected_fases)]
    else:
        filtered_df = filtered_df[filtered_df["Fase"].isin([])]
        
    # Apply sidebar filters
    if selected_families:
        filtered_df = filtered_df[filtered_df["familia"].isin(selected_families)]
        
    if selected_brands:
        filtered_df = filtered_df[filtered_df["Marca"].isin(selected_brands)]
        
    if selected_years:
        filtered_df = filtered_df[filtered_df["ano"].isin(selected_years)]
    
    # Apply Dias de Pátio filter
    filtered_df = filtered_df[
        (filtered_df["Dias estoque"] >= selected_dias[0]) &
        (filtered_df["Dias estoque"] <= selected_dias[1])
    ]
    
    # Apply Color filter
    if selected_colors:
        filtered_df = filtered_df[filtered_df["cor"].isin(selected_colors)]
        
    # Apply Situação filter
    if selected_situacao == "Livre (Disponível)":
        filtered_df = filtered_df[filtered_df["Situação"] == "Disponível"]
    elif selected_situacao == "Com Pedido/Reservado":
        filtered_df = filtered_df[filtered_df["Situação"].isin(["Pedido", "Proposta", "Bloqueado"])]
    elif selected_situacao == "Vendido":
        filtered_df = filtered_df[filtered_df["Situação"].str.lower().str.contains("vendido", na=False)]
        
    # Apply isolate_pedidos filter
    if isolate_pedidos:
        filtered_df = filtered_df[filtered_df["Situação"] == "Pedido"]
        
    # Apply free text search filter: Modelo OR Chassi OR OPC (case-insensitive conversion)
    if search_query:
        search_query_clean = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["modelo"].str.lower().str.contains(search_query_clean, na=False) |
            filtered_df["Chassi"].str.lower().str.contains(search_query_clean, na=False) |
            filtered_df["opc"].str.lower().str.contains(search_query_clean, na=False)
        ]
        
    # --- PLACAR DE RESULTADOS (MÉTRICAS DINÂMICAS) ---
    total_cars = len(filtered_df)
    estoque_fisico_count = len(filtered_df[filtered_df["Fase"] == "Estoque Físico"])
    em_progresso_count = len(filtered_df[filtered_df["Fase"] == "Em Progresso"])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Total Encontrado",
            value=f"{total_cars} veículos"
        )
    with col2:
        st.metric(
            label="Estoque Físico",
            value=f"{estoque_fisico_count} veículos"
        )
    with col3:
        st.metric(
            label="Em Progresso",
            value=f"{em_progresso_count} veículos"
        )
        if em_progresso_count > 0:
            progresso_df = filtered_df[filtered_df["Fase"] == "Em Progresso"]
            proprio_count = len(progresso_df[progresso_df["Origem"] == "Próprio"])
            extra_count = len(progresso_df[progresso_df["Origem"] == "Extra"])
            st.markdown(
                f"<p style='font-size: 0.85rem; color: #64748B; margin-top: -10px;'>"
                f"Divisão: <b>{proprio_count} Próprio</b> / <b>{extra_count} Extra</b>"
                f"</p>",
                unsafe_allow_html=True
            )
        
    # --- CRITICAL VEHICLES (OVER 90 DAYS) ---
    veiculos_criticos = filtered_df[filtered_df["Dias estoque"] > 90]
    if not veiculos_criticos.empty:
        veiculos_criticos_sorted = veiculos_criticos.sort_values(by="Dias estoque", ascending=False)
        criticos_cols = ["Fase", "ano", "modelo", "cor", "Dias estoque", "Situação"]
        criticos_cols = [c for c in criticos_cols if c in veiculos_criticos_sorted.columns]
        
        with st.expander(f"⚠️ Alerta: {len(veiculos_criticos)} Veículos Críticos com Mais de 90 Dias no Pátio", expanded=True):
            st.warning("Atenção! Estes veículos estão no estoque há muito tempo e necessitam de ação comercial prioritária:")
            st.dataframe(
                veiculos_criticos_sorted[criticos_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Dias estoque": st.column_config.NumberColumn("Dias no Pátio", format="%d")
                }
            )
    else:
        st.success("✅ Nenhum veículo acima de 90 dias no pátio!")
        
    st.markdown("<hr style='margin: 20px 0; border: 0; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
    
    # --- SUMMARY TABLE ---
    st.subheader("Resumo: Quantidade por Fase, Ano e Modelo")
    
    if filtered_df.empty:
        st.info("Nenhum veículo encontrado para os filtros selecionados.")
    else:
        summary_df = filtered_df.groupby(["Fase", "ano", "modelo"]).size().reset_index(name="Quantidade")
        summary_df = summary_df.sort_values(by=["Fase", "ano", "modelo"])
        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fase": st.column_config.TextColumn("Fase"),
                "ano": st.column_config.TextColumn("Ano"),
                "modelo": st.column_config.TextColumn("Modelo"),
                "Quantidade": st.column_config.NumberColumn("Quantidade", format="%d")
            }
        )
        
    st.markdown("<hr style='margin: 20px 0; border: 0; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
    
    # --- DATAFRAME VIEW ---
    st.subheader("Resultados do Estoque")
    
    if filtered_df.empty:
        st.info("Nenhum veículo encontrado para os filtros selecionados.")
    else:
        # Pandas logic to reorder columns with priority columns first
        priority_cols = ["Fase", "modelo", "opc", "ano", "cor", "Dias estoque", "Situação"]
        other_cols = [col for col in filtered_df.columns if col not in priority_cols]
        ordered_df = filtered_df[priority_cols + other_cols]
        
        # Use pandas formatting for table output visual styling and hide the index
        st.dataframe(
            ordered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Preço": st.column_config.NumberColumn(
                    "Preço",
                    format="R$ %.2f"
                ),
                "ano": st.column_config.TextColumn("Ano")
            }
        )
