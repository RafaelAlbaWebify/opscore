from pathlib import Path

from opscore.adapters.cloud_exports import (
    import_aws_ec2_export,
    import_azure_vm_export,
)


SAMPLES = Path("samples/imports")


def test_import_azure_vm_export() -> None:
    evidence = import_azure_vm_export(
        SAMPLES / "azure-vm-export-sample.json", target_reference="orders-web"
    )
    assert len(evidence) == 2
    assert evidence[0].source_system == "azure-export"
    assert evidence[0].normalized_data["provider"] == "azure"
    assert evidence[0].collected_at.tzinfo is not None


def test_import_aws_ec2_export() -> None:
    evidence = import_aws_ec2_export(
        SAMPLES / "aws-ec2-export-sample.json", target_reference="orders-web"
    )
    assert len(evidence) == 2
    assert evidence[0].source_system == "aws-export"
    assert evidence[0].normalized_data["provider"] == "aws"
    assert evidence[0].collected_at.tzinfo is not None
