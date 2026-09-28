from dataclasses import dataclass

from .layout import LayoutReport, LayoutSettings, measure_resume
from .models import Resume
from .rules import DEFAULT_RULES, FormattingRules


@dataclass(frozen=True)
class LayoutProfile:
    name: str

    # Approximate layout capacity.
    chars_per_line: int
    lines_per_page: int

    # Formatting density used later by the renderer.
    body_font_pt: float
    section_font_pt: float

    # Page 2 has its own visual rhythm. Experience should be larger and
    # more breathable than the compact profile material on page 1.
    experience_font_pt: float
    experience_line_spacing: float

    body_spacing_after_pt: float
    section_spacing_before_pt: float
    section_spacing_after_pt: float
    bullet_spacing_after_pt: float
    entry_spacing_after_pt: float

    @property
    def compactness(self) -> int:
        return (
            int(self.body_spacing_after_pt)
            + int(self.section_spacing_before_pt)
            + int(self.section_spacing_after_pt)
            + int(self.bullet_spacing_after_pt)
            + int(self.entry_spacing_after_pt)
        )


NORMAL_PROFILE = LayoutProfile(
    name="normal",
    chars_per_line=105,
    lines_per_page=50,
    body_font_pt=11.0,
    section_font_pt=11.5,
    experience_font_pt=11.5,
    experience_line_spacing=1.05,
    body_spacing_after_pt=3.5,
    section_spacing_before_pt=6,
    section_spacing_after_pt=4,
    bullet_spacing_after_pt=3,
    entry_spacing_after_pt=7,
)


COMPACT_PROFILE = LayoutProfile(
    name="compact",
    chars_per_line=105,
    lines_per_page=52,
    body_font_pt=10.5,
    section_font_pt=11.5,
    experience_font_pt=11.0,
    experience_line_spacing=1.04,
    body_spacing_after_pt=2,
    section_spacing_before_pt=4,
    section_spacing_after_pt=3,
    bullet_spacing_after_pt=2,
    entry_spacing_after_pt=5,
)


MINIMUM_SAFE_PROFILE = LayoutProfile(
    name="minimum-safe",
    chars_per_line=105,
    lines_per_page=54,
    body_font_pt=10.0,
    section_font_pt=11.5,
    experience_font_pt=10.5,
    experience_line_spacing=1.02,
    body_spacing_after_pt=1,
    section_spacing_before_pt=2,
    section_spacing_after_pt=2,
    bullet_spacing_after_pt=1,
    entry_spacing_after_pt=2,
)


LAYOUT_PROFILES = (
    NORMAL_PROFILE,
    COMPACT_PROFILE,
    MINIMUM_SAFE_PROFILE,
)


@dataclass(frozen=True)
class OptimizationResult:
    profile: LayoutProfile
    layout: LayoutReport
    changed: bool


def profile_to_layout_settings(
    profile: LayoutProfile,
) -> LayoutSettings:
    return LayoutSettings(
        chars_per_line=profile.chars_per_line,
        lines_per_page=profile.lines_per_page,
    )


def optimize_layout(
    resume: Resume,
    rules: FormattingRules = DEFAULT_RULES,
) -> OptimizationResult:
    """
    Select the least-compressed formatting profile that fits.

    This function never changes resume content.
    """

    previous_profile = NORMAL_PROFILE
    fitting: list[tuple[float, LayoutProfile, LayoutReport]] = []

    for profile in LAYOUT_PROFILES:
        settings = profile_to_layout_settings(profile)

        layout = measure_resume(
            resume,
            rules=rules,
            settings=settings,
        )

        if layout.fits_two_pages:
            # Prefer readable typography, but among profiles that fit,
            # penalize excessive whitespace and large page-to-page density
            # differences. This makes "two pages" a visual target, not merely
            # a pagination constraint.
            underfill_page_one = max(
                0.0,
                0.70 - layout.page_one_utilization,
            )
            underfill_page_two = max(
                0.0,
                0.70 - layout.page_two_utilization,
            )
            balance_penalty = layout.utilization_balance

            # Compression is a small penalty; readability remains primary.
            compression_penalty = {
                "normal": 0.0,
                "compact": 0.03,
                "minimum-safe": 0.08,
            }.get(profile.name, 0.05)

            score = (
                underfill_page_one * 3.0
                + underfill_page_two * 3.0
                + balance_penalty * 1.5
                + compression_penalty
            )

            fitting.append((score, profile, layout))

        previous_profile = profile

    if fitting:
        _, profile, layout = min(
            fitting,
            key=lambda item: item[0],
        )
        return OptimizationResult(
            profile=profile,
            layout=layout,
            changed=profile != NORMAL_PROFILE,
        )

    settings = profile_to_layout_settings(previous_profile)

    return OptimizationResult(
        profile=previous_profile,
        layout=measure_resume(
            resume,
            rules=rules,
            settings=settings,
        ),
        changed=previous_profile != NORMAL_PROFILE,
    )
