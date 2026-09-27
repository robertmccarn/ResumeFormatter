from pathlib import Path

from resume_formatter.validator import ValidationResult, find_pagination_engine, validate_docx

def test_missing_document_is_invalid(tmp_path: Path):
    result = validate_docx(tmp_path / 'missing.docx')
    assert result.available is False
    assert result.valid is False
    assert result.page_count is None
    assert result.issues

def test_find_pagination_engine_returns_path_or_none(monkeypatch):
    monkeypatch.setattr('resume_formatter.validator.shutil.which', lambda name: '/fake/engine' if name == 'soffice' else None)
    assert find_pagination_engine() == '/fake/engine'

def test_validate_without_engine_is_explicitly_unavailable(tmp_path: Path, monkeypatch):
    document = tmp_path / 'resume.docx'
    document.write_bytes(b'not really a docx')
    monkeypatch.setattr('resume_formatter.validator.find_pagination_engine', lambda: None)
    result = validate_docx(document)
    assert result.available is False
    assert result.valid is False
    assert result.page_count is None
    assert 'No supported pagination engine' in result.issues[0]

def test_validation_result_is_immutable():
    result = ValidationResult(True, True, 2, 2)
    try:
        result.valid = False
    except AttributeError:
        pass
    else:
        raise AssertionError('ValidationResult should be immutable.')

def test_page_count_parser_counts_page_objects(tmp_path: Path):
    from resume_formatter.validator import _pdf_page_count
    pdf = tmp_path / 'resume.pdf'
    pdf.write_bytes(b'1 0 obj << /Type /Page >> endobj 2 0 obj << /Type /Page >> endobj 3 0 obj << /Type /Pages >> endobj')
    assert _pdf_page_count(pdf) == 2
