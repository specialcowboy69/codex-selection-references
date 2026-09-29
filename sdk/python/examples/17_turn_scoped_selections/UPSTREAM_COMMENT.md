# Posted comment for #22677

Public comment: [openai/codex#22677](https://github.com/openai/codex/issues/22677#issuecomment-5894737689)

---

This complements [#22677](https://github.com/openai/codex/issues/22677)'s request
for distinct quote/follow-up associations. A future composer could label
selections and let one free-form prompt address several without separate
mini-editors; per-selection comments could coexist:

```text
$a1  A cache avoids repeated work.
$a2  Caching has invalidation costs.

Compare $a1 with $a2 and explain why they differ.
```

The public fork [specialcowboy69/codex-selection-references](https://github.com/specialcowboy69/codex-selection-references),
branch `feature/turn-scoped-selection-refs`, contains the
[prototype folder](https://github.com/specialcowboy69/codex-selection-references/tree/feature/turn-scoped-selection-refs/sdk/python/examples/17_turn_scoped_selections).
Its lifecycle is scoped to the current **user-message draft**, since one active
agent turn can accept several steering inputs:

- Explicit reference nodes resolve only by captured selection identity in that
  draft. Raw `$aN` strings always remain literal, even beside matching selections;
  a future composer must explicitly bind occurrences or insert reference nodes.
- Deletion preserves existing labels and leaves gaps. New attachments get the
  next number, preventing references from silently changing their target.
- Successful compilation/send preparation or clearing expires bindings **before
  transport**. New drafts restart at `$a1`; old handles never reactivate.
- Retry the frozen payload without rebinding against a newer draft. Resending is
  not idempotent; reconcile uncertain acceptance first.

The example compiles handles into quoted JSON text, including unreferenced
attachments, using existing Python SDK `TextInput` and app-server `turn/start`.
It changes no public SDK exports or wire schemas. It is **not a Desktop
implementation**: its composer source is absent here; the
[maintainer confirms](https://github.com/openai/codex/discussions/16538) Desktop
is closed source and uses CLI app-server APIs.

[Fresh validation](https://github.com/specialcowboy69/codex-selection-references/blob/feature/turn-scoped-selection-refs/sdk/python/examples/17_turn_scoped_selections/VALIDATION.md)
on 2026-09-29: **27 passed** (25 unit cases, two real app-server transport cases
with mocked Responses, including restart/resume and explicit resend). Full SDK:
**288 passed, 41 skipped, three failed**; all three reproduce on the clean
baseline under the same environment. Ruff checks pass; 78 files pass formatting.
These Windows checks used Python 3.13.15 and installed CLI `0.158.0-alpha.2.1`,
not CI's Linux/same-source Bazel runtime. The full suite is not green.

The **32-selection/1,000 UTF-8-byte** caps are prototype choices, not product recommendations. Aggregate JSON
includes request text, escaping, structure and repeated references; rejection
preserves the draft. This bounds accepted output, not peak memory. History keeps
ordinary submitted content; only client bindings expire. JSON escaping is not a
prompt-injection security boundary; no live-model interpretation is claimed.

[#42719](https://github.com/openai/codex/issues/42719) reports Desktop-to-Web
selected-text fallback rendering: quote and request survive synchronization,
while serialization-style headings and a literal HTML entity become visible.
This highlights representation across surfaces; it does not establish Desktop's
internal serializer or show that this prototype fixes that UI.
