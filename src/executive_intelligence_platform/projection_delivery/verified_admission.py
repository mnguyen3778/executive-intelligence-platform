"""Local signed-snapshot admission and governed delivery boundary.

The Assessment Service verifier is imported by package name when a trusted
gateway is constructed. Local tests provide its source path explicitly; this
module contains no machine-specific path or second cryptographic algorithm.
No trust material or verification evidence enters Website delivery content.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from executive_intelligence_platform.executive_intelligence_package import (
    ExecutiveIntelligencePackageAssembler,
    ExecutiveIntelligencePackageRequest,
)
from executive_intelligence_platform.executive_intelligence_projection import (
    ExecutiveIntelligenceProjection,
    ExecutiveIntelligenceProjectionProjector,
    ExecutiveIntelligenceProjectionRequest,
)
from executive_intelligence_platform.projection_delivery.delivery import (
    WebsiteProjectionDeliveryRequest,
    WebsiteProjectionDeliveryResult,
    _find_prohibited_key,
    _publish_governed_dashboard_content,
)
from executive_intelligence_platform.snapshot_catalog import SnapshotCatalog
from executive_intelligence_platform.snapshot_derivation import (
    SnapshotDerivationRequest,
    SnapshotDerivationRuntime,
)
from executive_intelligence_platform.snapshot_derivation.derivation import (
    GOVERNED_CONTENT_DERIVATION_RULE_VERSION,
)
from executive_intelligence_platform.snapshot_compatibility.compatibility import (
    GOVERNED_ASSESSMENT_VERSION,
    GOVERNED_CONCLUSION_FIELDS,
    GOVERNED_PACKAGE_FIELD_ORDER,
    GOVERNED_RECOMMENDATION_FIELDS,
    RESPONSE_STATUS_FIELD_ORDER,
    ROOT_FIELD_ORDER,
    SUPPORTED_METHODOLOGY_VERSION,
    SUPPORTED_RESPONSE_CONTRACT_VERSION,
)


LOCAL_V3_PACKAGE_VERSION = "business-decision-package-v3"
_LOCAL_V3_RECOMMENDATION_FIELDS = GOVERNED_RECOMMENDATION_FIELDS + (
    "recommendationActionText",
)


class VerifiedAdmissionError(ValueError):
    """Payload-free failure at the verified EIP entry point."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class VerificationEvidence:
    """Internal continuity metadata; never serialized into public delivery."""

    issuer_id: str
    producer_release_commit: str
    producer_snapshot_identity: str
    snapshot_digest: str
    governed_conclusions_digest: str
    verification_contract_version: str
    key_id: str


@dataclass(frozen=True)
class VerifiedSnapshotAdmission:
    """Retains immutable bytes and sidecar for mandatory re-verification."""

    _snapshot_bytes: bytes
    _sidecar_items: tuple[tuple[str, str], ...]
    evidence: VerificationEvidence
    _gateway_marker: object = None

    @property
    def snapshot(self) -> dict[str, Any]:
        """Return a separate copy; mutations cannot change admitted bytes."""
        return json.loads(self._snapshot_bytes)


@dataclass(frozen=True)
class LocalV3GovernedProjection:
    """Local read-only view of signed producer conclusions; no delivery type."""

    _snapshot_bytes: bytes
    evidence: VerificationEvidence
    _sidecar_items: tuple[tuple[str, str], ...] = ()
    _gateway_marker: object = None

    @property
    def governed_conclusions(self) -> dict[str, Any]:
        # Each access returns a copy; caller changes cannot alter admitted bytes.
        return json.loads(self._snapshot_bytes)["businessDecisionPackage"][
            "governedConclusions"
        ]


@dataclass(frozen=True)
class LocalV3GovernedDelivery:
    """Nonproduction local result; never a Website delivery contract."""

    _snapshot_bytes: bytes
    evidence: VerificationEvidence

    @property
    def governed_conclusions(self) -> dict[str, Any]:
        return json.loads(self._snapshot_bytes)["businessDecisionPackage"][
            "governedConclusions"
        ]


@dataclass(frozen=True)
class VerifiedWebsiteDelivery:
    delivery: WebsiteProjectionDeliveryResult
    evidence: VerificationEvidence


