import copy
import sys
import unittest
from pathlib import Path
from types import MappingProxyType


EIP_ROOT = Path(__file__).resolve().parents[2]
ASSESSMENT_SERVICE_ROOT = EIP_ROOT.parent / "nguyen-ai-assessment-service"

sys.path.insert(0, str(EIP_ROOT / "src"))
sys.path.insert(0, str(ASSESSMENT_SERVICE_ROOT / "src"))
sys.path.insert(0, str(ASSESSMENT_SERVICE_ROOT / "tests"))

from assessment.business_decision_package import (  # noqa: E402
    BUSINESS_DECISION_PACKAGE_COMPONENT_VERSIONS,
    BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION,
    GOVERNED_BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION,
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
from test_golden_fixture_regression import request  # noqa: E402
from assessment.methodology_config import (  # noqa: E402
    BUSINESS_DECISION_METHODOLOGY,
    METHODOLOGY_VERSION,
)
from executive_intelligence_platform.snapshot_catalog import (  # noqa: E402
    SnapshotCatalog,
)
from executive_intelligence_platform.snapshot_compatibility import (  # noqa: E402
    validate_snapshot_compatibility,
)


PRODUCER_SNAPSHOT_IDENTITY = (
    "assessment-service:executive-assessment-snapshot:integration-contract-v1"
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


def governed_fixture_snapshot(profile="mixed-strong", findings="two-high"):
    production_result = produce_executive_assessment_snapshot(
        request(75, profile, findings)
    )
    if not production_result.is_success:
        raise AssertionError(production_result.failure)
    return production_result.serialized_snapshot


def issue_codes(validation_result):
    return tuple(issue.code for issue in validation_result.issues)


class CrossRepositorySnapshotAdmissionContractTests(unittest.TestCase):
    def test_frozen_golden_fixture_v2_is_compatible_and_admitted(self):
        snapshot = governed_fixture_snapshot()
        original = copy.deepcopy(snapshot)
        catalog = SnapshotCatalog()

        compatibility = validate_snapshot_compatibility(snapshot)
        admitted = catalog.admit(
            snapshot, producer_snapshot_identity=PRODUCER_SNAPSHOT_IDENTITY,
        )

        self.assertTrue(compatibility.is_valid, compatibility.issues)
        self.assertTrue(admitted.accepted, admitted.issues)
        self.assertEqual(snapshot, original)
        self.assertEqual(admitted.entry.to_dict()["snapshotEvidence"], original)
        self.assertIs(catalog.get(PRODUCER_SNAPSHOT_IDENTITY), admitted.entry)
        self.assertEqual(len(catalog.list_entries()), 1)
        metadata = admitted.entry.admission_metadata
        package = original["businessDecisionPackage"]
        self.assertEqual(
            metadata.package_contract_version,
            GOVERNED_BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION,
        )
        self.assertEqual(metadata.assessment_version, package["versionMetadata"]["assessmentVersion"])
        self.assertEqual(metadata.methodology_version, METHODOLOGY_VERSION)
        self.assertEqual(metadata.source_component_ids, tuple(package["audit"]["sourceComponentIds"]))
        self.assertEqual(metadata.production_authority, NOT_PRODUCTION_AUTHORITATIVE)
        self.assertEqual(admitted.entry.snapshot_evidence["responseStatus"]["productionAuthority"],
                         NOT_PRODUCTION_AUTHORITATIVE)

    def test_frozen_empty_findings_fixture_is_compatible(self):
        snapshot = governed_fixture_snapshot("adequate", "none")
        self.assertEqual(snapshot["businessDecisionPackage"]["governedConclusions"]
                         ["severityAssignedFindings"], [])
        self.assertTrue(validate_snapshot_compatibility(snapshot).is_valid)

    def test_malformed_v2_snapshots_fail_closed_without_catalog_entry(self):
        def package(snapshot):
            return snapshot["businessDecisionPackage"]

        changes = (
            ("missing conclusions", lambda s: package(s).pop("governedConclusions"),
             "missing-package-field"),
            ("wrong conclusions type", lambda s: package(s).__setitem__("governedConclusions", []),
             "invalid-governed-conclusions"),
            ("missing conclusion member", lambda s: package(s)["governedConclusions"].pop("confidence"),
             "invalid-governed-conclusions"),
            ("invalid severity", lambda s: package(s)["governedConclusions"]["severityAssignedFindings"][0]
             .__setitem__("severityClassification", "unknown"), "invalid-governed-conclusions"),
            ("missing evidence reference", lambda s: package(s)["governedConclusions"]
             ["severityAssignedFindings"][0].__setitem__("sourceReferences", []),
             "invalid-governed-conclusions"),
            ("finding order", lambda s: package(s)["governedConclusions"]
             ["severityAssignedFindings"].reverse(), "invalid-governed-conclusions"),
            ("recommendation order", lambda s: package(s)["governedConclusions"]
             ["recommendations"].reverse(), "invalid-governed-conclusions"),
            ("missing recommendation", lambda s: package(s)["governedConclusions"]
             ["recommendations"].pop(), "invalid-governed-conclusions"),
            ("invalid summary", lambda s: package(s)["governedConclusions"]
             ["executiveSummary"].__setitem__("findingCount", 0),
             "invalid-governed-conclusions"),
            ("conflicting assessment", lambda s: package(s)["versionMetadata"]
             .__setitem__("assessmentVersion", EXECUTIVE_ASSESSMENT_VERSION),
             "unsupported-assessment-version"),
            ("audit binding", lambda s: package(s)["audit"]
             .__setitem__("assessmentVersion", "other"), "audit-assessment-version-mismatch"),
            ("unsupported package", lambda s: package(s)["versionMetadata"]
             .__setitem__("contractVersion", "business-decision-package-v3"),
             "unsupported-package-contract-version"),
            ("unsupported assessment", lambda s: package(s)["versionMetadata"]
             .__setitem__("assessmentVersion", "other"), "unsupported-assessment-version"),
            ("obsolete limitation", lambda s: package(s)["limitations"]
             .append("final-confidence-formulas-not-implemented"),
             "unsupported-package-limitations"),
            ("missing limitation", lambda s: package(s)["limitations"].pop(),
             "unsupported-package-limitations"),
            ("malformed limitation", lambda s: package(s)["limitations"]
             .append({"invalid": True}), "unsupported-package-limitations"),
            ("malformed provenance", lambda s: package(s)["audit"]
             .__setitem__("sourceComponentIds", None), "unsupported-source-components"),
            ("production authority", lambda s: s["responseStatus"]
             .__setitem__("productionAuthority", "PRODUCTION_AUTHORITY_UPGRADED"),
             "unsupported-response-status"),
            ("malformed status", lambda s: s["responseStatus"]
             .__setitem__("productionAuthority", []), "unsupported-response-status"),
        )
        for name, change, expected_code in changes:
            with self.subTest(name=name):
                snapshot = governed_fixture_snapshot()
                change(snapshot)
                compatibility = validate_snapshot_compatibility(snapshot)
                catalog = SnapshotCatalog()
                admission = catalog.admit(
                    snapshot, producer_snapshot_identity=PRODUCER_SNAPSHOT_IDENTITY,
                )
                self.assertFalse(compatibility.is_valid)
                self.assertIn(expected_code, issue_codes(compatibility))
                self.assertFalse(admission.accepted)
                self.assertIsNone(admission.entry)
                self.assertEqual(catalog.list_entries(), ())

    def test_assessment_service_snapshot_is_accepted_without_modification(self):
        serialized_snapshot = producer_serialized_snapshot()
        before_validation = copy.deepcopy(serialized_snapshot)

        compatibility_result = validate_snapshot_compatibility(serialized_snapshot)

        self.assertTrue(compatibility_result.is_valid)
        self.assertEqual(compatibility_result.issues, ())
        self.assertEqual(serialized_snapshot, before_validation)

    def test_assessment_service_snapshot_is_cataloged_without_mutation(self):
        serialized_snapshot = producer_serialized_snapshot()
        before_admission = copy.deepcopy(serialized_snapshot)
        catalog = SnapshotCatalog()

        admission_result = catalog.admit(
            serialized_snapshot,
            producer_snapshot_identity=PRODUCER_SNAPSHOT_IDENTITY,
        )

        self.assertTrue(admission_result.accepted)
        self.assertEqual(admission_result.issues, ())
        self.assertEqual(serialized_snapshot, before_admission)
        self.assertIsNotNone(admission_result.entry)
        self.assertIs(
            catalog.get(PRODUCER_SNAPSHOT_IDENTITY),
            admission_result.entry,
        )
        self.assertEqual(
            admission_result.entry.to_dict()["snapshotEvidence"],
            before_admission,
        )

    def test_catalog_entry_preserves_identity_versions_provenance_and_evidence(self):
        serialized_snapshot = producer_serialized_snapshot()
        catalog = SnapshotCatalog()

        admission_result = catalog.admit(
            serialized_snapshot,
            producer_snapshot_identity=PRODUCER_SNAPSHOT_IDENTITY,
        )

        self.assertTrue(admission_result.accepted)
        entry = admission_result.entry
        package = entry.snapshot_evidence["businessDecisionPackage"]
        version_metadata = package["versionMetadata"]

        self.assertEqual(entry.producer_snapshot_identity, PRODUCER_SNAPSHOT_IDENTITY)
        self.assertEqual(
            entry.admission_metadata.producer_snapshot_identity,
            PRODUCER_SNAPSHOT_IDENTITY,
        )
        self.assertEqual(
            entry.admission_metadata.response_contract_version,
            EXECUTIVE_RUNTIME_RESPONSE_CONTRACT_VERSION,
        )
        self.assertEqual(
            entry.admission_metadata.package_contract_version,
            BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION,
        )
        self.assertEqual(
            entry.admission_metadata.assessment_version,
            EXECUTIVE_ASSESSMENT_VERSION,
        )
        self.assertEqual(
            entry.admission_metadata.methodology_version,
            METHODOLOGY_VERSION,
        )
        self.assertEqual(
            entry.admission_metadata.production_authority,
            NOT_PRODUCTION_AUTHORITATIVE,
        )
        self.assertEqual(
            dict(version_metadata["componentVersions"]),
            dict(BUSINESS_DECISION_PACKAGE_COMPONENT_VERSIONS),
        )
        self.assertIsInstance(entry.snapshot_evidence, MappingProxyType)
        self.assertIsInstance(package, MappingProxyType)

    def test_catalog_evidence_is_immutable_and_isolated_from_later_input_mutation(self):
        serialized_snapshot = producer_serialized_snapshot()
        catalog = SnapshotCatalog()
        admission_result = catalog.admit(
            serialized_snapshot,
            producer_snapshot_identity=PRODUCER_SNAPSHOT_IDENTITY,
        )

        entry = admission_result.entry
        with self.assertRaises(TypeError):
            entry.snapshot_evidence["responseContractVersion"] = "mutated"
        with self.assertRaises(TypeError):
            entry.snapshot_evidence["businessDecisionPackage"][
                "versionMetadata"
            ]["contractVersion"] = "mutated"

        serialized_snapshot["responseContractVersion"] = "mutated-after-admission"

        self.assertEqual(
            entry.snapshot_evidence["responseContractVersion"],
            EXECUTIVE_RUNTIME_RESPONSE_CONTRACT_VERSION,
        )

    def test_rejects_mutated_response_contract_version_fail_closed(self):
        serialized_snapshot = producer_serialized_snapshot()
        serialized_snapshot["responseContractVersion"] = "unsupported-contract"

        result = validate_snapshot_compatibility(serialized_snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported-response-contract-version", issue_codes(result))

    def test_rejects_mutated_package_contract_version_fail_closed(self):
        serialized_snapshot = producer_serialized_snapshot()
        serialized_snapshot["businessDecisionPackage"]["versionMetadata"][
            "contractVersion"
        ] = "business-decision-package-v3"

        result = validate_snapshot_compatibility(serialized_snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported-package-contract-version", issue_codes(result))

    def test_rejects_mutated_component_versions_fail_closed(self):
        serialized_snapshot = producer_serialized_snapshot()
        serialized_snapshot["businessDecisionPackage"]["versionMetadata"][
            "componentVersions"
        ]["decisionEvaluation"] = "assessment-decision-engine-v3"

        result = validate_snapshot_compatibility(serialized_snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported-component-versions", issue_codes(result))

    def test_rejects_mutated_production_authority_fail_closed(self):
        serialized_snapshot = producer_serialized_snapshot()
        serialized_snapshot["responseStatus"]["productionAuthority"] = (
            "PRODUCTION_AUTHORITY_UPGRADED"
        )

        result = validate_snapshot_compatibility(serialized_snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported-response-status", issue_codes(result))

    def test_rejects_mutated_package_limitations_fail_closed(self):
        serialized_snapshot = producer_serialized_snapshot()
        serialized_snapshot["businessDecisionPackage"]["limitations"] = []

        result = validate_snapshot_compatibility(serialized_snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported-package-limitations", issue_codes(result))

    def test_catalog_rejects_incompatible_producer_snapshot_without_admission(self):
        serialized_snapshot = producer_serialized_snapshot()
        serialized_snapshot["responseContractVersion"] = "unsupported-contract"
        catalog = SnapshotCatalog()

        result = catalog.admit(
            serialized_snapshot,
            producer_snapshot_identity=PRODUCER_SNAPSHOT_IDENTITY,
        )

        self.assertFalse(result.accepted)
        self.assertIsNone(result.entry)
        self.assertIn("incompatible-snapshot", issue_codes(result))
        self.assertIn("unsupported-response-contract-version", issue_codes(result))
        self.assertEqual(catalog.list_entries(), ())


if __name__ == "__main__":
    unittest.main()
