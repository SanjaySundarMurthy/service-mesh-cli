"""Tests for mesh validator and parser."""
from service_mesh_cli.models import (
    MeshResource, ResourceKind, TLSMode,
)
from service_mesh_cli.parser import parse_resources, parse_yaml
from service_mesh_cli.analyzers.mesh_validator import validate_mesh


class TestParser:
    def test_parse_yaml_multi_doc(self, sample_mesh_yaml):
        docs = parse_yaml(sample_mesh_yaml)
        assert len(docs) == 4

    def test_parse_resources(self, sample_mesh_yaml):
        resources = parse_resources(sample_mesh_yaml)
        assert len(resources) == 4
        kinds = [r.kind for r in resources]
        assert ResourceKind.GATEWAY in kinds
        assert ResourceKind.VIRTUAL_SERVICE in kinds
        assert ResourceKind.DESTINATION_RULE in kinds
        assert ResourceKind.PEER_AUTHENTICATION in kinds

    def test_parse_gateway_tls(self, sample_mesh_yaml):
        resources = parse_resources(sample_mesh_yaml)
        gw = [r for r in resources if r.kind == ResourceKind.GATEWAY][0]
        assert gw.tls_mode == TLSMode.SIMPLE
        assert "*.example.com" in gw.hosts

    def test_parse_virtual_service(self, sample_mesh_yaml):
        resources = parse_resources(sample_mesh_yaml)
        vs = [r for r in resources if r.kind == ResourceKind.VIRTUAL_SERVICE][0]
        assert vs.timeout == "5s"
        assert vs.retry_policy is not None
        assert vs.retry_policy.attempts == 3
        assert len(vs.routes) == 1
        assert vs.routes[0].weight == 100

    def test_parse_destination_rule(self, sample_mesh_yaml):
        resources = parse_resources(sample_mesh_yaml)
        dr = [r for r in resources if r.kind == ResourceKind.DESTINATION_RULE][0]
        assert dr.tls_mode == TLSMode.ISTIO_MUTUAL
        assert dr.circuit_breaker is not None
        assert dr.circuit_breaker.max_ejection_percent == 50

    def test_parse_peer_auth(self, sample_mesh_yaml):
        resources = parse_resources(sample_mesh_yaml)
        pa = [r for r in resources if r.kind == ResourceKind.PEER_AUTHENTICATION][0]
        assert pa.tls_mode == TLSMode.STRICT

    def test_parse_unknown_kind(self):
        yaml_content = "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: test\n"
        resources = parse_resources(yaml_content)
        assert len(resources) == 0

    def test_parse_empty(self):
        resources = parse_resources("")
        assert resources == []


class TestMeshValidator:
    def test_mesh001_mtls_permissive(self, peer_auth_permissive):
        report = validate_mesh([peer_auth_permissive])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-001" in rule_ids

    def test_mesh001_mtls_strict_no_finding(self, peer_auth_strict):
        report = validate_mesh([peer_auth_strict])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-001" not in rule_ids

    def test_mesh001_destination_rule_no_tls(self, destination_rule_no_tls):
        report = validate_mesh([destination_rule_no_tls])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-001" in rule_ids

    def test_mesh002_no_circuit_breaker(self, destination_rule_no_tls):
        report = validate_mesh([destination_rule_no_tls])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-002" in rule_ids

    def test_mesh002_with_circuit_breaker(self, destination_rule_with_cb):
        report = validate_mesh([destination_rule_with_cb])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-002" not in rule_ids

    def test_mesh003_no_retry(self, virtual_service_no_retry):
        report = validate_mesh([virtual_service_no_retry])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-003" in rule_ids

    def test_mesh003_with_retry(self, virtual_service_with_retry):
        report = validate_mesh([virtual_service_with_retry])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-003" not in rule_ids

    def test_mesh004_no_timeout(self, virtual_service_no_retry):
        report = validate_mesh([virtual_service_no_retry])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-004" in rule_ids

    def test_mesh004_with_timeout(self, virtual_service_with_retry):
        report = validate_mesh([virtual_service_with_retry])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-004" not in rule_ids

    def test_mesh005_permissive_auth(self, auth_policy_permissive):
        report = validate_mesh([auth_policy_permissive])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-005" in rule_ids

    def test_mesh006_bad_weights(self, virtual_service_bad_weights):
        report = validate_mesh([virtual_service_bad_weights])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-006" in rule_ids

    def test_mesh006_good_weights(self, virtual_service_no_retry):
        report = validate_mesh([virtual_service_no_retry])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-006" not in rule_ids

    def test_mesh007_gateway_no_tls(self, gateway_no_tls):
        report = validate_mesh([gateway_no_tls])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-007" in rule_ids

    def test_mesh007_gateway_with_tls(self, gateway_with_tls):
        report = validate_mesh([gateway_with_tls])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-007" not in rule_ids

    def test_mesh008_no_rate_limiting(self, virtual_service_no_retry):
        report = validate_mesh([virtual_service_no_retry])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-008" in rule_ids

    def test_mesh008_with_envoy_filter(self, virtual_service_no_retry, envoy_filter):
        report = validate_mesh([virtual_service_no_retry, envoy_filter])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-008" not in rule_ids

    def test_mesh009_no_sidecar(self, virtual_service_no_retry):
        report = validate_mesh([virtual_service_no_retry])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-009" in rule_ids

    def test_mesh009_with_sidecar(self, virtual_service_no_retry, sidecar_resource):
        report = validate_mesh([virtual_service_no_retry, sidecar_resource])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-009" not in rule_ids

    def test_mesh010_aggressive_outlier(self, destination_rule_aggressive_outlier):
        report = validate_mesh([destination_rule_aggressive_outlier])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-010" in rule_ids

    def test_mesh010_normal_outlier(self, destination_rule_with_cb):
        report = validate_mesh([destination_rule_with_cb])
        rule_ids = [f.rule_id for f in report.findings]
        assert "MESH-010" not in rule_ids

    def test_well_configured_mesh(self, sample_mesh_yaml):
        resources = parse_resources(sample_mesh_yaml)
        report = validate_mesh(resources)
        # Well-configured: strict PA, TLS gateway, retry+timeout on VS, CB on DR
        # But no sidecar and no envoy filter, so MESH-008 and MESH-009 fire on the VS
        assert report.health_score > 0

    def test_report_has_correct_counts(self):
        resources = [
            MeshResource(kind=ResourceKind.GATEWAY, name="gw", tls_mode=TLSMode.DISABLE),
            MeshResource(kind=ResourceKind.PEER_AUTHENTICATION, name="pa", tls_mode=TLSMode.PERMISSIVE),
        ]
        report = validate_mesh(resources)
        assert report.critical_count >= 1  # MESH-001 and MESH-007


