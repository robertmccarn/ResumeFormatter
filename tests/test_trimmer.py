from resume_formatter.layout import LayoutSettings
from resume_formatter.models import (
    Bullet,
    Contact,
    Experience,
    Resume,
)
from resume_formatter.rules import FormattingRules
from resume_formatter.trimmer import trim_resume


def make_resume() -> Resume:
    return Resume(
        contact=Contact(
            name="Robert McCarn",
            email="robert@example.com",
            phone="555-555-5555",
            location="Spring, TX",
        ),
        headline="Data Engineer",
        summary="Experienced data engineer.",
        experience=[
            Experience(
                company="Current Company",
                title="Data Engineer",
                dates="2022–Present",
                bullets=[
                    Bullet("Current bullet one."),
                    Bullet("Current bullet two."),
                    Bullet("Current bullet three."),
                    Bullet("Current bullet four."),
                ],
            ),
            Experience(
                company="Previous Company",
                title="Data Analyst",
                dates="2019–2022",
                bullets=[
                    Bullet("Older bullet one."),
                    Bullet("Older bullet two."),
                    Bullet("Older bullet three."),
                    Bullet("Older bullet four."),
                    Bullet("Older bullet five."),
                ],
            ),
        ],
    )


def constrained_settings() -> LayoutSettings:
    """Create a deliberately constrained layout that requires trimming."""
    return LayoutSettings(
        chars_per_line=50,
        lines_per_page=5,
    )


def generous_settings() -> LayoutSettings:
    """Create a layout with enough capacity that no trimming is required."""
    return LayoutSettings(
        chars_per_line=105,
        lines_per_page=50,
    )


def test_fitting_resume_is_not_trimmed():
    resume = make_resume()

    result = trim_resume(
        resume,
        settings=generous_settings(),
    )

    assert not result.report.changed
    assert result.report.changes_count == 0
    assert result.report.fully_resolved
    assert result.resume == resume


def test_original_resume_is_not_modified():
    resume = make_resume()

    original_bullets = [
        bullet.text
        for experience in resume.experience
        for bullet in experience.bullets
    ]

    trim_resume(
        resume,
        settings=constrained_settings(),
    )

    resulting_original_bullets = [
        bullet.text
        for experience in resume.experience
        for bullet in experience.bullets
    ]

    assert resulting_original_bullets == original_bullets


def test_trim_removes_older_experience_bullets():
    resume = make_resume()

    result = trim_resume(
        resume,
        settings=constrained_settings(),
    )

    assert result.report.changed

    assert len(result.resume.experience[1].bullets) < 5
    assert len(result.resume.experience[1].bullets) >= 3


def test_current_experience_is_never_trimmed():
    resume = make_resume()

    result = trim_resume(
        resume,
        settings=constrained_settings(),
    )

    assert len(result.resume.experience[0].bullets) == 4

    assert [
        bullet.text
        for bullet in result.resume.experience[0].bullets
    ] == [
        "Current bullet one.",
        "Current bullet two.",
        "Current bullet three.",
        "Current bullet four.",
    ]


def test_trim_respects_minimum_bullet_count():
    resume = make_resume()

    rules = FormattingRules(
        minimum_experience_bullets=3,
    )

    result = trim_resume(
        resume,
        rules=rules,
        settings=constrained_settings(),
    )

    assert len(result.resume.experience[1].bullets) >= 3


def test_trim_report_records_each_change():
    resume = make_resume()

    result = trim_resume(
        resume,
        settings=constrained_settings(),
    )

    assert result.report.changed
    assert result.report.changes_count > 0

    for change in result.report.changes:
        assert change.action == "remove_bullet"
        assert change.location.startswith("experience[")
        assert change.original_text
        assert change.estimated_lines_recovered > 0
        assert change.reason


def test_trim_stops_when_layout_fits():
    resume = make_resume()

    result = trim_resume(
        resume,
        settings=constrained_settings(),
    )

    assert result.report.fully_resolved
    assert result.report.final_analysis.fits_two_pages
    assert result.report.final_analysis.layout.page_two_overflow == 0


def test_trim_does_not_remove_more_than_needed():
    resume = make_resume()

    result = trim_resume(
        resume,
        settings=constrained_settings(),
    )

    assert result.report.changed
    assert result.report.final_analysis.fits_two_pages

    # The trimmer must respect the minimum bullet count.
    assert len(result.resume.experience[1].bullets) >= 3


def test_unresolved_overflow_can_remain_when_only_protected_content_is_left():
    resume = make_resume()

    resume.experience[0].bullets = [
        Bullet(
            "This current experience bullet is intentionally "
            "extremely long and cannot be removed. " * 30
        )
        for _ in range(10)
    ]

    rules = FormattingRules(
        minimum_experience_bullets=3,
    )

    result = trim_resume(
        resume,
        rules=rules,
        settings=LayoutSettings(
            chars_per_line=50,
            lines_per_page=5,
        ),
    )

    # Two older bullets are removable, so the trimmer should make
    # those safe changes before stopping.
    assert result.report.changed
    assert result.report.changes_count == 2

    # Protected current-experience content still overflows.
    assert not result.report.fully_resolved
    assert result.report.final_analysis.layout.page_two_overflow > 0

    # The older experience must stop at the configured minimum.
    assert len(result.resume.experience[1].bullets) == 3

    # Current experience must remain untouched.
    assert len(result.resume.experience[0].bullets) == 10


def test_trim_preserves_original_bullet_text():
    resume = make_resume()

    original_text = {
        bullet.text
        for experience in resume.experience
        for bullet in experience.bullets
    }

    result = trim_resume(
        resume,
        settings=constrained_settings(),
    )

    resulting_text = {
        bullet.text
        for experience in result.resume.experience
        for bullet in experience.bullets
    }

    assert resulting_text.issubset(original_text)


def test_lines_recovered_are_recorded():
    resume = make_resume()

    result = trim_resume(
        resume,
        settings=constrained_settings(),
    )

    assert result.report.lines_recovered > 0

    assert result.report.lines_recovered == sum(
        change.estimated_lines_recovered
        for change in result.report.changes
    )
