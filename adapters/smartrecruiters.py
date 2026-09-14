"""
SmartRecruiters ATS Adapter.
"""
from typing import List
import httpx
from adapters.base import BaseAdapter
from models import JobOpening
from utils import parse_job_date, is_target_location, check_resume_match, classify_city, is_recent_enough

class SmartRecruitersAdapter(BaseAdapter):
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[JobOpening]:
        token = self.company_meta.get("token")
        if not token:
            return []

        url = f"https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100"
        jobs: List[JobOpening] = []

        try:
            resp = await client.get(url, headers=self.get_headers(), timeout=12.0)
            self.last_status = resp.status_code
            if resp.status_code != 200:
                self.last_error = f"HTTP {resp.status_code}"
                return []

            data = resp.json()
            raw_jobs = data.get("content", [])

            for j in raw_jobs:
                title = j.get("name", "").strip()
                loc_obj = j.get("location", {}) or {}
                city = loc_obj.get("city", "")
                country = loc_obj.get("country", "")
                loc_str = f"{city}, {country}" if city else country

                # Filter location
                if not is_target_location(loc_str):
                    continue

                # Filter by resume match
                dept_obj = j.get("department", {}) or {}
                dept_name = dept_obj.get("label", "") if isinstance(dept_obj, dict) else str(dept_obj)
                is_match, score, reason = check_resume_match(title, dept_name)
                if not is_match:
                    continue

                # Released date is ISO string
                raw_date = j.get("releasedDate")
                dt, age_cat, age_text = parse_job_date(raw_date)

                if not is_recent_enough(age_cat):
                    continue

                job_id = j.get("id")
                job_url = f"https://jobs.smartrecruiters.com/{token}/{job_id}"
                city_tag = classify_city(loc_str) or self.primary_city

                jobs.append(JobOpening(
                    company=self.name,
                    title=title,
                    location=loc_str or self.primary_city,
                    city_tag=city_tag,
                    url=job_url,
                    ats_type="smartrecruiters",
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
