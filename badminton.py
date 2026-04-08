#!/usr/bin/env python3
"""Badminton doubles partner assignment tool with history tracking."""

import argparse
import json
import random
import re
import sys
from datetime import date, datetime
from pathlib import Path
from itertools import combinations

DATA_FILE = Path(__file__).parent / "data.json"
NUM_GAMES = 2
NUM_ATTEMPTS = 5000


def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {"players": [], "sessions": []}


def save_data(data):
    data["sessions"].sort(key=lambda s: s["date"])
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def parse_date(s):
    """Try to parse a YYYY-MM-DD date string. Returns the string if valid, None otherwise."""
    s = s.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return s
        except ValueError:
            pass
    return None


# ── Player management ────────────────────────────────────────────────

def add_player(name, gender):
    data = load_data()
    name = name.strip()
    gender = gender.strip().upper()
    if gender not in ("M", "F"):
        print("Gender must be M or F")
        return
    if any(p["name"] == name for p in data["players"]):
        print(f"'{name}' already exists")
        return
    data["players"].append({"name": name, "gender": gender})
    save_data(data)
    print(f"Added {name} ({gender})")


def remove_player(name):
    data = load_data()
    name = name.strip()
    before = len(data["players"])
    data["players"] = [p for p in data["players"] if p["name"] != name]
    if len(data["players"]) == before:
        print(f"'{name}' not found")
        return
    save_data(data)
    print(f"Removed {name}")


def bulk_add(filepath):
    """Add players from a file. Each line: name,gender (e.g. Alice,F). Skips existing."""
    path = Path(filepath)
    if not path.exists():
        print(f"File not found: {filepath}")
        return
    data = load_data()
    existing = {p["name"] for p in data["players"]}
    added = 0
    skipped = 0
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 2:
            print(f"  Line {lineno}: invalid format '{line}' (expected: name,gender)")
            continue
        name, gender = parts
        gender = gender.upper()
        if gender not in ("M", "F"):
            print(f"  Line {lineno}: invalid gender '{gender}' for '{name}' (must be M or F)")
            continue
        if name in existing:
            print(f"  Skipped '{name}' (already exists)")
            skipped += 1
            continue
        data["players"].append({"name": name, "gender": gender})
        existing.add(name)
        added += 1
        print(f"  Added {name} ({gender})")
    save_data(data)
    print(f"Done: {added} added, {skipped} skipped")


def clear_players():
    data = load_data()
    count = len(data["players"])
    if count == 0:
        print("No players to clear")
        return
    data["players"] = []
    save_data(data)
    print(f"Cleared all {count} player(s)")


def count_players():
    data = load_data()
    males = sum(1 for p in data["players"] if p["gender"] == "M")
    females = sum(1 for p in data["players"] if p["gender"] == "F")
    print(f"Males: {males}")
    print(f"Females: {females}")
    print(f"Total: {males + females}")


def list_players():
    data = load_data()
    if not data["players"]:
        print("No players registered")
        return
    males = sorted(p["name"] for p in data["players"] if p["gender"] == "M")
    females = sorted(p["name"] for p in data["players"] if p["gender"] == "F")
    print(f"Males ({len(males)}):")
    for n in males:
        print(f"  {n}")
    print(f"Females ({len(females)}):")
    for n in females:
        print(f"  {n}")
    print(f"Total: {len(data['players'])}")


# ── History helpers ───────────────────────────────────────────────────

def get_recent_partners(data, lookback):
    """Return dict: player_name -> set of recent partner names."""
    recent = {}
    sessions = data["sessions"][-lookback:] if lookback > 0 else []
    for session in sessions:
        for game in session["games"]:
            for pair in game:
                a, b = pair
                recent.setdefault(a, set()).add(b)
                recent.setdefault(b, set()).add(a)
    return recent


def get_recent_same_gender_players(data, lookback):
    """Return set of player names who had a same-gender partner recently."""
    gender_map = {p["name"]: p["gender"] for p in data["players"]}
    result = set()
    sessions = data["sessions"][-lookback:] if lookback > 0 else []
    for session in sessions:
        for game in session["games"]:
            for pair in game:
                a, b = pair
                if gender_map.get(a) == gender_map.get(b):
                    result.add(a)
                    result.add(b)
    return result


