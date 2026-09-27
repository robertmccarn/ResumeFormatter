from dataclasses import dataclass, field


@dataclass
class Contact:
    name: str
    email: str = ""
    phone: str = ""
    location: str = ""
    links: list[str] = field(default_factory=list)


@dataclass
class SkillCategory:
    name: str
    skills: list[str] = field(default_factory=list)


@dataclass
class Education:
    institution: str
    degree: str = ""
    dates: str = ""
    details: list[str] = field(default_factory=list)


@dataclass
class Certification:
    name: str
    issuer: str = ""
    date: str = ""


@dataclass
class Bullet:
    text: str


@dataclass
class Experience:
    company: str
    title: str
    dates: str = ""
    location: str = ""
    bullets: list[Bullet] = field(default_factory=list)


@dataclass
class Resume:
    contact: Contact
    headline: str = ""
    summary: str = ""
    skills: list[SkillCategory] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    certifications: list[Certification] = field(default_factory=list)
    experience: list[Experience] = field(default_factory=list)
