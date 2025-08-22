### ✅ Bloque 5: Configuración inicial de Streamlit
st.set_page_config(page_title="Cotizador Michoacano", layout="centered")
st.image(Image.open("Cemex.png"), width=220)
st.title("Cotizador Móvil")
st.markdown("Completa los siguientes datos para generar una cotización:")

### ✅ Bloque 6: Selección de plaza y vendedores
plazas_disponibles = sorted(df_vendedores["plaza"].dropna().unique())
plaza_seleccionada = st.selectbox("Plaza", plazas_disponibles)
plaza_limpia = plaza_seleccionada.strip().upper()

vendedores_filtrados = df_vendedores[
    df_vendedores["plaza"] == plaza_limpia
]["Vendedor"].dropna().unique().tolist()

### ✅ Bloque 7: Formulario de datos generales
with st.form("datos_formulario"):
    cliente = st.text_input("Cliente")
    obra = st.text_input("Obra")
    contacto = st.text_input("Contacto")

    vendedor_seleccionado = st.selectbox(
        "Vendedor",
        options=vendedores_filtrados if vendedores_filtrados else ["(Sin vendedores disponibles)"]
    )

    submitted = st.form_submit_button("Guardar datos")

    if submitted:
        st.success("Datos registrados correctamente. Ahora selecciona productos para cotizar.")
        st.session_state["form_data"] = {
            "cliente": cliente,
            "obra": obra,
            "contacto": contacto,
            "plaza": plaza_limpia,
            "vendedor": vendedor_seleccionado
        }

### ✅ Bloque 8: Pantalla de productos y cotización dinámica
if "form_data" in st.session_state:

    st.subheader("Buscar productos")
    texto_busqueda = st.text_input("Buscar producto por clave o nombre", key="busqueda_producto")

    productos_filtrados = df_productos[
        df_productos['plaza'] == st.session_state["form_data"]["plaza"]
    ]

    if texto_busqueda:
        texto = texto_busqueda.strip().lower()
        productos_filtrados = productos_filtrados[
            productos_filtrados['clave'].str.lower().str.contains(texto, na=False) |
            productos_filtrados['nombre'].str.lower().str.contains(texto, na=False)
        ]

    if productos_filtrados.empty:
        st.warning("No se encontraron productos con los criterios de búsqueda.")
    else:
        st.markdown("Selecciona productos a agregar:")

        for row in productos_filtrados.itertuples(index=False):
            clave_producto = row.clave
            nombre_producto = row.nombre
            precio = row.precio

            with st.expander(f"{clave_producto} - {nombre_producto} (${precio:.2f})"):
                with st.form(key=f"form_{clave_producto}"):
                    volumen = st.number_input(
                        f"Volumen (m³) - {clave_producto}",
                        min_value=0.0,
                        value=1.0,
                        step=0.5,
                        key=f"vol_{clave_producto}"
                    )

                    precio_unitario = st.number_input(
                        f"Precio unitario ($ MXN) - {clave_producto}",
                        min_value=0.0,
                        value=float(precio),
                        step=1.0,
                        key=f"prec_{clave_producto}"
                    )

                    submitted = st.form_submit_button("Agregar producto")

                if submitted:
                    ya_agregado = any(
                        item.producto.clave == clave_producto
                        for item in st.session_state["cotizacion_items"]
                    )

                    if ya_agregado:
                        st.warning(f"El producto {nombre_producto} ya fue agregado.")
                    elif precio_unitario <= 0:
                        st.warning("El precio debe ser mayor a cero.")
                    elif volumen <= 0:
                        st.warning("El volumen debe ser mayor a cero.")
                    else:
                        nuevo_producto = Producto(clave=clave_producto, nombre=nombre_producto, plaza=row.plaza, precio_referencia=precio)
                        nuevo_item = CotizacionItem(producto=nuevo_producto, volumen=volumen, precio_unitario=precio_unitario)
                        st.session_state["cotizacion_items"].append(nuevo_item)

                        st.success(f"Producto agregado: {nombre_producto} ({volumen} m³)")
                        limpiar_busqueda()
                        st.rerun()


