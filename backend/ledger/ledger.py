import hashlib
import json
from pathlib import Path


# ============================================================
# DISTRIBUTED LEDGER CONFIGURATION
# ============================================================

LEDGER_DIR = Path("backend/ledger/nodes")

NODE_IDS = (
    "NODE-01",
    "NODE-02",
    "NODE-03",
)

QUORUM = 2


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

LEDGER_FILE = LEDGER_DIR / "ledger.json"

_DEFAULT_LEDGER_FILE = LEDGER_FILE


# ============================================================
# HASHING
# ============================================================

def calculate_hash(data: str) -> str:
    """
    Calculate SHA-256 hash.
    """

    return hashlib.sha256(
        data.encode("utf-8")
    ).hexdigest()


def _canonical_json(data) -> str:
    """
    Produce deterministic JSON for hashing.
    """

    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
    )


def _entry_hash(entry_without_hash: dict) -> str:
    """
    Calculate the hash of a ledger entry
    excluding current_hash.
    """

    return calculate_hash(
        _canonical_json(entry_without_hash)
    )


# ============================================================
# DIRECTORY / FILE HELPERS
# ============================================================

def _ensure_ledger_directory():
    LEDGER_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def _node_file(node_id: str) -> Path:
    return LEDGER_DIR / f"{node_id}.json"


def _load_node(node_id: str):
    """
    Load one distributed ledger replica.
    """

    path = _node_file(node_id)

    if not path.exists():
        return []

    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, list):
            return data

    except Exception:
        return []

    return []


def _write_node(node_id: str, entries):
    """
    Write one distributed ledger replica.
    """

    path = _node_file(node_id)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            entries,
            indent=4,
        ),
        encoding="utf-8",
    )


# ============================================================
# LEGACY SINGLE-FILE COMPATIBILITY
# ============================================================

def _using_legacy_ledger() -> bool:
    """
    Detect whether a test or legacy caller replaced LEDGER_FILE.
    """

    return LEDGER_FILE != _DEFAULT_LEDGER_FILE


def _load_legacy_ledger():
    """
    Load the temporary/legacy single-file ledger.
    """

    if not LEDGER_FILE.exists():
        return []

    try:
        data = json.loads(
            LEDGER_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, list):
            return data

    except Exception:
        return []

    return []


def _write_legacy_ledger(entries):
    """
    Write the temporary/legacy single-file ledger.
    """

    LEDGER_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    LEDGER_FILE.write_text(
        json.dumps(
            entries,
            indent=4,
        ),
        encoding="utf-8",
    )


def _add_legacy_entry(event: dict):
    """
    Add an entry to the compatibility
    single-file ledger.
    """

    entries = _load_legacy_ledger()

    previous_hash = (
        entries[-1]["current_hash"]
        if entries
        else "GENESIS"
    )

    entry = {
        "index": len(entries),
        "previous_hash": previous_hash,
        "event": event,
    }

    entry["current_hash"] = _entry_hash(
        entry
    )

    entries.append(entry)

    _write_legacy_ledger(entries)

    return entry


def _verify_legacy_ledger() -> bool:
    """
    Verify the compatibility single-file ledger.
    """

    entries = _load_legacy_ledger()

    previous_hash = "GENESIS"

    for index, entry in enumerate(entries):

        if not isinstance(entry, dict):
            return False

        if entry.get("index") != index:
            return False

        if entry.get("previous_hash") != previous_hash:
            return False

        if "event" not in entry:
            return False

        stored_hash = entry.get(
            "current_hash"
        )

        if not stored_hash:
            return False

        entry_without_hash = {
            "index": entry["index"],
            "previous_hash": entry["previous_hash"],
            "event": entry["event"],
        }

        calculated_hash = _entry_hash(
            entry_without_hash
        )

        if stored_hash != calculated_hash:
            return False

        previous_hash = stored_hash

    return True


# ============================================================
# CHAIN HELPERS
# ============================================================

def _get_node_last_hash(node_id: str) -> str:

    entries = _load_node(node_id)

    if not entries:
        return "GENESIS"

    return entries[-1]["current_hash"]


