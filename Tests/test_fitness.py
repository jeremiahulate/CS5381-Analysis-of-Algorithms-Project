import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolve.fitness import (
    FitnessWeights,
    EvaluationMetrics,
    compute_fitness,
)


def main() -> None:
    weights = FitnessWeights(
        w_score=0.5,
        w_survival=0.3,
        w_steps=0.2,
    )

    metrics = EvaluationMetrics(
        score=1000,
        survival_time=40,
        steps=150,
    )

    result = compute_fitness(metrics, weights)

    print(result.as_dict())


if __name__ == "__main__":
    main()