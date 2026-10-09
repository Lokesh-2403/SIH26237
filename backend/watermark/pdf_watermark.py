import hashlib
import hmac
import os
import re
import struct
from pathlib import Path

import fitz


MAGIC = b"SIH26237WM"
VERSION = b"01"
SECRET_FILE = Path("backend/watermark/watermark_secret.key")

PAYLOAD_BYTES = 64

XMP_NAMESPACE = "http://sih26237.local/ns/watermark/1.0/"
XMP_PREFIX = "sih"


def _get_secret():
    SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not SECRET_FILE.exists():
        SECRET_FILE.write_bytes(os.urandom(32))

    return SECRET_FILE.read_bytes()


def generate_watermark_id(document_id, recipient_id, session_id):
    secret = _get_secret()

    message = (
        f"{document_id}|"
        f"{recipient_id}|"
        f"{session_id}"
    ).encode("utf-8")

    digest = hmac.new(
        secret,
        message,
        hashlib.sha256
    ).hexdigest().upper()

    return f"WM-{digest[:24]}"


def _build_payload(watermark_id):
    watermark_bytes = watermark_id.encode("utf-8")

    payload = (
        MAGIC +
        VERSION +
        struct.pack(">H", len(watermark_bytes)) +
        watermark_bytes
    )

    if len(payload) > PAYLOAD_BYTES:
        raise ValueError(
            f"Watermark payload too large: "
            f"{len(payload)} bytes > {PAYLOAD_BYTES}"
        )

    return payload.ljust(PAYLOAD_BYTES, b"\x00")


def _parse_payload(payload):
    if not payload:
        return None

    minimum_size = len(MAGIC) + len(VERSION) + 2

    if len(payload) < minimum_size:
        return None

    if payload[:len(MAGIC)] != MAGIC:
        return None

    version_start = len(MAGIC)
    version_end = version_start + len(VERSION)

    if payload[version_start:version_end] != VERSION:
        return None

    length_start = version_end
    length_end = length_start + 2

    watermark_length = struct.unpack(
        ">H",
        payload[length_start:length_end]
    )[0]

    data_start = length_end
    data_end = data_start + watermark_length

    if data_end > len(payload):
        return None

    try:
        return payload[data_start:data_end].decode("utf-8")
    except UnicodeDecodeError:
        return None


def _xml_escape(value):
    return (
        value
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _create_xmp(watermark_id):
    payload = _build_payload(watermark_id)

    payload_hex = payload.hex()
    watermark_xml = _xml_escape(payload_hex)

    return f'''<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description
    rdf:about=""
    xmlns:{XMP_PREFIX}="{XMP_NAMESPACE}">
    <{XMP_PREFIX}:watermark>{watermark_xml}</{XMP_PREFIX}:watermark>
</rdf:Description>
</rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>'''


def _extract_xmp_watermark(xmp):
    if not xmp:
        return None

    pattern = (
        rf"<{re.escape(XMP_PREFIX)}:watermark>"
        r"(.*?)"
        rf"</{re.escape(XMP_PREFIX)}:watermark>"
    )

    match = re.search(
        pattern,
        xmp,
        flags=re.DOTALL
    )

    if not match:
        return None

    value = match.group(1).strip()

    value = (
        value
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
    )

    try:
        return bytes.fromhex(value)
    except ValueError:
        return None


def embed_watermark(pdf_data, watermark_id):
    """
    Embed an invisible watermark into PDF bytes.

    Compatible with the existing backend:
        embed_watermark(decrypted_data, watermark_id)

    Returns:
        bytes containing the watermarked PDF.
    """

    if not isinstance(pdf_data, (bytes, bytearray)):
        raise TypeError(
            "pdf_data must be bytes or bytearray"
        )

    xmp = _create_xmp(watermark_id)

    input_bytes = bytes(pdf_data)

    document = fitz.open(
        stream=input_bytes,
        filetype="pdf"
    )

    try:
        document.set_xml_metadata(xmp)

        output_bytes = document.tobytes(
            garbage=4,
            deflate=True,
            clean=True
        )
    finally:
        document.close()

    return output_bytes


def extract_watermark(pdf_data):
    """
    Extract the forensic watermark ID from PDF bytes.

    Returns:
        str: watermark ID when found
        None: when no valid watermark exists
    """

    if not isinstance(pdf_data, (bytes, bytearray)):
        raise TypeError(
            "pdf_data must be bytes or bytearray"
        )

    document = fitz.open(
        stream=bytes(pdf_data),
        filetype="pdf"
    )

    try:
        xmp = document.get_xml_metadata()
    finally:
        document.close()

    payload = _extract_xmp_watermark(xmp)

    if payload is None:
        return None

    return _parse_payload(payload)