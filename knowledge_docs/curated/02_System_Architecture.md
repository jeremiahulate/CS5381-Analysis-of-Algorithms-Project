# System Architecture (High Level)

Main components:
- UI: user selects mode and parameters, sees plots and best solution
- Candidate Generator: creates new code candidates (random/template/LLM)
- Retrieval Module (local): finds relevant templates/examples from vector DB
- Evaluator: runs candidates in Pacman and collects metrics
- Fitness Function: combines metrics into one fitness score
- Selector: keeps the best candidate(s)
- Logger: saves scores and plots

Data flow:
UI -> Generator (+retrieval) -> Evaluator -> Fitness -> Selector -> Logger -> UI