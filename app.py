import streamlit as st
import json
import os
from datetime import datetime

DB_FILE = 'habitaciones.json'
EVIDENCIAS_DIR = 'evidencias'

# Crea i dati iniziali automaticamente se il file non esiste
def inicializar_db():
    if not os.path.exists(DB_FILE):
        datos_iniciales = {
            "habitaciones": [
                {"numero": "101", "estado": "da_fare", "detalles": {}},
                {"numero": "102", "estado": "da_fare", "detalles": {}},
                {"numero": "105", "estado": "da_fare", "detalles": {}},
                {"numero": "210", "estado": "da_fare", "detalles": {}}
            ]
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(datos_iniciales, f, indent=4, ensure_ascii=False)

def cargar_datos():
    inicializar_db()
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_datos(datos):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# Configurazione della pagina
st.set_page_config(page_title="Courmayeur Couverture", layout="centered")

# CSS per bottoni grandi stile app mobile
st.markdown("""
<style>
    div.stButton > button {
        height: 75px;
        font-size: 18px !important;
        border-radius: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Controllo della navigazione tra Schermata 1 (Tabellone) e Schermata 2 (Menu camera)
if 'hab_activa' not in st.session_state:
    st.session_state.hab_activa = None

datos = cargar_datos()
habitaciones = datos['habitaciones']

# ==============================================================================
# SCHERMATA 1: TABELLONE DELLE CAMERE (Solo bottoni delle camere)
# ==============================================================================
if st.session_state.hab_activa is None:
    st.title("🛏️ Controllo Couverture — Turno Serale")
    
    # Barra di avanzamento rapido
    total = len(habitaciones)
    hechas = sum(1 for h in habitaciones if h['estado'] not in ['da_fare', 'pendiente'])
    st.progress(hechas / total if total > 0 else 0, text=f"Avanzamento: {hechas} di {total} camere controllate")
    
    st.write("Seleziona una camera:")

    # Mostra le camere in una griglia a 2 colonne (ideale per cellulare)
    cols = st.columns(2)
    for idx, hab in enumerate(habitaciones):
        numero = hab['numero']
        estado = hab['estado']
        
        if estado in ['da_fare', 'pendiente']:
            etiqueta = f"⚪ Cam. {numero}  \nDa fare"
        elif estado in ['Consegnato', 'Completata']:
            etiqueta = f"🟢 Cam. {numero}  \n{estado}"
        else:
            etiqueta = f"🔴 Cam. {numero}  \n{estado}"

        with cols[idx % 2]:
            if st.button(etiqueta, key=f"card_{numero}", use_container_width=True):
                st.session_state.hab_activa = numero
                st.rerun()

    # Pulsante rapido per azzerare durante la dimostrazione ai manager
    st.divider()
    if st.button("🔄 Azzera turno (Reset Demo)", use_container_width=True):
        for h in datos['habitaciones']:
            h['estado'] = 'da_fare'
            h['detalles'] = {}
        guardar_datos(datos)
        st.rerun()

# ==============================================================================
# SCHERMATA 2: MENU ESCLUSIVO DELLA CAMERA SELEZIONATA
# ==============================================================================
else:
    num_actual = st.session_state.hab_activa
    idx = next(i for i, h in enumerate(habitaciones) if h['numero'] == num_actual)
    hab = habitaciones[idx]
    estado = hab['estado']
    detalles = hab['detalles']

    # Bottone superiore per tornare al tabellone senza modifiche
    if st.button("⬅️ Torna alle camere"):
        st.session_state.hab_activa = None
        st.rerun()

    st.title(f"Camera {num_actual}")

    # --- SE LA CAMERA È DA FARE: MOSTRA IL MENU DELLE AZIONI ---
    if estado in ['da_fare', 'pendiente']:
        opcion = st.radio(
            "Quale situazione hai trovato?",
            [
                "👤 L'ospite è in camera e risponde",
                "🚪 L'ospite NON è in camera (Eseguire couverture)",
                "🛑 Cartello 'Non Disturbare'",
                "🔇 In camera senza cartello (Nessuna risposta)"
            ]
        )

        st.divider()

        # OPZIONE 1: CONSEGNATO ALL'OSPITE
        if opcion == "👤 L'ospite è in camera e risponde":
            col1, col2 = st.columns(2)
            with col1:
                agua = st.number_input("💧 Bottiglie d'acqua", min_value=0, max_value=6, value=0)
            with col2:
                cafe = st.number_input("☕ Capsule caffè", min_value=0, max_value=6, value=0)

            st.write("**Biancheria e asciugamani consegnati:**")
            c1, c2 = st.columns(2)
            with c1:
                t_toallon = st.checkbox("Telo bagno")
                t_mano = st.checkbox("Asciugamano viso")
                t_bidet = st.checkbox("Asciugamano bidet")
            with c2:
                t_scendi = st.checkbox("Scendibagno")
                t_bata = st.checkbox("Accappatoio")

            st.write("")
            note_extra = st.text_input(
                "📝 Altre richieste / Note (opzionale)",
                placeholder="Es. cuscino extra..."
            )

            st.write("")
            if st.button("✅ Salva e segna in verde", type="primary", use_container_width=True):
                datos['habitaciones'][idx]['estado'] = 'Consegnato'
                datos['habitaciones'][idx]['detalles'] = {
                    "tipo": "atendido",
                    "agua": agua,
                    "cafe": cafe,
                    "toallas": {
                        "Telo bagno": t_toallon,
                        "Asciugamano viso": t_mano,
                        "Asciugamano bidet": t_bidet,
                        "Scendibagno": t_scendi,
                        "Accappatoio": t_bata
                    },
                    "note": note_extra.strip(),
                    "hora": datetime.now().strftime("%H:%M")
                }
                guardar_datos(datos)
                st.session_state.hab_activa = None
                st.rerun()

        # OPZIONE 2: OSPITE ASSENTE (COUVERTURE COMPLETA)
        elif opcion == "🚪 L'ospite NON è in camera (Eseguire couverture)":
            st.info("Verrà registrata la couverture completa: letto preparato per la notte, tende chiuse, cestini svuotati, tazze/bicchieri puliti e rifornimento acqua.")
            if st.button("✅ Conferma couverture completata", type="primary", use_container_width=True):
                datos['habitaciones'][idx]['estado'] = 'Completata'
                datos['habitaciones'][idx]['detalles'] = {
                    "tipo": "ausente_realizado",
                    "hora": datetime.now().strftime("%H:%M")
                }
                guardar_datos(datos)
                st.session_state.hab_activa = None
                st.rerun()

        # OPZIONE 3: NON DISTURBARE (DND)
        elif opcion == "🛑 Cartello 'Non Disturbare'":
            st.warning("Scatta una foto della porta con il cartello come prova.")
            foto = st.camera_input("Fotocamera")
            if foto is not None:
                if st.button("✅ Salva cartello e foto", type="primary", use_container_width=True):
                    os.makedirs(EVIDENCIAS_DIR, exist_ok=True)
                    ruta_foto = os.path.join(EVIDENCIAS_DIR, f"cam_{num_actual}_{datetime.now().strftime('%H%M%S')}.jpg")
                    with open(ruta_foto, "wb") as f:
                        f.write(foto.getbuffer())

                    datos['habitaciones'][idx]['estado'] = 'Non Disturbare'
                    datos['habitaciones'][idx]['detalles'] = {
                        "tipo": "do_not_disturb",
                        "hora": datetime.now().strftime("%H:%M"),
                        "ruta_foto": ruta_foto
                    }
                    guardar_datos(datos)
                    st.session_state.hab_activa = None
                    st.rerun()

        # OPZIONE 4: NESSUNA RISPOSTA
        elif opcion == "🔇 In camera senza cartello (Nessuna risposta)":
            st.info("Verrà registrato l'orario esatto in cui si è bussato alla porta senza ricevere risposta.")
            if st.button("✅ Registra nessuna risposta", type="primary", use_container_width=True):
                datos['habitaciones'][idx]['estado'] = 'Nessuna risposta'
                datos['habitaciones'][idx]['detalles'] = {
                    "tipo": "intento_fallido",
                    "hora": datetime.now().strftime("%H:%M")
                }
                guardar_datos(datos)
                st.session_state.hab_activa = None
                st.rerun()

    # --- SE LA CAMERA È GIÀ STATA COMPLETATA: MOSTRA IL RIEPILOGO ---
    else:
        hora = detalles.get('hora', '--:--')
        tipo = detalles.get('tipo')

        if estado in ['Consegnato', 'Completata']:
            st.success(f"🟢 Couverture completata alle **{hora}** ({estado})")
        else:
            st.error(f"🔴 Registrato come **{estado}** alle **{hora}**")

        st.subheader("Dettagli registrati:")
        if tipo == "atendido":
            st.write(f"- **💧 Acqua consegnata:** {detalles.get('agua', 0)}")
            st.write(f"- **☕ Caffè consegnato:** {detalles.get('cafe', 0)}")
            toallas = [k for k, v in detalles.get('toallas', {}).items() if v]
            st.write(f"- **🛁 Biancheria:** {', '.join(toallas) if toallas else 'Nessuna'}")
            if detalles.get('note'):
                st.write(f"- **📝 Note / Extra:** {detalles.get('note')}")
        elif tipo == "ausente_realizado":
            st.write("- **✅ Servizio completo:** Letto preparato per la notte, tende chiuse, cestini svuotati, bicchieri/tazze puliti e acqua rifornita.")
        elif tipo == "do_not_disturb":
            st.write("- **🛑 Motivo:** Cartello *Non Disturbare (DND)* sulla porta.")
            ruta_foto = detalles.get('ruta_foto')
            if ruta_foto and os.path.exists(ruta_foto):
                st.image(ruta_foto, caption=f"Prova Cam. {num_actual} ({hora})")
        elif tipo == "intento_fallido":
            st.write("- **🔇 Motivo:** Ospite in camera senza cartello; nessuna risposta dopo aver bussato.")

        st.divider()
        if st.button("↩️ Annulla registrazione e riporta 'Da fare'", use_container_width=True):
            datos['habitaciones'][idx]['estado'] = 'da_fare'
            datos['habitaciones'][idx]['detalles'] = {}
            guardar_datos(datos)
            st.session_state.hab_activa = None
            st.rerun()