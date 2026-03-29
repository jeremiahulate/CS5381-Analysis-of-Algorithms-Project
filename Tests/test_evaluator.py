import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolve.evaluator import CandidateProgram, DeterministicStubPacmanEvaluator


def main() -> None:
    candidate = CandidateProgram(
        code="""
def pacman_agent(state):
    if state.isGhostNearby():
        return "run_away"
    return "eat_food"
""".strip(),
        language="python",
        description="Simple Pacman strategy",
    )

    evaluator = DeterministicStubPacmanEvaluator()
    metrics = evaluator.evaluate(candidate)

    print("Evaluation metrics:")
    print(metrics.as_dict())


if __name__ == "__main__":
    main()