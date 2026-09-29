# Turn-scoped selection references (client prototype)

This example demonstrates draft-local `$a1`, `$a2` labels using the public SDK
transport. **It does not modify Codex Desktop or implement its Add to chat UI.**
The association is structural in the client and compiled before sending. The
existing model boundary is still text; no native selection protocol is invented.

Run the offline demonstration from the repository root (no account or model call):

```shell
python sdk/python/examples/17_turn_scoped_selections/sync.py
```

The local module API is intentionally not exported from `openai_codex`:

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

`submit` freezes the payload and clears the draft **before transport**, transferring
ownership to the prepared message. After a network failure, retain that snapshot;
do not look up its old labels in a new draft. Resending a snapshot repeats its
content, not an idempotent server operation: reconcile uncertain acceptance first.

`clear` also invalidates all old handles. The next `add` starts at `$a1`. Removing
`$a1` leaves `$a2` unchanged; the next attachment is `$a3`. This deliberate gap
prevents a previously written reference from silently changing its target.
There is no reorder operation. Request parts can refer to selections in any order.

The model receives escaped JSON with request text and inline `quoted_text` parts,
plus unreferenced attachments. Generated labels and the registry are not sent.
Literal occurrences in user text or quote content are preserved, including `$a1`.
There is **no parser**, including when a matching attachment exists. A real rich
composer must bind an occurrence explicitly or insert its handle when clicked;
automatic binding of typed `$aN` is not demonstrated here.

At most 32 selections can be attached. Each captured string is capped at 1,000
UTF-8 bytes; the complete compiled payload with attachments is also capped at
1,000 bytes, including repeated references and JSON escaping. Rejection preserves
the draft. Ordinary text without selections follows the existing SDK path.

## Architecture verified at the public baseline

Baseline: `d515b2f85ec1b24a4b5ec3fbd86db27fd51aea3b`.

| File (relative to repository root) | Responsibility |
| --- | --- |
| `codex-rs/tui/src/transcript_view/input.rs` | Public transcript selection actions, principally copying |
| `codex-rs/tui/src/app/owned_transcript.rs` | Dispatches those actions to clipboard/browser |
| `codex-rs/tui/src/bottom_pane/chat_composer.rs` | TUI drafts, paste placeholders and submission lifecycle |
| `codex-rs/tui/src/ide_context/prompt.rs` | Renders current IDE context as prefixed input text |
| `sdk/python/src/openai_codex/_inputs.py` | `TextInput` to existing wire text input |
| `codex-rs/app-server-protocol/src/protocol/v2/turn.rs` | `TurnStartParams`, `UserInput`, conversion to core |
| `codex-rs/app-server/src/request_processors/turn_processor.rs` | `start_or_steer_turn` dispatch |
| `codex-rs/protocol/src/user_input.rs` | Text and UI-only `TextElement` spans |
| `codex-rs/protocol/src/models.rs` | Text to model input; discards UI-only spans |
| `codex-rs/core/src/state/additional_context.rs` | Context snapshot/diff storage; unsuitable for ephemeral aliases |
| `codex-rs/core/src/session/rollout_reconstruction.rs` | Replays persisted model message envelopes |
| `codex-rs/core/src/compact.rs` | Compacts historical text |

The exact Desktop selection-to-composer serialization cannot be traced in this
checkout. Its source is absent; an [OpenAI maintainer confirms the boundary](https://github.com/openai/codex/discussions/16538).
An [existing report](https://github.com/openai/codex/issues/42719) shows selected-text
fallback text in Web, but is not proof of Desktop's internal representation.
The TUI `/ide` bridge fetches current editor state on submission; it is a distinct
feature, not accumulated Add to chat attachments.

## Coverage and boundaries

| Scenario | Contract / verification target |
| --- | --- |
| One/many quotes, same content twice | Distinct handles, exact captured content |
| New message, different conversation | Fresh labels; old/foreign handles rejected |
| Delete then add | Stable IDs with gaps; removed references fail |
| Clear/cancel | Old handles expire; next label starts at one |
| Validation failure | Keep draft and handles for correction |
| Retry/regeneration | Explicit immutable compiled snapshot; no automatic resend |
| History/resume | Ordinary quote content persists; no registry restored |
| Compaction/model change | No client lookup depends on either; no model guarantee claimed |
| Raw `$a1` and code | Preserved literally even with attached selections |
| Unicode/delimiters/size limits | JSON round-trip and bounded UTF-8 payload |
| Reorder/click/typed binding | UI absent; not implemented |

History can still contain old quote content. Expiry means removal of **active
client bindings**, not erasure from history or prevention of model inference.
JSON escaping preserves data boundaries syntactically, not an authority or
prompt-injection security boundary. No live-model semantic evaluation is claimed.

OpenAI's smallest Desktop change would add a draft-owned selection list/counter,
secondary labels on existing cards, explicit rich reference nodes, and compilation
at send time. For native structured server/history support, a separate experimental
v2 selection-and-reference input design would need validation, schema generation,
UI event conversion and replay/compaction tests. Existing `TextElement`, `Mention`
and `additionalContext` are not substitutes for that design. Scope should be the
**user message**, since one running agent turn can receive multiple steering inputs.

See [DESIGN.md](DESIGN.md) for decisions and execution checklist, and
[UPSTREAM_ISSUE.md](UPSTREAM_ISSUE.md) for the unpublished proposal.
