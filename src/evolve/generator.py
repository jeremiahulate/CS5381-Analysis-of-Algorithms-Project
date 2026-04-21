from __future__ import annotations

import urllib.request
import urllib.error
import re
import ast
import json
import time
import random
from dataclasses import dataclass
from typing import Any
from pathlib import Path

VALID_ACTIONS = ["eat_food","run_away","wait","move_randomly"]
@dataclass(frozen=True)
class MutationOutput:
    code: str
    summary: str
    expected_improvement: str = ""
    provider: str = "heuristic"


@dataclass(frozen=True)
class LLMSettings:
    provider: str = "heuristic"
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None
    temperature: float = 0.0

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

def is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def is_valid_pacman_agent(code: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False


    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    if len(funcs) != 1:
        return False

    func = funcs[0]
    if func.name != "pacman_agent":
        return False

    if len(func.args.args) != 1:
        return False

    return func.args.args[0].arg == "state"

def has_valid_pacman_actions(code: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    allowed_actions = {
        "run_away",
        "eat_food",
        "wait",
        "move_randomly",
        "search_food",
        "stay_safe",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Return):
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                if value.value not in allowed_actions:
                    return False

    return True

def extract_llama_code(output: str, original_code: str) -> str:
    text = output.strip()

    if not text:
        return original_code

    lines = text.splitlines()
    filtered = []

    skip_starts = (
        "Loading model",
        "build      :",
        "model      :",
        "modalities :",
        "available commands:",
        "/exit",
        "/regen",
        "/clear",
        "/read",
        "/glob",
        "> [INST]",
        "[/INST]",
        "Exiting...",
        "[LLM",
        "load_backend:",
        "[ Prompt:",
    )

    for line in lines:
        s = line.strip()

        if not s:
            continue

        if s.startswith(skip_starts):
            continue

        if any(ch in s for ch in ("▄▄", "██", "▀▀")):
            continue

        filtered.append(line)

    text = "\n".join(filtered).strip()

    if not text:
        return original_code

    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if not part:
                continue

            part_lines = part.splitlines()
            if part_lines and part_lines[0].strip().lower() in {"python", "py"}:
                part = "\n".join(part_lines[1:])

            extracted = extract_complete_pacman_function(part, original_code)
            if extracted != original_code:
                return extracted

    return extract_complete_pacman_function(text, original_code)

def extract_complete_pacman_function(text: str, original_code: str) -> str:
    lines = text.splitlines()

    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("def pacman_agent"):
            start_idx = i
            break

    if start_idx is None:
        return original_code

    extracted = [lines[start_idx].rstrip()]
    found_return = False

    for line in lines[start_idx + 1:]:
        stripped = line.strip()

        if not stripped:
            break

        if not line.startswith((" ", "\t")):
            break

        extracted.append(line.rstrip())

        if stripped.startswith("return ") or " return " in stripped:
            found_return = True

    code = "\n".join(extracted).strip()

    if "def pacman_agent" not in code:
        return original_code

    if "return" not in code and not found_return:
        return original_code

    return code

def extract_llama_action(output: str) -> str | None:
    text = output.strip()

    if not text:
        return None

    # normalize common wrappers / markdown
    text = text.replace("`", "").strip()

    allowed_actions = [
        "run_away",
        "eat_food",
        "wait",
        "move_randomly",
    ]

    return text if text in allowed_actions else None


def wrap_action_as_pacman_agent(default_action: str,
                                ghost_action: str ) -> str:
    return f'''def pacman_agent(state):
    if state.isGhostNearby():
        return "{ghost_action}"
    return "{default_action}"
'''

class HeuristicLLMMutator:
    """
    Offline fallback mutator for the prototype.

    This keeps the current UI usable even when no real API key is configured.
    """

    def mutate(self, code: str, problem_description: str = "", language: str = "python") -> MutationOutput:
        improved = code.rstrip()
        lower = improved.lower()
        summary_parts: list[str] = []

        if "ghost" not in lower:
            if language.lower() == "python" and "def " in improved:
                improved += (
                    "\n\n# heuristic mutation: add ghost-awareness branch\n"
                    "def _ghost_priority_hint(state):\n"
                    "    return \"run_away\" if getattr(state, 'isGhostNearby', lambda: False)() else None\n"
                )
            else:
                improved += "\n# heuristic mutation: consider nearby ghosts before pursuing food"
            summary_parts.append("Added ghost-awareness logic")

        if "food" not in lower:
            improved += "\n# heuristic mutation: prioritize food when safe"
            summary_parts.append("Added food-priority hint")

        if "return" not in lower:
            improved += "\n# heuristic mutation: make decision outcome explicit"
            summary_parts.append("Added explicit decision hint")

        if problem_description and "fitness" in problem_description.lower():
            improved += "\n# heuristic mutation: align behavior with stated fitness objective"
            summary_parts.append("Aligned candidate with fitness wording")

        if not summary_parts:
            improved += "\n# heuristic mutation: small refinement to preserve valid candidate"
            summary_parts.append("Applied a small heuristic refinement")

        if language.lower() == "python" and not is_valid_python(improved):
            improved = code.rstrip() + "\n# heuristic mutation fallback"

        return MutationOutput(
            code=improved,
            summary="; ".join(summary_parts),
            expected_improvement="May improve evaluator signals by adding useful control-flow and domain references.",
            provider="heuristic",
        )

class LlamaServerMutator:
    def __init__(self, settings: LLMSettings):
        self.provider = "llama-server"
        self.temperature = settings.temperature
        self.base_url = (settings.base_url or "http://127.0.0.1:8080").rstrip("/")

    def mutate(self, code: str, problem_description: str = "", language: str = "python") -> MutationOutput:

        prompt = f"""
Return only one action string.

Choose the best action for Pacman based on this guidance.
Allowed actions:
- "eat_food"
- "run_away"
- "wait"
- "move_randomly"

Guidance:
{problem_description.strip()}

Current code:
{code}
""".strip()

        payload = {
            "prompt": prompt,
            "n_predict": 16,
            "temperature": float(self.temperature),
            "stop": [
                "```",
            ],
        }

        req = urllib.request.Request(
            url=f"{self.base_url}/completion",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            start = time.perf_counter()
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            elapsed = time.perf_counter() - start
        except urllib.error.URLError as exc:
            return MutationOutput(
                code=code,
                summary=f"llama-server unavailable ({exc}); original code preserved.",
                expected_improvement="",
                provider="llama-server-error",
            )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return MutationOutput(
                code=code,
                summary="llama-server returned invalid JSON; original code preserved.",
                expected_improvement="",
                provider="llama-server-error",
            )

        text = str(data.get("content", "")).strip()
        mutated = extract_llama_code(text, original_code=code)

        if not mutated.strip():
            return MutationOutput(
                code=code,
                summary="llama-server returned empty output; original code preserved.",
                expected_improvement="",
                provider=self.provider,
            )

        if language.lower() == "python":
            cleaned_mutated = clean_llm_code_output(mutated)

            if not is_valid_python(cleaned_mutated):
                return MutationOutput(
                    code=code,
                    summary="llama-server returned invalid Python after cleanup; original code preserved.",
                    expected_improvement="",
                    provider=self.provider,
                )

            mutated = cleaned_mutated

            if not is_valid_pacman_agent(mutated):
                return MutationOutput(
                    code=code,
                    summary="llama-server changed the required pacman_agent interface; original code preserved.",
                    expected_improvement="",
                    provider=self.provider,
                )
            
            if mutated.strip() == code.strip():
                return MutationOutput(
                    code=code,
                    summary="llama-server returned unchanged code; original code preserved.",
                    expected_improvement="",
                    provider=self.provider,
                )
            
        return MutationOutput(
            code=mutated,
            summary="Local llama-server mutation applied.",
            expected_improvement="Local server suggested a small targeted refinement.",
            provider=self.provider,
        )
    def mutate_action(self, code: str, problem_description: str = "") -> MutationOutput:
        prompt = f"""
Reply with exactly one of these strings:
eat_food
run_away
wait
move_randomly

Do not explain.
Do not add punctuation.
Do not add quotes.

Guidance:
{problem_description.strip()}

Answer with one word only:
""".strip()

        payload = {
            "prompt": prompt,
            "n_predict": 16,
            "temperature":0.3,
            "stop": [
                "```",
            ],
        }

        req = urllib.request.Request(
            url=f"{self.base_url}/completion",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            start = time.perf_counter()
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            elapsed = time.perf_counter() - start
        except urllib.error.URLError as exc:
            return MutationOutput(
                code=code,
                summary=f"llama-server unavailable ({exc}); original code preserved.",
                expected_improvement="",
                provider="llama-server-error",
            )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return MutationOutput(
                code=code,
                summary="llama-server returned invalid JSON; original code preserved.",
                expected_improvement="",
                provider="llama-server-error",
            )

        text = str(data.get("content", "")).strip()

        #epsilon-greedy exploration
        exploration_used = False
        epsilon = 0.2

        if random.random() < epsilon:
            action = random.choice(VALID_ACTIONS)
            exploration_used = True
        else:
            #try LLM output
            action = extract_llama_action(text)

            #fallback
            if action is None:
                action = random.choice(VALID_ACTIONS)
                exploration_used = True

        #new ghost branch mutation
        if random.random() < 0.3:
            ghost_action = random.choice(["run_away", "wait"])
        else:
            ghost_action = "run_away"

        mutated = wrap_action_as_pacman_agent(action, ghost_action)

        if mutated.strip() == code.strip():
            return MutationOutput(
                code=code,
                summary="llama-server returned unchanged action; original code preserved.",
                expected_improvement="",
                provider=self.provider,
            )
        
        if not is_valid_pacman_agent(mutated) or not has_valid_pacman_actions(mutated):
            return MutationOutput(
                code=code,
                summary="Invalid generated agent; original preserved.",
                expected_improvement="",
                provider=self.provider,
            )

        return MutationOutput(
            code=mutated,
            summary=(
                f'Local llama-server action mutation applied: "{action}"'
                if not exploration_used
                else f'Epsilon exploration applied: "{action}"'
            ),
            expected_improvement="Local server selected a guided Pacman action.",
            provider=self.provider,
        )

    

class LLMMutator:
    def __init__(self, settings: LLMSettings | None = None):
        self.settings = settings or LLMSettings()
        self.fallback = HeuristicLLMMutator()

    def mutate(self, code: str, problem_description: str = "", language: str = "python") -> MutationOutput:
        provider = (self.settings.provider or "heuristic").lower()

        if provider in {"", "heuristic", "offline", "none"}:
            return self.fallback.mutate(code, problem_description, language)

        if provider == "llama":
            try:
                mutator = LlamaServerMutator(self.settings)
                return mutator.mutate(code, problem_description, language)
            except Exception as exc:
                fallback = self.fallback.mutate(code, problem_description, language)
                return MutationOutput(
                    code=fallback.code,
                    summary=f"Llama unavailable ({exc}); used heuristic fallback. {fallback.summary}",
                    expected_improvement=fallback.expected_improvement,
                    provider="heuristic-fallback",
                )
    def mutate_action(self, code: str, problem_description: str = "") -> MutationOutput:
        provider = (self.settings.provider or "heuristic").lower()

        if provider in {"", "heuristic", "offline", "none"}:
            return self.fallback.mutate(code, problem_description, "python")

        if provider in {"llama", "llama-server"}:
            try:
                mutator = LlamaServerMutator(self.settings)
                return mutator.mutate_action(code, problem_description)
            except Exception as exc:
                fallback = self.fallback.mutate(code, problem_description, "python")
                return MutationOutput(
                    code=fallback.code,
                    summary=f"Llama action mode unavailable ({exc}); used heuristic fallback. {fallback.summary}",
                    expected_improvement=fallback.expected_improvement,
                    provider="heuristic-fallback",
                )

        return MutationOutput(
            code=code,
            summary=f"Unsupported provider '{provider}'; original code preserved.",
            expected_improvement="",
            provider="provider-error",
        )