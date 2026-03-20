"""Data models for service mesh configuration analysis."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MeshProvider(str, Enum):
    ISTIO = "istio"
    LINKERD = "linkerd"
    CONSUL = "consul"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ResourceKind(str, Enum):
    VIRTUAL_SERVICE = "VirtualService"
    DESTINATION_RULE = "DestinationRule"
    GATEWAY = "Gateway"
    SERVICE_ENTRY = "ServiceEntry"
    PEER_AUTHENTICATION = "PeerAuthentication"
    AUTHORIZATION_POLICY = "AuthorizationPolicy"
    SIDECAR = "Sidecar"
    ENVOY_FILTER = "EnvoyFilter"
    REQUEST_AUTHENTICATION = "RequestAuthentication"
    TRAFFIC_POLICY = "TrafficPolicy"


class TrafficProtocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    GRPC = "grpc"
    TCP = "tcp"
    TLS = "tls"


class LoadBalancerAlgorithm(str, Enum):
    ROUND_ROBIN = "ROUND_ROBIN"
    LEAST_CONN = "LEAST_CONNECTION"
    RANDOM = "RANDOM"
    PASSTHROUGH = "PASSTHROUGH"
    CONSISTENT_HASH = "CONSISTENT_HASH"


class TLSMode(str, Enum):
    DISABLE = "DISABLE"
    SIMPLE = "SIMPLE"
    MUTUAL = "MUTUAL"
    ISTIO_MUTUAL = "ISTIO_MUTUAL"
    PERMISSIVE = "PERMISSIVE"
    STRICT = "STRICT"


@dataclass
class RetryPolicy:
    attempts: int = 3
    per_try_timeout: str = "2s"
    retry_on: str = "5xx,reset,connect-failure"


@dataclass
class CircuitBreaker:
    max_connections: int = 1024
    max_pending_requests: int = 1024
    max_requests: int = 1024
    max_retries: int = 3
    consecutive_errors: int = 5
    interval: str = "10s"
    base_ejection_time: str = "30s"
    max_ejection_percent: int = 50


@dataclass
class TrafficRoute:
    destination_host: str = ""
    destination_port: int = 80
    weight: int = 100
    subset: str = ""
    headers_match: dict = field(default_factory=dict)


@dataclass
class MeshResource:
    kind: ResourceKind = ResourceKind.VIRTUAL_SERVICE
    name: str = ""
    namespace: str = "default"
    provider: MeshProvider = MeshProvider.ISTIO
    hosts: list[str] = field(default_factory=list)
    gateways: list[str] = field(default_factory=list)
    tls_mode: TLSMode = TLSMode.DISABLE
    protocol: TrafficProtocol = TrafficProtocol.HTTP
    routes: list[TrafficRoute] = field(default_factory=list)
    retry_policy: RetryPolicy | None = None
    circuit_breaker: CircuitBreaker | None = None
    load_balancer: LoadBalancerAlgorithm = LoadBalancerAlgorithm.ROUND_ROBIN
    timeout: str = ""
    labels: dict[str, str] = field(default_factory=dict)
    raw_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    rule_id: str = ""
    title: str = ""
    severity: Severity = Severity.INFO
    resource_name: str = ""
    resource_kind: str = ""
    namespace: str = "default"
    description: str = ""
    recommendation: str = ""


@dataclass
class MeshReport:
    provider: MeshProvider = MeshProvider.ISTIO
    resources: list[MeshResource] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    total_resources: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    health_score: float = 100.0
    grade: str = "A"

    def compute_summary(self):
        self.total_resources = len(self.resources)
        self.critical_count = sum(1 for f in self.findings if f.severity == Severity.CRITICAL)
        self.high_count = sum(1 for f in self.findings if f.severity == Severity.HIGH)
        self.medium_count = sum(1 for f in self.findings if f.severity == Severity.MEDIUM)
        self.low_count = sum(1 for f in self.findings if f.severity == Severity.LOW)
        self.info_count = sum(1 for f in self.findings if f.severity == Severity.INFO)
        penalty = (self.critical_count * 15) + (self.high_count * 10) + (self.medium_count * 5) + (self.low_count * 2)
        self.health_score = max(0.0, 100.0 - penalty)
        if self.health_score >= 90:
            self.grade = "A"
        elif self.health_score >= 80:
            self.grade = "B"
        elif self.health_score >= 70:
            self.grade = "C"
        elif self.health_score >= 60:
            self.grade = "D"
        else:
            self.grade = "F"


MESH_RULES = {
    "MESH-001": {
        "title": "mTLS Not Enforced",
        "severity": Severity.CRITICAL,
        "description": "Mutual TLS is not enabled, traffic is unencrypted",
        "recommendation": "Enable STRICT mTLS via PeerAuthentication",
    },
    "MESH-002": {
        "title": "No Circuit Breaker Configured",
        "severity": Severity.HIGH,
        "description": "Service has no circuit breaker, risking cascading failures",
        "recommendation": "Add connectionPool and outlierDetection to DestinationRule",
    },
    "MESH-003": {
        "title": "No Retry Policy Configured",
        "severity": Severity.MEDIUM,
        "description": "No retry policy set on VirtualService routes",
        "recommendation": "Add retries with per_try_timeout and retry_on conditions",
    },
    "MESH-004": {
        "title": "No Request Timeout Set",
        "severity": Severity.MEDIUM,
        "description": "VirtualService has no timeout, requests may hang indefinitely",
        "recommendation": "Set a timeout on VirtualService HTTP routes",
    },
    "MESH-005": {
        "title": "Permissive Authorization Policy",
        "severity": Severity.HIGH,
        "description": "AuthorizationPolicy allows all traffic without restrictions",
        "recommendation": "Define specific allow rules with principals and methods",
    },
    "MESH-006": {
        "title": "Traffic Weight Mismatch",
        "severity": Severity.HIGH,
        "description": "Route weights do not sum to 100",
        "recommendation": "Ensure route weights total exactly 100 for traffic splitting",
    },
    "MESH-007": {
        "title": "Gateway TLS Not Configured",
        "severity": Severity.CRITICAL,
        "description": "Gateway accepts plaintext HTTP traffic",
        "recommendation": "Configure TLS on Gateway with SIMPLE or MUTUAL mode",
    },
    "MESH-008": {
        "title": "No Rate Limiting Configured",
        "severity": Severity.MEDIUM,
        "description": "No rate limiting policy found for external-facing services",
        "recommendation": "Add EnvoyFilter or use rate limit service for traffic control",
    },
    "MESH-009": {
        "title": "Sidecar Injection Missing",
        "severity": Severity.HIGH,
        "description": "Namespace or pod lacks sidecar injection label",
        "recommendation": "Add istio-injection=enabled label to namespace",
    },
    "MESH-010": {
        "title": "Outlier Detection Too Aggressive",
        "severity": Severity.LOW,
        "description": "Max ejection percent above 80% may cause service unavailability",
        "recommendation": "Keep maxEjectionPercent at 50% or below",
    },
}
