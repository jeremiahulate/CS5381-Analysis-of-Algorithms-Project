from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class FitnessWeights:
    w_score: float
    w_survival: float
    w_steps: float

    def validate(self, tol: float = 1e-6) -> None:
        values = [self.w_score, self.w_survival, self.w_steps]

        if any (value < 0 for value in values):
            raise ValueError("All fitness weights must be nonnegative")
        
        total = sum(values)
        if abs(total -1.0) > tol:
            raise ValueError(f"Fitness weights must sum to 1.0. Got {total:.6f}.")
        
@dataclass(frozen=True)
class EvaluationMetrics:
    score: float
    survival_time: float
    steps: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "score": self.score,
            "survival_time": self.survival_time,
            "steps": self.steps,
        }

@dataclass(frozen=True)
class FitnessResult:
    fitness: float
    score_component: float
    survival_component: float
    steps_component: float
    raw_metrics: EvaluationMetrics

    def as_dict(self) -> Dict[str, float]:
        return {
            "fitness": self.fitness,
            "score_component": self.score_component,
            "survival_component": self.survival_component,
            "steps_component": self.steps_component,
            "score": self.raw_metrics.score,
            "survival_time": self.raw_metrics.survival_time,
            "steps": self.raw_metrics.steps,
        }

def compute_fitness(
        metrics: EvaluationMetrics,
        weights: FitnessWeights,
) -> FitnessResult:
    """
    compute fitness for the Pacman use case
    
    Fitness = w_score * score + w_survival * survival_time - w_steps * steps
    subject to w_score + w_survival + w_steps = 1
    """
    weights.validate()

    score_component = weights.w_score * metrics.score
    survival_component = weights.w_survival * metrics.survival_time
    steps_component = weights.w_steps * metrics.steps

    fitness = score_component + survival_component - steps_component

    return FitnessResult(
        fitness=fitness,
        score_component=score_component,
        survival_component=survival_component,
        steps_component=steps_component,
        raw_metrics=metrics,
    )
