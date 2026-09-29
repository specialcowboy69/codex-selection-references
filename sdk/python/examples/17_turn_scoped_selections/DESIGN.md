# Turn-scoped selection references: design and implementation plan

## Scope and evidence

Investigated public baseline: `d515b2f85ec1b24a4b5ec3fbd86db27fd51aea3b`.
Desktop's composer is absent. This is a public-client prototype, not a Desktop
patch. It uses the existing Python SDK `TextInput` and app-server `turn/start`.
No public API, generated schema, server state, or persistent alias registry changes.

## Contract

- Each `SelectionDraft` owns captured strings and monotonically increasing `$aN`
  labels. IDs are stable after deletion (gaps allowed); silently retargeting an
  already-written question is worse than gaps. No reorder API in this prototype.
- `add(content)` returns an immutable, identity-based `SelectionRef` with a label.
  Explicit rich-reference nodes and ordinary text strings form the request.
- `submit(parts)` validates ownership and membership, compiles referenced content
  in place, includes unreferenced attachments, and returns a frozen
  `PreparedMessage(text)`. Only after successful validation does it clear the draft.
- `clear()` starts a fresh message at `$a1`; old handles remain invalid even when
  their label is reused. References from another draft are rejected.
- A prepared snapshot is an in-memory retry payload. Retry exactly that snapshot;
  do not re-resolve old labels against the next draft. No automatic network retry.
- Serialize structured request parts and quoted attachments as JSON inside the
  existing TextInput. Do not include generated alias labels in this model text.
  This is a compatible textual boundary, not a native model selection type.
- Raw strings are never scanned or expanded. A literal `$a1`, including in code,
  stays literal. A future rich composer must explicitly bind typed occurrences or
  insert handles by clicking labels. Automatic typed-token binding is out of scope.
- Bound the complete serialized selection payload to 1,000 UTF-8 bytes, at most
  32 attached selections. Reject overflow without clearing the draft. Quoted data
  stays data via JSON escaping, but this does not create a model authority boundary.
- With no attachments/references, preserve plain user text exactly. The example
  still rejects an empty message. It creates no configuration or memory files.

History, replay, compaction, and model changes retain ordinary submitted content.
There is no alias lookup to reactivate. This guarantees client resolution, not a
claim that an LLM can never infer a meaning for historical or literal text.

## Implementation plan

> Execution: subagents implement and independently review, under the user's
> explicit authorization to proceed automatically after the technical report.

**Tech stack:** Python >=3.10, stdlib core, existing SDK, pytest and Ruff.

**Files:** `selection_refs.py` (draft/compiler), `sync.py` (offline demonstration),
`README.md` (usage/limitations), `UPSTREAM_ISSUE.md` (unpublished proposal),
`../../tests/test_selection_refs_example.py` (unit coverage),
`../../tests/test_selection_refs_transport.py` (real app-server/mock model).

### Task 1: draft and compiler

- [x] Write failing tests for one/many selections, stable deletion/addition,
      foreign/deleted/expired handles, clear/reset, raw literals, JSON escaping,
      overflow, failed submission preservation, and immutable retry snapshots.
- [x] Run tests red, implement the contract, run tests green and scoped lint/types.
- [x] Independently review scope, state lifecycle, and hostile/Unicode input.

### Task 2: public transport and handoff

- [x] Exercise compiled text through SDK + real app-server against the existing
      local mock Responses server; inspect two messages with reused labels,
      ordinary literal input, and resumed history. No real inference or billing.
- [x] Run existing relevant SDK tests and report environment/baseline failures.
- [x] Write offline executable example, usage and complete upstream issue draft.
- [x] Run formatting and review final diff; limitations recorded in VALIDATION.md.

## Review decisions

Independent review checked expiry, deletion, Unicode, failure preservation and
immutable retries. It reduced the original 4,096-byte cap to 1,000 UTF-8 bytes to
avoid the repository's >1,000-token context-item review threshold. Added explicit
duplicate-content identity coverage. Keep local commits on the dedicated branch;
documentation lives beside the example. Do not publish an issue or external PR.
