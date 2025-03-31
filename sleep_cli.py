import os
import json
import zipfile
import shutil
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.style import Style
from rich.box import ROUNDED
from rich import box
import logging
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()

def create_header():
    """Create a styled header for the application"""
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_row(
        Text("Sleep Data Analysis", style="bold blue", justify="center")
    )
    grid.add_row(
        Text("Track and analyze your sleep patterns", style="italic cyan", justify="center")
    )
    return Panel(grid, box=box.ROUNDED)

def check_file_status(filename):
    """Check if file exists and get its modification time"""
    if os.path.exists(filename):
        mod_time = datetime.fromtimestamp(os.path.getmtime(filename))
        size = os.path.getsize(filename)
        return True, mod_time, size
    return False, None, 0

def format_size(size):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"

def process_zip_file(zip_path="sleep-export.zip"):
    """Process the zip file and extract CSV"""
    try:
        with Progress(
            "[progress.description]{task.description}",
            SpinnerColumn(),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
        ) as progress:
            
            # Check if zip file exists
            if not os.path.exists(zip_path):
                console.print(Panel(
                    "[red]Error: sleep-export.zip not found[/red]\n\n"
                    "[yellow]To fix this:[/yellow]\n"
                    "1. Make sure you have exported your sleep data from Sleep as Android app\n"
                    "2. Place the sleep-export.zip file in the same directory as this script\n"
                    "3. The file should be named exactly 'sleep-export.zip'\n\n"
                    "[cyan]Need help?[/cyan]\n"
                    "1. Open Sleep as Android app\n"
                    "2. Go to Menu → Data Export\n"
                    "3. Select 'Export all data'\n"
                    "4. Save the ZIP file as 'sleep-export.zip'",
                    title="File Not Found",
                    border_style="red"
                ))
                return False
            
            extract_task = progress.add_task("Extracting zip file...", total=100)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find the CSV file in the zip
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if not csv_files:
                    console.print(Panel(
                        "[red]No CSV file found in the zip archive[/red]\n\n"
                        "[yellow]The ZIP file should contain a CSV file with your sleep data.[/yellow]\n"
                        "Please make sure you exported the correct data format from Sleep as Android.",
                        title="Error",
                        border_style="red"
                    ))
                    return False
                
                # Extract the CSV file with progress
                progress.update(extract_task, advance=50)
                zip_ref.extract(csv_files[0])
                
                # Rename to our standard name if different
                if csv_files[0] != "sleep-export.csv":
                    shutil.move(csv_files[0], "sleep-export.csv")
                
                progress.update(extract_task, advance=50)
                
        console.print(Panel(
            "[green]Successfully extracted CSV file[/green]\n\n"
            "[cyan]Next steps:[/cyan]\n"
            "1. The data will be processed automatically\n"
            "2. You can view your sleep statistics\n"
            "3. Generate visualizations of your sleep patterns",
            title="Success",
            border_style="green"
        ))
        return True
    except Exception as e:
        console.print(Panel(
            f"[red]Error processing zip file: {str(e)}[/red]\n\n"
            "[yellow]Please check:[/yellow]\n"
            "1. The ZIP file is not corrupted\n"
            "2. You have read permissions for the file\n"
            "3. There is enough disk space available",
            title="Error",
            border_style="red"
        ))
        return False

def show_file_info():
    """Show information about data files"""
    table = Table(
        title="File Status",
        box=box.ROUNDED,
        header_style="bold magenta",
        border_style="blue"
    )
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Last Modified", style="yellow")
    table.add_column("Size", style="magenta")
    
    files = ["sleep-export.zip", "sleep-export.csv", "sleep_data_2016_to_2025.json", "sleep_visualization.html"]
    
    for file in files:
        exists, mod_time, size = check_file_status(file)
        status = "✅ Present" if exists else "❌ Missing"
        mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S") if mod_time else "N/A"
        size_str = format_size(size) if exists else "N/A"
        table.add_row(file, status, mod_time_str, size_str)
    
    console.print(Panel(table, border_style="blue"))

