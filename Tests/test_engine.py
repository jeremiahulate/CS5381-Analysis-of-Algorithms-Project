import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolve.engine import run_evolution
from src.evolve.evaluator import DeterministicStubPacmanEvaluator
from src.evolve.fitness import FitnessWeights


def main() -> None:
    initial_code = """
function quicksort(A)
    if length(A) <= 1
        return A
    choose pivot
    left = elements less than pivot
    right = elements greater than pivot
    return quicksort(left) + pivot + quicksort(right)
""".strip()

    evaluator = DeterministicStubPacmanEvaluator()
    weights = FitnessWeights(
        w_score=0.5,
        w_survival=0.3,
        w_steps=0.2,
    )

    result = run_evolution(
        initial_code=initial_code,
        evaluator=evaluator,
        weights=weights,
        generations=5,
        population_size=4,
        selection_k=2,
        mutation_mode="random",
        language="python",
        seed=42,
    )

    print("History:")
    for item in result.history:
        print(
            {
                "generation": item.generation,
                "best_generation_fitness": item.best_generation_fitness,
                "best_so_far_fitness": item.best_so_far_fitness,
                "best_score": item.best_score,
                "best_survival_time": item.best_survival_time,
                "best_steps": item.best_steps,
            }
        )

    print("\nBest overall:")
    print(result.best_overall.fitness_result.as_dict())
    print("\nBest code:")
    print(result.best_overall.candidate.code)


if __name__ == "__main__":
    main()