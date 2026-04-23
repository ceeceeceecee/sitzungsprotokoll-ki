# Setup-Guide – Sitzungsprotokoll-KI

## 📋 Voraussetzungen

- Docker Engine 20.10+ und Docker Compose v2+
- Mindestens 8 GB RAM (16 GB empfohlen)
- 10 GB freier Festplattenplatz
- Optional: NVIDIA GPU mit CUDA (beschleunigt Whisper)

## 🔒 Sicherheitscheckliste

- [ ] Docker-Engine ist aktuell (`docker version`)
- [ ] Firewall blockiert Port 8501 (nur Reverse Proxy erlaubt)
- [ ] Reverse Proxy für HTTPS konfiguriert
- [ ] Streamlit-Passwortschutz aktiviert
- [ ] Whisper-Modell vorab heruntergeladen (Offline)
- [ ] Docker-Netzwerk ohne externen Zugang (`internal: true`)
- [ ] Keine Volume-Persistenz für Audio-Dateien
- [ ] Datenschutzbeauftragter informiert
- [ ] Einwilligung der Sitzungsteilnehmer eingeholt
- [ ] Löschkonzept dokumentiert

## 🚀 Installation

### 1. Repository klonen

```bash
git clone https://github.com/ceeceeceecee/sitzungsprotokoll-ki.git
cd sitzungsprotokoll-ki
```

### 2. Whisper-Modell herunterladen (Offline)

```bash
bash scripts/download-whisper-model.sh small
```

Modell-Empfehlung nach Hardware:

| Hardware | Empfohlenes Modell | RAM | Qualität |
|----------|-------------------|-----|----------|
| Raspberry Pi 4 | tiny | 1 GB | Akzeptabel |
| Standard-Server | base | 2 GB | Gut |
| Guter Server | small | 4 GB | Sehr gut |
| GPU-Server | medium | 8 GB | Hervorragend |

### 3. Konfigurieren

```bash
cp .env.example .env
nano .env
```

### 4. Docker starten

```bash
docker compose up -d
```

### 5. Web-UI öffnen

```
http://localhost:8501
```

## 🎤 Audioqualität-Tipps

### Empfohlen
- **Format:** WAV (unkomprimiert) oder MP3 (min. 128 kbps)
- **Abtastrate:** 16 kHz oder höher
- **Mikrofon:** Konferenzmikrofon oder Richtmikrofon
- **Raum:** Kleiner Raum mit geringer Hallzeit
- **Abstand:** Mikrofon max. 2 m von Rednern entfernt

### Problematisch
- Hintergrundgeräusche (Klimaanlage, Verkehr)
- Mehrere gleichzeitige Redner (Überlappung)
- Starke Akustik (große Säle ohne Beschallung)
- Handys als Aufnahmegerät (Ruhestörung)

### Qualität verbessern
- Rauschunterdrückung vor der Transkription
- Normalisierung der Lautstärke
- Konvertierung nach WAV 16 kHz mono
- Test-Aufnahme vor der Sitzung durchführen

## 🧪 Testbetrieb

```bash
# Mit Test-Audio
docker exec -it sitzungsprotokoll-ki python -c "
from processor.transcriber import AudioTranscriber
t = AudioTranscriber('tiny', 'cpu')
print('Transcriber initialisiert:', t.model_size)
"
```

## ⚠️ Fehlerbehebung

| Problem | Lösung |
|---------|--------|
| Modell nicht gefunden | `download-whisper-model.sh` ausführen |
| CUDA Fehler | CPU-Modus verwenden: `WHISPER_DEVICE=cpu` |
| GPU nicht erkannt | NVIDIA-Treiber und CUDA installieren |
| Ollama nicht erreichbar | Ollama Container starten: `docker run -d ollama/ollama` |
| Speicherplatz voll | Größeres Modell oder weniger Speicherbedarf |
