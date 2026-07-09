import pandas as pd
import os

def load_data_fixed(filepath):
    if not os.path.exists(filepath):
        return pd.DataFrame(columns=["modelo", "opc", "ano", "cor", "Dias estoque", "Situação", "Placa", "Chassi", "Marca", "Preço", "familia"])
    
    if filepath.endswith('.xlsx') or filepath.endswith('.xls'):
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath, sep=';', encoding='latin-1')
        if df.shape[1] <= 1:
            df = pd.read_csv(filepath, sep=',', encoding='utf-8')

    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.replace('"', '', regex=False).str.strip()

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

    if 'Marca' not in df.columns:
        df['Marca'] = 'Chevrolet'
    else:
        df['Marca'] = df['Marca'].fillna('Chevrolet').astype(str).str.strip()

    if 'Placa' in df.columns:
        df['Placa'] = df['Placa'].fillna('SEM PLACA').astype(str).str.strip()
        df['Placa'] = df['Placa'].replace('', 'SEM PLACA')
    else:
        df['Placa'] = 'SEM PLACA'

    if 'Chassi' in df.columns:
        df['Chassi'] = df['Chassi'].fillna('').astype(str).str.strip()
    else:
        df['Chassi'] = ''

    if 'Preço' in df.columns:
        df['Preço'] = df['Preço'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['Preço'] = pd.to_numeric(df['Preço'], errors='coerce').fillna(0.0)
    else:
        df['Preço'] = 0.0

    if 'ano' in df.columns:
        df['ano'] = df['ano'].fillna('').astype(str).str.strip()
    else:
        df['ano'] = 'N/A'

    if 'Situação' in df.columns:
        df['Situação'] = df['Situação'].fillna('Disponível').astype(str).str.strip()
        df['Situação'] = df['Situação'].replace('', 'Disponível')
    else:
        df['Situação'] = 'Disponível'

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

    for col in ["modelo", "opc", "cor"]:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
        else:
            df[col] = ''

    familia_col = next((col for col in df.columns if col.lower() == 'familia'), None)
    if familia_col:
        df = df.rename(columns={familia_col: 'familia'})
        df['familia'] = df['familia'].fillna('').astype(str).str.strip().str.upper()
    else:
        df['familia'] = df['modelo'].astype(str).apply(
            lambda x: (x.split()[1] if len(x.split()) > 1 else (x.split()[0] if x.split() else '')).upper()
        )

    return df

df1 = load_data_fixed('estoque.csv')
df2 = load_data_fixed('Rel_MalaDireta - 2026-06-30T114259.554.xls')
print("Columns match:", df1.columns.tolist() == df2.columns.tolist())
print("Columns list 1:", df1.columns.tolist())
print("Columns list 2:", df2.columns.tolist())
print("Dataframe 1 shapes:", df1.shape)
print("Dataframe 2 shapes:", df2.shape)
print("Dataframe 2 Chassi values type & nan count:", df2['Chassi'].isna().sum(), df2['Chassi'].dtype)
