from dataclasses import dataclass
from enum import IntEnum

from .models import Resume


class PreservationPriority(IntEnum):
    """
    Lower numbers are more protected.

    The trimmer will only consider lower-priority content after
    higher-priority formatting/layout options have been exhausted.
    """

    REQUIRED = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass(frozen=True)
class FormattingRules:
    # Document constraints
    max_pages: int = 2
    experience_starts_page: int = 2

    # Content constraints
    summary_max_lines: int = 4
    minimum_experience_bullets: int = 3
    maximum_experience_bullets: int = 6

    # Typography floor
    minimum_body_font_pt: float = 10.0

    # Structural requirements
    require_summary: bool = True
    require_skills: bool = True
    require_education: bool = True
    require_certifications: bool = False
    require_experience: bool = True


DEFAULT_RULES = FormattingRules()


@dataclass(frozen=True)
class ContentProtection:
    """
    Describes how strongly a piece of resume content should be protected
    if the document eventually requires trimming.
    """

    priority: PreservationPriority
    removable: bool
    compressible: bool


def contact_protection() -> ContentProtection:
    return ContentProtection(
        priority=PreservationPriority.REQUIRED,
        removable=False,
        compressible=False,
    )


def headline_protection() -> ContentProtection:
    return ContentProtection(
        priority=PreservationPriority.HIGH,
        removable=False,
        compressible=False,
    )


def summary_protection() -> ContentProtection:
    return ContentProtection(
        priority=PreservationPriority.HIGH,
        removable=False,
        compressible=True,
    )


def skills_protection() -> ContentProtection:
    return ContentProtection(
        priority=PreservationPriority.HIGH,
        removable=False,
        compressible=True,
    )


def education_protection() -> ContentProtection:
    return ContentProtection(
        priority=PreservationPriority.HIGH,
        removable=False,
        compressible=False,
    )


def certification_protection() -> ContentProtection:
    return ContentProtection(
        priority=PreservationPriority.HIGH,
        removable=False,
        compressible=False,
    )


def current_experience_bullet_protection() -> ContentProtection:
    return ContentProtection(
        priority=PreservationPriority.HIGH,
        removable=False,
        compressible=True,
    )


def older_experience_bullet_protection() -> ContentProtection:
    return ContentProtection(
        priority=PreservationPriority.NORMAL,
        removable=True,
        compressible=True,
    )


def validate_rules(rules: FormattingRules = DEFAULT_RULES) -> list[str]:
    """
    Return configuration problems rather than raising immediately.
    This makes the rule set easy to validate from tests or a future UI.
    """

    errors: list[str] = []

    if rules.max_pages < 1:
        errors.append("max_pages must be at least 1.")

    if rules.experience_starts_page < 1:
        errors.append("experience_starts_page must be at least 1.")

    if rules.experience_starts_page > rules.max_pages:
        errors.append(
            "experience_starts_page cannot be greater than max_pages."
        )

    if rules.summary_max_lines < 1:
        errors.append("summary_max_lines must be at least 1.")

    if rules.minimum_experience_bullets < 0:
        errors.append(
            "minimum_experience_bullets cannot be negative."
        )

    if rules.maximum_experience_bullets < 1:
        errors.append(
            "maximum_experience_bullets must be at least 1."
        )

    if (
        rules.minimum_experience_bullets
        > rules.maximum_experience_bullets
    ):
        errors.append(
            "minimum_experience_bullets cannot exceed "
            "maximum_experience_bullets."
        )

    if rules.minimum_body_font_pt <= 0:
        errors.append(
            "minimum_body_font_pt must be greater than zero."
        )

    return errors


def validate_resume_structure(
    resume: Resume,
    rules: FormattingRules = DEFAULT_RULES,
) -> list[str]:
    """
    Check structural requirements without modifying the resume.
    """

    errors = validate_rules(rules)

    if rules.require_summary and not resume.summary.strip():
        errors.append("Resume requires a summary.")

    if rules.require_skills and not resume.skills:
        errors.append("Resume requires skills.")

    if rules.require_education and not resume.education:
        errors.append("Resume requires education.")

    if rules.require_certifications and not resume.certifications:
        errors.append("Resume requires certifications.")

    if rules.require_experience and not resume.experience:
        errors.append("Resume requires professional experience.")

    return errors
