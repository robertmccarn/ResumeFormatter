from resume_formatter.layout import (
    LayoutSettings,
    estimate_wrapped_lines,
    measure_resume,
)
from resume_formatter.models import (
    Bullet,
    Certification,
    Contact,
    Education,
    Experience,
    Resume,
    SkillCategory,
)


def make_resume() -> Resume:
    return Resume(
        contact=Contact(
            name="Robert McCarn",
            email="robert@example.com",
            phone="555-555-5555",
            location="Spring, TX",
        ),
        headline="Data Engineer",
        summary=(
            "Data Engineer with experience building "
            "and maintaining data solutions."
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
            )
        ],
        certifications=[
            Certification(
                name="Microsoft Fabric DP-700",
                date="2026",
            )
        ],
        experience=[
            Experience(
                company="TEKsystems Global Services",
                title="Data Engineer",
                dates="2022–Present",
                bullets=[
                    Bullet(text="Developed T-SQL stored procedures."),
                    Bullet(text="Supported data modernization."),
                    Bullet(text="Performed query tuning."),
                ],
            )
        ],
    )


def test_empty_text_requires_zero_lines():
    assert estimate_wrapped_lines("") == 0
    assert estimate_wrapped_lines("   ") == 0


def test_short_text_requires_one_line():
    assert estimate_wrapped_lines("SQL Server") == 1


def test_long_text_wraps():
    text = "A" * 211

    assert estimate_wrapped_lines(
        text,
        chars_per_line=100,
    ) == 3


def test_measure_resume_contains_all_sections():
    report = measure_resume(make_resume())

    names = [section.name for section in report.sections]

    assert names == [
        "Header",
        "Summary",
        "Core Skills",
        "Education",
        "Certifications",
        "Professional Experience",
    ]


def test_experience_is_assigned_to_page_two():
    report = measure_resume(make_resume())

    assert report.page_two_lines > 0
    assert report.page_one_lines > 0


def test_small_resume_fits_two_pages():
    report = measure_resume(
        make_resume(),
        settings=LayoutSettings(
            chars_per_line=105,
            lines_per_page=50,
        ),
    )

    assert report.fits_two_pages
    assert report.page_count_estimate == 2


def test_overflow_is_detected():
    resume = make_resume()

    resume.experience[0].bullets = [
        Bullet(text="This is a deliberately long bullet. " * 20)
        for _ in range(20)
    ]

    report = measure_resume(
        resume,
        settings=LayoutSettings(
            chars_per_line=50,
            lines_per_page=10,
        ),
    )

    assert report.page_two_overflow > 0
    assert not report.fits_two_pages
