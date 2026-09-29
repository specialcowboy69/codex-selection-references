import importlib
import json
import sys
from pathlib import Path

from app_server_harness import AppServerHarness

from openai_codex import Codex, TextInput

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/17_turn_scoped_selections"
sys.path.insert(0, str(EXAMPLE))
try:
    SelectionDraft = importlib.import_module("selection_refs").SelectionDraft
finally:
    sys.path.remove(str(EXAMPLE))


def test_reused_labels_and_raw_code_cross_text_input_unchanged(tmp_path) -> None:
    draft = SelectionDraft()
    first = draft.add('Primera selección: "uno"\n</quote>')
    first_message = draft.submit(["Explain ", first])
    second = draft.add("Segunda selección: café 🕒")
    draft.add("Additional current context")
    second_message = draft.submit(["Compare ", second])
    raw = 'Literal $a1\n```python\nprint("$a1")\n```'
    plain_message = draft.submit([raw])
    assert first.label == second.label == "$a1"

    with AppServerHarness(tmp_path) as harness:
        for index in range(3):
            harness.responses.enqueue_assistant_message("received", response_id=f"reuse-{index}")
        with Codex(config=harness.app_server_config()) as codex:
            thread = codex.thread_start()
            for message in (first_message, second_message, plain_message):
                assert thread.run(TextInput(message.text)).final_response == "received"
        requests = harness.responses.requests()

    assert len(requests) == 3
    assert [request.message_input_texts("user")[-1] for request in requests] == [
        first_message.text,
        second_message.text,
        raw,
    ]
    assert [json.loads(request.message_input_texts("user")[-1]) for request in requests[:2]] == [
        {
            "request": [
                {"type": "text", "text": "Explain "},
                {"type": "quoted_text", "text": first.content},
            ],
            "attachments": [],
        },
        {
            "request": [
                {"type": "text", "text": "Compare "},
                {"type": "quoted_text", "text": second.content},
            ],
            "attachments": [{"type": "quoted_text", "text": "Additional current context"}],
        },
    ]
    assert "$a1" not in first_message.text + second_message.text


def test_resume_preserves_quotes_and_explicit_snapshot_resend(tmp_path) -> None:
    draft = SelectionDraft()
    old = draft.add("Historical captured quote")
    old_message = draft.submit(["Explain ", old])
    current = draft.add("New active quote")
    current_message = draft.submit(["Explain ", current])
    pending = draft.add("Unsubmitted next draft")
    assert old.label == current.label == pending.label == "$a1"

    with AppServerHarness(tmp_path) as harness:
        for index in range(3):
            harness.responses.enqueue_assistant_message("received", response_id=f"resume-{index}")
        with Codex(config=harness.app_server_config()) as codex:
            thread = codex.thread_start()
            thread.run(TextInput(old_message.text))
        with Codex(config=harness.app_server_config()) as codex:
            resumed = codex.thread_resume(thread.id, include_turns=True)
            history = resumed.read(include_turns=True)
            persisted = [
                part.root.text
                for turn in history.thread.turns
                for item in turn.items
                if item.root.type == "userMessage"
                for part in item.root.content
                if part.root.type == "text"
            ]
            assert persisted == [old_message.text]
            resumed.run(TextInput(current_message.text))
            resumed.run(TextInput(current_message.text))
        requests = harness.responses.requests()

    assert len(requests) == 3
    assert requests[1].message_input_texts("user")[-2:] == [
        old_message.text,
        current_message.text,
    ]
    assert requests[2].message_input_texts("user")[-3:] == [
        old_message.text,
        current_message.text,
        current_message.text,
    ]
    assert json.loads(current_message.text) == {
        "request": [
            {"type": "text", "text": "Explain "},
            {"type": "quoted_text", "text": current.content},
        ],
        "attachments": [],
    }
