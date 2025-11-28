#!/usr/bin/env python3
"""
Error Monitor CLI Tool

Real-time error monitoring with progress bars, analysis, and detailed feedback.
Run this tool to monitor errors in real-time with visual progress indicators.

Usage:
    python tools/monitor_errors.py
    python tools/monitor_errors.py --watch
    python tools/monitor_errors.py --analyze
    python tools/monitor_errors.py --export errors.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.layout import Layout
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from services.error_monitoring_service import (
    ErrorMonitoringService,
    ErrorReport,
    ErrorPriority,
    ErrorSeverity,
    get_error_monitor,
)


class ErrorMonitorCLI:
    """CLI tool for monitoring errors with rich terminal output."""
    
    def __init__(self, use_rich: bool = True):
        """Initialize CLI monitor."""
        self.use_rich = use_rich and RICH_AVAILABLE
        self.console = Console() if self.use_rich else None
        self.monitor = get_error_monitor()
        self.running = False
        
    def print_header(self) -> None:
        """Print header information."""
        if self.use_rich:
            header = Panel(
                "[bold cyan]Error Monitoring Service - Real-Time Monitor[/bold cyan]\n"
                "[dim]Press Ctrl+C to stop[/dim]",
                border_style="cyan",
                box=box.ROUNDED
            )
            self.console.print(header)
        else:
            print("=" * 70)
            print("  ERROR MONITORING SERVICE - REAL-TIME MONITOR")
            print("=" * 70)
            print("  Press Ctrl+C to stop")
            print("=" * 70)
            print()
    
    def watch_errors(self, refresh_interval: float = 0.5) -> None:
        """Watch for errors in real-time with live updates."""
        self.print_header()
        
        if self.use_rich:
            self._watch_with_rich(refresh_interval)
        else:
            self._watch_simple(refresh_interval)
    
    def _watch_with_rich(self, refresh_interval: float) -> None:
        """Watch errors with rich terminal UI."""
        from rich.live import Live
        from rich.layout import Layout
        
        def generate_layout() -> Layout:
            """Generate layout for live display."""
            layout = Layout()
            
            # Statistics panel
            stats = self._create_stats_panel()
            
            # Recent errors table
            errors_table = self._create_errors_table()
            
            # Resource monitoring
            resources = self._create_resources_panel()
            
            # Split layout
            layout.split_column(
                Layout(stats, size=8),
                Layout(errors_table, ratio=2),
                Layout(resources, size=6),
            )
            
            return layout
        
        try:
            with Live(generate_layout(), refresh_per_second=1/refresh_interval, screen=True) as live:
                self.running = True
                while self.running:
                    live.update(generate_layout())
                    time.sleep(refresh_interval)
        except KeyboardInterrupt:
            self.running = False
            self.console.print("\n[bold yellow]Monitoring stopped[/bold yellow]")
    
    def _watch_simple(self, refresh_interval: float) -> None:
        """Watch errors with simple terminal output."""
        try:
            self.running = True
            last_error_count = 0
            
            while self.running:
                # Clear screen (simple approach)
                print("\033[2J\033[H", end="")  # ANSI escape codes
                
                # Print header
                self.print_header()
                
                # Print statistics
                stats = self.monitor.get_statistics()
                print(f"Total Errors: {stats['total_errors']}")
                print(f"Recovery Success Rate: {stats['recovery_success_rate']:.1%}")
                print()
                
                # Print recent errors
                recent_errors = self.monitor.get_recent_errors(limit=10)
                if recent_errors:
                    print("Recent Errors:")
                    print("-" * 70)
                    for error in recent_errors[-5:]:
                        timestamp = datetime.fromtimestamp(error.timestamp).strftime("%H:%M:%S")
                        print(f"[{timestamp}] {error.error_type} in {error.component}")
                        print(f"  {error.error_message[:60]}...")
                        print()
                
                # Check for new errors
                current_count = stats['total_errors']
                if current_count > last_error_count:
                    new_errors = current_count - last_error_count
                    print(f"⚠ {new_errors} new error(s) detected!")
                    last_error_count = current_count
                
                time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            self.running = False
            print("\nMonitoring stopped")
    
    def _create_stats_panel(self) -> Panel:
        """Create statistics panel."""
        stats = self.monitor.get_statistics()
        
        stats_text = f"""
