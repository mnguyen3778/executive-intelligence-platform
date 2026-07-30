import copy
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from executive_intelligence_platform.snapshot_catalog import (  # noqa: E402
    SnapshotAdmissionMetadata,
    SnapshotCatalog,
    SnapshotCatalogEntry,
)
from executive_intelligence_platform.snapshot_derivation import (  # noqa: E402
    SNAPSHOT_DERIVATION_ISSUE_CODES,
    SNAPSHOT_DERIVATION_RULE_VERSION,
    SNAPSHOT_DERIVATION_RUNTIME_VERSION,
    SnapshotDerivationRequest,
    SnapshotDerivationRuntime,
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


def admitted_entry():
    catalog = SnapshotCatalog()
    result = catalog.admit(
        valid_snapshot(),
        producer_snapshot_identity="assessment-service-snapshot-001",
    )
    return result.entry


def issue_codes(result):
    return tuple(issue.code for issue in result.issues)


class SnapshotDerivationRuntimeTests(unittest.TestCase):
    def test_derives_metadata_artifact_from_admitted_catalog_entry(self):
        runtime = SnapshotDerivationRuntime()
        request = SnapshotDerivationRequest()

        result = runtime.derive(admitted_entry(), request)

        self.assertTrue(result.derived)
        self.assertEqual(result.issues, ())
        self.assertIsNotNone(result.artifact)
        self.assertEqual(
            result.artifact.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )
        self.assertEqual(
            result.artifact.snapshot_contract_version,
            "executive-runtime-response-v1",
        )
        self.assertEqual(
            result.artifact.derivation_rule_version,
            SNAPSHOT_DERIVATION_RULE_VERSION,
        )
        self.assertEqual(
            result.artifact.derivation_runtime_version,
            SNAPSHOT_DERIVATION_RUNTIME_VERSION,
        )

    def test_rejects_raw_snapshot(self):
        runtime = SnapshotDerivationRuntime()

        result = runtime.derive(valid_snapshot(), SnapshotDerivationRequest())

        self.assertFalse(result.derived)
        self.assertIsNone(result.artifact)
        self.assertEqual(issue_codes(result), ("invalid-catalog-entry",))

    def test_rejects_invalid_derivation_request(self):
        runtime = SnapshotDerivationRuntime()

        result = runtime.derive(admitted_entry(), request=None)

        self.assertFalse(result.derived)
        self.assertIsNone(result.artifact)
        self.assertEqual(issue_codes(result), ("invalid-derivation-request",))

    def test_rejects_unsupported_derivation_rule(self):
        runtime = SnapshotDerivationRuntime()
        request = SnapshotDerivationRequest(
            derivation_rule_version="unsupported-derivation-rule-v1"
        )

        result = runtime.derive(admitted_entry(), request)

        self.assertFalse(result.derived)
        self.assertIsNone(result.artifact)
        self.assertEqual(issue_codes(result), ("unsupported-derivation-rule",))

    def test_fails_closed_when_catalog_lineage_is_incomplete(self):
        runtime = SnapshotDerivationRuntime()
        entry = SnapshotCatalogEntry(
            admission_metadata=SnapshotAdmissionMetadata(
                producer_snapshot_identity="",
                admission_policy_version="snapshot-catalog-admission-v1",
                response_contract_version="executive-runtime-response-v1",
                package_contract_version="business-decision-package-v1",
                assessment_version="nguyen-ai-executive-assessment-v1",
                methodology_version="business-decision-methodology-v1",
                source_component_ids=(),
                production_authority="NOT_PRODUCTION_AUTHORITATIVE",
                admission_sequence=1,
            ),
            snapshot_evidence={},
        )

        result = runtime.derive(entry, SnapshotDerivationRequest())

        self.assertFalse(result.derived)
        self.assertIsNone(result.artifact)
        self.assertIn("incomplete-catalog-lineage", issue_codes(result))

    def test_fails_closed_when_snapshot_evidence_is_missing(self):
        runtime = SnapshotDerivationRuntime()
        entry = SnapshotCatalogEntry(
            admission_metadata=SnapshotAdmissionMetadata(
                producer_snapshot_identity="assessment-service-snapshot-001",
                admission_policy_version="snapshot-catalog-admission-v1",
                response_contract_version="executive-runtime-response-v1",
                package_contract_version="business-decision-package-v1",
                assessment_version="nguyen-ai-executive-assessment-v1",
                methodology_version="business-decision-methodology-v1",
                source_component_ids=("decisionEvaluation",),
                production_authority="NOT_PRODUCTION_AUTHORITATIVE",
                admission_sequence=1,
            ),
            snapshot_evidence=None,
        )

        result = runtime.derive(entry, SnapshotDerivationRequest())

        self.assertFalse(result.derived)
        self.assertIsNone(result.artifact)
        self.assertEqual(issue_codes(result), ("missing-snapshot-evidence",))

    def test_derivation_results_are_deterministic(self):
        entry = admitted_entry()
        request = SnapshotDerivationRequest()
        runtime = SnapshotDerivationRuntime()

        first_result = runtime.derive(entry, request)
        second_result = runtime.derive(entry, request)

        self.assertEqual(first_result, second_result)
        self.assertEqual(first_result.to_dict(), second_result.to_dict())

    def test_issue_codes_are_stable_and_documented(self):
        for code, description in SNAPSHOT_DERIVATION_ISSUE_CODES.items():
            self.assertIsInstance(code, str)
            self.assertRegex(code, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertIsInstance(description, str)
            self.assertTrue(description.strip())

    def test_request_model_is_immutable(self):
        request = SnapshotDerivationRequest()

        with self.assertRaises(FrozenInstanceError):
            request.derivation_rule_version = "changed"

    def test_derived_artifact_is_immutable(self):
        result = SnapshotDerivationRuntime().derive(
            admitted_entry(),
            SnapshotDerivationRequest(),
        )

        with self.assertRaises(FrozenInstanceError):
            result.artifact.producer_snapshot_identity = "changed"

        with self.assertRaises(FrozenInstanceError):
            result.artifact.producer_provenance.production_authority = "changed"

    def test_result_model_is_immutable(self):
        result = SnapshotDerivationRuntime().derive(
            admitted_entry(),
            SnapshotDerivationRequest(),
        )

        with self.assertRaises(FrozenInstanceError):
            result.derived = False

    def test_catalog_entry_is_not_mutated_by_derivation(self):
        entry = admitted_entry()
        before = entry.to_dict()

        SnapshotDerivationRuntime().derive(entry, SnapshotDerivationRequest())

        self.assertEqual(entry.to_dict(), before)

    def test_snapshot_evidence_is_not_mutated_by_derivation(self):
        snapshot = valid_snapshot()
        before = copy.deepcopy(snapshot)
        catalog = SnapshotCatalog()
        admission = catalog.admit(
            snapshot,
            producer_snapshot_identity="assessment-service-snapshot-001",
        )

        SnapshotDerivationRuntime().derive(
            admission.entry,
            SnapshotDerivationRequest(),
        )

        self.assertEqual(snapshot, before)
        self.assertEqual(
            admission.entry.snapshot_evidence["responseContractVersion"],
            "executive-runtime-response-v1",
        )

    def test_preserves_lineage_to_producer_snapshot_identity(self):
        result = SnapshotDerivationRuntime().derive(
            admitted_entry(),
            SnapshotDerivationRequest(),
        )

        artifact = result.artifact
        self.assertEqual(
            artifact.catalog_admission_metadata.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )
        self.assertEqual(
            artifact.producer_provenance.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )
        self.assertEqual(
            artifact.compatibility_validation_metadata.snapshot_contract_version,
            "executive-runtime-response-v1",
        )


if __name__ == "__main__":
    unittest.main()
