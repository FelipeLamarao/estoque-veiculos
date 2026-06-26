import streamlit as st
import pandas as pd
import os

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
@st.cache_data
def load_data(filepath):
    if not os.path.exists(filepath):
        # Return empty dataframe with correct columns if file not found yet
        return pd.DataFrame(columns=["modelo", "opc", "ano", "cor", "Dias estoque", "Situação", "Placa", "Chassi", "Marca", "Preço"])
    
    # Robust load supporting Excel or delimited CSV
    if filepath.endswith('.xlsx'):
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

    # 4. Clean and parse Year (extract model year or first part)
    if 'ano' in df.columns:
        df['ano'] = df['ano'].astype(str).str.split('/').str[0].str.strip()
        df['ano'] = pd.to_numeric(df['ano'], errors='coerce').fillna(0).astype(int)
    else:
        df['ano'] = 0

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

    return df

# Main Title
st.markdown("<h1 class='main-title'>🚗 Pedragon - Controle de Estoque</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Painel interativo para consulta e monitoramento do estoque de veículos em tempo real.</p>", unsafe_allow_html=True)

# Load the inventory
csv_path = "estoque.csv"
df = load_data(csv_path)

if df.empty:
    st.warning("O arquivo de dados 'estoque.csv' ainda não foi gerado ou está vazio. Por favor, gere os dados mockados.")
else:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filtros do Estoque")
    
    # 1. Brand Filter
    all_brands = sorted(df["Marca"].unique())
    selected_brands = st.sidebar.multiselect(
        "Filtrar por Marca",
        options=all_brands,
        placeholder="Todas as marcas"
    )
    
    # 2. Year range slider
    min_year = int(df["ano"].min())
    max_year = int(df["ano"].max())
    selected_years = st.sidebar.slider(
        "Intervalo de Ano",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
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
        placeholder="Digite o Chassi ou o Opcional (opc) do veículo para filtrar...",
        help="A pesquisa não diferencia maiúsculas/minúsculas e busca correspondências parciais."
    )
    
    # --- FILTERING LOGIC ---
    filtered_df = df.copy()
    
    # Apply sidebar filters
    if selected_brands:
        filtered_df = filtered_df[filtered_df["Marca"].isin(selected_brands)]
        
    filtered_df = filtered_df[
        (filtered_df["ano"] >= selected_years[0]) & 
        (filtered_df["ano"] <= selected_years[1])
    ]
    
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
        
    # Apply free text search filter: Chassi OR Opcionais (opc)
    if search_query:
        search_query_clean = search_query.strip()
        filtered_df = filtered_df[
            filtered_df["Chassi"].str.contains(search_query_clean, case=False, na=False) |
            filtered_df["opc"].str.contains(search_query_clean, case=False, na=False)
        ]
        
    # --- METRIC CARDS ---
    total_cars = len(filtered_df)
    total_value = filtered_df["Preço"].sum()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="Total de Carros Filtrados",
            value=f"{total_cars} veículos"
        )
    with col2:
        st.metric(
            label="Valor Total do Estoque Filtrado",
            value=format_currency(total_value)
        )
        
    st.markdown("<hr style='margin: 20px 0; border: 0; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
    
    # --- DATAFRAME VIEW ---
    st.subheader("Resultados do Estoque")
    
    if filtered_df.empty:
        st.info("Nenhum veículo encontrado para os filtros selecionados.")
    else:
        # Pandas logic to reorder columns with priority columns first
        priority_cols = ["modelo", "opc", "ano", "cor", "Dias estoque", "Situação"]
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
                "ano": st.column_config.NumberColumn(
                    "Ano",
                    format="%d"
                )
            }
        )
