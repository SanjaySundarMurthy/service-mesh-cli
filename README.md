# 🕸️ service-mesh-cli

[![CI](https://github.com/SanjaySundarMurthy/service-mesh-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/SanjaySundarMurthy/service-mesh-cli/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/service-mesh-cli)](https://pypi.org/project/service-mesh-cli/)
[![PyPI](https://img.shields.io/pypi/v/service-mesh-cli)](https://pypi.org/project/service-mesh-cli/)

**Service mesh configuration validator and traffic policy analyzer for Istio, Linkerd, and Consul.**

Validates mesh configurations against **10 best-practice rules** (MESH-001 → MESH-010) covering mTLS enforcement, circuit breakers, retry policies, gateway TLS, authorization policies, traffic weight correctness, rate limiting, sidecar injection, and outlier detection — with health scoring, grading, and multi-format reporting.

---

## ✨ Features

- 🔒 **10 validation rules** — MESH-001 to MESH-010, from critical security to operational best practices
- 🏥 **Health scoring** — 0–100 score with letter grades (A–F) based on finding severity
- 📊 **Multi-format output** — Rich terminal tables, JSON, and HTML reports
- 🎯 **CI/CD integration** — `--fail-on` threshold exits non-zero on severity match
- 🐳 **Docker-ready** — Multi-stage Dockerfile with non-root user
- 🔍 **Multi-mesh support** — Istio, Linkerd (ServiceProfile), and Consul provider targeting
- 📁 **File export** — Save JSON/HTML reports directly to file with `-o`

## 📦 Installation

```bash
pip install service-mesh-cli
```

**Development install:**

```bash
git clone https://github.com/SanjaySundarMurthy/service-mesh-cli.git
cd service-mesh-cli
pip install -e ".[dev]"
```

## 🚀 Usage

```bash
# Validate mesh config (default: Istio, terminal output)
service-mesh-cli validate mesh-config.yaml

# Specify mesh provider
service-mesh-cli validate mesh-config.yaml --provider linkerd

# Fail in CI if critical findings exist
service-mesh-cli validate mesh-config.yaml --fail-on critical

# JSON output
service-mesh-cli validate mesh-config.yaml --format json

# HTML report saved to file
service-mesh-cli validate mesh-config.yaml --format html -o report.html

# Quick health summary
service-mesh-cli summary mesh-config.yaml

# Run built-in demo with sample Istio configs
service-mesh-cli demo

# List all validation rules
service-mesh-cli rules

# Show version
service-mesh-cli --version
```

---

## 📋 Command Reference

### `validate`

Validate mesh configuration files against best practices.

```
service-mesh-cli validate <CONFIG_FILE> [OPTIONS]
```

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--provider` | `istio`, `linkerd`, `consul` | `istio` | Target mesh platform |
| `--format` | `terminal`, `json`, `html` | `terminal` | Output format |
| `--fail-on` | `critical`, `high`, `medium`, `low` | — | Exit code 1 if findings at this severity or above |
| `--output`, `-o` | file path | — | Write report to file |

### `summary`

Show a brief health summary of a mesh configuration.

```
service-mesh-cli summary <CONFIG_FILE> [--provider istio|linkerd|consul]
```

### `demo`

Run the built-in demo with sample Istio configurations showing intentional issues.

```
service-mesh-cli demo [--format terminal|json|html]
```

### `rules`

Display all 10 validation rules in a formatted table.

```
service-mesh-cli rules
```

---

## 📄 Sample Output

```
🕸️ Service Mesh Validation Report
─────────────────────────────────
Provider:     ISTIO
Resources:    7
Health Score: 25.0/100 (Grade F)
Findings:     7 (🔴 2 🟠 3 🟡 1 🔵 0 ⚪ 0)

┌──────────┬──────────┬─────────────────────┬────────────────────────────────┬─────────────────────────────────┐
│ Rule     │ Severity │ Resource            │ Issue                          │ Recommendation                  │
├──────────┼──────────┼─────────────────────┼────────────────────────────────┼─────────────────────────────────┤
│ MESH-007 │ CRITICAL │ Gateway/frontend-gw │ Gateway accepts plaintext HTTP │ Configure TLS on Gateway        │
│ MESH-001 │ CRITICAL │ PeerAuth/default-pa │ mTLS is not enabled            │ Enable STRICT mTLS              │
│ MESH-006 │ HIGH     │ VS/frontend-vs      │ Route weights sum to 110       │ Ensure weights total 100        │
│ MESH-009 │ HIGH     │ VS/frontend-vs      │ No sidecar config in namespace │ Add sidecar injection label     │
│ MESH-005 │ HIGH     │ AuthPol/allow-all   │ Allows all traffic             │ Define specific allow rules     │
│ MESH-008 │ MEDIUM   │ VS/frontend-vs      │ No rate limiting               │ Add EnvoyFilter for rate limits │
│ MESH-010 │ LOW      │ DR/payment-dr       │ Max ejection percent >80%      │ Keep at 50% or below            │
└──────────┴──────────┴─────────────────────┴────────────────────────────────┴─────────────────────────────────┘
```

---

## ✅ Validation Rules

| Rule ID   | Severity   | Title                              | Description |
|-----------|------------|------------------------------------|-------------|
| MESH-001  | CRITICAL   | mTLS Not Enforced                  | Mutual TLS is not enabled, traffic is unencrypted |
| MESH-002  | HIGH       | No Circuit Breaker Configured      | Service has no circuit breaker, risking cascading failures |
| MESH-003  | MEDIUM     | No Retry Policy Configured         | No retry policy set on VirtualService routes |
| MESH-004  | MEDIUM     | No Request Timeout Set             | VirtualService has no timeout, requests may hang indefinitely |
| MESH-005  | HIGH       | Permissive Authorization Policy    | AuthorizationPolicy allows all traffic without restrictions |
| MESH-006  | HIGH       | Traffic Weight Mismatch            | Route weights do not sum to 100 |
| MESH-007  | CRITICAL   | Gateway TLS Not Configured         | Gateway accepts plaintext HTTP traffic |
| MESH-008  | MEDIUM     | No Rate Limiting Configured        | No rate limiting policy found for external-facing services |
| MESH-009  | HIGH       | Sidecar Injection Missing          | Namespace or pod lacks sidecar injection label |
| MESH-010  | LOW        | Outlier Detection Too Aggressive   | Max ejection percent above 80% may cause service unavailability |

## 🏥 Health Scoring & Grading

The health score starts at **100** and deducts points per finding severity:

| Severity | Penalty |
|----------|---------|
| Critical | −15     |
| High     | −10     |
| Medium   | −5      |
| Low      | −2      |

**Grade scale:**

| Score Range | Grade |
|-------------|-------|
| 90–100      | A     |
| 80–89       | B     |
| 70–79       | C     |
| 60–69       | D     |
| 0–59        | F     |

---

## 🔧 Configuration File Format

service-mesh-cli accepts standard Istio/Linkerd YAML resources (multi-document supported):

```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: frontend-gw
  namespace: production
spec:
  servers:
  - port:
      number: 443
      protocol: HTTPS
    tls:
      mode: SIMPLE
    hosts:
    - "app.example.com"
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: api-vs
  namespace: production
spec:
  hosts:
  - api-service
  http:
  - timeout: 10s
    retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: 5xx,reset
    route:
    - destination:
        host: api-service
        port:
          number: 8080
      weight: 100
---
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: strict-mtls
  namespace: production
spec:
  mtls:
    mode: STRICT
```

### Supported Resource Types

| Kind | Mesh | Rules Checked |
|------|------|---------------|
| `VirtualService` | Istio | MESH-003, MESH-004, MESH-006, MESH-008, MESH-009 |
| `DestinationRule` | Istio | MESH-001, MESH-002, MESH-010 |
| `Gateway` | Istio | MESH-007 |
| `PeerAuthentication` | Istio | MESH-001 |
| `AuthorizationPolicy` | Istio | MESH-005 |
| `EnvoyFilter` | Istio | (suppresses MESH-008) |
| `Sidecar` | Istio | (suppresses MESH-009) |
| `RequestAuthentication` | Istio | JWT validation metadata |
| `ServiceEntry` | Istio | Parsed & tracked |
| `ServiceProfile` | Linkerd | Retry budget, route timeouts |

---

## 🏗️ Project Structure

```
service-mesh-cli/
├── service_mesh_cli/
│   ├── __init__.py              # Package version
│   ├── cli.py                   # Click CLI commands (validate, demo, rules, summary)
│   ├── models.py                # Data models, enums, MESH_RULES definitions
│   ├── parser.py                # YAML parser for mesh resources
│   ├── demo.py                  # Demo data generator
│   ├── analyzers/
│   │   ├── __init__.py
│   │   └── mesh_validator.py    # 10 validation rule implementations
│   └── reporters/
│       ├── __init__.py
│       ├── terminal_reporter.py # Rich terminal output
│       └── export_reporter.py   # JSON and HTML export
├── tests/
│   ├── conftest.py              # Shared test fixtures
│   ├── test_analyzers.py        # Parser + validator tests
│   ├── test_cli.py              # CLI integration tests
│   ├── test_models.py           # Data model tests
│   └── test_reporters.py        # Reporter output tests
├── blog/
│   └── dev-to-service-mesh-cli.md
├── .github/workflows/ci.yml     # CI/CD pipeline
├── Dockerfile                   # Multi-stage Docker build
├── .dockerignore
├── .gitignore
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## 🐳 Docker

Run without installing Python:

```bash
# Build the image
docker build -t service-mesh-cli .

# Run help
docker run --rm service-mesh-cli --help

# Validate a local config
docker run --rm -v ${PWD}:/workspace service-mesh-cli validate /workspace/mesh-config.yaml

# JSON output
docker run --rm -v ${PWD}:/workspace service-mesh-cli validate /workspace/mesh-config.yaml --format json
```

Or pull from the container registry:

```bash
docker pull ghcr.io/SanjaySundarMurthy/service-mesh-cli:latest
docker run --rm ghcr.io/SanjaySundarMurthy/service-mesh-cli:latest --help
```

## 🧪 Testing

```bash
# Run all 72 tests
pytest -v

# Run with coverage
pytest --cov=service_mesh_cli -v

# Lint check
ruff check .
```

**Test breakdown:**
- **Analyzer tests** — 30 tests covering all 10 rules (positive & negative), parser for all resource types, edge cases
- **CLI tests** — 15 tests covering all commands (validate, demo, rules, summary, version, help), output formats, fail-on
- **Model tests** — 15 tests covering data models, grading, scoring, enum counts
- **Reporter tests** — 8 tests covering JSON, HTML, terminal output, edge cases
- **Parser tests** — Extended tests for RequestAuthentication, ServiceProfile, load balancers, auth policies

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please ensure tests pass before submitting:

```bash
pip install -e ".[dev]"
pytest -v
ruff check .
```

## 🔗 Links

- **PyPI**: [https://pypi.org/project/service-mesh-cli/](https://pypi.org/project/service-mesh-cli/)
- **GitHub**: [https://github.com/SanjaySundarMurthy/service-mesh-cli](https://github.com/SanjaySundarMurthy/service-mesh-cli)
- **Issues**: [https://github.com/SanjaySundarMurthy/service-mesh-cli/issues](https://github.com/SanjaySundarMurthy/service-mesh-cli/issues)

## 📄 License

MIT
