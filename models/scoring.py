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
    Calculate a single player's score based on position (HARSH MODE).

    Position-specific weights with stricter normalization:
    - G (Guards): Points 35%, Assists 25%, FG% 10%, 3P% 10%, Steals 10%
    - F (Forwards): Points 30%, Rebounds 25%, FG% 20%, Assists 10%, Steals 8%, Blocks 7%
    - C (Centers): Points 28%, Rebounds 28%, FG% 18%, Blocks 15%, Assists 6%, Steals 5%

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

    # Base score calculation by position (STRICTER NORMALIZATION)
    if position == 'G':
        # Guard formula - stricter divisors
        score = (
                (points / 28) * 35 +           # 35% weight (28 PPG is elite for guards)
                (assists / 6) * 25 +           # 25% weight (6 APG is solid)
                (fg_pct / 48) * 10 +           # 10% weight (48% is elite FG)
                (three_pct / 38) * 10 +        # 10% weight (38% is good 3P)
                (steals / 1.8) * 10            # 10% weight (1.8 SPG is solid)
        )
    elif position == 'F':
        # Forward formula - stricter divisors
        score = (
                (points / 20) * 30 +           # 30% weight (20 PPG is solid for forwards)
                (rebounds / 5.5) * 25 +        # 25% weight (5.5 RPG is solid)
                (fg_pct / 48) * 20 +           # 20% weight (48% is good)
                (assists / 3.5) * 10 +         # 10% weight (3.5 APG is solid)
                (steals / 1.1) * 8 +           # 8% weight (1.1 SPG is good)
                (blocks / 0.6) * 7             # 7% weight (0.6 BPG is solid)
        )
    elif position == 'C':
        # Center formula - stricter divisors
        score = (
                (points / 19) * 28 +           # 28% weight (19 PPG is solid for centers)
                (rebounds / 9) * 28 +          # 28% weight (9 RPG is solid)
                (fg_pct / 54) * 18 +           # 18% weight (54% is elite for centers)
                (blocks / 1.2) * 15 +          # 15% weight (1.2 BPG is good)
                (assists / 2.3) * 6 +          # 6% weight (2.3 APG is decent)
                (steals / 0.75) * 5            # 5% weight (0.75 SPG is decent)
        )
    else:
        # Default to guard if position unknown
        score = (points / 28) * 50 + (assists / 6) * 50

    # VOLUME PENALTIES (replaces starter bonus)
    # Penalize players with low games or low minutes
    if games < 50:
        score *= 0.75  # 25% penalty for limited games
    elif games < 60:
        score *= 0.85  # 15% penalty for lower game count

    if minutes < 20:
        score *= 0.80  # 20% penalty for bench players
    elif minutes < 25:
        score *= 0.90  # 10% penalty for limited minutes

    # Slight volume bonus for high-usage players (not a big boost)
    if games >= 70 and minutes >= 32:
        score *= 1.05  # Only 5% bonus (was 10%)

    # Cap score at 100
    score = min(score, 100)
    score = max(score, 0)

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