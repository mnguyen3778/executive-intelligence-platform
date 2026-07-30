import copy
import sys
import unittest
from pathlib import Path


EIP_ROOT = Path(__file__).resolve().parents[2]
ASSESSMENT_SERVICE_ROOT = EIP_ROOT.parent / "nguyen-ai-assessment-service"

sys.path.insert(0, str(EIP_ROOT / "src"))
sys.path.insert(0, str(ASSESSMENT_SERVICE_ROOT / "src"))

from assessment.business_decision_package import (  # noqa: E402
    BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION,
)
from assessment.executive_orchestration import (  # noqa: E402
    ValidatedCanonicalExecutiveAssessmentInput,
)
from assessment.executive_runtime import (  # noqa: E402
    EXECUTIVE_ASSESSMENT_VERSION,
    EXECUTIVE_RUNTIME_RESPONSE_CONTRACT_VERSION,
    NOT_PRODUCTION_AUTHORITATIVE,
)
from assessment.executive_snapshot_handoff import (  # noqa: E402
    produce_executive_assessment_snapshot,
)
from assessment.methodology_config import (  # noqa: E402
    BUSINESS_DECISION_METHODOLOGY,
    METHODOLOGY_VERSION,
)
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
    EXECUTIVE_INTELLIGENCE_PROJECTION_RULE_VERSION,
    ExecutiveIntelligenceProjectionProjector,
    ExecutiveIntelligenceProjectionRequest,
)
from executive_intelligence_platform.snapshot_catalog import (  # noqa: E402
    SnapshotCatalog,
)
from executive_intelligence_platform.snapshot_compatibility import (  # noqa: E402
    validate_snapshot_compatibility,
)
from executive_intelligence_platform.snapshot_derivation import (  # noqa: E402
    SNAPSHOT_DERIVATION_RULE_VERSION,
    SNAPSHOT_DERIVATION_RUNTIME_VERSION,
    SnapshotDerivationRequest,
    SnapshotDerivationRuntime,
)


PRODUCER_SNAPSHOT_IDENTITY = (
    "assessment-service:executive-assessment-snapshot:projection-contract-v1"
)


def producer_answers(scale_value=4, numeric_value=100):
    return {
        question_id: (
            numeric_value
            if question.expected_answer_type == "numeric"
            else scale_value
        )
        for question_id, question in BUSINESS_DECISION_METHODOLOGY.questions.items()
    }


def producer_canonical_input(scale_value=4, numeric_value=100):
    return ValidatedCanonicalExecutiveAssessmentInput(
        assessment_version=EXECUTIVE_ASSESSMENT_VERSION,
        methodology_version=METHODOLOGY_VERSION,
        answers=producer_answers(scale_value, numeric_value),
    )


def producer_serialized_snapshot():
    production_result = produce_executive_assessment_snapshot(
        producer_canonical_input(scale_value=3, numeric_value=80)
    )
    if not production_result.is_success:
        raise AssertionError(
            "Assessment Service failed to produce serialized snapshot: "
            f"{production_result.failure}."
        )
    return production_result.serialized_snapshot


def produce_projection_pipeline(serialized_snapshot=None):
    snapshot = (
        producer_serialized_snapshot()
        if serialized_snapshot is None
        else serialized_snapshot
    )
    compatibility_result = validate_snapshot_compatibility(snapshot)
    if not compatibility_result.is_valid:
        raise AssertionError(
            "Executive Intelligence Platform rejected producer snapshot: "
            f"{issue_codes(compatibility_result)}."
        )

    catalog = SnapshotCatalog()
    admission_result = catalog.admit(
        snapshot,
        producer_snapshot_identity=PRODUCER_SNAPSHOT_IDENTITY,
    )
    if not admission_result.accepted:
        raise AssertionError(
            "Executive Intelligence Platform failed to admit producer snapshot: "
            f"{issue_codes(admission_result)}."
        )

    derivation_result = SnapshotDerivationRuntime().derive(
        admission_result.entry,
        SnapshotDerivationRequest(),
    )
    if not derivation_result.derived:
        raise AssertionError(
            "Executive Intelligence Platform failed to derive producer snapshot: "
            f"{issue_codes(derivation_result)}."
        )

    package_result = ExecutiveIntelligencePackageAssembler().assemble(
        ExecutiveIntelligencePackageRequest(),
        derivation_result.artifact,
    )
    if not package_result.packaged:
        raise AssertionError(
            "Executive Intelligence Platform failed to package producer snapshot: "
            f"{issue_codes(package_result)}."
        )

    projection_result = ExecutiveIntelligenceProjectionProjector().project(
        ExecutiveIntelligenceProjectionRequest(),
        package_result.package,
    )

    return (
        snapshot,
        admission_result,
        derivation_result,
        package_result,
        projection_result,
    )


