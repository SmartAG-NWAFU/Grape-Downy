from __future__ import annotations

import re
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


def paragraph_text(p: ET.Element) -> str:
    return "".join(t.text or "" for t in p.findall(".//w:t", NS))


def make_text_run(text: str) -> ET.Element:
    r = ET.Element(wtag("r"))
    t = ET.SubElement(r, wtag("t"))
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    return r


def payload(p: ET.Element) -> list[ET.Element]:
    return [child for child in list(p) if child.tag != wtag("pPr")]


def insert_after_ppr(p: ET.Element, elements: list[ET.Element]) -> None:
    idx = 1 if len(p) and p[0].tag == wtag("pPr") else 0
    for element in reversed(elements):
        p.insert(idx, element)


def parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def fix_document(docx: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        with zipfile.ZipFile(docx) as zf:
            zf.extractall(tmpdir)

        document = tmpdir / "word" / "document.xml"
        tree = ET.parse(document)
        root = tree.getroot()
        body = root.find(".//w:body", NS)
        if body is None:
            raise SystemExit("word/document.xml has no body")

        changed = 0
        paras = [child for child in list(body) if child.tag == wtag("p")]

        # Merge standalone equation labels, e.g. "(1)", into the preceding
        # display-equation paragraph.
        for p in list(paras):
            text = paragraph_text(p).strip()
            if not re.fullmatch(r"\([1-9]\)", text):
                continue
            idx = list(body).index(p)
            prev = None
            for candidate in reversed(list(body)[:idx]):
                if candidate.tag == wtag("p"):
                    prev = candidate
                    break
            if prev is None:
                continue
            for child in payload(p):
                p.remove(child)
                prev.append(child)
            body.remove(p)
            changed += 1

        # Refresh paragraph list after equation-label removal.
        paras = [child for child in list(body) if child.tag == wtag("p")]

        # Merge standalone reference labels, e.g. "[1]", into the following
        # reference entry paragraph so the number and entry start on one line.
        for p in list(paras):
            text = paragraph_text(p).strip()
            if not re.fullmatch(r"\[\d+\]", text):
                continue
            idx = list(body).index(p)
            nxt = None
            for candidate in list(body)[idx + 1 :]:
                if candidate.tag == wtag("p"):
                    nxt = candidate
                    break
            if nxt is None:
                continue
            moved = payload(p)
            for child in moved:
                p.remove(child)
            moved.append(make_text_run(" "))
            insert_after_ppr(nxt, moved)
            body.remove(p)
            changed += 1

        tree.write(document, encoding="utf-8", xml_declaration=True)

        backup = docx.with_suffix(".docx.bak")
        shutil.copy2(docx, backup)
        with zipfile.ZipFile(docx, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in tmpdir.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(tmpdir).as_posix())
        backup.unlink(missing_ok=True)
        print(f"Fixed {changed} standalone numbering paragraphs in {docx}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_docx_numbering_breaks.py <docx>")
    fix_document(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
