"""
Utility helpers for date parsing, location tagging, and tech keyword filtering.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import re
from dateutil import parser as date_parser
from config import TECH_KEYWORDS, EXCLUDE_KEYWORDS, TARGET_LOCATIONS, MAX_AGE_HOURS

def get_now_utc() -> datetime:
    return datetime.now(timezone.utc)

def parse_job_date(raw_date) -> Tuple[Optional[datetime], str, str]:
    """
    Parses various date formats (epoch, ISO, relative text) and returns:
    (parsed_datetime, age_category, age_text)
    age_category is one of: 'Today', 'Yesterday', 'Recent (<48h)', 'Older'
    """
    if raw_date is None:
        return None, "Recent", "Unknown"

    now = get_now_utc()
    target_dt: Optional[datetime] = None

    # 1. Numeric epoch (seconds or milliseconds)
    if isinstance(raw_date, (int, float)):
        try:
            # If greater than 10^11, it is likely in milliseconds
            secs = raw_date / 1000.0 if raw_date > 1e11 else float(raw_date)
            target_dt = datetime.fromtimestamp(secs, tz=timezone.utc)
        except Exception:
            pass

    # 2. String handling
    elif isinstance(raw_date, str):
        text = raw_date.strip().lower()

        # Handle relative phrases directly
        if "today" in text or "just now" in text or "just posted" in text or "few hours" in text:
            return now, "Today", "Today"
        if "yesterday" in text or "1 day ago" in text or "1d ago" in text or "24 hours ago" in text:
            y_dt = now - timedelta(days=1)
            return y_dt, "Yesterday", "Yesterday"

        # Regex for 'X hours ago' or 'X minutes ago'
        hr_match = re.search(r"(\d+)\s*(?:hour|hr|h)\b", text)
        if hr_match:
            hrs = int(hr_match.group(1))
            dt = now - timedelta(hours=hrs)
            cat = "Today" if hrs <= 24 else "Yesterday"
            return dt, cat, f"{hrs}h ago"

        min_match = re.search(r"(\d+)\s*(?:minute|min|m)\b", text)
        if min_match:
            mins = int(min_match.group(1))
            dt = now - timedelta(minutes=mins)
            return dt, "Today", f"{mins}m ago"

        day_match = re.search(r"(\d+)\s*(?:day|d)\b", text)
        if day_match:
            days = int(day_match.group(1))
            dt = now - timedelta(days=days)
            if days <= 1:
                return dt, "Yesterday", "1 day ago"
            elif days <= 2:
                return dt, "Recent (<48h)", f"{days} days ago"
            else:
                return dt, "Older", f"{days} days ago"

        # Try standard ISO/String parsing
        try:
            parsed = date_parser.parse(raw_date)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            target_dt = parsed
        except Exception:
            pass

    if target_dt is not None:
        delta = now - target_dt
        hours_ago = delta.total_seconds() / 3600.0

        if hours_ago <= 24.0:
            return target_dt, "Today", f"Today ({max(0, int(hours_ago))}h ago)"
        elif hours_ago <= 48.0:
            return target_dt, "Yesterday", f"Yesterday ({int(hours_ago)}h ago)"
        elif hours_ago <= (MAX_AGE_HOURS + 24):
            return target_dt, "Recent (<48h)", f"{int(hours_ago // 24)}d ago"
        else:
            return target_dt, "Older", f"{int(hours_ago // 24)}d ago"

    return None, "Recent", str(raw_date)

def is_recent_enough(age_category: str) -> bool:
    """Returns True if the posting is from Today or Yesterday / Recent."""
    return age_category in ("Today", "Yesterday", "Recent (<48h)")

FOREIGN_LOCATIONS = [
    "us", "usa", "united states", "estonia", "poland", "germany", "canada", "united kingdom",
    "uk", "australia", "ireland", "france", "spain", "netherlands", "japan", "singapore",
    "brazil", "mexico", "israel", "switzerland", "sweden", "austria", "czech", "romania",
    "philippines", "vietnam", "colombia", "argentina"
]

def classify_city(location_text: str) -> str:
    """Extracts city classification: Chennai, Bangalore, Hyderabad, Pune/Mumbai, Delhi NCR, Remote, or India."""
    loc = location_text.lower()
    if any(k in loc for k in ["chennai", "madras", "tamil nadu", "tamilnadu", "coimbatore"]):
        return "Chennai"
    if any(k in loc for k in ["bangalore", "bengaluru", "karnataka", "mysore", "mysuru"]):
        return "Bangalore"
    if any(k in loc for k in ["hyderabad", "secunderabad", "telangana", "andhra", "vizag"]):
        return "Hyderabad"
    if any(k in loc for k in ["pune", "mumbai", "navi mumbai", "thane", "maharashtra", "nagpur"]):
        return "Pune/Mumbai"
    if any(k in loc for k in ["gurgaon", "gurugram", "noida", "delhi", "new delhi", "ncr", "faridabad", "ghaziabad"]):
        return "Delhi NCR"
    if any(k in loc for k in ["kolkata", "calcutta", "west bengal"]):
        return "Kolkata"
    if any(k in loc for k in ["ahmedabad", "gandhinagar", "vadodara", "surat", "gujarat"]):
        return "Gujarat"
    if any(k in loc for k in ["kochi", "cochin", "trivandrum", "thiruvananthapuram", "kerala"]):
        return "Kerala"
    if "remote" in loc or "work from home" in loc or "virtual" in loc or "anywhere" in loc:
        return "Remote"
    return "India"

def is_target_location(location_text: str) -> bool:
    """Checks if location matches anywhere in India or Remote."""
    if not location_text:
        return True
    loc = location_text.lower()

    # Reject foreign locations unless India, an Indian city/state, or Remote is explicitly mentioned
    for foreign in FOREIGN_LOCATIONS:
        if re.search(r"\b" + re.escape(foreign) + r"\b", loc):
            if not any(target in loc for target in TARGET_LOCATIONS):
                return False

    return any(target in loc for target in TARGET_LOCATIONS)

from resume_matcher import evaluate_resume_match

def check_resume_match(title: str, department: str = "") -> Tuple[bool, int, str]:
    """
    Filters and scores job postings specifically against Rehman Sha's resume profile:
    Full Stack, React.js, Node.js, Java Spring Boot, Python, AI/RAG, 0-3 yrs.
    """
    return evaluate_resume_match(title, department)

def is_target_tech_role(title: str, department: str = "") -> bool:
    """Checks whether the job title matches Rehman Sha's resume profile."""
    is_match, _, _ = evaluate_resume_match(title, department)
    return is_match
