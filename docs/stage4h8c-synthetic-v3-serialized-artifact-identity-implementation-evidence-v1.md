# Stage 4H.8C synthetic v3 serialized artifact identity: local implementation evidence

**Disposition:** LOCAL IMPLEMENTATION PASS — CONTROLLED PROMOTION PENDING.

**EIP baseline:** `a75c7451dcdefcaa77d3870337f6741559f1e110` on `main`.

**Authoritative Platform decision:**
`91ea84e8b0c99b3e9c3d0f3f400fd9a8b96bb994`,
`docs/platform/cep-v3-serialized-artifact-instance-identity-contract-decision-v1.md`
(Stage 4H.8B, approved 2026-11-08).

## Scope and interface

This local, nonproduction implementation created:

- `src/executive_intelligence_platform/projection_delivery/non_production_v3_serialized_artifact.py`
- `tests/projection_delivery/test_non_production_v3_serialized_artifact.py`
- This evidence document.

It changed only:

- `src/executive_intelligence_platform/projection_delivery/non_production_v3_publication_evidence.py`
- `tests/projection_delivery/test_non_production_v3_publication_evidence.py`

`create_synthetic_v3_artifact` accepts a fixture-assigned immutable instance
identifier and separately held synthetic scope. It re-prepares the Stage
4H.6A candidate through the same `VerifiedSnapshotGateway` and binds the
verified producer snapshot identity, package/methodology/decision-table
versions, delivery version, and exact ordered recommendation text. It does
not allocate a production identifier, recompute producer scoring, or change
the client-safe projection.

The trusted internal envelope contains exactly `artifactInstanceId`,
`artifactScope` (`businessEntityId`, `engagementId`, `environmentId`),
`content` (`recommendations[]` with only `recommendationActionText`),
`deliveryContractVersion`, `fieldScope`, `producerLineage`
(`producerSnapshotIdentity`), `serializationProfileVersion`, and
`versionContext` (assessment, methodology, package, decision-table, and
snapshot-response versions). Engagement is `null` only when separately held
synthetic scope marks it inapplicable. These metadata fields are trusted-only;
the candidate's client-safe content shape remains unchanged.

The `eip-synthetic-v3-artifact-json-v1` byte profile uses UTF-8 JSON without
BOM, sorted ASCII object keys, compact comma/colon separators, no insignificant
whitespace, preserved array order, and `ensure_ascii=True` string escaping.
There is no Unicode normalization or type coercion. Verification rejects
duplicate keys, invalid Unicode, numeric values, missing/null/unknown fields,
wrong types and versions, and any byte sequence that differs from strict
reserialization. The separately held `sha256:` reference contains 64 lowercase
hex digits computed over the finalized bytes. The digest is never embedded in
those bytes and is never used as the artifact-instance identifier.

`verify_synthetic_v3_artifact` returns only a boolean. It recomputes the
SHA-256 digest, verifies exact bytes and identifier against the freshly
same-gateway-verified candidate and trusted scope, and returns no content.
The artifact is frozen and always has `release_eligible=False`. The former
projection-digest-based synthetic artifact name cannot substitute for the
assigned identifier.

`verify_synthetic_v3_publication` now requires that artifact and trusted
scope. Its historical fixture record binds the exact instance identifier,
serialized bytes, digest, scope, serialization version, and verified lineage.
Distinct publication occurrences may reference the same complete artifact
claim; conflicting claims for one identifier fail closed. The existing
independent occurrence, revision, generation, current-state, withdrawal,
supersession, revocation, invalidation, fixture mismatch, and unavailability
checks remain. A synthetic accepted result still has `release_eligible=False`
and no client-facing payload or publication token.

## Verification executed

All commands used `PYTHONDONTWRITEBYTECODE=1`. Commands below are shown in
full. The initial new-test run had one failed order test because two fixture
recommendations had identical text; the test was corrected to use distinct
producer recommendations. A subsequent run passed. A transient test-helper
error was also corrected before the final passing run. No production source
change was made for either test issue.

| Command | Final result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_non_production_v3_serialized_artifact.py -v` | 8 tests, 8 passed, 0 failed, 0 skipped |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_non_production_v3_publication_evidence.py -v` | 10 tests, 10 passed, 0 failed, 0 skipped |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_recommendation_action_explain_delivery.py -q` | 9 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_local_v3_admission.py -q` | 5 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_verified_admission.py -q` | 14 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/snapshot_derivation -p test_local_v3_recommendation_projection.py -q` | 9 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_delivery.py -q` | 58 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_non_production_publication_revision_evidence.py -q` | 27 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests -p test_producer_snapshot_attestation_v3.py -q` (Assessment Service, read-only) | 8 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests -q` (EIP) | 344 passed, 0 failed, 0 skipped |

The positive tests check exact canonical bytes, repeated serialization,
SHA-256, immutable and distinct instance identity, verified lineage and scope,
recommendation order/text, and non-release state. Negative tests check missing,
malformed or substituted identities; conflicting instance claims; modified
bytes/digests; wrong versions, producer and scope; altered content; duplicate
keys; invalid Unicode; noncanonical JSON; forged candidate or foreign gateway;
publication lifecycle, stale generation and unavailable fixture. Rejections
return no recommendation content. Existing v2 delivery and publication tests
passed unchanged.

## Boundaries and next dependency

This fixture-bound proof does not establish live EIP publication approval or
currentness, Resource selection, assessment-instance continuity, principal
authorization, or client release. It creates no authority source, persistent
store, API, publisher, or production identifier allocator. No AWS or Bedrock
calls, deployment, client release, Git staging, commit, or push occurred.

Stage 4H.8A can consume the promoted exact instance identifier and digest
through a separately authorized Trusted synthetic binding interface. That
future interface must check the governed Resource and its independent current
binding generation and lifecycle; this EIP proof grants no binding authority.

**Local Git state at preparation:** two existing tracked files modified and
three authorized new files untracked; index empty. No other repository was
modified.
