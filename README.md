# 🕸️ service-mesh-cli

[![CI](https://github.com/SanjaySundarMurthy/service-mesh-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/SanjaySundarMurthy/service-mesh-cli/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/service-mesh-cli)](https://pypi.org/project/service-mesh-cli/)
[![PyPI](https://img.shields.io/pypi/v/service-mesh-cli)](https://pypi.org/project/service-mesh-cli/)

**Service mesh configuration validator and traffic policy analyzer for Istio/Linkerd.**

Validates mesh configurations against 10 best-practice rules (MESH-001 to MESH-010) covering mTLS, circuit breakers, retry policies, gateway TLS, authorization, traffic weights, rate limiting, sidecar injection, and outlier detection.

## Installation

```bash
pip install service-mesh-cli
```

## Usage

```bash
# Validate mesh config
service-mesh-cli validate mesh-config.yaml

# Validate with fail threshold
service-mesh-cli validate mesh-config.yaml --fail-on critical

# JSON output
service-mesh-cli validate mesh-config.yaml --format json

# Run demo
service-mesh-cli demo

# List rules
service-mesh-cli rules
```




## Command Reference

### `service-mesh-cli validate`

Validate mesh configuration against best practices.

```bash
service-mesh-cli validate <config-file> [OPTIONS]

Options:
  --format [text|json]    Output format (default: text)
  --fail-on [SEVERITY]    Exit with code 1 if findings at this level
  --mesh [istio|linkerd]  Target mesh platform
```

### `service-mesh-cli demo`

Run demo with sample Istio configuration.

```bash
service-mesh-cli demo
```

### `service-mesh-cli rules`

Display all validation rules.

```bash
service-mesh-cli rules
```

## Sample Output

```
service-mesh-cli v1.0.0 - Service Mesh Validator

Validating: mesh-config.yaml (Istio)
Policies found: 12

  MESH-001 [CRITICAL] mTLS Not Enforced
    â†’ Namespace default has permissive mTLS mode
  MESH-003 [HIGH] Missing Circuit Breaker
    â†’ payment-service has no circuit breaker configured
  MESH-005 [MEDIUM] No Rate Limiting
    â†’ api-gateway missing rate limit policy
  MESH-008 [LOW] Verbose Access Logging
    â†’ Mesh-wide access logging may impact performance

Score: 55/100 (Grade: D)
Findings: 1 critical, 2 high, 2 medium, 1 low
```

## Configuration File

```yaml
mesh:
  platform: istio
  namespace: production
  mtls_mode: STRICT
  policies:
    - name: payment-service
      circuit_breaker:
        max_connections: 100
        max_retries: 3
      timeout: 30s
    - name: api-gateway
      rate_limit:
        requests_per_second: 1000
```## Rules

| Rule | Severity | Title |
|------|----------|-------|
| MESH-001 | CRITICAL | mTLS Not Enforced |
| MESH-002 | HIGH | No Circuit Breaker Configured |
| MESH-003 | MEDIUM | No Retry Policy Configured |
| MESH-004 | MEDIUM | No Request Timeout Set |
| MESH-005 | HIGH | Permissive Authorization Policy |
| MESH-006 | HIGH | Traffic Weight Mismatch |
| MESH-007 | CRITICAL | Gateway TLS Not Configured |
| MESH-008 | MEDIUM | No Rate Limiting Configured |
| MESH-009 | HIGH | Sidecar Injection Missing |
| MESH-010 | LOW | Outlier Detection Too Aggressive |

## License

MIT


## 🐳 Docker

Run without installing Python:

```bash
# Build the image
docker build -t service-mesh-cli .

# Run
docker run --rm service-mesh-cli --help

# Example with volume mount
docker run --rm -v ${PWD}:/workspace service-mesh-cli [command] /workspace
```

Or pull from the container registry:

```bash
docker pull ghcr.io/SanjaySundarMurthy/service-mesh-cli:latest
docker run --rm ghcr.io/SanjaySundarMurthy/service-mesh-cli:latest --help
```

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please ensure tests pass before submitting:

```bash
pip install service-mesh-cli
pytest -v
ruff check .
```

## 🔗 Links

- **PyPI**: [https://pypi.org/project/service-mesh-cli/](https://pypi.org/project/service-mesh-cli/)
- **GitHub**: [https://github.com/SanjaySundarMurthy/service-mesh-cli](https://github.com/SanjaySundarMurthy/service-mesh-cli)
- **Issues**: [https://github.com/SanjaySundarMurthy/service-mesh-cli/issues](https://github.com/SanjaySundarMurthy/service-mesh-cli/issues)