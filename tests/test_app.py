from pathlib import Path

from app import main


def make_input(tmp_path: Path) -> Path:
    path = tmp_path / "input.txt"
    path.write_text(
        """Robert McCarn
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
""",
        encoding="utf-8",
    )
    return path


def test_main_missing_input_returns_error(capsys, tmp_path: Path):
    code = main([str(tmp_path / "missing.txt")])
    captured = capsys.readouterr()

    assert code == 2
    assert "Input file not found" in captured.err


def test_main_compiles_resume(tmp_path: Path, monkeypatch, capsys):
    input_path = make_input(tmp_path)
    output_path = tmp_path / "resume.docx"

    from resume_formatter.validator import ValidationResult

    monkeypatch.setattr(
        "resume_formatter.compiler.validate_docx",
        lambda *args, **kwargs: ValidationResult(
            available=True,
            valid=True,
            page_count=2,
            experience_page=2,
        ),
    )

    code = main([str(input_path), "-o", str(output_path)])
    captured = capsys.readouterr()

    assert code == 0
    assert output_path.exists()
    assert "Status:      SUCCESS" in captured.out
    assert "Actual:      2 pages" in captured.out


def test_main_reports_incomplete_compilation(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    input_path = make_input(tmp_path)
    output_path = tmp_path / "resume.docx"

    from resume_formatter.validator import ValidationResult

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

    code = main([str(input_path), "-o", str(output_path)])
    captured = capsys.readouterr()

    assert code == 1
    assert output_path.exists()
    assert "Status:      INCOMPLETE" in captured.out
    assert "pagination unavailable" in captured.out
