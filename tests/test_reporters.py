"""Tests for export and terminal reporters."""
import json
from io import StringIO
from rich.console import Console
from service_mesh_cli.models import (
    MeshReport, MeshResource, Finding, Severity, ResourceKind,
    MeshProvider,
)
from service_mesh_cli.reporters.export_reporter import to_json, to_html, to_dict
from service_mesh_cli.reporters.terminal_reporter import print_report


class TestExportReporter:
    def _make_report(self):
        report = MeshReport(
            provider=MeshProvider.ISTIO,
            resources=[MeshResource(kind=ResourceKind.GATEWAY, name="gw")],
            findings=[
                Finding(rule_id="MESH-001", title="mTLS Not Enforced",
                        severity=Severity.CRITICAL, resource_name="gw",
                        resource_kind="Gateway", namespace="default",
                        description="mTLS disabled", recommendation="Enable STRICT"),
                Finding(rule_id="MESH-003", title="No Retry Policy",
                        severity=Severity.MEDIUM, resource_name="vs",
                        resource_kind="VirtualService", namespace="prod",
                        description="No retry", recommendation="Add retry"),
            ],
        )
        report.compute_summary()
        return report

    def test_to_dict(self):
        report = self._make_report()
        d = to_dict(report)
        assert d["provider"] == "istio"
        assert d["total_resources"] == 1
        assert d["grade"] in ("A", "B", "C", "D", "F")
        assert len(d["findings"]) == 2
        assert d["summary"]["critical"] == 1
        assert d["summary"]["medium"] == 1

    def test_to_json_valid(self):
        report = self._make_report()
        result = to_json(report)
        data = json.loads(result)
        assert data["provider"] == "istio"
        assert len(data["findings"]) == 2

    def test_to_html_structure(self):
        report = self._make_report()
        html = to_html(report)
        assert "<!DOCTYPE html>" in html
        assert "MESH-001" in html
        assert "MESH-003" in html
        assert "Service Mesh Validation Report" in html
        assert "Grade" in html

    def test_to_html_no_findings(self):
        report = MeshReport(provider=MeshProvider.ISTIO)
        report.compute_summary()
        html = to_html(report)
        assert "<!DOCTYPE html>" in html
        assert "Grade A" in html

    def test_to_dict_all_severities(self):
        findings = [
            Finding(severity=Severity.CRITICAL),
            Finding(severity=Severity.HIGH),
            Finding(severity=Severity.MEDIUM),
            Finding(severity=Severity.LOW),
            Finding(severity=Severity.INFO),
        ]
        report = MeshReport(findings=findings)
        report.compute_summary()
        d = to_dict(report)
        assert d["summary"]["critical"] == 1
        assert d["summary"]["high"] == 1
        assert d["summary"]["medium"] == 1
        assert d["summary"]["low"] == 1
        assert d["summary"]["info"] == 1


class TestTerminalReporter:
    def test_print_report_no_findings(self):
        report = MeshReport(provider=MeshProvider.ISTIO)
        report.compute_summary()
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        print_report(report, console)
        text = output.getvalue()
        assert "No issues found" in text

    def test_print_report_with_findings(self):
        report = MeshReport(
            provider=MeshProvider.ISTIO,
            findings=[
                Finding(rule_id="MESH-007", title="Gateway TLS",
                        severity=Severity.CRITICAL, resource_name="gw",
                        resource_kind="Gateway", namespace="default",
                        description="No TLS", recommendation="Add TLS"),
            ],
        )
        report.compute_summary()
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=200)
        print_report(report, console)
        text = output.getvalue()
        assert "MESH-007" in text
        assert "CRITICAL" in text

    def test_print_report_default_console(self):
        """Verify print_report works without explicit console."""
        report = MeshReport()
        report.compute_summary()
        # Should not raise
        print_report(report)
