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

- Arial typography with an 11 pt baseline body size, 10.5 pt compact profile, and 10 pt hard floor
- Deep navy for the candidate name and primary identity
- One medium-blue accent for section headings, role titles, bullets, and subtle section accents
- Muted gray for contact information, locations, dates, and engagement subtitles
- Black body text for maximum readability
- Strong company → engagement → role → dates hierarchy for experience entries
- Compact metadata spacing for certifications
- Page 1 profile hierarchy: Summary → Core Skills → Certifications → Education
- Professional Experience begins on page 2 with real, individually spaced bullet paragraphs
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


## Input normalization

The parser accepts clean plain text as well as common pasted-resume variants. It normalizes lightweight Markdown headings and mailto links, collects contact information spread across multiple lines, and recognizes experience blocks even when the pasted experience statements do not contain explicit bullet characters. The renderer—not the source text—owns the visual bullet formatting.

The compiler's visual system is intentionally content-preserving: it may trim eligible older-experience bullets only when the two-page constraint cannot otherwise be satisfied, but formatting and layout decisions do not rewrite resume content.
