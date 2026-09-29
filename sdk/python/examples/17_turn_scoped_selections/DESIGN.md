# Selection reference design and public architecture

Investigated public baseline: `d515b2f85ec1b24a4b5ec3fbd86db27fd51aea3b`.
Desktop's composer is absent; an [OpenAI maintainer confirms the boundary](https://github.com/openai/codex/discussions/16538).
Its exact selection serializer cannot be traced here. This client example uses
existing Python SDK `TextInput` and app-server `turn/start`, without changing
SDK exports, generated schemas, server state or a persistent alias registry.

## Decisions

`SelectionDraft` owns immutable identity-based handles and a monotonic label
counter. Stable labels with deletion gaps prevent existing questions from silently
changing targets. `submit` validates membership, compiles explicit nodes in place,
includes unreferenced attachments and clears only after successful compilation.
An immutable `PreparedMessage` carries retries independently of future drafts.
Raw strings are never scanned, including matching `$aN` tokens in code or quotes.
The [README](README.md) describes lifecycle, literal-text behavior and limits.

The 32-selection and 1,000-byte caps are prototype choices. The original review
reduced 4,096 bytes to 1,000 to keep this example's accepted context output small;
this does not establish a product contract. The aggregate JSON cap includes
overhead, so `add` acceptance need not imply `submit` acceptance. It bounds
accepted output, not temporary work or allocation; an allocation-budget redesign
and optional extra coverage are outside this polishing stage.

## Public paths inspected

Paths below are relative to `codex-rs/` unless marked otherwise.

| Path | Finding |
| --- | --- |
| `tui/src/transcript_view/input.rs`, `tui/src/app/owned_transcript.rs` | Selection actions primarily copy; no accumulated Add to chat collection found |
| `tui/src/bottom_pane/chat_composer.rs` | TUI drafts, paste placeholders and submission lifecycle |
| `tui/src/ide_context/prompt.rs` | Current IDE context fetched for submission, separate from captured selections |
| `sdk/python/src/openai_codex/_inputs.py` (repository root) | Existing `TextInput` serialization |
| `app-server-protocol/src/protocol/v2/turn.rs`, `app-server/src/request_processors/turn_processor.rs` | `UserInput`, `TurnStartParams` and turn dispatch |
| `protocol/src/user_input.rs`, `protocol/src/models.rs` | UI-only `TextElement` spans discarded on model conversion |
| `core/src/state/additional_context.rs` | Source-keyed snapshot/diff storage, unsuitable for ephemeral aliases |
| `core/src/session/rollout_reconstruction.rs`, `core/src/compact.rs` | Replay/compaction of ordinary submitted content |

A Desktop implementation would need draft-owned selections, secondary labels on
cards, explicit rich reference nodes and send-time compilation. A native v2 input
would additionally need validation, schema generation, UI conversion and
replay/compaction coverage. `TextElement`, `Mention` and `additionalContext` do not
provide this mechanism. Neither implementation is part of the example.

Unit tests cover identity, stable deletion, expiry, literal text, Unicode/escaping,
failed submission preservation and immutable snapshots. Transport tests inspect
actual local app-server requests and resumed history with a mock model endpoint.
These establish client resolution and transport, not Desktop UI, typed binding,
live-model semantics or a prompt-injection security boundary.
