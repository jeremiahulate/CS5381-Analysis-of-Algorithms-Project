from __future__ import annotations

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
    if state.isGhostNearby():
        return "run_away"
    return "eat_food"
""".strip()

    result = run_evolution(
        initial_code=initial_code,
        evaluator=DeterministicStubPacmanEvaluator(),
        weights=FitnessWeights(w_score=0.5, w_survival=0.3, w_steps=0.2),
        generations=5,
        population_size=4,
        selection_k=2,
        mutation_mode="llm",
        language="python",
        problem_description="Improve Pacman fitness while balancing score, survival time, and step cost.",
        llm_settings=LLMSettings(provider="heuristic"),
        seed=42,
    )

    print("Prototype check completed.")
    print("Best fitness:", result.best_overall.fitness_result.fitness)
    print("Best code:\n")
    print(result.best_overall.candidate.code)


if __name__ == "__main__":
    main()