def get_last_hash() -> str:
    """
    Return the latest hash agreed upon by the quorum.
    """

    if _using_legacy_ledger():

        entries = _load_legacy_ledger()

        if not entries:
            return "GENESIS"

        return entries[-1]["current_hash"]

    hashes = []

    for node_id in NODE_IDS:

        entries = _load_node(node_id)

        if entries:
            hashes.append(
                entries[-1]["current_hash"]
            )
        else:
            hashes.append("GENESIS")

    counts = {}

    for value in hashes:
        counts[value] = (
            counts.get(value, 0) + 1
        )

    for value, count in counts.items():

        if count >= QUORUM:
            return value

    return "GENESIS"


# ============================================================
# ENTRY CREATION
# ============================================================

def _create_entry(
    index: int,
    previous_hash: str,
    event: dict,
):
    """
    Create a canonical ledger entry.
    """

    entry = {
        "index": index,
        "previous_hash": previous_hash,
        "event": event,
    }

    entry["current_hash"] = _entry_hash(
        entry
    )

    return entry


# ============================================================
# ADD LEDGER ENTRY
# ============================================================

def add_ledger_entry(event: dict):
    """
    Add an event to the ledger.

    Normal mode:
        Replicate to NODE-01, NODE-02 and NODE-03.

    Legacy/test mode:
        Write to LEDGER_FILE.
    """

    # --------------------------------------------------------
    # Legacy compatibility mode
    # --------------------------------------------------------

    if _using_legacy_ledger():
        return _add_legacy_entry(event)

    # --------------------------------------------------------
    # Distributed mode
    # --------------------------------------------------------

    _ensure_ledger_directory()

    node_entries = {
        node_id: _load_node(node_id)
        for node_id in NODE_IDS
    }

    # --------------------------------------------------------
    # Determine quorum previous hash
    # --------------------------------------------------------

    last_hashes = {
        node_id: (
            entries[-1]["current_hash"]
            if entries
            else "GENESIS"
        )
        for node_id, entries in node_entries.items()
    }

    hash_counts = {}

    for value in last_hashes.values():

        hash_counts[value] = (
            hash_counts.get(value, 0) + 1
        )

    quorum_hash = None

    for value, count in hash_counts.items():

        if count >= QUORUM:
            quorum_hash = value
            break

    if quorum_hash is None:
        raise RuntimeError(
            "Ledger quorum unavailable: "
            "replicas do not agree on the previous hash."
        )

    # --------------------------------------------------------
    # Determine next index
    # --------------------------------------------------------

    indexes = [
        len(entries)
        for entries in node_entries.values()
    ]

    index = max(indexes) if indexes else 0

    # --------------------------------------------------------
    # Create canonical entry
    # --------------------------------------------------------

    entry = _create_entry(
        index=index,
        previous_hash=quorum_hash,
        event=event,
    )

    # --------------------------------------------------------
    # Replicate
    # --------------------------------------------------------

    successful_nodes = 0

    for node_id in NODE_IDS:

        entries = node_entries[node_id]

        node_previous_hash = (
            entries[-1]["current_hash"]
            if entries
            else "GENESIS"
        )

        # Do not overwrite divergent node.
        if node_previous_hash != quorum_hash:
            continue

        # Node must be at expected height.
        if len(entries) != index:
            continue

        entries.append(entry)

        _write_node(
            node_id,
            entries,
        )

        successful_nodes += 1

    # --------------------------------------------------------
    # Quorum requirement
    # --------------------------------------------------------

    if successful_nodes < QUORUM:

        raise RuntimeError(
            "Ledger quorum write failed: "
            f"{successful_nodes}/{len(NODE_IDS)} "
            "nodes accepted entry."
        )

    return entry


# ============================================================
# GET DISTRIBUTED LEDGER ENTRIES
# ============================================================

