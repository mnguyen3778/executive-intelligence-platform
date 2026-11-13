# Stage 4H.9B — EIP-owned synthetic v3 explanation metadata evidence v1

**Disposition:** LOCAL IMPLEMENTATION PASS — PROMOTION PENDING.

**Date:** 2026-11-13. Founder authorization covers exactly three new EIP files,
local nonproduction implementation and tests. Promotion is not authorized.

## Governing policy and verified baselines

Normative [Stage 4H.9C policy](../../nguyen-ai-platform/docs/platform/cep-v3-explanation-metadata-content-schema-founder-decision-proposal-v1.md),
at the independently configured Platform policy revision
`2a40b70af64bcd53a8eab1ef32b3ce3d445eb3a0`. The document records explicit
founder approval of Decisions A, B and C in §14 and the immutable
policy-revision clarification in §7. Approval was inspected in the exact
`git show <revision>:<path>` document, not inferred from a commit or filename.

Exact approved document SHA-256:
`9f1ac7e1f1175bb579e9b74aaf78736e737c6cb025765da2001abc3fa1ed88af`.
The promoted bytes and clean Platform working copy have this same digest.
The verifier checks the independent configured pin and these exact approved
record bytes before parsing presented metadata. Neither EIP/Trusted HEAD nor
the presented envelope can select or advance policy. This digest pins the
inspected approval record; it is not a substitute publication authority.

The policy's governing delivery, eligibility, serialized-instance identity,
publication freshness, logical-source and Dashboard EXPLAIN contracts were
inspected read-only. Their producer/consumer separation and release gates
remain unchanged.

For each starting repository, the correct root, branch `main`, HEAD, local
`origin/main`, and live remote `main` were verified. Each of the three commit
references equaled the value below. All tracked worktrees were clean and
indexes empty. Only Platform had an untracked file: its protected document.

| Repository | Verified starting commit |
| --- | --- |
| EIP | `6a9bbae85d6b7fdd3514fe5d75b078872cb00d72` |
| Platform | `2a40b70af64bcd53a8eab1ef32b3ce3d445eb3a0` |
| Trusted | `62e0c4ae0b4c344d1bb954089499deee6df41f47` |
| Assessment Service | `9d544e4864b418478cf67f99726dde6cb4a63cad` |
| Website | `52b3a5b4e44d9769f01338fbc5dc74b64fe450d0` |

Protected Platform path:
`docs/platform/cep-principal-mapping-nonproduction-source-read-contract-v1.md`.
Verified SHA-256 before and after implementation:
`14884bc189ae8a43c9e1583bd04b224f75265e8f394ccd9ac64bb222d83eb2b0`.
The file remains untracked and was never modified, staged or renamed.

## Exact three-file scope

- `src/executive_intelligence_platform/projection_delivery/non_production_v3_explain_metadata.py`
- `tests/projection_delivery/test_non_production_v3_explain_metadata.py`
- `docs/cep-stage-4h9b-synthetic-v3-explain-metadata-evidence-v1.md`

All targets were absent before implementation. Existing EIP files and all
reference repositories were read-only. The inspected test convention is
`tests/projection_delivery/`, using Python `unittest` and local producer
fixtures. No new test directory, dependency installation, service or runtime
route was introduced.

## Implemented interface and approved content

`SyntheticV3ExplainMetadataVerifier` is frozen trusted-harness configuration;
`verify(presented)` accepts only private canonical metadata bytes. It returns
either deeply immutable `VerifiedSyntheticV3ExplainMetadata` or exactly
`{"decision":"DENY"}`. It does not construct a client response or render an
explanation. The success type has no `to_dict()` or general JSON serializer.
Nested objects become mapping proxies and arrays become tuples; positive
tests verify nested immutability as well as fixed `release_eligible=False`.

The implementation uses exactly these approved limitations, in this order:

1. `scope-v1`: Only approved recommendation action text is included; finding details and implementation plans are outside this explanation.
2. `nonproduction-v1`: This explanation is for nonproduction verification only; client release is not authorized.
3. `no-findings-v1`, conditional: No findings in this assessment does not establish absence of business risk, guaranteed compliance or safety, or that future assessment or improvement is unnecessary.

Finding-scoped content requires exactly the first two. The third requires
the freshly verified sole producer rule
`recommendation-v1-no-findings-monitor`, null finding linkage and trusted-only
`monitor` classification. The existing signed gateway validates complete
no-findings semantics and exact producer rule-to-text mapping. Applicability
does not come from prose. Extra, missing, changed, reordered or inapplicable
IDs/text deny. Producer classes, rule identifiers and findings are not copied
to success metadata or exposed to a client/model. No v2 or generated wording
is used.

Exact ordered classification evidence:

| Field | Classification |
| --- | --- |
| `contractVersion` | `portal_operational` |
| `explanation` | `restricted_assessment` |
| `content.recommendations[].recommendationActionText` | `restricted_assessment` |
| `limitations[]` | `restricted_assessment` |
| `sourceReferences` | `portal_operational` |

