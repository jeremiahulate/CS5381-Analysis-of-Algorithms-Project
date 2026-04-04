from __future__ import annotations

import ast
import random
from dataclasses import dataclass
from typing import List, Literal

from src.evolve.evaluator import CandidateProgram, Evaluator
from src.evolve.fitness import FitnessWeights, FitnessResult, compute_fitness
from src.evolve.generator import LLMSettings, LLMMutator


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
    operation_summary: str = ""


@dataclass(frozen=True)
class EvolutionRunResult:
    history: List[GenerationSummary]
    best_overall: EvaluatedCandidate


def is_valid_python(code: str) -> bool:
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



def random_mutation(code: str, rng: random.Random, language: str = "python") -> tuple[str, str]:
    mutation_functions = [
        (mutate_add_comment, "Added a safe comment mutation"),
        (mutate_replace_literal, "Replaced one known strategy token/literal"),
        (mutate_insert_line, "Inserted a safe line"),
    ]

    original = code
    attempts = 5

    for _ in range(attempts):
        mutator, summary = rng.choice(mutation_functions)
        mutated = mutator(original, rng)

        if language.lower() == "python":
            if is_valid_python(mutated):
                return mutated, summary
        else:
            return mutated, summary

    return mutate_add_comment(original, rng), "Applied fallback comment mutation"



def generate_candidates(
    parents: List[CandidateProgram],
    population_size: int,
    mutation_mode: MutationMode,
    rng: random.Random,
    problem_description: str = "",
    llm_settings: LLMSettings | None = None,
) -> tuple[List[CandidateProgram], List[str]]:
    if not parents:
        raise ValueError("At least one parent candidate is required.")

    llm_mutator = LLMMutator(llm_settings or LLMSettings())
    candidates: List[CandidateProgram] = []
    operation_summaries: List[str] = []

    for _ in range(population_size):
        parent = rng.choice(parents)

        if mutation_mode == "none":
            new_code = parent.code
            summary = "No mutation applied; reused parent candidate"

        elif mutation_mode == "random":
            new_code, summary = random_mutation(parent.code, rng, parent.language)

        elif mutation_mode == "llm":
            mutation_output = llm_mutator.mutate(
                code=parent.code,
                problem_description=problem_description,
                language=parent.language,
            )
            new_code = mutation_output.code
            summary = mutation_output.summary

        else:
            raise ValueError(f"Unsupported mutation mode: {mutation_mode}")

        candidates.append(
            CandidateProgram(
                code=new_code,
                language=parent.language,
                description=summary,
            )
        )
        operation_summaries.append(summary)

    return candidates, operation_summaries



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
    problem_description: str = "",
    llm_settings: LLMSettings | None = None,
) -> EvolutionRunResult:
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
        candidates, operation_summaries = generate_candidates(
            parents=parents,
            population_size=population_size,
            mutation_mode=mutation_mode,
            rng=rng,
            problem_description=problem_description,
            llm_settings=llm_settings,
        )

        evaluated = evaluate_population(
            candidates=candidates,
            evaluator=evaluator,
            weights=weights,
            generation=generation,
            mutation_mode=mutation_mode,
        )

        selected = select_top_k(evaluated, selection_k)
        parents = [item.candidate for item in selected]

        best_generation = selected[0]

        if best_overall is None or best_generation.fitness_result.fitness > best_overall.fitness_result.fitness:
            best_overall = best_generation

        history.append(
            GenerationSummary(
                generation=generation,
                best_generation_fitness=best_generation.fitness_result.fitness,
                best_so_far_fitness=best_overall.fitness_result.fitness,
                best_score=best_generation.fitness_result.raw_metrics.score,
                best_survival_time=best_generation.fitness_result.raw_metrics.survival_time,
                best_steps=best_generation.fitness_result.raw_metrics.steps,
                best_code=best_overall.candidate.code,
                mutation_mode=mutation_mode,
                operation_summary=best_generation.candidate.description or operation_summaries[0],
            )
        )

    if best_overall is None:
        raise RuntimeError("Evolution run did not produce any candidates.")

    return EvolutionRunResult(history=history, best_overall=best_overall)
