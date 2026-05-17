"""
NBA Player Ranking Tool - Flask Web App
No pandas required - pure Python backend
"""

from flask import Flask, render_template, request, jsonify
from data.processor import (
    process_all_data,
    get_all_teams,
    get_all_positions,
    get_player_by_name,
    search_players
)
from models.scoring import (
    filter_players, get_team_rankings, compare_players,
    compare_teams, get_conference_rankings, compare_conferences,
    get_division_rankings, compare_divisions, get_playoff_bracket,
    DIVISIONS, CONFERENCES,
)

app = Flask(__name__)

# Load data once at startup
print("[app] Loading NBA player data...")
PLAYERS = process_all_data()
TEAMS = get_all_teams(PLAYERS)
POSITIONS = get_all_positions(PLAYERS)
print(f"[app] Ready! {len(PLAYERS)} players, {len(TEAMS)} teams")


@app.route('/')
def index():
    """Home page"""
    top_10 = PLAYERS[:10]
    return render_template('index.html', top_players=top_10)


@app.route('/rankings')
def rankings():
    """Player rankings with filters"""
    # Get filter params from query string
    team = request.args.get('team', '').upper()
    position = request.args.get('position', '').upper()
    min_score = request.args.get('min_score', type=float)
    max_score = request.args.get('max_score', type=float)
    min_minutes = request.args.get('min_minutes', type=float)

    # Apply filters
    filtered = filter_players(
        PLAYERS,
        team=team if team else None,
        position=position if position else None,
        min_score=min_score,
        max_score=max_score,
        min_minutes=min_minutes
    )

    return render_template(
        'rankings.html',
        players=filtered,
        teams=TEAMS,
        positions=POSITIONS,
        selected_team=team,
        selected_position=position,
        min_score_filter=min_score,
        max_score_filter=max_score
    )


@app.route('/player/<player_name>')
def player_detail(player_name):
    """Individual player detail page"""
    player = get_player_by_name(PLAYERS, player_name)

    if not player:
        return "Player not found", 404

    return render_template('player_detail.html', player=player)


@app.route('/teams')
def teams():
    """Teams hub - rankings, comparisons, conference/division views"""
    view = request.args.get('view', 'all')
    team1 = request.args.get('team1', '').upper()
    team2 = request.args.get('team2', '').upper()
    div1 = request.args.get('div1', '')
    div2 = request.args.get('div2', '')

    team_rankings = get_team_rankings(PLAYERS)
    all_team_codes = sorted(t['Team'] for t in team_rankings)

    ctx = {
        'view': view,
        'all_teams': team_rankings,
        'all_team_codes': all_team_codes,
        'divisions': DIVISIONS,
        'conferences': CONFERENCES,
        'selected_team1': team1,
        'selected_team2': team2,
        'selected_div1': div1,
        'selected_div2': div2,
        'comparison': None,
        'conf_data': None,
        'div_comparison': None,
        'conf_rankings': None,
        'div_rankings': None,
    }

    if view == 'conference':
        ctx['conf_rankings'] = get_conference_rankings(PLAYERS)

    elif view == 'division':
        ctx['div_rankings'] = get_division_rankings(PLAYERS)

    elif view == 'compare_teams' and team1 and team2:
        ctx['comparison'] = compare_teams(PLAYERS, team1, team2)

    elif view == 'compare_conferences':
        ctx['conf_data'] = compare_conferences(PLAYERS)

    elif view == 'compare_divisions' and div1 and div2:
        ctx['div_comparison'] = compare_divisions(PLAYERS, div1, div2)

    return render_template('teams.html', **ctx)


@app.route('/playoffs')
def playoffs():
    """Playoff bracket prediction page"""
    bracket = get_playoff_bracket(PLAYERS)
    return render_template('playoffs.html', bracket=bracket)


@app.route('/compare')
def compare():
    """Compare two players"""
    p1_name = request.args.get('player1', '').strip()
    p2_name = request.args.get('player2', '').strip()

    comparison = None
    if p1_name and p2_name:
        comparison = compare_players(PLAYERS, p1_name, p2_name)

    all_player_names = sorted(set(p['Player'] for p in PLAYERS))

    return render_template(
        'compare.html',
        comparison=comparison,
        player1=p1_name,
        player2=p2_name,
        all_players=all_player_names
    )


# ========== API ROUTES ==========

@app.route('/api/players')
def api_players():
    """API endpoint for players (JSON)"""
    team = request.args.get('team', '').upper()
    position = request.args.get('position', '').upper()
    min_score = request.args.get('min_score', type=float)
    max_score = request.args.get('max_score', type=float)
    limit = request.args.get('limit', 100, type=int)

    filtered = filter_players(
        PLAYERS,
        team=team if team else None,
        position=position if position else None,
        min_score=min_score,
        max_score=max_score
    )

    # Limit results
    filtered = filtered[:limit]

    return jsonify({
        'count': len(filtered),
        'players': filtered
    })


@app.route('/api/search')
def api_search():
    """API endpoint for player search (JSON)"""
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify({'results': [], 'error': 'No search query provided'})

    results = search_players(PLAYERS, query)[:20]

    return jsonify({
        'query': query,
        'count': len(results),
        'results': results
    })


@app.route('/api/compare')
def api_compare():
    """API endpoint for player comparison (JSON)"""
    p1 = request.args.get('player1', '').strip()
    p2 = request.args.get('player2', '').strip()

    if not p1 or not p2:
        return jsonify({'error': 'Both player1 and player2 required'}), 400

    comparison = compare_players(PLAYERS, p1, p2)

    if not comparison:
        return jsonify({'error': 'One or both players not found'}), 404

    return jsonify(comparison)


@app.route('/api/teams')
def api_teams():
    """API endpoint for team rankings (JSON)"""
    team_rankings = get_team_rankings(PLAYERS)
    return jsonify({'count': len(team_rankings), 'teams': team_rankings})


@app.route('/api/teams/compare')
def api_teams_compare():
    team1 = request.args.get('team1', '').upper()
    team2 = request.args.get('team2', '').upper()
    if not team1 or not team2:
        return jsonify({'error': 'Both team1 and team2 required'}), 400
    result = compare_teams(PLAYERS, team1, team2)
    if not result:
        return jsonify({'error': 'One or both teams not found'}), 404
    return jsonify(result)


@app.route('/api/conferences')
def api_conferences():
    return jsonify(compare_conferences(PLAYERS))


@app.route('/api/divisions')
def api_divisions():
    div1 = request.args.get('div1', '')
    div2 = request.args.get('div2', '')
    if div1 and div2:
        result = compare_divisions(PLAYERS, div1, div2)
        if not result:
            return jsonify({'error': 'One or both divisions not found'}), 404
        return jsonify(result)
    return jsonify(get_division_rankings(PLAYERS))


@app.route('/api/playoffs')
def api_playoffs():
    return jsonify(get_playoff_bracket(PLAYERS))


@app.route('/api/metadata')
def api_metadata():
    """API endpoint for metadata (teams, positions, etc)"""
    return jsonify({
        'total_players': len(PLAYERS),
        'teams': TEAMS,
        'positions': POSITIONS,
        'score_range': {
            'min': round(min(p.get('Score', 0) for p in PLAYERS), 2),
            'max': round(max(p.get('Score', 0) for p in PLAYERS), 2)
        }
    })


# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)