# Changelog

## 2026-04-09

### Added
- **Match history upload** (`upload`) — Import past match results from a CSV file. First line is the date (YYYY-MM-DD), pairs as `name1,name2`, games separated by `---`. Rejects unknown players.
- **Date support in `--csv`** — The attending list file can now have an optional date (YYYY-MM-DD) on the first line. If present, the session is saved with that date instead of today. If absent, it works as before.
- **Automatic session ordering** — Sessions in `data.json` are now sorted by date on every save, so uploaded historical sessions slot into the correct position.
- **Delete sessions by date** (`delete-session`) — Remove all sessions for a given date.
- **Clear all sessions** (`clear-sessions`) — Remove all session history at once.
- **Clear all players** (`clear-players`) — Remove all registered players at once.
- **Skill levels** (`B` beginner, `I` intermediate) — Players can now have a skill level. Game 1 softly prefers different-level partners; Game 2 softly prefers same-level partners (lowest weight constraint at +25).
- **Set skill level** (`set-level`) — Update an existing player's skill level.
- **Skill level in `add`** — Optional third argument: `add Alice F B`.
- **Skill level in `bulk-add`** — Optional third column: `name,gender,level` (backwards compatible with `name,gender`).
- **Level display** — `players` list and `generate` output now show skill level info.
- **Output to file** — `generate` always saves results to `output/<date>.txt` (e.g. `output/20260409.txt`). Override with `--output custom.txt`. `history --date` also auto-saves to the same format.
- **Filter history by date** (`history --date`) — View sessions for a specific date only.

### Changed
- **`bulk-add` updates skill levels** — If a player already exists and the file has a different level, the level is updated instead of skipping silently.
- **Removed court numbers from output** — `generate` and `history` no longer show court assignments.

## 2026-04-08

### Added
- **Bulk player registration** (`bulk-add`) — Register multiple players from a file (`name,gender` per line). Skips players that already exist in the database.
- **Player count command** (`count`) — Displays male, female, and total player counts.
- **CSV attending list** (`generate --csv`) — Load attending player names from a file (one name per line) instead of listing them on the command line.
- **README.md** — Documentation for all commands and features.
- **CHANGELOG.md** — This file.

### Fixed
- **Whitespace stripping on all inputs** — All name inputs are now stripped of leading/trailing whitespace across `add`, `remove`, `generate --attending`, and `stats` commands.

## 2026-04-01

### Initial version
- Player management: `add`, `remove`, `players`
- Pairing generation with constraint-based optimization: `generate`
  - Mixed-gender preference, no in-session repeats, recent partner avoidance
  - Configurable lookback window (`--lookback`)
  - Attending player filter (`--attending`)
- Session history: `history`
- Player stats: `stats`
- Session analysis: `analyse`
- Unicode support (`ensure_ascii=False` in JSON storage)
