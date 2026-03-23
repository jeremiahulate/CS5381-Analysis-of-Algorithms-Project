# Project Overview (AlgoChat)

Goal: Improve a baseline algorithm automatically over multiple generations.

Loop:
1) Generate candidate solutions (mutations of the baseline)
2) Evaluate each candidate in the Pacman environment
3) Compute fitness (one number)
4) Select best (top-1 or top-k)
5) Repeat for N generations

Outputs:
- Best fitness per generation (logged)
- Best final solution
- Plot: best fitness vs generation