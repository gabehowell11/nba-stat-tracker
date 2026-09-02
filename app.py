import streamlit as st
import pandas as pd
import requests
from dotenv import load_dotenv
import os

# Load the API key from .env instead of hardcoding it (keeps secrets out of source control)
load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io/nba/v1"


# Cached so Streamlit reuses results for a team/season combo already fetched,
# instead of re-hitting the API on every rerun (free tier is capped at 5 req/min)
@st.cache_data(ttl=3600)
def get_team_record(team_id, season):
    """
    Fetches all games for a given team/season and computes win-loss record
    and scoring averages ourselves — the balldontlie free tier doesn't
    include a pre-built stats/season-averages endpoint, so this is calculated
    directly from raw game data.
    """
    response = requests.get(
        f"{BASE_URL}/games",
        headers={"Authorization": API_KEY},
        params={"team_ids[]": team_id, "seasons[]": season}
    )

    # Fail gracefully (e.g. rate limit hit) instead of crashing the app
    if response.status_code != 200:
        return None

    games = response.json()['data']

    wins = 0
    losses = 0
    points_scored = []
    points_allowed = []

    for game in games:
        if game['status'] != 'Final':
            continue  # skip games that haven't been played yet

        # The team we're tracking could be either the home or visitor side,
        # so figure out which score belongs to them each time
        if game['home_team']['id'] == team_id:
            team_score = game['home_team_score']
            opp_score = game['visitor_team_score']
        else:
            team_score = game['visitor_team_score']
            opp_score = game['home_team_score']

        points_scored.append(team_score)
        points_allowed.append(opp_score)

        if team_score > opp_score:
            wins += 1
        else:
            losses += 1

    # No completed games for this team/season (e.g. season hasn't started)
    if len(points_scored) == 0:
        return None

    return {
        'wins': wins,
        'losses': losses,
        'avg_scored': sum(points_scored) / len(points_scored),
        'avg_allowed': sum(points_allowed) / len(points_allowed),
        'games_played': len(games),
        'points_scored': points_scored,
        'points_allowed': points_allowed
    }


# NBA team IDs 1-30 (balldontlie also has historical/international teams
# with higher IDs, which we don't need here)
TEAMS = {
    "Atlanta Hawks": 1, "Boston Celtics": 2, "Brooklyn Nets": 3,
    "Charlotte Hornets": 4, "Chicago Bulls": 5, "Cleveland Cavaliers": 6,
    "Dallas Mavericks": 7, "Denver Nuggets": 8, "Detroit Pistons": 9,
    "Golden State Warriors": 10, "Houston Rockets": 11, "Indiana Pacers": 12,
    "LA Clippers": 13, "Los Angeles Lakers": 14, "Memphis Grizzlies": 15,
    "Miami Heat": 16, "Milwaukee Bucks": 17, "Minnesota Timberwolves": 18,
    "New Orleans Pelicans": 19, "New York Knicks": 20, "Oklahoma City Thunder": 21,
    "Orlando Magic": 22, "Philadelphia 76ers": 23, "Phoenix Suns": 24,
    "Portland Trail Blazers": 25, "Sacramento Kings": 26, "San Antonio Spurs": 27,
    "Toronto Raptors": 28, "Utah Jazz": 29, "Washington Wizards": 30
}

st.title("NBA Team Tracker")

season = st.selectbox("Choose a season", [2024, 2023, 2022, 2021, 2020])
team_name = st.selectbox("Choose a team", list(TEAMS.keys()))
team_id = TEAMS[team_name]

result = get_team_record(team_id, season)

if result is None:
    st.warning("No data available — either the free-tier rate limit (5 requests/min) was hit, or this team/season has no completed games. Wait a few seconds and try again.")
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Record", f"{result['wins']}-{result['losses']}")
    col2.metric("Avg Points Scored", f"{result['avg_scored']:.1f}")
    col3.metric("Avg Points Allowed", f"{result['avg_allowed']:.1f}")

    chart_data = pd.DataFrame({
        "Points Scored": result['points_scored'],
        "Points Allowed": result['points_allowed']
    })
    st.line_chart(chart_data)