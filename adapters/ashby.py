"""
Ashby ATS Adapter.
"""
from typing import List
import httpx
from adapters.base import BaseAdapter
from models import JobOpening
from utils import parse_job_date, is_target_location, check_resume_match, classify_city, is_recent_enough

class AshbyAdapter(BaseAdapter):
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[JobOpening]:
        token = self.company_meta.get("token")
        if not token:
            return []

        url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
        jobs: List[JobOpening] = []

        try:
            resp = await client.get(url, headers=self.get_headers(), timeout=12.0)
            if resp.status_code != 200:
                return []

            data = resp.json()
            raw_jobs = data.get("jobs", [])

            for j in raw_jobs:
                title = j.get("title", "").strip()
                loc_name = j.get("location", "")
                dept_name = j.get("department", "")

                # Filter location
                if not is_target_location(loc_name):
                    continue

                # Filter by resume match
                is_match, score, reason = check_resume_match(title, dept_name)
                if not is_match:
                    continue

                # PublishedAt is ISO timestamp
                raw_date = j.get("publishedAt")
                dt, age_cat, age_text = parse_job_date(raw_date)

                if not is_recent_enough(age_cat):
                    continue

                job_url = j.get("jobUrl", f"https://jobs.ashbyhq.com/{token}")
                city_tag = classify_city(loc_name) or self.primary_city

                jobs.append(JobOpening(
                    company=self.name,
                    title=title,
                    location=loc_name or self.primary_city,
                    city_tag=city_tag,
                    url=job_url,
                    ats_type="ashby",
                    department=dept_name,
                    posted_at=dt,
                    age_category=age_cat,
                    age_text=age_text,
                    match_reason=reason,
                    match_score=score,
                ))

        except Exception:
            pass

        return jobs
