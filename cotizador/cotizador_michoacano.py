from pathlib import Path
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
IMG_DIR  = BASE_DIR / "images"

vendedores_path = DATA_DIR / "Vendedores zona centro APP.xlsx"
parquet_path    = DATA_DIR / "Rentabilidad.parquet"

from datetime import datetime
from fpdf import FPDF
import os
import pandas as pd
import streamlit as st
from typing import List
from PIL import Image
from dataclasses import dataclass

# =========================
# 0) CONFIG + SESIÓN SEGURA
# =========================
st.set_page_config(page_title="Cotizador Michoacano", layout="centered")

# Inicializa llaves base para evitar KeyError
if "form_data" not in st.session_state:
    st.session_state["form_data"] = {
        "cliente": "",
        "obra": "",
        "contacto": "",
        "plaza": None,
        "vendedor": "",
    }
if "cotizacion_items" not in st.session_state:
    st.session_state["cotizacion_items"] = []

# Utilidad
def limpiar_busqueda():
    if "busqueda_producto" in st.session_state:
        st.session_state["busqueda_producto"] = ""

# =========================
# 1) MODELOS DE DATOS
# =========================
@dataclass
class Producto:
    clave: str
    nombre: str
    plaza: str
    precio_referencia: float

@dataclass
class CotizacionItem:
    producto: Producto
    volumen: float
    precio_unitario: float
    def subtotal(self) -> float:
        return self.volumen * self.precio_unitario

@dataclass
class Cotizacion:
    cliente: str
    obra: str
    contacto: str
    plaza: str
    vendedor: str
    items: list
    def total(self) -> float:
        return sum(item.subtotal() for item in self.items)

# =========================
# 2) CARGA DE DATOS
# =========================
vendedores_path = "Vendedores zona centro APP.xlsx"
xlsb_path = "Rentabilidad .xlsb"

@st.cache_data
def cargar_vendedores(path):
    df = pd.read_excel(path, sheet_name="Hoja6")
    df = df[['Vendedor', 'plaza']].dropna()
    df['plaza'] = df['plaza'].astype(str).str.strip().str.upper()
    df['Vendedor'] = df['Vendedor'].astype(str).str.strip().str.upper()
    return df