class TestParserExtended:
    def test_parse_request_authentication(self):
        yaml_content = """apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: jwt-auth
  namespace: default
spec:
  jwtRules:
  - issuer: https://auth.example.com
    jwksUri: https://auth.example.com/.well-known/jwks.json
"""
        resources = parse_resources(yaml_content)
        assert len(resources) == 1
        assert resources[0].kind == ResourceKind.REQUEST_AUTHENTICATION
        assert resources[0].labels.get("_has_jwt") == "true"

    def test_parse_request_authentication_no_jwt(self):
        yaml_content = """apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: empty-auth
  namespace: default
spec: {}
"""
        resources = parse_resources(yaml_content)
        assert len(resources) == 1
        assert resources[0].labels.get("_no_jwt") == "true"

    def test_parse_service_profile(self):
        yaml_content = """apiVersion: linkerd.io/v1alpha2
kind: ServiceProfile
metadata:
  name: web-svc.default.svc.cluster.local
  namespace: default
spec:
  retryBudget:
    retryRatio: 0.2
    minRetriesPerSecond: 10
    ttl: 10s
  routes:
  - name: GET /api/v1/users
    condition:
      method: GET
      pathRegex: /api/v1/users
    timeout: 5s
"""
        resources = parse_resources(yaml_content)
        assert len(resources) == 1
        assert resources[0].kind == ResourceKind.SERVICE_PROFILE
        assert resources[0].timeout == "5s"
        assert len(resources[0].routes) == 1

    def test_parse_linkerd_provider(self):
        from service_mesh_cli.models import MeshProvider
        yaml_content = """apiVersion: linkerd.io/v1alpha2
kind: ServiceProfile
metadata:
  name: web-svc
  namespace: default
spec:
  routes:
  - name: GET /api
    condition:
      pathRegex: /api
"""
        resources = parse_resources(yaml_content, MeshProvider.LINKERD)
        assert len(resources) == 1
        assert resources[0].provider == MeshProvider.LINKERD

    def test_parse_gateway_http_protocol(self):
        yaml_content = """apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: http-gw
  namespace: default
spec:
  servers:
  - port:
      number: 80
      protocol: HTTP
    hosts:
    - "*.example.com"
"""
        resources = parse_resources(yaml_content)
        assert len(resources) == 1
        assert resources[0].tls_mode == TLSMode.DISABLE

    def test_parse_destination_rule_load_balancer(self):
        yaml_content = """apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: test-dr
  namespace: default
spec:
  host: test-service
  trafficPolicy:
    loadBalancer:
      simple: LEAST_CONN
"""
        from service_mesh_cli.models import LoadBalancerAlgorithm
        resources = parse_resources(yaml_content)
        assert len(resources) == 1
        assert resources[0].load_balancer == LoadBalancerAlgorithm.LEAST_CONN

    def test_parse_auth_policy_with_rules(self):
        yaml_content = """apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: strict-auth
  namespace: default
spec:
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/default/sa/web"]
"""
        resources = parse_resources(yaml_content)
        assert len(resources) == 1
        assert resources[0].labels.get("_has_rules") == "true"
        assert resources[0].labels.get("_permissive") is None
