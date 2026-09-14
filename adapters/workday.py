"""
Workday CXS API Adapter.
"""
from typing import List
import httpx
from adapters.base import BaseAdapter
from models import JobOpening
from utils import parse_job_date, is_target_location, check_resume_match, classify_city, is_recent_enough

class WorkdayAdapter(BaseAdapter):
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[JobOpening]:
        tenant = self.company_meta.get("tenant")
        board = self.company_meta.get("board", "Search") or self.company_meta.get("token", "Search")
        domain = self.company_meta.get("domain", f"{tenant}.wd1.myworkdayjobs.com")

        if not tenant:
            return []

        url = f"https://{domain}/wday/cxs/{tenant}/{board}/jobs"
        payload = {
            "appliedFacets": {},
            "limit": 20,
            "offset": 0,
            "searchText": ""
        }

        headers = self.get_headers()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        jobs: List[JobOpening] = []

        try:
            resp = await client.post(url, json=payload, headers=headers, timeout=14.0)
            if resp.status_code != 200:
                # Try alternate board if 'Search' failed
                if board != "Careers":
                    alt_url = f"https://{domain}/wday/cxs/{tenant}/Careers/jobs"
                    resp = await client.post(alt_url, json=payload, headers=headers, timeout=10.0)

            self.last_status = resp.status_code
            if resp.status_code != 200:
                self.last_error = f"HTTP {resp.status_code}"
                return []

            data = resp.json()
            postings = data.get("jobPostings", [])

            for j in postings:
                title = j.get("title", "").strip()
                loc_name = j.get("locationsText", "")

                # Filter location
                if not is_target_location(loc_name):
                    continue

                # Filter by resume match
                is_match, score, reason = check_resume_match(title)
                if not is_match:
                    continue

                # Workday provides 'postedOn' like 'Posted Today', 'Posted Yesterday', 'Posted 3 Days Ago'
                raw_posted = j.get("postedOn", "")
                dt, age_cat, age_text = parse_job_date(raw_posted)

                if not is_recent_enough(age_cat):
                    continue

                ext_path = j.get("externalPath", "")
                full_url = f"https://{domain}/en-US/{board}{ext_path}" if ext_path else f"https://{domain}"

                city_tag = classify_city(loc_name) or self.primary_city

                jobs.append(JobOpening(
                    company=self.name,
                    title=title,
                    location=loc_name or self.primary_city,
                    city_tag=city_tag,
                    url=full_url,
                    ats_type="workday",
                    department="",
                    posted_at=dt,
                    age_category=age_cat,
                    age_text=age_text or raw_posted,
                    match_reason=reason,
                    match_score=score,
                ))

        except Exception:
            pass

        return jobs
