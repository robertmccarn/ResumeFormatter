import pytest

from resume_formatter.models import (
    Contact,
    Education,
    Experience,
    Resume,
    SkillCategory,
)
from resume_formatter.rules import (
    DEFAULT_RULES,
    FormattingRules,
    PreservationPriority,
    certification_protection,
    contact_protection,
    current_experience_bullet_protection,
    education_protection,
    headline_protection,
    older_experience_bullet_protection,
    skills_protection,
    summary_protection,
    validate_resume_structure,
    validate_rules,
)


def make_valid_resume() -> Resume:
    return Resume(
        contact=Contact(name="Robert McCarn"),
        headline="Data Engineer",
        summary="Experienced data engineer.",
        skills=[
            SkillCategory(
                name="Databases",
                skills=["SQL Server"],
            )
        ],
        education=[
            Education(
                institution="University of Houston",
                degree="BBA",
            )
        ],
        experience=[
            Experience(
                company="Example Company",
                title="Data Engineer",
            )
        ],
    )


def test_default_rules():
    assert DEFAULT_RULES.max_pages == 2
    assert DEFAULT_RULES.experience_starts_page == 2
    assert DEFAULT_RULES.summary_max_lines == 4
    assert DEFAULT_RULES.minimum_body_font_pt == 10.0


def test_valid_rules_have_no_errors():
    assert validate_rules(DEFAULT_RULES) == []


def test_invalid_page_configuration():
    rules = FormattingRules(
        max_pages=1,
        experience_starts_page=2,
    )

    errors = validate_rules(rules)

    assert "experience_starts_page cannot be greater than max_pages." in errors


def test_invalid_bullet_configuration():
    rules = FormattingRules(
        minimum_experience_bullets=6,
        maximum_experience_bullets=3,
    )

    errors = validate_rules(rules)

    assert (
        "minimum_experience_bullets cannot exceed "
        "maximum_experience_bullets."
    ) in errors


def test_valid_resume_structure():
    errors = validate_resume_structure(make_valid_resume())

    assert errors == []


def test_missing_required_sections():
    resume = Resume(
        contact=Contact(name="Robert McCarn"),
    )

    errors = validate_resume_structure(resume)

    assert "Resume requires a summary." in errors
    assert "Resume requires skills." in errors
    assert "Resume requires education." in errors
    assert "Resume requires professional experience." in errors


@pytest.mark.parametrize(
    "factory, priority, removable, compressible",
    [
        (
            contact_protection,
            PreservationPriority.REQUIRED,
            False,
            False,
        ),
        (
            headline_protection,
            PreservationPriority.HIGH,
            False,
            False,
        ),
        (
            summary_protection,
            PreservationPriority.HIGH,
            False,
            True,
        ),
        (
            skills_protection,
            PreservationPriority.HIGH,
            False,
            True,
        ),
        (
            education_protection,
            PreservationPriority.HIGH,
            False,
            False,
        ),
        (
            certification_protection,
            PreservationPriority.HIGH,
            False,
            False,
        ),
        (
            current_experience_bullet_protection,
            PreservationPriority.HIGH,
            False,
            True,
        ),
        (
            older_experience_bullet_protection,
            PreservationPriority.NORMAL,
            True,
            True,
        ),
    ],
)
def test_content_protection(
    factory,
    priority,
    removable,
    compressible,
):
    protection = factory()

    assert protection.priority == priority
    assert protection.removable is removable
    assert protection.compressible is compressible
