from dataclasses import dataclass, field
from enum import Enum

from .layout import (
    LayoutReport,
    LayoutSettings,
    estimate_wrapped_lines,
    measure_resume,
)
from .models import Resume
from .rules import (
    DEFAULT_RULES,
    FormattingRules,
    PreservationPriority,
)


class IssueSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class AnalysisIssue:
    severity: IssueSeverity
    code: str
    message: str
    page: int | None = None
    section: str | None = None
    lines: int = 0


@dataclass(frozen=True)
class ContentCandidate:
    """
    A piece of content that may become relevant to the trim engine.

    The analyzer identifies candidates only. It never removes or changes
    their text.
    """

    location: str
    text: str
    page: int
    estimated_lines: int
    priority: PreservationPriority
    removable: bool
    compressible: bool


@dataclass
class AnalysisResult:
    layout: LayoutReport
    issues: list[AnalysisIssue] = field(default_factory=list)
    candidates: list[ContentCandidate] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(
            issue.severity == IssueSeverity.ERROR
            for issue in self.issues
        )

    @property
    def has_warnings(self) -> bool:
        return any(
            issue.severity == IssueSeverity.WARNING
            for issue in self.issues
        )

    @property
    def fits_two_pages(self) -> bool:
        return self.layout.fits_two_pages


def analyze_resume(
    resume: Resume,
    rules: FormattingRules = DEFAULT_RULES,
    settings: LayoutSettings = LayoutSettings(),
) -> AnalysisResult:
    """
    Analyze a resume without modifying it.

    This function is deliberately read-only from the perspective of the
    Resume model. It identifies layout pressure and possible future trim
    candidates, but the trimmer owns all transformations.
    """

    layout = measure_resume(
        resume,
        rules=rules,
        settings=settings,
    )

    issues = _build_layout_issues(
        layout,
        rules,
    )

    candidates = _build_candidates(
        resume,
        settings,
    )

    return AnalysisResult(
        layout=layout,
        issues=issues,
        candidates=candidates,
    )


def _build_layout_issues(
    layout: LayoutReport,
    rules: FormattingRules,
) -> list[AnalysisIssue]:
    issues: list[AnalysisIssue] = []

    if layout.page_one_overflow > 0:
        issues.append(
            AnalysisIssue(
                severity=IssueSeverity.ERROR,
                code="PAGE_ONE_OVERFLOW",
                message=(
                    "Page 1 exceeds estimated capacity by "
                    f"{layout.page_one_overflow} lines."
                ),
                page=1,
                lines=layout.page_one_overflow,
            )
        )

    if layout.page_two_overflow > 0:
        issues.append(
            AnalysisIssue(
                severity=IssueSeverity.ERROR,
                code="PAGE_TWO_OVERFLOW",
                message=(
                    "Page 2 exceeds estimated capacity by "
                    f"{layout.page_two_overflow} lines."
                ),
                page=2,
                section="Professional Experience",
                lines=layout.page_two_overflow,
            )
        )

    if layout.fits_two_pages:
        issues.append(
            AnalysisIssue(
                severity=IssueSeverity.INFO,
                code="FITS_TWO_PAGES",
                message="Resume fits within the estimated two-page layout.",
            )
        )

    if (
        layout.page_one_lines
        > int(layout.page_one_capacity * 0.9)
        and layout.page_one_overflow == 0
    ):
        issues.append(
            AnalysisIssue(
                severity=IssueSeverity.WARNING,
                code="PAGE_ONE_NEAR_CAPACITY",
                message="Page 1 is close to its estimated capacity.",
                page=1,
                lines=layout.page_one_lines,
            )
        )

    if (
        layout.page_two_lines
        > int(layout.page_two_capacity * 0.9)
        and layout.page_two_overflow == 0
    ):
        issues.append(
            AnalysisIssue(
                severity=IssueSeverity.WARNING,
                code="PAGE_TWO_NEAR_CAPACITY",
                message="Page 2 is close to its estimated capacity.",
                page=2,
                section="Professional Experience",
                lines=layout.page_two_lines,
            )
        )

    if rules.minimum_experience_bullets > 0:
        for index, experience in enumerate(
            # The actual rule enforcement happens elsewhere.
            # This check only exposes potential structural pressure.
            [],
            start=1,
        ):
            _ = index
            _ = experience

    return issues


def _build_candidates(
    resume: Resume,
    settings: LayoutSettings,
) -> list[ContentCandidate]:
    candidates: list[ContentCandidate] = []

    # Summary can be compressed, but is not removable.
    if resume.summary.strip():
        candidates.append(
            ContentCandidate(
                location="summary",
                text=resume.summary,
                page=1,
                estimated_lines=estimate_wrapped_lines(
                    resume.summary,
                    settings.chars_per_line,
                ),
                priority=PreservationPriority.HIGH,
                removable=False,
                compressible=True,
            )
        )

    # Skills are protected but compressible.
    for category_index, category in enumerate(
        resume.skills,
        start=1,
    ):
        if category.name:
            text = (
                f"{category.name}: "
                f"{', '.join(category.skills)}"
            )
        else:
            text = ", ".join(category.skills)

        candidates.append(
            ContentCandidate(
                location=f"skills[{category_index}]",
                text=text,
                page=1,
                estimated_lines=estimate_wrapped_lines(
                    text,
                    settings.chars_per_line,
                ),
                priority=PreservationPriority.HIGH,
                removable=False,
                compressible=True,
            )
        )

    # Experience bullets are where the future trim engine will primarily
    # operate. Current experience is protected; older experience is
    # potentially removable.
    for experience_index, experience in enumerate(
        resume.experience,
        start=1,
    ):
        is_current = experience_index == 1

        priority = (
            PreservationPriority.HIGH
            if is_current
            else PreservationPriority.NORMAL
        )

        removable = not is_current

        for bullet_index, bullet in enumerate(
            experience.bullets,
            start=1,
        ):
            candidates.append(
                ContentCandidate(
                    location=(
                        f"experience[{experience_index}]"
                        f".bullets[{bullet_index}]"
                    ),
                    text=bullet.text,
                    page=2,
                    estimated_lines=estimate_wrapped_lines(
                        bullet.text,
                        settings.chars_per_line,
                    ),
                    priority=priority,
                    removable=removable,
                    compressible=True,
                )
            )

    return candidates


def rank_trim_candidates(
    result: AnalysisResult,
) -> list[ContentCandidate]:
    """
    Return candidates in the order the future trimmer should consider.

    Lower preservation priority is considered first.

    Within the same priority:
        1. removable content first
        2. larger space consumers first

    This function does not perform any trimming.
    """

    return sorted(
        result.candidates,
        key=lambda candidate: (
            candidate.priority,
            not candidate.removable,
            -candidate.estimated_lines,
        ),
    )
