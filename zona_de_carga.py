
import pandas as pd

# Ruta del archivo
archivo = "DESPERDICIOS DE LA ZONA DE CARGA.xlsx"

# Cargar el archivo
df = pd.read_excel(archivo, sheet_name="Sheet1")

# Filtrar columnas válidas para planta (excluyendo báscula)
planta_columns = [col for col in df.columns if 'PLANTA' in col.upper() and 'BÁSCULA' not in col.upper()]
df['PLANTA'] = df[planta_columns].bfill(axis=1).iloc[:, 0]

# Detectar la columna de fecha
fecha_col = [col for col in df.columns if 'FECHA DE REALIZACIÓN' in col.upper()][0]
df[fecha_col] = pd.to_datetime(df[fecha_col], errors='coerce')

# Filtrar solo registros con planta
df_filtrado = df[df['PLANTA'].notna()]

# Crear resumen
resumen = (
    df_filtrado.groupby('PLANTA')[fecha_col]
    .agg([
        ('Cantidad de registros', 'count'),
        ('Fechas de realización', lambda x: ', '.join(sorted(x.dropna().dt.strftime('%Y-%m-%d'))))
    ])
    .reset_index()
    .sort_values(by='Cantidad de registros', ascending=False)
)

# Guardar en un Excel con dos hojas
with pd.ExcelWriter("Reporte_Desperdicios_Zona_Carga.xlsx", engine='openpyxl') as writer:
    resumen.to_excel(writer, sheet_name="Resumen_Registros", index=False)
    df_filtrado.to_excel(writer, sheet_name="Registros_Crudos", index=False)

