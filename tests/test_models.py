"""Tests for data models."""
from service_mesh_cli.models import (
    MeshResource, ResourceKind, MeshProvider, TLSMode, Severity,
    MeshReport, Finding, TrafficRoute, RetryPolicy, CircuitBreaker,
    LoadBalancerAlgorithm, TrafficProtocol, MESH_RULES,
)


class TestModels:
    def test_mesh_resource_defaults(self):
        r = MeshResource()
        assert r.kind == ResourceKind.VIRTUAL_SERVICE
        assert r.namespace == "default"
        assert r.provider == MeshProvider.ISTIO
        assert r.tls_mode == TLSMode.DISABLE
        assert r.routes == []

    def test_traffic_route_defaults(self):
        t = TrafficRoute()
        assert t.weight == 100
        assert t.destination_host == ""

    def test_retry_policy(self):
        rp = RetryPolicy(attempts=5, per_try_timeout="3s")
        assert rp.attempts == 5

    def test_circuit_breaker_defaults(self):
        cb = CircuitBreaker()
        assert cb.max_connections == 1024
        assert cb.max_ejection_percent == 50

    def test_report_compute_summary_no_findings(self):
        report = MeshReport(resources=[MeshResource()])
        report.compute_summary()
        assert report.total_resources == 1
        assert report.health_score == 100.0
        assert report.grade == "A"

    def test_report_compute_summary_with_findings(self):
        report = MeshReport(
            resources=[MeshResource()],
            findings=[
                Finding(severity=Severity.CRITICAL),
                Finding(severity=Severity.HIGH),
                Finding(severity=Severity.MEDIUM),
            ],
        )
        report.compute_summary()
        assert report.critical_count == 1
        assert report.high_count == 1
        assert report.medium_count == 1
        assert report.health_score == 70.0
        assert report.grade == "C"

    def test_report_grade_f(self):
        report = MeshReport(findings=[Finding(severity=Severity.CRITICAL)] * 7)
        report.compute_summary()
        assert report.grade == "F"
        assert report.health_score == 0.0  # 7*15=105, capped at 0

    def test_report_grade_b(self):
        report = MeshReport(findings=[Finding(severity=Severity.MEDIUM)] * 3)
        report.compute_summary()
        assert report.grade == "B"

    def test_report_grade_d(self):
        report = MeshReport(findings=[Finding(severity=Severity.HIGH)] * 4)
        report.compute_summary()
        assert report.grade == "D"

    def test_mesh_rules_exist(self):
        assert len(MESH_RULES) == 10
        for i in range(1, 11):
            assert f"MESH-{i:03d}" in MESH_RULES

    def test_all_severities_in_rules(self):
        severities = {rule["severity"] for rule in MESH_RULES.values()}
        assert Severity.CRITICAL in severities
        assert Severity.HIGH in severities
        assert Severity.MEDIUM in severities
        assert Severity.LOW in severities

    def test_resource_kinds(self):
        assert len(ResourceKind) == 10

    def test_tls_modes(self):
        assert len(TLSMode) == 6
