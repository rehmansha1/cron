"""
Telegram Notification Dispatcher for Career Watchdog.
Sends newly discovered job openings directly to your Telegram chat.
"""
import asyncio
from typing import List
import httpx
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED
from models import JobOpening

def escape_html(text: str) -> str:
    """Escapes raw text for Telegram HTML parse mode."""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

async def send_telegram_message(text: str, parse_mode: str = "HTML") -> bool:
    """Sends a single message to the configured Telegram chat."""
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
    except Exception as e:
        print(f"[Telegram] Failed to send message: {e}")
        return False

async def send_job_alerts(jobs: List[JobOpening], title: str = "🚀 Career Watchdog Alert") -> int:
    """
    Formats and delivers new job openings to Telegram.
    Chunks openings into safe message batches under Telegram's 4096 character limit.
    """
    if not jobs or not TELEGRAM_ENABLED:
        return 0

    batches: List[str] = []
    current_lines = [f"<b>{title}</b>\n<i>Found {len(jobs)} opening(s) matching your profile:</i>\n\n"]
    current_length = sum(len(l) for l in current_lines)

    for idx, j in enumerate(jobs, 1):
        clean_company = escape_html(j.company)
        clean_title = escape_html(j.title)
        clean_loc = escape_html(j.location or j.city_tag)
        clean_age = escape_html(j.age_text)
        clean_reason = escape_html(j.match_reason)
        clean_url = escape_html(j.url)

        entry = (
            f"<b>{idx}. {clean_company}</b> — {clean_title}\n"
            f"📍 <b>Location:</b> {clean_loc}\n"
            f"⏳ <b>Posted:</b> {clean_age}\n"
            f"🎯 <b>Match:</b> {clean_reason} ({j.match_score}%)\n"
            f"🔗 <a href=\"{clean_url}\"><b>Apply Now</b></a>\n\n"
        )

        if current_length + len(entry) > 3500:
            batches.append("".join(current_lines))
            current_lines = [f"<b>{title} (Cont.)</b>\n\n", entry]
            current_length = sum(len(l) for l in current_lines)
        else:
            current_lines.append(entry)
            current_length += len(entry)

    if current_lines:
        batches.append("".join(current_lines))

    sent_count = 0
    for batch in batches:
        ok = await send_telegram_message(batch)
        if ok:
            sent_count += 1
        await asyncio.sleep(0.5)  # Telegram rate limit safety

    return sent_count