def issue_codes(result):
    return tuple(issue.code for issue in result.issues)


def contains_key(value, key_name):
    if isinstance(value, dict):
        return key_name in value or any(
            contains_key(child, key_name) for child in value.values()
        )
    if isinstance(value, list):
        return any(contains_key(child, key_name) for child in value)
    return False


class CrossRepositoryExecutiveIntelligenceProjectionContractTests(unittest.TestCase):
    def test_assessment_service_snapshot_progresses_to_projection(self):
        (
            _snapshot,
            _admission_result,
            _derivation_result,
            _package_result,
            projection_result,
        ) = produce_projection_pipeline()

        self.assertTrue(projection_result.projected)
        self.assertEqual(projection_result.issues, ())
        self.assertIsNotNone(projection_result.projection)
        self.assertEqual(
            projection_result.projection.projection_contract_version,
            EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION,
        )
        self.assertEqual(
            projection_result.projection.projection_rule_version,
            EXECUTIVE_INTELLIGENCE_PROJECTION_RULE_VERSION,
        )

    def test_projection_preserves_versions_identity_and_lineage(self):
        (
            _snapshot,
            admission_result,
            derivation_result,
            package_result,
            projection_result,
        ) = produce_projection_pipeline()

        projection = projection_result.projection
        lineage = projection.lineage
        package = package_result.package
        package_lineage = package.lineage
        admission_metadata = admission_result.entry.admission_metadata

        self.assertEqual(
            projection.producer_snapshot_identity,
            PRODUCER_SNAPSHOT_IDENTITY,
        )
        self.assertEqual(
            projection.snapshot_contract_version,
            EXECUTIVE_RUNTIME_RESPONSE_CONTRACT_VERSION,
        )
        self.assertEqual(
            projection.package_contract_version,
            EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
        )
        self.assertEqual(
            projection.package_assembly_rule_version,
            EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION,
        )
        self.assertEqual(
            projection.assessment_version,
            EXECUTIVE_ASSESSMENT_VERSION,
        )
        self.assertEqual(projection.methodology_version, METHODOLOGY_VERSION)
        self.assertEqual(
            projection.derivation_rule_version,
            SNAPSHOT_DERIVATION_RULE_VERSION,
        )
        self.assertEqual(
            projection.derivation_runtime_version,
            SNAPSHOT_DERIVATION_RUNTIME_VERSION,
        )
        self.assertIs(projection.source_package, package)
        self.assertEqual(
            package.source_derived_artifact,
            derivation_result.artifact,
        )
        self.assertEqual(
            package_lineage.catalog_admission_metadata.package_contract_version,
            BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION,
        )
        self.assertIs(lineage.package_lineage, package_lineage)
        self.assertEqual(
            lineage.projection_contract_version,
            EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION,
        )
        self.assertEqual(
            lineage.projection_rule_version,
            EXECUTIVE_INTELLIGENCE_PROJECTION_RULE_VERSION,
        )
        self.assertEqual(
            lineage.package_contract_version,
            EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
        )
        self.assertEqual(
            lineage.package_assembly_rule_version,
            EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION,
        )
        self.assertEqual(
            lineage.producer_snapshot_identity,
            PRODUCER_SNAPSHOT_IDENTITY,
        )
        self.assertEqual(
            lineage.snapshot_contract_version,
            EXECUTIVE_RUNTIME_RESPONSE_CONTRACT_VERSION,
        )
        self.assertEqual(lineage.assessment_version, EXECUTIVE_ASSESSMENT_VERSION)
        self.assertEqual(lineage.methodology_version, METHODOLOGY_VERSION)
        self.assertEqual(
            lineage.derivation_rule_version,
            SNAPSHOT_DERIVATION_RULE_VERSION,
        )
        self.assertEqual(
            lineage.derivation_runtime_version,
            SNAPSHOT_DERIVATION_RUNTIME_VERSION,
        )
        self.assertEqual(
            package_lineage.catalog_admission_metadata.producer_snapshot_identity,
            PRODUCER_SNAPSHOT_IDENTITY,
        )
        self.assertEqual(
            package_lineage.catalog_admission_metadata.production_authority,
            NOT_PRODUCTION_AUTHORITATIVE,
        )
        self.assertEqual(
            package_lineage.producer_provenance.producer_snapshot_identity,
            PRODUCER_SNAPSHOT_IDENTITY,
        )
        self.assertEqual(
            package_lineage.producer_provenance.production_authority,
            NOT_PRODUCTION_AUTHORITATIVE,
        )
        self.assertEqual(
            package_lineage.producer_provenance.source_component_ids,
            tuple(admission_metadata.source_component_ids),
        )

    def test_projection_preserves_immutable_evidence_lineage_without_embedding_truth(
        self,
    ):
        (
            snapshot,
            admission_result,
            _derivation_result,
            _package_result,
            projection_result,
        ) = produce_projection_pipeline()

        projection_data = projection_result.projection.to_dict()
        snapshot_evidence = admission_result.entry.to_dict()["snapshotEvidence"]

        self.assertEqual(snapshot_evidence, snapshot)
        self.assertFalse(contains_key(projection_data, "businessDecisionPackage"))
        self.assertFalse(contains_key(projection_data, "decisionEvaluation"))
        self.assertFalse(contains_key(projection_data, "businessReadinessSnapshot"))
        self.assertFalse(contains_key(projection_data, "confidenceEvaluation"))
        self.assertFalse(
            contains_key(projection_data, "recommendationPriorityEvaluation")
        )

    def test_projection_does_not_mutate_pipeline_artifacts(self):
        serialized_snapshot = producer_serialized_snapshot()
        snapshot_before = copy.deepcopy(serialized_snapshot)
        (
            snapshot,
            admission_result,
            derivation_result,
            package_result,
            _projection_result,
        ) = produce_projection_pipeline(serialized_snapshot)
        catalog_entry_before = admission_result.entry.to_dict()
        derived_artifact_before = derivation_result.artifact.to_dict()
        package_before = package_result.package.to_dict()

        ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            package_result.package,
        )

        self.assertEqual(snapshot, snapshot_before)
        self.assertEqual(admission_result.entry.to_dict(), catalog_entry_before)
        self.assertEqual(
            derivation_result.artifact.to_dict(),
            derived_artifact_before,
        )
        self.assertEqual(package_result.package.to_dict(), package_before)
        self.assertEqual(
            admission_result.entry.to_dict()["snapshotEvidence"],
            snapshot_before,
        )

    def test_projection_output_is_deterministic_for_same_package(self):
        (
            _snapshot,
            _admission_result,
            _derivation_result,
            package_result,
            _projection_result,
        ) = produce_projection_pipeline()
        request = ExecutiveIntelligenceProjectionRequest()
        projector = ExecutiveIntelligenceProjectionProjector()

        first_result = projector.project(request, package_result.package)
        second_result = projector.project(request, package_result.package)

        self.assertEqual(first_result, second_result)
        self.assertEqual(first_result.to_dict(), second_result.to_dict())

    def test_projection_contains_no_dashboard_reporting_or_presentation_behavior(self):
        (
            _snapshot,
            _admission_result,
            _derivation_result,
            _package_result,
            projection_result,
        ) = produce_projection_pipeline()
        projection_data = projection_result.projection.to_dict()

        self.assertFalse(contains_key(projection_data, "dashboard"))
        self.assertFalse(contains_key(projection_data, "report"))
        self.assertFalse(contains_key(projection_data, "display"))
        self.assertFalse(contains_key(projection_data, "visualization"))
        self.assertFalse(contains_key(projection_data, "chart"))
        self.assertFalse(contains_key(projection_data, "table"))
        self.assertFalse(contains_key(projection_data, "narrative"))

    def test_incompatible_producer_snapshot_fails_before_projection(self):
        serialized_snapshot = producer_serialized_snapshot()
        serialized_snapshot["responseContractVersion"] = "unsupported-contract"

        compatibility_result = validate_snapshot_compatibility(serialized_snapshot)
        catalog_result = SnapshotCatalog().admit(
            serialized_snapshot,
            producer_snapshot_identity=PRODUCER_SNAPSHOT_IDENTITY,
        )

        self.assertFalse(compatibility_result.is_valid)
        self.assertIn(
            "unsupported-response-contract-version",
            issue_codes(compatibility_result),
        )
        self.assertFalse(catalog_result.accepted)
        self.assertIsNone(catalog_result.entry)
        self.assertIn("incompatible-snapshot", issue_codes(catalog_result))

    def test_projection_rejects_raw_snapshot_fail_closed(self):
        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            producer_serialized_snapshot(),
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(
            issue_codes(result),
            ("invalid-executive-intelligence-package",),
        )

    def test_projection_rejects_unadmitted_catalog_entry_fail_closed(self):
        (
            _snapshot,
            admission_result,
            _derivation_result,
            _package_result,
            _projection_result,
        ) = produce_projection_pipeline()

        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            admission_result.entry,
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(
            issue_codes(result),
            ("invalid-executive-intelligence-package",),
        )

    def test_projection_rejects_underived_artifact_fail_closed(self):
        (
            _snapshot,
            _admission_result,
            derivation_result,
            _package_result,
            _projection_result,
        ) = produce_projection_pipeline()

        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            derivation_result.artifact,
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(
            issue_codes(result),
            ("invalid-executive-intelligence-package",),
        )

    def test_projection_rejects_unprojectable_package_result_fail_closed(self):
        (
            _snapshot,
            _admission_result,
            _derivation_result,
            package_result,
            _projection_result,
        ) = produce_projection_pipeline()

        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            package_result,
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(
            issue_codes(result),
            ("invalid-executive-intelligence-package",),
        )

    def test_projection_rejects_unsupported_projection_contract_fail_closed(self):
        (
            _snapshot,
            _admission_result,
            _derivation_result,
            package_result,
            _projection_result,
        ) = produce_projection_pipeline()

        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(
                projection_contract_version="executive-intelligence-projection-v2"
            ),
            package_result.package,
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(
            issue_codes(result),
            ("unsupported-projection-contract-version",),
        )

    def test_projection_rejects_unsupported_projection_rule_fail_closed(self):
        (
            _snapshot,
            _admission_result,
            _derivation_result,
            package_result,
            _projection_result,
        ) = produce_projection_pipeline()

        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(
                projection_rule_version="unsupported-projection-rule-v1"
            ),
            package_result.package,
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertEqual(issue_codes(result), ("unsupported-projection-rule",))

    def test_projection_rejects_unsupported_package_version_fail_closed(self):
        (
            _snapshot,
            _admission_result,
            _derivation_result,
            package_result,
            _projection_result,
        ) = produce_projection_pipeline()
        source = package_result.package
        unsupported_package = ExecutiveIntelligencePackage(
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
            unsupported_package,
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertIn("unsupported-package-contract-version", issue_codes(result))

    def test_projection_rejects_incomplete_lineage_fail_closed(self):
        (
            _snapshot,
            _admission_result,
            _derivation_result,
            package_result,
            _projection_result,
        ) = produce_projection_pipeline()
        source = package_result.package
        incomplete_package = ExecutiveIntelligencePackage(
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
            incomplete_package,
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertIn("incomplete-package-lineage", issue_codes(result))

    def test_projection_rejects_inconsistent_lineage_fail_closed(self):
        (
            _snapshot,
            _admission_result,
            _derivation_result,
            package_result,
            _projection_result,
        ) = produce_projection_pipeline()
        source = package_result.package
        inconsistent_lineage = ExecutiveIntelligencePackageLineage(
            producer_snapshot_identity="different-snapshot",
            snapshot_contract_version=source.lineage.snapshot_contract_version,
            assessment_version=source.lineage.assessment_version,
            methodology_version=source.lineage.methodology_version,
            derivation_rule_version=source.lineage.derivation_rule_version,
            derivation_runtime_version=source.lineage.derivation_runtime_version,
            catalog_admission_metadata=source.lineage.catalog_admission_metadata,
            producer_provenance=source.lineage.producer_provenance,
        )
        inconsistent_package = ExecutiveIntelligencePackage(
            package_contract_version=source.package_contract_version,
            package_assembly_rule_version=source.package_assembly_rule_version,
            producer_snapshot_identity=source.producer_snapshot_identity,
            snapshot_contract_version=source.snapshot_contract_version,
            assessment_version=source.assessment_version,
            methodology_version=source.methodology_version,
            derivation_rule_version=source.derivation_rule_version,
            derivation_runtime_version=source.derivation_runtime_version,
            lineage=inconsistent_lineage,
            source_derived_artifact=source.source_derived_artifact,
        )

        result = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(),
            inconsistent_package,
        )

        self.assertFalse(result.projected)
        self.assertIsNone(result.projection)
        self.assertIn("inconsistent-package-lineage", issue_codes(result))


if __name__ == "__main__":
    unittest.main()
