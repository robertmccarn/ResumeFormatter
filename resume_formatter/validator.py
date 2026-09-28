from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from docx import Document

try:
    import win32com.client
except ImportError:  # pragma: no cover - exercised by environments without pywin32
    win32com = None
else:
    win32com = win32com.client


@dataclass(frozen=True)
class ValidationResult:
    available: bool
    valid: bool
    page_count: int | None
    experience_page: int | None
    issues: tuple[str, ...] = ()
    engine: str | None = None


def find_pagination_engine() -> str | None:
    if win32com is not None and shutil.which("WINWORD.EXE"):
        return "word"
    return shutil.which("soffice") or shutil.which("libreoffice")


def _pdf_page_count(pdf_path: Path) -> int:
    data = pdf_path.read_bytes()
    return len(re.findall(rb"/Type\s*/Page\b", data))


def _convert_to_pdf(docx_path: Path, output_dir: Path, engine: str) -> Path:
    completed = subprocess.run(
        [
            engine,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(docx_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(
            f"Pagination engine failed with exit code {completed.returncode}: {detail}"
        )
    pdf_path = output_dir / f"{docx_path.stem}.pdf"
    if not pdf_path.exists():
        raise RuntimeError("Pagination engine completed without producing a PDF.")
    return pdf_path


def _word_page_count(docx_path: Path) -> int:
    if win32com is None:
        raise RuntimeError("Microsoft Word validation requires pywin32.")

    word = None
    document = None
    try:
        word = win32com.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(
            str(docx_path.resolve()),
            ReadOnly=True,
            AddToRecentFiles=False,
        )
        document.Repaginate()

        # wdStatisticPages = 2.
        return int(document.ComputeStatistics(2))
    except Exception as exc:
        raise RuntimeError(f"Microsoft Word pagination failed: {exc}") from exc
    finally:
        if document is not None:
            try:
                document.Close(False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass


def _has_page_break_before_experience(docx_path: Path) -> bool:
    document = Document(docx_path)
    body_xml = document._element.body.xml
    page_break = body_xml.find('w:type="page"')
    experience = body_xml.find("PROFESSIONAL EXPERIENCE")
    return page_break != -1 and experience != -1 and page_break < experience


def validate_docx(
    docx_path: str | Path,
    *,
    max_pages: int = 2,
    experience_starts_page: int = 2,
    engine: str | None = None,
) -> ValidationResult:
    path = Path(docx_path)
    if not path.exists():
        return ValidationResult(
            False,
            False,
            None,
            None,
            (f"Document does not exist: {path}",),
        )

    selected_engine = engine or find_pagination_engine()
    if not selected_engine:
        return ValidationResult(
            False,
            False,
            None,
            None,
            (
                "No supported pagination engine was found. "
                "Install Microsoft Word or LibreOffice to enable actual DOCX pagination validation.",
            ),
        )

    try:
        if selected_engine == "word":
            page_count = _word_page_count(path)
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                pdf_path = _convert_to_pdf(
                    path,
                    Path(temp_dir),
                    selected_engine,
                )
                page_count = _pdf_page_count(pdf_path)
    except (OSError, RuntimeError) as exc:
        return ValidationResult(
            True,
            False,
            None,
            None,
            (str(exc),),
            selected_engine,
        )

    issues = []
    if page_count > max_pages:
        issues.append(
            f"Rendered document has {page_count} pages; maximum is {max_pages}."
        )

    page_break_ok = _has_page_break_before_experience(path)
    experience_page = (
        experience_starts_page
        if page_break_ok and page_count >= experience_starts_page
        else None
    )

    if not page_break_ok:
        issues.append(
            "Professional Experience does not have the required page break before it."
        )
    elif page_count < experience_starts_page:
        issues.append(
            f"Rendered document has only {page_count} page(s); "
            f"Professional Experience cannot start on page {experience_starts_page}."
        )

    return ValidationResult(
        True,
        not issues,
        page_count,
        experience_page,
        tuple(issues),
        selected_engine,
    )
