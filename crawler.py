"""
Async Career Crawler Orchestrator.
"""
import json
import asyncio
from typing import List, Dict, Any, Tuple
import httpx
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from config import (
    BASE_DIR,
    DEFAULT_TIMEOUT,
    MAX_CONCURRENT_WORKERS,
)
from models import JobOpening
from adapters.factory import get_adapter_for_company

class CareerCrawler:
    def __init__(self, companies_file=None):
        self.companies_file = companies_file or (BASE_DIR / "companies.json")
        self.companies: List[Dict[str, Any]] = self._load_companies()

    def _load_companies(self) -> List[Dict[str, Any]]:
        try:
            with open(self.companies_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading companies.json: {e}")
            return []

    async def scan_all(self, show_progress: bool = True) -> Tuple[List[JobOpening], int]:
        """
        Concurrently scans all company career boards for recent tech openings.
        Returns: (all_recent_openings, total_companies_scanned)
        """
        all_jobs: List[JobOpening] = []
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_WORKERS)
        total_companies = len(self.companies)

        active_count = 0
        errored_count = 0
        error_summary: Dict[str, int] = {}

        async with httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=30, max_keepalive_connections=15)
        ) as client:

            async def scan_company(comp_meta: Dict[str, Any], progress=None, task_id=None):
                nonlocal active_count, errored_count
                async with semaphore:
                    adapter = get_adapter_for_company(comp_meta)
                    if not adapter:
                        errored_count += 1
                        error_summary["No Adapter"] = error_summary.get("No Adapter", 0) + 1
                        if progress and task_id:
                            progress.advance(task_id)
                        return []

                    try:
                        jobs = await adapter.fetch_jobs(client)
                        
                        # Auto-Fallback to GenericWebAdapter if primary ATS returned non-200 or failed
                        if (adapter.last_status != 200 or adapter.last_error) and comp_meta.get("ats") != "web":
                            fallback_url = comp_meta.get("url") or comp_meta.get("fallback_url")
                            if fallback_url:
                                from adapters.generic_web import GenericWebAdapter
                                fb_meta = {**comp_meta, "ats": "web", "url": fallback_url}
                                fb_adapter = GenericWebAdapter(fb_meta)
                                fb_jobs = await fb_adapter.fetch_jobs(client)
                                if fb_adapter.last_status == 200 and not fb_adapter.last_error:
                                    adapter = fb_adapter
                                    jobs = fb_jobs

                        if adapter.last_status == 200 and not adapter.last_error:
                            active_count += 1
                        else:
                            errored_count += 1
                            err_tag = adapter.last_error or f"HTTP {adapter.last_status}"
                            error_summary[err_tag] = error_summary.get(err_tag, 0) + 1
                        return jobs
                    except Exception as e:
                        # Attempt fallback on unhandled exception as well
                        fallback_url = comp_meta.get("url") or comp_meta.get("fallback_url")
                        if fallback_url and comp_meta.get("ats") != "web":
                            try:
                                from adapters.generic_web import GenericWebAdapter
                                fb_meta = {**comp_meta, "ats": "web", "url": fallback_url}
                                fb_adapter = GenericWebAdapter(fb_meta)
                                fb_jobs = await fb_adapter.fetch_jobs(client)
                                if fb_adapter.last_status == 200 and not fb_adapter.last_error:
                                    active_count += 1
                                    return fb_jobs
                            except Exception:
                                pass

                        errored_count += 1
                        err_tag = f"Error: {type(e).__name__}"
                        error_summary[err_tag] = error_summary.get(err_tag, 0) + 1
                        return []
                    finally:
                        if progress and task_id:
                            progress.advance(task_id)

            if show_progress:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold cyan]Scanning Career Portals...[/bold cyan]"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TextColumn("({task.completed}/{task.total} companies)"),
                    TimeElapsedColumn(),
                ) as progress:
                    task_id = progress.add_task("Scanning", total=total_companies)
                    tasks = [scan_company(comp, progress, task_id) for comp in self.companies]
                    results = await asyncio.gather(*tasks)
            else:
                tasks = [scan_company(comp) for comp in self.companies]
                results = await asyncio.gather(*tasks)

            for job_list in results:
                if job_list:
                    all_jobs.extend(job_list)

        # Sort jobs: Today first, then Yesterday, then Recent
        def sort_priority(j: JobOpening):
            if j.age_category == "Today":
                return (0, -(j.posted_at.timestamp() if j.posted_at else 0))
            elif j.age_category == "Yesterday":
                return (1, -(j.posted_at.timestamp() if j.posted_at else 0))
            else:
                return (2, -(j.posted_at.timestamp() if j.posted_at else 0))

        all_jobs.sort(key=sort_priority)
        stats = {
            "total": total_companies,
            "active": active_count,
            "errored": errored_count,
            "error_breakdown": error_summary
        }
        return all_jobs, stats
