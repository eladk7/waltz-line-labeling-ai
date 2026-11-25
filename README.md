# Waltz Line Labeling AI

## Assignment 2 - Artificial Intelligence

Implementation of 3D line labeling as a Constraint
Satisfaction Problem (CSP).

## Algorithms

- Waltz: AC-3, MRV, MAC and backtracking.
- Random Restart Hill Climbing with sideways moves.
- Genetic Algorithm with tournament selection,
  crossover, mutation and elitism.

## Requirements

- Python 3.14.6 (tested version)
- Tkinter
- Matplotlib

## Installation

```bash
git clone https://github.com/eladk7/waltz-line-labeling-ai.git
cd waltz-line-labeling-ai
python -m pip install matplotlib
```

## Run the GUI

```bash
python -m src.gui
```

The GUI supports loading and saving JSON instances,
algorithm selection, parameter configuration,
search visualization and event playback.

## Project Structure

- src/ - Algorithms, validation, GUI and experiments.
- instances/ - JSON problem instances.
- instances/benchmark/ - 15 benchmark instances.
- results/ - Raw experimental results.
- docs/ - Assignment reports.

## Correctness Tests

```bash
python -m src.catalog
python -m src.domains
python -m src.revise
python -m src.ac3
python -m src.waltz
python -m src.validation
python -m src.waltz_enumeration
python -m src.hill_climbing
python -m src.genetic_algorithm
python -m src.test_hc_limits
python -m src.test_shared_init
python -m src.test_gui_events
```

## Reproduce Experiments

Generate benchmark instances:

```bash
python -m src.generate_instances
```

Run a preliminary experiment:

```bash
python -m src.benchmark --smoke
```

Run the full benchmark:

```bash
python -m src.benchmark
```

Run the ambiguity experiment:

```bash
python -m src.ambiguity
```

## Experimental Configuration

- Benchmark instances: 15
- Main experiment: 225 runs
- Ambiguity experiment: 80 runs
- Benchmark seeds: 42-46
- Ambiguity seeds: 42-61
- Time limit: 10 seconds per run
- Objective evaluation limit: 100,000
- HC sideways limit: 10
- GA population: 100
- Crossover probability: 0.8
- Mutation probability: 0.02
- Tournament size: 3
- Elite size: 1

## Results

- results/benchmark.csv
- results/ambiguity.csv

## Experimental Environment

- Windows
- Python 3.14.6
- Intel Core i7-6500U @ 2.50 GHz
- 2 physical cores, 4 logical processors
- 11.9 GiB RAM

## Limitations

The benchmark uses synthetic CSP instances.
Local search failure does not prove unsatisfiability.
Results depend on the selected instances and parameters.

## AI Assistance

Language models were used for implementation assistance,
debugging, testing and documentation.
Correctness was evaluated using regression tests,
reference examples and experimental validation.
