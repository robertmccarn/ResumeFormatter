from resume_formatter.models import Contact, Experience, SkillCategory
from resume_formatter.parser import parse_resume


SAMPLE_RESUME = """
Robert McCarn
robert@example.com | 555-555-5555 | Spring, TX | linkedin.com/in/robert

Data Engineer

SUMMARY
Data Engineer with 4+ years of experience building and maintaining data solutions.
Experienced in SQL Server, Azure, ETL, and data quality.

CORE SKILLS
Databases: SQL Server, Azure SQL
Cloud: Azure Synapse, ADLS Gen2
Languages: T-SQL, Python, PowerShell

EDUCATION
University of Houston | BBA, Management Information Systems | 2021

CERTIFICATIONS
Microsoft Fabric DP-700 | 2026
AWS Certified AI Practitioner | 2025

PROFESSIONAL EXPERIENCE
TEKsystems Global Services | Data Engineer | 2022–Present
- Developed T-SQL stored procedures supporting nightly data processing.
- Supported Guidewire data modernization initiatives.
- Performed query runtime and performance tuning.

Retail Company | Store Manager | 2015–2018
- Managed daily store operations.
- Trained and supported employees.
"""


MULTILINE_EXPERIENCE_RESUME = """
Robert McCarn
robert@example.com | 555-555-5555 | Spring, TX

Data Engineer

SUMMARY
Data Engineer with enterprise experience.

PROFESSIONAL EXPERIENCE
TEKsystems Global Services
Berkshire Hathaway Engagement
Data Engineer
2022 – Present
- Build and support production data pipelines.
- Develop SQL data solutions.
- Troubleshoot production data issues.

University of Houston
C.T. Bauer College of Business
Project Analyst, Office of Digital Learning / Academic Support Assistant
2018 – 2020
- Managed operational data.
- Automated recurring reporting.
- Delivered analytical reports.
"""


def test_parse_contact():
    resume = parse_resume(SAMPLE_RESUME)

    assert resume.contact.name == "Robert McCarn"
    assert resume.contact.email == "robert@example.com"
    assert resume.contact.phone == "555-555-5555"
    assert resume.contact.location == "Spring, TX"
    assert "linkedin.com/in/robert" in resume.contact.links


def test_parse_headline():
    resume = parse_resume(SAMPLE_RESUME)

    assert resume.headline == "Data Engineer"


def test_parse_summary():
    resume = parse_resume(SAMPLE_RESUME)

    assert "4+ years" in resume.summary
    assert "SQL Server" in resume.summary


def test_parse_skills():
    resume = parse_resume(SAMPLE_RESUME)

    assert len(resume.skills) == 3

    assert resume.skills[0].name == "Databases"
    assert "SQL Server" in resume.skills[0].skills
    assert "Azure SQL" in resume.skills[0].skills

    assert resume.skills[1].name == "Cloud"
    assert "Azure Synapse" in resume.skills[1].skills


def test_parse_education():
    resume = parse_resume(SAMPLE_RESUME)

    assert len(resume.education) == 1
    assert resume.education[0].institution == "University of Houston"


def test_parse_certifications():
    resume = parse_resume(SAMPLE_RESUME)

    assert len(resume.certifications) == 2
    assert resume.certifications[0].name == "Microsoft Fabric DP-700"
    assert resume.certifications[0].date == "2026"


def test_parse_experience():
    resume = parse_resume(SAMPLE_RESUME)

    assert len(resume.experience) == 2

    first = resume.experience[0]

    assert first.company == "TEKsystems Global Services"
    assert first.title == "Data Engineer"
    assert first.dates == "2022–Present"

    assert len(first.bullets) == 3
    assert "T-SQL stored procedures" in first.bullets[0].text


def test_parse_multiline_experience_headers():
    resume = parse_resume(MULTILINE_EXPERIENCE_RESUME)

    assert len(resume.experience) == 2

    first = resume.experience[0]
    assert first.company == "TEKsystems Global Services"
    assert first.subtitle == "Berkshire Hathaway Engagement"
    assert first.title == "Data Engineer"
    assert first.dates == "2022 – Present"
    assert len(first.bullets) == 3

    second = resume.experience[1]
    assert second.company == "University of Houston"
    assert second.subtitle == "C.T. Bauer College of Business"
    assert second.title == (
        "Project Analyst, Office of Digital Learning / "
        "Academic Support Assistant"
    )
    assert second.dates == "2018 – 2020"


def test_parse_empty_resume():
    try:
        parse_resume("")
        assert False, "Expected ValueError"
    except ValueError:
        pass



BULLETLESS_PASTED_RESUME = """
Robert McCarn
Spring, TX
(713) 517-8743
[robertmccarn@gmail.com](mailto:robertmccarn@gmail.com)
linkedin.com/in/robertmccarn

DATA ENGINEER | ANALYTICS ENGINEER
SQL | Power BI | Azure | Data Warehousing | Microsoft Fabric

PROFESSIONAL SUMMARY
Data Engineer with 4+ years of experience developing enterprise data solutions.

CORE SKILLS
SQL & Data Engineering: Advanced T-SQL, SQL Server, Stored Procedures
ETL & Cloud Data: Azure Data Factory, Azure Synapse Analytics, Microsoft Fabric

CERTIFICATIONS
Microsoft Certified: Fabric Data Engineer Associate (DP-700) — 2026

PROFESSIONAL EXPERIENCE
TEKsystems Global Services — Berkshire Hathaway Engagement
Data Engineer | 2022 – Present

Develop and optimize SQL Server data solutions supporting enterprise data warehouse modernization.

Design complex T-SQL queries, stored procedures, and transformation logic.

Build and maintain ETL/ELT pipelines using Azure Data Factory and SQL Server.

University of Houston — C.T. Bauer College of Business
Project Analyst, Office of Digital Learning / Academic Support Assistant | 2018 – 2020

Managed and analyzed data for 2,200+ students.

Automated recurring data extraction and reporting workflows.
"""


def test_parse_bulletless_pasted_resume():
    resume = parse_resume(BULLETLESS_PASTED_RESUME)

    assert resume.contact.name == "Robert McCarn"
    assert resume.contact.location == "Spring, TX"
    assert resume.contact.phone == "(713) 517-8743"
    assert resume.contact.email == "robertmccarn@gmail.com"
    assert "linkedin.com/in/robertmccarn" in resume.contact.links

    assert resume.headline == (
        "DATA ENGINEER | ANALYTICS ENGINEER | "
        "SQL | Power BI | Azure | Data Warehousing | Microsoft Fabric"
    )

    assert len(resume.experience) == 2

    first = resume.experience[0]
    assert first.company == "TEKsystems Global Services — Berkshire Hathaway Engagement"
    assert first.title == "Data Engineer"
    assert first.dates == "2022 – Present"
    assert len(first.bullets) == 3
    assert "SQL Server data solutions" in first.bullets[0].text

    second = resume.experience[1]
    assert second.company == "University of Houston — C.T. Bauer College of Business"
    assert second.title == (
        "Project Analyst, Office of Digital Learning / "
        "Academic Support Assistant"
    )
    assert second.dates == "2018 – 2020"
    assert len(second.bullets) == 2
