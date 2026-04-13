from __future__ import annotations

import ast
import random
from dataclasses import dataclass
from typing import List, Literal

from src.evolve.evaluator import CandidateProgram, Evaluator
from src.evolve.fitness import FitnessWeights, FitnessResult, compute_fitness
from src.evolve.generator import LLMSettings, LLMMutator


MutationMode = Literal["none", "random", "llm", "rag"]

print("[DEBUG] LOADED engine.py NEW VERSION")
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
    provider: str = ""


@dataclass(frozen=True)
class EvolutionRunResult:
    history: List[GenerationSummary]
    best_overall: EvaluatedCandidate

#cleanup function for LLM
def clean_llm_code_output(text: str) -> str:
    text = text.strip()

    if "```" in text:
        parts = text.split("```")
        for part in parts:
            cleaned = part.strip()
            if cleaned.startswith("python"):
                cleaned = cleaned[len("python"):].strip()
            if "def pacman_agent" in cleaned:
                text = cleaned
                break

    lines = text.splitlines()

    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("def pacman_agent"):
            start_idx = i
            break

    if start_idx is None:
        return text

    cleaned_lines = [lines[start_idx].rstrip()]
    base_indent = None

    for line in lines[start_idx + 1:]:
        stripped = line.strip()

        if not stripped:
            cleaned_lines.append("")
            continue

        current_indent = len(line) - len(line.lstrip())

        if base_indent is None:
            if current_indent == 0:
                break
            base_indent = current_indent
            cleaned_lines.append(line.rstrip())
            continue

        if current_indent < base_indent:
            break

        if stripped.startswith(("Return ", "Do not ", "The function ", "Mutated code:", "Original code:")):
            break

        cleaned_lines.append(line.rstrip())

    return "\n".join(cleaned_lines).strip()

#function to check if mutated code is valid Python syntax to avoid 
# introducing syntax errors during random mutations
def is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

#mutation that appends a comment to the end of the code to introduce 
#variation without breaking syntax
def mutate_add_comment(code: str, rng: random.Random) -> str:
    comments = [
        "# mutation applied",
        "# candidate refinement",
        "# adjusted strategy",
        "# random mutation",
    ]
    return code.rstrip() + "\n" + rng.choice(comments)


#mutation that replaces one known strategy token/literal with another 
#to introduce variation while keeping the code likely valid and meaningful
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


#mutation that inserts a safe line of code (like a comment or pass) at a random location 
#in the code to introduce variation without breaking syntax
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


#random mutation that tries multiple strategies and falls back to a safe comment mutation if needed
def random_mutation(code: str, rng: random.Random, language: str = "python") -> tuple[str, str]:
    actions = ["eat_food", "run_away", "wait", "move_randomly"]

    if language.lower() != "python":
        return code, "Random mutation skipped for unsupported language"

    mode = rng.choice(["simple", "conditional"])

    if mode == "simple":
        action = rng.choice(actions)
        mutated = f'''def pacman_agent(state):
    return "{action}"
'''
        return mutated, f'Random action mutation applied: "{action}"'

    safe_action = rng.choice(["eat_food", "wait", "move_randomly"])
    danger_action = rng.choice(["run_away", "wait"])

    mutated = f'''def pacman_agent(state):
    if getattr(state, "isGhostNearby", lambda: False)():
        return "{danger_action}"
    return "{safe_action}"
'''
    return mutated, f'Random conditional mutation applied: danger="{danger_action}", safe="{safe_action}"'

#rag guided mutation
def rag_guided_mutation(
    code: str,
    rng: random.Random,
    retrieved_contexts: List[str],
    language: str = "python",
) -> tuple[str, str]:
    """
    Use retrieved FAISS contexts to guide mutation.
    This is a simple deterministic mutation layer that can later be upgraded
    to use an LLM with retrieved context in the prompt.
    """
    if language.lower() != "python":
        return code, "RAG guidance available, but only Python mutation is implemented"

    context = " ".join(retrieved_contexts).lower()

    ghost_hits = sum(
    phrase in context
    for phrase in [
        "ghost",
        "run away",
        "avoid ghost",
        "prioritize survival",
        "move away",
    ]
)

    food_hits = sum(
        phrase in context
        for phrase in [
            "food",
            "collect food",
            "eat food",
            "prioritize food",
            "when safe",
        ]
    )

    has_ghost = ghost_hits >= 2
    has_food = food_hits >= 1
    
    #RAG debug
    print(f"[RAG DEBUG] ghost_hits={ghost_hits}, food_hits={food_hits}")
    
    if has_ghost and has_food:
        new_code = '''
        def pacman_agent(state):
            if state.isGhostNearby():
                return "run_away"
            return "eat_food"
    '''
        return new_code, "Applied RAG-guided ghost avoidance and food-priority mutation"

    if has_ghost:
        new_code = '''def pacman_agent(state):
        if state.isGhostNearby():
            return "run_away"
        return "stay_safe"
    '''
        return new_code, "Applied RAG-guided ghost avoidance mutation"

    if has_food:
        new_code = '''def pacman_agent(state):
        return "eat_food"
    '''
        return new_code, "Applied RAG-guided food-priority mutation"

    return code, "No useful RAG signal found; original candidate kept"

