"""Governed catalog admission for compatibility-validated snapshots."""

from .catalog import (
    SNAPSHOT_CATALOG_ADMISSION_POLICY_VERSION,
    SNAPSHOT_CATALOG_ISSUE_CODES,
    SnapshotAdmissionMetadata,
    SnapshotAdmissionResult,
    SnapshotCatalog,
    SnapshotCatalogEntry,
    SnapshotCatalogIssue,
)

__all__ = [
    "SNAPSHOT_CATALOG_ADMISSION_POLICY_VERSION",
    "SNAPSHOT_CATALOG_ISSUE_CODES",
    "SnapshotAdmissionMetadata",
    "SnapshotAdmissionResult",
    "SnapshotCatalog",
    "SnapshotCatalogEntry",
    "SnapshotCatalogIssue",
]
