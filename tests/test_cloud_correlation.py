from pathlib import Path

from opscore.imports import run_cloud_import_correlation


def test_azure_cloud_import_produces_findings(tmp_path: Path) -> None:
    _, json_path = run_cloud_import_correlation(
        Path("samples/incidents/orders-service-unavailable.json"),
        provider="azure",
        export_path=Path("samples/imports/azure-vm-export-sample.json"),
        target_reference="orders-web",
        workspace=tmp_path,
    )
    text = json_path.read_text(encoding="utf-8")
    assert "AZURE_NETWORK_REVIEW_REQUIRED" in text
    assert "AZURE_HIGH_CPU" in text
    assert "AZURE_LOW_DISK" in text


def test_aws_cloud_import_produces_findings(tmp_path: Path) -> None:
    _, json_path = run_cloud_import_correlation(
        Path("samples/incidents/orders-service-unavailable.json"),
        provider="aws",
        export_path=Path("samples/imports/aws-ec2-export-sample.json"),
        target_reference="orders-web",
        workspace=tmp_path,
    )
    text = json_path.read_text(encoding="utf-8")
    assert "AWS_STATUS_CHECK_REVIEW_REQUIRED" in text
    assert "AWS_NETWORK_REVIEW_REQUIRED" in text
    assert "AWS_LOW_DISK" in text
