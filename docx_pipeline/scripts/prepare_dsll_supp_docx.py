from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "paper" / "DSLL-Net_supporting_materials_merged.tex"
OUTPUT_DIR = ROOT / "docx_pipeline" / "output"
OUTPUT = OUTPUT_DIR / "DSLL-Net_supporting_materials_for_docx.tex"


def prefix_figure_captions(text: str) -> str:
    counter = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal counter
        counter += 1
        caption = match.group(1).strip()
        caption = re.sub(r"^Fig\.\s*S?\d+\.\s*", "", caption)
        return f"\\caption{{Fig. S{counter}. {caption}}}"

    return re.sub(r"\\caption\{(.*?)\}", repl, text, flags=re.DOTALL)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    text = SOURCE.read_text(encoding="utf-8")
    text = prefix_figure_captions(text)
    text = text.replace("\\maketitle", "")
    text = text.replace("\\clearpage", "")
    text = re.sub(r"\\label\{[^{}]+\}", "", text)
    text = re.sub(r"\[width=[^\]]+\]", "", text)
    text = re.sub(r"\$\\times\$", "x", text)
    OUTPUT.write_text(text, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
