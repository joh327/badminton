# Badminton Partner Assignment Tool

A CLI tool for organizing badminton doubles sessions. Automatically generates fair court pairings while tracking history to ensure variety across sessions.

## Features

- **Smart pairing generation** — Assigns doubles partners using constraint-based optimization (5,000 random attempts per game, scored by fairness)
  - Prefers mixed-gender pairs (male + female)
  - No repeated partners within the same session
  - Avoids recent partners from past sessions (configurable lookback window)
  - Spreads same-gender pairings fairly across players
- **Player management** — Add, remove, list, and bulk-register players
- **Match history upload** — Import past session results from CSV files to seed the history
- **Session history** — Every generated session is saved with date and pairings, sorted chronologically
- **Stats and analysis** — View per-player partner history or analyze a session for fairness
- **Unicode support** — Player names can use any characters (Korean, Japanese, etc.)

## Requirements

- Python 3.6+
- No external dependencies

## Usage

### Player Management

```bash
# Add a single player (level is optional: B=beginner, I=intermediate)
python badminton.py add Alice F
python badminton.py add Jake M B
python badminton.py add Eve F I

# Bulk register from a file (name,gender[,level] per line — skips existing players)
python badminton.py bulk-add players.txt

# Update a player's skill level
python badminton.py set-level Alice I

# List all players (shows level)
python badminton.py players

# Show player count
python badminton.py count

# Remove a player
python badminton.py remove Alice

# Clear all players
python badminton.py clear-players
```

The bulk-add file format is one `name,gender[,level]` per line (level is optional):

```
Alice,F,B
Jake,M,I
Eve,F
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

# Save results to output/ folder
python badminton.py generate --csv attending.txt --output results.txt
```

The `--csv` file format is one name per line, with an optional date on the first line:

```
2026-04-09
Alice
Jake
Tom
Eve
```

If the first line is a valid date (YYYY-MM-DD), the session is saved with that date. Otherwise it's treated as a name and today's date is used.

### Upload Match History

Import past match results so they're used in future pairing generation:

```bash
python badminton.py upload history.csv
```

The upload CSV format:

```
2026-03-25
Alice,Jake
Carol,Leo
Eve,Tom
---
Alice,Leo
Carol,Tom
Eve,Jake
```

- First line: date (YYYY-MM-DD, required)
- Each line: a pair as `name1,name2`
- `---` separates games within the session
- All players must be registered first (use `add` or `bulk-add`)

Sessions are automatically sorted by date in the database.

### Manage Sessions

```bash
# Delete all sessions for a specific date
python badminton.py delete-session 2026-03-25

# Clear all session history
python badminton.py clear-sessions
```

### History and Analysis

```bash
# View last 5 sessions
python badminton.py history

# View last N sessions
python badminton.py history -n 10

# View sessions for a specific date
python badminton.py history --date 2026-04-01

# Save history to output/ folder
python badminton.py history --date 2026-04-01 --output session.txt

# View stats for a player (last 5 sessions by default)
python badminton.py stats Alice
python badminton.py stats Alice --lookback 10

# Analyse the most recent session
python badminton.py analyse
python badminton.py analyse --lookback 3
```

## Data Storage

All data is stored in `data.json` in the same directory as the script. It contains:

- **players** — List of registered players with name, gender, and optional skill level
- **sessions** — History of all generated sessions with date, lookback value, and game pairings

## How Pairing Works

For each game in a session (default: 2 games), the tool:

1. Generates 5,000 random pairings
2. Scores each pairing based on constraints:
   - **Hard constraints** (score +10,000): No repeated partner within the session; no same-gender pair if the player already had one this session
   - **Soft constraints** (score +100): Avoid partners from recent sessions; penalize same-gender pairs for players who had one recently
   - **Skill level** (score +25, lowest priority): Game 1 prefers different-level partners; Game 2 prefers same-level partners. Only applies when both players have a level set.
3. Picks the lowest-scoring (fairest) pairing
