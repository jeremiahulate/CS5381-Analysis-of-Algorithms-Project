# Mutation Strategies

## Overview

Mutations modify code to explore new solutions while preserving syntax. Used in random and LLM-guided modes.

## Types of Mutations

1. **Add Comment**: Append a harmless comment.
2. **Replace Literal**: Swap keywords (e.g., "eat_food" ↔ "run_away").
3. **Insert Line**: Add a safe line (e.g., "pass").

## Pseudocode for Random Mutation

```python
def random_mutation(code, rng):
    mutations = [add_comment, replace_literal, insert_line]
    for _ in range(5):  # attempts
        mut = rng.choice(mutations)
        new_code = mut(code, rng)
        if is_valid_python(new_code):
            return new_code
    return add_comment(code, rng)  # fallback
```

## LLM-Guided Mutation

- Retrieve relevant docs from vector DB.
- Prompt LLM: "Improve this code using context: {docs}"
- Validate output syntax.

## Examples

- Original: `if ghost: run_away`
- Mutated: `if ghost: run_away  # mutation applied`

## Code Snippet (from engine.py)

```python
def mutate_replace_literal(code, rng):
    replacements = [("eat_food", "move_randomly"), ("True", "False")]
    for old, new in replacements:
        if old in code:
            return code.replace(old, new, 1)
    return mutate_add_comment(code, rng)
```
