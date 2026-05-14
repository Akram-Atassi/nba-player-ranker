"""
Process NBA player stats and calculate rankings.
No pandas required - pure Python.
"""

from data.fetcher import load_stats
from models.scoring import (
    calculate_player_scores,
    rank_players,
    get_team_rankings,
    filter_players,
    compare_players,
    normalize_position
)


def process_all_data():
    """
    Load stats and calculate scores for all players.

    Returns:
        List of player dicts with 'Score' field and normalized 'Position', sorted by score
    """
    print("[processor] Loading player stats...")
    df = load_stats()

    # Convert DataFrame to list of dicts
    players = []
    for row in df.data:
        players.append(row)

    print(f"[processor] Processing {len(players)} players...")

    # Calculate scores (also normalizes positions to G/F/C)
    scored_players = calculate_player_scores(players)

    # Rank by score
    ranked_players = rank_players(scored_players)

    print(f"[processor] Done. Top player: {ranked_players[0]['Player']} ({ranked_players[0]['Score']})")

    return ranked_players


def get_all_teams(players_list):
    """
    Get list of all teams from player list.

    Returns:
        Sorted list of team codes
    """
    teams = set()
    for player in players_list:
        team = player.get('Team', '')
        if team:
            teams.add(team)
    return sorted(list(teams))


def get_all_positions(players_list):
    """
    Get list of all positions from player list.
    Returns normalized positions: G (Guard), F (Forward), C (Center)

    Returns:
        Sorted list of positions
    """
    positions = set()
    for player in players_list:
        pos = player.get('Position', '')
        if pos:
            positions.add(normalize_position(pos))
    return sorted(list(positions))


def get_player_by_name(players_list, name):
    """
    Get a single player by name.

    Returns:
        Player dict or None
    """
    return next((p for p in players_list if p.get('Player', '').lower() == name.lower()), None)


def search_players(players_list, query):
    """
    Search players by name (case-insensitive partial match).

    Returns:
        List of matching players
    """
    query_lower = query.lower()
    return [p for p in players_list if query_lower in p.get('Player', '').lower()]


if __name__ == "__main__":
    print("Loading and processing NBA stats...\n")

    players = process_all_data()

    print("\n=== Top 10 Players ===")
    for i, player in enumerate(players[:10], 1):
        print(f"{i}. {player['Player']} ({player['Team']}, {player['Position']}) - {player['Score']}")

    print("\n=== Team Rankings ===")
    teams = get_team_rankings(players)
    for i, (team, score, count) in enumerate(teams[:10], 1):
        print(f"{i}. {team}: {score} ({count} players)")

    print("\n=== Filter Examples ===")

    # Guards with score > 30
    guards = filter_players(players, position='G', min_score=30)
    print(f"Guards with Score > 30: {len(guards)}")
    for p in guards[:3]:
        print(f"  - {p['Player']}: {p['Score']}")

    # Lakers players
    lakers = filter_players(players, team='LAL')
    print(f"\nLakers players: {len(lakers)}")
    for p in lakers[:3]:
        print(f"  - {p['Player']}: {p['Score']}")