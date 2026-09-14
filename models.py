"""
Data models for Job Openings.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import hashlib

@dataclass
class JobOpening:
    company: str
    title: str
    location: str
    url: str
    ats_type: str = "general"
    department: str = ""
    posted_at: Optional[datetime] = None
    age_category: str = "Recent"  # "Today", "Yesterday", "Recent (<48h)"
    age_text: str = ""
    city_tag: str = "General"  # "Chennai", "Bangalore", "Remote", "India"
    match_reason: str = ""     # e.g. "Full-Stack Match", "React.js Match"
    match_score: int = 0       # 0-100%
    first_seen_at: datetime = field(default_factory=datetime.utcnow)
    id: str = ""

    def __post_init__(self):
        if not self.id:
            # Generate deterministic unique hash from company + title + url
            raw_key = f"{self.company.strip().lower()}|{self.title.strip().lower()}|{self.url.strip()}"
            self.id = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

    def to_dict(self):
        d = asdict(self)
        if self.posted_at:
            d["posted_at"] = self.posted_at.isoformat()
        if self.first_seen_at:
            d["first_seen_at"] = self.first_seen_at.isoformat()
        return d
