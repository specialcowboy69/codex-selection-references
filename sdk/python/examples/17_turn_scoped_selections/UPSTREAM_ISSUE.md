# Turn-scoped references for quoted/selected context in the composer

## Problem

When several selections are added to the composer, referring to “the first
fragment” or “the second annotation” is cumbersome and becomes ambiguous after
deletion or when the request discusses several fragments in a different order.

Please give each attached selection a small temporary label:

```text
$a1  [A cache avoids repeated work.]
$a2  [Caching has invalidation costs.]

Explain $a1 and tell me whether it contradicts $a2.
```

## Expected behavior

- Labels start at `$a1` for each new user-message draft.
- A reference binds only to a captured selection in that message.
- Sending or clearing the draft expires its bindings. A later `$a1` can refer to
  a new selection; previous messages must not be searched for a target.
- Plain `$a1` without an explicitly bound current selection remains ordinary text,
  including shell variables, code and templates.
- Prefer stable IDs after deletion, allowing gaps. Renumbering could silently
  redirect existing questions. New attachments use the next unused number.
- Clicking a label could insert a rich reference at the current cursor position.
  Secondary labels on existing selection cards would suffice; no composer redesign.
- No global state, memory feature, or persistent registry of active aliases.

“Turn-scoped” here means **user-message-scoped**: an active agent turn can accept
multiple user inputs, including steering, so its server turn ID is too broad.

## Proposed design

Keep captured selections and explicit reference nodes in the composer draft.
Validate node ownership by draft and selection identity rather than label text.
Freeze a submission before sending and expire its draft handles. A retry may reuse
that exact frozen payload; it must not rebind old labels against the next draft.
An ambiguous network result must be reconciled before retrying; duplicate sends
are not automatically idempotent.

A compatible first step can compile each reference into its captured quote at the
client boundary using existing text input. This avoids asking the model to resolve
recycled names from history. For native structural preservation through the server,
consider an experimental v2 input for selections plus explicit reference spans,
validated atomically per message. This is a proposal, not an existing protocol.

## Public architecture findings

Inspected `openai/codex` at `d515b2f85ec1b24a4b5ec3fbd86db27fd51aea3b`:

- Desktop composer source is not present. The maintainer answer in
  https://github.com/openai/codex/discussions/16538 confirms Desktop is closed source
  and built on public app-server APIs. Its precise selection serializer is unknown.
- Public TUI selection actions in `codex-rs/tui/src/transcript_view/input.rs` and
  dispatch in `tui/src/app/owned_transcript.rs` copy selections; no equivalent
  accumulated Add to chat annotation collection was found.
- `tui/src/ide_context/prompt.rs` renders current editor context into ordinary text;
  this is separate from captured composer selections.
- `app-server-protocol/src/protocol/v2/turn.rs` defines `TurnStartParams.input` and
  `UserInput`; `app-server/src/request_processors/turn_processor.rs` dispatches it.
- `protocol/src/user_input.rs` defines `TextElement` as display range/placeholder.
  `protocol/src/models.rs` discards these spans on model conversion, so assigning
  a `$a1` placeholder would not give the model a structural target.
- `core/src/state/additional_context.rs` performs source-keyed snapshot/diff
  updates; old emitted content remains historical context. It is not an ephemeral
  selection registry.
- History reconstruction and `core/src/compact.rs` preserve/compact ordinary text;
  a new native input type must account for these paths.

Paths above are relative to `codex-rs/` after the first full path.

## Local prototype

The local research branch includes
`sdk/python/examples/17_turn_scoped_selections/selection_refs.py`, a bounded Python
client prototype using existing `TextInput`, plus an offline demonstration and
unit/transport tests. No fork URL is claimed: this branch has not been published.

It associates selections with immutable identity-based handles, resolves explicit
reference nodes before submission, preserves literal text, rejects expired/foreign
handles, and clears the draft only after successful validation. It caps selections
at 32 and the serialized selection payload at 1,000 UTF-8 bytes.

This prototype is **not a Desktop implementation**. It does not automatically bind
typed `$aN`, render selection cards, or implement cursor insertion. It demonstrates
the public-client part without changing SDK exports, Rust core or wire schemas.
Structured associations become JSON-escaped text at the model boundary. Quoted
content persists in normal history; only active bindings expire. No guarantee
about an LLM's interpretation of historical or literal text is asserted.

## Related reports and contribution route

- https://github.com/openai/codex/issues/42719: selected-text fallback rendering
  across Desktop/Web; related representation concern, not this feature request.
- https://github.com/openai/codex/issues/22103: selection gesture and Add to chat.

A focused search found no exact duplicate; please link one if this is tracked.
Current `docs/contributing.md` accepts issue reports and design feedback rather
than external PRs. This proposal is prepared for human review and is not posted.

## Verification

The 25 unit cases and two real local app-server transport tests pass, including
label reuse, expiry, removal, literal code, Unicode, bounds, and resumed history.
The transport tests use CLI `0.158.0-alpha.2.1` and a mock Responses endpoint;
they do not establish live-model semantics or Desktop integration. Strict mypy,
Ruff and Python compilation pass. The locked SDK run has 288 passes, 41 skips and
three unrelated failures;
`VALIDATION.md` records their names, results, and exact runnable commands.
