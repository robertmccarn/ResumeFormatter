import re

from .models import (
    Bullet,
    Certification,
    Contact,
    Education,
    Experience,
    Resume,
    SkillCategory,
)


SECTION_ALIASES = {
    "summary": "summary",
    "professional summary": "summary",
    "profile": "summary",
    "skills": "skills",
    "core skills": "skills",
    "technical skills": "skills",
    "education": "education",
    "certifications": "certifications",
    "certifications & licenses": "certifications",
    "professional experience": "experience",
    "experience": "experience",
    "work experience": "experience",
}

EMAIL_RE = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)

PHONE_RE = re.compile(
    r"(?:\+?1[\s.-]?)?"
    r"(?:\(?\d{3}\)?[\s.-]?)"
    r"\d{3}[\s.-]\d{4}"
)

YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def strip_markdown(line: str) -> str:
    """Remove lightweight Markdown decoration without changing content."""
    line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
    line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
    line = re.sub(r"__([^_]+)__", r"\1", line)
    line = re.sub(
        r"\[([^\]]+)\]\(mailto:[^)]+\)",
        r"\1",
        line,
        flags=re.IGNORECASE,
    )
    line = re.sub(
        r"\[([^\]]+)\]\(https?://[^)]+\)",
        r"\1",
        line,
        flags=re.IGNORECASE,
    )
    return line


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", strip_markdown(line).strip())


def is_section_heading(line: str) -> bool:
    normalized = normalize_line(line).lower()
    return normalized in SECTION_ALIASES


def clean_bullet(line: str) -> str:
    return re.sub(r"^\s*[-•▪◦*]\s*", "", line).strip()


def is_bullet(line: str) -> bool:
    return bool(re.match(r"^\s*[-•▪◦*]\s+", line))


def parse_contact(lines: list[str]) -> Contact:
    """Parse contact information from one or more lines after the name."""
    if not lines:
        raise ValueError("Resume is empty.")

    name = normalize_line(lines[0])

    contact_lines = [
        normalize_line(line)
        for line in lines[1:]
        if normalize_line(line)
    ]
    contact_text = " | ".join(contact_lines)

    email_match = EMAIL_RE.search(contact_text)
    phone_match = PHONE_RE.search(contact_text)

    email = email_match.group(0) if email_match else ""
    phone = phone_match.group(0) if phone_match else ""

    parts: list[str] = []
    for raw_line in contact_lines:
        parts.extend(
            part.strip()
            for part in re.split(r"\s*[|•]\s*", raw_line)
            if part.strip()
        )

    links = [
        part
        for part in parts
        if "linkedin.com" in part.lower()
        or "github.com" in part.lower()
        or part.startswith("http://")
        or part.startswith("https://")
    ]

    location = ""
    for part in parts:
        if part == email or part == phone:
            continue
        if part in links:
            continue
        # A line containing a headline/tagline should not become the location.
        if any(token in part.lower() for token in (
            "data engineer",
            "data analyst",
            "software engineer",
            "developer",
            "specialist",
            "analyst",
        )):
            continue
        location = part
        break

    return Contact(
        name=name,
        email=email,
        phone=phone,
        location=location,
        links=links,
    )


def split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for raw_line in lines:
        line = normalize_line(raw_line)

        if not line:
            # Preserve blank separators for experience parsing.
            if current_section is not None:
                sections.setdefault(current_section, []).append("")
            continue

        if is_section_heading(line):
            current_section = SECTION_ALIASES[line.lower()]
            sections.setdefault(current_section, [])
            continue

        if current_section is not None:
            sections[current_section].append(line)

    return sections


def parse_summary(lines: list[str]) -> str:
    return " ".join(line for line in lines if line).strip()


def parse_skills(lines: list[str]) -> list[SkillCategory]:
    categories: list[SkillCategory] = []

    for line in lines:
        if not line:
            continue

        if ":" in line:
            name, values = line.split(":", 1)
            skills = [
                item.strip()
                for item in re.split(r"[,;|]", values)
                if item.strip()
            ]
            categories.append(
                SkillCategory(name=name.strip(), skills=skills)
            )
        else:
            skills = [
                item.strip()
                for item in re.split(r"[,;|]", line)
                if item.strip()
            ]
            if skills:
                categories.append(
                    SkillCategory(name="", skills=skills)
                )

    return categories


def parse_education(lines: list[str]) -> list[Education]:
    education: list[Education] = []

    for line in lines:
        if not line:
            continue

        if is_bullet(line):
            if education:
                education[-1].details.append(clean_bullet(line))
            continue

        parts = [
            part.strip()
            for part in re.split(r"\s*\|\s*", line)
            if part.strip()
        ]

        if not parts:
            continue

        institution = parts[0]
        degree = parts[1] if len(parts) >= 2 else ""
        dates = parts[2] if len(parts) >= 3 else ""

        education.append(
            Education(
                institution=institution,
                degree=degree,
                dates=dates,
            )
        )

    return education


def parse_certifications(lines: list[str]) -> list[Certification]:
    certifications: list[Certification] = []

    for line in lines:
        if not line:
            continue

        line = clean_bullet(line)
        parts = [
            part.strip()
            for part in re.split(r"\s*\|\s*", line)
            if part.strip()
        ]

        if not parts:
            continue

        certifications.append(
            Certification(
                name=parts[0],
                date=parts[1] if len(parts) >= 2 else "",
            )
        )

    return certifications


