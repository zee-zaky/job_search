# Antigravity CV Tailoring Workspace

Use this folder for agent-driven CV tailoring only. Keep generated CVs faithful to the candidate evidence in `references/`, the source DOCX templates in `templates/docx/`, and the job advert text stored in the application database.

Required workflow:

1. Load starred jobs only.
2. Classify each job into one or more supported categories: `Integration`, `AI`, `BA`, `Sales`, `Dynamics 365`.
3. Select the closest DOCX template from `resources/template-map.yaml`.
4. Use `references/cv-format-and-faithfulness.md` before writing or editing CV content.
5. Use the relevant `references/category-guides/*.md` file before tailoring title, summary, capabilities, career summary, and project examples.
6. Do not invent employers, dates, certifications, degrees, technologies, metrics, or project outcomes.
7. Adjust role titles only when the underlying duties and project evidence support the wording.
8. Store each generated CV package under `/mnt/d/OneDrive/Work Related/Career Related/CV/Generated/{Employer}/{yyyymmdd - Job Title}/`.
9. Generate four files per job: tailored CV DOCX, cover letter DOCX, CV PDF, and cover letter PDF.
10. After all four files exist, update the job record with `status = cv_generated` and `generated_cv_path` pointing to the CV DOCX.