# ── Pairing generation ────────────────────────────────────────────────

def score_pairing(pairs, gender_map, recent_partners, same_gender_recent, current_session_pairs, current_session_sg):
    """Lower score = better. 0 = perfect."""
    score = 0
    for a, b in pairs:
        # Hard: no repeat within current session
        if frozenset((a, b)) in current_session_pairs:
            score += 10000

        # Hard: no same-gender pair if player already had one this session
        if gender_map[a] == gender_map[b]:
            if a in current_session_sg or b in current_session_sg:
                score += 10000

        # Soft: avoid recent partners (from past sessions)
        if a in recent_partners and b in recent_partners[a]:
            score += 100

        # Soft: if same-gender pair, penalize if either player had same-gender recently
        if gender_map[a] == gender_map[b]:
            if a in same_gender_recent or b in same_gender_recent:
                score += 50

    return score


def make_pairs(players, gender_map, recent_partners, same_gender_recent, current_session_pairs, current_session_sg):
    """Generate one game's pairings using weighted random search."""
    n = len(players)
    if n % 2 != 0:
        print(f"ERROR: Need even number of players, got {n}")
        sys.exit(1)

    males = [p for p in players if gender_map[p] == "M"]
    females = [p for p in players if gender_map[p] == "F"]
    n_mixed = min(len(males), len(females))

    best_pairs = None
    best_score = float("inf")

    for _ in range(NUM_ATTEMPTS):
        random.shuffle(males)
        random.shuffle(females)

        pairs = []
        # Mixed pairs first
        for i in range(n_mixed):
            pairs.append((females[i], males[i]))

        # Leftover same-gender pairs
        leftover_f = females[n_mixed:]
        leftover_m = males[n_mixed:]
        leftover = leftover_f + leftover_m
        for i in range(0, len(leftover), 2):
            pairs.append((leftover[i], leftover[i + 1]))

        s = score_pairing(pairs, gender_map, recent_partners, same_gender_recent, current_session_pairs, current_session_sg)
        if s < best_score:
            best_score = s
            best_pairs = pairs[:]
        if s == 0:
            break

    return best_pairs, best_score


def generate(lookback, attending_names=None, session_date=None):
    data = load_data()
    session_date = session_date or str(date.today())

    if attending_names:
        attending_names = [n.strip() for n in attending_names]
        known = {p["name"] for p in data["players"]}
        unknown = [n for n in attending_names if n not in known]
        if unknown:
            print(f"Unknown players: {', '.join(unknown)}")
            return
        players = attending_names
    else:
        players = [p["name"] for p in data["players"]]

    if len(players) < 4:
        print("Need at least 4 players")
        return
    if len(players) % 2 != 0:
        print(f"Need even number of players, got {len(players)}. Sit someone out or add one.")
        return

    gender_map = {p["name"]: p["gender"] for p in data["players"]}
    recent_partners = get_recent_partners(data, lookback)
    same_gender_recent = get_recent_same_gender_players(data, lookback)

    session_games = []
    current_session_pairs = set()
    current_session_sg = set()  # players who already had a same-gender pair this session

    for game_num in range(1, NUM_GAMES + 1):
        pairs, score = make_pairs(players, gender_map, recent_partners, same_gender_recent, current_session_pairs, current_session_sg)

        # Add this game's pairs to session tracker
        for a, b in pairs:
            current_session_pairs.add(frozenset((a, b)))
            if gender_map[a] == gender_map[b]:
                current_session_sg.add(a)
                current_session_sg.add(b)

        session_games.append([[a, b] for a, b in pairs])

        # Print
        print(f"\n{'=' * 55}")
        print(f"  GAME {game_num}" + (f"  (constraint score: {score})" if score > 0 else ""))
        print(f"{'=' * 55}")
        for i, (a, b) in enumerate(pairs, 1):
            tag = ""
            if gender_map[a] == gender_map[b]:
                tag = " [same gender]"
            if a in recent_partners and b in recent_partners[a]:
                tag += " [recent partner]"
            print(f"  Court {i:2d}: {a:>12} + {b}{tag}")

    # Verification
    print(f"\n{'=' * 55}")
    print("  VERIFICATION")
    print(f"{'=' * 55}")
    all_pairs = []
    for game in session_games:
        for pair in game:
            all_pairs.append(frozenset(pair))
    if len(all_pairs) == len(set(all_pairs)):
        print("  ✓ No repeated partners within this session")
    else:
        print("  ✗ WARNING: Some partners repeated within session!")

    # Analysis (before saving, so lookback checks against previous sessions only)
    analyse_session(session_games, data, lookback, players)

    # Save session
    session = {
        "date": session_date,
        "lookback": lookback,
        "games": session_games,
    }
    data["sessions"].append(session)
    save_data(data)
    print(f"  Session saved. (lookback={lookback})")


