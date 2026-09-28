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

    for profile in LAYOUT_PROFILES:
        settings = profile_to_layout_settings(profile)

        layout = measure_resume(
            resume,
            rules=rules,
            settings=settings,
        )

        if layout.fits_two_pages:
            return OptimizationResult(
                profile=profile,
                layout=layout,
                changed=profile != NORMAL_PROFILE,
            )

        previous_profile = profile

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
