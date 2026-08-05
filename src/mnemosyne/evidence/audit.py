import os
import json
import sqlite3
import hashlib
import hmac
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

class AuditLog:
    """
    Immutable, cryptographically chained, append-only SQLite log.
    """
    def __init__(self, db_path: str = "data/evidence/audit.db", secret_key: str = ""):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Use provided key or fallback to env var
        self.secret_key = secret_key or os.getenv("MNEMOSYNE_AUDIT_SECRET", "default_audit_secret_key_123").encode('utf-8')
        if isinstance(self.secret_key, str):
            self.secret_key = self.secret_key.encode('utf-8')
            
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    current_hash TEXT NOT NULL,
                    signature TEXT NOT NULL
                )
            """)
            conn.commit()
            
            # Initialize genesis block if empty
            cursor.execute("SELECT COUNT(*) FROM audit_log")
            if cursor.fetchone()[0] == 0:
                self._append_genesis()

    def _compute_hash(self, timestamp: str, action: str, payload: str, prev_hash: str) -> str:
        """Computes SHA-256 hash of the entry + previous hash to chain them."""
        msg = f"{timestamp}|{action}|{payload}|{prev_hash}"
        return hashlib.sha256(msg.encode('utf-8')).hexdigest()
        
    def _sign(self, current_hash: str) -> str:
        """HMAC-SHA256 signature to prove generation by MNEMOSYNE core."""
        return hmac.new(self.secret_key, current_hash.encode('utf-8'), hashlib.sha256).hexdigest()

    def _append_genesis(self) -> None:
        """Creates the root of the chain."""
        timestamp = datetime.now(timezone.utc).isoformat()
        action = "SYSTEM_INIT"
        payload = "{}"
        prev_hash = "0" * 64
        current_hash = self._compute_hash(timestamp, action, payload, prev_hash)
        signature = self._sign(current_hash)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO audit_log (timestamp, action, payload, prev_hash, current_hash, signature) VALUES (?, ?, ?, ?, ?, ?)",
                (timestamp, action, payload, prev_hash, current_hash, signature)
            )
            conn.commit()

    def append(self, action: str, payload: Dict[str, Any]) -> str:
        """Appends a new entry to the immutable log."""
        timestamp = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(payload, sort_keys=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Get previous hash
            cursor.execute("SELECT current_hash FROM audit_log ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            prev_hash = row[0] if row else ("0" * 64)
            
            current_hash = self._compute_hash(timestamp, action, payload_str, prev_hash)
            signature = self._sign(current_hash)
            
            cursor.execute(
                "INSERT INTO audit_log (timestamp, action, payload, prev_hash, current_hash, signature) VALUES (?, ?, ?, ?, ?, ?)",
                (timestamp, action, payload_str, prev_hash, current_hash, signature)
            )
            conn.commit()
            return current_hash

    def verify_chain(self) -> bool:
        """
        Validates the entire chain sequence and signatures.
        Runs automatically on startup (typically called by main.py).
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, action, payload, prev_hash, current_hash, signature FROM audit_log ORDER BY id ASC")
            rows = cursor.fetchall()
            
            if not rows:
                return True # Empty is technically valid, though we enforce genesis
                
            expected_prev = "0" * 64
            
            for i, row in enumerate(rows):
                timestamp, action, payload, prev_hash, current_hash, signature = row
                
                if i == 0:
                    expected_prev = "0" * 64
                
                # Check link
                if prev_hash != expected_prev:
                    logger.error(f"Audit chain broken at entry index {i}! Expected prev_hash {expected_prev}, got {prev_hash}")
                    return False
                    
                # Recompute hash
                computed_hash = self._compute_hash(timestamp, action, payload, prev_hash)
                if computed_hash != current_hash:
                    logger.error(f"Audit entry hash mismatch at index {i}!")
                    return False
                    
                # Verify signature
                expected_sig = self._sign(current_hash)
                if not hmac.compare_digest(expected_sig, signature):
                    logger.error(f"Audit entry signature mismatch at index {i}!")
                    return False
                    
                expected_prev = current_hash
                
        logger.info("Audit chain successfully verified.")
        return True

    def export_json(self, output_path: str) -> None:
        """Exports the chain to a JSON file for independent verification."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_log ORDER BY id ASC")
            rows = cursor.fetchall()
            
            entries = [dict(row) for row in rows]
            
            with open(output_path, "w") as f:
                json.dump(entries, f, indent=2)
