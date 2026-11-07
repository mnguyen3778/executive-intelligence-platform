# Stage 4H.4 — Local v3 Recommendation Projection Evidence v1

**Scope:** deterministic internal projection of producer-approved v3
recommendations from EIP's explicitly selected, signed, verified local delivery.
This is nonproduction preparation, not client-facing release.

## Baselines and implementation

EIP `main` and local `origin/main` were
`8fc31508ab435d565c2225cce6db8aba95be4958` before this three-file
promotion. The read-only Assessment Service checkout was clean at
`9d544e4864b418478cf67f99726dde6cb4a63cad`.

The implementation is
[`local_v3_recommendation_projection.py`](../src/executive_intelligence_platform/snapshot_derivation/local_v3_recommendation_projection.py);
its focused tests are
[`test_local_v3_recommendation_projection.py`](../tests/snapshot_derivation/test_local_v3_recommendation_projection.py).
The [producer v3 package contract](../../nguyen-ai-assessment-service/docs/architecture/business-decision-package-contract-v3.md)
defines the five-field recommendation record. The producer's approved
rule-to-text mapping owns all eight exact action statements. EIP adds no
business wording map, recommendation decision, or assessment interpretation.

`project_local_v3_recommendations` requires an owner-configured
`VerifiedSnapshotGateway`, its same-gateway local admission, and explicit v3
selection. It calls the existing `deliver_local_v3` method, which reverifies
signed snapshot bytes and sidecar evidence against the trusted issuer, key,
and expected producer release. A caller assertion of verification, raw JSON,
or an unrelated gateway is insufficient.

The frozen internal projection contains ordered records of finding ID,
recommendation classification, decision identifier, decision-table version,
and exact action text. It retains package and methodology versions, producer
snapshot identity, and verification evidence. Source order and the producer's
`findingId: null` no-findings link are preserved. It provides no display
serializer; `release_eligible` is always `False`.

## Verification

Fresh promotion checks used Python 3.14 with `PYTHONDONTWRITEBYTECODE=1` and
`PYTHONPATH=src`, running `unittest discover` for each named test module:

| Test module | Fresh result |
| --- | ---: |
| `test_local_v3_recommendation_projection.py` | 9 passed |
| `test_local_v3_admission.py` | 5 passed |
| `test_local_v3_delivery.py` | 10 passed |
| `test_delivery.py` (existing v2 delivery) | 58 passed |
| `test_assessment_service_snapshot_delivery.py` | 8 passed |
| `test_verified_admission.py` | 14 passed |

The earlier Stage 4H.4 implementation verification ran the full EIP suite:
**317 passed, 0 failed, 0 skipped**. The full suite was not rerun for this
documentation promotion. Both implementation files passed in-memory syntax
compilation, final-newline and trailing-whitespace checks. This repository has
no configured lint or type-check command; none is claimed as executed.

The focused tests cover all eight approved emitting rules, exact text and
ordering, no-findings null linkage, immutable results, and absence of
downstream publication. Negative cases reject missing or forged verification,
changed text, missing or extra records, changed order, classifications or
finding links, unknown or missing decision identifiers, cross-version input,
malformed content, an unrelated gateway, and a stale expected-release check.
The source code and existing v2 Dashboard delivery contracts were unchanged.

## Release limits and promotion disposition

This projection grants no client-facing eligibility, `EXPLAIN` or `VIEW`
authorization, Dashboard or REPORT field scope, Website or CEP response,
publisher, production route, or downstream v3 activation. Expected producer
release matching is the existing local stale-evidence control; this work does
not establish publication currentness or revocation authority. Producer
wording approval alone does not approve client display. A separate founder
decision is required before v3 action text enters any versioned delivery or
Dashboard EXPLAIN field scope. Roadmap Stage 4 remains **IN PROGRESS**.

Promotion is limited to this document and the two implementation files above.
The promotion report records the resulting commit, staged-diff checks, push,
and live remote synchronization. Upon those checks passing, the Stage 4H.4
internal-preparation milestone is **CLOSED**; client-facing release remains
**INELIGIBLE**.
