"""Pinned-policy synthetic metadata proof. No client serializer or release authority.

Only ``verify`` accepts presented data. All other inputs are trusted harness
configuration. Independent source readers return snapshots, never positive
result claims: the existing owners' verifiers run here on every read.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Callable

from .recommendation_action_explain_delivery import (
    RECOMMENDATION_ACTION_EXPLAIN_DELIVERY_CONTRACT_VERSION as DELIVERY_VERSION,
    prepare_recommendation_action_explain_delivery,
)
from .non_production_v3_serialized_artifact import (
    SERIALIZATION_PROFILE_VERSION, verify_synthetic_v3_artifact,
)
from .non_production_v3_publication_evidence import verify_synthetic_v3_publication
from .verified_admission import LOCAL_V3_PACKAGE_VERSION, VerifiedSnapshotGateway


CONTRACT_VERSION = "eip-synthetic-v3-explain-metadata-v1"
RESPONSE_VERSION = "cep-nonproduction-dashboard-recommendation-action-explain-contract-v1"
POLICY_REFERENCE = "docs/platform/cep-v3-explanation-metadata-content-schema-founder-decision-proposal-v1.md"
POLICY_REVISION = "2a40b70af64bcd53a8eab1ef32b3ce3d445eb3a0"
# Exact founder-approved document at POLICY_REVISION, inspected with its §14
# approval and §7 clarification. A revision or a caller approval flag alone
# cannot establish this record. No Git/network/runtime lookup occurs here.
_APPROVED_POLICY_SHA256 = "9f1ac7e1f1175bb579e9b74aaf78736e737c6cb025765da2001abc3fa1ed88af"
FIELD_CLASSIFICATIONS = (
    ("contractVersion", "portal_operational"),
    ("explanation", "restricted_assessment"),
    ("content.recommendations[].recommendationActionText", "restricted_assessment"),
    ("limitations[]", "restricted_assessment"),
    ("sourceReferences", "portal_operational"),
)
LIMITATION_IDS = ("scope-v1", "nonproduction-v1", "no-findings-v1")
LIMITATIONS = (
    "Only approved recommendation action text is included; finding details and implementation plans are outside this explanation.",
    "This explanation is for nonproduction verification only; client release is not authorized.",
    "No findings in this assessment does not establish absence of business risk, guaranteed compliance or safety, or that future assessment or improvement is unnecessary.",
)
_TOP = frozenset(("contract_version", "delivery_contract_version",
    "response_contract_version", "serialization_profile_version",
    "response_classification", "field_classifications", "limitation_ids",
    "limitations", "selection", "publication", "provenance", "release_eligible"))
_SELECTION = frozenset(("resource_reference", "business_entity_id", "environment_id",
    "engagement_id", "client_id", "workspace_id", "assessment_instance_id",
    "producer_snapshot_identity", "artifact_instance_id", "artifact_integrity_reference",
    "client_required", "workspace_required"))
_PUBLICATION = frozenset(("occurrence", "revision", "publication_generation", "state"))
_PROVENANCE = frozenset(("policy_reference", "policy_revision",
    "publication_source_reference", "continuity_source_reference", "binding_source_reference",
    "continuity_generation", "binding_generation"))
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z", re.ASCII)


def _identifier(value):
    return (type(value) is str and 1 <= len(value) <= 128 and value.isascii()
            and value == value.strip() and all(32 <= ord(c) <= 126 for c in value))


def _keys(value, keys):
    return type(value) is dict and value.keys() == keys


def _canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError()
        result[key] = value
    return result


def _no_number(_value):
    raise ValueError()


def _scalars(value):
    if type(value) is str:
        value.encode("utf-8", "strict")
    elif type(value) is dict:
        for key, item in value.items():
            _scalars(key)
            _scalars(item)
    elif type(value) is list:
        for item in value:
            _scalars(item)


def _parse(data):
    if type(data) is not bytes or not 0 < len(data) <= 16384:
        raise ValueError()
    value = json.loads(data.decode("utf-8", "strict"), object_pairs_hook=_unique,
                       parse_int=_no_number, parse_float=_no_number,
                       parse_constant=_no_number)
    _scalars(value)
    if _canonical(value) != data or not _keys(value, _TOP):
        raise ValueError()
    s, p, provenance = value["selection"], value["publication"], value["provenance"]
    if not (_keys(s, _SELECTION) and _keys(p, _PUBLICATION)
            and _keys(provenance, _PROVENANCE)):
        raise ValueError()
    if (value["contract_version"] != CONTRACT_VERSION
            or value["delivery_contract_version"] != DELIVERY_VERSION
            or value["response_contract_version"] != RESPONSE_VERSION
            or value["serialization_profile_version"] != SERIALIZATION_PROFILE_VERSION
            or value["response_classification"] != "restricted_assessment"
            or value["release_eligible"] is not False
            or value["field_classifications"] != [
                {"field": f, "classification": c} for f, c in FIELD_CLASSIFICATIONS]
            or p["state"] != "current"):
        raise ValueError()
    for name in _SELECTION - {"client_id", "workspace_id", "client_required",
                             "workspace_required", "producer_snapshot_identity",
                             "artifact_integrity_reference"}:
        if not _identifier(s[name]):
            raise ValueError()
    for name in ("client", "workspace"):
        required, reference = s[name + "_required"], s[name + "_id"]
        if type(required) is not bool or (
                not _identifier(reference) if required else reference is not None):
            raise ValueError()
    if (any(type(s[n]) is not str or _DIGEST.fullmatch(s[n]) is None
            for n in ("producer_snapshot_identity", "artifact_integrity_reference"))
            or s["artifact_instance_id"].startswith(("sha256:", "synthetic-v3-artifact:"))
            or s["artifact_instance_id"] in (s["producer_snapshot_identity"],
                                             p["occurrence"], p["revision"])):
        raise ValueError()
    if (not all(_identifier(p[n]) for n in _PUBLICATION - {"state"})
            or not all(_identifier(provenance[n]) for n in (
                "publication_source_reference", "continuity_generation", "binding_generation"))):
        raise ValueError()
    ids, texts = value["limitation_ids"], value["limitations"]
    if (type(ids) is not list or type(texts) is not list
            or len(ids) not in (2, 3) or len(texts) != len(ids)
            or ids != list(LIMITATION_IDS[:len(ids)])
            or any(type(t) is not str or len(t) > 256 or len(t.encode("utf-8")) > 1024
                   for t in texts)
            or sum(map(len, texts)) > 768
            or sum(len(t.encode("utf-8")) for t in texts) > 3072
            or texts != list(LIMITATIONS[:len(ids)])):
        raise ValueError()
    return value


def _freeze(value):
    if type(value) is dict:
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if type(value) is list:
        return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class VerifiedSyntheticV3ExplainMetadata:
    """Deeply immutable internal proof; deliberately has no serialization method."""

    contract_version: str
    delivery_contract_version: str
    response_contract_version: str
    serialization_profile_version: str
    response_classification: str
    field_classifications: tuple
    limitation_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    selection: MappingProxyType = field(repr=False)
    publication: MappingProxyType = field(repr=False)
    provenance: MappingProxyType = field(repr=False)
    release_eligible: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class SyntheticV3ExplainMetadataVerifier:
    """Construct only with independent trusted-harness dependencies.

    The source callbacks read snapshots. Their results are always verified by
    the real Trusted verifiers; a callback returning a manufactured positive
    result fails. No Principal, token or access decision enters this interface.
    """

    policy_revision: object
    policy_document: object = field(repr=False)
    gateway: object = field(repr=False)
    admission: object = field(repr=False)
    candidate: object = field(repr=False)
    artifact: object = field(repr=False)
    trusted_scope: object = field(repr=False)
    publication_selector: object = field(repr=False)
    publication_fixture: object = field(repr=False)
    publication_source_reference: object
    read_publication: Callable = field(repr=False)
    continuity_fixture: object = field(repr=False)
    continuity_request: object = field(repr=False)
    read_continuity: Callable = field(repr=False)
    binding_fixture: object = field(repr=False)
    binding_request: object = field(repr=False)
    read_binding: Callable = field(repr=False)

    def _publication(self, fresh):
        result = verify_synthetic_v3_publication(
            self.publication_selector, fresh, self.read_publication(),
            trusted_fixture=self.publication_fixture, gateway=self.gateway,
            admission=self.admission, artifact=self.artifact, trusted_scope=self.trusted_scope)
        if (result.status != "SYNTHETIC_ACCEPTED" or result.evidence is None
                or result.release_eligible is not False):
            raise ValueError()
        return result

    def verify(self, presented: object) -> VerifiedSyntheticV3ExplainMetadata | dict[str, str]:
        try:
            # The pin and approved record are trusted configuration, independent
            # of the presented envelope. Missing Trusted code also fails closed.
            if (type(self.policy_revision) is not str or self.policy_revision != POLICY_REVISION
                    or type(self.policy_document) is not bytes
                    or sha256(self.policy_document).hexdigest() != _APPROVED_POLICY_SHA256):
                return {"decision": "DENY"}
            value = _parse(presented)
            from trusted_authorization.non_production_v3_assessment_instance_continuity import (
                SyntheticV3ContinuityVerifier, SyntheticV3ContinuitySnapshot,
                VerifiedV3Continuity, SOURCE_ID as CONTINUITY_SOURCE,
            )
            from trusted_authorization.non_production_v3_resource_artifact_binding import (
                SyntheticV3BindingVerifier, SyntheticV3BindingSnapshot,
                VerifiedV3Binding, SOURCE_ID as BINDING_SOURCE,
            )
            if (type(self.gateway) is not VerifiedSnapshotGateway
                    or type(self.continuity_fixture) is not SyntheticV3ContinuitySnapshot
                    or type(self.binding_fixture) is not SyntheticV3BindingSnapshot
                    or self.binding_fixture.engagement_required is not True
                    or self.trusted_scope.engagement_applies is not True
                    or not _identifier(self.publication_source_reference)):
                raise ValueError()
            fresh = prepare_recommendation_action_explain_delivery(
                self.gateway, self.admission, package_contract_version=LOCAL_V3_PACKAGE_VERSION,
                delivery_contract_version=DELIVERY_VERSION)
            if (fresh != self.candidate or fresh.release_eligible is not False
                    or not verify_synthetic_v3_artifact(
                        self.artifact, fresh, self.gateway, self.admission,
                        expected_artifact_instance_id=self.publication_selector.artifact_identity,
                        trusted_scope=self.trusted_scope)):
                raise ValueError()
            publication = self._publication(fresh)
            # Existing verifier callbacks bind their own fixtures and readers.
            # EIP invokes them; it does not manufacture their positive results.
            continuity_verify = SyntheticV3ContinuityVerifier(
                trusted_fixture=self.continuity_fixture,
                read_current=self.read_continuity).verify
            binding_verify = SyntheticV3BindingVerifier(
                trusted_fixture=self.binding_fixture, read_current=self.read_binding).verify
            continuity = continuity_verify(self.continuity_request)
            binding = binding_verify(self.binding_request)
            if type(continuity) is not VerifiedV3Continuity or type(binding) is not VerifiedV3Binding:
                raise ValueError()
            scope, evidence = self.trusted_scope, publication.evidence
            if (any(getattr(continuity, name) != getattr(binding, name) for name in (
                    "assessment_instance_id", "producer_snapshot_identity", "business_entity_id",
                    "environment_id", "engagement_id"))
                    or (binding.business_entity_id, binding.environment_id, binding.engagement_id)
                    != (scope.business_entity_id, scope.environment_id, scope.engagement_id)
                    or binding.producer_snapshot_identity != fresh.verified_projection.producer_snapshot_identity
                    or (binding.artifact_instance_id, binding.artifact_integrity_reference,
                        binding.occurrence, binding.revision) != (
                        evidence.artifact_identity, evidence.artifact_integrity_reference,
                        evidence.occurrence, evidence.revision)):
                raise ValueError()
            rows = fresh.verified_projection.recommendations
            no_findings = any(r.recommendation_decision_identifier ==
                              "recommendation-v1-no-findings-monitor" for r in rows)
            if no_findings and not (len(rows) == 1 and rows[0].finding_id is None
                    and rows[0].recommendation_classification == "monitor"):
                raise ValueError()
            # Exact rule-to-text and complete no-findings linkage were freshly
            # checked by the signed gateway, not inferred from recommendation prose.
            count = 3 if no_findings else 2
            expected = {
                "contract_version": CONTRACT_VERSION,
                "delivery_contract_version": DELIVERY_VERSION,
                "response_contract_version": RESPONSE_VERSION,
                "serialization_profile_version": SERIALIZATION_PROFILE_VERSION,
                "response_classification": "restricted_assessment",
                "field_classifications": [{"field": f, "classification": c}
                                          for f, c in FIELD_CLASSIFICATIONS],
                "limitation_ids": list(LIMITATION_IDS[:count]),
                "limitations": list(LIMITATIONS[:count]),
                "selection": {name: getattr(binding, name) for name in _SELECTION
                              - {"client_required", "workspace_required"}},
                "publication": {"occurrence": evidence.occurrence, "revision": evidence.revision,
                    "publication_generation": evidence.authority_generation, "state": "current"},
                "provenance": {"policy_reference": POLICY_REFERENCE, "policy_revision": POLICY_REVISION,
                    "publication_source_reference": self.publication_source_reference,
                    "continuity_source_reference": CONTINUITY_SOURCE,
                    "binding_source_reference": BINDING_SOURCE,
                    "continuity_generation": continuity.generation, "binding_generation": binding.generation},
                "release_eligible": False,
            }
            expected["selection"].update(client_required=self.binding_fixture.client_required,
                                         workspace_required=self.binding_fixture.workspace_required)
            if value != expected:
                raise ValueError()
            # No old positive result may survive a changed final source read.
            if (self._publication(fresh) != publication
                    or continuity_verify(self.continuity_request) != continuity
                    or binding_verify(self.binding_request) != binding):
                raise ValueError()
            frozen = {key: _freeze(item) for key, item in value.items() if key != "release_eligible"}
            return VerifiedSyntheticV3ExplainMetadata(**frozen)
        except Exception:
            return {"decision": "DENY"}
