# Sitzungsprotokoll Ki

<p align="center">
</p>

![DSGVO](https://img.shields.io/badge/DSGVO-Konform-brightgreen) ![Offline](https://img.shields.io/badge/Offline-100%-success) ![Self-Hosted](https://img.shields.io/badge/Self-Hosted-100%-blue) ![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker) ![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)

> KI-gestützte Erstellung von Sitzungsprotokollen aus Transkriptionen

## Overview

Automatisiert die Erstellung professioneller Sitzungsprotokolle. Nutzt Whisper für Transkription und Claude/KI für Protokoll-Generierung. 100% offline-fähig, DSGVO-konform.

## Features

- Whisper-Transkription
- Sprecher-Erkennung
- KI-gestützte Protokoll-Generierung
- Export als PDF, DOCX, Markdown
- 100% offline-fähig
- Streamlit Web-Interface

## Tech Stack

| Tech | Zweck |
|------|-------|
| Python 3.10+ | Backend |
| Streamlit | Web-Interface |
| Whisper | Transkription |
| Claude AI | Protokoll-Generierung |
| Docker | Deployment |

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Screenshots

**Web-Interface**

<img src="screenshots/web-ui.png" alt="Web-Interface" width="800">

**Generiertes Sitzungsprotokoll**

<img src="screenshots/protokoll-output.png" alt="Generiertes Sitzungsprotokoll" width="800">

**Sprecher-Erkennung**

<img src="screenshots/speaker-detection.png" alt="Sprecher-Erkennung" width="800">

**Export-Optionen**

<img src="screenshots/export-options.png" alt="Export-Optionen" width="800">

---

## Contributing

Beiträge sind willkommen! Bitte erstelle einen Issue oder Pull Request.

## License

MIT License — siehe [LICENSE](LICENSE).

<p align="center">
</p>