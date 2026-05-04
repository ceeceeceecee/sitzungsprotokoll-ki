"""
ProtocolGenerator – Generiert strukturierte Sitzungsprotokolle aus Transkripten.
Verwendet KI zur Extraktion von Tagesordnung, Beschlüssen und Abstimmungen.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class ProtocolGenerator:
    """Generiert strukturierte Sitzungsprotokolle aus Transkripten."""

    def __init__(self, ai_provider: str = "ollama"):
        """
        Initialisiert den Protokoll-Generator.

        Args:
            ai_provider: KI-Anbieter ('ollama' oder 'openai')
        """
        self.ai_provider = ai_provider
        self.base_url = os.environ.get(
            "OLLAMA_BASE_URL", os.getenv("OLLAMA_HOST", "http://localhost:11434")
        )
        self.model = os.environ.get(
            "OLLAMA_MODEL", "llama3"
        )
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        self.openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def generate(
        self,
        transcript: str,
        gremium: str,
        sitzung_nr: str,
        datum: Any,
        uhrzeit: str,
        ort: str,
        sprecher_liste: Optional[List[str]] = None,
        behoerdenname: str = "Stadt Musterhausen"
    ) -> Dict[str, Any]:
        """
        Generiert ein strukturiertes Sitzungsprotokoll.

        Args:
            transcript: Vollständiges Transkript
            gremium: Name des Gremiums
            sitzung_nr: Sitzungsnummer
            datum: Datum der Sitzung
            uhrzeit: Beginn-Uhrzeit
            ort: Ort der Sitzung
            sprecher_liste: Liste der bekannten Sprecher
            behoerdenname: Name der Behörde

        Returns:
            Dict mit strukturiertem Protokoll
        """
        if not transcript or not transcript.strip():
            raise ValueError("Leeres Transkript übergeben.")

        # KI-Analyse durchführen
        try:
            analysis = self._analyze_transcript(
                transcript, gremium, sprecher_liste or []
            )
        except Exception as e:
            logger.error(f"KI-Analyse fehlgeschlagen: {e}")
            analysis = self._fallback_analysis(transcript)

        # Protokoll strukturieren
        protocol = {
            "titel": f"Sitzungsprotokoll {gremium} – Sitzung Nr. {sitzung_nr}",
            "behoerdenname": behoerdenname,
            "gremium": gremium,
            "sitzung_nr": sitzung_nr,
            "datum": str(datum) if datum else "",
            "uhrzeit": uhrzeit,
            "ort": ort,
            "sprecher": sprecher_liste or [],
            "tagesordnungspunkte": analysis.get("tagesordnungspunkte", []),
            "beschluesse": analysis.get("beschluesse", []),
            "abstimmungen": analysis.get("abstimmungen", []),
            "zusammenfassung": analysis.get("zusammenfassung", ""),
            "html": "",
            "generated_at": datetime.now().isoformat()
        }

        # HTML generieren
        protocol["html"] = self._generate_html(protocol)

        logger.info(
            f"Protokoll generiert: {len(protocol['tagesordnungspunkte'])} TOPs, "
            f"{len(protocol['beschluesse'])} Beschlüsse"
        )

        return protocol

    def _analyze_transcript(
        self,
        transcript: str,
        gremium: str,
        sprecher_liste: List[str]
    ) -> Dict[str, Any]:
        """Analysiert das Transkript mit KI."""

        # Prompt laden
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "protokoll-struktur.txt"
        )
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            system_prompt = self._default_system_prompt()

        user_prompt = f"""Analysiere folgendes Transkript einer {gremium}-Sitzung.

Bekannte Sprecher: {', '.join(sprecher_liste) if sprecher_liste else 'Keine angegeben'}

=== TRANSKRIPT ===
{transcript[:15000]}

=== AUFGABE ===
Extrahiere:
1. Tagesordnungspunkte mit Nummer und Titel
2. Beschlüsse mit Beschlussnummer und Text
3. Abstimmungen mit Ergebnis (Einstimmig/Mehrheit/Ablehnung)
4. Zusammenfassung der Sitzung (max 3 Sätze)

