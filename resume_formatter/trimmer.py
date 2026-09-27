from copy import deepcopy
from dataclasses import dataclass, field

from .analyzer import (
    AnalysisResult,
    analyze_resume,
    rank_trim_candidates,
)
from .layout import LayoutSettings
from .models import Resume
from .rules import DEFAULT_RULES, FormattingRules


@dataclass(frozen=True)
class TrimChange:
    action: str
    location: str
    original_text: str
    estimated_lines_recovered: int
    reason: str


@dataclass
class TrimReport:
    changed: bool
    original_analysis: AnalysisResult
    final_analysis: AnalysisResult
    changes: list[TrimChange] = field(default_factory=list)

    @property
    def changes_count(self) -> int:
        return len(self.changes)

    @property
    def lines_recovered(self) -> int:
        return sum(
            change.estimated_lines_recovered
            for change in self.changes
        )

    @property
    def fully_resolved(self) -> bool:
        return self.final_analysis.fits_two_pages


@dataclass
class TrimResult:
    resume: Resume
    report: TrimReport


def trim_resume(
    resume: Resume,
    rules: FormattingRules = DEFAULT_RULES,
    settings: LayoutSettings = LayoutSettings(),
) -> TrimResult:
    """
    Produce a trimmed copy of the resume.

    The input Resume is never modified.

    First-pass behavior:
        - Do nothing if the resume already fits.
        - Remove only eligible bullets from older experience.
        - Never remove from the first/current experience.
        - Never reduce an experience below minimum_experience_bullets.
        - Stop as soon as the estimated layout fits.
    """

    original_analysis = analyze_resume(
        resume,
        rules=rules,
        settings=settings,
    )

    working_resume = deepcopy(resume)

    if original_analysis.fits_two_pages:
        report = TrimReport(
            changed=False,
            original_analysis=original_analysis,
            final_analysis=original_analysis,
        )

        return TrimResult(
            resume=working_resume,
            report=report,
        )

    changes: list[TrimChange] = []

    while True:
        analysis = analyze_resume(
            working_resume,
            rules=rules,
            settings=settings,
        )

        if analysis.fits_two_pages:
            break

        candidate = _next_removable_candidate(
            analysis,
            working_resume,
            rules,
        )

        if candidate is None:
            break

        removed = _remove_candidate(
            working_resume,
            candidate.location,
        )

        if removed is None:
            break

        changes.append(
            TrimChange(
                action="remove_bullet",
                location=candidate.location,
                original_text=removed,
                estimated_lines_recovered=candidate.estimated_lines,
                reason=(
                    "Removed eligible older-experience bullet "
                    "to reduce layout overflow."
                ),
            )
        )

    final_analysis = analyze_resume(
        working_resume,
        rules=rules,
        settings=settings,
    )

    report = TrimReport(
        changed=bool(changes),
        original_analysis=original_analysis,
        final_analysis=final_analysis,
        changes=changes,
    )

    return TrimResult(
        resume=working_resume,
        report=report,
    )


def _next_removable_candidate(
    analysis: AnalysisResult,
    resume: Resume,
    rules: FormattingRules,
):
    """
    Select the highest-value safe deletion candidate.

    Candidates are already ranked by preservation priority and estimated
    space consumption. This additional check enforces the experience-level
    minimum bullet rule.
    """

    for candidate in rank_trim_candidates(analysis):
        if not candidate.removable:
            continue

        if not candidate.location.startswith("experience["):
            continue

        parsed = _parse_experience_location(
            candidate.location
        )

        if parsed is None:
            continue

        experience_index, bullet_index = parsed

        # The first/current experience is never removable.
        if experience_index == 1:
            continue

        experience = resume.experience[
            experience_index - 1
        ]

        if len(experience.bullets) <= rules.minimum_experience_bullets:
            continue

        if bullet_index > len(experience.bullets):
            continue

        return candidate

    return None


def _parse_experience_location(
    location: str,
) -> tuple[int, int] | None:
    """
    Parse locations such as:

        experience[2].bullets[4]
    """

    prefix = "experience["
    middle = "].bullets["

    if not location.startswith(prefix):
        return None

    if middle not in location:
        return None

    try:
        experience_part, bullet_part = location[
            len(prefix):
        ].split(middle, 1)

        bullet_part = bullet_part.rstrip("]")

        experience_index = int(experience_part)
        bullet_index = int(bullet_part)
    except ValueError:
        return None

    if experience_index < 1 or bullet_index < 1:
        return None

    return experience_index, bullet_index


def _remove_candidate(
    resume: Resume,
    location: str,
) -> str | None:
    parsed = _parse_experience_location(location)

    if parsed is None:
        return None

    experience_index, bullet_index = parsed

    if experience_index > len(resume.experience):
        return None

    experience = resume.experience[
        experience_index - 1
    ]

    if bullet_index > len(experience.bullets):
        return None

    bullet = experience.bullets.pop(
        bullet_index - 1
    )

    return bullet.text
