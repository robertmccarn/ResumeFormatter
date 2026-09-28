from pathlib import Path
from types import SimpleNamespace

from resume_formatter.validator import ValidationResult, find_pagination_engine, validate_docx


def test_missing_document_is_invalid(tmp_path: Path):
    result = validate_docx(tmp_path / "missing.docx")
    assert result.available is False
    assert result.valid is False
    assert result.page_count is None
    assert result.issues


def test_find_pagination_engine_prefers_word(monkeypatch):
    monkeypatch.setattr(
        "resume_formatter.validator._word_is_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "resume_formatter.validator.shutil.which",
        lambda name: "/fake/libreoffice",
    )
    assert find_pagination_engine() == "word"


def test_find_pagination_engine_falls_back_to_soffice(monkeypatch):
    monkeypatch.setattr(
        "resume_formatter.validator._word_is_available",
        lambda: False,
    )
    monkeypatch.setattr(
        "resume_formatter.validator.shutil.which",
        lambda name: "/fake/engine" if name == "soffice" else None,
    )
    assert find_pagination_engine() == "/fake/engine"


def test_validate_without_engine_is_explicitly_unavailable(tmp_path: Path, monkeypatch):
    document = tmp_path / "resume.docx"
    document.write_bytes(b"not really a docx")
    monkeypatch.setattr("resume_formatter.validator.find_pagination_engine", lambda: None)
    result = validate_docx(document)
    assert result.available is False
    assert result.valid is False
    assert result.page_count is None
    assert "No supported pagination engine" in result.issues[0]


def test_word_page_count_uses_worker_process(monkeypatch, tmp_path: Path):
    from resume_formatter.validator import _word_page_count

    path = tmp_path / "resume.docx"
    path.write_bytes(b"placeholder")

    completed = SimpleNamespace(
        returncode=0,
        stdout="2\n",
        stderr="",
    )

    def fake_run(command, **kwargs):
        assert command[0].endswith("python.exe")
        assert command[1:3] == ["-m", "resume_formatter.word_pagination"]
        assert command[3] == str(path)
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["check"] is False
        return completed

    monkeypatch.setattr("resume_formatter.validator.subprocess.run", fake_run)
    monkeypatch.setattr(
        "resume_formatter.validator.win32com",
        object(),
    )

    assert _word_page_count(path) == 2


def test_word_page_count_reports_worker_failure(monkeypatch, tmp_path: Path):
    from resume_formatter.validator import _word_page_count

    path = tmp_path / "resume.docx"
    path.write_bytes(b"placeholder")

    monkeypatch.setattr(
        "resume_formatter.validator.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="Microsoft Word pagination failed: RPC unavailable",
        ),
    )
    monkeypatch.setattr(
        "resume_formatter.validator.win32com",
        object(),
    )

    try:
        _word_page_count(path)
    except RuntimeError as exc:
        assert "RPC unavailable" in str(exc)
    else:
        raise AssertionError("Expected Word worker failure to raise RuntimeError.")


def test_validation_result_is_immutable():
    result = ValidationResult(True, True, 2, 2)
    try:
        result.valid = False
    except AttributeError:
        pass
    else:
        raise AssertionError("ValidationResult should be immutable.")


def test_page_count_parser_counts_page_objects(tmp_path: Path):
    from resume_formatter.validator import _pdf_page_count

    pdf = tmp_path / "resume.pdf"
    pdf.write_bytes(
        b"1 0 obj << /Type /Page >> endobj "
        b"2 0 obj << /Type /Page >> endobj "
        b"3 0 obj << /Type /Pages >> endobj"
    )
    assert _pdf_page_count(pdf) == 2
