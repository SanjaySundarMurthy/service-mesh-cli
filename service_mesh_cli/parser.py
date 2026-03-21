"""Parse mesh configuration YAML files into MeshResource objects."""
import yaml
from .models import (
    MeshResource, ResourceKind, MeshProvider, TLSMode, TrafficProtocol,
    TrafficRoute, RetryPolicy, CircuitBreaker, LoadBalancerAlgorithm,
)

KIND_MAP = {
    "VirtualService": ResourceKind.VIRTUAL_SERVICE,
    "DestinationRule": ResourceKind.DESTINATION_RULE,
    "Gateway": ResourceKind.GATEWAY,
    "ServiceEntry": ResourceKind.SERVICE_ENTRY,
    "PeerAuthentication": ResourceKind.PEER_AUTHENTICATION,
    "AuthorizationPolicy": ResourceKind.AUTHORIZATION_POLICY,
    "Sidecar": ResourceKind.SIDECAR,
    "EnvoyFilter": ResourceKind.ENVOY_FILTER,
    "RequestAuthentication": ResourceKind.REQUEST_AUTHENTICATION,
    "ServiceProfile": ResourceKind.SERVICE_PROFILE,
}

TLS_MAP = {
    "DISABLE": TLSMode.DISABLE,
    "SIMPLE": TLSMode.SIMPLE,
    "MUTUAL": TLSMode.MUTUAL,
    "ISTIO_MUTUAL": TLSMode.ISTIO_MUTUAL,
    "PERMISSIVE": TLSMode.PERMISSIVE,
    "STRICT": TLSMode.STRICT,
}

LB_MAP = {
    "ROUND_ROBIN": LoadBalancerAlgorithm.ROUND_ROBIN,
    "LEAST_CONN": LoadBalancerAlgorithm.LEAST_CONN,
    "RANDOM": LoadBalancerAlgorithm.RANDOM,
    "PASSTHROUGH": LoadBalancerAlgorithm.PASSTHROUGH,
    "CONSISTENT_HASH": LoadBalancerAlgorithm.CONSISTENT_HASH,
}


def parse_yaml(yaml_content: str) -> list[dict]:
    """Parse YAML content, handling multi-document YAML."""
    docs = []
    for doc in yaml.safe_load_all(yaml_content):
        if doc:
            docs.append(doc)
    return docs


def parse_resources(yaml_content: str, provider: MeshProvider = MeshProvider.ISTIO) -> list[MeshResource]:
    """Parse YAML into MeshResource objects."""
    docs = parse_yaml(yaml_content)
    resources = []
    for doc in docs:
        kind_str = doc.get("kind", "")
        if kind_str not in KIND_MAP:
            continue
        metadata = doc.get("metadata", {})
        spec = doc.get("spec", {})
        resource = MeshResource(
            kind=KIND_MAP[kind_str],
            name=metadata.get("name", "unknown"),
            namespace=metadata.get("namespace", "default"),
            provider=provider,
            labels=metadata.get("labels", {}),
            raw_config=doc,
        )
        # Parse kind-specific fields
        if kind_str == "VirtualService":
            _parse_virtual_service(resource, spec)
        elif kind_str == "DestinationRule":
            _parse_destination_rule(resource, spec)
        elif kind_str == "Gateway":
            _parse_gateway(resource, spec)
        elif kind_str == "PeerAuthentication":
            _parse_peer_auth(resource, spec)
        elif kind_str == "AuthorizationPolicy":
            _parse_auth_policy(resource, spec)
        elif kind_str == "RequestAuthentication":
            _parse_request_auth(resource, spec)
        elif kind_str == "ServiceProfile":
            _parse_service_profile(resource, spec)
        resources.append(resource)
    return resources


