# 🦅 Career Watchdog — Tech Openings Cron Monitor

A high-speed, asynchronous career portal scanner and background cron monitor that automatically tracks tech job openings posted **Today or Yesterday (< 48 hours)** across top companies in **Chennai & Bangalore** (and Remote India).

---

## ⚡ Key Features

- **Resume-Tailored Filtering**: Specifically calibrated for **Rehman Sha's** background:
  - Full-Stack Software Engineer (1.5+ years experience, 0–3 yrs target)
  - Core Stack: **React.js, Node.js, Java Spring Boot, Python, SQL, Generative AI / RAG**
  - **Excludes**: Senior / Lead / Staff / Architect / Director roles and non-tech positions.
  - **Excludes**: Foreign locations (only keeps Chennai, Bangalore, and Remote India).
- **Blazing Fast**: Scans 80+ top company career portals concurrently in **~7-12 seconds** without heavy browser sessions crashing.
- **ATS API Adapters**: Connects directly to **Greenhouse, Lever, Workday (CXS), SmartRecruiters, Ashby, and Amazon Jobs APIs**.
- **Freshness Detection**: Distinguishes between **Today's drops** (🔥), **Yesterday's drops** (⚡), and recent openings (< 48h).
- **Deduplication Engine**: Uses SQLite (`data/seen_jobs.db`) to record already-seen postings so repeated cron runs highlight only **brand-new openings**.
- **Rich Visual Console**: Formats tables with company names, role titles, match reasons, color-coded location badges (`[Chennai]`, `[Bangalore]`, `[Remote]`), age tags, and clickable application links.
- **Automatic Export**: Auto-saves every run to `recent_openings.csv` and `recent_openings.json`.

---

## 🚀 Quick Start

### 1. Run an Immediate Scan
Scan all monitored companies right now:
```powershell
python main.py scan
```
Or double-click:
```powershell
run_watchdog.bat
```

### 2. View Only Today's Openings (< 24h)
```powershell
python main.py scan --today-only
```

### 3. Filter by City
Filter specifically for Chennai or Bangalore:
```powershell
python main.py scan --city chennai
python main.py scan --city bangalore
```

### 4. Run as a Continuous Cron Daemon
Keep it running in the background checking periodically (default every 6 hours):
```powershell
python main.py watch --interval 6h
```
*(You can set any interval, e.g. `--interval 1h`, `--interval 30m`)*

### 5. Check Database Statistics
```powershell
python main.py stats
```

---

## 📂 Project Structure

```
cron/
├── config.py              # Filtering rules, target cities & tech keywords
├── models.py              # JobOpening dataclass and schema
├── utils.py               # Date parser (epoch/ISO/relative), city normalizer
├── db.py                  # SQLite database for job tracking & deduplication
├── companies.json         # Monitored companies registry (Chennai & Bangalore)
├── crawler.py             # Async worker pool orchestrator
├── console_view.py        # Rich terminal UI & CSV/JSON exporter
├── scheduler.py           # Background daemon runner loop
├── main.py                # CLI commands entrypoint (scan, watch, stats)
├── run_watchdog.bat       # One-click Windows launcher
├── requirements.txt       # Python dependencies
├── recent_openings.csv    # Generated CSV report
├── recent_openings.json   # Generated JSON report
└── data/
    └── seen_jobs.db       # Local SQLite tracking database
```

---

## 🛠 Adding More Companies

To add any new company to the scan list, simply append an entry in `companies.json`:

### Greenhouse:
```json
{ "name": "CompanyName", "city": "Bangalore", "ats": "greenhouse", "token": "board_token" }
```

### Lever:
```json
{ "name": "CompanyName", "city": "Chennai", "ats": "lever", "token": "board_token" }
```

### Workday:
```json
{ "name": "CompanyName", "city": "Chennai", "ats": "workday", "tenant": "tenant_id", "board": "Search", "domain": "tenant.wd1.myworkdayjobs.com" }
```

### SmartRecruiters:
```json
{ "name": "CompanyName", "city": "Bangalore", "ats": "smartrecruiters", "token": "company_token" }
```

### Custom Career Websites (No ATS API):
For companies that host their own custom HTML career portals, simply set `ats: "web"` and supply their career URL:
```json
{ "name": "CompanyName", "city": "Chennai", "ats": "web", "url": "https://company.com/careers" }
```
*(The scanner automatically extracts Schema.org `JobPosting` data and parses HTML job cards!)*
