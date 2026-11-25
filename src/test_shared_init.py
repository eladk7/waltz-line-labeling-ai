import random
from src.loader import load_csp
from src.hill_climbing import random_assignment
from src.genetic_algorithm import random_chromosome, decode

csp = load_csp("instances/cube.json")

for seed in [42, 43, 44, 45, 46]:
    hc = random_assignment(csp, random.Random(seed))
    ga = decode(csp, random_chromosome(csp, random.Random(seed)))

    assert hc == ga, f"Mismatch: seed={seed}"
    print(f"Seed {seed}: PASS")

print("All shared initialization tests passed!")
