"""
Greenhouse ATS Adapter.
"""
from typing import List
import httpx
from adapters.base import BaseAdapter
from models import JobOpening
from utils import parse_job_date, is_target_location, check_resume_match, classify_city, is_recent_enough

class GreenhouseAdapter(BaseAdapter):
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[JobOpening]:
        token = self.company_meta.get("token")
        if not token:
            return []

        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        jobs: List[JobOpening] = []

        try:
            resp = await client.get(url, headers=self.get_headers(), timeout=12.0)
            self.last_status = resp.status_code
            if resp.status_code != 200:
                self.last_error = f"HTTP {resp.status_code}"
                return []

            data = resp.json()
            raw_jobs = data.get("jobs", [])

            for j in raw_jobs:
                title = j.get("title", "").strip()
                loc_obj = j.get("location", {})
                loc_name = loc_obj.get("name", "") if isinstance(loc_obj, dict) else str(loc_obj)
                
                # Check department/team if present
                dept_list = [d.get("name", "") for d in j.get("departments", []) if isinstance(d, dict)]
                dept_name = ", ".join(dept_list)

                # Filter location
                if not is_target_location(loc_name):
                    continue

                # Filter by resume match
                is_match, score, reason = check_resume_match(title, dept_name)
                if not is_match:
                    continue

                # Parse updated date
                raw_updated = j.get("updated_at")
                dt, age_cat, age_text = parse_job_date(raw_updated)

                if not is_recent_enough(age_cat):
                    continue

                job_url = j.get("absolute_url", f"https://boards.greenhouse.io/{token}/jobs/{j.get('id')}")
                city_tag = classify_city(loc_name) or self.primary_city

                jobs.append(JobOpening(
                    company=self.name,
                    title=title,
                    location=loc_name or self.primary_city,
                    city_tag=city_tag,
                    url=job_url,
                    ats_type="greenhouse",
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
