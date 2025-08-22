# Exploración de datos MELI - Tiempos y Movimientos
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Configurar estilo visual
sns.set(style="whitegrid", palette="pastel")

# Cargar la base desde Excel
df = pd.read_excel("Meli_ME.xlsx")
print(df.columns.tolist())


# Histograma de Frecuencia de Uso Diaria
plt.figure(figsize=(8, 4))
sns.histplot(df["Frecuencia_Uso_Diaria"], bins=20, kde=True)
plt.title("Distribución de Frecuencia de Uso Diaria")
plt.xlabel("Frecuencia de Uso Diaria")
plt.ylabel("Cantidad de Productos")
plt.tight_layout()
plt.show()

# Histograma de Tiempo Promedio de Toma
plt.figure(figsize=(8, 4))
sns.histplot(df["Tiempo_Promedio_Toma (seg)"], bins=20, kde=True, color="orange")
plt.title("Distribución del Tiempo Promedio de Toma")
plt.xlabel("Tiempo Promedio (segundos)")
plt.ylabel("Cantidad de Productos")
plt.tight_layout()
plt.show()

# Boxplot de Tiempo de Toma por Categoría
plt.figure(figsize=(10, 5))
sns.boxplot(x="Categoría", y="Tiempo_Promedio_Toma (seg)", data=df)
plt.title("Tiempo Promedio de Toma por Categoría")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Scatter Plot entre Frecuencia y Tiempo de Toma
plt.figure(figsize=(8, 6))
sns.scatterplot(
    x="Frecuencia_Uso_Diaria",
    y="Tiempo_Promedio_Toma (seg)",
    hue="Categoría",
    data=df,
    palette="tab10"
)
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Cargar el archivo Excel
archivo = "Meli_ME.xlsx"
df = pd.read_excel(archivo)

# Verificamos que las columnas existan correctamente
print("Columnas disponibles:", df.columns.tolist())

# Seleccionar solo las columnas necesarias para el clustering
X = df[["Frecuencia_Uso_Diaria", "Tiempo_Promedio_Toma (seg)"]]

# Escalar los datos
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Aplicar KMeans con 3 clusters (puedes ajustar a 4 o más si lo deseas)
kmeans = KMeans(n_clusters=3, random_state=0)
df["Cluster"] = kmeans.fit_predict(X_scaled)

# Visualizar los resultados
plt.figure(figsize=(10, 6))
colors = ["red", "green", "blue"]

for cluster in range(3):
    cluster_data = df[df["Cluster"] == cluster]
    plt.scatter(
        cluster_data["Frecuencia_Uso_Diaria"],
        cluster_data["Tiempo_Promedio_Toma (seg)"],
        label=f"Cluster {cluster}",
        color=colors[cluster]
    )

