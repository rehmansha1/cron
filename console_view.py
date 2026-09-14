"""
Rich Console Output and Exporter for Recent Job Openings.
"""
import csv
import json
from datetime import datetime
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from models import JobOpening
from config import CSV_EXPORT_PATH, JSON_EXPORT_PATH

import sys

# Ensure UTF-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(force_terminal=True, legacy_windows=False)

def format_city_badge(city_tag: str) -> str:
    if city_tag == "Chennai":
        return "[bold cyan][Chennai][/bold cyan]"
    elif city_tag == "Bangalore":
        return "[bold green][Bangalore][/bold green]"
    elif city_tag == "Remote":
        return "[bold magenta][Remote][/bold magenta]"
    return f"[bold yellow][{city_tag}][/bold yellow]"

def format_age_badge(age_cat: str, age_text: str) -> str:
    if age_cat == "Today":
        return f"[bold bright_red]TODAY[/bold bright_red] ({age_text})"
    elif age_cat == "Yesterday":
        return f"[bold yellow]YESTERDAY[/bold yellow] ({age_text})"
    return f"[dim]{age_text}[/dim]"

def print_banner():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    banner_text = Text()
    banner_text.append("=== CAREER WATCHDOG -- RECENT OPENINGS MONITOR ===\n", style="bold bright_cyan")
    banner_text.append("Candidate Filter: Rehman Sha | Full-Stack SWE (1.5 - 2 yrs) | React, Node, Java Spring Boot, Python, AI/RAG\n", style="bold green")
    banner_text.append("Scanning Career Sites for Today & Yesterday's Tech Roles (0-3 yrs) in India & Remote\n", style="dim")
    banner_text.append(f"Cron Run Timestamp: {now_str}", style="italic white")
    console.print(Panel(banner_text, border_style="cyan", padding=(1, 2)))

def display_job_table(jobs: List[JobOpening], title: str = "Recent Tech Openings"):
    if not jobs:
        console.print(Panel("[bold yellow]No new openings matching criteria found in this scan.[/bold yellow]", border_style="yellow"))
        return

    table = Table(
        title=f"\n[bold white on blue] {title} ({len(jobs)}) [/bold white on blue]",
        title_justify="left",
        header_style="bold magenta",
        show_lines=True,
        expand=True
    )

    table.add_column("#", style="dim", width=4, justify="center")
    table.add_column("Company", style="bold white", width=18)
    table.add_column("Role / Job Title", style="bold white", min_width=30)
    table.add_column("Resume Match", style="bold green", width=22)
    table.add_column("Location", width=14, justify="center")
    table.add_column("Posted", width=20, justify="center")
    table.add_column("Apply Link", style="underline cyan", min_width=20)

    for idx, job in enumerate(jobs, 1):
        city_badge = format_city_badge(job.city_tag)
        age_badge = format_age_badge(job.age_category, job.age_text)
        match_tag = f"[bold green]{job.match_reason or 'Tech Match'}[/bold green]"
        
        # Clickable terminal hyperlink if supported, else URL string
        link_str = f"[link={job.url}]-> Apply Link[/link]"

        table.add_row(
            str(idx),
            job.company,
            job.title,
            match_tag,
            city_badge,
            age_badge,
            link_str
        )

    console.print(table)

def print_summary(stats: dict, all_jobs: List[JobOpening], new_jobs: List[JobOpening]):
    total = stats.get("total", 0) if isinstance(stats, dict) else stats
    active = stats.get("active", 0) if isinstance(stats, dict) else 0
    errored = stats.get("errored", 0) if isinstance(stats, dict) else 0
    breakdown = stats.get("error_breakdown", {}) if isinstance(stats, dict) else {}

    today_count = sum(1 for j in all_jobs if j.age_category == "Today")
    yesterday_count = sum(1 for j in all_jobs if j.age_category == "Yesterday")

    lines = []
    lines.append(
        f"[bold]Companies Monitored:[/bold] [cyan]{total}[/cyan]  "
        f"([bold green]✔ {active} Live Feeds OK[/bold green] | "
        f"[bold red]✖ {errored} Inactive/Errors (404/422/500)[/bold red])"
    )
    if breakdown:
        err_tags = [f"{k}: {v}" for k, v in sorted(breakdown.items())]
        lines.append(f"[dim]Endpoint Statuses: {' | '.join(err_tags)}[/dim]")

    lines.append(
        f"[bold]Openings Matching Resume (<48h):[/bold] [cyan]{len(all_jobs)}[/cyan] | "
        f"[bold bright_red]Today:[/bold bright_red] [bright_red]{today_count}[/bright_red] | "
        f"[bold yellow]Yesterday:[/bold yellow] [yellow]{yesterday_count}[/yellow] | "
        f"[bold bright_green]Newly Discovered in this Run:[/bold bright_green] [bright_green]{len(new_jobs)}[/bright_green]"
    )

    console.print("\n", Panel("\n".join(lines), title="[bold green]Scan Summary & Endpoint Health[/bold green]", border_style="green"))

def export_jobs_to_files(jobs: List[JobOpening]):
    """Exports all current jobs to CSV and JSON."""
    if not jobs:
        return

    # Export to CSV
    try:
        with open(CSV_EXPORT_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Company", "Title", "Match Reason", "Match Score", "Location", "City", "Posted Category", "Posted Text", "URL", "ATS Type", "ID"])
            for j in jobs:
                writer.writerow([
                    j.company,
                    j.title,
                    j.match_reason,
                    j.match_score,
                    j.location,
                    j.city_tag,
                    j.age_category,
                    j.age_text,
                    j.url,
                    j.ats_type,
                    j.id
                ])
        console.print(f"[dim]📁 Saved CSV report to: [cyan]{CSV_EXPORT_PATH}[/cyan][/dim]")
    except Exception as e:
        console.print(f"[red]Failed to export CSV: {e}[/red]")

    # Export to JSON
    try:
        data = [j.to_dict() for j in jobs]
        with open(JSON_EXPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        console.print(f"[dim]📁 Saved JSON report to: [cyan]{JSON_EXPORT_PATH}[/cyan][/dim]")
    except Exception as e:
        console.print(f"[red]Failed to export JSON: {e}[/red]")
