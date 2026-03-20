# 🕸️ service-mesh-cli

**Service mesh configuration validator and traffic policy analyzer for Istio/Linkerd.**

Validates mesh configurations against 10 best-practice rules (MESH-001 to MESH-010) covering mTLS, circuit breakers, retry policies, gateway TLS, authorization, traffic weights, rate limiting, sidecar injection, and outlier detection.

## Installation

```bash
pip install -e .
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

## Rules

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
