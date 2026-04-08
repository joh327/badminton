# Changelog

## 2026-04-09

### Added
- **Match history upload** (`upload`) — Import past match results from a CSV file. First line is the date (YYYY-MM-DD), pairs as `name1,name2`, games separated by `---`. Rejects unknown players.
- **Date support in `--csv`** — The attending list file can now have an optional date (YYYY-MM-DD) on the first line. If present, the session is saved with that date instead of today. If absent, it works as before.
- **Automatic session ordering** — Sessions in `data.json` are now sorted by date on every save, so uploaded historical sessions slot into the correct position.
- **Delete sessions by date** (`delete-session`) — Remove all sessions for a given date.
- **Clear all sessions** (`clear-sessions`) — Remove all session history at once.
- **Clear all players** (`clear-players`) — Remove all registered players at once.

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
