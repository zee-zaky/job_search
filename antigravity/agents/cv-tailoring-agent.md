# CV Tailoring Agent

## Purpose

Generate faithful, job-specific CV drafts for starred jobs in the job-search tracker.

## Inputs

- Starred jobs from SQLite: use `antigravity/scripts/list_starred_jobs.py`.
- Job advert fields: title, employer, description, location, source URL.
- CV evidence: `antigravity/references/source-cv-extracts/*.txt`.
- Formatting templates: `antigravity/templates/docx/*.docx`.
- Category guidance: `antigravity/references/category-guides/*.md`.
- Output location rules: `antigravity/resources/output-locations.yaml`.

## Workflow

1. Run `python antigravity/scripts/list_starred_jobs.py` from the repository root.
2. For each starred job, classify the role using `antigravity/resources/category-keywords.yaml`.
3. If multiple categories match, prioritise the job title first, then repeated requirements in the description.
4. Select a template via `antigravity/resources/template-map.yaml`.
5. Build a tailoring brief using `antigravity/templates/content/cv-tailoring-brief.md`.
6. Prepare the output folder with `python antigravity/scripts/prepare_output_folder.py <job_id>`.
7. Draft the CV in the section order from `antigravity/resources/cv-section-order.yaml`.
8. Draft the cover letter using `antigravity/templates/content/cover-letter-template.md`.
9. Preserve the source DOCX visual format by starting from the selected `.docx` template.
10. Save the tailored CV DOCX and cover letter DOCX under the generated employer/job folder.
11. Export both DOCX files to PDF in the same folder.
12. Mark the job as generated only after all four files exist:
    `python antigravity/scripts/mark_cv_generated.py <job_id> --cv-docx <path> --cover-letter-docx <path> --cv-pdf <path> --cover-letter-pdf <path>`.

## Quality Bar

- The CV must read as a natural, recruiter-facing document, not a keyword collage.
- The first page professional summary must fit one page in the selected DOCX format.
- Every tailored claim must be traceable to the sample CVs or job advert.
- Prefer concrete project examples over generic capability statements.
- Do not update the database until the CV DOCX, cover letter DOCX, CV PDF, and cover letter PDF all exist.
