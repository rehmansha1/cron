"""
Lever ATS Adapter.
"""
from typing import List
import httpx
from adapters.base import BaseAdapter
from models import JobOpening
from utils import parse_job_date, is_target_location, check_resume_match, classify_city, is_recent_enough

class LeverAdapter(BaseAdapter):
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[JobOpening]:
        token = self.company_meta.get("token")
        if not token:
            return []

        url = f"https://api.lever.co/v0/postings/{token}?mode=json"
        jobs: List[JobOpening] = []

        try:
            resp = await client.get(url, headers=self.get_headers(), timeout=12.0)
            self.last_status = resp.status_code
            if resp.status_code != 200:
                self.last_error = f"HTTP {resp.status_code}"
                return []

            raw_jobs = resp.json()
            if not isinstance(raw_jobs, list):
                return []

            for j in raw_jobs:
                title = j.get("text", "").strip()
                cats = j.get("categories", {}) or {}
                loc_name = cats.get("location", "")
                team_name = cats.get("team", "") or cats.get("department", "")

                # Filter location
                if not is_target_location(loc_name):
                    continue

                # Filter by resume match
                is_match, score, reason = check_resume_match(title, team_name)
                if not is_match:
                    continue

                # Lever timestamps are in epoch milliseconds: createdAt
                raw_created = j.get("createdAt")
                dt, age_cat, age_text = parse_job_date(raw_created)

                if not is_recent_enough(age_cat):
                    continue

                job_url = j.get("hostedUrl", f"https://jobs.lever.co/{token}/{j.get('id')}")
                city_tag = classify_city(loc_name) or self.primary_city

                jobs.append(JobOpening(
                    company=self.name,
                    title=title,
                    location=loc_name or self.primary_city,
                    city_tag=city_tag,
                    url=job_url,
                    ats_type="lever",
                    department=team_name,
                    posted_at=dt,
                    age_category=age_cat,
                    age_text=age_text,
                    match_reason=reason,
                    match_score=score,
                ))

        except Exception:
            pass

        return jobs
