#!/usr/bin/env python3
"""
test_processing.py
CLI tool for testing end-to-end ESG data processing.

Usage:
    python test_processing.py --company "TCS" --year 2024
    python test_processing.py --company-id 14 --year 2024 --standards BRSR,CDP
"""
import sys
import argparse
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

from backend.services.company_year_processor import process_company_year
from backend.database.db import get_session
from backend.database.models import Company


console = Console()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Test ESG data processing pipeline")
    parser.add_argument("--company", help="Company name (e.g., 'TCS')")
    parser.add_argument("--company-id", help="Company ID (e.g., '14')")
    parser.add_argument("--year", type=int, required=True, help="Year to process (e.g., 2024)")
    parser.add_argument("--standards", default="BRSR,CDP,EcoVadis,GRI",
                       help="Standards to process (comma-separated)")
    parser.add_argument("--force", action="store_true", help="Force re-processing")
    parser.add_argument("--no-scoring", action="store_true", help="Skip scoring calculation")
    parser.add_argument("--list-companies", action="store_true", help="List available companies")

    args = parser.parse_args()

    if args.list_companies:
        list_companies()
        return

    # Resolve company
    if not args.company and not args.company_id:
        console.print("[red]Error: Must specify either --company or --company-id[/red]")
        return

    company_id = resolve_company(args.company, args.company_id)
    if not company_id:
        return

    # Parse standards
    standards = [s.strip() for s in args.standards.split(",")]

    # Start processing
    console.print()
    console.print(Panel.fit(
        f"Processing Company ID: {company_id}\n"
        f"Year: {args.year}\n"
        f"Standards: {', '.join(standards)}\n"
        f"Force Refresh: {'Yes' if args.force else 'No'}",
        title="ESG Data Processing",
        border_style="blue"
    ))

    try:
        start_time = time.time()

        # Run processing with progress indicators
        console.print("\n[bold]Starting complete ESG data processing...[/bold]")

        result = process_company_year(
            company_id=company_id,
            year=args.year,
            force_refresh=args.force,
            trigger_scoring=not args.no_scoring
        )

        end_time = time.time()

        # Display results
        display_results(result, end_time - start_time)

    except Exception as e:
        console.print(f"[red]Processing failed: {e}[/red]")
        raise


def resolve_company(company_name: str = None, company_id: str = None) -> str:
    """Resolve company name to ID"""
    db = get_session()

    try:
        if company_id:
            company = db.query(Company).filter_by(id=int(company_id)).first()
            if not company:
                console.print(f"[red]Company ID {company_id} not found[/red]")
                return None
            console.print(f"[green]Found company: {company.name}[/green]")
            return company_id

        elif company_name:
            # Try exact match first
            company = db.query(Company).filter_by(name=company_name).first()

            if not company:
                # Try ticker match
                company = db.query(Company).filter(
                    Company.ticker.in_([
                        company_name.upper(),
                        company_name.upper() + ".NS",
                        company_name.upper() + ".BO"
                    ])
                ).first()

            if not company:
                # Try partial name match
                company = db.query(Company).filter(
                    Company.name.ilike(f"%{company_name}%")
                ).first()

            if not company:
                console.print(f"[red]Company '{company_name}' not found[/red]")
                console.print("Use --list-companies to see available companies")
                return None

            console.print(f"[green]Found company: {company.name} (ID: {company.id})[/green]")
            return str(company.id)

    finally:
        db.close()

    return None


def list_companies():
    """List all available companies"""
    db = get_session()

    try:
        companies = db.query(Company).order_by(Company.name).limit(20).all()

        table = Table(title="Available Companies (First 20)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Ticker", style="yellow")

        for company in companies:
            table.add_row(
                str(company.id),
                company.name,
                company.ticker or "N/A"
            )

        console.print(table)
        console.print(f"\n[dim]Showing first 20 companies. Total in database: {db.query(Company).count()}[/dim]")

    finally:
        db.close()


def display_results(result, processing_time: float):
    """Display processing results in a nice format"""
    console.print("\n" + "="*60)
    console.print("[bold green]PROCESSING COMPLETED[/bold green]")
    console.print("="*60)

    # Summary table
    table = Table(title="Processing Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Company ID", str(result.company_id))
    table.add_row("Year", str(result.year))
    table.add_row("Total Indicators", str(result.total_indicators))
    table.add_row("Processed Successfully", str(result.processed_indicators))
    table.add_row("Failed", str(result.failed_indicators))
    table.add_row("Completion Rate", f"{(result.processed_indicators / result.total_indicators * 100):.1f}%")
    table.add_row("Processing Time", f"{processing_time:.1f} seconds")
    table.add_row("Modules Processed", str(len(result.modules_processed)))

    if hasattr(result, 'final_score') and result.final_score:
        table.add_row("Final ESG Score", f"{result.final_score:.1f}/100")

    console.print(table)

    # Modules processed
    console.print("\n[bold]Modules Processed:[/bold]")
    for i, module in enumerate(result.modules_processed, 1):
        console.print(f"  {i}. {module}")

    # Module scores if available
    if hasattr(result, 'module_scores') and result.module_scores:
        console.print("\n[bold]Module Scores:[/bold]")
        score_table = Table()
        score_table.add_column("Module", style="cyan")
        score_table.add_column("Score", style="green")

        for module, score in sorted(result.module_scores.items(), key=lambda x: x[1], reverse=True):
            score_table.add_row(module, f"{score:.1f}")

        console.print(score_table)

    # Errors if any
    if hasattr(result, 'errors') and result.errors:
        console.print("\n[bold red]Errors Encountered:[/bold red]")
        for error in result.errors:
            console.print(f"  • {error}")

    console.print(f"\n[green]Processing complete![/green]")


if __name__ == "__main__":
    main()