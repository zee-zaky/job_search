#!/usr/bin/env python3
"""Classify a job JSON object into CV tailoring categories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def score_category(job: dict, category: dict) -> int:
    title = str(job.get("job_title") or "").lower()
    description = str(job.get("description") or "").lower()
    score = 0
    for keyword in category.get("title_keywords", []):
        if keyword.lower() in title:
            score += 3
    for keyword in category.get("description_keywords", []):
        if keyword.lower() in description:
            score += 1
    return score


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify jobs into supported CV categories.")
    parser.add_argument("job_json", help="Path to a JSON file containing one job or a list of jobs.")
    parser.add_argument("--categories", default="antigravity/resources/category-keywords.yaml")
    args = parser.parse_args()

    payload = json.loads(Path(args.job_json).read_text(encoding="utf-8"))
    jobs = payload if isinstance(payload, list) else [payload]
    categories = yaml.safe_load(Path(args.categories).read_text(encoding="utf-8"))["categories"]

    results = []
    for job in jobs:
        scored = [
            {"category": name, "score": score_category(job, category)}
            for name, category in categories.items()
        ]
        scored = [item for item in scored if item["score"] > 0]
        scored.sort(key=lambda item: item["score"], reverse=True)
        results.append({"job_id": job.get("id"), "job_title": job.get("job_title"), "matches": scored})

    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

