"""Export reporter — JSON and HTML output for mesh reports."""
import json
from ..models import MeshReport


def to_dict(report: MeshReport) -> dict:
    return {
        "provider": report.provider.value,
        "total_resources": report.total_resources,
        "health_score": report.health_score,
        "grade": report.grade,
        "summary": {
            "critical": report.critical_count,
            "high": report.high_count,
            "medium": report.medium_count,
            "low": report.low_count,
            "info": report.info_count,
        },
        "findings": [
            {
                "rule_id": f.rule_id,
                "title": f.title,
                "severity": f.severity.value,
                "resource_name": f.resource_name,
                "resource_kind": f.resource_kind,
                "namespace": f.namespace,
                "description": f.description,
                "recommendation": f.recommendation,
            }
            for f in report.findings
        ],
    }


def to_json(report: MeshReport) -> str:
    return json.dumps(to_dict(report), indent=2)


def to_html(report: MeshReport) -> str:
    d = to_dict(report)
    rows = ""
    for f in d["findings"]:
        color = {"critical": "#dc3545", "high": "#fd7e14", "medium": "#ffc107", "low": "#17a2b8"}.get(f["severity"], "#6c757d")
        rows += f"""<tr>
<td>{f['rule_id']}</td>
<td style="color:{color};font-weight:bold">{f['severity'].upper()}</td>
<td>{f['resource_kind']}/{f['resource_name']}</td>
<td>{f['description']}</td>
<td>{f['recommendation']}</td>
</tr>"""
    return f"""<!DOCTYPE html>
<html><head><title>Service Mesh Report</title>
<style>body{{font-family:sans-serif;margin:2em}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}th{{background:#f4f4f4}}</style></head>
<body><h1>Service Mesh Validation Report</h1>
<p><b>Provider:</b> {d['provider']} | <b>Score:</b> {d['health_score']}/100 (Grade {d['grade']}) | <b>Resources:</b> {d['total_resources']}</p>
<table><tr><th>Rule</th><th>Severity</th><th>Resource</th><th>Issue</th><th>Recommendation</th></tr>
{rows}</table></body></html>"""
