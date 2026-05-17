from __future__ import annotations

import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
ET.register_namespace("w", NS["w"])


def wtag(name: str) -> str:
    return f"{{{NS['w']}}}{name}"


def set_border(parent: ET.Element, name: str, val: str, size: str = "8") -> None:
    existing = parent.find(f"w:{name}", NS)
    if existing is not None:
        parent.remove(existing)
    attrs = {wtag("val"): val}
    if val != "nil":
        attrs.update({wtag("sz"): size, wtag("space"): "0", wtag("color"): "000000"})
    ET.SubElement(parent, wtag(name), attrs)


def tc_borders(tc: ET.Element) -> ET.Element:
    tcpr = tc.find("w:tcPr", NS)
    if tcpr is None:
        tcpr = ET.Element(wtag("tcPr"))
        tc.insert(0, tcpr)
    borders = tcpr.find("w:tcBorders", NS)
    if borders is None:
        borders = ET.SubElement(tcpr, wtag("tcBorders"))
    return borders


def clear_cell_borders(tc: ET.Element) -> ET.Element:
    borders = tc_borders(tc)
    for child in list(borders):
        borders.remove(child)
    for name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        set_border(borders, name, "nil")
    return borders


def format_table(tbl: ET.Element) -> None:
    tblpr = tbl.find("w:tblPr", NS)
    if tblpr is None:
        tblpr = ET.Element(wtag("tblPr"))
        tbl.insert(0, tblpr)
    tbl_borders = tblpr.find("w:tblBorders", NS)
    if tbl_borders is None:
        tbl_borders = ET.SubElement(tblpr, wtag("tblBorders"))
    for child in list(tbl_borders):
        tbl_borders.remove(child)
    for name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        set_border(tbl_borders, name, "nil")

    rows = tbl.findall("w:tr", NS)
    if not rows:
        return

    for row in rows:
        for tc in row.findall("w:tc", NS):
            clear_cell_borders(tc)

    for tc in rows[0].findall("w:tc", NS):
        borders = tc_borders(tc)
        set_border(borders, "top", "single", "12")
        set_border(borders, "bottom", "single", "8")

    for tc in rows[-1].findall("w:tc", NS):
        borders = tc_borders(tc)
        set_border(borders, "bottom", "single", "12")


def process_docx(docx: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        with zipfile.ZipFile(docx) as zf:
            zf.extractall(tmpdir)
        document = tmpdir / "word" / "document.xml"
        tree = ET.parse(document)
        root = tree.getroot()
        tables = root.findall(".//w:tbl", NS)
        for tbl in tables:
            format_table(tbl)
        tree.write(document, encoding="utf-8", xml_declaration=True)

        backup = docx.with_suffix(".docx.bak")
        shutil.copy2(docx, backup)
        with zipfile.ZipFile(docx, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in tmpdir.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(tmpdir).as_posix())
        backup.unlink(missing_ok=True)
        print(f"Formatted {len(tables)} table(s) as three-line tables in {docx}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: format_docx_three_line_tables.py <docx>")
    process_docx(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