class VerifiedSnapshotGateway:
    """Owner-configured trust boundary for one issuer and its trusted key."""

    def __init__(self, *, trusted_issuer_id: str, trusted_key_id: str,
                 trusted_public_key: object, expected_release_commit: str):
        try:
            from assessment.producer_snapshot_attestation import (
                ProducerSnapshotVerifier,
            )
        except ImportError:
            raise VerifiedAdmissionError("producer-verifier-unavailable") from None
        self._verifier = ProducerSnapshotVerifier(
            trusted_issuer_id=trusted_issuer_id,
            trusted_keys={trusted_key_id: trusted_public_key},
            expected_release_commit=expected_release_commit,
        )
        self._trusted_issuer_id = trusted_issuer_id
        self._trusted_key_id = trusted_key_id
        self._trusted_public_key = trusted_public_key
        self._expected_release_commit = expected_release_commit
        self._admission_marker = object()

    def admit_local_v3(
        self, snapshot_bytes: bytes, sidecar: object, *, package_contract_version: str,
    ) -> LocalV3GovernedProjection:
        """Explicit nonproduction admission; never enters catalog or delivery."""
        if type(package_contract_version) is not str or package_contract_version != LOCAL_V3_PACKAGE_VERSION:
            raise VerifiedAdmissionError("unsupported-local-package-version")
        if type(snapshot_bytes) is not bytes:
            raise VerifiedAdmissionError("invalid-snapshot-bytes")
        candidate = dict(sidecar) if type(sidecar) is dict else sidecar
        try:
            from assessment.producer_snapshot_attestation import (
                ProducerSnapshotVerifier, V3_VERIFICATION_CONTRACT_VERSION,
            )
        except ImportError:
            raise VerifiedAdmissionError("producer-v3-verifier-unavailable") from None
        verifier = ProducerSnapshotVerifier(
            trusted_issuer_id=self._trusted_issuer_id,
            trusted_keys={self._trusted_key_id: self._trusted_public_key},
            expected_release_commit=self._expected_release_commit,
            verification_contract_version=V3_VERIFICATION_CONTRACT_VERSION,
        )
        try:
            verifier.verify(snapshot_bytes, candidate)
        except ValueError as error:
            code = getattr(error, "code", None)
            raise VerifiedAdmissionError(
                code.value if code is not None else "attestation-verification-failed"
            ) from None
        try:
            snapshot = json.loads(snapshot_bytes)
            compatible = _local_v3_contract_valid(snapshot)
        except (ImportError, ValueError, TypeError, KeyError, IndexError, AttributeError):
            compatible = False
        if not compatible:
            raise VerifiedAdmissionError("local-v3-contract-invalid")
        return LocalV3GovernedProjection(
            _snapshot_bytes=snapshot_bytes,
            evidence=VerificationEvidence(
                issuer_id=candidate["issuerId"],
                producer_release_commit=candidate["producerReleaseCommit"],
                producer_snapshot_identity=candidate["producerSnapshotIdentity"],
                snapshot_digest=candidate["snapshotDigest"],
                governed_conclusions_digest=candidate["governedConclusionsDigest"],
                verification_contract_version=candidate["verificationContractVersion"],
                key_id=candidate["keyId"],
            ),
            _sidecar_items=tuple(candidate.items()),
            _gateway_marker=self._admission_marker,
        )

    def deliver_local_v3(
        self, admission: object, *, package_contract_version: str,
    ) -> LocalV3GovernedDelivery:
        """Reverify exact signed v3 bytes for one explicitly selected local use."""
        if (type(admission) is not LocalV3GovernedProjection or
                admission._gateway_marker is not self._admission_marker):
            raise VerifiedAdmissionError("unverified-local-v3-input")
        try:
            sidecar = dict(admission._sidecar_items)
        except (TypeError, ValueError):
            raise VerifiedAdmissionError("invalid-local-v3-evidence") from None
        verified = self.admit_local_v3(
            admission._snapshot_bytes, sidecar,
            package_contract_version=package_contract_version,
        )
        if verified.evidence != admission.evidence:
            raise VerifiedAdmissionError("verified-evidence-mismatch")
        return LocalV3GovernedDelivery(
            _snapshot_bytes=verified._snapshot_bytes,
            evidence=verified.evidence,
        )

    def _verified_entry(self, snapshot_bytes: bytes, sidecar: object):
        if type(snapshot_bytes) is not bytes:
            raise VerifiedAdmissionError("invalid-snapshot-bytes")
        try:
            self._verifier.verify(snapshot_bytes, sidecar)
        except ValueError as error:
            code = getattr(error, "code", None)
            raise VerifiedAdmissionError(
                code.value if code is not None else "attestation-verification-failed"
            ) from None
        # The Stage 1C verifier has already strictly parsed these exact bytes.
        snapshot = json.loads(snapshot_bytes)
        evidence = VerificationEvidence(
            issuer_id=sidecar["issuerId"],
            producer_release_commit=sidecar["producerReleaseCommit"],
            producer_snapshot_identity=sidecar["producerSnapshotIdentity"],
            snapshot_digest=sidecar["snapshotDigest"],
            governed_conclusions_digest=sidecar["governedConclusionsDigest"],
            verification_contract_version=sidecar["verificationContractVersion"],
            key_id=sidecar["keyId"],
        )
        catalog = SnapshotCatalog()
        admitted = catalog.admit(
            snapshot, producer_snapshot_identity=evidence.producer_snapshot_identity,
        )
        if not admitted.accepted or admitted.entry is None:
            raise VerifiedAdmissionError("verified-snapshot-incompatible")
        if admitted.entry.producer_snapshot_identity != evidence.producer_snapshot_identity:
            raise VerifiedAdmissionError("verified-chain-broken")
        return snapshot, evidence, admitted.entry

    def admit(self, snapshot_bytes: bytes, sidecar: object) -> VerifiedSnapshotAdmission:
        """Admit only producer-verified exact bytes and preserve signed evidence."""
        candidate = dict(sidecar) if type(sidecar) is dict else sidecar
        _snapshot, evidence, _entry = self._verified_entry(snapshot_bytes, candidate)
        return VerifiedSnapshotAdmission(
            _snapshot_bytes=snapshot_bytes,
            _sidecar_items=tuple(candidate.items()),
            evidence=evidence,
            _gateway_marker=self._admission_marker,
        )

    def verify_projection(
        self, admission: VerifiedSnapshotAdmission, projection: object,
    ) -> None:
        """Reverify signed bytes and compare with a fresh governed projection."""
        if (type(admission) is not VerifiedSnapshotAdmission or
                admission._gateway_marker is not self._admission_marker):
            raise VerifiedAdmissionError("unverified-derivation-input")
        snapshot, evidence, entry = self._verified_entry(
            admission._snapshot_bytes, dict(admission._sidecar_items)
        )
        if evidence != admission.evidence:
            raise VerifiedAdmissionError("verified-evidence-mismatch")
        derived = SnapshotDerivationRuntime().derive(
            entry, SnapshotDerivationRequest(GOVERNED_CONTENT_DERIVATION_RULE_VERSION)
        )
        if not derived.derived or derived.artifact is None:
            raise VerifiedAdmissionError("verified-derivation-failed")
        artifact = derived.artifact
        if artifact.to_dict().get("governedConclusions") != snapshot[
            "businessDecisionPackage"
        ]["governedConclusions"]:
            raise VerifiedAdmissionError("verified-chain-broken")
        packaged = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(), artifact
        )
        if not packaged.packaged or packaged.package is None:
            raise VerifiedAdmissionError("verified-package-failed")
        projected = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(), packaged.package
        )
        if (not projected.projected or projected.projection is None or
                not isinstance(projection, ExecutiveIntelligenceProjection) or
                projection.to_dict() != projected.projection.to_dict()):
            raise VerifiedAdmissionError("verified-chain-broken")

    def deliver(self, admission: VerifiedSnapshotAdmission) -> VerifiedWebsiteDelivery:
        """Reverify admission, then own every derivation and delivery input."""
        if (type(admission) is not VerifiedSnapshotAdmission or
                admission._gateway_marker is not self._admission_marker):
            raise VerifiedAdmissionError("unverified-derivation-input")
        snapshot, evidence, entry = self._verified_entry(
            admission._snapshot_bytes, dict(admission._sidecar_items)
        )
        if evidence != admission.evidence:
            raise VerifiedAdmissionError("verified-evidence-mismatch")

        derivation = SnapshotDerivationRuntime().derive(
            entry, SnapshotDerivationRequest(GOVERNED_CONTENT_DERIVATION_RULE_VERSION)
        )
        if not derivation.derived or derivation.artifact is None:
            raise VerifiedAdmissionError("verified-derivation-failed")
        artifact = derivation.artifact
        if (artifact.producer_snapshot_identity != evidence.producer_snapshot_identity or
                artifact.to_dict().get("governedConclusions") !=
                snapshot["businessDecisionPackage"]["governedConclusions"]):
            raise VerifiedAdmissionError("verified-chain-broken")

        packaged = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(), artifact
        )
        if not packaged.packaged or packaged.package is None:
            raise VerifiedAdmissionError("verified-package-failed")
        package = packaged.package
        if (package.producer_snapshot_identity != evidence.producer_snapshot_identity or
                package.source_derived_artifact is not artifact):
            raise VerifiedAdmissionError("verified-chain-broken")

        projected = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(), package
        )
        if not projected.projected or projected.projection is None:
            raise VerifiedAdmissionError("verified-projection-failed")
        projection = projected.projection
        if (projection.producer_snapshot_identity != evidence.producer_snapshot_identity or
                projection.source_package is not package):
            raise VerifiedAdmissionError("verified-chain-broken")

        delivered = _publish_governed_dashboard_content(
            WebsiteProjectionDeliveryRequest(), projection,
            verified_admission=admission, trusted_gateway=self,
        )
        if not delivered.delivered or delivered.delivery is None:
            raise VerifiedAdmissionError("verified-delivery-failed")
        payload = delivered.delivery.to_dict()
        if (_find_prohibited_key(payload) is not None or
                payload["projectionReference"]["producerSnapshotIdentity"] !=
                evidence.producer_snapshot_identity):
            raise VerifiedAdmissionError("verified-chain-broken")
        return VerifiedWebsiteDelivery(delivery=delivered, evidence=evidence)


