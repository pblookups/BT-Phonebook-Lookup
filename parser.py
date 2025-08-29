#!/usr/bin/env python3
"""
parser.py (Render-friendly)

Pure functions to:
- extract text from PDF bytes (no filesystem, no external binaries)
- parse text into individual records (same phone-delimited approach you used)
- map free-text records into structured fields for DB indexing
"""

from __future__ import annotations
import io
import re
from typing import List, Dict, Optional
from PyPDF2 import PdfReader

# Liberal UK phone pattern; keeps your original behavior but tolerates variants
PHONE_RE = re.compile(
    r"""
    (?:\(\s*0\d{1,4}\s*\)|0\d{2,4})        # area code: (01202) or 0207/0121 etc.
    [\s\-]*\d(?:[\d\s\-]){5,9}             # subscriber part, 6–10 digits total
    """,
    re.VERBOSE,
)

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text from an in-memory PDF using PyPDF2."""
    text_chunks: List[str] = []
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text:
                text_chunks.append(page_text)
    except Exception:
        # You can add logging here if desired
        pass
    return "\n".join(text_chunks).strip()

def parse_records(text: str) -> List[str]:
    """
    Your original logic: accumulate lines until a line contains a phone number,
    then yield the accumulated record.
    """
    records: List[str] = []
    current_record = ""
    boundary_phone_pattern = re.compile(r'\(\d+\)\s*\d+')

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        current_record = f"{current_record} {line}".strip() if current_record else line
        if boundary_phone_pattern.search(line):
            records.append(current_record)
            current_record = ""
    if current_record:
        records.append(current_record)
    return records

def _explode_record(record_text: str) -> Dict[str, Optional[str]]:
    """
    Heuristic splitter to derive (name, address, phone) from a record blob.
    """
    m = PHONE_RE.search(record_text)
    phone = m.group(0) if m else None
    prefix = record_text[:m.start()].strip() if m else record_text.strip()

    name, address = None, None
    if "," in prefix:
        name, address = prefix.split(",", 1)
    else:
        name = prefix

    def clean(s: Optional[str]) -> Optional[str]:
        return s.strip() if s else None

    return {
        "name": clean(name),
        "address": clean(address),
        "phone": clean(phone),
        "raw_text": record_text.strip()
    }

def records_from_pdf_bytes(pdf_bytes: bytes) -> List[Dict[str, Optional[str]]]:
    """extract text -> parse into record strings -> map to dicts"""
    text = extract_text_from_pdf_bytes(pdf_bytes)
    if not text:
        return []
    blobs = parse_records(text)
    return [_explode_record(b) for b in blobs]
