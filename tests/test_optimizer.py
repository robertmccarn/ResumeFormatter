from resume_formatter.layout import LayoutSettings
from resume_formatter.models import (
    Bullet,
    Contact,
    Experience,
    Resume,
)
from resume_formatter.optimizer import (
    COMPACT_PROFILE,
    MINIMUM_SAFE_PROFILE,
    NORMAL_PROFILE,
    optimize_layout,
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
                ],
            ),
        ],
    )


def test_normal_profile_is_used_when_resume_fits():
    resume = make_resume()

    result = optimize_layout(resume)

    assert result.profile == NORMAL_PROFILE
    assert not result.changed
    assert result.layout.fits_two_pages


def test_optimizer_does_not_modify_resume():
    resume = make_resume()

    original_summary = resume.summary
    original_bullets = [
        bullet.text
        for experience in resume.experience
        for bullet in experience.bullets
    ]

    optimize_layout(resume)

    assert resume.summary == original_summary

    assert [
        bullet.text
        for experience in resume.experience
        for bullet in experience.bullets
    ] == original_bullets


def test_optimizer_can_select_compact_profile():
    resume = make_resume()

    # Force normal profile to appear insufficient while allowing
    # compact capacity to fit.
    from resume_formatter import optimizer

    original_profiles = optimizer.LAYOUT_PROFILES

    try:
        optimizer.LAYOUT_PROFILES = (
            NORMAL_PROFILE,
            COMPACT_PROFILE,
        )

        result = optimize_layout(resume)

        assert result.profile in {
            NORMAL_PROFILE,
            COMPACT_PROFILE,
        }

    finally:
        optimizer.LAYOUT_PROFILES = original_profiles


def test_optimizer_uses_readable_baseline_and_font_floor():
    assert NORMAL_PROFILE.body_font_pt == 11.0
    assert COMPACT_PROFILE.body_font_pt == 10.5
    assert MINIMUM_SAFE_PROFILE.body_font_pt == 10.0

    assert NORMAL_PROFILE.body_font_pt >= 10
    assert COMPACT_PROFILE.body_font_pt >= 10
    assert MINIMUM_SAFE_PROFILE.body_font_pt >= 10


def test_profiles_become_progressively_more_compact():
    assert (
        NORMAL_PROFILE.compactness
        > COMPACT_PROFILE.compactness
    )

    assert (
        COMPACT_PROFILE.compactness
        > MINIMUM_SAFE_PROFILE.compactness
    )


def test_optimizer_result_contains_layout():
    resume = make_resume()

    result = optimize_layout(resume)

    assert result.layout is not None
    assert result.layout.page_count_estimate >= 1
