from __future__ import annotations

import urllib.request
import urllib.error
import ast
import json
import time
from dataclasses import dataclass
from typing import Any
from pathlib import Path


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
    temperature: float = 0.3

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

        # skip banner / block characters
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
            lines = part.splitlines()
            if lines and lines[0].strip().lower() in {"python", "py"}:
                part = "\n".join(lines[1:])
            if "def pacman_agent" in part:
                return part.strip() or original_code

    if "def pacman_agent" in text:
        start = text.find("def pacman_agent")
        return text[start:].strip() or original_code

    return original_code

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
    You are a code mutation engine.

    Return only valid {language} code.
    Return exactly one function named pacman_agent.
    The function signature must be exactly:
    def pacman_agent(state):

    Do not create helper functions.
    Do not rename the function.
    Do not explain anything.
    Do not include markdown.
    Do not output text before or after the code.

    Make exactly one small improvement only.

    Problem:
    {problem_description.strip() or "Improve Pacman behavior while balancing safety and food collection."}

    Original code:
    {code}
    """.strip()

        payload = {
            "prompt": prompt,
            "n_predict": 64,
            "temperature": float(self.temperature),
            "stop": ["```", "\n\n\n"],
        }

        req = urllib.request.Request(
            url=f"{self.base_url}/completion",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        #LLM DEBUG
        print(f"[LLM DEBUG] Calling llama-server at {self.base_url}/completion")

        try:
            start = time.perf_counter()
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            elapsed = time.perf_counter() - start
            #LLM DEBUG
            print(f"[LLM DEBUG] llama-server responded in {elapsed:.2f} seconds")
        except urllib.error.URLError as exc:
            #LLM DEBUG
            print(f"[LLM DEBUG] llama-server request failed: {exc}")
            return MutationOutput(
                code=code,
                summary=f"llama-server unavailable ({exc}); original code preserved.",
                expected_improvement="",
                provider="llama-server-error",
            )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            #LLM DEBUG
            print("[LLM DEBUG] llama-server returned non-JSON output")
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

        bad_markers = ["explanation", "this code", "here is", "to improve"]
        if any(marker in mutated.lower() for marker in bad_markers):
            return MutationOutput(
                code=code,
                summary="llama-server returned explanatory text; original code preserved.",
                expected_improvement="",
                provider=self.provider,
            )

        if language.lower() == "python":
            if not is_valid_python(mutated):
                return MutationOutput(
                    code=code,
                    summary="llama-server returned invalid Python; original code preserved.",
                    expected_improvement="",
                    provider=self.provider,
                )

            if not is_valid_pacman_agent(mutated):
                return MutationOutput(
                    code=code,
                    summary="llama-server changed the required pacman_agent interface; original code preserved.",
                    expected_improvement="",
                    provider=self.provider,
                )

            if not has_valid_pacman_actions(mutated):
                return MutationOutput(
                    code=code,
                    summary="llama-server returned an invalid Pacman action; original code preserved.",
                    expected_improvement="",
                    provider=self.provider,
                )

        return MutationOutput(
            code=mutated,
            summary="Local llama-server mutation applied.",
            expected_improvement="Local server suggested a small targeted refinement.",
            provider=self.provider,
        )
    

class LLMMutator:
    def __init__(self, settings: LLMSettings | None = None):
        self.settings = settings or LLMSettings()
        self.fallback = HeuristicLLMMutator()

    def mutate(self, code: str, problem_description: str = "", language: str = "python") -> MutationOutput:
        provider = (self.settings.provider or "heuristic").lower()
        #LLMDEBUG
        print(f"[LLM DEBUG] Requested provider: {provider}")

        if provider in {"", "heuristic", "offline", "none"}:
            #LLM DEBUG
            print("[LLM DEBUG] Using HEURISTIC mutator")
            return self.fallback.mutate(code, problem_description, language)

        if provider == "llama":
            #LLM DEBUG
            print("[LLM DEBUG] Using LLAMA.CPP mutator")
            try:
                mutator = LlamaServerMutator(self.settings)
                return mutator.mutate(code, problem_description, language)
            except Exception as exc:
                #LLM DEBUG
                print(f"[LLM DEBUG] Llama failed → fallback triggered: {exc}")
                fallback = self.fallback.mutate(code, problem_description, language)
                return MutationOutput(
                    code=fallback.code,
                    summary=f"Llama unavailable ({exc}); used heuristic fallback. {fallback.summary}",
                    expected_improvement=fallback.expected_improvement,
                    provider="heuristic-fallback",
                )