Whole-response classification is `restricted_assessment`. This mapping is
internal evidence; it adds no client classification field and grants no
principal access. Producer recommendation classification remains a separate
trusted validation fact.

## Schema, encoding and bounds

The contract is `eip-synthetic-v3-explain-metadata-v1`; delivery version is
`website-recommendation-action-explain-delivery-contract-v1`; response version
is `cep-nonproduction-dashboard-recommendation-action-explain-contract-v1`;
the selected artifact uses `eip-synthetic-v3-artifact-json-v1`.

All twelve required top-level members are enforced: `contract_version`,
`delivery_contract_version`, `response_contract_version`,
`serialization_profile_version`, `response_classification`,
`field_classifications`, `limitation_ids`, `limitations`, `selection`,
`publication`, `provenance`, and `release_eligible`.

The exact twelve selection keys, four publication keys and seven provenance
keys are those approved in policy §6. No nested or top-level unknown/missing
key is accepted. Client/workspace are strings only when their independently
verified applicability flags are true, otherwise null. Engagement is required
in this minimum profile. Client is not presumed to equal Business Entity.

Strict UTF-8 JSON parsing rejects duplicate keys at every depth, BOM, invalid
Unicode/lone surrogates, numeric/nonfinite values and wrong types. Sorted keys,
compact separators, ASCII escaping and byte-for-byte canonical reserialization
are required. Arbitrary pre-parsed mappings are rejected. Constants and ordered
arrays are compared exactly, without coercion, normalization or truncation.

Identifiers are 1–128 printable ASCII characters without surrounding whitespace
or controls. Each limitation has a 256-scalar / 1,024-byte bound; the complete
array has 768-scalar / 3,072-byte bounds. Private metadata is at most 16,384
UTF-8 bytes. Snapshot/digest syntax is exact lowercase SHA-256. Artifact ID
cannot be a digest, former projection-derived identifier, snapshot identity,
occurrence or revision. These metadata bytes stay separate from the frozen
artifact: no artifact bytes or digest are changed.

## Independent evidence and exact binding

The trusted harness independently configures policy bytes/pin, gateway and
same-gateway admission, candidate/artifact/scope, publication selector,
publication fixture/reader/source reference, and separate continuity and
binding fixtures/readers/requests. Presented metadata supplies comparison
claims only; it cannot configure any authority.

1. The existing `VerifiedSnapshotGateway` re-verifies the exact signed source
   and sidecar during candidate preparation. Existing producer validators
   verify five-field records, versions, rule mapping, linkage, text and order.
2. The existing serialized artifact verifier checks assigned instance identity,
   exact canonical bytes, recomputed SHA-256, scope and producer lineage.
3. The existing EIP publication verifier checks the independent fixture/current
   read, exact instance/bytes/digest, occurrence/revision/generation, complete
   scoped claims and lifecycle. Only synthetic accepted evidence with false
   release eligibility is usable. The configured publication source reference
   identifies that same fixture/reader binding; presented references do not
   create it.
4. Owner-configured continuity and binding reader callbacks return their
   owners' source snapshots. The module wraps them with the existing Trusted
   `SyntheticV3ContinuityVerifier.verify` and `SyntheticV3BindingVerifier.verify`
   callbacks on every verification. The real verifiers check separate fixture
   equality, source IDs, contract versions, source/record provenance,
   completeness, availability, applicability, current lifecycle, exact requests
   and independent generations. EIP neither fabricates positive results nor
   duplicates their authority logic. Returning a manufactured positive result
   instead of a source snapshot denies. Trusted modules are lazy imports from
   existing local source paths; absent dependencies deny.
5. The verified results must agree on Business Entity, environment, Engagement,
   assessment instance, signed snapshot, assigned artifact instance, digest,
   exact occurrence/revision and applicable Client/workspace/Resource scope.
   Continuity provides execution-to-snapshot association; binding provides
   exact Resource selection. Neither is inferred from equal signed bytes.
6. Exact expected metadata is built from these independently verified facts,
   fixed policy content and deterministic applicability. The whole presented
   envelope must equal it.
7. Publication, continuity and binding are read and verified again immediately
   before success. Selected results, generations, scope and currentness must
   remain unchanged. A generation cannot silently advance; no old positive
   result, replacement artifact or older revision is selected.

The implementation adaptation is a wrapper around existing Trusted verifiers
and owner-held source readers; it requires no frozen code changes or private
verifier attribute access. It imports no principal/token authorization into
EIP. There is no new publication, continuity or binding source.

## Test coverage and observed results

Focused suite: **95 independently named test scenarios: 3 positive and 92
negative**. Each generated scenario is its own `unittest` method. Multiple
assertions are not counted as separate scenarios.

Positive scenarios cover finding-scoped content, complete no-findings content,
and independently verified inapplicable Client/workspace scope. All require
two actual reads of each current source, exact artifact/occurrence/revision,
fixed policy pin, approved classifications, complete limitations and immutable
non-releasable success.

