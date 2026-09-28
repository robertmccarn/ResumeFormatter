from __future__ import annotations

import argparse
import sys
from pathlib import Path

from resume_formatter.compiler import compile_resume


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile resume text into a deterministic DOCX."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the plain-text resume input.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("formatted_resume.docx"),
        help="Output DOCX path (default: formatted_resume.docx).",
    )
    return parser


def run_cli(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        return 2

    if not args.input.is_file():
        print(f"ERROR: Input path is not a file: {args.input}", file=sys.stderr)
        return 2

    try:
        text = args.input.read_text(encoding="utf-8")
        result = compile_resume(text, args.output)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print("Resume Compiler")
    print("-" * 32)
    print(f"Input:       {args.input}")
    print(f"Output:      {result.output_path or args.output}")
    print(f"Profile:     {result.audit.profile.name}")
    print(f"Estimated:   {result.audit.estimated_pages} pages")

    validation = result.audit.actual_validation

    if validation.page_count is not None:
        print(f"Actual:      {validation.page_count} pages")
    else:
        print("Actual:      unavailable")

    if validation.experience_page is not None:
        print(f"Experience:  page {validation.experience_page}")
    else:
        print("Experience:  unverified")

    print(f"Trimmed:     {'yes' if result.audit.trimmed else 'no'}")

    if result.success:
        print()
        print("Status:      SUCCESS")
        return 0

    print()
    print("Status:      INCOMPLETE")

    for issue in result.audit.structural_errors:
        print(f"Reason:      {issue}")

    for issue in validation.issues:
        print(f"Reason:      {issue}")

    return 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args or args == ["--gui"]:
        from resume_formatter.gui import run_gui

        run_gui()
        return 0

    return run_cli(args)


if __name__ == "__main__":
    raise SystemExit(main())