def _parse_virtual_service(resource: MeshResource, spec: dict):
    resource.hosts = spec.get("hosts", [])
    resource.gateways = spec.get("gateways", [])
    http_routes = spec.get("http", [])
    for http_route in http_routes:
        timeout = http_route.get("timeout", "")
        if timeout:
            resource.timeout = timeout
        retries = http_route.get("retries", {})
        if retries:
            resource.retry_policy = RetryPolicy(
                attempts=retries.get("attempts", 3),
                per_try_timeout=retries.get("perTryTimeout", "2s"),
                retry_on=retries.get("retryOn", "5xx"),
            )
        for route_entry in http_route.get("route", []):
            dest = route_entry.get("destination", {})
            resource.routes.append(TrafficRoute(
                destination_host=dest.get("host", ""),
                destination_port=dest.get("port", {}).get("number", 80),
                weight=route_entry.get("weight", 100),
                subset=dest.get("subset", ""),
            ))


def _parse_destination_rule(resource: MeshResource, spec: dict):
    resource.hosts = [spec.get("host", "")]
    tp = spec.get("trafficPolicy", {})
    tls = tp.get("tls", {})
    tls_mode = tls.get("mode", "DISABLE")
    resource.tls_mode = TLS_MAP.get(tls_mode, TLSMode.DISABLE)
    lb = tp.get("loadBalancer", {})
    lb_simple = lb.get("simple", "ROUND_ROBIN")
    resource.load_balancer = LB_MAP.get(lb_simple, LoadBalancerAlgorithm.ROUND_ROBIN)
    conn_pool = tp.get("connectionPool", {})
    outlier = tp.get("outlierDetection", {})
    if conn_pool or outlier:
        tcp = conn_pool.get("tcp", {})
        http = conn_pool.get("http", {})
        resource.circuit_breaker = CircuitBreaker(
            max_connections=tcp.get("maxConnections", 1024),
            max_pending_requests=http.get("h2UpgradePolicy", 1024),
            max_requests=http.get("maxRequestsPerConnection", 1024),
            max_retries=http.get("maxRetries", 3),
            consecutive_errors=outlier.get("consecutiveErrors", 5),
            interval=outlier.get("interval", "10s"),
            base_ejection_time=outlier.get("baseEjectionTime", "30s"),
            max_ejection_percent=outlier.get("maxEjectionPercent", 50),
        )


def _parse_gateway(resource: MeshResource, spec: dict):
    servers = spec.get("servers", [])
    for server in servers:
        port = server.get("port", {})
        protocol = port.get("protocol", "HTTP").upper()
        if protocol in ("HTTPS", "TLS"):
            tls = server.get("tls", {})
            mode = tls.get("mode", "SIMPLE")
            resource.tls_mode = TLS_MAP.get(mode, TLSMode.SIMPLE)
            resource.protocol = TrafficProtocol.HTTPS
        else:
            resource.tls_mode = TLSMode.DISABLE
            resource.protocol = TrafficProtocol.HTTP
        resource.hosts.extend(server.get("hosts", []))


def _parse_peer_auth(resource: MeshResource, spec: dict):
    mtls = spec.get("mtls", {})
    mode = mtls.get("mode", "PERMISSIVE")
    resource.tls_mode = TLS_MAP.get(mode, TLSMode.PERMISSIVE)


def _parse_auth_policy(resource: MeshResource, spec: dict):
    rules = spec.get("rules", [])
    if not rules:
        resource.labels["_permissive"] = "true"
    else:
        resource.labels["_has_rules"] = "true"


def _parse_request_auth(resource: MeshResource, spec: dict):
    """Parse RequestAuthentication — check for JWT rules."""
    jwt_rules = spec.get("jwtRules", [])
    if jwt_rules:
        resource.labels["_has_jwt"] = "true"
    else:
        resource.labels["_no_jwt"] = "true"


def _parse_service_profile(resource: MeshResource, spec: dict):
    """Parse Linkerd ServiceProfile — extract retry budget and routes."""
    retry_budget = spec.get("retryBudget", {})
    if retry_budget:
        resource.retry_policy = RetryPolicy(
            attempts=int(retry_budget.get("retryRatio", 0.2) * 10),
            per_try_timeout=retry_budget.get("ttl", "10s"),
        )
    routes = spec.get("routes", [])
    for route in routes:
        timeout = route.get("timeout", "")
        if timeout:
            resource.timeout = timeout
        condition = route.get("condition", {})
        resource.routes.append(TrafficRoute(
            destination_host=condition.get("pathRegex", ""),
            destination_port=0,
            weight=100,
        ))
