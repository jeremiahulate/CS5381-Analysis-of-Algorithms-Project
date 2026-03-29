import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolve.engine import run_evolution
from src.evolve.evaluator import DeterministicStubPacmanEvaluator
from src.evolve.fitness import FitnessWeights


EXAMPLES = [
    {
        "name": "Pacman Python",
        "language": "python",
        "initial_code": """
def pacman_agent(state):
    if state.isGhostNearby():
        return "run_away"
    return "eat_food"
""".strip(),
    },
    {
        "name": "Quicksort Pseudocode",
        "language": "text",
        "initial_code": """
function quicksort(A)
    if length(A) <= 1
        return A
    choose pivot
    left = elements less than pivot
    right = elements greater than pivot
    return quicksort(left) + pivot + quicksort(right)
""".strip(),
    },
    {
        "name": "Pathfinding Pseudocode",
        "language": "text",
        "initial_code": """
function find_path(graph, start, goal)
    open_set = [start]
    while open_set not empty
        current = node with lowest cost
        if current == goal
            return path
        expand neighbors
""".strip(),
    },
    {
        "name": "Matrix Multiply Pseudocode",
        "language": "text",
        "initial_code": """
function matrix_multiply(A, B)
    for i in rows of A
        for j in columns of B
            C[i][j] = 0
            for k in columns of A
                C[i][j] += A[i][k] * B[k][j]
    return C
""".strip(),
    },
]


def main() -> None:
    evaluator = DeterministicStubPacmanEvaluator()
    weights = FitnessWeights(
        w_score=0.5,
        w_survival=0.3,
        w_steps=0.2,
    )

    for example in EXAMPLES:
        print("\n" + "=" * 70)
        print("TEST CASE:", example["name"])
        print("=" * 70)

        result = run_evolution(
            initial_code=example["initial_code"],
            evaluator=evaluator,
            weights=weights,
            generations=5,
            population_size=4,
            selection_k=2,
            mutation_mode="random",
            language=example["language"],
            seed=42,
        )

        print("History:")
        for item in result.history:
            print(
                {
                    "generation": item.generation,
                    "best_generation_fitness": item.best_generation_fitness,
                    "best_so_far_fitness": item.best_so_far_fitness,
                }
            )

        print("\nBest overall:")
        print(result.best_overall.fitness_result.as_dict())

        print("\nBest code/pseudocode:")
        print(result.best_overall.candidate.code)


if __name__ == "__main__":
    main()