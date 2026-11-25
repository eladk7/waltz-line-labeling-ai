import random
from dataclasses import dataclass, field, asdict
from statistics import mean, pstdev
from time import perf_counter

from src.loader import load_csp
from src.domains import build_domains
from src.validation import objective
from src.hill_climbing import random_assignment


# Chromosome representation

def edge_order(csp):
    return sorted(csp.edges)


def encode(csp, assignment):
    return tuple(assignment[e] for e in edge_order(csp))


def decode(csp, chromosome):
    return dict(zip(edge_order(csp), chromosome))


def random_chromosome(csp, rng):
    return encode(csp, random_assignment(csp, rng))


# Tournament selection

def tournament_selection(population, rng):
    candidates = rng.choices(population, k=3)
    best_h = min(h for _, h in candidates)

    winners = [
        chromosome
        for chromosome, h in candidates
        if h == best_h
    ]

    return rng.choice(winners)


# Single-point crossover

def crossover(parent1, parent2, p_c, rng):

    if len(parent1) < 2 or rng.random() >= p_c:
        return parent1, parent2

    cut = rng.randint(1, len(parent1) - 1)

    child1 = parent1[:cut] + parent2[cut:]
    child2 = parent2[:cut] + parent1[cut:]

    return child1, child2


# Independent mutation per gene

def mutate(csp, chromosome, p_m, rng):

    child = list(chromosome)

    for i, edge_id in enumerate(edge_order(csp)):

        domain = csp.edges[edge_id].domain

        if len(domain) <= 1:
            continue

        if rng.random() < p_m:

            alternatives = [
                label for label in domain
                if label != child[i]
            ]

            child[i] = rng.choice(alternatives)

    return tuple(child)


# Performance metrics

@dataclass
class GAStats:

    runtime_ms: float = 0.0
    objective_evaluations: int = 0
    constraint_checks: int = 0
    generations: int = 0
    best_h: int | None = None
    solved: bool = False
    stop_reason: str = ""
    history: list = field(default_factory=list)


def generation_metrics(population, generation):

    values = [h for _, h in population]

    return {
        "generation": generation,
        "population_size": len(population),
        "best_h": min(values),
        "average_h": mean(values),
        "std_h": pstdev(values),
        "unique_chromosomes": len({
            chromosome
            for chromosome, _ in population
        })
    }


# Genetic algorithm

def genetic_algorithm(
    csp,
    P=100,
    p_c=0.8,
    p_m=0.02,
    max_evaluations=100000,
    timeout=10.0,
    seed=42
):

    if not isinstance(P, int) or P < 2:
        raise ValueError("P must be an integer >= 2")

    if not 0 <= p_c <= 1:
        raise ValueError("Invalid crossover probability")

    if not 0 <= p_m <= 1:
        raise ValueError("Invalid mutation probability")

    if max_evaluations < 1 or timeout <= 0:
        raise ValueError("Invalid search budget")

    rng = random.Random(seed)
    start = perf_counter()
    domains = build_domains(csp)

    stats = GAStats()

    population = []
    best = None
    best_h = float("inf")

    def limit_reason():

        if perf_counter() - start >= timeout:
            return "TIME_LIMIT"

        if stats.objective_evaluations >= max_evaluations:
            return "EVALUATION_LIMIT"

        return None

    def evaluate(chromosome):

        nonlocal best, best_h

        h = objective(
            csp,
            decode(csp, chromosome),
            domains
        )

        stats.objective_evaluations += 1
        stats.constraint_checks += len(csp.junctions)

        if h < best_h:
            best = chromosome
            best_h = h

        return chromosome, h

    def finish(reason):

        stats.runtime_ms = (
            perf_counter() - start
        ) * 1000

        stats.best_h = (
            None if best is None else best_h
        )

        stats.solved = best_h == 0
        stats.stop_reason = reason

        solution = (
            None if best is None
            else decode(csp, best)
        )

        return solution, stats

    # Initial population

    for _ in range(P):

        reason = limit_reason()

        if reason:
            return finish(reason)

        chromosome = random_chromosome(csp, rng)
        individual = evaluate(chromosome)

        population.append(individual)

        if individual[1] == 0:

            if len(population) == P:
                stats.history.append(
                    generation_metrics(population, 0)
                )

            return finish("SOLVED")

    stats.history.append(
        generation_metrics(population, 0)
    )

    # Generational evolution

    while True:

        reason = limit_reason()

        if reason:
            return finish(reason)

        # Preserve one elite without mutation

        elite = min(
            population,
            key=lambda individual: individual[1]
        )

        new_population = [elite]

        while len(new_population) < P:

            reason = limit_reason()

            if reason:
                return finish(reason)

            parent1 = tournament_selection(
                population, rng
            )

            parent2 = tournament_selection(
                population, rng
            )

            children = crossover(
                parent1, parent2, p_c, rng
            )

            for child in children:

                if len(new_population) == P:
                    break

                reason = limit_reason()

                if reason:
                    return finish(reason)

                child = mutate(
                    csp, child, p_m, rng
                )

                individual = evaluate(child)

                new_population.append(individual)

                if individual[1] == 0:

                    if len(new_population) == P:

                        stats.generations += 1

                        stats.history.append(
                            generation_metrics(
                                new_population,
                                stats.generations
                            )
                        )

                    return finish("SOLVED")

        population = new_population

        stats.generations += 1

        stats.history.append(
            generation_metrics(
                population,
                stats.generations
            )
        )


def print_stats(stats):

    for name, value in asdict(stats).items():

        if name == "history":
            continue

        if isinstance(value, float):
            print(f"{name}: {value:.3f}")
        else:
            print(f"{name}: {value}")


# Tests

