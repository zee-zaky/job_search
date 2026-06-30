# CV Format and Faithfulness Rules

## Required CV Structure

1. Header with name, location, phone, email, and LinkedIn line.
2. Professional Summary. This must be tailored to the job category and fit on the first page in the selected Word template.
3. Core Capabilities. Use 3-4 capability groups with 3-4 strong items per group.
4. Education, Certifications, Languages and Skills summary.
5. Career Summary.
6. Some Key Roles and Projects.
7. Cover letter as a separate one-page DOCX using the same role positioning and faithful evidence.

## Faithfulness Rules

- Use only evidence present in the source CV extracts, DOCX templates, or job advert.
- Do not invent employers, job dates, degrees, certifications, awards, tools, client names, metrics, publications, or project outcomes.
- Tailor by selecting, reordering, compressing, and reframing verified experience.
- Adjust job titles only when duties overlap enough to be truthful. Example: a role involving requirements, stakeholder workshops, data validation, and delivery support may be framed as Senior Technical Business Analyst. A role involving integration architecture, middleware, APIs, and delivery governance may be framed as Integration Architect or Senior Integration Consultant.
- If a job asks for experience not evidenced, avoid pretending direct experience. Use adjacent truthful wording such as "exposure to", "worked across", "supported", or omit it.
- Prefer concrete examples from Westpac, MSD, TWG, NSW RMS, Alinma, IBM, university AI projects, and consultancy capstone work when relevant.

## Formatting Rules

- Start from the closest DOCX file in `antigravity/templates/docx/`.
- Preserve the same visual style, heading hierarchy, spacing, and section order.
- Keep the summary concise enough for one page.
- Keep capability bullets crisp and scannable.
- Avoid long keyword lists in the summary; put tool lists in the skills summary.

## Output Rules

- Store each generated package under `/mnt/d/OneDrive/Work Related/Career Related/CV/Generated/{Employer}/{yyyymmdd - Job Title}/`.
- The date in the folder name should use the job posting date when available; otherwise use the current date.
- Generate and save:
  - CV DOCX.
  - Cover letter DOCX.
  - CV PDF.
  - Cover letter PDF.
- Update the database only after all four files exist.