def parse_experience_header(line: str) -> Experience:
    parts = [
        part.strip()
        for part in re.split(r"\s*\|\s*", line)
        if part.strip()
    ]

    if len(parts) >= 2:
        return Experience(
            company=parts[0],
            title=parts[1],
            dates=parts[2] if len(parts) >= 3 else "",
        )

    parts = [
        part.strip()
        for part in re.split(r"\s+[—–-]\s+", line)
        if part.strip()
    ]

    if len(parts) >= 2:
        return Experience(
            company=parts[0],
            title=parts[1],
            dates=parts[2] if len(parts) >= 3 else "",
        )

    return Experience(company=line, title="")


def parse_experience_header_block(lines: list[str]) -> Experience:
    cleaned = [
        normalize_line(line)
        for line in lines
        if normalize_line(line)
    ]

    if not cleaned:
        raise ValueError("Experience header cannot be empty.")

    if len(cleaned) == 1:
        return parse_experience_header(cleaned[0])

    if len(cleaned) == 2:
        # Common multiline form:
        # Company / engagement
        # Title | dates
        if YEAR_RE.search(cleaned[1]):
            parts = [
                part.strip()
                for part in re.split(r"\s*\|\s*", cleaned[1])
                if part.strip()
            ]
            return Experience(
                company=cleaned[0],
                title=parts[0],
                dates=parts[1] if len(parts) >= 2 else "",
            )
        return Experience(company=cleaned[0], title=cleaned[1])

    if len(cleaned) == 3:
        if YEAR_RE.search(cleaned[1]):
            parts = [
                part.strip()
                for part in re.split(r"\s*\|\s*", cleaned[1])
                if part.strip()
            ]
            return Experience(
                company=cleaned[0],
                subtitle="",
                title=parts[0],
                dates=parts[1] if len(parts) >= 2 else cleaned[2],
            )

        return Experience(
            company=cleaned[0],
            subtitle=cleaned[1],
            title=cleaned[2],
        )

    return Experience(
        company=cleaned[0],
        subtitle=" | ".join(cleaned[1:-2]),
        title=cleaned[-2],
        dates=cleaned[-1],
    )


def _is_role_line(line: str) -> bool:
    """Identify a role/date line in plain pasted resume text."""
    return bool(
        YEAR_RE.search(line)
        and (
            "|" in line
            or "—" in line
            or "–" in line
            or re.search(r"\s-\s", line)
        )
    )


def parse_experience(lines: list[str]) -> list[Experience]:
    """Parse both explicitly bulleted and clean, bulletless pasted resumes."""
    normalized = [normalize_line(line) if line else "" for line in lines]
    experiences: list[Experience] = []

    current: Experience | None = None
    pending_header: list[str] = []

    for line in normalized:
        if not line:
            continue

        if is_bullet(line):
            if current is None:
                if pending_header:
                    current = parse_experience_header_block(pending_header)
                    pending_header = []
                else:
                    continue

            current.bullets.append(Bullet(text=clean_bullet(line)))
            continue

        if current is None:
            pending_header.append(line)

            if _is_role_line(line):
                current = parse_experience_header_block(pending_header)
                pending_header = []

            continue

        # Once a role has started, a new role/date line means the current
        # experience has ended. The immediately preceding non-bullet line
        # becomes the next company's header.
        if _is_role_line(line):
            experiences.append(current)
            pending_header = [line]
            current = None
            continue

        # Unbulleted narrative lines are treated as experience bullets.
        current.bullets.append(Bullet(text=line))

    if current is not None:
        experiences.append(current)
    elif pending_header:
        experiences.append(parse_experience_header_block(pending_header))

    return experiences


def parse_resume(text: str) -> Resume:
    if not text or not text.strip():
        raise ValueError("Resume text cannot be empty.")

    raw_lines = text.splitlines()
    nonempty_lines = [
        line
        for line in raw_lines
        if normalize_line(line)
    ]

    if not nonempty_lines:
        raise ValueError("Resume text cannot be empty.")

    # The first recognized section marks the end of the header/contact area.
    first_section_index = next(
        (
            index
            for index, line in enumerate(raw_lines)
            if is_section_heading(line)
        ),
        None,
    )

    if first_section_index is None:
        raise ValueError(
            "Resume requires at least one recognized section."
        )

    header_lines = raw_lines[:first_section_index]
    contact = parse_contact(header_lines)

    contact_values = {
        contact.email,
        contact.phone,
        *contact.links,
        contact.location,
    }

    headline_candidates: list[str] = []
    for line in header_lines[1:]:
        normalized = normalize_line(line)
        if not normalized:
            continue
        if normalized in contact_values:
            continue
        if EMAIL_RE.search(normalized) or PHONE_RE.search(normalized):
            continue
        if "linkedin.com" in normalized.lower() or "github.com" in normalized.lower():
            continue
        headline_candidates.append(normalized)

    headline = " | ".join(headline_candidates)

    remaining = raw_lines[first_section_index:]
    sections = split_sections(remaining)

    return Resume(
        contact=contact,
        headline=headline,
        summary=parse_summary(sections.get("summary", [])),
        skills=parse_skills(sections.get("skills", [])),
        education=parse_education(sections.get("education", [])),
        certifications=parse_certifications(
            sections.get("certifications", [])
        ),
        experience=parse_experience(sections.get("experience", [])),
    )
