# Fitness and Metrics

## Pacman Evaluation Metrics

The evaluator returns three metrics per candidate:

- **score**: Total points earned (food eaten, etc.).
- **survival_time**: Time survived in the game.
- **steps**: Number of actions taken (higher = more inefficient).

## Fitness Computation

Fitness combines metrics into one score for selection:

```
fitness = w_score * score + w_survival * survival_time - w_steps * steps
```

Where weights (w_score, w_survival, w_steps) sum to 1.0.

### Example Weights

- Balanced: w_score=0.5, w_survival=0.3, w_steps=0.2
- Score-focused: w_score=0.7, w_survival=0.2, w_steps=0.1

### Notes

- Higher fitness is better.
- All candidates evaluated with same settings for fairness.
- Weights tunable for different objectives (e.g., prioritize survival over score).

## Pseudocode

```python
def compute_fitness(metrics, weights):
    score_comp = weights.w_score * metrics.score
    survival_comp = weights.w_survival * metrics.survival_time
    steps_comp = weights.w_steps * metrics.steps
    return score_comp + survival_comp - steps_comp
```

## Example Output

For a candidate with score=200, survival=10.5, steps=50:

- With balanced weights: fitness ≈ 0.5*200 + 0.3*10.5 - 0.2\*50 = 100 + 3.15 - 10 = 93.15
