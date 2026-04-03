# Chess Engine
- A simple chess engine with minimax + alpha-beta pruning AI.
- Playable on: (https://chess-smoky-eta.vercel.app/)

# AI Details
- Algorithm: Negamax with alpha-beta pruning
- Evaluation: Material + piece-square tables (PST)
- Move ordering: MVV-LVA (Most Valuable Victim – Least Valuable Attacker) for better pruning
- Depth: Configurable 1–5 (5 is fairly slow even with pruning)
