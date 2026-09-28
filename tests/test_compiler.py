from pathlib import Path

from resume_formatter.compiler import compile_resume
from resume_formatter.optimizer import NORMAL_PROFILE
from resume_formatter.validator import ValidationResult


def sample_text() -> str:
    return """Robert McCarn
robert@example.com | 555-555-5555 | Spring, TX
Data Engineer
Summary
Data Engineer with experience building data solutions.
Core Skills
Databases: SQL Server, Azure SQL
Education
University of Houston | BBA, Management Information Systems | 2021
Professional Experience
TEKsystems Global Services | Data Engineer | 2022-Present
- Developed T-SQL stored procedures.
- Supported data modernization initiatives.
- Improved query performance.
"""


def test_compile_resume_parses_and_writes_document(tmp_path: Path, monkeypatch):
    output = tmp_path / "resume.docx"

    monkeypatch.setattr(
        "resume_formatter.compiler.validate_docx",
        lambda *args, **kwargs: ValidationResult(
            available=True,
            valid=True,
            page_count=2,
            experience_page=2,
        ),
    )

    result = compile_resume(sample_text(), output)

    assert result.success is True
    assert result.output_path == output
    assert output.exists()
    assert result.resume.contact.name == "Robert McCarn"
    assert result.audit.actual_validation.valid is True


def test_compile_resume_fails_structural_validation(tmp_path: Path):
    text = """Robert McCarn
robert@example.com | 555-555-5555 | Spring, TX
Data Engineer
Summary
Data Engineer with experience building data solutions.
Education
University of Houston | BBA, Management Information Systems | 2021
"""

    result = compile_resume(text, tmp_path / "resume.docx")

    assert result.success is False
    assert result.output_path is None
    assert result.audit.structural_errors


def test_compile_resume_can_report_unavailable_pagination(
    tmp_path: Path,
    monkeypatch,
):
    output = tmp_path / "resume.docx"

    monkeypatch.setattr(
        "resume_formatter.compiler.validate_docx",
        lambda *args, **kwargs: ValidationResult(
            available=False,
            valid=False,
            page_count=None,
            experience_page=None,
            issues=("pagination unavailable",),
        ),
    )

    result = compile_resume(sample_text(), output)

    assert result.success is False
    assert output.exists()
    assert result.audit.actual_validation.available is False
    assert "pagination unavailable" in result.audit.actual_validation.issues


def test_compile_resume_preserves_resume_content(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "resume_formatter.compiler.validate_docx",
        lambda *args, **kwargs: ValidationResult(
            available=True,
            valid=True,
            page_count=2,
            experience_page=2,
        ),
    )

    result = compile_resume(sample_text(), tmp_path / "resume.docx")

    assert result.resume.summary == (
        "Data Engineer with experience building data solutions."
    )
    assert [bullet.text for bullet in result.resume.experience[0].bullets] == [
        "Developed T-SQL stored procedures.",
        "Supported data modernization initiatives.",
        "Improved query performance.",
    ]


def test_compilation_result_keeps_selected_profile(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "resume_formatter.compiler.validate_docx",
        lambda *args, **kwargs: ValidationResult(
            available=True,
            valid=True,
            page_count=2,
            experience_page=2,
        ),
    )

    result = compile_resume(sample_text(), tmp_path / "resume.docx")

    assert result.audit.profile == NORMAL_PROFILE
