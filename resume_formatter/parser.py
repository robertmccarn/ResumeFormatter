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


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def is_section_heading(line: str) -> bool:
    normalized = normalize_line(line).lower()
    return normalized in SECTION_ALIASES


def clean_bullet(line: str) -> str:
    return re.sub(r"^\s*[-•▪◦*]\s*", "", line).strip()


def is_bullet(line: str) -> bool:
    return bool(re.match(r"^\s*[-•▪◦*]\s+", line))


def parse_contact(lines: list[str]) -> Contact:
    if not lines:
        raise ValueError("Resume is empty.")

    name = normalize_line(lines[0])

    contact_line = normalize_line(lines[1]) if len(lines) > 1 else ""

    email_match = re.search(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        contact_line,
        re.IGNORECASE,
    )

    phone_match = re.search(
        r"(?:\+?1[\s.-]?)?"
        r"(?:\(?\d{3}\)?[\s.-]?)"
        r"\d{3}[\s.-]\d{4}",
        contact_line,
    )

    email = email_match.group(0) if email_match else ""
    phone = phone_match.group(0) if phone_match else ""

    parts = [
        part.strip()
        for part in re.split(r"\s*[|•]\s*", contact_line)
        if part.strip()
    ]

    location = ""

    for part in parts:
        if part == email or part == phone:
            continue

        if "linkedin.com" in part.lower() or "github.com" in part.lower():
            continue

        location = part
        break

    links = [
        part
        for part in parts
        if "linkedin.com" in part.lower()
        or "github.com" in part.lower()
        or part.startswith("http://")
        or part.startswith("https://")
    ]

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
            continue

        if is_section_heading(line):
            current_section = SECTION_ALIASES[line.lower()]
            sections.setdefault(current_section, [])
            continue

        if current_section is not None:
            sections[current_section].append(line)

    return sections


def parse_summary(lines: list[str]) -> str:
    return " ".join(lines).strip()


def parse_skills(lines: list[str]) -> list[SkillCategory]:
    categories: list[SkillCategory] = []

    for line in lines:
        if ":" in line:
            name, values = line.split(":", 1)

            skills = [
                item.strip()
                for item in re.split(r"[,;|]", values)
                if item.strip()
            ]

            categories.append(
                SkillCategory(
                    name=name.strip(),
                    skills=skills,
                )
            )
        else:
            skills = [
                item.strip()
                for item in re.split(r"[,;|]", line)
                if item.strip()
            ]

            if skills:
                categories.append(
                    SkillCategory(
                        name="",
                        skills=skills,
                    )
                )

    return categories


def parse_education(lines: list[str]) -> list[Education]:
    education: list[Education] = []

    for line in lines:
        if is_bullet(line):
            if education:
                education[-1].details.append(
                    clean_bullet(line)
                )
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
        line = clean_bullet(line)

        parts = [
            part.strip()
            for part in re.split(r"\s*\|\s*", line)
            if part.strip()
        ]

        if not parts:
            continue

        name = parts[0]
        date = parts[1] if len(parts) >= 2 else ""

        certifications.append(
            Certification(
                name=name,
                date=date,
            )
        )

    return certifications


def parse_experience(lines: list[str]) -> list[Experience]:
    experiences: list[Experience] = []

    current: Experience | None = None

    for line in lines:
        if is_bullet(line):
            if current is not None:
                current.bullets.append(
                    Bullet(text=clean_bullet(line))
                )
            continue

        if current is not None:
            experiences.append(current)

        current = parse_experience_header(line)

    if current is not None:
        experiences.append(current)

    return experiences


def parse_experience_header(line: str) -> Experience:
    parts = [
        part.strip()
        for part in re.split(r"\s*\|\s*", line)
        if part.strip()
    ]

    if len(parts) >= 2:
        company = parts[0]
        title = parts[1]
        dates = parts[2] if len(parts) >= 3 else ""

        return Experience(
            company=company,
            title=title,
            dates=dates,
        )

    # Fallback for "Company — Title — Dates"
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

    return Experience(
        company=line,
        title="",
    )


def parse_resume(text: str) -> Resume:
    if not text or not text.strip():
        raise ValueError("Resume text cannot be empty.")

    lines = [line.rstrip() for line in text.splitlines()]

    nonempty_lines = [
        line
        for line in lines
        if normalize_line(line)
    ]

    if not nonempty_lines:
        raise ValueError("Resume text cannot be empty.")

    contact = parse_contact(nonempty_lines)

    remaining = nonempty_lines[2:]

    sections = split_sections(remaining)

    headline = ""

    # Text before the first recognized section is treated as the headline.
    for line in remaining:
        if is_section_heading(line):
            break

        headline = line
        break

    return Resume(
        contact=contact,
        headline=headline,
        summary=parse_summary(
            sections.get("summary", [])
        ),
        skills=parse_skills(
            sections.get("skills", [])
        ),
        education=parse_education(
            sections.get("education", [])
        ),
        certifications=parse_certifications(
            sections.get("certifications", [])
        ),
        experience=parse_experience(
            sections.get("experience", [])
        ),
    )
