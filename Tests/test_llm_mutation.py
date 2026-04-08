import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolve.engine import run_evolution
from src.evolve.evaluator import DeterministicStubPacmanEvaluator
from src.evolve.fitness import FitnessWeights
from src.evolve.generator import LLMSettings


def main() -> None:
    initial_code = """
def pacman_agent(state):
    return "eat_food"
""".strip()

    evaluator = DeterministicStubPacmanEvaluator()
    weights = FitnessWeights(w_score=0.5, w_survival=0.3, w_steps=0.2)

    result = run_evolution(
        initial_code=initial_code,
        evaluator=evaluator,
        weights=weights,
        generations=3,
        population_size=2,
        selection_k=1,
        mutation_mode="llm",
        language="python",
        problem_description="Improve Pacman survival while keeping food collection behavior.",
        llm_settings=LLMSettings(provider="heuristic"),
        seed=7,
    )

    print("Best fitness:", result.best_overall.fitness_result.fitness)
    print("Operation summaries:")
    for item in result.history:
        print(f"Gen {item.generation}: {item.operation_summary}")


if __name__ == "__main__":
    main()
