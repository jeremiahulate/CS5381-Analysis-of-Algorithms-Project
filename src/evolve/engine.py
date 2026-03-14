from __future__ import annotations

import ast
import random
from dataclasses import dataclass
from typing import List, Literal

from src.evolve.evaluator import CandidateProgram, Evaluator
from src.evolve.fitness import FitnessWeights, FitnessResult, compute_fitness


MutationMode = Literal["none", "random", "llm"]


@dataclass(frozen=True)
class EvaluatedCandidate:
    candidate: CandidateProgram
    fitness_result: FitnessResult
    generation: int
    mutation_mode: str


@dataclass(frozen=True)
class GenerationSummary:
    generation: int
    best_generation_fitness: float
    best_so_far_fitness: float
    best_score: float
    best_survival_time: float
    best_steps: float
    best_code: str
    mutation_mode: str


@dataclass(frozen=True)
class EvolutionRunResult:
    history: List[GenerationSummary]
    best_overall: EvaluatedCandidate


def is_valid_python(code: str) -> bool:
    """
    Check whether mutated Python code is syntactically valid.
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def mutate_add_comment(code: str, rng: random.Random) -> str:
    comments = [
        "# mutation applied",
        "# candidate refinement",
        "# adjusted strategy",
        "# random mutation",
    ]
    return code.rstrip() + "\n" + rng.choice(comments)


def mutate_replace_literal(code: str, rng: random.Random) -> str:
    replacements = [
        ("eat_food", "move_randomly"),
        ("move_randomly", "eat_food"),
        ("run_away", "eat_food"),
        ("eat_food", "run_away"),
        ("True", "False"),
        ("False", "True"),
    ]

    possible = [(old, new) for old, new in replacements if old in code]
    if not possible:
        return mutate_add_comment(code, rng)

    old, new = rng.choice(possible)
    return code.replace(old, new, 1)


def mutate_insert_line(code: str, rng: random.Random) -> str:
    lines = code.splitlines()
    insertions = [
        "    # inserted mutation",
        "    pass",
    ]

    if not lines:
        return code

    insert_at = rng.randrange(len(lines) + 1)
    lines.insert(insert_at, rng.choice(insertions))
    return "\n".join(lines)


def random_mutation(code: str, rng: random.Random, language: str = "python") -> str:
    """
    Safer mutation strategy than swapping arbitrary lines.

    For Python:
    - add a comment
    - replace known literals/tokens
    - insert a safe line
    - validate syntax; if invalid, fall back
    """
    mutation_functions = [
        mutate_add_comment,
        mutate_replace_literal,
        mutate_insert_line,
    ]

    original = code
    attempts = 5

    for _ in range(attempts):
        mutator = rng.choice(mutation_functions)
        mutated = mutator(original, rng)

        if language.lower() == "python":
            if is_valid_python(mutated):
                return mutated
        else:
            return mutated

    return mutate_add_comment(original, rng)


def generate_candidates(
    parents: List[CandidateProgram],
    population_size: int,
    mutation_mode: MutationMode,
    rng: random.Random,
) -> List[CandidateProgram]:
    """
    Generate a new population from parent candidates.
    """
    if not parents:
        raise ValueError("At least one parent candidate is required.")

    candidates: List[CandidateProgram] = []

    for _ in range(population_size):
        parent = rng.choice(parents)

        if mutation_mode == "none":
            new_code = parent.code

        elif mutation_mode == "random":
            new_code = random_mutation(parent.code, rng, parent.language)

        elif mutation_mode == "llm":
            # Placeholder for future teammate integration
            new_code = parent.code.rstrip() + "\n# llm mutation placeholder"

        else:
            raise ValueError(f"Unsupported mutation mode: {mutation_mode}")

        candidates.append(
            CandidateProgram(
                code=new_code,
                language=parent.language,
                description=f"Generated via {mutation_mode} mutation",
            )
        )

    return candidates


def evaluate_population(
    candidates: List[CandidateProgram],
    evaluator: Evaluator,
    weights: FitnessWeights,
    generation: int,
    mutation_mode: str,
) -> List[EvaluatedCandidate]:
    evaluated: List[EvaluatedCandidate] = []

    for candidate in candidates:
        metrics = evaluator.evaluate(candidate)
        fitness_result = compute_fitness(metrics, weights)

        evaluated.append(
            EvaluatedCandidate(
                candidate=candidate,
                fitness_result=fitness_result,
                generation=generation,
                mutation_mode=mutation_mode,
            )
        )

    return evaluated


def select_top_k(
    evaluated_candidates: List[EvaluatedCandidate],
    k: int,
) -> List[EvaluatedCandidate]:
    if k < 1:
        raise ValueError("k must be at least 1.")

    ranked = sorted(
        evaluated_candidates,
        key=lambda x: x.fitness_result.fitness,
        reverse=True,
    )

    return ranked[:k]


def run_evolution(
    initial_code: str,
    evaluator: Evaluator,
    weights: FitnessWeights,
    generations: int,
    population_size: int,
    selection_k: int,
    mutation_mode: MutationMode = "random",
    language: str = "python",
    seed: int | None = None,
) -> EvolutionRunResult:
    """
    Run the evolutionary process for the requested number of generations.
    """
    if generations < 1:
        raise ValueError("generations must be at least 1")
    if population_size < 1:
        raise ValueError("population_size must be at least 1")
    if selection_k < 1:
        raise ValueError("selection_k must be at least 1")
    if selection_k > population_size:
        raise ValueError("selection_k cannot be greater than population_size")

    rng = random.Random(seed)

    initial_candidate = CandidateProgram(
        code=initial_code,
        language=language,
        description="Initial user-provided solution",
    )

    parents: List[CandidateProgram] = [initial_candidate]
    history: List[GenerationSummary] = []
    best_overall: EvaluatedCandidate | None = None

    for generation in range(1, generations + 1):
        candidates = generate_candidates(
            parents=parents,
            population_size=population_size,
            mutation_mode=mutation_mode,
            rng=rng,
        )

        evaluated = evaluate_population(
            candidates=candidates,
            evaluator=evaluator,
            weights=weights,
            generation=generation,
            mutation_mode=mutation_mode,
        )

        selected = select_top_k(evaluated, selection_k)
        best_this_generation = selected[0]

        parents = [item.candidate for item in selected]

        if (
            best_overall is None
            or best_this_generation.fitness_result.fitness > best_overall.fitness_result.fitness
        ):
            best_overall = best_this_generation

        history.append(
            GenerationSummary(
                generation=generation,
                best_generation_fitness=best_this_generation.fitness_result.fitness,
                best_so_far_fitness=best_overall.fitness_result.fitness,
                best_score=best_this_generation.fitness_result.raw_metrics.score,
                best_survival_time=best_this_generation.fitness_result.raw_metrics.survival_time,
                best_steps=best_this_generation.fitness_result.raw_metrics.steps,
                best_code=best_this_generation.candidate.code,
                mutation_mode=mutation_mode,
            )
        )

    if best_overall is None:
        raise RuntimeError("Evolution run produced no evaluated candidates.")

    return EvolutionRunResult(
        history=history,
        best_overall=best_overall,
    )