# Sitzungsprotokoll-KI – Audio zu strukturiertem Protokoll

![DSGVO-Konform](https://img.shields.io/badge/DSGVO-Konform-brightgreen)
![100% Offline](https://img.shields.io/badge/Offline-100%25-success)
![Self-Hosted](https://img.shields.io/badge/Self--Hosted-100%25-blue)
![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)
![License: MIT](https://img.shields.io/badge/Lizenz-MIT-yellow)

> 🏛️ **Vollständig offline fähige KI für Ratssitzungsprotokolle** — Automatische Transkription mit Whisper, Sprechererkennung und strukturiertes Protokoll. Keine Daten verlassen Ihr Netzwerk.

---

## ⚠️ Datenschutz (DSGVO) – Kernprinzip

**Dieses Projekt wurde speziell für den Einsatz in deutschen Behörden entwickelt, bei dem der Datenschutz höchste Priorität hat:**

- 🔒 **100% Offline:** Audio und Transkripte verlassen niemals Ihren Server
- 🚫 **Keine Cloud-Dienste:** Weder Whisper-Modell noch KI-Verarbeitung nutzen externe APIs
- 🗑️ **Löschkonzept:** Audio-Dateien werden nach der Verarbeitung automatisch gelöscht
- 📋 **Audit-Trail:** Jeder Verarbeitungsschritt wird protokolliert
- 🏗️ **Docker ohne Internet:** Container läuft komplett isoliert ohne Netzwerkanbindung

👉 [Vollständige Datenschutz-Dokumentation](docs/datenschutz.md)

---

## ✨ Features

| Feature | Beschreibung |
|---------|-------------|
| 🎙️ **Automatische Transkription** | Whisper AI wandelt Audio in Text um (Deutsch optimiert) |
| 👥 **Sprechererkennung** | Identifiziert Redner automatisch anhand von Sprachmerkmalen |
| 📋 **Strukturiertes Protokoll** | Tagesordnungspunkte, Beschlüsse und Abstimmungen automatisch erkannt |
| 🗳️ **Abstimmungserkennung** | Einstimmig/Mehrheit/Einstimmig gegen automatisch extrahiert |
| 📄 **Export** | DOCX (Behörden-Stil), PDF und HTML mit eingebettetem CSS |
| 🖥️ **Web-UI** | Streamlit-basierte Oberfläche, komplett auf Deutsch |
| 🐳 **Docker** | Ein-Kommando-Deployment, optional mit GPU-Unterstützung |
| 🔌 **Offline** | Funktioniert ohne Internetverbindung nach Modell-Download |
| 📝 **Editierbar** | Transkript und Protokoll können nachträglich bearbeitet werden |

---

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────┐
│                   Streamlit Web-UI                  │
│              (Audio-Upload, Vorschau, Export)        │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  Protokoll-Generator                │
│         (Tagesordnung, Beschlüsse, Abstimmungen)    │
└──────┬───────────────────────────────────┬──────────┘
       │                                   │
┌──────▼──────────┐              ┌────────▼──────────┐
│  Transcriber    │              │ Document Exporter │
│  (faster-whisper)│              │ (DOCX/PDF/HTML)  │
└──────┬──────────┘              └───────────────────┘
       │
┌──────▼──────────┐
│  Speaker ID     │
│  (pyannote)     │
└─────────────────┘
```

---

## 🚀 Schnellstart

### Voraussetzungen

| Komponente | Minimum | Empfohlen | Zweck |
|---|---|---|---|
| Python | 3.10+ | 3.11 | Streamlit & Transkription |
| RAM | 8 GB | 16 GB | Whisper-Modell |
| Docker | 20.10+ | 24.0+ | Container-Deployment |
| GPU | — | NVIDIA 4+ GB VRAM | Beschleunigte Transkription |
| Festplatte | 5 GB | 10 GB | Whisper-Modellgewichte |

### Installation

```bash
git clone https://github.com/ceeceeceecee/sitzungsprotokoll-ki.git
cd sitzungsprotokoll-ki

# Mit Docker (empfohlen)
docker compose up -d

# Oder lokal
pip install -r requirements.txt
streamlit run app.py
```

### Erste Schritte

1. **Web-UI öffnen** — Docker: `http://localhost:8501`, lokal: `streamlit run app.py`
2. **Audio-Datei hochladen** — MP3, WAV oder M4A
3. **Transkription starten** — Whisper analysiert automatisch, Sprecher werden erkannt
4. **Protokoll exportieren** — DOCX, PDF oder HTML im Behördenstil

---

## 💻 Systemanforderungen

| Komponente | Minimum | Empfohlen |
|-----------|---------|-----------|
| CPU | 4 Kerne | 8+ Kerne |
| RAM | 8 GB | 16+ GB |
| GPU | — | NVIDIA (4+ GB VRAM) |
| Festplatte | 5 GB (Modell) | 10 GB |
| Python | 3.10+ | 3.11 |
| Docker | 20.10+ | 24.0+ |

### Whisper-Modell-Empfehlung

| Modell | Größe | RAM | Qualität | Geschwindigkeit |
|--------|-------|-----|----------|----------------|
| tiny | 75 MB | 1 GB | Akzeptabel | Sehr schnell |
| base | 150 MB | 1 GB | Gut | Schnell |
| small | 500 MB | 2 GB | Sehr gut | Mittel |
| medium | 1.5 GB | 5 GB | Hervorragend | Langsam |
| large-v3 | 3 GB | 10 GB | Bestmöglich | Sehr langsam |

---

## 🚀 Quick Start

### Mit Docker (Empfohlen)

```bash
# Repository klonen
git clone https://github.com/ceeceeceecee/sitzungsprotokoll-ki.git
cd sitzungsprotokoll-ki

# Modell vorab herunterladen
bash scripts/download-whisper-model.sh small

# Docker starten
docker compose up -d

# Web-UI öffnen
# http://localhost:8501
```

### Ohne Docker (Entwicklung)

```bash
git clone https://github.com/ceeceeceecee/sitzungsprotokoll-ki.git
cd sitzungsprotokoll-ki

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

streamlit run app.py
```

---

## 📸 Screenshots

![Web-UI](screenshots/web-ui.png)
*Streamlit-Oberfläche mit Audio-Upload und Fortschrittsanzeige*

![Protokoll-Output](screenshots/protokoll-output.png)
*Automatisch generiertes Sitzungsprotokoll*

![Sprecher-Erkennung](screenshots/speaker-detection.png)
*Transkript mit farbcodierter Sprechererkennung*

![Export-Optionen](screenshots/export-options.png)
*Download als DOCX, PDF oder HTML*

---

## 🏛️ Use Cases für Behörden

| Szenario | Beschreibung |
|----------|-------------|
| **Gemeinderat** | Ratssitzungen automatisch protokollieren |
| **Bauausschuss** | Beschlüsse zu Bauvorhaben dokumentieren |
| **Haushaltsberatung** | Abstimmungsergebnisse festhalten |
| **Planungsausschuss** | Bebauungsplan-Beratungen protokollieren |
| **Hauptausschuss** | Strukturierte Protokolle für alle Ausschüsse |

---

## 🗺️ Roadmap

- [x] Grundlegende Transkription mit Whisper
- [x] Streamlit Web-UI (Deutsch)
- [x] DOCX/PDF/HTML Export
- [x] Sprechererkennung (pyannote.audio)
- [x] Beschluss- und Abstimmungserkennung
- [x] Docker-Deployment (Offline-fähig)
- [x] Batch-Verarbeitung mehrerer Audio-Dateien
- [x] Historien-Suche über vergangene Protokolle (Volltext, FTS5)
- [x] Wiedervorlage und Aufgabenverfolgung
- [x] Automatische Aufgabenextraktion aus Beschlüssen
- [ ] Integration mit Behörden-Software (z.B. Fabasoft)
- [ ] Automatische Verteilung an Ratsmitglieder

---

## 🤝 Contributing

Beiträge sind willkommen! Bitte beachten Sie:

1. Fork des Repositories erstellen
2. Feature-Branch anlegen (`git checkout -b feature/neues-feature`)
3. Änderungen committen
4. Branch pushen
5. Pull Request erstellen

---

## 📄 Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).

---

## 👤 Autor

**Cela** — Freelancer für digitale Verwaltungslösungen

[GitHub](https://github.com/ceeceeceecee)