# ── History view ──────────────────────────────────────────────────────

def show_history(n=5):
    data = load_data()
    sessions = data["sessions"][-n:]
    if not sessions:
        print("No session history")
        return
    gender_map = {p["name"]: p["gender"] for p in data["players"]}
    for session in sessions:
        print(f"\n{'=' * 55}")
        print(f"  Date: {session['date']}  (lookback={session.get('lookback', '?')})")
        print(f"{'=' * 55}")
        for gi, game in enumerate(session["games"], 1):
            print(f"  Game {gi}:")
            for i, pair in enumerate(game, 1):
                a, b = pair
                tag = " [same gender]" if gender_map.get(a) == gender_map.get(b) else ""
                print(f"    Court {i:2d}: {a:>12} + {b}{tag}")


# ── Analysis ──────────────────────────────────────────────────────────

def analyse_session(session_games, data, lookback, attending):
    """Analyse a session's pairings against recent history."""
    gender_map = {p["name"]: p["gender"] for p in data["players"]}
    recent_partners = get_recent_partners(data, lookback)
    same_gender_recent = get_recent_same_gender_players(data, lookback)

    # — Same-gender pairs this session —
    sg_pairs = []
    for gi, game in enumerate(session_games, 1):
        for pair in game:
            a, b = pair
            if gender_map.get(a) == gender_map.get(b):
                sg_pairs.append((gi, a, b))

    # — Same-gender history per player (last N sessions) —
    sg_history = {}  # player -> count of same-gender pairings in lookback
    sessions = data["sessions"][-lookback:] if lookback > 0 else []
    for session in sessions:
        for game in session["games"]:
            for pair in game:
                a, b = pair
                if gender_map.get(a) == gender_map.get(b):
                    sg_history[a] = sg_history.get(a, 0) + 1
                    sg_history[b] = sg_history.get(b, 0) + 1

    # — Recent partner repeats this session —
    repeat_pairs = []
    for gi, game in enumerate(session_games, 1):
        for pair in game:
            a, b = pair
            if a in recent_partners and b in recent_partners[a]:
                repeat_pairs.append((gi, a, b))

    # — Repeat partner frequency per player —
    repeat_counts = {}
    for _, a, b in repeat_pairs:
        repeat_counts[a] = repeat_counts.get(a, 0) + 1
        repeat_counts[b] = repeat_counts.get(b, 0) + 1

    # — Print analysis —
    print(f"\n{'=' * 55}")
    print(f"  ANALYSIS (lookback={lookback})")
    print(f"{'=' * 55}")

    # Same-gender this session
    if sg_pairs:
        print(f"\n  Same-gender pairs this session: {len(sg_pairs)}")
        for gi, a, b in sg_pairs:
            past = sg_history.get(a, 0) + sg_history.get(b, 0)
            hist_note = ""
            if past > 0:
                parts = []
                if sg_history.get(a, 0) > 0:
                    parts.append(f"{a} had {sg_history[a]}x")
                if sg_history.get(b, 0) > 0:
                    parts.append(f"{b} had {sg_history[b]}x")
                hist_note = f" — past {lookback} sessions: {', '.join(parts)}"
            print(f"    Game {gi}: {a} + {b}{hist_note}")
    else:
        print(f"\n  Same-gender pairs this session: 0")

    # Recent partner repeats
    if repeat_pairs:
        print(f"\n  Recent partner repeats this session: {len(repeat_pairs)}")
        for gi, a, b in repeat_pairs:
            print(f"    Game {gi}: {a} + {b}")
        if repeat_counts:
            print(f"  Players with multiple repeat partners:")
            for name, count in sorted(repeat_counts.items(), key=lambda x: -x[1]):
                if count > 1:
                    print(f"    {name}: {count} repeat partners")
    else:
        print(f"\n  Recent partner repeats this session: 0")

    print()