def _local_v3_contract_valid(snapshot: object) -> bool:
    """Consumer checks after independent signature and producer validation."""
    from assessment.approved_methodology_runtime_config import (
        APPROVED_RECOMMENDATION_ACTION_TEXT_BY_RULE,
    )

    if type(snapshot) is not dict or tuple(snapshot) != ROOT_FIELD_ORDER:
        return False
    status = snapshot.get("responseStatus")
    package = snapshot.get("businessDecisionPackage")
    if (snapshot.get("responseContractVersion") != SUPPORTED_RESPONSE_CONTRACT_VERSION
            or type(status) is not dict or tuple(status) != RESPONSE_STATUS_FIELD_ORDER
            or status["productionAuthority"] != "NOT_PRODUCTION_AUTHORITATIVE"
            or type(package) is not dict or tuple(package) != GOVERNED_PACKAGE_FIELD_ORDER):
        return False
    metadata = package.get("versionMetadata")
    governed = package.get("governedConclusions")
    if (type(metadata) is not dict or
            (metadata.get("contractVersion"), metadata.get("assessmentVersion"),
             metadata.get("methodologyVersion")) !=
            (LOCAL_V3_PACKAGE_VERSION, GOVERNED_ASSESSMENT_VERSION,
             SUPPORTED_METHODOLOGY_VERSION) or
            type(governed) is not dict or tuple(governed) != GOVERNED_CONCLUSION_FIELDS):
        return False
    findings = governed["severityAssignedFindings"]
    recommendations = governed["recommendations"]
    if (type(findings) is not list or type(recommendations) is not list or
            len(recommendations) != max(1, len(findings))):
        return False
    finding_ids = [item["findingId"] for item in findings]
    for index, recommendation in enumerate(recommendations):
        if type(recommendation) is not dict or tuple(recommendation) != _LOCAL_V3_RECOMMENDATION_FIELDS:
            return False
        rule = recommendation["recommendationDecisionIdentifier"]
        if (type(rule) is not str or
                recommendation["recommendationDecisionTableVersion"] != "recommendation-decision-table-set-v1" or
                recommendation["recommendationActionText"] !=
                APPROVED_RECOMMENDATION_ACTION_TEXT_BY_RULE.get(rule) or
                recommendation["findingId"] !=
                (finding_ids[index] if finding_ids else None)):
            return False
    return bool(findings) or (
        recommendations[0]["recommendationDecisionIdentifier"]
        == "recommendation-v1-no-findings-monitor"
        and recommendations[0]["recommendationClassification"] == "monitor"
    )
