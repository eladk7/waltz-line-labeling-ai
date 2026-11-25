from itertools import product


def check_equivalence(catalog):
    labels = ["+", "-", "I", "O"]

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

    return reconstructed == set(catalog)


catalog_y = [
    ("+", "+", "+"),
    ("-", "-", "-"),
    ("-", "I", "O"),
    ("O", "-", "I"),
    ("I", "O", "-")
]

print("Y equivalence:", check_equivalence(catalog_y))