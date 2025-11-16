# analysis.py

# Placeholder for Prop Data (You will fetch this from the API later)
# In a real scenario, this data would be passed from the API function.
def get_dummy_prop_data():
    return [
        {'id': 'prop-1', 'name': 'LeBron James', 'market': 'Player Points', 'line': 25.5, 'trend_score': 3, 'game_id': 'LAL@DEN'},
        {'id': 'prop-2', 'name': 'Nikola Jokic', 'market': 'Player Rebounds', 'line': 12.5, 'trend_score': 2, 'game_id': 'LAL@DEN'},
        {'id': 'prop-3', 'name': 'Jayson Tatum', 'market': 'Player Assists', 'line': 5.5, 'trend_score': 3, 'game_id': 'BOS@NYK'},
        {'id': 'prop-4', 'name': 'Luka Doncic', 'market': 'Player Points', 'line': 32.5, 'trend_score': 1, 'game_id': 'DAL@PHX'},
        {'id': 'prop-5', 'name': 'Luka Doncic', 'market': 'Player Assists', 'line': 7.5, 'trend_score': 2, 'game_id': 'DAL@PHX'},
    ]

# --- 1. Prop Trend Analysis (Simplified L/F Score) ---

def get_trend_indicator(score: int):
    """Maps the score (1-3) to a text indicator."""
    if score >= 3:
        return ('LOCK', 'green')
    elif score == 2:
        return ('NEUTRAL', 'orange')
    else:
        return ('FADE', 'red')

# --- 2. Slip Analyzer Logic (Correlation Risk) ---

def analyze_slip_risk(slip_selections: list):
    """Analyzes the slip for correlation risk and assigns a warning."""
    if not slip_selections:
        return 0, None, 0

    correlation_warning = None
    correlation_penalty = 0

    # 1. Detect Self-Correlation (Same Player, Different Prop in the same game)
    player_prop_counts = {}
    for selection in slip_selections:
        key = (selection['playerName'], selection['propMarket'])
        player_prop_counts[key] = player_prop_counts.get(key, 0) + 1

    for count in player_prop_counts.values():
        if count > 1:
            correlation_penalty += 4
            correlation_warning = 'EXTREME: Multiple picks from the same player/prop market (Self-Correlation).'
            break

    # 2. Detect High Game Correlation (More than 2 picks in the same game)
    game_counts = {}
    for selection in slip_selections:
        game_id = selection['game_id']
        game_counts[game_id] = game_counts.get(game_id, 0) + 1

    for game_id, count in game_counts.items():
        if count > 2 and not correlation_warning:
            correlation_penalty += 2
            correlation_warning = f'HIGH: {count} picks from the same game ({game_id}). Positive correlation risk.'

    # 3. Calculate Trend Strength Score (TS)
    total_trend_score = sum(selection['trend_score'] for selection in slip_selections)
    trend_strength = total_trend_score / len(slip_selections)

    # Risk Score Formula (Lower is better): 10 - Trend Strength - Correlation Penalty
    risk_score = 10 - trend_strength - correlation_penalty
    
    return max(0, risk_score), correlation_warning, trend_strength