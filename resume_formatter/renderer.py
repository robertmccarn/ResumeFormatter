from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from .models import Resume


FONT_NAME = "Arial"

PAGE_MARGIN = Inches(0.6)

NAME_SIZE = Pt(18)
HEADLINE_SIZE = Pt(11)
BODY_SIZE = Pt(10)
SECTION_SIZE = Pt(11)
CONTACT_SIZE = Pt(9)

SPACING_AFTER_BODY = Pt(3)
SPACING_AFTER_SECTION = Pt(4)
SPACING_AFTER_ENTRY = Pt(5)


def configure_document(document: Document) -> None:
    section = document.sections[0]

    section.top_margin = PAGE_MARGIN
    section.bottom_margin = PAGE_MARGIN
    section.left_margin = PAGE_MARGIN
    section.right_margin = PAGE_MARGIN

    styles = document.styles

    normal = styles["Normal"]
    normal.font.name = FONT_NAME
    normal.font.size = BODY_SIZE
    normal.paragraph_format.space_after = SPACING_AFTER_BODY
    normal.paragraph_format.line_spacing = 1.0

    if "Resume Bullet" not in styles:
        bullet_style = styles.add_style(
            "Resume Bullet",
            WD_STYLE_TYPE.PARAGRAPH,
        )
    else:
        bullet_style = styles["Resume Bullet"]

    bullet_style.base_style = normal
    bullet_style.font.name = FONT_NAME
    bullet_style.font.size = BODY_SIZE
    bullet_style.paragraph_format.left_indent = Inches(0.18)
    bullet_style.paragraph_format.first_line_indent = Inches(-0.12)
    bullet_style.paragraph_format.space_after = Pt(2)
    bullet_style.paragraph_format.line_spacing = 1.0


def add_run(
    paragraph,
    text: str,
    *,
    bold: bool = False,
    size: Pt | None = None,
) -> None:
    run = paragraph.add_run(text)
    run.font.name = FONT_NAME
    run.bold = bold

    if size is not None:
        run.font.size = size


def add_header(document: Document, resume: Resume) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(1)

    add_run(
        paragraph,
        resume.contact.name,
        bold=True,
        size=NAME_SIZE,
    )

    contact_parts = []

    if resume.contact.email:
        contact_parts.append(resume.contact.email)

    if resume.contact.phone:
        contact_parts.append(resume.contact.phone)

    if resume.contact.location:
        contact_parts.append(resume.contact.location)

    contact_parts.extend(resume.contact.links)

    if contact_parts:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(4)

        add_run(
            paragraph,
            " | ".join(contact_parts),
            size=CONTACT_SIZE,
        )


def add_headline(document: Document, headline: str) -> None:
    if not headline:
        return

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(5)

    add_run(
        paragraph,
        headline,
        bold=True,
        size=HEADLINE_SIZE,
    )


def add_section_heading(document: Document, title: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = SPACING_AFTER_SECTION

    add_run(
        paragraph,
        title.upper(),
        bold=True,
        size=SECTION_SIZE,
    )


def add_summary(document: Document, summary: str) -> None:
    if not summary:
        return

    add_section_heading(document, "Summary")

    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(4)

    add_run(
        paragraph,
        summary,
        size=BODY_SIZE,
    )


def add_skills(document: Document, resume: Resume) -> None:
    if not resume.skills:
        return

    add_section_heading(document, "Core Skills")

    for category in resume.skills:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(2)

        if category.name:
            add_run(
                paragraph,
                f"{category.name}: ",
                bold=True,
                size=BODY_SIZE,
            )

        add_run(
            paragraph,
            ", ".join(category.skills),
            size=BODY_SIZE,
        )


def add_education(document: Document, resume: Resume) -> None:
    if not resume.education:
        return

    add_section_heading(document, "Education")

    for education in resume.education:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(2)

        add_run(
            paragraph,
            education.institution,
            bold=True,
            size=BODY_SIZE,
        )

        if education.degree:
            add_run(
                paragraph,
                f" | {education.degree}",
                size=BODY_SIZE,
            )

        if education.dates:
            add_run(
                paragraph,
                f" | {education.dates}",
                size=BODY_SIZE,
            )

        for detail in education.details:
            bullet = document.add_paragraph(style="Resume Bullet")
            add_run(
                bullet,
                detail,
                size=BODY_SIZE,
            )


def add_certifications(document: Document, resume: Resume) -> None:
    if not resume.certifications:
        return

    add_section_heading(document, "Certifications")

    for certification in resume.certifications:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(2)

        add_run(
            paragraph,
            certification.name,
            size=BODY_SIZE,
        )

        if certification.issuer:
            add_run(
                paragraph,
                f" | {certification.issuer}",
                size=BODY_SIZE,
            )

        if certification.date:
            add_run(
                paragraph,
                f" | {certification.date}",
                size=BODY_SIZE,
            )


def add_experience(document: Document, resume: Resume) -> None:
    if not resume.experience:
        return

    add_section_heading(document, "Professional Experience")

    for experience in resume.experience:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(1)

        add_run(
            paragraph,
            experience.company,
            bold=True,
            size=BODY_SIZE,
        )

        if experience.location:
            add_run(
                paragraph,
                f" | {experience.location}",
                size=BODY_SIZE,
            )

        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(2)

        add_run(
            paragraph,
            experience.title,
            bold=True,
            size=BODY_SIZE,
        )

        if experience.dates:
            add_run(
                paragraph,
                f" | {experience.dates}",
                size=BODY_SIZE,
            )

        for bullet in experience.bullets:
            paragraph = document.add_paragraph(
                style="Resume Bullet"
            )

            add_run(
                paragraph,
                bullet.text,
                size=BODY_SIZE,
            )

        # Small separation between employers.
        if experience is not resume.experience[-1]:
            spacer = document.add_paragraph()
            spacer.paragraph_format.space_after = Pt(0)
            spacer.paragraph_format.space_before = Pt(0)


def render_resume(resume: Resume, output_path: str | Path) -> Path:
    """
    Render a structured Resume into a deterministic DOCX file.

    Professional Experience intentionally begins on page 2.
    """

    output_path = Path(output_path)

    document = Document()
    configure_document(document)

    add_header(document, resume)
    add_headline(document, resume.headline)
    add_summary(document, resume.summary)
    add_skills(document, resume)
    add_education(document, resume)
    add_certifications(document, resume)

    # Experience is intentionally forced onto page 2.
    document.add_page_break()

    add_experience(document, resume)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    document.save(output_path)

    return output_path
