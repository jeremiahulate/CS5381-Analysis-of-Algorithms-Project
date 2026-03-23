# Experiment Modes to Compare

Mode 1: Single-shot LLM (no evolution)
- Ask LLM once for a solution, evaluate it.

Mode 2: Random mutation (evolution without LLM guidance)
- Generate candidates by random small changes.

Mode 3: LLM-guided mutation (evolution with LLM)
- Use retrieval + LLM prompts to propose improvements each generation.

Compare using:
- Best fitness achieved
- Fitness progression plot across generations
- Runtime