@st.cache_data
def cargar_productos(path):
    df = pd.read_excel(
        path,
        sheet_name="Query",
        engine="pyxlsb",
        usecols=['Material_clave', 'Material', 'Plaza', 'Imp PB']
    )
    df = df.rename(columns={
        'Material_clave': 'clave',
        'Material': 'nombre',
        'Plaza': 'plaza',
        'Imp PB': 'precio'
    })
    df.dropna(subset=['clave', 'nombre', 'plaza', 'precio'], inplace=True)
    df = df.drop_duplicates(subset=['clave', 'plaza'])

    @st.cache_data
    def cargar_productos(path):
        df = pd.read_excel(
            path,
            sheet_name="Query",
            engine="pyxlsb",
            usecols=['Material_clave', 'Material', 'Plaza', 'Imp PB']
        ).rename(columns={
            'Material_clave': 'clave',
            'Material': 'nombre',
            'Plaza': 'plaza',
            'Imp PB': 'precio'
        })

        # Limpieza robusta
        df = df.dropna(subset=['clave', 'nombre', 'plaza', 'precio'])
        df['clave'] = df['clave'].astype(str).str.strip()
        df['nombre'] = df['nombre'].astype(str).str.strip()
        df['plaza'] = df['plaza'].astype(str).str.strip().str.upper()  # <= AQUÍ ESTABA EL ERROR
        df['precio'] = pd.to_numeric(df['precio'], errors='coerce')

        df = df.dropna(subset=['precio'])
        df = df.drop_duplicates(subset=['clave', 'plaza'])
        return df

    df_vendedores = cargar_vendedores(vendedores_path)

    # --- Cargar productos con manejo de errores ---
    try:
        df_productos = cargar_productos(xlsb_path)
    except Exception as e:
        st.error("❌ Falló cargar el catálogo de productos.")
        st.exception(e)  # muestra el error real de lectura (ruta, hoja o engine)
        st.stop()

    # 1) Validar None
    if df_productos is None:
        st.error("❌ df_productos es None. Revisa la función 'cargar_productos', la ruta, hoja y columnas.")
        st.stop()

    # 2) Validar que sea DataFrame
    if not isinstance(df_productos, pd.DataFrame):
        st.error(f"❌ df_productos no es un DataFrame. Tipo: {type(df_productos)}")
        st.stop()

    # 3) Validar vacío
    if df_productos.empty:
        st.warning("⚠️ El catálogo de productos se cargó pero está vacío.")
        st.stop()

    # 4) Solo si pasó todas las validaciones, mostramos debug

    try:
        df = pd.read_excel(
            path, sheet_name="Query", engine="pyxlsb",
            usecols=['Material_clave','Material','Plaza','Imp PB']
        )
    except Exception as e_xlsb:
        try:
            df = pd.read_excel(
                path, sheet_name="Query",
                usecols=['Material_clave','Material','Plaza','Imp PB']
            )
        except Exception as e_xlsx:
            raise RuntimeError(f"No se pudo leer productos.\nXLSB: {e_xlsb}\nXLSX: {e_xlsx}")

    df = df.rename(columns={
        'Material_clave': 'clave',
        'Material': 'nombre',
        'Plaza': 'plaza',
        'Imp PB': 'precio'
    }).dropna(subset=['clave','nombre','plaza','precio']).copy()

    df['clave']  = df['clave'].astype(str).str.strip()
    df['nombre'] = df['nombre'].astype(str).str.strip()
    df['plaza']  = df['plaza'].astype(str).str.strip().str.upper()
    df['precio'] = pd.to_numeric(df['precio'], errors='coerce')
    df = df.dropna(subset=['precio']).drop_duplicates(subset=['clave','plaza']).reset_index(drop=True)

    if df.empty:
        raise ValueError("El DataFrame de productos quedó vacío tras la limpieza.")

    return df
# =========================
# 3) UI ENCABEZADO
# =========================
try:
    st.image(Image.open("Cemex.png"), width=220)
except Exception:
    pass
st.title("Cotizador Móvil")
st.markdown("Completa los siguientes datos para generar una cotización:")

# =========================
# CARGA DE VENDEDORES
# =========================

try:
    df_vendedores = cargar_vendedores(vendedores_path)
except Exception as e:
    st.error("❌ Falló cargar el catálogo de vendedores.")
    st.exception(e)
    st.stop()

if df_vendedores is None:
    st.error("❌ df_vendedores es None. Revisa la función 'cargar_vendedores' y la ruta.")
    st.stop()

if not isinstance(df_vendedores, pd.DataFrame):
    st.error(f"❌ df_vendedores no es un DataFrame. Tipo: {type(df_vendedores)}")
    st.stop()

if df_vendedores.empty:
    st.warning("⚠️ El catálogo de vendedores está vacío.")
    st.stop()
# 4) FORMULARIO DATOS GENERALES (blindado)
# =========================

# --- Guardas previas (por si algo falló antes)
if "form_data" not in st.session_state:
    st.session_state["form_data"] = {"cliente":"", "obra":"", "contacto":"", "plaza": None, "vendedor": ""}

if "df_vendedores" not in globals() or df_vendedores is None:
    st.error("❌ df_vendedores no está disponible. Revisa la carga de vendedores antes de esta sección.")
    st.stop()

if not isinstance(df_vendedores, pd.DataFrame) or df_vendedores.empty or "plaza" not in df_vendedores.columns:
    st.error("❌ El catálogo de vendedores está vacío o sin columna 'plaza'.")
    st.stop()

# --- Plazas disponibles
plazas_disponibles = sorted(df_vendedores["plaza"].dropna().astype(str).str.strip().str.upper().unique().tolist())
if not plazas_disponibles:
    st.error("❌ No hay plazas disponibles en df_vendedores.")
    st.stop()

