"""
AudioTranscriber – Transkribiert Audio-Aufnahmen mit Whisper AI.
Unterstützt Sprechererkennung und verschiedene Modellgrößen.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class AudioTranscriber:
    """Transkribiert Audio-Aufnahmen mit faster-whisper und optionaler Sprechererkennung."""

    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "float32",
        model_path: Optional[str] = None
    ):
        """
        Initialisiert den Transcriber.

        Args:
            model_size: Whisper-Modellgröße (tiny, base, small, medium, large-v3)
            device: Gerät (cpu oder cuda)
            compute_type: Berechnungstyp (float32 für CPU, float16 für GPU)
            model_path: Optionaler Pfad zu einem lokalen Modell
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model_path = model_path
        self._model = None

    def _load_model(self):
        """Lädt das Whisper-Modell (lazy loading)."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                model_dir = self.model_path or os.environ.get(
                    "WHISPER_MODEL_PATH",
                    os.path.expanduser("~/.cache/huggingface/hub")
                )

                logger.info(f"Lade Whisper-Modell '{self.model_size}' auf '{self.device}'...")
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root=model_dir
                )
                logger.info("Modell erfolgreich geladen.")
            except ImportError:
                raise ImportError(
                    "faster-whisper ist nicht installiert. "
                    "Installieren Sie es mit: pip install faster-whisper"
                )
            except Exception as e:
                raise RuntimeError(f"Fehler beim Laden des Whisper-Modells: {e}")

    def transcribe(
        self,
        audio_path: str,
        language: str = "de",
        known_speakers: Optional[List[str]] = None,
        beam_size: int = 5,
        vad_filter: bool = True
    ) -> Dict[str, Any]:
        """
        Transkribiert eine Audio-Datei.

        Args:
            audio_path: Pfad zur Audio-Datei
            language: Sprache (Standard: Deutsch)
            known_speakers: Liste bekannter Sprechnamen
            beam_size: Beam-Size für die Dekodierung
            vad_filter: Voice Activity Detection aktivieren

        Returns:
            Dict mit Transkript, Zeitstempeln und Sprecher-Informationen
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio-Datei nicht gefunden: {audio_path}")

        self._load_model()

        logger.info(f"Starte Transkription: {audio_path}")

        try:
            # Transkription durchführen
            segments_iter, info = self._model.transcribe(
                audio_path,
                language=language,
                beam_size=beam_size,
                vad_filter=vad_filter,
                vad_parameters={
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 400
                }
            )

            segments = list(segments_iter)
            total_duration = info.duration

            # Segmente formatieren
            formatted_segments = []
            for seg in segments:
                formatted_segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip(),
                    "start_formatted": self._format_timestamp(seg.start),
                    "end_formatted": self._format_timestamp(seg.end)
                })

            # Sprechererkennung (optional)
            speaker_segments = []
            if known_speakers and len(known_speakers) > 0:
                speaker_segments = self._detect_speakers(
                    audio_path, formatted_segments, known_speakers
                )

            # Vollständigen Text zusammenfassen
            full_text = self._assemble_text(formatted_segments, speaker_segments)

            # Dauer formatieren
            duration_str = self._format_duration(total_duration)

            result = {
                "text": full_text,
                "segments": formatted_segments,
                "speaker_segments": speaker_segments,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": duration_str,
                "duration_seconds": total_duration,
                "num_segments": len(segments),
                "num_speakers": len(set(
                    s.get("speaker", "Unbekannt") for s in speaker_segments
                )) if speaker_segments else 0,
                "processed_at": datetime.now().isoformat()
            }

            logger.info(
                f"Transkription abgeschlossen: {len(segments)} Segmente, "
                f"{duration_str}, Sprache: {info.language} "
                f"({info.language_probability:.1%})"
            )

            return result

        except Exception as e:
            logger.error(f"Fehler bei der Transkription: {e}")
            raise RuntimeError(f"Transkription fehlgeschlagen: {e}")

    def _detect_speakers(
        self,
        audio_path: str,
        segments: List[Dict],
        known_speakers: List[str]
    ) -> List[Dict]:
        """
        Erkennt Sprecher in den Segmenten.
        Verwendet pyannote.audio für die Sprecherdiarisierung.
        """
        try:
            from pyannote.audio import Pipeline

            logger.info("Starte Sprechererkennung...")

            # pyannote Pipeline laden
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=os.environ.get("HF_TOKEN", "")
            )

            # Diarisierung durchführen
            diarization = pipeline(audio_path)

            # Sprecher-Zuordnung
            speaker_map = {}
            speaker_counter = {}
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                if speaker not in speaker_counter:
                    idx = len(speaker_counter)
                    if idx < len(known_speakers):
                        speaker_map[speaker] = known_speakers[idx]
                    else:
                        speaker_map[speaker] = f"Sprecher {idx + 1}"
                    speaker_counter[speaker] = 0
                speaker_counter[speaker] += 1

            # Segmente mit Sprecher-Informationen anreichern
            result = []
            for seg in segments:
                assigned_speaker = "Unbekannt"
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    if turn.start <= seg["start"] <= turn.end:
                        assigned_speaker = speaker_map.get(speaker, "Unbekannt")
                        break

                result.append({
                    **seg,
                    "speaker": assigned_speaker
                })

            logger.info(f"Sprechererkennung abgeschlossen: {len(speaker_map)} Sprecher erkannt")
            return result

        except ImportError:
            logger.warning("pyannote.audio nicht installiert. Sprechererkennung übersprungen.")
            return [{**s, "speaker": "Unbekannt"} for s in segments]
        except Exception as e:
            logger.warning(f"Sprechererkennung fehlgeschlagen: {e}")
            return [{**s, "speaker": "Unbekannt"} for s in segments]

    def _format_timestamp(self, seconds: float) -> str:
        """Formatiert Sekunden als HH:MM:SS."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _format_duration(self, seconds: float) -> str:
        """Formatiert Dauer als Xh Ym."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"

    def _assemble_text(
        self,
        segments: List[Dict],
        speaker_segments: List[Dict]
    ) -> str:
        """Setzt das Transkript mit Sprecher-Informationen zusammen."""
        lines = []
        for seg in speaker_segments if speaker_segments else segments:
            speaker = seg.get("speaker", "")
            text = seg.get("text", "")
            timestamp = seg.get("start_formatted", "")
            if speaker:
                lines.append(f"[{timestamp}] {speaker}: {text}")
            else:
                lines.append(f"[{timestamp}] {text}")
        return "\n".join(lines)
