from dataclasses import dataclass, field
import math
import re

from .models import Resume
from .rules import DEFAULT_RULES, FormattingRules


# These are deliberately estimates, not Word pagination measurements.
# Actual pagination will be handled later by the validator.
DEFAULT_CHARS_PER_LINE = 105
DEFAULT_LINES_PER_PAGE = 50


@dataclass(frozen=True)
class LayoutSettings:
    chars_per_line: int = DEFAULT_CHARS_PER_LINE
    experience_chars_per_line: int = 95
    lines_per_page: int = DEFAULT_LINES_PER_PAGE


@dataclass(frozen=True)
class SectionMeasurement:
    name: str
    characters: int
    estimated_lines: int
    fixed: bool = False


@dataclass
class LayoutReport:
    page_count_estimate: int
    page_one_lines: int
    page_two_lines: int
    page_one_capacity: int
    page_two_capacity: int
    page_one_overflow: int
    page_two_overflow: int
    sections: list[SectionMeasurement] = field(default_factory=list)

    @property
    def total_lines(self) -> int:
        return self.page_one_lines + self.page_two_lines

    @property
    def total_overflow(self) -> int:
        return self.page_one_overflow + self.page_two_overflow

    @property
    def fits_two_pages(self) -> bool:
        return self.page_count_estimate <= 2 and self.total_overflow == 0


def estimate_wrapped_lines(
    text: str,
    chars_per_line: int = DEFAULT_CHARS_PER_LINE,
) -> int:
    """
    Estimate how many visual lines a block of text will occupy.

    This is intentionally conservative and deterministic.
    It is not a replacement for actual Word pagination.
    """

    if not text.strip():
        return 0

    normalized = re.sub(r"\s+", " ", text.strip())

    if not normalized:
        return 0

    return max(
        1,
        math.ceil(len(normalized) / chars_per_line),
    )


def measure_text(
    name: str,
    text: str,
    *,
    chars_per_line: int = DEFAULT_CHARS_PER_LINE,
    fixed: bool = False,
) -> SectionMeasurement:
    characters = len(text.strip())

    return SectionMeasurement(
        name=name,
        characters=characters,
        estimated_lines=estimate_wrapped_lines(
            text,
            chars_per_line,
        ),
        fixed=fixed,
    )


def measure_header(
    resume: Resume,
    settings: LayoutSettings,
) -> SectionMeasurement:
    parts = [
        resume.contact.name,
        resume.contact.email,
        resume.contact.phone,
        resume.contact.location,
        *resume.contact.links,
        resume.headline,
    ]

    text = " | ".join(
        part.strip()
        for part in parts
        if part and part.strip()
    )

    return measure_text(
        "Header",
        text,
        chars_per_line=settings.chars_per_line,
        fixed=True,
    )


def measure_summary(
    resume: Resume,
    settings: LayoutSettings,
) -> SectionMeasurement:
    return measure_text(
        "Summary",
        resume.summary,
        chars_per_line=settings.chars_per_line,
        fixed=False,
    )


def measure_skills(
    resume: Resume,
    settings: LayoutSettings,
) -> SectionMeasurement:
    lines = []

    for category in resume.skills:
        if category.name:
            lines.append(
                f"{category.name}: "
                f"{', '.join(category.skills)}"
            )
        else:
            lines.append(", ".join(category.skills))

    return measure_text(
        "Core Skills",
        "\n".join(lines),
        chars_per_line=settings.chars_per_line,
        fixed=False,
    )


def measure_education(
    resume: Resume,
    settings: LayoutSettings,
) -> SectionMeasurement:
    lines = []

    for education in resume.education:
        parts = [education.institution]

        if education.degree:
            parts.append(education.degree)

        if education.dates:
            parts.append(education.dates)

        lines.append(" | ".join(parts))
        lines.extend(education.details)

    return measure_text(
        "Education",
        "\n".join(lines),
        chars_per_line=settings.chars_per_line,
        fixed=True,
    )


def measure_certifications(
    resume: Resume,
    settings: LayoutSettings,
) -> SectionMeasurement:
    lines = []

    for certification in resume.certifications:
        parts = [certification.name]

        if certification.issuer:
            parts.append(certification.issuer)

        if certification.date:
            parts.append(certification.date)

        lines.append(" | ".join(parts))

    return measure_text(
        "Certifications",
        "\n".join(lines),
        chars_per_line=settings.chars_per_line,
        fixed=True,
    )


def measure_experience(
    resume: Resume,
    settings: LayoutSettings,
) -> SectionMeasurement:
    lines = []

    for experience in resume.experience:
        header_parts = [
            experience.company,
            experience.subtitle,
            experience.location,
            experience.title,
            experience.dates,
        ]

        lines.append(
            " | ".join(
                part
                for part in header_parts
                if part
            )
        )

        lines.extend(
            bullet.text
            for bullet in experience.bullets
        )

    return measure_text(
        "Professional Experience",
        "\n".join(lines),
        chars_per_line=settings.chars_per_line,
        fixed=False,
    )


def measure_resume(
    resume: Resume,
    rules: FormattingRules = DEFAULT_RULES,
    settings: LayoutSettings = LayoutSettings(),
) -> LayoutReport:
    """
    Produce a deterministic estimate of resume layout demand.

    Page 1 contains:
        Header
        Headline
        Summary
        Core Skills
        Education
        Certifications

    Page 2 contains:
        Professional Experience

    The analyzer intentionally does not modify the resume.
    """

    sections = [
        measure_header(resume, settings),
        measure_summary(resume, settings),
        measure_skills(resume, settings),
        measure_education(resume, settings),
        measure_certifications(resume, settings),
        measure_experience(resume, settings),
    ]

    page_one_sections = sections[:-1]
    page_two_sections = sections[-1:]

    page_one_lines = sum(
        section.estimated_lines
        for section in page_one_sections
    )

    page_two_lines = sum(
        section.estimated_lines
        for section in page_two_sections
    )

    page_one_overflow = max(
        0,
        page_one_lines - settings.lines_per_page,
    )

    page_two_overflow = max(
        0,
        page_two_lines - settings.lines_per_page,
    )

    page_count_estimate = 1

    if page_one_overflow > 0:
        page_count_estimate += math.ceil(
            page_one_overflow / settings.lines_per_page
        )

    # Experience is structurally placed on page 2.
    if page_two_lines > 0:
        page_count_estimate = max(
            page_count_estimate,
            2,
        )

    if page_two_overflow > 0:
        page_count_estimate = max(
            page_count_estimate,
            2 + math.ceil(
                page_two_overflow / settings.lines_per_page
            ),
        )

    # Respect the configured maximum when reporting overflow,
    # but do not hide that the content exceeds it.
    if page_count_estimate > rules.max_pages:
        page_count_estimate = max(
            page_count_estimate,
            rules.max_pages + 1,
        )

    return LayoutReport(
        page_count_estimate=page_count_estimate,
        page_one_lines=page_one_lines,
        page_two_lines=page_two_lines,
        page_one_capacity=settings.lines_per_page,
        page_two_capacity=settings.lines_per_page,
        page_one_overflow=page_one_overflow,
        page_two_overflow=page_two_overflow,
        sections=sections,
    )
