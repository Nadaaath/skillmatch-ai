from pathlib import Path
import fitz

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_upload_file(upload_file, destination: Path) -> Path:
    with destination.open("wb") as buffer:
        buffer.write(upload_file.file.read())
    return destination

def extract_text_from_pdf(file_path: Path) -> str:
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()
