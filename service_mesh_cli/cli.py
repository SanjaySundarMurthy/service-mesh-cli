"""CLI entry point for service-mesh-cli."""
import sys
import click
from rich.console import Console
from rich.table import Table
from .models import MESH_RULES, MeshProvider
from .parser import parse_resources
from .analyzers.mesh_validator import validate_mesh
from .reporters.terminal_reporter import print_report
from .reporters.export_reporter import to_json, to_html
from .demo import get_demo_mesh_config

console = Console()


@click.group()
def cli():
    """🕸️ service-mesh-cli — Service mesh configuration validator."""
    pass


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--provider", type=click.Choice(["istio", "linkerd", "consul"]), default="istio")
@click.option("--format", "fmt", type=click.Choice(["terminal", "json", "html"]), default="terminal")
@click.option("--fail-on", type=click.Choice(["critical", "high", "medium", "low"]), default=None)
@click.option("--output", "-o", type=click.Path(), default=None)
def validate(config_file, provider, fmt, fail_on, output):
    """Validate mesh configuration against best practices."""
    with open(config_file, "r") as f:
        content = f.read()
    mesh_provider = MeshProvider(provider)
    resources = parse_resources(content, mesh_provider)
    report = validate_mesh(resources, mesh_provider)
    if fmt == "json":
        result = to_json(report)
        if output:
            with open(output, "w") as f:
                f.write(result)
            console.print(f"[green]Report saved to {output}[/]")
        else:
            console.print(result)
    elif fmt == "html":
        result = to_html(report)
        if output:
            with open(output, "w") as f:
                f.write(result)
            console.print(f"[green]Report saved to {output}[/]")
        else:
            console.print(result)
    else:
        print_report(report, console)
    if fail_on:
        severity_order = ["critical", "high", "medium", "low"]
        threshold = severity_order.index(fail_on)
        for finding in report.findings:
            if severity_order.index(finding.severity.value) <= threshold:
                sys.exit(1)


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["terminal", "json", "html"]), default="terminal")
def demo(fmt):
    """Run demo with sample Istio configuration."""
    content = get_demo_mesh_config()
    resources = parse_resources(content, MeshProvider.ISTIO)
    report = validate_mesh(resources, MeshProvider.ISTIO)
    if fmt == "json":
        console.print(to_json(report))
    elif fmt == "html":
        console.print(to_html(report))
    else:
        print_report(report, console)


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


if __name__ == "__main__":
    cli()
