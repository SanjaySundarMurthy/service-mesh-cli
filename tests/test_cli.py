"""Tests for CLI commands."""
import json
from click.testing import CliRunner
from service_mesh_cli.cli import cli


class TestCLI:
    def test_demo_terminal(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["demo"])
        assert result.exit_code == 0
        assert "Service Mesh" in result.output or "MESH-" in result.output

    def test_demo_json(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["demo", "--format", "json"])
        assert result.exit_code == 0
        assert "health_score" in result.output
        assert "findings" in result.output
        assert "istio" in result.output

    def test_demo_html(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["demo", "--format", "html"])
        assert result.exit_code == 0
        assert "<html>" in result.output

    def test_rules_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["rules"])
        assert result.exit_code == 0
        assert "mTLS Not Enforced" in result.output
        assert "Outlier Detection" in result.output

    def test_validate_file(self, tmp_path):
        config = tmp_path / "mesh.yaml"
        config.write_text("""apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: test-vs
  namespace: default
spec:
  hosts:
  - test
  http:
  - route:
    - destination:
        host: test
        port:
          number: 8080
      weight: 100
""")
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", str(config)])
        assert result.exit_code == 0

    def test_validate_json_output(self, tmp_path):
        config = tmp_path / "mesh.yaml"
        config.write_text("""apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: test-pa
  namespace: default
spec:
  mtls:
    mode: STRICT
""")
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", str(config), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["provider"] == "istio"

    def test_validate_fail_on(self, tmp_path):
        config = tmp_path / "mesh.yaml"
        config.write_text("""apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: insecure-gw
  namespace: default
spec:
  servers:
  - port:
      number: 80
      protocol: HTTP
    hosts:
    - "*.example.com"
""")
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", str(config), "--fail-on", "critical"])
        assert result.exit_code == 1

    def test_validate_output_file(self, tmp_path):
        config = tmp_path / "mesh.yaml"
        config.write_text("""apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: strict-pa
spec:
  mtls:
    mode: STRICT
""")
        out_file = tmp_path / "report.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", str(config), "--format", "json", "-o", str(out_file)])
        assert result.exit_code == 0
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert "health_score" in data

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "service-mesh-cli" in result.output
