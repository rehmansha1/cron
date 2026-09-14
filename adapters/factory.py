"""
Adapter Factory to instantiate appropriate ATS scanner.
"""
from typing import Dict, Any, Optional
from adapters.base import BaseAdapter
from adapters.greenhouse import GreenhouseAdapter
from adapters.lever import LeverAdapter
from adapters.workday import WorkdayAdapter
from adapters.smartrecruiters import SmartRecruitersAdapter
from adapters.ashby import AshbyAdapter
from adapters.custom_apis import AmazonJobsAdapter
from adapters.generic_web import GenericWebAdapter

def get_adapter_for_company(company_meta: Dict[str, Any]) -> Optional[BaseAdapter]:
    ats = company_meta.get("ats", "").lower()

    if ats == "greenhouse":
        return GreenhouseAdapter(company_meta)
    elif ats == "lever":
        return LeverAdapter(company_meta)
    elif ats == "workday":
        return WorkdayAdapter(company_meta)
    elif ats == "smartrecruiters":
        return SmartRecruitersAdapter(company_meta)
    elif ats == "ashby":
        return AshbyAdapter(company_meta)
    elif ats == "amazon_api":
        return AmazonJobsAdapter(company_meta)
    elif ats in ("web", "custom", "html") or "url" in company_meta:
        return GenericWebAdapter(company_meta)

    return None
