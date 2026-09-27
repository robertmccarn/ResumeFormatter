from pathlib import Path

from docx import Document

from resume_formatter.models import (
    Bullet,
    Certification,
    Contact,
    Education,
    Experience,
    Resume,
    SkillCategory,
)
from resume_formatter.renderer import render_resume


def make_resume() -> Resume:
    return Resume(
        contact=Contact(
            name="Robert McCarn",
            email="robert@example.com",
            phone="555-555-5555",
            location="Spring, TX",
            links=["linkedin.com/in/robert"],
        ),
        headline="Data Engineer",
        summary=(
            "Data Engineer with 4+ years of experience "
            "building and maintaining data solutions."
        ),
        skills=[
            SkillCategory(
                name="Databases",
                skills=["SQL Server", "Azure SQL"],
            ),
            SkillCategory(
                name="Languages",
                skills=["T-SQL", "Python", "PowerShell"],
            ),
        ],
        education=[
            Education(
                institution="University of Houston",
                degree="BBA, Management Information Systems",
                dates="2021",
            ),
        ],
        certifications=[
            Certification(
                name="Microsoft Fabric DP-700",
                date="2026",
            ),
        ],
        experience=[
            Experience(
                company="TEKsystems Global Services",
                title="Data Engineer",
                dates="2022–Present",
                bullets=[
                    Bullet(
                        text="Developed T-SQL stored procedures."
                    ),
                    Bullet(
                        text="Supported data modernization initiatives."
                    ),
                ],
            ),
        ],
    )


def test_render_resume_creates_docx(tmp_path: Path):
    output = tmp_path / "resume.docx"

    result = render_resume(make_resume(), output)

    assert result == output
    assert output.exists()
    assert output.stat().st_size > 0


def test_render_resume_contains_expected_content(tmp_path: Path):
    output = tmp_path / "resume.docx"

    render_resume(make_resume(), output)

    document = Document(output)

    text = "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )

    assert "Robert McCarn" in text
    assert "Data Engineer" in text
    assert "SUMMARY" in text
    assert "Databases:" in text
    assert "University of Houston" in text
    assert "Microsoft Fabric DP-700" in text
    assert "PROFESSIONAL EXPERIENCE" in text
    assert "TEKsystems Global Services" in text


def test_render_resume_has_page_break_before_experience(
    tmp_path: Path,
):
    output = tmp_path / "resume.docx"

    render_resume(make_resume(), output)

    document = Document(output)

    body_xml = document._element.body.xml

    page_break_position = body_xml.find(
        'w:type="page"'
    )

    experience_position = body_xml.find(
        "PROFESSIONAL EXPERIENCE"
    )

    assert page_break_position != -1
    assert experience_position != -1
    assert page_break_position < experience_position
