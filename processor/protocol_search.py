"""
ProtocolSearch – Volltextsuche ueber vergangene Protokolle.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ProtocolSearch:
    """Volltextsuche ueber gespeicherte Sitzungsprotokolle."""

    def __init__(self, db_path: str = "data/protokolle.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialisiert die SQLite-Datenbank."""
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS protokolle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gremium TEXT NOT NULL,
                sitzung_nr TEXT,
                datum TEXT,
                ort TEXT,
                transcript TEXT,
                protokoll_json TEXT,
                beschluesse_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS protokolle_fts USING fts5(
                gremium, transcript, beschluesse_json,
                content=protokolle,
                content_rowid=id
            );
            CREATE INDEX IF NOT EXISTS idx_protokolle_gremium ON protokolle(gremium);
            CREATE INDEX IF NOT EXISTS idx_protokolle_datum ON protokolle(datum);
        """)
        conn.commit()
        conn.close()

    def save_protocol(self, protocol: Dict[str, Any], transcript: str = "") -> int:
        """Speichert ein Protokoll in der Datenbank."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO protokolle (gremium, sitzung_nr, datum, ort, transcript, protokoll_json, beschluesse_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            protocol.get("gremium", ""),
            protocol.get("sitzung_nr", ""),
            protocol.get("datum", ""),
            protocol.get("ort", ""),
            transcript,
            json.dumps(protocol, ensure_ascii=False),
            json.dumps(protocol.get("beschluesse", []), ensure_ascii=False)
        ))
        conn.commit()
        row_id = cur.lastrowid

        # FTS Index aktualisieren
        cur.execute("""
            INSERT INTO protokolle_fts (rowid, gremium, transcript, beschluesse_json)
            VALUES (?, ?, ?, ?)
        """, (row_id, protocol.get("gremium", ""), transcript,
              json.dumps(protocol.get("beschluesse", []), ensure_ascii=False)))
        conn.commit()
        conn.close()

        logger.info(f"Protokoll gespeichert: ID {row_id}")
        return row_id

    def search(
        self,
        query: str,
        gremium: Optional[str] = None,
        datum_von: Optional[str] = None,
        datum_bis: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Volltextsuche ueber Protokolle.

        Args:
            query: Suchbegriff
            gremium: Optionaler Gremium-Filter
            datum_von: Datum ab (DD.MM.YYYY)
            datum_bis: Datum bis (DD.MM.YYYY)
            limit: Max. Ergebnisse

        Returns:
            Liste von Treffer-Dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        where_clauses = []
        params = []

        if query:
            where_clauses.append("protokolle_fts MATCH ?")
            params.append(query)
        if gremium:
            where_clauses.append("p.gremium = ?")
            params.append(gremium)
        if datum_von:
            where_clauses.append("p.datum >= ?")
            params.append(datum_von)
        if datum_bis:
            where_clauses.append("p.datum <= ?")
            params.append(datum_bis)

        where = " AND ".join(where_clauses) if where_clauses else "1=1"

        sql = f"""
            SELECT p.*, rank as suchrang
            FROM protokolle p
            {'JOIN protokolle_fts fts ON p.id = fts.rowid' if query else ''}
            WHERE {where}
            ORDER BY {f'suchrang' if query else 'p.datum DESC'}
            LIMIT ?
        """
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "gremium": row["gremium"],
                "sitzung_nr": row["sitzung_nr"],
                "datum": row["datum"],
                "ort": row["ort"],
                "transcript": row["transcript"][:300] + "..." if row["transcript"] and len(row["transcript"]) > 300 else row["transcript"],
                "beschluesse": json.loads(row["beschluesse_json"]) if row["beschluesse_json"] else [],
                "suchrang": row["suchrang"] if "suchrang" in row.keys() else None
            })

        logger.info(f"Suche '{query}': {len(results)} Treffer")
        return results

    def get_protocol(self, protocol_id: int) -> Optional[Dict[str, Any]]:
        """Laedt ein einzelnes Protokoll."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM protokolle WHERE id = ?", (protocol_id,)).fetchone()
        conn.close()

        if row:
            return {
                "id": row["id"],
                "gremium": row["gremium"],
                "sitzung_nr": row["sitzung_nr"],
                "datum": row["datum"],
                "ort": row["ort"],
                "transcript": row["transcript"],
                "protocol": json.loads(row["protokoll_json"]) if row["protokoll_json"] else None,
                "beschluesse": json.loads(row["beschluesse_json"]) if row["beschluesse_json"] else [],
                "created_at": row["created_at"]
            }
        return None

    def get_all_gremien(self) -> List[str]:
        """Gibt alle gespeicherten Gremien zurueck."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT DISTINCT gremium FROM protokolle ORDER BY gremium").fetchall()
        conn.close()
        return [r[0] for r in rows]

    def delete_protocol(self, protocol_id: int) -> bool:
        """Loescht ein Protokoll (DSGVO Loeschkonzept)."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("DELETE FROM protokolle WHERE id = ?", (protocol_id,))
        conn.execute("DELETE FROM protokolle_fts WHERE rowid = ?", (protocol_id,))
        conn.commit()
        conn.close()
        return cur.rowcount > 0
