from __future__ import annotations

import ast
import json
import os
from dataclasses import dataclass
from typing import Any


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


DEFAULT_MODEL = "gpt-4o-mini"


def is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


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


class OpenAICompatibleMutator:
    """
    Optional API-backed mutator for OpenAI-compatible chat endpoints.
    """

    def __init__(self, settings: LLMSettings):
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "The 'openai' package is not installed. Install it or use heuristic mode."
            ) from exc

        api_key = settings.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("No API key provided for OpenAI-compatible mutation.")

        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if settings.base_url:
            client_kwargs["base_url"] = settings.base_url

        self.client = OpenAI(**client_kwargs)
        self.model = settings.model or os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
        self.temperature = settings.temperature
        self.provider = settings.provider

    def mutate(self, code: str, problem_description: str = "", language: str = "python") -> MutationOutput:
        prompt = f"""
You are an algorithm-improvement agent inside an evolutionary search loop.

Rules:
- Make one small targeted improvement.
- Preserve the overall structure.
- Keep the output valid {language} when possible.
- Return strict JSON only.

Problem description:
{problem_description.strip() or '(not provided)'}

Current candidate code:
{code}

Return JSON with keys:
modified_code, mutation_summary, expected_improvement
""".strip()

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": "You improve algorithm candidates with small safe mutations."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        mutated = str(data.get("modified_code", code)).strip() or code

        if language.lower() == "python" and not is_valid_python(mutated):
            mutated = code.rstrip() + "\n# llm mutation rejected due to invalid syntax"
            summary = "LLM output was invalid Python; preserved original code with note."
        else:
            summary = str(data.get("mutation_summary", "LLM-guided mutation applied."))

        return MutationOutput(
            code=mutated,
            summary=summary,
            expected_improvement=str(data.get("expected_improvement", "")),
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

        try:
            mutator = OpenAICompatibleMutator(self.settings)
            return mutator.mutate(code, problem_description, language)
        except Exception as exc:
            fallback = self.fallback.mutate(code, problem_description, language)
            return MutationOutput(
                code=fallback.code,
                summary=f"API mutation unavailable ({exc}); used heuristic fallback. {fallback.summary}",
                expected_improvement=fallback.expected_improvement,
                provider="heuristic-fallback",
            )
