from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .layout import measure_resume
from .models import Resume
from .optimizer import (
    LAYOUT_PROFILES,
    LayoutProfile,
    optimize_layout,
    profile_to_layout_settings,
)
from .parser import parse_resume
from .renderer import render_resume
from .rules import (
    DEFAULT_RULES,
    FormattingRules,
    validate_resume_structure,
)
from .trimmer import TrimReport, trim_resume
from .validator import ValidationResult, validate_docx


@dataclass
class CompilationAudit:
    profile: LayoutProfile
    estimated_pages: int
    actual_validation: ValidationResult
    trimmed: bool = False
    trim_report: TrimReport | None = None
    structural_errors: list[str] = field(default_factory=list)


@dataclass
class CompilationResult:
    resume: Resume
    output_path: Path | None
    audit: CompilationAudit
    success: bool


def compile_resume(
    text: str,
    output_path: str | Path,
    rules: FormattingRules = DEFAULT_RULES,
) -> CompilationResult:
    resume = parse_resume(text)

    structural_errors = validate_resume_structure(
        resume,
        rules=rules,
    )

    if structural_errors:
        audit = CompilationAudit(
            profile=LAYOUT_PROFILES[0],
            estimated_pages=0,
            actual_validation=ValidationResult(
                available=False,
                valid=False,
                page_count=None,
                experience_page=None,
                issues=("Structural validation failed.",),
            ),
            structural_errors=structural_errors,
        )

        return CompilationResult(
            resume=resume,
            output_path=None,
            audit=audit,
            success=False,
        )

    baseline = optimize_layout(
        resume,
        rules=rules,
    )

    working_resume = resume
    trim_report: TrimReport | None = None
    last_layout = baseline.layout
    last_profile = baseline.profile
    candidate_path = Path(output_path)

    for profile in LAYOUT_PROFILES:
        settings = profile_to_layout_settings(profile)

        layout = measure_resume(
            working_resume,
            rules=rules,
            settings=settings,
        )

        last_layout = layout
        last_profile = profile

        if not layout.fits_two_pages:
            trimmed = trim_resume(
                working_resume,
                rules=rules,
                settings=settings,
            )

            if trimmed.report.changed:
                working_resume = trimmed.resume
                trim_report = trimmed.report
                last_layout = trimmed.report.final_analysis.layout

        render_resume(
            working_resume,
            candidate_path,
            profile=profile,
        )

        validation = validate_docx(
            candidate_path,
            max_pages=rules.max_pages,
            experience_starts_page=rules.experience_starts_page,
        )

        audit = CompilationAudit(
            profile=profile,
            estimated_pages=last_layout.page_count_estimate,
            actual_validation=validation,
            trimmed=trim_report is not None,
            trim_report=trim_report,
        )

        if validation.available and validation.valid:
            return CompilationResult(
                resume=working_resume,
                output_path=candidate_path,
                audit=audit,
                success=True,
            )

    final_validation = validate_docx(
        candidate_path,
        max_pages=rules.max_pages,
        experience_starts_page=rules.experience_starts_page,
    )

    final_audit = CompilationAudit(
        profile=last_profile,
        estimated_pages=last_layout.page_count_estimate,
        actual_validation=final_validation,
        trimmed=trim_report is not None,
        trim_report=trim_report,
    )

    return CompilationResult(
        resume=working_resume,
        output_path=candidate_path if candidate_path.exists() else None,
        audit=final_audit,
        success=False,
    )