# --- Índice preseleccionado seguro
plaza_actual = st.session_state["form_data"].get("plaza")
plaza_idx = plazas_disponibles.index(plaza_actual) if plaza_actual in plazas_disponibles else 0

with st.form("datos_formulario"):
    plaza_seleccionada = st.selectbox("Plaza", plazas_disponibles, index=plaza_idx)

    # Filtrar vendedores por plaza seleccionada (sin reventar si no hay)
    if "Vendedor" not in df_vendedores.columns:
        st.error("❌ Falta la columna 'Vendedor' en df_vendedores.")
        st.stop()

    vendedores_filtrados = (
        df_vendedores[df_vendedores["plaza"] == plaza_seleccionada]["Vendedor"]
        .dropna().astype(str).str.strip().str.upper().unique().tolist()
    )
    if not vendedores_filtrados:
        vendedores_filtrados = ["(Sin vendedores disponibles)"]

    # Valores por defecto desde session_state
    cliente  = st.text_input("Cliente",  value=st.session_state["form_data"].get("cliente",""))
    obra     = st.text_input("Obra",     value=st.session_state["form_data"].get("obra",""))
    contacto = st.text_input("Contacto", value=st.session_state["form_data"].get("contacto",""))
    vendedor_seleccionado = st.selectbox("Vendedor", options=vendedores_filtrados, index=0)

    form_ok = st.form_submit_button("Guardar datos")

if form_ok:
    st.session_state["form_data"].update({
        "cliente": cliente.strip(),
        "obra": obra.strip(),
        "contacto": contacto.strip(),
        "plaza": str(plaza_seleccionada).strip().upper(),
        "vendedor": str(vendedor_seleccionado).strip().upper(),
    })
    st.success("Datos registrados. Ahora selecciona productos para cotizar.")

# --- Reglas mínimas para continuar
campos_obligatorios = ["cliente", "obra", "plaza"]
faltantes = [c for c in campos_obligatorios if not st.session_state["form_data"].get(c)]
if faltantes:
    st.info("Completa estos campos: " + ", ".join(faltantes))
    st.stop()
# =========================
# CARGA Y VALIDACIÓN PREVIA (debe ir ANTES de usar df_productos)
# =========================
# 1) Cargar productos
try:
    df_productos = cargar_productos(xlsb_path)   # <- tu ruta al catálogo
except Exception as e:
    st.error("❌ Falló cargar el catálogo de productos.")
    st.exception(e)
    st.stop()

# 2) Validaciones
if df_productos is None:
    st.error("❌ df_productos es None. Revisa 'cargar_productos', ruta/hoja/columnas.")
    st.stop()

if not isinstance(df_productos, pd.DataFrame):
    st.error(f"❌ df_productos no es DataFrame. Tipo: {type(df_productos)}")
    st.stop()

if df_productos.empty:
    st.warning("⚠️ df_productos está vacío.")
    st.stop()

# 3) Validar que ya haya plaza seleccionada
plaza_sel = st.session_state.get("form_data", {}).get("plaza")
if not plaza_sel:
    st.info("Selecciona y guarda la **Plaza** en Datos Generales para continuar.")
    st.stop()

    productos_filtrados = df_productos[df_productos['plaza'] == plaza_sel]
    st.subheader("Buscar y agregar productos")

    # (A) APLICAR LIMPIEZA *ANTES* DE CREAR EL WIDGET
    # si en el ciclo anterior marcamos el flag, aquí lo consumimos
    if st.session_state.get("_clear_search"):
        st.session_state["_clear_search"] = False  # consumimos el flag
        st.session_state["busqueda_producto"] = ""  # limpiamos el valor

    # (B) CREAR EL WIDGET DE BÚSQUEDA
    texto_busqueda = st.text_input(
        "Buscar por clave o nombre",
        key="busqueda_producto"
    )
# 5) BÚSQUEDA Y AGREGADO DE PRODUCTOS
# =========================
st.subheader("Buscar y agregar productos")
texto_busqueda = st.text_input("Buscar por clave o nombre", key="busqueda_producto")

plaza_sel = st.session_state.get("form_data", {}).get("plaza")