### ✅ Bloque 9: Mostrar resumen de cotización
if st.session_state.get("cotizacion_items"):
    st.subheader("Resumen de productos en la cotización")

    resumen_data = [{
        "Clave": item.producto.clave,
        "Nombre": item.producto.nombre,
        "Volumen (m³)": item.volumen,
        "Precio unitario ($)": item.precio_unitario,
        "Subtotal ($)": item.subtotal()
    } for item in st.session_state["cotizacion_items"]]

    df_resumen = pd.DataFrame(resumen_data)
    st.dataframe(
        df_resumen.style.format({
            "Precio unitario ($)": "${:,.2f}",
            "Subtotal ($)": "${:,.2f}"
        }),
        use_container_width=True
    )

### ✅ Bloque 10: Vista previa de datos generales
if "form_data" in st.session_state:
    datos = st.session_state["form_data"]
    st.subheader("Vista previa de datos generales")
    st.write(f"**Cliente:** {datos['cliente']}")
    st.write(f"**Obra:** {datos['obra']}")
    st.write(f"**Contacto:** {datos['contacto']}")
    st.write(f"**Plaza:** {datos['plaza']}")
    st.write(f"**Vendedor:** {datos['vendedor']}")
    st.write(f"**Total estimado:** ${sum(item.subtotal() for item in st.session_state['cotizacion_items']):,.2f}")

    cotizacion = Cotizacion(
        cliente=datos["cliente"],
        obra=datos["obra"],
        contacto=datos["contacto"],
        plaza=datos["plaza"],
        vendedor=datos["vendedor"],
        items=st.session_state["cotizacion_items"]
    )
    st.session_state["cotizacion"] = cotizacion


### ✅ Bloque 11: Generación de PDF
if "cotizacion" in st.session_state:
    cotizacion = st.session_state["cotizacion"]

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    try:
        pdf.image("Cemex.png", x=10, y=8, w=50)
    except:
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
    for item in cotizacion.items:
        nombre_corto = item.producto.nombre[:35]
        pdf.cell(35, 8, item.producto.clave, 1)
        pdf.cell(65, 8, nombre_corto, 1)
        pdf.cell(25, 8, f"{item.volumen:.2f}", 1, align="R")
        pdf.cell(30, 8, f"${item.precio_unitario:,.2f}", 1, align="R")
        pdf.cell(35, 8, f"${item.subtotal():,.2f}", 1, align="R")
        pdf.ln()

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(155, 8, "Total:", 1)
    pdf.cell(35, 8, f"${cotizacion.total():,.2f}", 1, align="R")
    pdf.ln(15)

    try:
        with open("notas_y_aclaraciones.txt", "r", encoding="utf-8") as file:
            notas = file.read()
            pdf.multi_cell(0, 6, notas)
    except Exception as e:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 10, f"⚠ Error al leer notas: {str(e)}", ln=True)
        pdf.set_text_color(0, 0, 0)

    try:
        pdf.image("servicios_adicionales.png", x=10, y=None, w=190)
        pdf.ln(10)
    except:
        pass

    pdf.add_page()
    try:
        img_width = 190
        x_position = (pdf.w - img_width) / 2
        pdf.image("hidratium.png", x=x_position, y=10, w=img_width)
    except:
        pass

    nombre_pdf = f"cotizacion_{cotizacion.cliente.replace(' ', '')}{datetime.today().strftime('%Y-%m-%d')}.pdf"
    pdf.output(nombre_pdf)

    with open(nombre_pdf, "rb") as file:
        st.download_button(
            label="📄 Descargar PDF",
            data=file,
            file_name=nombre_pdf,
        )

    os.remove(nombre_pdf)
