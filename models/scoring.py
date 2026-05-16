"""
Position-specific scoring formulas for NBA players (HARSH MODE).
No pandas required - pure Python.
"""

NBA_STRUCTURE = {
    # Eastern Conference
    'BOS': {'conference': 'East', 'division': 'Atlantic'},
    'BRK': {'conference': 'East', 'division': 'Atlantic'},
    'NYK': {'conference': 'East', 'division': 'Atlantic'},
    'PHI': {'conference': 'East', 'division': 'Atlantic'},
    'TOR': {'conference': 'East', 'division': 'Atlantic'},

    'CHI': {'conference': 'East', 'division': 'Central'},
    'CLE': {'conference': 'East', 'division': 'Central'},
    'DET': {'conference': 'East', 'division': 'Central'},
    'IND': {'conference': 'East', 'division': 'Central'},
    'MIL': {'conference': 'East', 'division': 'Central'},

    'ATL': {'conference': 'East', 'division': 'Southeast'},
    'CHO': {'conference': 'East', 'division': 'Southeast'},
    'MIA': {'conference': 'East', 'division': 'Southeast'},
    'ORL': {'conference': 'East', 'division': 'Southeast'},
    'WAS': {'conference': 'East', 'division': 'Southeast'},

    # Western Conference
    'DEN': {'conference': 'West', 'division': 'Northwest'},
    'MIN': {'conference': 'West', 'division': 'Northwest'},
    'OKC': {'conference': 'West', 'division': 'Northwest'},
    'POR': {'conference': 'West', 'division': 'Northwest'},
    'UTA': {'conference': 'West', 'division': 'Northwest'},

    'GSW': {'conference': 'West', 'division': 'Pacific'},
    'LAC': {'conference': 'West', 'division': 'Pacific'},
    'LAL': {'conference': 'West', 'division': 'Pacific'},
    'PHO': {'conference': 'West', 'division': 'Pacific'},
    'SAC': {'conference': 'West', 'division': 'Pacific'},

    'DAL': {'conference': 'West', 'division': 'Southwest'},
    'HOU': {'conference': 'West', 'division': 'Southwest'},
    'MEM': {'conference': 'West', 'division': 'Southwest'},
    'NOP': {'conference': 'West', 'division': 'Southwest'},
    'SAS': {'conference': 'West', 'division': 'Southwest'},
}

DIVISIONS = ['Atlantic', 'Central', 'Southeast', 'Northwest', 'Pacific', 'Southwest']
CONFERENCES = ['East', 'West']


