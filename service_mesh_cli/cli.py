"""CLI entry point for service-mesh-cli."""
import sys
import click
from rich.console import Console
from rich.table import Table
from . import __version__
from .models import MESH_RULES, MeshProvider, Severity
from .parser import parse_resources
from .analyzers.mesh_validator import validate_mesh
from .reporters.terminal_reporter import print_report
from .reporters.export_reporter import to_json, to_html
from .demo import get_demo_mesh_config

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="service-mesh-cli")
def cli():
    """🕸️ service-mesh-cli — Service mesh configuration validator."""
    pass


def _output_report(report, fmt, output, console):
    """Write report in the chosen format."""
    if fmt == "json":
        result = to_json(report)
    elif fmt == "html":
        result = to_html(report)
    else:
        print_report(report, console)
        return
    if output:
        with open(output, "w") as f:
            f.write(result)
        console.print(f"[green]Report saved to {output}[/]")
    else:
        console.print(result)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--provider", type=click.Choice(["istio", "linkerd", "consul"]), default="istio",
              help="Target mesh platform.")
@click.option("--format", "fmt", type=click.Choice(["terminal", "json", "html"]), default="terminal",
              help="Output format.")
@click.option("--fail-on", type=click.Choice(["critical", "high", "medium", "low"]), default=None,
              help="Exit code 1 if findings at this severity or above.")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Write report to file instead of stdout.")
def validate(config_file, provider, fmt, fail_on, output):
    """Validate mesh configuration against best practices."""
    with open(config_file, "r") as f:
        content = f.read()
    mesh_provider = MeshProvider(provider)
    resources = parse_resources(content, mesh_provider)
    report = validate_mesh(resources, mesh_provider)
    _output_report(report, fmt, output, console)
    if fail_on:
        severity_order = ["critical", "high", "medium", "low"]
        threshold = severity_order.index(fail_on)
        for finding in report.findings:
            if severity_order.index(finding.severity.value) <= threshold:
                sys.exit(1)


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["terminal", "json", "html"]), default="terminal",
              help="Output format.")
def demo(fmt):
    """Run demo with sample Istio configuration."""
    content = get_demo_mesh_config()
    resources = parse_resources(content, MeshProvider.ISTIO)
    report = validate_mesh(resources, MeshProvider.ISTIO)
    _output_report(report, fmt, None, console)


@cli.command()
def rules():
    """List all validation rules."""
    table = Table(title="Service Mesh Validation Rules", show_lines=True)
    table.add_column("Rule ID", style="bold", width=10)
    table.add_column("Severity", width=10)
    table.add_column("Title", width=35)
    table.add_column("Description", width=50)
    for rule_id, rule in MESH_RULES.items():
        color = {"critical": "red bold", "high": "red", "medium": "yellow", "low": "cyan"}.get(rule["severity"].value, "white")
        table.add_row(rule_id, f"[{color}]{rule['severity'].value.upper()}[/]", rule["title"], rule["description"])
    console.print(table)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--provider", type=click.Choice(["istio", "linkerd", "consul"]), default="istio")
def summary(config_file, provider):
    """Show a brief health summary of mesh configuration."""
    with open(config_file, "r") as f:
        content = f.read()
    mesh_provider = MeshProvider(provider)
    resources = parse_resources(content, mesh_provider)
    report = validate_mesh(resources, mesh_provider)
    grade_color = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red bold"}.get(report.grade, "white")
    console.print(f"\n[bold]Provider:[/] {report.provider.value.upper()}")
    console.print(f"[bold]Resources:[/] {report.total_resources}")
    console.print(f"[bold]Health Score:[/] [{grade_color}]{report.health_score:.1f}/100 (Grade {report.grade})[/]")
    sev_counts = {
        Severity.CRITICAL: report.critical_count,
        Severity.HIGH: report.high_count,
        Severity.MEDIUM: report.medium_count,
        Severity.LOW: report.low_count,
        Severity.INFO: report.info_count,
    }
    parts = []
    for sev, count in sev_counts.items():
        if count:
            parts.append(f"{count} {sev.value}")
    console.print(f"[bold]Findings:[/] {', '.join(parts) if parts else 'None'}\n")


if __name__ == "__main__":
    cli()
