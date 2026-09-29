# Selection-reference validation

Date: **2026-09-29**. Tested code: `048d43cea2d7c1ddfaecd9737d9d0e7b88338231`
on `feature/turn-scoped-selection-refs`, before this evidence-only commit.
Clean `origin/main` baseline: `65c3f40befaa213788ca7f97cc955ba996ffa3f5`.

Environment: Windows 11 (build 26200), Python **3.13.15**, uv **0.12.20**,
pytest **9.0.3**, Ruff **0.15.12**, installed `codex-cli 0.158.0-alpha.2.1`.
Both checkouts used the same checked-in SDK lockfile and a frozen dev-only sync.
`CODEX_EXEC_PATH` selected the installed CLI. It is not a same-source Bazel binary.

## Fresh results

| Check | Result |
| --- | --- |
| Targeted example and transport tests, run first | 27 passed in 20.86s |
| Full SDK Ruff check | Passed, exit 0 |
| Full SDK Ruff format check | Passed, 78 files already formatted |
| Initial full SDK suite | 284 passed, 41 skipped, 7 failed in 234.27s |
| Exact seven initial failures on clean baseline | 7 failed in 97.27s |
| Four packaging cases after putting uv on process PATH | 4 passed in 2.79s |
| Final full SDK suite with corrected PATH | **288 passed, 41 skipped, 3 failed** in 248.61s |
| Exact three final failures on baseline with corrected PATH | 3 failed in 78.02s |

The initial run invoked uv by its executable path, but four packaging cases spawn
`uv` by name and failed with `FileNotFoundError: [WinError 2]`. All four exact cases
of `tests/test_artifact_workflow_and_binaries.py::test_built_sdk_uses_explicit_release_versions`
reproduced on the baseline: `[0.154.0-0.147.0]`, `[0.154.0-0.153.0]`,
`[0.2.0b1-0.147.0]`, and `[0.2.0b1-0.153.0]`. Adding the uv executable directory
to the process PATH fixed preparation without changing code or dependencies.
The final counts above come from another complete execution, not inferred totals.

The remaining failures reproduce with matching assertions on the clean baseline:

- `tests/test_app_server_goal_operations.py::test_private_goal_operation_coalesces_runtime_continuations`:
  `objective_reached_model` is false; the installed runtime's model input lacks
  the expected `<objective>\nImprove benchmark coverage\n</objective>` string.
- `tests/test_artifact_workflow_and_binaries.py::test_root_format_driver_covers_all_formatter_groups`:
  the assertion expects individual `rustfmt` commands; `scripts/format.py` uses `cargo fmt`.
- `tests/test_mcp_conformance_fixtures.py::test_mcp_conformance_fixture_self_tests`:
  its nested suite reports **237 passed, 2 failed** on both checkouts. Failures are
  `scripts/mcp_conformance/test_codex_compliance.py::test_registration_commands_select_stdio_then_http_shapes`
  and `scripts/mcp_conformance/test_review_regressions.py::test_shipping_legacy_registration_preserves_the_reserved_protocol_environment`.
  Both compare `/opt/codex` with Windows-normalized `\opt\codex`.

The baseline remained at the exact baseline SHA with detached HEAD and a clean
tracked/untracked status before and after testing. The feature checkout was also
clean after both full runs: no source, test, dependency or generated-file drift.
The failing sources and SDK lockfile are identical between the two code revisions.
No product fixes occurred, so the fresh targeted results still apply to identical
code. Since the tested SHA, only documentation has changed. No feature regression was
observed in these checks; the full SDK suite is not green in this environment.

## Reproduction

Use Python 3.13.15 and put uv on PATH, including for child processes. From the
repository root, select the installed CLI; then run the Python checks from `sdk/python`:

```powershell
$env:CODEX_EXEC_PATH = (Get-Command codex).Source
Set-Location sdk/python
uv sync --only-group dev --frozen --python 3.13.15
uv run --only-group dev --frozen --no-sync pytest tests/test_selection_refs_example.py tests/test_selection_refs_transport.py
uv run --only-group dev --frozen --no-sync ruff check --output-format=github .
uv run --only-group dev --frozen --no-sync ruff format --check .
uv run --only-group dev --frozen --no-sync pytest
```

Create an isolated worktree at the recorded baseline revision, sync with the same
Python and lockfile, and retain the same PATH and `CODEX_EXEC_PATH`. From its
`sdk/python` directory, compare precisely the final failing cases:

```powershell
$failed = @(
    'tests/test_app_server_goal_operations.py::test_private_goal_operation_coalesces_runtime_continuations'
    'tests/test_artifact_workflow_and_binaries.py::test_root_format_driver_covers_all_formatter_groups'
    'tests/test_mcp_conformance_fixtures.py::test_mcp_conformance_fixture_self_tests'
)
uv run --only-group dev --frozen --no-sync pytest @failed
```

## Scope and limitations

The 27 focused cases cover draft ownership, expiry/reset, repeated labels, raw
text/code, hostile delimiters, UTF-8/serialized bounds and rejected drafts. Two
transport cases use the installed app-server with local mocked Responses, temporary
CODEX_HOME and a read-only temporary workspace, including restart/resume and explicit resend.

These use the Python commands from `.github/workflows/sdk.yml`, but do not establish
full CI equivalence: CI runs Linux with its same-source Bazel CLI and pins uv 0.11.3.
No Rust or Bazel files changed. The earlier `just fmt` attempt could not start Rust
and Bazel formatters because `cargo` and `dotslash` were absent; repository-wide
format/build success is not claimed by these Python checks.

The 41 skips include existing opt-in real-inference tests. Real Desktop UI,
automatic typed-token binding, real model inference/interpretation, live compaction
and model switching were not tested. Quote text remains in normal history; this
prototype guarantees deterministic draft-handle expiry, not model forgetting.
