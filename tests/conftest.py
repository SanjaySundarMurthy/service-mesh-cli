"""Shared test fixtures for service-mesh-cli."""
import pytest
from service_mesh_cli.models import (
    MeshResource, ResourceKind, MeshProvider, TLSMode, Severity,
    TrafficRoute, RetryPolicy, CircuitBreaker, LoadBalancerAlgorithm,
    TrafficProtocol, MeshReport, Finding,
)


@pytest.fixture
def virtual_service_no_retry():
    return MeshResource(
        kind=ResourceKind.VIRTUAL_SERVICE,
        name="frontend-vs",
        namespace="production",
        hosts=["frontend"],
        gateways=["frontend-gw"],
        routes=[
            TrafficRoute(destination_host="frontend-v1", weight=80),
            TrafficRoute(destination_host="frontend-v2", weight=20),
        ],
    )


@pytest.fixture
def virtual_service_with_retry():
    return MeshResource(
        kind=ResourceKind.VIRTUAL_SERVICE,
        name="api-vs",
        namespace="production",
        hosts=["api-service"],
        timeout="10s",
        retry_policy=RetryPolicy(attempts=3, per_try_timeout="2s"),
        routes=[TrafficRoute(destination_host="api-service", weight=100)],
    )


@pytest.fixture
def virtual_service_bad_weights():
    return MeshResource(
        kind=ResourceKind.VIRTUAL_SERVICE,
        name="canary-vs",
        namespace="staging",
        hosts=["canary"],
        routes=[
            TrafficRoute(destination_host="canary-v1", weight=80),
            TrafficRoute(destination_host="canary-v2", weight=30),
        ],
    )


@pytest.fixture
def destination_rule_no_tls():
    return MeshResource(
        kind=ResourceKind.DESTINATION_RULE,
        name="api-dr",
        namespace="production",
        hosts=["api-service"],
        tls_mode=TLSMode.DISABLE,
    )


@pytest.fixture
def destination_rule_with_cb():
    return MeshResource(
        kind=ResourceKind.DESTINATION_RULE,
        name="payment-dr",
        namespace="production",
        hosts=["payment-service"],
        tls_mode=TLSMode.ISTIO_MUTUAL,
        circuit_breaker=CircuitBreaker(max_ejection_percent=50),
    )


@pytest.fixture
def destination_rule_aggressive_outlier():
    return MeshResource(
        kind=ResourceKind.DESTINATION_RULE,
        name="aggressive-dr",
        namespace="production",
        tls_mode=TLSMode.ISTIO_MUTUAL,
        circuit_breaker=CircuitBreaker(max_ejection_percent=90),
    )


@pytest.fixture
def gateway_no_tls():
    return MeshResource(
        kind=ResourceKind.GATEWAY,
        name="frontend-gw",
        namespace="production",
        hosts=["app.example.com"],
        tls_mode=TLSMode.DISABLE,
        protocol=TrafficProtocol.HTTP,
    )


@pytest.fixture
def gateway_with_tls():
    return MeshResource(
        kind=ResourceKind.GATEWAY,
        name="secure-gw",
        namespace="production",
        hosts=["secure.example.com"],
        tls_mode=TLSMode.SIMPLE,
        protocol=TrafficProtocol.HTTPS,
    )


@pytest.fixture
def peer_auth_permissive():
    return MeshResource(
        kind=ResourceKind.PEER_AUTHENTICATION,
        name="default-pa",
        namespace="production",
        tls_mode=TLSMode.PERMISSIVE,
    )


@pytest.fixture
def peer_auth_strict():
    return MeshResource(
        kind=ResourceKind.PEER_AUTHENTICATION,
        name="strict-pa",
        namespace="production",
        tls_mode=TLSMode.STRICT,
    )


@pytest.fixture
def auth_policy_permissive():
    return MeshResource(
        kind=ResourceKind.AUTHORIZATION_POLICY,
        name="allow-all",
        namespace="production",
        labels={"_permissive": "true"},
    )


@pytest.fixture
def sidecar_resource():
    return MeshResource(
        kind=ResourceKind.SIDECAR,
        name="default-sidecar",
        namespace="production",
    )


@pytest.fixture
def envoy_filter():
    return MeshResource(
        kind=ResourceKind.ENVOY_FILTER,
        name="rate-limiter",
        namespace="production",
    )


@pytest.fixture
def sample_mesh_yaml():
    return """apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: test-gw
  namespace: default
spec:
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
    hosts:
    - "*.example.com"
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: test-vs
  namespace: default
spec:
  hosts:
  - test-service
  gateways:
  - test-gw
  http:
  - timeout: 5s
    retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: 5xx,reset
    route:
    - destination:
        host: test-service
        port:
          number: 8080
      weight: 100
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: test-dr
  namespace: default
spec:
  host: test-service
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
    connectionPool:
      tcp:
        maxConnections: 100
    outlierDetection:
      consecutiveErrors: 5
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
---
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: strict-pa
  namespace: default
spec:
  mtls:
    mode: STRICT
"""
