from pathlib import Path

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


def test_word_page_count_uses_word_com(monkeypatch, tmp_path: Path):
    class FakeDocument:
        def __init__(self):
            self.closed = False
            self.repaginate_called = False

        def Repaginate(self):
            self.repaginate_called = True

        def ComputeStatistics(self, stat):
            assert stat == 2
            return 2

        def Close(self, save_changes=False):
            self.closed = True

    class FakeDocuments:
        def __init__(self, document):
            self.document = document

        def Open(self, *args, **kwargs):
            return self.document

    class FakeWord:
        def __init__(self, document):
            self.Documents = FakeDocuments(document)
            self.Visible = None
            self.DisplayAlerts = None
            self.quit_called = False

        def Quit(self):
            self.quit_called = True

    document = FakeDocument()
    word = FakeWord(document)

    class FakeClient:
        def DispatchEx(self, name):
            assert name == "Word.Application"
            return word

    monkeypatch.setattr("resume_formatter.validator.win32com", FakeClient())

    from resume_formatter.validator import _word_page_count

    path = tmp_path / "resume.docx"
    path.write_bytes(b"placeholder")

    assert _word_page_count(path) == 2
    assert document.repaginate_called is True
    assert document.closed is True
    assert word.quit_called is True


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
