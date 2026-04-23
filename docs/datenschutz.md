# Datenschutz-Dokumentation – Sitzungsprotokoll-KI

## ⚖️ Rechtsgrundlage

Die Verarbeitung personenbezogener Daten erfolgt auf Grundlage von:

- **Art. 6 Abs. 1 lit. e DSGVO** – Ausführung einer Aufgabe im öffentlichen Interesse
- **Art. 6 Abs. 1 lit. c DSGVO** – Erfüllung einer rechtlichen Verpflichtung
- **§ 3 BDSG** – Verarbeitung durch öffentliche Stellen

## 🔒 Datenschutz als Kernprinzip

Dieses Projekt wurde von Grund auf für den Datenschutz konzipiert:

### 100% Offline
- Alle Datenverarbeitung erfolgt auf dem eigenen Server
- Keine Internetverbindung erforderlich (nach Modell-Download)
- Keine Daten werden an externe Dienste gesendet

### Keine Cloud-Dienste
- Whisper-Modell läuft lokal
- KI-Protokollgenerierung erfolgt lokal (Ollama)
- Optional: OpenAI für verbesserte Qualität (nur Transkript-Text)

## 📊 Datenfluss-Diagramm

```
Audio-Datei (MP3/WAV)
       │
       ▼
┌──────────────────┐
│  Streamlit UI    │ ← Nur Web-Interface, keine Daten gespeichert
│  (Lokal)         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Whisper AI      │ ← Lokales Modell, keine externe Verbindung
│  (Transkription) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Sprecher-ID     │ ← Lokale Verarbeitung (pyannote.audio)
│  (Optional)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Protokoll-KI    │ ← Lokal (Ollama) oder Cloud (OpenAI, nur Text)
│  (Strukturierung)│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  DOCX/PDF/HTML   │ ← Lokal generiert
│  (Export)        │
└──────────────────┘

⬆️ Audio wird nach Verarbeitung automatisch GELÖSCHT
```

## 🗑️ Löschkonzept

| Daten | Löschzeitpunkt | Methode |
|-------|---------------|---------|
| Audio-Datei | Nach Transkription | Automatisch |
| Transkript (RAM) | Bei Session-Ende | Automatisch |
| Protokoll-Export | Vom Nutzer gesteuert | Manuell |
| Docker-Volumes | Bei Container-Entfernung | Manuell |

### Automatische Audio-Löschung
Die Audio-Datei wird unmittelbar nach Abschluss der Transkription gelöscht. Es werden keine Kopien oder Zwischendateien zurückbehalten.

## 🏗️ Technische und organisatorische Maßnahmen (TOMs)

- **Isolation:** Docker-Container ohne Netzwerkanbindung (`internal: true`)
- **Kein Persistenz:** Audio-Dateien werden nur im temporären Speicher verarbeitet
- **Verschlüsselung:** TLS bei Streamlit-Zugriff (via Reverse Proxy)
- **Zugangskontrolle:** Passwortschutz für Streamlit-UI
- **Protokollierung:** Verarbeitungsschritte werden geloggt

## 📝 Besondere Schutzbedarfsfaktoren

### Besonders betroffene Personen
Sitzungsteilnehmer können besonders betroffene Personen sein (z.B. bei sozialen Themen). Die automatische Transkription erfordert eine Datenschutz-Folgenabschätzung.

### Empfehlung
- **DSGVO-Art. 35:** Datenschutz-Folgenabschätzung durchführen
- **Transparenz:** Teilnehmer über Aufzeichnung und KI-Verarbeitung informieren
- **Einwilligung:** Nachweis der Einwilligung der Teilnehmer einholen
- **Löschung:** Klare Löschfristen für Protokolle definieren
