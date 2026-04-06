# Evaluator and Metrics Computation

## Overview

The evaluator simulates Pacman runs to score candidates. Uses deterministic stub for fairness/reproducibility.

## Metrics Computed

- **Score**: Based on code structure (if/else counts, refs to "ghost"/"food").
- **Survival Time**: Rewards conditionals and state handling.
- **Steps**: Penalizes bloated code.

## Scoring Formula

```
score = 150 + 12*lines + 30*if_count + 15*elif_count + 10*else_count + 18*return_count + 25*ghost_refs + 20*food_refs + 8*state_refs + hash_bonus
survival_time = 5.0 + 0.35*lines + 1.5*if_count + 0.75*elif_count + 0.5*else_count + 1.25*ghost_refs + 0.2*state_refs + hash_bonus
steps = 60 + 5*lines + (chars/18) + 2*comment_count + hash_penalty
```

## Deterministic Hash

Adds small variation from SHA256 of code for realism without randomness.

## Pseudocode

```python
def evaluate_stub(code):
    lines = [l for l in code.splitlines() if l.strip()]
    if_count = code.lower().count("if ")
    # ... compute as above
    return {"score": score, "survival_time": survival_time, "steps": steps}
```

## Example

Code: "if ghost: run_away"

- Score: ~200
- Survival: ~8.0
- Steps: ~70

## Code Snippet (from evaluator.py)

```python
def evaluate(self, candidate):
    code = candidate.code.strip()
    # ... feature extraction
    return EvaluationMetrics(score=score, survival_time=survival_time, steps=steps)
```
