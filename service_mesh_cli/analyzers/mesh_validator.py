"""Mesh configuration validator — applies MESH-001 to MESH-010 rules."""
from ..models import (
    MeshResource, MeshReport, Finding, ResourceKind,
    TLSMode, MESH_RULES, MeshProvider,
)


def validate_mesh(resources: list[MeshResource], provider: MeshProvider = MeshProvider.ISTIO) -> MeshReport:
    """Validate mesh resources and produce a report."""
    report = MeshReport(provider=provider, resources=resources)
    for resource in resources:
        _check_mtls(resource, report)
        _check_circuit_breaker(resource, report)
        _check_retry_policy(resource, report)
        _check_timeout(resource, report)
        _check_auth_policy(resource, report)
        _check_traffic_weights(resource, report)
        _check_gateway_tls(resource, report)
        _check_rate_limiting(resource, resources, report)
        _check_sidecar_injection(resource, resources, report)
        _check_outlier_detection(resource, report)
    report.compute_summary()
    return report


def _make_finding(rule_id: str, resource: MeshResource, **overrides) -> Finding:
    rule = MESH_RULES[rule_id]
    return Finding(
        rule_id=rule_id,
        title=overrides.get("title", rule["title"]),
        severity=overrides.get("severity", rule["severity"]),
        resource_name=resource.name,
        resource_kind=resource.kind.value,
        namespace=resource.namespace,
        description=overrides.get("description", rule["description"]),
        recommendation=overrides.get("recommendation", rule["recommendation"]),
    )


def _check_mtls(resource: MeshResource, report: MeshReport):
    """MESH-001: mTLS not enforced."""
    if resource.kind == ResourceKind.PEER_AUTHENTICATION:
        if resource.tls_mode in (TLSMode.DISABLE, TLSMode.PERMISSIVE):
            report.findings.append(_make_finding("MESH-001", resource))
    elif resource.kind == ResourceKind.DESTINATION_RULE:
        if resource.tls_mode == TLSMode.DISABLE:
            report.findings.append(_make_finding("MESH-001", resource,
                description="DestinationRule has no mTLS configured"))


def _check_circuit_breaker(resource: MeshResource, report: MeshReport):
    """MESH-002: No circuit breaker."""
    if resource.kind == ResourceKind.DESTINATION_RULE and resource.circuit_breaker is None:
        report.findings.append(_make_finding("MESH-002", resource))


def _check_retry_policy(resource: MeshResource, report: MeshReport):
    """MESH-003: No retry policy."""
    if resource.kind == ResourceKind.VIRTUAL_SERVICE and resource.retry_policy is None:
        report.findings.append(_make_finding("MESH-003", resource))


def _check_timeout(resource: MeshResource, report: MeshReport):
    """MESH-004: No timeout."""
    if resource.kind == ResourceKind.VIRTUAL_SERVICE and not resource.timeout:
        report.findings.append(_make_finding("MESH-004", resource))


def _check_auth_policy(resource: MeshResource, report: MeshReport):
    """MESH-005: Permissive auth policy."""
    if resource.kind == ResourceKind.AUTHORIZATION_POLICY:
        if resource.labels.get("_permissive") == "true":
            report.findings.append(_make_finding("MESH-005", resource))


def _check_traffic_weights(resource: MeshResource, report: MeshReport):
    """MESH-006: Traffic weights don't sum to 100."""
    if resource.kind == ResourceKind.VIRTUAL_SERVICE and len(resource.routes) > 1:
        total = sum(r.weight for r in resource.routes)
        if total != 100:
            report.findings.append(_make_finding("MESH-006", resource,
                description=f"Route weights sum to {total}, expected 100"))


def _check_gateway_tls(resource: MeshResource, report: MeshReport):
    """MESH-007: Gateway without TLS."""
    if resource.kind == ResourceKind.GATEWAY:
        if resource.tls_mode == TLSMode.DISABLE:
            report.findings.append(_make_finding("MESH-007", resource))


def _check_rate_limiting(resource: MeshResource, resources: list[MeshResource], report: MeshReport):
    """MESH-008: No rate limiting for gateway-attached virtual services."""
    if resource.kind == ResourceKind.VIRTUAL_SERVICE and resource.gateways:
        has_envoy_filter = any(r.kind == ResourceKind.ENVOY_FILTER for r in resources)
        if not has_envoy_filter:
            report.findings.append(_make_finding("MESH-008", resource))


def _check_sidecar_injection(resource: MeshResource, resources: list[MeshResource], report: MeshReport):
    """MESH-009: Missing sidecar config."""
    if resource.kind == ResourceKind.VIRTUAL_SERVICE:
        has_sidecar = any(
            r.kind == ResourceKind.SIDECAR and r.namespace == resource.namespace
            for r in resources
        )
        if not has_sidecar:
            report.findings.append(_make_finding("MESH-009", resource))


def _check_outlier_detection(resource: MeshResource, report: MeshReport):
    """MESH-010: Aggressive outlier detection."""
    if resource.kind == ResourceKind.DESTINATION_RULE and resource.circuit_breaker:
        if resource.circuit_breaker.max_ejection_percent > 80:
            report.findings.append(_make_finding("MESH-010", resource))