[bold]Statistics[/bold]
  Total Errors: [cyan]{stats['total_errors']}[/cyan]
  Recovery Success Rate: [green]{stats['recovery_success_rate']:.1%}[/green]
  Average Errors/Hour: [yellow]{stats['average_errors_per_hour']:.1f}[/yellow]
  
[bold]By Severity[/bold]
  Critical: [red]{stats['errors_by_severity'].get('critical', 0)}[/red]
  High: [yellow]{stats['errors_by_severity'].get('high', 0)}[/yellow]
  Medium: [blue]{stats['errors_by_severity'].get('medium', 0)}[/blue]
  Low: [green]{stats['errors_by_severity'].get('low', 0)}[/green]
        """
        
        return Panel(stats_text, title="[bold]Error Statistics[/bold]", border_style="cyan")
    
    def _create_errors_table(self) -> Table:
        """Create recent errors table."""
        table = Table(title="Recent Errors", show_header=True, header_style="bold cyan")
        table.add_column("Time", style="dim", width=8)
        table.add_column("Type", style="cyan", width=20)
        table.add_column("Component", style="yellow", width=20)
        table.add_column("Message", style="white", width=30)
        table.add_column("Count", justify="right", style="magenta", width=6)
        
        recent_errors = self.monitor.get_recent_errors(limit=10)
        for error in recent_errors[-10:]:
            timestamp = datetime.fromtimestamp(error.timestamp).strftime("%H:%M:%S")
            severity_color = {
                ErrorSeverity.CRITICAL: "red",
                ErrorSeverity.HIGH: "yellow",
                ErrorSeverity.MEDIUM: "blue",
                ErrorSeverity.LOW: "green",
            }.get(error.severity, "white")
            
            error_type = Text(error.error_type, style=severity_color)
            message = error.error_message[:30] + "..." if len(error.error_message) > 30 else error.error_message
            
            table.add_row(
                timestamp,
                error_type,
                error.component,
                message,
                str(error.occurrence_count),
            )
        
        if not recent_errors:
            table.add_row("No errors", "", "", "", "")
        
        return table
    
    def _create_resources_panel(self) -> Panel:
        """Create resource monitoring panel."""
        if not self.monitor.enable_resource_monitoring:
            return Panel("[dim]Resource monitoring disabled[/dim]", title="Resources")
        
        # Get latest resource snapshot
        if self.monitor.resource_history:
            latest = self.monitor.resource_history[-1]
            resources_text = f"""
