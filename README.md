# ResumeFormatter

ResumeFormatter is a local resume compiler that converts structured plain-text resume content into a deterministic, ATS-friendly DOCX.

The compiler preserves user-supplied resume content as the primary invariant. It optimizes layout before considering conservative trimming and validates the resulting DOCX with an actual pagination engine when one is available.

## Requirements

- Python 3.11+
- Microsoft Word on Windows for actual Word pagination validation
- pywin32

LibreOffice can be used as a fallback pagination engine on systems where Microsoft Word is unavailable.

## Setup

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt

## CLI

Provide the resume as plain text:

    python app.py sample_resume.txt -o formatted_resume.docx

The compiler reports:

- selected layout profile
- estimated page count
- actual Word/LibreOffice page count when available
- Professional Experience page
- whether content was trimmed
- final compilation status

A successful compilation requires actual pagination validation.

## Tests

Run the normal unit and integration-safe suite:

    pytest -v

The Microsoft Word acceptance test is opt-in because it requires a locally installed Word application:

    $env:RUN_WORD_ACCEPTANCE="1"
    pytest -v tests/test_acceptance.py

The acceptance test uses the representative fixture in tests/fixtures/representative_resume.txt and verifies that the compiled DOCX is two pages with Professional Experience beginning on page 2.