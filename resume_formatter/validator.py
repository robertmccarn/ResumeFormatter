from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

@dataclass(frozen=True)
class ValidationResult:
    available: bool
    valid: bool
    page_count: int | None
    experience_page: int | None
    issues: tuple[str, ...] = ()
    engine: str | None = None

def find_pagination_engine() -> str | None:
    return shutil.which('soffice') or shutil.which('libreoffice')

def _pdf_page_count(pdf_path: Path) -> int:
    data = pdf_path.read_bytes()
    return len(re.findall(rb'/Type\\s*/Page\\b', data))

def _convert_to_pdf(docx_path: Path, output_dir: Path, engine: str) -> Path:
    completed = subprocess.run([engine, '--headless', '--convert-to', 'pdf', '--outdir', str(output_dir), str(docx_path)], capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f'Pagination engine failed with exit code {completed.returncode}: {detail}')
    pdf_path = output_dir / f'{docx_path.stem}.pdf'
    if not pdf_path.exists():
        raise RuntimeError('Pagination engine completed without producing a PDF.')
    return pdf_path

def _experience_page_from_pdf(pdf_path: Path) -> int | None:
    pdftotext = shutil.which('pdftotext')
    if not pdftotext:
        return None
    with tempfile.TemporaryDirectory() as temp_dir:
        text_path = Path(temp_dir) / 'resume.txt'
        completed = subprocess.run([pdftotext, '-layout', str(pdf_path), str(text_path)], capture_output=True, text=True, check=False)
        if completed.returncode != 0 or not text_path.exists():
            return None
        pages = text_path.read_text(encoding='utf-8', errors='replace').split('\f')
    for index, page in enumerate(pages, start=1):
        if 'PROFESSIONAL EXPERIENCE' in page.upper():
            return index
    return None

def validate_docx(docx_path: str | Path, *, max_pages: int = 2, experience_starts_page: int = 2, engine: str | None = None) -> ValidationResult:
    path = Path(docx_path)
    if not path.exists():
        return ValidationResult(False, False, None, None, (f'Document does not exist: {path}',))
    selected_engine = engine or find_pagination_engine()
    if not selected_engine:
        return ValidationResult(False, False, None, None, ('No supported pagination engine was found. Install LibreOffice to enable actual DOCX pagination validation.',))
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = _convert_to_pdf(path, Path(temp_dir), selected_engine)
            page_count = _pdf_page_count(pdf_path)
            experience_page = _experience_page_from_pdf(pdf_path)
    except (OSError, RuntimeError) as exc:
        return ValidationResult(True, False, None, None, (str(exc),), selected_engine)
    issues = []
    if page_count > max_pages:
        issues.append(f'Rendered document has {page_count} pages; maximum is {max_pages}.')
    if experience_page is None:
        issues.append('Could not verify the Professional Experience page from rendered PDF text.')
    elif experience_page != experience_starts_page:
        issues.append(f'Professional Experience rendered on page {experience_page}; expected page {experience_starts_page}.')
    return ValidationResult(True, not issues, page_count, experience_page, tuple(issues), selected_engine)