if not plaza_sel:
    st.warning("Selecciona una plaza en la pantalla inicial para continuar.")
    st.stop()

productos_filtrados = df_productos[df_productos['plaza'] == plaza_sel]
if texto_busqueda:
    t = texto_busqueda.strip().lower()
    productos_filtrados = productos_filtrados[
        productos_filtrados['clave'].str.lower().str.contains(t, na=False) |
        productos_filtrados['nombre'].str.lower().str.contains(t, na=False)
    ]

if productos_filtrados.empty:
    st.warning("No se encontraron productos con los criterios de búsqueda.")
else:
    st.markdown("Selecciona productos a agregar:")
    for row in productos_filtrados.itertuples(index=False):
        clave_producto = row.clave
        nombre_producto = row.nombre
        precio = float(row.precio)

        with st.expander(f"{clave_producto} - {nombre_producto} (${precio:,.2f})"):
            # un form por producto para que Enter dispare el submit
            with st.form(key=f"form_{clave_producto}"):
                volumen = st.number_input(
                    f"Volumen (m³) - {clave_producto}",
                    min_value=0.0, value=1.0, step=0.5, key=f"vol_{clave_producto}"
                )
                precio_unitario = st.number_input(
                    f"Precio unitario ($ MXN) - {clave_producto}",
                    min_value=0.0, value=precio, step=1.0, key=f"prec_{clave_producto}"
                )
                add_ok = st.form_submit_button("Agregar producto")

            if add_ok:
                ya_agregado = any(it.producto.clave == clave_producto for it in st.session_state["cotizacion_items"])
                if ya_agregado:
                    st.warning(f"El producto {nombre_producto} ya fue agregado.")
                elif precio_unitario <= 0:
                    st.warning("El precio debe ser mayor a cero.")
                elif volumen <= 0:
                    st.warning("El volumen debe ser mayor a cero.")
                else:
                    nuevo_item = CotizacionItem(
                        producto=Producto(clave=clave_producto, nombre=nombre_producto,
                                          plaza=row.plaza, precio_referencia=precio),
                        volumen=volumen,
                        precio_unitario=precio_unitario
                    )
                    st.session_state["cotizacion_items"].append(nuevo_item)
                    st.success(f"Producto agregado: {nombre_producto} ({volumen} m³)")
                    def pedir_limpiar_busqueda():
                        st.session_state["_clear_search"] = True

