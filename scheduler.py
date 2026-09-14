"""
Cron Scheduler and Daemon Loop for periodic job monitoring.
"""
import time
import asyncio
from datetime import datetime
from rich.console import Console
from crawler import CareerCrawler
from db import JobDatabase
from config import TELEGRAM_ENABLED, TELEGRAM_CHAT_ID
from console_view import print_banner, display_job_table, print_summary, export_jobs_to_files
from telegram_notifier import send_job_alerts

console = Console()

async def run_single_scan(
    db: JobDatabase,
    crawler: CareerCrawler,
    today_only: bool = False,
    notify_new_only: bool = False,
    quiet: bool = False,
    send_telegram: bool = True,
):
    """Executes a single scan cycle."""
    if not quiet:
        print_banner()

    all_jobs, stats = await crawler.scan_all(show_progress=not quiet)

    if today_only:
        all_jobs = [j for j in all_jobs if j.age_category == "Today"]

    # Filter against database to identify brand new jobs
    new_jobs, _ = db.filter_and_save_new(all_jobs)

    # Decide what to display
    jobs_to_display = new_jobs if notify_new_only else all_jobs

    if not quiet:
        display_job_table(jobs_to_display, title="Today & Yesterday's Tech Openings")
        print_summary(stats, all_jobs, new_jobs)
    else:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console.print(
            f"[dim]{now_str}[/dim] | [cyan]Scanned {stats['total']} companies[/cyan] | "
            f"[green]{len(all_jobs)} matched[/green] | "
            f"[bold magenta]{len(new_jobs)} newly found[/bold magenta]"
        )

    export_jobs_to_files(all_jobs)

    # Dispatch newly discovered jobs to Telegram
    if send_telegram and TELEGRAM_ENABLED and new_jobs:
        if not quiet:
            console.print(f"[bold cyan]Dispatching {len(new_jobs)} new opening(s) to Telegram...[/bold cyan]")
        sent = await send_job_alerts(new_jobs, title="🚀 Career Watchdog: New Tech Openings")
        if sent and not quiet:
            console.print(f"[bold green]✔ Delivered to Telegram chat {TELEGRAM_CHAT_ID}[/bold green]")

    return all_jobs, new_jobs

async def start_cron_daemon(
    interval_seconds: int = 3600,
    today_only: bool = False,
    quiet: bool = False,
    send_telegram: bool = True,
):
    """
    Runs the scanner as a continuous background daemon (default every 1 hour = 3600s).
    """
    db = JobDatabase()
    crawler = CareerCrawler()

    hours = interval_seconds / 3600.0
    interval_desc = f"{hours:g} hour(s)" if hours >= 1 else f"{interval_seconds // 60} minutes"

    console.print(f"[bold green]Starting Career Watchdog Cron Monitor...[/bold green]")
    # Start lightweight dummy HTTP health check for Render / Cloud Web Services
    from health_server import start_health_server
    health_port = start_health_server()
    console.print(f"[dim]Health check server listening on port {health_port} (for Render/Cloud health checks)[/dim]")

    if send_telegram and TELEGRAM_ENABLED:
        console.print(f"[bold magenta]Telegram alerts enabled -> Chat ID: {TELEGRAM_CHAT_ID}[/bold magenta]")
    if quiet:
        console.print("[dim]Quiet mode active (long console output suppressed)[/dim]")
    console.print("[dim]Press Ctrl+C at any time to stop.[/dim]\n")

    iteration = 1
    while True:
        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not quiet:
                console.print(f"\n[bold magenta]═════════════ [Cron Run #{iteration} - {now_str}] ═════════════[/bold magenta]")
            
            # On run #1: scan and save; on subsequent runs, alert on new jobs
            notify_new_only = (iteration > 1)
            await run_single_scan(
                db,
                crawler,
                today_only=today_only,
                notify_new_only=notify_new_only,
                quiet=quiet,
                send_telegram=send_telegram,
            )

            iteration += 1
            next_run = datetime.fromtimestamp(time.time() + interval_seconds).strftime("%H:%M:%S")
            console.print(f"[dim]Next scan at {next_run} ({interval_desc})...[/dim]")
            await asyncio.sleep(interval_seconds)

        except (KeyboardInterrupt, asyncio.CancelledError):
            console.print("\n[bold red]Cron monitor stopped by user.[/bold red]")
            break
        except Exception as e:
            console.print(f"[bold red]Error during cron run: {e}[/bold red]")
            await asyncio.sleep(60)
