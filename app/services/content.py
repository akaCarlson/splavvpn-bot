from pathlib import Path

def read_text_file(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8")