plt.title("Segmentación de productos por K-Means")
plt.xlabel("Frecuencia de Uso Diaria")
plt.ylabel("Tiempo Promedio de Toma (seg)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
etiquetas = {
    0: "Alta rotación / bajo tiempo",
    1: "Rotación media / tiempo eficiente",
    2: "Tiempo alto / eficiencia baja"
}
df["Etiqueta_Cluster"] = df["Cluster"].map(etiquetas)
resumen = df.groupby("Etiqueta_Cluster")[["Frecuencia_Uso_Diaria", "Tiempo_Promedio_Toma (seg)"]].agg(["mean", "count", "std"])
print(resumen)
df.to_excel("Segmentacion_Productos_KMeans.xlsx", index=False)

import pandas as pd

# Cargar archivo Excel con datos
file_path = "/mnt/data/Meli_ME.xlsx"
df = pd.read_excel(file_path)

# Convertir nombres de columnas para uso más cómodo
df.columns = [col.strip().replace(' ', '_').replace('(', '').replace(')', '') for col in df.columns]

# Calcular métricas base de productividad
df['Tiempo_Total_Por_Producto'] = df['Frecuencia_Uso_Diaria'] * df['Tiempo_Promedio_Toma_seg']

# Métricas generales
tiempo_total_diario = df['Tiempo_Total_Por_Producto'].sum()
tiempo_promedio_por_producto = df['Tiempo_Total_Por_Producto'].mean()
productos_totales = df['Frecuencia_Uso_Diaria'].sum()

# Tiempo total por categoría
tiempo_por_categoria = df.groupby('Categoría')['Tiempo_Total_Por_Producto'].sum().sort_values(ascending=False).reset_index()

# Productividad (volumen movido / tiempo total)
volumen_total = (df['Volumen_cm³'] * df['Frecuencia_Uso_Diaria']).sum()
productividad_global = volumen_total / tiempo_total_diario

import seaborn as sns
import matplotlib.pyplot as plt
import ace_tools as tools

# Gráfico: Tiempo total por categoría
plt.figure(figsize=(10,6))
sns.barplot(data=tiempo_por_categoria, x='Tiempo_Total_Por_Producto', y='Categoría', palette='viridis')
plt.xlabel("Tiempo Total de Toma Diario (seg)")
plt.ylabel("Categoría")
plt.title("Distribución del Tiempo de Toma por Categoría")
plt.tight_layout()
plt.grid(axis='x')

# Mostrar tabla de resultados
resumen = pd.DataFrame({
    "Métrica": [
        "Tiempo total diario (segundos)",
        "Tiempo promedio por producto (segundos)",
        "Volumen total movido (cm³)",
        "Índice de productividad (cm³ por segundo)"
    ],
    "Valor": [
        round(tiempo_total_diario, 2),
        round(tiempo_promedio_por_producto, 2),
        round(volumen_total, 2),
        round(productividad_global, 4)
    ]
})

tools.display_dataframe_to_user(name="Resumen de Productividad", dataframe=resumen)

import pandas as pd

# Cargar archivo Excel con datos
file_path = "/mnt/data/Meli_ME.xlsx"
df = pd.read_excel(file_path)

# Convertir nombres de columnas para uso más cómodo
df.columns = [col.strip().replace(' ', '_').replace('(', '').replace(')', '') for col in df.columns]

# Calcular métricas base de productividad
df['Tiempo_Total_Por_Producto'] = df['Frecuencia_Uso_Diaria'] * df['Tiempo_Promedio_Toma_seg']

# Métricas generales
tiempo_total_diario = df['Tiempo_Total_Por_Producto'].sum()
tiempo_promedio_por_producto = df['Tiempo_Total_Por_Producto'].mean()
productos_totales = df['Frecuencia_Uso_Diaria'].sum()

# Tiempo total por categoría
tiempo_por_categoria = df.groupby('Categoría')['Tiempo_Total_Por_Producto'].sum().sort_values(ascending=False).reset_index()

# Productividad (volumen movido / tiempo total)
volumen_total = (df['Volumen_cm³'] * df['Frecuencia_Uso_Diaria']).sum()
productividad_global = volumen_total / tiempo_total_diario

import seaborn as sns
import matplotlib.pyplot as plt
import ace_tools as tools

# Gráfico: Tiempo total por categoría
plt.figure(figsize=(10,6))
sns.barplot(data=tiempo_por_categoria, x='Tiempo_Total_Por_Producto', y='Categoría', palette='viridis')
plt.xlabel("Tiempo Total de Toma Diario (seg)")
plt.ylabel("Categoría")
plt.title("Distribución del Tiempo de Toma por Categoría")
plt.tight_layout()
plt.grid(axis='x')

# Mostrar tabla de resultados
resumen = pd.DataFrame({
    "Métrica": [
        "Tiempo total diario (segundos)",
        "Tiempo promedio por producto (segundos)",
        "Volumen total movido (cm³)",
        "Índice de productividad (cm³ por segundo)"
    ],
    "Valor": [
        round(tiempo_total_diario, 2),
        round(tiempo_promedio_por_producto, 2),
        round(volumen_total, 2),
        round(productividad_global, 4)
    ]
})

tools.display_dataframe_to_user(name="Resumen de Productividad", dataframe=resumen)
