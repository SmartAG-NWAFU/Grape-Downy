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
}
ET.register_namespace("w", NS["w"])


def wtag(name: str) -> str:
    return f"{{{NS['w']}}}{name}"


def paragraph_text(p: ET.Element) -> str:
    return "".join(t.text or "" for t in p.findall(".//w:t", NS))


def run(text: str, hyperlink: bool = False) -> ET.Element:
    r = ET.Element(wtag("r"))
    rpr = ET.SubElement(r, wtag("rPr"))
    if hyperlink:
        ET.SubElement(rpr, wtag("rStyle"), {wtag("val"): "Hyperlink"})
        ET.SubElement(rpr, wtag("color"), {wtag("val"): "0563C1"})
        ET.SubElement(rpr, wtag("u"), {wtag("val"): "single"})
    t = ET.SubElement(r, wtag("t"))
    if text.startswith(" ") or text.endswith(" "):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    return r


def hyperlink(text: str, anchor: str) -> ET.Element:
    h = ET.Element(wtag("hyperlink"), {wtag("anchor"): anchor, wtag("history"): "1"})
    h.append(run(text, hyperlink=True))
    return h


def first_ref_number(label: str) -> str | None:
    match = re.search(r"\d+", label)
    return match.group(0) if match else None


def add_bookmark(p: ET.Element, name: str, bookmark_id: int) -> int:
    children = list(p)
    insert_at = 1 if children and children[0].tag == wtag("pPr") else 0
    start = ET.Element(wtag("bookmarkStart"), {wtag("id"): str(bookmark_id), wtag("name"): name})
    end = ET.Element(wtag("bookmarkEnd"), {wtag("id"): str(bookmark_id)})
    p.insert(insert_at, start)
    p.append(end)
    return bookmark_id + 1


def replace_paragraph_with_links(p: ET.Element, text: str) -> None:
    ppr = p.find("w:pPr", NS)
    for child in list(p):
        if child is not ppr:
            p.remove(child)

    pattern = re.compile(r"(\[[0-9,\-\s]+\]|Fig\. ?\d+|Table\. ?\d+)")
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            p.append(run(text[pos : match.start()]))
        token = match.group(0)
        anchor = None
        if token.startswith("["):
            n = first_ref_number(token)
            if n:
                anchor = f"ref_{n}"
        elif token.startswith("Fig."):
            n = first_ref_number(token)
            if n:
                anchor = f"fig_{n}"
        elif token.startswith("Table."):
            n = first_ref_number(token)
            if n:
                anchor = f"table_{n}"
        p.append(hyperlink(token, anchor) if anchor else run(token))
        pos = match.end()
    if pos < len(text):
        p.append(run(text[pos:]))


def process_docx(docx: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        with zipfile.ZipFile(docx) as zf:
            zf.extractall(tmpdir)

        document = tmpdir / "word" / "document.xml"
        tree = ET.parse(document)
        root = tree.getroot()
        paragraphs = root.findall(".//w:p", NS)

        bookmark_id = 1000
        in_references = False
        caption_paragraphs: set[int] = set()
        reference_paragraphs: set[int] = set()

        for p in paragraphs:
            text = paragraph_text(p).strip()
            if text == "References":
                in_references = True
                continue
            ref_match = re.match(r"^\[(\d+)\]", text)
            fig_match = re.match(r"^Fig\. ?(\d+)\.", text)
            table_match = re.match(r"^Table\. ?(\d+)", text)
            if in_references and ref_match:
                bookmark_id = add_bookmark(p, f"ref_{ref_match.group(1)}", bookmark_id)
                reference_paragraphs.add(id(p))
            elif fig_match:
                bookmark_id = add_bookmark(p, f"fig_{fig_match.group(1)}", bookmark_id)
                caption_paragraphs.add(id(p))
            elif table_match:
                bookmark_id = add_bookmark(p, f"table_{table_match.group(1)}", bookmark_id)
                caption_paragraphs.add(id(p))

        for p in paragraphs:
            if id(p) in caption_paragraphs or id(p) in reference_paragraphs:
                continue
            text = paragraph_text(p)
            if not text or not re.search(r"\[[0-9,\-\s]+\]|Fig\. ?\d+|Table\. ?\d+", text):
                continue
            if p.findall(".//w:drawing", NS):
                continue
            replace_paragraph_with_links(p, text)

        tree.write(document, encoding="utf-8", xml_declaration=True)

        backup = docx.with_suffix(".docx.bak")
        shutil.copy2(docx, backup)
        with zipfile.ZipFile(docx, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in tmpdir.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(tmpdir).as_posix())
        backup.unlink(missing_ok=True)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: postprocess_dsll_docx_links.py <docx>")
    process_docx(Path(sys.argv[1]))
    print(f"Postprocessed links in {sys.argv[1]}")


if __name__ == "__main__":
    main()