| Negative coverage | Evidence in the focused suite |
| --- | --- |
| Classification | Missing, wrong/unsupported, duplicate and reordered mapping. |
| Limitations | Missing, empty, wrong type/text/IDs, duplicate, extra, reordered, oversized; missing conditional or inapplicable caveat. |
| Instance/linkage/scope | Wrong instance including same presented digest; digest as ID; wrong snapshot, execution, Entity, environment, Engagement, Resource, Client/workspace, applicability, occurrence and revision. |
| Publication | Revoked, superseded with a current replacement present, withdrawn, invalidated, conflicting records, missing source, generation change; no fallback. |
| Provenance | Missing/forged configured approval record; unapproved configured revision; wrong presented pin; missing/wrong policy/source provenance; missing continuity source and binding record provenance. |
| Strict encoding/schema | Unknown/missing keys, duplicate top-level/nested keys, invalid UTF-8/BOM/surrogate, noncanonical key order/escaping/whitespace, numeric/nonfinite values, wrong types/nulls, identifier limits, oversized metadata, pre-parsed mappings. |
| Independent current sources | Unavailable continuity/binding; stale generation claims; changed second publication/continuity/binding read; callback exception; constructed positives replacing sources; independently wrong execution or binding instance with same digest. |
| Producer/artifact trust | Tampered signed bytes, foreign gateway, altered artifact bytes. |
| Disclosure/no fallback | Authority/token/debug fields, release flag true, invalid partial limitations/v2 fallback. Every negative checks exact content-free DENY bytes. |

All 92 negatives returned exactly `{"decision":"DENY"}` and nothing else.
The common assertion compares the complete object and its complete canonical
bytes. It therefore excludes partial content, reasons, IDs, internal
classification/limitations, exceptions, signatures, snapshots, artifacts,
authority records, tokens and audit data. The source-exception case uses a
sensitive marker that cannot appear in the exact response. There was no
negative content leak or unexpected test failure.

All commands below were actually executed from EIP root using Python 3.14:

| Exact command | Executed | Passed | Failed/errors | Expected skips | Unexpected skips |
| --- | ---: | ---: | ---: | ---: | ---: |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_non_production_v3_explain_metadata.py -v` | 95 | 95 | 0 | 0 | 0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_recommendation_action_explain_delivery.py -v` | 9 | 9 | 0 | 0 | 0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_non_production_v3_serialized_artifact.py -v` | 8 | 8 | 0 | 0 | 0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_non_production_v3_publication_evidence.py -v` | 10 | 10 | 0 | 0 | 0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_verified_admission.py -v` | 14 | 14 | 0 | 0 | 0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_local_v3_admission.py -v` | 5 | 5 | 0 | 0 | 0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests/projection_delivery -p test_assessment_service_snapshot_delivery.py -v` | 8 | 8 | 0 | 0 | 0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3.14 -m unittest discover -s tests -q` | 439 | 439 | 0 | 0 | 0 |

The six requested existing regression modules executed 54 tests, all passed.
The full-suite total above was observed directly, not assumed from historical
totals. The initial focused run, regression runs and full run all passed.
Static parsing of the two new Python files also succeeded.

## Final change-control verification and limitations

Final verification confirmed the same five roots/main/HEAD/origin/main/live-main
baselines above, clean tracked worktrees, empty indexes, exactly these three
new untracked EIP files, and only the original protected untracked document
in Platform. The policy and protected document hashes remain as recorded.
No staging, commit, push, tag, dependency installation, deployment, AWS call,
production credential, Website integration or client release occurred.

Synthetic fixture equality is deterministic local tamper/conformance evidence,
not live source authenticity, production publication approval or production
freshness. The trusted fixture custodian and configured source readers are
part of this internal proof's trust boundary; presented metadata cannot supply
them. Policy bytes and the fixed Platform pin are external configuration,
never inferred from presented claims. A future policy change requires separate
founder approval and promotion, not automatic pin advancement.

The metadata success retains `release_eligible=False`. No client serializer,
ALLOW response, standing authorization, explanation renderer, release
orchestrator, publication mutation, infrastructure or production source is
implemented. Inherited question/context/response limits remain requirements
for a separately authorized future renderer, not claims of client readiness.

Stage 4H.9B: LOCAL IMPLEMENTATION PASS — PROMOTION PENDING.
Stage 4H.9C: FOUNDER APPROVED / PROMOTED / CLOSED.
Stage 4H.9A: BLOCKED PENDING PROMOTED EIP METADATA IMPLEMENTATION.
Stage 4H.8: PROMOTED / CLOSED. Roadmap Stage 4: IN PROGRESS.
Roadmap Stage 5: NOT STARTED.

Next bounded action: review this implementation evidence and authorize
controlled EIP promotion separately if all gates pass. No promotion under the
implementation authorization.