if __name__ == "__main__":

    csp = load_csp("instances/cube.json")
    rng = random.Random(42)

    print("\nTEST 1 - Chromosome representation")

    assignment = random_assignment(csp, rng)
    chromosome = encode(csp, assignment)

    assert len(chromosome) == 9
    assert decode(csp, chromosome) == assignment

    print("Chromosome:", chromosome)
    print("Edge order:", edge_order(csp))
    print("Encoding and decoding passed")


    print("\nTEST 2 - Tournament selection")

    population = [
        (("R",), 1),
        (("L",), 3),
        (("+",), 5)
    ]

    from unittest.mock import Mock

    mock_rng = Mock()
    mock_rng.choices.return_value = population
    mock_rng.choice.side_effect = lambda x: x[0]

    winner = tournament_selection(
        population, mock_rng
    )

    assert winner == ("R",)
    mock_rng.choices.assert_called_once_with(
        population, k=3
    )

    print("Best tournament participant selected")


    print("\nTEST 3 - Single-point crossover")

    parent1 = ("R",) * 9
    parent2 = ("+",) * 9

    child1, child2 = crossover(
        parent1, parent2, 1.0, rng
    )

    assert child1 != parent1
    assert child2 != parent2

    cut = child1.index("+")

    assert child1 == (
        parent1[:cut] + parent2[cut:]
    )

    assert child2 == (
        parent2[:cut] + parent1[cut:]
    )

    assert crossover(
        parent1, parent2, 0.0, rng
    ) == (parent1, parent2)

    print("Parent 1:", parent1)
    print("Parent 2:", parent2)
    print("Child 1:", child1)
    print("Child 2:", child2)
    print("Crossover passed")


    print("\nTEST 4 - Mutation and fixed genes")

    csp.edges["e1"].domain = ("R",)

    original = random_chromosome(csp, rng)

    mutated = mutate(
        csp, original, 1.0, rng
    )

    for i, edge_id in enumerate(edge_order(csp)):

        domain = csp.edges[edge_id].domain

        assert mutated[i] in domain

        if len(domain) == 1:
            assert mutated[i] == original[i]
        else:
            assert mutated[i] != original[i]

    assert mutate(
        csp, original, 0.0, rng
    ) == original

    print("Original:", original)
    print("Mutated:", mutated)
    print("Fixed genes preserved")


    print("\nTEST 5 - Solve cube")

    csp = load_csp("instances/cube.json")

    solution, stats = genetic_algorithm(csp, p_m=0.15)

    print("Solution:", solution)
    print_stats(stats)

    assert stats.solved
    assert objective(csp, solution) == 0


    print("\nTEST 6 - Reproducibility")

    solution2, stats2 = genetic_algorithm(csp, p_m=0.15)

    assert solution == solution2

    assert (
        stats.objective_evaluations
        == stats2.objective_evaluations
    )

    assert stats.history == stats2.history

    print("Same seed produces same results")


    print("\nTEST 7 - Immediate solution")

    for edge_id, label in solution.items():
        csp.edges[edge_id].domain = (label,)

    result, stats = genetic_algorithm(csp)

    assert stats.solved
    assert stats.objective_evaluations == 1
    assert stats.generations == 0

    print_stats(stats)


    print("\nTEST 8 - Evaluation limit")

    csp = load_csp("instances/cube.json")
    csp.edges["e7"].domain = ("-",)

    result, stats = genetic_algorithm(
        csp,
        P=20,
        max_evaluations=500
    )

    print_stats(stats)

    assert not stats.solved
    assert stats.objective_evaluations == 500
    assert stats.stop_reason == "EVALUATION_LIMIT"
    assert result["e7"] == "-"
    assert stats.best_h == objective(csp, result)


    print("\nTEST 9 - Elitism and generation metrics")

    history = stats.history

    assert len(history) == stats.generations + 1

    assert all(
        row["population_size"] == 20
        for row in history
    )

    assert all(
        1 <= row["unique_chromosomes"] <= 20
        for row in history
    )

    assert all(
        row["std_h"] >= 0
        for row in history
    )

    assert all(
        history[i]["best_h"]
        <= history[i - 1]["best_h"]
        for i in range(1, len(history))
    )

    print("Complete generations:", stats.generations)
    print("Initial generation:", history[0])
    print("Final complete generation:", history[-1])
    print("Best h never increased")


    print("\nTEST 10 - Time limit")

    result, stats = genetic_algorithm(
        csp,
        timeout=1e-12
    )

    assert stats.stop_reason == "TIME_LIMIT"

    print("Time limit enforced")


    print("\nTEST 11 - Invalid parameters")

    for params in [
        {"P": 1},
        {"p_c": -0.1},
        {"p_m": 1.1},
        {"max_evaluations": 0},
        {"timeout": 0}
    ]:

        try:
            genetic_algorithm(csp, **params)

        except ValueError:
            pass

        else:
            raise AssertionError(
                "Invalid parameters accepted"
            )

    print("Invalid parameters rejected")


    print("\nTEST 12 - Default configuration experiment")

    csp = load_csp("instances/cube.json")

    runs = []

    for seed in range(30):

        result, stats = genetic_algorithm(
            csp,
            seed=seed,
            max_evaluations=10000
        )

        assert result is not None
        assert stats.best_h == objective(csp, result)

        runs.append(stats)

    solved = sum(s.solved for s in runs)

    print(f"Solved: {solved}/30")
    print(f"Success: {100 * solved / 30:.2f}%")

    for metric in [
        "runtime_ms",
        "objective_evaluations",
        "constraint_checks",
        "generations",
        "best_h"
    ]:

        average = mean(
            getattr(s, metric) for s in runs
        )

        print(f"Average {metric}: {average:.3f}")

    print("\nAll genetic algorithm tests passed!")
