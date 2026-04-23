"""
Processor-Modul für Sitzungsprotokoll-KI.
"""
from .transcriber import AudioTranscriber
from .protocol_generator import ProtocolGenerator
from .document_exporter import DocumentExporter

__all__ = ["AudioTranscriber", "ProtocolGenerator", "DocumentExporter"]
