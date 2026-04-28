"""
Sitzungsprotokoll-KI - Streamlit Web-App
Automatische Transkription und Protokollgenerierung fuer Behoerdensitzungen.
"""

import streamlit as st
import os
import uuid
import tempfile
from datetime import datetime
from pathlib import Path

# -- Unified Theme System --
import sys, os as _theme_os
sys.path.insert(0, _theme_os.path.dirname(_theme_os.path.abspath(__file__)))
from theme import init_theme, theme_toggle_sidebar, app_footer

from processor.transcriber import AudioTranscriber
from processor.protocol_generator import ProtocolGenerator
from processor.document_exporter import DocumentExporter
from processor.batch_processor import BatchProcessor
from processor.protocol_search import ProtocolSearch
from processor.task_tracker import TaskTracker

# Seitenkonfiguration
st.set_page_config(
    page_title="Sitzungsprotokoll-KI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_theme()

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
    .priority-high { color: #ef4444; font-weight: bold; }
    .priority-medium { color: #eab308; font-weight: bold; }
    .priority-low { color: #22c55e; font-weight: bold; }
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
    """Initialisiert den Audio-Transcriber."""
    model_size = os.environ.get("WHISPER_MODEL", "small")
    device = os.environ.get("WHISPER_DEVICE", "cpu")
    compute_type = "float32" if device == "cpu" else "float16"
    return AudioTranscriber(model_size=model_size, device=device, compute_type=compute_type)

@st.cache_resource
def init_protocol_generator():
    return ProtocolGenerator()

@st.cache_resource
def init_exporter():
    return DocumentExporter()

@st.cache_resource
def init_search():
    return ProtocolSearch()

@st.cache_resource
def init_task_tracker():
    return TaskTracker()


def cleanup_audio(file_path):
    """Loescht die Audio-Datei nach der Verarbeitung (DSGVO)."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            st.sidebar.success("Audio-Datei geloescht (DSGVO)")
    except OSError as e:
        st.sidebar.error(f"Fehler beim Loeschen: {e}")


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

    st.subheader("Sitzung")
    gremium = st.text_input("Gremium", value="Gemeinderat")
    sitzung_nr = st.text_input("Sitzungsnr.", value="42")
    datum = st.date_input("Datum")
    uhrzeit = st.time_input("Beginn", value=datetime.strptime("18:00", "%H:%M").time())
    ort = st.text_input("Ort", value="Rathaus Musterhausen, Ratssaal")

    st.divider()

    st.subheader("Bekannte Sprecher")
    st.caption("Tragen Sie bekannte Sprecher ein zur Verbesserung der Erkennung.")
    num_speaker = st.number_input("Anzahl Sprecher", min_value=0, max_value=20, value=3)
    sprecher = []
    for i in range(num_speaker):
        name = st.text_input(f"Sprecher {i+1}", key=f"sprecher_{i}")
        if name:
            sprecher.append(name)

    st.divider()

    st.subheader("Export")
    wappen_pfad = st.text_input("Wappen (Pfad)", value="", placeholder="/pfad/zum/wappen.png")
    behoerdenname = st.text_input("Behoerde", value="Stadt Musterhausen")

    st.divider()
    st.caption(f"Anfrage-ID: {st.session_state.anfrage_id[:8]}")

# ─────────────────────────────────────────────
# HAUPTBEREICH
# ─────────────────────────────────────────────

tab_upload, tab_transkript, tab_protokoll, tab_export, tab_batch, tab_suche, tab_aufgaben = st.tabs([
    "🎙️ Upload", "📝 Transkript", "📋 Protokoll", "📄 Export",
    "📦 Batch", "🔍 Suche", "📌 Aufgaben"
])

# ─────────────────────────────────────────────
# TAB 1: AUDIO-UPLOAD
# ─────────────────────────────────────────────
with tab_upload:
    st.markdown("""
    ### Audio-Datei hochladen
    Laden Sie die Audio-Aufnahme der Sitzung hoch. Unterstuetzte Formate: MP3, WAV, M4A, OGG, FLAC

    ⚠️ **Datenschutz:** Die Audio-Datei wird nach der Verarbeitung automatisch geloescht.
    """)

    uploaded_file = st.file_uploader(
        "Audio-Datei auswaehlen",
        type=["mp3", "wav", "m4a", "ogg", "flac", "mp4"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Dateiname", uploaded_file.name)
        with col2:
            st.metric("Groesse", f"{uploaded_file.size / 1024 / 1024:.1f} MB")
        with col3:
            st.metric("Typ", uploaded_file.type)

        if st.button("🎙️ Transkription starten", type="primary", use_container_width=True):
            with st.spinner("Audio wird verarbeitet..."):
                try:
                    with tempfile.NamedTemporaryFile(
                        suffix=Path(uploaded_file.name).suffix,
                        delete=False
                    ) as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name

                    transcriber = init_transcriber()
                    result = transcriber.transcribe(
                        audio_path=tmp_path,
                        known_speakers=sprecher,
                        language="de"
                    )
                    st.session_state.transcript = result
                    cleanup_audio(tmp_path)
                    st.success("Transkription abgeschlossen!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler bei der Transkription: {e}")
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
        edited_text = st.text_area(
            "Transkript",
            value=st.session_state.transcript.get("text", ""),
            height=400,
            label_visibility="collapsed"
        )
        if edited_text != st.session_state.transcript.get("text", ""):
            st.session_state.transcript["text"] = edited_text

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Dauer", st.session_state.transcript.get("duration", "0:00"))
        with col2:
            st.metric("Woerter", len(edited_text.split()))
        with col3:
            st.metric("Sprecher", st.session_state.transcript.get("num_speakers", 0))

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
                    st.error(f"Fehler: {e}")

# ─────────────────────────────────────────────
# TAB 3: PROTOKOLL
# ─────────────────────────────────────────────
with tab_protokoll:
    if st.session_state.protocol is None:
        st.info("Noch kein Protokoll vorhanden.")
    else:
        st.subheader("Sitzungsprotokoll – Vorschau")
        st.markdown(f"### {st.session_state.protocol.get('titel', 'Sitzungsprotokoll')}")
        st.caption(f"{st.session_state.protocol.get('datum', '')} | {st.session_state.protocol.get('ort', '')}")
        st.divider()
        st.markdown(st.session_state.protocol.get("html", "Kein Inhalt"))

        beschluesse = st.session_state.protocol.get("beschluesse", [])
        if beschluesse:
            st.divider()
            st.subheader("Beschluesse")
            for b in beschluesse:
                with st.expander(f"Beschluss {b.get('nummer', '?')}: {b.get('text', '')[:60]}..."):
                    st.write(b.get("text", ""))
                    st.write(f"**Abstimmung:** {b.get('abstimmung', 'Keine Angabe')}")

        # Aufgaben automatisch extrahieren
        if st.button("📌 Aufgaben aus Beschluesen erstellen", use_container_width=True):
            tracker = init_task_tracker()
            created = tracker.extract_tasks_from_protocol(
                protocol=st.session_state.protocol
            )
            if created:
                st.success(f"{len(created)} Aufgaben erstellt!")
            else:
                st.info("Keine Aufgaben identifiziert.")

        # Protokoll in Suchindex speichern
        if st.button("💾 In Archiv speichern", use_container_width=True):
            search = init_search()
            search.save_protocol(
                protocol=st.session_state.protocol,
                transcript=st.session_state.transcript.get("text", "")
            )
            st.success("Protokoll im Archiv gespeichert!")

# ─────────────────────────────────────────────
# TAB 4: EXPORT
# ─────────────────────────────────────────────
with tab_export:
    if st.session_state.protocol is None:
        st.info("Generieren Sie zuerst ein Protokoll.")
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

# ─────────────────────────────────────────────
# TAB 5: BATCH-VERARBEITUNG
# ─────────────────────────────────────────────
with tab_batch:
    st.subheader("📦 Batch-Verarbeitung")
    st.markdown("""
    Verarbeiten Sie mehrere Audio-Dateien automatisch. Ideal fuer Sitzungsreihen
    oder nachgeholte Protokolle.
    """)

    batch_files = st.file_uploader(
        "Mehrere Audio-Dateien auswaehlen",
        type=["mp3", "wav", "m4a", "ogg", "flac"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if batch_files:
        st.info(f"{len(batch_files)} Dateien ausgewaehlt")

        col1, col2 = st.columns(2)
        with col1:
            batch_gremium = st.text_input("Gremium fuer Batch", value=gremium)
        with col2:
            batch_prefix = st.text_input("Sitzungsnr.-Praefix", value="")

        if st.button("🚀 Batch starten", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                transcriber = init_transcriber()
                generator = init_protocol_generator()
                batch = BatchProcessor(transcriber, generator)

                # Temporaere Dateien speichern
                temp_paths = []
                for f in batch_files:
                    with tempfile.NamedTemporaryFile(
                        suffix=Path(f.name).suffix, delete=False
                    ) as tmp:
                        tmp.write(f.read())
                        temp_paths.append(tmp.name)

                # Batch verarbeiten
                results = batch.process_batch(
                    audio_files=temp_paths,
                    gremium=batch_gremium,
                    sitzung_nr_prefix=batch_prefix,
                    known_speakers=sprecher,
                    progress_callback=lambda i, t, n: (
                        progress_bar.progress(i / t),
                        status_text.text(f"Verarbeite {i}/{t}: {n}")
                    )
                )

                progress_bar.progress(1.0)
                status_text.text("Batch abgeschlossen!")

                # Ergebnisse anzeigen
                st.divider()
                st.subheader("Ergebnisse")
                for r in results:
                    if r["status"] == "erfolgreich":
                        st.markdown(f"✅ **{r['filename']}** — Transkription OK")
                    else:
                        st.markdown(f"❌ **{r['filename']}** — {r['error']}")

            except Exception as e:
                st.error(f"Batch-Fehler: {e}")

    else:
        st.markdown("""
        <div class="upload-section">
            <p style="font-size: 48px;">📁</p>
            <p>Klicken oder ziehen Sie mehrere Audio-Dateien hierher</p>
            <p style="color: #888;">MP3 · WAV · M4A · OGG · FLAC</p>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 6: PROTOKOLL-SUCHE
# ─────────────────────────────────────────────
with tab_suche:
    st.subheader("🔍 Protokoll-Archiv durchsuchen")
    st.markdown("Volltextsuche ueber alle gespeicherten Protokolle.")

    search = init_search()

    col1, col2, col3 = st.columns(3)
    with col1:
        search_query = st.text_input("Suchbegriff", placeholder="z.B. Strassenbau, Haushalt...")
    with col2:
        gremien = search.get_all_gremien()
        filter_gremium = st.selectbox("Gremium", ["Alle"] + gremien) if gremien else "Alle"
    with col3:
        st.markdown("")

    if search_query:
        results = search.search(
            query=search_query,
            gremium=filter_gremium if filter_gremium != "Alle" else None
        )

        st.metric("Treffer", len(results))

        if results:
            for r in results:
                with st.expander(
                    f"📋 {r['gremium']} — Sitzung {r['sitzung_nr']} ({r['datum']})"
                ):
                    st.write(r["transcript"] or "Kein Text verfuegbar")
                    if r["beschluesse"]:
                        st.markdown("**Beschluesse:**")
                        for b in r["beschluesse"]:
                            st.write(f"- {b.get('text', '')[:100]}")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Anzeigen", key=f"show_{r['id']}"):
                            protocol = search.get_protocol(r["id"])
                            if protocol and protocol.get("protocol"):
                                st.session_state.protocol = protocol["protocol"]
                                st.info("Protokoll geladen — wechseln Sie zum Tab 'Protokoll'")
                    with col_b:
                        if st.button("Loeschen", key=f"del_{r['id']}"):
                            search.delete_protocol(r["id"])
                            st.success("Protokoll geloescht!")
                            st.rerun()
        else:
            st.info("Keine Treffer gefunden.")
    else:
        # Letzte Protokolle anzeigen
        all_results = search.search(query=None, limit=10)
        if all_results:
            st.subheader("Letzte Protokolle")
            for r in all_results:
                st.markdown(f"- **{r['gremium']}** — Sitzung {r['sitzung_nr']} ({r['datum']})")
        else:
            st.info("Noch keine Protokolle gespeichert. Generieren und speichern Sie ein Protokoll im Tab 'Protokoll'.")

# ─────────────────────────────────────────────
# TAB 7: WIEDERVORLAGE / AUFGABEN
# ─────────────────────────────────────────────
with tab_aufgaben:
    st.subheader("📌 Wiedervorlage und Aufgabenverfolgung")

    tracker = init_task_tracker()
    stats = tracker.get_statistics()

    # Statistiken
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Offen", stats["offen"])
    col2.metric("In Bearbeitung", stats["in_bearbeitung"])
    col3.metric("Erledigt", stats["erledigt"])
    col4.metric("Ueberfaellig", stats["ueberfaellig"])

    st.divider()

    # Neue Aufgabe manuell erstellen
    with st.expander("➕ Neue Aufgabe erstellen"):
        col1, col2 = st.columns(2)
        with col1:
            new_titel = st.text_input("Titel", key="new_task_titel")
            new_zustaendig = st.text_input("Zustaendig", key="new_task_zustaendig")
        with col2:
            new_faelligkeit = st.text_input("Faelligkeit (DD.MM.YYYY)", key="new_task_faellig")
            new_prioritaet = st.selectbox("Prioritaet", ["hoch", "mittel", "niedrig"], key="new_task_prio")
        new_beschreibung = st.text_area("Beschreibung", key="new_task_desc")

        if st.button("Aufgabe erstellen"):
            if new_titel:
                tracker.add_task(
                    titel=new_titel,
                    beschreibung=new_beschreibung,
                    zustaendig=new_zustaendig,
                    faelligkeit=new_faelligkeit or None,
                    prioritaet=new_prioritaet,
                    gremium=gremium
                )
                st.success("Aufgabe erstellt!")
                st.rerun()
            else:
                st.warning("Bitte geben Sie einen Titel ein.")

    # Filter
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.selectbox("Status", ["Alle", "offen", "in_bearbeitung", "erledigt"])
    with col2:
        filter_prio = st.selectbox("Prioritaet", ["Alle", "hoch", "mittel", "niedrig"])
    with col3:
        show_ueberfaellig = st.checkbox("Nur ueberfaellig")

    # Aufgaben laden
    tasks = tracker.get_tasks(
        status=filter_status if filter_status != "Alle" else None,
        prioritaet=filter_prio if filter_prio != "Alle" else None,
        ueberfaellig=show_ueberfaellig
    )

    st.markdown(f"**{len(tasks)} Aufgaben**")

    for task in tasks:
        prio_emoji = "🔴" if task["prioritaet"] == "hoch" else ("🟡" if task["prioritaet"] == "mittel" else "🟢")
        status_emoji = "⬜" if task["status"] == "offen" else ("🔄" if task["status"] == "in_bearbeitung" else "✅")

        with st.expander(f"{prio_emoji} {status_emoji} **{task['titel']}** — Faellig: {task['faelligkeit']}"):
            st.write(f"**Zustaendig:** {task['zustaendig'] or 'Nicht zugewiesen'}")
            st.write(f"**Gremium:** {task['gremium'] or '—'}")
            st.write(f"**Erstellt:** {task['datum']}")

            if task["beschreibung"]:
                st.write(task["beschreibung"])
            if task["notizen"]:
                st.write(f"📝 *{task['notizen']}*")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("In Bearbeitung", key=f"ib_{task['id']}"):
                    tracker.update_task(task["id"], status="in_bearbeitung")
                    st.rerun()
            with col2:
                if st.button("Erledigt", key=f"done_{task['id']}"):
                    tracker.update_task(task["id"], status="erledigt")
                    st.rerun()
            with col3:
                if st.button("Loeschen", key=f"del_{task['id']}"):
                    tracker.update_task(task["id"], status="erledigt")
                    st.rerun()

# -- Theme Toggle --
theme_toggle_sidebar()

# -- Footer --
app_footer()
