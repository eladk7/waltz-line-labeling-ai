
def global_to_local(label, is_first_endpoint):
    if label in ("+", "-"):
        return label

    if label == "R":
        return "O" if is_first_endpoint else "I"

    if label == "L":
        return "I" if is_first_endpoint else "O"

    raise ValueError(f"Invalid global label: {label}")


def local_to_global(label, is_first_endpoint):
    if label in ("+", "-"):
        return label

    if label == "O":
        return "R" if is_first_endpoint else "L"

    if label == "I":
        return "L" if is_first_endpoint else "R"

    raise ValueError(f"Invalid local label: {label}")


def reflect_tuple(labels):
    reflection = {
        "I": "O",
        "O": "I",
        "+": "+",
        "-": "-"
    }

    return tuple(reflection[label] for label in labels)


if __name__ == "__main__":
    for label in ["R", "L", "+", "-"]:
        first = global_to_local(label, True)
        second = global_to_local(label, False)

        print(f"{label}: A={first}, B={second}")

        assert local_to_global(first, True) == label
        assert local_to_global(second, False) == label

    original = ("I", "O", "-")
    reflected = reflect_tuple(original)

    print("\nOriginal:", original)
    print("Reflected:", reflected)

    assert reflect_tuple(reflected) == original

    print("\nAll tests passed!")
