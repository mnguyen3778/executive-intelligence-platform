import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from executive_intelligence_platform.executive_intelligence_package import (  # noqa: E402
    EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION,
    EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
    ExecutiveIntelligencePackage,
    ExecutiveIntelligencePackageAssembler,
    ExecutiveIntelligencePackageLineage,
    ExecutiveIntelligencePackageRequest,
)
from executive_intelligence_platform.executive_intelligence_projection import (  # noqa: E402
    EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION,
    EXECUTIVE_INTELLIGENCE_PROJECTION_ISSUE_CODES,
    EXECUTIVE_INTELLIGENCE_PROJECTION_RULE_VERSION,
    ExecutiveIntelligenceProjectionProjector,
    ExecutiveIntelligenceProjectionRequest,
)
from executive_intelligence_platform.snapshot_catalog import (  # noqa: E402
    SnapshotCatalog,
)
from executive_intelligence_platform.snapshot_derivation import (  # noqa: E402
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


def derived_artifact():
    result = SnapshotDerivationRuntime().derive(
        admitted_entry(),
        SnapshotDerivationRequest(),
    )
    return result.artifact


def executive_package():
    result = ExecutiveIntelligencePackageAssembler().assemble(
        ExecutiveIntelligencePackageRequest(),
        derived_artifact(),
    )
    return result.package


def package_result():
    return ExecutiveIntelligencePackageAssembler().assemble(
        ExecutiveIntelligencePackageRequest(),
        derived_artifact(),
    )


def issue_codes(result):
    return tuple(issue.code for issue in result.issues)


class ExecutiveIntelligenceProjectionTests(unittest.TestCase):
    def test_projects_package_metadata_and_lineage(self):
        package = executive_package()
        request = ExecutiveIntelligenceProjectionRequest()

        result = ExecutiveIntelligenceProjectionProjector().project(request, package)

        self.assertTrue(result.projected)
        self.assertEqual(result.issues, ())
        self.assertIsNotNone(result.projection)
        self.assertEqual(
            result.projection.projection_contract_version,
            EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION,
        )
        self.assertEqual(
            result.projection.projection_rule_version,
            EXECUTIVE_INTELLIGENCE_PROJECTION_RULE_VERSION,
        )
        self.assertEqual(
            result.projection.package_contract_version,
            EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
        )
        self.assertEqual(
            result.projection.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )
        self.assertIs(result.projection.source_package, package)

    def test_rejects_raw_snapshot(self):
        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            valid_snapshot(),
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(
            issue_codes(result),
            ("invalid-executive-intelligence-package",),
        )

    def test_rejects_catalog_entry(self):
        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            admitted_entry(),
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(
            issue_codes(result),
            ("invalid-executive-intelligence-package",),
        )

    def test_rejects_derived_artifact(self):
        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            derived_artifact(),
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(
            issue_codes(result),
            ("invalid-executive-intelligence-package",),
        )

    def test_rejects_package_result(self):
        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            package_result(),
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(
            issue_codes(result),
            ("invalid-executive-intelligence-package",),
        )

    def test_rejects_invalid_request(self):
        result = ExecutiveIntelligenceProjectionProjector().project(
            None,
            executive_package(),
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(issue_codes(result), ("invalid-projection-request",))

    def test_rejects_unsupported_projection_contract(self):
        request = ExecutiveIntelligenceProjectionRequest(
            projection_contract_version="executive-intelligence-projection-v2"
        )

        result = ExecutiveIntelligenceProjectionProjector().project(
            request,
            executive_package(),
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(
            issue_codes(result),
            ("unsupported-projection-contract-version",),
        )

    def test_rejects_unsupported_projection_rule(self):
        request = ExecutiveIntelligenceProjectionRequest(
            projection_rule_version="unsupported-projection-rule-v1"
        )

        result = ExecutiveIntelligenceProjectionProjector().project(
            request,
            executive_package(),
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(issue_codes(result), ("unsupported-projection-rule",))

    def test_rejects_unsupported_package_contract(self):
        source = executive_package()
        package = ExecutiveIntelligencePackage(
            package_contract_version="executive-intelligence-package-v2",
            package_assembly_rule_version=source.package_assembly_rule_version,
            producer_snapshot_identity=source.producer_snapshot_identity,
            snapshot_contract_version=source.snapshot_contract_version,
            assessment_version=source.assessment_version,
            methodology_version=source.methodology_version,
            derivation_rule_version=source.derivation_rule_version,
            derivation_runtime_version=source.derivation_runtime_version,
            lineage=source.lineage,
            source_derived_artifact=source.source_derived_artifact,
        )

        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            package,
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertIn("unsupported-package-contract-version", issue_codes(result))

    def test_rejects_unsupported_package_assembly_rule(self):
        source = executive_package()
        package = ExecutiveIntelligencePackage(
            package_contract_version=source.package_contract_version,
            package_assembly_rule_version="unsupported-package-assembly-rule-v1",
            producer_snapshot_identity=source.producer_snapshot_identity,
            snapshot_contract_version=source.snapshot_contract_version,
            assessment_version=source.assessment_version,
            methodology_version=source.methodology_version,
            derivation_rule_version=source.derivation_rule_version,
            derivation_runtime_version=source.derivation_runtime_version,
            lineage=source.lineage,
            source_derived_artifact=source.source_derived_artifact,
        )

        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            package,
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertIn("unsupported-package-assembly-rule", issue_codes(result))

    def test_rejects_incomplete_lineage(self):
        source = executive_package()
        package = ExecutiveIntelligencePackage(
            package_contract_version=source.package_contract_version,
            package_assembly_rule_version=source.package_assembly_rule_version,
            producer_snapshot_identity="",
            snapshot_contract_version=source.snapshot_contract_version,
            assessment_version=source.assessment_version,
            methodology_version=source.methodology_version,
            derivation_rule_version=source.derivation_rule_version,
            derivation_runtime_version=source.derivation_runtime_version,
            lineage=source.lineage,
            source_derived_artifact=source.source_derived_artifact,
        )

        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            package,
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertIn("incomplete-package-lineage", issue_codes(result))

    def test_rejects_inconsistent_lineage(self):
        source = executive_package()
        lineage = ExecutiveIntelligencePackageLineage(
            producer_snapshot_identity="different-snapshot",
            snapshot_contract_version=source.lineage.snapshot_contract_version,
            assessment_version=source.lineage.assessment_version,
            methodology_version=source.lineage.methodology_version,
            derivation_rule_version=source.lineage.derivation_rule_version,
            derivation_runtime_version=source.lineage.derivation_runtime_version,
            catalog_admission_metadata=source.lineage.catalog_admission_metadata,
            producer_provenance=source.lineage.producer_provenance,
        )
        package = ExecutiveIntelligencePackage(
            package_contract_version=source.package_contract_version,
            package_assembly_rule_version=source.package_assembly_rule_version,
            producer_snapshot_identity=source.producer_snapshot_identity,
            snapshot_contract_version=source.snapshot_contract_version,
            assessment_version=source.assessment_version,
            methodology_version=source.methodology_version,
            derivation_rule_version=source.derivation_rule_version,
            derivation_runtime_version=source.derivation_runtime_version,
            lineage=lineage,
            source_derived_artifact=source.source_derived_artifact,
        )

        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            package,
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertIn("inconsistent-package-lineage", issue_codes(result))

    def test_projection_output_is_deterministic(self):
        package = executive_package()
        request = ExecutiveIntelligenceProjectionRequest()
        projector = ExecutiveIntelligenceProjectionProjector()

        first_result = projector.project(request, package)
        second_result = projector.project(request, package)

        self.assertEqual(first_result, second_result)
        self.assertEqual(first_result.to_dict(), second_result.to_dict())

    def test_issue_codes_are_stable_and_documented(self):
        for code, description in EXECUTIVE_INTELLIGENCE_PROJECTION_ISSUE_CODES.items():
            self.assertIsInstance(code, str)
            self.assertRegex(code, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertIsInstance(description, str)
            self.assertTrue(description.strip())

    def test_request_model_is_immutable(self):
        request = ExecutiveIntelligenceProjectionRequest()

        with self.assertRaises(FrozenInstanceError):
            request.projection_contract_version = "changed"

    def test_projection_model_is_immutable(self):
        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            executive_package(),
        )

        with self.assertRaises(FrozenInstanceError):
            result.projection.producer_snapshot_identity = "changed"

    def test_projection_result_model_is_immutable(self):
        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            executive_package(),
        )

        with self.assertRaises(FrozenInstanceError):
            result.projected = False

    def test_projection_lineage_model_is_immutable(self):
        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            executive_package(),
        )

        with self.assertRaises(FrozenInstanceError):
            result.projection.lineage.producer_snapshot_identity = "changed"

    def test_package_is_not_mutated_by_projection(self):
        package = executive_package()
        before = package.to_dict()

        ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            package,
        )

        self.assertEqual(package.to_dict(), before)

    def test_preserves_complete_lineage_to_producer_snapshot(self):
        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            executive_package(),
        )

        projection = result.projection
        self.assertEqual(
            projection.lineage.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )
        self.assertEqual(
            projection.lineage.package_lineage.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )
        self.assertEqual(
            projection.lineage.package_lineage.catalog_admission_metadata.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )
        self.assertEqual(
            projection.lineage.package_lineage.producer_provenance.producer_snapshot_identity,
            "assessment-service-snapshot-001",
        )

    def test_projection_contains_no_reporting_or_presentation_metadata(self):
        projection_data = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            executive_package(),
        ).projection.to_dict()

        self.assertNotIn("dashboard", projection_data)
        self.assertNotIn("report", projection_data)
        self.assertNotIn("display", projection_data)
        self.assertNotIn("visualization", projection_data)
        self.assertNotIn("chart", projection_data)
        self.assertNotIn("table", projection_data)
        self.assertNotIn("narrative", projection_data)


if __name__ == "__main__":
    unittest.main()
