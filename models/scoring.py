"""
Position-specific scoring formulas for NBA players (HARSH MODE).
No pandas required - pure Python.
"""


def normalize_position(position):
    """
    Normalize position to G (Guard), F (Forward), or C (Center).

    PG, SG -> G
    SF, PF -> F
    C -> C
    """
    pos = position.upper() if position else 'G'

    if pos in ['PG', 'SG']:
        return 'G'
    elif pos in ['SF', 'PF']:
        return 'F'
    elif pos == 'C':
        return 'C'
    else:
        return 'G'  # Default to guard


def calculate_player_scores(players_list):
    """
    Calculate custom scores for each player based on position.

    Args:
        players_list: List of dicts with player stats

    Returns:
        List of dicts with 'Score' field added and normalized 'Position'
    """
    scored_players = []

    for player in players_list:
        player_copy = player.copy()
        # Normalize position to G/F/C
        player_copy['Position'] = normalize_position(player.get('Position', 'SG'))
        score = calculate_score(player_copy)
        player_copy['Score'] = score
        scored_players.append(player_copy)

    return scored_players


def calculate_score(player):
    """
    Calculate a single player's score based on position.

    Position-specific weights:
    - G (Guards): Points 35%, Assists 25%, FG% 10%, 3P% 10%, Steals 10%
    - F (Forwards): Points 30%, Rebounds 25%, FG% 20%, Assists 10%, Steals 8%, Blocks 7%
    - C (Centers): Points 28%, Rebounds 28%, FG% 18%, Blocks 15%, Assists 6%, Steals 5%
      Centers also apply a 3P volume adjustment and a low-scoring penalty.

    Also includes volume penalties for low games/minutes.
    """

    position = normalize_position(player.get('Position', 'SG'))
    points = float(player.get('Points', 0))
    assists = float(player.get('Assists', 0))
    rebounds = float(player.get('Rebounds', 0))
    steals = float(player.get('Steals', 0))
    blocks = float(player.get('Blocks', 0))
    fg_pct = float(player.get('FG%', 0.450)) * 100  # Convert to 0-100 scale
    three_pct = float(player.get('3P%', 0.350)) * 100
    games = float(player.get('Games', 70))
    minutes = float(player.get('Minutes', 30))

    if position == 'G':
        score = (
                (points / 28) * 35 +
                (assists / 6) * 25 +
                (fg_pct / 48) * 10 +
                (three_pct / 38) * 10 +
                (steals / 1.8) * 10
        )
    elif position == 'F':
        score = (
                (points / 20) * 30 +
                (rebounds / 5.5) * 25 +
                (fg_pct / 48) * 20 +
                (assists / 3.5) * 10 +
                (steals / 1.1) * 8 +
                (blocks / 0.6) * 7
        )
    elif position == 'C':
        three_pa = float(player.get('3PA', 0.0))  # per-game 3P attempts

        # Adjusted 3P% based on volume (penalizes centers who rarely attempt 3s)
        if three_pa < 1.0:
            adjusted_three_pct = three_pct * (three_pa / 1.5)
        else:
            adjusted_three_pct = three_pct

        # 3P modifier: centers with negligible 3P volume are penalized
        if adjusted_three_pct == 0.0:
            three_pt_modifier = 0.82
        elif adjusted_three_pct < 15:
            three_pt_modifier = 0.88
        elif adjusted_three_pct < 20:
            three_pt_modifier = 0.92
        else:
            three_pt_modifier = 1.0

        score = (
                (points / 19) * 28 +
                (rebounds / 9) * 28 +
                (fg_pct / 54) * 8 +
                (blocks / 1.2) * 15 +
                (assists / 2.3) * 6 +
                (steals / 0.75) * 5
        )

        score *= three_pt_modifier

        # Low-scoring center penalty
        if points < 12:
            score *= 0.75
        elif points < 15:
            score *= 0.85
    else:
        score = (points / 28) * 50 + (assists / 6) * 50

    # Games played penalty
    if games < 15:
        score *= 0.50
    elif games < 30:
        score *= 0.70
    elif games < 50:
        score *= 0.82
    elif games < 60:
        score *= 0.90

    # Minutes per game penalty
    if minutes < 20:
        score *= 0.80
    elif minutes < 25:
        score *= 0.90

    # High volume bonus (must meet both thresholds)
    if games >= 70 and minutes >= 32:
        score *= 1.05

    score = min(100, max(0, score))
    return round(score, 2)


