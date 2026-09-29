"""Compile explicit, draft-local selection handles into an immutable text snapshot."""

import json
from collections.abc import Sequence
from dataclasses import dataclass

MAX_SELECTIONS = 32
MAX_PAYLOAD_BYTES = 1000


@dataclass(frozen=True, eq=False)
class SelectionRef:
    """Captured quote with a display label; only this exact object can be referenced."""

    label: str
    content: str


@dataclass(frozen=True)
class PreparedMessage:
    """A completed payload that can be retried without consulting another draft."""

    text: str


class SelectionDraft:
    """Own the selections for one message, resetting only after successful compilation."""

    def __init__(self) -> None:
        self._selections: list[SelectionRef] = []
        self._next_id = 1

    def add(self, content: str) -> SelectionRef:
        """Capture a bounded quote without renumbering existing labels."""
        if not isinstance(content, str):
            raise TypeError("selection content must be a string")
        if len(self._selections) >= MAX_SELECTIONS:
            raise ValueError("a draft can attach at most 32 selections")
        if len(content.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            raise ValueError("selection content exceeds 1000 UTF-8 bytes")
        ref = SelectionRef(f"$a{self._next_id}", content)
        self._selections.append(ref)
        self._next_id += 1
        return ref

    def remove(self, ref: SelectionRef) -> None:
        """Delete a currently attached handle; preserve other labels and their gaps."""
        for index, selection in enumerate(self._selections):
            if selection is ref:
                del self._selections[index]
                return
        raise ValueError("selection reference is not attached to this draft")

    def clear(self) -> None:
        """Begin a fresh message; reused labels never reactivate previous objects."""
        self._selections.clear()
        self._next_id = 1

    def submit(self, parts: Sequence[str | SelectionRef]) -> PreparedMessage:
        """Compile explicit nodes, preserving raw text and whitespace without expansion."""
        if isinstance(parts, (str, bytes)) or not isinstance(parts, Sequence):
            raise TypeError("parts must be a sequence of strings and selection references")
        request: list[dict[str, str]] = []
        referenced: set[int] = set()
        for part in parts:
            if isinstance(part, str):
                request.append({"type": "text", "text": part})
            elif isinstance(part, SelectionRef):
                if not any(selection is part for selection in self._selections):
                    raise ValueError("selection reference is not attached to this draft")
                request.append({"type": "quoted_text", "text": part.content})
                referenced.add(id(part))
            else:
                raise TypeError("parts must contain only strings and selection references")

        if self._selections:
            attachments = [
                {"type": "quoted_text", "text": selection.content}
                for selection in self._selections
                if id(selection) not in referenced
            ]
            text = json.dumps(
                {"request": request, "attachments": attachments},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            if len(text.encode("utf-8")) > MAX_PAYLOAD_BYTES:
                raise ValueError("serialized selection payload exceeds 1000 UTF-8 bytes")
        else:
            text = "".join(part["text"] for part in request)
            if not text:
                raise ValueError("cannot submit an empty message")

        prepared = PreparedMessage(text)
        self.clear()
        return prepared
