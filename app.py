"""
Sitzungsprotokoll-KI – Streamlit Web-App
Automatische Transkription und Protokollgenerierung für Behördensitzungen.
"""

import streamlit as st
import os
import uuid
import tempfile
from datetime import datetime
from pathlib import Path

from processor.transcriber import AudioTranscriber
from processor.protocol_generator import ProtocolGenerator
from processor.document_exporter import DocumentExporter

# Seitenkonfiguration
st.set_page_config(
    page_title="Sitzungsprotokoll-KI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Benutzerdefiniertes CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px 0;
    }
    .privacy-badge {
        display: inline-block;
        background: #22c55e;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .upload-section {
        border: 2px dashed #4a5568;
        border-radius: 10px;
        padding: 40px;
        text-align: center;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialisierung
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "protocol" not in st.session_state:
    st.session_state.protocol = None
if "anfrage_id" not in st.session_state:
    st.session_state.anfrage_id = str(uuid.uuid4())

# Initialisiere Processor
@st.cache_resource
def init_transcriber():
    """Initialisiert den Audio-Transcriber mit konfigurierbarem Modell."""
    model_size = os.environ.get("WHISPER_MODEL", "small")
    device = os.environ.get("WHISPER_DEVICE", "cpu")
    compute_type = "float32" if device == "cpu" else "float16"
    return AudioTranscriber(
        model_size=model_size,
        device=device,
        compute_type=compute_type
    )

@st.cache_resource
def init_protocol_generator():
    """Initialisiert den Protokoll-Generator."""
    return ProtocolGenerator()

@st.cache_resource
def init_exporter():
    """Initialisiert den Dokument-Exporter."""
    return DocumentExporter()


def cleanup_audio(file_path):
    """Löscht die Audio-Datei nach der Verarbeitung (DSGVO)."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            st.sidebar.success("Audio-Datei wurde gelöscht (DSGVO)")
    except OSError as e:
        st.sidebar.error(f"Fehler beim Löschen: {e}")


# ─────────────────────────────────────────────
# SEITENKOPF
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🏛️ Sitzungsprotokoll-KI</h1>
    <p>Audio-Aufnahme → Strukturiertes Protokoll</p>
    <span class="privacy-badge">🔒 100% Offline · DSGVO-Konform</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SEITENLEISTE
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("Einstellungen")

    # Sitzungsinformationen
    st.subheader("Sitzung")
    gremium = st.text_input("Gremium", value="Gemeinderat")
    sitzung_nr = st.text_input("Sitzungsnr.", value="42")
    datum = st.date_input("Datum")
    uhrzeit = st.time_input("Beginn", value=datetime.strptime("18:00", "%H:%M").time())
    ort = st.text_input("Ort", value="Rathaus Musterhausen, Ratssaal")

    st.divider()

    # Sprecher-Liste
    st.subheader("Bekannte Sprecher")
    st.caption("Tragen Sie bekannte Sprecher ein zur Verbesserung der Erkennung.")
    num_speaker = st.number_input("Anzahl Sprecher", min_value=0, max_value=20, value=3)
    sprecher = []
    for i in range(num_speaker):
        name = st.text_input(f"Sprecher {i+1}", key=f"sprecher_{i}")
        if name:
            sprecher.append(name)

    st.divider()

    # Export-Einstellungen
    st.subheader("Export")
    wappen_pfad = st.text_input("Wappen (Pfad)", value="", placeholder="/pfad/zum/wappen.png")
    behoerdenname = st.text_input("Behörde", value="Stadt Musterhausen")

    st.divider()
    st.caption(f"Anfrage-ID: {st.session_state.anfrage_id[:8]}")

# ─────────────────────────────────────────────
# HAUPTBEREICH
# ─────────────────────────────────────────────

# Tab-Navigation
tab_upload, tab_transkript, tab_protokoll, tab_export = st.tabs([
    "🎙️ Upload", "📝 Transkript", "📋 Protokoll", "📄 Export"
])

# ─────────────────────────────────────────────
# TAB 1: AUDIO-UPLOAD
# ─────────────────────────────────────────────
with tab_upload:
    st.markdown("""
    ### Audio-Datei hochladen
    Laden Sie die Audio-Aufnahme der Sitzung hoch. Unterstützte Formate: MP3, WAV, M4A, OGG, FLAC

    ⚠️ **Datenschutz:** Die Audio-Datei wird nach der Verarbeitung automatisch gelöscht.
    """)

    uploaded_file = st.file_uploader(
        "Audio-Datei auswählen",
        type=["mp3", "wav", "m4a", "ogg", "flac", "mp4"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        # Dateiinformationen anzeigen
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Dateiname", uploaded_file.name)
        with col2:
            st.metric("Größe", f"{uploaded_file.size / 1024 / 1024:.1f} MB")
        with col3:
            st.metric("Typ", uploaded_file.type)

        if st.button("🎙️ Transkription starten", type="primary", use_container_width=True):
            with st.spinner("Audio wird verarbeitet... Dies kann einige Minuten dauern."):
                try:
                    # Temporäre Datei speichern
                    with tempfile.NamedTemporaryFile(
                        suffix=Path(uploaded_file.name).suffix,
                        delete=False
                    ) as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name

                    # Transkription durchführen
                    transcriber = init_transcriber()
                    result = transcriber.transcribe(
                        audio_path=tmp_path,
                        known_speakers=sprecher,
                        language="de"
                    )

                    st.session_state.transcript = result

                    # Audio-Datei löschen (DSGVO)
                    cleanup_audio(tmp_path)

                    st.success("Transkription abgeschlossen!")
                    st.balloons()
                    st.rerun()

                except Exception as e:
                    st.error(f"Fehler bei der Transkription: {e}")
                    st.error("Bitte überprüfen Sie die Audio-Datei und versuchen Sie es erneut.")
    else:
        st.markdown("""
        <div class="upload-section">
            <p style="font-size: 48px;">📁</p>
            <p>Klicken Sie oben oder ziehen Sie eine Audio-Datei hierher</p>
            <p style="color: #888;">MP3 · WAV · M4A · OGG · FLAC</p>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 2: TRANSKRIPT
# ─────────────────────────────────────────────
with tab_transkript:
    if st.session_state.transcript is None:
        st.info("Noch kein Transkript vorhanden. Laden Sie zuerst eine Audio-Datei hoch.")
    else:
        st.subheader("Transkript bearbeiten")

        # Transkript als Textarea anzeigen
        edited_text = st.text_area(
            "Transkript",
            value=st.session_state.transcript.get("text", ""),
            height=400,
            label_visibility="collapsed"
        )

        # Aktualisieren
        if edited_text != st.session_state.transcript.get("text", ""):
            st.session_state.transcript["text"] = edited_text

        # Statistiken
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Dauer", st.session_state.transcript.get("duration", "0:00"))
        with col2:
            st.metric("Wörter", len(edited_text.split()))
        with col3:
            st.metric("Sprecher erkannt", st.session_state.transcript.get("num_speakers", 0))

        if st.button("📋 Protokoll generieren", type="primary", use_container_width=True):
            with st.spinner("Protokoll wird generiert..."):
                try:
                    generator = init_protocol_generator()
                    protocol = generator.generate(
                        transcript=edited_text,
                        gremium=gremium,
                        sitzung_nr=sitzung_nr,
                        datum=datum,
                        uhrzeit=str(uhrzeit),
                        ort=ort,
                        sprecher_liste=sprecher,
                        behoerdenname=behoerdenname
                    )
                    st.session_state.protocol = protocol
                    st.success("Protokoll generiert!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler bei der Protokollgenerierung: {e}")

# ─────────────────────────────────────────────
# TAB 3: PROTOKOLL
# ─────────────────────────────────────────────
with tab_protokoll:
    if st.session_state.protocol is None:
        st.info("Noch kein Protokoll vorhanden. Generieren Sie zuerst ein Protokoll aus dem Transkript.")
    else:
        st.subheader("Sitzungsprotokoll – Vorschau")

        # Protokoll-Header
        st.markdown(f"### {st.session_state.protocol.get('titel', 'Sitzungsprotokoll')}")
        st.caption(f"{st.session_state.protocol.get('datum', '')} | {st.session_state.protocol.get('ort', '')}")

        st.divider()

        # Protokoll-Inhalt
        st.markdown(st.session_state.protocol.get("html", "Kein Inhalt verfügbar"))

        # Beschlüsse-Übersicht
        beschluesse = st.session_state.protocol.get("beschluesse", [])
        if beschluesse:
            st.divider()
            st.subheader("Beschlüsse")
            for b in beschluesse:
                with st.expander(f"Beschluss {b.get('nummer', '?')}: {b.get('text', '')[:60]}..."):
                    st.write(b.get("text", ""))
                    st.write(f"**Abstimmung:** {b.get('abstimmung', 'Keine Angabe')}")

        # Abstimmungen
        abstimmungen = st.session_state.protocol.get("abstimmungen", [])
        if abstimmungen:
            st.divider()
            st.subheader("Abstimmungen")
            for a in abstimmungen:
                st.write(f"- {a}")

# ─────────────────────────────────────────────
# TAB 4: EXPORT
# ─────────────────────────────────────────────
with tab_export:
    if st.session_state.protocol is None:
        st.info("Generieren Sie zuerst ein Protokoll, bevor Sie es exportieren können.")
    else:
        st.subheader("Protokoll exportieren")

        col1, col2, col3 = st.columns(3)

        exporter = init_exporter()

        with col1:
            if st.button("📄 DOCX Export", use_container_width=True, type="primary"):
                try:
                    docx_bytes = exporter.export_docx(
                        protocol=st.session_state.protocol,
                        wappen_pfad=wappen_pfad if wappen_pfad else None
                    )
                    st.download_button(
                        label="DOCX herunterladen",
                        data=docx_bytes,
                        file_name=f"protokoll_{gremium}_{sitzung_nr}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"DOCX-Fehler: {e}")

        with col2:
            if st.button("📑 PDF Export", use_container_width=True):
                try:
                    pdf_bytes = exporter.export_pdf(
                        protocol=st.session_state.protocol,
                        wappen_pfad=wappen_pfad if wappen_pfad else None
                    )
                    st.download_button(
                        label="PDF herunterladen",
                        data=pdf_bytes,
                        file_name=f"protokoll_{gremium}_{sitzung_nr}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"PDF-Fehler: {e}")

        with col3:
            if st.button("🌐 HTML Export", use_container_width=True):
                try:
                    html_content = exporter.export_html(
                        protocol=st.session_state.protocol,
                        wappen_pfad=wappen_pfad if wappen_pfad else None
                    )
                    st.download_button(
                        label="HTML herunterladen",
                        data=html_content.encode("utf-8"),
                        file_name=f"protokoll_{gremium}_{sitzung_nr}.html",
                        mime="text/html"
                    )
                except Exception as e:
                    st.error(f"HTML-Fehler: {e}")
