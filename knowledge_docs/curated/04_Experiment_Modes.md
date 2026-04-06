# Experiment Modes to Compare

## Mode 1: Single-Shot LLM

- **Description**: Ask LLM once for a complete solution, evaluate it.
- **No Evolution**: Baseline for comparison.
- **Pros/Cons**: Fast but may not improve iteratively.
- **Pseudocode**:
  ```
  solution = llm.generate("Write Pacman agent")
  metrics = evaluate(solution)
  return metrics
  ```

## Mode 2: Random Mutation (Evolution without Guidance)

- **Description**: Mutate baseline randomly each generation.
- **Mutations**: Add comments, replace tokens, insert lines (syntax-safe).
- **Pros/Cons**: Explores blindly; may find good variants by chance.
- **Pseudocode**:
  ```
  for gen in generations:
      candidates = [mutate_random(parent) for _ in population]
      evaluate_and_select(candidates)
  ```

## Mode 3: LLM-Guided Mutation (Evolution with Retrieval)

- **Description**: Use retrieval + LLM to propose targeted improvements.
- **Retrieval**: Query vector DB for relevant code/docs.
- **Pros/Cons**: Smarter mutations; requires knowledge corpus.
- **Pseudocode**:
  ```
  for gen in generations:
      context = retrieve_relevant_docs(parent)
      candidates = [llm.mutate(parent, context) for _ in population]
      evaluate_and_select(candidates)
  ```

## Comparison Metrics

- **Best Fitness Achieved**: Highest score across runs.
- **Fitness Progression**: Plot best fitness vs. generation.
- **Runtime**: Time per generation/mode.
- **Stability**: Variance in results across seeds.

## Example Comparison Table

| Mode        | Best Fitness | Generations | Runtime (s) |
| ----------- | ------------ | ----------- | ----------- |
| Single-Shot | 85.2         | 1           | 5           |
| Random      | 92.1         | 10          | 50          |
| LLM-Guided  | 98.5         | 10          | 120         |