# =========================
# 6) RESUMEN DE COTIZACIÓN
# =========================
if st.session_state["cotizacion_items"]:
    st.subheader("Resumen de productos en la cotización")
    resumen_data = [{
        "Clave": it.producto.clave,
        "Nombre": it.producto.nombre,
        "Volumen (m³)": it.volumen,
        "Precio unitario ($)": it.precio_unitario,
        "Subtotal ($)": it.subtotal()
    } for it in st.session_state["cotizacion_items"]]

    df_resumen = pd.DataFrame(resumen_data)
    st.dataframe(
        df_resumen.style.format({"Precio unitario ($)": "${:,.2f}", "Subtotal ($)": "${:,.2f}"}),
        use_container_width=True
    )

    datos = st.session_state["form_data"]
    st.subheader("Vista previa de datos generales")
    st.write(f"**Cliente:** {datos['cliente']}")
    st.write(f"**Obra:** {datos['obra']}")
    st.write(f"**Contacto:** {datos['contacto']}")
    st.write(f"**Plaza:** {datos['plaza']}")
    st.write(f"**Vendedor:** {datos['vendedor']}")
    st.write(f"**Total estimado:** ${sum(it.subtotal() for it in st.session_state['cotizacion_items']):,.2f}")

    # Botón para generar PDF (todo en un solo bloque)
    if st.button("📄 Generar PDF"):
        cotizacion = Cotizacion(
            cliente=datos["cliente"], obra=datos["obra"], contacto=datos["contacto"],
            plaza=datos["plaza"], vendedor=datos["vendedor"],
            items=st.session_state["cotizacion_items"]
        )

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        try:
            pdf.image("Cemex.png", x=10, y=8, w=50)
        except Exception:
            pass

        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Cotización de productos", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 8, f"Cliente: {cotizacion.cliente}", ln=True)
        pdf.cell(0, 8, f"Obra: {cotizacion.obra}", ln=True)
        pdf.cell(0, 8, f"Contacto: {cotizacion.contacto}", ln=True)
        pdf.cell(0, 8, f"Plaza: {cotizacion.plaza}", ln=True)
        pdf.cell(0, 8, f"Vendedor: {cotizacion.vendedor}", ln=True)
        pdf.cell(0, 8, f"Fecha: {datetime.today().strftime('%d/%m/%Y')}", ln=True)
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 10)
        pdf.cell(35, 8, "Clave", 1)
        pdf.cell(65, 8, "Producto", 1)
        pdf.cell(25, 8, "Volumen", 1, align="C")
        pdf.cell(30, 8, "Precio", 1, align="C")
        pdf.cell(35, 8, "Subtotal", 1, align="C")
        pdf.ln()

        pdf.set_font("Arial", '', 10)
        for it in cotizacion.items:
            nombre_corto = it.producto.nombre[:35]
            pdf.cell(35, 8, it.producto.clave, 1)
            pdf.cell(65, 8, nombre_corto, 1)
            pdf.cell(25, 8, f"{it.volumen:.2f}", 1, align="R")
            pdf.cell(30, 8, f"${it.precio_unitario:,.2f}", 1, align="R")
            pdf.cell(35, 8, f"${it.subtotal():,.2f}", 1, align="R")
            pdf.ln()

        pdf.set_font("Arial", 'B', 10)
        pdf.cell(155, 8, "Total:", 1)
        pdf.cell(35, 8, f"${cotizacion.total():,.2f}", 1, align="R")
        pdf.ln(10)

        # Notas/condiciones (opcional)
        try:
            with open("notas_y_aclaraciones.txt", "r", encoding="utf-8") as fh:
                notas = fh.read()
                pdf.set_font("Arial", '', 9)
                pdf.multi_cell(0, 6, notas)
        except Exception:
            pass

        # Imágenes extra (si existen)
        try:
            pdf.add_page()
            pdf.image("servicios_adicionales.png", x=10, y=None, w=190)
            pdf.ln(5)
            pdf.add_page()
            pdf.image("hidratium.png", x=10, y=10, w=190)
        except Exception:
            pass

        nombre_pdf = f"cotizacion_{cotizacion.cliente.replace(' ', '')}{datetime.today().strftime('%Y-%m-%d')}.pdf"
        pdf.output(nombre_pdf)
        with open(nombre_pdf, "rb") as f:
            st.download_button("📥 Descargar PDF", data=f, file_name=nombre_pdf)
        os.remove(nombre_pdf)

# =========================
# 7) NUEVA COTIZACIÓN
# =========================
if st.button("🧹 Nueva cotización"):
    plaza_keep = st.session_state["form_data"].get("plaza")
    vendedor_keep = st.session_state["form_data"].get("vendedor")
    st.session_state.clear()
    st.session_state["form_data"] = {
        "cliente": "",
        "obra": "",
        "contacto": "",
        "plaza": plaza_keep,
        "vendedor": vendedor_keep,
    }
    st.session_state["cotizacion_items"] = []

def nueva_cotizacion():
    # conservar plaza/vendedor
    plaza_keep    = st.session_state.get("form_data", {}).get("plaza")
    vendedor_keep = st.session_state.get("form_data", {}).get("vendedor")

    # preservar catálogos/cache en sesión para no recargar
    keep_keys = ["df_productos", "df_productos_custom", "custom_version"]
    keep = {k: st.session_state[k] for k in keep_keys if k in st.session_state}

    st.session_state.clear()
    st.session_state.update(keep)

    st.session_state["form_data"] = {
        "cliente": "", "obra": "", "contacto": "",
        "plaza": plaza_keep, "vendedor": vendedor_keep,
    }
    st.session_state["cotizacion_items"] = []
    st.session_state["_clear_search"] = True  # limpiar búsqueda en el próximo render

    st.rerun()

