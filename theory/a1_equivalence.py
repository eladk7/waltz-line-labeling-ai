
from itertools import product


def check_equivalence(catalog, labels):
    c12 = {(a, b) for a, b, c in catalog}
    c13 = {(a, c) for a, b, c in catalog}
    c23 = {(b, c) for a, b, c in catalog}

    reconstructed = set()

    for a, b, c in product(labels, repeat=3):
        if (
            (a, b) in c12
            and (a, c) in c13
            and (b, c) in c23
        ):
            reconstructed.add((a, b, c))

    original = set(catalog)
    extra = reconstructed - original

    return original == reconstructed, reconstructed, extra


catalogs = {
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


labels = ["+", "-", "I", "O"]

for name, catalog in catalogs.items():
    equivalent, reconstructed, extra = check_equivalence(
        catalog, labels
    )

    print(f"\nJunction: {name}")
    print(f"Original tuples: {len(catalog)}")
    print(f"Reconstructed tuples: {len(reconstructed)}")
    print(f"Equivalent: {equivalent}")
    print(f"Extra tuples: {sorted(extra)}")


# Artificial counterexample
counterexample = [
    (0, 0, 0),
    (0, 1, 1),
    (1, 0, 1),
    (1, 1, 0)
]

equivalent, reconstructed, extra = check_equivalence(
    counterexample, [0, 1]
)

print("\nArtificial counterexample")
print(f"Original tuples: {len(counterexample)}")
print(f"Reconstructed tuples: {len(reconstructed)}")
print(f"Equivalent: {equivalent}")
print(f"Extra tuples: {sorted(extra)}")
