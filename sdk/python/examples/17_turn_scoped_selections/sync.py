"""Demonstrate selection compilation offline, without starting Codex or a model."""

from selection_refs import SelectionDraft


def main() -> None:
    draft = SelectionDraft()
    first = draft.add("A cache avoids repeated work.")
    second = draft.add("Caching has invalidation costs.")
    print(f"Message 1: {first.label} / {second.label}")
    prepared = draft.submit(["Explain ", first, " and compare it with ", second, "."])
    print(prepared.text)

    current = draft.add("Fresh context for the next message.")
    print(f"Message 2: {current.label}")
    try:
        draft.submit(["This old reference must fail: ", first])
    except ValueError:
        print("Previous message's reference rejected; current draft preserved.")
    print(draft.submit(["Explain ", current]).text)
    print(draft.submit(['Literal shell code: echo "$a1"']).text)


if __name__ == "__main__":
    main()
