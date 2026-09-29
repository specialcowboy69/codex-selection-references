# Validation record

Date: 2026-09-29. Public baseline: `d515b2f85ec1b24a4b5ec3fbd86db27fd51aea3b`.
Windows; installed app-server `codex-cli 0.158.0-alpha.2.1`, not a Rust build of this
checkout. Python 3.14.4 for initial scoped checks; Python 3.13.15 plus the checked-in
SDK lockfile for generation and the final SDK run. No real model calls were made.

## New deliverable

- 25 unit cases pass; two transport tests pass (27 total, independently reviewed).
- The cap regression was observed red (four failures) before reducing the bound,
  then green. Original missing-module runs established initial test discovery.
- SDK transport uses the actual installed app-server and existing local Responses
  mock, temporary CODEX_HOME and a read-only temporary workspace. It verifies current
  content, repeated labels, raw code, process restart/resume and explicit resend.
- Ruff check/format pass on changed Python; strict mypy targeting Python 3.10 passes
  on both example source files. `compileall` and the offline demonstration pass.
- `git diff --check` passes. No Rust, generated API or schema files changed.

PowerShell reproduction from the repository root, with uv and a compatible CLI:

```powershell
$env:CODEX_EXEC_PATH = (Get-Command codex).Source
uv run --frozen --project sdk/python --python 3.13 --only-group test python -m pytest -o addopts='' sdk/python/tests/test_selection_refs_example.py sdk/python/tests/test_selection_refs_transport.py -q
uv run --frozen --project sdk/python --python 3.13 --only-group test python -m pytest -o addopts='' sdk/python/tests -q
python sdk/python/examples/17_turn_scoped_selections/sync.py
```

## Existing SDK failures investigated separately

Final locked SDK run: **288 passed, 41 skipped, 3 failed** in 184.05 seconds.

These tests reproduce without importing the new example; their source and the
production source they test are unchanged from the public baseline:

- `tests/test_app_server_goal_operations.py::test_private_goal_operation_coalesces_runtime_continuations`:
  expects an `<objective>` string in model input; the installed runtime does not
  produce that expected string. This is runtime/baseline compatibility evidence,
  not a defect attributed to this prototype.
- `tests/test_artifact_workflow_and_binaries.py::test_root_format_driver_covers_all_formatter_groups`:
  expects individual `rustfmt` commands; existing `scripts/format.py` uses `cargo fmt`.
- `tests/test_mcp_conformance_fixtures.py::test_mcp_conformance_fixture_self_tests`:
  its nested suite has 237 passes and two Windows path assertion failures:
  `test_registration_commands_select_stdio_then_http_shapes` and
  `test_shipping_legacy_registration_preserves_the_reserved_protocol_environment`.
  Both compare `/opt/codex` with the Windows-normalized `\opt\codex`.

The first full run on Python 3.14 had 286 passes, 41 skips and four failures. Its
fourth failure was `test_generated_files_are_up_to_date`: initially a missing
`datamodel-code-generator==0.31.2`, then incompatibility with Python 3.14. It passes
on Python 3.13 with the locked test dependencies; no generated files drifted.

`just fmt` was run: Python and Just formatting completed, but Rust and Bazel
formatters could not start because `cargo` and `dotslash` are absent. Scoped Python
checks pass; a full repository format/build success is not claimed. Incidental
line-ending-only formatter changes to `justfile` were restored to baseline.

The skipped tests include existing opt-in real-inference tests. Desktop UI,
automatic typed-token binding, actual model interpretation, live compaction and
model-switch behavior are not validated here. History keeps quote text normally;
the guarantee is deterministic draft-handle expiry, not model forgetting.