def _build_team_stats(team_code, players):
    """Build a comprehensive stats dict for a team from its players list."""
    if not players:
        return None

    n = len(players)
    structure = NBA_STRUCTURE.get(team_code, {'conference': 'Unknown', 'division': 'Unknown'})
    top_player = max(players, key=lambda p: p.get('Score', 0))

    # Only include players who logged meaningful minutes (≥12 mpg, ≥10 team games).
    # Deep bench players with garbage-time stats skew the weighted average without
    # contributing to wins, so we exclude them from the quality calculation.
    rotation = [
        p for p in players
        if p.get('Minutes', 0) >= 12 and p.get('Games_For_Team', p.get('Games', 0)) >= 10
    ]
    if not rotation:
        rotation = players  # fallback if entire roster is filtered

    # Weight each player by minutes × games played for this team so that:
    # - starters who log 35 min over 80 games dominate the team score
    # - bench players and mid-season trades contribute proportionally less
    def _weight(p):
        g = p.get('Games_For_Team', p.get('Games', 1))
        return max(0.1, g * p.get('Minutes', 1))

    # Cap to top 10 by weight so teams with large rosters aren't penalized relative
    # to teams with leaner rosters — every team is judged on its best 10 contributors.
    rotation_sorted = sorted(rotation, key=_weight, reverse=True)[:10]

    weights = [_weight(p) for p in rotation_sorted]
    total_weight = sum(weights)
    raw_avg = (
        sum(p.get('Score', 0) * w for p, w in zip(rotation_sorted, weights)) / total_weight
    ) if total_weight > 0 else 0

    # Star amplification: MVP-caliber players win more games than the weighted
    # average suggests. Add a bonus proportional to how much the star exceeds the
    # team average, capped at +12 points. This helps teams like OKC (SGA) and CLE
    # (Mitchell) which are otherwise underrated because of defensive-only depth players.
    top_score = max(p.get('Score', 0) for p in rotation_sorted) if rotation_sorted else 0
    star_gap = max(0.0, top_score - raw_avg)
    star_bonus = min(12.0, star_gap * 0.28) if top_score >= 88 else 0.0

    total_score = round(raw_avg + star_bonus, 2)

    return {
        'Team': team_code,
        'Conference': structure['conference'],
        'Division': structure['division'],
        'Total_Score': total_score,
        'Num_Players': n,
        'Avg_Points': round(sum(p.get('Points', 0) for p in players) / n, 1),
        'Avg_Assists': round(sum(p.get('Assists', 0) for p in players) / n, 1),
        'Avg_Rebounds': round(sum(p.get('Rebounds', 0) for p in players) / n, 1),
        'Avg_Steals': round(sum(p.get('Steals', 0) for p in players) / n, 2),
        'Avg_Blocks': round(sum(p.get('Blocks', 0) for p in players) / n, 2),
        'Avg_FG': round(sum(p.get('FG%', 0) for p in players) / n * 100, 1),
        'Avg_3P': round(sum(p.get('3P%', 0) for p in players) / n * 100, 1),
        'Avg_FT': round(sum(p.get('FT%', 0) for p in players) / n * 100, 1),
        'Avg_Minutes': round(sum(p.get('Minutes', 0) for p in players) / n, 1),
        'Top_Player': top_player.get('Player', ''),
        'Top_Player_Score': round(top_player.get('Score', 0), 2),
    }


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
        # Steals raised to 15% to give credit to defensive-minded guards (e.g. elite defenders)
        score = (
                (points / 28) * 32 +
                (assists / 6) * 23 +
                (fg_pct / 48) * 10 +
                (three_pct / 38) * 10 +
                (steals / 1.5) * 15 +
                (rebounds / 4.0) * 10
        )
    elif position == 'F':
        # Blocks raised to 10%, steals to 10%; rebounds reference raised to 7 to dampen
        # extreme rebound totals and better balance the position formula
        score = (
                (points / 20) * 28 +
                (rebounds / 7.0) * 22 +
                (fg_pct / 48) * 15 +
                (assists / 3.5) * 10 +
                (steals / 1.0) * 13 +
                (blocks / 0.8) * 12
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

        # Blocks raised to 20% to reward shot-blockers more
        score = (
                (points / 19) * 25 +
                (rebounds / 9) * 25 +
                (fg_pct / 54) * 10 +
                (blocks / 1.2) * 20 +
                (assists / 2.3) * 8 +
                (steals / 0.75) * 7 +
                (rebounds / 9) * 5
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

    Returns:
        List of team stat dicts sorted by Total_Score descending, with Team_Rank added.
    """
    team_buckets = {}
    for player in players_list:
        team = player.get('Team', 'UNK')
        if team not in team_buckets:
            team_buckets[team] = []
        team_buckets[team].append(player)

    team_stats = [
        _build_team_stats(code, players)
        for code, players in team_buckets.items()
        if players
    ]

    sorted_teams = sorted(team_stats, key=lambda x: x['Total_Score'], reverse=True)
    for i, t in enumerate(sorted_teams, 1):
        t['Team_Rank'] = i

    return sorted_teams


def compare_teams(players_list, team1_code, team2_code):
    """
    Compare two teams head-to-head across all stats.

    Returns:
        Dict with team1, team2 stats and winner (team code or 'tie').
    """
    t1 = team1_code.upper()
    t2 = team2_code.upper()

    t1_players = [p for p in players_list if p.get('Team', '').upper() == t1]
    t2_players = [p for p in players_list if p.get('Team', '').upper() == t2]

    if not t1_players or not t2_players:
        return None

    stats1 = _build_team_stats(t1, t1_players)
    stats2 = _build_team_stats(t2, t2_players)
    winner = t1 if stats1['Total_Score'] > stats2['Total_Score'] else (
        t2 if stats2['Total_Score'] > stats1['Total_Score'] else 'tie'
    )

    return {'team1': stats1, 'team2': stats2, 'winner': winner}


def get_conference_rankings(players_list):
    """
    Get team rankings split by conference.

    Returns:
        Dict {'East': [...], 'West': [...]} each sorted by Total_Score with Conf_Rank added.
    """
    all_teams = get_team_rankings(players_list)

    east = [t for t in all_teams if t['Conference'] == 'East']
    west = [t for t in all_teams if t['Conference'] == 'West']

    for i, t in enumerate(east, 1):
        t['Conf_Rank'] = i
    for i, t in enumerate(west, 1):
        t['Conf_Rank'] = i

    return {'East': east, 'West': west}


def compare_conferences(players_list):
    """
    Compare Eastern vs Western Conference by aggregated team scores.

    Returns:
        Dict with east stats, west stats, winner, and per-conference team lists.
    """
    conf = get_conference_rankings(players_list)
    east_teams = conf['East']
    west_teams = conf['West']

    def _agg(teams, key):
        return round(sum(t[key] for t in teams) / len(teams), 2) if teams else 0

    def _conf_stats(teams, name):
        return {
            'Conference': name,
            'Total_Score': round(sum(t['Total_Score'] for t in teams) / len(teams), 2) if teams else 0,
            'Num_Teams': len(teams),
            'Avg_Points': _agg(teams, 'Avg_Points'),
            'Avg_Assists': _agg(teams, 'Avg_Assists'),
            'Avg_Rebounds': _agg(teams, 'Avg_Rebounds'),
            'Avg_Steals': _agg(teams, 'Avg_Steals'),
            'Avg_Blocks': _agg(teams, 'Avg_Blocks'),
            'Avg_FG': _agg(teams, 'Avg_FG'),
            'Avg_3P': _agg(teams, 'Avg_3P'),
            'Top_Team': teams[0]['Team'] if teams else '',
            'Top_Team_Score': teams[0]['Total_Score'] if teams else 0,
        }

    east_stats = _conf_stats(east_teams, 'East')
    west_stats = _conf_stats(west_teams, 'West')
    winner = (
        'East' if east_stats['Total_Score'] > west_stats['Total_Score'] else
        ('West' if west_stats['Total_Score'] > east_stats['Total_Score'] else 'tie')
    )

    return {
        'east': east_stats,
        'west': west_stats,
        'winner': winner,
        'east_teams': east_teams,
        'west_teams': west_teams,
    }


def get_division_rankings(players_list):
    """
    Get team rankings split by division.

    Returns:
        Dict keyed by division name, each value is a list of team dicts with Div_Rank.
    """
    all_teams = get_team_rankings(players_list)

    divisions = {}
    for t in all_teams:
        div = t['Division']
        if div not in divisions:
            divisions[div] = []
        divisions[div].append(t)

    for div_teams in divisions.values():
        for i, t in enumerate(div_teams, 1):
            t['Div_Rank'] = i

    return divisions


def compare_divisions(players_list, div1_name, div2_name):
    """
    Compare two divisions head-to-head by aggregated team scores.

    Returns:
        Dict with div1 stats, div2 stats, winner string, and per-division team lists.
    """
    all_divs = get_division_rankings(players_list)
    div1_teams = all_divs.get(div1_name, [])
    div2_teams = all_divs.get(div2_name, [])

    if not div1_teams or not div2_teams:
        return None

    def _div_stats(teams, name):
        n = len(teams)
        return {
            'Division': name,
            'Conference': teams[0]['Conference'] if teams else '',
            'Total_Score': round(sum(t['Total_Score'] for t in teams) / n, 2) if n else 0,
            'Num_Teams': n,
            'Avg_Points': round(sum(t['Avg_Points'] for t in teams) / n, 1),
            'Avg_Assists': round(sum(t['Avg_Assists'] for t in teams) / n, 1),
            'Avg_Rebounds': round(sum(t['Avg_Rebounds'] for t in teams) / n, 1),
            'Avg_Steals': round(sum(t['Avg_Steals'] for t in teams) / n, 2),
            'Avg_Blocks': round(sum(t['Avg_Blocks'] for t in teams) / n, 2),
            'Avg_FG': round(sum(t['Avg_FG'] for t in teams) / n, 1),
            'Avg_3P': round(sum(t['Avg_3P'] for t in teams) / n, 1),
            'Top_Team': teams[0]['Team'],
            'Top_Team_Score': teams[0]['Total_Score'],
        }

    d1 = _div_stats(div1_teams, div1_name)
    d2 = _div_stats(div2_teams, div2_name)
    winner = (
        div1_name if d1['Total_Score'] > d2['Total_Score'] else
        (div2_name if d2['Total_Score'] > d1['Total_Score'] else 'tie')
    )

    return {'div1': d1, 'div2': d2, 'winner': winner, 'div1_teams': div1_teams, 'div2_teams': div2_teams}


def get_playoff_bracket(players_list):
    """
    Generate playoff bracket predictions based on team Total_Score.
    Top 8 per conference = playoff seeds 1-8.
    Higher seed (higher score) always advances.

    Returns:
        Dict with east bracket, west bracket, and nba_finals prediction.
    """
    conf = get_conference_rankings(players_list)

    def _build_bracket(seeds):
        # seeds: list of team dicts sorted by score desc, already seeded 1-8
        first_round = [
            {'seed_hi': seeds[0]['seed'], 'team_hi': seeds[0], 'seed_lo': seeds[7]['seed'], 'team_lo': seeds[7], 'winner': seeds[0]},
            {'seed_hi': seeds[1]['seed'], 'team_hi': seeds[1], 'seed_lo': seeds[6]['seed'], 'team_lo': seeds[6], 'winner': seeds[1]},
            {'seed_hi': seeds[2]['seed'], 'team_hi': seeds[2], 'seed_lo': seeds[5]['seed'], 'team_lo': seeds[5], 'winner': seeds[2]},
            {'seed_hi': seeds[3]['seed'], 'team_hi': seeds[3], 'seed_lo': seeds[4]['seed'], 'team_lo': seeds[4], 'winner': seeds[3]},
        ]
        second_round = [
            {'team_hi': first_round[0]['winner'], 'team_lo': first_round[3]['winner'],
             'winner': first_round[0]['winner']},
            {'team_hi': first_round[1]['winner'], 'team_lo': first_round[2]['winner'],
             'winner': first_round[1]['winner']},
        ]
        conf_finals = {
            'team_hi': second_round[0]['winner'],
            'team_lo': second_round[1]['winner'],
            'winner': second_round[0]['winner'],
        }
        return {'first_round': first_round, 'second_round': second_round, 'conf_finals': conf_finals,
                'champion': conf_finals['winner']}

    east_seeds = conf['East'][:8]
    west_seeds = conf['West'][:8]

    for i, t in enumerate(east_seeds, 1):
        t['seed'] = i
    for i, t in enumerate(west_seeds, 1):
        t['seed'] = i

    east_bracket = _build_bracket(east_seeds)
    west_bracket = _build_bracket(west_seeds)

    e_champ = east_bracket['champion']
    w_champ = west_bracket['champion']
    finals_winner = e_champ if e_champ['Total_Score'] >= w_champ['Total_Score'] else w_champ

    return {
        'east': {'seeds': east_seeds, 'bracket': east_bracket},
        'west': {'seeds': west_seeds, 'bracket': west_bracket},
        'nba_finals': {'east_champion': e_champ, 'west_champion': w_champ, 'winner': finals_winner},
    }


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