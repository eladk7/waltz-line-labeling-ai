
from src.labels import reflect_tuple


CATALOG = {
    "L": [
        ("I", "O"),
        ("O", "I"),
        ("O", "+"),
        ("+", "I"),
        ("I", "-"),
        ("-", "O")
    ],

    "Y": [
        ("+", "+", "+"),
        ("-", "-", "-"),
        ("-", "I", "O"),
        ("O", "-", "I"),
        ("I", "O", "-")
    ],

   "Arrow": [
    ("+", "-", "-"),
    ("-", "+", "+"),
    ("I", "O", "+")
    ],

    "T": [
        ("O", "I", "O"),
        ("O", "I", "I"),
        ("-", "O", "I"),
        ("+", "O", "I")
    ]
}


def get_catalog(junction_type, reflection=False):
    if junction_type not in CATALOG:
        raise ValueError(
            f"Unknown junction type: {junction_type}"
        )

    labels = CATALOG[junction_type]

    if reflection:
        return [reflect_tuple(t) for t in labels]

    return list(labels)


if __name__ == "__main__":
    expected_counts = {
        "L": 6,
        "Y": 5,
        "Arrow": 3,
        "T": 4
    }

    for name, count in expected_counts.items():
        catalog = get_catalog(name)

        assert len(catalog) == count
        assert len(set(catalog)) == count

        print(f"{name}: {len(catalog)} legal tuples")

    print("\nOriginal Y:")
    print(get_catalog("Y"))

    print("\nReflected Y:")
    print(get_catalog("Y", reflection=True))

    print("\nAll catalog tests passed!")
