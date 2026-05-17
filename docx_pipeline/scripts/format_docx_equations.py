from __future__ import annotations

import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}
ET.register_namespace("w", NS["w"])
ET.register_namespace("m", NS["m"])


def wtag(name: str) -> str:
    return f"{{{NS['w']}}}{name}"


def paragraph_text(p: ET.Element) -> str:
    return "".join(t.text or "" for t in p.findall(".//w:t", NS))


def make_tab_run() -> ET.Element:
    r = ET.Element(wtag("r"))
    ET.SubElement(r, wtag("tab"))
    return r


def ensure_ppr(p: ET.Element) -> ET.Element:
    ppr = p.find("w:pPr", NS)
    if ppr is None:
        ppr = ET.Element(wtag("pPr"))
        p.insert(0, ppr)
    return ppr


def format_equation_paragraph(p: ET.Element) -> bool:
    if not (p.findall(".//m:oMath", NS) or p.findall(".//m:oMathPara", NS)):
        return False
    label = paragraph_text(p).strip()
    if not re.fullmatch(r"\([1-9]\)", label):
        return False

    ppr = ensure_ppr(p)
    jc = ppr.find("w:jc", NS)
    if jc is not None:
        ppr.remove(jc)

    tabs = ppr.find("w:tabs", NS)
    if tabs is not None:
        ppr.remove(tabs)
    tabs = ET.SubElement(ppr, wtag("tabs"))
    ET.SubElement(tabs, wtag("tab"), {wtag("val"): "center", wtag("pos"): "4680"})
    ET.SubElement(tabs, wtag("tab"), {wtag("val"): "right", wtag("pos"): "9360"})

    children = list(p)
    start = 1 if children and children[0].tag == wtag("pPr") else 0
    if len(children) <= start or children[start].find("w:tab", NS) is None:
        p.insert(start, make_tab_run())

    label_child = None
    for child in list(p):
        if child.tag == wtag("r") and paragraph_text(child).strip() == label:
            label_child = child
            break
    if label_child is None:
        return True

    idx = list(p).index(label_child)
    previous = list(p)[idx - 1] if idx > 0 else None
    if previous is None or previous.find("w:tab", NS) is None:
        p.insert(idx, make_tab_run())
    return True


def process_docx(docx: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        with zipfile.ZipFile(docx) as zf:
            zf.extractall(tmpdir)

        document = tmpdir / "word" / "document.xml"
        tree = ET.parse(document)
        root = tree.getroot()
        count = 0
        for p in root.findall(".//w:p", NS):
            if format_equation_paragraph(p):
                count += 1
        tree.write(document, encoding="utf-8", xml_declaration=True)

        backup = docx.with_suffix(".docx.bak")
        shutil.copy2(docx, backup)
        with zipfile.ZipFile(docx, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in tmpdir.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(tmpdir).as_posix())
        backup.unlink(missing_ok=True)
        print(f"Formatted {count} equation paragraph(s) in {docx}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: format_docx_equations.py <docx>")
    process_docx(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
