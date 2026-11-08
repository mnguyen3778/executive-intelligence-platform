# Stage 4H.6D — Internal EIP Synthetic v3 Publication-Evidence Adapter Evidence v1

**Disposition:** LOCAL IMPLEMENTATION PASS — PROMOTION PENDING. This is a
nonproduction fixture proof. It does not establish authoritative publication
currentness, approval, release eligibility, or client delivery.

## Baselines and scope

- EIP `main` and local `origin/main`: `a5f84208d0b574dd601099766d35229921da8540`.
  The tracked tree, index, and untracked inventory were clean before work.
- Platform `main`: `f34b1d3bce1c9d7a646e1679f991fbc081bdcb08`.
  The founder-approved [logical authority-source decision](../../nguyen-ai-platform/docs/platform/cep-v3-publication-binding-continuity-logical-authority-source-decision-v1.md)
  separates the EIP Publication Register, Continuity Authority Instance Bridge
  Register, and Binding Authority Current-Selection Register. Its Stage 4H.6C
  logical decision is promoted. This separate founder instruction authorizes
  only the bounded Stage 4H.6D local implementation.
- Exactly these files were created: the adapter at
  `src/executive_intelligence_platform/projection_delivery/non_production_v3_publication_evidence.py`,
  focused tests at
  `tests/projection_delivery/test_non_production_v3_publication_evidence.py`,
  and this evidence document. No existing file was changed.

## Adapter and synthetic evidence

The entry point is `verify_synthetic_v3_publication`. It accepts the frozen
Stage 4H.6A internal candidate, its original local admission and gateway, an
untrusted selection, presented synthetic evidence, and a separate immutable
`trusted_fixture` held by the local test harness. Fixture equality checks
tampering relative to that harness fixture. It is deterministic fixture
integrity, **not production-grade authenticity or a signing authority**.

Historical `SyntheticV3PublicationRecord` values, effective
`SyntheticV3CurrentState` values, and the immutable verification result are
separate. The fixture snapshot carries a generation and availability state.
No caller `current=true` field establishes currentness. The fixture creates
no register, live source, mutation route, or release token.

The adapter reparses and reverifies the signed producer snapshot through the
same `VerifiedSnapshotGateway` by preparing a fresh Stage 4H.6A candidate.
It compares that candidate with the supplied frozen candidate. The synthetic
artifact identity and SHA-256 integrity reference derive from a canonical
encoding of the **trusted internal projection and verification evidence**;
client-safe content is not treated as an authority source. The record must
match that identity, integrity reference, producer snapshot identity, full
verified producer lineage, `business-decision-package-v3`, the existing
`business-decision-methodology-v1`, the existing
`recommendation-decision-table-set-v1`, the approved
`recommendationActionText` field scope, and
`website-recommendation-action-explain-delivery-contract-v1`.

Artifact identity, occurrence, revision, and generation are separate. Equal
artifact integrity references can occur in distinct occurrences. A revision
is selected by exact occurrence and revision; another revision does not
silently supersede it. Explicit synthetic `superseded_by` state is required.
Duplicate occurrences, duplicate series/revision identities, conflicting
states, and two current revisions in a series fail closed. Generation mismatch
rejects stale evidence. Withdrawal, supersession, revocation, and invalidation
reject, including when older positive historical records remain. Revocation
never restores an earlier revision.

Missing, unavailable, malformed, forged relative to the held fixture, or
ambiguous evidence rejects with payload-free reason codes. Rejected results
contain no action text or trusted producer evidence. Accepted results contain
only synthetic internal identity and remain `release_eligible=False`. Neither
result serializes a client payload or authorizes delivery.

## Local verification

Commands used `PYTHONDONTWRITEBYTECODE=1` to avoid generating additional
files. Initial focused run found two test fixture setup errors; those were
corrected. The final focused and full runs below were after the final adapter
type guard.

| Executed command | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_non_production_v3_publication_evidence.py -q` | 9 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_recommendation_action_explain_delivery.py -q` | 9 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_local_v3_admission.py -q` | 5 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_local_v3_delivery.py -q` | 10 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/snapshot_derivation -p test_local_v3_recommendation_projection.py -q` | 9 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_non_production_publication_revision_evidence.py -q` | 27 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_delivery.py -q` | 58 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_verified_admission.py -q` | 14 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests -p 'test_*.py' -q` | 335 passed |

The focused tests cover exact signed v3 matching, distinct occurrences with
identical artifact integrity, identity and version mismatches, stale generation,
missing and conflicting records, ambiguous current state, withdrawal,
supersession, revocation, invalidation, unavailable and malformed fixtures,
fixture-relative forgery, same-gateway provenance, non-release invariants,
and absence of v2 publisher calls or a live source.

## Remaining boundaries and change control

The Platform decision reserves concrete source custodians and mutation actors,
physical infrastructure, final evidence schemas, trusted retrieval, freshness
and audit controls, and production integration. The Continuity Authority,
Binding Authority, and fresh principal authorization are separate future
dependencies. Synthetic verification is not authoritative currentness.

No Git commit or push, publication activation, client-facing release,
production deployment, AWS/Bedrock call, or live authority source was made.
The Git index remains empty. Final Git status shows only the three authorized
untracked files; `git diff --stat` and `git diff --check` show no tracked changes,
and explicit whitespace checks of all three new files pass. Local disposition:
**Stage 4H.6D implementation passed; promotion pending.** Roadmap Stage 4
remains in progress.
