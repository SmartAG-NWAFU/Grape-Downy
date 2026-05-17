from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "paper" / "DSLL-Net_6000.tex"
OUTPUT_DIR = ROOT / "docx_pipeline" / "output"
OUTPUT = OUTPUT_DIR / "DSLL-Net_6000_for_docx.tex"


def strip_balanced_command(text: str, command: str, arg_index: int = 0) -> str:
    pattern = "\\" + command + "{"
    i = 0
    out: list[str] = []
    while i < len(text):
        start = text.find(pattern, i)
        if start == -1:
            out.append(text[i:])
            break
        out.append(text[i:start])
        pos = start + len(pattern) - 1
        args: list[str] = []
        ok = True
        for _ in range(arg_index + 1):
            if pos >= len(text) or text[pos] != "{":
                ok = False
                break
            depth = 0
            arg_start = pos + 1
            while pos < len(text):
                ch = text[pos]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        args.append(text[arg_start:pos])
                        pos += 1
                        break
                pos += 1
            else:
                ok = False
                break
        if ok:
            out.append(args[arg_index])
            i = pos
        else:
            out.append(text[start : start + len(pattern)])
            i = start + len(pattern)
    return "".join(out)


def replace_hyperlink(text: str) -> str:
    pattern = r"\\hyperlink\{[^{}]+\}\{"
    i = 0
    out: list[str] = []
    while i < len(text):
        match = re.search(pattern, text[i:])
        if not match:
            out.append(text[i:])
            break
        start = i + match.start()
        brace = i + match.end() - 1
        out.append(text[i:start])
        depth = 0
        arg_start = brace + 1
        pos = brace
        while pos < len(text):
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
                if depth == 0:
                    out.append(text[arg_start:pos])
                    pos += 1
                    break
            pos += 1
        i = pos
    return "".join(out)


def prepare_equations(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        tag_match = re.search(r"\\tag\{([^{}]+)\}", body)
        label = ""
        if tag_match:
            label = tag_match.group(1).strip()
            body = body[: tag_match.start()] + body[tag_match.end() :]
        body = body.strip().rstrip(".,;")
        if label:
            return "\\[\n" + body + "\n\\]\n\n" + f"({label})"
        return "\\[\n" + body + "\n\\]"

    return re.sub(
        r"\\begin\{equation\}(.*?)\\end\{equation\}",
        repl,
        text,
        flags=re.DOTALL,
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="utf-8")

    text = prepare_equations(text)

    # Remove PDF-only anchors while preserving visible content.
    text = re.sub(r"\\hypertarget\{[^{}]+\}\{\s*%\s*\n", "", text)
    text = re.sub(r"\\hypertarget\{[^{}]+\}\{\}", "", text)
    text = text.replace("}\n\\section", "\n\\section")
    text = text.replace("}\n\\subsection", "\n\\subsection")
    text = replace_hyperlink(text)
    text = strip_balanced_command(text, "textcolor", arg_index=1)
    text = re.sub(r"\\label\{[^{}]+\}", "", text)
    text = re.sub(r"\\texorpdfstring\{([^{}]*)\}\{([^{}]*)\}", r"\1", text)
    # Removing \hypertarget{...}{% leaves the closing brace after Pandoc
    # headings; strip that extra brace while preserving multiline titles.
    text = re.sub(
        r"(\\(?:sub)*section\*?\{[^{}]*(?:\n[^{}]*)*\})\}",
        r"\1",
        text,
    )

    # Word conversion should preserve visible figure/table/reference text
    # without LaTeX-only sizing and hyperlink commands.
    text = text.replace("[width=\\linewidth]", "")
    text = text.replace("\\scriptsize", "")
    text = text.replace("\\normalsize", "")
    text = re.sub(r"\\setlength\{\\tabcolsep\}\{[^{}]+\}", "", text)
    text = re.sub(r"\\hypertarget\{[^{}]+\}\{\}", "", text)

    # Section numbering should stop at the conclusion; Pandoc respects starred
    # sections for the back matter.
    text = text.replace("\\setcounter{secnumdepth}{2}", "\\setcounter{secnumdepth}{2}")

    OUTPUT.write_text(text, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
