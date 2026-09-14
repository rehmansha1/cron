"""
Base adapter for ATS career scanners.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import httpx
from models import JobOpening
from config import REQUEST_HEADERS, DEFAULT_TIMEOUT

class BaseAdapter(ABC):
    def __init__(self, company_meta: Dict[str, Any]):
        self.company_meta = company_meta
        self.name = company_meta.get("name", "Unknown")
        self.primary_city = company_meta.get("city", "All")
        self.ats_type = company_meta.get("ats", "general")
        self.identifier = company_meta.get("token") or company_meta.get("url")
        self.last_status: int = 200
        self.last_error: str = ""

    @abstractmethod
    async def fetch_jobs(self, client: httpx.AsyncClient) -> List[JobOpening]:
        """Fetch and return normalized list of JobOpening objects."""
        pass

    def get_headers(self) -> Dict[str, str]:
        return REQUEST_HEADERS.copy()
