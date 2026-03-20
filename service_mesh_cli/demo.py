"""Demo data generator for service-mesh-cli."""
import yaml


def get_demo_mesh_config() -> str:
    """Generate sample Istio mesh configurations with intentional issues."""
    docs = [
        {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "Gateway",
            "metadata": {"name": "frontend-gw", "namespace": "production"},
            "spec": {
                "servers": [{
                    "port": {"number": 80, "name": "http", "protocol": "HTTP"},
                    "hosts": ["app.example.com"],
                }],
            },
        },
        {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "VirtualService",
            "metadata": {"name": "frontend-vs", "namespace": "production"},
            "spec": {
                "hosts": ["frontend"],
                "gateways": ["frontend-gw"],
                "http": [{
                    "route": [
                        {"destination": {"host": "frontend-v1", "port": {"number": 8080}}, "weight": 80},
                        {"destination": {"host": "frontend-v2", "port": {"number": 8080}}, "weight": 30},
                    ],
                }],
            },
        },
        {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "VirtualService",
            "metadata": {"name": "api-vs", "namespace": "production"},
            "spec": {
                "hosts": ["api-service"],
                "http": [{
                    "timeout": "10s",
                    "retries": {"attempts": 3, "perTryTimeout": "2s", "retryOn": "5xx,reset"},
                    "route": [{"destination": {"host": "api-service", "port": {"number": 8080}}}],
                }],
            },
        },
        {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "DestinationRule",
            "metadata": {"name": "api-dr", "namespace": "production"},
            "spec": {
                "host": "api-service",
                "trafficPolicy": {
                    "tls": {"mode": "DISABLE"},
                    "loadBalancer": {"simple": "ROUND_ROBIN"},
                },
            },
        },
        {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "DestinationRule",
            "metadata": {"name": "payment-dr", "namespace": "production"},
            "spec": {
                "host": "payment-service",
                "trafficPolicy": {
                    "tls": {"mode": "ISTIO_MUTUAL"},
                    "connectionPool": {"tcp": {"maxConnections": 100}},
                    "outlierDetection": {
                        "consecutiveErrors": 5,
                        "interval": "10s",
                        "baseEjectionTime": "30s",
                        "maxEjectionPercent": 90,
                    },
                },
            },
        },
        {
            "apiVersion": "security.istio.io/v1beta1",
            "kind": "PeerAuthentication",
            "metadata": {"name": "default-pa", "namespace": "production"},
            "spec": {"mtls": {"mode": "PERMISSIVE"}},
        },
        {
            "apiVersion": "security.istio.io/v1beta1",
            "kind": "AuthorizationPolicy",
            "metadata": {"name": "allow-all", "namespace": "production"},
            "spec": {},
        },
    ]
    return "\n---\n".join(yaml.dump(doc, default_flow_style=False) for doc in docs)
