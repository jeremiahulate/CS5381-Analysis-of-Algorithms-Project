from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from src.evolve.fitness import EvaluationMetrics


@dataclass(frozen=True)
class CandidateProgram:
    """
    Represents one candidate solution in the evolutionary loop.
    """
    code: str
    language: str = "python"
    description: str = ""
    provider: str = ""


class Evaluator(Protocol):
    """
    Protocol for evaluators.
    """
    def evaluate(self, candidate: CandidateProgram) -> EvaluationMetrics:
        ...

def extract_action_from_code(code: str) -> str | None:
    actions = ["eat_food", "run_away", "wait", "move_randomly"]
    for action in actions:
        if f'return "{action}"' in code or f"return '{action}'" in code:
            return action
    return None

class DeterministicStubPacmanEvaluator:
    """
    Deterministic prototype evaluator.

    The same candidate code always produces the same metrics.
    This is useful for:
    - stable testing
    - fair comparison across modes
    - cleaner plots for the prototype

    It does NOT run real Pacman yet. It scores based on simple
    code features and hashed content.
    """

    def evaluate(self, candidate: CandidateProgram) -> EvaluationMetrics:
        code = candidate.code.strip()

        if not code:
            return EvaluationMetrics(
                score=0.0,
                survival_time=0.0,
                steps=999.0,
            )

        lines = [line.rstrip() for line in code.splitlines() if line.strip()]
        line_count = len(lines)
        char_count = len(code)

        lowered = code.lower()

        action = extract_action_from_code(code)

        # Structural signals
        if_count = lowered.count("if ")
        elif_count = lowered.count("elif ")
        else_count = lowered.count("else")
        return_count = lowered.count("return")
        ghost_refs = lowered.count("ghost")
        food_refs = lowered.count("food")
        state_refs = lowered.count("state")
        comment_count = sum(1 for line in lines if line.strip().startswith("#"))

        action_score_bonus = 0
        action_survival_bonus = 0.0
        action_step_adjustment = 0

        if action == "eat_food":
            action_score_bonus = 60
            action_survival_bonus = 2.0
            action_step_adjustment = -8
        elif action == "run_away":
            action_score_bonus = 40
            action_survival_bonus = 4.0
            action_step_adjustment = -5
        elif action == "wait":
            action_score_bonus = 10
            action_survival_bonus = 1.0
            action_step_adjustment = 0
        elif action == "move_randomly":
            action_score_bonus = 5
            action_survival_bonus = 0.5
            action_step_adjustment = 5
        # Deterministic content hash
        digest = hashlib.sha256(code.encode("utf-8")).hexdigest()
        hash_value = int(digest[:8], 16)

        # Small deterministic variation from hash
        hash_score_bonus = hash_value % 40
        hash_survival_bonus = (hash_value % 20) / 10.0
        hash_step_penalty = hash_value % 25

        # Score:
        # reward structure, control logic, references to useful concepts
        score = (
            150
            + (line_count * 12)
            + (if_count * 30)
            + (elif_count * 15)
            + (else_count * 10)
            + (return_count * 18)
            + (ghost_refs * 25)
            + (food_refs * 20)
            + (state_refs * 8)
            + hash_score_bonus
            + action_score_bonus
        )

        # Survival time:
        # reward conditionals / ghost handling / branching
        survival_time = (
            5.0
            + (line_count * 0.35)
            + (if_count * 1.5)
            + (elif_count * 0.75)
            + (else_count * 0.5)
            + (ghost_refs * 1.25)
            + (state_refs * 0.2)
            + hash_survival_bonus
            + action_survival_bonus
        )

        # Steps:
        # penalize bloated code/comments a bit
        steps = (
            60
            + (line_count * 5)
            + (char_count // 18)
            + (comment_count * 2)
            + hash_step_penalty
            + action_step_adjustment
        )
        
        # Keep values in a reasonable prototype range
        score = float(max(0, score))
        survival_time = float(max(0.0, survival_time))
        steps = float(max(1, steps))

        #EVAL DEBUG
        print(f"[EVAL DEBUG] action={action}, score={score}, survival={survival_time}, steps={steps}")

        return EvaluationMetrics(
            score=score,
            survival_time=survival_time,
            steps=steps,
        )