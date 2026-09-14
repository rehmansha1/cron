import os
from pathlib import Path
from dotenv import load_dotenv

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")

# Database & output paths
DB_PATH = DATA_DIR / "seen_jobs.db"
CSV_EXPORT_PATH = BASE_DIR / "recent_openings.csv"
JSON_EXPORT_PATH = BASE_DIR / "recent_openings.json"

# Job Freshness Filter
MAX_AGE_HOURS = 48  # Captures "Today" and "Yesterday"
MAX_AGE_DAYS = 2

# Target locations to monitor (case-insensitive substring match) - Anywhere in India or Remote
TARGET_LOCATIONS = [
    # General India & Remote indicators
    "india",
    "remote",
    "work from home",
    "wfh",
    "virtual",
    "anywhere",
    # South India
    "chennai",
    "madras",
    "tamil nadu",
    "tamilnadu",
    "coimbatore",
    "bangalore",
    "bengaluru",
    "karnataka",
    "mysore",
    "mysuru",
    "hyderabad",
    "secunderabad",
    "telangana",
    "andhra",
    "visakhapatnam",
    "vizag",
    "kochi",
    "cochin",
    "trivandrum",
    "thiruvananthapuram",
    "kerala",
    # West India
    "pune",
    "mumbai",
    "navi mumbai",
    "thane",
    "maharashtra",
    "nagpur",
    "ahmedabad",
    "gandhinagar",
    "vadodara",
    "surat",
    "gujarat",
    "goa",
    # North India & NCR
    "delhi",
    "new delhi",
    "ncr",
    "gurgaon",
    "gurugram",
    "noida",
    "greater noida",
    "faridabad",
    "ghaziabad",
    "haryana",
    "uttar pradesh",
    "chandigarh",
    "mohali",
    "punjab",
    "jaipur",
    "rajasthan",
    "lucknow",
    "dehradun",
    # Central & East India
    "indore",
    "bhopal",
    "madhya pradesh",
    "kolkata",
    "calcutta",
    "west bengal",
    "bhubaneswar",
    "odisha",
]

# Relevant tech keywords for role filtering
TECH_KEYWORDS = [
    "software",
    "engineer",
    "developer",
    "sde",
    "backend",
    "frontend",
    "full stack",
    "fullstack",
    "full-stack",
    "data engineer",
    "machine learning",
    "ai",
    "devops",
    "cloud",
    "systems",
    "platform",
    "architect",
    "qa",
    "sdet",
    "python",
    "java",
    "golang",
    "react",
    "node",
    "embedded",
    "firmware",
    "security",
    "infrastructure",
    "intern",
    "mobile",
    "android",
    "ios",
    "flutter",
    "react native",
    "swift",
]

# Non-tech roles to exclude (e.g. Sales, Account Executive, HR)
EXCLUDE_KEYWORDS = [
    "sales representative",
    "account executive",
    "business development",
    "bdr",
    "sdr",
    "human resources",
    "hr generalist",
    "recruiter",
    "talent acquisition",
    "legal counsel",
    "office manager",
    "receptionist",
    "content writer",
    "telecaller",
]

# Async Crawler Network settings
DEFAULT_TIMEOUT = 15.0
MAX_CONCURRENT_WORKERS = 15
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/html, application/xhtml+xml, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

# Cron settings
DEFAULT_CRON_INTERVAL_HOURS = 1

# Telegram Notification Settings (loaded from .env)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "true").strip().lower() in ("true", "1", "yes")

