"""
Custom API Adapters for Major Tech Employers (Amazon, etc.) & JSON Feeds.
"""
from typing import List
import httpx
from adapters.base import BaseAdapter
from models import JobOpening
from utils import parse_job_date, is_target_location, check_resume_match, classify_city, is_recent_enough

class AmazonJobsAdapter(BaseAdapter):
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[JobOpening]:
        # Amazon Jobs public search API for India
        url = "https://www.amazon.jobs/en/search.json?country=IND&result_limit=30&sort=recent"
        jobs: List[JobOpening] = []

        try:
            resp = await client.get(url, headers=self.get_headers(), timeout=12.0)
            if resp.status_code != 200:
                return []

            data = resp.json()
            raw_jobs = data.get("jobs", [])

            for j in raw_jobs:
                title = j.get("title", "").strip()
                city = j.get("city", "")
                loc_name = f"{city}, India"

                if not is_target_location(loc_name):
                    continue

                is_match, score, reason = check_resume_match(title)
                if not is_match:
                    continue

                raw_date = j.get("posted_date")  # e.g., "September 14, 2026" or ISO
                dt, age_cat, age_text = parse_job_date(raw_date)

                if not is_recent_enough(age_cat):
                    continue

                job_path = j.get("job_path", "")
                job_url = f"https://www.amazon.jobs{job_path}" if job_path else "https://www.amazon.jobs"
                city_tag = classify_city(loc_name) or "Bangalore"

                jobs.append(JobOpening(
                    company="Amazon",
                    title=title,
                    location=loc_name,
                    city_tag=city_tag,
                    url=job_url,
                    ats_type="amazon_api",
                    department=j.get("business_category", ""),
                    posted_at=dt,
                    age_category=age_cat,
                    age_text=age_text,
                    match_reason=reason,
                    match_score=score,
                ))
        except Exception:
            pass

        return jobs
