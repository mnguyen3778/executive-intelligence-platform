import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from executive_intelligence_platform.executive_intelligence_package import (  # noqa: E402
    EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION,
    EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
    EXECUTIVE_INTELLIGENCE_PACKAGE_ISSUE_CODES,
    ExecutiveIntelligencePackageAssembler,
    ExecutiveIntelligencePackageRequest,
)
from executive_intelligence_platform.snapshot_catalog import (  # noqa: E402
    SnapshotAdmissionMetadata,
    SnapshotCatalog,
)
from executive_intelligence_platform.snapshot_derivation import (  # noqa: E402
    SNAPSHOT_DERIVATION_RULE_VERSION,
    SNAPSHOT_DERIVATION_RUNTIME_VERSION,
    SnapshotCompatibilityValidationMetadata,
    SnapshotDerivationRequest,
    SnapshotDerivationRuntime,
    SnapshotDerivedArtifact,
    SnapshotProducerProvenance,
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


def derived_artifact():
    result = SnapshotDerivationRuntime().derive(
        admitted_entry(),
        SnapshotDerivationRequest(),
    )
    return result.artifact


def derivation_result():
    return SnapshotDerivationRuntime().derive(
        admitted_entry(),
        SnapshotDerivationRequest(),
    )


def issue_codes(result):
    return tuple(issue.code for issue in result.issues)


class ExecutiveIntelligencePackageTests(unittest.TestCase):
    def test_assembles_package_from_single_derived_artifact(self):
        request = ExecutiveIntelligencePackageRequest()
        artifact = derived_artifact()

        result = ExecutiveIntelligencePackageAssembler().assemble(request, artifact)

        self.assertTrue(result.packaged)
        self.assertEqual(result.issues, ())
        self.assertIsNotNone(result.package)
        self.assertEqual(
            result.package.package_contract_version,
            EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
        )
        self.assertEqual(
            result.package.package_assembly_rule_version,
            EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION,
        )
        self.assertEqual(
            result.package.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )
        self.assertIs(result.package.source_derived_artifact, artifact)

    def test_rejects_raw_snapshot(self):
        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            valid_snapshot(),
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertEqual(issue_codes(result), ("invalid-derived-artifact",))

    def test_rejects_catalog_entry(self):
        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            admitted_entry(),
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertEqual(issue_codes(result), ("invalid-derived-artifact",))

    def test_rejects_derivation_result(self):
        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            derivation_result(),
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertEqual(issue_codes(result), ("invalid-derived-artifact",))

    def test_rejects_zero_derived_artifacts(self):
        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest()
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertEqual(issue_codes(result), ("missing-derived-artifact",))

    def test_rejects_multiple_derived_artifacts(self):
        artifact = derived_artifact()

        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            artifact,
            artifact,
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertEqual(issue_codes(result), ("multiple-derived-artifacts",))

    def test_rejects_invalid_request(self):
        result = ExecutiveIntelligencePackageAssembler().assemble(
            None,
            derived_artifact(),
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertEqual(issue_codes(result), ("invalid-package-request",))

    def test_rejects_unsupported_package_contract(self):
        request = ExecutiveIntelligencePackageRequest(
            package_contract_version="executive-intelligence-package-v2"
        )

        result = ExecutiveIntelligencePackageAssembler().assemble(
            request,
            derived_artifact(),
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertEqual(
            issue_codes(result),
            ("unsupported-package-contract-version",),
        )

    def test_rejects_unsupported_assembly_rule(self):
        request = ExecutiveIntelligencePackageRequest(
            package_assembly_rule_version="unsupported-assembly-rule-v1"
        )

        result = ExecutiveIntelligencePackageAssembler().assemble(
            request,
            derived_artifact(),
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertEqual(issue_codes(result), ("unsupported-package-assembly-rule",))

    def test_rejects_incomplete_derived_artifact_lineage(self):
        artifact = SnapshotDerivedArtifact(
            producer_snapshot_identity="",
            snapshot_contract_version="executive-runtime-response-v1",
            assessment_version="nguyen-ai-executive-assessment-v1",
            methodology_version="business-decision-methodology-v1",
            catalog_admission_metadata=admitted_entry().admission_metadata,
            compatibility_validation_metadata=(
                SnapshotCompatibilityValidationMetadata(
                    snapshot_contract_version="executive-runtime-response-v1",
                    assessment_version="nguyen-ai-executive-assessment-v1",
                    methodology_version="business-decision-methodology-v1",
                )
            ),
            producer_provenance=SnapshotProducerProvenance(
                producer_snapshot_identity="assessment-service-snapshot-001",
                source_component_ids=("decisionEvaluation",),
                production_authority="NOT_PRODUCTION_AUTHORITATIVE",
            ),
            derivation_rule_version=SNAPSHOT_DERIVATION_RULE_VERSION,
            derivation_runtime_version=SNAPSHOT_DERIVATION_RUNTIME_VERSION,
        )

        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            artifact,
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertIn("incomplete-derived-artifact-lineage", issue_codes(result))

    def test_rejects_inconsistent_derived_artifact_lineage(self):
        source = derived_artifact()
        artifact = SnapshotDerivedArtifact(
            producer_snapshot_identity=source.producer_snapshot_identity,
            snapshot_contract_version="different-snapshot-contract",
            assessment_version=source.assessment_version,
            methodology_version=source.methodology_version,
            catalog_admission_metadata=source.catalog_admission_metadata,
            compatibility_validation_metadata=source.compatibility_validation_metadata,
            producer_provenance=source.producer_provenance,
            derivation_rule_version=source.derivation_rule_version,
            derivation_runtime_version=source.derivation_runtime_version,
        )

        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            artifact,
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertIn("inconsistent-derived-artifact-lineage", issue_codes(result))

    def test_package_output_is_deterministic(self):
        artifact = derived_artifact()
        request = ExecutiveIntelligencePackageRequest()
        assembler = ExecutiveIntelligencePackageAssembler()

        first_result = assembler.assemble(request, artifact)
        second_result = assembler.assemble(request, artifact)

        self.assertEqual(first_result, second_result)
        self.assertEqual(first_result.to_dict(), second_result.to_dict())

    def test_issue_codes_are_stable_and_documented(self):
        for code, description in EXECUTIVE_INTELLIGENCE_PACKAGE_ISSUE_CODES.items():
            self.assertIsInstance(code, str)
            self.assertRegex(code, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertIsInstance(description, str)
            self.assertTrue(description.strip())

    def test_request_model_is_immutable(self):
        request = ExecutiveIntelligencePackageRequest()

        with self.assertRaises(FrozenInstanceError):
            request.package_contract_version = "changed"

    def test_package_model_is_immutable(self):
        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            derived_artifact(),
        )

        with self.assertRaises(FrozenInstanceError):
            result.package.producer_snapshot_identity = "changed"

    def test_package_result_model_is_immutable(self):
        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            derived_artifact(),
        )

        with self.assertRaises(FrozenInstanceError):
            result.packaged = False

    def test_lineage_model_is_immutable(self):
        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            derived_artifact(),
        )

        with self.assertRaises(FrozenInstanceError):
            result.package.lineage.producer_snapshot_identity = "changed"

    def test_derived_artifact_is_not_mutated_by_package_assembly(self):
        artifact = derived_artifact()
        before = artifact.to_dict()

        ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            artifact,
        )

        self.assertEqual(artifact.to_dict(), before)

    def test_preserves_lineage_to_producer_snapshot_identity(self):
        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            derived_artifact(),
        )

        package = result.package
        self.assertEqual(
            package.lineage.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )
        self.assertEqual(
            package.lineage.catalog_admission_metadata.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )
        self.assertEqual(
            package.lineage.producer_provenance.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )
        self.assertEqual(
            package.lineage.derivation_rule_version,
            SNAPSHOT_DERIVATION_RULE_VERSION,
        )

    def test_package_contains_no_projection_or_reporting_metadata(self):
        package_data = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            derived_artifact(),
        ).package.to_dict()

        self.assertNotIn("projection", package_data)
        self.assertNotIn("report", package_data)
        self.assertNotIn("dashboard", package_data)
        self.assertNotIn("packageIdentity", package_data)


if __name__ == "__main__":
    unittest.main()
