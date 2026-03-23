# Fitness and Metrics

Pacman evaluation returns:
- score
- survival_time
- steps (cost)

Fitness example:
fitness = w1*score + w2*survival_time - w3*steps
with w1 + w2 + w3 = 1

Notes:
- Higher fitness is better
- All candidates must be evaluated with the same settings for fairness