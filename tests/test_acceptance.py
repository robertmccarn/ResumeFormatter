import os
from pathlib import Path

import pytest

from resume_formatter.compiler import compile_resume


FIXTURE = Path(__file__).parent / "fixtures" / "representative_resume.txt"


@pytest.mark.skipif(
    os.environ.get("RUN_WORD_ACCEPTANCE") != "1",
    reason="Set RUN_WORD_ACCEPTANCE=1 to run the Microsoft Word acceptance test.",
)
def test_representative_resume_compiles_with_word(tmp_path: Path):
    source = FIXTURE.read_text(encoding="utf-8")
    output = tmp_path / "representative_resume.docx"

    result = compile_resume(source, output)

    assert result.success is True
    assert result.output_path == output
    assert output.exists()
    assert result.audit.actual_validation.engine == "word"
    assert result.audit.actual_validation.page_count == 2
    assert result.audit.actual_validation.experience_page == 2
    assert result.audit.trimmed is False

    # The compiler must preserve the parsed content even when Word validates it.
    assert result.resume.summary in source
    assert all(
        bullet.text in source
        for experience in result.resume.experience
        for bullet in experience.bullets
    )
