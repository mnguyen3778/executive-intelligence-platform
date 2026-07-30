import copy
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import MappingProxyType


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from executive_intelligence_platform.snapshot_catalog import (  # noqa: E402
    SNAPSHOT_CATALOG_ISSUE_CODES,
    SnapshotCatalog,
)


def valid_snapshot():
    return {
        "responseContractVersion": "executive-runtime-response-v1",
        "responseStatus": {
            "packageValidation": "VALIDATED",
            "runtimeEligibility": "RUNTIME_ELIGIBLE",
            "exposure": "EXPOSURE_ELIGIBLE",
            "productionAuthority": "NOT_PRODUCTION_AUTHORITATIVE",
        },
        "businessDecisionPackage": {
            "decisionEvaluation": {
                "overallScore": 78.0,
                "totalWeight": 10.0,
                "questionCount": 5,
            },
            "businessReadinessSnapshot": {
                "overallReadiness": {
                    "score": 78.0,
                },
                "audit": {
                    "questionCount": 5,
                    "totalWeight": 10.0,
                },
            },
            "confidenceEvaluation": {},
            "recommendationPriorityEvaluation": {},
            "executiveSummaryFoundation": {},
            "audit": {
                "assessmentVersion": "nguyen-ai-executive-assessment-v1",
                "methodologyVersion": "business-decision-methodology-v1",
                "sourceComponentIds": [
                    "decisionEvaluation",
                    "businessReadinessSnapshot",
                    "confidenceEvaluation",
                    "recommendationPriorityEvaluation",
                    "executiveSummaryFoundation",
                ],
                "evaluatedDimensions": ["ai-readiness"],
                "questionCount": 5,
                "totalWeight": 10.0,
            },
            "limitations": [
                "final-confidence-formulas-not-implemented",
                "final-confidence-level-assignment-not-implemented",
                "final-recommendation-assignment-not-implemented",
                "recommendation-generation-not-implemented",
                "service-decisions-not-implemented",
                "executive-reporting-not-implemented",
                "executive-narratives-not-implemented",
                "evidence-ingestion-not-implemented",
                "persistence-not-implemented",
                "api-exposure-of-snapshot-consumers-not-implemented",
            ],
            "versionMetadata": {
                "contractVersion": "business-decision-package-v1",
                "assessmentVersion": "nguyen-ai-executive-assessment-v1",
                "methodologyVersion": "business-decision-methodology-v1",
                "componentVersions": {
                    "decisionEvaluation": "assessment-decision-engine-v2",
                    "businessReadinessSnapshot": "sprint3-snapshot-foundation-v1",
                    "confidenceEvaluation": "sprint3-confidence-foundation-v1",
                    "recommendationPriorityEvaluation": (
                        "sprint3-recommendation-priority-foundation-v1"
                    ),
                    "executiveSummaryFoundation": (
                        "sprint3-executive-summary-foundation-v1"
                    ),
                },
            },
        },
    }


def issue_codes(result):
    return tuple(issue.code for issue in result.issues)


