#!/bin/bash
# =====================================================
# Whisper-Modell vorab herunterladen
# Wird vor dem Docker-Start ausgeführt für Offline-Betrieb
# =====================================================

set -euo pipefail

MODEL="${1:-small}"
MODEL_PATH="${HOME}/.cache/huggingface/hub"

echo "================================================"
echo "Sitzungsprotokoll-KI – Whisper Modell-Download"
echo "================================================"
echo ""
echo "Modell: ${MODEL}"
echo "Speicherort: ${MODEL_PATH}"
echo ""

# Verfügbare Modelle
case "$MODEL" in
    tiny)   SIZE="75 MB" ;;
    base)   SIZE="150 MB" ;;
    small)  SIZE="500 MB" ;;
    medium) SIZE="1.5 GB" ;;
    large-v3) SIZE="3 GB" ;;
    *)
        echo "FEHLER: Unbekanntes Modell '${MODEL}'"
        echo "Verfügbar: tiny, base, small, medium, large-v3"
        exit 1
        ;;
esac

echo "Benötigter Speicher: ca. ${SIZE}"
echo ""

# Prüfe ob Modell bereits existiert
if python3 -c "
from huggingface_hub import scan_cache_dir
for repo in scan_cache_dir().repos:
    if '${MODEL}' in repo.repo_id:
        exit(0)
exit(1)
" 2>/dev/null; then
    echo "Modell '${MODEL}' bereits heruntergeladen."
    echo "Überspringe Download."
    exit 0
fi

# Download
echo "Starte Download..."
python3 -c "
from faster_whisper import WhisperModel
print(f'Lade Modell ${MODEL}...')
model = WhisperModel('${MODEL}', download_root='${MODEL_PATH}')
print('Download abgeschlossen.')
" || {
    echo ""
    echo "FEHLER: Download fehlgeschlagen."
    echo ""
    echo "Manuelle Installation:"
    echo "  pip install faster-whisper"
    echo "  python3 -c \"from faster_whisper import WhisperModel; WhisperModel('${MODEL}')\""
    exit 1
}

echo ""
echo "================================================"
echo "Download abgeschlossen!"
echo "Modell '${MODEL}' ist jetzt für Offline-Betrieb verfügbar."
echo "================================================"
