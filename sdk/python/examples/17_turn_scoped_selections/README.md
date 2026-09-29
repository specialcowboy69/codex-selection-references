# Turn-scoped selection references (client prototype)

This example demonstrates draft-local `$a1`, `$a2` labels with the public SDK
transport. **It does not modify Codex Desktop or implement its Add to chat UI.**
Client handles resolve before sending through the existing text input protocol;
the module is intentionally not exported from `openai_codex`.

Run the offline demonstration from the repository root (no account or model call):

```shell
python sdk/python/examples/17_turn_scoped_selections/sync.py
```

```python
from selection_refs import SelectionDraft
from openai_codex import TextInput

draft = SelectionDraft()
a = draft.add("A cache avoids repeated work.")  # a.label == "$a1"
b = draft.add("Caching has invalidation costs.")  # b.label == "$a2"
prepared = draft.submit(["Explain ", a, " and compare it with ", b, "."])
# With an existing public SDK Thread:
# result = thread.run(TextInput(prepared.text))
```

## Draft lifecycle

- Only the exact attached handle resolves; foreign, forged, deleted and expired
  handles are rejected. Identical quotes still have distinct identities.
- Successful `submit` freezes a `PreparedMessage` and clears the draft **before
  transport**. Validation failure preserves the draft for correction.
- `clear` also expires old handles. The next `add` starts at `$a1`; reused labels
  never reactivate old objects. Scope is the **user message**, since one running
  agent turn can receive multiple steering inputs.
- Removing `$a1` leaves `$a2` unchanged; the next attachment is `$a3`. Request
  parts can refer to handles in any order; there is no reorder operation.
- Retain the frozen snapshot for retry instead of resolving against a new draft.
  Resending repeats content and is not idempotent; reconcile uncertain acceptance.

## Text boundary and prototype limits

The model receives JSON containing request text, inline `quoted_text` parts and
unreferenced attachments. Generated labels and the registry are not sent. All raw
`$aN` strings remain literal, even with a matching attachment. A rich composer
would need explicit binding or handle insertion; automatic typed-token binding,
selection cards and cursor insertion are absent here. Labels would let one
free-form prompt address several selections without separate mini-editors.

`PROTOTYPE_MAX_SELECTIONS` (32) and `PROTOTYPE_MAX_PAYLOAD_BYTES` (1,000 UTF-8 bytes)
are demonstration choices, **not Codex product recommendations**. Each quote must
fit the byte cap at `add`; at `submit`, the complete JSON must also fit, including
request text, attachments, structure, escaping and repeated references. Thus an
accepted `add` does not guarantee an accepted `submit`: a 1,000-byte quote alone
exceeds the aggregate cap after JSON overhead. Rejection preserves the draft.
The cap bounds accepted serialized output, not temporary serialization work or
peak memory. Plain text without selections follows the existing SDK path.

History retains submitted quote text; expiry removes active client bindings.
JSON escaping preserves syntax, not a model authority or prompt-injection security
boundary. Live-model interpretation, compaction and model switching are untested.

See [DESIGN.md](DESIGN.md) for architecture and decisions,
[VALIDATION.md](VALIDATION.md) for historical evidence and reproduction commands,
and [UPSTREAM_COMMENT.md](UPSTREAM_COMMENT.md) for the unpublished comment draft
targeting [openai/codex#22677](https://github.com/openai/codex/issues/22677).