def get_last_7_days_stats():
    """Show statistics for the last 7 days"""
    try:
        with open('sleep_data_2016_to_2025.json', 'r') as f:
            data = json.load(f)
        
        # Get current time and 7 days ago
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        
        # Filter records for last 7 days
        recent_records = []
        for record in data['sleeps']:
            record_date = datetime.fromtimestamp(record['fromTime'] / 1000)
            if seven_days_ago <= record_date <= now:
                recent_records.append(record)
        
        if not recent_records:
            console.print(Panel("[yellow]No sleep records found for the last 7 days[/yellow]", 
                              title="Warning", border_style="yellow"))
            return
        
        # Calculate statistics
        avg_duration = sum(r['hours'] for r in recent_records) / len(recent_records)
        avg_quality = sum(r['rating'] for r in recent_records) / len(recent_records)
        avg_deep_sleep = sum(r['deepSleep'] * 100 for r in recent_records) / len(recent_records)
        avg_cycles = sum(r['cycles'] for r in recent_records) / len(recent_records)
        
        # Create summary stats panel
        summary = Table.grid(padding=1)
        summary.add_column("Metric", style="cyan")
        summary.add_column("Value", style="green")
        summary.add_row("Average Duration", f"{avg_duration:.1f}h")
        summary.add_row("Average Quality", f"{avg_quality:.1f}/5")
        summary.add_row("Average Deep Sleep", f"{avg_deep_sleep:.1f}%")
        summary.add_row("Average Cycles", f"{avg_cycles:.1f}")
        
        # Create detailed table
        table = Table(
            title="Daily Sleep Records",
            box=box.ROUNDED,
            header_style="bold magenta",
            border_style="blue"
        )
        table.add_column("Date", style="cyan")
        table.add_column("Duration", style="green")
        table.add_column("Quality", style="yellow")
        table.add_column("Deep Sleep", style="magenta")
        table.add_column("Cycles", style="blue")
        
        # Add daily records
        for record in sorted(recent_records, key=lambda x: x['fromTime']):
            date = datetime.fromtimestamp(record['fromTime'] / 1000).strftime("%Y-%m-%d")
            table.add_row(
                date,
                f"{record['hours']:.1f}h",
                f"{record['rating']:.1f}/5",
                f"{record['deepSleep']*100:.1f}%",
                str(record['cycles'])
            )
        
        # Display both panels
        console.print(Panel(summary, title="Summary Statistics", border_style="green"))
        console.print(Panel(table, title="Detailed Records", border_style="blue"))
        
    except Exception as e:
        console.print(Panel(f"[red]Error getting statistics: {str(e)}[/red]", 
                          title="Error", border_style="red"))

def generate_report(days=1):
    """Generate a report for specified number of days"""
    try:
        if days == 1:
            title = "Today's Sleep Report"
        else:
            title = f"Last {days} Days Sleep Report"
            
        with Progress(
            "[progress.description]{task.description}",
            SpinnerColumn(),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
        ) as progress:
            
            console.print(Panel(f"[blue]{title}[/blue]", border_style="blue"))
            
            # Process sleep data
            process_task = progress.add_task("Processing sleep data...", total=100)
            os.system('python3 process_sleep_data.py')
            progress.update(process_task, completed=100)
            
            # Generate visualization
            viz_task = progress.add_task("Generating visualization...", total=100)
            os.system('python3 generate_sleep_visualization.py')
            progress.update(viz_task, completed=100)
        
        console.print(Panel(
            "[green]Report generated successfully!\n[cyan]You can view the report in sleep_visualization.html[/cyan][/green]",
            title="Success",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(Panel(f"[red]Error generating report: {str(e)}[/red]", 
                          title="Error", border_style="red"))

def main_menu():
    """Display and handle the main menu"""
    while True:
        console.clear()
        console.print(create_header())
        
        menu_items = [
            ("Process new zip file", "Extract and process new sleep data"),
            ("Show file information", "View status of all data files"),
            ("Show last 7 days statistics", "View recent sleep statistics"),
            ("Generate today's report", "Create report for today"),
            ("Generate last 7 days report", "Create report for last week"),
            ("Quit", "Exit the application")
        ]
        
        menu = Table(box=box.ROUNDED, show_header=False, border_style="blue")
        menu.add_column("Option", style="cyan")
        menu.add_column("Description", style="white")
        
        for i, (title, desc) in enumerate(menu_items, 1):
            key = f"[{i if i < 6 else 'q'}]"
            menu.add_row(f"{key} {title}", desc)
        
        console.print(Panel(menu, title="Menu Options", border_style="blue"))
        
        choice = Prompt.ask(
            "Select an option",
            choices=["1", "2", "3", "4", "5", "q"],
            show_choices=False
        )
        
        console.clear()
        console.print(create_header())
        
        if choice == "1":
            process_zip_file()
        elif choice == "2":
            show_file_info()
        elif choice == "3":
            get_last_7_days_stats()
        elif choice == "4":
            generate_report(days=1)
        elif choice == "5":
            generate_report(days=7)
        elif choice.lower() == "q":
            if Confirm.ask("Are you sure you want to quit?"):
                console.print(Panel("[yellow]Thank you for using Sleep Data Analysis![/yellow]",
                                  border_style="yellow"))
                break
        
        if choice != "q":
            Prompt.ask("\nPress Enter to continue")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print(Panel("\n[yellow]Program terminated by user[/yellow]",
                          border_style="yellow"))
    except Exception as e:
        console.print(Panel(f"\n[red]Unexpected error: {str(e)}[/red]",
                          title="Error", border_style="red")) 