def rank_players(players_list):
    """
    Rank players by score (highest first).

    Args:
        players_list: List of dicts with 'Score' field

    Returns:
        Sorted list of players by score descending
    """
    return sorted(players_list, key=lambda p: p.get('Score', 0), reverse=True)


def get_team_rankings(players_list):
    """
    Calculate team rankings by summing player scores.

    Args:
        players_list: List of player dicts with 'Team' and 'Score'

    Returns:
        List of (team, total_score, player_count) tuples sorted by score
    """
    teams = {}

    for player in players_list:
        team = player.get('Team', 'UNK')
        score = player.get('Score', 0)

        if team not in teams:
            teams[team] = {'score': 0, 'count': 0}

        teams[team]['score'] += score
        teams[team]['count'] += 1

    # Convert to list of tuples and sort by score descending
    team_rankings = [
        (team, round(data['score'], 2), data['count'])
        for team, data in teams.items()
    ]

    return sorted(team_rankings, key=lambda x: x[1], reverse=True)


def filter_players(players_list, team=None, position=None, min_score=None, max_score=None, min_minutes=None):
    """
    Filter players by various criteria.

    Args:
        players_list: List of player dicts
        team: Filter by team (e.g., 'LAL')
        position: Filter by position (e.g., 'PG')
        min_score: Minimum score
        max_score: Maximum score
        min_minutes: Minimum minutes per game

    Returns:
        Filtered list of players
    """
    filtered = players_list

    if team:
        filtered = [p for p in filtered if p.get('Team', '').upper() == team.upper()]

    if position:
        filtered = [p for p in filtered if p.get('Position', '').upper() == position.upper()]

    if min_score is not None:
        filtered = [p for p in filtered if p.get('Score', 0) >= min_score]

    if max_score is not None:
        filtered = [p for p in filtered if p.get('Score', 0) <= max_score]

    if min_minutes is not None:
        filtered = [p for p in filtered if p.get('Minutes', 0) >= min_minutes]

    return filtered


def compare_players(players_list, player_name_1, player_name_2):
    """
    Get side-by-side comparison of two players.

    Args:
        players_list: List of player dicts
        player_name_1: Name of first player
        player_name_2: Name of second player

    Returns:
        Dict with 'player1', 'player2', and 'winner' keys
    """
    p1 = next((p for p in players_list if p.get('Player', '').lower() == player_name_1.lower()), None)
    p2 = next((p for p in players_list if p.get('Player', '').lower() == player_name_2.lower()), None)

    if not p1 or not p2:
        return None

    score1 = p1.get('Score', 0)
    score2 = p2.get('Score', 0)
    winner = 'player1' if score1 > score2 else ('player2' if score2 > score1 else 'tie')

    return {
        'player1': p1,
        'player2': p2,
        'winner': winner
    }


if __name__ == "__main__":
    # Test with sample data
    test_players = [
        {
            'Player': 'Luka Dončić',
            'Team': 'LAL',
            'Position': 'PG',
            'Games': 64,
            'Minutes': 35.77,
            'Points': 33.48,
            'Assists': 8.28,
            'Rebounds': 7.73,
            'Steals': 1.64,
            'Blocks': 0.53,
            'FG%': 0.476,
            '3P%': 0.366,
            'FT%': 0.780,
        },
        {
            'Player': 'Nikola Jokić',
            'Team': 'DEN',
            'Position': 'C',
            'Games': 65,
            'Minutes': 34.85,
            'Points': 27.67,
            'Assists': 10.72,
            'Rebounds': 12.86,
            'Steals': 1.42,
            'Blocks': 0.82,
            'FG%': 0.569,
            '3P%': 0.380,
            'FT%': 0.831,
        }
    ]

    scored = calculate_player_scores(test_players)
    ranked = rank_players(scored)

    print("Player Scores:")
    for p in ranked:
        print(f"  {p['Player']} ({p['Position']}) - {p['Score']}")

    print("\nTeam Rankings:")
    teams = get_team_rankings(scored)
    for team, score, count in teams:
        print(f"  {team}: {score} ({count} players)")