class SnapshotCatalogAdmissionTests(unittest.TestCase):
    def test_admits_compatible_snapshot(self):
        catalog = SnapshotCatalog()

        result = catalog.admit(
            valid_snapshot(),
            producer_snapshot_identity="assessment-service-snapshot-001",
        )

        self.assertTrue(result.accepted)
        self.assertEqual(result.issues, ())
        self.assertIsNotNone(result.entry)
        self.assertEqual(
            result.entry.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )
        self.assertIs(
            catalog.get("assessment-service-snapshot-001"),
            result.entry,
        )

    def test_rejects_incompatible_snapshot_without_cataloging_it(self):
        catalog = SnapshotCatalog()
        snapshot = valid_snapshot()
        snapshot["responseContractVersion"] = "executive-runtime-response-v2"

        result = catalog.admit(
            snapshot,
            producer_snapshot_identity="assessment-service-snapshot-001",
        )

        self.assertFalse(result.accepted)
        self.assertIsNone(result.entry)
        self.assertIn("incompatible-snapshot", issue_codes(result))
        self.assertIn("unsupported-response-contract-version", issue_codes(result))
        self.assertEqual(catalog.list_entries(), ())
        self.assertIsNone(catalog.get("assessment-service-snapshot-001"))

    def test_rejects_missing_producer_snapshot_identity(self):
        catalog = SnapshotCatalog()

        result = catalog.admit(valid_snapshot(), producer_snapshot_identity=" ")

        self.assertFalse(result.accepted)
        self.assertEqual(issue_codes(result), ("invalid-producer-snapshot-identity",))
        self.assertEqual(catalog.list_entries(), ())

    def test_rejects_duplicate_admission(self):
        catalog = SnapshotCatalog()
        first = catalog.admit(
            valid_snapshot(),
            producer_snapshot_identity="assessment-service-snapshot-001",
        )
        second = catalog.admit(
            valid_snapshot(),
            producer_snapshot_identity="assessment-service-snapshot-001",
        )

        self.assertTrue(first.accepted)
        self.assertFalse(second.accepted)
        self.assertEqual(issue_codes(second), ("duplicate-producer-snapshot-identity",))
        self.assertEqual(len(catalog.list_entries()), 1)

    def test_lookup_is_deterministic(self):
        catalog = SnapshotCatalog()
        admitted = catalog.admit(
            valid_snapshot(),
            producer_snapshot_identity="assessment-service-snapshot-001",
        )

        first_lookup = catalog.get("assessment-service-snapshot-001")
        second_lookup = catalog.get("assessment-service-snapshot-001")

        self.assertIs(first_lookup, admitted.entry)
        self.assertIs(second_lookup, admitted.entry)
        self.assertIsNone(catalog.get("missing-snapshot"))

    def test_listing_is_deterministic(self):
        catalog = SnapshotCatalog()
        catalog.admit(valid_snapshot(), producer_snapshot_identity="snapshot-b")
        catalog.admit(valid_snapshot(), producer_snapshot_identity="snapshot-a")

        first_listing = catalog.list_entries()
        second_listing = catalog.list_entries()

        self.assertEqual(first_listing, second_listing)
        self.assertEqual(
            tuple(entry.producer_snapshot_identity for entry in first_listing),
            ("snapshot-a", "snapshot-b"),
        )

    def test_catalog_entry_metadata_is_immutable(self):
        catalog = SnapshotCatalog()
        result = catalog.admit(
            valid_snapshot(),
            producer_snapshot_identity="assessment-service-snapshot-001",
        )

        with self.assertRaises(FrozenInstanceError):
            result.entry.admission_metadata.producer_snapshot_identity = "changed"

        with self.assertRaises(FrozenInstanceError):
            result.entry.admission_metadata = result.entry.admission_metadata

    def test_preserved_snapshot_evidence_is_immutable(self):
        catalog = SnapshotCatalog()
        result = catalog.admit(
            valid_snapshot(),
            producer_snapshot_identity="assessment-service-snapshot-001",
        )

        self.assertIsInstance(result.entry.snapshot_evidence, MappingProxyType)
        with self.assertRaises(TypeError):
            result.entry.snapshot_evidence["responseContractVersion"] = "changed"

        response_status = result.entry.snapshot_evidence["responseStatus"]
        self.assertIsInstance(response_status, MappingProxyType)
        with self.assertRaises(TypeError):
            response_status["packageValidation"] = "PENDING"

    def test_input_is_not_mutated_by_admission(self):
        catalog = SnapshotCatalog()
        snapshot = valid_snapshot()
        before = copy.deepcopy(snapshot)

        catalog.admit(
            snapshot,
            producer_snapshot_identity="assessment-service-snapshot-001",
        )

        self.assertEqual(snapshot, before)

    def test_post_admission_input_mutation_does_not_change_catalog_evidence(self):
        catalog = SnapshotCatalog()
        snapshot = valid_snapshot()
        result = catalog.admit(
            snapshot,
            producer_snapshot_identity="assessment-service-snapshot-001",
        )

        snapshot["responseContractVersion"] = "mutated-after-admission"

        self.assertEqual(
            result.entry.snapshot_evidence["responseContractVersion"],
            "executive-runtime-response-v1",
        )

    def test_catalog_issue_codes_are_stable_and_documented(self):
        for code, description in SNAPSHOT_CATALOG_ISSUE_CODES.items():
            self.assertIsInstance(code, str)
            self.assertRegex(code, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertIsInstance(description, str)
            self.assertTrue(description.strip())

    def test_admission_results_are_deterministic(self):
        snapshot = valid_snapshot()
        first_catalog = SnapshotCatalog()
        second_catalog = SnapshotCatalog()

        first_result = first_catalog.admit(
            snapshot,
            producer_snapshot_identity="assessment-service-snapshot-001",
        )
        second_result = second_catalog.admit(
            snapshot,
            producer_snapshot_identity="assessment-service-snapshot-001",
        )

        self.assertEqual(first_result, second_result)
        self.assertEqual(first_result.to_dict(), second_result.to_dict())


if __name__ == "__main__":
    unittest.main()
