"""
Database storage for tracking seen and newly posted job openings.
"""
import sqlite3
from typing import List, Tuple
from config import DB_PATH
from models import JobOpening

class JobDatabase:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS seen_jobs (
                    id TEXT PRIMARY KEY,
                    company TEXT NOT NULL,
                    title TEXT NOT NULL,
                    location TEXT,
                    city_tag TEXT,
                    url TEXT,
                    ats_type TEXT,
                    age_category TEXT,
                    age_text TEXT,
                    posted_at TEXT,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def is_job_seen(self, job_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM seen_jobs WHERE id = ?", (job_id,))
            return cursor.fetchone() is not None

    def filter_and_save_new(self, jobs: List[JobOpening]) -> Tuple[List[JobOpening], List[JobOpening]]:
        """
        Saves jobs to the database.
        Returns: (newly_discovered_jobs, already_seen_jobs)
        """
        new_jobs = []
        seen_jobs = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for job in jobs:
                cursor.execute("SELECT 1 FROM seen_jobs WHERE id = ?", (job.id,))
                if cursor.fetchone() is None:
                    # Brand new job
                    cursor.execute("""
                        INSERT INTO seen_jobs (
                            id, company, title, location, city_tag, url,
                            ats_type, age_category, age_text, posted_at, first_seen_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        job.id,
                        job.company,
                        job.title,
                        job.location,
                        job.city_tag,
                        job.url,
                        job.ats_type,
                        job.age_category,
                        job.age_text,
                        job.posted_at.isoformat() if job.posted_at else None,
                        job.first_seen_at.isoformat()
                    ))
                    new_jobs.append(job)
                else:
                    seen_jobs.append(job)

            conn.commit()

        return new_jobs, seen_jobs

    def get_total_seen_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM seen_jobs")
            row = cursor.fetchone()
            return row[0] if row else 0
