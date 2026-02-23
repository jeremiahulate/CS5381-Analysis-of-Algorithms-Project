Round 1 Report (Draft) — CS5381

 
Group Members: 
GitHub Repo Link: 

Proposal (Objective)
This Round 1 document describes our planned system framework for a simplified evolutionary agent inspired by AlphaEvolve. The agent will generate candidate solutions using an LLM, evaluate them with a fitness score (Pacman use case), select the best candidate(s), and iterate across generations to improve fitness.

System Framework (High-Level Design)

Candidate Generation
For each generation, the system will generate multiple candidate programs based on the user’s initial code snippet (any language) or algorithm description (pseudocode/text). Candidate generation will include:
- random perturbation of parameters,
- replacing code fragments using templates,
- applying mutation rules (example: swapping two lines of code),
- and LLM-based improvement via a small LLM API (minimum: prompt-based improvement).

Evaluation (Fitness)
Each candidate will be evaluated in the Pacman use case and assigned a fitness score. Possible evaluation metrics include score, steps (cost), and survival time. A sample fitness function is:
Fitness = w1 × score + w2 × survival_time − w3 × steps**, where weights sum to 1.
(Exact weights will be chosen during experimentation.)

Selection and Iteration
After evaluation, the system will select either the single best candidate or the top-k candidates (top-k selection) to generate the next iteration. This process repeats for *n* generations and should show improvement in fitness across iterations.