def generate_candidates(
    parents: List[CandidateProgram],
    population_size: int,
    mutation_mode: MutationMode,
    rng: random.Random,
    problem_description: str = "",
    llm_settings: LLMSettings | None = None,
    retriever=None,
    retrieval_top_k: int = 1,
    knowledge_docs=None,
) -> tuple[List[CandidateProgram], List[str], List[str]]:
    if not parents:
        raise ValueError("At least one parent candidate is required.")

    llm_mutator = LLMMutator(llm_settings or LLMSettings())
    candidates: List[CandidateProgram] = []
    operation_summaries: List[str] = []
    operation_providers: List[str] = []

    for idx in range(population_size):
        #GEN DEBUG
        print(f"\n[GEN DEBUG] generation candidate index = {idx}, mutation_mode = {mutation_mode}")
        parent = rng.choice(parents)

        if mutation_mode == "none":
            new_code = parent.code
            summary = "No mutation applied; reused parent candidate"
            provider = "none"

        elif mutation_mode == "random":
            new_code, summary = random_mutation(parent.code, rng, parent.language)
            provider = "random"

        elif mutation_mode == "llm":
            mutation_output = llm_mutator.mutate(
                code=parent.code,
                problem_description=problem_description,
                language=parent.language,
            )
            new_code = mutation_output.code
            summary = mutation_output.summary
            provider = mutation_output.provider
        
        elif mutation_mode == "rag":
            if retriever is None:
                new_code, summary = rag_guided_mutation(
                    parent.code,
                    rng,
                    [],
                    parent.language,
                )
                provider = "rag-fallback"
            else:
                query_text = f"{problem_description}\n\n{parent.code}"
                retrieved_items = retriever.retrieve(query_text, top_k=retrieval_top_k)

                #RAG + LLM DEBUG
                print(f"[GEN DEBUG] Candidate {idx} retrieved {len(retrieved_items)} contexts:")
                for item in retrieved_items:
                    source = "unknown"
                    if knowledge_docs is not None and 0 <= item.index < len(knowledge_docs):
                        source = knowledge_docs[item.index].source
                    print(f"[SOURCE: {source}]")
                    print("-", item.text)

                retrieved_contexts = [item.text for item in retrieved_items]

                retrieved_context_block = "\n".join(
                    f"- {ctx}" for ctx in retrieved_contexts
                )

                rag_problem_description = (
                    f"User goal: {problem_description.strip()}\n"
                    f"Retrieved guidance: {retrieved_context_block}\n"
                    'Prefer "eat_food" when safe. Choose "run_away" only if danger is the dominant concern.\n'
                )

                mutation_output = llm_mutator.mutate_action(
                    code=parent.code,
                    problem_description=rag_problem_description,
                )
                #RAG+LLM DEBUG
                print("\n[RAG+LLM ACTION DEBUG] Raw mutation output code:")
                print(mutation_output.code)
                #RAG+LLM DEBUG
                print("\n[RAG+LLM ACTION DEBUG] Raw mutation summary:")
                print(mutation_output.summary)

                new_code = mutation_output.code

                summary = (
                    #RAG+LLM DEBUG
                    f"RAG+LLM action mutation: {mutation_output.summary} | "
                    f"Retrieved {len(retrieved_contexts)} context(s)"
                )
                provider = f"{mutation_output.provider}+rag"

                if parent.language.lower() == "python" and not is_valid_python(new_code):
                    #RAG+LLM DEBUG
                    print("[RAG+LLM DEBUG] Invalid Python from LLM, using rule-based RAG fallback")
                    new_code, fallback_summary = rag_guided_mutation(
                        parent.code,
                        rng,
                        retrieved_contexts,
                        parent.language,
                    )
                    summary = f"RAG+LLM mutation invalid; used rule-based RAG fallback ({fallback_summary})"
                    provider = f"{provider}-fallback"
        else:
            raise ValueError(f"Unsupported mutation mode: {mutation_mode}")

        candidates.append(
            CandidateProgram(
                code=new_code,
                language=parent.language,
                description=summary,
                provider=provider,
            )
        )
        operation_summaries.append(summary)
        operation_providers.append(provider)

    return candidates, operation_summaries, operation_providers



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
    retriever=None,
    retrieval_top_k: int = 1,
    knowledge_docs=None,
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
        candidates, operation_summaries, operation_providers = generate_candidates(
            parents=parents,
            population_size=population_size,
            mutation_mode=mutation_mode,
            rng=rng,
            problem_description=problem_description,
            llm_settings=llm_settings,
            retriever=retriever,
            retrieval_top_k=retrieval_top_k,
            knowledge_docs=knowledge_docs,
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
                provider=best_generation.candidate.provider,
            )
        )

    if best_overall is None:
        raise RuntimeError("Evolution run did not produce any candidates.")

    return EvolutionRunResult(history=history, best_overall=best_overall)