[bold]System Resources[/bold]
  CPU: [yellow]{latest.cpu_percent:.1f}%[/yellow]
  Memory: [yellow]{latest.memory_percent:.1f}%[/yellow] ({latest.memory_used_mb:.1f} MB)
  Available Memory: [green]{latest.memory_available_mb:.1f} MB[/green]
  Threads: [cyan]{latest.thread_count}[/cyan]
            """
        else:
            resources_text = "[dim]No resource data available[/dim]"
        
        return Panel(resources_text, title="[bold]Resources[/bold]", border_style="green")
    
    def analyze_errors(self) -> None:
        """Analyze errors and display comprehensive report."""
        self.print_header()
        
        analysis = self.monitor.get_error_analysis()
        
        if self.use_rich:
            self._analyze_with_rich(analysis)
        else:
            self._analyze_simple(analysis)
    
    def _analyze_with_rich(self, analysis: Dict) -> None:
        """Display analysis with rich formatting."""
        stats = analysis["statistics"]
        
        # Statistics panel
        stats_panel = self._create_stats_panel()
        self.console.print(stats_panel)
        self.console.print()
        
        # Top errors
        if analysis["top_errors"]:
            top_table = Table(title="Top Errors by Frequency", show_header=True)
            top_table.add_column("Rank", justify="right", style="dim")
            top_table.add_column("Error ID", style="cyan", width=12)
            top_table.add_column("Type", style="yellow", width=20)
            top_table.add_column("Component", style="blue", width=20)
            top_table.add_column("Occurrences", justify="right", style="magenta")
            top_table.add_column("Priority", style="red")
            
            for idx, error_data in enumerate(analysis["top_errors"], 1):
                report = error_data["report"]
                priority = ErrorPriority(report["priority"])
                priority_color = {
                    ErrorPriority.CRITICAL: "red",
                    ErrorPriority.HIGH: "yellow",
                    ErrorPriority.MEDIUM: "blue",
                    ErrorPriority.LOW: "green",
                }.get(priority, "white")
                
                top_table.add_row(
                    str(idx),
                    error_data["error_id"][:12],
                    report["error_type"],
                    report["component"],
                    str(error_data["occurrence_count"]),
                    Text(priority.name, style=priority_color),
                )
            
            self.console.print(top_table)
        else:
            self.console.print("[dim]No errors to analyze[/dim]")
    
    def _analyze_simple(self, analysis: Dict) -> None:
        """Display analysis with simple formatting."""
        stats = analysis["statistics"]
        
        print("Error Analysis")
        print("=" * 70)
        print(f"Total Errors: {stats['total_errors']}")
        print(f"Unique Errors: {analysis['total_unique_errors']}")
        print(f"Recovery Success Rate: {stats['recovery_success_rate']:.1%}")
        print()
        
        print("Top Errors by Frequency:")
        print("-" * 70)
        for idx, error_data in enumerate(analysis["top_errors"][:10], 1):
            report = error_data["report"]
            print(f"{idx}. {report['error_type']} in {report['component']}")
            print(f"   Occurrences: {error_data['occurrence_count']}")
            print(f"   Message: {report['error_message'][:60]}...")
            print()
    
    def export_errors(self, file_path: Path) -> None:
        """Export errors to JSON file."""
        analysis = self.monitor.get_error_analysis()
        
        # Convert to JSON-serializable format
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "statistics": analysis["statistics"],
            "top_errors": [],
            "all_errors": [],
        }
        
        # Export top errors
        for error_data in analysis["top_errors"]:
            export_data["top_errors"].append({
                "error_id": error_data["error_id"],
                "occurrence_count": error_data["occurrence_count"],
                "report": error_data["report"],
            })
        
        # Export all error reports
        for error_id, report in self.monitor.error_reports.items():
            report_dict = {
                "error_id": error_id,
                "error_type": report.error_type,
                "error_message": report.error_message,
                "severity": report.severity.value,
                "priority": report.priority.value,
                "timestamp": report.timestamp,
                "occurrence_count": report.occurrence_count,
                "component": report.component,
                "file_path": report.file_path,
                "line_number": report.line_number,
            }
            export_data["all_errors"].append(report_dict)
        
        # Write to file
        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)
        
        if self.use_rich:
            self.console.print(f"[green]✓[/green] Exported {len(export_data['all_errors'])} errors to {file_path}")
        else:
            print(f"✓ Exported {len(export_data['all_errors'])} errors to {file_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Error Monitoring Service - Real-Time Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch for errors in real-time (default)",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze errors and display report",
    )
    parser.add_argument(
        "--export",
        type=Path,
        help="Export errors to JSON file",
    )
    parser.add_argument(
        "--refresh",
        type=float,
        default=0.5,
        help="Refresh interval in seconds (default: 0.5)",
    )
    parser.add_argument(
        "--no-rich",
        action="store_true",
        help="Disable rich terminal output",
    )
    
    args = parser.parse_args()
    
    # Create monitor CLI
    cli = ErrorMonitorCLI(use_rich=not args.no_rich)
    
    # Ensure monitor is running
    if not cli.monitor.running:
        cli.monitor.start()
    
    try:
        if args.export:
            cli.export_errors(args.export)
        elif args.analyze:
            cli.analyze_errors()
        else:
            # Default to watch mode
            cli.watch_errors(refresh_interval=args.refresh)
    except KeyboardInterrupt:
        if cli.use_rich:
            cli.console.print("\n[bold yellow]Stopped by user[/bold yellow]")
        else:
            print("\nStopped by user")
    finally:
        if cli.monitor.running:
            cli.monitor.stop()


if __name__ == "__main__":
    main()

