import streamlit as st
import pdfplumber
import re
from datetime import datetime
from docx import Document
from io import BytesIO
import zipfile

# --- CONFIGURACIÓN DE NEGOCIO ---
PRECIO_SERVICIO = 14990
# ⚠️ CAMBIA ESTO: Pega aquí tu link real de Mercado Pago cuando lo tengas
LINK_MERCADO_PAGO = "https://link.mercadopago.cl/TU_LINK_AQUI" 
CLAVE_ACCESO = "AUTO2026"

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="BorraTusMultas.cl", page_icon="⚖️", layout="centered")

st.markdown("""
    <style>
    /* Reset visual */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    html, body, [class*="css"]  {font-family: 'Inter', sans-serif; background-color: #f8fafc;}
    
    /* Hero Section */
    .hero {text-align: center; padding: 30px 0;}
    .hero h1 {color: #0f172a; font-weight: 900; font-size: 2.5rem; letter-spacing: -1px; margin-bottom: 5px;}
    .hero p {color: #64748b; font-size: 1.1rem;}

    /* Cajas de Instrucción */
    .instruction-box {
        background: white; padding: 25px; border-radius: 12px;
        border: 1px solid #e2e8f0; text-align: center; margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        height: 100%;
    }
    .step-badge {
        background-color: #3b82f6; color: white; padding: 5px 12px; border-radius: 20px;
        font-weight: bold; font-size: 0.8rem; text-transform: uppercase; margin-bottom: 10px; display: inline-block;
    }
    
    /* Botón Externo (Registro Civil) */
    .btn-registrocivil {
        display: block; width: 100%; padding: 15px; margin-top: 15px;
        background-color: #00519E; color: white; /* Azul Gobierno */
        text-decoration: none; border-radius: 8px; text-align: center; font-weight: bold; 
        border: 1px solid #003f7a; transition: 0.3s;
    }
    .btn-registrocivil:hover {background-color: #003f7a;}

    /* Botón de Pago (Mercado Pago) */
    .pay-btn {
        display: block; width: 100%; background: #FACC15; color: black;
        font-weight: 900; text-align: center; padding: 20px; border-radius: 12px;
        text-decoration: none; font-size: 1.4rem; box-shadow: 0 10px 15px -3px rgba(250, 204, 21, 0.3);
        border: 2px solid #eab308;
    }
    .pay-btn:hover {transform: scale(1.02); background: #fde047;}

    /* Resultados */
    .success-box {
        background: white; border: 2px solid #22c55e; border-radius: 16px;
        padding: 30px; text-align: center; margin-top: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .money-tag {
        font-size: 3.5rem; font-weight: 900; color: #15803d;
        letter-spacing: -2px; line-height: 1.1; margin: 15px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BACKEND (CEREBRO) ---
def limpiar_texto(texto):
    if not texto: return ""
    return texto.replace('"', '').replace(',', '').strip().upper()

def es_prescribible(fecha_str):
    try:
        fecha_clean = fecha_str.split(" ")[0].strip()
        fecha_obj = datetime.strptime(fecha_clean, '%d-%m-%Y')
        hoy = datetime.now()
        # 3 años = 1095 días
        return (hoy - fecha_obj).days > 1095
    except:
        return False

def procesar_pdf(archivo):
    multas = []
    datos = {"patente": "NO DETECTADA", "rut": "NO DETECTADO", "nombre": "PROPIETARIO"}
    try:
        with pdfplumber.open(archivo) as pdf:
            texto_completo = ""
            for page in pdf.pages: texto_completo += page.extract_text() + "\n"
        
        # Filtro: Validar que sea un certificado real
        if "REGISTRO DE MULTAS" not in texto_completo and "TRANSITO NO PAGADAS" not in texto_completo:
            return None, None

        # Extracción de Datos
        match_patente = re.search(r'PATENTE UNICA\s+([A-Z0-9\.\-]+)', texto_completo)
        if match_patente: datos['patente'] = limpiar_texto(match_patente.group(1))
        match_rut = re.search(r'R\.U\.N\.\s*:\s*([\d\.\-Kk]+)', texto_completo)
        if match_rut: datos['rut'] = limpiar_texto(match_rut.group(1))
        match_nombre = re.search(r'Nombre\s*:\s*(.+)', texto_completo)
        if match_nombre: datos['nombre'] = limpiar_texto(match_nombre.group(1).split("\n")[0])

        # Extracción de Multas
        bloques = texto_completo.split("ID MULTA")
        for bloque in bloques:
            if "TRIBUNAL" in bloque:
                juzgado_match = re.search(r'TRIBUNAL\s*:\s*(.+)', bloque)
                rol_match = re.search(r'(?<!AÑO )ROL\s*:\s*([\w\-\.]+)', bloque)
                anio_match = re.search(r'AÑO ROL\s*:\s*(\d{4})', bloque)
                fecha_ingreso_match = re.search(r'FECHA INGRESO RMNP\s*:\s*([\d\-\s:]+)', bloque)
                
                if juzgado_match and rol_match and fecha_ingreso_match:
                    rol_final = rol_match.group(1).strip()
                    if anio_match: rol_final += f"-{anio_match.group(1)}"
                    fecha_ingreso = fecha_ingreso_match.group(1).strip()
                    
                    if es_prescribible(fecha_ingreso):
                        multas.append({
                            "juzgado": juzgado_match.group(1).strip(),
                            "rol": rol_final,
                            "fecha_ingreso": fecha_ingreso.split(" ")[0]
                        })
        return datos, multas
    except: return None, None

def generar_zip(datos, multas):
    multas_por_juzgado = {}
    for m in multas:
        jz = m['juzgado']
        if jz not in multas_por_juzgado: multas_por_juzgado[jz] = []
        multas_por_juzgado[jz].append(m)
    
    memoria_zip = BytesIO()
    with zipfile.ZipFile(memoria_zip, 'w') as zf:
        for juzgado, lista_multas in multas_por_juzgado.items():
            doc = Document()
            # Redacción del Word
            doc.add_heading('SOLICITUD DE PRESCRIPCIÓN', 0).alignment = 1
            doc.add_paragraph(f"JUZGADO: {juzgado}").bold = True
            doc.add_paragraph(f"PATENTE: {datos['patente']}")
            p = doc.add_paragraph()
            p.add_run("EN LO PRINCIPAL: SOLICITA PRESCRIPCIÓN.\nS.J.L.\n\n").bold = True
            p.add_run(f"Yo, {datos['nombre']}, R.U.N {datos['rut']}, propietario del vehículo patente {datos['patente']}, solicito declarar la prescripción (Art. 24 Ley 18.287) de las siguientes anotaciones por tener más de 3 años de antigüedad:")
            
            table = doc.add_table(rows=1, cols=2)
            table.style = 'Table Grid'
            hdr = table.rows[0].cells; hdr[0].text = 'ROL CAUSA'; hdr[1].text = 'FECHA INGRESO RMNP'
            for m in lista_multas:
                row = table.add_row().cells
                row[0].text = str(m['rol']); row[1].text = str(m['fecha_ingreso'])
            
            doc.add_paragraph("\nPOR TANTO, Ruego a US. acceder a lo solicitado.\n\n___________________________\nFIRMA PROPIETARIO")
            doc.add_paragraph(f"{datos['nombre']}\nR.U.N: {datos['rut']}")
            doc_io = BytesIO(); doc.save(doc_io); doc_io.seek(0)
            zf.writestr(f"Escrito_{juzgado[:10]}_{datos['patente']}.docx", doc_io.getvalue())
        zf.writestr("INSTRUCCIONES.txt", "1. Imprime 3 copias.\n2. Firma.\n3. Lleva al Juzgado.")
    memoria_zip.seek(0)
    return memoria_zip

# --- FRONTEND ---

st.markdown("""
<div class="hero">
    <h1>⚖️ BorraTusMultas.cl</h1>
    <p>La forma más inteligente de limpiar tu historial para el 2026</p>
</div>
""", unsafe_allow_html=True)

# COLUMNAS DE ACCIÓN
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("""
    <div class="instruction-box">
        <div class="step-badge">Paso 1</div>
        <h3>Consigue el Certificado Oficial</h3>
        <p style="color:#64748b; font-size:0.9rem;">
            Compra el "Certificado de Multas de Tránsito no Pagadas" ($1.310). 
            Sin este documento oficial no podemos redactar el escrito.
        </p>
        <a href="https://www.registrocivil.cl/principal/servicios-en-linea" target="_blank" class="btn-registrocivil">
            🏛️ Ir a RegistroCivil.cl
        </a>
        <div style="margin-top:10px; font-size:0.8rem; color:#94a3b8;">(Se abrirá en nueva pestaña)</div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown("""
    <div class="instruction-box">
        <div class="step-badge">Paso 2</div>
        <h3>Sube el PDF y Ahorra</h3>
        <p style="color:#64748b; font-size:0.9rem;">
            Nuestra IA analizará las fechas exactas y generará los escritos legales para borrar las multas antiguas.
        </p>
        <div style="margin-top:20px; font-weight:bold; color:#3b82f6;">👇 Carga tu archivo abajo</div>
    </div>
    """, unsafe_allow_html=True)

# ZONA UPLOAD
uploaded_file = st.file_uploader("", type="pdf")

if uploaded_file:
    with st.spinner('Analizando prescripciones...'):
        datos, multas = procesar_pdf(uploaded_file)
    
    if datos is None:
        st.error("⚠️ El archivo subido no es válido. Asegúrate de que sea el Certificado de Multas original.")
    
    elif multas:
        # ÉXITO
        ahorro = len(multas) * 65000
        st.markdown(f"""
        <div class="success-box">
            <h2 style="color:#0f172a; margin:0;">¡ENCONTRAMOS {len(multas)} MULTAS BORRABLES!</h2>
            <p style="font-size:1.1rem; margin-top:5px;">Vehículo: <b>{datos['patente']}</b></p>
            <div class="money-tag">${ahorro:,.0f}</div>
            <p style="font-weight:bold; color:#15803d;">AHORRO POTENCIAL DETECTADO</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("✅ Documentos legales generados con éxito.")

        # PAGO Y DESCARGA
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.write(" ")
            # LINK MERCADO PAGO
            st.markdown(f'<a href="{LINK_MERCADO_PAGO}" target="_blank" class="pay-btn">DESCARGAR PACK LEGAL<br><span style="font-size:1rem; font-weight:normal">${PRECIO_SERVICIO:,.0f}</span></a>', unsafe_allow_html=True)
            st.caption("Pago único. Incluye todos los escritos necesarios.")
        
        with c2:
            st.write(" ")
            clave = st.text_input("Ingresa tu clave de pago:", placeholder=f"Ej: {CLAVE_ACCESO}")
            if clave == CLAVE_ACCESO:
                zip_buffer = generar_zip(datos, multas)
                st.balloons()
                st.download_button("📥 DESCARGAR ARCHIVOS", zip_buffer, f"Pack_{datos['patente']}.zip", "application/zip")
            elif clave:
                st.error("Clave incorrecta.")
                
    else:
        # FALLO
        st.warning(f"Analizamos el certificado de {datos['nombre']}, pero todas las multas tienen menos de 3 años. No se pueden borrar aún.")
        st.info("No te cobraremos nada por este análisis.")

st.markdown("<div style='text-align:center; margin-top:50px; color:#cbd5e1; font-size:0.8rem;'>BorraTusMultas.cl - 2026</div>", unsafe_allow_html=True)
