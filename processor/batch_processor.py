"""
BatchProcessor – Batch-Verarbeitung mehrerer Audio-Dateien.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Verarbeitet mehrere Audio-Dateien automatisch."""

    def __init__(self, transcriber, protocol_generator):
        """
        Args:
            transcriber: AudioTranscriber Instanz
            protocol_generator: ProtocolGenerator Instanz
        """
        self.transcriber = transcriber
        self.protocol_generator = protocol_generator

    def process_batch(
        self,
        audio_files: List[str],
        gremium: str = "Gemeinderat",
        sitzung_nr_prefix: str = "",
        known_speakers: Optional[List[str]] = None,
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """
        Verarbeitet mehrere Audio-Dateien als Batch.

        Args:
            audio_files: Liste von Dateipfaden
            gremium: Name des Gremiums
            sitzung_nr_prefix: Praefix fuer Sitzungsnummern
            known_speakers: Bekannte Sprecher
            progress_callback: Funktion(fortschritt, gesamt, dateiname)

        Returns:
            Liste von Ergebnis-Dicts
        """
        results = []
        total = len(audio_files)

        logger.info(f"Starte Batch-Verarbeitung: {total} Dateien")

        for i, audio_path in enumerate(audio_files, 1):
            filename = os.path.basename(audio_path)

            if progress_callback:
                progress_callback(i, total, filename)

            try:
                # Transkribieren
                transcript = self.transcriber.transcribe(
                    audio_path=audio_path,
                    known_speakers=known_speakers,
                    language="de"
                )

                # Protokoll generieren
                sitzung_nr = f"{sitzung_nr_prefix}{i}" if sitzung_nr_prefix else str(i)
                protocol = self.protocol_generator.generate(
                    transcript=transcript.get("text", ""),
                    gremium=gremium,
                    sitzung_nr=sitzung_nr,
                    datum=datetime.now().strftime("%d.%m.%Y"),
                    uhrzeit="",
                    ort="",
                    sprecher_liste=known_speakers or [],
                    behoerdenname=""
                )

                results.append({
                    "filename": filename,
                    "audio_path": audio_path,
                    "transcript": transcript,
                    "protocol": protocol,
                    "status": "erfolgreich",
                    "error": None
                })

                # Audio-Datei loeschen (DSGVO)
                try:
                    os.remove(audio_path)
                except OSError:
                    pass

            except Exception as e:
                logger.error(f"Fehler bei {filename}: {e}")
                results.append({
                    "filename": filename,
                    "audio_path": audio_path,
                    "transcript": None,
                    "protocol": None,
                    "status": "fehler",
                    "error": str(e)
                })

        logger.info(f"Batch abgeschlossen: {len(results)} verarbeitet")
        return results
