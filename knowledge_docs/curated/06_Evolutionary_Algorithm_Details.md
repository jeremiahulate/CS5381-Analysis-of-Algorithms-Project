# Evolutionary Algorithm Details

## Overview

The evolutionary algorithm iteratively improves a baseline algorithm through generations of mutation, evaluation, and selection. Inspired by genetic algorithms, adapted for code optimization.

## Key Concepts

- **Population**: Set of candidate solutions (code strings).
- **Generation**: One iteration of mutation/evaluation/selection.
- **Mutation Modes**: "none", "random", "llm".
- **Selection**: Top-k based on fitness.

## Pseudocode

```
def run_evolution(baseline, generations, pop_size, k, mode):
    parents = [baseline]
    history = []
    for gen in 1..generations:
        candidates = generate_candidates(parents, pop_size, mode)
        evaluated = [evaluate(c) for c in candidates]
        fitnesses = [compute_fitness(e) for e in evaluated]
        best_fitness = max(fitnesses)
        history.append((gen, best_fitness))
        parents = select_top_k(candidates, fitnesses, k)
    return parents[0], history
```

## Mutation Strategies

- **None**: No change.
- **Random**: Syntax-safe mutations (add comment, replace token, insert line).
- **LLM**: Use retrieval + LLM for targeted changes.

## Selection

Rank by fitness (descending), keep top-k.

## Example Generation

Gen 1: Baseline fitness = 50
Gen 2: Mutated candidate fitness = 65 (selected)
Gen 3: Further mutation fitness = 78

## Code Snippet (from engine.py)

```python
def select_top_k(evaluated_candidates, k):
    ranked = sorted(evaluated_candidates, key=lambda x: x.fitness_result.fitness, reverse=True)
    return ranked[:k]
```
