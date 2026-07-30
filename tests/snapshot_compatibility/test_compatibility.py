import copy
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from executive_intelligence_platform.snapshot_compatibility import (  # noqa: E402
    SNAPSHOT_COMPATIBILITY_ISSUE_CODES,
    validate_snapshot_compatibility,
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


class SnapshotCompatibilityTests(unittest.TestCase):
    def test_accepts_compatible_serialized_snapshot(self):
        result = validate_snapshot_compatibility(valid_snapshot())

        self.assertTrue(result.is_valid)
        self.assertEqual(result.issues, ())
        self.assertEqual(result.to_dict(), {"isValid": True, "issues": []})

    def test_rejects_non_mapping_snapshot(self):
        result = validate_snapshot_compatibility([])

        self.assertFalse(result.is_valid)
        self.assertEqual(
            issue_codes(result),
            ("invalid-snapshot-serialization-type",),
        )

    def test_rejects_missing_root_field_without_partial_acceptance(self):
        snapshot = valid_snapshot()
        snapshot.pop("responseStatus")

        result = validate_snapshot_compatibility(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("snapshot-field-order-mismatch", issue_codes(result))
        self.assertIn("missing-snapshot-field", issue_codes(result))
        self.assertIn("invalid-response-status", issue_codes(result))

    def test_rejects_unexpected_root_field(self):
        snapshot = valid_snapshot()
        snapshot["generatedAt"] = "2026-07-29T00:00:00Z"

        result = validate_snapshot_compatibility(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("snapshot-field-order-mismatch", issue_codes(result))
        self.assertIn("unexpected-snapshot-field", issue_codes(result))

    def test_rejects_unsupported_response_contract_version(self):
        snapshot = valid_snapshot()
        snapshot["responseContractVersion"] = "executive-runtime-response-v2"

        result = validate_snapshot_compatibility(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported-response-contract-version", issue_codes(result))

    def test_rejects_unsupported_response_status_value(self):
        snapshot = valid_snapshot()
        snapshot["responseStatus"]["packageValidation"] = "PENDING"

        result = validate_snapshot_compatibility(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported-response-status", issue_codes(result))

    def test_accepts_both_production_authority_values(self):
        authoritative = valid_snapshot()
        authoritative["responseStatus"]["productionAuthority"] = (
            "PRODUCTION_AUTHORITATIVE"
        )

        self.assertTrue(validate_snapshot_compatibility(valid_snapshot()).is_valid)
        self.assertTrue(validate_snapshot_compatibility(authoritative).is_valid)

    def test_rejects_invalid_business_decision_package(self):
        snapshot = valid_snapshot()
        snapshot["businessDecisionPackage"] = "not-a-package"

        result = validate_snapshot_compatibility(snapshot)

        self.assertFalse(result.is_valid)
        self.assertEqual(
            issue_codes(result),
            ("invalid-business-decision-package",),
        )

    def test_rejects_unsupported_package_contract_version(self):
        snapshot = valid_snapshot()
        snapshot["businessDecisionPackage"]["versionMetadata"]["contractVersion"] = (
            "business-decision-package-v2"
        )

        result = validate_snapshot_compatibility(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported-package-contract-version", issue_codes(result))

    def test_rejects_unsupported_assessment_and_methodology_versions(self):
        snapshot = valid_snapshot()
        metadata = snapshot["businessDecisionPackage"]["versionMetadata"]
        metadata["assessmentVersion"] = "nguyen-ai-readiness-v1"
        metadata["methodologyVersion"] = "other-methodology"

        result = validate_snapshot_compatibility(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported-assessment-version", issue_codes(result))
        self.assertIn("unsupported-methodology-version", issue_codes(result))

    def test_rejects_unsupported_component_versions(self):
        snapshot = valid_snapshot()
        component_versions = snapshot["businessDecisionPackage"]["versionMetadata"][
            "componentVersions"
        ]
        component_versions["decisionEvaluation"] = "unexpected-version"

        result = validate_snapshot_compatibility(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported-component-versions", issue_codes(result))

    def test_rejects_invalid_producer_source_components(self):
        snapshot = valid_snapshot()
        snapshot["businessDecisionPackage"]["audit"]["sourceComponentIds"] = [
            "decisionEvaluation"
        ]

        result = validate_snapshot_compatibility(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported-source-components", issue_codes(result))

    def test_rejects_audit_version_mismatch(self):
        snapshot = valid_snapshot()
        snapshot["businessDecisionPackage"]["audit"]["assessmentVersion"] = (
            "other-assessment"
        )

        result = validate_snapshot_compatibility(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("audit-assessment-version-mismatch", issue_codes(result))

    def test_rejects_missing_or_changed_limitations(self):
        snapshot = valid_snapshot()
        snapshot["businessDecisionPackage"]["limitations"] = []

        result = validate_snapshot_compatibility(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported-package-limitations", issue_codes(result))

    def test_rejects_invariant_mismatch_without_recomputing(self):
        snapshot = valid_snapshot()
        snapshot["businessDecisionPackage"]["businessReadinessSnapshot"][
            "overallReadiness"
        ]["score"] = 40.0

        result = validate_snapshot_compatibility(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("decision-snapshot-score-mismatch", issue_codes(result))

    def test_validation_does_not_mutate_snapshot(self):
        snapshot = valid_snapshot()
        before = copy.deepcopy(snapshot)

        validate_snapshot_compatibility(snapshot)

        self.assertEqual(snapshot, before)

    def test_failure_reasons_are_deterministic(self):
        snapshot = valid_snapshot()
        snapshot.pop("responseContractVersion")
        snapshot["businessDecisionPackage"]["limitations"] = []

        first = validate_snapshot_compatibility(snapshot)
        second = validate_snapshot_compatibility(snapshot)

        self.assertEqual(first, second)
        self.assertEqual(issue_codes(first), issue_codes(second))

    def test_emitted_issue_codes_are_documented_for_automation(self):
        invalid_cases = [
            [],
            {**valid_snapshot(), "responseContractVersion": "unsupported"},
            {**valid_snapshot(), "businessDecisionPackage": "not-a-package"},
        ]

        emitted_codes = set()
        for snapshot in invalid_cases:
            emitted_codes.update(issue_codes(validate_snapshot_compatibility(snapshot)))

        self.assertTrue(emitted_codes)
        self.assertLessEqual(emitted_codes, set(SNAPSHOT_COMPATIBILITY_ISSUE_CODES))

    def test_documented_issue_codes_are_stable_machine_codes(self):
        for code, description in SNAPSHOT_COMPATIBILITY_ISSUE_CODES.items():
            self.assertIsInstance(code, str)
            self.assertRegex(code, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertIsInstance(description, str)
            self.assertTrue(description.strip())

    def test_issue_codes_do_not_depend_on_message_text(self):
        result = validate_snapshot_compatibility([])
        issue = result.issues[0]

        self.assertEqual(issue.code, "invalid-snapshot-serialization-type")
        self.assertNotEqual(issue.code, issue.message)
        self.assertEqual(
            issue.to_dict()["code"],
            "invalid-snapshot-serialization-type",
        )


if __name__ == "__main__":
    unittest.main()
