"""
Career Watchdog - CLI Entry Point.
"""
import sys
import os
import argparse
import asyncio
from crawler import CareerCrawler
from db import JobDatabase
from scheduler import run_single_scan, start_cron_daemon
from console_view import display_job_table, print_banner
from health_server import start_health_server
from rich.console import Console

console = Console()

def parse_interval(interval_str: str) -> int:
    """Parses string like '6h', '30m', '3600s' into seconds."""
    s = interval_str.strip().lower()
    if s.endswith("h"):
        return int(float(s[:-1]) * 3600)
    elif s.endswith("m"):
        return int(float(s[:-1]) * 60)
    elif s.endswith("s"):
        return int(s[:-1])
    else:
        try:
            return int(s)
        except ValueError:
            return 3600  # 1 hour default

def main():
    # If running on Render or any cloud host with $PORT, bind dummy port immediately
    if os.environ.get("PORT"):
        start_health_server()

    parser = argparse.ArgumentParser(
        description="Career Watchdog: Cron job to monitor today and yesterday's tech openings in India & Remote."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: scan (immediate one-time scan)
    scan_parser = subparsers.add_parser("scan", help="Run a single scan right now across career sites.")
    scan_parser.add_argument("--today-only", action="store_true", help="Only show jobs posted today (last 24h)")
    scan_parser.add_argument("--city", choices=["chennai", "bangalore", "all"], default="all", help="Filter by city")
    scan_parser.add_argument("--limit", type=int, default=None, help="Limit number of companies scanned")
    scan_parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode: suppress long table output, minimal one-line console logs")
    scan_parser.add_argument("--no-telegram", action="store_true", help="Disable dispatching findings to Telegram")

    # Command: watch (continuous cron monitor)
    watch_parser = subparsers.add_parser("watch", help="Run continuously as a scheduled cron monitor (default: 1 hour).")
    watch_parser.add_argument(
        "--interval",
        type=str,
        default="1h",
        help="Check interval (e.g. '1h', '30m', '3600s'). Default is 1h."
    )
    watch_parser.add_argument("--today-only", action="store_true", help="Only alert on jobs posted today")
    watch_parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode: avoid long console output, send alerts to Telegram")
    watch_parser.add_argument("--no-telegram", action="store_true", help="Disable sending alerts to Telegram")

    # Command: stats
    subparsers.add_parser("stats", help="Display statistics of tracked jobs in local database.")

    # Command: test-telegram
    subparsers.add_parser("test-telegram", help="Send a test notification to verified Telegram chat.")

    args = parser.parse_args()

    # Default to 'scan' if no command provided
    command = args.command or "scan"

    if command == "scan":
        crawler = CareerCrawler()
        if hasattr(args, "limit") and args.limit:
            crawler.companies = crawler.companies[:args.limit]
        if hasattr(args, "city") and args.city != "all":
            target = args.city.lower()
            crawler.companies = [c for c in crawler.companies if c.get("city", "").lower() == target]

        db = JobDatabase()
        send_tg = not getattr(args, "no_telegram", False)
        asyncio.run(run_single_scan(
            db,
            crawler,
            today_only=getattr(args, "today_only", False),
            quiet=getattr(args, "quiet", False),
            send_telegram=send_tg,
        ))

    elif command == "watch":
        interval_secs = parse_interval(args.interval)
        send_tg = not getattr(args, "no_telegram", False)
        asyncio.run(start_cron_daemon(
            interval_seconds=interval_secs,
            today_only=args.today_only,
            quiet=getattr(args, "quiet", False),
            send_telegram=send_tg,
        ))

    elif command == "test-telegram":
        from telegram_notifier import send_telegram_message
        console.print("[bold cyan]Sending test message to Telegram...[/bold cyan]")
        ok = asyncio.run(send_telegram_message("🔔 <b>Career Watchdog</b>: Test message received successfully! Bot is connected."))
        if ok:
            console.print("[bold green]✔ Telegram message sent successfully![/bold green]")
        else:
            console.print("[bold red]✖ Failed to send Telegram message. Please check token/chat ID.[/bold red]")

    elif command == "stats":
        db = JobDatabase()
        count = db.get_total_seen_count()
        console.print(f"[bold cyan]Total unique job postings tracked in database:[/bold cyan] [bold green]{count}[/bold green]")

if __name__ == "__main__":
    main()
