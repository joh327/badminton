# Badminton Partner Assignment Tool

A CLI tool for organizing badminton doubles sessions. Automatically generates fair court pairings while tracking history to ensure variety across sessions.

## Features

- **Smart pairing generation** — Assigns doubles partners using constraint-based optimization (5,000 random attempts per game, scored by fairness)
  - Prefers mixed-gender pairs (male + female)
  - No repeated partners within the same session
  - Avoids recent partners from past sessions (configurable lookback window)
  - Spreads same-gender pairings fairly across players
- **Player management** — Add, remove, list, and bulk-register players
- **Session history** — Every generated session is saved with date and pairings
- **Stats and analysis** — View per-player partner history or analyze a session for fairness
- **Unicode support** — Player names can use any characters (Korean, Japanese, etc.)

## Requirements

- Python 3.6+
- No external dependencies

## Usage

### Player Management

```bash
# Add a single player
python badminton.py add Alice F
python badminton.py add Jake M

# Bulk register from a file (name,gender per line — skips existing players)
python badminton.py bulk-add players.txt

# List all players
python badminton.py players

# Show player count
python badminton.py count

# Remove a player
python badminton.py remove Alice
```

The bulk-add file format is one `name,gender` per line:

```
Alice,F
Jake,M
```

### Generate Pairings

```bash
# Generate pairings for all registered players
python badminton.py generate

# Generate with specific attending players
python badminton.py generate --attending Alice Jake Tom Eve Carol Leo Grace Ryan

# Generate from an attending list file (one name per line)
python badminton.py generate --csv attending.txt

# Adjust lookback window (default: 2 sessions)
python badminton.py generate --lookback 3
```

The `--csv` file format is one name per line:

```
Alice
Jake
Tom
Eve
```

### History and Analysis

```bash
# View last 5 sessions
python badminton.py history

# View last N sessions
python badminton.py history -n 10

# View stats for a player (last 5 sessions by default)
python badminton.py stats Alice
python badminton.py stats Alice --lookback 10

# Analyse the most recent session
python badminton.py analyse
python badminton.py analyse --lookback 3
```

## Data Storage

All data is stored in `data.json` in the same directory as the script. It contains:

- **players** — List of registered players with name and gender
- **sessions** — History of all generated sessions with date, lookback value, and game pairings

## How Pairing Works

For each game in a session (default: 2 games), the tool:

1. Generates 5,000 random pairings
2. Scores each pairing based on constraints:
   - **Hard constraints** (score +10,000): No repeated partner within the session; no same-gender pair if the player already had one this session
   - **Soft constraints** (score +100): Avoid partners from recent sessions; penalize same-gender pairs for players who had one recently
3. Picks the lowest-scoring (fairest) pairing
