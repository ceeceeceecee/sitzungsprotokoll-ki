"""
TaskTracker – Wiedervorlage und Aufgabenverfolgung aus Protokollen.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class TaskTracker:
    """Verfolgt Aufgaben und Wiedervorlagen aus Sitzungsprotokollen."""

    def __init__(self, db_path: str = "data/aufgaben.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialisiert die Datenbank."""
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS aufgaben (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titel TEXT NOT NULL,
                beschreibung TEXT,
                zustaendig TEXT,
                protokoll_id INTEGER,
                gremium TEXT,
                datum TEXT,
                faelligkeit TEXT,
                prioritaet TEXT DEFAULT 'mittel',
                status TEXT DEFAULT 'offen',
                kategorie TEXT,
                notizen TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_aufgaben_status ON aufgaben(status);
            CREATE INDEX IF NOT EXISTS idx_aufgaben_faelligkeit ON aufgaben(faelligkeit);
            CREATE INDEX IF NOT EXISTS idx_aufgaben_zustaendig ON aufgaben(zustaendig);
            CREATE INDEX IF NOT EXISTS idx_aufgaben_kategorie ON aufgaben(kategorie);
        """)
        conn.commit()
        conn.close()

    def add_task(
        self,
        titel: str,
        beschreibung: str = "",
        zustaendig: str = "",
        protokoll_id: Optional[int] = None,
        gremium: str = "",
        faelligkeit: Optional[str] = None,
        prioritaet: str = "mittel",
        kategorie: str = "Sonstiges"
    ) -> int:
        """Fuegt eine neue Aufgabe hinzu."""
        if not faelligkeit:
            faelligkeit = (datetime.now() + timedelta(days=14)).strftime("%d.%m.%Y")

        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("""
            INSERT INTO aufgaben (titel, beschreibung, zustaendig, protokoll_id, gremium,
                datum, faelligkeit, prioritaet, status, kategorie)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            titel, beschreibung, zustaendig, protokoll_id, gremium,
            datetime.now().strftime("%d.%m.%Y"), faelligkeit, prioritaet, "offen", kategorie
        ))
        conn.commit()
        conn.close()
        logger.info(f"Aufgabe erstellt: {titel}")
        return cur.lastrowid

    def extract_tasks_from_protocol(
        self,
        protocol: Dict[str, Any],
        protocol_id: Optional[int] = None
    ) -> List[int]:
        """
        Extrahiert automatisch Aufgaben aus einem Protokoll.
        Sucht nach Schluesseln wie "wird geprueft", "ist zu erstellen", "wird vorgelegt" etc.
        """
        tasks_created = []
        text = json.dumps(protocol, ensure_ascii=False).lower()

        # Schluesselwoerter fuer Aufgaben
        schluessel = [
            "wird geprueft", "ist zu erstellen", "wird vorgelegt",
            "wird erarbeitet", "soll ueberprueft", "ist zu pruefen",
            "wird vorbereitet", "wird beantragt", "soll erstellt",
            "ist zu koordinieren", "wird beauftragt", "wird bearbeitet",
            "faellig", "wiedervorlage", "termin"
        ]

        # Einfache Extraktion: Beschluesse nach Aufgaben-Schluesseln durchsuchen
        beschluesse = protocol.get("beschluesse", [])
        gremium = protocol.get("gremium", "")

        for beschluss in beschluesse:
            beschluss_text = beschluss.get("text", "").lower()

            for schluesselwort in schluessel:
                if schluesselwort in beschluss_text:
                    titel = beschluss.get("text", "")[:100]
                    if len(beschluss.get("text", "")) > 100:
                        titel += "..."
                    task_id = self.add_task(
                        titel=titel,
                        beschreibung=beschluss.get("text", ""),
                        protokoll_id=protocol_id,
                        gremium=gremium,
                        kategorie="Beschluss"
                    )
                    tasks_created.append(task_id)
                    break

        logger.info(f"{len(tasks_created)} Aufgaben aus Protokoll extrahiert")
        return tasks_created

    def get_tasks(
        self,
        status: Optional[str] = None,
        zustaendig: Optional[str] = None,
        prioritaet: Optional[str] = None,
        ueberfaellig: bool = False
    ) -> List[Dict[str, Any]]:
        """Gibt Aufgaben zurueck, optional gefiltert."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        where_clauses = []
        params = []

        if status:
            where_clauses.append("status = ?")
            params.append(status)
        if zustaendig:
            where_clauses.append("zustaendig = ?")
            params.append(zustaendig)
        if prioritaet:
            where_clauses.append("prioritaet = ?")
            params.append(prioritaet)
        if ueberfaellig:
            where_clauses.append("faelligkeit < ? AND status != 'erledigt'")
            params.append(datetime.now().strftime("%d.%m.%Y"))

        where = " AND ".join(where_clauses) if where_clauses else "1=1"

        rows = conn.execute(f"""
            SELECT * FROM aufgaben
            WHERE {where}
            ORDER BY
                CASE WHEN status = 'offen' AND faelligkeit < ? THEN 0 ELSE 1 END,
                faelligkeit ASC
        """, params + [datetime.now().strftime("%d.%m.%Y")]).fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_task(
        self,
        task_id: int,
        status: Optional[str] = None,
        faelligkeit: Optional[str] = None,
        notizen: Optional[str] = None,
        prioritaet: Optional[str] = None
    ) -> bool:
        """Aktualisiert eine Aufgabe."""
        updates = []
        params = []

        if status:
            updates.append("status = ?")
            params.append(status)
        if faelligkeit:
            updates.append("faelligkeit = ?")
            params.append(faelligkeit)
        if notizen is not None:
            updates.append("notizen = ?")
            params.append(notizen)
        if prioritaet:
            updates.append("prioritaet = ?")
            params.append(prioritaet)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        params.append(task_id)

        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(f"UPDATE aufgaben SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Aufgabenstatistiken zurueck."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        gesamt = cur.execute("SELECT COUNT(*) FROM aufgaben").fetchone()[0]
        offen = cur.execute("SELECT COUNT(*) FROM aufgaben WHERE status = 'offen'").fetchone()[0]
        erledigt = cur.execute("SELECT COUNT(*) FROM aufgaben WHERE status = 'erledigt'").fetchone()[0]
        in_bearbeitung = cur.execute("SELECT COUNT(*) FROM aufgaben WHERE status = 'in_bearbeitung'").fetchone()[0]
        ueberfaellig = cur.execute(
            "SELECT COUNT(*) FROM aufgaben WHERE faelligkeit < ? AND status != 'erledigt'",
            (datetime.now().strftime("%d.%m.%Y"),)
        ).fetchone()[0]

        # Pro Gremium
        gremien = cur.execute("""
            SELECT gremium, COUNT(*) as cnt
            FROM aufgaben WHERE status != 'erledigt'
            GROUP BY gremium ORDER BY cnt DESC
        """).fetchall()

        conn.close()

        return {
            "gesamt": gesamt,
            "offen": offen,
            "in_bearbeitung": in_bearbeitung,
            "erledigt": erledigt,
            "ueberfaellig": ueberfaellig,
            "gremien": [{"name": g[0], "anzahl": g[1]} for g in gremien]
        }