Antworte im JSON-Format."""

        # KI-Aufruf
        if self.ai_provider == "openai" and self.openai_api_key:
            return self._call_openai(system_prompt, user_prompt)
        else:
            return self._call_ollama(system_prompt, user_prompt)

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> Dict:
        """Ruft Ollama lokal auf."""
        import urllib.request
        import urllib.error

        url = f"{self.base_url}/api/generate"

        payload = json.dumps({
            "model": self.model,
            "prompt": f"### System:\n{system_prompt}\n\n### User:\n{user_prompt}\n\n### Antwort:",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
                "top_p": 0.9
            }
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=300) as response:
                result = json.loads(response.read().decode("utf-8"))
                content = result.get("response", "{}")

                # JSON aus der Antwort extrahieren
                return self._parse_json_response(content)
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Ollama nicht erreichbar unter {self.base_url}. "
                f"Stellen Sie sicher, dass Ollama läuft: {e}"
            )
        except Exception as e:
            raise RuntimeError(f"Fehler beim Ollama-Aufruf: {e}")

    def _call_openai(self, system_prompt: str, user_prompt: str) -> Dict:
        """Ruft die OpenAI API auf."""
        import urllib.request
        import urllib.error

        url = "https://api.openai.com/v1/chat/completions"

        payload = json.dumps({
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                return self._parse_json_response(content)
        except Exception as e:
            raise RuntimeError(f"Fehler beim OpenAI-Aufruf: {e}")

    def _parse_json_response(self, content: str) -> Dict:
        """Parst die JSON-Antwort der KI."""
        try:
            # Versuche direkten JSON-Parse
            return json.loads(content)
        except json.JSONDecodeError:
            # Versuche JSON-Block zu extrahieren
            import re
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            raise ValueError("KI-Antwort konnte nicht als JSON geparst werden.")

    def _fallback_analysis(self, transcript: str) -> Dict:
        """Fallback-Analyse ohne KI."""
        lines = transcript.strip().split("\n")
        return {
            "tagesordnungspunkte": [
                {"nummer": 1, "titel": "Allgemeine Beratung", "inhalt": transcript[:500]}
            ],
            "beschluesse": [],
            "abstimmungen": [],
            "zusammenfassung": "Sitzung wurde protokolliert. Automatische Analyse nicht verfügbar."
        }

    def _default_system_prompt(self) -> str:
        """Standard-Prompt falls Datei nicht gefunden."""
        return """Du bist ein KI-Assistent für deutsche Behörden. Analysiere Sitzungstranskripte und erstelle strukturierte Protokolle. Verwende Verwaltungsstil (3. Person, Präteritum). Antworte im JSON-Format."""

    def _generate_html(self, protocol: Dict) -> str:
        """Generiert HTML für das Protokoll."""
        html_parts = [
            f"<h2>{protocol['titel']}</h2>",
            f"<p><strong>{protocol['behoerdenname']}</strong></p>",
            f"<p>Datum: {protocol['datum']} | Beginn: {protocol['uhrzeit']} Uhr</p>",
            f"<p>Ort: {protocol['ort']}</p>",
            "<hr>"
        ]

        if protocol["sprecher"]:
            html_parts.append("<p><strong>Anwesende:</strong> " + ", ".join(protocol["sprecher"]) + "</p>")

        html_parts.append("<h3>Tagesordnungspunkte</h3>")
        for top in protocol["tagesordnungspunkte"]:
            html_parts.append(
                f"<h4>TOP {top.get('nummer', '?')} – {top.get('titel', 'Ohne Titel')}</h4>"
            )
            html_parts.append(f"<p>{top.get('inhalt', '')}</p>")

        if protocol["beschluesse"]:
            html_parts.append("<h3>Beschlüsse</h3>")
            for b in protocol["beschluesse"]:
                html_parts.append(
                    f"<p><strong>Beschluss {b.get('nummer', '?')}:</strong> {b.get('text', '')}</p>"
                )
                if b.get("abstimmung"):
                    html_parts.append(f"<p><em>Abstimmung: {b['abstimmung']}</em></p>")

        if protocol["zusammenfassung"]:
            html_parts.append("<h3>Zusammenfassung</h3>")
            html_parts.append(f"<p>{protocol['zusammenfassung']}</p>")

        html_parts.append("<hr><p><em>Automatisch generiert mit Sitzungsprotokoll-KI</em></p>")

        return "\n".join(html_parts)

    def extract_agenda_items(self, transcript: str) -> List[Dict]:
        """Extrahiert Tagesordnungspunkte aus dem Transkript."""
        analysis = self._analyze_transcript(transcript, "", [])
        return analysis.get("tagesordnungspunkte", [])

    def extract_decisions(self, transcript: str) -> List[Dict]:
        """Extrahiert Beschlüsse aus dem Transkript."""
        analysis = self._analyze_transcript(transcript, "", [])
        return analysis.get("beschluesse", [])

    def extract_votes(self, transcript: str) -> List[str]:
        """Extrahiert Abstimmungsergebnisse."""
        analysis = self._analyze_transcript(transcript, "", [])
        return analysis.get("abstimmungen", [])

    def generate_summary(self, transcript: str) -> str:
        """Generiert eine Zusammenfassung der Sitzung."""
        analysis = self._analyze_transcript(transcript, "", [])
        return analysis.get("zusammenfassung", "")

    def format_protocol(self, protocol: Dict) -> str:
        """Formatiert das Protokoll als reinen Text."""
        lines = [
            protocol["titel"],
            "=" * len(protocol["titel"]),
            "",
            f"{protocol['behoerdenname']}",
            f"Datum: {protocol['datum']} | Beginn: {protocol['uhrzeit']} Uhr",
            f"Ort: {protocol['ort']}",
            ""
        ]
        if protocol["sprecher"]:
            lines.append(f"Anwesende: {', '.join(protocol['sprecher'])}")
            lines.append("")

        for top in protocol["tagesordnungspunkte"]:
            lines.append(f"TOP {top.get('nummer', '?')} – {top.get('titel', '')}")
            lines.append("-" * 40)
            lines.append(top.get("inhalt", ""))
            lines.append("")

        if protocol["beschluesse"]:
            lines.append("BESCHLÜSSE")
            lines.append("-" * 40)
            for b in protocol["beschluesse"]:
                lines.append(f"Beschluss {b.get('nummer', '?')}: {b.get('text', '')}")
                if b.get("abstimmung"):
                    lines.append(f"  Abstimmung: {b['abstimmung']}")
            lines.append("")

        if protocol["zusammenfassung"]:
            lines.append("ZUSAMMENFASSUNG")
            lines.append("-" * 40)
            lines.append(protocol["zusammenfassung"])

        return "\n".join(lines)
