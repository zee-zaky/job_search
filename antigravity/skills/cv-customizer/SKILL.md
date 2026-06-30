---
name: cv-customizer
description: Generate faithful, job-specific CV drafts from starred jobs in the local job-search tracker. Use when an agent needs to inspect favourite/starred jobs, classify them as Integration, AI, BA, Sales, or Dynamics 365 roles, select the closest DOCX CV template, and tailor Muhammad Zaky's CV using verified source CV content without inventing experience.
---

# CV Customizer

## Core Workflow

1. List starred jobs with `python antigravity/scripts/list_starred_jobs.py`.
2. Classify each job with `antigravity/resources/category-keywords.yaml` or `python antigravity/scripts/classify_job.py <job-json>`.
3. Select the DOCX template and category reference from `antigravity/resources/template-map.yaml`.
4. Read `antigravity/references/cv-format-and-faithfulness.md` and `antigravity/references/candidate-profile.md`.
5. Read only the relevant category guide from `antigravity/references/category-guides/`.
6. Use source evidence from `antigravity/references/source-cv-extracts/` and the selected DOCX under `antigravity/templates/docx/`.
7. Prepare the required output folder with `python antigravity/scripts/prepare_output_folder.py <job_id>`.
8. Draft or generate the tailored CV using the section order in `antigravity/resources/cv-section-order.yaml`.
9. Draft a tailored cover letter using `antigravity/templates/content/cover-letter-template.md`.
10. Save CV DOCX, cover letter DOCX, CV PDF, and cover letter PDF under `/mnt/d/OneDrive/Work Related/Career Related/CV/Generated/{Employer}/{yyyymmdd - Job Title}/`.
11. Update the job only after all four files exist with `python antigravity/scripts/mark_cv_generated.py <job_id> --cv-docx <path> --cover-letter-docx <path> --cv-pdf <path> --cover-letter-pdf <path>`.

## Required CV Structure

- Header.
- Professional Summary: category-specific and one formatted first page.
- Core Capabilities: 3-4 groups, 3-4 items per group.
- Education, Certifications, Languages and Skills summary.
- Career Summary.
- Some Key Roles and Projects.
- Cover letter: one-page recruiter-facing letter in DOCX and PDF format.

## Faithfulness Rules

- Do not invent employers, dates, certifications, technologies, project outcomes, publications, or metrics.
- Tailor by selecting, compressing, reordering, and faithfully reframing existing evidence.
- Adjust career titles only when the duties and projects support the category wording.
- Prefer specific project evidence from Westpac, MSD, TWG, NSW RMS, Alinma, IBM, university AI projects, or the business consultancy capstone.
- If the job advert asks for something not evidenced, avoid claiming it directly.
- Do not mark the database record as generated until both Word files and both PDF files exist.

## Output and Database Rules

- Base folder: `/mnt/d/OneDrive/Work Related/Career Related/CV/Generated`.
- Folder structure: `{Employer}/{yyyymmdd - Job Title}/`.
- Keep all generated artifacts for the same employer grouped under the employer folder.
- Save `generated_cv_path` as the generated CV DOCX path.
- Set job `status` to `cv_generated`.
- Use `antigravity/resources/output-locations.yaml` as the source of truth for file names and status.

## Category Routing

- **Integration**: use `category-guides/integration.md` and `integration-template.docx`.
- **AI**: use `category-guides/ai.md` and `ai-ba-template.docx`.
- **BA**: use `category-guides/ba.md` and `ba-template.docx`.
- **Sales**: use `category-guides/sales.md` and `integration-sales-template.docx`.
- **Dynamics 365**: use `category-guides/dynamics-365.md` and usually `ba-template.docx`.

When a role spans categories, use the dominant job-title category for the CV title and summary, then blend secondary category evidence into capabilities and project examples.
