"""Consumer-side compatibility validation for ExecutiveAssessmentSnapshot artifacts."""

from .compatibility import (
    SNAPSHOT_COMPATIBILITY_ISSUE_CODES,
    SnapshotCompatibilityIssue,
    SnapshotCompatibilityResult,
    validate_snapshot_compatibility,
)

__all__ = [
    "SNAPSHOT_COMPATIBILITY_ISSUE_CODES",
    "SnapshotCompatibilityIssue",
    "SnapshotCompatibilityResult",
    "validate_snapshot_compatibility",
]
