# Draft comment for openai/codex#22677

**Unpublished draft.** Target: [openai/codex#22677](https://github.com/openai/codex/issues/22677).
The planned fork branch is
[feature/turn-scoped-selection-refs](https://github.com/specialcowboy69/codex-selection-references/tree/feature/turn-scoped-selection-refs);
it is not public yet. Publication and refreshed validation must precede posting.

---

This overlaps with #22677's request to keep each selected quote associated with
its follow-up. A complementary lightweight interaction model is to give existing
selection cards temporary labels such as `$a1` and `$a2`, and let one free-form
prompt address several selections without requiring separate mini-editors:

```text
$a1  [A cache avoids repeated work.]
$a2  [Caching has invalidation costs.]

Explain $a1 and tell me whether it contradicts $a2.
```

Per-selection comments could still coexist with these references. Labels also
allow comparison or discussion of multiple quotes in a single question.

The proposed bindings belong to one **user-message draft**: an active agent turn
can accept several steering inputs, so its server turn ID is too broad.

- Start each draft at `$a1`. Bind explicit reference nodes by captured selection
  identity, not by searching label text or previous messages.
- Preserve labels after deletion, allowing gaps; new attachments take the next
  number so existing references never silently change their target.
- Expire bindings on successful compilation/send preparation or clearing the
  draft. Reused labels belong to new selections; old handles remain invalid.
- Keep raw `$aN` strings literal, including code and strings beside a matching
  attachment. A composer must explicitly bind typed occurrences or insert a rich
  reference when a label is clicked; there is no global token parser.
- Freeze the payload before transport. Retry that exact snapshot without
  consulting a newer draft; reconcile uncertain acceptance before resending.

The local prototype in `sdk/python/examples/17_turn_scoped_selections` demonstrates
this identity/resolution lifecycle and transport through the existing public
Python SDK `TextInput` and app-server `turn/start`. It compiles explicit handles
into inline quoted JSON text and includes unreferenced attachments. It changes
no SDK exports, Rust core or wire schemas.

It is **not a Desktop implementation**. The composer is absent from the public
checkout, as [the maintainer explains](https://github.com/openai/codex/discussions/16538).
Selection cards, click insertion and automatic typed-token binding are not
implemented. Quoted content persists in ordinary history; only active client
bindings expire. JSON escaping is a syntactic boundary, not a model authority or
prompt-injection security boundary, and no live-model semantic guarantee is made.

The demonstration caps remain 32 selections and 1,000 UTF-8 bytes, not product
recommendations. The aggregate submission cap includes JSON overhead, request
text, escaping and repeated references; accepted quotes can still yield a rejected
submission, preserving the draft. It bounds accepted output, not peak memory.

The historical validation record reports 25 unit cases and two local transport
tests using installed CLI `0.158.0-alpha.2.1` and a mock Responses endpoint. Those
results predate the current rebase/polish; `VALIDATION.md` retains the environment,
commands and unrelated full-SDK failures pending fresh validation. They do not
prove Desktop integration or live-model interpretation.

[#22670](https://github.com/openai/codex/issues/22670) is adjacent: it requests
visible selected context in sent messages/history. The prototype preserves quote
text through transport/resume but does not implement that history UI. Native
structural preservation would require a separate experimental v2 input design
with validation and replay/compaction coverage.
