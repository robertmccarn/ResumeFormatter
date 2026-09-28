# ResumeFormatter

ResumeFormatter is a local resume compiler that converts structured plain-text resume content into a deterministic, ATS-friendly DOCX.

The compiler preserves user-supplied resume content as the primary invariant. It optimizes layout before considering conservative trimming and validates the resulting DOCX with an actual pagination engine when one is available.

## Requirements

- Python 3.11+
- Microsoft Word on Windows for actual Word pagination validation
- pywin32
- Tkinter (normally included with the standard Windows Python distribution)

LibreOffice can be used as a fallback pagination engine on systems where Microsoft Word is unavailable.

## Setup

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt

## Desktop application

Launch the GUI with:

    python app.py

Or explicitly:

    python app.py --gui

The desktop app provides a plain-text resume editor, TXT open/save, DOCX output selection, background compilation, and an audit panel showing pagination and trimming results.

## Visual language

The renderer uses a restrained, single-column professional design:

- Arial typography with conventional 10–12 pt body sizing
- Deep navy for the candidate name and primary identity
- One medium-blue accent for section headings, role titles, bullets, and divider rules
- Muted gray for contact information, locations, and dates
- Black body text for maximum readability
- Consistent spacing and hierarchy across every section
- No tables, columns, graphics, photos, text boxes, icons, or decorative elements that could interfere with ATS parsing

The visual system is intentionally conservative: color is used to direct attention rather than decorate the page. This follows current ATS-oriented guidance emphasizing standard headings, readable fonts, simple single-column structure, and consistent formatting.

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