def run_analyse(lookback):
    """Analyse the most recent session."""
    data = load_data()
    if not data["sessions"]:
        print("No sessions to analyse")
        return
    last_session = data["sessions"][-1]
    attending = set()
    for game in last_session["games"]:
        for pair in game:
            attending.update(pair)

    # Analyse against history *before* the last session
    data_before = {
        "players": data["players"],
        "sessions": data["sessions"][:-1],
    }
    print(f"  Analysing session from {last_session['date']}")
    analyse_session(last_session["games"], data_before, lookback, list(attending))


# ── History upload ────────────────────────────────────────────────────

def upload_history(filepath):
    """Upload match history from a CSV file.

    Format:
        2026-04-01
        Alice,Jake
        Carol,Leo
        Eve,Tom
        ---
        Alice,Leo
        Carol,Tom
        Eve,Jake
    """
    path = Path(filepath)
    if not path.exists():
        print(f"File not found: {filepath}")
        return
    data = load_data()
    known = {p["name"] for p in data["players"]}

    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]

    # First non-empty line must be a date
    non_empty = [l for l in lines if l]
    if not non_empty:
        print("File is empty")
        return
    session_date = parse_date(non_empty[0])
    if not session_date:
        print(f"First line must be a date (YYYY-MM-DD), got: '{non_empty[0]}'")
        return

    # Parse games separated by ---
    games = []
    current_game = []
    unknown = set()
    for line in lines[1:]:  # skip the date line (first line, possibly with blank lines before it)
        if not line:
            continue
        if line == non_empty[0]:  # skip if date line appears again
            continue
        if line == "---":
            if current_game:
                games.append(current_game)
                current_game = []
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 2:
            print(f"Invalid pair format: '{line}' (expected: name1,name2)")
            return
        a, b = parts
        if a not in known:
            unknown.add(a)
        if b not in known:
            unknown.add(b)
        current_game.append([a, b])
    if current_game:
        games.append(current_game)

    if unknown:
        print(f"Unknown players (register them first with 'add' or 'bulk-add'):")
        for name in sorted(unknown):
            print(f"  {name}")
        return

    if not games:
        print("No games found in file")
        return

    session = {
        "date": session_date,
        "lookback": 0,
        "games": games,
    }
    data["sessions"].append(session)
    save_data(data)

    total_pairs = sum(len(g) for g in games)
    print(f"Uploaded session for {session_date}: {len(games)} game(s), {total_pairs} pair(s)")


# ── Session management ────────────────────────────────────────────────

def delete_sessions(target_date):
    """Delete all sessions matching a date."""
    data = load_data()
    target_date = target_date.strip()
    if not parse_date(target_date):
        print(f"Invalid date format: '{target_date}' (expected YYYY-MM-DD)")
        return
    before = len(data["sessions"])
    data["sessions"] = [s for s in data["sessions"] if s["date"] != target_date]
    removed = before - len(data["sessions"])
    if removed == 0:
        print(f"No sessions found for {target_date}")
        return
    save_data(data)
    print(f"Removed {removed} session(s) for {target_date}")


def clear_sessions():
    """Remove all sessions."""
    data = load_data()
    count = len(data["sessions"])
    if count == 0:
        print("No sessions to clear")
        return
    data["sessions"] = []
    save_data(data)
    print(f"Cleared all {count} session(s)")


# ── Player stats ──────────────────────────────────────────────────────