def get_ledger_entries():
    """
    Return the ledger entries from the distributed replicas.

    The quorum-agreed chain is returned.

    If the replicas do not currently agree, the longest
    available chain is returned for diagnostic visibility.
    """

    # --------------------------------------------------------
    # Legacy mode
    # --------------------------------------------------------

    if _using_legacy_ledger():
        return _load_legacy_ledger()

    # --------------------------------------------------------
    # Distributed mode
    # --------------------------------------------------------

    _ensure_ledger_directory()

    node_entries = {
        node_id: _load_node(node_id)
        for node_id in NODE_IDS
    }

    chains = list(
        node_entries.values()
    )

    if not chains:
        return []

    # --------------------------------------------------------
    # Count identical chains
    # --------------------------------------------------------

    chain_counts = {}

    for chain in chains:

        key = _canonical_json(
            chain
        )

        chain_counts[key] = (
            chain_counts.get(key, 0) + 1
        )

    # --------------------------------------------------------
    # Return quorum-agreed chain
    # --------------------------------------------------------

    for chain in chains:

        key = _canonical_json(
            chain
        )

        if chain_counts.get(key, 0) >= QUORUM:
            return chain

    # --------------------------------------------------------
    # No quorum agreement.
    #
    # Return longest chain for diagnostic visibility.
    # --------------------------------------------------------

    return max(
        chains,
        key=len,
        default=[],
    )


# ============================================================
# VERIFY ONE NODE
# ============================================================

def _verify_node(node_id: str) -> bool:
    """
    Verify an entire distributed ledger replica.
    """

    path = _node_file(node_id)

    # A missing node is treated as unavailable rather
    # than automatically making quorum invalid.
    if not path.exists():
        return True

    try:

        entries = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return False

    if not isinstance(entries, list):
        return False

    previous_hash = "GENESIS"

    for index, entry in enumerate(entries):

        if not isinstance(entry, dict):
            return False

        if entry.get("index") != index:
            return False

        if entry.get("previous_hash") != previous_hash:
            return False

        if "event" not in entry:
            return False

        stored_hash = entry.get(
            "current_hash"
        )

        if not stored_hash:
            return False

        entry_without_hash = {
            "index": entry["index"],
            "previous_hash": entry["previous_hash"],
            "event": entry["event"],
        }

        calculated_hash = _entry_hash(
            entry_without_hash
        )

        if stored_hash != calculated_hash:
            return False

        previous_hash = stored_hash

    return True


# ============================================================
# VERIFY COMPLETE LEDGER
# ============================================================

def verify_ledger() -> bool:
    """
    Verify the complete ledger.

    Distributed mode requires:
        - at least 2 valid nodes
        - valid nodes agreeing on the same chain

    Legacy mode verifies the temporary single-file ledger.
    """

    # --------------------------------------------------------
    # Legacy compatibility
    # --------------------------------------------------------

    if _using_legacy_ledger():
        return _verify_legacy_ledger()

    # --------------------------------------------------------
    # Distributed mode
    # --------------------------------------------------------

    _ensure_ledger_directory()

    valid_nodes = []

    for node_id in NODE_IDS:

        if _verify_node(node_id):
            valid_nodes.append(
                node_id
            )

    if len(valid_nodes) < QUORUM:
        return False

    # --------------------------------------------------------
    # Compare valid chains
    # --------------------------------------------------------

    chains = [
        _load_node(node_id)
        for node_id in valid_nodes
    ]

    reference_chain = chains[0]

    agreeing_nodes = sum(
        1
        for chain in chains
        if chain == reference_chain
    )

    return agreeing_nodes >= QUORUM


# ============================================================
# LEDGER STATUS
# ============================================================

def get_ledger_status():
    """
    Return diagnostic information for all ledger replicas.
    """

    # --------------------------------------------------------
    # Legacy mode
    # --------------------------------------------------------

    if _using_legacy_ledger():

        entries = _load_legacy_ledger()

        last_hash = (
            entries[-1]["current_hash"]
            if entries
            else "GENESIS"
        )

        valid = _verify_legacy_ledger()

        return {
            "legacy": {
                "entries": len(entries),
                "valid": valid,
                "last_hash": last_hash,
            },
            "quorum": {
                "required": 1,
                "valid_nodes": 1 if valid else 0,
                "available": valid,
            },
        }

    # --------------------------------------------------------
    # Distributed mode
    # --------------------------------------------------------

    _ensure_ledger_directory()

    status = {}

    for node_id in NODE_IDS:

        entries = _load_node(node_id)

        status[node_id] = {
            "entries": len(entries),
            "valid": _verify_node(
                node_id
            ),
            "last_hash": (
                entries[-1]["current_hash"]
                if entries
                else "GENESIS"
            ),
        }

    valid_count = sum(
        1
        for value in status.values()
        if value["valid"]
    )

    status["quorum"] = {
        "required": QUORUM,
        "valid_nodes": valid_count,
        "available": valid_count >= QUORUM,
    }

    return status