# Project Overview (AlgoChat)

## Goal

Improve a baseline algorithm automatically over multiple generations using evolutionary techniques.

## Evolutionary Loop

1. **Initialize**: Start with a user-provided baseline algorithm (e.g., a simple Pacman strategy).
2. **Generate Candidates**: Create mutated versions of the baseline (random or LLM-guided).
3. **Evaluate**: Run each candidate in the Pacman environment to collect metrics (score, survival time, steps).
4. **Compute Fitness**: Combine metrics into a single fitness score using weighted formula.
5. **Select Best**: Keep top-k candidates for the next generation.
6. **Repeat**: Iterate for N generations, logging progress and best solutions.

## Outputs

- Best fitness per generation (for plotting progress).
- Best final solution (code and metrics).
- Fitness vs. generation plot.
- Comparison across experiment modes (single-shot, random mutation, LLM-guided).

## Pseudocode for Evolution

```
def evolve_algorithm(baseline_code, generations, population_size, mutation_mode):
    parents = [baseline_code]
    for gen in 1 to generations:
        candidates = generate_mutations(parents, population_size, mutation_mode)
        evaluated = [evaluate(candidate) for candidate in candidates]
        fitness_scores = [compute_fitness(metrics) for metrics in evaluated]
        parents = select_top_k(candidates, fitness_scores, k=1)
        log_best_fitness(gen, max(fitness_scores))
    return best_candidate
```

## Example Baseline Algorithm

A simple Pacman strategy in Python:

```python
def pacman_agent(state):
    # Eat food if available
    if state.has_food_nearby():
        return "eat_food"
    # Run from ghosts
    elif state.ghosts_nearby():
        return "run_away"
    # Otherwise, move randomly
    else:
        return "move_randomly"
```
