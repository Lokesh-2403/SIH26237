import sqlite3
from pathlib import Path


# =========================================================
# DATABASE PATH
# =========================================================

DB_PATH = Path("backend/database/sih26237.db")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # ---------------------------------------------------------
        # RECIPIENTS
        # ---------------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                public_key TEXT,
                kem_public_key TEXT
            )
        """)

        # ---------------------------------------------------------
        # DATABASE MIGRATION
        # ---------------------------------------------------------

        cursor.execute("""
            PRAGMA table_info(recipients)
        """)

        columns = [
            row[1]
            for row in cursor.fetchall()
        ]

        # Add ML-KEM public key column to older databases
        if "kem_public_key" not in columns:
            cursor.execute("""
                ALTER TABLE recipients
                ADD COLUMN kem_public_key TEXT
            """)

        # ---------------------------------------------------------
        # DOCUMENTS
        # ---------------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                encrypted_data BLOB NOT NULL,
                nonce BLOB NOT NULL,
                encryption_key BLOB NOT NULL
            )
        """)

        # ---------------------------------------------------------
        # DOCUMENT RECIPIENTS
        # ---------------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                recipient_id TEXT NOT NULL,
                kem_ciphertext TEXT NOT NULL,
                wrapped_key TEXT NOT NULL,
                wrap_nonce TEXT NOT NULL,
                UNIQUE(document_id, recipient_id)
            )
        """)

        # ---------------------------------------------------------
        # DECRYPTION EVENTS
        # ---------------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decryption_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                recipient_id TEXT NOT NULL,
                session_id TEXT UNIQUE NOT NULL,
                watermark_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                signature TEXT
            )
        """)

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# RECIPIENT FUNCTIONS
# =========================================================

def add_recipient(
    recipient_id,
    name,
    email,
    public_key=None,
    kem_public_key=None
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO recipients (
                recipient_id,
                name,
                email,
                public_key,
                kem_public_key
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            recipient_id,
            name,
            email,
            public_key,
            kem_public_key
        ))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_recipient(recipient_id):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                recipient_id,
                name,
                email,
                public_key,
                kem_public_key
            FROM recipients
            WHERE recipient_id = ?
        """, (recipient_id,))

        recipient = cursor.fetchone()

        return recipient

    finally:
        connection.close()


def get_all_recipients():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                recipient_id,
                name,
                email,
                public_key,
                kem_public_key
            FROM recipients
            ORDER BY id ASC
        """)

        recipients = cursor.fetchall()

        return recipients

    finally:
        connection.close()


def update_recipient_kem_public_key(
    recipient_id,
    kem_public_key
):
    """
    Update the ML-KEM public key for an existing recipient.

    This is used to repair older recipient records that were
    created before ML-KEM public-key storage was implemented.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE recipients
            SET kem_public_key = ?
            WHERE recipient_id = ?
        """, (
            kem_public_key,
            recipient_id
        ))

        updated = cursor.rowcount

        connection.commit()

        return updated

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# DOCUMENT FUNCTIONS
# =========================================================

def add_document(
    document_id,
    filename,
    encrypted_data,
    nonce,
    encryption_key
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO documents (
                document_id,
                filename,
                encrypted_data,
                nonce,
                encryption_key
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            document_id,
            filename,
            encrypted_data,
            nonce,
            encryption_key
        ))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_document(document_id):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                document_id,
                filename,
                encrypted_data,
                nonce,
                encryption_key
            FROM documents
            WHERE document_id = ?
        """, (document_id,))

        document = cursor.fetchone()

        return document

    finally:
        connection.close()


# =========================================================
# ML-KEM DOCUMENT DISTRIBUTION
# =========================================================

def add_document_recipient(
    document_id,
    recipient_id,
    kem_ciphertext,
    wrapped_key,
    wrap_nonce
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT OR REPLACE INTO document_recipients (
                document_id,
                recipient_id,
                kem_ciphertext,
                wrapped_key,
                wrap_nonce
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            document_id,
            recipient_id,
            kem_ciphertext,
            wrapped_key,
            wrap_nonce
        ))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_document_recipient(
    document_id,
    recipient_id
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                document_id,
                recipient_id,
                kem_ciphertext,
                wrapped_key,
                wrap_nonce
            FROM document_recipients
            WHERE document_id = ?
            AND recipient_id = ?
        """, (
            document_id,
            recipient_id
        ))

        record = cursor.fetchone()

        return record

    finally:
        connection.close()


# =========================================================
# DECRYPTION EVENT FUNCTIONS
# =========================================================

def add_decryption_event(
    document_id,
    recipient_id,
    session_id,
    watermark_id,
    timestamp,
    signature=None
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO decryption_events (
                document_id,
                recipient_id,
                session_id,
                watermark_id,
                timestamp,
                signature
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            document_id,
            recipient_id,
            session_id,
            watermark_id,
            timestamp,
            signature
        ))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_decryption_event_by_watermark(watermark_id):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                document_id,
                recipient_id,
                session_id,
                watermark_id,
                timestamp,
                signature
            FROM decryption_events
            WHERE watermark_id = ?
        """, (watermark_id,))

        event = cursor.fetchone()

        return event

    finally:
        connection.close()