def show_stats(name, lookback=5):
    data = load_data()
    name = name.strip()
    gender_map = {p["name"]: p["gender"] for p in data["players"]}
    if name not in gender_map:
        print(f"'{name}' not found")
        return

    sessions = data["sessions"][-lookback:]
    partners = []
    same_gender_count = 0
    for session in sessions:
        for game in session["games"]:
            for pair in game:
                if name in pair:
                    partner = pair[0] if pair[1] == name else pair[1]
                    partners.append((session["date"], partner))
                    if gender_map.get(name) == gender_map.get(partner):
                        same_gender_count += 1

    print(f"\nStats for {name} ({gender_map[name]}) — last {lookback} sessions:")
    print(f"  Same-gender pairings: {same_gender_count}")
    print(f"  Partners:")
    for d, p in partners:
        tag = " [same gender]" if gender_map.get(name) == gender_map.get(p) else ""
        print(f"    {d}: {p}{tag}")


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Badminton partner assignment")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="Add a player")
    p_add.add_argument("name")
    p_add.add_argument("gender", help="M or F")

    p_rm = sub.add_parser("remove", help="Remove a player")
    p_rm.add_argument("name")

    p_bulk = sub.add_parser("bulk-add", help="Bulk register players from file (name,gender per line)")
    p_bulk.add_argument("file", help="Path to file with one 'name,gender' per line")

    sub.add_parser("players", help="List players")
    sub.add_parser("count", help="Show player count")
    sub.add_parser("clear-players", help="Remove all players")

    p_gen = sub.add_parser("generate", help="Generate pairings")
    p_gen.add_argument("--lookback", type=int, default=2, help="Sessions to check (default: 2)")
    p_gen.add_argument("--attending", nargs="+", help="Names of attending players (default: all)")
    p_gen.add_argument("--csv", type=str, help="Path to file with one player name per line")

    p_hist = sub.add_parser("history", help="View session history")
    p_hist.add_argument("-n", type=int, default=5, help="Number of sessions to show")

    p_stats = sub.add_parser("stats", help="View player stats")
    p_stats.add_argument("name")
    p_stats.add_argument("--lookback", type=int, default=5)

    p_analyse = sub.add_parser("analyse", help="Analyse the most recent session")
    p_analyse.add_argument("--lookback", type=int, default=2)

    p_upload = sub.add_parser("upload", help="Upload match history from CSV file")
    p_upload.add_argument("file", help="Path to CSV (date on first line, pairs as name1,name2, --- between games)")

    p_delete = sub.add_parser("delete-session", help="Delete all sessions for a given date")
    p_delete.add_argument("date", help="Date in YYYY-MM-DD format")

    sub.add_parser("clear-sessions", help="Remove all session history")

    args = parser.parse_args()

    if args.command == "add":
        add_player(args.name, args.gender)
    elif args.command == "remove":
        remove_player(args.name)
    elif args.command == "bulk-add":
        bulk_add(args.file)
    elif args.command == "players":
        list_players()
    elif args.command == "count":
        count_players()
    elif args.command == "clear-players":
        clear_players()
    elif args.command == "generate":
        attending = args.attending
        session_date = None
        if args.csv:
            csv_path = Path(args.csv)
            if not csv_path.exists():
                print(f"File not found: {args.csv}")
                sys.exit(1)
            lines = [line.strip() for line in csv_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not lines:
                print(f"No names found in {args.csv}")
                sys.exit(1)
            if parse_date(lines[0]):
                session_date = lines[0]
                lines = lines[1:]
            if not lines:
                print(f"No names found in {args.csv} (only a date)")
                sys.exit(1)
            attending = lines
        generate(args.lookback, attending, session_date)
    elif args.command == "history":
        show_history(args.n)
    elif args.command == "stats":
        show_stats(args.name, args.lookback)
    elif args.command == "analyse":
        run_analyse(args.lookback)
    elif args.command == "upload":
        upload_history(args.file)
    elif args.command == "delete-session":
        delete_sessions(args.date)
    elif args.command == "clear-sessions":
        clear_sessions()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
