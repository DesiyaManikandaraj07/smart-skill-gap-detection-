"""Generate a sample resume PDF for demos and tests."""

from pathlib import Path

import fitz

TEXT = """Alex Rivera
alex.rivera@email.com | github.com/alexrivera

Skills
Python, JavaScript, React, SQL, Git, Pandas, scikit-learn, HTML, CSS

Education
B.Tech in Computer Science, State University, 2021 – 2025

Projects
- Campus Connect: React + Node campus events board
- Skill Matcher: Python NLP tool for resume skill extraction
- Sales Insights: SQL + Tableau dashboard on public retail data

Internships
- Data Intern at InsightLabs (Jun 2024 – Aug 2024): built ETL scripts in Python
- Web Intern at BrightApps (May 2023 – Jul 2023): React UI components

Experience
1.5 years of experience building full-stack prototypes and data notebooks

Certifications
Google Data Analytics (Coursera)
"""


def main():
    out = Path(__file__).resolve().parents[2] / "docs" / "sample_resume.pdf"
    doc = fitz.open()
    page = doc.new_page()
    # Simple multi-line insert
    y = 50
    for line in TEXT.strip().splitlines():
        page.insert_text((50, y), line, fontsize=11)
        y += 14
    doc.save(out)
    doc.close()
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
