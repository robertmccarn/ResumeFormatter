from resume_formatter.analyzer import (
    IssueSeverity,
    analyze_resume,
    rank_trim_candidates,
)
from resume_formatter.layout import LayoutSettings
from resume_formatter.models import (
    Bullet,
    Contact,
    Experience,
    Resume,
    SkillCategory,
)
from resume_formatter.rules import PreservationPriority


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
            )
        ],
        experience=[
            Experience(
                company="Current Company",
                title="Data Engineer",
                dates="2022–Present",
                bullets=[
                    Bullet(
                        text="Developed T-SQL stored procedures."
                    ),
                    Bullet(
                        text="Supported data modernization."
                    ),
                    Bullet(
                        text="Performed query tuning."
                    ),
                ],
            ),
            Experience(
                company="Previous Company",
                title="Data Analyst",
                dates="2019–2022",
                bullets=[
                    Bullet(
                        text="Created reporting solutions."
                    ),
                    Bullet(
                        text="Maintained analytical datasets."
                    ),
                ],
            ),
        ],
    )


def test_analysis_does_not_modify_resume():
    resume = make_resume()

    original_summary = resume.summary
    original_bullets = [
        bullet.text
        for experience in resume.experience
        for bullet in experience.bullets
    ]

    analyze_resume(resume)

    assert resume.summary == original_summary

    assert [
        bullet.text
        for experience in resume.experience
        for bullet in experience.bullets
    ] == original_bullets


def test_fitting_resume_reports_info():
    result = analyze_resume(
        make_resume(),
        settings=LayoutSettings(
            chars_per_line=105,
            lines_per_page=50,
        ),
    )

    assert result.fits_two_pages
    assert not result.has_errors

    assert any(
        issue.code == "FITS_TWO_PAGES"
        and issue.severity == IssueSeverity.INFO
        for issue in result.issues
    )


def test_overflow_produces_error():
    resume = make_resume()

    resume.experience[0].bullets = [
        Bullet(
            text="This is an intentionally long bullet. " * 20
        )
        for _ in range(20)
    ]

    result = analyze_resume(
        resume,
        settings=LayoutSettings(
            chars_per_line=50,
            lines_per_page=10,
        ),
    )

    assert result.has_errors

    assert any(
        issue.code == "PAGE_TWO_OVERFLOW"
        and issue.page == 2
        for issue in result.issues
    )


def test_summary_is_high_priority_and_non_removable():
    result = analyze_resume(make_resume())

    candidate = next(
        candidate
        for candidate in result.candidates
        if candidate.location == "summary"
    )

    assert candidate.priority == PreservationPriority.HIGH
    assert not candidate.removable
    assert candidate.compressible


def test_current_experience_bullets_are_protected():
    result = analyze_resume(make_resume())

    candidate = next(
        candidate
        for candidate in result.candidates
        if candidate.location == "experience[1].bullets[1]"
    )

    assert candidate.priority == PreservationPriority.HIGH
    assert not candidate.removable
    assert candidate.compressible


def test_older_experience_bullets_are_removable():
    result = analyze_resume(make_resume())

    candidate = next(
        candidate
        for candidate in result.candidates
        if candidate.location == "experience[2].bullets[1]"
    )

    assert candidate.priority == PreservationPriority.NORMAL
    assert candidate.removable
    assert candidate.compressible


def test_rank_trim_candidates_prefers_removable_content():
    result = analyze_resume(make_resume())

    ranked = rank_trim_candidates(result)

    first_removable_index = next(
        index
        for index, candidate in enumerate(ranked)
        if candidate.removable
    )

    assert all(
        not candidate.removable
        or candidate.priority
        >= ranked[first_removable_index].priority
        for candidate in ranked[first_removable_index:]
    )


def test_rank_trim_candidates_prefers_larger_same_priority_candidates():
    resume = make_resume()

    resume.experience[1].bullets = [
        Bullet(text="Short bullet."),
        Bullet(text="Long bullet. " * 30),
    ]

    result = analyze_resume(resume)

    ranked = rank_trim_candidates(result)

    removable = [
        candidate
        for candidate in ranked
        if candidate.removable
    ]

    assert removable[0].estimated_lines >= removable[1].estimated_lines
