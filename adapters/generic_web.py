"""
Generic Web Adapter: Scrapes custom company career pages that do not use standard ATS APIs.

Uses:
1. Schema.org 'JobPosting' structured JSON (application/ld+json)
2. Semantic HTML card/link heuristics via BeautifulSoup
"""
import json
import re
from typing import List
import httpx
from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from models import JobOpening
from utils import parse_job_date, is_target_location, check_resume_match, classify_city, is_recent_enough

class GenericWebAdapter(BaseAdapter):
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[JobOpening]:
        career_url = self.company_meta.get("url")
        if not career_url:
            return []

        jobs: List[JobOpening] = []

        html = ""
        try:
            resp = await client.get(career_url, headers=self.get_headers(), timeout=12.0)
            self.last_status = resp.status_code
            if resp.status_code == 200:
                html = resp.text
            else:
                self.last_error = f"HTTP {resp.status_code}"
        except Exception as e:
            self.last_error = f"Error: {type(e).__name__}"

        # If httpx was blocked (HTTP 403/429/400) by Cloudflare/WAF, attempt browser impersonation via curl_cffi
        if not html:
            try:
                from curl_cffi.requests import AsyncSession
                async with AsyncSession(impersonate="chrome124") as session:
                    c_resp = await session.get(career_url, timeout=12.0)
                    self.last_status = c_resp.status_code
                    if c_resp.status_code == 200:
                        html = c_resp.text
                        self.last_error = ""
                    else:
                        self.last_error = f"HTTP {c_resp.status_code}"
            except Exception:
                pass

        if not html:
            return []

        try:
            soup = BeautifulSoup(html, "html.parser")

            # ── Strategy 1: Check for Schema.org structured JSON-LD ─────────────
            ld_scripts = soup.find_all("script", type="application/ld+json")
            for script in ld_scripts:
                try:
                    data = json.loads(script.string or "{}")
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if item.get("@type") == "JobPosting":
                            title = item.get("title", "").strip()
                            loc_info = item.get("jobLocation", {})
                            loc_name = ""
                            if isinstance(loc_info, dict):
                                addr = loc_info.get("address", {})
                                if isinstance(addr, dict):
                                    loc_name = f"{addr.get('addressLocality', '')}, {addr.get('addressCountry', '')}"
                                elif isinstance(addr, str):
                                    loc_name = addr

                            if not is_target_location(loc_name):
                                continue

                            is_match, score, reason = check_resume_match(title)
                            if not is_match:
                                continue

                            raw_date = item.get("datePosted")
                            dt, age_cat, age_text = parse_job_date(raw_date)
                            if not is_recent_enough(age_cat):
                                continue

                            job_url = item.get("url") or career_url
                            city_tag = classify_city(loc_name) or self.primary_city

                            jobs.append(JobOpening(
                                company=self.name,
                                title=title,
                                location=loc_name or self.primary_city,
                                city_tag=city_tag,
                                url=job_url,
                                ats_type="web_ldjson",
                                department="",
                                posted_at=dt,
                                age_category=age_cat,
                                age_text=age_text,
                                match_reason=reason,
                                match_score=score,
                            ))
                except Exception:
                    pass

            if jobs:
                return jobs

            # ── Strategy 2: HTML Job Card Heuristics ────────────────────────────
            # Look for job links or card containers
            candidate_links = soup.find_all("a", href=re.compile(r"/(?:job|career|position|opening|apply)/", re.I))
            seen_urls = set()

            for a in candidate_links:
                href = a.get("href", "")
                full_url = href if href.startswith("http") else httpx.URL(career_url).join(href)
                if str(full_url) in seen_urls:
                    continue
                seen_urls.add(str(full_url))

                title = a.get_text(strip=True)
                if not title or len(title) > 90 or len(title) < 4:
                    continue

                is_match, score, reason = check_resume_match(title)
                if not is_match:
                    continue

                # Check parent text for location or date indicators
                parent_text = a.parent.get_text(" ", strip=True) if a.parent else ""
                if not is_target_location(parent_text):
                    continue

                dt, age_cat, age_text = parse_job_date(parent_text)
                if not is_recent_enough(age_cat):
                    continue

                city_tag = classify_city(parent_text) or self.primary_city

                jobs.append(JobOpening(
                    company=self.name,
                    title=title,
                    location=self.primary_city,
                    city_tag=city_tag,
                    url=str(full_url),
                    ats_type="web_html",
                    department="",
                    posted_at=dt,
                    age_category=age_cat,
                    age_text=age_text or "Recent",
                    match_reason=reason,
                    match_score=score,
                ))

        except Exception:
            pass

        return jobs
