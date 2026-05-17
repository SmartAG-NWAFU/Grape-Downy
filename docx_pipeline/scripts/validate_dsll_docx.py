from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def paragraph_text(p: ET.Element) -> str:
    return "".join(t.text or "" for t in p.findall(".//w:t", NS))


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_dsll_docx.py <docx>")
    docx = Path(sys.argv[1])
    if not docx.exists():
        raise SystemExit(f"missing docx: {docx}")

    with zipfile.ZipFile(docx) as zf:
        names = set(zf.namelist())
        document_xml = zf.read("word/document.xml")
        media = [name for name in names if name.startswith("word/media/")]

    root = ET.fromstring(document_xml)
    paragraphs = [paragraph_text(p) for p in root.findall(".//w:p", NS)]
    text = "\n".join(paragraphs)

    required = [
        "Abstract",
        "Introduction",
        "Conclusion",
        "Data and code availability",
        "References",
        "Fig. 1.",
        "Fig. 10.",
        "Table. 1",
        "[1]",
        "[47]",
        "(1)",
        "(9)",
        "https://github.com/SmartAG-NWAFU/Grape-Downy",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit("Missing expected DOCX text: " + ", ".join(missing))

    refs = re.findall(r"\[\d+\]", text)
    if len(set(refs)) < 40:
        raise SystemExit(f"Too few reference labels found: {len(set(refs))}")
    if len(media) < 10:
        raise SystemExit(f"Expected at least 10 embedded media files, found {len(media)}")

    print(f"Validated {docx}")
    print(f"Paragraphs: {len(paragraphs)}")
    print(f"Reference labels: {len(set(refs))}")
    print(f"Embedded media: {len(media)}")


if __name__ == "__main__":
    main()
